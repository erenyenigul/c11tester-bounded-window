import json
import sys
import os
import subprocess

# helper to load json data from file
def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def compute_po(events):
    po = []
    threads = {}
    # for each event, we track the last event id for its thread
    # create a po edge from the last event of the same thread to the current event
    # then update the last event id for that thread
    for event in events:
        t = event['thread']
        eid = event['event_id']
        if t in threads:
            po.append((threads[t], eid))
        threads[t] = eid
    return po

def is_store(action):
    a = action.lower()
    return 'write' in a or 'store' in a or 'rmw' in a

def is_load(action):
    a = action.lower()
    return 'read' in a or 'load' in a or 'rmw' in a

def compute_sw(events, po):
    sw = []
    event_by_id = {e['event_id']: e for e in events}
    
    # phase 1: get subset of valid rf edges
    for ei in events:
        if ei.get('rf') is not None:
            ej_id = ei['rf']
            ej = event_by_id.get(ej_id)
            if ej and is_store(ej['action']) and is_load(ei['action']):
                sw.append((ej['event_id'], ei['event_id']))
    
    # phase 2: thread synchronization
    for e1 in events:
        for e2 in events:
            # thread create -> thread start
            if e1['action'] == "thread create" and e2['action'] == "thread start":
                if e1['location'] == e2['location'] or e1['value'] == e2['value']:
                    sw.append((e1['event_id'], e2['event_id']))
            # thread finish -> thread join
            if e1['action'] == "thread finish" and e2['action'] == "thread join":
                if e1['location'] == e2['location']:
                    sw.append((e1['event_id'], e2['event_id']))
                    
    # phase 3: fences
    for ef in events:
        if "fence" in ef['action'].lower():
            for ei_id, ef_id in po:
                if ef_id == ef['event_id']:
                    ei = event_by_id.get(ei_id)
                    if ei:
                        # e_i ->rf e_j means e_j reads from e_i
                        for ej in events:
                            if ej.get('rf') == ei['event_id']:
                                if ei['location'] == ej['location']:
                                    sw.append((ef['event_id'], ej['event_id']))
                                    
    return list(set(sw))


def compute_hb(events, po, sw):
    # hb is the transitive closure of (po union sw)
    adj = {e['event_id']: set() for e in events}
    for u, v in po:
        adj[u].add(v)
    for u, v in sw:
        adj[u].add(v)
    
    hb = []
    nodes = [e['event_id'] for e in events]
    
    # perform dfs from each node to find all reachable nodes in the hb graph
    for start_node in nodes:
        visited = set()
        stack = [start_node]
        while stack:
            curr = stack.pop()
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        for reached in visited:
            hb.append((start_node, reached))
            
    return hb


def create_graph_data(events, po, hb):
    # nodes should have 4 fields  (event id, rf, po, hb)
    graph = {}
    
    po_map = {e['event_id']: [] for e in events}
    for u, v in po:
        po_map[u].append(v)
        
    hb_map = {e['event_id']: [] for e in events}
    for u, v in hb:
        hb_map[u].append(v)
        
    for e in events:
        eid = e['event_id']
        graph[eid] = {
            "event_id": eid,
            "rf": e['rf'],
            "po": po_map[eid],
            "hb": hb_map[eid]
        }
    return graph

# visualize the execution graph using dot, save the dot file and png file
def visualize_execution_graph(events, po, sw, hb, output_png):
    dot_content = "digraph G {\n"
    dot_content += "  rankdir=LR;\n"
    dot_content += "  node [shape=box];\n"
    
    for e in events:
        label = f"ID: {e['event_id']}\\nT{e['thread']}\\n{e['action']}\\n{e['memory_order']}"
        dot_content += f'  {e["event_id"]} [label="{label}"];\n'
    
    for u, v in po:
        dot_content += f'  {u} -> {v} [label="po"];\n'
    
    for u, v in sw:
        dot_content += f'  {u} -> {v} [label="sw", color="red"];\n'
    
    # also show rf edges if present
    for e in events:
        if e['rf'] is not None:
            dot_content += f'  {e["rf"]} -> {e["event_id"]} [label="rf", color="green", style="dashed"];\n'

    dot_content += "}\n"
    
    dot_file = output_png.replace(".png", ".dot")
    with open(dot_file, "w") as f:
        f.write(dot_content)
    
    try:
        subprocess.run(["dot", "-Tpng", dot_file, "-o", output_png], check=True)
        print(f"Execution graph saved to {output_png}")
    except Exception as e:
        print(f"Error running dot for {output_png}: {e}")

# visualize the happens-before graph using dot
def visualize_hb_graph(events, hb, output_png):
    dot_content = "digraph G {\n"
    dot_content += "  rankdir=LR;\n"
    dot_content += "  node [shape=box];\n"
    
    for e in events:
        label = f"ID: {e['event_id']}\\nT{e['thread']}\\n{e['action']}"
        dot_content += f'  {e["event_id"]} [label="{label}"];\n'
    
    for u, v in hb:
        dot_content += f'  {u} -> {v} [label="hb", color="blue"];\n'

    dot_content += "}\n"
    
    dot_file = output_png.replace(".png", ".dot")
    with open(dot_file, "w") as f:
        f.write(dot_content)
    
    try:
        subprocess.run(["dot", "-Tpng", dot_file, "-o", output_png], check=True)
        print(f"HB graph saved to {output_png}")
    except Exception as e:
        print(f"Error running dot for {output_png}: {e}")


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
    visualize_execution_graph(events, po, sw, hb, exec_png_out)

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

    output_dir = os.path.join("analysis/graphs", os.path.join(parts[-2], parts[-1]))
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
