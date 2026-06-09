import os
import re
import hmac
import hashlib
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8698397652:AAEJqZhsV2fcK4V6UyKIzbhqW-TteguMg_I")
SHOPEE_APP_ID   = os.environ.get("SHOPEE_APP_ID", "14364560001")
SHOPEE_SECRET   = os.environ.get("SHOPEE_SECRET", "FF65DB2VWMFD4NTTLQU43QMYRJWID5AI")

# ── SHOPEE AFFILIATE API ──────────────────────────────────────────────────────
def generate_shopee_affiliate_link(original_url: str) -> str | None:
    """Convert any Shopee product URL to Jaymee's affiliate link."""
    endpoint = "https://open-api.affiliate.shopee.sg/graphql"
    timestamp = int(time.time())
    payload = f"{SHOPEE_APP_ID}{timestamp}"
    signature = hmac.new(
        SHOPEE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }

    body = {
        "query": """
        mutation generateShortLink($input: GenerateShortLinkInput!) {
            generateShortLink(input: $input) {
                shortLink
                originLink
            }
        }
        """,
        "variables": {
            "input": {
                "originUrl": original_url,
                "subIds": ["hwj"]
            }
        }
    }

    try:
        response = requests.post(endpoint, json=body, headers=headers, timeout=10)
        data = response.json()
        short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
        return short_link
    except Exception as e:
        print(f"Shopee API error: {e}")
        return None


def extract_shopee_url(text: str) -> str | None:
    """Extract a Shopee URL from a message."""
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
