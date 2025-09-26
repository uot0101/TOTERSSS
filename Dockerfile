FROM python:3.11-slim

WORKDIR /app

# نسخ requirements وتثبيت المكتبات + تثبيت Chrome + ChromeDriver
COPY requirements.txt ./
RUN apt-get update && apt-get install -y wget unzip chromium chromium-driver \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# لا تضع أمر التشغيل هنا، Railway يستخدم Procfile
