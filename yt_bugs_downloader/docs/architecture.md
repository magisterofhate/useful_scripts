# Архитектура проекта

Документ описывает структуру проекта, зоны ответственности модулей и основные потоки данных.

## 1. Общая идея

Проект построен по принципу:

`YouTrack API → Data → Enrichment → Excel → Analytics (Charts + DER)`

Основные этапы:
1. Получение данных из YouTrack
2. Преобразование в DataFrame
3. Обогащение (версии, связи, расчёты)
4. Экспорт в Excel
5. Расчёт метрик
6. Построение графиков

## 2. Структура проекта

```text
yt_exporter/
├── cli/
│   ├── export_defects.py
│   └── get_versions.py
│
├── services/
│   ├── youtrack_client.py
│   ├── defects.py
│   └── versions.py
│
├── exporters/
│   ├── excel.py
│   └── charts.py
│
├── metrics/
│   └── der.py
│
├── config/
│   └── settings.py
│
└── utils/
    └── helpers.py (опционально)
```

## 3. CLI слой

### `cli/export_defects.py`
Основной entrypoint.

Отвечает за:
- выбор проекта (`VM`, `DCI6`, `BA`)
- запуск пайплайна
- последовательность шагов:
  1. загрузка задач
  2. сбор DataFrame
  3. экспорт Excel
  4. построение графиков
  5. расчёт DER

### `cli/get_versions.py`
Отдельный скрипт для получения списка версий.

## 4. Services слой

### `services/youtrack_client.py`
Обёртка над YouTrack API.

Отвечает за:
- авторизацию
- запросы
- пагинацию

### `services/defects.py`
Ключевой модуль.

Отвечает за:
- преобразование issue → DataFrame
- вычисление:
  - Lifetime
  - кварталов и месяцев
- обработку:
  - PS links
  - версий

### Внутренняя архитектура
Разделение по проектам:

`build_defects_dataframe() → build_vm_dci_row() / build_ba_row()`

### Общая логика
`issue → common_fields → project_specific_fields → row`

### `services/versions.py`
Отвечает за:
- парсинг страниц с версиями
- фильтрацию версий
- извлечение дат релизов

## 5. Export слой

### `exporters/excel.py`
Отвечает за:
- запись DataFrame в Excel
- пост-обработку:
  - заполнение Fix version
  - заполнение Affected version
  - подсветку ошибок
- добавление листа Versions

### `exporters/charts.py`
Отвечает за построение dashboard.

Графики:
1. Open defects
2. Created
3. Resolved
4. Backlog delta

Особенности:
- overlay линий:
  - critical defects
  - PS defects
- расчёт по неделям

## 6. Metrics слой

### `metrics/der.py`
Отвечает за расчёт:
- DER by affected version
- DER by quarter

Дополнительно:
- отдельные таблицы для:
  - Major
  - Critical
  - Неотложный

## 7. Поток данных

### Основной pipeline

```text
YouTrack API
    ↓
issues (raw JSON)
    ↓
services/defects.py
    ↓
DataFrame
    ↓
exporters/excel.py
    ↓
Excel (Defects + Versions)
    ↓
metrics/der.py
    ↓
DER Excel
    ↓
exporters/charts.py
    ↓
PNG Dashboard
```

## 8. Разделение ответственности

| Слой | Ответственность |
|---|---|
| CLI | orchestration |
| services | бизнес-логика |
| exporters | вывод (Excel, графики) |
| metrics | аналитика |
| config | настройки |

## 9. Расширяемость

### Добавление нового проекта
Нужно:
1. Добавить настройки в CLI
2. Добавить row-builder в `defects.py`
3. При необходимости добавить специфические поля

### Добавление новой метрики
1. Создать модуль в `metrics/`
2. Подключить в CLI
3. При необходимости добавить график

### Добавление нового графика
1. Добавить в `charts.py`
2. Включить в dashboard

## 10. Принципы проектирования

### 1. Разделение по слоям
- API отдельно
- бизнес-логика отдельно
- визуализация отдельно

### 2. Минимум логики в CLI
CLI только orchestrates.

### 3. DataFrame как единый контракт
Все модули работают через DataFrame:
- exporters
- metrics
- charts

### 4. Проектная изоляция
BA ≠ VM/DCI

Разные проекты:
- могут иметь разные поля
- могут иметь разную логику

### 5. Постобработка в Excel
Некоторые вещи делаются на этапе Excel:
- Fix version
- Affected version

## 11. Потенциальные улучшения

### Архитектура
- вынести schemas (описание колонок)
- ввести типизацию DataFrame
- сделать plugin-систему для проектов

### Производительность
- кеширование версий
- батчевые запросы

### UI
- Flask / FastAPI
- web dashboard

### Аналитика
- DER trends
- Lead Time
- Defect density
- Cost of Quality

## 12. Ограничения
- зависимость от структуры YouTrack
- нестабильность HTML при парсинге versions
- Excel как основной формат хранения