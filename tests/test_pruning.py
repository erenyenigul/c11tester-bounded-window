import os
import unittest

from algorithm.race import detect_from_multiple_executions
from algorithm.prune import (
    NoPruningStrategy,
    ConservativePruningStrategy,
    AggressivePruningStrategy,
)

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_cases")

STRATEGIES = [
    ("no_pruning",    NoPruningStrategy()),
    ("conservative",  ConservativePruningStrategy()),
    ("aggressive_10", AggressivePruningStrategy(10)),
]

class TestPruningEquivalence(unittest.TestCase):

    def test_all_strategies_agree(self):
        for name in sorted(os.listdir(TEST_DIR)):
            path = os.path.join(TEST_DIR, name)
            if not os.path.isdir(path):
                continue
            if not any(f.startswith("execution_") for f in os.listdir(path)):
                continue

            results = {label: detect_from_multiple_executions(path, s) for label, s in STRATEGIES}
            baseline_label, baseline = next(iter(results.items()))

            for label, result in results.items():
                self.assertEqual(
                    result, baseline,
                    msg=f"[{name}] {label} differs from {baseline_label}",
                )

if __name__ == "__main__":
    unittest.main(verbosity=2)
