#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Вспомогательные функции для веб-приложения
"""

import os
import re
import email
from typing import List, Tuple, Dict, Optional

try:
    from PIL import Image
    import pytesseract
    import platform
    import shutil
    
    # Автоматическое определение пути к Tesseract для Windows
    if platform.system() == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            rf'C:\Users\{os.environ.get("USERNAME", "")}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
        tesseract_found = False
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                tesseract_found = True
                break
        
        if not tesseract_found:
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                tesseract_found = True
    
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_urls_emails_phones(text: str) -> Tuple[List[str], List[str], List[str]]:
    """Извлекает URL, email и телефоны из текста"""
    urls = []
    emails = []
    phones = []
    
    if not text:
        return urls, emails, phones
    
    # Извлечение URL
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+|ftp://[^\s]+)'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    # Извлечение email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    
    # Извлечение телефонов
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10,}',
        r'\+?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
    ]
    
    for pattern in phone_patterns:
        found_phones = re.findall(pattern, text)
        phones.extend(found_phones)
    
    # Убираем дубликаты
    urls = list(set(urls))
    emails = list(set(emails))
    phones = list(set(phones))
    
    return urls, emails, phones


def extract_text_from_image(image_path: str) -> str:
    """Извлекает текст из изображения с помощью OCR"""
    if not OCR_AVAILABLE:
        raise ImportError(
            "Библиотеки для OCR не установлены. Установите:\n"
            "pip install pytesseract pillow"
        )
    
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='eng+rus')
        return text.strip()
    except Exception as e:
        raise Exception(f"Ошибка при извлечении текста: {str(e)}")


def parse_eml_file(eml_path: str) -> Dict[str, str]:
    """Парсит .eml файл и извлекает данные"""
    try:
        with open(eml_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = email.message_from_file(f)
        
        email_data = {
            'from': msg.get('From', ''),
            'to': msg.get('To', ''),
            'subject': msg.get('Subject', ''),
            'date': msg.get('Date', ''),
            'body': ''
        }
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        email_data['body'] = body
        return email_data
        
    except Exception as e:
        raise Exception(f"Ошибка при парсинге .eml: {str(e)}")


def get_risk_level(percentage: float) -> Dict[str, str]:
    """Возвращает информацию об уровне риска"""
    if percentage < 30:
        return {
            'level': 'safe',
            'name': 'Безопасно',
            'emoji': '🟢',
            'color': '#28a745'
        }
    elif percentage < 50:
        return {
            'level': 'warning',
            'name': 'Подозрительно',
            'emoji': '🟡',
            'color': '#ffc107'
        }
    elif percentage < 70:
        return {
            'level': 'danger',
            'name': 'Опасно',
            'emoji': '🟠',
            'color': '#fd7e14'
        }
    else:
        return {
            'level': 'critical',
            'name': 'Критично',
            'emoji': '🔴',
            'color': '#dc3545'
        }


def format_result_json(
    result: Dict,
    text: str,
    urls: List[str],
    emails: List[str],
    phones: List[str],
    source: str = "неизвестно",
    email_info: Optional[Dict] = None
) -> Dict:
    """Форматирует результат для JSON ответа"""
    percentage = result.get('percentage', 0)
    is_phishing = result.get('is_phishing', False)
    confidence = result.get('confidence', 0)
    
    risk_info = get_risk_level(percentage)
    
    response = {
        'success': True,
        'result': {
            'percentage': round(percentage, 2),
            'is_phishing': is_phishing,
            'confidence': round(confidence, 2),
            'risk_level': risk_info['level'],
            'risk_name': risk_info['name'],
            'risk_emoji': risk_info['emoji'],
            'risk_color': risk_info['color']
        },
        'found': {
            'urls': urls[:10],  # Ограничиваем количество
            'emails': emails[:10],
            'phones': phones[:10],
            'url_count': len(urls),
            'email_count': len(emails),
            'phone_count': len(phones)
        },
        'source': source,
        'text_preview': text[:500] + "..." if len(text) > 500 else text,
        'text_length': len(text)
    }
    
    if email_info:
        response['email_info'] = email_info
    
    # Рекомендации
    if percentage >= 70:
        response['recommendation'] = 'Высокий риск! Не переходите по ссылкам и не вводите данные.'
    elif percentage >= 50:
        response['recommendation'] = 'Средний риск. Будьте осторожны, проверьте отправителя.'
    elif percentage >= 30:
        response['recommendation'] = 'Низкий риск. Возможны подозрительные элементы.'
    else:
        response['recommendation'] = 'Низкий риск. Скорее всего безопасно.'
    
    return response


