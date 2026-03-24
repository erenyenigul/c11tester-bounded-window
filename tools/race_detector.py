import json
import os
import sys
import argparse
from algorithm.node import Node
from algorithm.prune import AggressivePruningStrategy, ConservativePruningStrategy, NoPruningStrategy
from algorithm.state import ExecutionState

# main function to run the race detector on a given trace file
def main():
    parser = argparse.ArgumentParser(description="Run C11 bounded-window race detection.")
    parser.add_argument("json_file", help="Path to parsed execution JSON file")
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
        help="Aggressive mode target trace window size in events (default: 2000)",
    )
    parser.add_argument(
        "--prune-interval",
        type=int,
        default=64,
        help="Trigger pruning every N processed events (default: 64)",
    )
    args = parser.parse_args()

    filepath = args.json_file
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        data = json.load(f)
    
    pruning_strategy = NoPruningStrategy()

    if args.pruning_mode == "conservative":
        pruning_strategy = ConservativePruningStrategy()
    elif args.pruning_mode == "aggressive":
        pruning_strategy = AggressivePruningStrategy(args.window_size)

    state = ExecutionState(
        pruning_strategy=pruning_strategy
    )
    # we sort events by event_id to ensure we process them in trace order
    events = sorted(data['events'], key=lambda x: x['event_id'])
    
    for event_data in events:
        node = Node(
            event_id=event_data['event_id'],
            thread=event_data['thread'],
            action=event_data['action'],
            memory_order=event_data['memory_order'],
            location=event_data['location'],
            value=event_data['value'],
            rf=event_data.get('rf'),
            cv=event_data.get('cv')
        )
        state.add_node(node)

    state.report()

if __name__ == "__main__":
    main()
