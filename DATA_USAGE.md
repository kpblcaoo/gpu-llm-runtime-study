# Data Usage and Reproducibility Notes

This repository contains sanitized benchmark outputs, derived tables, charts, and report material from a personal GPU LLM runtime study.

## Included

- normalized benchmark result tables;
- selected Prometheus/DCGM metric summaries;
- LiteLLM and llama.cpp metric summaries where safe to publish;
- charts derived from benchmark artifacts;
- sanitized methodology and run notes.

## Not included

- secrets, API keys, tokens, or credentials;
- private repositories or internal tooling;
- employer-owned data or infrastructure;
- customer data;
- internal company materials;
- unsanitized logs containing sensitive paths, hosts, or labels;
- raw Prometheus TSDB snapshots (archived privately, not included in the public dataset).

## Reuse

The data is provided to support transparency and reproducibility of the report. When reusing charts, tables, or conclusions:

- preserve attribution (see [NOTICE.md](NOTICE.md));
- do not present exploratory results as production-grade benchmarks;
- note that agent workload results are single-run observations and path variance is uncontrolled.

## Caveat

This dataset is not a universal GPU benchmark corpus. It reflects specific hardware, runtime configuration, model files, and test methodology described in the report. Results are scoped to the tested stack and should not be generalized beyond the conditions documented in the full report.
