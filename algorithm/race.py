from dataclasses import dataclass
import json
import os

from algorithm.node import Node
from algorithm.state import DataRace, ExecutionState

@dataclass
class SingleExecutionResult:
    races: list[DataRace]
    state: ExecutionState

@dataclass
class ProgramRaceSummary:
    num_executions: int
    num_executions_with_races: int
    total_races: int
    races: dict[str, list[DataRace]]

def detect_from_single_execution(filepath: str, pruning_strategy) -> SingleExecutionResult:
    """
    Takes a single execution JSON file and returns the detected races
    """
    
    with open(filepath, "r") as f:
        data = json.load(f)

    state = ExecutionState(pruning_strategy=pruning_strategy)

    events = sorted(data["events"], key=lambda x: x["event_id"])
    for event_data in events:
        node = Node(
            event_id=event_data["event_id"],
            thread=event_data["thread"],
            action=event_data["action"],
            memory_order=event_data["memory_order"],
            location=event_data["location"],
            value=event_data["value"],
            mo=event_data.get("mo"),
            rf=event_data.get("rf"),
            cv=event_data.get("cv"),
        )
        state.add_node(node)

    return SingleExecutionResult(races=state.races, state=state)

def detect_from_multiple_executions(execution_dir, pruning_strategy) -> ProgramRaceSummary:
    """
    Takes a directory containing execution_*.json files and returns a summary of detections
    """

    execution_files = sorted(
        f for f in os.listdir(execution_dir)
        if f.startswith("execution_") and f.endswith(".json") and not f.endswith("_graph.json")
    )

    total_races = 0
    executions_with_races = 0
    all_races = {}

    for filename in execution_files:
        filepath = os.path.join(execution_dir, filename)
        races = detect_from_single_execution(filepath, pruning_strategy).races
        if races:
            executions_with_races += 1
            total_races += len(races)
            all_races[filename] = races

    return ProgramRaceSummary(
        num_executions=len(execution_files),
        num_executions_with_races=executions_with_races,
        total_races=total_races,
        races=all_races
    )