import ast
import logging
import math
import time
from typing import Any

logger = logging.getLogger(__name__)

_SESSION_VARS: dict[str, dict[str, Any]] = {}

_ALLOWED_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset, "int": int,
    "isinstance": isinstance, "issubclass": issubclass, "len": len,
    "list": list, "map": map, "max": max, "min": min, "ord": ord,
    "pow": pow, "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
    "True": True, "False": False, "None": None,
    "math": math,
}

_ALLOWED_NAMES = {
    "print": lambda *a: None,
}


class SandboxError(Exception):
    pass


_ALLOWED_AST_NODES = {
    ast.Expression, ast.Expr, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Is, ast.IsNot,
    ast.Num, ast.Constant, ast.Name, ast.Attribute, ast.Subscript, ast.Index,
    ast.List, ast.Dict, ast.Tuple, ast.Set, ast.Starred,
    ast.Call, ast.keyword, ast.comprehension, ast.ListComp, ast.DictComp, ast.SetComp,
    ast.Slice, ast.IfExp, ast.FormattedValue, ast.JoinedStr,
    ast.NameConstant,
}

_DANGEROUS_ATTRS = {"__class__", "__base__", "__subclasses__", "__globals__", "__code__",
                      "__builtins__", "__import__", "__loader__", "__spec__"}


def _validate_node(node: ast.AST):
    if type(node) not in _ALLOWED_AST_NODES:
        raise SandboxError(f"Node type {type(node).__name__} not allowed")
    if isinstance(node, ast.Attribute):
        if node.attr in _DANGEROUS_ATTRS:
            raise SandboxError(f"Access to {node.attr} is forbidden")
    for child in ast.iter_child_nodes(node):
        _validate_node(child)


def _safe_namespace(session_id: str) -> dict:
    if session_id not in _SESSION_VARS:
        _SESSION_VARS[session_id] = {}
    ns = {**_ALLOWED_BUILTINS, **_ALLOWED_NAMES, **_SESSION_VARS[session_id]}
    ns["__session_vars__"] = _SESSION_VARS[session_id]
    return ns


def _save_vars(session_id: str, ns: dict):
    saved = {}
    for k, v in ns.items():
        if k.startswith("_") or k in _ALLOWED_BUILTINS or k in _ALLOWED_NAMES:
            continue
        try:
            hash(v)
            saved[k] = v
        except TypeError:
            continue
    _SESSION_VARS[session_id] = saved


def execute(session_id: str, code_lines: list[str]) -> dict:
    if len(code_lines) > 100 or sum(len(l) for l in code_lines) > 10000:
        return {"success": False, "results": [], "variables": {}, "error": "Code too long"}
    ns = _safe_namespace(session_id)
    output = []
    for line in code_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tree = ast.parse(stripped, "<compute>", "eval")
            _validate_node(tree)
            compiled = compile(tree, "<compute>", "eval")
            result = eval(compiled, ns)
            if result is not None:
                fmt = _format_result(result)
                output.append(fmt)
        except SyntaxError:
            try:
                tree = ast.parse(stripped, "<compute>", "exec")
                _validate_node(tree)
                compiled = compile(tree, "<compute>", "exec")
                exec(compiled, ns)
            except SandboxError:
                raise
            except Exception as e:
                output.append(f"Error: {e}")
        except SandboxError:
            raise
        except Exception as e:
            output.append(f"Error: {e}")
    _save_vars(session_id, ns)
    return {"success": True, "results": output, "variables": {k: _format_result(v) for k, v in _SESSION_VARS.get(session_id, {}).items() if not k.startswith("_")}}


def _format_result(val: Any) -> str:
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return f"{val:.2f}"
    return str(val)


def clear_session(session_id: str):
    _SESSION_VARS.pop(session_id, None)
