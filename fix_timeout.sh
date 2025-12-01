#!/bin/bash
echo "🔧 Исправление таймаутов для experimental версии"

# Увеличиваем таймауты в gunicorn и nginx
ssh yc-user@158.160.126.200 << 'EOF'
    echo "📝 Обновление конфигурации gunicorn..."
    sudo sed -i 's/--timeout [0-9]*/--timeout 120/g' /etc/systemd/system/wordoorio.service
    
    echo "📝 Обновление конфигурации nginx..."
    sudo sed -i 's/proxy_read_timeout [0-9]*;/proxy_read_timeout 120s;/g' /etc/nginx/sites-available/wordoorio
    sudo sed -i 's/proxy_connect_timeout [0-9]*;/proxy_connect_timeout 120s;/g' /etc/nginx/sites-available/wordoorio
    
    # Если таймауты отсутствуют, добавляем их
    if ! grep -q "proxy_read_timeout" /etc/nginx/sites-available/wordoorio; then
        sudo sed -i '/proxy_set_header X-Forwarded-Proto/a \        proxy_read_timeout 120s;\n        proxy_connect_timeout 120s;' /etc/nginx/sites-available/wordoorio
    fi
    
    echo "🔄 Перезапуск сервисов..."
    sudo systemctl daemon-reload
    sudo systemctl restart wordoorio
    sudo nginx -t && sudo systemctl restart nginx
    
    echo "✅ Таймауты увеличены до 120 секунд"
EOF