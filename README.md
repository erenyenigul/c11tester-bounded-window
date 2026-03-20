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
    Select which test suite to run: `c11tester` for the built-in tests, or `bounded` for custom bounded window tests. Then run:
    ```shell
    /analysis/run_analysis.sh <test_suite>
    ```
    
    where `<test_suite>` is either `c11tester` or `bounded`.
    This compiles the target programs, runs them 100 times each with `-verbose=2` and generates the JSON files.

### Pruning Test Cases (`bounded`)

The `analysis/test_cases/programs/` directory contains a suite of C11 atomic programs designed to stress bounded-window pruning logic:

- `prune01_two_loads_same_loc.c`: Two competing stores and two reads from same location; coherence-sensitive read sequence.
- `prune02_old_store_pinned_by_reader.c`: Old store followed by newer store while a reader can still observe old/new values.
- `prune03_rmw_chain.c`: RMW edges on same location plus observer.
- `prune04_release_acquire_fence.c`: Release/acquire fence synchronization and fence-pruning behavior.
- `prune05_sc_fence_order.c`: Sequentially consistent fences across two threads.
- `prune06_unsynced_stale_reader.c`: Unsynchronized reader continuously loading while writer advances values.
- `prune07_cross_location_noise.c`: Heavy activity on unrelated location to test per-location pruning isolation.
- `prune08_reader_then_writer_same_loc.c`: Thread reads then writes same location while another thread writes competing values.
- `prune09_release_seq_chain.c`: Release sequence via CAS chain with third-thread acquire read.
- `prune10_long_trace_window.c`: Longer mixed trace to trigger aggressive window pressure.

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
3.  **Compute `sw` (Synchronized-With):**
    *   **Phase 1: Valid `rf` edges:** For each load that reads from a store, an `sw` edge is added between the store and the load.
    *   **Phase 2: Thread synchronization:** Connects thread lifecycle events (`thread create` $\to$ `thread start` and `thread finish` $\to$ `thread join`).
    *   **Phase 3: Fences:** Connects a store $e_i$ to a load $e_j$ through a fence $e_f$ if $e_i \xrightarrow{po} e_f$ and $e_i \xrightarrow{rf} e_j$.
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
*   **Execution Graph Image:** (`*_execution_graph.png`) A visual representation of the standard execution graph.
    *   **Black edges:** Program Order (`po`)
    *   **Red edges:** Synchronized-With (`sw`)
    *   **Green dashed edges:** Reads-From (`rf`)
*   **HB Graph Image:** (`*_hb_graph.png`) A visual representation of the Happens-Before relations.
    *   **Blue edges:** Happens-Before (`hb`)
    *   *Note: HB edges are shown in a separate graph to avoid cluttering the execution graph.*

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
