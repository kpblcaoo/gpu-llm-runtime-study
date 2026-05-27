# Общий реестр метрик (Metrics Index)

Данный документ описывает основные метрики, собираемые во время бенчмарков (Ada A6000, RTX 5090). 
Метрики можно визуализировать в Grafana, загрузив соответствующие TSDB-снапшоты в локальный инстанс Prometheus.

## 1. Аппаратные метрики (DCGM Exporter)
Метрики, начинающиеся с `DCGM_FI_`, переименованы (relabelled) при экспорте для удобства чтения:
- `gpu_utilization`: Общая утилизация GPU (%).
- `gpu_memory_utilization`: Утилизация памяти GPU (%).
- `gpu_memory_used_mb`: Занятая VRAM (в мегабайтах).
- `gpu_memory_free_mb`: Свободная VRAM (в мегабайтах).
- `gpu_memory_total_mb`: Общий объем VRAM (в мегабайтах).
- `gpu_power_draw`: Энергопотребление видеокарты (в ваттах).
- `gpu_temperature`: Температура видеочипа (в градусах Цельсия).
- `gpu_sm_clock`: Частота ядер Streaming Multiprocessor (МГц).
- `gpu_memory_clock`: Частота памяти GPU (МГц).

## 2. Метрики балансировщика (LiteLLM)
- `litellm_requests`: Общее количество запросов, прошедших через прокси.
- `litellm_failed_requests`: Количество запросов, завершившихся ошибкой (HTTP 4xx/5xx).
- `litellm_latency_p95` (и другие перцентили): Задержка обработки запроса на стороне прокси (Time-to-first-token и end-to-end).
- `litellm_up`: Статус доступности прокси (1 - доступен, 0 - недоступен).

## 3. Метрики LLM Runtime (llama.cpp)
- `llama_busy_slots`: Количество активных (занятых) слотов генерации (показывает реальную конкурентность/concurrency).
- `llama_predicted_tokens_per_second` (и `llama_predicted_tokens_rate_5m`): Скорость генерации новых токенов (Decode speed).
- `llama_prompt_tokens_per_second` (и `llama_prompt_tokens_rate_5m`): Скорость обработки входящего промпта (Prefill speed).
- `llama_requests_processing`: Запросы в процессе генерации.
- `llama_requests_deferred`: Отложенные запросы (находящиеся в очереди из-за нехватки свободных слотов).

## Примечание по безопасности
Сырые TSDB-снапшоты (`prometheus-snapshot/`, `prometheus-data/`) содержат метаданные и внутренние лейблы (например, захэшированные ключи API и идентификаторы пользователей). Они намеренно игнорируются в git, чтобы предотвратить утечки. Если вы экспортируете эти данные в JSON для публикации, используйте скрипт `scripts/sanitize-metrics.py` для вырезания приватной информации.
