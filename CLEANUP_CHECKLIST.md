# ✅ CLEANUP CHECKLIST

**Дата:** 7 декабря 2025
**Цель:** Быстрый чеклист для очистки проекта от мертвого кода

---

## 🔴 URGENT (делать сейчас - 15 минут)

### 1. Удалить мертвый код

```bash
# Перейти в проект
cd "/Users/andrewkondakow/Library/Mobile Documents/com~apple~CloudDocs/Documents/Projects/Wordoorio"

# Удалить папку interface (мертвый код, 322 строки)
rm -rf interface/

# Удалить backup файл
rm core/prompts/versions/v3_adaptive.py.backup

# Проверить что удалили
ls -la interface/  # Должна быть ошибка "No such file"
ls -la core/prompts/versions/*.backup  # Должна быть ошибка "No such file"
```

**Экономия:** 332 строки кода, ~12 KB

---

### 2. Исправить ImportError в prompt_manager.py

```bash
# Открыть файл
nano core/prompts/prompt_manager.py

# УДАЛИТЬ строку 25:
# from core.prompts.versions.v2_dual import DualPromptV2

# УДАЛИТЬ строку 29:
# self.register_prompt(DualPromptV2())

# Сохранить: Ctrl+O, Enter, Ctrl+X
```

**ИЛИ через sed:**

```bash
# Удалить строку с v2_dual import
sed -i '' '/from core.prompts.versions.v2_dual import DualPromptV2/d' core/prompts/prompt_manager.py

# Удалить строку с register v2_dual
sed -i '' '/self.register_prompt(DualPromptV2())/d' core/prompts/prompt_manager.py
```

---

### 3. Исправить маппинг в analysis_service.py

```bash
# Открыть файл
nano core/analysis_service.py

# НАЙТИ строку 37:
# 'experimental': 'v2_dual',

# ИЗМЕНИТЬ на:
# 'experimental': 'v1_basic',

# Сохранить: Ctrl+O, Enter, Ctrl+X
```

**ИЛИ через sed:**

```bash
sed -i '' "s/'experimental': 'v2_dual'/'experimental': 'v1_basic'/g" core/analysis_service.py
```

---

### 4. Удалить маршруты к несуществующим шаблонам

```bash
# Открыть файл
nano web_app.py

# УДАЛИТЬ строки 186-189:
# @app.route('/my-highlights')
# def my_highlights_page():
#     return render_template('my_highlights.html')
#     (пустая строка)

# УДАЛИТЬ строки 485-488:
# @app.route('/youtube')
# def youtube_page():
#     return render_template('youtube.html')
#     (пустая строка)

# Сохранить: Ctrl+O, Enter, Ctrl+X
```

---

### 5. Проверить что все работает

```bash
# Запустить приложение локально
python web_app.py

# Проверить что нет ошибок импорта:
# ✅ Должно быть: "Зарегистрировано 2 версий промптов" (v1, v3)
# ❌ НЕ должно быть: "Ошибка импорта версий промптов"

# Открыть в браузере:
# http://localhost:5000/           ✅ Должно работать
# http://localhost:5000/experimental ✅ Должно работать (теперь v1_basic)
# http://localhost:5000/v3         ✅ Должно работать

# Проверить что 404 на удаленных маршрутах:
# http://localhost:5000/my-highlights ✅ Должен быть 404
# http://localhost:5000/youtube       ✅ Должен быть 404

# Остановить: Ctrl+C
```

---

## 🟡 HIGH (сделать сегодня - 10 минут)

### 6. Консолидировать token refresh скрипты

```bash
# Создать архивную папку
mkdir archive/

# Переместить старые скрипты
mv server_token_refresh.py archive/
mv deploy_token.py archive/

# Проверить что остался только refresh_token.py
ls -la *.py | grep refresh
# Должен быть только: refresh_token.py
```

---

### 7. Создать .gitignore для backup файлов

```bash
# Добавить в .gitignore
echo "*.backup" >> .gitignore
echo "archive/" >> .gitignore

# Проверить
cat .gitignore | grep -E "backup|archive"
```

---

## 🟢 OPTIONAL (если есть время - 5 минут)

### 8. Добавить проверку шаблонов при старте

```python
# Добавить в начало web_app.py (после импортов)

def validate_templates():
    """Проверяет наличие всех необходимых шаблонов"""
    required_templates = [
        'index.html',
        'experimental.html',
        'v3.html',
        'history.html'
    ]

    for template in required_templates:
        path = f'templates/{template}'
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ Template not found: {template}")

    print("✅ All templates validated")

# Вызвать перед app.run()
if __name__ == '__main__':
    validate_templates()
    app.run(debug=True, port=5000)
```

---

### 9. Создать документацию используемых скриптов

```bash
# Создать файл
cat > SCRIPTS.md << 'EOF'
# 📜 СКРИПТЫ ПРОЕКТА

## Token Refresh

**Используемый скрипт:** `refresh_token.py`

**Назначение:** Автоматическое обновление Yandex IAM токенов

**Запуск:**
```bash
python refresh_token.py
```

**Cron (production):**
```
0 */3 * * * cd /var/www/wordoorio && python refresh_token.py >> /var/log/wordoorio/token_refresh.log 2>&1
```

**Как работает:**
1. Проверяет валидность текущего токена
2. Если истек - генерирует новый через yc CLI
3. Обновляет .env файл
4. Перезапускает wordoorio service

## Архив

**Папка:** `archive/`

**Содержимое:**
- `server_token_refresh.py` - старый серверный скрипт (не используется)
- `deploy_token.py` - старый SSH деплой скрипт (не используется)

EOF

# Просмотреть
cat SCRIPTS.md
```

---

## 🎯 ФИНАЛЬНАЯ ПРОВЕРКА

### Чеклист выполненных задач:

```
✅ 1. Удалена папка interface/
✅ 2. Удален v3_adaptive.py.backup
✅ 3. Исправлен ImportError в prompt_manager.py
✅ 4. Исправлен маппинг в analysis_service.py
✅ 5. Удалены маршруты к несуществующим шаблонам
✅ 6. Консолидированы token refresh скрипты
✅ 7. Обновлен .gitignore
✅ 8. (Optional) Добавлена валидация шаблонов
✅ 9. (Optional) Создана документация скриптов
```

### Команды для финальной проверки:

```bash
# 1. Проверить что мертвый код удален
! [ -d interface/ ] && echo "✅ interface/ удалена" || echo "❌ interface/ еще существует"
! [ -f core/prompts/versions/v3_adaptive.py.backup ] && echo "✅ backup удален" || echo "❌ backup еще существует"

# 2. Проверить что ImportError исправлен
! grep -q "v2_dual" core/prompts/prompt_manager.py && echo "✅ v2_dual удален" || echo "❌ v2_dual еще упоминается"

# 3. Проверить маппинг
grep "'experimental': 'v1_basic'" core/analysis_service.py && echo "✅ Маппинг исправлен" || echo "❌ Маппинг не исправлен"

# 4. Проверить что маршруты удалены
! grep -q "my-highlights" web_app.py && echo "✅ my-highlights удален" || echo "❌ my-highlights еще есть"
! grep -q "@app.route('/youtube')" web_app.py && echo "✅ youtube удален" || echo "❌ youtube еще есть"

# 5. Проверить архив
[ -d archive/ ] && echo "✅ archive/ создана" || echo "⚠️ archive/ не создана"
[ -f archive/server_token_refresh.py ] && echo "✅ Скрипты в архиве" || echo "⚠️ Скрипты не перемещены"

# 6. Запустить приложение и проверить логи
python web_app.py 2>&1 | head -20
# Должно быть:
# ✅ "Зарегистрировано 2 версий промптов"
# ❌ НЕ должно быть "Ошибка импорта"
```

---

## 📊 РЕЗУЛЬТАТЫ CLEANUP

### До:
```
Python файлов:     18
Строк кода:        1974
Мертвого кода:     322 строки (16%)
ImportError:       Да
404 маршруты:      2
```

### После:
```
Python файлов:     17 (-1)
Строк кода:        1642 (-332, -17%)
Мертвого кода:     0 строк (0%)
ImportError:       Нет ✅
404 маршруты:      0 ✅
```

### Экономия:
- ✅ 332 строки кода удалено
- ✅ 1 папка удалена (interface/)
- ✅ 2 backup файла удалено
- ✅ 2 дублирующихся скрипта в архив
- ✅ 2 broken маршрута исправлено
- ✅ 1 ImportError исправлена

---

## 🚀 DEPLOY (после cleanup)

### Если нужно задеплоить на production:

```bash
# 1. Коммит изменений
git add .
git commit -m "cleanup: Remove dead code, fix ImportError, update mappings

- Removed interface/pages/page_configs.py (322 lines of dead code)
- Removed v3_adaptive.py.backup
- Fixed ImportError in prompt_manager.py (v2_dual)
- Updated experimental mapping to use v1_basic
- Removed routes to non-existent templates
- Archived duplicate token refresh scripts

Fixes #cleanup #technical-debt"

# 2. Проверить production сервер
ssh yc-user@158.160.126.200

# 3. Забэкапить текущую версию
cd /var/www/wordoorio
cp -r . ../wordoorio_backup_$(date +%Y%m%d_%H%M%S)

# 4. Запулить изменения
git pull origin main

# 5. Перезапустить сервис
sudo systemctl restart wordoorio

# 6. Проверить логи
sudo journalctl -u wordoorio -f

# Должно быть:
# ✅ "Зарегистрировано 2 версий промптов"
# ✅ Нет ошибок импорта

# 7. Проверить в браузере
# https://wordoorio.ru/           ✅
# https://wordoorio.ru/experimental ✅
# https://wordoorio.ru/v3         ✅
```

---

## 📝 NOTES

### Что делать с YouTube функционалом?

**Вариант 1: Создать youtube.html**
```bash
# Скопировать шаблон из experimental
cp templates/experimental.html templates/youtube.html
# Адаптировать под YouTube
nano templates/youtube.html
# Вернуть маршрут в web_app.py
```

**Вариант 2: Удалить YouTube код (если не нужен)**
```bash
# Удалить agents/youtube_agent.py
rm agents/youtube_agent.py
# Маршрут /youtube/analyze уже удален
```

**Рекомендация:** Решить позже, оставить как есть сейчас

---

### Что делать с v2_dual?

**Вариант 1: Создать v2_dual.py**
```bash
# Скопировать v1_basic как основу
cp core/prompts/versions/v1_basic.py core/prompts/versions/v2_dual.py
# Адаптировать под dual-prompt
nano core/prompts/versions/v2_dual.py
# Вернуть импорт в prompt_manager.py
```

**Вариант 2: Оставить как есть (experimental = v1_basic)**
- Сейчас experimental использует v1_basic
- Работает стабильно
- Нет необходимости в dual-prompt

**Рекомендация:** Оставить experimental на v1_basic

---

## ✅ DONE!

После выполнения всех шагов проект будет:
- ✅ Без мертвого кода
- ✅ Без ImportError
- ✅ Без 404 маршрутов
- ✅ Чистый и поддерживаемый
- ✅ Готов к дальнейшему развитию

**Время выполнения:** ~30 минут
**Сложность:** Легко
**Риски:** Минимальные (все изменения безопасные)
