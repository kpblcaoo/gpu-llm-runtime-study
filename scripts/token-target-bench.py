#!/usr/bin/env python3
"""Token-accurate multi-target benchmark runner.

Combines /tokenize calibration with multi-target iteration, warmup/repeats,
parallel execution, and p50/p95 summaries for the Ada 6000 test plan matrix.
"""
import json
import os
import pathlib
import random
import subprocess
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


RUN_DIR = pathlib.Path("/tmp/vast-bench-token-target-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
RUN_DIR.mkdir(parents=True, exist_ok=True)
pathlib.Path("/tmp/vast-bench-token-target-latest").write_text(str(RUN_DIR))

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4001/v1")
MODEL = os.environ.get("MODEL", "Loopy")
PARALLEL = int(os.environ.get("PARALLEL", "3"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "64"))
TARGET_TOKENS = [int(t) for t in os.environ.get("TARGET_TOKENS", "1000 32000 95000").split()]
WARMUP = int(os.environ.get("WARMUP", "1"))
REPEATS = int(os.environ.get("REPEATS", "3"))
TOKENIZE_URL = os.environ.get("TOKENIZE_URL", "http://127.0.0.1:8001/tokenize")
SLEEP_BETWEEN = int(os.environ.get("SLEEP_BETWEEN", "10"))

API_KEY = os.environ.get("LITELLM_MASTER_KEY") or os.environ.get("OPEN_BUTTON_TOKEN")
if not API_KEY and os.path.exists("/proc/1/environ"):
    env_raw = open("/proc/1/environ", "rb").read()
    env_items = env_raw.split(b"\x00")
    values = dict(item.split(b"=", 1) for item in env_items if b"=" in item)
    API_KEY = (values.get(b"LITELLM_MASTER_KEY") or values.get(b"OPEN_BUTTON_TOKEN") or b"").decode()
if not API_KEY:
    raise SystemExit("missing LITELLM_MASTER_KEY/OPEN_BUTTON_TOKEN")

VOCAB = (
    "time person year way day thing man world life hand part child eye woman place work week case point "
    "government company number group problem fact good new first last long great little own other old right "
    "big high different small large next early young important public random vector matrix scalar token cache "
    "prompt decode prefill latency throughput memory clock power thermal slot queue request response compute "
    "kernel graph warp block tensor attention sample layer route server proxy"
).split()

TEMPLATE_OVERHEAD = 20
PROMPT_CACHE: dict[int, tuple[int, str]] = {}


def tokenize_count(text):
    data = json.dumps({"content": text}).encode()
    req = urllib.request.Request(TOKENIZE_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return len(json.loads(response.read())["tokens"])


def calibrate_prompt(target_tokens, seed):
    if target_tokens in PROMPT_CACHE:
        return PROMPT_CACHE[target_tokens]
    rng = random.Random(seed)
    words = [rng.choice(VOCAB) + str(rng.randrange(1000000)) for _ in range(90000)]
    prefix = "Read the random filler then answer with exactly: ok\n\nRANDOM_FILLER:\n"
    target_content = max(target_tokens - TEMPLATE_OVERHEAD, 1)
    lo, hi = 1, len(words)
    best_count, best_text = 0, prefix
    while lo <= hi:
        mid = (lo + hi) // 2
        text = prefix + " ".join(words[:mid])
        count = tokenize_count(text)
        if count <= target_content:
            best_count, best_text = count, text
            lo = mid + 1
        else:
            hi = mid - 1
    result = (best_count, best_text)
    PROMPT_CACHE[target_tokens] = result
    return result


def make_payload(target, run_idx):
    content_tokens, prompt = calibrate_prompt(target, seed=100000 + target)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
    }
    path = RUN_DIR / f"payload-{target}-{run_idx}.json"
    path.write_text(json.dumps(payload))
    return content_tokens, path


def run_one(target, run_idx, payload_path):
    body_path = RUN_DIR / f"body-{target}-{run_idx}.json"
    metrics_path = RUN_DIR / f"metrics-{target}-{run_idx}.txt"
    err_path = RUN_DIR / f"curl-{target}-{run_idx}.err"
    started = time.time()
    curl_w = (
        "http_code=%{http_code}\n"
        "time_total=%{time_total}\n"
        "time_starttransfer=%{time_starttransfer}\n"
        "size_download=%{size_download}\n"
    )
    cmd = [
        "curl", "-sS",
        "-o", str(body_path),
        "-w", curl_w,
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-d", "@" + str(payload_path),
        BASE_URL + "/chat/completions",
    ]
    with open(metrics_path, "w") as mf, open(err_path, "w") as ef:
        subprocess.run(cmd, stdout=mf, stderr=ef, check=False)
    ended = time.time()
    with open(metrics_path, "a") as mf:
        mf.write(f"started={started}\nended={ended}\nwall={ended - started:.3f}\n")
    return run_idx


def read_metrics(path):
    data = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k] = v
    return data


def percentile(data, p):
    if not data:
        return 0.0
    sorted_d = sorted(data)
    k = (len(sorted_d) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_d):
        return sorted_d[f]
    return sorted_d[f] + (k - f) * (sorted_d[c] - sorted_d[f])


def main():
    log_path = RUN_DIR / "progress.log"
    log_path.open("a").close()

    log_path.write_text(
        f"started={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"targets={TARGET_TOKENS}\n"
        f"parallel={PARALLEL}\n"
        f"warmup={WARMUP}\n"
        f"repeats={REPEATS}\n"
        f"max_tokens={MAX_TOKENS}\n"
        f"model={MODEL}\n"
        f"base_url={BASE_URL}\n"
        f"tokenize_url={TOKENIZE_URL}\n"
        f"sleep_between={SLEEP_BETWEEN}\n"
    )

    for target in TARGET_TOKENS:
        _, prompt = calibrate_prompt(target, seed=100000 + target)
        plines = (RUN_DIR / f"prompt-{target}.txt").open("w")
        plines.write(prompt[:2000] + "...\n")
        plines.close()

    target_stats = {}

    for target in TARGET_TOKENS:
        target_stats[target] = {"prefill_ms": [], "total_ms": [], "content_tokens": 0}
        content_tokens, payload_path = make_payload(target, 0)
        target_stats[target]["content_tokens"] = content_tokens
        log_path.write_text(
            (log_path.read_text()
             + f"\ncalibrated target={target} tokens={content_tokens} "
             f"(overhead={TEMPLATE_OVERHEAD})\n")
        )

    for target in TARGET_TOKENS:
        for w in range(WARMUP):
            _, payload_path = make_payload(target, 0)
            run_one(target, w, payload_path)
            log_path.write_text(
                (log_path.read_text() + f"warmup target={target} run={w}\n")
            )
            time.sleep(SLEEP_BETWEEN)

    for target in TARGET_TOKENS:
        for r in range(REPEATS):
            tasks = {}
            with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
                for slot in range(PARALLEL):
                    run_idx = r * PARALLEL + slot + WARMUP
                    content_tokens, payload_path = make_payload(target, run_idx)
                    future = pool.submit(run_one, target, run_idx, payload_path)
                    tasks[future] = run_idx
                for future in as_completed(tasks):
                    run_idx = tasks[future]
                    try:
                        future.result()
                        mp = RUN_DIR / f"metrics-{target}-{run_idx}.txt"
                        m = read_metrics(mp)
                        t_total = float(m.get("time_total", "0"))
                        t_starttransfer = float(m.get("time_starttransfer", "0"))
                        prefill_ms = (t_starttransfer * 1000)
                        total_ms = (t_total * 1000)
                        target_stats[target]["prefill_ms"].append(prefill_ms)
                        target_stats[target]["total_ms"].append(total_ms)
                        log_path.write_text(
                            (log_path.read_text() +
                             f"done target={target} run={run_idx} "
                             f"prefill_ms={prefill_ms:.1f} "
                             f"total_ms={total_ms:.1f}\n")
                        )
                    except Exception as e:
                        log_path.write_text(
                            (log_path.read_text()
                             + f"error target={target} run={run_idx} {e}\n")
                        )
            time.sleep(SLEEP_BETWEEN)

    summary_lines = []
    summary_lines.append("=" * 72)
    summary_lines.append("Token-Target Benchmark Summary")
    summary_lines.append(f"Run dir: {RUN_DIR}")
    summary_lines.append(f"Model: {MODEL}")
    summary_lines.append(f"Base URL: {BASE_URL}")
    summary_lines.append(f"Parallel: {PARALLEL}")
    summary_lines.append(f"Warmup: {WARMUP}")
    summary_lines.append(f"Repeats: {REPEATS}")
    summary_lines.append(f"Max tokens: {MAX_TOKENS}")
    summary_lines.append("=" * 72)
    summary_lines.append("")
    summary_lines.append(
        f"{'Target':>8} {'Actual':>8} {'Runs':>6} "
        f"{'p50_pre':>10} {'p95_pre':>10} "
        f"{'p50_tot':>10} {'p95_tot':>10}"
    )
    summary_lines.append("-" * 72)

    summary_data = {}
    for target in TARGET_TOKENS:
        st = target_stats[target]
        n = len(st["prefill_ms"])
        p50_pre = percentile(st["prefill_ms"], 50)
        p95_pre = percentile(st["prefill_ms"], 95)
        p50_tot = percentile(st["total_ms"], 50)
        p95_tot = percentile(st["total_ms"], 95)
        line = (
            f"{target:>8} {st['content_tokens']:>8} {n:>6} "
            f"{p50_pre:>10.1f} {p95_pre:>10.1f} "
            f"{p50_tot:>10.1f} {p95_tot:>10.1f}"
        )
        summary_lines.append(line)
        summary_data[target] = {
            "actual_tokens": st["content_tokens"],
            "runs": n,
            "p50_prefill_ms": round(p50_pre, 1),
            "p95_prefill_ms": round(p95_pre, 1),
            "p50_total_ms": round(p50_tot, 1),
            "p95_total_ms": round(p95_tot, 1),
        }

    summary_lines.append("")
    summary_lines.append("=" * 72)
    summary_lines.append("Per-Target Runs")
    summary_lines.append("=" * 72)
    for target in TARGET_TOKENS:
        st = target_stats[target]
        summary_lines.append(f"\nTarget: {target} (actual: {st['content_tokens']})")
        for i in range(len(st["prefill_ms"])):
            run_idx = i + WARMUP
            summary_lines.append(
                f"  Run {run_idx}: prefill={st['prefill_ms'][i]:.1f}ms  "
                f"total={st['total_ms'][i]:.1f}ms"
            )

    summary_txt = "\n".join(summary_lines) + "\n"
    (RUN_DIR / "summary.txt").write_text(summary_txt)
    (RUN_DIR / "summary.json").write_text(json.dumps(summary_data, indent=2) + "\n")

    (RUN_DIR / "meta.txt").write_text(
        f"run_dir={RUN_DIR}\n"
        f"model={MODEL}\n"
        f"base_url={BASE_URL}\n"
        f"tokenize_url={TOKENIZE_URL}\n"
        f"parallel={PARALLEL}\n"
        f"max_tokens={MAX_TOKENS}\n"
        f"targets={TARGET_TOKENS}\n"
        f"warmup={WARMUP}\n"
        f"repeats={REPEATS}\n"
        f"template_overhead={TEMPLATE_OVERHEAD}\n"
        f"ended={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
    )

    print(summary_txt)


if __name__ == "__main__":
    main()
