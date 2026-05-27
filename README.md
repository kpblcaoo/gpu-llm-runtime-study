# Исследование GPU Runtime: RTX 6000 Ada vs RTX 5090 · May 2026

Практическое исследование поведения LLM-инференса с длинным контекстом на арендованных GPU.\
A practical study of long-context LLM inference runtime behavior on rented GPUs.

**→ [Полная версия на русском / Full Russian landing](README.ru.md)**\
**→ [Full English landing](README.en.md)**

---

## Что исследовалось / What was studied

Стек: `llama.cpp` + `LiteLLM` + `Prometheus/DCGM` на Vast.ai.\
Stack: `llama.cpp` + `LiteLLM` + `Prometheus/DCGM` on Vast.ai.

| GPU | VRAM | Роли в тестах |
|---|---|---|
| NVIDIA RTX 6000 Ada Generation | 48 508 МиБ | Q4 200k/300k/400k/524k, Q6 400k |
| NVIDIA RTX 5090 | 32 607 МиБ | Q4 200k/2 (синтетика + агент) |
| 2× RTX 5090 (LiteLLM routing) | 32 607 МиБ × 2 | Топологический зонд, Q4 200k |

Модель: `Qwen3.6-27B-UD-Q4_K_XL.gguf` / `Q6_K_XL.gguf`.\
Нагрузки: синтетические token-target бенчмарки + сценарии OpenCode-агента.

---

## Главные результаты / Key findings

| | |
|---|---|
| RTX 5090 быстрее при `200k / 2` Q4 | 1.53×–1.63× по wall-latency и decode TPS |
| Ada A6000 — эндпоинт длинного контекста | Единственная протестированная платформа для 300k / 400k / 524k |
| Ada Q4 400k/2 — лучший кандидат для агентных задач | ~12 ГБ запаса VRAM, все 5 сценариев пройдены |
| Q6 на Ada 400k/2 операционально жизнеспособен | +10–16% медленнее, +7 ГиБ VRAM, качество **не доказано** |
| Dual RTX 5090 — только топологический зонд | Маршрутизация работает; надёжность и телеметрия не подтверждены |
| Агент ≠ синтетика | Бимодальная утилизация GPU; tool-call время не конвертируется в TPS |

---

## Документация / Documentation

| | RU | EN |
|---|---|---|
| Полный отчёт | [docs/ru/](docs/ru/gpu-runtime-research-report-2026-05.md) | [docs/en/](docs/en/gpu-runtime-research-report-2026-05.md) |
| Нормализованные результаты | [data/normalized-results.md](data/normalized-results.md) | same |
| Анализ Prometheus/DCGM | [data/prometheus-observability-analysis.md](data/prometheus-observability-analysis.md) | same |
| Аудит утверждений | [data/claim-audit.md](data/claim-audit.md) | same |
| Инвентарь артефактов | [data/artifact-inventory.md](data/artifact-inventory.md) | same |

---

## Ограничения / Limitations

Это не:

- оценка качества модели (perplexity, задачи, рассуждение);
- универсальный рейтинг GPU;
- тест производственной многопользовательской нагрузки;
- модель стоимость/производительность.

Агентные результаты — однократные наблюдения. Dual RTX 5090 — зонд без полной телеметрии.

---

## Об авторе / About the author

Михаил Степанов, DevSecOps-инженер, ИБ, сисадмин.\
Mikhail Stepanov, DevSecOps engineer, security and sysadmin background.

Личное техническое исследование. Исследование выполнено независимо.\
Personal technical investigation, conducted independently.

---

## Лицензия / License

Docs: [CC BY 4.0](LICENSE-DOCS.md) · Scripts: [MIT](LICENSE-CODE.md) · [NOTICE.md](NOTICE.md) · [DATA_USAGE.md](DATA_USAGE.md)

---

*May 2026 · Preliminary research artifact*
