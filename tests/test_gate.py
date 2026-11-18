from mowbot import check_syntax, LEVELS


def test_plain_calls_pass_at_level_0():
    assert check_syntax("forward()\nturn_left()\nx = 3\n", LEVELS[0].allowed_syntax) is None


def test_for_is_refused_before_level_1_and_named_with_its_line():
    msg = check_syntax("forward()\nfor i in range(3):\n    forward()\n", LEVELS[0].allowed_syntax)
    assert msg == "Line 2: you haven't unlocked `for` loops yet."
    assert check_syntax("for i in range(3):\n    forward()\n", LEVELS[1].allowed_syntax) is None


def test_comparison_counts_as_if():
    assert "`if`" in check_syntax("x = 3 > 2\n", LEVELS[2].allowed_syntax)
    assert check_syntax("if 3 > 2:\n    forward()\n", LEVELS[3].allowed_syntax) is None


def test_def_import_list_dict():
    assert "def" in check_syntax("def f():\n    return 1\n", LEVELS[5].allowed_syntax)
    assert check_syntax("def f():\n    return 1\n", LEVELS[6].allowed_syntax) is None
    assert "lists" in check_syntax("a = [1, 2]\n", LEVELS[6].allowed_syntax)
    assert "import" in check_syntax("import tools\n", LEVELS[7].allowed_syntax)
    assert "dicts" in check_syntax("d = {}\n", LEVELS[12].allowed_syntax)
    assert check_syntax("d = {(1, 2): 3}\n", LEVELS[13].allowed_syntax) is None


def test_syntax_error_is_reported_not_raised():
    assert check_syntax("forward(\n", LEVELS[0].allowed_syntax).startswith("Syntax error")
