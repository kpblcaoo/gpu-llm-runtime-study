#!/usr/bin/env python3
import argparse
import concurrent.futures
import csv
import json
import math
import os
import re
import shlex
import signal
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


BACKEND = "http://127.0.0.1:8001"
LITELLM = "http://127.0.0.1:4001/v1"
PROM = "http://127.0.0.1:9090"
MODEL = "Loopy"


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sanitize(text):
    text = re.sub(r"https?://[^\s'\"]+", "https://example.local", text or "")
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<TOKEN>", text)
    text = re.sub(r"(?i)(api[_-]?key|token|secret|password|master[_-]?key)(=|:)[^\s'\"]+", r"\1\2<SECRET>", text)
    return text


def proc_cmdline(pid):
    data = Path(f"/proc/{pid}/cmdline").read_bytes()
    return [x.decode("utf-8", "replace") for x in data.split(b"\0") if x]


def proc_environ(pid):
    out = {}
    try:
        data = Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return out
    for item in data.split(b"\0"):
        if item and b"=" in item:
            k, v = item.split(b"=", 1)
            out[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
    return out


def find_pid(name):
    pids = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            cmd = proc_cmdline(p.name)
        except OSError:
            continue
        if cmd and Path(cmd[0]).name == name:
            pids.append(int(p.name))
    if not pids:
        raise RuntimeError(f"no process found: {name}")
    return sorted(pids)[0]


def http_json(url, data=None, headers=None, timeout=30):
    body = json.dumps(data).encode() if data is not None else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def http_text(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def headers():
    key = ""
    try:
        key = proc_environ(find_pid("litellm")).get("LITELLM_MASTER_KEY", "")
    except Exception:
        pass
    if not key:
        for p in [Path("/run/vast-runtime/litellm-metrics-token"), *sorted(Path("/runs").glob("*/litellm-metrics-token"), key=lambda x: x.stat().st_mtime, reverse=True)]:
            if p.exists():
                key = p.read_text(encoding="utf-8").strip()
                if key:
                    break
    return {"Authorization": f"Bearer {key}"} if key else {}


def set_arg(args, flag, value):
    args = list(args)
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            args[i + 1] = value
        else:
            args.append(value)
    else:
        args.extend([flag, value])
    return args


def mode_command(ctx):
    args = proc_cmdline(find_pid("llama-server"))
    for flag, value in (
        ("--ctx-size", str(ctx)),
        ("--parallel", "2"),
        ("--cache-type-k", "q8_0"),
        ("--cache-type-v", "q8_0"),
        ("--flash-attn", "on"),
        ("--port", "8001"),
    ):
        args = set_arg(args, flag, value)
    return args


def terminate(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
        except ProcessLookupError:
            return
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def start_llama(args, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "ab", buffering=0)
    return subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def wait_backend(timeout=420):
    last = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, data = http_json(f"{BACKEND}/v1/models", timeout=10)
            if code == 200:
                return data
        except Exception as exc:
            last = exc
            time.sleep(3)
    raise RuntimeError(f"backend not ready: {last}")


def smoke(h):
    payload = {"model": MODEL, "messages": [{"role": "user", "content": "Say OK."}], "max_tokens": 16, "temperature": 0}
    return http_json(f"{LITELLM}/chat/completions", payload, h, timeout=90)


def observed_nctx(slots):
    if isinstance(slots, list):
        return [x.get("n_ctx") for x in slots if isinstance(x, dict) and "n_ctx" in x]
    return []


def slots_idle(slots):
    if not isinstance(slots, list):
        return False
    return all(not x.get("is_processing", x.get("processing", False)) for x in slots if isinstance(x, dict))


def prom_targets():
    code, data = http_json(f"{PROM}/api/v1/targets", timeout=30)
    names = []
    for t in data.get("data", {}).get("activeTargets", []):
        job = t.get("labels", {}).get("job")
        if job:
            names.append(job)
    return sorted(set(names))


def percentile(vals, pct):
    vals = sorted(v for v in vals if v is not None and not math.isnan(v))
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * pct / 100.0
    f, c = math.floor(k), math.ceil(k)
    return vals[f] if f == c else vals[f] * (c - k) + vals[c] * (k - f)


def prom_range(path, start, end):
    queries = {
        "vram_used": "DCGM_FI_DEV_FB_USED",
        "gpu_util": "DCGM_FI_DEV_GPU_UTIL",
        "power": "DCGM_FI_DEV_POWER_USAGE",
        "temperature": "DCGM_FI_DEV_GPU_TEMP",
    }
    summary = {}
    path.mkdir(parents=True, exist_ok=True)
    for name, query in queries.items():
        url = f"{PROM}/api/v1/query_range?query={urllib.parse.quote(query)}&start={start:.3f}&end={end:.3f}&step=5"
        try:
            _, text = http_text(url, timeout=60)
            (path / f"{name}.query_range.json").write_text(text, encoding="utf-8")
            data = json.loads(text)
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
    write_json(path / "summary.json", summary)
    return summary


def corpus_files(root):
    picks = []
    allow = {".md", ".sh", ".py", ".conf", ".csv", ".toml"}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in allow and len(picks) < 80:
            rel = p.relative_to(root).as_posix()
            if any(part in rel.split("/") for part in (".git", "runs", ".venv")):
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")[:10000]
            except Exception:
                continue
            picks.append((rel, txt))
    return picks


def build_context(root, keywords=None, limit=18):
    files = corpus_files(root)
    if keywords:
        ranked = []
        for rel, txt in files:
            score = sum((rel.lower() + "\n" + txt.lower()).count(k) for k in keywords)
            if score:
                ranked.append((score, rel, txt))
        files = [(rel, txt) for _, rel, txt in sorted(ranked, reverse=True)] or files
    chunks = []
    for rel, txt in files[:limit]:
        chunks.append(f"### {rel}\n```\n{txt[:6000]}\n```")
    return "\n\n".join(chunks), min(len(files), limit)


def stream_chat(prompt, h, log_path, max_tokens=900):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a careful repo-analysis agent. Do not request or print secrets. Be concise and factual."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req_headers = dict(h)
    req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{LITELLM}/chat/completions", data=json.dumps(payload).encode(), headers=req_headers)
    start = time.monotonic()
    first_data = None
    first_content = None
    out = []
    usage = {}
    status = 0
    error = ""
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            status = resp.status
            for raw in resp:
                now = time.monotonic()
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                if first_data is None:
                    first_data = now
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if obj.get("usage"):
                    usage = obj["usage"]
                for choice in obj.get("choices", []):
                    delta = choice.get("delta") or {}
                    content = delta.get("content") or delta.get("reasoning_content") or ""
                    if content:
                        if first_content is None:
                            first_content = now
                        out.append(content)
    except Exception as exc:
        error = str(exc)
    end = time.monotonic()
    text = "".join(out)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(log_path, {"sanitized_text": sanitize(text), "usage": usage, "error": sanitize(error), "status": status})
    wall = end - start
    ttft = (first_content or first_data or end) - start
    return {"http_code": status, "wall_s": wall, "ttft_s": ttft, "usage": usage, "error": sanitize(error), "text": text}


def run_agent(name, task, root, mode_dir, h):
    start_utc = utc()
    start_epoch = time.time()
    _, before = http_json(f"{BACKEND}/slots", timeout=30)
    keywords = task["keywords"]
    context, tool_calls = build_context(root, keywords=keywords, limit=task.get("limit", 18))
    prompt = task["prompt"] + "\n\nRepo excerpts:\n" + context
    result = stream_chat(prompt, h, mode_dir / "logs" / f"{name}.raw.sanitized.json", max_tokens=task.get("max_tokens", 900))
    _, after = http_json(f"{BACKEND}/slots", timeout=30)
    end_epoch = time.time()
    prom = prom_range(mode_dir / "metrics" / "prometheus" / name, start_epoch, end_epoch)
    text = result["text"].lower()
    passed = result["http_code"] == 200 and not result["error"] and all(s in text for s in task["must_contain"])
    note = "pass" if passed else "manual review needed or missing expected terms"
    usage = result["usage"] or {}
    row = {
        "scenario": name,
        "start_utc": start_utc,
        "end_utc": utc(),
        "wall_s": round(end_epoch - start_epoch, 3),
        "model_request_count": 1,
        "input_tokens": usage.get("prompt_tokens") or usage.get("input_tokens") or "",
        "output_tokens": usage.get("completion_tokens") or usage.get("output_tokens") or "",
        "reasoning_tokens": usage.get("reasoning_tokens") or "",
        "tool_calls": tool_calls,
        "failed_tool_calls": 0,
        "request_latency_p50_s": round(result["wall_s"], 3),
        "request_latency_p95_s": round(result["wall_s"], 3),
        "streaming_ttft_p50_s": round(result["ttft_s"], 6),
        "streaming_ttft_p95_s": round(result["ttft_s"], 6),
        "pass_fail": "pass" if passed else "fail",
        "quality_note": note,
        "vram_max_mib": prom.get("vram_used", {}).get("max", ""),
        "vram_p95_mib": prom.get("vram_used", {}).get("p95", ""),
        "gpu_util_avg": prom.get("gpu_util", {}).get("avg", ""),
        "gpu_util_p95": prom.get("gpu_util", {}).get("p95", ""),
        "power_avg_w": prom.get("power", {}).get("avg", ""),
        "power_p95_w": prom.get("power", {}).get("p95", ""),
        "temp_max_c": prom.get("temperature", {}).get("max", ""),
        "temp_p95_c": prom.get("temperature", {}).get("p95", ""),
    }
    write_json(mode_dir / "agent" / f"{name}-slots-before.json", before)
    write_json(mode_dir / "agent" / f"{name}-slots-after.json", after)
    (mode_dir / "agent" / f"{name}.summary.sanitized.md").write_text(sanitize(result["text"])[:12000] + "\n", encoding="utf-8")
    return row


def append_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


TASKS = {
    "scenario-a": {
        "keywords": ["vast", "llama", "benchmark", "runtime", "harness"],
        "must_contain": ["vast", "runtime", "benchmark"],
        "prompt": "Scenario A: Explore the repository excerpts and produce a concise operational summary. Identify Vast lifecycle scripts, the custom llama runtime path, benchmark/run-harness assets, and explicitly state that secrets/local runs should not be inspected or printed.",
    },
    "scenario-b-launch": {
        "keywords": ["launch", "runtime", "vast", "llama"],
        "must_contain": ["launch", "runtime", "llama"],
        "prompt": "Scenario B task 1: Summarize the Vast launch and llama runtime workflow from the repository excerpts. Include safety boundaries.",
    },
    "scenario-b-observability": {
        "keywords": ["benchmark", "prometheus", "dcgm", "observability", "metrics"],
        "must_contain": ["benchmark", "prometheus", "metrics"],
        "prompt": "Scenario B task 2: Summarize the benchmark and observability workflow from the repository excerpts. Include artifact locations and Prometheus/DCGM usage.",
    },
    "scenario-d-heavy": {
        "keywords": ["vast", "llama", "benchmark", "prometheus", "runtime", "agent", "q6"],
        "must_contain": ["vast", "llama", "benchmark"],
        "limit": 35,
        "max_tokens": 1200,
        "prompt": "Scenario D heavy task: Do broad repo analysis and produce a practical operations report. Cover lifecycle, runtime, benchmarking, observability, safety rules, and likely next tests. Keep it concise but complete.",
    },
    "scenario-d-normal": {
        "keywords": ["runbook", "agent", "phase 3"],
        "must_contain": ["phase", "agent"],
        "max_tokens": 500,
        "prompt": "Scenario D normal task: Answer this small planning question while the heavy task may be running: what should be checked before running Phase 3 agent scenarios?",
    },
}


def run_scenarios(run_dir, mode):
    mode_dir = run_dir / f"mode-{mode}"
    root = run_dir / "repo-corpus"
    h = headers()
    rows = []
    rows.append(run_agent("scenario-a", TASKS["scenario-a"], root, mode_dir, h))
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_agent, n, TASKS[n], root, mode_dir, h) for n in ("scenario-b-launch", "scenario-b-observability")]
        for fut in concurrent.futures.as_completed(futs):
            row = fut.result(); row["scenario_group_wall_s"] = round(time.time() - start, 3); rows.append(row)
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_agent, n, TASKS[n], root, mode_dir, h) for n in ("scenario-d-heavy", "scenario-d-normal")]
        for fut in concurrent.futures.as_completed(futs):
            row = fut.result(); row["scenario_group_wall_s"] = round(time.time() - start, 3); rows.append(row)
    fields = ["scenario", "start_utc", "end_utc", "wall_s", "scenario_group_wall_s", "model_request_count", "input_tokens", "output_tokens", "reasoning_tokens", "tool_calls", "failed_tool_calls", "request_latency_p50_s", "request_latency_p95_s", "streaming_ttft_p50_s", "streaming_ttft_p95_s", "pass_fail", "quality_note", "vram_max_mib", "vram_p95_mib", "gpu_util_avg", "gpu_util_p95", "power_avg_w", "power_p95_w", "temp_max_c", "temp_p95_c"]
    append_csv(mode_dir / "agent" / "scenarios.csv", rows, fields)
    append_csv(mode_dir / "agent" / "request-metrics.csv", rows, fields)
    md = [f"# Phase 3 Agent Summary {mode}", "", "| scenario | pass | wall_s | ttft_s | note |", "|---|---:|---:|---:|---|"]
    for r in rows:
        md.append(f"| `{r['scenario']}` | `{r['pass_fail']}` | `{r['wall_s']}` | `{r['streaming_ttft_p50_s']}` | {r['quality_note']} |")
    (mode_dir / "summary.sanitized.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rows


def capture_pre(run_dir):
    cfg = run_dir / "configs"
    cfg.mkdir(parents=True, exist_ok=True)
    pid = find_pid("llama-server")
    cmd = proc_cmdline(pid)
    (cfg / "current-524k-command.sanitized.txt").write_text(sanitize(shlex.join(cmd)) + "\n", encoding="utf-8")
    _, props = http_json(f"{BACKEND}/props", timeout=30)
    _, slots = http_json(f"{BACKEND}/slots", timeout=30)
    write_json(cfg / "current-props.sanitized.json", props)
    write_json(cfg / "current-slots.sanitized.json", slots)
    targets = prom_targets()
    write_json(cfg / "prometheus-targets.sanitized.json", {"active_jobs": targets})
    write_json(run_dir / "status.json", {"run_id": run_dir.name, "started_at": utc(), "active_backend_n_ctx": observed_nctx(slots), "slots_idle": slots_idle(slots), "prometheus_targets": targets})


def switch_and_verify(run_dir, mode, ctx):
    mode_dir = run_dir / f"mode-{mode}"
    mode_dir.mkdir(parents=True, exist_ok=True)
    repl = mode_command(ctx)
    (mode_dir / "backend-command.sanitized.txt").write_text(sanitize(shlex.join(repl)) + "\n", encoding="utf-8")
    old = find_pid("llama-server")
    terminate(old)
    proc = start_llama(repl, mode_dir / "logs" / f"backend-{mode}.log")
    (mode_dir / "logs" / f"backend-{mode}.pid").write_text(str(proc.pid) + "\n", encoding="utf-8")
    wait_backend()
    h = headers()
    props_code, props = http_json(f"{BACKEND}/props", timeout=30)
    slots_code, slots = http_json(f"{BACKEND}/slots", timeout=30)
    models_code, models = http_json(f"{LITELLM}/models", headers=h, timeout=30)
    smoke_code, smoke_data = smoke(h)
    write_json(mode_dir / "props.sanitized.json", props)
    write_json(mode_dir / "slots-before.json", slots)
    status = {
        "mode": mode,
        "ctx_size": ctx,
        "parallel": 2,
        "props_http": props_code,
        "slots_http": slots_code,
        "litellm_models_http": models_code,
        "smoke_http": smoke_code,
        "observed_n_ctx": observed_nctx(slots),
        "verified_at": utc(),
    }
    write_json(mode_dir / "status.json", status)
    write_json(mode_dir / "logs" / "litellm-models.sanitized.json", models)
    write_json(mode_dir / "logs" / "smoke.sanitized.json", smoke_data)
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--mode", choices=["200k", "400k"])
    ap.add_argument("--ctx", type=int)
    ap.add_argument("--switch-only", action="store_true")
    args = ap.parse_args()
    run_dir = Path("/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.precheck:
        capture_pre(run_dir)
        return
    if not args.mode or not args.ctx:
        raise SystemExit("--mode and --ctx required unless --precheck")
    status = switch_and_verify(run_dir, args.mode, args.ctx)
    print(json.dumps({"mode": args.mode, "observed_n_ctx": status.get("observed_n_ctx")}), flush=True)
    if args.switch_only:
        return
    run_scenarios(run_dir, args.mode)


if __name__ == "__main__":
    main()
