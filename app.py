import cv2
import base64
import asyncio
import time
import math
import requests
import numpy as np
from io import BytesIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from azure.storage.blob import BlobServiceClient

app = FastAPI(title="Sentinel Enterprise AI Surveillance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models
pose_model = YOLO('yolov8n-pose.pt')
object_model = YOLO('yolov8s.pt')

executor = ThreadPoolExecutor(max_workers=3)

# --- CREDENTIALS (PLACEHOLDERS) ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
AZURE_CONNECTION_STRING = "YOUR_AZURE_CONNECTION_STRING"
AZURE_CONTAINER_NAME = "surveillance-alerts"
VENUE_LOCATION = "Store_Front_Gate_01"

# COCO Threat Class IDs: 43 (Knife), 76 (Scissors)
THREAT_CLASSES = [43, 76]

LAST_ALERT_TIME = 0
ALERT_COOLDOWN = 4
SUSPICIOUS_BEHAVIOR_COUNT = 0
MAX_SUSPICIOUS_THRESHOLD = 5

prev_person_keypoints = {}

def dist(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def upload_to_azure_blob(frame, threat_type):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

        if not container_client.exists():
            container_client.create_container()

        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{VENUE_LOCATION}/{time_stamp}_{threat_type}.jpg"

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(buffer.tobytes(), overwrite=True)
        print(f"Uploaded Incident to Azure Blob Storage: {blob_name}")
    except Exception as e:
        print(f"Azure Blob Upload Error: {e}")

def send_telegram_task(frame, threat_type):
    global LAST_ALERT_TIME
    current_time = time.time()
    if current_time - LAST_ALERT_TIME < ALERT_COOLDOWN:
        return

    LAST_ALERT_TIME = current_time

    try:
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        bio = BytesIO(buffer)
        bio.name = 'alert.jpg'

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caption = f"🚨 SECURITY THREAT DETECTED!\nVenue: {VENUE_LOCATION}\nStatus: {threat_type}\nTime: {time_str}"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {'photo': bio}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}

        requests.post(url, data=data, files=files, timeout=4)
    except Exception as e:
        print(f"Telegram Dispatch Error: {e}")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sentinel AI High-Quality Surveillance</title>
    <style>
        * { box-sizing: border-box; }
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .feed-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 25px;
            width: 100%;
        }
        .feed-box {
            flex: 1;
            background: #1e1e1e;
            border: 2px solid #00ff66;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 255, 102, 0.15);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .feed-box h3 { margin: 0 0 15px 0; color: #ffffff; font-size: 22px; }
        .img-wrapper {
            width: 100%;
            height: 500px;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
        }
        video, img { width: 100%; height: 100%; object-fit: contain; display: block; }
        .logs-container {
            background: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #333;
            width: 100%;
        }
        .logs-container h3 { color: #00ff66; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #2a2a2a; }
        th { color: #ffaa00; }
        .threat-tag { color: #ff0055; font-weight: bold; }
        .status-badge {
            background: #0088cc;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
</head>
<body>

    <div class="feed-container">
        <div class="feed-box">
            <h3>Live CCTV Feed</h3>
            <div class="img-wrapper">
                <video id="webcam" autoplay playsinline muted></video>
            </div>
        </div>
        <div class="feed-box">
            <h3>AI Threat Analytics (Low Latency HD)</h3>
            <div class="img-wrapper">
                <img id="ai_feed" src="" alt="Live Stream Active..." />
            </div>
        </div>
    </div>

    <div class="logs-container">
        <h3>📝 Real-Time Threat Event Logs</h3>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Threat Detected</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="log_table">
            </tbody>
        </table>
    </div>

    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById("webcam");
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");
        const aiImg = document.getElementById("ai_feed");
        const logTable = document.getElementById("log_table");

        const ws = new WebSocket("ws://" + window.location.host + "/ws");
        let isProcessing = false;

        navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 } } })
            .then((stream) => { video.srcObject = stream; })
            .catch((err) => { alert("Please allow camera access!"); });

        function sendFrame() {
            if (!isProcessing && video.readyState === video.HAVE_ENOUGH_DATA && ws.readyState === WebSocket.OPEN) {
                isProcessing = true;
                canvas.width = 1280;
                canvas.height = 720;
                ctx.drawImage(video, 0, 0, 1280, 720);
                const base64Frame = canvas.toDataURL("image/jpeg", 0.75).split(",")[1];
                ws.send(base64Frame);
            }
        }

        ws.onopen = () => {
            setInterval(sendFrame, 40);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.ai_frame) {
                aiImg.src = "data:image/jpeg;base64," + data.ai_frame;
            }

            if (data.threat) {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${data.timestamp}</td>
                    <td class="threat-tag">${data.threat}</td>
                    <td><span class="status-badge">ALERTED</span></td>
                `;
                logTable.insertBefore(row, logTable.firstChild);
            }
            isProcessing = false;
        };
    </script>
</body>
</html>
"""

@app.get("/")
def get_dashboard():
    return HTMLResponse(content=HTML_LAYOUT)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global prev_person_keypoints, SUSPICIOUS_BEHAVIOR_COUNT
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            loop = asyncio.get_event_loop()

            obj_results, pose_results = await asyncio.gather(
                loop.run_in_executor(None, lambda: object_model(frame, imgsz=416, conf=0.25, verbose=False)),
                loop.run_in_executor(None, lambda: pose_model(frame, imgsz=416, conf=0.30, verbose=False))
            )

            annotated_frame = frame.copy()
            detected_threat_name = None

            cv2.putText(annotated_frame, "SYSTEM ACTIVE - REALTIME SURVEILLANCE", (25, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 1. Object Detection
            for r in obj_results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = object_model.names[cls_id].upper()
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if cls_id in THREAT_CLASSES:
                        if conf >= 0.55:
                            detected_threat_name = f"WEAPON_{label}"
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.putText(annotated_frame, f"CRITICAL: {label} {conf:.2f}", (x1, max(y1 - 10, 25)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, f"{label} {conf:.2f}", (x1, max(y1 - 10, 25)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 2. Pose & Behavior Analytics
            current_person_keypoints = {}

            for r in pose_results:
                if r.keypoints is not None and len(r.keypoints) > 0:
                    for person_idx, kps in enumerate(r.keypoints.data):
                        nose = kps[0]
                        l_wrist, r_wrist = kps[9], kps[10]
                        l_hip, r_hip = kps[11], kps[12]

                        if nose[2] > 0.3:
                            cv2.circle(annotated_frame, (int(nose[0]), int(nose[1])), 5, (0, 255, 255), -1)

                        # A. Half-Face Cover
                        for wrist in [l_wrist, r_wrist]:
                            if wrist[2] > 0.35 and nose[2] > 0.35:
                                d = dist((wrist[0].item(), wrist[1].item()), (nose[0].item(), nose[1].item()))
                                if d < 110:
                                    cv2.putText(annotated_frame, "⚠️ HALF FACE COVERED!", (25, 80),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                    if not detected_threat_name:
                                        detected_threat_name = "HALF_FACE_COVERED"

                        # B. Pocket Entry / Concealment
                        for wrist in [l_wrist, r_wrist]:
                            for hip in [l_hip, r_hip]:
                                if wrist[2] > 0.35 and hip[2] > 0.35:
                                    d = dist((wrist[0].item(), wrist[1].item()), (hip[0].item(), hip[1].item()))
                                    if d < 75:
                                        cv2.putText(annotated_frame, "⚠️ SUSPECTED CONCEALMENT", (25, 120),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                                        if not detected_threat_name:
                                            detected_threat_name = "POCKET_CONCEALMENT"

                        # C. Violent Motion Tracking
                        current_person_keypoints[person_idx] = (l_wrist[0].item(), l_wrist[1].item(), l_wrist[2].item())
                        if person_idx in prev_person_keypoints and l_wrist[2] > 0.35 and prev_person_keypoints[person_idx][2] > 0.35:
                            prev_x, prev_y, _ = prev_person_keypoints[person_idx]
                            hand_velocity = dist((l_wrist[0].item(), l_wrist[1].item()), (prev_x, prev_y))

                            if hand_velocity > 300:
                                cv2.putText(annotated_frame, "⚡ VIOLENT MOTION DETECTED", (25, 160),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
                                if not detected_threat_name:
                                    detected_threat_name = "FIGHT_MOTION"

            prev_person_keypoints = current_person_keypoints

            # 3. Alert Processing & Cloud Upload
            if detected_threat_name:
                SUSPICIOUS_BEHAVIOR_COUNT += 1
                loop.run_in_executor(executor, send_telegram_task, annotated_frame.copy(), detected_threat_name)

                if SUSPICIOUS_BEHAVIOR_COUNT >= MAX_SUSPICIOUS_THRESHOLD or "WEAPON" in detected_threat_name:
                    cv2.putText(annotated_frame, f"☁️ CLOUD SYNCED ({SUSPICIOUS_BEHAVIOR_COUNT}/{MAX_SUSPICIOUS_THRESHOLD})", (25, 200),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    loop.run_in_executor(executor, upload_to_azure_blob, annotated_frame.copy(), detected_threat_name)
                    SUSPICIOUS_BEHAVIOR_COUNT = 0

            _, ai_buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            ai_b64 = base64.b64encode(ai_buffer).decode('utf-8')

            payload = {
                "ai_frame": ai_b64,
                "threat": detected_threat_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if detected_threat_name else None
            }

            await websocket.send_json(payload)

    except WebSocketDisconnect:
        pass
