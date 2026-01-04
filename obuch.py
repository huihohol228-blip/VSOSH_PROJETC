import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import re
import os

# Загрузка датасета
print("Загрузка датасета...")
dataset_path = os.path.join(os.path.dirname(__file__), "Dataset_5971.csv")
df = pd.read_csv(dataset_path, encoding='utf-8')

print(f"Загружено записей: {len(df)}")
print(f"Колонки: {df.columns.tolist()}")
print(f"\nРаспределение меток:")
print(df['LABEL'].value_counts())

# Подготовка данных
print("\nПодготовка данных...")

# Создаем бинарную метку: фишинг (1) или нет (0)
# Smishing и spam считаем фишингом, ham - нет
df['is_phishing'] = df['LABEL'].apply(lambda x: 1 if x.lower() in ['smishing', 'spam'] else 0)

print(f"\nРаспределение классов:")
print(df['is_phishing'].value_counts())
print(f"Фишинг: {df['is_phishing'].sum()} ({df['is_phishing'].sum()/len(df)*100:.2f}%)")
print(f"Не фишинг: {(df['is_phishing']==0).sum()} ({(df['is_phishing']==0).sum()/len(df)*100:.2f}%)")

# Очистка текста
def clean_text(text):
    """Очистка и предобработка текста"""
    if pd.isna(text):
        return ""
    text = str(text)
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем специальные символы, но оставляем буквы, цифры и основные знаки
    text = re.sub(r'[^\w\s.,!?]', ' ', text)
    return text.strip().lower()

# Применяем очистку
df['TEXT_cleaned'] = df['TEXT'].apply(clean_text)

# Удаляем пустые тексты
df = df[df['TEXT_cleaned'].str.len() > 0]

print(f"\nПосле очистки осталось записей: {len(df)}")

# Подготовка признаков
X_text = df['TEXT_cleaned'].values
y = df['is_phishing'].values

# Дополнительные признаки из URL, EMAIL, PHONE
X_features = df[['URL', 'EMAIL', 'PHONE']].apply(
    lambda x: [1 if str(val).lower() in ['yes', 'true', '1'] else 0 for val in x], 
    axis=1
).tolist()

# Векторизация текста с помощью TF-IDF
print("\nВекторизация текста...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),  # униграммы и биграммы
    min_df=2,
    max_df=0.95,
    stop_words='english'
)

X_tfidf = vectorizer.fit_transform(X_text)
print(f"Размерность TF-IDF матрицы: {X_tfidf.shape}")

# Объединяем текстовые признаки с дополнительными
from scipy.sparse import hstack
X_features_sparse = np.array(X_features)
X_combined = hstack([X_tfidf, X_features_sparse])

# Разделение на обучающую и тестовую выборки
print("\nРазделение на train/test...")
X_train, X_test, y_train, y_test = train_test_split(
    X_combined, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Обучающая выборка: {X_train.shape[0]} записей")
print(f"Тестовая выборка: {X_test.shape[0]} записей")

# Обучение модели Random Forest
print("\nОбучение модели Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'
)

rf_model.fit(X_train, y_train)

# Предсказания
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

# Метрики для Random Forest
print("\n" + "="*50)
print("РЕЗУЛЬТАТЫ ОБУЧЕНИЯ - Random Forest")
print("="*50)
print(f"\nТочность (Accuracy): {accuracy_score(y_test, y_pred_rf):.4f}")
print("\nОтчет о классификации:")
print(classification_report(y_test, y_pred_rf, target_names=['Не фишинг', 'Фишинг']))
print("\nМатрица ошибок:")
print(confusion_matrix(y_test, y_pred_rf))

# Обучение модели Logistic Regression (для сравнения)
print("\n" + "="*50)
print("Обучение модели Logistic Regression...")
print("="*50)
lr_model = LogisticRegression(
    max_iter=1000,
    random_state=42,
    class_weight='balanced',
    C=1.0
)

lr_model.fit(X_train, y_train)

# Предсказания
y_pred_lr = lr_model.predict(X_test)
y_pred_proba_lr = lr_model.predict_proba(X_test)[:, 1]

# Метрики для Logistic Regression
print("\nРЕЗУЛЬТАТЫ ОБУЧЕНИЯ - Logistic Regression")
print("="*50)
print(f"\nТочность (Accuracy): {accuracy_score(y_test, y_pred_lr):.4f}")
print("\nОтчет о классификации:")
print(classification_report(y_test, y_pred_lr, target_names=['Не фишинг', 'Фишинг']))
print("\nМатрица ошибок:")
print(confusion_matrix(y_test, y_pred_lr))

# Сохранение лучшей модели (выбираем Random Forest)
print("\n" + "="*50)
print("Сохранение модели...")
print("="*50)

model_dir = os.path.dirname(__file__)
modelN_dir = os.path.join(model_dir, "modelN")

# Создаем папку modelN если её нет
os.makedirs(modelN_dir, exist_ok=True)

# Сохраняем Random Forest модель
model_path = os.path.join(modelN_dir, "phishing_model_rf.pkl")
vectorizer_path = os.path.join(modelN_dir, "tfidf_vectorizer.pkl")

with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print(f"Модель сохранена: {model_path}")
print(f"Векторизатор сохранен: {vectorizer_path}")

# Сохраняем также Logistic Regression для сравнения
lr_model_path = os.path.join(modelN_dir, "phishing_model_lr.pkl")
with open(lr_model_path, 'wb') as f:
    pickle.dump(lr_model, f)

print(f"Модель LR сохранена: {lr_model_path}")

# Функция для предсказания процента фишинга
def predict_phishing_percentage(text, url=False, email=False, phone=False):
    """Предсказание процента фишинга для нового текста"""
    # Очистка текста
    text_cleaned = clean_text(text)
    
    # Векторизация
    text_tfidf = vectorizer.transform([text_cleaned])
    
    # Дополнительные признаки
    features = [[1 if url else 0, 1 if email else 0, 1 if phone else 0]]
    features_sparse = np.array(features)
    
    # Объединение
    X_new = hstack([text_tfidf, features_sparse])
    
    # Предсказание вероятности
    proba = rf_model.predict_proba(X_new)[0, 1]
    
    return proba * 100  # Возвращаем в процентах

# Тестирование на нескольких примерах
print("\n" + "="*50)
print("ТЕСТИРОВАНИЕ НА ПРИМЕРАХ")
print("="*50)

test_examples = [
    ("Your opinion about me? 1. Over 2. Jada", False, False, False),
    ("BankOfAmerica Alert 137943. Please follow http://bit.do/cgjK-and re-activate", True, False, True),
    ("Please Stay At Home. All tax-paying citizens are entitled to $305.96 or more emergency refund. smsg.io/fCVbD", True, False, False),
]

for text, url, email, phone in test_examples:
    percentage = predict_phishing_percentage(text, url, email, phone)
    print(f"\nТекст: {text[:60]}...")
    print(f"URL: {url}, EMAIL: {email}, PHONE: {phone}")
    print(f"Вероятность фишинга: {percentage:.2f}%")

print("\n" + "="*50)
print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
print("="*50)

