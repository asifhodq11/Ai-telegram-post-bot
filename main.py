import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import os
from datetime import datetime
from telegram_post import send_telegram_post
from personal_post import send_personal_alert

# ✅ Try RSS First
def fetch_desidime_rss():
    url = "https://www.desidime.com/deals.rss"
    rss = feedparser.parse(url)
    if not rss.entries:
        return None
    first = rss.entries[0]
    return {"title": first.title, "link": first.link}

# ✅ Fallback Deals Scraper if RSS fails
def fetch_desidime_html():
    url = "https://www.desidime.com/deals"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        card = soup.select_one(".deal-info")
        title = card.select_one(".deal-title").get_text(strip=True)
        link = "https://www.desidime.com" + card.select_one("a")["href"]
        return {"title": title, "link": link}
    except Exception as e:
        print("❌ HTML scrape failed:", e)
        return None

# ✅ Full Getter with fallback logic
def fetch_desidime_deal():
    deal = fetch_desidime_rss()
    if deal:
        return deal
    print("⚠️ RSS failed, trying fallback...")
    deal = fetch_desidime_html()
    return deal

def fetch_smartprix_prices():
    url = 'https://www.smartprix.com/laptops'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
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
    return "\n".join(results) if results else "⚠️ No prices found."

def generate_image(title, prices):
    img = Image.new("RGB", (800,600), color=(255,255,255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    draw.text((50, 50), title, fill="black", font=font)
    draw.text((50, 150), prices, fill="blue", font=font)
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"deal-{now}.png"
    img.save(filename)
    return filename

def convert_to_earnkaro_link(original_url):
    user_id = os.environ.get("EARNKARO_ID")
    return f"https://ekaro.in/en?k={user_id}&url={original_url}" if user_id else original_url

def generate_caption(title, prices, deal_url):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-pro")
    affiliate = convert_to_earnkaro_link(deal_url)
    prompt = f"Write a short catchy caption for this product deal:\nTitle: {title}\nPrices:\n{prices}"
    response = model.generate_content(prompt)
    return response.text.strip() + f"\n\n🛍️ Buy Now: {affiliate}"

def main():
    deal = fetch_desidime_deal()
    if not deal:
        send_personal_alert("❌ No deals found in RSS or HTML today!")
        return
    prices = fetch_smartprix_prices()
    caption = generate_caption(deal['title'], prices, deal['link'])
    image_file = generate_image(deal['title'], prices)

    with open("caption.txt", "w") as f:
        f.write(caption)

    print("✅ Image:", image_file)
    print("📝 Caption:", caption)

    # Auto-post to channel
    send_telegram_post(image_file, caption)

if __name__ == "__main__":
    main()
