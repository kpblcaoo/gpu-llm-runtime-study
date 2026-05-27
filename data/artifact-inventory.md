# GPU Runtime Research Artifact Inventory

This document provides a comprehensive inventory of all documentation, benchmark runs, and metric sources collected during the GPU runtime performance research (May 2026). It covers the Ada A6000, RTX 5090, and Dual RTX 5090 configurations.

---

## 1. Document Inventory

The following table lists all markdown and documentation artifacts relevant to the benchmark and research execution:

| path | type | topic | contains numeric results? | contains methodology? | contains caveats? | should be used in main report? | notes |
|---|---|---|:---:|:---:|:---:|:---:|---|
| [docs/agent-and-benchmark-harness.md](source repo) | Markdown | Test Harness Spec | no | yes | no | yes | Describes python harness usage, model configurations, and script parameters. |
| [docs/langfuse-local.md](source repo) | Markdown | Tooling Docs | no | no | no | no | Details local Langfuse integration setup. |
| [docs/observability-artifact-handoff.md](source repo) | Markdown | Ops / Telemetry | yes | yes | yes | yes | Notes on TSDB vs JSON export workflows and egress cost controls. |
| [docs/vast-llama-template-notes.md](source repo) | Markdown | VM Configuration | no | no | yes | no | Setup notes for Llama Vast templates. |
| [docs/vast-run-harness-plan.md](source repo) | Markdown | Research Plan | no | yes | yes | yes | Initial scope, test configurations, and goals of the benchmark. |
| [docs/vast-vllm-template-notes.md](source repo) | Markdown | VM Configuration | no | no | no | no | Notes regarding vLLM runtime alternative. |
| [data/metrics_index.md](source repo) | Markdown | Telemetry Schema | no | yes | yes | yes | Re-labeling maps and explanations for DCGM, llama.cpp, and LiteLLM metrics. |
| docs/benchmarks/process/workflows.md (source repo) | Markdown | Procedures | no | yes | no | yes | Standardized workflow for benchmarks (warmup, snapshots, sanitization). |
| docs/benchmarks/process/follow-up-gpu-test-handoff.md (source repo) | Markdown | Handoff notes | no | no | yes | yes | Identifies issues with TTFT and routing warmup anomalies. |
| docs/benchmarks/ada-a6000/README.md (source repo) | Markdown | Repo / Run Guide | no | yes | no | no | Execution details specifically for Ada A6000. |
| docs/benchmarks/ada-a6000/automation.md (source repo) | Markdown | Scripts Guide | no | yes | no | no | Automation setups for Ada tests. |
| docs/benchmarks/ada-a6000/progress.md (source repo) | Markdown | Project Log | yes | yes | yes | yes | Chronological logging of phase completions and debug issues. |
| docs/benchmarks/ada-a6000/report-draft.md (source repo) | Markdown | Results Draft | yes | yes | yes | yes | Baseline, scaling, and agent numbers for Ada A6000. |
| docs/benchmarks/ada-a6000/report-handoff.md (source repo) | Markdown | Results Handoff | yes | no | yes | no | Post-run notes on results and telemetry exports. |
| docs/benchmarks/ada-a6000/report-outline.md (source repo) | Markdown | Structure Outline| no | no | no | no | Initial outline mapping for the Ada report. |
| docs/benchmarks/ada-a6000/runbook.md (source repo) | Markdown | Runbook Guide | no | yes | no | no | Instructions for replication of benchmarks. |
| docs/benchmarks/rtx-5090/progress.md (source repo) | Markdown | Project Log | yes | yes | yes | yes | Phase completions and execution details for RTX 5090. |
| docs/benchmarks/rtx-5090/report-draft.md (source repo) | Markdown | Results Draft | yes | yes | yes | yes | Performance speedups, VRAM limits, and agent results for RTX 5090. |
| docs/benchmarks/rtx-5090/test-plan.md (source repo) | Markdown | Test Plan | no | yes | yes | yes | Specific guidelines for evaluating Single RTX 5090. |
| docs/benchmarks/dual-rtx-5090/litellm-routing-plan.md (source repo) | Markdown | Configuration | no | yes | yes | yes | Details routing parameters and configs for dual backends. |
| docs/benchmarks/dual-rtx-5090/report-draft.md (source repo) | Markdown | Results Draft | yes | yes | yes | yes | Contains concurrency wall-time numbers and warmup asymmetry analysis. |
| docs/benchmarks/dual-rtx-5090/test-plan.md (source repo) | Markdown | Test Plan | no | yes | yes | yes | Multi-GPU routing baseline definition and harness parameters. |

---

## 2. Run Inventory

The table below lists all execution runs located in `runs/`. Incomplete, aborted, or developer/sandbox runs are explicitly flagged.

| run_id | hardware | model | quant/model file | ctx_size | parallel/slots | workload type | rows/scenarios completed | success status | benchmark CSV available | request rows available | Prometheus/DCGM available | LiteLLM metrics available | llama.cpp metrics/logs available | caveats |
|---|---|---|---|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|---|
| `ada6000-phase0-20260525T191508Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Smoke Test | 1 scenario (smoke) | success | no | no | no | yes | yes | Basic connection and validation smoke test only. |
| `ada6000-phase1-baseline-20260525T192443Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Synthetic | None | failed/aborted | no | no | no | no | no | Run aborted early during container startup. |
| `ada6000-phase1-baseline-20260525T202158Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Synthetic | 6 (1k, 32k, 95k c1/c2) | success | yes | yes | yes | yes | yes | Non-streaming TTFT was backend-only and discarded from CLI metrics. |
| `ada6000-phase2-ctx300k-20260525T212923Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 300k | 2 | Synthetic | None | failed/aborted | yes | yes | yes | yes | yes | Run aborted/superseded by `T215448Z`. |
| `ada6000-phase2-ctx300k-20260525T215448Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 300k | 2 | Synthetic | 8 (1k, 32k, 95k, 140k c1/c2) | success | yes | yes | yes | yes | yes | Baseline for 300k scaling. |
| `ada6000-ctx400k-probe-20260525T223711Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 400k | 2 | Probe | 1 (VRAM startup check) | success | no | no | no | yes | yes | Context validation probe, not a full benchmark run. |
| `ada6000-ctx400k-bench-20260525T224115Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 400k | 2 | Synthetic | None | failed/aborted | no | no | no | no | no | Empty directory; failed to execute. |
| `ada6000-ctx400k-bench-20260525T224858Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 400k | 2 | Synthetic | 8 (1k, 32k, 95k, 190k c1/c2) | success | yes | yes | yes | yes | yes | Baseline for 400k scaling. |
| `ada6000-ctx524k-probe-20260525T234230Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 524k | 2 | Probe | 1 (250k request) | success | yes | yes | no | yes | yes | Probe to check maximum stable context constraints. |
| `ada6000-ctx524k-bench-20260526T001055Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 524k | 2 | Synthetic | 10 (1k, 32k, 95k, 190k, 250k c1/c2) | success | yes | yes | yes | yes | yes | Tighter VRAM footprint limits. |
| `ada6000-phase3-agent-200k-vs-400k-20260526T042003Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q4_K_XL | 200k & 400k | 2 | Agent | 5 scenarios per mode | success | yes | yes | yes | yes | yes | Agent comparison under realistic workloads. Single-run variance exists. |
| `ada6000-phase4-q6-agent-20260526T054743Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q6_K_XL | 400k | 2 | Agent | 4 scenarios (missing A) | success | yes | yes | yes | yes | yes | Q6 agent evaluation. Slower decode rates and higher VRAM footprint. |
| `ada6000-phase4-q6-synthetic-sanity-20260526T065829Z` | RTX 6000 Ada | Qwen3.6 27B UD | Q6_K_XL | 400k | 2 | Synthetic | 4 (1k c2, 95k c2, 190k c1/c2) | success | yes | yes | yes | yes | yes | Direct Q6 synthetic validation vs Q4 baseline. |
| `5090-phase1-bench-20260526T111748Z` | RTX 5090 | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Synthetic | 4 (1k c2, 32k c2, 95k c1/c2) | success | yes | yes | yes | yes | yes | Blackwell architecture required `LD_LIBRARY_PATH` libcuda override. Slow TTFT anomaly. |
| `5090-phase3-agent-20260526T115309Z` | RTX 5090 | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Agent | None | failed/aborted | no | no | no | no | no | Aborted early during Scenario A execution. |
| `5090-phase3-agent-20260526T115516Z` | RTX 5090 | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Agent | 5 scenarios | success | yes | yes | yes | yes | yes | Main 5090 agent benchmark. All scenarios passed cleanly. |
| `5090-phase3-agent-test` | RTX 5090 | Qwen3.6 27B UD | Q4_K_XL | 200k | 2 | Agent | 5 (partial fail) | partial | yes | yes | yes | yes | yes | Sandbox run; Scenario A and D-normal failed, others passed. |
| `dual-5090-bench-20260526T150629Z` | 2x RTX 5090 | Qwen3.6 27B UD | Q4_K_XL | 200k per GPU | 2 per GPU (total 4) | Synthetic | 9 (1k, 32k, 95k for c1, c4, c6) | success | no | yes | yes | yes | yes | LiteLLM `least-busy` routing to independent backends. Warmup asymmetry. |

---

## 3. Metric Source Inventory

The following table lists the telemetry metrics captured across all successful benchmarks. These metrics serve as the primary numerical evidence for the final report.

| metric family | source | file/path | unit | meaning | useful for which report section |
|---|---|---|---|---|---|
| `gpu_utilization` | DCGM Exporter | `metrics/prometheus/gpu_util.query_range.json` or `/metrics/gpu.csv` | `%` | Streaming multiprocessor (SM) execution utilization | Sections 8, 9, 10, 12, 14 (GPU Performance, Q6 Study) |
| `gpu_memory_used_mb` | DCGM Exporter | `metrics/prometheus/vram_used.query_range.json` or `metrics/nvidia-smi.csv` | `MiB` | Amount of allocated GPU VRAM | Sections 8, 9, 10, 12, 14 (VRAM ceilings, scaling limits) |
| `gpu_power_draw` | DCGM Exporter | `metrics/prometheus/power.query_range.json` or `metrics/nvidia-smi.csv` | `W` | Power consumption of the board | Sections 8, 9, 10, 14 (Power consumption analysis) |
| `gpu_temperature` | DCGM Exporter | `metrics/prometheus/temperature.query_range.json` or `metrics/nvidia-smi.csv` | `°C` | Core temperature of the GPU silicon | Sections 8, 9, 10, 14 (Thermal headroom/throttling) |
| `litellm_requests` | LiteLLM | `metrics/prometheus/litellm_requests.json` or logs | requests | Total requests processed by the load balancer | Section 7, 11, 13 (Run inventory, Agent workload) |
| `litellm_latency_p95` | LiteLLM | `metrics/prometheus/litellm_latency_p95.json` | seconds | 95th percentile end-to-end request duration | Sections 8, 9, 10, 11, 14 (End-to-end user latency) |
| `llama_busy_slots` | llama.cpp | `metrics/prometheus/llama_busy_slots.json` | slots | Active slots processing tokens concurrently | Sections 8, 9, 10, 11, 15 (Concurrency, Routing strategy) |
| `llama_predicted_tokens_per_second` | llama.cpp | `metrics/prometheus/llama_predicted_tokens_per_second.json` | tokens/sec | Output token generation speed (Decode speed) | Sections 8, 9, 10, 12, 14 (Raw decode speed comparison) |
| `llama_prompt_tokens_per_second` | llama.cpp | `metrics/prometheus/llama_prompt_tokens_per_second.json` | tokens/sec | Input token ingestion speed (Prefill speed) | Sections 8, 9, 10, 14 (Prefill performance comparison) |
| `llama_requests_deferred` | llama.cpp | `metrics/prometheus/llama_requests_deferred.json` | requests | Requests waiting in server queues due to slot saturation | Sections 10, 11, 15 (Queuing, deployment recommendations) |
