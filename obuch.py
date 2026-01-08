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
from scipy.sparse import hstack

print("="*70)
print("TRAINING MODEL ON COMBINED DATASET")
print("="*70)

def load_dataset_5971(bases_dir):
    print("\n[1/3] Loading Dataset_5971.csv...")
    dataset_path = os.path.join(bases_dir, "Dataset_5971.csv")
    
    try:
        df = pd.read_csv(dataset_path, encoding='utf-8')
        print(f"   Loaded: {len(df)} records")
        
        df['is_phishing'] = df['LABEL'].apply(
            lambda x: 1 if str(x).lower() in ['smishing', 'spam'] else 0
        )
        
        texts = df['TEXT'].fillna('').astype(str)
        has_url = df['URL'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        has_email = df['EMAIL'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        has_phone = df['PHONE'].apply(lambda x: 1 if str(x).lower() in ['yes', 'true', '1'] else 0)
        labels = df['is_phishing'].values
        
        print(f"   Phishing: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Safe: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
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
        print(f"   ERROR loading Dataset_5971.csv: {e}")
        return pd.DataFrame()


def load_phishing_email(bases_dir):
    print("\n[2/3] Loading Phishing_Email.csv...")
    dataset_path = os.path.join(bases_dir, "Phishing_Email.csv")
    
    try:
        df = pd.read_csv(dataset_path, encoding='utf-8')
        print(f"   Loaded: {len(df)} records")
        
        df['is_phishing'] = df['Email Type'].apply(
            lambda x: 1 if str(x).lower() == 'phishing email' else 0
        )
        
        texts = df['Email Text'].fillna('').astype(str)
        labels = df['is_phishing'].values
        
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}')
        
        has_url = texts.apply(lambda x: 1 if url_pattern.search(str(x)) else 0)
        has_email = texts.apply(lambda x: 1 if email_pattern.search(str(x)) else 0)
        has_phone = texts.apply(lambda x: 1 if phone_pattern.search(str(x)) else 0)
        
        print(f"   Phishing: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Safe: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
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
        print(f"   ERROR loading Phishing_Email.csv: {e}")
        return pd.DataFrame()


def load_phiusiil_url(bases_dir):
    print("\n[3/3] Loading PhiUSIIL_Phishing_URL_Dataset.csv...")
    dataset_path = os.path.join(bases_dir, "PhiUSIIL_Phishing_URL_Dataset.csv")
    
    try:
        df = pd.read_csv(dataset_path, encoding='utf-8', usecols=['URL', 'label'])
        print(f"   Loaded: {len(df)} records")
        
        labels = df['label'].fillna(0).astype(int)
        texts = df['URL'].fillna('').astype(str)
        
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}')
        
        has_url = pd.Series([1] * len(texts))
        has_email = texts.apply(lambda x: 1 if email_pattern.search(str(x)) else 0)
        has_phone = texts.apply(lambda x: 1 if phone_pattern.search(str(x)) else 0)
        
        print(f"   Phishing: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
        print(f"   Safe: {(labels==0).sum()} ({(labels==0).sum()/len(labels)*100:.1f}%)")
        
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
        print(f"   ERROR loading PhiUSIIL_Phishing_URL_Dataset.csv: {e}")
        print(f"   Trying to load all columns...")
        try:
            df = pd.read_csv(dataset_path, encoding='utf-8')
            if 'label' not in df.columns:
                print(f"   Column 'label' not found. Available columns: {list(df.columns)[:10]}")
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
            print(f"   ERROR on retry: {e2}")
            return pd.DataFrame()


bases_dir = os.path.join(os.path.dirname(__file__), "bases")

print("\n" + "="*70)
print("LOADING DATASETS")
print("="*70)

df1 = load_dataset_5971(bases_dir)
df2 = load_phishing_email(bases_dir)
df3 = load_phiusiil_url(bases_dir)

dataframes = [df for df in [df1, df2, df3] if not df.empty]

if not dataframes:
    print("\nERROR: Failed to load any dataset!")
    exit(1)

df_combined = pd.concat(dataframes, ignore_index=True)

print("\n" + "="*70)
print("COMBINED DATASET")
print("="*70)
print(f"\nTotal records: {len(df_combined)}")
print(f"\nDistribution by source:")
print(df_combined['source'].value_counts())
print(f"\nLabel distribution:")
print(f"  Phishing: {df_combined['label'].sum()} ({df_combined['label'].sum()/len(df_combined)*100:.2f}%)")
print(f"  Safe: {(df_combined['label']==0).sum()} ({(df_combined['label']==0).sum()/len(df_combined)*100:.2f}%)")

print("\n" + "="*70)
print("PREPROCESSING DATA")
print("="*70)

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?@:/]', ' ', text)
    return text.strip().lower()

print("\nCleaning text...")
df_combined['text_cleaned'] = df_combined['text'].apply(clean_text)
df_combined = df_combined[df_combined['text_cleaned'].str.len() > 0]

print(f"Records after cleaning: {len(df_combined)}")

X_text = df_combined['text_cleaned'].values
y = df_combined['label'].values
X_features = df_combined[['has_url', 'has_email', 'has_phone']].values

print("\nVectorizing text...")
vectorizer = TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    stop_words='english'
)

X_tfidf = vectorizer.fit_transform(X_text)
print(f"TF-IDF matrix shape: {X_tfidf.shape}")

X_combined = hstack([X_tfidf, X_features])

print("\nSplitting into train/test...")
X_train, X_test, y_train, y_test = train_test_split(
    X_combined, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape[0]} records")
print(f"Test set: {X_test.shape[0]} records")

print("\n" + "="*70)
print("TRAINING RANDOM FOREST MODEL")
print("="*70)

rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=25,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'
)

rf_model.fit(X_train, y_train)

y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

print("\nRANDOM FOREST RESULTS")
print("="*70)
print(f"\nAccuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred_rf, target_names=['Not phishing', 'Phishing']))
print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred_rf))

print("\n" + "="*70)
print("TRAINING LOGISTIC REGRESSION MODEL")
print("="*70)

lr_model = LogisticRegression(
    max_iter=2000,
    random_state=42,
    class_weight='balanced',
    C=1.0,
    n_jobs=-1
)

lr_model.fit(X_train, y_train)

y_pred_lr = lr_model.predict(X_test)
y_pred_proba_lr = lr_model.predict_proba(X_test)[:, 1]

print("\nLOGISTIC REGRESSION RESULTS")
print("="*70)
print(f"\nAccuracy: {accuracy_score(y_test, y_pred_lr):.4f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred_lr, target_names=['Not phishing', 'Phishing']))
print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred_lr))

print("\n" + "="*70)
print("SAVING MODELS")
print("="*70)

model_dir = os.path.dirname(__file__)
modelN_dir = os.path.join(model_dir, "modelN")

os.makedirs(modelN_dir, exist_ok=True)

model_path = os.path.join(modelN_dir, "phishing_model_rf.pkl")
vectorizer_path = os.path.join(modelN_dir, "tfidf_vectorizer.pkl")

with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print(f"RF model saved: {model_path}")
print(f"Vectorizer saved: {vectorizer_path}")

lr_model_path = os.path.join(modelN_dir, "phishing_model_lr.pkl")
with open(lr_model_path, 'wb') as f:
    pickle.dump(lr_model, f)

print(f"LR model saved: {lr_model_path}")

def predict_phishing_percentage(text, url=False, email=False, phone=False):
    text_cleaned = clean_text(text)
    text_tfidf = vectorizer.transform([text_cleaned])
    features = [[1 if url else 0, 1 if email else 0, 1 if phone else 0]]
    X_new = hstack([text_tfidf, features])
    proba = rf_model.predict_proba(X_new)[0, 1]
    return proba * 100

print("\n" + "="*70)
print("TESTING ON EXAMPLES")
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
    print(f"\nText: {text[:60]}...")
    print(f"URL: {url}, EMAIL: {email}, PHONE: {phone}")
    print(f"Phishing probability: {percentage:.2f}%")

print("\n" + "="*70)
print("TRAINING COMPLETE!")
print("="*70)
print(f"\nDatasets used: {len(dataframes)}")
print(f"Total records for training: {len(df_combined)}")
print(f"Model accuracy (RF): {accuracy_score(y_test, y_pred_rf):.4f}")
