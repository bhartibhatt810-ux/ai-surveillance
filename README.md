# Sentinel AI - Real-Time Surveillance & Threat Detection

An AI-powered real-time surveillance system built with **FastAPI**, **YOLOv8**, and **WebSockets**. It detects security threats, suspicious behavior (face-covering, concealment, violent motion), dispatches alerts to **Telegram**, and syncs incident logs to **Azure Blob Storage**.

## Features
- Real-time video stream analytics via WebSockets.
- Object & Threat Detection using YOLOv8.
- Behavior analytics (Fall detection, violent motion, concealment).
- Automated Telegram alert notifications.
- Incident cloud archiving on Azure Blob Storage.

## Installation & Setup
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd ai-surveillance
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

