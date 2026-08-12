import logging
import requests
from config import config

logger = logging.getLogger("SurveillanceLogger")

def send_telegram_alert(image_bytes: bytes, caption: str) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured. Skipping alert.")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {"chat_id": config.TELEGRAM_CHAT_ID, "caption": caption}
    files = {"photo": ("alert.jpg", image_bytes, "image/jpeg")}

    try:
        response = requests.post(url, data=data, files=files, timeout=10)
        response.raise_for_status()
        logger.info("Telegram alert sent successfully.")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
