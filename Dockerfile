FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папку для загрузок
RUN mkdir -p webapp/uploads && chmod 755 webapp/uploads

# Переменная окружения для порта (Railway установит PORT)
ENV PORT=5000

# Запуск через скрипт, который правильно обработает PORT
CMD python -c "import os; port = int(os.environ.get('PORT', 5000)); from webapp.app_production import app; app.run(host='0.0.0.0', port=port, debug=False)"
