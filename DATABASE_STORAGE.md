# Database Storage Strategy for Wordoorio

## Проблема

Wordoorio развернут на **Yandex Serverless Containers** - это stateless окружение.
Файловая система контейнера **эфемерна** (временная):
- При каждом холодном старте контейнера файлы создаются заново
- При масштабировании разные экземпляры не имеют общей файловой системы
- SQLite файл `wordoorio.db` теряется при перезапуске

## Решение: Yandex Object Storage

Используем **Yandex Object Storage** (S3-совместимое хранилище) для персистентности БД.

### Преимущества:
- ✅ **Дешево**: ~$0.0001/месяц для БД размером 10 MB (копейки)
- ✅ **Serverless**: платим только за хранение и операции, без фиксированных платежей
- ✅ **Надежно**: автоматическое резервное копирование
- ✅ **Просто**: остается SQLite, не нужна миграция на PostgreSQL

### Экономика:
- Хранение: $0.0128/GB/месяц (10 MB = $0.00013/месяц)
- Операции: минимальная плата за GET/PUT
- **Итого**: ~$0.001-0.01/месяц (1-10 копеек)

## Архитектура

```
┌─────────────────────────────────────────────────┐
│  Yandex Serverless Container (stateless)        │
│                                                  │
│  1. Container Start                             │
│     ↓                                            │
│  2. Download wordoorio.db from S3               │
│     ↓                                            │
│  3. Work with local SQLite (fast)               │
│     ↓                                            │
│  4. On data change → Upload to S3 (async)       │
│                                                  │
└─────────────────────────────────────────────────┘
                     ↕
         ┌───────────────────────┐
         │  Object Storage (S3)  │
         │                       │
         │  Bucket: wordoorio-db │
         │  File: wordoorio.db   │
         └───────────────────────┘
```

## Реализация

### 1. S3 Bucket

**Название**: `wordoorio-db`
**Файл**: `wordoorio.db`

### 2. Переменные окружения

Добавить в Serverless Container:
```bash
AWS_ACCESS_KEY_ID=<service_account_key_id>
AWS_SECRET_ACCESS_KEY=<service_account_secret>
S3_ENDPOINT=https://storage.yandexcloud.net
S3_BUCKET=wordoorio-db
```

### 3. Логика синхронизации

**При старте контейнера** (`database.py:__init__`):
1. Проверить, существует ли `wordoorio.db` локально
2. Если нет - скачать из S3 (если существует в bucket)
3. Если в S3 тоже нет - создать новую пустую БД
4. Инициализировать таблицы

**При изменении данных**:
1. Изменения применяются к локальной БД (быстро)
2. После commit - асинхронная загрузка в S3 (в фоне)
3. Не блокирует основной поток

**При новом релизе/деплое**:
1. Новый контейнер стартует
2. Скачивает актуальную БД из S3
3. Продолжает работу с сохраненными данными

## Использование

### Создание S3 bucket (один раз)

```bash
yc storage bucket create --name wordoorio-db --default-storage-class standard
```

### Создание Service Account ключей (один раз)

```bash
# Создать ключи доступа для SA
yc iam access-key create --service-account-name <sa-name>

# Сохранить:
# key_id -> AWS_ACCESS_KEY_ID
# secret -> AWS_SECRET_ACCESS_KEY
```

### Деплой с переменными окружения

```bash
yc serverless container revision deploy \
  --container-name=wordoorio \
  --image=cr.yandex/crp1mj4p9ro0clhe5t61/wordoorio:latest \
  --cores=1 --memory=1GB --execution-timeout=180s \
  --service-account-id=aje3bsioau9v6s0n5b6s \
  --environment YANDEX_CLOUD_API_KEY=... \
  --environment YANDEX_DICT_API_KEY=... \
  --environment YANDEX_FOLDER_ID=... \
  --environment AWS_ACCESS_KEY_ID=... \
  --environment AWS_SECRET_ACCESS_KEY=... \
  --environment S3_ENDPOINT=https://storage.yandexcloud.net \
  --environment S3_BUCKET=wordoorio-db
```

## Ручное управление БД

### Скачать БД локально (для проверки/бэкапа)

```bash
aws --endpoint-url=https://storage.yandexcloud.net \
    s3 cp s3://wordoorio-db/wordoorio.db ./wordoorio_backup.db
```

### Загрузить БД в S3 (восстановление)

```bash
aws --endpoint-url=https://storage.yandexcloud.net \
    s3 cp ./wordoorio.db s3://wordoorio-db/wordoorio.db
```

## Мониторинг

### Проверить размер БД в S3

```bash
aws --endpoint-url=https://storage.yandexcloud.net \
    s3 ls s3://wordoorio-db/ --human-readable
```

### Логи синхронизации

В Cloud Logging искать:
```
[DATABASE] Downloaded DB from S3
[DATABASE] Uploaded DB to S3
[DATABASE] S3 sync error
```

## Важные заметки

### ⚠️ Concurrency
- Serverless Container может запустить несколько экземпляров параллельно
- Каждый экземпляр скачивает свою копию БД
- При одновременной записи возможны конфликты (last-write-wins)
- **Решение**: используем pessimistic locking в SQLite + retry механизм

### ⚠️ Performance
- Скачивание БД при холодном старте: ~100-500ms для 10 MB
- Загрузка в S3 асинхронная, не блокирует
- Локальная работа с SQLite: быстрая (в памяти/диске контейнера)

### ⚠️ Costs
- При частых изменениях (много PUT операций) стоимость может вырасти
- Оптимизация: батчинг (загружать раз в N секунд, а не при каждом изменении)
- Для продакшена: рассмотреть Yandex Managed PostgreSQL при росте нагрузки

## Альтернативы (не используем)

❌ **Yandex Managed PostgreSQL**: $20-30/месяц (дорого для MVP)
❌ **Yandex Database (YDB)**: сложнее интеграция, нужна миграция с SQLite
❌ **Mounted Disk**: Serverless Containers не поддерживают volumes
❌ **Compute Instance**: $5-10/месяц (дороже, чем нужно для малой нагрузки)

## Roadmap

**MVP (сейчас)**: Object Storage + SQLite
**При росте**: Миграция на Managed PostgreSQL или YDB
**Оптимизация**: Батчинг загрузок, кэширование, read replicas
