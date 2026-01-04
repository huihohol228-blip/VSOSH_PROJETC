"""
Скрипт для создания простых иконок расширения
"""

import os
import sys

def create_icon_with_pillow(size, output_path):
    """Создает иконку используя PIL/Pillow"""
    from PIL import Image, ImageDraw
    
    # Создаем изображение
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Рисуем градиент (упрощенный)
    for i in range(size):
        color_value = int(102 + (118 - 102) * i / size)
        draw.rectangle([(0, i), (size, i+1)], fill=(color_value, 126, 234))
    
    # Рисуем щит (простой символ)
    shield_size = int(size * 0.6)
    shield_x = (size - shield_size) // 2
    shield_y = (size - shield_size) // 2
    
    # Простой щит - треугольник с закругленным основанием
    points = [
        (size // 2, shield_y),
        (shield_x, shield_y + shield_size // 3),
        (shield_x, shield_y + shield_size),
        (shield_x + shield_size, shield_y + shield_size),
        (shield_x + shield_size, shield_y + shield_size // 3),
    ]
    draw.polygon(points, fill='white')
    
    # Сохраняем
    img.save(output_path, 'PNG')
    print(f"✓ Создана иконка: {os.path.basename(output_path)} ({size}x{size})")

def create_icon_base64(size, output_path):
    """Создает иконку используя base64 encoded PNG"""
    # Минимальный валидный PNG файл (фиолетовый квадрат)
    # PNG signature + минимальная структура
    import base64
    
    # Простой 1x1 фиолетовый PNG в base64
    # Но нам нужен нужный размер, поэтому создадим через простой способ
    
    # Создаем простой PNG используя минимальную структуру
    png_data = bytearray()
    
    # PNG signature
    png_data.extend([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    
    # Для простоты, используем метод создания через base64 шаблон
    # Создадим фиолетовый квадрат размером size x size
    
    # Используем простой подход: создадим через цвета
    try:
        from PIL import Image
        create_icon_with_pillow(size, output_path)
        return True
    except:
        pass
    
    # Если PIL недоступен, создадим через альтернативный метод
    # Используем библиотеку для создания PNG или создадим заглушку
    print(f"⚠ Не удалось создать {os.path.basename(output_path)} через PIL")
    return False

def main():
    """Главная функция"""
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    icon_sizes = [16, 48, 128]
    created_count = 0
    
    # Пробуем использовать PIL/Pillow
    try:
        from PIL import Image, ImageDraw
        print("Использование PIL/Pillow для создания иконок...")
        
        for size in icon_sizes:
            output_path = os.path.join(icons_dir, f'icon{size}.png')
            if os.path.exists(output_path):
                print(f"⏭ Иконка {size}x{size} уже существует, пропускаем")
                created_count += 1
                continue
            
            create_icon_with_pillow(size, output_path)
            created_count += 1
        
        if created_count == len(icon_sizes):
            print(f"\n✓ Все иконки успешно созданы в папке: {icons_dir}")
            return 0
        
    except ImportError:
        print("⚠ PIL (Pillow) не установлен.")
        print("Установка Pillow...")
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
            print("✓ Pillow установлен, повторная попытка...")
            
            from PIL import Image, ImageDraw
            for size in icon_sizes:
                output_path = os.path.join(icons_dir, f'icon{size}.png')
                if os.path.exists(output_path):
                    continue
                create_icon_with_pillow(size, output_path)
                created_count += 1
            
            if created_count == len(icon_sizes):
                print(f"\n✓ Все иконки успешно созданы в папке: {icons_dir}")
                return 0
                
        except Exception as e:
            print(f"❌ Не удалось установить Pillow: {e}")
            print("\nАльтернативные способы создания иконок:")
            print("1. Установите Pillow вручную: pip install Pillow")
            print("2. Используйте create_icons.html в браузере")
            print("3. Создайте иконки в любом графическом редакторе")
            print(f"   Размеры: 16x16, 48x48, 128x128 пикселей")
            print(f"   Цвет: #667eea (градиент от #667eea до #764ba2)")
            print(f"   Папка для сохранения: {icons_dir}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

