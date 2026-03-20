#!/bin/bash

TEST_PRESET_OR_PATH="${1:-c11}"

case "$TEST_PRESET_OR_PATH" in
    c11tester)
        TEST_DIR="$HOME/c11tester-tests/test"
        ;;
    bounded)
        TEST_DIR="/analysis/test_cases/programs"
        ;;
    *)
        TEST_DIR="$TEST_PRESET_OR_PATH"
        ;;
esac

OBJ_DIR=~/objects
ANALYSIS_DIR=/analysis/parsed

mkdir -p "$ANALYSIS_DIR"
mkdir -p "$OBJ_DIR"

# Compile with clang all tester programs in the TEST_DIR and store their
# object file at OBJ_DIR
for file in "$TEST_DIR"/*.c "$TEST_DIR"/*.cc; do
    [ -e "$file" ] || continue

    chmod 777 "$file"

    filename=$(basename "$file")
    name="${filename%.*}"
    output="$OBJ_DIR/$name"

    clang -std=c11 -I/home/c11tester/c11tester/include -o "$output" "$file" || {
        echo "Compilation failed for $filename, skipping..."
        continue
    }
done

# For all object files, run them with C11Tester and parse their output
for obj in "$OBJ_DIR"/*; do
    [ -e "$obj" ] || continue

    name=$(basename "$obj")
    dir="$ANALYSIS_DIR/$name"

    mkdir -p "$dir"

    (
        cd "$dir"
        C11TESTER="-v2 -x 100" "$obj" > output.txt 2>&1
        python3 "/analysis/c11_parser.py" "$dir"
    )
done