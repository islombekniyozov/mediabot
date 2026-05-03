#!/usr/bin/env python3
"""
MediaBot - Instagram, YouTube, TikTok video downloader
Token: ...
Admin ID: 1079953976
"""

import asyncio
import logging
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, ChatMember
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOKEN = "BOT_TOKEN"
ADMIN_ID = 1079953976
DB_PATH = "mediabot.db"

# ffmpeg to'liq yo'li (where ffmpeg buyrug'i natijasi)
# Masalan: r"C:\ffmpeg\bin\ffmpeg.exe"
FFMPEG_PATH = r"C:\Users\Dell\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── LANGUAGES ─────────────────────────────────────────────────────────────────
TEXTS = {
    "uz": {
        "welcome": "🎬 Xush kelibsiz!\n\nInstagram, YouTube yoki TikTok havolasini yuboring — video yuklab olaman!\n\n📌 Buyruqlar:\n/round — Video dumaloq formatga\n/unround — Dumaloq → MP4\n/top — Top mashhur qo'shiqlar\n/new — Yangi mashhur qo'shiqlar\n/lang — Tilni o'zgartirish",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'zgartirildi: O'zbek",
        "send_link": "🔗 Havola yuboring (Instagram / YouTube / TikTok):",
        "downloading": "⏳ Yuklanmoqda...",
        "done": "✅ Tayyor!",
        "error": "❌ Xato yuz berdi. Havola to'g'ri ekanligini tekshiring.",
        "find_music": "🎵 Original musiqa qidirish va yuklab olish",
        "add_to_group": "➕ Botni guruhga qo'shish",
        "round_prompt": "📹 Dumaloq qilish uchun video yuboring:",
        "unround_prompt": "⭕ MP4 ga aylantirish uchun video note yuboring:",
        "converting": "🔄 Aylantirilmoqda...",
        "top_songs": "🔥 TOP Mashhur Qo'shiqlar:",
        "new_songs": "🆕 Yangi Mashhur Qo'shiqlar:",
        "music_search": "🎵 Qo'shiq nomi yoki ijrochi nomini yuboring:",
        "searching_music": "🔍 Qidirilmoqda...",
        "music_found": "🎵 Topildi! Yuklanmoqda...",
        "music_error": "❌ Qo'shiq topilmadi.",
        "invalid_link": "❌ Noto'g'ri havola. Instagram, YouTube yoki TikTok havolasi yuboring.",
        "file_too_large": "❌ Fayl juda katta (50MB dan ko'p). YouTube havolasini sinab ko'ring.",
        "video_note_only": "❌ Faqat video xabar (video note) yuboring.",
    },
    "ru": {
        "welcome": "🎬 Добро пожаловать!\n\nОтправьте ссылку Instagram, YouTube или TikTok — скачаю видео!\n\n📌 Команды:\n/round — Видео в круглый формат\n/unround — Круглое → MP4\n/top — Топ популярных песен\n/new — Новые популярные песни\n/lang — Сменить язык",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык изменён: Русский",
        "send_link": "🔗 Отправьте ссылку (Instagram / YouTube / TikTok):",
        "downloading": "⏳ Загружается...",
        "done": "✅ Готово!",
        "error": "❌ Произошла ошибка. Проверьте правильность ссылки.",
        "find_music": "🎵 Найти и скачать оригинальную музыку",
        "add_to_group": "➕ Добавить бота в группу",
        "round_prompt": "📹 Отправьте видео для конвертации в круглое:",
        "unround_prompt": "⭕ Отправьте видео-кружок для конвертации в MP4:",
        "converting": "🔄 Конвертируется...",
        "top_songs": "🔥 ТОП Популярных Песен:",
        "new_songs": "🆕 Новые Популярные Песни:",
        "music_search": "🎵 Отправьте название песни или имя исполнителя:",
        "searching_music": "🔍 Поиск...",
        "music_found": "🎵 Найдено! Загружается...",
        "music_error": "❌ Песня не найдена.",
        "invalid_link": "❌ Неверная ссылка. Отправьте ссылку Instagram, YouTube или TikTok.",
        "file_too_large": "❌ Файл слишком большой (более 50МБ).",
        "video_note_only": "❌ Отправьте только видео-кружок.",
    },
    "en": {
        "welcome": "🎬 Welcome!\n\nSend an Instagram, YouTube or TikTok link — I'll download the video!\n\n📌 Commands:\n/round — Convert video to circle format\n/unround — Circle → MP4\n/top — Top popular songs\n/new — New popular songs\n/lang — Change language",
        "choose_lang": "🌐 Choose language:",
        "lang_set": "✅ Language set: English",
        "send_link": "🔗 Send a link (Instagram / YouTube / TikTok):",
        "downloading": "⏳ Downloading...",
        "done": "✅ Done!",
        "error": "❌ An error occurred. Please check the link.",
        "find_music": "🎵 Find & download original music",
        "add_to_group": "➕ Add bot to group",
        "round_prompt": "📹 Send a video to convert to circle format:",
        "unround_prompt": "⭕ Send a video note to convert to MP4:",
        "converting": "🔄 Converting...",
        "top_songs": "🔥 TOP Popular Songs:",
        "new_songs": "🆕 New Popular Songs:",
        "music_search": "🎵 Send a song name or artist:",
        "searching_music": "🔍 Searching...",
        "music_found": "🎵 Found! Downloading...",
        "music_error": "❌ Song not found.",
        "invalid_link": "❌ Invalid link. Send an Instagram, YouTube or TikTok link.",
        "file_too_large": "❌ File too large (over 50MB).",
        "video_note_only": "❌ Please send a video note only.",
    }
}

TOP_SONGS = [
    ("Doja Cat - Paint The Town Red", "paint the town red doja cat"),
    ("SZA - Snooze", "snooze sza"),
    ("Miley Cyrus - Flowers", "flowers miley cyrus"),
    ("The Weeknd - Die For You", "die for you weeknd"),
    ("Harry Styles - As It Was", "as it was harry styles"),
    ("Bad Bunny - Tití Me Preguntó", "titi me pregunto bad bunny"),
    ("Taylor Swift - Anti-Hero", "anti hero taylor swift"),
    ("Beyoncé - Cuff It", "cuff it beyonce"),
    ("Shakira, Bizarrap - BZRP Music Sessions #53", "shakira bzrp session 53"),
    ("Peso Pluma - Ella Baila Sola", "ella baila sola peso pluma"),
]

NEW_SONGS = [
    ("Sabrina Carpenter - Espresso", "espresso sabrina carpenter"),
    ("Billie Eilish - Birds Of A Feather", "birds of a feather billie eilish"),
    ("Charli XCX - Brat", "brat charli xcx"),
    ("Kendrick Lamar - Not Like Us", "not like us kendrick lamar"),
    ("Chappell Roan - Good Luck, Babe!", "good luck babe chappell roan"),
    ("Benson Boone - Beautiful Things", "beautiful things benson boone"),
    ("Teddy Swims - Lose Control", "lose control teddy swims"),
    ("Post Malone - I Had Some Help", "i had some help post malone"),
    ("Shaboozey - A Bar Song", "a bar song shaboozey"),
    ("Tommy Richman - Million Dollar Baby", "million dollar baby tommy richman"),
]

# ─── DATABASE ──────────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'uz',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS online_users (
                user_id INTEGER PRIMARY KEY,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def upsert_user(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                last_seen=CURRENT_TIMESTAMP,
                is_active=1
        """, (user.id, user.username, user.first_name, user.last_name))
        await db.execute("""
            INSERT INTO online_users (user_id, last_active)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET last_active=CURRENT_TIMESTAMP
        """, (user.id,))
        await db.commit()

async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else "uz"

async def set_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
        await db.commit()

async def upsert_group(chat_id: int, title: str, username: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO groups (chat_id, title, username)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title, is_active=1
        """, (chat_id, title, username))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        total = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        today = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE date(joined_at)=date('now')"
        )).fetchone())[0]
        month = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE joined_at>=date('now','-30 days')"
        )).fetchone())[0]
        year = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE joined_at>=date('now','-365 days')"
        )).fetchone())[0]
        online = (await (await db.execute(
            "SELECT COUNT(*) FROM online_users WHERE last_active>=datetime('now','-5 minutes')"
        )).fetchone())[0]
        groups_total = (await (await db.execute(
            "SELECT COUNT(*) FROM groups WHERE is_active=1"
        )).fetchone())[0]
        return {
            "total": total, "today": today, "month": month,
            "year": year, "online": online, "groups": groups_total
        }

async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_active=1") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]

async def get_groups_list():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT chat_id, title, username, added_at FROM groups WHERE is_active=1 ORDER BY added_at DESC"
        ) as cur:
            return await cur.fetchall()

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def detect_platform(url: str):
    if re.search(r"instagram\.com|instagr\.am", url):
        return "instagram"
    if re.search(r"youtube\.com|youtu\.be", url):
        return "youtube"
    if re.search(r"tiktok\.com|vm\.tiktok", url):
        return "tiktok"
    return None

def t(lang: str, key: str) -> str:
    return TEXTS.get(lang, TEXTS["uz"]).get(key, key)

async def download_video(url: str, tmp_dir: str):
    """Download video using yt-dlp Python API (fastest method)."""
    import yt_dlp
    platform = detect_platform(url)
    out_template = os.path.join(tmp_dir, "video.%(ext)s")

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 10,
        "retries": 1,
        "ffmpeg_location": FFMPEG_PATH,
        "concurrent_fragment_downloads": 4,
        "noprogress": True,
    }

    if platform == "youtube":
        ydl_opts["extractor_args"] = {"youtube": {"player_client": ["android"]}}
    elif platform == "instagram":
        ydl_opts["http_headers"] = {
            "Referer": "https://www.instagram.com/",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        }
    elif platform == "tiktok":
        ydl_opts["http_headers"] = {
            "Referer": "https://www.tiktok.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    loop = asyncio.get_event_loop()
    def _download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            files = [f for f in Path(tmp_dir).glob("*.*")
                     if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")]
            return str(files[0]) if files else None
        except Exception as e:
            logger.error(f"yt_dlp video error: {e}")
            return None

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _download),
            timeout=45
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Video timeout: {url}")
        return None

async def download_audio(query: str, tmp_dir: str):
    """Download audio using yt-dlp Python API (fastest method)."""
    import yt_dlp
    out_template = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 10,
        "retries": 1,
        "ffmpeg_location": FFMPEG_PATH,
        "noprogress": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }

    loop = asyncio.get_event_loop()
    def _download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{query}"])
            for ext in ("*.mp3", "*.m4a", "*.webm", "*.opus"):
                files = list(Path(tmp_dir).glob(ext))
                if files:
                    return str(files[0])
            return None
        except Exception as e:
            logger.error(f"yt_dlp audio error: {e}")
            return None

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _download),
            timeout=45
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Audio timeout: {query}")
        return None

async def get_video_title(url: str) -> str:
    cmd = ["python", "-m", "yt_dlp", "--get-title", "--no-warnings", "--quiet", url]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        title = stdout.decode().strip()
        return title if title else "video"
    except Exception:
        return "video"

async def convert_to_round(input_path: str, output_path: str) -> bool:
    """Convert video to circle (video note) format 360x360."""
    cmd = [
        FFMPEG_PATH, "-i", input_path,
        "-vf", "scale=360:360:force_original_aspect_ratio=increase,crop=360:360",
        "-c:v", "libx264", "-c:a", "aac",
        "-t", "60",
        "-y", output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=120)
        return proc.returncode == 0
    except Exception:
        return False

async def convert_from_round(input_path: str, output_path: str) -> bool:
    """Convert video note back to mp4."""
    cmd = [
        FFMPEG_PATH, "-i", input_path,
        "-c:v", "libx264", "-c:a", "aac",
        "-y", output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=120)
        return proc.returncode == 0
    except Exception:
        return False

# ─── USER STATE ────────────────────────────────────────────────────────────────
user_states = {}  # user_id -> state string

# ─── HANDLERS ──────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type in ("group", "supergroup"):
        await upsert_group(chat.id, chat.title, getattr(chat, "username", None))

    await upsert_user(user)
    lang = await get_user_lang(user.id)

    bot_me = await ctx.bot.get_me()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
    ]])
    await update.message.reply_text(t(lang, "welcome"), reply_markup=kb)

async def lang_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])
    await update.message.reply_text(t(lang, "choose_lang"), reply_markup=kb)

async def round_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    user_states[user.id] = "waiting_video_for_round"
    await update.message.reply_text(t(lang, "round_prompt"))

async def unround_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    user_states[user.id] = "waiting_note_for_unround"
    await update.message.reply_text(t(lang, "unround_prompt"))

async def top_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    bot_me = await ctx.bot.get_me()

    text = t(lang, "top_songs") + "\n\n"
    buttons = []
    for i, (name, query) in enumerate(TOP_SONGS, 1):
        text += f"{i}. {name}\n"
        buttons.append([InlineKeyboardButton(f"⬇️ {name[:40]}", callback_data=f"dl_music:{query}")])

    buttons.append([InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def new_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    bot_me = await ctx.bot.get_me()

    text = t(lang, "new_songs") + "\n\n"
    buttons = []
    for i, (name, query) in enumerate(NEW_SONGS, 1):
        text += f"{i}. {name}\n"
        buttons.append([InlineKeyboardButton(f"⬇️ {name[:40]}", callback_data=f"dl_music:{query}")])

    buttons.append([InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# ─── ADMIN PANEL ───────────────────────────────────────────────────────────────
async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return

    stats = await get_stats()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Guruhlar ro'yxati", callback_data="admin_groups")],
        [InlineKeyboardButton("📢 Hammaga xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_refresh")],
    ])

    text = (
        "🛡️ <b>Admin Panel</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{stats['total']}</b>\n"
        f"🟢 Online (5 daqiqa): <b>{stats['online']}</b>\n"
        f"📅 Bugun qo'shildi: <b>{stats['today']}</b>\n"
        f"📆 1 oyda qo'shildi: <b>{stats['month']}</b>\n"
        f"📅 1 yilda qo'shildi: <b>{stats['year']}</b>\n"
        f"💬 Guruhlar soni: <b>{stats['groups']}</b>\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await upsert_user(user)
    lang = await get_user_lang(user.id)
    data = query.data

    # Language selection
    if data.startswith("lang_"):
        new_lang = data.split("_")[1]
        await set_user_lang(user.id, new_lang)
        await query.answer(TEXTS[new_lang]["lang_set"])
        bot_me = await ctx.bot.get_me()
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(TEXTS[new_lang]["add_to_group"], url=f"https://t.me/{bot_me.username}?startgroup=1")
        ]])
        await query.edit_message_text(TEXTS[new_lang]["welcome"], reply_markup=kb)

    # Music download
    elif data.startswith("dl_music:"):
        music_query = data[9:]
        await query.answer("⏳")
        msg = await query.message.reply_text(t(lang, "searching_music"))
        with tempfile.TemporaryDirectory() as tmp:
            path = await download_audio(music_query, tmp)
            if path and os.path.exists(path):
                await msg.edit_text(t(lang, "music_found"))
                bot_me = await ctx.bot.get_me()
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
                ]])
                with open(path, "rb") as f:
                    await query.message.reply_audio(f, title=music_query, reply_markup=kb)
                await msg.delete()
            else:
                await msg.edit_text(t(lang, "music_error"))

    # Admin callbacks
    elif data == "admin_stats" and user.id == ADMIN_ID:
        stats = await get_stats()
        text = (
            "📊 <b>Batafsil Statistika</b>\n\n"
            f"👤 Jami: <b>{stats['total']}</b>\n"
            f"🟢 Online: <b>{stats['online']}</b>\n"
            f"📅 Bugun: <b>{stats['today']}</b>\n"
            f"📆 1 oy: <b>{stats['month']}</b>\n"
            f"🗓 1 yil: <b>{stats['year']}</b>\n"
            f"💬 Guruhlar: <b>{stats['groups']}</b>"
        )
        await query.answer()
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)

    elif data == "admin_groups" and user.id == ADMIN_ID:
        groups = await get_groups_list()
        if not groups:
            await query.answer("Guruhlar yo'q")
            return
        text = "💬 <b>Guruhlar:</b>\n\n"
        for chat_id, title, username, added_at in groups[:20]:
            link = f"@{username}" if username else str(chat_id)
            text += f"• <b>{title}</b> ({link})\n  📅 {added_at[:10]}\n"
        await query.answer()
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)

    elif data == "admin_broadcast" and user.id == ADMIN_ID:
        user_states[ADMIN_ID] = "waiting_broadcast"
        await query.answer()
        await query.message.reply_text("📢 Hammaga yuboriladigan xabarni yozing:")

    elif data == "admin_refresh" and user.id == ADMIN_ID:
        stats = await get_stats()
        await query.answer(f"✅ Yangilandi! Jami: {stats['total']}")

    # Find original music from video
    elif data.startswith("find_music:"):
        video_title = data[11:]
        await query.answer("🔍")
        msg = await query.message.reply_text(t(lang, "searching_music"))
        with tempfile.TemporaryDirectory() as tmp:
            path = await download_audio(video_title, tmp)
            if path and os.path.exists(path):
                await msg.edit_text(t(lang, "music_found"))
                bot_me = await ctx.bot.get_me()
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
                ]])
                with open(path, "rb") as f:
                    await query.message.reply_audio(f, title=video_title, reply_markup=kb)
                await msg.delete()
            else:
                await msg.edit_text(t(lang, "music_error"))

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.message

    if not msg:
        return

    await upsert_user(user)

    if chat.type in ("group", "supergroup"):
        await upsert_group(chat.id, chat.title, getattr(chat, "username", None))

    lang = await get_user_lang(user.id)
    state = user_states.get(user.id)

    # Admin broadcast
    if state == "waiting_broadcast" and user.id == ADMIN_ID:
        user_states.pop(user.id, None)
        all_ids = await get_all_user_ids()
        sent = 0
        failed = 0
        status_msg = await msg.reply_text(f"📤 Yuborilmoqda... (0/{len(all_ids)})")
        for uid in all_ids:
            try:
                await ctx.bot.copy_message(chat_id=uid, from_chat_id=chat.id, message_id=msg.message_id)
                sent += 1
                if sent % 50 == 0:
                    await status_msg.edit_text(f"📤 Yuborilmoqda... ({sent}/{len(all_ids)})")
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
        await status_msg.edit_text(f"✅ Broadcast tugadi!\n📤 Yuborildi: {sent}\n❌ Xato: {failed}")
        return

    # Music search state
    if state == "waiting_music_search":
        user_states.pop(user.id, None)
        search_q = msg.text or ""
        wait_msg = await msg.reply_text(t(lang, "searching_music"))
        with tempfile.TemporaryDirectory() as tmp:
            path = await download_audio(search_q, tmp)
            if path and os.path.exists(path):
                await wait_msg.edit_text(t(lang, "music_found"))
                bot_me = await ctx.bot.get_me()
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
                ]])
                with open(path, "rb") as f:
                    await msg.reply_audio(f, title=search_q, reply_markup=kb)
                await wait_msg.delete()
            else:
                await wait_msg.edit_text(t(lang, "music_error"))
        return

    # Round: convert video to video note
    if state == "waiting_video_for_round":
        user_states.pop(user.id, None)
        if msg.video or msg.document:
            file_obj = msg.video or msg.document
            if file_obj.file_size and file_obj.file_size > 50 * 1024 * 1024:
                await msg.reply_text(t(lang, "file_too_large"))
                return
            wait_msg = await msg.reply_text(t(lang, "converting"))
            with tempfile.TemporaryDirectory() as tmp:
                tg_file = await ctx.bot.get_file(file_obj.file_id)
                in_path = os.path.join(tmp, "input.mp4")
                out_path = os.path.join(tmp, "round.mp4")
                await tg_file.download_to_drive(in_path)
                ok = await convert_to_round(in_path, out_path)
                if ok and os.path.exists(out_path):
                    bot_me = await ctx.bot.get_me()
                    with open(out_path, "rb") as f:
                        await msg.reply_video_note(f)
                    await wait_msg.delete()
                else:
                    await wait_msg.edit_text(t(lang, "error"))
        else:
            await msg.reply_text(t(lang, "round_prompt"))
        return

    # Unround: convert video note to mp4
    if state == "waiting_note_for_unround":
        user_states.pop(user.id, None)
        if msg.video_note:
            wait_msg = await msg.reply_text(t(lang, "converting"))
            with tempfile.TemporaryDirectory() as tmp:
                tg_file = await ctx.bot.get_file(msg.video_note.file_id)
                in_path = os.path.join(tmp, "input.mp4")
                out_path = os.path.join(tmp, "output.mp4")
                await tg_file.download_to_drive(in_path)
                ok = await convert_from_round(in_path, out_path)
                if ok and os.path.exists(out_path):
                    bot_me = await ctx.bot.get_me()
                    kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
                    ]])
                    with open(out_path, "rb") as f:
                        await msg.reply_video(f, reply_markup=kb)
                    await wait_msg.delete()
                else:
                    await wait_msg.edit_text(t(lang, "error"))
        else:
            await msg.reply_text(t(lang, "video_note_only"))
        return

    # Video/URL download
    text_content = msg.text or msg.caption or ""
    url_match = re.search(r'https?://\S+', text_content)

    if url_match:
        url = url_match.group(0)
        platform = detect_platform(url)

        if not platform:
            await msg.reply_text(t(lang, "invalid_link"))
            return

        wait_msg = await msg.reply_text(t(lang, "downloading"))
        bot_me = await ctx.bot.get_me()

        with tempfile.TemporaryDirectory() as tmp:
            video_path = await download_video(url, tmp)

            if not video_path or not os.path.exists(video_path):
                logger.error(f"Video download failed for URL: {url}")
                await wait_msg.edit_text(
                    t(lang, "error") + f"\n\n🔗 URL: {url[:60]}"
                )
                return

            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:
                await wait_msg.edit_text(t(lang, "file_too_large"))
                return

            video_title = await get_video_title(url)

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "find_music"), callback_data=f"find_music:{video_title[:50]}")],
                [InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")],
            ])

            with open(video_path, "rb") as f:
                await msg.reply_video(f, reply_markup=kb)

            await wait_msg.delete()

    elif msg.text and not msg.text.startswith("/"):
        wait_msg = await msg.reply_text(t(lang, "searching_music"))
        with tempfile.TemporaryDirectory() as tmp:
            path = await download_audio(msg.text, tmp)
            if path and os.path.exists(path):
                await wait_msg.edit_text(t(lang, "music_found"))
                bot_me = await ctx.bot.get_me()
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t(lang, "add_to_group"), url=f"https://t.me/{bot_me.username}?startgroup=1")
                ]])
                with open(path, "rb") as f:
                    await msg.reply_audio(f, title=msg.text, reply_markup=kb)
                await wait_msg.delete()
            else:
                await wait_msg.edit_text(t(lang, "music_error"))

async def my_chat_member_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Track when bot is added to or removed from groups."""
    result = update.my_chat_member
    chat = result.chat
    if chat.type in ("group", "supergroup"):
        new_status = result.new_chat_member.status
        if new_status in ("member", "administrator"):
            await upsert_group(chat.id, chat.title, getattr(chat, "username", None))
        elif new_status in ("left", "kicked"):
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE groups SET is_active=0 WHERE chat_id=?", (chat.id,))
                await db.commit()

# ─── MAIN ──────────────────────────────────────────────────────────────────────
async def post_init(application: Application):
    await init_db()
    await application.bot.set_my_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("round", "Videoni dumaloq qilish"),
        BotCommand("unround", "Dumaloq videoni MP4 qilish"),
        BotCommand("top", "Top qo'shiqlar"),
        BotCommand("new", "Yangi qo'shiqlar"),
        BotCommand("lang", "Tilni tanlash"),
        BotCommand("admin", "Admin panel"),
    ])

def main():
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    from telegram.ext import ChatMemberHandler

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("round", round_cmd))
    app.add_handler(CommandHandler("unround", unround_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("new", new_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start))
    app.add_handler(ChatMemberHandler(my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

    logger.info("Bot started successfully!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
