# main.py — v1.3: Final Patch — Safe f-string rendering inside Colab

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import os
from datetime import datetime

# ✅ 1. Fetch Deal from DesiDime RSS
def fetch_desidime_deals():
    rss = feedparser.parse('https://www.desidime.com/deals.rss')
    if not rss.entries:
        return None
    entry = rss.entries[0]
    return {
        "title": entry.title,
        "link": entry.link
    }

# ✅ 2. Fetch Comparison Prices from Smartprix (HTML Safe)
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

# ✅ 3. Create Poster Image using PIL
def generate_image(title, smart_prices):
    img = Image.new("RGB", (800, 600), color=(255,255,255))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 28)

    draw.text((50, 50), title, fill="black", font=font)
    draw.text((50, 150), smart_prices, fill="blue", font=font)

    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"deal-{now}.png"
    img.save(filename)
    return filename

# ✅ 4. Generate Caption from Gemini Free API
def generate_caption(title, prices):
    genai.configure(api_key="AIzaSyA2Q5P_bdCFVYNdlpZB33dBpLt7eaMIuJo")
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = f"Write a short, catchy caption for this product deal post:\nTitle: {title}\n\nPrices:\n{prices}"
    response = model.generate_content(prompt)
    return response.text.strip()

# ✅ 5. Run Everything

def fetch_cuelinks_deal():
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://www.cuelinks.com/deal-of-the-day"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("❌ Cuelinks page blocked or dead")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        deal = soup.select_one(".deal-box")

        if not deal:
            print("❌ No deals found on Cuelinks")
            return None

        title = deal.select_one(".deal-title").text.strip()
        merchant = deal.select_one(".merchant").text.strip()
        link_tag = deal.select_one("a")
        link = link_tag["href"] if link_tag else None

        return {
            "title": f"{merchant} - {title}",
            "link": link
        }
    except Exception as e:
        print("⚠️ Cuelinks fetch error:", str(e))
        return None



def fetch_deal():
    deal = fetch_cuelinks_deal()
    if deal:
        return deal
    else:
        send_personal_alert("❌ No deals found from Cuelinks.")
        return None


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

    print("✅ Image generated:", image_file)
    print("📝 Caption:\n", caption)

if __name__ == "__main__":
    main()
