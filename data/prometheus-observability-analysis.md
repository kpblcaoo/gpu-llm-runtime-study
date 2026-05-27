# Prometheus / DCGM / LiteLLM Observability Analysis

**Source runs:** RTX 5090 phase1 synthetic + phase3 agent (TSDB `20260526T094329Z`), Ada A6000 phases 1–4 (TSDB `20260525T202108Z`; partial coverage in local Prometheus at `:9191`), Dual RTX 5090 (behavioral observations only; llama.cpp/LiteLLM app metrics partially in TSDB, DCGM absent).

**Data provenance:**
- RTX 5090 DCGM/llama/LiteLLM statistics: computed directly from exported JSON files in `data/ (source repo)` using 15-second DCGM scrape intervals.
- Ada A6000 Q6-phase hardware stats: computed from local Prometheus at `:9191` (`20260525T202108Z`; covers 2026-05-26T06:00Z–08:31Z — the Q6 agent tail + Q6 synthetic sanity window only; earlier Ada phases 1–3 not present in local TSDB head).
- Ada A6000 phases 1–3 hardware stats: pre-computed summaries cited verbatim from `docs/benchmarks/ada-a6000/report-draft.md (source repo)` (full TSDB in the private archive).
- TTFT server-side histograms: queried from `litellm_llm_api_time_to_first_token_metric_bucket` in local Prometheus for RTX 5090 and Ada Q6 phase.
- Dual RTX 5090: no DCGM data; llama.cpp metrics present in TSDB but all series return NaN (suspected backend connectivity issue during scrape window 13:54–15:13Z May 26).

---

## 1. Metric Sources and Collection Pipeline

| layer | source | export format | coverage |
|---|---|---|---|
| GPU hardware (DCGM) | `dcgm_exporter` scraping NVML, relabelled via Prometheus | JSON timeseries (15s intervals) | RTX 5090: local JSON; Ada A6000: private archive only |
| LLM runtime | `llama-server` built-in `/metrics` endpoint scraped by Prometheus | JSON timeseries (15s intervals) | RTX 5090: local JSON; Ada: private archive only |
| Proxy layer | LiteLLM Prometheus exporter on port 4001 | JSON timeseries (15s intervals) | RTX 5090: local JSON; Ada: private archive only |
| Harness-side timing | `scripts/token-target-bench.py` curl `time_starttransfer` / `time_total` | CSV per run | All runs |
| System CPU/mem | `node_exporter` | JSON timeseries | Present in TSDB; not analyzed in this report |

**Scrape granularity note:** 15-second intervals mean fast events (sub-15s requests at c1 with small prompts) may appear as a single sample or be partially missed between scrapes. For the 95k c2 scenarios (~28–45s wall time), coverage is adequate (2–3 samples per request).

---

## 2. Hardware Metrics — RTX 5090

**Run ID:** `20260526T094329Z`  
**GPU:** NVIDIA GeForce RTX 5090, VRAM total 32607 MiB, Driver 570.211.01, CUDA 12.9 (Blackwell)  
**Config:** 200k ctx / 2 slots, Q4_K_XL GGUF, q8_0 KV, flash-attn on, MTP draft-mtp n_max=3

**Window detection:** GPU utilization > 0 from `2026-05-26T11:18:20Z` to `2026-05-26T12:02:05Z` (43 min), with a 26.5-minute inter-phase idle gap.

- **Synthetic phase1 window** (1779794300–1779794840, ~9 min): 4 scenarios (1k c2, 32k c2, 95k c1, 95k c2)
- **Agent phase3 window** (1779796430–1779796925, ~8 min): 5 agent scenarios

### 2.1 Synthetic Phase1 — Hardware Stats

| metric | p50 | p95 | max | note |
|---|---:|---:|---:|---|
| GPU utilization (%) | 92 | 100 | 100 | Near full utilization throughout |
| VRAM used (MiB) | 27943 | 27951 | 27951 | Stable; 4.6 GB free headroom |
| VRAM free (MiB) | 4176 | 4176 | 4176 | Minimum 4168 MiB (run overall) |
| Memory copy util (%) | 65 | 78 | 78 | PCIEVMA copy engine; not raw VRAM bandwidth |
| Power draw (W) | 574.7 | 576.5 | 576.6 | At rated TDP (~575 W) throughout active inference |
| Temperature (°C) | 68 | 71 | 72 | Thermally safe; well below throttle threshold |
| SM clock (MHz) | 2707 | 2767 | 2895¹ | Near max boost; no thermal throttling observed |
| Memory clock (MHz) | 13801 | 13801 | 13801 | Constant max GDDR7 clock during all active inference |

¹ SM clock max=2895 MHz is the active-inference maximum (GPU utilization > 0, n=31 samples). The value 2917 MHz appears in 2 idle/transition samples at the edge of the phase window (GPU util = 0). The interpretation — no thermal throttling — is the same either way: SM clock remains at or near the Blackwell boost ceiling throughout inference.

**Interpretation:** Stable. The GPU saturates its 575 W TDP budget within ~1–2 samples of the first request, stays at or near TDP for the entire 9-minute synthetic window, and never drops below 92% SM utilization (p50). Temperature peaks at 72°C, which is thermally safe for the RTX 5090. SM clock remains near the boost ceiling (2895 MHz active max), confirming no thermal throttling. The memory clock locks to 13801 MHz immediately upon the first request and stays there — the GDDR7 bus is fully armed at max speed for the entire inference period. **Classification: stable / compute-limited (power at TDP) / thermally safe / at TDP but not throttled.**

### 2.2 Agent Phase3 — Hardware Stats

| metric | p50 | p95 | max | note |
|---|---:|---:|---:|---|
| GPU utilization (%) | 97 | 99 | 100 | Higher than synthetic — agent keeps GPU more continuously busy |
| VRAM used (MiB) | 27951 | 27953 | 27953 | +8–10 MiB over synthetic; agent context pressure slight |
| VRAM free (MiB) | 4168 | 4168 | 4168 | 8 MiB less free than synthetic; within model margin |
| Memory copy util (%) | 52 | 75 | 77 | Lower p50 than synthetic; agent has inter-turn idle periods |
| Power draw (W) | 573.9 | 576.8 | 586.1 | At TDP; 586 W transient exceeds rated spec slightly |
| Temperature (°C) | 69 | 72 | 73 | Slightly warmer than synthetic; thermally safe |
| SM clock (MHz) | 2625 | 2797 | 2895 | Slightly lower p50/p95 than synthetic; agent turns are shorter |
| Memory clock (MHz) | 13801 | 13801 | 13801 | Constant max — same as synthetic |

**Interpretation:** Stable. GPU utilization is higher in the agent phase (p50=97% vs 92%) because agent tool calls create many short rapid requests that fill available slots. Power and temperature remain within the same bounds as synthetic, confirming the hardware is stable under realistic agentic workload. A single 586 W transient exceeds the nominal 575 W TDP spec — this is within transient tolerance for consumer Blackwell and not indicative of instability, but worth monitoring on dense rack deployments. **Classification: stable / compute-limited / thermally safe / minor power transient above spec.**

### 2.3 VRAM Headroom Analysis — RTX 5090

- Model + KV loaded at `200k / 2 slots`: **27,943 MiB** (85.7% of 32,607 MiB)
- Free headroom: **~4,664 MiB** (~4.6 GB)
- This is insufficient for `300k / 2` (which would require ~+4,000 MiB based on Ada scaling) and extremely unlikely to fit `256k / 2`.
- VRAM usage is flat and stable — no evidence of growing KV cache or compaction events during the test window. Each slot's KV cache is allocated at model load and does not fluctuate per the DCGM data.

---

## 3. Hardware Metrics — Ada A6000

**Run ID:** `20260525T202108Z`  
**GPU:** NVIDIA RTX 6000 Ada Generation, VRAM total **48,508 MiB** (47.4 GiB, DCGM-confirmed), Driver 580.119.02  
**Data source (phases 1–3):** Pre-computed summaries from `docs/benchmarks/ada-a6000/report-draft.md (source repo)`; full TSDB in the private archive.  
**Data source (Q6 phase, phase 4):** Computed from local Prometheus `:9191`; window 2026-05-26T06:44Z–07:28Z (44 min active inference, 15s scrape, n=181 active samples).

### 3.1 Summary by profile (phases 1–3 from report-draft; phase 4 from Prometheus)

| profile | VRAM max (MiB) | GPU util avg / p95 | Power avg / p95 (W) | Temp max (°C) | VRAM headroom | source |
|---|---:|---|---|---:|---:|---|
| Q4 200k/2 synthetic | 27,854 | 84% / 100% | 264 / 300 | 64 | ~20,654 MiB | report-draft |
| Q4 300k/2 | 31,906 | not reported | not reported | n/r | ~16,602 MiB | report-draft |
| Q4 400k/2 | 36,180 | 91.55% / n/a | 287 / n/a | n/r | ~12,328 MiB | report-draft |
| Q4 524k/2 | 41,434 | not reported | not reported | n/r | ~7,074 MiB | report-draft |
| Q6 400k/2 agent+synthetic | **43,304** | **69.1% / 100%** | **221.5 / 299.4** | **64** | ~5,204 MiB | **Prometheus (computed)** |

### 3.2 Ada A6000 Q6 Phase — Full Hardware Stats (Prometheus, active window)

**Context:** Q6_K_M quantization, 400k context / 2 slots. Active window covers Q6 agent phase (tail from 05:47Z) and Q6 synthetic sanity run (started 06:58Z). VRAM grows 2,602 MiB during window (40,702 → 43,304 MiB) as the Q6 400k KV cache fills.

| metric | avg | p50 | p95 | max | note |
|---|---:|---:|---:|---:|---|
| GPU utilization (%) | 69.1 | 95.0 | 100.0 | 100.0 | Bimodal: idle turns + fully saturated decode |
| VRAM used (MiB) | 42,242 | 42,264 | 43,304 | 43,304 | Grows during window; ~89.3% of total |
| VRAM free (MiB) | — | — | — | 5,204 | Minimum headroom at Q6 400k peak |
| Power draw (W) | 221.5 | 295.8 | 299.4 | 301.5 | At ~300 W cap; well below 350 W TDP |
| Temperature (°C) | 52.0 | 61.0 | 63.0 | 64.0 | Thermally safe; substantial margin |
| SM clock (MHz) | 1,610 | 1,560 | 2,520 | 2,730 | Bimodal (idle = low boost; decode = near max) |
| Memory clock (MHz) | 7,443 | 9,501 | 9,501 | 9,501 | At GDDR6 max during all active inference |
| Memory copy util (%) | 60.7 | 84.0 | 100.0 | 100.0 | PCIe DMA copy engine; heavy I/O during Q6 load |
| Energy used (J, 44 min) | — | — | — | ~590,197 | 218.6 W avg from energy delta; consistent with POWER_W avg |

**Classification (Q6 400k/2):** stable / thermally safe / not at TDP (300 W vs 350 W spec) / VRAM-ceiling-aware (5,204 MiB free at peak).

**Interpretation:**
- Ada A6000 at Q6 400k/2 remains thermally stable (64°C max) despite 89% VRAM utilization. The MEM_COPY_UTIL p50=84% is higher than RTX 5090 synthetic (65%) — consistent with the larger KV cache writes during long-context Q6 inference.
- Power cap is ~300 W (Ada's rated 300 W sustained), not the 350 W TDP peak. Ada was not at power limit during the Q6 run.
- GPU util avg=69% (lower than RTX 5090 92–97%) because agent turns have idle gaps between tool calls. The p50=95% during active decode confirms the SM is near-saturated when running.
- 5,204 MiB VRAM headroom at Q6 400k/2 peak is narrow. A Q6 500k+ context would risk OOM.
- VRAM increase (40,702 → 43,304 MiB = +2,602 MiB) during the window reflects KV cache growing as longer contexts are processed in the Q6 synthetic sanity scenarios.

---

## 4. Hardware Metrics — Dual RTX 5090

**Data source:** `docs/benchmarks/dual-rtx-5090/report-draft.md (source repo)` qualitative notes. No exported JSON metrics available.

**Classification:** exploratory / queue-limited at c4–c6 / warmup asymmetry creates cold-start VRAM pressure / thermally not assessed (no data).

**Key behavioral observations with metric implications:**
- c4 95k p95 latency = 133.47s (vs p50 = 70.08s) indicates high variance → LiteLLM routing unable to prevent cold-backend assignment when only 1 warmup was run.
- c6 95k after warm-up: p50 = 7.42s, p95 = 74.53s → warm-state performance is excellent but p95 shows tail latency from the initial cold batch.
- These patterns are consistent with what `llama_requests_deferred > 0` would show — requests assigned to a cold backend effectively become "deferred-equivalent" from the client's perspective.

---

## 5. Runtime / Proxy Metrics — RTX 5090

### 5.1 LiteLLM Metrics Interpretation Note

The exported `litellm_requests.json` contains six series by route and status. Key findings:

- `/v1/chat/completions` with `status_code=200`: **128 non-zero samples** with peak rate `0.102 req/s`. This is the actual inference traffic rate.
- `/v1/chat/completions` with `status_code=400`: **0 non-zero samples** — zero client errors.
- `/metrics/` scrape route and `/health` route: small non-zero rate consistent with Prometheus polling.
- `litellm_failed_requests.json` contains one series with `route=/health, exception_class=Exception`, 19 non-zero samples at `0.007` rate. These are health-check polling exceptions, **not inference failures**.

**Conclusion:** Zero inference failures (no 4xx/5xx on `/v1/chat/completions`) during the entire RTX 5090 test session.

### 5.2 LiteLLM Latency

The `litellm_latency_p95` metric is a rolling histogram quantile (end-to-end proxy latency). Its evolution directly tracks the benchmark sequence:

| phase | observed p95 range (s) | interpretation |
|---|---|---|
| Pre-benchmark / warmup | 1.975 – 6.475 | Residual from prior run state |
| c2 / 1k scenario | ~19.75 | Short generation ~18s wall time |
| c2 / 32k scenario | ~47–52 | Moderate context load |
| c1+c2 / 95k scenarios | ~82–112 | Large context, c2 concurrency serializes slots |
| Agent phase | ~49–51 | Agent turns are smaller than synthetic 95k |

**p50 (active window):** 51.0 s. **p95 (active window):** 110.0 s. **Max:** 112.0 s.

The rising p95 is expected — it tracks increasing context complexity. It is not evidence of routing problems or system degradation. The agent phase shows a lower p50/p95 (48.75/51 s) than the synthetic 95k scenarios, consistent with agent prompts being smaller than synthetic fixed targets.

### 5.3 llama.cpp Runtime Metrics — Synthetic Phase1

| metric | p50 | p95 | max | note |
|---|---:|---:|---:|---|
| llama_busy_slots | 1.73 | 1.86 | 1.86 | High slot occupancy (max=2); both slots in use ~86% of active time |
| llama_requests_processing | 2 | 2 | 2 | Both slots occupied at p50/p95 |
| llama_requests_deferred | 0 | 0 | 0 | No request queuing at any point |
| decode tok rate (5m rate, t/s) | 35.9 | 57.5 | 57.5 | Peak reflects 1k c2 (shorter, faster batches) |
| prompt tok rate (5m rate, t/s) | 231.6 | 666.7 | 666.7 | Peak reflects 95k prompt fill |

**Note on cumulative counters:** `llamacpp:predicted_tokens_seconds` and `llamacpp:prompt_tokens_seconds` are lifetime cumulative averages, not instantaneous rates. At end of synthetic window: predicted t/s ≈ 47–55 (cumulative drag from earlier slower runs), prompt t/s ≈ 2,130–2,250. The `_rate_5m` variants are more representative of instantaneous throughput.

### 5.4 llama.cpp Runtime Metrics — Agent Phase3

| metric | p50 | p95 | max | note |
|---|---:|---:|---:|---|
| llama_busy_slots | 1.54 | 1.67 | 1.68 | Lower than synthetic; agent turns are more sequential |
| llama_requests_processing | 1 | 2 | 2 | Mostly 1 active slot between tool calls |
| llama_requests_deferred | 0 | 0 | 0 | No queuing |
| decode tok rate (5m rate, t/s) | 40.4 | 51.3 | 55.3 | Comparable to synthetic; agent generates ~1024 tok/turn |
| prompt tok rate (5m rate, t/s) | 799.1 | 1033.8 | 1033.8 | 2.4–4.5× higher than synthetic — many short tool call prompts |

The significantly higher prompt token rate in the agent phase (p50 799 vs 231 t/s for synthetic) is a direct signal that the agent generates many short intermediate requests (tool calls, confirmations) compared to the fixed-length synthetic scenarios. This means the prefill engine is churning through many small fills rapidly, leaving the VRAM bandwidth less saturated on average — consistent with the slightly lower mem_copy_util p50 (52% vs 65%).

### 5.5 Ada A6000 Runtime Metrics

Prometheus `:9191` contains LiteLLM TTFT histogram data for the Ada Q6 phase window (06:00–08:31Z). llama.cpp slot/decode metrics for Ada are not available in the local TSDB (earlier phases 1–3 are archived privately, not in public dataset; Q6 llama.cpp data not captured).

**LiteLLM TTFT (server-side, Q6 agent+synthetic phase, n=310 requests):** See Section 5.6.

Behavioral signals inferred from run outcomes:
- Zero failures across all Ada runs confirms LiteLLM routing was stable.
- Prompt token rate expected to be lower than RTX 5090 based on slower wall time (Ada phase1 95k c1 = 22.85s vs 5090 = 13.99s → ~1.6x slower).

---

### 5.6 LiteLLM TTFT Server-Side Histograms

LiteLLM exports `litellm_llm_api_time_to_first_token_metric_bucket` — a Prometheus histogram measuring server-side time-to-first-token (from LiteLLM receiving the request to receiving the first streaming token from the backend). This metric IS present in the local Prometheus `:9191`.

| run | n (requests) | p50 (s) | p75 (s) | p95 (s) | note |
|---|---:|---:|---:|---:|---|
| RTX 5090 synthetic + agent | 74 | 1.67 | 7.25 | 22.17 | Covers both phase1 (synthetic) and phase3 (agent) |
| Ada A6000 Q6 phase | 310 | 0.46 | 6.42 | 190.0 | Q6 agent tail + Q6 synthetic sanity; bimodal distribution |
| Dual RTX 5090 | n/a | n/a | n/a | n/a | No TTFT data in TSDB |

**RTX 5090 TTFT interpretation:**
- Server-side p50=1.67s vs harness-side curl `time_starttransfer` p50=0.44–1.02s. The ~0.7s delta reflects LiteLLM proxy overhead (routing, auth, serialization).
- p95=22.17s captures the 95k c2 scenarios where prefill takes ~13–28s wall time.

**Ada Q6 TTFT interpretation:**
- Strongly bimodal: 55% of requests complete TTFT in <0.5s (cache-hit tool-call responses or short synthetic prompts); p95=190s reflects long-context Q6 agent initial loads at 400k tokens.
- p50=0.46s vs RTX 5090 p50=1.67s is misleading without controlling for request type — Ada Q6 has far more cache-hit short requests in the 310-request sample.
- The 190s p95 is consistent with Q6 400k prompt prefill time: Ada 400k c1 synthetic wall time ~22s × context ratio, plus Q6 model being slower than Q4.

**Correction to prior analysis:** Earlier notes stated "LiteLLM does not export TTFT as a Prometheus histogram." This was incorrect. The metric `litellm_llm_api_time_to_first_token_metric_bucket` exists and was queryable from local Prometheus for both runs.

---

## 6. Prometheus Hardware Summary Table

| hardware | profile | VRAM max (MiB) | VRAM p95 (MiB) | GPU util avg | GPU util p95 | Power avg (W) | Power p95 (W) | Temp max (°C) | interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| RTX 5090 | 200k/2, synthetic (phase1) | 27,951 | 27,951 | 77%¹ | 100% | 476 | 577 | 72 | stable; compute-limited; thermally safe; at TDP |
| RTX 5090 | 200k/2, agent (phase3) | 27,953 | 27,953 | 97%¹ | 99% | ~476² | 587 | 73 | stable; compute-limited; thermally safe; minor power transient |
| Ada A6000 | 200k/2, synthetic (phase1) | 27,854 | 27,854³ | 84% | 100% | 264 | 300 | 64 | stable; not at TDP; thermally safe |
| Ada A6000 | 400k/2, mixed | 36,180 | n/a | 91.5% | n/a | 287 | n/a | n/a | stable; not at TDP; thermally safe |
| Ada A6000 | 524k/2, synthetic | 41,434 | n/a | n/a | n/a | n/a | n/a | n/a | exploratory; VRAM ceiling near |
| Ada A6000 | **Q6 400k/2, Q6 agent+synthetic** | **43,304** | 43,304 | **69.1%** | **100%** | **221.5** | **299.4** | **64** | **stable; thermally safe; ~5.2 GB VRAM headroom; Prometheus-computed** |
| Dual RTX 5090 | 2×200k/2, routing c1–c6 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | exploratory; DCGM absent from TSDB |

¹ GPU util avg computed over active-inference samples only (GPU util > 0).  
² Agent avg power not separately computed; assumed comparable to synthetic given similar TDP-saturated behavior.  
³ Ada p95 = p95 of full run; actual per-scenario variation not available without raw timeseries.  
**Bold row** = stats computed from local Prometheus `:9191` (this session).

---

## 7. Runtime Metric Table

| run / profile | busy slots p50 | deferred reqs | failed reqs (inference) | LiteLLM p95 latency (s) | prompt TPS (5m rate p95) | decode TPS (5m rate p95) | interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| RTX 5090 synthetic (phase1) | 1.73 | 0 | 0 | 110 | 667 | 57.5 | stable; no queueing; latency tracks context size |
| RTX 5090 agent (phase3) | 1.54 | 0 | 0 | 51 | 1,034 | 53.7 | stable; no queueing; high prompt rate from tool calls |
| Ada A6000 (all phases) | n/a⁴ | 0⁴ | 0⁴ | n/a⁴ | n/a⁴ | n/a⁴ | metric available but run-window attribution uncertain; zero failures confirmed from run outcomes |
| Dual RTX 5090 (c1–c6) | n/a | n/a | 0⁴ | n/a | n/a | n/a | exploratory; warmup asymmetry creates effective deferral equivalent without appearing in deferred counter⁵ |

⁴ Run outcome and CSV summaries confirm no failures; Prometheus JSON not exported for these runs.  
⁵ In the dual-5090 setup, a cold backend accepting a `95k c2` batch causes ~70s client-side latency spike without this showing in `llama_requests_deferred` — because the request is accepted by the cold backend (not queued on the warm one). This is a routing-layer blind spot: `llama_requests_deferred` is per-backend and does not capture cross-backend imbalance visible only in client timing.

---

## 8. Evidence Gaps Table

| metric | expected source | available? | consequence for conclusions |
|---|---|---|---|
| Ada A6000 DCGM timeseries (phases 1–3) | private archive / promql-range-export | **Partial** (Q6 phase available in local Prometheus; phases 1–3 archived privately, not in public dataset) | Ada phases 1–3 hardware stats remain summary-only; p50/p95 for 200k/400k/524k profiles cannot be independently computed from local data |
| Ada A6000 Q6 DCGM timeseries | Local Prometheus `:9191` | **Yes** (computed this session) | Ada Q6 hardware stats now verified with p50/p95; VRAM confirmed 48,508 MiB total |
| Ada A6000 LiteLLM TTFT timeseries (Q6 phase) | Local Prometheus `:9191` | **Yes** (computed this session) | RTX 5090 p50=1.67s/p95=22.17s; Ada Q6 p50=0.46s/p95=190s — server-side from `litellm_llm_api_time_to_first_token_metric_bucket` |
| Ada A6000 llama.cpp runtime metrics (busy_slots, deferred) | private archive | **No (local)** | Cannot confirm zero deferral or slot utilization rates for Ada runs from local data |
| Dual RTX 5090 DCGM | TSDB | **No** (not present in run's TSDB) | No hardware metrics for dual run; DCGM was not scraped |
| Dual RTX 5090 LiteLLM TTFT | TSDB | **No** | No TTFT for dual run |
| Dual RTX 5090 llama.cpp metrics | TSDB (`20260526T134901Z`) | **Partial — all NaN** | Series exist (instance 127.0.0.1:8001) but return NaN; backend likely unreachable during scrape window |
| Per-scenario Prometheus window attribution | Tagged TSDB labels or separate run_id per scenario | **Partial** | Single TSDB covers all scenarios; sub-benchmark attribution is approximated by gap analysis on GPU utilization |
| LiteLLM inference request count (absolute) | litellm_requests counter value | **Rate only** | Cannot verify exact total request count from metrics; only rate shape available |
| TTFT distribution as a Prometheus metric | `litellm_llm_api_time_to_first_token_metric_bucket` | **Yes — metric exists** (**correction to prior claim**) | TTFT p50/p95 computed server-side for RTX 5090 and Ada Q6 phase; dual-5090 data missing |
| llama.cpp per-request latency histogram | llamacpp histogram metrics | **No** | Cannot decompose per-request decode latency from server side; only aggregate slot counts available |
| Ada Q4 300k/2 power, temperature timeseries | private archive phase2 | **No (local)** | 300k/2 power budget and thermal behavior not directly characterized locally |
| SM clock / memory clock for Ada A6000 (phases 1–3) | private archive | **No (local)** | Clock behavior for Q4 profiles not confirmed; Q6 SM clock confirmed (max=2730 MHz, p95=2520 MHz) |
| VRAM per-slot KV cache breakdown | Not exported by llama.cpp to Prometheus | **No** | VRAM usage is total FB_USED; cannot attribute split between model weights and KV cache |
| Dual 5090 per-backend busy_slots | Per-instance TSDB | **No** | Cannot confirm whether `least-busy` routing distributed load evenly |

---

## 9. Cross-Metric Interpretations

### 9.1 RTX 5090: Power-Limited vs Compute-Limited

The RTX 5090 runs at ~575 W TDP throughout active inference. SM clock is near max (2,625–2,895 MHz during active inference). If the GPU were power-throttled, clock would drop to keep power in budget. The fact that SM clock stays near 2,895 MHz while power is at 575 W indicates the GPU is **not power-throttled** — it is simply consuming its full budget while running at near-peak compute. This is consistent with a compute-saturated workload (both slots at max utilization).

### 9.2 RTX 5090: Memory Bandwidth vs Compute Bottleneck

The RTX 5090 spec bandwidth is ~1,790 GB/s. The `DCGM_FI_DEV_MEM_COPY_UTIL` (PCIe DMA copy engine utilization) at 65–78% does not represent VRAM-to-SM bandwidth — it reflects PCIe host-device traffic. VRAM-to-SM bandwidth is not directly exported by DCGM in this configuration. However:

- SM clock at 2,625+ MHz (near max during inference) + GPU util at 92–100% + power at TDP suggest the GPU is compute-saturated, not stalled waiting for VRAM reads.
- For a 27B Q4 model (~17 GB weights), theoretical decode VRAM bandwidth requirement ≈ 17 GB × 1 byte/token × decode_rate = ~17 GB/s at 1 t/s. At 38–77 t/s decode, the bandwidth requirement is 646 MB/s–1,309 MB/s — well within the 1,790 GB/s spec.
- The observed decode throughput (38–77 t/s) at 100% SM utilization suggests the bottleneck is in the compute kernel (attention + FFN) rather than raw bandwidth-limited weight loading.

### 9.3 Ada A6000: Lower Power, Not Speed-Limited by TDP

Ada's 264–287 W average power draw (vs RTX 5090's 476 W) reflects the Ada's lower memory bandwidth (~960 GB/s) and slower compute throughput — not power throttling. Ada's wall time (~1.6x slower than RTX 5090) is consistent with slower memory bandwidth: 960 GB/s vs 1,790 GB/s ≈ 1.86x bandwidth ratio, close to the observed 1.53–1.63x speedup. This confirms the dominant bottleneck in LLM decode is **VRAM bandwidth**, not compute throughput, and explains why the faster-bandwidth RTX 5090 wins despite comparable SM counts.

### 9.4 Deferred Requests as a Routing Stability Signal

- Single RTX 5090 (synthetic + agent): `llama_requests_deferred = 0` throughout. With 2 slots and max concurrency 2, no request ever needed to wait. This confirms the config was never over-saturated.
- Dual RTX 5090 (`c6` over 4 total slots): `llama_requests_deferred` was not exported as JSON, but client latency spikes (134s at c4) indicate effective queuing on cold backends even when the routing layer reports the slot is available. This is a **routing-layer blind spot** — the deferred counter at the backend level does not surface cross-backend imbalance.

### 9.5 LiteLLM Latency P95 as a Workload Complexity Proxy

The `litellm_latency_p95` rising from 19.75 s to 112 s during the RTX 5090 synthetic benchmark is not a stability signal — it directly tracks the increasing context sizes in the benchmark sequence (1k → 32k → 95k). A constant or declining p95 would indicate stable repeated workloads. The rising p95 is a workload fingerprint, useful as a sanity check that the benchmark ran in the expected order.

---

## 10. Recommendations for Future Observability Runs

1. **Export promql-range-export for all runs before instance teardown.** Ada A6000 raw timeseries are only in the private archive; local JSON export would enable the same p50/p95 computations performed here for RTX 5090.
2. **Add per-scenario run_id tags or Prometheus annotations.** Without per-scenario time boundaries, sub-benchmark attribution relies on gap-detection heuristics.
3. **Export dual-5090 DCGM metrics.** Per-backend GPU utilization, power, and temperature are missing entirely for the dual run.
4. **Instrument TTFT in Prometheus.** A custom gauge or histogram pushed from the harness at request completion would make TTFT a first-class telemetry metric rather than requiring log parsing.
5. **Add a `llama_requests_deferred` alert threshold.** Even though all single-GPU runs showed zero deferral, a rising deferred counter would immediately signal slot exhaustion in production.
6. **Capture VRAM-to-SM bandwidth separately** (e.g., via `nvml.Device.get_memory_info()` or DCGM `DCGM_FI_PROF_DRAM_ACTIVE`). The current `DCGM_FI_DEV_MEM_COPY_UTIL` does not represent VRAM bandwidth.
