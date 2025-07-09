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

# ✅ Fallback Deals Scraper if RSS fails

# ✅ Full Getter with fallback logic

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







    # 🔹 Gemini Primary AI
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip() + f"\n\n🛒 Link: {deal_url}"
    
    except Exception as gemini_exc:
        print("⚠️ Gemini failed:", gemini_exc)
        print("Trying OpenRouter backup...")

        # 🔹 OpenRouter Fallback
        try:
            import openai
            openai.api_key = os.environ.get("OPENROUTER_API_KEY")
            openai.api_base = "https://openrouter.ai/api/v1"

            response = openai.ChatCompletion.create(
                model="claude-3-haiku",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip() + f"\n\n🛒 Link: {deal_url}"

        except Exception as openrouter_exc:
            print("❌ Both AI services failed.")
            print("Using fallback caption...")
            return f"🔥 Deal: {title}\n💸 Prices: {prices}\n🛒 Link: {deal_url}"



def generate_caption(title, prices, deal_url):
    import os
    import traceback

    prompt = f"Write a short, catchy caption for an exclusive deal:\n\nTitle: {title}\nPrices:\n{prices}\nLink: {deal_url}"

    # ✅ Try Gemini first
    try:
        import google.generativeai as genai
        from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted

        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("❌ GEMINI_API_KEY not set.")

        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip() + f"\n\n🛒 {deal_url}"

    # Fallback if Gemini fails
    except (GoogleAPICallError, ResourceExhausted, Exception) as gemini_error:
        print("⚠️ Gemini failed:", gemini_error)
        print("➡️ Switching to OpenRouter fallback...")

        try:
            import openai
            openai.api_key = os.environ.get("OPENROUTER_API_KEY")
            openai.api_base = "https://openrouter.ai/api/v1"

            response = openai.ChatCompletion.create(
                model="claude-3-haiku",
                messages=[{"role": "user", "content": prompt}]
            )
            return response['choices'][0]['message']['content'].strip() + f"\n\n🛒 {deal_url}"

        except Exception as openrouter_error:
            print("❌ Fallback OpenRouter also failed:", openrouter_error)
            return f"🔥 Deal: {title}\n💸 Prices: {prices}\n🛒 Link: {deal_url}"



def fetch_amazon_deal(keyword="smartphone"):
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.amazon.in/s?k={keyword.replace(' ', '+')}"
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("❌ Amazon blocked the request (status not 200)")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        block = soup.select_one(".s-result-item h2 a")
        if not block:
            print("❌ No product found in Amazon search DOM")
            return None

        title = block.text.strip()
        href = block.get("href")
        link = "https://www.amazon.in" + href
        return {
            "title": title,
            "link": link
        }
    except Exception as e:
        print("⚠️ Error in fetch_amazon_deal():", e)
        return None

def fetch_smartprix_top():
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://www.smartprix.com/laptops"  # Could alternate to smartphones
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        card = soup.select_one(".sm-product")
        name = card.select_one(".title").text.strip()
        price = card.select_one(".price").text.strip()
        return name + " - " + price
    except Exception as e:
        print("⚠️ Smartprix failed:", e)
        return "⚠️ Price Unavailable"

def fetch_deal(keyword="smartphone"):
    deal = fetch_amazon_deal(keyword)
    if deal:
        return deal
    print("🔁 Amazon failed. Trying Smartprix...")
    alt_title = fetch_smartprix_top()
    return {
        "title": alt_title,
        "link": "https://www.smartprix.com/laptops"
    }



def fetch_amazon_deal(keyword="smartphone"):
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.amazon.in/s?k={keyword.replace(' ', '+')}"
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("❌ Amazon blocked the request")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        item = soup.select_one(".s-result-item h2 a")
        if not item:
            print("❌ No product found on Amazon")
            return None

        title = item.text.strip()
        href = item.get('href')
        link = "https://www.amazon.in" + href
        return {"title": title, "link": link}
    except Exception as e:
        print("⚠️ Amazon fetch error:", e)
        return None

def fetch_smartprix_top():
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://www.smartprix.com/laptops"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        prod = soup.select_one(".sm-product .title")
        price = soup.select_one(".sm-product .price")
        if prod and price:
            return prod.get_text(strip=True) + " - " + price.get_text(strip=True)
    except Exception as e:
        print("⚠️ Smartprix fetch error:", e)
    return "⚠️ Price not available"

def fetch_deal(keyword="smartphone"):
    deal = fetch_amazon_deal(keyword)
    if deal:
        return deal
    print("🔁 Amazon failed – trying Smartprix...")
    alt = fetch_smartprix_top()
    return {"title": alt, "link": "https://www.smartprix.com/laptops"}


def main():
    deal = fetch_deal()
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
