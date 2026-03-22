import json
import sys
import os
from algorithm.graph_logic import *

# helper to load json data from file
def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

# main function to process a json file and generate graph data and visualization
def process_file(json_path, output_dir):
    data = load_json(json_path)
    events = data['events']
    base_name = os.path.basename(json_path).replace(".json", "")
    
    print(f"Processing {base_name}...")
    po = compute_po(events)
    sw = compute_sw(events, po)
    hb = compute_hb(events, po, sw)
    graph = create_graph_data(events, po, hb)
    
    json_out = os.path.join(output_dir, f"{base_name}_graph.json")
    with open(json_out, "w") as f:
        json.dump(graph, f, indent=2)
    
    exec_png_out = os.path.join(output_dir, f"{base_name}_execution_graph.png")
    visualize_execution_graph(events, po, sw, exec_png_out)

    hb_png_out = os.path.join(output_dir, f"{base_name}_hb_graph.png")
    visualize_hb_graph(events, hb, hb_png_out)


def main():
    if len(sys.argv) < 2:
        print("Usage: python graph_generator.py <json_file_or_directory>")
        sys.exit(1)
        
    path = sys.argv[1]
    parts = os.path.normpath(path).split(os.sep)

    if len(parts) < 2:
        print("Longer path expected.")
        sys.exit(1)

    # create output directory based on input path
    output_dir = os.path.join("data/graphs", os.path.join(parts[-2], parts[-1]))
    os.makedirs(output_dir, exist_ok=True)
    
    if os.path.isdir(path):
        # sort files to process them in order
        files = sorted([f for f in os.listdir(path) if f.endswith(".json") and not f.endswith("_graph.json")])
        for f in files:
            process_file(os.path.join(path, f), output_dir)
    else:
        process_file(path, output_dir)

if __name__ == "__main__":
    main()
