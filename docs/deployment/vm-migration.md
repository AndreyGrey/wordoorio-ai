# ⚠️ УСТАРЕВШАЯ ДОКУМЕНТАЦИЯ - ИСТОРИЯ МИГРАЦИИ НА VM

> **ВНИМАНИЕ**: Эта документация описывает миграцию НА VM в ноябре 2025.
> **ПОЗЖЕ (декабрь 2025)**: Мы мигрировали С VM на Serverless Container
> **Текущая архитектура**: Yandex Cloud Serverless Container (экономия 94%)
> **Актуальная документация**: См. `SERVERLESS_DEPLOYMENT.md`

Этот файл сохранен для истории.

---

# ✅ ИСТОРИЯ МИГРАЦИИ WORDOORIO НА VM (УСТАРЕЛО - БЫЛА ПОВТОРНАЯ МИГРАЦИЯ)

## ✅ РЕЗУЛЬТАТ МИГРАЦИИ (ВРЕМЕННЫЙ - ПОЗЖЕ МИГРИРОВАЛИ НА SERVERLESS)

**Дата завершения:** Ноябрь 2025
**Дата миграции на Serverless:** Декабрь 2025
**Статус:** ❌ Заменено на Serverless Container

## 💰 ФАКТИЧЕСКАЯ ЭКОНОМИКА
- **Реальная VM (2 vCPU 50% + 1GB RAM + 10GB SSD)**: 567₽/месяц
- **Домен wordoorio.ru**: Уже оплачен
- **SSL сертификат**: Бесплатный (Let's Encrypt)
- **ИТОГО**: 567₽/месяц
- **vs Cloud Functions**: Стабильность и полный контроль

---

## 📋 РЕАЛИЗОВАННЫЕ ШАГИ

### ✅ ШАГ 1: СОЗДАНИЕ VM В YANDEX CLOUD (ВЫПОЛНЕНО)
```bash
# Создать VM через консоль или CLI
yc compute instance create \
  --name wordoorio-vm \
  --hostname wordoorio.ai \
  --platform standard-v3 \
  --cores 1 \
  --core-fraction 50 \
  --memory 1GB \
  --create-boot-disk size=10GB,type=network-ssd,image-folder-id=standard-images,image-family=ubuntu-2204-lts \
  --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 \
  --ssh-key ~/.ssh/id_rsa.pub
```

**Результат**: ✅ VM создана, IP: 158.160.126.200, Ubuntu 22.04

### ✅ ШАГ 2: ПЕРВИЧНАЯ НАСТРОЙКА VM (ВЫПОЛНЕНО)
```bash
# Подключение к VM
ssh ubuntu@<ВНЕШНИЙ_IP_VM>

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git htop curl
```

### ШАГ 3: НАСТРОЙКА ОКРУЖЕНИЯ
```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash wordoorio
sudo mkdir -p /var/www/wordoorio
sudo chown wordoorio:wordoorio /var/www/wordoorio

# Переключение на пользователя
sudo su - wordoorio
cd /var/www/wordoorio

# Клонирование репозитория
git clone <ВАШ_GIT_РЕПОЗИТОРИЙ> .
```

### ✅ ШАГ 4: УСТАНОВКА ЗАВИСИМОСТЕЙ (ВЫПОЛНЕНО)
```bash
# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
pip install -r requirements.txt
pip install gunicorn

# Создание .env файла
cat > .env << EOF
YANDEX_IAM_TOKEN=ваш_токен
YANDEX_FOLDER_ID=ваш_folder_id
EOF
```

### ✅ ШАГ 5: НАСТРОЙКА SYSTEMD SERVICE (ВЫПОЛНЕНО)
```bash
# Создание systemd service файла
sudo tee /etc/systemd/system/wordoorio.service << EOF
[Unit]
Description=Wordoorio AI Flask App
After=network.target

[Service]
User=wordoorio
Group=wordoorio
WorkingDirectory=/var/www/wordoorio
Environment=PATH=/var/www/wordoorio/venv/bin
ExecStart=/var/www/wordoorio/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8081 web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Запуск и автозагрузка сервиса
sudo systemctl daemon-reload
sudo systemctl enable wordoorio
sudo systemctl start wordoorio
sudo systemctl status wordoorio
```

### ШАГ 6: НАСТРОЙКА NGINX
```bash
# Создание конфигурации nginx
sudo tee /etc/nginx/sites-available/wordoorio << EOF
server {
    listen 80;
    server_name ваш.домен.com;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Статические файлы (если нужно)
    location /static {
        alias /var/www/wordoorio/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Активация сайта
sudo ln -s /etc/nginx/sites-available/wordoorio /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### ШАГ 7: НАСТРОЙКА SSL (Let's Encrypt)
```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d ваш.домен.com

# Автообновление сертификатов
sudo systemctl enable certbot.timer
```

### ❌ ШАГ 8: НАСТРОЙКА OBJECT STORAGE (НЕ ПОТРЕБОВАЛОСЬ)
```bash
# Создание bucket для статических файлов
yc storage bucket create --name wordoorio-static

# Загрузка статических файлов
yc storage cp static/ s3://wordoorio-static/static/ --recursive

# Обновление nginx для статики из Object Storage
```

### ШАГ 9: НАСТРОЙКА ДОМЕНА
```
A-запись: ваш.домен.com -> ВНЕШНИЙ_IP_VM
```

### ✅ ШАГ 10: ФИНАЛЬНАЯ ПРОВЕРКА (ВЫПОЛНЕНО)
```bash
# Проверка статуса сервисов
sudo systemctl status wordoorio nginx

# Проверка логов
sudo journalctl -u wordoorio -f

# Тест работоспособности
curl -I http://ваш.домен.com
```

---

## 🔧 УПРАВЛЕНИЕ VM

### Мониторинг
```bash
# Просмотр логов приложения
sudo journalctl -u wordoorio -f

# Мониторинг ресурсов
htop
df -h
free -m

# Статус nginx
sudo systemctl status nginx
```

### Обновление приложения
```bash
# Зайти на сервер
ssh ubuntu@<IP_VM>
sudo su - wordoorio
cd /var/www/wordoorio

# Обновить код
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Перезапустить сервис
sudo systemctl restart wordoorio
```

### Backup
```bash
# Backup кода и конфигурации
tar -czf /tmp/wordoorio_backup_$(date +%Y%m%d).tar.gz \
  /var/www/wordoorio \
  /etc/nginx/sites-available/wordoorio \
  /etc/systemd/system/wordoorio.service
```

---

## ⚡ ПРЕИМУЩЕСТВА VM РЕШЕНИЯ

1. **💰 Дешевизна**: 415₽/мес vs 1391₽/мес
2. **🔧 Полный контроль**: SSH доступ, любые пакеты
3. **📈 Масштабируемость**: Легко увеличить ресурсы
4. **🚀 Производительность**: Нет Cold Start как в Functions
5. **🔒 Безопасность**: Прямое управление сервером
6. **📊 Мониторинг**: Полные логи и метрики
7. **🌐 Домен**: Прямая привязка без API Gateway

---

## 🎯 ПОСЛЕ МИГРАЦИИ

1. **Удалить Cloud Functions** - экономия ресурсов
2. **Настроить мониторинг** - Yandex Monitoring
3. **Автобэкапы** - через cron
4. **SSL обновления** - через certbot
5. **Логи ротация** - через logrotate

**ИТОГОВАЯ АРХИТЕКТУРА:**
```
Интернет → Домен → VM (nginx + Flask) → Yandex GPT API
                 ↓
            Object Storage (статика)
```

**СТОИМОСТЬ: 419₽/месяц** 🎉