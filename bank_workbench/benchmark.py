"""Reproducible synthetic streaming benchmark; deletes its temporary CSV."""

import argparse
import csv
import io
import json
import tempfile
import time
from pathlib import Path

from bank_workbench.bank_core import execute_pipeline
from bank_workbench.demo import demo_csv


def peak_process_mib():
    """Windows peak working set includes Python/pandas, not just traced objects."""
    import os

    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize",
                "WorkingSetSize",
                "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage",
                "PagefileUsage",
                "PeakPagefileUsage",
            )
        ]

    process = ctypes.windll.kernel32.GetCurrentProcess
    process.restype = wintypes.HANDLE
    get_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    info = Counters()
    info.cb = ctypes.sizeof(info)
    if not get_info(process(), ctypes.byref(info), info.cb):
        raise ctypes.WinError()
    return round(info.PeakWorkingSetSize / 1024**2, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=100000)
    parser.add_argument("--chunksize", type=int, default=5000)
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("rows must be positive")
    template = list(csv.reader(io.StringIO(demo_csv().decode("utf-8-sig"))))
    with tempfile.TemporaryDirectory(prefix="bank-benchmark-") as directory:
        source = Path(directory) / "synthetic.csv"
        # The generator never builds the full benchmark dataset in memory.
        with source.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(template[0])
            for index in range(args.rows):
                row = template[1 + index % (len(template) - 1)].copy()
                row[0] = str(index % 10**10)
                writer.writerow(row)
        started = time.perf_counter()
        report = execute_pipeline(source, chunksize=args.chunksize)
        elapsed = time.perf_counter() - started
        assert report.stats["rows"] == args.rows
        totals = report.questions[17]["summary"]
        assert totals["total_before"] == totals["total_after"]
        print(
            json.dumps(
                dict(
                    rows=args.rows,
                    chunksize=args.chunksize,
                    seconds=round(elapsed, 3),
                    rows_per_second=round(args.rows / elapsed),
                    peak_process_mib=peak_process_mib(),
                    balances_conserved=True,
                ),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
