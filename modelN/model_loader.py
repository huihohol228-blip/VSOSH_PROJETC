import pickle
import os
import re
import numpy as np
from scipy.sparse import hstack

class PhishingModel:
    
    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.model_dir = model_dir
        self.model = None
        self.vectorizer = None
        self.load_model()
    
    def load_model(self):
        model_path = os.path.join(self.model_dir, "phishing_model_lr.pkl")
        vectorizer_path = os.path.join(self.model_dir, "tfidf_vectorizer.pkl")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Vectorizer not found: {vectorizer_path}")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
    
    def clean_text(self, text):
        if text is None:
            return ""
        text = str(text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?@:/]', ' ', text)
        return text.strip().lower()
    
    def predict(self, text, url=False, email=False, phone=False):
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model not loaded. Call load_model()")
        
        text_cleaned = self.clean_text(text)
        
        if len(text_cleaned) == 0:
            return {
                'percentage': 0.0,
                'is_phishing': False,
                'confidence': 0.0
            }
        
        text_tfidf = self.vectorizer.transform([text_cleaned])
        
        features = [[1 if url else 0, 1 if email else 0, 1 if phone else 0]]
        features_sparse = np.array(features)
        
        X_new = hstack([text_tfidf, features_sparse])
        
        proba = self.model.predict_proba(X_new)[0, 1]
        prediction = self.model.predict(X_new)[0]
        
        return {
            'percentage': float(proba * 100),
            'is_phishing': bool(prediction == 1),
            'confidence': float(max(proba, 1 - proba) * 100)
        }
    
    def predict_percentage(self, text, url=False, email=False, phone=False):
        result = self.predict(text, url, email, phone)
        return result['percentage']


_model_instance = None

def get_model(model_dir=None):
    global _model_instance
    if _model_instance is None:
        _model_instance = PhishingModel(model_dir)
    return _model_instance


if __name__ == "__main__":
    model = PhishingModel()
    
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
    print("TESTING MODEL")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        result = model.predict(
            test["text"],
            test["url"],
            test.get("email", False),
            test.get("phone", False)
        )
        
        print(f"\nTest {i}:")
        print(f"Text: {test['text'][:60]}...")
        print(f"URL: {test['url']}, EMAIL: {test.get('email', False)}, PHONE: {test.get('phone', False)}")
        print(f"Phishing probability: {result['percentage']:.2f}%")
        print(f"Is phishing: {result['is_phishing']}")
        print(f"Confidence: {result['confidence']:.2f}%")
