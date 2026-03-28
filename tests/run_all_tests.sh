#!/bin/bash

set -e
export PYTHONPATH=$PYTHONPATH:.
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Step 2: always run tests
echo ""
echo "--- Step 2: Running Python tests in ./tests ---"

for test_file in ./tests/*.py; do
    [ -f "$test_file" ] || continue
    echo "Running: $(basename "$test_file")"
    python3 "$test_file"
done

echo ""
echo "--- Done ---"