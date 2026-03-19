# C11Tester Bounded Window Analysis

This project implements the Bounded Window algorithm for C11 execution traces. It consists of the following phases:

*(TODO: fill in every time we implement a new step)*
1.  **Parsing:** Converting C11Tester's verbose output into structured JSON files.
2.  **Execution Graph Generation:** Computing memory model relations (PO, SW, HB) and visualizing the execution graph.

---

## 1. Trace Parsing

The parser processes the raw text output of C11Tester and produces structured JSON files for each execution.

### How to Run Parsing
1.  Navigate to the `analysis/` directory.
2.  Run the analysis script (typically inside the provided Docker environment). First load the built C11Tester docker image: 
    ```shell
    docker run -it -v $(pwd):/analysis pcp:latest
    ```
    When inside the image, simply run the script: 
    ```shell
    /analysis/run_analysis.sh
    ```
    *This compiles the target programs, runs them 100 times each with `-verbose=2` and generates the JSON files.*

### Parsed Output
Each JSON file contains the following structure:
```json
{
  "execution_id": 1,
  "events": [
    {
      "event_id": 1,
      "thread": 1,
      "action": "atomic write",
      "memory_order": "seq_cst",
      "location": "0x100",
      "value": "0x1",
      "rf": null,
      "cv": "(1, 0)"
    }
  ]
}
```



## 2. Execution Graph Generation

Once the JSON files are generated, the `graph_generator.py` script computes the execution graph based on the C11 memory model rules.

### Algorithm Steps
The graph is constructed through the following five steps:

1.  **Load JSON:** Reads the events from a single execution trace (e.g. `execution_1.json`).
2.  **Compute `po` (Program Order):**
    *   Connects events within the same thread.
    *   For each thread, edges are created between an event and its immediate successor (based on `event_id`).
3.  **Compute `sw` (Synchronizes-With):**
    *   Identifies pairs of events at the same memory location.
    *   Ensures memory orders are **not** `relaxed`.
    *   Requires at least one event to be a **store** action.
    *   Connects the store to the other action.
    *   Also includes thread-level synchronization (thread create $\to$ thread start and thread finish $\to$ thread join).
4.  **Compute `hb` (Happens-Before):**
    *   Computes the **transitive closure** of the set of edges ($po \cup sw$).
    *   If $A \to B$ and $B \to C$, then $A \to C$ is added as an `hb` edge.
5.  **Create Graph Data:**
    *   Generates a final node structure where each node contains: `event_id`, `rf` (reads-from), `po` successors and `hb` successors.

### How to Run Graph Generation
You can process a single file or an entire directory of executions:

**Process a single file:**
```shell
python3 analysis/graph_generator.py analysis/parsed/fences2/execution_1.json
```

**Process an entire directory (100 executions):**
```shell
python3 analysis/graph_generator.py analysis/parsed/fences2/
```

### Visualization
The script automatically generates visualizations in the `analysis/graphs/` folder:
*   **JSON Graph:** (`*_graph.json`) Contains the 4 fields per node (id, rf, po, hb).
*   **PNG Image:** (`*_graph.png`) A visual representation of the graph.
    *   **Black edges:** Program Order (`po`)
    *   **Red edges:** Synchronizes-With (`sw`)
    *   **Green dashed edges:** Reads-From (`rf`)

---

## Requirements
*   **Python 3.x**
*   **Graphviz:** The `dot` command must be installed and available in your PATH for PNG generation.
    ```shell
    # macOS
    brew install graphviz
    # Ubuntu
    sudo apt-get install graphviz
    ```
