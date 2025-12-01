#!/usr/bin/env python3
"""
Скрипт для генерации токена локально и обновления на сервере
"""

import subprocess
import sys
import paramiko
import os

def get_local_token():
    """Получает новый токен локально через Yandex CLI"""
    try:
        # Генерируем токен локально
        result = subprocess.run([
            '/Users/andrewkondakow/yandex-cloud/bin/yc', 
            'iam', 
            'create-token'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            token = result.stdout.strip()
            print(f"✅ Получен новый токен локально: {token[:20]}...")
            return token
        else:
            print(f"❌ Ошибка получения токена: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def update_remote_env(token):
    """Обновляет .env файл на удаленном сервере"""
    try:
        # SSH подключение
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключаемся к серверу
        ssh.connect(
            '158.160.126.200',
            username='yc-user',
            key_filename=os.path.expanduser('~/.ssh/id_rsa')
        )
        
        # Команда для обновления токена в .env файле
        update_cmd = f"""
        sudo sed -i 's/^YANDEX_IAM_TOKEN=.*/YANDEX_IAM_TOKEN={token}/' /var/www/wordoorio/.env
        """
        
        stdin, stdout, stderr = ssh.exec_command(update_cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("✅ Токен обновлен в .env файле")
        else:
            print(f"❌ Ошибка обновления .env файла: {stderr.read().decode()}")
            return False
        
        # Перезапускаем сервис
        restart_cmd = "sudo systemctl reload wordoorio"
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("✅ Сервис wordoorio перезагружен")
        else:
            print(f"⚠️ Не удалось перезагрузить сервис: {stderr.read().decode()}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка SSH подключения: {e}")
        return False

def main():
    """Основная функция"""
    print("🔄 Обновление токена на сервере...")
    
    # Получаем токен локально
    token = get_local_token()
    if not token:
        sys.exit(1)
    
    # Обновляем на сервере
    if update_remote_env(token):
        print("✅ Токен успешно обновлен на сервере")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()