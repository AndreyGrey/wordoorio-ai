# ⚠️ УСТАРЕВШАЯ ДОКУМЕНТАЦИЯ - VM DEPLOYMENT

> **ВНИМАНИЕ**: Эта документация описывает старое VM развертывание (IP: 158.160.126.200).
> **Текущая архитектура**: Yandex Cloud Serverless Container
> **Актуальная документация**: См. `SERVERLESS_DEPLOYMENT.md` в корне проекта

---

# 🚀 DEPLOYMENT ИНСТРУКЦИИ WORDOORIO (УСТАРЕЛО)

## 🎯 БЫСТРЫЙ СТАРТ

### **Локальное развертывание (разработка)**
```bash
# 1. Клонирование репозитория
git clone <your-repo-url>
cd wordoorio

# 2. Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Установка зависимостей  
pip install -r requirements.txt

# 4. Настройка переменных окружения
cp .env.example .env
# Заполнить .env файл вашими токенами:
# YANDEX_IAM_TOKEN=ваш_токен
# YANDEX_FOLDER_ID=b1gcdpfvt5vkfn3o9nm1

# 5. Запуск приложения
python web_app.py
```
**Результат:** 
- Основная версия: http://localhost:8081
- Experimental версия: http://localhost:8081/experimental

---

## 🌐 PRODUCTION DEPLOYMENT (VM - Текущий)

### **✅ VM уже развернут и работает**

**Текущее состояние:**
- **URL:** https://wordoorio.ru
- **Experimental:** https://wordoorio.ru/experimental  
- **IP:** 158.160.126.200
- **Пользователь:** yc-user
- **Статус:** ✅ Активен

### **Подключение к серверу**
```bash
# SSH подключение
ssh yc-user@158.160.126.200

# Проверка статуса сервиса
sudo systemctl status wordoorio

# Просмотр логов
sudo journalctl -u wordoorio -f
```

**Стоимость VM:**
- CPU: 2 × 0,216₽/час × 50% = 311₽/месяц  
- RAM: 1GB × 0,3456₽/час = 247₽/месяц
- SSD: 10GB × 0,0132₽/час = 9₽/месяц
- **ИТОГО: ~567₽/месяц**

### **🔄 ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ**

#### **Обновление experimental версии (основной способ):**
```bash
# Из локальной папки проекта
./deploy_experimental.sh
```

#### **Ручное обновление файлов:**
```bash
# Подключение к серверу
ssh yc-user@158.160.126.200

# Переход в папку приложения
cd /var/www/wordoorio

# Обновление файлов (если используется git)
git pull origin main

# Или загрузка отдельных файлов через scp
scp web_app.py yc-user@158.160.126.200:/var/www/wordoorio/

# Перезапуск сервиса после обновления
sudo systemctl restart wordoorio
```

#### **Обновление зависимостей:**
```bash
ssh yc-user@158.160.126.200
cd /var/www/wordoorio
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart wordoorio
```

### **⚙️ АВТОМАТИЗАЦИЯ (уже настроена)**

#### **Автообновление токенов:**
```bash
# Проверка cron задачи
ssh yc-user@158.160.126.200 "crontab -l"

# Вывод: 0 */3 * * * sudo /usr/bin/python3 /var/www/wordoorio/server_token_refresh.py >> /var/log/wordoorio-tokens.log 2>&1

# Просмотр логов автообновления
ssh yc-user@158.160.126.200 "sudo tail -f /var/log/wordoorio-tokens.log"
```

#### **Мониторинг системы:**
```bash
# Статус всех сервисов
ssh yc-user@158.160.126.200 "sudo systemctl status wordoorio nginx"

# Проверка конфигурации nginx
ssh yc-user@158.160.126.200 "sudo nginx -t"

# Системные ресурсы
ssh yc-user@158.160.126.200 "htop"
```

#### **SSL сертификат (уже настроен):**
```bash
# Проверка статуса сертификата
ssh yc-user@158.160.126.200 "sudo certbot certificates"

# Тест обновления
ssh yc-user@158.160.126.200 "sudo certbot renew --dry-run"
```

---

### **Вариант 2: Docker Container (для сложных проектов)**

#### **Сборка и развертывание**
```bash
# Сборка образа
docker build -t wordoorio-ai .

# Тестовый запуск
docker run -p 8080:8080 --env-file .env wordoorio-ai

# Деплой в Yandex Container Registry
./deploy.sh
```

**Стоимость:** ~600-800₽/месяц

---

### **Вариант 3: Cloud Functions (текущий)**
```bash
# Деплой функции (НЕ ИСПОЛЬЗУЙТЕ - simple-deploy.sh удален)
# Используйте VM вместо этого
```

**Проблемы:** Лимиты размера, Cold Start, ограничения статических файлов

---

## 🔧 УПРАВЛЕНИЕ И МОНИТОРИНГ

### **Проверка статуса сервисов**
```bash
# Статус приложения
sudo systemctl status wordoorio

# Статус nginx
sudo systemctl status nginx

# Просмотр логов
sudo journalctl -u wordoorio -f
sudo journalctl -u nginx -f

# Мониторинг ресурсов
htop
df -h
free -m
```

### **Обновление приложения**
```bash
# Подключение к серверу
ssh ubuntu@<VM_IP>
sudo su - wordoorio
cd /var/www/wordoorio

# Обновление кода
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск приложения
sudo systemctl restart wordoorio
sudo systemctl status wordoorio
```

### **Резервное копирование**
```bash
# Создание backup
tar -czf /tmp/wordoorio_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  /var/www/wordoorio \
  /etc/nginx/sites-available/wordoorio \
  /etc/systemd/system/wordoorio.service

# Копирование на локальную машину
scp ubuntu@<VM_IP>:/tmp/wordoorio_backup_*.tar.gz ./backups/
```

---

## 🌐 ДОМЕН (уже настроен)

### **Текущие DNS записи**
```
Тип    Имя              Значение
A      wordoorio.ru     158.160.126.200
CNAME  www.wordoorio.ru wordoorio.ru
```

### **Проверка домена**
```bash
# Проверка DNS
nslookup wordoorio.ru
dig wordoorio.ru

# Проверка доступности
curl -I https://wordoorio.ru
curl -I https://wordoorio.ru/experimental

# Тест SSL
openssl s_client -connect wordoorio.ru:443 -servername wordoorio.ru
```

---

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### **❌ "Для AI анализа нужны токены Yandex GPT"**
```bash
# Проверка автообновления токенов
ssh yc-user@158.160.126.200 "sudo tail -f /var/log/wordoorio-tokens.log"

# Ручное обновление токена
~/yandex-cloud/bin/yc iam create-token
ssh yc-user@158.160.126.200 "sudo systemctl restart wordoorio"
```

### **❌ "Ошибка соединения с сервером" (experimental)**
```bash
# Проверка таймаутов (должны быть 180 сек)
./fix_timeout_final.sh

# Проверка логов
ssh yc-user@158.160.126.200 "sudo journalctl -u wordoorio | grep TIMEOUT"
```

### **❌ Приложение не запускается**
```bash
# Проверка статуса сервиса
ssh yc-user@158.160.126.200 "sudo systemctl status wordoorio"

# Просмотр логов
ssh yc-user@158.160.126.200 "sudo journalctl -u wordoorio -n 50"

# Ручной запуск для диагностики
ssh yc-user@158.160.126.200 "cd /var/www/wordoorio && source venv/bin/activate && python web_app.py"
```

### **❌ Nginx проблемы**
```bash
# Проверка конфигурации
ssh yc-user@158.160.126.200 "sudo nginx -t"

# Логи nginx
ssh yc-user@158.160.126.200 "sudo tail -f /var/log/nginx/error.log"
```

### **❌ SSL проблемы**
```bash
# Проверка сертификата
ssh yc-user@158.160.126.200 "sudo certbot certificates"

# Принудительное обновление
ssh yc-user@158.160.126.200 "sudo certbot renew --force-renewal"
```

---

## 📊 МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ

### **Системные метрики**
```bash
# CPU и память
top -p $(pgrep -f gunicorn)

# Дисковое пространство
df -h

# Сетевая активность
sudo netstat -i
```

### **Логи приложения**
```bash
# Ошибки приложения
sudo journalctl -u wordoorio --priority=err

# Статистика запросов
sudo grep "POST /analyze" /var/log/nginx/access.log | wc -l

# Медленные запросы
sudo grep "POST /analyze" /var/log/nginx/access.log | awk '$10 > 5000'
```

---

## ⚡ ПРОИЗВОДИТЕЛЬНОСТЬ (уже оптимизирована)

### **Текущие настройки gunicorn:**
- **Workers:** 2  
- **Timeout:** 180 секунд (для experimental dual-prompt)
- **Keep-alive:** 60 секунд
- **Memory:** ~256MB на worker

### **Текущие настройки nginx:**
- **Proxy timeouts:** 180 секунд
- **SSL:** Let's Encrypt с автообновлением
- **Gzip:** Включен для текста и JSON

### **Мониторинг производительности:**
```bash
# Мониторинг ресурсов
ssh yc-user@158.160.126.200 "htop"

# Проверка медленных запросов
ssh yc-user@158.160.126.200 "sudo journalctl -u wordoorio | grep 'took.*ms'"

# Статистика nginx
ssh yc-user@158.160.126.200 "sudo tail -100 /var/log/nginx/access.log"
```

---

## 🔒 БЕЗОПАСНОСТЬ (настроена)

### **Текущие настройки безопасности:**
- ✅ **SSH:** Только по ключам
- ✅ **Firewall:** ufw настроен (SSH + HTTP/HTTPS)  
- ✅ **SSL:** Let's Encrypt с автообновлением
- ✅ **Токены:** Автообновление каждые 3 часа
- ✅ **Системные обновления:** unattended-upgrades

### **Проверка безопасности:**
```bash
# Проверка SSH попыток
ssh yc-user@158.160.126.200 "sudo grep 'Failed password' /var/log/auth.log | tail -10"

# Проверка firewall
ssh yc-user@158.160.126.200 "sudo ufw status"

# Активные соединения
ssh yc-user@158.160.126.200 "sudo netstat -tuln"
```

---

## 🎉 ИТОГОВЫЕ URL

**Основной сайт:** https://wordoorio.ru  
**Experimental версия:** https://wordoorio.ru/experimental  
**Статус:** ✅ Работает стабильно с автообновлением токенов

---

**Последнее обновление:** 30 ноября 2025  
**Версия:** VM Production v3.0 с dual-prompt experimental