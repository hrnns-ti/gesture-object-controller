import os
import time
import csv
import json
import psutil


class StatTimer:
    def __init__(self):
        self.samples = []

    def record(self, dt: float) -> None:
        self.samples.append(dt)

    def summary(self):
        if not self.samples:
            return None
        s = sorted(self.samples)
        n = len(s)
        total = sum(s)

        def p(q):
            idx = int(q * (n - 1))
            return s[idx]

        return {
            "count": n,
            "avg_sec": total / n,
            "min_sec": s[0],
            "max_sec": s[-1],
            "p50_sec": p(0.5),
            "p90_sec": p(0.9),
            "p99_sec": p(0.99),
        }


def run_benchmark(
    duration_sec: float = 60.0,
    interval_sec: float = 1.0,
    csv_path: str = "benchmark_stats.csv",
) -> None:
    """Run system-level benchmark for the current process.

    - Logs CPU% and RSS memory (MB) every `interval_sec` seconds.
    - At the end, writes a CSV file with per-sample stats and overall summary.
    """
    proc = psutil.Process(os.getpid())

    samples = []
    timer = StatTimer()

    t_start = time.perf_counter()
    t_prev = t_start

    # psutil.cpu_percent needs an initial call
    proc.cpu_percent(interval=None)

    while True:
        now = time.perf_counter()
        elapsed = now - t_start
        if elapsed >= duration_sec:
            break

        # sleep until next interval
        to_sleep = interval_sec - (now - t_prev)
        if to_sleep > 0:
            time.sleep(to_sleep)
        t_now = time.perf_counter()
        dt = t_now - t_prev
        t_prev = t_now

        cpu = proc.cpu_percent(interval=None)
        mem_mb = proc.memory_info().rss / (1024 * 1024)

        timer.record(dt)
        samples.append(
            {
                "time_sec": elapsed,
                "dt_sec": dt,
                "cpu_percent": cpu,
                "mem_mb": mem_mb,
            }
        )

    # compute summary for dt (interval stability)
    summ = timer.summary() or {}

    # write CSV
    fieldnames = ["time_sec", "dt_sec", "cpu_percent", "mem_mb"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in samples:
            writer.writerow(row)

    # write small JSON summary
    summary_path = os.path.splitext(csv_path)[0] + "_summary.json"
    with open(summary_path, "w") as f:
        json.dump(
            {
                "duration_sec": duration_sec,
                "interval_sec": interval_sec,
                "dt_stats": summ,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    # Example: run 60-second benchmark with 1-second interval
    run_benchmark(60.0, 1.0)
