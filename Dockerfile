# Microsoft'un resmi Playwright ve Python imajı
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Geçici dosyalar için klasör
RUN mkdir -p /app/downloads

# Botu çalıştır
CMD ["python", "src/main.py"]