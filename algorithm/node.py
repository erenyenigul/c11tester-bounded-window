from algorithm.common import *

# this class represents a single event in the execution trace, along with its relations and metadata
class Node:
    def __init__(self, event_id, thread, action, memory_order, location, value, rf=None, cv=None):
        # taken from the JSON event data
        self.event_id = event_id
        self.thread = thread
        self.action = action.lower()
        self.memory_order = memory_order.lower()
        self.location = location
        self.value = value
        self.rf = rf
        self.cv_provided = self.parse_cv(cv)
        
        # necessary relations for the race detection algorithm
        self.sb_prior = None        # last event in the same thread (po)
        self.sw_prior = []          # events that synchronize with this event
        self.hb_reachable = set()   # set of node_ids that happen before this node
        self.prior_set_edges = []   # edges added via WritePriorSet/ReadPriorSet
    
    # parse cv string into a dictionary
    def parse_cv(self, cv_str):
        if not cv_str:
            return {}
        if isinstance(cv_str, dict):
            return cv_str
        
        import re
        # c11tester might have multiple () groups; the clock vector is usually the last one
        matches = re.findall(r'\((.*?)\)', cv_str)
        if not matches:
            return {}
        
        # take the last matched group
        inner = matches[-1]
        
        # c11tester cvs are usually space-separated, but we handle commas too
        # we also filter out anything that isn't a digit
        parts = []
        for x in re.split(r'[\s,]+', inner):
            x = x.strip()
            if x.isdigit():
                parts.append(int(x))
            elif x:
                # if it's not a pure digit, try to find the digit part (e.g., '13b' -> 13)
                digit_match = re.search(r'\d+', x)
                if digit_match:
                    parts.append(int(digit_match.group()))
        
        return {i+1: val for i, val in enumerate(parts)}

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

    def __repr__(self):
        return f"Node({self.event_id}, T{self.thread}, {self.action}, {self.memory_order}, {self.location}, {self.value})"
