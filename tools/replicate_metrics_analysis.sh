#!/bin/bash

set -e
export PYTHONPATH=$PYTHONPATH:.
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/tools/compare_memory.py"
TEST_DATA_DIR="$PROJECT_ROOT/data/parsed"

# Step 1: Compile our custom programs + the C11Tester suite
echo "--- Step 1: Running C11Tester via Docker ---"
mkdir -p data/raw && rm -rf data/raw/* data/raw/.[!.]* data/raw/..?*

echo "--- Step 1.1: Running C11Tester via Docker on our custom programs ---"
docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh bounded

echo "--- Step 1.2: Running C11Tester via Docker on C11Tester's test suite ---"
docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh c11tester

# Step 2: Parse the raw traces into structured data
echo ""
echo "--- Step 2: Parsing C11Tester traces ---"
mkdir -p data/parsed && rm -rf data/parsed/* data/parsed/.[!.]* data/parsed/..?*
for program_dir in data/raw/*; do
    [ -d "$program_dir" ] || continue
    echo "Parsing: $(basename "$program_dir")"
    python3 tools/c11_parser.py "$program_dir"/output.txt data/parsed/$(basename "$program_dir")
done

# Step 3: Run the comparison script for various WINDOW_SIZES and fixed PRUNE_INTERVAL (default: 16)
WINDOW_SIZES=(50 100 200 300 400)
for WS in "${WINDOW_SIZES[@]}"; do
    echo "--- Step 3: Running compare_memory.py for window size $WS ---"
    
    # Run Python script on all test cases, generate CSV row
    python3 "$PYTHON_SCRIPT" \
        "$TEST_DATA_DIR" \
        --all-cases \
        --window-size "$WS" \
        --csv
done

# Step 4: Run the comparison script for various PRUNE_INTERVALS and fixed WINDOW_SIZE (default: 200)
PRUNE_INTERVALS=(8 16 32 64)
for PI in "${PRUNE_INTERVALS[@]}"; do
    echo "--- Step 4: Running compare_memory.py for prune interval $PI ---"

    # Run Python script on all test cases, generate CSV row
    python3 "$PYTHON_SCRIPT" \
        "$TEST_DATA_DIR" \
        --all-cases \
        --prune-interval "$PI" \
        --csv
done

echo "--- Done: Results appended to memory.csv ---"
