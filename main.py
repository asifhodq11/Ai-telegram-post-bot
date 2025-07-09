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
    if not deal:
        print("⚠️ DesiDime RSS failed. Trying Reddit backup...")
        deal = fetch_reddit_backup()
    if not deal:
        send_personal_alert("❌ No deals from DesiDime or Reddit RSS 😓")
        return
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




def fetch_reddit_backup():
    import feedparser
    url = "https://www.reddit.com/r/deals/.rss"
    rss = feedparser.parse(url)
    if not rss.entries:
        print("❌ Reddit RSS is empty.")
        return None
    entry = rss.entries[0]
    return {
        "title": entry.title,
        "link": entry.link
    }



    # 🔹 Gemini Primary AI
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-pro")
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
        model = genai.GenerativeModel("gemini-pro")
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
