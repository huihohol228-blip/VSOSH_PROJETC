#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для запуска Flask приложения (альтернатива для Railway)
"""

import os
import sys

# Устанавливаем порт из переменной окружения
port = int(os.environ.get('PORT', 5000))

# Импортируем приложение
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from webapp.app_production import app
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


