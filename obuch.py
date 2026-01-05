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

print("="*70)
print("ОБУЧЕНИЕ МОДЕЛИ НА ОБЪЕДИНЕННОМ ДАТАСЕТЕ")
print("="*70)

# ============================================================================
# ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ И ОБРАБОТКИ ДАТАСЕТОВ
# ============================================================================

def load_dataset_5971(bases_dir):
    """Загрузка Dataset_5971.csv"""
    print("\n[1/3] Загрузка Dataset_5971.csv...")
    dataset_path = os.path.join(bases_dir, "Dataset_5971.csv")
    
    try:
        df = pd.read_csv(dataset_path, encoding='utf-8')
        print(f"   Загружено: {len(df)} записей")
        
        # Создаем бинарную метку: фишинг (1) или нет (0)
        # Smishing и spam считаем фишингом, ham - нет
        df['is_phishing'] = df['LABEL'].apply(
            lambda x: 1 if str(x).lower() in ['smishing', 'spam'] else 0
        )
        
        # Извлекаем текст и признаки
        texts = df['TEXT'].fillna('').astype(str)
        has_url = df['URL'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        has_email = df['EMAIL'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        has_phone = df['PHONE'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        labels = df['is_phishing'].values
        
        print(f"   Фишинг: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Безопасно: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
        result_df = pd.DataFrame({
            'text': texts,
            'has_url': has_url,
            'has_email': has_email,
            'has_phone': has_phone,
            'label': labels,
            'source': 'Dataset_5971'
        })
        
        return result_df
        
    except Exception as e:
        print(f"   ОШИБКА при загрузке Dataset_5971.csv: {e}")
        return pd.DataFrame()


def load_phishing_email(bases_dir):
    """Загрузка Phishing_Email.csv"""
    print("\n[2/3] Загрузка Phishing_Email.csv...")
    dataset_path = os.path.join(bases_dir, "Phishing_Email.csv")
    
    try:
        df = pd.read_csv(dataset_path, encoding='utf-8')
        print(f"   Загружено: {len(df)} записей")
        
        # Создаем бинарную метку
        df['is_phishing'] = df['Email Type'].apply(
            lambda x: 1 if str(x).lower() == 'phishing email' else 0
        )
        
        # Извлекаем текст
        texts = df['Email Text'].fillna('').astype(str)
        labels = df['is_phishing'].values
        
        # Для email датасета определяем наличие URL/EMAIL/PHONE из текста
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}')
        
        has_url = texts.apply(lambda x: 1 if url_pattern.search(str(x)) else 0)
        has_email = texts.apply(lambda x: 1 if email_pattern.search(str(x)) else 0)
        has_phone = texts.apply(lambda x: 1 if phone_pattern.search(str(x)) else 0)
        
        print(f"   Фишинг: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Безопасно: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
        result_df = pd.DataFrame({
            'text': texts,
            'has_url': has_url,
            'has_email': has_email,
            'has_phone': has_phone,
            'label': labels,
            'source': 'Phishing_Email'
        })
        
        return result_df
        
    except Exception as e:
        print(f"   ОШИБКА при загрузке Phishing_Email.csv: {e}")
        return pd.DataFrame()


def load_phiusiil_url(bases_dir):
    """Загрузка PhiUSIIL_Phishing_URL_Dataset.csv"""
    print("\n[3/3] Загрузка PhiUSIIL_Phishing_URL_Dataset.csv...")
    dataset_path = os.path.join(bases_dir, "PhiUSIIL_Phishing_URL_Dataset.csv")
    
    try:
        # Читаем только нужные колонки для экономии памяти
        df = pd.read_csv(dataset_path, encoding='utf-8', usecols=['URL', 'label'])
        print(f"   Загружено: {len(df)} записей")
        
        # Метка уже должна быть 0/1, но проверим
        labels = df['label'].fillna(0).astype(int)
        
        # Используем URL как текст
        texts = df['URL'].fillna('').astype(str)
        
        # Для URL датасета: URL всегда есть, email и phone определяем из URL
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}')
        
        has_url = pd.Series([1] * len(texts))  # Всегда есть URL
        has_email = texts.apply(lambda x: 1 if email_pattern.search(str(x)) else 0)
        has_phone = texts.apply(lambda x: 1 if phone_pattern.search(str(x)) else 0)
        
        print(f"   Фишинг: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Безопасно: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
        result_df = pd.DataFrame({
            'text': texts,
            'has_url': has_url,
            'has_email': has_email,
            'has_phone': has_phone,
            'label': labels,
            'source': 'PhiUSIIL_URL'
        })
        
        return result_df
        
    except Exception as e:
        print(f"   ОШИБКА при загрузке PhiUSIIL_Phishing_URL_Dataset.csv: {e}")
        print(f"   Пробуем загрузить все колонки...")
        try:
            df = pd.read_csv(dataset_path, encoding='utf-8')
            if 'label' not in df.columns:
                print(f"   Колонка 'label' не найдена. Доступные колонки: {list(df.columns)[:10]}")
                return pd.DataFrame()
            labels = df['label'].fillna(0).astype(int)
            texts = df['URL'].fillna('').astype(str)
            has_url = pd.Series([1] * len(texts))
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}')
            has_email = texts.apply(lambda x: 1 if email_pattern.search(str(x)) else 0)
            has_phone = texts.apply(lambda x: 1 if phone_pattern.search(str(x)) else 0)
            result_df = pd.DataFrame({
                'text': texts,
                'has_url': has_url,
                'has_email': has_email,
                'has_phone': has_phone,
                'label': labels,
                'source': 'PhiUSIIL_URL'
            })
            return result_df
        except Exception as e2:
            print(f"   ОШИБКА при повторной загрузке: {e2}")
            return pd.DataFrame()


# ============================================================================
# ОБЪЕДИНЕНИЕ ДАТАСЕТОВ
# ============================================================================

bases_dir = os.path.join(os.path.dirname(__file__), "bases")

print("\n" + "="*70)
print("ЗАГРУЗКА ДАТАСЕТОВ")
print("="*70)

# Загружаем все датасеты
df1 = load_dataset_5971(bases_dir)
df2 = load_phishing_email(bases_dir)
df3 = load_phiusiil_url(bases_dir)

# Объединяем
dataframes = [df for df in [df1, df2, df3] if not df.empty]

if not dataframes:
    print("\nОШИБКА: Не удалось загрузить ни один датасет!")
    exit(1)

df_combined = pd.concat(dataframes, ignore_index=True)

print("\n" + "="*70)
print("ОБЪЕДИНЕННЫЙ ДАТАСЕТ")
print("="*70)
print(f"\nВсего записей: {len(df_combined)}")
print(f"\nРаспределение по источникам:")
print(df_combined['source'].value_counts())
print(f"\nОбщее распределение меток:")
print(f"  Фишинг: {df_combined['label'].sum()} ({df_combined['label'].sum()/len(df_combined)*100:.2f}%)")
print(f"  Безопасно: {(df_combined['label']==0).sum()} ({(df_combined['label']==0).sum()/len(df_combined)*100:.2f}%)")

# ============================================================================
# ПОДГОТОВКА ДАННЫХ
# ============================================================================

print("\n" + "="*70)
print("ПОДГОТОВКА ДАННЫХ")
print("="*70)

def clean_text(text):
    """Очистка и предобработка текста"""
    if pd.isna(text):
        return ""
    text = str(text)
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем специальные символы, но оставляем буквы, цифры и основные знаки
    text = re.sub(r'[^\w\s.,!?@:/]', ' ', text)
    return text.strip().lower()

# Применяем очистку
print("\nОчистка текста...")
df_combined['text_cleaned'] = df_combined['text'].apply(clean_text)

# Удаляем пустые тексты
df_combined = df_combined[df_combined['text_cleaned'].str.len() > 0]

print(f"После очистки осталось записей: {len(df_combined)}")

# Подготовка признаков
X_text = df_combined['text_cleaned'].values
y = df_combined['label'].values

# Дополнительные признаки
X_features = df_combined[['has_url', 'has_email', 'has_phone']].values

# Векторизация текста с помощью TF-IDF
print("\nВекторизация текста...")
vectorizer = TfidfVectorizer(
    max_features=10000,  # Увеличиваем для большего объема данных
    ngram_range=(1, 2),  # униграммы и биграммы
    min_df=2,
    max_df=0.95,
    stop_words='english'
)

X_tfidf = vectorizer.fit_transform(X_text)
print(f"Размерность TF-IDF матрицы: {X_tfidf.shape}")

# Объединяем текстовые признаки с дополнительными
from scipy.sparse import hstack
X_combined = hstack([X_tfidf, X_features])

# Разделение на обучающую и тестовую выборки
print("\nРазделение на train/test...")
X_train, X_test, y_train, y_test = train_test_split(
    X_combined, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Обучающая выборка: {X_train.shape[0]} записей")
print(f"Тестовая выборка: {X_test.shape[0]} записей")

# ============================================================================
# ОБУЧЕНИЕ МОДЕЛЕЙ
# ============================================================================

# Обучение модели Random Forest
print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ RANDOM FOREST")
print("="*70)

rf_model = RandomForestClassifier(
    n_estimators=200,  # Увеличиваем для лучшего качества
    max_depth=25,
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
print("\nРЕЗУЛЬТАТЫ ОБУЧЕНИЯ - Random Forest")
print("="*70)
print(f"\nТочность (Accuracy): {accuracy_score(y_test, y_pred_rf):.4f}")
print("\nОтчет о классификации:")
print(classification_report(y_test, y_pred_rf, target_names=['Не фишинг', 'Фишинг']))
print("\nМатрица ошибок:")
print(confusion_matrix(y_test, y_pred_rf))

# Обучение модели Logistic Regression (для сравнения)
print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ LOGISTIC REGRESSION")
print("="*70)

lr_model = LogisticRegression(
    max_iter=2000,
    random_state=42,
    class_weight='balanced',
    C=1.0,
    n_jobs=-1
)

lr_model.fit(X_train, y_train)

# Предсказания
y_pred_lr = lr_model.predict(X_test)
y_pred_proba_lr = lr_model.predict_proba(X_test)[:, 1]

# Метрики для Logistic Regression
print("\nРЕЗУЛЬТАТЫ ОБУЧЕНИЯ - Logistic Regression")
print("="*70)
print(f"\nТочность (Accuracy): {accuracy_score(y_test, y_pred_lr):.4f}")
print("\nОтчет о классификации:")
print(classification_report(y_test, y_pred_lr, target_names=['Не фишинг', 'Фишинг']))
print("\nМатрица ошибок:")
print(confusion_matrix(y_test, y_pred_lr))

# ============================================================================
# СОХРАНЕНИЕ МОДЕЛЕЙ
# ============================================================================

print("\n" + "="*70)
print("СОХРАНЕНИЕ МОДЕЛЕЙ")
print("="*70)

model_dir = os.path.dirname(__file__)
modelN_dir = os.path.join(model_dir, "modelN")

# Создаем папку modelN если её нет
os.makedirs(modelN_dir, exist_ok=True)

# Сохраняем Random Forest модель (лучшая)
model_path = os.path.join(modelN_dir, "phishing_model_rf.pkl")
vectorizer_path = os.path.join(modelN_dir, "tfidf_vectorizer.pkl")

with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print(f"Модель RF сохранена: {model_path}")
print(f"Векторизатор сохранен: {vectorizer_path}")

# Сохраняем также Logistic Regression для сравнения
lr_model_path = os.path.join(modelN_dir, "phishing_model_lr.pkl")
with open(lr_model_path, 'wb') as f:
    pickle.dump(lr_model, f)

print(f"Модель LR сохранена: {lr_model_path}")

# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

# Функция для предсказания процента фишинга
def predict_phishing_percentage(text, url=False, email=False, phone=False):
    """Предсказание процента фишинга для нового текста"""
    # Очистка текста
    text_cleaned = clean_text(text)
    
    # Векторизация
    text_tfidf = vectorizer.transform([text_cleaned])
    
    # Дополнительные признаки
    features = [[1 if url else 0, 1 if email else 0, 1 if phone else 0]]
    
    # Объединение
    X_new = hstack([text_tfidf, features])
    
    # Предсказание вероятности
    proba = rf_model.predict_proba(X_new)[0, 1]
    
    return proba * 100  # Возвращаем в процентах

print("\n" + "="*70)
print("ТЕСТИРОВАНИЕ НА ПРИМЕРАХ")
print("="*70)

test_examples = [
    ("Your opinion about me? 1. Over 2. Jada", False, False, False),
    ("BankOfAmerica Alert 137943. Please follow http://bit.do/cgjK-and re-activate", True, False, True),
    ("Please Stay At Home. All tax-paying citizens are entitled to $305.96 or more emergency refund. smsg.io/fCVbD", True, False, False),
    ("Click here to verify your account: https://secure-bank.com/verify", True, False, False),
    ("Hello, this is a normal email from a friend.", False, False, False),
]

for text, url, email, phone in test_examples:
    percentage = predict_phishing_percentage(text, url, email, phone)
    print(f"\nТекст: {text[:60]}...")
    print(f"URL: {url}, EMAIL: {email}, PHONE: {phone}")
    print(f"Вероятность фишинга: {percentage:.2f}%")

print("\n" + "="*70)
print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
print("="*70)
print(f"\nИспользовано датасетов: {len(dataframes)}")
print(f"Всего записей для обучения: {len(df_combined)}")
print(f"Точность модели (RF): {accuracy_score(y_test, y_pred_rf):.4f}")
