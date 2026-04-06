import os
import sqlite3
import logging
from datetime import datetime
from urllib.parse import quote

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import UserNotParticipant

# =========================
# CONFIG
# =========================
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# Optional: force users to join a channel before getting files
# Example: FORCE_SUB_CHANNEL = "@Shivam_Animes"
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "").strip()

# Owner/admin IDs separated by commas
# Example: OWNER_IDS=123456789,987654321
OWNER_IDS = {
    int(x.strip())
    for x in os.getenv("OWNER_IDS", "").split(",")
    if x.strip().isdigit()
}

BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip()  # optional, auto-detected if empty

DB_NAME = "fileshare_bot.db"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("FileShareBot")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_code TEXT UNIQUE,
    file_id TEXT NOT NULL,
    file_unique_id TEXT NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    file_type TEXT,
    caption TEXT,
    uploaded_by INTEGER,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    joined_at TEXT,
    last_seen TEXT
)
""")

conn.commit()

# =========================
# APP
# =========================
app = Client(
    "fileshare_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================
# HELPERS
# =========================
def save_user(msg: Message):
    user = msg.from_user
    if not user:
        return

    now = datetime.utcnow().isoformat()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("""
            UPDATE users
            SET first_name = ?, username = ?, last_seen = ?
            WHERE user_id = ?
        """, (
            user.first_name or "",
            user.username or "",
            now,
            user.id
        ))
    else:
        cur.execute("""
            INSERT INTO users (user_id, first_name, username, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.first_name or "",
            user.username or "",
            now,
            now
        ))
    conn.commit()


def make_code(file_unique_id: str, row_id: int) -> str:
    return f"{file_unique_id[:12]}_{row_id}"


def get_file_info(message: Message):
    """
    Returns:
    {
        "file_id": ...,
        "file_unique_id": ...,
        "file_name": ...,
        "file_size": ...,
        "file_type": ...
    }
    """
    media_map = [
        ("document", message.document),
        ("video", message.video),
        ("audio", message.audio),
        ("photo", message.photo),
        ("voice", message.voice),
        ("video_note", message.video_note),
        ("animation", message.animation),
        ("sticker", message.sticker)
    ]

    for media_type, media in media_map:
        if media:
            file_name = getattr(media, "file_name", None)
            if not file_name:
                if media_type == "photo":
                    file_name = "photo.jpg"
                elif media_type == "voice":
                    file_name = "voice.ogg"
                elif media_type == "video_note":
                    file_name = "video_note.mp4"
                elif media_type == "animation":
                    file_name = "animation.mp4"
                elif media_type == "sticker":
                    file_name = "sticker.webp"
                else:
                    file_name = f"{media_type}_file"

            return {
                "file_id": media.file_id,
                "file_unique_id": media.file_unique_id,
                "file_name": file_name,
                "file_size": getattr(media, "file_size", 0) or 0,
                "file_type": media_type
            }
    return None


def insert_file(file_data: dict, uploaded_by: int, caption: str = None):
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO files (
            unique_code, file_id, file_unique_id, file_name,
            file_size, file_type, caption, uploaded_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "temp",
        file_data["file_id"],
        file_data["file_unique_id"],
        file_data["file_name"],
        file_data["file_size"],
        file_data["file_type"],
        caption or "",
        uploaded_by,
        now
    ))
    row_id = cur.lastrowid
    unique_code = make_code(file_data["file_unique_id"], row_id)

    cur.execute(
        "UPDATE files SET unique_code = ? WHERE id = ?",
        (unique_code, row_id)
    )
    conn.commit()
    return unique_code


def get_file_by_code(code: str):
    cur.execute("""
        SELECT id, unique_code, file_id, file_unique_id, file_name,
               file_size, file_type, caption, uploaded_by, created_at
        FROM files
        WHERE unique_code = ?
    """, (code,))
    return cur.fetchone()


def format_size(size: int) -> str:
    if size is None:
        return "Unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    s = float(size)
    for unit in units:
        if s < 1024 or unit == units[-1]:
            return f"{s:.2f} {unit}"
        s /= 1024
    return f"{size} B"


async def check_force_sub(client: Client, user_id: int) -> bool:
    if not FORCE_SUB_CHANNEL:
        return True

    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.warning("Force sub check failed: %s", e)
        return False
    return False


def join_keyboard():
    if not FORCE_SUB_CHANNEL:
        return None

    channel_link = f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Channel", url=channel_link)],
        [InlineKeyboardButton("Try Again", callback_data="checksub")]
    ])


async def get_bot_username(client: Client) -> str:
    global BOT_USERNAME
    if BOT_USERNAME:
        return BOT_USERNAME
    me = await client.get_me()
    BOT_USERNAME = me.username
    return BOT_USERNAME


# =========================
# COMMANDS
# =========================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    save_user(message)

    text_parts = message.text.split(maxsplit=1)
    start_arg = text_parts[1].strip() if len(text_parts) > 1 else None

    if start_arg and start_arg.startswith("get_"):
        code = start_arg.replace("get_", "", 1)

        allowed = await check_force_sub(client, message.from_user.id)
        if not allowed:
            await message.reply_text(
                "You must join the channel first to access this file.",
                reply_markup=join_keyboard()
            )
            return

        row = get_file_by_code(code)
        if not row:
            await message.reply_text("File not found or invalid link.")
            return

        _, unique_code, file_id, _, file_name, file_size, file_type, caption, _, _ = row

        try:
            send_caption = caption or f"**{file_name}**"
            await client.send_cached_media(
                chat_id=message.chat.id,
                file_id=file_id,
                caption=send_caption
            )
        except Exception as e:
            logger.exception("Failed to send cached media: %s", e)
            await message.reply_text("Failed to send file. The stored file may no longer be valid.")
        return

    await message.reply_text(
        "Hello!\n\n"
        "Send me any file/media and I will generate a shareable link.\n\n"
        "Supported media:\n"
        "- document\n"
        "- video\n"
        "- audio\n"
        "- photo\n"
        "- voice\n"
        "- animation\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Help\n"
        "/stats - Bot stats (owner only)"
    )


@app.on_message(filters.private & filters.command("help"))
async def help_handler(client: Client, message: Message):
    save_user(message)
    await message.reply_text(
        "How to use:\n\n"
        "1. Send a file to the bot\n"
        "2. Bot stores its Telegram file_id\n"
        "3. Bot gives you a deep-link\n"
        "4. Anyone opening that link can receive the file\n\n"
        "Tip: you can also send a caption with the media, and that caption will be reused."
    )


@app.on_message(filters.private & filters.command("stats"))
async def stats_handler(client: Client, message: Message):
    save_user(message)

    if message.from_user.id not in OWNER_IDS:
        await message.reply_text("You are not allowed to use this command.")
        return

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM files")
    total_files = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM files WHERE uploaded_by = ?", (message.from_user.id,))
    your_files = cur.fetchone()[0]

    await message.reply_text(
        f"**Bot Stats**\n\n"
        f"Total Users: `{total_users}`\n"
        f"Total Files: `{total_files}`\n"
        f"Your Uploaded Files: `{your_files}`"
    )


# =========================
# CALLBACK
# =========================
@app.on_callback_query(filters.regex("^checksub$"))
async def checksub_callback(client, callback_query):
    user_id = callback_query.from_user.id
    allowed = await check_force_sub(client, user_id)

    if allowed:
        await callback_query.answer("You joined successfully.", show_alert=True)
        try:
            await callback_query.message.edit_text(
                "Joined successfully.\nNow open your file link again."
            )
        except Exception:
            pass
    else:
        await callback_query.answer("You still need to join the channel.", show_alert=True)


# =========================
# MEDIA HANDLER
# =========================
@app.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.audio
        | filters.photo
        | filters.voice
        | filters.video_note
        | filters.animation
        | filters.sticker
    )
)
async def media_handler(client: Client, message: Message):
    save_user(message)

    file_data = get_file_info(message)
    if not file_data:
        await message.reply_text("Unsupported media.")
        return

    # Extra safety check for 2 GB
    if file_data["file_size"] and file_data["file_size"] > 2000 * 1024 * 1024:
        await message.reply_text("File is larger than 2 GB, so I can't store/share it.")
        return

    caption = message.caption.html if message.caption else ""

    try:
        unique_code = insert_file(
            file_data=file_data,
            uploaded_by=message.from_user.id,
            caption=caption
        )

        bot_username = await get_bot_username(client)
        deep_link = f"https://t.me/{bot_username}?start=get_{quote(unique_code)}"

        await message.reply_text(
            f"**File Saved Successfully**\n\n"
            f"File Name: `{file_data['file_name']}`\n"
            f"Type: `{file_data['file_type']}`\n"
            f"Size: `{format_size(file_data['file_size'])}`\n\n"
            f"**Share Link:**\n{deep_link}",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Open Link", url=deep_link)]
            ])
        )

    except Exception as e:
        logger.exception("Error while saving file: %s", e)
        await message.reply_text("Failed to save this file.")


# =========================
# FALLBACK
# =========================
@app.on_message(filters.private & filters.text)
async def text_handler(client: Client, message: Message):
    save_user(message)
    await message.reply_text("Send me a file/media and I will generate a shareable link.")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
