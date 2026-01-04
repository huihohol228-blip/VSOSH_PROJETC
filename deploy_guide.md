# 🚀 Руководство по развертыванию Telegram Web App

## 📦 Что нужно подготовить

### 1. Файлы для деплоя (уже готовы ✅):
- ✅ `requirements.txt` - все зависимости
- ✅ `Procfile` - команда запуска (для Railway/Heroku)
- ✅ `Dockerfile` - для контейнеризации
- ✅ `webapp/app_production.py` - продакшен версия Flask
- ✅ `railway.json` - конфигурация для Railway

### 2. Что нужно будет:

**Для готового хостинга (Railway/Render):**
- Аккаунт на хостинге
- GitHub репозиторий (или GitLab)
- Модели из папки `modelN/` (должны быть в репозитории)

**Для VPS + Домен:**
- VPS сервер (Ubuntu/Debian)
- Домен с настроенной A-записью на IP сервера
- SSH доступ к серверу
- Модели из папки `modelN/`

---

## 🎯 Вариант 1: Railway.app (САМЫЙ ПРОСТОЙ) ⭐

### Шаг 1: Подготовка

1. **Создайте GitHub репозиторий:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ваш-username/your-repo.git
   git push -u origin main
   ```

2. **Важно:** Убедитесь что модели в репозитории:
   - `modelN/phishing_model_rf.pkl`
   - `modelN/phishing_model_lr.pkl`
   - `modelN/tfidf_vectorizer.pkl`

### Шаг 2: Деплой на Railway

1. Зайдите на https://railway.app
2. Войдите через GitHub
3. Нажмите "New Project"
4. Выберите "Deploy from GitHub repo"
5. Выберите ваш репозиторий
6. Railway автоматически обнаружит `Procfile` и запустит приложение

### Шаг 3: Получение URL

1. В настройках проекта Railway найдите "Settings"
2. Во вкладке "Domains" будет URL типа: `https://your-app.railway.app`
3. Скопируйте этот URL

### Шаг 4: Обновление бота

Откройте `tgbot/webapp_bot.py` и замените:
```python
WEBAPP_URL = "https://your-app.railway.app/webapp"
```

Готово! ✅

---

## 🎯 Вариант 2: Render.com

### Шаг 1: Подготовка (аналогично Railway)

1. Загрузите код в GitHub
2. Убедитесь что модели в репозитории

### Шаг 2: Деплой на Render

1. Зайдите на https://render.com
2. Войдите через GitHub
3. Нажмите "New +" → "Web Service"
4. Выберите репозиторий
5. Настройки:
   - **Name:** phishing-checker (любое)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 webapp.app_production:app`
6. Нажмите "Create Web Service"

### Шаг 3: Получение URL

Render даст URL типа: `https://phishing-checker.onrender.com`

### Шаг 4: Обновление бота

```python
WEBAPP_URL = "https://phishing-checker.onrender.com/webapp"
```

---

## 🎯 Вариант 3: VPS + Домен

### Шаг 1: Подготовка сервера

```bash
# Подключитесь к серверу по SSH
ssh user@your-server-ip

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx tesseract-ocr

# Клонирование репозитория
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 2: Настройка Nginx

Создайте файл `/etc/nginx/sites-available/phishing-app`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте:
```bash
sudo ln -s /etc/nginx/sites-available/phishing-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Шаг 3: Получение SSL сертификата

```bash
sudo certbot --nginx -d your-domain.com
```

### Шаг 4: Настройка Systemd сервиса

Создайте `/etc/systemd/system/phishing-app.service`:
```ini
[Unit]
Description=Phishing Checker Flask App
After=network.target

[Service]
User=your-username
WorkingDirectory=/home/your-username/your-repo
Environment="PATH=/home/your-username/your-repo/venv/bin"
ExecStart=/home/your-username/your-repo/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 webapp.app_production:app

[Install]
WantedBy=multi-user.target
```

Запустите:
```bash
sudo systemctl daemon-reload
sudo systemctl enable phishing-app
sudo systemctl start phishing-app
```

### Шаг 5: Обновление бота

```python
WEBAPP_URL = "https://your-domain.com/webapp"
```

---

## ✅ Проверка работы

1. Откройте в браузере: `https://your-url/api/health`
2. Должен вернуться: `{"status": "ok", "model_loaded": true}`
3. Откройте: `https://your-url/webapp`
4. Должна открыться страница Web App

---

## 🔧 Обновление бота после деплоя

После получения HTTPS URL:

1. Откройте `tgbot/webapp_bot.py`
2. Найдите строку:
   ```python
   WEBAPP_URL = "https://your-ngrok-url.ngrok.io/webapp"
   ```
3. Замените на ваш URL:
   ```python
   WEBAPP_URL = "https://your-app.railway.app/webapp"
   ```
4. Перезапустите бота

---

## 🆘 Проблемы и решения

**Проблема:** Модели не найдены
- **Решение:** Убедитесь что `.pkl` файлы в репозитории (не в .gitignore)

**Проблема:** Ошибка 500
- **Решение:** Проверьте логи на хостинге, убедитесь что модели загружаются

**Проблема:** Web App не открывается
- **Решение:** Проверьте что URL правильный и доступен по HTTPS

---

## 📝 Чек-лист перед деплоем

- [ ] Модели (`*.pkl`) в репозитории
- [ ] `requirements.txt` актуален
- [ ] `Procfile` или `Dockerfile` настроен
- [ ] `WEBAPP_URL` обновлен в `webapp_bot.py`
- [ ] HTTPS URL получен
- [ ] Тест `/api/health` работает
- [ ] Тест `/webapp` работает

Готово! 🎉

