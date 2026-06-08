import unittest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.ZoneGraph import ZoneGraph


class ZoneGraphTestCase(unittest.TestCase):
    def test_zone_graph_builder(self):
        tcgs = TimedCGS()
        tcgs.read_file("data/4-pipeline.txt")
        zone_graph = ZoneGraph(tcgs)
        self.assertEqual(len(zone_graph.states), 6)

    def test_4_pipeline_path_from(self):
        tcgs = TimedCGS()
        tcgs.read_file("data/4-pipeline.txt")
        zone_graph = ZoneGraph(tcgs)
        paths = zone_graph.find_path_from("s3")
        self.assertEqual(len(paths), 8)

        tcgs.read_file("data/4-pipeline.txt")
        zone_graph = ZoneGraph(tcgs)
        paths = zone_graph.find_path_from("s3", [(1, ">", 200)])  # s3 and z > 20
        self.assertEqual(len(paths), 0)

    def test_4_pipeline_positive(self):
        tcgs = TimedCGS()
        tcgs.read_file("data/4-pipeline.txt")
        zone_graph = ZoneGraph(tcgs)
        paths = zone_graph.find_path_from("s3", [(2, ">=", 12)])
        self.assertTrue(len(paths) > 0)
