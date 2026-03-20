import json
import re
import os
import sys

def split_executions(text):
    parts = re.split(r'Execution trace \d+:', text)
    return parts[1:] # ignores initial unneccessary header

def parse_trace(trace_text, exec_id):
    events = []
    lines = trace_text.splitlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('-') or line.startswith('#'):
            continue

        if line.startswith("HASH"):
            break

        try:
            # 1. Extract CV (might be multiple sets of parentheses, CV is the last)
            # Find all groups in parentheses
            all_cv_matches = re.findall(r'\(.*?\)', line)
            cv = " ".join(all_cv_matches) if all_cv_matches else None

            # Remove all CV groups from line to get the clean action part
            line_no_cv = line
            for match in all_cv_matches:
                line_no_cv = line_no_cv.replace(match, "").strip()

            # 2. Split the remaining part
            parts = re.split(r'\s+', line_no_cv)

            event_id = int(parts[0])
            thread = int(parts[1])

            # 3. handle multi-word action
            if parts[2] == "thread" or parts[2] == "atomic":
                action = parts[2] + " " + parts[3]
                memory_order = parts[4]
                idx = 5
            else:
                action = parts[2]
                memory_order = parts[3]
                idx = 4
            location = parts[idx]
            value = parts[idx + 1]

            # 4. rf is optional
            rf = None
            if len(parts) > idx + 2 and parts[idx + 2].isdigit():
                rf = int(parts[idx + 2])

            event = {
                "event_id": event_id,
                "thread": thread,
                "action": action,
                "memory_order": memory_order,
                "location": location,
                "value": value,
                "rf": rf,
                "cv": cv
            }

            events.append(event)

        except Exception as e:
            print(f"Skipping line due to error: {line}. Reason: {e}")
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
    if len(sys.argv) != 2:
        print("Please pass the absolute path of the output directory as a parameter")
        sys.exit(1)

    output_dir = sys.argv[1]
    input_file = os.path.join(output_dir, "output.txt")
    
    if os.path.exists(input_file):
        parse_file(input_file, output_dir)
    else:
        print(f"Warning: {input_file} not found in {output_dir}")

    print(f"Finished parsing at {output_dir}")
