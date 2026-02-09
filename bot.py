import os
import asyncio
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiohttp import web

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_PATH = "downloads"
PORT = int(os.getenv("PORT", 8000)) # Koyeb porti

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Health Check uchun) ---
async def handle_health(request):
    return web.Response(text="Bot is alive and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Web server {PORT}-portda ishga tushdi")

# --- DOWNLOAD LOGIC ---
async def download_video(url, user_id):
    file_path = f"{DOWNLOAD_PATH}/{user_id}_video.mp4"
    ydl_opts = {
        # 720p dan yuqori bo'lmagan eng yaxshi sifat (50MB limit uchun xavfsizroq)
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
    return file_path

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("🚀 **Tayyorman!**\n\nMenga video linkini yuboring, men uni eng yaxshi sifatda yuklab beraman.")

@dp.message(F.text.regexp(r'(https?://\S+)'))
async def handle_link(message: types.Message):
    url = message.text
    status = await message.answer("📥 **Yuklash boshlandi...**")
    
    try:
        file_path = await download_video(url, message.from_user.id)
        
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)
            if size > 50:
                await status.edit_text(f"⚠️ **Hajm juda katta ({size:.1f}MB).**\nTelegram bot limiti 50MB.")
            else:
                await status.edit_text("📤 **Yuborilmoqda...**")
                video = FSInputFile(file_path)
                await message.answer_video(video, caption="✅ @SizningBot_nomi orqali yuklandi")
                await status.delete()
            os.remove(file_path)
        else:
            raise Exception("Fayl topilmadi")
    except Exception as e:
        logging.error(f"Error: {e}")
        await status.edit_text("❌ **Xatolik!** Video yuklanmadi. Link noto'g'ri yoki sayt cheklov qo'ygan.")

# --- MAIN ---
async def main():
    # Veb-serverni task qilib qo'shamiz (Health Check uchun)
    asyncio.create_task(start_web_server())
    # Bot pollingni boshlaymiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
