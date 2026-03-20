#!/bin/bash

# Master script for the C11 Bounded Window Analysis Framework.
# This script should be run FROM THE PROJECT ROOT on your host machine.

# Stop on first error
set -e

# Ensure PYTHONPATH is set so that 'algorithm' package is importable for host scripts
export PYTHONPATH=$PYTHONPATH:.

# 1. Compilation, Execution and Parsing via Docker
echo "--- Step 1: Running C11 Analysis via Docker ---"
docker run --rm -v "$(pwd):/analysis" pcp:latest /analysis/tools/run_analysis.sh

# 2. Graph Generation
echo ""
echo "--- Step 2: Generating Execution Graphs (on host) ---"
for program_dir in data/parsed/*; do
    if [ -d "$program_dir" ]; then
        echo "Processing program: $(basename "$program_dir")"
        python3 tools/graph_generator.py "$program_dir"
    fi
done

# 3. Baseline Race Detection
echo ""
echo "--- Step 3: Running Baseline Race Detection (on host) ---"
for program_dir in data/parsed/*; do
    if [ -d "$program_dir" ]; then
        echo "Detecting races for program: $(basename "$program_dir")"
        for execution_file in "$program_dir"/execution_*.json; do
            # Skip the graph.json files generated in Step 2
            if [ -f "$execution_file" ] && [[ ! "$execution_file" == *"_graph.json" ]]; then
                echo "Trace: $(basename "$execution_file")"
                python3 tools/race_detector.py "$execution_file"
            fi
        done
    fi
done

echo ""
echo "--- C11 Bounded Window Analysis Framework: Task Completed ---"
