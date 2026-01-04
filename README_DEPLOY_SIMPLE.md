# 🚀 Простое развертывание

## ✅ Лучший вариант: Render.com

**Инструкция:** См. файл `DEPLOY_RENDER.md`

Render.com - самый простой и надежный вариант для Flask приложений!

## 🔄 Альтернативы:

### PythonAnywhere (если Render не работает)

1. Зайдите на https://www.pythonanywhere.com
2. Создайте бесплатный аккаунт
3. Откройте Bash консоль
4. Клонируйте репозиторий: `git clone https://github.com/huihohol228-blip/VSOSH_PROJETC.git`
5. Настройте веб-приложение через панель

### Fly.io

1. Установите flyctl: https://fly.io/docs/getting-started/installing-flyctl/
2. Выполните: `fly launch`
3. Следуйте инструкциям

## 📝 Быстрая команда для Render:

**Start Command для Render:**
```
python -c "import os; port = int(os.environ.get('PORT', 5000)); from webapp.app_production import app; app.run(host='0.0.0.0', port=port, debug=False)"
```

**Build Command:**
```
pip install -r requirements.txt
```

---

**Рекомендую Render.com - он самый простой!** 🎯

