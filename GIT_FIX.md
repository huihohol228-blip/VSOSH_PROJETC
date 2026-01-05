# 🔧 Исправление проблем с Git

## Проблема: нужна настройка пользователя Git

Выполните следующие команды:

```bash
# 1. Настройте ваше имя (замените на ваше имя)
git config --global user.name "Your Name"

# 2. Настройте ваш email (замените на ваш email)
git config --global user.email "your.email@example.com"

# 3. Теперь сделайте коммит
git commit -m "Initial commit: Phishing detection project"

# 4. Загрузите на GitHub
git push -u origin main
```

## Полная последовательность команд:

```bash
# Настройка Git (один раз, для всех проектов)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Коммит
git commit -m "Initial commit: Phishing detection project"

# Push на GitHub
git push -u origin main
```

## Если хотите настроить только для этого проекта:

Вместо `--global` используйте без флага:
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```


