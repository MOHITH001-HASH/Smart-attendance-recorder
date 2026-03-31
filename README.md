# Smart Attendance and Zone Monitor

## Overview
Smart Attendance and Zone Monitor is a computer vision based campus management system that automates attendance using face recognition and monitors crowd levels in shared campus spaces such as libraries, labs, and gyms.

This project was built as a Bring Your Own Project (BYOP) to solve a real-world problem observed in educational institutions: manual attendance takes time, and public campus spaces can become overcrowded without any live monitoring system.

## Problem Statement
Traditional attendance systems are slow, manual, and prone to human error. At the same time, campus spaces like libraries, labs, cafeterias, and gyms often become crowded, making it difficult for administrators to monitor occupancy levels in real time.

This project addresses both issues by using computer vision:
- Face recognition for automatic attendance
- Human detection for zone occupancy monitoring

## Features
- Admin-controlled system
- Master password required to create the admin account
- Separate enrollment for students and employees
- Face-based attendance system
- Displays stored personal details after recognition
- Attendance logging with timestamp
- Zone occupancy monitoring
- Status classification: `SAFE`, `BUSY`, `OVERCROWDED`
- Tkinter-based GUI with sidebar navigation
- Camera settings for selecting webcam index

## Technologies Used
- Python
- OpenCV
- NumPy
- Tkinter
- Haar Cascade for face detection
- LBPH Face Recognizer for face recognition
- HOG-based people detector for human counting
- Git and GitHub for version control

## Project Structure
```text
Smart Attendance and Zone Monitor/
│
├── smart_attendance_zone_monitor.py
├── smart_attendance_admin_gui.py
├── requirements_smart_attendance.txt
├── README.md
└── smart_attendance_data/
