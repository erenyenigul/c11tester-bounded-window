"""
Validate our computed HB clock vectors against C11Tester's ground-truth CVs.

cv_provided uses 1-based thread indexing: cv_provided[t+1] corresponds to thread t.
Our node.cv uses 0-based: cv.get(t) is the max event_id seen from thread t.

The sound property to assert is that our CV never exceeds C11Tester's CV —
i.e. we never claim an HB relation that C11Tester did not establish.
Our CV may be strictly less when we do not handle all sync primitives
(e.g. pthread_join), which is expected and results in conservative race detection.
"""

import os
import unittest

from algorithm.race import detect_from_single_execution
from algorithm.prune import NoPruningStrategy

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_cases")

def provided_as_zero_indexed(node):
    """Convert cv_provided {1: epoch, 2: epoch, ...} to {0: epoch, 1: epoch, ...}."""
    return {t - 1: epoch for t, epoch in node.cv_provided.items()}

class TestClockVectors(unittest.TestCase):

    def _check_execution(self, filepath):
        result = detect_from_single_execution(filepath, NoPruningStrategy())
        for node in result.state.nodes.values():
            if not node.cv_provided:
                continue
            provided = provided_as_zero_indexed(node)
            for thread, provided_epoch in provided.items():
                our_epoch = node.cv.get(thread)
                self.assertLessEqual(
                    our_epoch,
                    provided_epoch,
                    msg=(
                        f"{os.path.basename(filepath)} node {node.event_id} "
                        f"(T{node.thread} {node.action}): "
                        f"cv[{thread}]={our_epoch} > cv_provided={provided_epoch} "
                        f"— over-approximating HB"
                    ),
                )

    def test_all_executions(self):
        for case_name in sorted(os.listdir(TEST_DIR)):
            case_path = os.path.join(TEST_DIR, case_name)
            if not os.path.isdir(case_path):
                continue
            for filename in sorted(os.listdir(case_path)):
                if not (filename.startswith("execution_") and filename.endswith(".json")):
                    continue
                with self.subTest(case=case_name, file=filename):
                    self._check_execution(os.path.join(case_path, filename))


if __name__ == "__main__":
    unittest.main(verbosity=2)
