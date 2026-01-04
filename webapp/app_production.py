#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Веб-приложение для проверки на фишинг (Production версия)
Использует Gunicorn для продакшена
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response
from werkzeug.utils import secure_filename
from flask_cors import CORS
import logging

# Добавляем путь к modelN для импорта модели
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modelN"))

# Импорт модели
from model_loader import PhishingModel

# Импорт утилит из текущей папки
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from utils import (
    extract_urls_emails_phones,
    extract_text_from_image,
    parse_eml_file,
    format_result_json
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'

# Включаем CORS
CORS(app)

# Создаем папку для загрузок
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Разрешенные расширения
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'eml'}

# Глобальный экземпляр модели
phishing_model = None


def load_model():
    """Загрузка модели при старте"""
    global phishing_model
    try:
        model_dir = project_root / "modelN"
        phishing_model = PhishingModel(model_dir=str(model_dir))
        logger.info("Модель успешно загружена")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        logger.error("Приложение запустится, но проверка на фишинг не будет работать")
        phishing_model = None
        return False


# Загружаем модель при импорте (не падаем если модель не загрузилась)
try:
    load_model()
except Exception as e:
    logger.error(f"Критическая ошибка при загрузке модели: {e}")
    # Продолжаем работу, но модель будет None


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/webapp')
def webapp():
    """Telegram Web App версия - отдает файлы из web_tg"""
    webapp_path = project_root / "web_tg" / "index.html"
    if webapp_path.exists():
        with open(webapp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Заменяем пути к статическим файлам на абсолютные
        content = content.replace('href="style.css"', 'href="/webapp/style.css"')
        content = content.replace('src="app.js"', 'src="/webapp/app.js"')
        return Response(content, mimetype='text/html')
    return render_template('index.html')


@app.route('/webapp/<path:filename>')
def webapp_static(filename):
    """Статические файлы для Web App (CSS, JS)"""
    webapp_dir = project_root / "web_tg"
    file_path = webapp_dir / filename
    
    # Безопасность - проверяем что файл в нужной директории
    try:
        file_path.resolve().relative_to(webapp_dir.resolve())
    except ValueError:
        return "Access denied", 403
    
    if file_path.exists() and file_path.is_file():
        mimetypes = {
            'css': 'text/css',
            'js': 'application/javascript',
            'html': 'text/html'
        }
        ext = filename.split('.')[-1] if '.' in filename else 'html'
        mimetype = mimetypes.get(ext, 'text/plain')
        return send_file(str(file_path), mimetype=mimetype)
    return "File not found", 404


@app.route('/api/health')
def health():
    """Проверка здоровья API"""
    try:
        return jsonify({
            "status": "ok",
            "model_loaded": phishing_model is not None,
            "service": "phishing-detector"
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/predict/text', methods=['POST'])
def predict_text():
    """Проверка текста на фишинг"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "Текст не предоставлен"
            }), 400
        
        text = data['text']
        if not text or len(text.strip()) == 0:
            return jsonify({
                "success": False,
                "error": "Текст пустой"
            }), 400
        
        # Извлекаем URL, email, телефоны
        urls, emails, phones = extract_urls_emails_phones(text)
        has_url = len(urls) > 0
        has_email = len(emails) > 0
        has_phone = len(phones) > 0
        
        # Анализ через модель
        result = phishing_model.predict(text, has_url, has_email, has_phone)
        
        # Форматируем результат
        response = format_result_json(
            result=result,
            text=text,
            urls=urls,
            emails=emails,
            phones=phones,
            source="текст"
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке текста: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict/image', methods=['POST'])
def predict_image():
    """Проверка изображения на фишинг (OCR)"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "Файл не найден"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Файл не выбран"
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Разрешенные форматы: PNG, JPG, JPEG, GIF"
            }), 400
        
        # Сохраняем файл
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        
        file.save(str(filepath))
        
        try:
            # Извлекаем текст с помощью OCR
            extracted_text = extract_text_from_image(str(filepath))
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                return jsonify({
                    "success": False,
                    "error": "Не удалось распознать текст на изображении"
                }), 400
            
            # Извлекаем URL, email, телефоны
            urls, emails, phones = extract_urls_emails_phones(extracted_text)
            has_url = len(urls) > 0
            has_email = len(emails) > 0
            has_phone = len(phones) > 0
            
            # Анализ через модель
            result = phishing_model.predict(
                text=extracted_text,
                url=has_url,
                email=has_email,
                phone=has_phone
            )
            
            # Форматируем результат
            response = format_result_json(
                result=result,
                text=extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                urls=urls,
                emails=emails,
                phones=phones,
                source="изображение (OCR)"
            )
            
            return jsonify(response)
            
        finally:
            # Удаляем временный файл
            if filepath.exists():
                filepath.unlink()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке изображения: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/predict/eml', methods=['POST'])
def predict_eml():
    """Проверка .eml файла на фишинг"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "Файл не найден"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Файл не выбран"
            }), 400
        
        if not file.filename.lower().endswith('.eml'):
            return jsonify({
                "success": False,
                "error": "Разрешен только .eml файл"
            }), 400
        
        # Сохраняем файл
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        
        file.save(str(filepath))
        
        try:
            # Парсим .eml файл
            email_data = parse_eml_file(str(filepath))
            
            if not email_data.get('body'):
                return jsonify({
                    "success": False,
                    "error": "Не удалось извлечь содержимое письма"
                }), 400
            
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
            result = phishing_model.predict(
                text=full_text,
                url=has_url,
                email=has_email,
                phone=has_phone
            )
            
            # Форматируем результат с дополнительной информацией о письме
            response = format_result_json(
                result=result,
                text=full_text[:500] + "..." if len(full_text) > 500 else full_text,
                urls=urls,
                emails=emails,
                phones=phones,
                source=".eml файл",
                email_info=email_data
            )
            
            return jsonify(response)
            
        finally:
            # Удаляем временный файл
            if filepath.exists():
                filepath.unlink()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке .eml: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    # Для локальной разработки
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Для продакшена с Gunicorn
    pass

