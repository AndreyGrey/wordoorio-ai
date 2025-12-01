#!/usr/bin/env python3
"""
Скрипт для автоматического обновления Yandex IAM токенов на сервере
Использует Service Account ключ для аутентификации
"""

import subprocess
import sys
import os
import time

def get_new_token():
    """Получает новый токен через Service Account"""
    try:
        # Используем установленный yc с service account ключом
        yc_command = '/home/yc-user/yandex-cloud/bin/yc'
        
        # Проверяем, что yc установлен
        result = subprocess.run([yc_command, 'version'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print("❌ Yandex CLI не найден")
            return None
        
        # Инициализируем профиль с service account ключом
        init_cmd = [yc_command, 'config', 'set', 'service-account-key', '/var/www/wordoorio/sa-key.json']
        result = subprocess.run(init_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"⚠️ Предупреждение при настройке SA: {result.stderr}")
        
        # Получаем новый токен
        result = subprocess.run([yc_command, 'iam', 'create-token'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            token = result.stdout.strip()
            print(f"✅ Получен новый токен: {token[:20]}...")
            return token
        else:
            print(f"❌ Ошибка получения токена: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def update_env_file(token, env_path='/var/www/wordoorio/.env'):
    """Обновляет токен в .env файле, сохраняя правильный формат"""
    try:
        # Создаем .env файл с правильным форматом
        env_content = f"YANDEX_IAM_TOKEN={token}\nYANDEX_FOLDER_ID=b1gcdpfvt5vkfn3o9nm1\n"
        
        # Записываем содержимое
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Обновлен токен в {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления .env файла: {e}")
        return False

def restart_service():
    """Перезапускает сервис wordoorio"""
    try:
        result = subprocess.run(['systemctl', 'restart', 'wordoorio'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Сервис wordoorio перезапущен")
            return True
        else:
            print(f"❌ Не удалось перезапустить сервис: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при перезапуске сервиса: {e}")
        return False

def main():
    """Основная функция"""
    print(f"🔄 Начинаем обновление токенов - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Получаем новый токен
    new_token = get_new_token()
    if not new_token:
        print("❌ Не удалось получить новый токен")
        sys.exit(1)
    
    # Обновляем .env файл
    if not update_env_file(new_token):
        print("❌ Не удалось обновить .env файл")
        sys.exit(1)
    
    # Перезапускаем сервис
    if restart_service():
        print("✅ Обновление токенов завершено успешно")
    else:
        print("⚠️ Сервис не был перезапущен, но токен обновлен")

if __name__ == "__main__":
    main()