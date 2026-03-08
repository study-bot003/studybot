"""
╔══════════════════════════════════════════════════════════════╗
║       ˹𝚩𝛌𝛂𝛇𝛆 ꭙ 𝐒ᴛᴜᴅʏ𝐇ᴇʟᴘᴇʀ˼ — FUTURISTIC EDITION          ║
║        Powered by SambaNova DeepSeek + Telegram API          ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging
import asyncio
import aiohttp
import random
import datetime
import base64
from collections import defaultdict, deque
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatAction

# ════════════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ════════════════════════════════════════════════════════════
BOT_TOKEN         = "8364929501:AAGBHHYFgiQ-64-R21jdqFFobLnJLrj9CsI"
SAMBANOVA_API_KEY = "33990fcd-94a4-45bb-b785-a9dd93a7cc5a"
ADMIN_IDS         = [8568245247]

SAMBANOVA_BASE_URL = "https://api.sambanova.ai/v1/chat/completions"
MAX_MEMORY        = 40   # messages per user (user + assistant combined)

# Model names — verified on SambaNova cloud
MODELS = {
    "deepseek_v3":         "DeepSeek-V3-0324",
    "deepseek_r1":         "DeepSeek-R1",
    "deepseek_r1_distill": "DeepSeek-R1-Distill-Llama-70B",
}
DEFAULT_MODEL = "DeepSeek-V3-0324"

# Fallback chain — if primary 500s, try next
MODEL_FALLBACK = ["DeepSeek-V3-0324", "DeepSeek-R1-Distill-Llama-70B", "DeepSeek-R1"]

# ════════════════════════════════════════════════════════════
# 🧠 PER-USER CONVERSATION MEMORY  (last 40 messages)
# ════════════════════════════════════════════════════════════
# { user_id: deque([ {"role": "user"/"assistant", "content": "..."}, ... ]) }
user_memory: dict[int, deque] = defaultdict(lambda: deque(maxlen=MAX_MEMORY))

def get_history(user_id: int) -> list:
    return list(user_memory[user_id])

def add_to_history(user_id: int, role: str, content: str):
    user_memory[user_id].append({"role": role, "content": content})

def clear_history(user_id: int):
    user_memory[user_id].clear()

# ════════════════════════════════════════════════════════════
# 📚 RESOURCES
# ════════════════════════════════════════════════════════════
RESOURCES = {
    "books": [
        {"name": "HC Verma Physics",                 "url": "https://drive.google.com/drive/folders/1zi5sSNh2v0wF2O6Nx4JG6H84BsF1kgNP"},
        {"name": "Math Made Easy (Class 10)",        "url": "https://drive.google.com/file/d/1dvETKGiH_EYiH3Fl9Hftlo0EeI6guVgr/view"},
        {"name": "MS Chauhan Organic Chemistry",     "url": "https://drive.google.com/file/d/1RoJoghPR3z0cX6ysOK7vUEINdFLDJgTJ/view"},
        {"name": "Math Made Eajee (Sachin Sir)",     "url": "https://drive.google.com/file/d/1RK5VScgtnw3v8NRsQKSmCAamktVJZEB5/view"},
        {"name": "VK Jaiswal Inorganic Chemistry",   "url": "https://drive.google.com/file/d/1RsP_bm-_CMiIgpKiYDdwE6wh0BVxmJiF/view"},
        {"name": "N Awasthi Physical Chemistry",     "url": "https://drive.google.com/file/d/12u7I0JC__3vN9PQXqtMfbTNZVZCdtuzd/view"},
        {"name": "Cengage Series",                   "url": "https://drive.google.com/drive/folders/1J8cCmrSTcUZ1cbFMqvhZLzenPmcLhJyb"},
        {"name": "Eajee Physical Chem (Faisal Sir)", "url": "https://drive.google.com/drive/folders/1hHYyjBMJaBMhwVGamjQEUKtbYOg4pYJX"},
        {"name": "Irodov Problems",                  "url": "https://drive.google.com/drive/folders/1zLa_9k9U-7o-n4njA4MqSKQ0k3abMMxt"},
        {"name": "RD Sharma Objective",              "url": "https://drive.google.com/drive/folders/1p1ZWgpoFAxHTDrqouUEB0ayAobnNTg8g"},
        {"name": "A Das Gupta Mathematics",          "url": "https://drive.google.com/file/d/18Eqr9WXelWCEVYTkOKc1dx6Ew0leW3Sv/view"},
    ],
    "modules": [
        {"name": "Arjuna JEE Modules",  "url": "https://drive.google.com/drive/folders/1mZaT9E-zrbiAWqTTUH8dUudSGsQSAvt5"},
        {"name": "Lakshya JEE Modules", "url": "https://drive.google.com/drive/folders/1nGQxpBzgKn9OrtTP6Hhp-qaG9x1xR_-O"},
        {"name": "Prayas JEE Modules",  "url": "https://drive.google.com/drive/folders/1yPIRL9I_0zlaZjQTPS48Q_jEpJECEzlM"},
        {"name": "Allen Modules",       "url": "https://drive.google.com/drive/folders/1yjWqnH4fqGaCx0SW5jO3vqJ66sPCL_8i"},
        {"name": "Arjuna AIR Modules",  "url": "https://drive.google.com/drive/folders/175ZybDCg0pA8lT5Yy2htp2SAh6sussKA"},
    ],
    "pyqs": [
        {"name": "JEE Advanced PYQs",        "url": "https://drive.google.com/drive/folders/1omIy2ZmvVDrRUSlJ5SK60YtPKOvxyUv_"},
        {"name": "JEE Mains PYQs",           "url": "https://drive.google.com/drive/folders/1odsK6Erh70ezoT6q_KEUzvO2TFgI9FPq"},
        {"name": "NEET PYQ Biology (PW)",    "url": "https://drive.google.com/file/d/1dn-Fk6ZcIRP3VrnqNKhwRbR1KpRL9bvj/view"},
        {"name": "NEET PYQ Physics (PW)",    "url": "https://drive.google.com/file/d/1eFdF_Vv26d2QWApaFkIlkAlWxX3T62pk/view"},
        {"name": "NEET PYQ Chemistry (PW)",  "url": "https://drive.google.com/file/d/1dwJcMOF8Fd-MepULMMGVPKamVJCkUrz5/view"},
        {"name": "Disha PYQs",               "url": "https://drive.google.com/drive/folders/1z6m8mPjl7fGVGayXZ8FJGKXsSmY2mOfH"},
        {"name": "PW 7 Years PYQs",          "url": "https://drive.google.com/file/d/1IqHUB8yzrQh1_J-fn8DTUjAqw1OjSWCa/view"},
        {"name": "JEE Advanced Papers",      "url": "https://drive.google.com/drive/folders/1yqefoSrFhQq4Qd0m5RSHiDzxrIJCabpF"},
    ],
    "formulas": [
        {"name": "Complete Formula Sheet",     "url": "https://drive.google.com/drive/folders/181t1DrbwqTvcdmMpM4gADWcy2WZq90as"},
        {"name": "Physics Formulas",           "url": "https://drive.google.com/file/d/1GEgTz7GoWkkNpqQZOhqv5nMRdY_llY4M/view"},
        {"name": "SKC Class 12 (Saleem Sir)",  "url": "https://drive.google.com/file/d/17WIoAsCCa-oPuCzaoABZ244rsxMDIsN-/view"},
        {"name": "Periodic Table",             "url": "https://drive.google.com/file/d/1ISJ3kmo31qhThYnn-V9Y232HJpk9Avrd/view"},
        {"name": "SKC Class 11 (Saleem Sir)",  "url": "https://drive.google.com/file/d/1SMjJaeW18EGKTNeVAV7e4TRKYsaoNKLA/view"},
    ],
    "practice": [
        {"name": "JEE Super 500",             "url": "https://drive.google.com/drive/folders/1889awiS3SvegtZRhkDYRWmH4GtUunoZu"},
        {"name": "AITS Papers",               "url": "https://drive.google.com/drive/folders/1yfwfX-tkFElASIgRN1wkpS9n8V8cSfvY"},
        {"name": "NEET Ranker Test Series",   "url": "https://drive.google.com/drive/folders/1etM6sjeKtQga6H4J5cZdf74V8-rQ9mTw"},
        {"name": "Advanced Practice Sheets",  "url": "https://drive.google.com/drive/folders/1xj9Cd8FwmLkRxd10-janJs6MIq_i_9Lt"},
        {"name": "Short Notes",               "url": "https://drive.google.com/drive/folders/1ysbuQgLp7QmVmFtkjgr5lPLQDK8RY5ca"},
        {"name": "Math Black Book",           "url": "https://drive.google.com/drive/folders/1zP1RANMAz8XJqfc6-bEpNUYU6gz6sk2B"},
        {"name": "DC Pandey Physics",         "url": "https://drive.google.com/drive/folders/1y4Ja3jOFvqF8ct5IxDL3Z78RT6tyB__e"},
    ],
}

# ════════════════════════════════════════════════════════════
# 😤 NON-STUDY FILTER
# ════════════════════════════════════════════════════════════
GALI_RESPONSES = [
    "🖕 Bro, go study! Your exam won't pass itself.",
    "😤 This is a STUDY BOT, not an entertainment bot! Use /help.",
    "🤬 Only academics here. What topic do you need help with?",
    "💀 Wrong place for that. Go solve a JEE paper first, then talk.",
    "😒 Really? Use /ask for something useful instead.",
    "🙄 Stop that and ask something productive!",
]

NON_STUDY_KEYWORDS = [
    "girlfriend", "boyfriend", "sex", "porn", "tiktok", "reels",
    "gossip", "dating", "love story", "romance", "flirt", "netflix",
]

# ════════════════════════════════════════════════════════════
# 📊 STATS
# ════════════════════════════════════════════════════════════
bot_stats = {
    "total_users": set(),
    "total_queries": 0,
    "ai_calls": 0,
    "start_time": datetime.datetime.now(),
}

# ════════════════════════════════════════════════════════════
# 🔤 MONOSPACE MATH FONT CONVERTER
# Maps normal chars → mathematical monospace unicode
# ════════════════════════════════════════════════════════════
_MONO_MAP = {}
# Uppercase A-Z  →  𝙰-𝚉  (Mathematical Monospace Capital)
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _MONO_MAP[c] = chr(0x1D670 + i)
# Lowercase a-z  →  𝚊-𝚣
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _MONO_MAP[c] = chr(0x1D68A + i)
# Digits 0-9     →  𝟶-𝟿
for i, c in enumerate("0123456789"):
    _MONO_MAP[c] = chr(0x1D7F6 + i)

def to_mono(text: str) -> str:
    """Convert plain text to mathematical monospace unicode font."""
    return "".join(_MONO_MAP.get(ch, ch) for ch in text)

def mono_header(text: str) -> str:
    """Make a header line in monospace."""
    return to_mono(text)

# ════════════════════════════════════════════════════════════
# 🤖 SAMBANOVA AI CALL  (with fallback + memory)
# ════════════════════════════════════════════════════════════
SYSTEM_PROMPT = (
    "You are Blaze X StudyHelper — a powerful AI assistant that helps students with ANY academic subject. "
    "This includes Math, Physics, Chemistry, Biology, History, Geography, Economics, English, "
    "Computer Science, Coding, Programming, Literature, Political Science, Accountancy, and ALL other subjects. "
    "Also help with homework, assignments, essay writing, concept explanations, and exam prep for "
    "any exam: JEE, NEET, CBSE, ICSE, UPSC, SSC, CAT, SAT, boards, or any other. "
    "Answer in the same language the user uses: English, Hindi, or Hinglish. "
    "IMPORTANT: Do NOT use any markdown symbols (* _ ` # ~). Plain text ONLY. "
    "For math formulas use plain notation like: F = ma, E = mc^2, v^2 = u^2 + 2as. "
    "Use numbered lists and blank lines for structure. "
    "Remember the conversation history to give contextual, helpful answers."
)

async def _call_api(messages: list, model: str) -> tuple[int, str]:
    """Single API call. Returns (status_code, response_text)."""
    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  1500,
        "temperature": 0.4,
    }
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(
            SAMBANOVA_BASE_URL, headers=headers, json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw = data["choices"][0]["message"]["content"].strip()
                # Strip DeepSeek-R1 <think>...</think> reasoning block
                import re
                raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
                # Strip stray markdown symbols
                clean = raw.replace("**", "").replace("__", "").replace("```", "").replace("`", "")
                return 200, clean
            else:
                err = await resp.text()
                return resp.status, err[:300]


async def ask_ai(user_id: int, user_msg: str, system: str = None, use_history: bool = True) -> str:
    """
    Call SambaNova with per-user conversation history.
    Tries MODEL_FALLBACK chain on 500 errors.
    """
    sys_prompt = system or SYSTEM_PROMPT

    # Build messages list
    messages = [{"role": "system", "content": sys_prompt}]
    if use_history:
        messages += get_history(user_id)
    messages.append({"role": "user", "content": user_msg})

    # Get preferred model for this user
    model = user_memory.get  # placeholder — resolved below
    # We store preferred model in a separate dict
    preferred = _user_model.get(user_id, DEFAULT_MODEL)

    # Build fallback list starting from preferred
    fallback_order = [preferred] + [m for m in MODEL_FALLBACK if m != preferred]

    last_error = "Unknown error"
    for model in fallback_order:
        try:
            status, text = await _call_api(messages, model)
            if status == 200:
                bot_stats["ai_calls"] += 1
                # Save to memory
                if use_history:
                    add_to_history(user_id, "user",      user_msg)
                    add_to_history(user_id, "assistant", text)
                return text
            else:
                last_error = f"[{model}] HTTP {status}"
                logging.warning(f"API {status} on model {model}, trying next...")
                continue
        except asyncio.TimeoutError:
            last_error = f"[{model}] Timeout"
            continue
        except Exception as e:
            last_error = f"[{model}] {str(e)}"
            continue

    return f"⚠️ All models failed. Last error: {last_error}\nPlease try again in a moment."


# Per-user preferred model store
_user_model: dict[int, str] = {}

def get_user_model(user_id: int) -> str:
    return _user_model.get(user_id, DEFAULT_MODEL)

def set_user_model(user_id: int, model: str):
    _user_model[user_id] = model

# ════════════════════════════════════════════════════════════
# 🔧 SAFE SEND HELPERS  (never crash on long/special text)
# ════════════════════════════════════════════════════════════
async def safe_reply(message, text: str, reply_markup=None):
    try:
        await message.reply_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await message.reply_text(text[:4000], reply_markup=reply_markup)
        except Exception as e:
            await message.reply_text(f"Error sending response: {e}")

async def safe_edit(msg, text: str, reply_markup=None):
    try:
        await msg.edit_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await msg.edit_text(text[:4000], reply_markup=reply_markup)
        except Exception:
            pass

# ════════════════════════════════════════════════════════════
# 🎨 KEYBOARDS
# ════════════════════════════════════════════════════════════
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Books",     callback_data="cat_books"),
            InlineKeyboardButton("📂 Modules",   callback_data="cat_modules"),
        ],
        [
            InlineKeyboardButton("📝 PYQs",      callback_data="cat_pyqs"),
            InlineKeyboardButton("🧮 Formulas",  callback_data="cat_formulas"),
        ],
        [
            InlineKeyboardButton("🏋️ Practice",  callback_data="cat_practice"),
            InlineKeyboardButton("🤖 AI Models", callback_data="show_models"),
        ],
        [
            InlineKeyboardButton("📖 Help",      callback_data="show_help"),
            InlineKeyboardButton("📊 Stats",     callback_data="show_stats"),
        ],
    ])

def resource_keyboard(category: str):
    items = RESOURCES.get(category, [])
    rows = [[InlineKeyboardButton(f"🔗 {item['name']}", url=item["url"])] for item in items]
    rows.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)

def model_select_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ DeepSeek-V3-0324  (Fast + Smart)",  callback_data="model_deepseek_v3")],
        [InlineKeyboardButton("🧠 DeepSeek-R1  (Deep Reasoning)",     callback_data="model_deepseek_r1")],
        [InlineKeyboardButton("🦙 DeepSeek-R1-Distill-Llama-70B",     callback_data="model_deepseek_r1_distill")],
        [InlineKeyboardButton("🔙 Back",                              callback_data="main_menu")],
    ])

def menu_btn():
    """Small menu button — appended only to resource/category messages."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Live Stats",   callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users",        callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🤖 Model",        callback_data="admin_model"),
            InlineKeyboardButton("📢 Broadcast",    callback_data="admin_broadcast_info"),
        ],
        [
            InlineKeyboardButton("🖥️ System Info",  callback_data="admin_sysinfo"),
            InlineKeyboardButton("🗑️ Clear Memory", callback_data="admin_clearmem"),
        ],
        [InlineKeyboardButton("❌ Close",           callback_data="main_menu")],
    ])

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def uptime_str() -> str:
    d = datetime.datetime.now() - bot_stats["start_time"]
    h = int(d.total_seconds() // 3600)
    m = int((d.total_seconds() % 3600) // 60)
    s = int(d.total_seconds() % 60)
    return f"{h}h {m}m {s}s"

SEP = "─" * 32   # separator line

# ════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_stats["total_users"].add(user.id)
    name = to_mono(user.first_name[:20])
    text = (
    "˹𝚩𝛌𝛂𝛇𝛆 ꭙ 𝐒ᴛᴜᴅʏ𝐇ᴇʟᴘᴇʀ˼ 🚀\n"
    "𝚈𝚘𝚞𝚛 𝙰𝙸-𝙿𝚘𝚠𝚎𝚛𝚎𝚍 𝚂𝚝𝚞𝚍𝚢 𝙲𝚘𝚖𝚙𝚊𝚗𝚒𝚘𝚗\n\n"
    "⚡ 𝚆𝚎𝚕𝚌𝚘𝚖𝚎! 👋\n\n"
    "📡 𝙰𝚕𝚠𝚊𝚢𝚜 𝚘𝚗𝚕𝚒𝚗𝚎. 𝙰𝚕𝚠𝚊𝚢𝚜 𝚛𝚎𝚊𝚍𝚢.\n\n"
    "──────────────────────────────────\n"
    "𝚀𝚄𝙸𝙲𝙺 𝙲𝙾𝙼𝙼𝙰𝙽𝙳𝚂 🔥\n"
    "──────────────────────────────────\n"
    "/𝚊𝚜𝚔 ➤ 𝙰𝚜𝚔 𝙰𝙸 𝚊𝚗𝚢𝚝𝚑𝚒𝚗𝚐\n"
    "/𝚙𝚢𝚚 ➤ 𝙿𝚈𝚀 𝚊𝚗𝚊𝚕𝚢𝚜𝚒𝚜 & 𝚙𝚊𝚝𝚝𝚎𝚛𝚗𝚜\n"
    "/𝚙𝚍𝚏 ➤ 𝙵𝚒𝚗𝚍 𝙿𝙳𝙵 𝚛𝚎𝚜𝚘𝚞𝚛𝚌𝚎𝚜\n"
    "/𝚎𝚡𝚙𝚕𝚊𝚒𝚗 ➤ 𝙴𝚡𝚙𝚕𝚊𝚒𝚗 𝚊𝚗𝚢 𝚌𝚘𝚗𝚌𝚎𝚙𝚝\n"
    "/𝚏𝚘𝚛𝚖𝚞𝚕𝚊 ➤ 𝙶𝚎𝚝 𝚏𝚘𝚛𝚖𝚞𝚕𝚊𝚜\n"
    "/𝚖𝚘𝚍𝚎𝚕 ➤ 𝚂𝚠𝚒𝚝𝚌𝚑 𝙰𝙸 𝚖𝚘𝚍𝚎𝚕\n"
    "/𝚌𝚕𝚎𝚊𝚛 ➤ 𝙲𝚕𝚎𝚊𝚛 𝚌𝚑𝚊𝚝 𝚖𝚎𝚖𝚘𝚛𝚢\n"
    "/𝚑𝚎𝚕𝚙 ➤ 𝙵𝚞𝚕𝚕 𝚌𝚘𝚖𝚖𝚊𝚗𝚍 𝚕𝚒𝚜𝚝\n"
    "──────────────────────────────────\n\n"
    "👇 𝚄𝚜𝚎 𝚝𝚑𝚎 𝚖𝚎𝚗𝚞 𝚋𝚎𝚕𝚘𝚠 𝚝𝚘 𝚐𝚎𝚝 𝚜𝚝𝚊𝚛𝚝𝚎𝚍!"
)
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        f"╔══════════════════════════════════╗\n"
        f"║  {to_mono('HELP MENU')}  📖              ║\n"
        f"╚══════════════════════════════════╝\n\n"
        f"{to_mono('AI COMMANDS')}\n"
        f"{SEP}\n"
        "/ask <question>     ➤  Ask anything\n"
        "/pyq <topic>        ➤  PYQ patterns\n"
        "/explain <concept>  ➤  Explain concept\n"
        "/formula <topic>    ➤  Get formulas\n"
        "/model              ➤  Switch AI model\n"
        "/clear              ➤  Clear chat memory\n\n"
        f"{to_mono('RESOURCE COMMANDS')}\n"
        f"{SEP}\n"
        "/books    ➤  Books library\n"
        "/modules  ➤  Study modules\n"
        "/pyqs     ➤  PYQ collections\n"
        "/formulas ➤  Formula sheets\n"
        "/practice ➤  Practice sets\n"
        "/pdf <topic> ➤ Search PDFs\n\n"
        f"{to_mono('INFO')}\n"
        f"{SEP}\n"
        "/stats  ➤  Bot statistics\n"
        "/start  ➤  Restart bot\n\n"
        f"{to_mono('ADMIN ONLY')}\n"
        f"{SEP}\n"
        "/admin           ➤  Admin panel\n"
        "/broadcast <msg> ➤  Message all users\n\n"
        "💡 TIP: Just send a message — AI replies with full context memory!"
    )
    await update.message.reply_text(text)


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args)
    if not query:
        await update.message.reply_text(
            "❓ Please provide a question!\n"
            "Usage: /ask What is Newton's second law?"
        )
        return
    uid = update.effective_user.id
    bot_stats["total_users"].add(uid)
    bot_stats["total_queries"] += 1
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🤖 {to_mono('Thinking')}... ⏳")
    answer = await ask_ai(uid, query)
    result = (
        f"🎯 {to_mono('QUESTION')}\n"
        f"{SEP}\n"
        f"{query}\n\n"
        f"🤖 {to_mono('ANSWER')}\n"
        f"{SEP}\n"
        f"{answer}"
    )
    await safe_edit(msg, result)


async def cmd_pyq(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args)
    if not query:
        await update.message.reply_text(
            "📝 Please provide a topic!\nUsage: /pyq Rotational Motion"
        )
        return
    uid = update.effective_user.id
    bot_stats["total_queries"] += 1
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"📝 {to_mono('Analyzing PYQ patterns')}... ⏳")
    system = (
        "You are a PYQ and exam expert. Plain text only, no markdown symbols. "
        "For the topic give: 1) Key PYQ patterns 2) Important question types "
        "3) Years this topic appeared heavily 4) Tips to score. Be exam-focused."
    )
    answer = await ask_ai(uid, f"PYQ analysis for: {query}", system=system, use_history=False)
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 JEE Advanced PYQs", url="https://drive.google.com/drive/folders/1omIy2ZmvVDrRUSlJ5SK60YtPKOvxyUv_"),
            InlineKeyboardButton("📁 JEE Mains PYQs",    url="https://drive.google.com/drive/folders/1odsK6Erh70ezoT6q_KEUzvO2TFgI9FPq"),
        ],
    ])
    result = (
        f"📝 {to_mono('PYQ ANALYSIS')}: {query}\n"
        f"{SEP}\n\n"
        f"{answer}"
    )
    await safe_edit(msg, result, kb)


async def cmd_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args).lower()
    if not query:
        await update.message.reply_text(
            "📄 Provide a topic!\nUsage: /pdf organic chemistry"
        )
        return
    uid = update.effective_user.id
    bot_stats["total_queries"] += 1
    matched = []
    for items in RESOURCES.values():
        for item in items:
            if any(kw in item["name"].lower() for kw in query.split()):
                matched.append(item)
    if matched:
        rows = [[InlineKeyboardButton(f"📄 {m['name']}", url=m["url"])] for m in matched[:8]]
        await update.message.reply_text(
            f"🔍 {to_mono('PDFs found for')}: {query}",
            reply_markup=InlineKeyboardMarkup(rows)
        )
    else:
        await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        answer = await ask_ai(
            uid,
            f"Best books and PDFs for studying {query}. Plain text only.",
            use_history=False
        )
        await safe_reply(
            update.message,
            f"🔍 {to_mono('AI Recommendations for')}: {query}\n{SEP}\n\n{answer}"
        )


async def cmd_explain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args)
    if not query:
        await update.message.reply_text(
            "💡 What should I explain?\nUsage: /explain Photoelectric Effect"
        )
        return
    uid = update.effective_user.id
    bot_stats["total_queries"] += 1
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🧠 {to_mono('Preparing explanation')}... ⏳")
    system = (
        "You are a brilliant teacher for all academic subjects. Plain text only, no markdown symbols. "
        "Explain clearly: 1) Simple explanation 2) Key formulas in plain notation "
        "3) Important points 4) Common mistakes 5) Exam tips."
    )
    answer = await ask_ai(uid, f"Explain this concept: {query}", system=system)
    result = (
        f"💡 {to_mono('CONCEPT')}: {query}\n"
        f"{SEP}\n\n"
        f"{answer}"
    )
    await safe_edit(msg, result)


async def cmd_formula(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args)
    if not query:
        await update.message.reply_text(
            "🧮 Which formulas?\nUsage: /formula kinematics"
        )
        return
    uid = update.effective_user.id
    bot_stats["total_queries"] += 1
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🧮 {to_mono('Fetching formulas')}... ⏳")
    system = (
        "You are a formula expert for all academic subjects. Plain text ONLY, no markdown. "
        "List all important formulas: Formula name: expression — when to use."
    )
    answer = await ask_ai(uid, f"All formulas for: {query}", system=system, use_history=False)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Full Formula Sheets", url="https://drive.google.com/drive/folders/181t1DrbwqTvcdmMpM4gADWcy2WZq90as")
    ]])
    result = (
        f"🧮 {to_mono('FORMULAS')}: {query}\n"
        f"{SEP}\n\n"
        f"{answer}"
    )
    await safe_edit(msg, result, kb)


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    count = len(user_memory[uid])
    clear_history(uid)
    await update.message.reply_text(
        f"🗑️ {to_mono('Memory cleared!')} {count} messages removed.\n"
        "Starting fresh conversation."
    )


async def cmd_books(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📚 {to_mono('BOOKS LIBRARY')}\nClick to access:",
        reply_markup=resource_keyboard("books")
    )

async def cmd_modules(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📂 {to_mono('STUDY MODULES')}\nClick to access:",
        reply_markup=resource_keyboard("modules")
    )

async def cmd_pyqs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📝 {to_mono('PYQ COLLECTIONS')}\nClick to access:",
        reply_markup=resource_keyboard("pyqs")
    )

async def cmd_formulas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🧮 {to_mono('FORMULA SHEETS')}\nClick to access:",
        reply_markup=resource_keyboard("formulas")
    )

async def cmd_practice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏋️ {to_mono('PRACTICE SETS')}\nClick to access:",
        reply_markup=resource_keyboard("practice")
    )

async def cmd_model(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    current = get_user_model(uid)
    text = (
        f"╔══════════════════════════════╗\n"
        f"║  {to_mono('SELECT AI MODEL')}  🤖      ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"Current: {to_mono(current)}\n\n"
        f"{to_mono('DeepSeek-V3-0324')}\n"
        "  ➤ Fastest, best for all topics\n\n"
        f"{to_mono('DeepSeek-R1')}\n"
        "  ➤ Deep reasoning, hard problems\n\n"
        f"{to_mono('DeepSeek-R1-Distill-Llama-70B')}\n"
        "  ➤ Balanced speed + reasoning\n"
    )
    await update.message.reply_text(text, reply_markup=model_select_keyboard())

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total_mem = sum(len(v) for v in user_memory.values())
    text = (
        f"╔══════════════════════════════╗\n"
        f"║  {to_mono('BOT STATS')}  📊           ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"  {to_mono('Total Users')}   :  {len(bot_stats['total_users'])}\n"
        f"  {to_mono('Total Queries')} :  {bot_stats['total_queries']}\n"
        f"  {to_mono('AI Calls')}      :  {bot_stats['ai_calls']}\n"
        f"  {to_mono('Memory Msgs')}   :  {total_mem}\n"
        f"  {to_mono('Uptime')}        :  {uptime_str()}\n"
        f"  {to_mono('AI Engine')}     :  SambaNova DeepSeek\n"
        f"  {to_mono('Status')}        :  Online\n\n"
        f"  Started: {bot_stats['start_time'].strftime('%d %b %Y, %H:%M')}"
    )
    await update.message.reply_text(text)

# ════════════════════════════════════════════════════════════
# 🔑 ADMIN
# ════════════════════════════════════════════════════════════

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Access denied! You are not an admin.")
        return
    total_mem = sum(len(v) for v in user_memory.values())
    text = (
        f"╔══════════════════════════════════════╗\n"
        f"║  {to_mono('ADMIN CONTROL PANEL')}  🔐     ║\n"
        f"╚══════════════════════════════════════╝\n\n"
        f"  👑 {to_mono('Welcome, Administrator!')}\n\n"
        f"  {SEP}\n"
        f"  {to_mono('LIVE STATS')}\n"
        f"  {SEP}\n"
        f"  Users        :  {len(bot_stats['total_users'])}\n"
        f"  Queries      :  {bot_stats['total_queries']}\n"
        f"  AI Calls     :  {bot_stats['ai_calls']}\n"
        f"  Memory Msgs  :  {total_mem}\n"
        f"  Uptime       :  {uptime_str()}\n"
        f"  Status       :  Online ✅\n"
        f"  {SEP}\n\n"
        "  Use buttons below to manage:"
    )
    await update.message.reply_text(text, reply_markup=admin_keyboard())


async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Only admins can broadcast!")
        return
    msg_text = " ".join(ctx.args)
    if not msg_text:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return
    broadcast_text = (
        f"📢 {to_mono('BOT ANNOUNCEMENT')}\n"
        f"{SEP}\n\n"
        f"{msg_text}\n\n"
        f"{SEP}\n"
        "— Blaze X StudyHelper"
    )
    sent = failed = 0
    for uid in list(bot_stats["total_users"]):
        try:
            await ctx.bot.send_message(uid, broadcast_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"✅ Broadcast complete!\nSent: {sent}  |  Failed: {failed}"
    )

# ════════════════════════════════════════════════════════════
# 🖼️  PHOTO / IMAGE HANDLER
# ════════════════════════════════════════════════════════════

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot_stats["total_users"].add(uid)
    bot_stats["total_queries"] += 1

    caption = update.message.caption or ""

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🖼️ {to_mono('Analyzing image')}... ⏳")

    try:
        # Download highest resolution photo
        photo = update.message.photo[-1]
        tg_file = await ctx.bot.get_file(photo.file_id)

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(tg_file.file_path) as resp:
                img_bytes = await resp.read()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        user_prompt = caption if caption else "Analyze this image carefully. If it contains a question, problem, or exercise — solve it step by step. If it contains notes or a diagram — explain it clearly."

        headers = {
            "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model": "Llama-4-Maverick-17B-128E-Instruct",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Blaze X StudyHelper — an expert AI tutor that solves academic problems from images. "
                        "Carefully read all text, equations, and diagrams visible in the image. "
                        "Provide clear step-by-step solutions for any problems. "
                        "Plain text only — absolutely no markdown symbols (* _ ` # ~). "
                        "Answer in the same language the user uses."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.3,
        }

        connector2 = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector2) as session:
            async with session.post(
                SAMBANOVA_BASE_URL, headers=headers, json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bot_stats["ai_calls"] += 1
                    import re
                    raw = data["choices"][0]["message"]["content"].strip()
                    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
                    answer = raw.replace("**", "").replace("__", "").replace("```", "").replace("`", "")

                    add_to_history(uid, "user", f"[Image sent]{(': ' + caption) if caption else ''}")
                    add_to_history(uid, "assistant", answer)

                    result = (
                        f"🖼️ {to_mono('IMAGE ANALYSIS')}\n"
                        f"{SEP}\n\n"
                        f"{answer}"
                    )
                    await safe_edit(msg, result)
                else:
                    err = await resp.text()
                    await safe_edit(msg, f"⚠️ Vision error {resp.status}\n{err[:200]}")

    except Exception as e:
        await safe_edit(msg, f"❌ Could not process image: {str(e)}\nTry sending your question as text.")



# ════════════════════════════════════════════════════════════
# 💬 FREE-TEXT MESSAGE HANDLER
# ════════════════════════════════════════════════════════════

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid  = update.effective_user.id
    bot_stats["total_users"].add(uid)

    if any(kw in text.lower() for kw in NON_STUDY_KEYWORDS):
        await update.message.reply_text(random.choice(GALI_RESPONSES))
        return

    bot_stats["total_queries"] += 1
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    answer = await ask_ai(uid, text)
    await safe_reply(update.message, answer)

# ════════════════════════════════════════════════════════════
# 🔘 CALLBACK HANDLER
# ════════════════════════════════════════════════════════════

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    uid  = q.from_user.id
    await q.answer()

    if data == "main_menu":
        text = (
            f"╔══════════════════════════════════════╗\n"
            f"║  ˹𝚩𝛌𝛂𝛇𝛆 ꭙ 𝐒ᴛᴜᴅʏ𝐇ᴇʟᴘᴇʀ˼  🚀         ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            "Select a category:"
        )
        await safe_edit(q.message, text, main_menu_keyboard())

    elif data.startswith("cat_"):
        cat = data.replace("cat_", "")
        titles = {
            "books":    f"📚 {to_mono('BOOKS LIBRARY')}",
            "modules":  f"📂 {to_mono('STUDY MODULES')}",
            "pyqs":     f"📝 {to_mono('PYQ COLLECTIONS')}",
            "formulas": f"🧮 {to_mono('FORMULA SHEETS')}",
            "practice": f"🏋️ {to_mono('PRACTICE SETS')}",
        }
        await safe_edit(
            q.message,
            f"{titles.get(cat, cat)}\n\nClick any link to access:",
            resource_keyboard(cat)
        )

    elif data == "show_models":
        current = get_user_model(uid)
        await safe_edit(
            q.message,
            f"🤖 {to_mono('SELECT AI MODEL')}\n\nCurrent: {to_mono(current)}\n\nChoose:",
            model_select_keyboard()
        )

    elif data == "show_help":
        await safe_edit(
            q.message,
            f"📖 {to_mono('COMMANDS')}\n\n"
            "AI: /ask /pyq /explain /formula /pdf /model /clear\n"
            "Resources: /books /modules /pyqs /formulas /practice\n"
            "Info: /stats /start /help\n"
            "Admin: /admin /broadcast",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        )

    elif data == "show_stats":
        total_mem = sum(len(v) for v in user_memory.values())
        await safe_edit(
            q.message,
            f"📊 {to_mono('BOT STATS')}\n\n"
            f"Users    : {len(bot_stats['total_users'])}\n"
            f"Queries  : {bot_stats['total_queries']}\n"
            f"AI Calls : {bot_stats['ai_calls']}\n"
            f"Memory   : {total_mem} msgs\n"
            f"Uptime   : {uptime_str()}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        )

    elif data.startswith("model_"):
        key = data.replace("model_", "")
        model_name = MODELS.get(key, DEFAULT_MODEL)
        set_user_model(uid, model_name)
        await safe_edit(
            q.message,
            f"✅ {to_mono('Model changed!')}\n\nNow using:\n{to_mono(model_name)}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        )

    # ── Admin callbacks ──────────────────────────────────
    elif data == "admin_stats" and is_admin(uid):
        total_mem = sum(len(v) for v in user_memory.values())
        await safe_edit(
            q.message,
            f"╔══════════════════════════════════════╗\n"
            f"║  {to_mono('DETAILED STATS')}  📊         ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"  Users        :  {len(bot_stats['total_users'])}\n"
            f"  Queries      :  {bot_stats['total_queries']}\n"
            f"  AI API Calls :  {bot_stats['ai_calls']}\n"
            f"  Memory Msgs  :  {total_mem}\n"
            f"  Uptime       :  {uptime_str()}\n"
            f"  Started      :  {bot_stats['start_time'].strftime('%d %b %Y %H:%M')}\n"
            f"  Default Model:  {DEFAULT_MODEL}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]])
        )

    elif data == "admin_users" and is_admin(uid):
        await safe_edit(
            q.message,
            f"👥 {to_mono('USER STATS')}\n\n"
            f"Total registered users: {len(bot_stats['total_users'])}\n"
            f"Active memory sessions: {len([v for v in user_memory.values() if len(v) > 0])}\n"
            f"Total memory messages : {sum(len(v) for v in user_memory.values())}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]])
        )

    elif data == "admin_model" and is_admin(uid):
        await safe_edit(
            q.message,
            f"🤖 {to_mono('Change Default Model')}\nCurrent: {DEFAULT_MODEL}",
            model_select_keyboard()
        )

    elif data == "admin_broadcast_info" and is_admin(uid):
        await safe_edit(
            q.message,
            f"📢 {to_mono('Broadcast')}\n\nUsage:\n/broadcast Your message here",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]])
        )

    elif data == "admin_sysinfo" and is_admin(uid):
        await safe_edit(
            q.message,
            f"🖥️ {to_mono('SYSTEM INFO')}\n\n"
            f"  Bot Name     :  Blaze X StudyHelper\n"
            f"  AI Provider  :  SambaNova\n"
            f"  Models       :  DeepSeek-V3, R1, R1-Distill\n"
            f"  Memory/User  :  {MAX_MEMORY} messages\n"
            f"  Fallback     :  Auto model fallback on 500\n"
            f"  Framework    :  python-telegram-bot v21\n"
            f"  Status       :  Running",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]])
        )

    elif data == "admin_clearmem" and is_admin(uid):
        total_before = sum(len(v) for v in user_memory.values())
        for k in list(user_memory.keys()):
            user_memory[k].clear()
        await safe_edit(
            q.message,
            f"🗑️ {to_mono('All memory cleared!')}\n\n{total_before} messages removed from all users.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]])
        )

    elif data == "back_admin" and is_admin(uid):
        total_mem = sum(len(v) for v in user_memory.values())
        await safe_edit(
            q.message,
            f"╔══════════════════════════════════════╗\n"
            f"║  {to_mono('ADMIN CONTROL PANEL')}  🔐     ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"  Users    :  {len(bot_stats['total_users'])}\n"
            f"  Queries  :  {bot_stats['total_queries']}\n"
            f"  Memory   :  {total_mem} msgs\n"
            f"  Uptime   :  {uptime_str()}\n"
            f"  Status   :  Online ✅",
            admin_keyboard()
        )

# ════════════════════════════════════════════════════════════
# 🚀 STARTUP
# ════════════════════════════════════════════════════════════

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start",     "Start the bot"),
        BotCommand("help",      "Help & commands"),
        BotCommand("ask",       "Ask AI anything"),
        BotCommand("pyq",       "PYQ analysis"),
        BotCommand("explain",   "Explain a concept"),
        BotCommand("formula",   "Get formulas"),
        BotCommand("pdf",       "Search PDF resources"),
        BotCommand("books",     "Books library"),
        BotCommand("modules",   "Study modules"),
        BotCommand("pyqs",      "PYQ collections"),
        BotCommand("formulas",  "Formula sheets"),
        BotCommand("practice",  "Practice sets"),
        BotCommand("model",     "Change AI model"),
        BotCommand("clear",     "Clear chat memory"),
        BotCommand("stats",     "Bot statistics"),
        BotCommand("admin",     "Admin panel"),
        BotCommand("broadcast", "Broadcast message (Admin)"),
    ])
    print("✅ Commands registered!")


def main():
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s",
        level=logging.INFO
    )
    print("╔══════════════════════════════════════════╗")
    print("║  ˹𝚩𝛌𝛂𝛇𝛆 ꭙ 𝐒ᴛᴜᴅʏ𝐇ᴇʟᴘᴇʀ˼  STARTING...   ║")
    print("║     Powered by SambaNova DeepSeek        ║")
    print("╚══════════════════════════════════════════╝")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("ask",       cmd_ask))
    app.add_handler(CommandHandler("pyq",       cmd_pyq))
    app.add_handler(CommandHandler("pdf",       cmd_pdf))
    app.add_handler(CommandHandler("explain",   cmd_explain))
    app.add_handler(CommandHandler("formula",   cmd_formula))
    app.add_handler(CommandHandler("clear",     cmd_clear))
    app.add_handler(CommandHandler("books",     cmd_books))
    app.add_handler(CommandHandler("modules",   cmd_modules))
    app.add_handler(CommandHandler("pyqs",      cmd_pyqs))
    app.add_handler(CommandHandler("formulas",  cmd_formulas))
    app.add_handler(CommandHandler("practice",  cmd_practice))
    app.add_handler(CommandHandler("model",     cmd_model))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("admin",     cmd_admin))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🟢 Bot is LIVE!\n")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()