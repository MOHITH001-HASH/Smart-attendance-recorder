import argparse
import csv
import getpass
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "smart_attendance_data"
ADMIN_CONFIG_PATH = DATA_DIR / "admin_config.json"
METADATA_PATH = DATA_DIR / "metadata.json"
MODEL_PATH = DATA_DIR / "face_model.yml"
ATTENDANCE_LOG_PATH = DATA_DIR / "attendance_log.csv"
ZONE_LOG_PATH = DATA_DIR / "zone_log.csv"
FACE_DATASET_DIR = DATA_DIR / "face_dataset"

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
MASTER_ADMIN_CREATION_PASSWORD = "CREATEADMIN2026"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_csv(path: Path, headers: List[str]) -> None:
    ensure_dir(path.parent)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def admin_is_initialized() -> bool:
    return ADMIN_CONFIG_PATH.exists()


def setup_admin(
    username: str,
    password: str | None = None,
    confirm_password: str | None = None,
    master_password: str | None = None,
) -> None:
    if admin_is_initialized():
        raise RuntimeError("Admin is already initialized.")

    if master_password is None:
        master_password = getpass.getpass("Enter master admin creation password: ").strip()
    else:
        master_password = master_password.strip()

    if master_password != MASTER_ADMIN_CREATION_PASSWORD:
        raise RuntimeError("Invalid master admin creation password.")

    if password is None:
        password = getpass.getpass("Create admin password: ").strip()
    else:
        password = password.strip()

    if confirm_password is None:
        confirm_password = getpass.getpass("Confirm admin password: ").strip()
    else:
        confirm_password = confirm_password.strip()

    if not password:
        raise RuntimeError("Password cannot be empty.")
    if password != confirm_password:
        raise RuntimeError("Passwords do not match.")

    save_json(
        ADMIN_CONFIG_PATH,
        {
            "username": username,
            "password_hash": hash_password(password),
        },
    )
    print(f"Admin '{username}' created successfully.")


def verify_admin_login(username: str, password: str) -> None:
    if not admin_is_initialized():
        raise RuntimeError("Admin not initialized. Run init-admin first.")

    config = load_json(ADMIN_CONFIG_PATH, {})
    if username != config.get("username"):
        raise RuntimeError("Invalid admin username.")

    if hash_password(password.strip()) != config.get("password_hash"):
        raise RuntimeError("Invalid admin password.")


def require_admin_login(username: str) -> None:
    password = getpass.getpass("Enter admin password: ").strip()
    verify_admin_login(username, password)


def get_detector():
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    if detector.empty():
        raise RuntimeError("Failed to load Haar Cascade.")
    return detector


def get_recognizer():
    return cv2.face.LBPHFaceRecognizer_create()


def load_metadata() -> Dict:
    return load_json(METADATA_PATH, {"next_label": 0, "people": {}, "label_map": {}})


def save_metadata(data: Dict) -> None:
    save_json(METADATA_PATH, data)


def get_or_create_label(metadata: Dict, person_id: str) -> int:
    label_map = metadata["label_map"]
    if person_id in label_map:
        return int(label_map[person_id])

    label = int(metadata["next_label"])
    metadata["next_label"] += 1
    metadata["label_map"][person_id] = label
    return label


def detect_faces(gray_frame: np.ndarray, detector) -> List[Tuple[int, int, int, int]]:
    faces = detector.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(60, 60),
    )
    return faces


def capture_face_samples(
    person_id: str,
    sample_count: int = 10,
    camera_index: int = 0,
) -> int:
    detector = get_detector()
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError("Unable to open camera.")

    person_dir = FACE_DATASET_DIR / person_id
    ensure_dir(person_dir)

    captured = 0
    print("Enrollment started.")
    print("Look at the camera. Press 'q' to stop.")

    while captured < sample_count:
        ok, frame = camera.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detect_faces(gray, detector)

        cv2.putText(
            frame,
            f"Captured: {captured}/{sample_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        if len(faces) == 0:
            cv2.putText(
                frame,
                "Face not detected. Move closer / improve light",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
        else:
            x, y, w, h = faces[0]
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))
            captured += 1
            img_path = person_dir / f"{captured:03d}.jpg"
            cv2.imwrite(str(img_path), face_img)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Enrollment", frame)
        key = cv2.waitKey(300) & 0xFF
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()
    return captured


def train_model() -> None:
    metadata = load_metadata()
    if not metadata["people"]:
        raise RuntimeError("No registered people found.")

    faces = []
    labels = []

    for person_id, details in metadata["people"].items():
        label = int(details["label"])
        person_dir = FACE_DATASET_DIR / person_id
        if not person_dir.exists():
            continue

        for img_path in person_dir.glob("*.jpg"):
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            faces.append(img)
            labels.append(label)

    if not faces:
        raise RuntimeError("No training images found.")

    recognizer = get_recognizer()
    recognizer.train(faces, np.array(labels))
    recognizer.save(str(MODEL_PATH))
    print("Face model trained successfully.")


def enroll_person(
    admin_username: str,
    person_id: str,
    name: str,
    role: str,
    department: str,
    email: str,
    phone: str,
    extra_info: str,
    camera_index: int = 0,
) -> None:
    require_admin_login(admin_username)

    metadata = load_metadata()
    label = get_or_create_label(metadata, person_id)

    metadata["people"][person_id] = {
        "label": label,
        "name": name,
        "role": role,
        "department": department,
        "email": email,
        "phone": phone,
        "extra_info": extra_info,
    }
    save_metadata(metadata)

    captured = capture_face_samples(person_id=person_id, sample_count=10, camera_index=camera_index)
    if captured < 5:
        raise RuntimeError("Not enough face samples captured. Try again.")

    train_model()
    print(f"Saved {role} record for {name} ({person_id}).")


def append_attendance(person_id: str, name: str, role: str, department: str) -> None:
    ensure_csv(ATTENDANCE_LOG_PATH, ["timestamp", "person_id", "name", "role", "department"])

    today_key = datetime.now().strftime("%Y-%m-%d")
    existing_ids = set()

    with ATTENDANCE_LOG_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["timestamp"].startswith(today_key):
                existing_ids.add(row["person_id"])

    if person_id in existing_ids:
        return

    with ATTENDANCE_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().isoformat(timespec="seconds"), person_id, name, role, department])


def load_model_and_metadata():
    if not MODEL_PATH.exists():
        raise RuntimeError("Trained model not found. Enroll people first.")

    metadata = load_metadata()
    recognizer = get_recognizer()
    recognizer.read(str(MODEL_PATH))
    detector = get_detector()

    reverse_map = {}
    for person_id, details in metadata["people"].items():
        reverse_map[int(details["label"])] = {"person_id": person_id, **details}

    return recognizer, detector, reverse_map


def draw_info(frame: np.ndarray, x: int, y: int, lines: List[str], color: Tuple[int, int, int]) -> None:
    yy = max(25, y - 15)
    for line in lines:
        cv2.putText(
            frame,
            line,
            (x, yy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
        yy += 22


def run_attendance(camera_index: int = 0, confidence_threshold: float = 65.0) -> None:
    recognizer, detector, reverse_map = load_model_and_metadata()
    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        raise RuntimeError("Unable to open camera.")

    print("Attendance mode started. Press 'q' to quit.")

    while True:
        ok, frame = camera.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detect_faces(gray, detector)

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))

            label, confidence = recognizer.predict(face_img)

            if label in reverse_map and confidence <= confidence_threshold:
                person = reverse_map[label]
                color = (0, 200, 0)
                lines = [
                    f"Name: {person['name']}",
                    f"ID: {person['person_id']} | Role: {person['role']}",
                    f"Dept/Class: {person.get('department', 'N/A') or 'N/A'}",
                ]
                if person.get("email"):
                    lines.append(f"Email: {person['email']}")
                if person.get("phone"):
                    lines.append(f"Phone: {person['phone']}")
                if person.get("extra_info"):
                    lines.append(f"Info: {person['extra_info']}")

                append_attendance(
                    person["person_id"],
                    person["name"],
                    person["role"],
                    person.get("department", ""),
                )
            else:
                color = (0, 0, 255)
                lines = [
                    "Unknown person",
                    f"Confidence score: {confidence:.2f}",
                ]

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            draw_info(frame, x, y, lines, color)

        cv2.putText(
            frame,
            "Attendance Mode - Press q to quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2,
        )
        cv2.imshow("Smart Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


def append_zone_log(zone_name: str, count: int, status: str) -> None:
    ensure_csv(ZONE_LOG_PATH, ["timestamp", "zone_name", "count", "status"])
    with ZONE_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().isoformat(timespec="seconds"), zone_name, count, status])


def build_people_detector():
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return hog


def run_zone_monitor(zone_name: str, max_capacity: int, camera_index: int = 0) -> None:
    detector = build_people_detector()
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError("Unable to open camera.")

    print("Zone monitor started. Press 'q' to quit.")

    last_count = None
    last_status = None

    while True:
        ok, frame = camera.read()
        if not ok:
            break

        resized = cv2.resize(frame, (640, 480))
        boxes, _ = detector.detectMultiScale(
            resized,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )

        count = len(boxes)
        if count >= max_capacity:
            status = "OVERCROWDED"
            color = (0, 0, 255)
        elif count >= int(max_capacity * 0.75):
            status = "BUSY"
            color = (0, 165, 255)
        else:
            status = "SAFE"
            color = (0, 200, 0)

        for (x, y, w, h) in boxes:
            cv2.rectangle(resized, (x, y), (x + w, y + h), color, 2)

        if count != last_count or status != last_status:
            append_zone_log(zone_name, count, status)
            last_count = count
            last_status = status

        cv2.putText(resized, f"Zone: {zone_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(resized, f"Count: {count}/{max_capacity}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(resized, f"Status: {status}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Zone Monitor", resized)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


def show_registered_people() -> None:
    metadata = load_metadata()
    people = metadata.get("people", {})
    if not people:
        print("No people registered.")
        return

    for person_id, details in people.items():
        print("-" * 50)
        print(f"ID: {person_id}")
        print(f"Name: {details.get('name', '')}")
        print(f"Role: {details.get('role', '')}")
        print(f"Department/Class: {details.get('department', '')}")
        print(f"Email: {details.get('email', '')}")
        print(f"Phone: {details.get('phone', '')}")
        print(f"Extra Info: {details.get('extra_info', '')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smart Attendance and Zone Monitor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin_parser = subparsers.add_parser("init-admin", help="Create admin account")
    admin_parser.add_argument("--username", required=True)

    enroll_parser = subparsers.add_parser("enroll", help="Enroll student or employee")
    enroll_parser.add_argument("--admin-user", required=True)
    enroll_parser.add_argument("--id", required=True)
    enroll_parser.add_argument("--name", required=True)
    enroll_parser.add_argument("--role", required=True, choices=["student", "employee"])
    enroll_parser.add_argument("--department", default="")
    enroll_parser.add_argument("--email", default="")
    enroll_parser.add_argument("--phone", default="")
    enroll_parser.add_argument("--extra-info", default="")
    enroll_parser.add_argument("--camera", type=int, default=0)

    attendance_parser = subparsers.add_parser("attendance", help="Run attendance recognition")
    attendance_parser.add_argument("--camera", type=int, default=0)
    attendance_parser.add_argument("--confidence-threshold", type=float, default=65.0)

    zone_parser = subparsers.add_parser("zone", help="Run zone monitor")
    zone_parser.add_argument("--name", required=True)
    zone_parser.add_argument("--capacity", type=int, required=True)
    zone_parser.add_argument("--camera", type=int, default=0)

    subparsers.add_parser("list-people", help="Show all registered people")
    subparsers.add_parser("train", help="Retrain face model")

    return parser


def main() -> None:
    ensure_dir(DATA_DIR)
    ensure_dir(FACE_DATASET_DIR)

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-admin":
        setup_admin(args.username)
    elif args.command == "enroll":
        enroll_person(
            admin_username=args.admin_user,
            person_id=args.id,
            name=args.name,
            role=args.role,
            department=args.department,
            email=args.email,
            phone=args.phone,
            extra_info=args.extra_info,
            camera_index=args.camera,
        )
    elif args.command == "attendance":
        run_attendance(
            camera_index=args.camera,
            confidence_threshold=args.confidence_threshold,
        )
    elif args.command == "zone":
        run_zone_monitor(
            zone_name=args.name,
            max_capacity=args.capacity,
            camera_index=args.camera,
        )
    elif args.command == "list-people":
        show_registered_people()
    elif args.command == "train":
        train_model()
    else:
        parser.error("Unknown command.")


if __name__ == "__main__":
    main()
