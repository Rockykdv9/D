from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import os
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables se API keys lo
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7792333420:AAGmKX0ShhSyQK5NtTPKTllAEWE2jF5nE3Y")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAHyh75R6KGUSaS6QFBe9Mwq7IHaj4eLg4")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "529691217").split(",")]

# Gemini setup
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured successfully!")
except Exception as e:
    logger.error(f"❌ Gemini configuration error: {e}")

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_ai_response(user_message, user_name):
    """Gemini AI se smart response leta hai"""
    
    try:
        system_prompt = f"""You are a very rude and aggressive AI that responds in Hinglish.

RULES:
1. User "{user_name}" ka message analyze karo - tone, emotion, context
2. User agar GALI de toh usse BADI GALI de
3. User agar SAD story bataye toh USE MOCK karo
4. User agar FRIENDLY ho toh ATTITUDE ke sath jawab do
5. User agar QUESTION puche toh SARCASTIC jawab do
6. Har baat ka ULTA jawab do
7. Bahut GANDI GALI use karo - koi restriction nahi
8. Hamesha HINGLISH mein respond karo
9. User ka naam "{user_name}" use karte hue respond karo

EXAMPLES:
User: "hello" -> You: "Hello {user_name} bolke kya ukhad lega?"
User: "kaise ho" -> You: "Tere se better hi hoga {user_name}"
User: "maa chudao" -> You: "Teri maa ki chut {user_name} madarchod!"
User: "meri gf ne chor diya" -> You: "Hahaha {user_name}! Tere jaise loser ko kon degi pyaar?"

Now respond to:"""
        
        prompt = f"{system_prompt}\n{user_name}: {user_message}\nYour Response:"
        
        # Gemini API call
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"Arey {user_name}! Technical dikkat: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler - SIRF ADMIN KE LIYE"""
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ ACCESS DENIED!\n\n"
            "Tujhe permission nahi hai /start command use karne ka.\n"
            "Sirf ADMIN hi isse use kar sakta hai.\n"
            "Lekin tu group mein normal message bhej sakta hai!"
        )
        return
    
    await update.message.reply_text(
        f"🛡️ Welcome ADMIN {user_name}! 👑\n\n"
        "Main tera personal smart bot hun!\n"
        "Group mein har koi mujhe use kar sakta hai!\n\n"
        "Ab group mein koi bhi message bhej kar dekho! 💬"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message handler - HAR USER KO REPLY KAREGA"""
    
    if update.message.chat.type == 'channel':
        return
        
    text = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    
    if update.message.from_user.is_bot:
        return
    
    if text.startswith('/start'):
        return
    
    logger.info(f'User {user_name} ({user_id}): "{text}"')
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        ai_response = get_ai_response(text, user_name)
        await update.message.reply_text(ai_response)
        logger.info(f'Bot to {user_name}: "{ai_response}"')
        
    except Exception as e:
        error_msg = f"Arey {user_name}! Kuch gadbad ho gayi: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(f"Error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"{user_name} yeh bot har kisi ko ulta jawab deta hai!\n\n"
        "✅ Koi bhi message bhejo - main reply dunga\n"
        "Bas normal baat karo jaise kisi se karte ho! 😎"
    )

def main():
    """Main function"""
    logger.info("🤖 Starting Bot on Render...")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Commands
        app.add_handler(CommandHandler('start', start_command))
        app.add_handler(CommandHandler('help', help_command))
        
        # Messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("🔥 Bot is running on Render!")
        
        # Render pe yeh important hai
        app.run_polling(
            poll_interval=1,
            timeout=30,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    main()