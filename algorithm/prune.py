class PruningStrategy:
    def __init__(self, prune_interval=1):
        self.prune_interval = prune_interval
        self._count = 0  # events seen since last prune attempt

    def step(self, state):
        """Called after every event. Delegates to _prune every prune_interval events."""
        self._count += 1
        if self._count % self.prune_interval == 0:
            self._prune(state)

    def _prune(self, state):
        """Override in subclasses to implement pruning logic."""
        raise NotImplementedError("Subclasses must implement _prune method")

    def _do_prune(self, state, prunable_ids):
        """Remove nodes from every state data structure."""
        for eid in prunable_ids:
            state.nodes.pop(eid, None)

        for tid in list(state.threads_history):
            state.threads_history[tid] = [
                n for n in state.threads_history[tid]
                if n.event_id not in prunable_ids
            ]

        for loc in list(state.ALocs):
            state.ALocs[loc] = [
                n for n in state.ALocs[loc]
                if n.event_id not in prunable_ids
            ]
            if not state.ALocs[loc]:
                del state.ALocs[loc]

        for tid in list(state.sc_fences):
            state.sc_fences[tid] = [
                n for n in state.sc_fences[tid]
                if n.event_id not in prunable_ids
            ]

        for tid in list(state.release_fences):
            state.release_fences[tid] = [
                n for n in state.release_fences[tid]
                if n.event_id not in prunable_ids
            ]

        for tid in list(state.acquire_fences):
            state.acquire_fences[tid] = [
                n for n in state.acquire_fences[tid]
                if n.event_id not in prunable_ids
            ]

        for loc in list(state.sc_stores):
            state.sc_stores[loc] = [
                n for n in state.sc_stores[loc]
                if n.event_id not in prunable_ids
            ]


class NoPruningStrategy(PruningStrategy):
    
    def _prune(self, state):
        pass

class ConservativePruningStrategy(PruningStrategy):
    """
    Conservative pruning (Section 6.1). Finds stores that no thread can ever
    read from again using CVmin (component-wise min of all threads' last CVs),
    then removes those stores, any loads that read from them, and stale fences.
    """

    def _prune(self, state):
        if not state.threads_history:
            return

        thread_last = {tid: history[-1]
                       for tid, history in state.threads_history.items()
                       if history}
        if not thread_last:
            return

        # Skip thread 0 (initial write only) to avoid collapsing CVmin to zero.
        cvmin = None
        for last_node in thread_last.values():
            if last_node.action == "initial write":
                continue
            if cvmin is None:
                cvmin = last_node.cv.copy()
            else:
                cvmin = cvmin.intersect(last_node.cv)

        if cvmin is None:
            return

        prunable = set()

        # Per location: keep only the latest store all threads have seen; prune the rest.
        for accesses in state.ALocs.values():
            stores_at_loc = [n for n in accesses if n.is_store()]

            latest_synced = None
            for s in stores_at_loc:
                if s.event_id <= cvmin.get(s.thread):
                    if latest_synced is None or s.event_id > latest_synced.event_id:
                        latest_synced = s

            if latest_synced is None:
                continue

            for s in stores_at_loc:
                if s.event_id < latest_synced.event_id:
                    prunable.add(s.event_id)

        # Loads reading from pruned stores are now dangling.
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_load() and n.rf in prunable:
                    prunable.add(n.event_id)

        # Release/SC fences strictly before CVmin are redundant; acquire fences always are.
        for tid, fences in state.release_fences.items():
            for f in fences:
                if f.event_id < cvmin.get(tid):
                    prunable.add(f.event_id)

        for tid, fences in state.sc_fences.items():
            for f in fences:
                if f.event_id < cvmin.get(tid):
                    prunable.add(f.event_id)

        for fences in state.acquire_fences.values():
            for f in fences:
                prunable.add(f.event_id)

        if not prunable:
            return

        self._do_prune(state, prunable)


class AggressivePruningStrategy(PruningStrategy):
    """
    Aggressive pruning (Section 6.1). Keeps only the most recent window_size
    events. For each store outside the window, all stores mo-before it are also
    removed — even if they fall inside the window — to stay sound. May miss
    races that conservative mode would catch.
    """

    def __init__(self, window_size, prune_interval=1):
        super().__init__(prune_interval)
        self.window_size = window_size

    def _prune(self, state):
        if not state.nodes:
            return

        max_event_id = max(state.nodes)
        cutoff = max_event_id - self.window_size
        if cutoff <= 0:
            return

        prunable = set()

        # Built once per prune call; discarded after. Avoids O(N^2) scan in the worklist loop.
        rf_index = {}
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_load() and n.rf is not None:
                    rf_index.setdefault(n.rf, []).append(n)

        # Seed: stores outside the window.
        worklist = []
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_store() and n.event_id <= cutoff:
                    prunable.add(n.event_id)
                    worklist.append(n)

        # Follow mo-predecessors via prior_set_edges.
        # When a store is pruned, loads reading from it are also pruned;
        # their prior_set_edges reveal extra mo-predecessors of that store.
        while worklist:
            node = worklist.pop()
            for pred_id in node.prior_set_edges:
                if pred_id not in prunable:
                    pred = state.nodes.get(pred_id)
                    if pred is not None:
                        prunable.add(pred_id)
                        worklist.append(pred)
            if node.is_store():
                for load in rf_index.get(node.event_id, []):
                    if load.event_id not in prunable:
                        prunable.add(load.event_id)
                        worklist.append(load)

        # Release/SC fences outside the window; acquire fences always.
        for fences in state.release_fences.values():
            for f in fences:
                if f.event_id <= cutoff:
                    prunable.add(f.event_id)

        for fences in state.sc_fences.values():
            for f in fences:
                if f.event_id <= cutoff:
                    prunable.add(f.event_id)

        for fences in state.acquire_fences.values():
            for f in fences:
                prunable.add(f.event_id)

        if not prunable:
            return

        self._do_prune(state, prunable)