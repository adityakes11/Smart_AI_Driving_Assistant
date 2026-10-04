# Smart AI Driving Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Node.js](https://img.shields.io/badge/Node.js-20%2B-green) ![Flutter](https://img.shields.io/badge/Flutter-3.22%2B-purple)

## 📌 Project Definition

The **Smart AI Driving Assistant** is an integrated safety platform that continuously monitors a vehicle’s surroundings using computer‑vision, evaluates risky situations (lane departure, traffic‑light violations, imminent collisions, and accidents), and instantly informs the driver through voice alerts. When a severe accident is detected, the system automatically generates an SOS payload and forwards it to a cloud backend for emergency response and logging. A companion Flutter mobile app provides real‑time status, location tracking, and manual SOS capability, completing an end‑to‑end solution from perception to emergency management.



---

## 📖 Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Setup & Installation (Windows)](#setup--installation-windows)
   - [Python – Accident Detection](#python–accident-detection)
   - [Node.js – Backend API](#nodejs–backend-api)
   - [Flutter – Mobile App](#flutter–mobile-app)
6. [Configuration](#configuration)
7. [Running the System](#running-the-system)
8. [Contributing](#contributing)
9. [License](#license)
10. [Acknowledgements](#acknowledgements)

---

## 🚀 Features

| Category | Description |
|----------|-------------|
| **Computer Vision** | YOLO v8 (nano & small) for vehicle, sign & lane detection. |
| **Collision / Accident Detection** | Motion‑spike analysis, distance‑gap heuristics, impact‑score thresholds. |
| **Voice Assistant (JARVIS)** | Text‑to‑speech alerts for lane departure, traffic‑light, collision & accident. |
| **SOS Handler** | Automatic JSON payload to backend when a severe accident is detected. |
| **REST Backend** | Express API for authentication, SOS logging, location tracking. |
| **Mobile UI** | Flutter map view, live status, manual SOS button, user profile. |
| **Cross‑Platform** | Core perception runs on Windows/Linux; mobile UI works on Android & iOS. |
| **Extensible** | Modular Python classes, clear API endpoints, configurable thresholds. |

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    subgraph CV["Python CV Engine"]
        A[Dash‑cam Video] --> B[AccidentDetector]
        B --> C[VoiceAssistant (TTS)]
        B --> D[Dashboard (annotated frames)]
        B --> E[SOSHandler]
    end

    subgraph API["Node.js Backend"]
        E --> F[POST /api/sos]
        F --> G[MongoDB (SOS logs)]
        F --> H[Push/Socket notifications]
    end

    subgraph Mobile["Flutter App"]
        I[GET /api/user] --> J[Auth]
        K[GET /api/sos] --> L[Live SOS Feed]
        M[GET /api/location] --> N[Map view]
    end

    CV -->|HTTP POST| API
    API -->|WebSocket / REST| Mobile
```

- The **Python engine** performs all heavy‑weight perception locally (no cloud latency).  
- When an accident is confirmed, **SOSHandler** posts to **/api/sos**.  
- **Backend** stores the alert, can push notifications to the mobile app, and logs the event in the database.  
- **Flutter app** pulls the latest status (including any SOS alerts) and presents it to the driver.

---

## 🛠️ Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| **Perception / AI** | **Python 3.10+**, OpenCV, NumPy, **Ultralytics YOLOv8** (`yolov8n.pt`, `yolov8s.pt`) | State‑of‑the‑art object detection, lightweight enough for real‑time inference on a laptop/edge device. |
| **Voice** | `pyttsx3` (Windows TTS) | Offline, low‑latency speech synthesis. |
| **Backend** | **Node.js 20**, Express, Mongoose (MongoDB), Redis, Socket.io | Scalable, event‑driven API with simple CRUD & real‑time push. |
| **Mobile** | **Flutter 3.22**, Dart, `flutter_map`, `geolocator`, `http` | Cross‑platform UI, fast dev cycle, native map rendering. |
| **Data Store** | MongoDB (cloud or local), optional Redis cache | Persistent SOS logs & user data. |
| **Configuration** | YAML (`pubspec.yaml`), Python `Config` class | Centralised, easy to tweak thresholds. |
| **Packaging** | Virtualenv (`.venv`) for Python, `npm` for Node, `flutter` CLI for mobile | Isolated environments per component. |

---

## 📂 Project Structure

```
Smart_AI_Driving_Assistant
│
├─ accident-detection/                # Python perception pipeline
│   ├─ main.py                       # Entry point – SmartDrivingAssistant
│   ├─ accident_detector.py
│   ├─ vehicle_detector.py
│   ├─ lane_detector.py
│   ├─ sign_detector.py
│   ├─ collision_warning.py
│   ├─ dashboard.py
│   ├─ voice_assistant_windows.py
│   ├─ traffic_voice_alerts.py
│   ├─ sos_handler.py
│   └─ requirements.txt
│
├─ backend/                           # Node/Express API
│   ├─ server.js                     # Starts Express & connects DB
│   ├─ package.json
│   └─ src/
│       ├─ config/
│       │   ├─ db.js
│       │   └─ redis.js
│       ├─ controllers/
│       │   ├─ auth.controller.js
│       │   ├─ sos.controller.js
│       │   └─ location.controller.js
│       ├─ models/
│       │   ├─ user.js
│       │   ├─ sos.js
│       │   └─ location.model.js
│       └─ routes/
│           ├─ auth.js
│           ├─ sos.routes.js
│           ├─ location.routes.js
│           └─ user.routes.js
│
└─ flutter-app/                       # Mobile UI (Flutter)
    ├─ pubspec.yaml                  # Dependencies
    ├─ lib/
    │   ├─ main.dart                 # App entry point
    │   └─ … (screens, widgets, services)
    └─ android/ / ios/                # Platform‑specific folders
```

*Key files you may want to open directly:*  
- Python entry: **[main.py](file:///c:/Users/adity/Smart_AI_Driving_Assistant/accident-detection/main.py)**  
- Accident detection core: **[accident_detector.py](file:///c:/Users/adity/Smart_AI_Driving_Assistant/accident-detection/accident_detector.py)**  
- Backend entry: **[server.js](file:///c:/Users/adity/Smart_AI_Driving_Assistant/backend/server.js)**  
- Flutter dependencies: **[pubspec.yaml](file:///c:/Users/adity/Smart_AI_Driving_Assistant/flutter-app/pubspec.yaml)**  

---

## 📦 Setup & Installation (Windows)

> **Prerequisite**: Ensure you have **Python 3.10+**, **Node.js 20+**, **Flutter 3.22+**, and **Git** installed.

### 1. Python – Accident Detection

```powershell
cd C:\Users\adity\Smart_AI_Driving_Assistant\accident-detection
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Download the YOLO model (first run will auto‑download or you can manually place the files):

```powershell
# Optional – pre‑download smaller model
curl -L -o yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
curl -L -o yolov8s.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
```

Run the assistant (default uses the video source defined in `config.py`):

```powershell
python main.py --input-source 0   # 0 = webcam, or path to a video file
```

### 2. Node.js – Backend API

```powershell
cd C:\Users\adity\Smart_AI_Driving_Assistant\backend
npm install
# (Optional) create a .env file with MONGODB_URI, REDIS_URL, JWT_SECRET
node server.js
```

The API listens on **http://0.0.0.0:8000**.

### 3. Flutter – Mobile App

```powershell
cd C:\Users\adity\Smart_AI_Driving_Assistant\flutter-app
flutter pub get
flutter run   # Connect a device or emulator
```

*If you need to point the app to a custom backend URL, edit `lib/services/api_service.dart` (or use a config file).*  

---

## ⚙️ Configuration

| File | What to edit | Example |
|------|--------------|---------|
| `accident-detection/config.py` | Thresholds, video source, model filenames | `collision_distance = 80` |
| `backend/.env` (create) | MongoDB URI, JWT secret, port | `MONGODB_URI=mongodb://localhost:27017/smart_ai` |
| `flutter-app/lib/services/api_service.dart` | Base URL for the backend | `const String baseUrl = "http://192.168.1.10:8000";` |

All thresholds are deliberately set **low** for faster detection; feel free to increase (`collision_distance`, `gap_closing_threshold`, etc.) to reduce false positives.

---

## ▶️ Running the Full System

1. **Start the backend** (`node server.js`).
2. **Launch the Python driver** (`python main.py`).
3. **Open the Flutter app** on a phone or emulator.
4. The phone will display the driver’s current status. When the Python engine detects an accident, you’ll hear a voice alert and the app will show an SOS notification automatically.

*Tip*: Keep the Python console window open to see logging (e.g., “🚗 Loading YOLO model…”, “✅ Accident detected – sending SOS”).

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my‑new‑sensor`).
3. Follow the same coding style (PEP 8 for Python, ESLint for Node, `flutter format` for Dart).
4. Submit a PR with a clear description and, if applicable, updated documentation.

> **Testing** – Python unit tests are located in `accident-detection/tests/`. Run with `pytest`.  
> **Backend tests** – Use `npm test` (Jest).

---

## 📄 License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## 🙏 Acknowledgements

- **Ultralytics** for the YOLOv8 models and Python API.
- **Flutter** team for the cross‑platform UI toolkit.
- Open‑source contributors of `opencv-python`, `pyttsx3`, `express`, `mongoose`, and many others.

---

*Happy coding! 🚗💨*
