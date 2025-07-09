import os
import requests

def send_personal_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    personal_chat_id = os.environ.get("TELEGRAM_PERSONAL_CHAT_ID")
    
    if not (bot_token and personal_chat_id):
        print("⚠️ Telegram personal alert credentials missing.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": personal_chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    print("📩 Personal alert sent:", response.status_code)
    print(response.text)
