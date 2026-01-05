#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Telegram бот с Web App для проверки на фишинг
"""

import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8442272401:AAGVDGyYOixzQESjNDhfaw_xMXW5zE6rdjw"

# ⚠️ ЗАМЕНИТЕ НА ВАШ HTTPS URL ПОСЛЕ ДЕПЛОЯ НА RENDER/Railway
# Например: https://phishing-detector.onrender.com/webapp
WEBAPP_URL = "https://web-production-4689.up.railway.app/webapp"  # Railway.app URL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с кнопкой Web App"""
    
    # Создаем клавиатуру с кнопкой Web App
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛡️ Открыть проверку фишинга",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Красивое приветствие
    welcome_text = """
🛡️ <b>Добро пожаловать в бот для проверки на фишинг!</b>

Я помогу вам проверить различные материалы на фишинг с помощью AI модели.

<b>📱 Что я умею:</b>
• ✅ Проверка текста на фишинг
• ✅ Анализ изображений (OCR)
• ✅ Проверка .eml файлов
• ✅ Определение уровня опасности

<b>🚀 Как использовать:</b>
Просто нажмите кнопку ниже, чтобы открыть веб-приложение!

<i>Веб-приложение работает прямо в Telegram - не нужно ничего устанавливать!</i>
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 <b>Справка</b>

<b>Как использовать бота:</b>
1. Нажмите кнопку "🛡️ Открыть проверку фишинга" в меню
2. Откроется веб-приложение прямо в Telegram
3. Выберите способ проверки:
   • 📝 Текст - вставьте текст для проверки
   • 📷 Изображение - загрузите фото с текстом
   • 📧 E-mail - загрузите .eml файл

<b>Команды:</b>
/start - Начать работу
/help - Показать справку

<b>⚠️ Важно:</b>
Для работы Web App нужен HTTPS URL.
Если кнопка не работает, убедитесь что бот настроен правильно.
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='HTML'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Проверьте настройки Web App URL в коде бота."
        )


def main():
    """Главная функция"""
    print("=" * 60)
    print("🚀 Запуск Telegram бота с Web App")
    print("=" * 60)
    
    # Проверка URL
    if "your-app-url" in WEBAPP_URL or "localhost" in WEBAPP_URL:
        print("⚠️ ВНИМАНИЕ: Web App URL не настроен!")
        print()
        print("Для работы Web App нужно:")
        print("1. Развернуть приложение на Render.com (см. DEPLOY_RENDER.md)")
        print("2. Получить HTTPS URL (например: https://phishing-detector.onrender.com)")
        print("3. Обновить WEBAPP_URL в этом файле:")
        print(f"   WEBAPP_URL = \"https://your-app.onrender.com/webapp\"")
        print()
        print("Бот запустится, но кнопка Web App не будет работать до настройки URL!")
        print("=" * 60)
        print()
    
    print(f"📍 Web App URL: {WEBAPP_URL}")
    print("=" * 60)
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_error_handler(error_handler)
    
    print("✓ Бот успешно запущен!")
    print("📱 Откройте Telegram и отправьте /start")
    print("=" * 60)
    
    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()
