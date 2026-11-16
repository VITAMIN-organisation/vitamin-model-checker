"""TOL temporal operators."""

import re
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.TOL.preimage import triangle_down
from model_checker.parsers.formulas.TOL.parser import DemonicBinary, DemonicOp
from model_checker.parsers.game_structures.timed_cgs.regions import all_regions

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

_DEMONIC_COST_DIGITS = re.compile(r"\d+")


def handle_globally(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicOp) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    operand_regions = node.operand.satisfying_regions
    node.satisfying_regions = greatest_fixpoint(
        all_regions(zone_graph),
        lambda regions: (
            operand_regions & triangle_down(tcgs, zone_graph, bound, regions)
        ),
    )


def handle_eventually(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicOp
) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    operand_regions = node.operand.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        operand_regions,
        lambda regions: (
            operand_regions | triangle_down(tcgs, zone_graph, bound, regions)
        ),
    )


def handle_until(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary
) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    regions1 = node.left.satisfying_regions
    regions2 = node.right.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        regions2,
        lambda regions: (
            regions2 | (regions1 & triangle_down(tcgs, zone_graph, bound, regions))
        ),
    )


def handle_release(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary
) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    regions1 = node.left.satisfying_regions
    regions2 = node.right.satisfying_regions
    node.satisfying_regions = greatest_fixpoint(
        all_regions(zone_graph),
        lambda regions: (
            regions2 & (regions1 | triangle_down(tcgs, zone_graph, bound, regions))
        ),
    )


def handle_weak(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    regions1 = node.left.satisfying_regions
    regions2 = node.right.satisfying_regions
    regions_weak = regions1 | regions2
    node.satisfying_regions = greatest_fixpoint(
        all_regions(zone_graph),
        lambda regions: (
            regions_weak & (regions2 | triangle_down(tcgs, zone_graph, bound, regions))
        ),
    )
