#!/bin/bash

# Master script for the C11 Bounded Window Analysis Framework.
# Run FROM THE PROJECT ROOT on your host machine.
#
# Usage: ./c11_bounded_window.sh [--docker] [--parse] [--graphs] [--detect]
# If no flags are given, all steps except graph generation run by default (enable with --graphs).

set -e
export PYTHONPATH=$PYTHONPATH:.

RUN_DOCKER=false
RUN_PARSE=false
RUN_GRAPHS=false
RUN_DETECT=false
WHAT_TESTS="bounded"

if [ $# -eq 0 ]; then
    RUN_DOCKER=true
    RUN_PARSE=true
    RUN_GRAPHS=false # it takes a long time to generate graphs for all programs, so we disable it by default
    RUN_DETECT=true
    WHAT_TESTS="bounded"
fi

for arg in "$@"; do
    case "$arg" in
        --docker) RUN_DOCKER=true ;;
        --parse)  RUN_PARSE=true ;;
        --graphs) RUN_GRAPHS=true ;;
        --detect) RUN_DETECT=true ;;
        --c11tester) WHAT_TESTS="c11tester" ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: $0 [--docker] [--parse] [--graphs] [--detect] [--c11tester]"
            exit 1
            ;;
    esac
done

if $RUN_DOCKER; then
    echo "--- Step 1: Running C11Tester via Docker ---"
    mkdir -p data/raw && rm -rf data/raw/* data/raw/.[!.]* data/raw/..?*
    # docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh c11tester
    # docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh bounded
    docker run --rm -v "$(pwd):/analysis" pcp:latest bash /analysis/tools/run_c11tester.sh cdschecker
fi

if $RUN_PARSE; then
    echo ""
    echo "--- Step 2: Parsing C11Tester traces ---"
    mkdir -p data/parsed && rm -rf data/parsed/* data/parsed/.[!.]* data/parsed/..?*
    for program_dir in data/raw/*; do
        [ -d "$program_dir" ] || continue
        echo "Parsing: $(basename "$program_dir")"
        python3 tools/c11_parser.py "$program_dir"/output.txt data/parsed/$(basename "$program_dir")
    done
fi

if $RUN_GRAPHS; then
    echo ""
    echo "--- Step 3: Generating Execution Graphs ---"
    for program_dir in data/parsed/*; do
        [ -d "$program_dir" ] || continue
        echo "Processing: $(basename "$program_dir")"
        python3 tools/graph_generator.py "$program_dir"
    done
fi

if $RUN_DETECT; then
    echo ""
    echo "--- Step 4: Running Race Detection ---"
    for program_dir in data/parsed/*; do
        [ -d "$program_dir" ] || continue
        echo "Detecting races for: $(basename "$program_dir")"
        python3 tools/race_detector.py --pruning-mode conservative "$program_dir"
    done
fi

echo ""
echo "--- Done ---"
