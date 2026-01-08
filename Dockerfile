FROM python:3.11-slim

# Устанавливаем системные зависимости (Tesseract OCR)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Устанавливаем переменную окружения
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 5000

# Команда запуска
CMD python -c "import os; port = int(os.environ.get('PORT', 5000)); from webapp.app_production import app; app.run(host='0.0.0.0', port=port, debug=False)"



