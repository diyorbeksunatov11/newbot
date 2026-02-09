FROM python:3.11-slim

# FFmpeg va tizim yangilanishlarini o'rnatish
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Koyeb portini ko'rsatish
EXPOSE 8000

CMD ["python", "bot.py"]
