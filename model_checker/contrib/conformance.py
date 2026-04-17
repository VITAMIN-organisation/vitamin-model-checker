"""Conformance checks for external logic modules."""

from inspect import signature
from typing import Any, Dict, Type


def check_parser_conformance(parser_class: Type[Any]) -> Dict[str, Any]:
    checks = {
        "has_parse": hasattr(parser_class, "parse"),
        "has_verify": hasattr(parser_class, "verify"),
        "has_build": hasattr(parser_class, "build"),
    }
    ok = all(checks.values())
    return {"ok": ok, "checks": checks}


def check_checker_conformance(module: Any, entry_point: str = "model_checking") -> Dict[str, Any]:
    if not hasattr(module, entry_point):
        return {"ok": False, "error": f"Missing checker entry point: {entry_point}"}

    fn = getattr(module, entry_point)
    sig = signature(fn)
    param_count = len(sig.parameters)
    ok = param_count >= 2
    return {
        "ok": ok,
        "checks": {
            "entry_point": entry_point,
            "parameter_count": param_count,
            "signature": str(sig),
        },
    }


def check_model_compatibility(model_parser: Any) -> Dict[str, Any]:
    required = (
        "get_states",
        "get_initial_state",
        "get_graph",
    )
    checks = {name: hasattr(model_parser, name) for name in required}
    return {"ok": all(checks.values()), "checks": checks}
