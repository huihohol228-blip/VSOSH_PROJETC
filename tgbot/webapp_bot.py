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

# ⚠️ ВАЖНО: Telegram требует HTTPS для Web App!
# Используйте ngrok для создания HTTPS туннеля:
#   1. Запустите Flask API: python webapp/app.py
#   2. Запустите ngrok: ngrok http 5000
#   3. Скопируйте HTTPS URL (например: https://abc123.ngrok.io)
#   4. Замените URL ниже на ваш ngrok URL
WEBAPP_URL = "https://your-ngrok-url.ngrok.io/webapp"  # ⚠️ ЗАМЕНИТЕ НА ВАШ NGROK URL!


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с кнопкой Web App"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛡️ Открыть проверку фишинга",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛡️ <b>Бот для проверки на фишинг</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть веб-приложение:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📖 <b>Помощь</b>\n\n"
        "Нажмите кнопку 'Открыть проверку фишинга' для использования веб-приложения.\n\n"
        "<b>Настройка:</b>\n"
        "1. Запустите Flask API: <code>python webapp/app.py</code>\n"
        "2. Запустите ngrok: <code>ngrok http 5000</code>\n"
        "3. Обновите WEBAPP_URL в webapp_bot.py",
        parse_mode='HTML'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Проверьте настройки Web App URL."
        )


def main():
    """Главная функция"""
    print("=" * 60)
    print("Запуск Telegram бота с Web App")
    print("=" * 60)
    
    # Проверка URL
    if "your-ngrok-url" in WEBAPP_URL or "localhost" in WEBAPP_URL:
        print("⚠️ ВНИМАНИЕ: Web App URL не настроен!")
        print()
        print("Telegram требует HTTPS для Web App.")
        print("Используйте ngrok для создания HTTPS туннеля:")
        print()
        print("1. Запустите Flask API: python webapp/app.py")
        print("2. В другом окне запустите: ngrok http 5000")
        print("3. Скопируйте HTTPS URL (например: https://abc123.ngrok.io)")
        print("4. Обновите WEBAPP_URL в этом файле")
        print()
        print("Или запустите: setup_ngrok.bat")
        print()
        print("Бот запустится, но Web App не будет работать до настройки URL!")
        print("=" * 60)
        print()
    
    print(f"Web App URL: {WEBAPP_URL}")
    print("⚠️ Убедитесь, что Flask API запущен и ngrok настроен")
    print("=" * 60)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_error_handler(error_handler)
    
    print("✓ Бот запущен!")
    print("Откройте Telegram и отправьте /start")
    print("=" * 60)
    
    app.run_polling()


if __name__ == "__main__":
    main()
