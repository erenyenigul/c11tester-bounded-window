import os
import unittest

from algorithm.race import detect_from_multiple_executions
from algorithm.prune import (
    NoPruningStrategy,
    ConservativePruningStrategy,
    AggressivePruningStrategy,
)

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_cases")

def make_equivalent_strategies():
    return [
        ("no_pruning",      NoPruningStrategy()),
        ("conservative",    ConservativePruningStrategy()),
        # Basically no pruning. Just to check that aggressive mode doesn't differ from no pruning when the window is large.
        ("aggressive_1000", AggressivePruningStrategy(1000)),
    ]


class TestPruningEquivalence(unittest.TestCase):

    def test_all_strategies_agree(self):
        for name in sorted(os.listdir(TEST_DIR)):
            path = os.path.join(TEST_DIR, name)
            if not os.path.isdir(path):
                continue
            if not any(f.startswith("execution_") for f in os.listdir(path)):
                continue

            results = {label: detect_from_multiple_executions(path, s) for label, s in make_equivalent_strategies()}
            baseline_label, baseline = next(iter(results.items()))

            for label, result in results.items():
                self.assertEqual(
                    result, baseline,
                    msg=f"[{name}] {label} differs from {baseline_label}",
                )

    def test_aggressive_small_window_subset(self):
        for name in sorted(os.listdir(TEST_DIR)):
            path = os.path.join(TEST_DIR, name)
            if not os.path.isdir(path):
                continue
            if not any(f.startswith("execution_") for f in os.listdir(path)):
                continue

            baseline = detect_from_multiple_executions(path, NoPruningStrategy())
            result   = detect_from_multiple_executions(path, AggressivePruningStrategy(10))

            self.assertLessEqual(
                result.total_races, baseline.total_races,
                msg=f"[{name}] aggressive_10 found more races than no_pruning",
            )
            for filename, races in result.races.items():
                baseline_races = baseline.races.get(filename, [])
                baseline_ids = {(r.a.event_id, r.b.event_id) for r in baseline_races}
                for race in races:
                    self.assertIn(
                        (race.a.event_id, race.b.event_id), baseline_ids,
                        msg=f"[{name}/{filename}] aggressive_10 reported a race not in baseline",
                    )

if __name__ == "__main__":
    unittest.main(verbosity=2)
