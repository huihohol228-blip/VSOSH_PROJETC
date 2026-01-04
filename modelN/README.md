# Модель определения фишинга

Эта папка содержит обученную модель для определения фишинга в текстовых сообщениях.

## Файлы

- `phishing_model_rf.pkl` - Обученная модель Random Forest
- `phishing_model_lr.pkl` - Обученная модель Logistic Regression (альтернатива)
- `tfidf_vectorizer.pkl` - Векторизатор текста (TF-IDF)
- `model_loader.py` - Модуль для загрузки и использования модели
- `flask_example.py` - Пример Flask приложения

## Использование модели

### Простой пример

```python
from model_loader import PhishingModel

# Инициализация модели
model = PhishingModel()

# Предсказание
result = model.predict(
    text="BankOfAmerica Alert. Please follow http://bit.do/cgjK",
    url=True,
    email=False,
    phone=False
)

print(f"Вероятность фишинга: {result['percentage']:.2f}%")
print(f"Это фишинг: {result['is_phishing']}")
```

### Использование в Flask

```python
from flask import Flask, request, jsonify
from model_loader import get_model

app = Flask(__name__)
model = get_model()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    result = model.predict(
        data['text'],
        data.get('url', False),
        data.get('email', False),
        data.get('phone', False)
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
```

### Запуск примера Flask приложения

```bash
cd modelN
python flask_example.py
```

Затем отправьте POST запрос:
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Your message here", "url": false, "email": false, "phone": false}'
```

## API Endpoints (Flask пример)

- `GET /` - Информация об API
- `GET /health` - Проверка работоспособности
- `POST /predict` - Полное предсказание с деталями
- `POST /predict/simple` - Упрощенное предсказание (только процент)

## Формат ответа

### POST /predict
```json
{
  "success": true,
  "result": {
    "phishing_percentage": 69.98,
    "is_phishing": true,
    "confidence": 69.98
  },
  "input": {
    "text": "BankOfAmerica Alert...",
    "url": true,
    "email": false,
    "phone": false
  }
}
```

### POST /predict/simple
```json
{
  "phishing_percentage": 69.98
}
```

## Параметры модели

- **Алгоритм**: Random Forest
- **Точность**: ~98%
- **Векторизация**: TF-IDF (5000 признаков)
- **Дополнительные признаки**: URL, EMAIL, PHONE

## Требования

```txt
pandas
scikit-learn
numpy
scipy
flask (для примера)
```

## Примечания

- Модель обучена на датасете с 5971 записями
- Поддерживает определение фишинга по тексту и дополнительным признакам
- Возвращает процент вероятности фишинга (0-100%)

