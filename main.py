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

def fetch_deal(keyword="smartphone"):
    import requests
    from bs4 import BeautifulSoup
    import os
    import feedparser

    headers = {"User-Agent": "Mozilla/5.0"}

    # ✅ 1. Try Cuelinks (safe, monetized)
    try:
        print("🔍 Trying Cuelinks...")
        r = requests.get("https://www.cuelinks.com/deal-of-the-day", headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        box = soup.select_one(".deal-box")
        if box:
            title = box.select_one(".deal-title").text.strip()
            merchant = box.select_one(".merchant").text.strip()
            link = box.select_one("a")["href"]
            redirect = requests.get(link, headers=headers, allow_redirects=True)
            actual = redirect.url
            ek_id = os.environ.get("EARNKARO_ID")
            affiliate_url = f"https://ekaro.in/en?k={ek_id}&url={actual}" if ek_id else actual
            return {"title": f"{merchant}: {title}", "link": affiliate_url}
    except Exception as e:
        print("❌ Cuelinks failed:", e)

    # ✅ 2. Smartprix RSS feed
    try:
        print("🌐 Trying Smartprix RSS...")
        rss = feedparser.parse("https://www.smartprix.com/feeds/deals")
        if rss.entries:
            entry = rss.entries[0]
            return {"title": entry.title, "link": entry.link}
    except Exception as e:
        print("❌ Smartprix RSS failed:", e)

    # ✅ 3. Smartprix HTML via ScraperAPI (no block)
    try:
        print("🛠 Fallback: Smartprix HTML via ScraperAPI...")
        api_key = os.environ.get("SCRAPERAPI_KEY")
        clean_url = "https://www.smartprix.com/deals"
        proxied = f"http://api.scraperapi.com?api_key={api_key}&url={clean_url}"

        r = requests.get(proxied)
        soup = BeautifulSoup(r.text, "html.parser")
        block = soup.select_one(".sm-product .title")
        price = soup.select_one(".sm-product .price")
        if block and price:
            return {
                "title": f"{block.text.strip()} - {price.text.strip()}",
                "link": clean_url
            }
    except Exception as e:
        print("❌ ScraperAPI fallback failed:", e)

    print("🚫 All sources failed.")
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
