import json
import re
import os
import sys
from enum import Enum

# All possible memory orders in C11, according to the paper's Section 2
class MemoryOrder(str, Enum):
    RELAXED = "relaxed"
    ACQUIRE = "acquire"
    RELEASE = "release"
    ACQ_REL = "acq_rel"
    SEQ_CST = "seq_cst"
    CONSUME = "consume" # Note: Section 2 claims that consume is not supported by C11Tester, but I will include it for completeness
MO_VALUES = {mo.value for mo in MemoryOrder}

def split_executions(text):
    parts = re.split(r'Execution trace \d+:', text)
    return parts[1:]

def parse_trace(trace_text, exec_id):
    events = []

    # Initial synthetic event
    events.append({
        "event_id": 0,
        "thread": 0,
        "action": "initial write",
        "memory_order": "relaxed",
        "location": "initial",
        "value": "0",
        "mo": None,
        "rf": None,
        "cv": [0]
    })

    lines = trace_text.splitlines()

    for line in lines:
        line = line.strip()
        copy_line = line
        
        # Skip all lines until I hit the first event and end parsing when I hit the "HASH" line
        if not line or line.startswith('-') or line.startswith('#'):
            continue
        if line.startswith("HASH"):
            break

        try:
            # 1. Extract CV (LAST parentheses) and remove it from line
            cv_match = re.search(r'\(([^()]*)\)\s*$', line)
            if not cv_match:
                continue

            cv_raw = cv_match.group(1)
            cv = [int(x.strip()) for x in cv_raw.split(',') if x.strip()]

            line = line[:cv_match.start()].strip()

            # 2. Extract mo_index (the only parenthesized element left, if it exists) 
            mo = None
            mo_match = re.search(r'\(([^()]*)\)', line)
            if mo_match:
                mo_str = mo_match.group(1).strip()
                # mo_index is a hexadecimal number, but I will store it as an integer (for easier use as an index later)
                try:
                    mo = int(mo_str, 16)
                except ValueError:
                    mo = int(mo_str)
                line = line[:mo_match.start()] + line[mo_match.end():]
                line = line.strip()

            # 3. Parse event_id and thread_id (always the first two numbers in the line)
            parts = line.split()
            event_id = int(parts[0])
            thread = int(parts[1])

            # 4. Parse action which can be multiple words, so keep consuming parts until we hit a memory order keyword
            action_parts = []
            i = 2
            while i < len(parts) and parts[i] not in MO_VALUES:
                action_parts.append(parts[i])
                i += 1

            action = " ".join(action_parts)
            try:
                memory_order = MemoryOrder(parts[i])
            except ValueError:
                raise ValueError(f"Unknown memory order: {parts[i]}")
            i += 1

            # 5. Once we hit the memory order, the next two parts are always the location and value
            location = parts[i]
            value = parts[i + 1]
            parts = parts[i + 2:]

            # 6. Extract rf (the last number in the line now, if it exists)
            rf = None
            if parts and parts[0].isdigit():
                rf = int(parts[0])

            event = {
                "event_id": event_id,
                "thread": thread,
                "action": action,
                "memory_order": memory_order.value,
                "location": location,
                "value": value,
                "mo": mo,
                "rf": rf,
                "cv": cv
            }

            events.append(event)

        except Exception as e:
            print(f"Skipping line due to error: {copy_line}. Reason: {e}")
            continue

    return {
        "execution_id": exec_id,
        "events": events
    }


def parse_file(filepath, output_dir):
    with open(filepath, "r") as f:
        text = f.read()

    execution_texts = split_executions(text)
    os.makedirs(output_dir, exist_ok=True)

    for i, exec_text in enumerate(execution_texts, start=1):
        parsed = parse_trace(exec_text, i)
        output_file = os.path.join(output_dir, f"execution_{i}.json")
        with open(output_file, "w") as f:
            json.dump(parsed, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Please pass the absolute path of the input file and output directory as parameters")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    if os.path.exists(input_file):
        parse_file(input_file, output_dir)
    else:
        print(f"Error: {input_file} not found in {output_dir}")

    print(f"Finished parsing at {output_dir}")
