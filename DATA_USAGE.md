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

The data is provided to support transparency and partial reproducibility of the report. When reusing charts, tables, or conclusions:

- preserve attribution (see [NOTICE.md](NOTICE.md));
- do not present exploratory results as production-grade benchmarks;
- note that agent workload results are single-run observations and path variance is uncontrolled.

## Public Reproducibility Boundary

The public repository is sufficient to inspect the published methodology, normalized result tables, caveats, claim audit, charts, and benchmark harness scripts. It is also sufficient to verify which claims are explicitly marked as strong, moderate, weak, unsupported, or telemetry-limited.

The public repository is not sufficient to independently recompute every reported number from raw samples. Full raw Prometheus TSDB snapshots, unsanitized logs, per-request bodies, and some run-local artifacts remain in a private archive because they may contain sensitive labels, host paths, internal identifiers, or operational metadata.

Treat the public data as an auditable report package, not as a complete benchmark corpus. Claims that depend on pre-computed summaries, private TSDB windows, dual-backend route attribution, or per-scenario agent traces require access to the private archive or a fresh rerun with equivalent instrumentation.

## Recoverable From Private Artifacts

The following gaps may be recoverable from the private archive if the raw artifacts are inspected and sanitized:

- Ada Q4 phase 1-3 per-sample Prometheus/DCGM timeseries;
- Ada 400k/2 and 524k/2 per-row streaming TTFT, if present in run artifacts;
- dual RTX 5090 DCGM range exports, if the TSDB contains valid hardware series;
- dual RTX 5090 per-request route attribution, if structured routing logs or backend-specific request markers exist;
- per-scenario agent token counts, request counts, and tool-call variance;
- stronger evidence for dual-backend routing only if route attribution or backend-specific logs are present.

## Caveat

This dataset is not a universal GPU benchmark corpus. It reflects specific hardware, runtime configuration, model files, and test methodology described in the report. Results are scoped to the tested stack and should not be generalized beyond the conditions documented in the full report.
