FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папку для загрузок
RUN mkdir -p webapp/uploads

# Порты (Railway использует переменную PORT)
EXPOSE 5000

# Запуск приложения (используем PORT из окружения)
# Railway автоматически устанавливает PORT, используем его
# Используем shell форму для раскрытия переменной $PORT
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile - --error-logfile - --log-level info webapp.app_production:app"]

