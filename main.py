import os
import requests
from bs4 import BeautifulSoup
import feedparser
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import google.generativeai as genai

print("🟢 Running updated main.py — Build v3.2")

def send_personal_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    personal_id = os.environ.get("TELEGRAM_PERSONAL_CHAT_ID")
    if not bot_token or not personal_id:
        return
    payload = {
        "chat_id": personal_id,
        "text": message
    }
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, data=payload)
    except:
        pass

def fetch_deal():
    headers = {"User-Agent": "Mozilla/5.0"}

    # ✅ Cuelinks
    try:
        print("➡️ Trying Cuelinks...")
        r = requests.get("https://www.cuelinks.com/deal-of-the-day", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        box = soup.select_one(".deal-box")
        if box:
            title = box.select_one(".deal-title").text.strip()
            merchant = box.select_one(".merchant").text.strip()
            short_url = box.select_one("a")["href"]
            resolved = requests.get(short_url, headers=headers, allow_redirects=True)
            real = resolved.url
            ek_id = os.environ.get("EARNKARO_ID")
            if ek_id:
                real = f"https://ekaro.in/en?k={ek_id}&url={real}"
            return { "title": f"{merchant}: {title}", "link": real }
    except Exception as e:
        print("❌ Cuelinks failed:", e)

    # ✅ Smartprix RSS
    try:
        print("➡️ Trying Smartprix RSS...")
        rss = feedparser.parse("https://www.smartprix.com/feeds/deals")
        if rss.entries:
            entry = rss.entries[0]
            return { "title": entry.title, "link": entry.link }
    except Exception as e:
        print("❌ Smartprix RSS failed:", e)

    # ✅ ScraperAPI backup
    try:
        print("➡️ Trying Smartprix HTML via ScraperAPI...")
        scraper_key = os.environ.get("SCRAPERAPI_KEY")
        base = "https://www.smartprix.com/deals"
        proxied = f"http://api.scraperapi.com?api_key={scraper_key}&url={base}"
        r = requests.get(proxied)
        soup = BeautifulSoup(r.text, "html.parser")
        prod = soup.select_one(".sm-product .title")
        price = soup.select_one(".sm-product .price")
        if prod and price:
            return {
                "title": prod.text.strip() + " - " + price.text.strip(),
                "link": base
            }
    except Exception as e:
        print("❌ ScraperAPI failed:", e)

    print("❌ All sources failed.")
    send_personal_alert("❗ No deals found by the bot.")
    return None

def fetch_smartprix_prices():
    try:
        r = requests.get("https://www.smartprix.com/laptops", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".sm-product")
        result = []
        for card in cards[:2]:
            name = card.select_one(".title").text.strip()
            price = card.select_one(".price").text.strip()
            result.append(f"🔹 {name} - {price}")
        return "\n".join(result)
    except:
        return "❌ Price data not fetched"


def generate_caption(title, prices, deal_url):
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        prompt = f"Create a short caption for product: {title}\nPrices:\n{prices}\nLink: {deal_url}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"🔥 {title}\n{prices}\n🛒 {deal_url}"


def generate_image(title, prices):
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font = ImageFont.load_default()
    draw.text((50, 50), title, fill="black", font=font)
    draw.text((50, 150), prices, fill="blue", font=font)
    fname = f"deal-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    img.save(fname)
    return fname


def send_telegram_post(image, caption):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    channel = os.environ.get("TELEGRAM_CHANNEL")
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image, "rb") as img:
        files = {"photo": img}
        data = {"chat_id": channel, "caption": caption}
        try:
            r = requests.post(url, data=data, files=files)
            print("✅ Telegram:", r.status_code)
        except:
            print("❌ Telegram post failed")


def main():
    print("✅ BOT VERSION: Fetch Engine v3.2 with ScraperAPI + Gemini + Alerts")
    deal = fetch_deal()
    if not deal:
        return
    prices = fetch_smartprix_prices()
    link = deal['link']
    caption = generate_caption(deal['title'], prices, link)
    image = generate_image(deal['title'], prices)
    send_telegram_post(image, caption)


if __name__ == "__main__":
    main()
