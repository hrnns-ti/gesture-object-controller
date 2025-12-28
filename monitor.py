import os
import time
import csv
import threading
import psutil


class SystemMonitor:
    def __init__(
        self,
        interval_sec: float = 1.0,
        csv_path: str = "system_benchmark.csv",
    ):
        self.interval_sec = interval_sec
        self.csv_path = csv_path
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _run(self):
        proc = psutil.Process(os.getpid())
        fieldnames = [
            "time_sec",
            "cpu_total_percent",
            "cpu_proc_percent",
            "mem_total_percent",
            "mem_proc_mb",
        ]

        t0 = time.perf_counter()

        # warm up cpu_percent
        psutil.cpu_percent(interval=None)
        proc.cpu_percent(interval=None)

        with open(self.csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            while not self._stop.is_set():
                now = time.perf_counter()
                elapsed = now - t0

                cpu_total = psutil.cpu_percent(interval=None)  # semua core
                cpu_proc = proc.cpu_percent(interval=None)      # proses ini
                mem = psutil.virtual_memory()
                mem_total = mem.percent
                mem_proc_mb = proc.memory_info().rss / (1024 * 1024)

                writer.writerow(
                    {
                        "time_sec": elapsed,
                        "cpu_total_percent": cpu_total,
                        "cpu_proc_percent": cpu_proc,
                        "mem_total_percent": mem_total,
                        "mem_proc_mb": mem_proc_mb,
                    }
                )

                # flush supaya aman kalau crash
                f.flush()

                # tidur sampai sampling berikutnya
                time.sleep(self.interval_sec)
