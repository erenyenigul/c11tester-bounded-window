# C11Tester Bounded Window Analysis

This project implements the **Bounded Window** algorithm from the C11Tester paper (*Section 6.1: Pruning the Execution Graph*).

### What is the Bounded Window Algorithm?
In concurrent program analysis, we track an "Execution Graph" of memory accesses (loads, stores, fences). For long-running programs, this graph grows indefinitely, eventually exhausting system memory. The Bounded Window algorithm is a technique to **safely prune** (delete) old parts of the execution trace that are no longer needed for future analysis.

### Why is it important?
1.  **Memory Efficiency:** Without pruning, race detectors cannot analyze long executions.
2.  **Soundness:** You cannot simply delete old events. In the C11 memory model, an "older" store might be modification-ordered *after* a "newer" store. Naive pruning would lead to invalid executions or false race reports.
3.  **Safety:** The algorithm uses **Priorsets** and **Clock Vector Intersection (`CVmin`)** to prove which stores can no longer be "read-from" by any thread.

### Project Structure
*   `algorithm/`: Core logic and C11 memory model data structures.
*   `tools/`: Command-line tools for parsing, graph generation, and race detection.
*   `data/`: Test cases, parsed JSON traces, and generated graphs.

---

## Glossary & Abbreviations

| Abbreviation | Meaning | Description |
| :--- | :--- | :--- |
| **mo** | Modification Order | The "timeline" of values for a single memory address. |
| **rf** | Reads-From | A relationship where a Load reads a value written by a specific Store. |
| **rmw** | Read-Modify-Write | An atomic operation that does both (like `fetch_add`). |
| **L** | Load | The current Load operation being analyzed. |
| **S** | Store | The current Store operation being analyzed. |
| **F** | Fence | A synchronization barrier. |
| **FL** | Fence of Load L | The last SC fence in the thread performing Load L. |
| **FS** | Fence of Store S | The last SC fence in the thread performing Store S. |
| **Ft** | Fence of thread t | The last SC fence in some other thread t. |
| **pset** | Priorset | The set of "old" operations that we are adding $hb$ edges to. |
| **a** | Address | The memory location (e.g., `0x50`). |
| **v** | Value | The data being written or read (e.g., `42`). |
| **t** | Thread | The ID of the execution context. |
| **SC** | Sequentially Consistent | Strongest memory order; implies a total order of all SC operations. |

## Running the Tools

Before running any tool, ensure your `PYTHONPATH` includes the project root so the `algorithm` package can be imported:

```shell
export PYTHONPATH=$PYTHONPATH:.
```

## Full Execution Workflow

A master script is provided to automate the entire process. This script should be run **from the project root on your host machine**.

```shell
chmod +x c11_bounded_window.sh
./c11_bounded_window.sh
```

This will:
1.  **Step 1:** Run `tools/run_analysis.sh` **via Docker** (mounting current directory to `/analysis`).
2.  **Step 2:** Run `tools/graph_generator.py` (locally on host) on all parsed programs in `data/parsed/`.
3.  **Step 3:** Run `tools/race_detector.py` (locally on host) on every execution trace found.

---

## 1. Trace Analysis via Docker

Step 1 requires the C11Tester environment, provided via a Docker container.

### Prerequisites
*   Built Docker image tagged as `pcp:latest`.

### Running Manually
If you wish to run only the trace analysis manually:
```shell
docker run --rm -v "$(pwd):/analysis" pcp:latest /analysis/tools/run_analysis.sh
```
This script compiles target programs, runs them with `-verbose=2`, and generates structured JSON in `data/parsed/`.

---

## 2. Execution Graph Generation

Computes memory model relations (PO, SW, HB) and visualizes the graph.

### How to Run
```shell
python3 tools/graph_generator.py data/parsed/fences2/
```
Visualizations are saved in `data/graphs/`.

---

## 3. Baseline Race Detection Framework

Tracks memory accesses and detects races using conflict rules and Priorsets.

### How to Run
```shell
python3 tools/race_detector.py data/test_cases/test_hb.json
```

---

## Requirements
*   **Python 3.x**
*   **Graphviz:** Required for PNG generation.
