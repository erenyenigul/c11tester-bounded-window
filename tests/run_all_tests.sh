#!/bin/bash

set -e
export PYTHONPATH=$PYTHONPATH:.

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
    mkdir -p data/raw && rm -rf data/raw/* data/raw/.[!.]* data/raw/..?*
    mkdir -p data/test_cases && rm -rf data/test_cases/* data/test_cases/.[!.]* data/test_cases/..?*
    
    echo "--- Step 1: Running C11Tester via Docker ---"
    docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh bounded
    echo ""
    
    echo "--- Step 2: Parsing C11Tester traces ---"
    for program_dir in data/raw/*; do
        [ -d "$program_dir" ] || continue
        echo "Parsing: $(basename "$program_dir")"
        python3 tools/c11_parser.py "$program_dir"/output.txt data/test_cases/$(basename "$program_dir")
    done
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