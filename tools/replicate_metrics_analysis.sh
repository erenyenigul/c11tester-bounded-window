#!/bin/bash

set -e
export PYTHONPATH=$PYTHONPATH:.
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/tools/compare_memory.py"
TEST_DATA_DIR="$PROJECT_ROOT/data/test_cases"

RUN_COMPILE=false

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --compile) RUN_COMPILE=true ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: $0 [--compile]"
            exit 1
            ;;
    esac
done

# Step 1: optionally run compile pipeline
if $RUN_COMPILE; then
    echo "--- Step 1: Running compile pipeline (docker + parse) ---"
    bash "$PROJECT_ROOT/c11_bounded_window.sh" --docker --parse
fi

# Step 2: run the comparison script
WINDOW_SIZES=(50 100 200 300 400)

for WS in "${WINDOW_SIZES[@]}"; do
    echo "--- Step 2: Running compare_memory.py for window size $WS ---"
    
    # Run Python script on all test cases, generate CSV row
    python3 "$PYTHON_SCRIPT" \
        "$TEST_DATA_DIR" \
        --all-cases \
        --window-size "$WS" \
        --csv
done

echo "--- Done: Results appended to memory.csv ---"
