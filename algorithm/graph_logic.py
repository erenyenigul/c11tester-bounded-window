import json
import sys
import os
import subprocess
from algorithm.common import *

# computes the po (program order) relation for a list of events
def compute_po(events):
    po = []
    threads = {}
    for event in events:
        t = event['thread']
        eid = event['event_id']
        if t in threads:
            po.append((threads[t], eid))
        threads[t] = eid
    return po

# computes the sw (synchronized-with) relation for a list of events
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
        if is_fence(ef['action']):
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

# computes the hb (happens-before) relation as the transitive closure of po and sw
def compute_hb(events, po, sw):
    adj = {e['event_id']: set() for e in events}
    for u, v in po:
        adj[u].add(v)
    for u, v in sw:
        adj[u].add(v)
    
    hb = []
    nodes = [e['event_id'] for e in events]
    
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

# prepares graph data for json output
def create_graph_data(events, po, hb):
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

# visualize the execution graph using dot
def visualize_execution_graph(events, po, sw, output_png):
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
