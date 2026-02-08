import os
import asyncio
import logging
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile

# --- SOZLAMALAR ---
TOKEN = "8596487785:AAE8OFQ5TYYC_EuVQ4-QGBDVPC8hXURfgVE"
DOWNLOAD_PATH = "downloads"

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- YUKLASH LOGIKASI ---
async def download_best_video(url, user_id):
    """Videoni eng yaxshi sifatda (lekin 50MB dan oshmaslikka harakat qilib) yuklaydi."""
    file_path = f"{DOWNLOAD_PATH}/{user_id}_video.mp4"
    
    ydl_opts = {
        # 'best' formatini tanlaydi, Telegram limitini hisobga olgan holda
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
    return file_path

def get_info(url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("🌟 **Professional Downloader Bot**\n\nMenga link yuboring, men darhol videoni yuklab beraman!")

@dp.message(F.text.regexp(r'(https?://\S+)'))
async def handle_link(message: types.Message):
    url = message.text
    status_msg = await message.answer("⏳ **Yuklash boshlandi...**")
    
    try:
        # Video haqida ma'lumot olish (Sarlavha uchun)
        info = await asyncio.to_thread(get_info, url)
        title = info.get('title', 'Video')

        # Yuklash
        file_path = await download_best_video(url, message.from_user.id)
        
        if os.path.exists(file_path):
            # Hajmini tekshirish
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size > 50:
                await status_msg.edit_text(f"⚠️ **Video hajmi juda katta ({file_size:.1f}MB).**\nTelegram botlar uchun limit 50MB.")
            else:
                await status_msg.edit_text("📤 **Yuborilmoqda...**")
                video = FSInputFile(file_path)
                await message.answer_video(video, caption=f"✅ **{title}**")
                await status_msg.delete()
            
            # Faylni o'chirish (Serverda joy band qilmasligi uchun)
            os.remove(file_path)
        else:
            raise Exception("Fayl yuklanmadi.")

    except Exception as e:
        logging.error(f"Xato: {e}")
        await status_msg.edit_text("❌ **Xato yuz berdi.** Link noto'g'ri yoki video juda uzun bo'lishi mumkin.")

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
