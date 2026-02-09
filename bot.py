import os
import asyncio
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiohttp import web

# --- KONFIGURATSIYA ---
TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_PATH = "downloads"
PORT = int(os.getenv("PORT", 8000))

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- HEALTH CHECK SERVER (Koyeb o'chirib qo'ymasligi uchun) ---
async def handle_health(request):
    return web.Response(text="Bot is running perfectly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Health Check server {PORT}-portda yoqildi")

# --- YUKLASH LOGIKASI (YouTube va Sifat uchun optimallashtirilgan) ---
async def download_video(url, user_id):
    file_path = f"{DOWNLOAD_PATH}/{user_id}_video.mp4"
    
    ydl_opts = {
        # YouTube uchun eng yaxshi video va audioni birlashtirish (max 1080p)
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        # YouTube blokirovkasini aylanib o'tish uchun:
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    
    loop = asyncio.get_event_loop()
    # yt-dlp ni bloklamaydigan rejimda ishga tushirish
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
    return file_path

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("🤖 **Professional Video Downloader**\n\nYouTube, Instagram, TikTok va Pinterest linklarini yuboring!")

@dp.message(F.text.regexp(r'(https?://\S+)'))
async def handle_url(message: types.Message):
    url = message.text
    status = await message.answer("🔍 **Video tahlil qilinmoqda...**")
    
    try:
        await status.edit_text("📥 **Yuklash boshlandi...** (Bu biroz vaqt olishi mumkin)")
        file_path = await download_video(url, message.from_user.id)
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size > 50:
                await status.edit_text(f"⚠️ **Hajm juda katta: {file_size:.1f}MB**\nTelegram botlar faqat 50MB gacha yubora oladi.")
            else:
                await status.edit_text("📤 **Yuborilmoqda...**")
                video_file = FSInputFile(file_path)
                await message.answer_video(video_file, caption="✅ Muvaffaqiyatli yuklandi!")
                await status.delete()
            
            os.remove(file_path) # Serverni tozalash
        else:
            raise Exception("Fayl yaratilmadi")
            
    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        await status.edit_text("❌ **Xatolik!** Video yuklanmadi.\n\nSababi: YouTube cheklovi yoki link noto'g'ri.")

# --- ISHGA TUSHIRISH ---
async def main():
    # Veb-serverni orqa fonda ishga tushirish
    asyncio.create_task(start_web_server())
    # Bot pollingni boshlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
