import requests

def send_telegram_post(image_path, caption):
    url = f"https://api.telegram.org/bot7414769864:AAFxaCSPVtbCbelo-BeyO2Mk6p-1aM_DC6M/sendPhoto"
    with open(image_path, "rb") as img:
        data = {
            "chat_id": "@cheapsale3",
            "caption": caption
        }
        files = {
            "photo": img
        }
        response = requests.post(url, data=data, files=files)
        print("📤 Telegram response:", response.status_code)
        print(response.text)
