"""
Модуль для загрузки и использования модели определения фишинга
Готов для использования в Flask приложении
"""

import pickle
import os
import re
import numpy as np
from scipy.sparse import hstack

class PhishingModel:
    """Класс для работы с моделью определения фишинга"""
    
    def __init__(self, model_dir=None):
        """
        Инициализация модели
        
        Args:
            model_dir: Путь к директории с моделями. 
                      Если None, используется текущая директория
        """
        if model_dir is None:
            # Определяем путь к папке modelN относительно этого файла
            model_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.model_dir = model_dir
        self.model = None
        self.vectorizer = None
        self.load_model()
    
    def load_model(self):
        """Загрузка модели и векторизатора (использует Logistic Regression - лучшая точность 98.82%)"""
        model_path = os.path.join(self.model_dir, "phishing_model_lr.pkl")
        vectorizer_path = os.path.join(self.model_dir, "tfidf_vectorizer.pkl")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель не найдена: {model_path}")
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Векторизатор не найден: {vectorizer_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        print(f"Модель загружена из {model_path}")
        print(f"Векторизатор загружен из {vectorizer_path}")
    
    def clean_text(self, text):
        """Очистка и предобработка текста"""
        if text is None:
            return ""
        text = str(text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        # Удаляем специальные символы, но оставляем буквы, цифры и основные знаки (включая @ и / для URL и email)
        text = re.sub(r'[^\w\s.,!?@:/]', ' ', text)
        return text.strip().lower()
    
    def predict(self, text, url=False, email=False, phone=False):
        """
        Предсказание вероятности фишинга
        
        Args:
            text: Текст для анализа
            url: Наличие URL в тексте (bool)
            email: Наличие email в тексте (bool)
            phone: Наличие телефона в тексте (bool)
        
        Returns:
            dict: Словарь с результатами:
                - percentage: процент вероятности фишинга (0-100)
                - is_phishing: бинарное предсказание (True/False)
                - confidence: уверенность модели
        """
        if self.model is None or self.vectorizer is None:
            raise ValueError("Модель не загружена. Вызовите load_model()")
        
        # Очистка текста
        text_cleaned = self.clean_text(text)
        
        if len(text_cleaned) == 0:
            return {
                'percentage': 0.0,
                'is_phishing': False,
                'confidence': 0.0
            }
        
        # Векторизация
        text_tfidf = self.vectorizer.transform([text_cleaned])
        
        # Дополнительные признаки
        features = [[1 if url else 0, 1 if email else 0, 1 if phone else 0]]
        features_sparse = np.array(features)
        
        # Объединение
        X_new = hstack([text_tfidf, features_sparse])
        
        # Предсказание вероятности
        proba = self.model.predict_proba(X_new)[0, 1]
        prediction = self.model.predict(X_new)[0]
        
        return {
            'percentage': float(proba * 100),
            'is_phishing': bool(prediction == 1),
            'confidence': float(max(proba, 1 - proba) * 100)
        }
    
    def predict_percentage(self, text, url=False, email=False, phone=False):
        """
        Упрощенный метод - возвращает только процент фишинга
        
        Args:
            text: Текст для анализа
            url: Наличие URL в тексте (bool)
            email: Наличие email в тексте (bool)
            phone: Наличие телефона в тексте (bool)
        
        Returns:
            float: Процент вероятности фишинга (0-100)
        """
        result = self.predict(text, url, email, phone)
        return result['percentage']


# Глобальный экземпляр модели для использования в Flask
_model_instance = None

def get_model(model_dir=None):
    """
    Получить глобальный экземпляр модели (singleton pattern)
    Удобно для использования в Flask приложении
    
    Args:
        model_dir: Путь к директории с моделями
    
    Returns:
        PhishingModel: Экземпляр модели
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = PhishingModel(model_dir)
    return _model_instance


# Пример использования
if __name__ == "__main__":
    # Инициализация модели
    model = PhishingModel()
    
    # Тестовые примеры
    test_cases = [
        {
            "text": "Your opinion about me? 1. Over 2. Jada",
            "url": False,
            "email": False,
            "phone": False
        },
        {
            "text": "BankOfAmerica Alert 137943. Please follow http://bit.do/cgjK-and re-activate",
            "url": True,
            "email": False,
            "phone": True
        },
        {
            "text": "Please Stay At Home. All tax-paying citizens are entitled to $305.96 or more emergency refund. smsg.io/fCVbD",
            "url": True,
            "email": False,
            "phone": False
        }
    ]
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        result = model.predict(
            test["text"],
            test["url"],
            test.get("email", False),
            test.get("phone", False)
        )
        
        print(f"\nТест {i}:")
        print(f"Текст: {test['text'][:60]}...")
        print(f"URL: {test['url']}, EMAIL: {test.get('email', False)}, PHONE: {test.get('phone', False)}")
        print(f"Вероятность фишинга: {result['percentage']:.2f}%")
        print(f"Это фишинг: {result['is_phishing']}")
        print(f"Уверенность: {result['confidence']:.2f}%")

