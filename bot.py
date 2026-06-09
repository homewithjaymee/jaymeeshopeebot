import os
import re
import hashlib
import time
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8698397652:AAEJqZhsV2fcK4V6UyKIzbhqW-TteguMg_I")
SHOPEE_APP_ID  = os.environ.get("SHOPEE_APP_ID", "14364560001")
SHOPEE_SECRET  = os.environ.get("SHOPEE_SECRET", "FF65DB2VWMFD4NTTLQU43QMYRJWID5AI")
SHOPEE_API_URL = "https://open-api.affiliate.shopee.sg/graphql"

# ── SHOPEE AFFILIATE API ──────────────────────────────────────────────────────
def generate_shopee_affiliate_link(original_url: str):
    query = (
        'mutation{\n'
        '  generateShortLink(input:{'
        'originUrl:"' + original_url + '",'
        'subIds:["hwj"]'
        '}){\n'
        '    shortLink\n'
        '  }\n'
        '}'
    )
    payload_str = json.dumps({"query": query}, separators=(',', ':'))
    timestamp = int(time.time())
    factor = SHOPEE_APP_ID + str(timestamp) + payload_str + SHOPEE_SECRET
    signature = hashlib.sha256(factor.encode("utf-8")).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }
    try:
        response = requests.post(SHOPEE_API_URL, data=payload_str, headers=headers, timeout=10)
        data = response.json()
        return data.get("data", {}).get("generateShortLink", {}).get("shortLink")
    except Exception as e:
        print(f"Shopee API error: {e}")
        return None


def extract_shopee_urls(text: str):
    pattern = r'https?://(?:www\.)?(?:shopee\.sg|s\.shopee\.sg|shp\.ee)/[^\s]+'
    return re.findall(pattern, text)


# ── BOT HANDLERS ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐱 ling activated! *sniffs your links suspiciously*\n\n"
        "send me up to 5 shopee links at a time and i'll convert them for you.\n\n"
        "exclusive vouchers apply when jaymee has an active campaign — follow @homewithjaymee on ig for announcements! 🎉"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    urls = extract_shopee_urls(text)

    if not urls:
        await update.message.reply_text(
            "ling tried but couldn't find any shopee links in that message 😿 "
            "make sure it's a valid shopee.sg link and try again!"
        )
        return

    # Cap at 5 links
    urls = urls[:5]

    await update.message.reply_text("ling is inspecting your link(s)... 🔍🐱")

    results = []
    failed = 0

    for url in urls:
        affiliate_link = generate_shopee_affiliate_link(url)
        if affiliate_link:
            results.append(affiliate_link)
        else:
            failed += 1

    if results:
        reply = "inspection complete! here are your converted links 🐱🛒\n\n"
        reply += "\n\n".join(results)
        if failed > 0:
            reply += f"\n\n😿 {failed} link(s) couldn't be converted — try sending them again!"
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(
            "ling tried but couldn't convert those links 😿 "
            "make sure they're valid shopee.sg links and try again!"
        )


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ling is on duty 🐱")
    app.run_polling()
