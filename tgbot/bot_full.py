#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Полнофункциональный Telegram бот для проверки на фишинг
Поддерживает: текст, изображения (OCR), .eml файлы
БЕЗ Web App - работает напрямую в Telegram
"""

import sys
import os
import re
import logging
import tempfile
from pathlib import Path

# Добавляем путь к modelN
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modelN"))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from model_loader import PhishingModel

# Импорт утилит из webapp
sys.path.insert(0, str(project_root / "webapp"))
from utils import (
    extract_urls_emails_phones,
    extract_text_from_image,
    parse_eml_file,
    OCR_AVAILABLE
)

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
    help_text = """
🛡️ <b>Бот для проверки на фишинг</b>

<b>Как использовать:</b>

📝 <b>Текст:</b> Просто отправьте текст боту

📷 <b>Изображение:</b> Отправьте фото с текстом (используется OCR)

📧 <b>E-mail файл:</b> Отправьте .eml файл

<b>Команды:</b>
/start - Начать работу
/help - Помощь
/stats - Статистика проверок
"""
    await update.message.reply_text(help_text, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await start(update, context)


def format_result(percentage, confidence, urls, emails, phones):
    """Форматирует результат проверки"""
    if percentage < 30:
        emoji, status = "🟢", "Безопасно"
    elif percentage < 50:
        emoji, status = "🟡", "Подозрительно"
    elif percentage < 70:
        emoji, status = "🟠", "Опасно"
    else:
        emoji, status = "🔴", "Критично"
    
    result_text = f"{emoji} <b>Результат проверки</b>\n\n"
    result_text += f"Вероятность фишинга: <b>{percentage:.1f}%</b>\n"
    result_text += f"Статус: {status}\n"
    result_text += f"Уверенность: {confidence:.1f}%\n"
    
    if urls:
        result_text += f"\n🔗 Найдено URL: {len(urls)}\n"
        for url in urls[:3]:
            result_text += f"  • {url[:50]}...\n" if len(url) > 50 else f"  • {url}\n"
    
    if emails:
        result_text += f"\n📧 Найдено email: {len(emails)}\n"
        for email in emails[:3]:
            result_text += f"  • {email}\n"
    
    if phones:
        result_text += f"\n📞 Найдено телефонов: {len(phones)}\n"
        for phone in phones[:3]:
            result_text += f"  • {phone}\n"
    
    if percentage >= 70:
        result_text += "\n⚠️ <b>ВНИМАНИЕ!</b> Высокий риск фишинга! Не переходите по ссылкам!"
    
    return result_text


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
        await update.message.reply_text("⏳ Проверяю...")
        
        # Извлекаем URL, email, телефоны
        urls, emails, phones = extract_urls_emails_phones(text)
        has_url = len(urls) > 0
        has_email = len(emails) > 0
        has_phone = len(phones) > 0
        
        # Анализ через модель
        result = phishing_model.predict(text, has_url, has_email, has_phone)
        
        # Форматируем результат
        result_text = format_result(
            result['percentage'],
            result['confidence'],
            urls,
            emails,
            phones
        )
        
        await update.message.reply_text(result_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def check_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка изображения (OCR)"""
    if not phishing_model:
        await update.message.reply_text("❌ Модель не загружена")
        return
    
    if not OCR_AVAILABLE:
        await update.message.reply_text(
            "❌ OCR не доступен. Установите:\n"
            "pip install pytesseract pillow\n"
            "И установите Tesseract OCR"
        )
        return
    
    try:
        await update.message.reply_text("⏳ Обрабатываю изображение...")
        
        # Скачиваем фото
        photo = update.message.photo[-1]  # Берем самое большое фото
        file = await context.bot.get_file(photo.file_id)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Извлекаем текст с помощью OCR
            extracted_text = extract_text_from_image(tmp_path)
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                await update.message.reply_text("❌ Не удалось распознать текст на изображении")
                return
            
            # Извлекаем URL, email, телефоны
            urls, emails, phones = extract_urls_emails_phones(extracted_text)
            has_url = len(urls) > 0
            has_email = len(emails) > 0
            has_phone = len(phones) > 0
            
            # Анализ через модель
            result = phishing_model.predict(extracted_text, has_url, has_email, has_phone)
            
            # Форматируем результат
            result_text = "📷 <b>Результат проверки изображения</b>\n\n"
            result_text += f"📝 Извлечено символов: {len(extracted_text)}\n\n"
            result_text += format_result(
                result['percentage'],
                result['confidence'],
                urls,
                emails,
                phones
            )
            
            # Показываем превью текста
            if len(extracted_text) > 200:
                result_text += f"\n\n📄 <b>Превью текста:</b>\n{extracted_text[:200]}..."
            else:
                result_text += f"\n\n📄 <b>Извлеченный текст:</b>\n{extracted_text}"
            
            await update.message.reply_text(result_text, parse_mode='HTML')
            
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке изображения: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def check_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка .eml файла"""
    if not phishing_model:
        await update.message.reply_text("❌ Модель не загружена")
        return
    
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Файл не найден")
        return
    
    # Проверяем расширение
    if not document.file_name or not document.file_name.lower().endswith('.eml'):
        await update.message.reply_text("❌ Пожалуйста, отправьте .eml файл")
        return
    
    try:
        await update.message.reply_text("⏳ Обрабатываю .eml файл...")
        
        # Скачиваем файл
        file = await context.bot.get_file(document.file_id)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.eml') as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Парсим .eml файл
            email_data = parse_eml_file(tmp_path)
            
            if not email_data.get('body'):
                await update.message.reply_text("❌ Не удалось извлечь содержимое письма")
                return
            
            # Объединяем все данные для анализа
            full_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
            
            # Извлекаем URL, email, телефоны
            urls, emails, phones = extract_urls_emails_phones(full_text)
            
            # Добавляем email отправителя и получателя
            if email_data.get('from'):
                emails.append(email_data['from'])
            if email_data.get('to'):
                emails.extend([e.strip() for e in email_data['to'].split(',')])
            
            has_url = len(urls) > 0
            has_email = len(emails) > 0
            has_phone = len(phones) > 0
            
            # Анализ через модель
            result = phishing_model.predict(full_text, has_url, has_email, has_phone)
            
            # Форматируем результат
            result_text = "📧 <b>Результат проверки письма</b>\n\n"
            result_text += f"<b>От:</b> {email_data.get('from', 'Неизвестно')}\n"
            result_text += f"<b>Кому:</b> {email_data.get('to', 'Неизвестно')}\n"
            result_text += f"<b>Тема:</b> {email_data.get('subject', 'Без темы')}\n\n"
            result_text += format_result(
                result['percentage'],
                result['confidence'],
                urls,
                emails,
                phones
            )
            
            await update.message.reply_text(result_text, parse_mode='HTML')
            
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке .eml: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")


def main():
    """Главная функция"""
    print("=" * 60)
    print("Запуск полнофункционального Telegram бота")
    print("=" * 60)
    
    try:
        load_model()
        print("✓ Модель загружена")
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_text))
    app.add_handler(MessageHandler(filters.PHOTO, check_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, check_document))
    
    app.add_error_handler(error_handler)
    
    print("✓ Бот запущен!")
    print("=" * 60)
    print("Поддерживаемые функции:")
    print("  • Проверка текста")
    print("  • Проверка изображений (OCR)")
    print("  • Проверка .eml файлов")
    print("=" * 60)
    
    app.run_polling()


if __name__ == "__main__":
    main()




