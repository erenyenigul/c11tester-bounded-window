class ClockVector:
    """
    Clock vector mapping thread_id -> max epoch (event_id) seen from that thread.

    Defined as in Section 4.2 / 5.1 of the C11Tester paper:
        CV_A           = λt. s_A if t == t_A else 0
        CV1 union CV2  = λt. max(CV1(t), CV2(t))   -- merge (in-place)
        CV1 intersect CV2  = λt. min(CV1(t), CV2(t))   -- intersect (new CV)
        CV1 <= CV2  = forall t. CV1(t) <= CV2(t)
    """

    def __init__(self, data=None):
        self._cv = dict(data) if data else {}

    def get(self, thread):
        """Return the epoch for thread, or 0 if unseen."""
        return self._cv.get(thread, 0)

    def update(self, thread, epoch):
        """Raise the epoch for a single thread (component-wise max)."""
        if epoch > self._cv.get(thread, 0):
            self._cv[thread] = epoch

    def merge(self, other):
        """In-place union: self = self ∪ other (component-wise max)."""
        for t, epoch in other._cv.items():
            if epoch > self._cv.get(t, 0):
                self._cv[t] = epoch

    def intersect(self, other):
        """Return new CV = self ∩ other (component-wise min over all threads)."""
        all_threads = set(self._cv) | set(other._cv)
        return ClockVector({t: min(self.get(t), other.get(t)) for t in all_threads})

    def __le__(self, other):
        """CV1 ≤ CV2: ∀t. CV1(t) ≤ CV2(t)"""
        return all(epoch <= other.get(t) for t, epoch in self._cv.items())

    def copy(self):
        return ClockVector(self._cv)

    def __repr__(self):
        return f"CV({self._cv})"
