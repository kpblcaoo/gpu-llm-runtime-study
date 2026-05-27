# Normalized Benchmark Results

**Generated:** 2026-05-26  
**Status:** Data normalization only. No new interpretation beyond what is cited from source documents.  
**Sources:** `ada-a6000/report-draft.md`, `ada-a6000/progress.md`, `rtx-5090/report-draft.md`, `rtx-5090/progress.md`, `dual-rtx-5090/report-draft.md`, `prometheus-observability-analysis.md`, `gpu-runtime-research-report-2026-05.md`

---

## Conventions

- All wall latency and TTFT values in **seconds (s)** unless noted.
- `not available` = metric was not collected or not extracted from artifacts for this row. It is not zero.
- `—` = not reported in source (p95 from a 3-sample window has high variance and was not always published).
- **Do not mix streaming TTFT and backend TTFT.** They are different measurements. See Section 6.2 of the main report.
- `streaming_ttft`: client-side first-chunk timestamp (includes queue wait + prefill + first-chunk RTT).
- `backend_ttft`: from llama.cpp log `prompt eval time` (prefill compute only; excludes queue wait and network).
- Agent workload wall times include tool execution, inter-step latency, and agent framework overhead. They are not pure GPU compute times and must not be converted to TPS figures.
- P50/P95 over 3 measured repeats have high variance; treat as directional, not precise percentile estimates.

---

## Table 1: Synthetic Benchmark Master Table

TTFT columns:
- `streaming_ttft_p50_s` / `streaming_ttft_p95_s`: client-side harness measurement (includes queue + prefill + network)
- `backend_ttft_p50_s` / `backend_ttft_p95_s`: llama.cpp log `prompt eval time` only

<!-- Notes on TTFT availability:
     - Ada 200k/2 Q4 (phase1): non-streaming curl; TTFT discarded per Section 6.2.1. backend_ttft from logs not extracted.
     - Ada 300k/2 Q4 (phase2): streaming harness; streaming_ttft available per row.
     - Ada 400k/2 Q4: streaming harness was used (same as 300k+); Q4 TTFT per row not extracted from artifacts into source documents.
     - Ada 524k/2 Q4: TTFT per row not extracted.
     - Ada 400k/2 Q6: streaming harness; streaming_ttft available per row.
     - RTX 5090 200k/2 Q4: streaming harness (same post-300k version); streaming_ttft available per row.
     - Dual RTX 5090: TTFT not collected (client-side timing only).
-->

| hardware | run_id | profile | model/quant | ctx_size | parallel | per_slot_ctx | prompt_target | actual_prompt_tokens | concurrency | success_rate | wall_p50_s | wall_p95_s | streaming_ttft_p50_s | streaming_ttft_p95_s | backend_ttft_p50_s | backend_ttft_p95_s | prompt_tps_p50 | decode_tps_p50 | vram_max_mib | gpu_util_avg | power_avg_w | notes |
|---|---|---|---|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 1k | calibrated | 1 | 3/3 | 15.325 | 15.348 | not available | not available | not available | not available | not available | not available | 27854 | 84.03% | 264.06 | TTFT discarded: non-streaming curl (see §6.2.1) |
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 1k | calibrated | 2 | 6/6 | 29.454 | 29.598 | not available | not available | not available | not available | not available | 35.1 | 27854 | 84.03% | 264.06 | TTFT discarded: non-streaming curl. Decode t/s from 5090 comparison table |
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 32k | calibrated | 1 | 3/3 | 18.024 | 18.038 | not available | not available | not available | not available | not available | not available | 27854 | 84.03% | 264.06 | TTFT discarded |
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 32k | calibrated | 2 | 6/6 | 34.016 | 34.233 | not available | not available | not available | not available | not available | 30.3 | 27854 | 84.03% | 264.06 | TTFT discarded. Decode t/s from 5090 comparison table |
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 95k | calibrated | 1 | 3/3 | 22.851 | 22.855 | not available | not available | not available | not available | not available | 45.3 | 27854 | 84.03% | 264.06 | TTFT discarded. Decode t/s from 5090 comparison table |
| RTX 6000 Ada | ada6000-phase1-baseline-20260525T202158Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 95k | calibrated | 2 | 6/6 | 45.581 | 45.830 | not available | not available | not available | not available | not available | 22.6 | 27854 | 84.03% | 264.06 | TTFT discarded. Decode t/s from 5090 comparison table |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 1k | calibrated | 1 | 3/3 | 16.259 | 16.709 | 0.080 | 0.081 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness. DCGM from progress.md summary |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 1k | calibrated | 2 | 6/6 | 31.746 | 31.822 | 0.125 | 0.169 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 32k | calibrated | 1 | 3/3 | 20.055 | 20.112 | 0.127 | 0.127 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 32k | calibrated | 2 | 6/6 | 34.760 | 35.799 | 0.179 | 0.241 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 95k | calibrated | 1 | 3/3 | 22.435 | 22.440 | 0.212 | 0.219 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 95k | calibrated | 2 | 6/6 | 45.346 | 45.630 | 0.287 | 0.377 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 140k | calibrated | 1 | 3/3 | 27.260 | 27.270 | 0.253 | 0.262 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | near per-slot limit (140k of 150k); streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase2-ctx300k-20260525T215448Z | Q4 300k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 300000 | 2 | 150000 | 140k | calibrated | 2 | 6/6 | 54.770 | 54.891 | 0.366 | 0.477 | not available | not available | not available | not available | 31906 | 92.76% | 289.92 | near per-slot limit; streaming_ttft from harness |
| RTX 6000 Ada | ada6000-ctx400k-bench-20260525T224858Z | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 400000 | 2 | 200000 | 1k | calibrated | 2 | 6/6 | 31.839 | — | not available | not available | not available | not available | not available | not available | 36180 | 91.55% | 286.82 | Q4 wall from Q6 sanity comparison table; TTFT not extracted from 400k artifacts |
| RTX 6000 Ada | ada6000-ctx400k-bench-20260525T224858Z | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 400000 | 2 | 200000 | 95k | calibrated | 2 | 6/6 | 45.322 | — | not available | not available | not available | not available | not available | not available | 36180 | 91.55% | 286.82 | Q4 wall from Q6 sanity comparison table; TTFT not extracted |
| RTX 6000 Ada | ada6000-ctx400k-bench-20260525T224858Z | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 400000 | 2 | 200000 | 190k | calibrated | 1 | 3/3 | 32.600 | — | not available | not available | not available | not available | not available | not available | 36180 | 91.55% | 286.82 | near per-slot limit (190k of 200k); TTFT not extracted |
| RTX 6000 Ada | ada6000-ctx400k-bench-20260525T224858Z | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 400000 | 2 | 200000 | 190k | calibrated | 2 | 6/6 | 64.868 | — | not available | not available | not available | not available | not available | not available | 36180 | 91.55% | 286.82 | near per-slot limit; TTFT not extracted |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 1k | calibrated | 1 | 3/3 | 16.267 | 16.505 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted from 524k artifacts; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 1k | calibrated | 2 | 6/6 | 31.806 | 31.867 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 32k | calibrated | 1 | 3/3 | 19.996 | 20.077 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 32k | calibrated | 2 | 6/6 | 34.789 | 36.002 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 95k | calibrated | 1 | 3/3 | 22.505 | 22.506 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 95k | calibrated | 2 | 6/6 | 45.172 | 45.459 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 180k | calibrated | 1 | 3/3 | 31.870 | 31.875 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 180k | calibrated | 2 | 6/6 | 63.784 | 63.793 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 190k | calibrated | 1 | 3/3 | 32.657 | 32.658 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 190k | calibrated | 2 | 6/6 | 64.763 | 64.828 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 250k | calibrated | 1 | 3/3 | 37.887 | 37.902 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | near per-slot limit (250k of 262144); TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-ctx524k-bench-20260526T001055Z | Q4 524k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 524288 | 2 | 262144 | 250k | calibrated | 2 | 6/6 | 76.620 | 77.774 | not available | not available | not available | not available | not available | not available | 41434 | not available | not available | near per-slot limit; TTFT not extracted; DCGM private archive only |
| RTX 6000 Ada | ada6000-phase4-q6-synthetic-sanity-20260526T065829Z | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 400000 | 2 | 200000 | 1k | calibrated | 2 | 6/6 | 37.088 | — | 0.574 | 1.507 | not available | not available | not available | not available | 43304 | 69.1% | 221.5 | streaming_ttft from harness; DCGM from local Prometheus (Q6 phase only, §5.2) |
| RTX 6000 Ada | ada6000-phase4-q6-synthetic-sanity-20260526T065829Z | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 400000 | 2 | 200000 | 95k | calibrated | 2 | 6/6 | 49.790 | — | 1.218 | 1.228 | not available | not available | not available | not available | 43304 | 69.1% | 221.5 | streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase4-q6-synthetic-sanity-20260526T065829Z | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 400000 | 2 | 200000 | 190k | calibrated | 1 | 3/3 | 37.894 | — | 1.154 | 1.186 | not available | not available | not available | not available | 43304 | 69.1% | 221.5 | near per-slot limit; streaming_ttft from harness |
| RTX 6000 Ada | ada6000-phase4-q6-synthetic-sanity-20260526T065829Z | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 400000 | 2 | 200000 | 190k | calibrated | 2 | 6/6 | 74.157 | — | 1.537 | 1.542 | not available | not available | not available | not available | 43304 | 69.1% | 221.5 | near per-slot limit; streaming_ttft from harness |
| RTX 5090 | 5090-phase1-bench-20260526T111748Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 1k | calibrated | 2 | 6/6 | 18.994 | — | 0.445 | not available | not available | not available | not available | 55.3 | 27943 | 92% | 574.7 | streaming_ttft harness-side; DCGM from exported JSON; server-side LiteLLM TTFT p50/p95 aggregate only (1.67s/22.17s across all 74 requests, not per row) |
| RTX 5090 | 5090-phase1-bench-20260526T111748Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 32k | calibrated | 2 | 6/6 | 22.286 | — | 0.729 | not available | not available | not available | not available | 47.5 | 27943 | 92% | 574.7 | streaming_ttft harness-side |
| RTX 5090 | 5090-phase1-bench-20260526T111748Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 95k | calibrated | 1 | 3/3 | 13.997 | — | 0.818 | not available | not available | not available | 77.7 | not available | 27943 | 92% | 574.7 | streaming_ttft harness-side; per-row p95 not published |
| RTX 5090 | 5090-phase1-bench-20260526T111748Z | Q4 200k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 | 2 | 100000 | 95k | calibrated | 2 | 6/6 | 27.964 | — | 1.018 | not available | not available | not available | not available | 38.0 | 27951 | 92% | 574.7 | streaming_ttft harness-side; TTFT p95 per row not published |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 1k | calibrated | 1 | not available | 2.26 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | LiteLLM least-busy routing; warm KV cache; no DCGM/TTFT data for this run |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 32k | calibrated | 1 | not available | 2.89 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | warm KV cache; no DCGM/TTFT data |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 95k | calibrated | 1 | not available | 1.45 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | KV cache hit; anomalously low — cache warm state, not steady-state |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 1k | calibrated | 4 | 12/12 | 8.48 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | 4-slot saturation (4 clients, 4 total slots); private curl metrics show HTTP 200 for measured requests; no route attribution |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 32k | calibrated | 4 | 12/12 | 15.30 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | 4-slot saturation; private curl metrics show HTTP 200 for measured requests; no route attribution |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 95k | calibrated | 4 | 12/12 | 70.08 | 133.47 | not available | not available | not available | not available | not available | not available | not available | not available | not available | high variance; cold-backend assignment inferred in batch 1; p95 tail = cold backend receiving 95k request; no per-request route attribution |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 1k | calibrated | 6 | 18/18 | 9.77 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | over-saturation (6 clients > 4 slots); private curl metrics show HTTP 200 for measured requests; queueing expected |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 32k | calibrated | 6 | 18/18 | 14.25 | — | not available | not available | not available | not available | not available | not available | not available | not available | not available | over-saturation; private curl metrics show HTTP 200 for measured requests; no route attribution |
| 2× RTX 5090 | dual-5090-bench-20260526T150629Z | Q4 200k/2 per GPU | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 200000 per GPU | 2 per GPU (4 total) | 100000 | 95k | calibrated | 6 | 18/18 | 7.42 | 74.53 | not available | not available | not available | not available | not available | not available | not available | not available | not available | p50 fast (both backends warm); p95 tail from cold batch 1; warm steady-state p50 is not comparable to cold-start runs; no per-request route attribution |

**Hardware metric coverage note:**
- RTX 6000 Ada (200k/2, 300k/2, 400k/2, 524k/2 phases 1–3): `vram_max_mib` and `gpu_util_avg`/`power_avg_w` are pre-computed summaries from run artifacts; raw timeseries archived privately, not in public dataset. Per-row attribution not available.
- RTX 6000 Ada Q6 (400k/2, phase 4): DCGM computed from local Prometheus `:9191` during Q6 window.
- RTX 5090 (phase1+3): DCGM computed from exported JSON timeseries under `data/ (source repo)`.
- Dual RTX 5090: no DCGM JSON exports pulled; hardware metrics not available.

---

## Table 2: Context Scaling Table (Ada A6000 only)

Rows: one per context configuration. All runs: `Qwen3.6-27B-UD-Q4_K_XL.gguf`, 2 slots, RTX 6000 Ada.  
"max tested prompt" = largest prompt target in the run. "c2 success at max" = whether c2 (2 concurrent requests) succeeded at the maximum tested prompt size.

| profile | run_id | ctx_size | per_slot_ctx | max_tested_prompt | c2_success_at_max | vram_max_mib | vram_headroom_mib | wall_p50_at_max_c2_s | wall_p95_at_max_c2_s | interpretation |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| Q4 200k/2 | ada6000-phase1-baseline-20260525T202158Z | 200000 | 100000 | 95k | 6/6 | 27854 | ~21286 | 45.581 | 45.830 | largest prompt is 95k; per-slot ctx (100k) leaves 5k token overhead above tested max; TTFT not available for this run |
| Q4 300k/2 | ada6000-phase2-ctx300k-20260525T215448Z | 300000 | 150000 | 140k | 6/6 | 31906 | ~17234 | 54.770 | 54.891 | 140k prompt at 150k slot ctx = 93% slot fill; streaming_ttft 140k c2 p50=0.366s, p95=0.477s |
| Q4 400k/2 | ada6000-ctx400k-bench-20260525T224858Z | 400000 | 200000 | 190k | 6/6 | 36180 | ~12960 | 64.868 | — | 190k prompt at 200k slot ctx = 95% slot fill; streaming TTFT not extracted from 400k artifacts |
| Q4 524k/2 | ada6000-ctx524k-bench-20260526T001055Z | 524288 | 262144 | 250k | 6/6 | 41434 | ~7706 | 76.620 | 77.774 | 250k prompt at 262144 slot ctx = 95% slot fill; VRAM headroom ~7.5 GB — viable but limited; streaming TTFT not extracted |

**VRAM scaling note:** Each +100k context step adds approximately 4,000–5,000 MiB. Values are from DCGM pre-computed summaries (phases 1–3 in the private archive; phase 4 Q6 local). VRAM is flat once loaded; headroom values are approximate (total VRAM = 49,140 MiB confirmed for Ada A6000).

**Missing data:** Streaming TTFT per row for 400k and 524k runs is not extracted from artifacts. The streaming harness was in use for those runs (same version as 300k), but the values were not published in the source documents used for normalization.

---

## Table 3: Agent Workload Table

**Caveat (apply to all rows):** Each scenario was executed once per configuration. Single-run variance is uncharacterized. Wall time includes tool call execution, inter-step latency, and agent framework overhead — it is not pure GPU inference time and must not be converted to TPS. Pass/fail is runtime pass/fail only; output correctness was not evaluated.

| hardware | profile | run_id | scenario | result | wall_s | tool_failures | notes | caveats |
|---|---|---|---|---|---:|---|---|---|
| RTX 6000 Ada | Q4 200k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | A: repo summary | pass | 83.0 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 200k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | B: launch/runtime | pass | 105.4 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 200k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | B: bench/observability | pass | 107.7 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 200k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | D: normal | pass | 51.3 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 200k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | D: heavy | pass | 919.4 | not available | Anomalously high; likely tool retry or agent path divergence; single run | Single-run observation; not representative of steady-state; do not treat as a typical workload time |
| RTX 6000 Ada | Q4 400k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | A: repo summary | pass | 81.9 | not available | Single run; same run ID as 200k comparison | Single-run observation only |
| RTX 6000 Ada | Q4 400k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | B: launch/runtime | pass | 85.0 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 400k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | B: bench/observability | pass | 86.1 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 400k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | D: normal | pass | 33.3 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q4 400k/2 | ada6000-phase3-agent-200k-vs-400k-20260526T042003Z | D: heavy | pass | 167.7 | not available | Single run | Dramatic drop vs 200k D:heavy (919s→168s); single run, no variance data |
| RTX 6000 Ada | Q6 400k/2 | ada6000-phase4-q6-agent-20260526T054743Z | A: repo summary | not available | not available | not available | Scenario A was not run in Q6 phase | Missing: Q6 phase skipped scenario A |
| RTX 6000 Ada | Q6 400k/2 | ada6000-phase4-q6-agent-20260526T054743Z | B: launch/runtime | pass | 137.974 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q6 400k/2 | ada6000-phase4-q6-agent-20260526T054743Z | B: bench/observability | pass | 196.418 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q6 400k/2 | ada6000-phase4-q6-agent-20260526T054743Z | D: normal | pass | 70.289 | not available | Single run | Single-run observation only |
| RTX 6000 Ada | Q6 400k/2 | ada6000-phase4-q6-agent-20260526T054743Z | D: heavy | pass | 227.044 | not available | Single run | Single-run observation only |
| RTX 5090 | Q4 200k/2 | 5090-phase3-agent-20260526T115516Z | A: repo summary | pass | 26.7 | not available | Single run; KV cache warm from prior synthetic run | Single-run; warm cache state; not comparable to cold-start |
| RTX 5090 | Q4 200k/2 | 5090-phase3-agent-20260526T115516Z | B: launch/runtime | pass | 58.1 | not available | Single run; warm cache | Single-run observation only |
| RTX 5090 | Q4 200k/2 | 5090-phase3-agent-20260526T115516Z | B: bench/observability | pass | 66.8 | not available | Single run; warm cache | Single-run observation only |
| RTX 5090 | Q4 200k/2 | 5090-phase3-agent-20260526T115516Z | D: normal | pass | 37.3 | not available | Single run; warm cache | Single-run observation only |
| RTX 5090 | Q4 200k/2 | 5090-phase3-agent-20260526T115516Z | D: heavy | pass | 113.2 | not available | Single run; warm cache | Single-run; warm cache; Ada D:heavy 919s was a different execution path — direct ratio is not a controlled GPU speedup |

**What is not in this table:**
- Token counts per scenario (agent varies per run; not extracted from artifacts).
- LLM request counts per scenario (not extracted per-scenario from source documents).
- TTFT per agent step (not available at per-step granularity in source documents).
- Dual RTX 5090 agent workload (not run; only synthetic was benchmarked for dual config).

---

## Table 4: Quant Comparison Table (Q4_K_XL vs Q6_K_XL, Ada A6000 400k/2)

All rows: RTX 6000 Ada, ctx_size=400000, parallel=2, per_slot_ctx=200000, Qwen3.6 27B UD.  
Baseline = Q4_K_XL. Comparison = Q6_K_XL.  
`delta_vs_baseline`: positive = Q6 is slower/larger than Q4 baseline. Negative = Q6 is faster/smaller (not expected here).

**Synthetic rows** (source: `ada6000-phase4-q6-synthetic-sanity-20260526T065829Z` vs `ada6000-ctx400k-bench-20260525T224858Z`):

| hardware | profile | model/quant | scenario/row | wall_s | ttft_s | vram_max_mib | delta_vs_baseline | quality_evidence_available |
|---|---|---|---|---:|---:|---:|---|---|
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 1k c2 (synthetic) | 31.839 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 1k c2 (synthetic) | 37.088 | 0.574 (streaming) | 43304 | wall +5.249s (+16.5%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 95k c2 (synthetic) | 45.322 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 95k c2 (synthetic) | 49.790 | 1.218 (streaming) | 43304 | wall +4.468s (+9.9%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 190k c1 (synthetic) | 32.600 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 190k c1 (synthetic) | 37.894 | 1.154 (streaming) | 43304 | wall +5.294s (+16.2%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | 190k c2 (synthetic) | 64.868 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | 190k c2 (synthetic) | 74.157 | 1.537 (streaming) | 43304 | wall +9.289s (+14.3%); VRAM +7124 MiB (+19.7%) | no |

**Agent rows** (source: `ada6000-phase4-q6-agent-20260526T054743Z` vs `ada6000-phase3-agent-200k-vs-400k-20260526T042003Z`):

| hardware | profile | model/quant | scenario/row | wall_s | ttft_s | vram_max_mib | delta_vs_baseline | quality_evidence_available |
|---|---|---|---|---:|---|---:|---|---|
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | B: launch/runtime (agent) | 85.006 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | B: launch/runtime (agent) | 137.974 | not available | 43304 | wall +52.968s (+62.3%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | B: bench/observability (agent) | 86.058 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | B: bench/observability (agent) | 196.418 | not available | 43304 | wall +110.360s (+128.2%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | D: normal (agent) | 33.275 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | D: normal (agent) | 70.289 | not available | 43304 | wall +37.014s (+111.2%); VRAM +7124 MiB (+19.7%) | no |
| RTX 6000 Ada | Q4 400k/2 | `Qwen3.6-27B-UD-Q4_K_XL.gguf` | D: heavy (agent) | 167.697 | not available | 36180 | baseline | no |
| RTX 6000 Ada | Q6 400k/2 | `Qwen3.6-27B-UD-Q6_K_XL.gguf` | D: heavy (agent) | 227.044 | not available | 43304 | wall +59.347s (+35.4%); VRAM +7124 MiB (+19.7%) | no |

**Notes on quant comparison:**
- `ttft_s` column: Q4 TTFT was not extracted for 400k runs. Q6 TTFT is streaming (harness-side) from the Q6 sanity run.
- VRAM delta for Q6 vs Q4 at 400k/2: +7,124 MiB (+19.7% of Q4 footprint). Q4 VRAM from DCGM pre-computed summary; Q6 VRAM from local Prometheus.
- Agent wall time deltas reflect the combined effect of slower Q6 decode AND the specific execution path taken by OpenCode in each single run. Deltas are not a controlled measurement of quant overhead alone.
- `quality_evidence_available: no` for all rows. Quality evaluation (perplexity, task accuracy) is out of scope for this study.

---

## Coverage Gaps Summary

The following data was expected but not available in source documents for normalization:

| gap | affected rows | reason | recovery path |
|---|---|---|---|
| Streaming TTFT for Ada 400k/2 Q4 synthetic | ada6000-ctx400k-bench rows | Streaming harness used but per-row TTFT not extracted into published docs | Pull from the private archive run artifacts |
| Streaming TTFT for Ada 524k/2 Q4 synthetic | ada6000-ctx524k-bench rows | Same as above | Pull from the private archive run artifacts |
| DCGM per-run metrics for Ada phases 1–3 | 200k/300k/400k/524k rows | Raw timeseries in the private archive `20260525T202108Z` only; not exported locally | Run `promql-range-export` from the private archive |
| DCGM for dual RTX 5090 | dual-5090-bench rows | TSDB exists in the private archive but no local range export was pulled | Pull from the private archive |
| Per-scenario token counts for agent runs | all agent rows | Not extracted from harness outputs | Parse run artifacts (`body-*.json`) |
| Q4 400k/2 TTFT in quant comparison table | Table 4 Q4 rows | Not extracted; Q6 sanity comparison table only showed Q6 TTFT | Pull from the private archive or re-derive from 400k run artifacts |
| Per-row TTFT p95 for RTX 5090 synthetic | 5090 phase1 rows | Source published p95 as "—"; 3-sample window high variance | Not recoverable; would require re-run with more repeats |
| per-request route attribution for dual RTX 5090 rows | dual-5090-bench rows | Not captured in LiteLLM access logs, response bodies, curl metrics, or valid backend metrics | Requires rerun with structured LiteLLM routing logs, response header marker, or custom callback |
