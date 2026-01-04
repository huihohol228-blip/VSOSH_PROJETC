#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Веб-приложение для проверки на фишинг (Production версия)
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from flask_cors import CORS
import logging

# Добавляем путь к modelN для импорта модели
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "modelN"))

# Импорт модели
try:
    from model_loader import PhishingModel
except ImportError as e:
    print(f"Warning: Could not import model_loader: {e}")
    PhishingModel = None

# Импорт утилит из текущей папки
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
try:
    from utils import (
        extract_urls_emails_phones,
        extract_text_from_image,
        parse_eml_file,
        format_result_json
    )
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")
    extract_urls_emails_phones = None
    extract_text_from_image = None
    parse_eml_file = None
    format_result_json = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
_model_loading_attempted = False


def load_model():
    """Загрузка модели"""
    global phishing_model, _model_loading_attempted
    if _model_loading_attempted:
        return phishing_model is not None
    
    _model_loading_attempted = True
    if PhishingModel is None:
        logger.error("PhishingModel class not available")
        return False
    
    try:
        model_dir = project_root / "modelN"
        phishing_model = PhishingModel(model_dir=str(model_dir))
        logger.info("✓ Модель успешно загружена")
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки модели: {e}")
        import traceback
        logger.error(traceback.format_exc())
        phishing_model = None
        return False


# Пытаемся загрузить модель при старте (но не падаем если не получилось)
try:
    load_model()
except Exception as e:
    logger.warning(f"Модель не загружена при старте: {e}")


@app.route('/')
def index():
    """Главная страница"""
    try:
        return render_template('index.html')
    except:
        return "<h1>Phishing Detector API</h1><p>API работает. Используйте /api/health для проверки.</p>"


@app.route('/webapp')
def webapp():
    """Telegram Web App версия"""
    webapp_path = project_root / "web_tg" / "index.html"
    if webapp_path.exists():
        try:
            with open(webapp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('href="style.css"', 'href="/webapp/style.css"')
            content = content.replace('src="app.js"', 'src="/webapp/app.js"')
            return Response(content, mimetype='text/html')
        except Exception as e:
            logger.error(f"Error loading webapp: {e}")
    return "<h1>Web App</h1><p>Web App файлы не найдены</p>"


@app.route('/webapp/<path:filename>')
def webapp_static(filename):
    """Статические файлы для Web App"""
    webapp_dir = project_root / "web_tg"
    file_path = webapp_dir / filename
    
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


@app.route('/api/health', methods=['GET'])
def health():
    """Проверка здоровья API - ВСЕГДА возвращает 200"""
    try:
        model_loaded = load_model()
        return jsonify({
            "status": "ok",
            "model_loaded": model_loaded,
            "service": "phishing-detector"
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        # ВСЕГДА возвращаем 200 для healthcheck
        return jsonify({
            "status": "ok",
            "model_loaded": False,
            "error": str(e)
        }), 200


@app.route('/api/predict/text', methods=['POST'])
def predict_text():
    """Проверка текста на фишинг"""
    if not load_model() or phishing_model is None:
        return jsonify({
            "success": False,
            "error": "Модель не загружена"
        }), 503
    
    if not extract_urls_emails_phones:
        return jsonify({
            "success": False,
            "error": "Utils не загружены"
        }), 500
    
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
        
        urls, emails, phones = extract_urls_emails_phones(text)
        has_url = len(urls) > 0
        has_email = len(emails) > 0
        has_phone = len(phones) > 0
        
        result = phishing_model.predict(text, has_url, has_email, has_phone)
        
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
    if not load_model() or phishing_model is None:
        return jsonify({
            "success": False,
            "error": "Модель не загружена"
        }), 503
    
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
        
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(str(filepath))
        
        try:
            if not extract_text_from_image:
                return jsonify({
                    "success": False,
                    "error": "OCR не доступен"
                }), 500
            
            extracted_text = extract_text_from_image(str(filepath))
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                return jsonify({
                    "success": False,
                    "error": "Не удалось распознать текст"
                }), 400
            
            urls, emails, phones = extract_urls_emails_phones(extracted_text)
            has_url = len(urls) > 0
            has_email = len(emails) > 0
            has_phone = len(phones) > 0
            
            result = phishing_model.predict(
                text=extracted_text,
                url=has_url,
                email=has_email,
                phone=has_phone
            )
            
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
    if not load_model() or phishing_model is None:
        return jsonify({
            "success": False,
            "error": "Модель не загружена"
        }), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "Файл не найден"
            }), 400
        
        file = request.files['file']
        if not file.filename or not file.filename.lower().endswith('.eml'):
            return jsonify({
                "success": False,
                "error": "Разрешен только .eml файл"
            }), 400
        
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(str(filepath))
        
        try:
            if not parse_eml_file:
                return jsonify({
                    "success": False,
                    "error": "EML парсер не доступен"
                }), 500
            
            email_data = parse_eml_file(str(filepath))
            
            if not email_data.get('body'):
                return jsonify({
                    "success": False,
                    "error": "Не удалось извлечь содержимое"
                }), 400
            
            full_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
            
            urls, emails, phones = extract_urls_emails_phones(full_text)
            
            if email_data.get('from'):
                emails.append(email_data['from'])
            if email_data.get('to'):
                emails.extend([e.strip() for e in email_data['to'].split(',')])
            
            has_url = len(urls) > 0
            has_email = len(emails) > 0
            has_phone = len(phones) > 0
            
            result = phishing_model.predict(
                text=full_text,
                url=has_url,
                email=has_email,
                phone=has_phone
            )
            
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
            if filepath.exists():
                filepath.unlink()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке .eml: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    print(f"Health check: http://0.0.0.0:{port}/api/health")
    app.run(host='0.0.0.0', port=port, debug=False)
