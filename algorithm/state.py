from dataclasses import dataclass, field
from typing import List, Dict

from algorithm.node import Node
from algorithm.prune import NoPruningStrategy

@dataclass
class DataRace:
    a: Node
    b: Node
    location: str = field(init=False)

    def __post_init__(self):
        self.location = self.a.location

# this class represents the overall execution state and implements the race detection algorithm
class ExecutionState:
    def __init__(self, pruning_strategy=None):
        self.nodes : Dict[str, Node] = {}             # event_id -> Node (mapping of all events)
        self.ALocs = {}             # location -> [Node] (atomic accesses)
        self.NALocs = {}            # location -> [Node] (nonatomic accesses)
        self.threads_history = {}   # thread_id -> [Node] (events in thread)
        self.races : List[DataRace] = []
        self.sc_fences = {}         # thread_id -> [Node] (sc fences per thread)
        self.release_fences = {}    # thread_id -> [Node] (release fences per thread)
        self.acquire_fences = {}    # thread_id -> [Node] (acquire fences per thread)
        self.sc_stores = {}         # location -> [Node] (seq_cst stores per location)
        self.pruning_strategy = NoPruningStrategy() if pruning_strategy is None else pruning_strategy

    def get_last_sc_fence(self, thread_id):
        fences = self.sc_fences.get(thread_id, [])
        return fences[-1] if fences else None

    def get_last_sc_store(self, location):
        stores = self.sc_stores.get(location, [])
        return stores[-1] if stores else None

    def get_last_release_fence(self, thread_id):
        fences = self.release_fences.get(thread_id, [])
        return fences[-1] if fences else None

    def get_last_acquire_fence(self, thread_id):
        fences = self.acquire_fences.get(thread_id, [])
        return fences[-1] if fences else None
    
    # check if u_id happens before v_id using the hb_reachable sets
    def hb(self, u_id, v_id):
        if u_id == v_id: return True
        v = self.nodes.get(v_id)
        if not v: return False
        return u_id in v.hb_reachable


    # computes the WritePriorSet for a store s is the set of stores
    # that must be ordered before s to preserve sequential consistency semantics
    # necessary for the bounded window algorithm!!
    def write_prior_set(self, S):
        priorset = set()
        # the last sc fence in the same thread before s
        FS = self.get_last_sc_fence(S.thread)
        is_sc_store = S.is_sc()
        
        # if s is a seq_cst store, then the last seq_cst store to the same location must be in the prior set
        if is_sc_store:
            last_sc = self.get_last_sc_store(S.location)
            if last_sc:
                priorset.add(last_sc.event_id)


        # for each thread, we look for the following candidates:
        for t in self.threads_history:
            Ft = self.get_last_sc_fence(t)
            Fb = None
            if FS:
                for f in reversed(self.sc_fences.get(t, [])):
                    if f.event_id < FS.event_id:
                        Fb = f
                        break

            # s1: the last store before fs (if fs exists) 
            # in that thread to the same location
            S1 = None
            if is_sc_store and Ft:
                for n in reversed(self.threads_history[t]):
                    if n.is_store() and n.location == S.location and n.event_id < Ft.event_id:
                        S1 = n
                        break
            
            # s2: the last sc store before fs (if fs exists) 
            # in that thread to the same location
            S2 = None
            if FS:
                for n in reversed(self.threads_history[t]):
                    if n.is_sc() and n.is_store() and n.location == S.location and n.event_id < FS.event_id:
                        S2 = n
                        break
            
            # s3: the last store before the last sc fence (if it exists) 
            # in that thread to the same location
            S3 = None
            if Fb:
                for n in reversed(self.threads_history[t]):
                    if n.is_store() and n.location == S.location and n.event_id < Fb.event_id:
                        S3 = n
                        break
            
            # s4: the last store or load before s 
            # in that thread to the same location that hb s
            S4 = None
            for n in reversed(self.threads_history[t]):
                if n.event_id == S.event_id: continue
                if (n.is_load() or n.is_store()) and n.location == S.location and self.hb(n.event_id, S.event_id):
                    S4 = n
                    break
            
            # among these candidates, we take the one with the largest event id (the most recent one)
            candidates = [c for c in [S1, S2, S3, S4] if c is not None]
            if candidates:
                last_cand = sorted(candidates, key=lambda x: x.event_id)[-1]
                priorset.add(last_cand.event_id)
                
        return priorset


    # computes the ReadPriorSet for a load l reading from a store s is the set of stores
    # that must be ordered before l to preserve sequential consistency semantics
    # necessary for the bounded window algorithm!!
    def read_prior_set(self, L, S):
        priorset = set()
        # the last sc fence in the same thread before l
        FL = self.get_last_sc_fence(L.thread)
        is_sc_load = L.is_sc()

        # if l is a seq_cst load, then the last seq_cst store to the same location must be in the prior set
        for t in self.threads_history:
            Ft = self.get_last_sc_fence(t)
            Fb = None
            if FL:
                for f in reversed(self.sc_fences.get(t, [])):
                    if f.event_id < FL.event_id:
                        Fb = f
                        break

            # s1: the last store before fl (if fl exists) 
            # in that thread to the same location
            S1 = None
            if is_sc_load and Ft:
                for n in reversed(self.threads_history[t]):
                    if n.is_store() and n.location == L.location and n.event_id < Ft.event_id:
                        S1 = n
                        break
            
            # s2: the last sc store before fl (if fl exists) 
            # in that thread to the same location
            S2 = None
            if FL:
                for n in reversed(self.threads_history[t]):
                    if n.is_sc() and n.is_store() and n.location == L.location and n.event_id < FL.event_id:
                        S2 = n
                        break
            
            # s3: the last store before the last sc fence (if it exists) 
            # in that thread to the same location
            S3 = None
            if Fb:
                for n in reversed(self.threads_history[t]):
                    if n.is_store() and n.location == L.location and n.event_id < Fb.event_id:
                        S3 = n
                        break
            
            # s4: the last store or load before l 
            # in that thread to the same location that hb l
            S4 = None
            for n in reversed(self.threads_history[t]):
                if n.event_id == L.event_id: continue
                if (n.is_load() or n.is_store()) and n.location == L.location and self.hb(n.event_id, L.event_id):
                    S4 = n
                    break
            
            # among these candidates, we take the most recent one again
            candidates = [c for c in [S1, S2, S3, S4] if c is not None]
            if candidates:
                last_cand = sorted(candidates, key=lambda x: x.event_id)[-1]
                if last_cand.event_id != S.event_id:
                    priorset.add(last_cand.event_id)
        
        # check mo-graph reachability (Figure 11, lines 15-19)
        # In a trace, mo-order is the trace order of stores to the same location.
        for e_id in priorset:
            if e_id > S.event_id:
                 return set(), False

        return priorset, True


    def add_node(self, node):
        self.nodes[node.event_id] = node
        # update thread history for po edges
        self.threads_history.setdefault(node.thread, []).append(node) 
        
        # 1. compute hb incrementally
        if len(self.threads_history[node.thread]) > 1:
            prev_sb = self.threads_history[node.thread][-2]
            node.sb_prior = prev_sb.event_id
            node.hb_reachable.add(prev_sb.event_id)
            node.hb_reachable.update(prev_sb.hb_reachable)
        
        if node.rf is not None:
            store_node = self.nodes.get(node.rf)
            if store_node:
                # basic rf synchronization: store(release) -> load(acquire)
                if node.is_acquire() and store_node.is_release():
                    node.sw_prior.append(store_node.event_id)
                    node.hb_reachable.add(store_node.event_id)
                    node.hb_reachable.update(store_node.hb_reachable)
                
                # fence synchronization: release fence -> atomic store -> atomic load -> acquire fence
                # if current node is an acquire load, it synchronizes with a release store if it reads from it.
                # if current node is an acquire fence, it synchronizes with a release fence via some atomic rf.
                if node.is_acquire():
                    # for a load(acquire), it already synchronizes with a store(release) if it reads from it.
                    # but if it reads from any store, it might synchronize with a release fence before it.
                    last_rel_fence = self.get_last_release_fence(store_node.thread)
                    if last_rel_fence and last_rel_fence.event_id in store_node.hb_reachable:
                        # (rel-fence sb-> store) and (store rf-> load(acq)) -> sw edge from rel-fence to load(acq)
                        node.sw_prior.append(last_rel_fence.event_id)
                        node.hb_reachable.add(last_rel_fence.event_id)
                        node.hb_reachable.update(last_rel_fence.hb_reachable)
                
                if node.is_load():
                    # if an acquire fence follows this load, the load must also happen-after the store.
                    # this is usually handled when the acquire fence is processed.
                    pass

        # if current node is an acquire fence
        if node.is_fence() and node.is_acquire():
             # for each previous load in the same thread (sb-before this fence)
             for prev in reversed(self.threads_history[node.thread]):
                 if prev.event_id == node.event_id: continue
                 if prev.is_load() and prev.rf is not None:
                     store_node = self.nodes.get(prev.rf)
                     if store_node:
                         # (store rf-> load) and (load sb-> acq-fence) -> load(acq) effectively?
                         # actually, it's: (store(any) rf-> load) and (load sb-> acq-fence)
                         # AND (rel-fence sb-> store) -> rel-fence sw-> acq-fence.
                         last_rel_fence = self.get_last_release_fence(store_node.thread)
                         if last_rel_fence and last_rel_fence.event_id in store_node.hb_reachable:
                             node.sw_prior.append(last_rel_fence.event_id)
                             node.hb_reachable.add(last_rel_fence.event_id)
                             node.hb_reachable.update(last_rel_fence.hb_reachable)
                         
                         # (store(rel) rf-> load) and (load sb-> acq-fence) -> store(rel) sw-> acq-fence.
                         if store_node.is_release():
                             node.sw_prior.append(store_node.event_id)
                             node.hb_reachable.add(store_node.event_id)
                             node.hb_reachable.update(store_node.hb_reachable)

        if node.action == "thread start":
            for n in self.nodes.values():
                if n.action == "thread create" and n.location == node.location:
                    node.sw_prior.append(n.event_id)
                    node.hb_reachable.add(n.event_id)
                    node.hb_reachable.update(n.hb_reachable)

        # 2. add priorset edges
        if node.is_atomic():
            if node.is_store():
                pset = self.write_prior_set(node)
                #if pset:
                #    print(f"Node {node.event_id} (Store) adding priorset edges: {pset}")
                node.prior_set_edges.extend(list(pset))
                for pid in pset:
                    node.hb_reachable.add(pid)
                    node.hb_reachable.update(self.nodes[pid].hb_reachable)
            
            if node.is_load() and node.rf is not None:
                store_node = self.nodes.get(node.rf)
                if store_node:
                    pset, ok = self.read_prior_set(node, store_node)
                    if ok and pset:
                        #print(f"Node {node.event_id} (Load) adding priorset edges: {pset}")
                        node.prior_set_edges.extend(list(pset))
                        for pid in pset:
                            node.hb_reachable.add(pid)
                            node.hb_reachable.update(self.nodes[pid].hb_reachable)

        # 3. check for data races
        self.check_data_race(node)
        
        # 4. update sc/fence state
        if node.is_fence():
            if node.is_release():
                self.release_fences.setdefault(node.thread, []).append(node)
            if node.is_acquire():
                self.acquire_fences.setdefault(node.thread, []).append(node)
            if node.is_sc():
                self.sc_fences.setdefault(node.thread, []).append(node)
        
        if node.is_sc() and node.is_store():
            self.sc_stores.setdefault(node.location, []).append(node)

        # 5. update location history
        if node.is_atomic():
            self.ALocs.setdefault(node.location, []).append(node)
        else:
            self.NALocs.setdefault(node.location, []).append(node)

        self.pruning_strategy.prune(self)

    def check_data_race(self, node: Node):
        # conflicts: same location, at least one write, at least one non-atomic
        prev_accesses : List[Node] = self.ALocs.get(node.location, []) + self.NALocs.get(node.location, [])
        
        for prev in prev_accesses:
            if node.is_atomic() and prev.is_atomic():
                # we ignore non-relaxed atomics
                if not node.is_relaxed() and not prev.is_relaxed():
                    continue
            if not node.is_store() and not prev.is_store(): continue
            if prev.event_id not in node.hb_reachable:
                # potential race
                # check if node hb prev (not possible in trace order usually)
                if node.event_id in prev.hb_reachable: continue
                
                race = DataRace(a=prev, b=node)
                self.races.append(race)