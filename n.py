import telebot
import os
import time
import random
import threading

# Bot Token
token = "7953654368:AAEWiU_0jPmcgPdFYU3JIVGMAa4_9sekr_M"
bot = telebot.TeleBot(token)

APPROVED_USERS_FILE = "approved_users.txt"
GALI_FILE = "galis.txt"  # Single file for all galis
approved_users = []
admins = [529691217]
owner_id = 529691217
stop_gali = False
delete_messages = False
target_user_id = None

CHANNEL_LINK = "https://t.me/DEMON_ROCKY"
GROUP_LINK = "https://t.me/DEMON_ROCKY"
OWNER_LINK = "https://t.me/DEMON_ROCKY"

def load_approved_users():
    users = []
    if os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, "r") as f:
            for line in f:
                data = line.strip().split(',')
                if len(data) == 2:
                    users.append({'id': int(data[0]), 'username': data[1]})
    return users

def save_approved_users():
    with open(APPROVED_USERS_FILE, "w") as f:
        for user in approved_users:
            f.write(f"{user['id']},{user['username']}\n")

def load_galis_from_file():
    """Load galis from the gali text file"""
    galis = []
    if os.path.exists(GALI_FILE):
        try:
            with open(GALI_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        galis.append(line)
        except Exception as e:
            print(f"Error loading galis: {e}")
    return galis

approved_users = load_approved_users()

@bot.message_handler(commands=["start"])
def welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    name = message.from_user.first_name

    if any(user['id'] == user_id for user in approved_users) or user_id in admins or user_id == owner_id:
        # Create inline keyboard for group add
        markup = telebot.types.InlineKeyboardMarkup()
        add_to_group_btn = telebot.types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
        markup.add(add_to_group_btn)
        
        bot.reply_to(message,
            "✨ 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝙏𝙝𝙚 𝙐𝙡𝙩𝙞𝙢𝙖𝙩𝙚 𝙂𝙖𝙡𝙞 𝘽𝙤𝙩 ✨\n\n"
            "👑 Owner Commands:\n"
            "- /admin <user_id>\n"
            "- /remove_admin <user_id>\n"
            "- /list_admins\n\n"
            "🛡️ Admin Commands:\n"
            "- /approve <user_id>\n"
            "- /remove <user_id>\n"
            "- /remove_all\n"
            "- /list_approved\n"
            "- /upload_gali_file (Upload TXT file)\n"
            "- /delete_on <user_id/username> (Auto delete user messages)\n"
            "- /delete_off (Stop auto delete)\n\n"
            "🔥 User Commands:\n"
            "- /fuck <username>\n"
            "- /stop\n"
            "- /ping\n\n"
            "💬 Add me to your group for fun!",
            reply_markup=markup
        )
    else:
        # Create inline keyboard for new users
        markup = telebot.types.InlineKeyboardMarkup()
        add_to_group_btn = telebot.types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
        join_channel_btn = telebot.types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)
        join_group_btn = telebot.types.InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)
        dm_owner_btn = telebot.types.InlineKeyboardButton("👑 DM Owner", url=OWNER_LINK)
        
        markup.add(add_to_group_btn)
        markup.add(join_channel_btn, join_group_btn)
        markup.add(dm_owner_btn)
        
        bot.reply_to(message,
            f"⚠️ To use this bot, follow these steps:\n\n"
            f"1️⃣ Join our Channel & Group\n"
            f"2️⃣ After joining, send a DM to the owner\n"
            f"3️⃣ Once approved, you'll get access to all features\n\n"
            f"⏳ Add me to your group for instant fun!",
            reply_markup=markup,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if user_id != owner_id:
            try:
                bot.send_message(owner_id, f"👤 New user started the bot:\n• Name: {name}\n• Username: @{username}\n• ID: `{user_id}`", parse_mode="Markdown")
            except Exception as e:
                print(f"Error notifying owner: {e}")

@bot.message_handler(commands=["addgroup"])
def add_to_group(message):
    """Command to get group add link"""
    bot_username = bot.get_me().username
    group_add_link = f"https://t.me/{bot_username}?startgroup=true"
    
    markup = telebot.types.InlineKeyboardMarkup()
    add_btn = telebot.types.InlineKeyboardButton("➕ Add to Group", url=group_add_link)
    markup.add(add_btn)
    
    bot.reply_to(message,
        "💬 Click the button below to add me to your group:\n\n"
        "⚠️ Note: Make sure you have admin rights in the group where you want to add me.",
        reply_markup=markup
    )

@bot.message_handler(commands=["delete_on"])
def delete_messages_on(message):
    """Start auto deleting messages from specific user"""
    global delete_messages, target_user_id
    
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /delete_on <user_id_or_username>")
        return
    
    target = parts[1]
    
    try:
        # Try to get user info
        if target.startswith('@'):
            # It's a username
            user_info = bot.get_chat(target)
            target_user_id = user_info.id
        else:
            # It's a user ID
            target_user_id = int(target)
            user_info = bot.get_chat(target_user_id)
        
        delete_messages = True
        username = user_info.username or user_info.first_name
        bot.reply_to(message, f"🗑️ Auto-delete activated for user: {username} (ID: {target_user_id})\n\nEvery message from this user will be instantly deleted!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: User not found or invalid user ID/username\nError: {e}")

@bot.message_handler(commands=["delete_off"])
def delete_messages_off(message):
    """Stop auto deleting messages"""
    global delete_messages, target_user_id
    
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    delete_messages = False
    target_user_id = None
    bot.reply_to(message, "✅ Auto-delete feature turned off")

@bot.message_handler(func=lambda message: delete_messages and message.from_user.id == target_user_id)
def handle_auto_delete(message):
    """Auto delete messages from target user"""
    try:
        bot.delete_message(message.chat.id, message.message_id)
        print(f"Deleted message from user {message.from_user.id}")
    except Exception as e:
        print(f"Error deleting message: {e}")

@bot.message_handler(commands=["ping"])
def ping(message):
    if message.from_user.id not in [u['id'] for u in approved_users] and message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    start_time = time.time()
    sent = bot.reply_to(message, "Pinging...")
    end_time = time.time()
    latency = round((end_time - start_time) * 1000)
    bot.edit_message_text(f"🏓 Pong! {latency}ms", message.chat.id, sent.message_id)

@bot.message_handler(commands=["admin"])
def make_admin(message):
    if message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /admin <user_id>")
        return
    try:
        uid = int(parts[1])
        if uid not in admins:
            admins.append(uid)
            bot.reply_to(message, f"✅ User {uid} promoted to admin.")
        else:
            bot.reply_to(message, f"ℹ️ User {uid} is already an admin.")
    except:
        bot.reply_to(message, "❌ Invalid user ID.")

@bot.message_handler(commands=["remove_admin"])
def remove_admin(message):
    if message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /remove_admin <user_id>")
        return
    try:
        uid = int(parts[1])
        if uid == owner_id:
            bot.reply_to(message, "❌ You can't remove yourself (owner).")
            return
        if uid in admins:
            admins.remove(uid)
            bot.reply_to(message, f"✅ Admin {uid} removed.")
        else:
            bot.reply_to(message, "⚠️ User is not an admin.")
    except:
        bot.reply_to(message, "❌ Invalid user ID.")

@bot.message_handler(commands=["list_admins"])
def list_admins(message):
    if message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    if not admins:
        bot.reply_to(message, "📭 No admins found.")
        return
    reply = "👮 Admins:\n"
    for uid in admins:
        try:
            user = bot.get_chat(uid)
            username = f"@{user.username}" if user.username else "NoUsername"
            reply += f"- {uid} ({username})\n"
        except:
            reply += f"- {uid} (Unknown)\n"
    bot.reply_to(message, reply)

@bot.message_handler(commands=["approve"])
def approve_user(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /approve <user_id>")
        return
    try:
        uid = int(parts[1])
        user_obj = bot.get_chat(uid)
        username = user_obj.username or "NoUsername"
        for user in approved_users:
            if user['id'] == uid:
                bot.reply_to(message, "✅ User already approved.")
                return
        approved_users.append({'id': uid, 'username': username})
        save_approved_users()
        bot.reply_to(message, f"✅ Approved user {uid} (@{username})")
    except:
        bot.reply_to(message, "❌ Invalid user ID or user not found.")

@bot.message_handler(commands=["remove"])
def remove_user(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /remove <user_id>")
        return
    try:
        uid = int(parts[1])
        for user in approved_users:
            if user['id'] == uid:
                approved_users.remove(user)
                save_approved_users()
                bot.reply_to(message, f"❌ Removed user {uid}")
                return
        bot.reply_to(message, "⚠️ User not found.")
    except:
        bot.reply_to(message, "❌ Invalid user ID.")

@bot.message_handler(commands=["remove_all"])
def remove_all_users(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    approved_users.clear()
    save_approved_users()
    bot.reply_to(message, "🧹 All approved users removed.")

@bot.message_handler(commands=["list_approved"])
def list_approved(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    if not approved_users:
        bot.reply_to(message, "📭 No users are currently approved.")
        return
    reply = "✅ Approved Users:\n"
    for user in approved_users:
        uname = f"@{user['username']}" if user['username'] != "NoUsername" else "NoUsername"
        reply += f"- {user['id']} ({uname})\n"
    bot.reply_to(message, reply)

@bot.message_handler(commands=["upload_gali_file"])
def handle_gali_file_upload(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    bot.reply_to(message, "📁 Please upload your TXT file containing galis. Each line should contain one gali.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    if message.document.mime_type == 'text/plain' or message.document.file_name.endswith('.txt'):
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open(GALI_FILE, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            # Count lines in the file
            galis = load_galis_from_file()
            bot.reply_to(message, f"✅ Gali file uploaded successfully! Loaded {len(galis)} galis.")
        except Exception as e:
            bot.reply_to(message, f"❌ Error uploading file: {e}")
    else:
        bot.reply_to(message, "❌ Please upload a TXT file.")

@bot.message_handler(commands=["fuck"])
def send_all_galis(message):
    global stop_gali
    
    # Check if user is authorized
    if message.from_user.id not in [u['id'] for u in approved_users] and message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /fuck <username>")
        return
    
    username = parts[1]
    
    # Load galis from file
    galis = load_galis_from_file()
    if not galis:
        bot.reply_to(message, "❌ No galis found in the file. Please upload a TXT file first using /upload_gali_file")
        return
    
    # Delete the command message instantly
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    # Send starting message and delete it after 2 seconds
    starting_msg = bot.send_message(message.chat.id, f"🔥 Starting gali spam for {username}... (Total: {len(galis)} galis)")
    
    def delete_starting_msg():
        time.sleep(2)
        try:
            bot.delete_message(message.chat.id, starting_msg.message_id)
        except:
            pass
    
    threading.Thread(target=delete_starting_msg, daemon=True).start()

    def spam():
        count = 0
        while not stop_gali and count < len(galis):
            gali = galis[count]
            if stop_gali:
                return
            try:
                bot.send_message(message.chat.id, f"{username} {gali}")
                count += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"Error sending message: {e}")
                continue

    stop_gali = False
    t = threading.Thread(target=spam)
    t.daemon = True
    t.start()

@bot.message_handler(commands=["stop"])
def stop_galis(message):
    global stop_gali
    
    # Check if user is authorized
    if message.from_user.id not in [u['id'] for u in approved_users] and message.from_user.id not in admins and message.from_user.id != owner_id:
        return  # No reply for unauthorized users
    
    stop_gali = True
    
    # Delete the stop command message
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    stop_msg = bot.send_message(message.chat.id, "🛑 Stopping all galis...")
    
    # Delete stop message after 2 seconds
    def delete_stop_msg():
        time.sleep(2)
        try:
            bot.delete_message(message.chat.id, stop_msg.message_id)
        except:
            pass
    
    threading.Thread(target=delete_stop_msg, daemon=True).start()

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(msg):
    # Handle unauthorized users - no reply at all
    user_id = msg.from_user.id
    if user_id not in [u['id'] for u in approved_users] and user_id not in admins and user_id != owner_id:
        # Only notify owner about messages from unauthorized users in private chats
        if msg.chat.type == 'private':
            try:
                bot.send_message(owner_id, f"📩 Message from {msg.from_user.first_name} (@{msg.from_user.username}):\n{msg.text}")
            except:
                pass
        return  # No reply to unauthorized users

print("Bot is running...")
bot.infinity_polling()