class NoPruningStrategy:
    def prune(self, state):
        return False


class ConservativePruningStrategy:
    def prune(self, state):
        """
        Conservative pruning from Section 6.1 of the C11Tester paper.

        The idea is to find old stores that no thread could ever read from
        again, and throw them away. We do this in four passes:

        1. Compute CVmin, the component-wise minimum of each thread's clock
           vector. CVmin[t] is the latest event in thread t that all threads
           have already seen.

        2. For each memory location, find the most recent store within CVmin.
           Any store older than that one can never be read by anyone, so it
           is safe to delete. We approximate mo-order by event_id order.

        3. Any load pointing at a deleted store becomes meaningless, so
           delete those too.

        4. Release and SC fences strictly before CVmin are redundant since
           all threads have moved past them. Acquire fences can always be
           dropped since their effect is baked into subsequent clock vectors.
        """
        if not state.threads_history:
            return

        thread_last = {tid: history[-1]
                       for tid, history in state.threads_history.items()
                       if history}
        if not thread_last:
            return

        # hb_reachable stores event ids, not thread ids, so we look each
        # one up to find its thread and track the max event_id per thread.
        def compute_cv(last_node):
            cv = {last_node.thread: last_node.event_id}
            for eid in last_node.hb_reachable:
                n = state.nodes.get(eid)
                if n:
                    cv[n.thread] = max(cv.get(n.thread, 0), n.event_id)
            return cv

        # Thread 0 only holds the initial write and knows nothing about other
        # threads, so we skip it to avoid collapsing CVmin to zero.
        cvmin = None
        for last_node in thread_last.values():
            if last_node.action == "initial write":
                continue
            cv = compute_cv(last_node)
            if cvmin is None:
                cvmin = dict(cv)
            else:
                all_threads = set(cvmin) | set(cv)
                cvmin = {t: min(cvmin.get(t, 0), cv.get(t, 0))
                         for t in all_threads}

        if cvmin is None:
            return

        prunable = set()

        # Find the latest globally-synced store per location and mark
        # everything older than it as prunable.
        for accesses in state.ALocs.values():
            stores_at_loc = [n for n in accesses if n.is_store()]

            latest_synced = None
            for s in stores_at_loc:
                if s.event_id <= cvmin.get(s.thread, 0):
                    if latest_synced is None or s.event_id > latest_synced.event_id:
                        latest_synced = s

            if latest_synced is None:
                continue

            for s in stores_at_loc:
                if s.event_id < latest_synced.event_id:
                    prunable.add(s.event_id)

        # Loads pointing at pruned stores are dangling, remove them too.
        for accesses in state.ALocs.values():
            for n in accesses:
                if n.is_load() and n.rf in prunable:
                    prunable.add(n.event_id)

        # Strict less-than keeps the fence at the CVmin boundary alive since
        # it is still the anchor for future synchronisation checks.
        for tid, fences in state.release_fences.items():
            cvmin_t = cvmin.get(tid, 0)
            for f in fences:
                if f.event_id < cvmin_t:
                    prunable.add(f.event_id)

        for tid, fences in state.sc_fences.items():
            cvmin_t = cvmin.get(tid, 0)
            for f in fences:
                if f.event_id < cvmin_t:
                    prunable.add(f.event_id)

        # Acquire fences are always safe to drop.
        for fences in state.acquire_fences.values():
            for f in fences:
                prunable.add(f.event_id)

        if not prunable:
            return

        self._do_prune(state, prunable)

    def _do_prune(self, state, prunable_ids):
        """Remove pruned nodes from all state data structures."""
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


class AggressivePruningStrategy:

    def __init__(self, window_size):
        self.window_size = window_size

    def prune(self, state):
        pass
