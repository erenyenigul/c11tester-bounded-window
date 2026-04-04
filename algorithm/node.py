from algorithm.common import *
from algorithm.clockvector import ClockVector

# this class represents a single event in the execution trace, along with its relations and metadata
class Node:
    def __init__(self, event_id, thread, action, memory_order, location, value, mo=None, rf=None, cv=None):
        # taken from the JSON event data
        self.event_id = event_id
        self.thread = thread
        self.action = action.lower()
        self.memory_order = memory_order.lower()
        self.location = location
        self.value = value
        self.mo = mo
        self.rf = rf
        self.cv_provided = self.parse_cv(cv)
        
        self.cv = ClockVector({thread: event_id})  # happens-before clock vector (includes self)
        self.prior_set_edges = []   # edges added via WritePriorSet/ReadPriorSet
    
    # parse cv string into a dictionary
    def parse_cv(self, cv_str):
        if cv_str:
            cv_dict = ClockVector({i: val for i, val in enumerate(cv_str)})
        else:
            cv_dict = ClockVector(None)
        return cv_dict

    def is_atomic(self):
        return is_atomic(self.action, self.memory_order)

    def is_store(self):
        return is_store(self.action)

    def is_load(self):
        return is_load(self.action)

    def is_fence(self):
        return is_fence(self.action)

    def is_rmw(self):
        return is_rmw(self.action)
        
    def is_release(self):
        return is_release(self.memory_order)

    def is_acquire(self):
        return is_acquire(self.memory_order)
    
    def is_sc(self):
        return is_sc(self.memory_order)

    def is_relaxed(self):
        return is_relaxed(self.memory_order)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.event_id == other.event_id

    def __repr__(self):
        return f"Node({self.event_id}, T{self.thread}, {self.action}, {self.memory_order}, {self.location}, {self.value})"