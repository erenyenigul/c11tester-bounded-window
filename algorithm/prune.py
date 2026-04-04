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
        if not prunable_ids:
            return

        for eid in prunable_ids:
            state.nodes.pop(eid, None)

        for tid in list(state.threads_history):
            state.threads_history[tid] = [
                n for n in state.threads_history[tid]
                if n.event_id not in prunable_ids
            ]
            if not state.threads_history[tid]:
                del state.threads_history[tid]

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
    Conservative pruning (Section 6.1).
    Identifies stores that are modification-ordered before a store that all threads have seen.
    These stores and any loads reading from them can be safely removed.
    Also removes redundant fences.
    """

    def _prune(self, state):
        if not state.threads_history:
            return

        # CVmin = component-wise min of all threads' last CVs
        # Skip thread 0 (initial write only) to avoid collapsing CVmin to zero.
        cvmin = None
        for tid, history in state.threads_history.items():
            if not history:
                continue
            last_node = history[-1]
            if last_node.action == "initial write":
                continue
            if cvmin is None:
                cvmin = last_node.cv.copy()
            else:
                cvmin = cvmin.intersect(last_node.cv)

        if cvmin is None:
            return

        prunable = set()

        # 1. Identify synced stores: stores S such that S hb CVmin
        # Then prune all stores mo-before such S.
        for loc, accesses in state.ALocs.items():
            stores = [n for n in accesses if n.is_store()]
            synced_stores = [s for s in stores if s.event_id <= cvmin.get(s.thread)]
            
            if not synced_stores:
                continue
            
            # Since MO is a total order, we just need to find the "latest" synced store in MO.
            # In our trace, MO usually follows trace order, but we should follow the mo-chain to be safe.
            # To find stores mo-before any synced store, we can collect all mo-predecessors.
            loc_prunable_stores = set()
            for s_synced in synced_stores:
                curr_mo = s_synced.mo
                while curr_mo is not None and curr_mo not in loc_prunable_stores:
                    pred = state.nodes.get(curr_mo)
                    if pred:
                        loc_prunable_stores.add(curr_mo)
                        curr_mo = pred.mo
                    else:
                        break
            
            prunable.update(loc_prunable_stores)

        # 2. Prune loads that read from pruned stores.
        for loc, accesses in state.ALocs.items():
            for n in accesses:
                if n.is_load() and n.rf in prunable:
                    prunable.add(n.event_id)

        # 3. Prune stale fences.
        # Release/SC fences strictly before CVmin are redundant.
        for tid, fences in state.release_fences.items():
            for f in fences:
                if f.event_id < cvmin.get(tid):
                    prunable.add(f.event_id)

        for tid, fences in state.sc_fences.items():
            for f in fences:
                if f.event_id < cvmin.get(tid):
                    prunable.add(f.event_id)

        # Acquire fences can be removed after they are executed (CV already merged).
        for tid, fences in state.acquire_fences.items():
            for f in fences:
                # If we have seen a later event in this thread, the acquire fence is summarized.
                if f.event_id < state.threads_history[tid][-1].event_id:
                    prunable.add(f.event_id)

        if not prunable:
            return

        self._do_prune(state, prunable)


class AggressivePruningStrategy(PruningStrategy):
    """
    Aggressive pruning (Section 6.1).
    Keeps only the most recent window_size events.
    For each store outside the window, all stores mo-before it are also
    removed — even if they fall inside the window — to stay sound.
    May miss races that conservative mode would catch.
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

        # 1. Identify stores outside the window.
        # Prune them and all their mo-predecessors.
        worklist = []
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_store() and n.event_id <= cutoff:
                    if n.event_id not in prunable:
                        prunable.add(n.event_id)
                        worklist.append(n)

        # Follow mo-chain backwards.
        while worklist:
            node = worklist.pop()
            if node.is_store() and node.mo is not None:
                if node.mo not in prunable:
                    pred = state.nodes.get(node.mo)
                    if pred:
                        prunable.add(pred.event_id)
                        worklist.append(pred)

        # 2. Prune loads that read from pruned stores.
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_load() and n.rf in prunable:
                    prunable.add(n.event_id)

        # 3. Fences outside the window are safe to prune if summarized in CVs.
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
                if f.event_id <= cutoff:
                    prunable.add(f.event_id)

        if not prunable:
            return

        self._do_prune(state, prunable)
