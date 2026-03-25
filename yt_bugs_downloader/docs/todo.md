# TODO / Roadmap

## High priority

### 1. Разделение логики проектов
- [ ] Вынести build_vm_dci_row
- [ ] Вынести build_ba_row
- [ ] Убрать if-ы внутри одной функции

---

### 2. Конфиг по проектам
- [ ] Сделать settings per project
- [ ] Вынести:
  - поля
  - названия колонок
  - правила

---

### 3. Валидация данных
- [ ] Проверка обязательных колонок
- [ ] Проверка корректности дат
- [ ] Логи ошибок

---

## Medium priority

### 4. Метрики

#### Добавить:
- [ ] Lead Time
- [ ] Fix Cycle Time
- [ ] Regression duration
- [ ] Automation coverage (если появится)

---

### 5. DER улучшения
- [ ] DER trend (по времени)
- [ ] DER vs backlog
- [ ] DER по приоритетам (график)

---

### 6. Dashboard улучшения
- [ ] Линия cumulative resolved
- [ ] Moving average (7 недель)
- [ ] Выделение аномалий

---

## Low priority

### 7. Архитектура
- [ ] Plugin-система для проектов
- [ ] Типизация DataFrame
- [ ] Разделение schemas

---

### 8. UI
- [ ] Flask / FastAPI
- [ ] Web dashboard
- [ ] Фильтры (период, проект)

---

### 9. Производительность
- [ ] Кеширование версий
- [ ] Параллельные запросы
- [ ] Incremental выгрузка

---

## Ideas

- Экономика качества (COPQ)
- Связь DER ↔ Revenue
- Авто-анализ требований через LLM