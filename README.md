# 🛡️ Sentinel — Enterprise AI Surveillance Cloud Application

A modern, secure, and production-ready real-time AI surveillance web application. This project features high-efficiency computer vision powered by YOLOv8 for object and pose detection, deployed on Azure Cloud infrastructure, and integrated with automated cloud storage backup and real-time Telegram alert dispatching.

---

## 🛠️ Tech Stack & Architecture

- **Computer Vision & AI:** Ultralytics YOLOv8 (Object Detection & Pose Estimation), OpenCV
- **Backend Framework:** Python 3.10+, FastAPI, WebSockets, Uvicorn
- **Cloud Infrastructure:** Microsoft Azure Virtual Machine (Linux/Ubuntu), Azure Blob Storage
- **Alert System:** Telegram Bot API
- **Version Control:** Git, GitHub

---

## 🚀 Key Features Implemented

- **Real-Time Threat Detection:** Continuous scanning of live video feeds to detect physical threat objects like weapons and knives with minimal latency.
- **Pose & Concealment Analytics:** Keypoint tracking to identify suspicious postures, face masking, pocket concealment, and rapid violent hand gestures.
- **Centralized Event Logging (`detections/`):** Unified local directory storing time-stamped incident snapshots labeled with standardized event prefixes.
- **Automated Azure Cloud Storage:** Direct integration with Azure Blob Storage to backup verified threat evidence for audit trails and security logs.
- **Instant Telegram Alert Dispatch:** Real-time push notification pipeline delivering immediate threat descriptions, venue details, and snapshot attachments to security personnel.

---

## 📸 Application Preview & Visual Proof

### 🖥️ Real-Time Detection & Behavioral Analytics

1. **Weapon Threat Detection**
   System flags restricted physical items in real time, drawing bounding boxes and assigning confidence scores.

2. **Face Masking & Concealment Alert**
   Identifies hidden facial keypoints or suspicious face coverage during active video monitoring.

3. **Suspicious Posture Analytics**
   Detects abrupt movements, pocket concealment gestures, and unnatural pose positions.

### ⚙️ Backend & Cloud Infrastructure

4. **Central Evidence Storage (`detections/`)**
   Standardized incident snapshot logging across local storage and cloud syncing pipelines.

5. **Azure Virtual Machine Hosting**
   Demonstrates continuous background execution and live WebSocket endpoint streaming on cloud infrastructure.

6. **Azure Blob Storage Bucket**
   Cloud storage table tracking synced snapshot payloads, image logs, and historical security data.

7. **Instant Telegram Alert System**
   Live verification of immediate notification alerts with attached image proof sent directly to security channels.
