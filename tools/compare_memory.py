#!/usr/bin/env python3
# Usage:
#   python tools/compare_memory.py data/test_cases/race06_three_thread
#   python tools/compare_memory.py data/test_cases --all-cases [--keep-bins]

import os
import sys
import argparse
import tempfile
import shutil
import memray

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithm.prune import AggressivePruningStrategy, ConservativePruningStrategy, NoPruningStrategy
from algorithm.race import detect_from_multiple_executions

STRATEGIES = {
    "none":         lambda args: NoPruningStrategy(),
    "conservative": lambda args: ConservativePruningStrategy(prune_interval=args.prune_interval),
    "aggressive":   lambda args: AggressivePruningStrategy(args.window_size, prune_interval=args.prune_interval),
}

def peak_mb(bin_file):
    with memray.FileReader(bin_file) as reader:
        return reader.metadata.peak_memory / (1024 * 1024)

def run_strategy(factory, args, dirs, bin_file):
    with memray.Tracker(bin_file):
        for d in dirs:
            detect_from_multiple_executions(d, factory(args))
    return peak_mb(bin_file)

def has_executions(d):
    return any(f.startswith("execution_") and f.endswith(".json") for f in os.listdir(d))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--all-cases", action="store_true")
    parser.add_argument("--window-size",    type=int, default=300)
    parser.add_argument("--prune-interval", type=int, default=16)
    parser.add_argument("--keep-bins",      action="store_true")
    parser.add_argument("--csv",            action="store_true", help="Print results as a CSV row (no header)")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"Directory not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if args.all_cases:
        dirs = sorted(
            os.path.join(args.path, d) for d in os.listdir(args.path)
            if os.path.isdir(os.path.join(args.path, d)) and has_executions(os.path.join(args.path, d))
        )
        if not dirs:
            print(f"No execution subdirectories found under: {args.path}", file=sys.stderr)
            sys.exit(1)
        print(f"Running on {len(dirs)} test cases (window={args.window_size}, interval={args.prune_interval})\n")
    else:
        if not has_executions(args.path):
            print(f"No execution_*.json files found in: {args.path}", file=sys.stderr)
            sys.exit(1)
        dirs = [args.path]
        print(f"Running on: {args.path} (window={args.window_size}, interval={args.prune_interval})\n")

    tmpdir = tempfile.mkdtemp(prefix="memray_compare_")
    results = {}

    for name, factory in STRATEGIES.items():
        bin_file = os.path.join(tmpdir, f"{name}.bin")
        print(f"  [{name}] running...", end=" ", flush=True)
        peak = run_strategy(factory, args, dirs, bin_file)
        results[name] = (peak, bin_file)
        print(f"{peak:.3f} MiB")

    baseline = results["none"][0]
    if args.csv:
        peaks = [f"{results[n][0]:.3f}" for n in STRATEGIES]
        print(",".join([str(args.window_size)] + peaks))
    else:
        print(f"\n{'Strategy':<15} {'Peak (MiB)':>12} {'vs none':>10}")
        print("-" * 40)
        for name, (peak, _) in results.items():
            pct = (peak - baseline) / baseline * 100 if baseline > 0 else 0
            sign = "+" if pct >= 0 else ""
            print(f"{name:<15} {peak:>12.3f} {sign}{pct:.1f}%")

    if args.keep_bins:
        print(f"\nBin files: {tmpdir}/")
        for name in results:
            print(f"  memray flamegraph {tmpdir}/{name}.bin")
    else:
        shutil.rmtree(tmpdir)

if __name__ == "__main__":
    main()
