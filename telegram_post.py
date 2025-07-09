import os
import requests

def send_telegram_post(image_path, caption):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    channel = os.environ.get("TELEGRAM_CHANNEL")
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image_path, "rb") as img:
        data = {
            "chat_id": channel,
            "caption": caption
        }
        files = {
            "photo": img
        }
        response = requests.post(url, data=data, files=files)
        print("📤 Telegram response:", response.status_code)
        print(response.text)
