#!/usr/bin/env python3
"""
Скрипт для автоматического обновления Yandex IAM токенов
СРОК ЖИЗНИ: до 12 часов
СТРАТЕГИЯ: максимальная экономия ресурсов + надежность
Запускается каждые 3 часа (4 раза в сутки вместо 180)
"""

import subprocess
import sys
import os
import time
import requests
import json
from pathlib import Path

def check_token_validity(token, folder_id):
    """Проверяет действительность текущего токена через простой GPT запрос"""
    try:
        # Проверяем токен через Yandex GPT API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 10
            },
            "messages": [{"role": "user", "text": "test"}]
        }
        
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            print("✅ Текущий токен действителен")
            return True
        elif response.status_code == 401:
            print("❌ Токен истек, требуется обновление")
            return False
        else:
            print(f"⚠️ Статус {response.status_code}, обновляем токен на всякий случай")
            return False
            
    except Exception as e:
        print(f"⚠️ Ошибка проверки токена: {e}")
        return False

def read_current_token(env_path):
    """Читает текущий токен из .env файла"""
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('YANDEX_IAM_TOKEN='):
                    return line.replace('YANDEX_IAM_TOKEN=', '').strip()
        return None
    except Exception:
        return None

def get_new_token():
    """Получает новый токен через Yandex CLI"""
    try:
        # Попробуем найти yc команду в разных местах
        yc_paths = [
            '/home/yc-user/yandex-cloud/bin/yc',
            '/usr/local/bin/yc',
            'yc'
        ]
        
        yc_command = None
        for path in yc_paths:
            try:
                result = subprocess.run([path, 'version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    yc_command = path
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        if not yc_command:
            print("❌ Yandex CLI не найден")
            return None
            
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
    """Обновляет токен в .env файле"""
    try:
        # Читаем содержимое файла
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Заменяем токен
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith('YANDEX_IAM_TOKEN='):
                updated_lines.append(f'YANDEX_IAM_TOKEN={token}')
                print(f"✅ Обновлен токен в {env_path}")
            else:
                updated_lines.append(line)
        
        # Записываем обновленное содержимое
        with open(env_path, 'w') as f:
            f.write('\n'.join(updated_lines))
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления .env файла: {e}")
        return False

def restart_service():
    """Перезапускает сервис wordoorio"""
    try:
        result = subprocess.run(['sudo', 'systemctl', 'reload', 'wordoorio'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Сервис wordoorio перезагружен")
            return True
        else:
            print(f"⚠️ Ошибка перезагрузки сервиса: {result.stderr}")
            # Пробуем restart вместо reload
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'wordoorio'], 
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
    """Основная функция с умной проверкой токена"""
    print(f"🔄 Проверка токенов - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Определяем путь к .env
    env_path = '/Users/andrewkondakow/Documents/Projects/Wordoorio/.env'
    if not os.path.exists(env_path):
        env_path = '/var/www/wordoorio/.env'  # Для продакшена
    
    # Читаем текущий токен
    current_token = read_current_token(env_path)
    if not current_token:
        print("⚠️ Токен не найден в .env, получаем новый")
    else:
        # Проверяем действительность текущего токена
        if check_token_validity(current_token, 'b1gcdpfvt5vkfn3o9nm1'):
            print("✅ Токен еще действителен, обновление не требуется")
            print("💰 Ресурсы сэкономлены!")
            return
    
    print("🔄 Получаем новый токен...")
    
    # Получаем новый токен
    new_token = get_new_token()
    if not new_token:
        print("❌ Не удалось получить новый токен")
        sys.exit(1)
    
    # Обновляем .env файл
    if not update_env_file(new_token, env_path):
        print("❌ Не удалось обновить .env файл")
        sys.exit(1)
    
    # Перезапускаем сервис только если это продакшен
    if env_path.startswith('/var/www/'):
        if not restart_service():
            print("⚠️ Сервис не был перезапущен, но токен обновлен")
    
    print("✅ Обновление токенов завершено успешно")

if __name__ == "__main__":
    main()