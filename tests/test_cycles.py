import pytest
import os
from tools.check_cycles import CycleDetector

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class TestDependencyCycles:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.cycle_detector = CycleDetector(PROJECT_ROOT)

    def test_no_cycles_exist(self):
        self.cycle_detector.add_directory('/expeditions/')
        self.cycle_detector.add_directory('/authentication/')
        cycles = self.cycle_detector.detect()
        assert len(cycles) == 0, (
            f"Circular dependencies detected:\n"
            + "\n".join(" -> ".join(c) for c in cycles)
        )