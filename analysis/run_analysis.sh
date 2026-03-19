#!/bin/bash

TEST_DIR=~/c11tester-tests/test
OBJ_DIR=~/objects
ANALYSIS_DIR=/analysis

mkdir -p "$ANALYSIS_DIR"
mkdir -p "$OBJ_DIR"

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