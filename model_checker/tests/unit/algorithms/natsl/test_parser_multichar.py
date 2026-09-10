from model_checker.parsers.formulas.NatSL.parser import parse_formula


def test_multichar_strategy_variables():
    parsed = parse_formula(
        "E{2}controllerA{1}opponent:"
        "(controller,1)(opponent,2)Fgoal"
    )

    assert [q.kind for q in parsed.quantifiers] == ["E", "A"]
    assert [q.variable for q in parsed.quantifiers] == ["controller", "opponent"]
    assert [q.bound for q in parsed.quantifiers] == [2, 1]
    assert parsed.bindings == (("controller", 1), ("opponent", 2))


def test_single_char_variables_remain_supported():
    parsed = parse_formula("E{2}xA{1}y:(x,1)(y,2)Fgoal")

    assert [q.variable for q in parsed.quantifiers] == ["x", "y"]
