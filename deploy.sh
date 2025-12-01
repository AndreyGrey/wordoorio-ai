#!/bin/bash

# Скрипт деплоя Wordoorio AI на Yandex Cloud

echo "🚀 Деплой Wordoorio AI на Yandex Cloud"
echo "======================================"

# Настраиваем путь к yc CLI
export PATH="$HOME/yandex-cloud/bin:$PATH"
YC_CLI="$HOME/yandex-cloud/bin/yc"

# Проверяем yc CLI
if ! command -v yc &> /dev/null; then
    if [ ! -f "$YC_CLI" ]; then
        echo "❌ Yandex Cloud CLI не найден. Установите: https://cloud.yandex.ru/docs/cli/quickstart"
        exit 1
    fi
fi

# Проверяем docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker Desktop"
    exit 1
fi

# Переменные
IMAGE_NAME="wordoorio-ai"
REGISTRY_ID="crp1mj4p9ro0clhe5t61" # wordoorio-registry
SERVICE_NAME="wordoorio"
FOLDER_ID=$(~/yandex-cloud/bin/yc config get folder-id)

if [ -z "$FOLDER_ID" ]; then
    echo "❌ Folder ID не найден. Выполните: yc init"
    exit 1
fi

echo "📦 Собираем Docker образ..."
docker build -t $IMAGE_NAME .

echo "🏷️ Создаем тег для Yandex Container Registry..."
docker tag $IMAGE_NAME cr.yandex/$REGISTRY_ID/$IMAGE_NAME:latest

echo "📤 Загружаем образ в registry..."
docker push cr.yandex/$REGISTRY_ID/$IMAGE_NAME:latest

echo "☁️ Создаем/обновляем Serverless Container..."
yc serverless container create --name $SERVICE_NAME 2>/dev/null || echo "Контейнер уже существует"

~/yandex-cloud/bin/yc serverless container revision deploy \
  --container-name $SERVICE_NAME \
  --image cr.yandex/$REGISTRY_ID/$IMAGE_NAME:latest \
  --memory 512m \
  --cores 1 \
  --execution-timeout 60s \
  --environment YANDEX_FOLDER_ID=$FOLDER_ID \
  --service-account-id ajetorbok30ucvg88kqn

echo "🌐 Создаем/обновляем API Gateway..."
cat > api-gateway.yaml << EOF
openapi: 3.0.0
info:
  title: Wordoorio AI API
  version: 1.0.0
paths:
  /{proxy+}:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: \$(yc serverless container get $SERVICE_NAME --format json | jq -r .id)
        service_account_id: \$(yc iam service-account get default --format json | jq -r .id)
EOF

yc serverless api-gateway create --name wordoorio-gateway --spec api-gateway.yaml 2>/dev/null || \
yc serverless api-gateway update wordoorio-gateway --spec api-gateway.yaml

GATEWAY_DOMAIN=$(yc serverless api-gateway get wordoorio-gateway --format json | jq -r .domain)

echo "✅ Деплой завершен!"
echo "🌍 Ваше приложение доступно по адресу:"
echo "   https://$GATEWAY_DOMAIN"
echo ""
echo "📝 Для настройки переменных окружения:"
echo "   export YANDEX_IAM_TOKEN=ваш_токен"
echo "   export YANDEX_FOLDER_ID=ваш_folder_id"