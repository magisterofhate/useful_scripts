# YouTrack Defects Exporter & Analytics

Скрипт для выгрузки дефектов из YouTrack, обогащения данных и расчёта метрик качества.

## Что делает скрипт

### 1. Выгрузка дефектов
- Загружает дефекты из YouTrack по проекту:
  - VM
  - DCI6
  - BA (BILLmanager)
- Поддерживает пагинацию через API
- Выгружает:
  - основные поля (id, summary, статус, приоритет и т.д.)
  - связи с проектом PS (support / production)
  - версии

---

### 2. Обогащение данных
В процессе выгрузки и пост-обработки:

- рассчитываются:
  - Lifetime (в рабочих днях)
  - кварталы и месяцы (Created / Resolved)
- вычисляются:
  - Affected version
  - Fix version
- подтягиваются:
  - версии релизов (из внешнего источника)
  - связи с PS

---

### 3. Excel-отчёт
Формируется файл:
<project>_defects.xlsx

Содержит:
- лист `Defects`
- лист `Versions`

---

### 4. Графики (Dashboard)

Генерируется PNG:
<project>_defects_dashboard.png

Содержит 4 графика:

#### 1. Open defects by week
- все открытые дефекты
- критичные (Major / Critical / Неотложный)
- дефекты с PS (production)

#### 2. Created defects by week

#### 3. Resolved defects by week

#### 4. Net backlog delta

---

### 5. DER (Defect Escape Rate)

Генерируется файл:
<project>_defects_der.xlsx

Содержит:

#### DER by affected version
#### DER by quarter

И отдельные листы для критичных дефектов:
- Major
- Critical
- Неотложный

---

## Основные метрики

### 📊 Backlog (Open defects)
Количество открытых дефектов на конец каждой недели.

---

### 📈 Created defects
Сколько дефектов создано за неделю.

---

### 📉 Resolved defects
Сколько дефектов закрыто за неделю.

---

### ⚖️ Net backlog delta

Показывает:
- растёт ли backlog
- уменьшается ли backlog

---

### 🚨 Critical defects trend
Количество открытых дефектов с приоритетами:
- Major
- Critical
- Неотложный

---

### 🔥 Production defects (PS)
Количество дефектов, найденных через support / клиентами.

---

### 🧪 Defect Escape Rate (DER)
DER = Escapes / Total

Где:
- Escapes — дефекты с PS links
- Total — все дефекты (кроме аннулированных)

---

## Поддерживаемые проекты

| Проект | Особенности |
|-------|------------|
| VM | стандартная схема |
| DCI6 | аналогично VM |
| BA (BILL) | дополнительные поля: Подсистема, Категория BILL, Тэги |

---

## Технологии

- Python
- pandas
- matplotlib
- openpyxl
- YouTrack REST API

---

## Запуск

```bash
python cli/export_defects.py --project VM
```

## Результат

После выполнения создаются:
- Excel с дефектами
- Excel с DER
- PNG dashboard