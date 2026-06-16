import requests
import asyncio
import time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========= CONFIG =========
TELEGRAM_TOKEN = "8915801157:AAGiVcDBUQCGRpLji-tZS__LfY0AYM_7Qx8"
DELAY = 5  # Seconds between checks
MAX_USERNAMES = 50

# ========= INSTAGRAM CHECKER =========
def check_instagram(username):
    """Return True if available, False if taken, None if error"""
    url = f"https://www.instagram.com/{username}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return False
        elif response.status_code == 404:
            return True
        else:
            return None
    except:
        return None

# ========= BOT COMMANDS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Instagram Username Checker\n\n"
        "Send me a list of usernames (one per line or comma-separated)\n"
        f"Max {MAX_USERNAMES} usernames with {DELAY}s delay between checks.\n\n"
        "Example:\n"
        "john_doe\n"
        "cool_name_2026\n"
        "test_account"
    )

async def handle_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # Parse usernames (split by newline or comma)
    usernames = []
    for line in text.split('\n'):
        for item in line.split(','):
            clean = item.strip()
            if clean and not clean.startswith('#'):  # Skip comments
                usernames.append(clean)
    
    # Remove duplicates
    usernames = list(dict.fromkeys(usernames))
    
    # Validate count
    if len(usernames) > MAX_USERNAMES:
        await update.message.reply_text(
            f"⚠️ Too many! Max {MAX_USERNAMES} usernames. You sent {len(usernames)}."
        )
        return
    
    if not usernames:
        await update.message.reply_text("❌ No valid usernames found.")
        return
    
    # Send initial status
    msg = await update.message.reply_text(
        f"🔍 Checking {len(usernames)} usernames...\n"
        f"⏱️ Estimated time: {len(usernames) * DELAY} seconds"
    )
    
    # Check each username
    results = []
    available = []
    taken = []
    errors = []
    
    for i, username in enumerate(usernames, 1):
        status = check_instagram(username)
        
        if status is True:
            results.append(f"✅ {username} - AVAILABLE")
            available.append(username)
        elif status is False:
            results.append(f"❌ {username} - TAKEN")
            taken.append(username)
        else:
            results.append(f"⚠️ {username} - ERROR (rate limited or network)")
            errors.append(username)
        
        # Update progress every 5 checks
        if i % 5 == 0 or i == len(usernames):
            await msg.edit_text(
                f"🔍 Checking... {i}/{len(usernames)}\n"
                f"✅ Found {len(available)} available so far"
            )
        
        # Delay between checks (except last)
        if i < len(usernames):
            await asyncio.sleep(DELAY)
    
    # Format final response
    summary = f"📊 **Results** ({len(usernames)} checked)\n"
    summary += f"✅ Available: {len(available)}\n"
    summary += f"❌ Taken: {len(taken)}\n"
    summary += f"⚠️ Errors: {len(errors)}\n\n"
    
    # Show available names first
    if available:
        summary += "**🎯 AVAILABLE:**\n" + "\n".join(f"• {u}" for u in available[:20])
        if len(available) > 20:
            summary += f"\n... and {len(available)-20} more"
    
    if taken:
        summary += "\n\n**❌ TAKEN:**\n" + "\n".join(f"• {u}" for u in taken[:10])
        if len(taken) > 10:
            summary += f"\n... and {len(taken)-10} more"
    
    await msg.edit_text(summary, parse_mode='Markdown')

# ========= MAIN =========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_usernames))
    
    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()