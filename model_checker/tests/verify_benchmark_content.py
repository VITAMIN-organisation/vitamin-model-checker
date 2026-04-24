import sys

from model_checker.benchmarking.adapters import get_model_content


def verify_benchmark_groups():
    # Test cases: (logic_name, expected_group)
    test_cases = [
        ("NatATL", "natATL"),
        ("NatATLF", "natATL"),
        ("NatSL", "natATL"),
        ("ATL", "CGS"),
        ("CapATL", "capCGS"),
        ("RBATL", "costCGS"),
    ]

    print("Verifying Benchmark Groups and Generators:\n")

    for logic, expected_group in test_cases:
        try:
            content = get_model_content(logic, "linear", 5)

            # 1. Identify characteristics
            # NatATL uses "C" for controllable and "I" for idle
            # Since num_agents=2, it uses "CC" and "II"
            has_nat_actions = "II" in content and "CC" in content

            # CapCGS uses "Capacities" section
            has_cap = "Capacities" in content

            # CostCGS uses "Costs_for_actions"
            has_cost = "Costs_for_actions" in content

            # Standard CGS uses "ACAC" actions
            has_standard_actions = "ACAC" in content

            print(f"- Logic {logic:8}: ", end="")

            if expected_group == "natATL":
                if has_nat_actions and not has_standard_actions:
                    print("SUCCESS (Verified NatATL Generator)")
                else:
                    print(f"FAILED (Wrong generator for {logic})")
                    sys.exit(1)
            elif expected_group == "capCGS":
                if has_cap:
                    print("SUCCESS (Verified CapCGS Generator)")
                else:
                    print(f"FAILED (Wrong generator for {logic})")
                    sys.exit(1)
            elif expected_group == "costCGS":
                if has_cost:
                    print("SUCCESS (Verified CostCGS Generator)")
                else:
                    print(f"FAILED (Wrong generator for {logic})")
                    sys.exit(1)
            else:  # CGS
                if (
                    has_standard_actions
                    and not has_nat_actions
                    and not has_cap
                    and not has_cost
                ):
                    print("SUCCESS (Verified Standard CGS Generator)")
                else:
                    print(f"FAILED (Wrong generator for {logic})")
                    sys.exit(1)

        except Exception as e:
            print(f"ERROR for {logic}: {e}")
            sys.exit(1)

    print("\nAll benchmark group verifications passed!")


if __name__ == "__main__":
    verify_benchmark_groups()
