#!/bin/bash

set -e
export PYTHONPATH=$PYTHONPATH:.

PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/tools/compare_memory.py"
RAW_DIR="$PROJECT_ROOT/data/raw"
PARSED_DIR="$PROJECT_ROOT/data/parsed"

# Step 1: Compile & run CDSChecker benchmarks
#echo "--- Step 1: Compiling and running benchmarks ---"
#mkdir -p "$RAW_DIR" && rm -rf "$RAW_DIR"/*
 
#docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh bounded

# Step 2: Parse traces into JSON
echo "--- Step 2: Parsing traces ---"
mkdir -p "$PARSED_DIR" && rm -rf "$PARSED_DIR"/*

for program_dir in "$RAW_DIR"/*; do
    [ -d "$program_dir" ] || continue
    echo "Parsing: $(basename "$program_dir")"
    python3 tools/c11_parser.py "$program_dir"/output.txt "$PARSED_DIR"/$(basename "$program_dir")
done

# Step 3: Run analysis for all strategies and window sizes
WINDOW_SIZES=(50 100 200 300 400)
PRUNE_INTERVALS=(8 16 32 64)

for WS in "${WINDOW_SIZES[@]}"; do
    for PI in "${PRUNE_INTERVALS[@]}"; do
        echo "--- Step 3: Running compare_memory.py (WS=$WS, PI=$PI) ---"

        python3 "$PYTHON_SCRIPT" \
            "$PARSED_DIR" \
            --window-size "$WS" \
            --prune-interval "$PI" \
            --csv
    done
done

echo "--- Done. All results stored in report.csv ---"