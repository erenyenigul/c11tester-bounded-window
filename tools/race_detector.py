import json
import os
import sys
from algorithm.node import Node
from algorithm.state import ExecutionState

# main function to run the race detector on a given trace file
def main():
    if len(sys.argv) < 2:
        print("Usage: python race_detector.py <json_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        data = json.load(f)
    
    state = ExecutionState()
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
