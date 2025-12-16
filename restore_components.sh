#!/bin/bash

# Скрипт для восстановления компонентов после синхронизации iCloud

set -e  # Остановить при ошибке

cd "/Users/andrewkondakow/Library/Mobile Documents/com~apple~CloudDocs/Documents/Projects/Wordoorio"

echo "🔍 Проверка наличия файлов..."

# Проверяем что файлы появились
if [ ! -f "static/components/Header.js" ]; then
    echo "❌ Header.js еще не синхронизировался"
    echo "⏳ Подождите пока iCloud синхронизирует файлы"
    exit 1
fi

if [ ! -f "static/components/AnalysisForm.js" ]; then
    echo "❌ AnalysisForm.js еще не синхронизировался"
    exit 1
fi

if [ ! -f "static/js/HighlightsStorage.js" ]; then
    echo "❌ HighlightsStorage.js еще не синхронизировался"
    exit 1
fi

echo "✅ Все файлы найдены!"
echo ""

# Показываем файлы
echo "📁 Найденные файлы:"
ls -lh static/components/Header.js
ls -lh static/components/AnalysisForm.js
ls -lh static/js/HighlightsStorage.js
echo ""

# Откатываем последний коммит (soft - оставляя изменения staged)
echo "🔄 Откатываем последний коммит..."
git reset --soft HEAD~1
echo "✅ Коммит откачен"
echo ""

# Восстанавливаем experimental.html к версии с импортами
echo "🔄 Восстанавливаем experimental.html..."
git restore --staged templates/experimental.html
git restore templates/experimental.html
echo "✅ experimental.html восстановлен"
echo ""

# Добавляем новые файлы
echo "📦 Добавляем компоненты в git..."
git add static/components/Header.js
git add static/components/AnalysisForm.js
git add static/js/HighlightsStorage.js
git add templates/experimental.html
echo "✅ Файлы добавлены"
echo ""

# Коммитим
echo "💾 Создаем коммит..."
git commit -m "feat: Add missing components for experimental page

Added components that were synced from another computer via iCloud:
- static/components/Header.js
- static/components/AnalysisForm.js
- static/js/HighlightsStorage.js

These components are required for experimental.html to work properly.
Fixed iCloud sync issue."

echo "✅ Коммит создан"
echo ""

# Показываем статус
echo "📊 Текущий статус:"
git log --oneline -3
echo ""

# Перезапускаем сервер
echo "🔄 Перезапускаем сервер..."
lsof -ti:8081 | xargs kill 2>/dev/null || echo "Сервер не был запущен"
sleep 1

nohup venv/bin/python web_app.py > /tmp/wordoorio.log 2>&1 &
sleep 3

if lsof -ti:8081 > /dev/null; then
    echo "✅ Сервер запущен на http://localhost:8081"
else
    echo "❌ Ошибка запуска сервера"
    echo "Проверьте логи: tail /tmp/wordoorio.log"
    exit 1
fi

echo ""
echo "🎉 ВСЕ ГОТОВО!"
echo ""
echo "Откройте в браузере:"
echo "  http://localhost:8081/experimental"
echo ""
echo "Должно работать без ошибок!"
