# main.py — v1.4 with Telegram Integration

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from datetime import datetime
from telegram_post import send_telegram_post

def fetch_desidime_deals():
    rss = feedparser.parse('https://www.desidime.com/deals.rss')
    if not rss.entries:
        return None
    entry = rss.entries[0]
    return {"title": entry.title, "link": entry.link}

def fetch_smartprix_prices():
    url = 'https://www.smartprix.com/laptops'
    response = requests.get(url)
    if response.status_code != 200:
        return "⚠️ Failed to fetch Smartprix data."
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.select(".sm-product")
    results = []
    for p in products[:5]:
        title_elem = p.select_one(".title")
        price_elem = p.select_one(".price")
        if title_elem and price_elem:
            name = title_elem.get_text(strip=True)
            price = price_elem.get_text(strip=True)
            results.append(f"🔹 {name} - {price}")
            if len(results) >= 2:
                break
    return "\n".join(results) if results else "⚠️ No valid products found."

def generate_image(title, smart_prices):
    img = Image.new("RGB", (800,600), color=(255,255,255))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 28)
    draw.text((50, 50), title, fill="black", font=font)
    draw.text((50, 150), smart_prices, fill="blue", font=font)
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"deal-{now}.png"
    img.save(filename)
    return filename

def generate_caption(title, prices):
    genai.configure(api_key="AIzaSyA2Q5P_bdCFVYNdlpZB33dBpLt7eaMIuJo")
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"Write a catchy promo caption:\n\nTitle: {title}\n\nPrices:\n{prices}"
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    deal = fetch_desidime_deals()
    if not deal:
        print("❌ No deals found.")
        return
    smart_prices = fetch_smartprix_prices()
    caption = generate_caption(deal['title'], smart_prices)
    image_file = generate_image(deal['title'], smart_prices)

    with open("caption.txt", "w") as f:
        f.write(caption)

    print("✅ Image:", image_file)
    print("📝 Caption:", caption)

    # ✅ Post to Telegram
    send_telegram_post(image_file, caption)

if __name__ == "__main__":
    main()
