#!/bin/bash
echo "🧪 Деплой экспериментальной версии Wordoorio"
echo "=============================================="

# Переменные
SERVER="yc-user@158.160.126.200"
APP_DIR="/var/www/wordoorio"
ARCHIVE="wordoorio_experimental_deploy.tar.gz"
NEW_TOKEN="t1.9euelZqdkM3HnpaTjImPzI_Ii57Omu3rnpWamJWVzJCejc2Wx8zPm8-PnJTl9PcLY1Q2-e8RIxeE3fT3SxFSNvnvESMXhM3n9euelZqSi5mYy5DPmpmOyY2QjYmUmO_8xeuelZqSi5mYy5DPmpmOyY2QjYmUmA.C5JlC-W8a_VB7oDIdazkAwCwcqs436QYWGBOqayESGL1feKqS7sSfd2TzHOUdBNk0j8Vl5xyDkxPJln-c3XBCw"
FOLDER_ID="b1gcdpfvt5vkfn3o9nm1"

echo "📋 Статус сервера: ✅ Основной сайт работает"
echo "📋 Experimental: ❌ Недоступен (404)"
echo ""

# Проверяем архив
if [ ! -f "$ARCHIVE" ]; then
    echo "❌ Архив $ARCHIVE не найден"
    exit 1
fi

echo "📦 Архив: $(ls -lh $ARCHIVE | awk '{print $5}')"

# Вариант 1: Прямой деплой через SSH (если работает)
echo "🚀 Попытка деплоя через SSH..."

# Отправляем файлы
echo "📤 Отправка архива..."
if scp -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
   "$ARCHIVE" "$SERVER:/tmp/"; then
    
    echo "✅ Архив отправлен"
    
    # Развертывание
    echo "🔧 Развертывание на сервере..."
    ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER" << EOF
        echo "📁 Распаковка архива..."
        cd "$APP_DIR" || exit 1
        sudo tar -xzf /tmp/$ARCHIVE
        
        echo "🔄 Обновление .env токена..."
        sudo sed -i 's/^YANDEX_IAM_TOKEN=.*/YANDEX_IAM_TOKEN=$NEW_TOKEN/' .env
        sudo sed -i 's/^YANDEX_FOLDER_ID=.*/YANDEX_FOLDER_ID=$FOLDER_ID/' .env
        
        echo "🔄 Перезапуск сервиса..."
        sudo systemctl restart wordoorio || {
            echo "⚠️  Systemd сервис не найден, перезапуск gunicorn..."
            sudo pkill -f gunicorn
            sudo systemctl status wordoorio
        }
        
        echo "✅ Развертывание завершено"
        rm -f /tmp/$ARCHIVE
EOF
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 ДЕПЛОЙ УСПЕШЕН!"
        echo "✅ Основной сайт: https://wordoorio.ru"
        echo "🧪 Experimental: https://wordoorio.ru/experimental"
        echo ""
        echo "🧪 Тестируем experimental..."
        sleep 3
        
        # Тест experimental маршрута
        EXPERIMENTAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://wordoorio.ru/experimental)
        if [ "$EXPERIMENTAL_STATUS" = "200" ]; then
            echo "✅ Experimental версия доступна!"
        else
            echo "❌ Experimental версия недоступна ($EXPERIMENTAL_STATUS)"
        fi
    else
        echo "❌ Ошибка развертывания"
    fi
    
else
    echo "❌ SSH недоступен"
    echo ""
    echo "📋 АЛЬТЕРНАТИВНЫЕ ВАРИАНТЫ:"
    echo ""
    echo "🔧 Вариант 1: Yandex Cloud Console"
    echo "   1. https://console.cloud.yandex.ru"
    echo "   2. Compute Cloud → wordoorio-vm → Подключиться"
    echo "   3. Выполнить команды вручную"
    echo ""
    echo "🔧 Вариант 2: GitHub деплой"
    echo "   1. Создать GitHub репозиторий"
    echo "   2. Залить код с experimental файлами"  
    echo "   3. На сервере: git clone/pull"
    echo ""
    echo "📦 Готовый архив: $ARCHIVE ($(ls -lh $ARCHIVE | awk '{print $5}'))"
    echo "🔑 Новый токен готов к использованию"
fi

echo ""
echo "🎯 После успешного деплоя будет доступно:"
echo "   • https://wordoorio.ru - основная версия"
echo "   • https://wordoorio.ru/experimental - dual-prompt анализ"