#!/bin/bash

# This script runs the C11Tester analysis.
# It is intended to be executed inside the C11Tester Docker container.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MODE="$1"

if [ -z "$MODE" ]; then
    echo "Usage: $0 {c11tester|bounded}"
    exit 1
fi

case "$MODE" in
    c11tester)
        TEST_DIR="$HOME/c11tester-tests/test"
        ;;
    bounded)
        TEST_DIR="$PROJECT_ROOT/data/test_programs"
        ;;
    *)
        echo "Invalid mode: $MODE"
        echo "Usage: $0 {c11tester|bounded}"
        exit 1
        ;;
esac

OBJ_DIR=~/objects
ANALYSIS_DIR="$PROJECT_ROOT/data/parsed"

mkdir -p "$ANALYSIS_DIR"
mkdir -p "$OBJ_DIR"

echo "Compiling test programs..."
for file in "$TEST_DIR"/*.c "$TEST_DIR"/*.cc; do
    [ -e "$file" ] || continue

    chmod 777 "$file"

    filename=$(basename "$file")
    name="${filename%.*}"
    output="$OBJ_DIR/$name"

    clang -I/home/c11tester/c11tester/include -o "$output" "$file" || {
        echo "Compilation failed for $filename, skipping..."
        continue
    }
done

echo "Running C11Tester and parsing traces..."
for obj in "$OBJ_DIR"/*; do
    [ -e "$obj" ] || continue

    name=$(basename "$obj")
    dir="$ANALYSIS_DIR/$name"

    mkdir -p "$dir"

    (
        cd "$dir"
        C11TESTER="-v2 -x 100" "$obj" > output.txt 2>&1
        python3 "$PROJECT_ROOT/tools/c11_parser.py" "$dir"
    )
done