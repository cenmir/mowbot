"""Refuse language features the student has not unlocked yet, before the code runs.

The check walks the syntax tree, so it costs nothing at run time and names the line.
"""
import ast

# which syntax-tree nodes each unlockable feature covers
FEATURES = {
    "for": (ast.For,),
    "while": (ast.While,),
    "if": (ast.If, ast.IfExp, ast.Compare),
    "def": (ast.FunctionDef, ast.Return, ast.Lambda),
    "import": (ast.Import, ast.ImportFrom),
    "list": (ast.List, ast.ListComp, ast.Subscript),
    "bool": (ast.BoolOp, ast.Not),
    "dict": (ast.Dict, ast.DictComp, ast.Tuple),
}
NAMES = {
    "for": "`for` loops", "while": "`while` loops", "if": "`if` and comparisons",
    "def": "your own functions (`def`)", "import": "`import`", "list": "lists",
    "bool": "`and`, `or`, `not`", "dict": "dicts and tuples",
}


def check_syntax(code, allowed):
    """Return None if `code` uses only unlocked features, else a message naming the first
    offending feature and line."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error on line {e.lineno}: {e.msg}"
    for node in ast.walk(tree):
        for feature, kinds in FEATURES.items():
            if feature in allowed:
                continue
            if isinstance(node, kinds):
                line = getattr(node, "lineno", "?")
                return f"Line {line}: you haven't unlocked {NAMES[feature]} yet."
    return None
