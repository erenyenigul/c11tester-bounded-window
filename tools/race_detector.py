import os
import sys
import argparse
from algorithm.prune import AggressivePruningStrategy, ConservativePruningStrategy, NoPruningStrategy
from algorithm.race import detect_from_multiple_executions

def make_pruning_strategy(args):
    if args.pruning_mode == "conservative":
        return ConservativePruningStrategy(prune_interval=args.prune_interval)
    if args.pruning_mode == "aggressive":
        return AggressivePruningStrategy(args.window_size, prune_interval=args.prune_interval)
    return NoPruningStrategy()

def main():
    parser = argparse.ArgumentParser(description="Run C11 bounded-window race detection.")
    parser.add_argument("execution_dir", help="Directory containing execution_*.json files")
    parser.add_argument(
        "--pruning-mode",
        choices=["none", "conservative", "aggressive"],
        default="none",
        help="Execution graph pruning mode (default: none)",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=2000,
        help="Aggressive mode window size in events (default: 2000)",
    )
    parser.add_argument(
        "--prune-interval",
        type=int,
        default=16,
        help="Trigger pruning every N events (default: 16)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.execution_dir):
        print(f"Directory not found: {args.execution_dir}")
        sys.exit(1)

    summary = detect_from_multiple_executions(args.execution_dir, make_pruning_strategy(args))

    print("-"*50)
    print(f"Executions analysed : {summary.num_executions}")
    print(f"Executions with race: {summary.num_executions_with_races}")
    print(f"Total races found   : {summary.total_races}")

    if summary.races:
        print("\nProgram has a data race.")
        print("\nRaces:")
        for filename, races in summary.races.items():
            for race in races:
                print(f"  [{filename}] {race.a} <-> {race.b} at {race.location}")
    else:
        print(f"\nNo data races detected across all {summary.num_executions} executions.")

    print("\n" + "="*50)

if __name__ == "__main__":
    main()