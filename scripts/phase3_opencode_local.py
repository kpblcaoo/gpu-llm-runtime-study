#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sanitize(text):
    text = text or ""
    text = re.sub(r"https?://[^\s'\"]+", "https://example.local", text)
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<TOKEN>", text)
    text = re.sub(r"(?i)(api[_-]?key|token|secret|password|master[_-]?key)(=|:)[^\s'\"]+", r"\1\2<SECRET>", text)
    return text


def percentile(vals, pct):
    vals = sorted(v for v in vals if v is not None and not math.isnan(v))
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * pct / 100.0
    f, c = math.floor(k), math.ceil(k)
    return vals[f] if f == c else vals[f] * (c - k) + vals[c] * (k - f)


def http_json(url, data=None, headers=None, timeout=30):
    body = json.dumps(data).encode() if data is not None else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def prom_export(prom_url, start, end, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    queries = {
        "vram_used": "DCGM_FI_DEV_FB_USED",
        "gpu_util": "DCGM_FI_DEV_GPU_UTIL",
        "power": "DCGM_FI_DEV_POWER_USAGE",
        "temperature": "DCGM_FI_DEV_GPU_TEMP",
    }
    summary = {}
    for name, query in queries.items():
        url = f"{prom_url}/api/v1/query_range?query={urllib.parse.quote(query)}&start={start:.3f}&end={end:.3f}&step=5"
        try:
            data = http_json(url, timeout=90)
            (out_dir / f"{name}.query_range.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            vals = []
            for result in data.get("data", {}).get("result", []):
                for _, v in result.get("values", []):
                    try:
                        vals.append(float(v))
                    except ValueError:
                        pass
            if vals:
                summary[name] = {"avg": sum(vals) / len(vals), "max": max(vals), "p95": percentile(vals, 95)}
        except Exception as exc:
            summary[name] = {"error": str(exc)}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_jsonl(path):
    request_count = 0
    tool_calls = 0
    failed_tool_calls = 0
    input_tokens = output_tokens = reasoning_tokens = ""
    text_parts = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        typ = str(obj.get("type", ""))
        if typ:
            if "tool" in typ.lower():
                tool_calls += 1
            if "error" in typ.lower():
                failed_tool_calls += 1
        if typ in ("message", "content", "assistant"):
            text_parts.append(json.dumps(obj, ensure_ascii=False))
        if typ in ("message", "request", "response"):
            request_count += 1
        usage = obj.get("usage") or obj.get("tokens") or {}
        if isinstance(usage, dict):
            input_tokens = usage.get("input") or usage.get("prompt_tokens") or usage.get("input_tokens") or input_tokens
            output_tokens = usage.get("output") or usage.get("completion_tokens") or usage.get("output_tokens") or output_tokens
            reasoning_tokens = usage.get("reasoning") or usage.get("reasoning_tokens") or reasoning_tokens
    return {
        "model_request_count": request_count or 1,
        "tool_calls": tool_calls,
        "failed_tool_calls": failed_tool_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "text": "\n".join(text_parts),
    }


def run_opencode(name, prompt, must, mode_dir, env, backend_url, prom_url):
    start_utc = utc()
    start_epoch = time.time()
    before = http_json(f"{backend_url}/slots", timeout=30)
    raw = mode_dir / "logs" / f"{name}.opencode.jsonl"
    raw.parent.mkdir(parents=True, exist_ok=True)
    (mode_dir / "agent").mkdir(parents=True, exist_ok=True)
    cmd = [
        "opencode",
        "run",
        "--format",
        "json",
        "--dangerously-skip-permissions",
        "--title",
        f"phase3-{name}",
        prompt,
    ]
    with raw.open("w", encoding="utf-8") as out:
        proc = subprocess.run(cmd, cwd=Path.cwd(), env=env, stdout=out, stderr=subprocess.STDOUT, timeout=1200)
    end_epoch = time.time()
    after = http_json(f"{backend_url}/slots", timeout=30)
    parsed = parse_jsonl(raw)
    sanitized = sanitize(raw.read_text(encoding="utf-8", errors="replace"))
    (mode_dir / "logs" / f"{name}.opencode.sanitized.jsonl").write_text(sanitized, encoding="utf-8")
    summary_text = sanitize(parsed["text"] or sanitized)[-12000:]
    (mode_dir / "agent" / f"{name}.summary.sanitized.md").write_text(summary_text + "\n", encoding="utf-8")
    (mode_dir / "agent" / f"{name}-slots-before.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    (mode_dir / "agent" / f"{name}-slots-after.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    prom = prom_export(prom_url, start_epoch, end_epoch, mode_dir / "metrics" / "prometheus" / name)
    lower = sanitized.lower()
    passed = proc.returncode == 0 and all(x in lower for x in must)
    return {
        "scenario": name,
        "start_utc": start_utc,
        "end_utc": utc(),
        "wall_s": round(end_epoch - start_epoch, 3),
        "model_request_count": parsed["model_request_count"],
        "input_tokens": parsed["input_tokens"],
        "output_tokens": parsed["output_tokens"],
        "reasoning_tokens": parsed["reasoning_tokens"],
        "tool_calls": parsed["tool_calls"],
        "failed_tool_calls": parsed["failed_tool_calls"],
        "request_latency_p50_s": round(end_epoch - start_epoch, 3),
        "request_latency_p95_s": round(end_epoch - start_epoch, 3),
        "streaming_ttft_p50_s": "",
        "streaming_ttft_p95_s": "",
        "pass_fail": "pass" if passed else "fail",
        "quality_note": "opencode run completed" if passed else f"opencode return={proc.returncode}; manual review needed",
        "vram_max_mib": prom.get("vram_used", {}).get("max", ""),
        "vram_p95_mib": prom.get("vram_used", {}).get("p95", ""),
        "gpu_util_avg": prom.get("gpu_util", {}).get("avg", ""),
        "gpu_util_p95": prom.get("gpu_util", {}).get("p95", ""),
        "power_avg_w": prom.get("power", {}).get("avg", ""),
        "power_p95_w": prom.get("power", {}).get("p95", ""),
        "temp_max_c": prom.get("temperature", {}).get("max", ""),
        "temp_p95_c": prom.get("temperature", {}).get("p95", ""),
    }


def write_csv(path, rows):
    fields = ["scenario", "start_utc", "end_utc", "wall_s", "scenario_group_wall_s", "model_request_count", "input_tokens", "output_tokens", "reasoning_tokens", "tool_calls", "failed_tool_calls", "request_latency_p50_s", "request_latency_p95_s", "streaming_ttft_p50_s", "streaming_ttft_p95_s", "pass_fail", "quality_note", "vram_max_mib", "vram_p95_mib", "gpu_util_avg", "gpu_util_p95", "power_avg_w", "power_p95_w", "temp_max_c", "temp_p95_c"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--mode", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--api-key", required=True)
    ap.add_argument("--backend-url", required=True)
    ap.add_argument("--prom-url", required=True)
    ap.add_argument("--context-limit", type=int, required=True)
    args = ap.parse_args()

    run_dir = Path("runs") / args.run_id
    mode_dir = run_dir / f"mode-{args.mode}"
    env = os.environ.copy()
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps({
        "model": "vast-llama/Loopy",
        "provider": {"vast-llama": {"npm": "@ai-sdk/openai-compatible", "name": "Vast llama.cpp", "options": {"baseURL": args.base_url, "apiKey": args.api_key, "timeout": False, "chunkTimeout": 600000}, "models": {"Loopy": {"name": "Loopy", "tool_call": True, "reasoning": True, "temperature": True, "limit": {"context": args.context_limit, "output": 4096}}}}},
    })

    prompts = {
        "scenario-a": ("Explore this repo using tools and produce a concise operational summary. Must identify Vast lifecycle scripts, custom llama runtime path, benchmark/run-harness assets. Do not inspect or print .env, runs/latest, certs, keys, chat IDs, or raw benchmark logs.", ["vast", "runtime", "benchmark"]),
        "scenario-b-launch": ("Summarize the launch/runtime workflow in this repo using tools. Include scripts, custom llama runtime, restart boundaries, and safety notes. Do not inspect or print secrets/local run state.", ["launch", "runtime", "llama"]),
        "scenario-b-observability": ("Summarize benchmark and observability workflow in this repo using tools. Include benchmark scripts, run harness, Prometheus/DCGM, artifact paths, and sanitization rules. Do not inspect or print secrets/local run state.", ["benchmark", "prometheus", "metrics"]),
        "scenario-d-heavy": ("Do a broad repo analysis/report using tools. Cover lifecycle, runtime, benchmarks, observability, safety boundaries, and recommended next tests. Do not inspect or print secrets/local run state.", ["vast", "llama", "benchmark"]),
        "scenario-d-normal": ("Small planning question: before Phase 3 agent scenarios, what should be checked and what should not be run? Use repo docs if needed. Do not inspect or print secrets/local run state.", ["phase", "agent"]),
    }
    rows = []
    rows.append(run_opencode("scenario-a", *prompts["scenario-a"], mode_dir, env, args.backend_url, args.prom_url))
    start = time.time()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_opencode, name, *prompts[name], mode_dir, env, args.backend_url, args.prom_url) for name in ("scenario-b-launch", "scenario-b-observability")]
        for fut in concurrent.futures.as_completed(futs):
            rows.append(fut.result())
    group_wall = round(time.time() - start, 3)
    for row in rows[-2:]:
        row["scenario_group_wall_s"] = group_wall
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_opencode, name, *prompts[name], mode_dir, env, args.backend_url, args.prom_url) for name in ("scenario-d-heavy", "scenario-d-normal")]
        for fut in concurrent.futures.as_completed(futs):
            rows.append(fut.result())
    group_wall = round(time.time() - start, 3)
    for row in rows[-2:]:
        row["scenario_group_wall_s"] = group_wall
    write_csv(mode_dir / "agent" / "scenarios.csv", rows)
    write_csv(mode_dir / "agent" / "request-metrics.csv", rows)
    md = [f"# OpenCode Agent Summary {args.mode}", "", "| scenario | pass | wall_s | note |", "|---|---:|---:|---|"]
    for row in rows:
        md.append(f"| `{row['scenario']}` | `{row['pass_fail']}` | `{row['wall_s']}` | {row['quality_note']} |")
    (mode_dir / "summary.sanitized.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
