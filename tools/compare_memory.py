#!/usr/bin/env python3

import os
import sys
import argparse
import tempfile
import time
import shutil
import memray

# Allow importing from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithm.prune import AggressivePruningStrategy, ConservativePruningStrategy, NoPruningStrategy
from algorithm.race import detect_from_multiple_executions

# Map strategy names to constructors
STRATEGIES = {
    "none":         lambda args: NoPruningStrategy(),
    "conservative": lambda args: ConservativePruningStrategy(prune_interval=args.prune_interval),
    "aggressive":   lambda args: AggressivePruningStrategy(args.window_size, prune_interval=args.prune_interval),
}

CSV_PATH = "report.csv"

# Fixed order for consistent output (CSV + terminal)
ORDER = ["none", "conservative", "aggressive"]


def peak_mb(bin_file):
    """
    Read memray output file and return peak memory usage in MiB.
    """
    with memray.FileReader(bin_file) as reader:
        return reader.metadata.peak_memory / (1024 * 1024)


def extract_race_ids(summary):
    """
    Convert a ProgramRaceSummary into a set of unique race identifiers.

    Each race is represented as a tuple of (event_id_a, event_id_b),
    allowing easy comparison between strategies.
    """
    ids = set()
    for races in summary.races.values():
        for r in races:
            ids.add((r.a.event_id, r.b.event_id))
    return ids


def run_strategy(factory, args, dirs, bin_file):
    """
    Run a single pruning strategy over all test case directories.

    Returns:
        peak memory (MiB),
        runtime (seconds),
        per-test-case summaries
    """
    start = time.perf_counter()

    summaries = {}

    # Track memory usage for the entire run
    with memray.Tracker(bin_file):
        for d in dirs:
            # Store summary PER TEST CASE (important for accuracy metrics)
            summaries[d] = detect_from_multiple_executions(d, factory(args))

    runtime = time.perf_counter() - start
    peak = peak_mb(bin_file)

    return peak, runtime, summaries


def has_executions(d):
    """
    Check if a directory contains execution_*.json files.
    """
    return any(f.startswith("execution_") and f.endswith(".json") for f in os.listdir(d))


def compute_metrics(results):
    """
    Compute macro-averaged precision and recall.

    For each test case:
        - Compare strategy results against baseline (no pruning)
        - Compute precision + recall

    Then average across all test cases.
    """
    metrics = {}

    # Baseline = ground truth (no pruning)
    baseline_summaries = results["none"][2]

    for strategy in ORDER:
        _, _, summaries = results[strategy]

        precisions = []
        recalls = []

        for case in summaries:
            # Ground truth races
            baseline_ids = extract_race_ids(baseline_summaries[case])

            # Races found by this strategy
            ids = extract_race_ids(summaries[case])

            # True positives = intersection
            tp = len(ids & baseline_ids)

            # Precision: how many reported races are correct
            precision = tp / len(ids) if ids else 1.0

            # Recall: how many real races were found
            recall = tp / len(baseline_ids) if baseline_ids else 1.0

            precisions.append(precision)
            recalls.append(recall)

        # Macro average across test cases
        avg_precision = sum(precisions) / len(precisions) if precisions else 1.0
        avg_recall = sum(recalls) / len(recalls) if recalls else 1.0

        metrics[strategy] = (avg_precision, avg_recall)

    return metrics


def append_csv(window_size, prune_interval, results, metrics):
    """
    Append a row to CSV containing:
    - memory usage
    - runtime
    - precision
    - recall
    for all strategies.
    """
    file_exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, "a") as f:
        # Write header once
        if not file_exists:
            f.write(
                "window_size,prune_interval,"
                "none_mib,conservative_mib,aggressive_mib,"
                "none_sec,conservative_sec,aggressive_sec,"
                "none_precision,conservative_precision,aggressive_precision,"
                "none_recall,conservative_recall,aggressive_recall\n"
            )

        # Extract values in fixed order
        peaks = [f"{results[n][0]:.3f}" for n in ORDER]
        times = [f"{results[n][1]:.3f}" for n in ORDER]
        precisions = [f"{metrics[n][0]:.3f}" for n in ORDER]
        recalls = [f"{metrics[n][1]:.3f}" for n in ORDER]

        # Combine into single CSV row
        row = ",".join(
            [str(window_size), str(prune_interval)] + peaks + times + precisions + recalls
        )
        f.write(row + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--all-cases", action="store_true")
    parser.add_argument("--window-size", type=int, default=200)
    parser.add_argument("--prune-interval", type=int, default=16)
    parser.add_argument("--keep-bins", action="store_true")
    parser.add_argument("--csv", action="store_true")
    args = parser.parse_args()

    # Validate input path
    if not os.path.isdir(args.path):
        print(f"Directory not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    # Determine which test case directories to run
    if args.all_cases:
        dirs = sorted(
            os.path.join(args.path, d)
            for d in os.listdir(args.path)
            if os.path.isdir(os.path.join(args.path, d)) and has_executions(os.path.join(args.path, d))
        )
        if not dirs:
            print(f"No execution subdirectories found under: {args.path}", file=sys.stderr)
            sys.exit(1)
    else:
        if not has_executions(args.path):
            print(f"No execution_*.json files found in: {args.path}", file=sys.stderr)
            sys.exit(1)
        dirs = [args.path]

    # Temporary directory for memray output
    tmpdir = tempfile.mkdtemp(prefix="memray_compare_")
    results = {}

    try:
        # Run all strategies
        for name, factory in STRATEGIES.items():
            bin_file = os.path.join(tmpdir, f"{name}.bin")
            print(f"[{name}] running...", end=" ", flush=True)

            peak, runtime, summaries = run_strategy(factory, args, dirs, bin_file)
            results[name] = (peak, runtime, summaries)

            print(f"{peak:.3f} MiB, {runtime:.3f}s")

        # Compute accuracy metrics
        metrics = compute_metrics(results)

        if args.csv:
            append_csv(args.window_size, args.prune_interval, results, metrics)
            print(f"\nAppended results to {CSV_PATH}")
        else:
            # Pretty terminal output
            print(f"\n{'Strategy':<15} {'Mem(MiB)':>10} {'Time(s)':>10} {'Prec':>8} {'Recall':>8}")
            print("-" * 60)

            for name in ORDER:
                peak, runtime, _ = results[name]
                precision, recall = metrics[name]

                print(f"{name:<15} {peak:>10.3f} {runtime:>10.3f} {precision:>8.3f} {recall:>8.3f}")

        # Optionally keep memray files for analysis
        if args.keep_bins:
            print(f"\nBin files: {tmpdir}/")
            for name in results:
                print(f"  memray flamegraph {tmpdir}/{name}.bin")
    finally:
        # Clean up temp files unless requested otherwise
        if not args.keep_bins:
            shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
