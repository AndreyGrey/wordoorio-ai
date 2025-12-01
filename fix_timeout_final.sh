#!/bin/bash
echo "🔧 Финальное исправление таймаутов для experimental версии"

ssh yc-user@158.160.126.200 << 'EOF'
    echo "📝 Обновление systemd сервиса..."
    sudo cp /etc/systemd/system/wordoorio.service /etc/systemd/system/wordoorio.service.bak
    
    # Создаем новый конфиг с правильными таймаутами
    sudo tee /etc/systemd/system/wordoorio.service << 'SERVICEFILE'
[Unit]
Description=Wordoorio AI Flask App
After=network.target

[Service]
User=wordoorio
Group=wordoorio
WorkingDirectory=/var/www/wordoorio
Environment=PATH=/var/www/wordoorio/venv/bin
ExecStart=/var/www/wordoorio/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8081 --timeout 180 --keep-alive 60 web_app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEFILE

    echo "📝 Обновление nginx конфигурации..."
    sudo cp /etc/nginx/sites-available/wordoorio /etc/nginx/sites-available/wordoorio.bak
    
    # Проверяем текущий конфиг и добавляем таймауты если их нет
    if ! grep -q "proxy_read_timeout" /etc/nginx/sites-available/wordoorio; then
        sudo sed -i '/proxy_set_header X-Forwarded-Proto/a \        proxy_read_timeout 180s;\n        proxy_connect_timeout 180s;\n        proxy_send_timeout 180s;' /etc/nginx/sites-available/wordoorio
    else
        # Обновляем существующие таймауты
        sudo sed -i 's/proxy_read_timeout [0-9]*s;/proxy_read_timeout 180s;/g' /etc/nginx/sites-available/wordoorio
        sudo sed -i 's/proxy_connect_timeout [0-9]*s;/proxy_connect_timeout 180s;/g' /etc/nginx/sites-available/wordoorio
        sudo sed -i 's/proxy_send_timeout [0-9]*s;/proxy_send_timeout 180s;/g' /etc/nginx/sites-available/wordoorio
    fi
    
    echo "🔄 Перезапуск сервисов..."
    sudo systemctl daemon-reload
    sudo systemctl restart wordoorio
    sudo nginx -t && sudo systemctl restart nginx
    
    echo "✅ Проверка конфигурации:"
    echo "--- Gunicorn ---"
    sudo systemctl status wordoorio --no-pager -l | grep ExecStart
    echo "--- Nginx ---"
    grep -E "(proxy_read_timeout|proxy_connect_timeout|proxy_send_timeout)" /etc/nginx/sites-available/wordoorio
    
    echo "✅ Таймауты увеличены до 180 секунд"
EOF