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
    ns = _safe_namespace(session_id)
    output = []
    for line in code_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            compiled = compile(stripped, "<compute>", "eval", flags=0)
            result = eval(compiled, ns)
            if result is not None:
                fmt = _format_result(result)
                output.append(fmt)
        except SyntaxError:
            try:
                compiled = compile(stripped, "<compute>", "exec", flags=0)
                exec(compiled, ns)
            except Exception as e:
                output.append(f"Error: {e}")
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
