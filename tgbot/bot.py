#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Простой Telegram бот для проверки на фишинг
"""

import sys
import logging
from pathlib import Path

# Добавляем путь к modelN
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modelN"))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from model_loader import PhishingModel

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8442272401:AAGVDGyYOixzQESjNDhfaw_xMXW5zE6rdjw"
phishing_model = None


def load_model():
    """Загрузка модели"""
    global phishing_model
    try:
        model_dir = project_root / "modelN"
        phishing_model = PhishingModel(model_dir=str(model_dir))
        logger.info("Модель загружена")
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        raise


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🛡️ <b>Бот для проверки на фишинг</b>\n\n"
        "Отправьте текст для проверки на фишинг.",
        parse_mode='HTML'
    )


async def check_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка текста"""
    if not phishing_model:
        await update.message.reply_text("❌ Модель не загружена. Запустите сначала obuch.py")
        return
    
    text = update.message.text or ""
    if not text.strip():
        await update.message.reply_text("❌ Пожалуйста, отправьте текст")
        return
    
    try:
        import re
        has_url = bool(re.search(r'https?://|www\.', text, re.I))
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        has_phone = bool(re.search(r'\d{10,}', text))
        
        result = phishing_model.predict(text, has_url, has_email, has_phone)
        percentage = result['percentage']
        
        if percentage < 30:
            emoji, status = "🟢", "Безопасно"
        elif percentage < 50:
            emoji, status = "🟡", "Подозрительно"
        elif percentage < 70:
            emoji, status = "🟠", "Опасно"
        else:
            emoji, status = "🔴", "Критично"
        
        await update.message.reply_text(
            f"{emoji} <b>Результат проверки</b>\n\n"
            f"Вероятность фишинга: <b>{percentage:.1f}%</b>\n"
            f"Статус: {status}\n"
            f"Уверенность: {result['confidence']:.1f}%",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("Запуск Telegram бота")
    print("=" * 60)
    
    try:
        load_model()
        print("✓ Модель загружена")
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_text))
    app.add_error_handler(error_handler)
    
    print("✓ Бот запущен!")
    print("=" * 60)
    app.run_polling()


if __name__ == "__main__":
    main()

