"""安全数学表达式求值工具。"""

import math
import re

from langchain_core.tools import tool


_SAFE_NODES = {
    "Expression": lambda node: node.body,
    # numbers
    "Constant": lambda node: node.value,
    "UnaryOp": lambda node, op=eval: _eval_unary(node, op),
    "BinOp": lambda node, op=eval: _eval_binary(node, op),
    # names
    "Name": lambda node: _SAFE_NAMES[node.id],
}

_SAFE_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "nan": math.nan,
}


def _eval_unary(node, op):
    import operator
    ops = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
    return ops[type(node.op)](op(node.operand))


def _eval_binary(node, op):
    import operator
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.LShift: operator.lshift,
        ast.RShift: operator.rshift, ast.BitOr: operator.or_,
        ast.BitXor: operator.xor, ast.BitAnd: operator.and_,
    }
    return ops[type(node.op)](op(node.left), op(node.right))


def _safe_eval(expr: str) -> float | int:
    """仅允许白名单 AST 节点的表达式求值。"""
    import ast
    tree = ast.parse(expr.strip(), mode="eval")

    def _walk(node):
        name = type(node).__name__
        if name not in _SAFE_NODES:
            raise ValueError(f"不允许的操作: {name}")
        return _SAFE_NODES[name](node)

    return _walk(tree.body)


@tool
def calculator(expression: str) -> str:
    """安全计算数学表达式。支持 + - * / ** 和 pi/e/tau/inf 常量。示例: '2 + 3 * 4', 'pi * 2**2'"""
    # 清理全角符号
    expression = expression.replace("（", "(").replace("）", ")")
    expression = re.sub(r"[^\d\s+\-*/%.()eEpi\b]", "", expression)
    try:
        result = _safe_eval(expression)
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"
