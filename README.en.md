# GPU Runtime Research: RTX 6000 Ada vs RTX 5090 (May 2026)

**[Русская версия](README.ru.md)**

---

## What this is

This repository is a research artifact documenting a practical runtime and performance study of local long-context LLM inference on rented Vast.ai GPUs. The study covers NVIDIA RTX 6000 Ada Generation (48 GB) and RTX 5090 (32 GB) — including an exploratory dual RTX 5090 configuration — running `Qwen3.6-27B-UD` GGUF models through a `llama.cpp` + `LiteLLM` stack, with Prometheus/DCGM telemetry.

---

## Why it matters

The practical questions driving the study:

- How far can a 48 GB Ada A6000 be pushed for long-context serving (300k / 400k / 524k) before hitting VRAM or stability limits?
- At the same `200k / 2` profile, how much faster is the RTX 5090 vs Ada A6000?
- Does Q6 quantization fit the Ada A6000 at 400k context, and what does it cost operationally?
- Can LiteLLM route benchmark traffic across two independent RTX 5090 llama.cpp backends, and what telemetry is missing for that topology?
- How does GPU behavior differ between synthetic token-target benchmarks and realistic OpenCode agent workloads?
- Which metrics in the Prometheus/DCGM stack are genuinely informative, which are proxies, and which are misleading?

---

## Hardware and runtime stack

| component | details |
|---|---|
| GPU A | NVIDIA RTX 6000 Ada Generation — 48,508 MiB VRAM (DCGM-confirmed) |
| GPU B | NVIDIA RTX 5090 — 32,607 MiB VRAM, Blackwell compute 12.0, Driver 570.211.01, CUDA 12.9 |
| GPU C (exploratory) | 2× RTX 5090, two independent backends routed via LiteLLM |
| Inference backend | `llama-server` (llama.cpp), flash attention on, `q8_0` KV cache |
| Proxy layer | LiteLLM OpenAI-compatible endpoint, `least-busy` routing for dual-GPU |
| Model | `Qwen3.6-27B-UD-Q4_K_XL.gguf` (primary), `Qwen3.6-27B-UD-Q6_K_XL.gguf` (comparison) |
| Platform | Vast.ai rented GPU instances |
| Observability | Prometheus + DCGM Exporter + llama.cpp `/metrics` + LiteLLM exporter + node_exporter |
| Synthetic harness | `scripts/token-target-bench.py` — token-target prompts, calibrated via `/tokenize` |
| Agent harness | `scripts/phase3_opencode_local.py` — OpenCode scenarios A, B, D via SSH tunnel |

---

## Key findings

All claims are scoped to the tested stack and run IDs documented in the full report. See [claim audit](data/claim-audit.md) for evidence strength classification.

- **RTX 5090 is the faster `200k / 2` Q4 worker.** In identical-profile synthetic rows, RTX 5090 was 1.53×–1.63× faster than Ada A6000 (wall latency and decode TPS). All five OpenCode agent scenarios also completed faster, though agent wall times include tool execution and are not pure GPU throughput.

- **Ada A6000 is the better-supported long-context endpoint.** It successfully ran Q4 at 300k/2, 400k/2, and 524288/2 — profiles that exceed RTX 5090's ~4.6 GB VRAM headroom at 200k/2. Ada Q4 VRAM scales at roughly +4–5 GiB per +100k context step.

- **Ada Q4 400k/2 is the best-supported long-context agent candidate** in the tested stack: 36.2 GiB VRAM, ~12 GiB headroom, all five OpenCode scenarios completed. Scenario D (heavy) dropped from 919 s at 200k/2 to 168 s at 400k/2, though the exact cause was not traced.

- **Ada Q4 524288/2 is a viable but aggressive mode.** Completed all tested synthetic rows through 250k c2. VRAM headroom shrinks to ~7 GiB (DCGM-confirmed). Agent workloads were not tested at this profile.

- **Q6 on Ada 400k/2 is operationally viable** for the tested subset (+10–16% slower synthetically, +35–128% on single-run agent scenarios, +7.1 GiB VRAM vs Q4). VRAM headroom narrows to ~5.2 GiB. No quality evaluation was performed: there is no evidence that Q6 produces better outputs.

- **Dual RTX 5090 is a topology probe, not a benchmark.** LiteLLM successfully served benchmark traffic through one endpoint backed by two independent llama.cpp backends. Routing balance reliability, DCGM hardware data, and per-backend metrics were absent from this run.

- **Agent workloads behave differently from synthetic benchmarks.** GPU utilization shows a bimodal pattern: near-100% during inference, near-zero during tool execution. Scenario wall times include tool call latency and cannot be converted to GPU TPS figures.

- **Prometheus/DCGM telemetry is part of the evidence base.** RTX 5090 data is locally confirmed (exported JSON). Ada Q6 data is computed from local Prometheus. Ada Q4 phases 1–3 use pre-computed summaries (full TSDB in the private archive).

---

## Observed role candidates

Guidance derived from tested profiles only. Not production policy.

| role | candidate | notes |
|---|---|---|
| Fast interactive worker | RTX 5090, Q4 200k/2 | Fastest tested wall latency and decode TPS; 32 GB VRAM limits context scaling |
| Long-context agent endpoint | Ada A6000, Q4 400k/2 | Best-supported long-context candidate; ~12 GB headroom; all agent scenarios passed |
| Huge-context synthetic | Ada A6000, Q4 524288/2 | Tested through 250k c2; ~7 GB headroom; agent behavior untested |
| Higher-fidelity experiment | Ada A6000, Q6 400k/2 | Operationally viable; ~5 GB headroom; no quality benefit proven |
| Routed dual-backend pool | 2× RTX 5090, LiteLLM | Exploratory; warm-cache fast; routing reliability unproven |

---

## What was measured

| dimension | measurement | source |
|---|---|---|
| End-to-end wall latency | wall p50 / p95 per prompt/concurrency cell | harness CSV |
| Streaming TTFT (client-side) | first-chunk timestamp from streaming HTTP | harness (phases 2+ and RTX 5090) |
| Backend prefill time | llama.cpp `prompt eval time` log | llama.cpp logs |
| Server-side TTFT | `litellm_llm_api_time_to_first_token_metric_bucket` histogram | Prometheus (RTX 5090 + Ada Q6) |
| Decode throughput | predicted tokens per second | llama.cpp metrics + harness CSV |
| VRAM footprint | `gpu_memory_used_mb` (DCGM NVML) | Prometheus JSON / pre-computed summaries |
| GPU utilization | `gpu_utilization` SM % (DCGM) | Prometheus JSON |
| Power draw | `gpu_power_draw` W (DCGM) | Prometheus JSON |
| Temperature | `gpu_temperature` °C (DCGM) | Prometheus JSON |
| SM / memory clock | `gpu_sm_clock` / `gpu_memory_clock` MHz (DCGM) | Prometheus JSON |
| Slot utilization | `llama_busy_slots` / `llama_requests_deferred` | Prometheus JSON |
| Proxy request health | `litellm_requests`, `litellm_failed_requests`, `litellm_latency_p95` | Prometheus JSON |
| Agent scenario wall time | end-to-end scenario time including tool calls | harness output |
| Agent pass/fail | runtime completion + log pattern match | harness output |

---

## Full documentation

| document | contents |
|---|---|
| [Full report (EN)](docs/en/gpu-runtime-research-report-2026-05.md) | Research questions, methodology, all results, interpretations, caveats |
| [Full report (RU)](docs/ru/gpu-runtime-research-report-2026-05.md) | Russian-language version of the full report |
| [Normalized results](data/normalized-results.md) | All numeric results in uniform tables; coverage gaps documented |
| [Prometheus / DCGM analysis](data/prometheus-observability-analysis.md) | Per-metric interpretation, data provenance, scrape coverage |
| [Claim audit](data/claim-audit.md) | Every major claim mapped to evidence type and strength rating |
| [Artifact inventory](data/artifact-inventory.md) | All runs (including failed/aborted), documents, and metric sources |
| [Metrics index](data/metrics_index.md) | DCGM relabelling map, full metric catalogue |

---

## Repository layout

```
├── README.md                  Short bilingual landing
├── README.ru.md               Full Russian landing
├── README.en.md               This file — full English landing
├── docs/
│   ├── en/                    Full report (English)
│   └── ru/                    Full report (Russian)
├── data/                      Normalized results, claim audit, metrics index, artifact inventory
├── charts/                    Benchmark charts (EN); charts/ru/ — Russian-labelled charts
└── scripts/                   Benchmark harnesses and data processing tools
    ├── token-target-bench.py  Synthetic benchmark harness
    ├── phase3_opencode_local.py  Agent harness (local)
    ├── phase3_agent_remote.py    Agent harness (remote)
    └── sanitize-metrics.py    Prometheus export sanitization
```

---

## Limitations

This study does not establish:

- **Model output quality.** No perplexity, MMLU, coding benchmark, or task-accuracy evaluation was performed. Q6 quality superiority is not proven. Agent pass/fail is runtime completion only.
- **Universal GPU ranking.** Results are scoped to the tested stack (llama.cpp + LiteLLM, specific GGUF files, specific Vast.ai host configurations).
- **Production multi-user load behavior.** The benchmark harness controlled concurrency at 1–6 parallel requests.
- **Reproducible speedup ratios.** Agent workload results are single-run observations. Path variance (tool retries, reasoning path branching) is uncontrolled.
- **Cost/performance model.** No normalized cost model was built. Rental price data was not included.
- **VRAM-bandwidth bottleneck confirmation.** The 1.5–1.6× speedup is consistent with hardware bandwidth differences, but VRAM-to-SM bandwidth was not directly measured.
- **Dual RTX 5090 routing reliability.** The dual run lacks DCGM exports, per-backend llama.cpp metrics, and LiteLLM TTFT data. It is a topology probe, not a capacity baseline.

---

## Data and reproducibility

Raw Prometheus TSDB snapshots are archived privately and not included in the public dataset. Sanitized metric JSON for RTX 5090 is available via `data/metrics_index.md`. Benchmark harness scripts are in `scripts/`. Benchmark prompts use pseudo-random filler text.

Internal labels, API keys, host identifiers, and personal data have been removed from all published artifacts.

---

## About the author

This study was conducted by Mikhail Stepanov, a DevSecOps engineer with a background in information security and systems administration.

The work reflects a personal technical investigation into practical long-context LLM inference, GPU runtime behavior, and operational observability for agent-oriented workflows.

---

## Resource and independence statement

This study was conducted independently, using personal time, personal tooling, and rented or personally controlled compute resources.

No employer-owned infrastructure, internal repositories, confidential datasets, production systems, customer data, or non-public company materials were used in the benchmark workloads or report artifacts.

The test workloads were synthetic, public, sanitized, or personally prepared for the purpose of this study.

---

## Resource limitations

The study was intentionally limited to the hardware and runtime profiles available during the test window. It should be interpreted as a practical runtime investigation, not a complete academic benchmark.

The following constraints affected the scope:

- limited rental and test time;
- limited number of repeated agent workload runs;
- no production multi-user workload;
- no exhaustive model or quantization matrix;
- no formal answer-quality evaluation;
- some profiles were exploratory rather than final steady-state benchmarks.

These limitations are documented throughout the full report and should be considered when interpreting the conclusions.

---

## License and reuse

Reports, documentation, charts, and derived data tables are licensed under [CC BY 4.0](LICENSE-DOCS.md). Scripts in `scripts/` are licensed under the [MIT License](LICENSE-CODE.md). See [NOTICE.md](NOTICE.md) for attribution details.

When reusing charts, tables, or conclusions, please preserve attribution and avoid presenting exploratory results as production-grade benchmarks.

---

*May 2026 · Preliminary research artifact*
