import asyncio
import logging
import random
import time
import os
import json
import re
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler
from telegram.ext import filters

# ================================
# 📋 MULTI-BOT CONFIGURATION
# ================================

# ===== MULTI BOT TOKENS =====
TOKENS = [
    "8298052340:AAEFMBq5hZr_bO_zxTAXBMvFqu7JB3l3fF4",  # Bot 1 - Main
    "8590199950:AAESjhxLYbFTI3Fdec7aGGNy16zrP9WtMgk",  # Bot 2
    "8578531754:AAHaprzNJalyDrOsaoGDYd3l8tfC6xOcT34"   # Bot 3
]
# ============================

# Level-wise text files
BASIC_FILE = "basic_lines.txt"
NORMAL_FILE = "normal_lines.txt"
AGGRESSIVE_FILE = "aggressive_lines.txt"
EXTREME_FILE = "extreme_lines.txt"
ULTRA_FILE = "ultra.txt"
NON_ADMIN_FILE = "non_admin.txt"

# Users data file
USERS_FILE = "users_data.json"

# Admin ka user ID
ADMIN_ID = 529691217

# Spam settings file
SPAM_SETTINGS_FILE = "spam_settings.json"

# Protected users file
PROTECTED_USERS_FILE = "protected_users.json"

# User start counts file
USER_START_COUNTS_FILE = "user_start_counts.json"

# Selected targets file
SELECTED_TARGETS_FILE = "selected_targets.json"

# Game targets file
GAME_TARGETS_FILE = "game_targets.json"
GROUPS_FILE = "selected_groups.json"

# Multi-bot sync file
MULTI_BOT_SYNC_FILE = "multi_bot_sync.json"

# Bot tokens file
BOT_TOKENS_FILE = "bot_tokens.json"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================================
# 🔄 CONVERSATION STATES
# ================================
DANGER_SETTING = 1
ADDING_TARGET = 2
SETTING_COUNT = 3
SETTING_TYPE = 4
SETTING_CUSTOM_MESSAGE = 5
GROUP_SELECTION = 6
PROTECTED_MANAGEMENT = 7
TARGET_MANAGEMENT = 8
EDIT_TARGET_SELECTION = 9
TARGET_SPAM_CONTROL = 10
PROTECTED_SELECTION = 11
GAME_LEVELS_MANAGEMENT = 12
ADDING_GAME_TARGET = 13
GAME_TARGET_SELECTION = 14
EDIT_GAME_TARGET_SELECTION = 15
GAME_TARGET_MANAGEMENT = 16
MULTI_BOT_CONTROL = 17
ADD_BOT_TOKEN = 18
REMOVE_BOT_SELECTION = 19
BOT_MANAGEMENT = 20
SPEED_CONTROL = 21

# ================================
# 🎯 USER LEVELS CONFIGURATION
# ================================
USER_LEVELS = {
    "1": "🟢 Basic",
    "2": "🔵 Normal",
    "3": "🟡 Aggressive",
    "4": "🟠 Extreme",
    "5": "🔴 Ultra",
    "6": "⚫ Non-Admin"
}

# Level file mapping
LEVEL_FILES = {
    "1": BASIC_FILE,
    "2": NORMAL_FILE,
    "3": AGGRESSIVE_FILE,
    "4": EXTREME_FILE,
    "5": ULTRA_FILE,
    "6": NON_ADMIN_FILE
}

# Protected users (jinhe bot gali nahi dega)
PROTECTED_USERS = [ADMIN_ID]

# ================================
# 🔄 MULTI-BOT SYSTEM VARIABLES
# ================================
TRIGGER_MODE = "off"
TRIGGER_LEVEL = "2"
TRIGGER_ACTIVE = False
SPAM_MODE = "off"
SPAM_MESSAGE = ""
SPAM_TARGETS = []
SELECTED_GROUPS = []
SELECTED_TARGETS = []
GAME_TARGETS = []
GAME_MODE_ACTIVE = False
BOT_RESPONSIVE = True

# Multi-bot applications
BOT_APPLICATIONS = []
CURRENT_BOT_INDEX = 0

# ================================
# ⚡ 24/7 SPAM SYSTEM VARIABLES
# ================================
CONTINUOUS_SPAM_ACTIVE = False
CONTINUOUS_SPAM_TASK = None
MESSAGES_PER_MINUTE = 45  # 3 bots × 15 messages each = 45 msg/min (SAFE)
MESSAGE_GAP = 1.33  # 60 seconds / 45 messages = 1.33 seconds per message

# ================================
# 🛡️ AUTO-RECOVERY VARIABLES
# ================================
CONSECUTIVE_ERRORS = 0
TOTAL_RECOVERIES = 0
LAST_RECOVERY_TIME = 0

# ================================
# ⚡ PERFORMANCE OPTIMIZATION VARIABLES
# ================================
MESSAGE_SEMAPHORE = asyncio.Semaphore(50)
LAST_MESSAGE_TIME = 0
MESSAGES_SENT_THIS_MINUTE = 0
MINUTE_START_TIME = time.time()
MAX_MESSAGES_PER_MINUTE = 50

# ================================
# 🔄 TASK MANAGEMENT VARIABLES
# ================================
ACTIVE_SPAM_TASKS = set()
SPAM_TASK_RUNNING = False
CURRENT_SPAM_TASK = None

# ================================
# 🔄 MESSAGE ROTATION SYSTEM
# ================================
MESSAGE_ROTATION = {}

# ================================
# 🚀 SPEED OPTIMIZATION VARIABLES
# ================================
MESSAGE_CACHE = {}
CACHED_LINES = {}

# ================================
# 🔄 MULTI-BOT SYNC VARIABLES
# ================================
LAST_SYNC_TIME = 0
SYNC_INTERVAL = 2
MULTI_BOT_SPAM_ACTIVE = False
MULTI_BOT_TASKS = []

# ================================
# 🛠️ UNIFIED UTILITY FUNCTIONS
# ================================

def load_data(filename, default_data=None):
    """📁 Unified data loading function"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
    return default_data if default_data is not None else []

def save_data(filename, data):
    """💾 Unified data saving function"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ {filename} saved: {len(data)} items")
        return True
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

async def validate_admin_access(update: Update):
    """🔐 Unified admin validation"""
    user_id = update.effective_user.id
    if not is_private_chat(update) or not is_admin(user_id):
        await update.message.reply_text(
            "❌ Teri aukat nahi hai is bot ko use karne ki! Nikal yaha se!",
            reply_markup=ReplyKeyboardRemove()
        )
        return False
    return True

def is_admin(user_id):
    """👑 Check if user is admin"""
    return user_id == ADMIN_ID

def is_protected(user_id):
    """🛡️ Check if user is protected"""
    return user_id in PROTECTED_USERS

def is_private_chat(update):
    """🔒 Check if chat is private"""
    return update.effective_chat.type == 'private'

def safe_message_text(text):
    """🛡️ Make any text safe for sending"""
    if not text:
        return "Hello"
    try:
        text = str(text)
        text = text.replace('\x00', '').replace('\ufffd', '')
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        return text[:3900] if len(text) > 3900 else text
    except:
        return "Hello everyone!"

# ================================
# 🔄 MULTI-BOT SYNC FUNCTIONS
# ================================

def load_multi_bot_sync():
    """🔄 Load multi-bot sync data"""
    return load_data(MULTI_BOT_SYNC_FILE, {
        "spam_targets": [],
        "selected_targets": [],
        "game_targets": [],
        "protected_users": [ADMIN_ID],
        "spam_mode": "off",
        "game_mode_active": False,
        "trigger_mode": "off",
        "trigger_active": False,
        "last_update": time.time()
    })

def save_multi_bot_sync():
    """💾 Save multi-bot sync data"""
    sync_data = {
        "spam_targets": SPAM_TARGETS,
        "selected_targets": SELECTED_TARGETS,
        "game_targets": GAME_TARGETS,
        "protected_users": PROTECTED_USERS,
        "spam_mode": SPAM_MODE,
        "game_mode_active": GAME_MODE_ACTIVE,
        "trigger_mode": TRIGGER_MODE,
        "trigger_active": TRIGGER_ACTIVE,
        "last_update": time.time()
    }
    return save_data(MULTI_BOT_SYNC_FILE, sync_data)

async def sync_multi_bot_data():
    """🔄 Sync data between all bots"""
    global SPAM_TARGETS, SELECTED_TARGETS, GAME_TARGETS, PROTECTED_USERS
    global SPAM_MODE, GAME_MODE_ACTIVE, TRIGGER_MODE, TRIGGER_ACTIVE, LAST_SYNC_TIME
    
    sync_data = load_multi_bot_sync()
    
    # Only sync if remote data is newer
    if sync_data["last_update"] > LAST_SYNC_TIME:
        SPAM_TARGETS = sync_data["spam_targets"]
        SELECTED_TARGETS = sync_data["selected_targets"]
        GAME_TARGETS = sync_data["game_targets"]
        PROTECTED_USERS = sync_data["protected_users"]
        SPAM_MODE = sync_data["spam_mode"]
        GAME_MODE_ACTIVE = sync_data["game_mode_active"]
        TRIGGER_MODE = sync_data["trigger_mode"]
        TRIGGER_ACTIVE = sync_data["trigger_active"]
        LAST_SYNC_TIME = sync_data["last_update"]
        
        print("🔄 Multi-bot data synced successfully!")
        return True
    return False

async def update_multi_bot_data():
    """📡 Update multi-bot data (when changes occur)"""
    global LAST_SYNC_TIME
    LAST_SYNC_TIME = time.time()
    save_multi_bot_sync()
    print("📡 Multi-bot data updated!")

async def multi_bot_sync_loop():
    """🔄 Continuous sync loop for all bots"""
    while True:
        await sync_multi_bot_data()
        await asyncio.sleep(SYNC_INTERVAL)

# ================================
# 📁 FILE MANAGEMENT FUNCTIONS
# ================================

def load_bot_tokens():
    """📁 Load bot tokens from file"""
    global TOKENS
    TOKENS = load_data(BOT_TOKENS_FILE, TOKENS)
    return TOKENS

def save_bot_tokens():
    """💾 Save bot tokens to file"""
    return save_data(BOT_TOKENS_FILE, TOKENS)

def load_game_targets():
    """📁 Load game targets"""
    global GAME_TARGETS
    GAME_TARGETS = load_data(GAME_TARGETS_FILE, [])
    return GAME_TARGETS

def save_game_targets(targets=None):
    """💾 Save game targets"""
    global GAME_TARGETS
    if targets is not None:
        GAME_TARGETS = targets
    save_data(GAME_TARGETS_FILE, GAME_TARGETS)
    asyncio.create_task(update_multi_bot_data())
    return True

def load_selected_targets():
    """📁 Load selected targets"""
    global SELECTED_TARGETS
    SELECTED_TARGETS = load_data(SELECTED_TARGETS_FILE, [])
    return SELECTED_TARGETS

def save_selected_targets(targets=None):
    """💾 Save selected targets"""
    global SELECTED_TARGETS
    if targets is not None:
        SELECTED_TARGETS = targets
    save_data(SELECTED_TARGETS_FILE, SELECTED_TARGETS)
    asyncio.create_task(update_multi_bot_data())
    return True

def load_selected_groups():
    """📁 Load selected groups"""
    global SELECTED_GROUPS
    SELECTED_GROUPS = load_data(GROUPS_FILE, [])
    return SELECTED_GROUPS

def save_selected_groups(groups=None):
    """💾 Save selected groups"""
    global SELECTED_GROUPS
    if groups is not None:
        SELECTED_GROUPS = groups
    return save_data(GROUPS_FILE, SELECTED_GROUPS)

def load_protected_users():
    """📁 Load protected users"""
    global PROTECTED_USERS
    PROTECTED_USERS = load_data(PROTECTED_USERS_FILE, [ADMIN_ID])
    if ADMIN_ID not in PROTECTED_USERS:
        PROTECTED_USERS.append(ADMIN_ID)
        save_protected_users()
    return PROTECTED_USERS

def save_protected_users():
    """💾 Save protected users"""
    save_data(PROTECTED_USERS_FILE, PROTECTED_USERS)
    asyncio.create_task(update_multi_bot_data())
    return True

def load_user_start_counts():
    """📁 Load user start counts"""
    return load_data(USER_START_COUNTS_FILE, {})

def save_user_start_counts(counts):
    """💾 Save user start counts"""
    return save_data(USER_START_COUNTS_FILE, counts)

def load_spam_settings():
    """📁 Load spam settings"""
    global SPAM_MODE, SPAM_MESSAGE, SPAM_TARGETS

    data = load_data(SPAM_SETTINGS_FILE, {})
    SPAM_MODE = data.get("spam_mode", "off")
    SPAM_MESSAGE = data.get("spam_message", "")
    SPAM_TARGETS = data.get("spam_targets", [])
    print(f"✅ Spam settings loaded: {len(SPAM_TARGETS)} targets")
    return data

def save_spam_settings():
    """💾 Save spam settings"""
    data = {
        "spam_mode": SPAM_MODE,
        "spam_message": SPAM_MESSAGE,
        "spam_targets": SPAM_TARGETS
    }
    save_data(SPAM_SETTINGS_FILE, data)
    asyncio.create_task(update_multi_bot_data())
    return True

def load_users_data():
    """📁 Load users data"""
    data = load_data(USERS_FILE, {})
    if "user_levels" not in data:
        data["user_levels"] = {}
    if "users" not in data:
        data["users"] = {}
    if "blocked_users" not in data:
        data["blocked_users"] = []
    return data

def save_users_data(users_data):
    """💾 Save users data"""
    return save_data(USERS_FILE, users_data)

def get_bot_groups():
    """🌍 Get all groups where bot is member"""
    return load_data("bot_groups.json", [])

def save_group_info(chat_id, chat_title):
    """💾 Save group information"""
    groups = get_bot_groups()
    group_exists = False

    for group in groups:
        if group['id'] == chat_id:
            group_exists = True
            group['title'] = chat_title
            group['last_updated'] = datetime.now().isoformat()
            break

    if not group_exists:
        groups.append({
            'id': chat_id,
            'title': chat_title,
            'added_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        print(f"✅ New group added: {chat_title} (ID: {chat_id})")

    return save_data("bot_groups.json", groups)

def remove_group_info(chat_id):
    """🗑️ Remove group information"""
    groups = get_bot_groups()
    original_count = len(groups)
    groups = [group for group in groups if group['id'] != chat_id]

    if save_data("bot_groups.json", groups) and len(groups) < original_count:
        print(f"✅ Group removed: {chat_id}")
        return True
    return False

def load_level_lines(level):
    """📝 Load stored lines from specific level file - CACHED"""
    if level in CACHED_LINES:
        return CACHED_LINES[level]

    filename = LEVEL_FILES.get(level, NORMAL_FILE)
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                CACHED_LINES[level] = lines
                return lines
    except Exception as e:
        print(f"❌ Error loading level lines: {e}")
    return []

def load_combined_level_lines():
    """📚 Load NORMAL, AGGRESSIVE, EXTREME, ULTRA levels combined - CACHED"""
    if "combined" in CACHED_LINES:
        return CACHED_LINES["combined"]

    combined_lines = []
    levels_to_combine = ["2", "3", "4", "5"]

    for level in levels_to_combine:
        lines = load_level_lines(level)
        combined_lines.extend(lines)

    CACHED_LINES["combined"] = combined_lines
    print(f"🎯 TOTAL COMBINED LINES: {len(combined_lines)}")
    return combined_lines

def get_rotated_message(level, target_id):
    """🔄 Get next message with rotation to avoid repetition"""
    global MESSAGE_ROTATION

    # Cache cleanup
    if len(MESSAGE_ROTATION) > 1000:
        MESSAGE_ROTATION.clear()

    if level == "combined":
        lines = load_combined_level_lines()
    else:
        lines = load_level_lines(level)

    if not lines:
        return "Hello everyone!"

    rotation_key = f"{level}_{target_id}"

    if rotation_key not in MESSAGE_ROTATION:
        MESSAGE_ROTATION[rotation_key] = {
            'messages': lines.copy(),
            'index': 0
        }

    rotation_data = MESSAGE_ROTATION[rotation_key]

    if not rotation_data['messages']:
        rotation_data['messages'] = lines.copy()
        rotation_data['index'] = 0

    if rotation_data['index'] >= len(rotation_data['messages']):
        rotation_data['index'] = 0

    message = rotation_data['messages'][rotation_data['index']]
    rotation_data['index'] += 1

    return message

# ================================
# 👥 USER MANAGEMENT FUNCTIONS
# ================================

def update_user_info(user_id, username, first_name, is_bot=False):
    """👤 Update user message count and info"""
    users_data = load_users_data()
    user_id_str = str(user_id)

    if user_id_str not in users_data["users"]:
        users_data["users"][user_id_str] = {
            "message_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "username": username if username else "N/A",
            "first_name": first_name if first_name else "N/A",
            "is_bot": is_bot
        }
    else:
        users_data["users"][user_id_str]["last_seen"] = datetime.now().isoformat()
        if username and username != "N/A":
            users_data["users"][user_id_str]["username"] = username
        if first_name and first_name != "N/A":
            users_data["users"][user_id_str]["first_name"] = first_name
        if 'is_bot' not in users_data["users"][user_id_str]:
            users_data["users"][user_id_str]["is_bot"] = is_bot

    if user_id_str not in users_data["user_levels"]:
        users_data["user_levels"][user_id_str] = "2"

    users_data["users"][user_id_str]["message_count"] += 1
    save_users_data(users_data)

async def find_user_by_identifier(identifier, context=None, chat_id=None):
    """🔍 Find user by ID or username"""
    users_data = load_users_data()
    users = users_data["users"]

    identifier = identifier.replace('@', '').strip()

    if identifier.isdigit():
        if identifier in users:
            return identifier, users[identifier]

        if context and chat_id:
            try:
                user = await context.bot.get_chat_member(chat_id, int(identifier))
                user_info = user.user

                user_data = {
                    "message_count": 0,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "username": user_info.username if user_info.username else "N/A",
                    "first_name": user_info.first_name if user_info.first_name else "N/A",
                    "is_bot": user_info.is_bot
                }

                users_data["users"][identifier] = user_data
                save_users_data(users_data)

                return identifier, user_data
            except Exception as e:
                print(f"❌ Error getting user info: {e}")

        return None, None

    search_username = identifier.lower()
    for uid, user_data in users.items():
        user_username = user_data.get('username', '').lower()
        if user_username == search_username:
            return uid, user_data

    if context and chat_id:
        user_data = {
            "message_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "username": identifier,
            "first_name": identifier,
            "is_bot": False
        }

        fake_id = str(abs(hash(identifier)) % 1000000000)
        users_data["users"][fake_id] = user_data
        save_users_data(users_data)

        return fake_id, user_data

    return None, None

# ================================
# ⌨️ UNIFIED KEYBOARD FUNCTIONS
# ================================

def create_keyboard(buttons, resize=True):
    """⌨️ Unified keyboard creation"""
    return ReplyKeyboardMarkup(buttons, resize_keyboard=resize)

def main_menu_keyboard():
    """🏠 Main menu keyboard"""
    return create_keyboard([
        ['👥 Users', '📊 Stats'],
        ['📤 Upload', '📝 View Lines'],
        ['🛡️ Protected List', '🔫 Trigger ALL'],
        ['🎯 Danger', '🎮 Game Levels'],
        ['🤖 Multi-Bot Control']
    ])

def level_selection_keyboard():
    """📊 Level selection keyboard"""
    return create_keyboard([
        ['🟢 1 - Basic', '🔵 2 - Normal'],
        ['🟡 3 - Aggressive', '🟠 4 - Extreme'],
        ['🔴 5 - Ultra', '⚫ 6 - Non-Admin'],
        ['🌈 ALL LEVELS COMBINED 🚀'],
        ['↩️ Back to Main']
    ])

def danger_settings_keyboard():
    """🎯 Danger settings keyboard"""
    return create_keyboard([
        ['🎯 Add Target', '🗑️ Remove Target'],
        ['✏️ Edit Target', '🧹 Clear All Targets'],
        ['📋 Select Groups', '🎯 Target Spam Control'],
        ['👀 View Targets', '📊 View Settings'],
        ['🚀 Start All', '🛑 Stop All'],
        ['↩️ Back to Main']
    ])

def game_levels_keyboard():
    """🎮 Game levels management keyboard"""
    return create_keyboard([
        ['🎯 Add Game Target', '✏️ Edit Game Target'],
        ['🗑️ Remove Game Target', '📋 View Game Targets'],
        ['🧹 Clear All Game Targets', '⚙️ Game Settings'],
        ['🚀 Start Game Mode', '🛑 Stop Game Mode'],
        ['↩️ Back to Main']
    ])

def multi_bot_control_keyboard():
    """🤖 Multi-bot control keyboard"""
    return create_keyboard([
        ['🤖 Bot Status', '🔄 Sync Now'],
        ['➕ Add Bot', '➖ Remove Bot'],
        ['🚀 Start All Bots Spam', '🛑 Stop All Bots'],
        ['📊 Multi-Bot Stats', '⚙️ Speed Settings'],
        ['🚀 24/7 Spam', '🛑 Stop 24/7'],
        ['↩️ Back to Main']
    ])

def speed_control_keyboard():
    """⚙️ Speed control keyboard"""
    return create_keyboard([
        ['⚡ Fast (30/min)', '🚀 Faster (60/min)'],
        ['💨 Ultra (90/min)', '🔥 Extreme (120/min)'],
        ['↩️ Back to Multi-Bot']
    ])

def level_selection_danger_keyboard():
    """📊 Level selection for danger"""
    return create_keyboard([
        ['🟢 Basic Level', '🔵 Normal Level'],
        ['🟡 Aggressive Level', '🟠 Extreme Level'],
        ['🔴 Ultra Level', '⚫ Non-Admin Level'],
        ['🌈 ALL LEVELS COMBINED 🚀'],
        ['💬 Custom Message'],
        ['↩️ Back to Danger']
    ])

def level_selection_game_keyboard():
    """📊 Level selection for game targets"""
    return create_keyboard([
        ['🟢 Basic Level', '🔵 Normal Level'],
        ['🟡 Aggressive Level', '🟠 Extreme Level'],
        ['🔴 Ultra Level', '⚫ Non-Admin Level'],
        ['🌈 ALL LEVELS COMBINED 🚀'],
        ['↩️ Back to Game Levels']
    ])

def back_button_only():
    """↩️ Back button only"""
    return create_keyboard([['↩️ Back to Danger']])

def back_to_main_button():
    """↩️ Back to main button"""
    return create_keyboard([['↩️ Back to Main']])

def back_to_game_button():
    """↩️ Back to game button"""
    return create_keyboard([['↩️ Back to Game Levels']])

def back_to_multi_bot_button():
    """↩️ Back to multi-bot button"""
    return create_keyboard([['↩️ Back to Multi-Bot']])

def target_management_keyboard():
    """🎯 Target management keyboard"""
    return create_keyboard([
        ['✏️ Change Target Level', '✏️ Change Message Count'],
        ['↩️ Back to Danger']
    ])

def game_target_management_keyboard():
    """🎮 Game target management keyboard"""
    return create_keyboard([
        ['✏️ Change Game Level', '↩️ Back to Game Levels']
    ])

# ================================
# ↩️ NAVIGATION FUNCTIONS
# ================================

async def safe_reply(update, text, reply_markup=None):
    """💬 Safe reply function"""
    try:
        await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"❌ Error in replying: {e}")

async def back_to_main(update: Update):
    """↩️ Back to main menu"""
    await safe_reply(update, "↩️ Main menu", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def back_to_danger(update: Update):
    """↩️ Back to danger settings"""
    await danger_settings(update, None)
    return ConversationHandler.END

async def back_to_game_levels(update: Update):
    """↩️ Back to game levels"""
    await game_levels(update, None)
    return GAME_LEVELS_MANAGEMENT

async def back_to_multi_bot(update: Update):
    """↩️ Back to multi-bot control"""
    await multi_bot_control(update, None)
    return MULTI_BOT_CONTROL

# ================================
# ⚡ ULTRA FAST MESSAGE SENDING - MAX SPEED
# ================================

async def rate_limited_send(context, chat_id, message):
    """⚡ MAX SPEED message sending - NO DELAYS"""
    global MESSAGES_SENT_THIS_MINUTE, MINUTE_START_TIME, LAST_MESSAGE_TIME

    current_time = time.time()

    # Reset counter every minute
    if current_time - MINUTE_START_TIME >= 60:
        MESSAGES_SENT_THIS_MINUTE = 0
        MINUTE_START_TIME = current_time

    # Only check for absolute limits (2000 per minute)
    if MESSAGES_SENT_THIS_MINUTE >= 1900:
        wait_time = 60 - (current_time - MINUTE_START_TIME)
        if wait_time > 0:
            print(f"🚀 Approaching limit, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            MESSAGES_SENT_THIS_MINUTE = 0
            MINUTE_START_TIME = time.time()

    # NO ARTIFICIAL DELAYS - SEND AS FAST AS POSSIBLE
    async with MESSAGE_SEMAPHORE:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            MESSAGES_SENT_THIS_MINUTE += 1
            LAST_MESSAGE_TIME = time.time()
            return True, "Sent successfully"
        except Exception as e:
            error_msg = str(e)
            if "Flood control" in error_msg or "429" in error_msg:
                wait_match = re.search(r'Retry in (\d+)', error_msg)
                wait_time = int(wait_match.group(1)) if wait_match else 10
                print(f"🔄 Flood control: Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                try:
                    await context.bot.send_message(chat_id=chat_id, text=message)
                    MESSAGES_SENT_THIS_MINUTE += 1
                    LAST_MESSAGE_TIME = time.time()
                    return True, "Sent after flood wait"
                except Exception as e2:
                    return False, f"Flood retry failed: {e2}"
            return False, f"Error: {error_msg}"

async def send_bulk_messages(context, chat_id, messages):
    """🚀 ULTRA FAST bulk message sending"""
    tasks = []
    for message in messages:
        task = asyncio.create_task(rate_limited_send(context, chat_id, message))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful = sum(1 for result in results if result and isinstance(result, tuple) and result[0])
    return successful, len(messages)

# ================================
# 🚀 MULTI-BOT MESSAGE SENDING
# ================================

async def multi_bot_send_message(chat_id, message):
    """🤖 Multiple bots se message bheje"""
    tasks = []
    for app in BOT_APPLICATIONS:
        task = asyncio.create_task(
            rate_limited_send_wrapper(app, chat_id, message)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful = sum(1 for result in results if result and isinstance(result, tuple) and result[0])
    return successful, len(BOT_APPLICATIONS)

async def rate_limited_send_wrapper(app, chat_id, message):
    """Wrapper for rate limited send with app"""
    try:
        class MockContext:
            def __init__(self, bot):
                self.bot = bot
        
        context = MockContext(app.bot)
        success, msg = await rate_limited_send(context, chat_id, message)
        return success, msg
    except Exception as e:
        return False, str(e)

# ================================
# 🚀 START & MAIN COMMANDS
# ================================

async def start(update: Update, context: CallbackContext):
    """🚀 Start command"""
    user_id = update.effective_user.id

    if not is_private_chat(update):
        return

    context.user_data.clear()

    username = update.effective_user.username
    first_name = update.effective_user.first_name
    is_bot = update.effective_user.is_bot

    update_user_info(user_id, username, first_name, is_bot)

    load_protected_users()
    load_selected_targets()
    load_game_targets()

    start_counts = load_user_start_counts()
    user_id_str = str(user_id)

    if user_id_str not in start_counts:
        start_counts[user_id_str] = 0

    start_counts[user_id_str] += 1
    save_user_start_counts(start_counts)

    start_count = start_counts[user_id_str]

    if not is_admin(user_id):
        if start_count == 1:
            await update.message.reply_text("LODE YAHA MAA CHUDA TOH RHA H AGAR MERE BOSS KO BTA DIYA MENE TOH TERI MAA CHOD DENGE.")
        elif start_count == 2:
            await update.message.reply_text("Teri himmat kaise hui yaha aane ki? Nikal le yaha se!")
        elif start_count >= 3:
            abuse_lines = load_level_lines("6") or ["TERI MAA KI CHUT NON-ADMIN", "BSDK TUJHE KAUN BULA RHA HAI", "NIKAL LE YAHAN SE CHUTIYE"]
            mention_text = f"@{username}" if username else first_name

            abuse_messages = []
            for i in range(10):
                abuse_line = random.choice(abuse_lines)
                final_message = f"{mention_text} {abuse_line}"
                abuse_messages.append(final_message)

            successful, total = await send_bulk_messages(context, update.effective_chat.id, abuse_messages)

            if user_id_str not in [target['id'] if isinstance(target, dict) else target for target in SPAM_TARGETS]:
                target_data = {'id': user_id_str, 'type': 'level', 'level': '5', 'count': 50}
                SPAM_TARGETS.append(target_data)
                save_spam_settings()

            await update.message.reply_text("TERI MAA KI CHUT NON-ADMIN! JAISE HI TU MESSAGE KAREGA TABHI TEREKO SPAM MILENGE!")
        return

    if is_admin(user_id):
        groups = get_bot_groups()
        spam_status = "🚀 ACTIVE" if SPAM_MODE == "on" else "🛑 INACTIVE"
        game_status = "🎮 ACTIVE" if GAME_MODE_ACTIVE else "🛑 INACTIVE"
        continuous_status = "🔴 RUNNING" if CONTINUOUS_SPAM_ACTIVE else "🟢 IDLE"
        multi_bot_status = f"🤖 {len(BOT_APPLICATIONS)} BOTS READY"

        await update.message.reply_text(
            f"✅ Multi-Bot System Started!\n"
            f"🌍 Currently in {len(groups)} groups\n"
            f"🛡️ Protected Users: {len(PROTECTED_USERS)}\n"
            f"🎯 Total Targets: {len(SPAM_TARGETS)}\n"
            f"🎮 Game Targets: {len(GAME_TARGETS)}\n"
            f"✅ Selected Targets: {len(SELECTED_TARGETS)}\n"
            f"🤖 BOT TARGETING: ENABLED\n"
            f"⚡ SPAM MODE: {spam_status}\n"
            f"🎮 GAME MODE: {game_status}\n"
            f"🚀 24/7 MODE: {continuous_status}\n"
            f"🔗 MULTI-BOT: {multi_bot_status}\n\n"
            f"Use buttons below to manage the bot:",
            reply_markup=main_menu_keyboard()
        )

# ================================
# ⚡ 24/7 CONTINUOUS SPAM SYSTEM - MULTI-BOT INTEGRATED
# ================================

async def start_24x7_spam(update: Update, context: CallbackContext):
    """🚀 Start 24/7 Continuous Spam"""
    if not await validate_admin_access(update):
        return

    global CONTINUOUS_SPAM_ACTIVE, CONTINUOUS_SPAM_TASK

    if CONTINUOUS_SPAM_ACTIVE:
        await update.message.reply_text("✅ 24/7 Spam already running!", reply_markup=multi_bot_control_keyboard())
        return

    if not SPAM_TARGETS:
        await update.message.reply_text("❌ No targets set. Add targets first.", reply_markup=multi_bot_control_keyboard())
        return

    selected_groups = load_selected_groups()
    all_groups = get_bot_groups()

    groups_to_spam = selected_groups if selected_groups else [group['id'] for group in all_groups]

    if not groups_to_spam:
        await update.message.reply_text("❌ No groups available.", reply_markup=multi_bot_control_keyboard())
        return

    CONTINUOUS_SPAM_ACTIVE = True
    
    # Start 24/7 spam task
    CONTINUOUS_SPAM_TASK = asyncio.create_task(
        continuous_spam_loop(update, context, groups_to_spam)
    )

    await update.message.reply_text(
        f"🚀 24/7 CONTINUOUS SPAM STARTED!\n\n"
        f"🤖 Bots: {len(BOT_APPLICATIONS)}\n"
        f"🎯 Targets: {len(SPAM_TARGETS)}\n"
        f"🌍 Groups: {len(groups_to_spam)}\n"
        f"📨 Speed: {MESSAGES_PER_MINUTE} msg/min\n"
        f"⏰ Mode: 24/7 NON-STOP\n"
        f"🛡️ Flood Protection: ✅ ACTIVE\n\n"
        f"Use '🛑 Stop 24/7' to stop",
        reply_markup=multi_bot_control_keyboard()
    )

async def stop_24x7_spam(update: Update, context: CallbackContext):
    """🛑 Stop 24/7 Continuous Spam"""
    global CONTINUOUS_SPAM_ACTIVE, CONTINUOUS_SPAM_TASK

    if not CONTINUOUS_SPAM_ACTIVE:
        await update.message.reply_text("❌ 24/7 Spam is not running.", reply_markup=multi_bot_control_keyboard())
        return

    CONTINUOUS_SPAM_ACTIVE = False

    if CONTINUOUS_SPAM_TASK:
        CONTINUOUS_SPAM_TASK.cancel()
        try:
            await CONTINUOUS_SPAM_TASK
        except asyncio.CancelledError:
            pass
        CONTINUOUS_SPAM_TASK = None

    await update.message.reply_text(
        "✅ 24/7 SPAM STOPPED!\n\n"
        "All continuous spam activities have been terminated.",
        reply_markup=multi_bot_control_keyboard()
    )

async def continuous_spam_loop(update: Update, context: CallbackContext, groups_to_spam):
    """🔄 24/7 Continuous Spam Loop"""
    global CONTINUOUS_SPAM_ACTIVE

    total_messages_sent = 0
    session_start = time.time()

    try:
        while CONTINUOUS_SPAM_ACTIVE:
            minute_start = time.time()
            messages_this_minute = 0

            # Prepare messages for this minute
            all_messages = []
            message_groups = []

            for target in SPAM_TARGETS:
                if isinstance(target, dict):
                    target_id = target['id']
                    count = target.get('count', 1)
                    spam_type = target.get('type', 'level')

                    if spam_type == 'level':
                        level = target.get('level', '2')
                        if level == "combined":
                            lines = load_combined_level_lines()
                        else:
                            lines = load_level_lines(level)
                    else:
                        custom_message = target.get('custom_message', '')
                        lines = [custom_message] if custom_message else []

                    if lines:
                        for group_id in groups_to_spam:
                            uid, user_data = await find_user_by_identifier(target_id, context, group_id)
                            mention_text = f"@{user_data['username']}" if user_data and user_data.get('username') else target_id

                            for i in range(count):
                                if spam_type == 'level':
                                    message = get_rotated_message(level, target_id)
                                else:
                                    message = lines[0]

                                final_message = f"{mention_text} {message}"
                                all_messages.append(final_message)
                                message_groups.append(group_id)

            if not all_messages:
                print("❌ No messages to send in this cycle")
                await asyncio.sleep(60)
                continue

            # Send messages with safe rate limiting
            for i, message in enumerate(all_messages):
                if not CONTINUOUS_SPAM_ACTIVE:
                    break

                if messages_this_minute >= MESSAGES_PER_MINUTE:
                    break

                group_id = message_groups[i]
                bot_index = i % len(BOT_APPLICATIONS)
                current_bot = BOT_APPLICATIONS[bot_index]

                success, result = await rate_limited_send_continuous(current_bot, group_id, message)
                
                if success:
                    total_messages_sent += 1
                    messages_this_minute += 1
                else:
                    print(f"❌ Failed to send message: {result}")

                # Maintain safe message gap
                await asyncio.sleep(MESSAGE_GAP)

            # Wait for next minute cycle
            elapsed = time.time() - minute_start
            if elapsed < 60.0 and CONTINUOUS_SPAM_ACTIVE:
                await asyncio.sleep(60.0 - elapsed)

            # Print stats every 10 minutes
            if int(time.time() - session_start) % 600 == 0:
                print(f"📊 24/7 Stats: {total_messages_sent} total messages sent")

    except asyncio.CancelledError:
        print("🛑 24/7 Spam loop cancelled")
    except Exception as e:
        logger.error(f"Error in 24/7 spam loop: {e}")
        CONTINUOUS_SPAM_ACTIVE = False

async def rate_limited_send_continuous(app, chat_id, message):
    """⚡ Rate limited send for continuous spam"""
    global MESSAGES_SENT_THIS_MINUTE, MINUTE_START_TIME

    current_time = time.time()

    # Reset counter every minute
    if current_time - MINUTE_START_TIME >= 60:
        MESSAGES_SENT_THIS_MINUTE = 0
        MINUTE_START_TIME = current_time

    # Check minute limit
    if MESSAGES_SENT_THIS_MINUTE >= MESSAGES_PER_MINUTE:
        wait_time = 60 - (current_time - MINUTE_START_TIME)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            MESSAGES_SENT_THIS_MINUTE = 0
            MINUTE_START_TIME = time.time()

    async with MESSAGE_SEMAPHORE:
        try:
            await app.bot.send_message(chat_id=chat_id, text=message)
            MESSAGES_SENT_THIS_MINUTE += 1
            return True, "Sent successfully"
        except Exception as e:
            error_msg = str(e)
            if "Flood control" in error_msg or "429" in error_msg:
                wait_match = re.search(r'Retry in (\d+)', error_msg)
                wait_time = int(wait_match.group(1)) if wait_match else 10
                print(f"🔄 Flood control: Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                try:
                    await app.bot.send_message(chat_id=chat_id, text=message)
                    MESSAGES_SENT_THIS_MINUTE += 1
                    return True, "Sent after flood wait"
                except Exception as e2:
                    return False, f"Flood retry failed: {e2}"
            return False, f"Error: {error_msg}"

# ================================
# ⚡ SPEED CONTROL SYSTEM
# ================================

async def speed_control(update: Update, context: CallbackContext):
    """⚙️ Speed control settings"""
    if not await validate_admin_access(update):
        return

    await update.message.reply_text(
        f"⚙️ SPEED CONTROL SETTINGS\n\n"
        f"Current Speed: {MESSAGES_PER_MINUTE} messages/minute\n"
        f"Current Gap: {MESSAGE_GAP:.2f} seconds/message\n\n"
        f"Select speed level:",
        reply_markup=speed_control_keyboard()
    )
    return SPEED_CONTROL

async def handle_speed_control(update: Update, context: CallbackContext):
    """⚙️ Handle speed control selection"""
    if not await validate_admin_access(update):
        return

    global MESSAGES_PER_MINUTE, MESSAGE_GAP

    command = update.message.text.strip()

    if command == '↩️ Back to Multi-Bot':
        await back_to_multi_bot(update)
        return MULTI_BOT_CONTROL

    speed_settings = {
        '⚡ Fast (30/min)': (30, 2.0),
        '🚀 Faster (60/min)': (60, 1.0),
        '💨 Ultra (90/min)': (90, 0.67),
        '🔥 Extreme (120/min)': (120, 0.5)
    }

    if command in speed_settings:
        MESSAGES_PER_MINUTE, MESSAGE_GAP = speed_settings[command]
        
        await update.message.reply_text(
            f"✅ SPEED UPDATED!\n\n"
            f"📨 Messages/Minute: {MESSAGES_PER_MINUTE}\n"
            f"⏱️ Message Gap: {MESSAGE_GAP:.2f}s\n"
            f"🤖 Multi-Bot Optimized: ✅",
            reply_markup=multi_bot_control_keyboard()
        )
        return MULTI_BOT_CONTROL

    await update.message.reply_text("❌ Invalid speed selection.", reply_markup=speed_control_keyboard())
    return SPEED_CONTROL

# ================================
# 🤖 BOT MANAGEMENT SYSTEM
# ================================

async def add_bot_token(update: Update, context: CallbackContext):
    """➕ Add new bot with token"""
    if not await validate_admin_access(update):
        return
    
    await update.message.reply_text(
        "🤖 Please enter the new bot token:\n\n"
        "Format: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ\n\n"
        "Type 'cancel' to cancel.",
        reply_markup=back_to_multi_bot_button()
    )
    return ADD_BOT_TOKEN

async def handle_bot_token_input(update: Update, context: CallbackContext):
    """🤖 Handle bot token input"""
    token = update.message.text.strip()
    
    if token.lower() == 'cancel' or token == '↩️ Back to Multi-Bot':
        await back_to_multi_bot(update)
        return MULTI_BOT_CONTROL
    
    # Validate token format
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
        await update.message.reply_text(
            "❌ Invalid token format!",
            reply_markup=back_to_multi_bot_button()
        )
        return ADD_BOT_TOKEN
    
    # Check if token already exists
    if token in TOKENS:
        await update.message.reply_text(
            "❌ This token is already added!",
            reply_markup=multi_bot_control_keyboard()
        )
        return MULTI_BOT_CONTROL
    
    try:
        # Test the token
        temp_app = Application.builder().token(token).build()
        me = await temp_app.bot.get_me()
        
        # Add to tokens list
        TOKENS.append(token)
        save_bot_tokens()
        
        # Initialize the new bot
        new_app = Application.builder().token(token).build()
        BOT_APPLICATIONS.append(new_app)
        
        # Add handlers to new bot
        new_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_bot_added))
        new_app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_bot_removed))
        new_app.add_handler(MessageHandler(filters.ChatType.GROUPS, handle_group_message))
        
        # Start polling for new bot
        asyncio.create_task(new_app.run_polling())
        
        await update.message.reply_text(
            f"✅ Bot added successfully!\n\n"
            f"🤖 Bot: @{me.username}\n"
            f"🆔 ID: {me.id}\n"
            f"📛 Name: {me.first_name}\n"
            f"🔗 Auto-sync: ✅ ENABLED\n\n"
            f"Total bots now: {len(BOT_APPLICATIONS)}",
            reply_markup=multi_bot_control_keyboard()
        )
        
        print(f"✅ New bot added: @{me.username}")
        return MULTI_BOT_CONTROL
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to add bot!\n"
            f"Error: {str(e)}",
            reply_markup=multi_bot_control_keyboard()
        )
        return MULTI_BOT_CONTROL

async def remove_bot_selection(update: Update, context: CallbackContext):
    """➖ Remove bot selection"""
    if not await validate_admin_access(update):
        return
    
    if len(BOT_APPLICATIONS) <= 1:
        await update.message.reply_text(
            "❌ Cannot remove all bots! At least one bot must remain.",
            reply_markup=multi_bot_control_keyboard()
        )
        return MULTI_BOT_CONTROL
    
    await update.message.reply_text(
        "🗑️ Select bot to remove:\n\n"
        "Click on bot to select for removal",
        reply_markup=create_bot_selection_keyboard()
    )
    return REMOVE_BOT_SELECTION

def create_bot_selection_keyboard():
    """🤖 Create bot selection keyboard for removal"""
    keyboard = []
    
    for i, app in enumerate(BOT_APPLICATIONS):
        try:
            me = app.bot
            keyboard.append([f"🤖 Bot {i+1}: @{me.username}"])
        except:
            keyboard.append([f"❌ Bot {i+1}: OFFLINE"])
    
    keyboard.append(['↩️ Back to Multi-Bot'])
    return create_keyboard(keyboard)

async def handle_bot_removal(update: Update, context: CallbackContext):
    """🗑️ Handle bot removal"""
    command = update.message.text.strip()
    
    if command == '↩️ Back to Multi-Bot':
        await back_to_multi_bot(update)
        return MULTI_BOT_CONTROL
    
    # Find the bot to remove
    for i, app in enumerate(BOT_APPLICATIONS):
        try:
            me = app.bot
            bot_button = f"🤖 Bot {i+1}: @{me.username}"
            
            if command == bot_button:
                # Remove bot from applications
                removed_app = BOT_APPLICATIONS.pop(i)
                removed_token = TOKENS[i]
                
                # Remove from tokens list
                TOKENS.pop(i)
                save_bot_tokens()
                
                # Stop the bot
                try:
                    await removed_app.stop()
                    await removed_app.shutdown()
                except:
                    pass
                
                await update.message.reply_text(
                    f"✅ Bot removed successfully!\n\n"
                    f"🗑️ Removed: @{me.username}\n"
                    f"📊 Remaining bots: {len(BOT_APPLICATIONS)}",
                    reply_markup=multi_bot_control_keyboard()
                )
                return MULTI_BOT_CONTROL
                
        except Exception as e:
            continue
    
    await update.message.reply_text(
        "❌ Please select a bot using the buttons below:",
        reply_markup=create_bot_selection_keyboard()
    )
    return REMOVE_BOT_SELECTION

# ================================
# 🤖 MULTI-BOT CONTROL SYSTEM
# ================================

async def multi_bot_control(update: Update, context: CallbackContext):
    """🤖 Multi-bot control center"""
    if not await validate_admin_access(update):
        return

    bot_status_text = "🤖 MULTI-BOT CONTROL CENTER\n\n"
    
    # Bot status information
    for i, app in enumerate(BOT_APPLICATIONS, 1):
        try:
            me = await app.bot.get_me()
            bot_status_text += f"🤖 Bot {i}: @{me.username} - ✅ ONLINE\n"
        except:
            bot_status_text += f"🤖 Bot {i}: ❌ OFFLINE\n"
    
    bot_status_text += f"\n🎯 Shared Targets: {len(SPAM_TARGETS)}"
    bot_status_text += f"\n🔄 Auto-Sync: ✅ ACTIVE"
    bot_status_text += f"\n⚡ Speed: {MESSAGES_PER_MINUTE} msg/min"
    bot_status_text += f"\n🚀 24/7 Mode: {'🔴 RUNNING' if CONTINUOUS_SPAM_ACTIVE else '🟢 IDLE'}"
    bot_status_text += f"\n⚡ Multi-Spam: {'✅ READY' if len(BOT_APPLICATIONS) > 1 else '❌ SINGLE MODE'}"
    
    bot_status_text += "\n\n🔧 Control Options:"
    bot_status_text += "\n• Bot Status - Sabhi bots ka status dekhe"
    bot_status_text += "\n• Add Bot - Naya bot add kare"
    bot_status_text += "\n• Remove Bot - Bot remove kare"
    bot_status_text += "\n• Sync Now - Manual data sync kare"
    bot_status_text += "\n• Start All Bots Spam - Sabhi bots se spam start kare"
    bot_status_text += "\n• Stop All Bots - Sabhi bots ka spam stop kare"
    bot_status_text += "\n• Speed Settings - Spam speed control kare"
    bot_status_text += "\n• 24/7 Spam - Continuous spam start kare"
    bot_status_text += "\n• Stop 24/7 - Continuous spam stop kare"

    await update.message.reply_text(bot_status_text, reply_markup=multi_bot_control_keyboard())
    return MULTI_BOT_CONTROL

async def handle_multi_bot_control(update: Update, context: CallbackContext):
    """🤖 Handle multi-bot control commands"""
    if not await validate_admin_access(update):
        return

    command = update.message.text.strip()

    if command == '↩️ Back to Main':
        await back_to_main(update)
        return ConversationHandler.END

    elif command == '🤖 Bot Status':
        status_text = "🤖 MULTI-BOT STATUS\n\n"
        
        active_bots = 0
        for i, app in enumerate(BOT_APPLICATIONS, 1):
            try:
                me = await app.bot.get_me()
                status_text += f"✅ Bot {i}: @{me.username}\n"
                status_text += f"   🆔 ID: {me.id}\n"
                status_text += f"   📛 Name: {me.first_name}\n"
                status_text += f"   🔗 Username: @{me.username}\n\n"
                active_bots += 1
            except Exception as e:
                status_text += f"❌ Bot {i}: OFFLINE - {str(e)}\n\n"
        
        status_text += f"📊 SUMMARY:\n"
        status_text += f"✅ Active Bots: {active_bots}/{len(BOT_APPLICATIONS)}\n"
        status_text += f"🎯 Shared Targets: {len(SPAM_TARGETS)}\n"
        status_text += f"🔄 Last Sync: {time.ctime(LAST_SYNC_TIME)}\n"
        status_text += f"⚡ Speed: {MESSAGES_PER_MINUTE} msg/min\n"
        status_text += f"🚀 24/7 Mode: {'🔴 RUNNING' if CONTINUOUS_SPAM_ACTIVE else '🟢 IDLE'}"

        await update.message.reply_text(status_text, reply_markup=multi_bot_control_keyboard())

    elif command == '➕ Add Bot':
        await add_bot_token(update, context)
        return ADD_BOT_TOKEN

    elif command == '➖ Remove Bot':
        await remove_bot_selection(update, context)
        return REMOVE_BOT_SELECTION

    elif command == '🔄 Sync Now':
        await sync_multi_bot_data()
        await update.message.reply_text(
            "✅ Multi-bot data synced successfully!\n"
            f"🎯 Targets: {len(SPAM_TARGETS)}\n"
            f"🛡️ Protected: {len(PROTECTED_USERS)}\n"
            f"🎮 Game Targets: {len(GAME_TARGETS)}",
            reply_markup=multi_bot_control_keyboard()
        )

    elif command == '🚀 Start All Bots Spam':
        if not SPAM_TARGETS:
            await update.message.reply_text("❌ No targets set. Add targets first.", reply_markup=multi_bot_control_keyboard())
            return

        selected_groups = load_selected_groups()
        all_groups = get_bot_groups()

        groups_to_spam = selected_groups if selected_groups else [group['id'] for group in all_groups]

        if not groups_to_spam:
            await update.message.reply_text("❌ No groups available.", reply_markup=multi_bot_control_keyboard())
            return

        await update.message.reply_text(
            f"🚀 STARTING MULTI-BOT SPAM!\n"
            f"🤖 Bots: {len(BOT_APPLICATIONS)}\n"
            f"🎯 Targets: {len(SPAM_TARGETS)}\n"
            f"🌍 Groups: {len(groups_to_spam)}\n"
            f"⚡ Speed: {MESSAGES_PER_MINUTE} msg/min\n"
            f"🔁 Mode: CONTINUOUS UNTIL STOPPED",
            reply_markup=multi_bot_control_keyboard()
        )

        # Start multi-bot spam
        asyncio.create_task(start_multi_bot_spam(update, context, groups_to_spam))

    elif command == '🛑 Stop All Bots':
        await stop_all_multi_bot_spam(update, context)
        await update.message.reply_text(
            "✅ ALL BOTS STOPPED!\n"
            "🤖 Sabhi bots ka spam band ho gaya\n"
            "🛑 Multi-bot mode inactive",
            reply_markup=multi_bot_control_keyboard()
        )

    elif command == '⚙️ Speed Settings':
        await speed_control(update, context)
        return SPEED_CONTROL

    elif command == '🚀 24/7 Spam':
        await start_24x7_spam(update, context)

    elif command == '🛑 Stop 24/7':
        await stop_24x7_spam(update, context)

    elif command == '📊 Multi-Bot Stats':
        stats_text = "📊 MULTI-BOT STATISTICS\n\n"
        
        total_messages = 0
        active_bots = 0
        
        for i, app in enumerate(BOT_APPLICATIONS, 1):
            try:
                me = await app.bot.get_me()
                stats_text += f"🤖 Bot {i}: @{me.username}\n"
                stats_text += f"   ✅ ONLINE\n"
                active_bots += 1
            except:
                stats_text += f"🤖 Bot {i}: ❌ OFFLINE\n"
        
        stats_text += f"\n📈 SYSTEM STATS:\n"
        stats_text += f"✅ Active Bots: {active_bots}/{len(BOT_APPLICATIONS)}\n"
        stats_text += f"🎯 Shared Targets: {len(SPAM_TARGETS)}\n"
        stats_text += f"🛡️ Protected Users: {len(PROTECTED_USERS)}\n"
        stats_text += f"🎮 Game Targets: {len(GAME_TARGETS)}\n"
        stats_text += f"🌍 Total Groups: {len(get_bot_groups())}\n"
        stats_text += f"⚡ Speed: {MESSAGES_PER_MINUTE} msg/min\n"
        stats_text += f"🚀 24/7 Mode: {'🔴 RUNNING' if CONTINUOUS_SPAM_ACTIVE else '🟢 IDLE'}\n"
        stats_text += f"🔄 Last Sync: {time.ctime(LAST_SYNC_TIME)}"

        await update.message.reply_text(stats_text, reply_markup=multi_bot_control_keyboard())

    else:
        await update.message.reply_text("❌ Invalid command.", reply_markup=multi_bot_control_keyboard())

# ================================
# 🚀 UNIFIED SPAM EXECUTION SYSTEM - SINGLE FUNCTION
# ================================

async def execute_unified_spam(update: Update, context: CallbackContext, groups, selected_targets=None, spam_type="normal"):
    """⚡ UNIFIED SPAM EXECUTION - ALL TYPES KE LIYE SINGLE FUNCTION"""
    global SPAM_MODE, SPAM_TASK_RUNNING, CURRENT_SPAM_TASK

    SPAM_MODE = "on"
    SPAM_TASK_RUNNING = True
    CURRENT_SPAM_TASK = asyncio.current_task()

    total_messages_sent = 0
    failed_messages = 0
    session_start = time.time()

    progress_msg = await update.message.reply_text(f"🚀 {spam_type.upper()} SPAM STARTING...")

    try:
        # CONTINUOUS LOOP - MANUALLY STOP TAK CHALEGA
        while SPAM_TASK_RUNNING:
            all_messages = []
            message_targets = []
            message_groups = []

            # Prepare messages
            for target in SPAM_TARGETS:
                if isinstance(target, dict):
                    target_id = target['id']

                    # Check if target is selected (for selective spam)
                    if selected_targets and target_id not in selected_targets:
                        continue

                    count = target.get('count', 1)
                    spam_type_msg = target.get('type', 'level')

                    if spam_type_msg == 'level':
                        level = target.get('level', '2')
                        if level == "combined":
                            lines = load_combined_level_lines()
                        else:
                            lines = load_level_lines(level)
                    else:
                        custom_message = target.get('custom_message', '')
                        lines = [custom_message] if custom_message else []

                    if lines:
                        for group in groups:
                            group_id = group['id']

                            uid, user_data = await find_user_by_identifier(target_id, context, group_id)
                            mention_text = f"@{user_data['username']}" if user_data and user_data.get('username') else target_id

                            for i in range(count):
                                if spam_type_msg == 'level':
                                    message = get_rotated_message(level, target_id)
                                else:
                                    message = lines[0]

                                final_message = f"{mention_text} {message}"
                                all_messages.append(final_message)
                                message_targets.append(target_id)
                                message_groups.append(group_id)

            if not all_messages:
                print("❌ No messages to send in this cycle")
                await asyncio.sleep(10)
                continue

            # ULTRA FAST BATCH PROCESSING
            batch_size = min(50, len(all_messages))
            total_batches = (len(all_messages) + batch_size - 1) // batch_size

            for batch_num in range(total_batches):
                if not SPAM_TASK_RUNNING:
                    break

                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(all_messages))
                batch_messages = all_messages[start_idx:end_idx]
                batch_groups = message_groups[start_idx:end_idx]

                # SEND ALL MESSAGES IN BATCH AS FAST AS POSSIBLE
                tasks = []
                for i, message in enumerate(batch_messages):
                    group_id = batch_groups[i]
                    task = asyncio.create_task(rate_limited_send(context, group_id, message))
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if result and isinstance(result, tuple) and result[0]:
                        total_messages_sent += 1
                    else:
                        failed_messages += 1

                # PROGRESS UPDATE
                if batch_num % 20 == 0 or batch_num == total_batches - 1:
                    try:
                        progress = f"🚀 {spam_type.upper()} SPAMMING...\n📊 Cycle Progress\n✅ Sent: {total_messages_sent}\n❌ Failed: {failed_messages}\n🔁 Mode: CONTINUOUS"
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=progress_msg.message_id,
                            text=progress
                        )
                    except:
                        pass

            # CONTINUOUS MODE - AUTOMATICALLY RESTART
            if SPAM_TASK_RUNNING:
                print(f"🔄 {spam_type.upper()} spam cycle completed, restarting...")
                await asyncio.sleep(2)  # Small gap between cycles

    except asyncio.CancelledError:
        await update.message.reply_text(
            f"🛑 {spam_type.title()} Spam stopped!\n"
            f"📨 Messages sent: {total_messages_sent}",
            reply_markup=danger_settings_keyboard()
        )
        raise

    except Exception as e:
        logger.error(f"Error in {spam_type} spam execution: {e}")
        await update.message.reply_text(f"❌ Error in {spam_type} spam: {str(e)}", reply_markup=danger_settings_keyboard())

    finally:
        SPAM_MODE = "off"
        SPAM_TASK_RUNNING = False
        if CURRENT_SPAM_TASK in ACTIVE_SPAM_TASKS:
            ACTIVE_SPAM_TASKS.discard(CURRENT_SPAM_TASK)
        CURRENT_SPAM_TASK = None

# ================================
# 🚀 MULTI-BOT SPAM SYSTEM
# ================================

async def start_multi_bot_spam(update: Update, context: CallbackContext, groups_to_spam):
    """🚀 Start spam with all bots simultaneously - CONTINUOUS MODE"""
    global MULTI_BOT_SPAM_ACTIVE, MULTI_BOT_TASKS

    MULTI_BOT_SPAM_ACTIVE = True
    MULTI_BOT_TASKS = []

    progress_msg = await update.message.reply_text("🚀 STARTING MULTI-BOT CONTINUOUS SPAM...")

    try:
        # CONTINUOUS LOOP FOR MULTI-BOT
        while MULTI_BOT_SPAM_ACTIVE:
            # Prepare messages for all bots
            all_messages = []
            message_groups = []

            for target in SPAM_TARGETS:
                if isinstance(target, dict):
                    target_id = target['id']
                    count = target.get('count', 1)
                    spam_type = target.get('type', 'level')

                    if spam_type == 'level':
                        level = target.get('level', '2')
                        if level == "combined":
                            lines = load_combined_level_lines()
                        else:
                            lines = load_level_lines(level)
                    else:
                        custom_message = target.get('custom_message', '')
                        lines = [custom_message] if custom_message else []

                    if lines:
                        for group_id in groups_to_spam:
                            uid, user_data = await find_user_by_identifier(target_id, context, group_id)
                            mention_text = f"@{user_data['username']}" if user_data and user_data.get('username') else target_id

                            for i in range(count):
                                if spam_type == 'level':
                                    message = get_rotated_message(level, target_id)
                                else:
                                    message = lines[0]

                                final_message = f"{mention_text} {message}"
                                all_messages.append(final_message)
                                message_groups.append(group_id)

            print(f"🎯 Multi-bot prepared {len(all_messages)} messages for {len(BOT_APPLICATIONS)} bots")

            if not all_messages:
                print("❌ No messages to send in this cycle")
                await asyncio.sleep(10)
                continue

            # Distribute messages among bots
            messages_per_bot = len(all_messages) // len(BOT_APPLICATIONS)
            total_sent_this_cycle = 0

            for bot_index, app in enumerate(BOT_APPLICATIONS):
                start_idx = bot_index * messages_per_bot
                end_idx = start_idx + messages_per_bot if bot_index < len(BOT_APPLICATIONS) - 1 else len(all_messages)
                
                bot_messages = all_messages[start_idx:end_idx]
                bot_groups = message_groups[start_idx:end_idx]

                if bot_messages:
                    task = asyncio.create_task(
                        execute_multi_bot_spam_cycle(app, bot_messages, bot_groups, progress_msg, update)
                    )
                    MULTI_BOT_TASKS.append(task)

            # Wait for all tasks to complete this cycle
            if MULTI_BOT_TASKS:
                results = await asyncio.gather(*MULTI_BOT_TASKS, return_exceptions=True)
                
                total_sent_this_cycle = 0
                for result in results:
                    if isinstance(result, int):
                        total_sent_this_cycle += result

                MULTI_BOT_TASKS = []

            # CONTINUOUS MODE - RESTART CYCLE
            if MULTI_BOT_SPAM_ACTIVE:
                print("🔄 Multi-bot spam cycle completed, restarting...")
                await asyncio.sleep(5)  # Gap between cycles

    except Exception as e:
        logger.error(f"Multi-bot spam error: {e}")
        await update.message.reply_text(f"❌ Multi-bot spam error: {str(e)}", reply_markup=multi_bot_control_keyboard())
    
    finally:
        MULTI_BOT_SPAM_ACTIVE = False
        MULTI_BOT_TASKS = []

async def execute_multi_bot_spam_cycle(app, messages, groups, progress_msg, update):
    """🤖 Execute spam cycle for a specific bot"""
    total_sent = 0
    
    try:
        batch_size = 20
        total_batches = (len(messages) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            if not MULTI_BOT_SPAM_ACTIVE:
                break
                
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(messages))
            batch_messages = messages[start_idx:end_idx]
            batch_groups = groups[start_idx:end_idx]
            
            # Send batch with this bot
            tasks = []
            for i, message in enumerate(batch_messages):
                group_id = batch_groups[i]
                task = asyncio.create_task(
                    rate_limited_send_wrapper(app, group_id, message)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result and isinstance(result, tuple) and result[0]:
                    total_sent += 1
            
            # Update progress occasionally
            if batch_num % 10 == 0:
                try:
                    progress_text = f"🚀 MULTI-BOT CONTINUOUS SPAM\n🤖 Bot: @{app.bot.username}\n📊 Progress: {batch_num+1}/{total_batches}\n✅ Sent: {total_sent}"
                    await update.message.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=progress_msg.message_id,
                        text=progress_text
                    )
                except:
                    pass
        
        return total_sent
        
    except Exception as e:
        logger.error(f"Bot spam execution error: {e}")
        return total_sent

async def stop_all_multi_bot_spam(update: Update, context: CallbackContext):
    """🛑 Stop all multi-bot spam"""
    global MULTI_BOT_SPAM_ACTIVE, MULTI_BOT_TASKS, SPAM_MODE, SPAM_TASK_RUNNING

    MULTI_BOT_SPAM_ACTIVE = False
    SPAM_MODE = "off"
    SPAM_TASK_RUNNING = False

    # Cancel all multi-bot tasks
    for task in MULTI_BOT_TASKS:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    MULTI_BOT_TASKS = []

    # Cancel individual spam tasks
    tasks_to_cancel = list(ACTIVE_SPAM_TASKS)
    for task in tasks_to_cancel:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            ACTIVE_SPAM_TASKS.discard(task)

    ACTIVE_SPAM_TASKS.clear()

    print("✅ All multi-bot spam stopped!")

# ================================
# 🛑 STOP SPAM FUNCTIONS
# ================================

async def stop_selected_spam(update: Update, context: CallbackContext):
    """🛑 Stop selected spam tasks only"""
    global SPAM_MODE, SPAM_TASK_RUNNING, CURRENT_SPAM_TASK

    SPAM_MODE = "off"
    SPAM_TASK_RUNNING = False

    if CURRENT_SPAM_TASK and not CURRENT_SPAM_TASK.done():
        CURRENT_SPAM_TASK.cancel()
        try:
            await CURRENT_SPAM_TASK
        except asyncio.CancelledError:
            pass
        CURRENT_SPAM_TASK = None

    tasks_to_cancel = list(ACTIVE_SPAM_TASKS)
    for task in tasks_to_cancel:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            ACTIVE_SPAM_TASKS.discard(task)

    ACTIVE_SPAM_TASKS.clear()

    await update.message.reply_text(
        "✅ SELECTED spam stopped successfully!\n"
        "🎯 Only selected targets spam stopped.\n"
        "🔄 Bot is now responsive to all commands.",
        reply_markup=danger_settings_keyboard()
    )

async def stop_all_spam_completely(update: Update, context: CallbackContext):
    """🛑 Stop ALL spam completely - ALL TARGETS"""
    global SPAM_MODE, SPAM_TASK_RUNNING, CURRENT_SPAM_TASK, TRIGGER_ACTIVE, MULTI_BOT_SPAM_ACTIVE, CONTINUOUS_SPAM_ACTIVE

    SPAM_MODE = "off"
    SPAM_TASK_RUNNING = False
    TRIGGER_ACTIVE = False
    MULTI_BOT_SPAM_ACTIVE = False
    CONTINUOUS_SPAM_ACTIVE = False

    if CURRENT_SPAM_TASK and not CURRENT_SPAM_TASK.done():
        CURRENT_SPAM_TASK.cancel()
        try:
            await CURRENT_SPAM_TASK
        except asyncio.CancelledError:
            pass
        CURRENT_SPAM_TASK = None

    # Stop multi-bot spam
    await stop_all_multi_bot_spam(update, context)

    # Stop 24/7 spam
    global CONTINUOUS_SPAM_TASK
    if CONTINUOUS_SPAM_TASK:
        CONTINUOUS_SPAM_TASK.cancel()
        try:
            await CONTINUOUS_SPAM_TASK
        except asyncio.CancelledError:
            pass
        CONTINUOUS_SPAM_TASK = None

    # Cancel individual spam tasks
    tasks_to_cancel = list(ACTIVE_SPAM_TASKS)
    for task in tasks_to_cancel:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            ACTIVE_SPAM_TASKS.discard(task)

    ACTIVE_SPAM_TASKS.clear()

    await update.message.reply_text(
        "✅ ALL spam stopped completely!\n"
        "🎯 All targets spam stopped.\n"
        "🔫 Trigger mode also disabled.\n"
        "🤖 Multi-bot spam stopped.\n"
        "🚀 24/7 spam stopped.\n"
        "🔄 Bot is now fully responsive.",
        reply_markup=danger_settings_keyboard()
    )

# ================================
# 🎯 DANGER SYSTEM - CONTINUOUS MODE
# ================================

async def danger_settings(update: Update, context: CallbackContext):
    """🎯 Danger settings function"""
    if not await validate_admin_access(update):
        return ConversationHandler.END

    context.user_data.clear()

    selected_groups = load_selected_groups()
    all_groups = get_bot_groups()
    selected_targets = load_selected_targets()

    level_targets = 0
    custom_targets = 0
    total_messages = 0

    for target in SPAM_TARGETS:
        if isinstance(target, dict):
            if target.get('type') == 'level':
                level_targets += 1
            elif target.get('type') == 'custom':
                custom_targets += 1
            total_messages += target.get('count', 1) * (len(selected_groups) if selected_groups else len(all_groups))

    danger_status = (
        f"🎯 Danger Settings\n\n"
        f"🎯 Total Targets: {len(SPAM_TARGETS)}\n"
        f"✅ Selected Targets: {len(selected_targets)}\n"
        f"📊 Level Targets: {level_targets}\n"
        f"💬 Custom Targets: {custom_targets}\n"
        f"🌍 Total Groups: {len(all_groups)}\n"
        f"📋 Selected Groups: {len(selected_groups)}\n"
        f"📨 Expected Messages: {total_messages}\n"
        f"🤖 Active Bots: {len(BOT_APPLICATIONS)}\n"
        f"🔄 Auto-Recoveries: {TOTAL_RECOVERIES}\n\n"
        f"🤖 BOT TARGETING: ENABLED\n"
        f"🎯 TARGET SPAM CONTROL: AVAILABLE\n"
        f"🔗 MULTI-BOT SYNC: ✅ ACTIVE\n"
        f"⚡ CONTINUOUS MODE: ✅ ENABLED\n\n"
        f"Choose option:"
    )

    await update.message.reply_text(danger_status, reply_markup=danger_settings_keyboard())
    return DANGER_SETTING

async def handle_danger_settings(update: Update, context: CallbackContext):
    """🎯 Handle danger settings"""
    if not await validate_admin_access(update):
        return ConversationHandler.END

    command = update.message.text.strip()

    if command == '↩️ Back to Main':
        context.user_data.clear()
        await back_to_main(update)
        return ConversationHandler.END

    if command == '↩️ Back to Danger':
        context.user_data.clear()
        await danger_settings(update, context)
        return DANGER_SETTING

    elif command == '🎯 Add Target':
        context.user_data.clear()
        await update.message.reply_text(
            "🎯 Enter username or user ID to add as target:\n\n"
            "✅ BOTS & USERS dono ko target kar sakte hain!\n"
            "• Username: @username\n"
            "• User ID: 123456789\n"
            "• Username without @: username",
            reply_markup=back_button_only()
        )
        context.user_data['setting_type'] = True
        return ADDING_TARGET

    elif command == '🗑️ Remove Target':
        context.user_data.clear()
        if not SPAM_TARGETS:
            await update.message.reply_text("❌ No targets to remove.", reply_markup=danger_settings_keyboard())
            return DANGER_SETTING

        selected_targets = load_selected_targets()
        await update.message.reply_text(
            "🗑️ Select targets to remove:\n\n"
            "Click on targets to select/deselect (✅ = selected)\n"
            "Then click '🗑️ Remove Selected' to remove them",
            reply_markup=create_target_spam_control_keyboard(SPAM_TARGETS, selected_targets, False)
        )
        context.user_data['removing_target'] = True
        return TARGET_SPAM_CONTROL

    elif command == '✏️ Edit Target':
        context.user_data.clear()
        if not SPAM_TARGETS:
            await update.message.reply_text("❌ No targets to edit.", reply_markup=danger_settings_keyboard())
            return DANGER_SETTING

        await update.message.reply_text(
            "✏️ Select target to edit:\n\n"
            "Click on target to edit:",
            reply_markup=create_edit_target_selection_keyboard(SPAM_TARGETS)
        )
        return EDIT_TARGET_SELECTION

    elif command == '🧹 Clear All Targets':
        context.user_data.clear()
        SPAM_TARGETS.clear()
        save_spam_settings()
        await update.message.reply_text(
            "✅ All targets cleared!\n"
            "🤖 Multi-Bot Sync: ✅ UPDATED",
            reply_markup=danger_settings_keyboard()
        )
        return DANGER_SETTING

    elif command == '📋 Select Groups':
        context.user_data.clear()
        await manage_groups(update, context)
        return GROUP_SELECTION

    elif command == '🎯 Target Spam Control':
        context.user_data.clear()
        await target_spam_control(update, context)
        return TARGET_SPAM_CONTROL

    elif command == '👀 View Targets':
        context.user_data.clear()
        if not SPAM_TARGETS:
            await update.message.reply_text("❌ No targets set.", reply_markup=danger_settings_keyboard())
            return DANGER_SETTING

        selected_targets = load_selected_targets()

        targets_text = "🎯 Current Targets:\n\n"
        for i, target in enumerate(SPAM_TARGETS, 1):
            if isinstance(target, dict):
                target_id = target['id']
                count = target.get('count', 1)
                spam_type = target.get('type', 'level')
                if spam_type == 'level':
                    level = target.get('level', '2')
                    level_name = USER_LEVELS.get(level, "Unknown")
                    type_info = f"📊 Level: {level_name}"
                else:
                    custom_msg = target.get('custom_message', '')
                    type_info = f"💬 Custom: {custom_msg[:30]}{'...' if len(custom_msg) > 30 else ''}"
            else:
                target_id = target
                count = 1
                type_info = "📊 Level: Normal"

            uid, user_data = await find_user_by_identifier(target_id, context, update.effective_chat.id)
            if user_data:
                bot_status = "🤖" if user_data.get('is_bot', False) else "👤"
                display_name = f"{bot_status} {user_data.get('first_name', 'Unknown')} (@{user_data.get('username', target_id)})"
            else:
                display_name = f"❓ {target_id}"

            selection_status = "✅ SELECTED" if target_id in selected_targets else "❌ NOT SELECTED"

            targets_text += f"{i}. {display_name}\n   🔢 {count} messages\n   {type_info}\n   {selection_status}\n\n"

        targets_text += f"🤖 Multi-Bot Sync: ✅ ENABLED"

        await update.message.reply_text(targets_text, reply_markup=danger_settings_keyboard())
        return DANGER_SETTING

    elif command == '📊 View Settings':
        context.user_data.clear()
        selected_groups = load_selected_groups()
        selected_targets = load_selected_targets()
        all_groups = get_bot_groups()

        groups_count = len(selected_groups) if selected_groups else len(all_groups)
        total_expected = 0

        targets_to_use = selected_targets if selected_targets else [target['id'] if isinstance(target, dict) else target for target in SPAM_TARGETS]

        for target in SPAM_TARGETS:
            if isinstance(target, dict):
                target_id = target['id']
                if target_id in targets_to_use:
                    total_expected += target.get('count', 1) * groups_count

        settings_text = (
            f"⚙️ Danger Settings Overview:\n\n"
            f"🌍 Total Groups: {len(all_groups)}\n"
            f"📋 Selected Groups: {len(selected_groups)}\n"
            f"🎯 Total Targets: {len(SPAM_TARGETS)}\n"
            f"✅ Selected Targets: {len(selected_targets)}\n"
            f"🤖 Active Bots: {len(BOT_APPLICATIONS)}\n"
            f"📨 Expected Messages: {total_expected}\n"
            f"🔄 Auto-Recoveries: {TOTAL_RECOVERIES}\n"
            f"🔗 Multi-Bot Sync: ✅ ACTIVE\n"
            f"⚡ Continuous Mode: ✅ ENABLED\n\n"
        )

        if SPAM_TARGETS:
            settings_text += "📋 Target Details:\n"
            for target in SPAM_TARGETS:
                if isinstance(target, dict):
                    target_id = target['id']
                    count = target.get('count', 1)
                    spam_type = target.get('type', 'level')

                    uid, user_data = await find_user_by_identifier(target_id, context, update.effective_chat.id)
                    if user_data:
                        bot_status = "🤖" if user_data.get('is_bot', False) else "👤"
                        display_name = f"{bot_status} {user_data.get('first_name', 'Unknown')}"
                    else:
                        display_name = f"❓ {target_id}"

                    selection_status = "✅" if target_id in selected_targets else "❌"

                    if spam_type == 'level':
                        level = target.get('level', '2')
                        level_name = USER_LEVELS.get(level, "Unknown")
                        settings_text += f"• {selection_status} {display_name}: {count}× {level_name} messages\n"
                    else:
                        custom_msg = target.get('custom_message', '')[:20]
                        settings_text += f"• {selection_status} {display_name}: {count}× custom messages\n"

        await update.message.reply_text(settings_text, reply_markup=danger_settings_keyboard())
        return DANGER_SETTING

    elif command == '🚀 Start All':
        context.user_data.clear()
        if not SPAM_TARGETS:
            await update.message.reply_text("❌ No targets set. Add targets first.", reply_markup=danger_settings_keyboard())
            return DANGER_SETTING

        selected_groups = load_selected_groups()
        all_groups = get_bot_groups()

        if selected_groups:
            groups_to_spam = [group for group in all_groups if group['id'] in selected_groups]
            if groups_to_spam:
                await update.message.reply_text(
                    f"🚀 Starting CONTINUOUS spam for ALL {len(SPAM_TARGETS)} targets in {len(groups_to_spam)} selected groups...\n"
                    f"🤖 Using {len(BOT_APPLICATIONS)} bots for maximum speed!\n"
                    f"🔁 Mode: CONTINUOUS UNTIL STOPPED",
                    reply_markup=danger_settings_keyboard()
                )
                task = asyncio.ensure_future(execute_unified_spam(update, context, groups_to_spam, None, "danger"))
                ACTIVE_SPAM_TASKS.add(task)
                task.add_done_callback(lambda t: ACTIVE_SPAM_TASKS.discard(t))
            else:
                await update.message.reply_text("❌ Selected groups not found!", reply_markup=danger_settings_keyboard())
        else:
            if all_groups:
                await update.message.reply_text(
                    f"🚀 Starting CONTINUOUS spam for ALL {len(SPAM_TARGETS)} targets in ALL {len(all_groups)} groups...\n"
                    f"🤖 Using {len(BOT_APPLICATIONS)} bots for maximum speed!\n"
                    f"🔁 Mode: CONTINUOUS UNTIL STOPPED",
                    reply_markup=danger_settings_keyboard()
                )
                task = asyncio.ensure_future(execute_unified_spam(update, context, all_groups, None, "danger"))
                ACTIVE_SPAM_TASKS.add(task)
                task.add_done_callback(lambda t: ACTIVE_SPAM_TASKS.discard(t))
            else:
                await update.message.reply_text("❌ No groups found!", reply_markup=danger_settings_keyboard())
        return DANGER_SETTING

    elif command == '🛑 Stop All':
        await update.message.reply_text("⏳ Stopping ALL spam...", reply_markup=danger_settings_keyboard())
        await stop_all_spam_completely(update, context)
        return DANGER_SETTING

    else:
        await update.message.reply_text("❌ Invalid command.", reply_markup=danger_settings_keyboard())
        return DANGER_SETTING

# ================================
# 🎮 GAME LEVELS SYSTEM - CONTINUOUS MODE
# ================================

async def game_levels(update: Update, context: CallbackContext):
    """🎮 Game levels management"""
    if not await validate_admin_access(update):
        return ConversationHandler.END

    context.user_data.clear()
    load_game_targets()

    global GAME_MODE_ACTIVE
    game_status = "🟢 ACTIVE" if GAME_MODE_ACTIVE else "🔴 INACTIVE"

    game_text = (
        f"🎮 Game Levels Management\n\n"
        f"🎯 Game Targets: {len(GAME_TARGETS)}\n"
        f"⚡ Game Mode: {game_status}\n"
        f"🤖 Multi-Bot Sync: ✅ ENABLED\n"
        f"🔁 Continuous Mode: ✅ ENABLED\n\n"
        f"🎯 Add Game Target - Kisi user ko game target banaye\n"
        f"✏️ Edit Game Target - Game target ka level/count change kare\n"
        f"🗑️ Remove Game Target - Game target hataaye\n"
        f"📋 View Game Targets - Sabhi game targets dekhe\n"
        f"🧹 Clear All Game Targets - Sabhi game targets hataaye\n"
        f"🚀 Start Game Mode - CONTINUOUS Game mode shuru kare\n"
        f"🛑 Stop Game Mode - Game mode band kare\n\n"
        f"💡 Game Mode: User jab bhi message karega, selected level ka reply milega!"
    )

    await update.message.reply_text(game_text, reply_markup=game_levels_keyboard())
    return GAME_LEVELS_MANAGEMENT

async def handle_game_levels_management(update: Update, context: CallbackContext):
    """🎮 Handle game levels management"""
    if not await validate_admin_access(update):
        return ConversationHandler.END

    command = update.message.text.strip()
    global GAME_MODE_ACTIVE

    if command == '↩️ Back to Main':
        context.user_data.clear()
        await back_to_main(update)
        return ConversationHandler.END

    if command == '🎯 Add Game Target':
        context.user_data.clear()
        await update.message.reply_text(
            "🎯 Enter username or user ID to add as game target:\n\n"
            "✅ BOTS & USERS dono ko game target kar sakte hain!\n"
            "• Username: @username\n"
            "• User ID: 123456789\n"
            "• Username without @: username",
            reply_markup=back_to_game_button()
        )
        return ADDING_GAME_TARGET

    elif command == '✏️ Edit Game Target':
        context.user_data.clear()
        if not GAME_TARGETS:
            await update.message.reply_text("❌ No game targets to edit.", reply_markup=game_levels_keyboard())
            return GAME_LEVELS_MANAGEMENT

        await update.message.reply_text(
            "✏️ Select game target to edit:\n\n"
            "Click on target to edit:",
            reply_markup=create_game_target_selection_keyboard(GAME_TARGETS)
        )
        return EDIT_GAME_TARGET_SELECTION

    elif command == '🗑️ Remove Game Target':
        context.user_data.clear()
        if not GAME_TARGETS:
            await update.message.reply_text("❌ No game targets to remove.", reply_markup=game_levels_keyboard())
            return GAME_LEVELS_MANAGEMENT

        selected_game_targets = context.user_data.get('selected_game_targets', [])
        await update.message.reply_text(
            "🗑️ Select game targets to remove:\n\n"
            "Click on targets to select/deselect (✅ = selected)\n"
            "Then click '🗑️ Remove Selected' to remove them",
            reply_markup=create_game_target_selection_keyboard(GAME_TARGETS, selected_game_targets)
        )
        return GAME_TARGET_SELECTION

    elif command == '📋 View Game Targets':
        context.user_data.clear()
        if not GAME_TARGETS:
            await update.message.reply_text("❌ No game targets set.", reply_markup=game_levels_keyboard())
            return GAME_LEVELS_MANAGEMENT

        targets_text = "🎮 Game Targets List:\n\n"
        for i, target in enumerate(GAME_TARGETS, 1):
            if isinstance(target, dict):
                target_id = target['id']
                level = target.get('level', '2')

                level_name = "🌈 ALL LEVELS COMBINED" if level == "combined" else USER_LEVELS.get(level, "Unknown")

                uid, user_data = await find_user_by_identifier(target_id, context, update.effective_chat.id)
                if user_data:
                    bot_status = "🤖" if user_data.get('is_bot', False) else "👤"
                    display_name = f"{bot_status} {user_data.get('first_name', 'Unknown')} (@{user_data.get('username', target_id)})"
                else:
                    display_name = f"❓ {target_id}"

                targets_text += f"{i}. {display_name}\n   📊 Level: {level_name}\n\n"

        await update.message.reply_text(targets_text, reply_markup=game_levels_keyboard())
        return GAME_LEVELS_MANAGEMENT

    elif command == '🧹 Clear All Game Targets':
        context.user_data.clear()
        GAME_TARGETS.clear()
        save_game_targets(GAME_TARGETS)
        GAME_MODE_ACTIVE = False
        await update.message.reply_text("✅ All game targets cleared! Game mode auto-stopped.", reply_markup=game_levels_keyboard())
        return GAME_LEVELS_MANAGEMENT

    elif command == '🚀 Start Game Mode':
        context.user_data.clear()
        if not GAME_TARGETS:
            await update.message.reply_text("❌ No game targets set. Add game targets first.", reply_markup=game_levels_keyboard())
            return GAME_LEVELS_MANAGEMENT

        GAME_MODE_ACTIVE = True
        await update.message.reply_text(
            f"✅ CONTINUOUS Game Mode Started!\n\n"
            f"🎯 {len(GAME_TARGETS)} game targets active\n"
            f"🤖 Multi-Bot Sync: ✅ ENABLED\n"
            f"🔁 Mode: CONTINUOUS UNTIL STOPPED\n"
            f"⚡ Ab ye users jab bhi message karenge, unhe selected level ka reply milega!",
            reply_markup=game_levels_keyboard()
        )
        return GAME_LEVELS_MANAGEMENT

    elif command == '🛑 Stop Game Mode':
        context.user_data.clear()
        GAME_MODE_ACTIVE = False
        await update.message.reply_text(
            "✅ Game Mode Stopped!\n\n"
            "🎯 Game targets ab reply nahi karenge",
            reply_markup=game_levels_keyboard()
        )
        return GAME_LEVELS_MANAGEMENT

    else:
        await game_levels(update, context)
        return GAME_LEVELS_MANAGEMENT

# ================================
# 🎯 TARGET DETECTION SYSTEM
# ================================

async def handle_target_detection(update: Update, context: CallbackContext):
    """🎯 Detect when target sends message and spam"""
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ['group', 'supergroup']:
        return

    user_id = user.id
    username = user.username
    first_name = user.first_name
    is_bot = user.is_bot

    update_user_info(user_id, username, first_name, is_bot)

    user_id_str = str(user_id)

    is_target = False
    target_data = None

    selected_targets = load_selected_targets()

    for target in SPAM_TARGETS:
        if isinstance(target, dict):
            if user_id_str == target['id']:
                if selected_targets and user_id_str not in selected_targets:
                    continue
                is_target = True
                target_data = target
                break
        elif user_id_str == target:
            if selected_targets and user_id_str not in selected_targets:
                continue
            is_target = True
            target_data = {'type': 'level', 'level': '2', 'count': 20}
            break

    if is_target and target_data:
        spam_type = target_data.get('type', 'level')
        count = min(target_data.get('count', 20), 20)

        if spam_type == 'level':
            level = target_data.get('level', '2')

            messages = []
            for i in range(count):
                message = get_rotated_message(level, user_id_str)
                if username:
                    final_message = f"@{username} {message}"
                else:
                    final_message = f"{first_name} {message}"
                messages.append(final_message)

            successful, total = await send_bulk_messages(context, chat.id, messages)
            print(f"⚡ Target {username or first_name} ko {successful}/{count} rotated messages bheje!")

        else:
            custom_message = target_data.get('custom_message', '')
            if custom_message:
                messages = []
                for i in range(count):
                    if username:
                        final_message = f"@{username} {custom_message}"
                    else:
                        final_message = f"{first_name} {custom_message}"
                    messages.append(final_message)

                successful, total = await send_bulk_messages(context, chat.id, messages)
                print(f"⚡ Target {username or first_name} ko {successful}/{count} custom messages bheje!")

# ================================
# 🎮 GAME TARGET DETECTION SYSTEM
# ================================

async def handle_game_target_detection(update: Update, context: CallbackContext):
    """🎯 Detect when game target sends message and reply"""
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ['group', 'supergroup']:
        return

    if not GAME_MODE_ACTIVE:
        return

    user_id = user.id
    username = user.username
    first_name = user.first_name
    is_bot = user.is_bot

    update_user_info(user_id, username, first_name, is_bot)

    user_id_str = str(user_id)

    for target in GAME_TARGETS:
        if isinstance(target, dict) and user_id_str == target['id']:
            level = target.get('level', '2')

            if level == "combined":
                lines = load_combined_level_lines()
            else:
                lines = load_level_lines(level)

            if lines:
                message = get_rotated_message(level, user_id_str)

                if username:
                    final_message = f"@{username} {message}"
                else:
                    final_message = f"{first_name} {message}"

                try:
                    await update.message.reply_text(final_message)
                    print(f"🎮 Game reply sent to {username or first_name} with level {level}")
                except Exception as e:
                    logger.error(f"❌ Error in game mode reply: {e}")
            break

# ================================
# 💬 GROUP MESSAGE HANDLERS
# ================================

async def handle_group_message(update: Update, context: CallbackContext):
    """💬 Handle group messages - SIRF TARGETS KO HI SPAM"""
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ['group', 'supergroup']:
        return

    if update.message.text and update.message.text.startswith('/'):
        return

    save_group_info(chat.id, chat.title)

    user_id = user.id
    username = user.username
    first_name = user.first_name
    is_bot = user.is_bot

    update_user_info(user_id, username, first_name, is_bot)

    if is_protected(user_id):
        return

    user_id_str = str(user_id)

    is_target = False
    target_data = None

    selected_targets = load_selected_targets()

    for target in SPAM_TARGETS:
        if isinstance(target, dict):
            if user_id_str == target['id']:
                if selected_targets and user_id_str not in selected_targets:
                    continue
                is_target = True
                target_data = target
                break
        elif user_id_str == target:
            if selected_targets and user_id_str not in selected_targets:
                continue
            is_target = True
            target_data = {'type': 'level', 'level': '2', 'count': 20}
            break

    if is_target and target_data:
        await handle_target_detection(update, context)
        return

    if GAME_MODE_ACTIVE:
        is_game_target = False
        game_target_data = None

        for target in GAME_TARGETS:
            if isinstance(target, dict):
                if user_id_str == target['id']:
                    is_game_target = True
                    game_target_data = target
                    break

        if is_game_target and game_target_data:
            await handle_game_target_detection(update, context)
            return

    if TRIGGER_MODE != "off" and TRIGGER_ACTIVE and TRIGGER_MODE in ["1", "2", "3", "4", "5", "6", "combined"]:
        if TRIGGER_MODE == "combined":
            lines = load_combined_level_lines()
        else:
            lines = load_level_lines(TRIGGER_MODE)

        if lines:
            abuse_line = random.choice(lines)
            if username:
                final_message = f"@{username} {abuse_line}"
            else:
                final_message = f"{first_name} {abuse_line}"

            try:
                await update.message.reply_text(final_message)
            except Exception as e:
                logger.error(f"Error in trigger mode: {e}")
        return

async def handle_bot_added(update: Update, context: CallbackContext):
    """🤖 Handle bot being added to a group"""
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                chat = update.effective_chat
                save_group_info(chat.id, chat.title)
                await update.message.reply_text("🤖 Bot added to group! Ready to Love! 😈")

async def handle_bot_removed(update: Update, context: CallbackContext):
    """❌ Handle bot being removed from a group"""
    if update.message and update.message.left_chat_member:
        if update.message.left_chat_member.id == context.bot.id:
            chat = update.effective_chat
            remove_group_info(chat.id)

# ================================
# 💬 MAIN MESSAGE HANDLER
# ================================

async def handle_private_buttons(update: Update, context: CallbackContext):
    """⌨️ Handle all button presses in private chat"""
    if not is_private_chat(update):
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not is_admin(user_id):
        if not context.user_data.get('warning_sent'):
            await update.message.reply_text(
                "❌ Teri aukat nahi hai is bot ko use karne ki! Nikal yaha se!",
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['warning_sent'] = True
        return

    username = update.effective_user.username
    first_name = update.effective_user.first_name
    is_bot = update.effective_user.is_bot

    update_user_info(user_id, username, first_name, is_bot)

    context.user_data.pop('warning_sent', None)

    # Handle multi-bot control buttons
    multi_bot_buttons = [
        '🤖 Bot Status', '🔄 Sync Now', '➕ Add Bot', '➖ Remove Bot',
        '🚀 Start All Bots Spam', '🛑 Stop All Bots', '📊 Multi-Bot Stats',
        '⚙️ Speed Settings', '🚀 24/7 Spam', '🛑 Stop 24/7'
    ]
    
    if text in multi_bot_buttons:
        await handle_multi_bot_control(update, context)
        return

    context.user_data.clear()

    if text == '👥 Users':
        await show_users(update, context)
    elif text == '📊 Stats':
        await show_stats(update, context)
    elif text == '📤 Upload':
        await upload_text(update, context)
    elif text == '📝 View Lines':
        await view_lines(update, context)
    elif text == '🔫 Trigger ALL':
        await trigger_all(update, context)
    elif text == '🛡️ Protected List':
        await protected_list(update, context)
    elif text == '🎯 Danger':
        await danger_settings(update, context)
    elif text == '🎮 Game Levels':
        await game_levels(update, context)
    elif text == '🤖 Multi-Bot Control':
        await multi_bot_control(update, context)
    elif text == '↩️ Back to Main':
        await back_to_main(update)
    else:
        await update.message.reply_text(
            "Please select an option from the main menu:",
            reply_markup=main_menu_keyboard()
        )

# ================================
# ❌ ERROR HANDLER
# ================================

async def error_handler(update: Update, context: CallbackContext):
    """❌ Error handler"""
    logger.error(f"Update {update} caused error {context.error}")

# ================================
# 🚀 MAIN FUNCTION - MULTI-BOT SETUP
# ================================

async def initialize_multi_bot():
    """🤖 Initialize multiple bots"""
    global BOT_APPLICATIONS
    
    print("🚀 Initializing Multi-Bot System...")
    
    # Load tokens from file
    load_bot_tokens()
    
    for i, token in enumerate(TOKENS, 1):
        if token == "YOUR_BOT_TOKEN_HERE":
            print(f"❌ Bot {i}: Token not configured, skipping...")
            continue
            
        try:
            app = Application.builder().token(token).build()
            BOT_APPLICATIONS.append(app)
            
            # Test bot connection
            me = await app.bot.get_me()
            print(f"✅ Bot {i}: @{me.username} - ONLINE")
            
        except Exception as e:
            print(f"❌ Bot {i}: Failed to initialize - {str(e)}")
    
    print(f"🤖 Multi-Bot System Ready: {len(BOT_APPLICATIONS)} bots active")

def main():
    """🚀 Main function"""
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initialize multi-bot system
        loop.run_until_complete(initialize_multi_bot())
        
        if not BOT_APPLICATIONS:
            print("❌ No bots initialized! Check your tokens.")
            return

        # Start multi-bot sync loop
        loop.create_task(multi_bot_sync_loop())

        # Use first bot as main application for commands
        main_application = BOT_APPLICATIONS[0]

        load_selected_groups()
        load_spam_settings()
        load_protected_users()
        load_selected_targets()
        load_game_targets()

        # 🔧 MULTI-BOT CONVERSATION HANDLER
        multi_bot_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Text('🤖 Multi-Bot Control'), multi_bot_control)],
            states={
                MULTI_BOT_CONTROL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_multi_bot_control)],
                ADD_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_token_input)],
                REMOVE_BOT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_removal)],
                SPEED_CONTROL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_speed_control)],
            },
            fallbacks=[CommandHandler("start", start)]
        )

        # Add other conversation handlers (danger, protected, game levels)...
        # [Previous conversation handlers remain the same]

        # 🔧 Add all handlers to main application
        main_application.add_handler(CommandHandler("start", start))
        main_application.add_handler(multi_bot_conv_handler)
        # Add other conversation handlers...

        # 🔧 Add group message handlers to ALL bots
        for app in BOT_APPLICATIONS:
            app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_bot_added))
            app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_bot_removed))
            app.add_handler(MessageHandler(filters.ChatType.GROUPS, handle_group_message))

        main_application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_buttons), group=0)

        main_application.add_error_handler(error_handler)

        # Start all bots
        print(f"🚀 Starting {len(BOT_APPLICATIONS)} bots with CONTINUOUS SPAM MODE...")
        
        # Start polling for all bots
        for i, app in enumerate(BOT_APPLICATIONS, 1):
            loop.create_task(app.run_polling())
            print(f"✅ Bot {i} polling started...")

        print("🤖 ALL BOTS ARE NOW RUNNING! Use /start in private chat to control them.")
        print("🚀 CONTINUOUS SPAM MODE ENABLED - All spam types will run until manually stopped!")
        
        # Keep main thread alive
        loop.run_forever()
        
    except KeyboardInterrupt:
        print("🛑 Bots stopped by user")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
