"""
benchmarks/bench_load.py

HTTP load test against the live /scout/chat endpoint.

Fires `--requests` total HTTP requests spread across `--concurrency` threads
and reports throughput, latency percentiles, and error rate.

Usage — against local server:
    python -m benchmarks.bench_load

Usage — against EC2:
    python -m benchmarks.bench_load --url http://<EC2-IP>:5000 --concurrency 10 --requests 100

Flags:
    --url           Base URL of the running Flask server (default: http://localhost:5000)
    --concurrency   Number of parallel threads (default: 5)
    --requests      Total number of requests to fire (default: 50)
    --timeout       Per-request timeout in seconds (default: 60)
"""

import sys
import os
import time
import threading
import statistics
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from benchmarks.ground_truth import GROUND_TRUTH

QUERIES = [item["query"] for item in GROUND_TRUTH]


def _worker(
    url: str,
    query_batch: list[str],
    results: list[float],
    errors: list,
    lock: threading.Lock,
    timeout: int,
):
    for q in query_batch:
        t0 = time.perf_counter()
        try:
            resp = requests.post(
                f"{url}/scout/chat",
                json={"question": q, "history": []},
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            with lock:
                if resp.status_code == 200:
                    results.append(elapsed_ms)
                else:
                    errors.append(f"HTTP {resp.status_code}")
        except Exception as exc:
            with lock:
                errors.append(str(exc))


def run(url: str, concurrency: int, total_requests: int, timeout: int):
    # Distribute queries across threads
    batches: list[list[str]] = [[] for _ in range(concurrency)]
    for i in range(total_requests):
        batches[i % concurrency].append(QUERIES[i % len(QUERIES)])

    results: list[float] = []
    errors:  list        = []
    lock = threading.Lock()

    print(f"\nLoad test")
    print(f"  Target:       {url}/scout/chat")
    print(f"  Requests:     {total_requests}")
    print(f"  Concurrency:  {concurrency} threads")
    print(f"  Timeout:      {timeout}s per request\n")

    threads = [
        threading.Thread(
            target=_worker,
            args=(url, batches[i], results, errors, lock, timeout),
        )
        for i in range(concurrency)
    ]

    t_start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed_total = time.perf_counter() - t_start

    n = len(results)
    if n == 0:
        print("  No successful requests — check that the server is running.")
        if errors:
            print(f"  Errors: {errors[:5]}")
        return

    s = sorted(results)

    def pct(p):
        idx = max(0, int(p / 100 * n) - 1)
        return s[idx]

    print("┌──────────────────────────────────────┐")
    print(f"│  Total wall time     {elapsed_total:>8.2f}s         │")
    print(f"│  Throughput          {n / elapsed_total:>8.2f} req/s     │")
    print(f"│  Successful          {n:>5} / {total_requests:<5}          │")
    print(f"│  Errors              {len(errors):>8}              │")
    print(f"│  Avg latency         {statistics.mean(results):>8.0f}ms         │")
    print(f"│  p50                 {pct(50):>8.0f}ms         │")
    print(f"│  p95                 {pct(95):>8.0f}ms         │")
    print(f"│  p99                 {pct(99):>8.0f}ms         │")
    print(f"│  Min                 {min(results):>8.0f}ms         │")
    print(f"│  Max                 {max(results):>8.0f}ms         │")
    print("└──────────────────────────────────────┘")

    if errors:
        print(f"\n  Error samples: {errors[:5]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test for /scout/chat")
    parser.add_argument("--url",         default="http://localhost:5000")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--requests",    type=int, default=50)
    parser.add_argument("--timeout",     type=int, default=60)
    args = parser.parse_args()

    run(
        url=args.url,
        concurrency=args.concurrency,
        total_requests=args.requests,
        timeout=args.timeout,
    )
