import logging
import math
import cv2
import numpy as np
from ultralytics import YOLO
from config import config

logger = logging.getLogger("SurveillanceLogger")

class SurveillanceDetector:
    def __init__(self):
        try:
            self.object_model = YOLO("yolov8n.pt")
            self.pose_model = YOLO("yolov8n-pose.pt")
            logger.info("YOLO Models loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load YOLO models: {e}")
            raise e

    @staticmethod
    def calculate_distance(p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def analyze_frame(self, frame):
        # Frame processing and threat detection logic here
        results = self.object_model(frame, conf=config.CONFIDENCE_THRESHOLD)
        # Returns annotated frame and detected threats list
        return frame, []
