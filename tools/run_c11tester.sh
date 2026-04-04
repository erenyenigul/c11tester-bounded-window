#!/bin/bash

# Compiles test programs and runs C11Tester on them.
# Intended to be executed inside the C11Tester Docker container.
# Parameters:
# c11tester: Compiles c11tester-tests/test programs
# bounded: Compiles our custom test programs in data/test_programs
# cdschecker: Compiles and runs the c11tester-benchmarks/cdschecker_modified_benchmarks

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MODE="$1"

if [ -z "$MODE" ]; then
    echo "Usage: $0 {c11tester|bounded|cdschecker}"
    exit 1
fi

OBJ_DIR=~/objects
RAW_DIR="$PROJECT_ROOT/data/raw"

mkdir -p "$RAW_DIR"
mkdir -p "$OBJ_DIR"

case "$MODE" in

# CORRECTNESS TESTS MODE (c11tester or bounded)
c11tester|bounded)

    if [ "$MODE" == "c11tester" ]; then
        TEST_DIR="$HOME/c11tester-tests/test"
    else
        TEST_DIR="$PROJECT_ROOT/data/test_programs"
    fi

    echo "Compiling test programs from $TEST_DIR..."

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

    echo "Running C11Tester on compiled programs..."

    for obj in "$OBJ_DIR"/*; do
        [ -e "$obj" ] || continue

        name=$(basename "$obj")
        dir="$RAW_DIR/$name"

        mkdir -p "$dir"

        (
            cd "$dir"
            C11TESTER="-v2 -x100" "$obj" > output.txt 2>&1
        )
    done
    ;;

# CDSCHECKER MODE (benchmarks)
cdschecker)

    BENCH_DIR="$HOME/c11tester-benchmarks/cdschecker_modified_benchmarks"

    echo "Building CDSChecker benchmarks..."
    cd "$BENCH_DIR" || exit 1

    make clean
    make || { echo "Build failed"; exit 1; }

    echo "Running CDSChecker benchmarks..."

    BENCHES=("barrier" "chase-lev-deque" "dekker-fences" "linuxrwlocks" "mcs-lock" "mpmc-queue" "ms-queue")

    for bench in "${BENCHES[@]}"; do
        echo "Running $bench..."

        cd "$BENCH_DIR/$bench" || continue

        OUT_DIR="$RAW_DIR/$bench"
        mkdir -p "$OUT_DIR"

        export LD_LIBRARY_PATH="/home/c11tester/c11tester"
        export C11TESTER="-v2 -x100"

        ./$bench > "$OUT_DIR/output.txt" 2>&1

        cd "$BENCH_DIR"
    done

    ;;

# INVALID MODE
*)
    echo "Invalid mode: $MODE"
    echo "Usage: $0 {c11tester|bounded|cdschecker}"
    exit 1
    ;;

esac

echo "Done. Raw traces stored in $RAW_DIR"