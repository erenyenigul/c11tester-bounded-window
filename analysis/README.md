# Running
1. Make sure you are running these commands from inside the directory containing `c11_parser.py` and `run_analysis.sh`

2. Load the built C11Tester docker image via
```shell
docker run -it -v $(pwd):/analysis pcp:latest
```

3. When inside the image, simply run:
```shell
/analysis/run_analysis.sh
```

Or run it without entering the image via:
```shell
docker run -it -v $(pwd):/analysis pcp:latest /analysis/run_analysis.sh
```

# What Happens

In general, the script performs the following actions:
- Compiles with clang all `.c` and `.cc` programs in `~/c11tester-tests/test` and stores their compile object files in `~/objects`, ignoring those that failed to compile.
- For each of these object files, it runs them 100 times with C11Tester with `-verbose=2` and then parses each execution's trace as a JSON object and places them in the local directory.
- For each of these traces, it searches for data races using the bounded window data race detection algorithm (TBD).

## Parsing Output

### The `$(program)/output.txt` file

Contains the exact output of the C11Tester tool after being ran with the target program.

### The `$(program)/execution_i.json` files

For each execution trace $i\in [1,100]$, parse it into the following object:

```json
{
  "execution_id": The execution number i,
  "events": [
    {
      "event_id": Trace's "#" column (integer),
      "thread": Trace's "t" column (integer),
      "action": Trace's "Action Type" column (one or two strings),
      "memory_order": Trace's "MO" column (string),
      "location": Trace's "Location" column (string),
      "value": Trace's "Value" column (string),
      "rf": Trace's "Rf" column (integer) OR null,
      "cv": Trace's "CV" column (string)
    }
    >> >>
  ]
}
```