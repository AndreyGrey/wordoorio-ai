FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Порт для Yandex Cloud
ENV PORT=8080

# Запускаем приложение
EXPOSE 8080
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 web_app:app