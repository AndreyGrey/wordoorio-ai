#!/bin/bash

# Деплой Wordoorio AI как Yandex Cloud Function

echo "🚀 Деплой Wordoorio AI как Cloud Function"
echo "=========================================="

# Настраиваем путь к yc CLI
export PATH="$HOME/yandex-cloud/bin:$PATH"
YC_CLI="$HOME/yandex-cloud/bin/yc"

# Проверяем yc CLI
if [ ! -f "$YC_CLI" ]; then
    echo "❌ Yandex Cloud CLI не найден"
    exit 1
fi

# Переменные
FUNCTION_NAME="wordoorio-function"
SERVICE_ACCOUNT_NAME="wordoorio-sa"
FOLDER_ID=$(yc config get folder-id)

if [ -z "$FOLDER_ID" ]; then
    echo "❌ Folder ID не найден. Выполните: yc init"
    exit 1
fi

echo "📦 Создаем архив с кодом..."
# Создаем временную директорию
mkdir -p /tmp/wordoorio-deploy
cp -r . /tmp/wordoorio-deploy/
cd /tmp/wordoorio-deploy

# Создаем requirements.txt для Cloud Function
cat > requirements.txt << 'EOF'
Flask==2.3.3
python-dotenv==1.0.0
requests==2.31.0
functions-framework==3.4.0
EOF

# Создаем main.py для Cloud Function
cat > main.py << 'EOF'
import functions_framework
from flask import Flask, request, jsonify, render_template_string
import os
import sys

# Добавляем текущую директорию в путь
sys.path.append('.')

# Импортируем наше приложение
from web_app import app

@functions_framework.http
def wordoorio_handler(request):
    """HTTP Cloud Function entry point."""
    with app.test_request_context(request.url, method=request.method, 
                                 data=request.get_data(), headers=request.headers):
        try:
            response = app.full_dispatch_request()
            return response.get_data(as_text=True), response.status_code, dict(response.headers)
        except Exception as e:
            return str(e), 500
EOF

echo "☁️ Создаем/обновляем Cloud Function..."
yc serverless function create --name $FUNCTION_NAME 2>/dev/null || echo "Function уже существует"

# Создаем версию функции
yc serverless function version create \
  --function-name $FUNCTION_NAME \
  --runtime python39 \
  --entrypoint main.wordoorio_handler \
  --memory 512m \
  --execution-timeout 60s \
  --source-path . \
  --environment YANDEX_IAM_TOKEN=$YANDEX_IAM_TOKEN,YANDEX_FOLDER_ID=$YANDEX_FOLDER_ID

echo "🌐 Делаем функцию публичной..."
yc serverless function allow-unauthenticated-invoke $FUNCTION_NAME

# Получаем URL функции
FUNCTION_ID=$(yc serverless function get $FUNCTION_NAME --format json | grep '"id"' | head -1 | cut -d'"' -f4)
FUNCTION_URL="https://functions.yandexcloud.net/$FUNCTION_ID"

echo "✅ Деплой завершен!"
echo "🌍 Ваше приложение доступно по адресу:"
echo "   $FUNCTION_URL"

# Возвращаемся в исходную директорию
cd - > /dev/null
rm -rf /tmp/wordoorio-deploy