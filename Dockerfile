FROM python:3.9-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем spacy модель для лемматизации
RUN pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Копируем исходный код
COPY . .

# Порт для Yandex Cloud
ENV PORT=8080

# Запускаем приложение с увеличенным timeout для dual-prompt
EXPOSE 8080
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 180 web_app:app