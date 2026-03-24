# shared utilities for c11 memory model analysis

def is_atomic(action, memory_order):
    return "atomic" in action.lower() or memory_order.lower() != "na"

def is_store(action):
    a = action.lower()
    return 'write' in a or 'store' in a or 'rmw' in a

def is_load(action):
    a = action.lower()
    return 'read' in a or 'load' in a or 'rmw' in a

def is_fence(action):
    return "fence" in action.lower()

def is_rmw(action):
    return "rmw" in action.lower()

def is_release(memory_order):
    return memory_order.lower() in ["release", "acq_rel", "seq_cst"]

def is_acquire(memory_order):
    return memory_order.lower() in ["acquire", "acq_rel", "seq_cst"]

def is_sc(memory_order):
    return memory_order.lower() == "seq_cst"

def is_relaxed(memory_order):
    return memory_order.lower() == "relaxed"