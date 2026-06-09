import os
import re
import hmac
import hashlib
import time
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8698397652:AAEJqZhsV2fcK4V6UyKIzbhqW-TteguMg_I")
SHOPEE_APP_ID   = os.environ.get("SHOPEE_APP_ID", "14364560001")
SHOPEE_SECRET   = os.environ.get("SHOPEE_SECRET", "FF65DB2VWMFD4NTTLQU43QMYRJWID5AI")

SHOPEE_API_URL = "https://open-api.affiliate.shopee.sg/graphql"

# ── SHOPEE AFFILIATE API ──────────────────────────────────────────────────────
def generate_shopee_affiliate_link(original_url: str):
    query = """mutation generateShortLink($input: GenerateShortLinkInput!) {
  generateShortLink(input: $input) {
    shortLink
    originLink
  }
}"""
    variables = {
        "input": {
            "originUrl": original_url,
            "subIds": ["hwj"]
        }
    }

    # Build payload string (must be compact JSON, no extra spaces)
    payload_dict = {"query": query, "variables": variables}
    payload_str = json.dumps(payload_dict, separators=(',', ':'))

    timestamp = int(time.time())

    # Signature = SHA256(AppId + Timestamp + Payload + Secret)
    factor = SHOPEE_APP_ID + str(timestamp) + payload_str + SHOPEE_SECRET
    signature = hashlib.sha256(factor.encode("utf-8")).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }

    try:
        response = requests.post(SHOPEE_API_URL, data=payload_str, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        data = response.json()
        short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
        return short_link
    except Exception as e:
        print(f"Shopee API error: {e}")
        return None


def extract_shopee_url(text: str):
    pattern = r'https?://(?:www\.)?(?:shopee\.sg|s\.shopee\.sg|shp\.ee)/[^\s]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


# ── BOT HANDLERS ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "hi! 👋 send me any shopee link and i'll convert it to your affiliate link instantly. 🛒"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    url = extract_shopee_url(text)

    if not url:
        await update.message.reply_text("hmm, i don't see a shopee link in that message. paste the full shopee URL and i'll convert it! 🛒")
        return

    await update.message.reply_text("converting... ⏳")

    affiliate_link = generate_shopee_affiliate_link(url)

    if affiliate_link:
        await update.message.reply_text(f"✅ here's your affiliate link:\n\n{affiliate_link}")
    else:
        await update.message.reply_text("❌ something went wrong with the shopee API. try again in a moment!")


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("bot is running...")
    app.run_polling()
