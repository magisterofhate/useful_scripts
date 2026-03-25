# Changelog

## v0.1 — Initial analytics pipeline

### Added
- Выгрузка дефектов из YouTrack (VM, DCI6, BA)
- Поддержка пагинации API
- Экспорт в Excel (Defects + Versions)

### Enrichment
- Lifetime (в рабочих днях)
- Кварталы и месяцы (Created / Resolved)
- Affected version
- Fix version
- PS links (support / production)

### Analytics
- Dashboard (PNG):
  - Open defects
  - Created defects
  - Resolved defects
  - Net backlog delta
- Дополнительные линии:
  - Critical defects (Major/Critical/Неотложный)
  - PS defects

### DER
- DER by affected version
- DER by quarter
- DER для критичных дефектов

---

## v0.2 — Улучшение логики

### Improved
- Корректный расчёт DER (fix NaN)
- Сортировка кварталов (Q1 2024 → Q2 2024 и т.д.)
- Улучшена логика Fix version:
  - учитывается Release
  - исключён "Не определен"
  - исключён статус Аннулирована

### Added
- PS-based Affected version
- Автозаполнение версий через Versions sheet

---

## v0.3 — BA support

### Added
- Поддержка проекта BA (BILL)
- Дополнительные поля:
  - Подсистема
  - Категория BILL
  - Тэги

### Architecture
- Подготовка к разделению логики:
  - VM/DCI
  - BA