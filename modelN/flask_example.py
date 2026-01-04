"""
Пример Flask приложения для использования модели определения фишинга
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from model_loader import get_model
import os

app = Flask(__name__)
# Включаем CORS для работы с Chrome расширением
CORS(app, resources={r"/*": {"origins": "*"}})

# Загружаем модель при старте приложения
model_dir = os.path.dirname(os.path.abspath(__file__))
phishing_model = get_model(model_dir)

@app.route('/')
def index():
    """Главная страница"""
    return jsonify({
        "message": "API для определения фишинга",
        "endpoints": {
            "/predict": "POST - предсказание фишинга",
            "/health": "GET - проверка работоспособности"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Проверка работоспособности API"""
    return jsonify({
        "status": "ok",
        "model_loaded": phishing_model.model is not None
    })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Предсказание вероятности фишинга
    
    Пример запроса:
    {
        "text": "BankOfAmerica Alert. Please follow http://bit.do/cgjK",
        "url": true,
        "email": false,
        "phone": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "error": "Отсутствует поле 'text' в запросе"
            }), 400
        
        text = data.get('text', '')
        url = data.get('url', False)
        email = data.get('email', False)
        phone = data.get('phone', False)
        
        # Получаем предсказание
        result = phishing_model.predict(text, url, email, phone)
        
        return jsonify({
            "success": True,
            "result": {
                "phishing_percentage": round(result['percentage'], 2),
                "is_phishing": result['is_phishing'],
                "confidence": round(result['confidence'], 2)
            },
            "input": {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "url": url,
                "email": email,
                "phone": phone
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/predict/simple', methods=['POST'])
def predict_simple():
    """
    Упрощенный endpoint - возвращает только процент фишинга
    
    Пример запроса:
    {
        "text": "Your normal message here"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "error": "Отсутствует поле 'text' в запросе"
            }), 400
        
        text = data.get('text', '')
        url = data.get('url', False)
        email = data.get('email', False)
        phone = data.get('phone', False)
        
        percentage = phishing_model.predict_percentage(text, url, email, phone)
        
        return jsonify({
            "phishing_percentage": round(percentage, 2)
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("Запуск Flask сервера...")
    print("API доступно по адресу: http://localhost:5000")
    print("\nПримеры использования:")
    print("POST http://localhost:5000/predict")
    print('{"text": "Your message here", "url": false, "email": false, "phone": false}')
    
    app.run(debug=True, host='0.0.0.0', port=5000)

