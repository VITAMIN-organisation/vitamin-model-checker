import unittest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS


class DBMAdapterTestCase(unittest.TestCase):

    def setUp(self):
        self.tctl_small_example_path = "data/small.txt"
        self.tctl_not_so_small_example_path = "data/Simple_TCTL"
        self.tctl_stages = "data/stages.txt"

    def test_tctl_small(self):
        # Testing the DBMAdapter with a small model
        tcgs = TimedCGS()
        tcgs.read_file(self.tctl_small_example_path)
        with self.assertRaises(ValueError, msg="DBM is not consistent"):
            DBMAdapter.compute_predecessors(
                tcgs, source="s1", target="s2", formulas=("x<2")
            )[0]

        zone = DBMAdapter.compute_predecessors(
            tcgs, source="s1", target="s2", formulas=("x>=3")
        )[0]
        self.assertFalse(zone.is_empty())

    def test_tctl_not_so_small(self):
        # Testing the DBMAdapter with a bigger model
        tcgs = TimedCGS()
        tcgs.read_file(self.tctl_not_so_small_example_path)
        with self.assertRaises(ValueError, msg="DBM is not consistent"):
            DBMAdapter.compute_predecessors(
                tcgs, source="s3", target="s5", formulas=("x<2")
            )[0]
        zone = DBMAdapter.compute_predecessors(
            tcgs, source="s3", target="s5", formulas=("x>3")
        )[0]
        self.assertFalse(zone.is_empty())

    def test_compute_zone_at(self):
        tcgs = TimedCGS()
        tcgs.read_file(self.tctl_not_so_small_example_path)
        zone = DBMAdapter.compute_zone_at(tcgs, "s4", "x>6")
        self.assertTrue(zone.is_empty())

    def test_max_constants(self):
        tcgs = TimedCGS()
        tcgs.read_file("data/4-pipeline.txt")
        max_constants = DBMAdapter.get_max_clock_constraints(tcgs)
        self.assertListEqual(max_constants, [4, 0])

        tcgs.read_file("data/Simple_TCTL")
        max_constants = DBMAdapter.get_max_clock_constraints(tcgs)
        self.assertListEqual(max_constants, [6, 1])

        tcgs.read_file("data/TOL_generated.txt")
        max_constants = DBMAdapter.get_max_clock_constraints(tcgs)
        self.assertListEqual(max_constants, [0, 5, 5])

    def test_pipeline(self):
        tcgs = TimedCGS()
        tcgs.read_file("data/4-pipeline.txt")
        zones = DBMAdapter.compute_predecessors(tcgs, "s0", "s1", "z>9")
