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

def compute_sw(events):
    sw = []
    # logic for computing sw edges:
    # 1. same location? yes then check mo
    # 2. mo should NOT be relaxed
    # 3. at least one is store
    # 4. connect store and the other one
    
    for i in range(len(events)):
        for j in range(len(events)):
            if i == j: continue
            e1 = events[i]
            e2 = events[j]
            
            # atomic/normal synchronization
            if e1['location'] == e2['location'] and e1['location'] != "0xdeadbeef":
                if e1['memory_order'] != 'relaxed' and e2['memory_order'] != 'relaxed':
                    if is_store(e1['action']):
                        sw.append((e1['event_id'], e2['event_id']))
                    elif is_store(e2['action']):
                        sw.append((e2['event_id'], e1['event_id']))
            
            # thread creation and start
            if e1['action'] == "thread create" and e2['action'] == "thread start":
                if e1['location'] == e2['location'] or e1['value'] == e2['value']:
                    sw.append((e1['event_id'], e2['event_id']))
            
            if e1['action'] == "thread finish" and e2['action'] == "thread join":
                if e1['location'] == e2['location']:
                    sw.append((e1['event_id'], e2['event_id']))
                    
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

# visualize the graph using dot, save the dot file and png file
def visualize_graph(events, po, sw, hb, output_png):
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
        print(f"Graph saved to {output_png}")
    except Exception as e:
        print(f"Error running dot for {output_png}: {e}")


def process_file(json_path, output_dir):
    data = load_json(json_path)
    events = data['events']
    base_name = os.path.basename(json_path).replace(".json", "")
    
    print(f"Processing {base_name}...")
    po = compute_po(events)
    sw = compute_sw(events)
    hb = compute_hb(events, po, sw)
    graph = create_graph_data(events, po, hb)
    
    json_out = os.path.join(output_dir, f"{base_name}_graph.json")
    with open(json_out, "w") as f:
        json.dump(graph, f, indent=2)
    
    png_out = os.path.join(output_dir, f"{base_name}_graph.png")
    visualize_graph(events, po, sw, hb, png_out)


def main():
    if len(sys.argv) < 2:
        print("Usage: python graph_generator.py <json_file_or_directory>")
        sys.exit(1)
        
    path = sys.argv[1]
    output_dir = "analysis/graphs"
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
