"""
scanner/ast_engine.py
Dynamic Abstract Syntax Tree (AST) Scanner Engine.
Supports Visual No-Code Scanner Builder (AND, OR, NOT, Nested conditions).
Evaluates dynamic technical, orderflow, volume, and structural rules against data.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class ComparisonOperator(str, Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    CROSSES_ABOVE = "CROSSES_ABOVE"
    CROSSES_BELOW = "CROSSES_BELOW"
    BETWEEN = "BETWEEN"


class ASTNode:
    """Base class for AST Nodes."""
    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        raise NotImplementedError


class LogicalNode(ASTNode):
    def __init__(self, operator: LogicalOperator, children: List[ASTNode]):
        self.operator = operator
        self.children = children

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        if not self.children:
            return True

        if self.operator == LogicalOperator.AND:
            return all(child.evaluate(df, current_idx) for child in self.children)
        elif self.operator == LogicalOperator.OR:
            return any(child.evaluate(df, current_idx) for child in self.children)
        elif self.operator == LogicalOperator.NOT:
            return not self.children[0].evaluate(df, current_idx)
        return False


class ConditionNode(ASTNode):
    """
    Evaluates a specific indicator or column condition.
    Example: 'close' > 'ema_20'
             'rsi_21' BETWEEN (40, 60)
             'close' CROSSES_ABOVE 'vwap'
    """
    def __init__(
        self,
        left_operand: str,
        operator: ComparisonOperator,
        right_operand: Any,
        is_right_column: bool = False
    ):
        self.left_operand = left_operand
        self.operator = operator
        self.right_operand = right_operand
        self.is_right_column = is_right_column

    def _get_val(self, df: pd.DataFrame, idx: int, operand: str, is_col: bool) -> float:
        if is_col:
            if operand in df.columns:
                return float(df[operand].iloc[idx])
            return 0.0
        return float(operand)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        if current_idx < 1:
            return False

        left_val = self._get_val(df, current_idx, self.left_operand, True)
        
        if self.operator == ComparisonOperator.BETWEEN:
            if isinstance(self.right_operand, list) and len(self.right_operand) == 2:
                lower = float(self.right_operand[0])
                upper = float(self.right_operand[1])
                return lower <= left_val <= upper
            return False

        right_val = self._get_val(df, current_idx, str(self.right_operand), self.is_right_column)

        if self.operator == ComparisonOperator.GT:
            return left_val > right_val
        elif self.operator == ComparisonOperator.LT:
            return left_val < right_val
        elif self.operator == ComparisonOperator.GTE:
            return left_val >= right_val
        elif self.operator == ComparisonOperator.LTE:
            return left_val <= right_val
        elif self.operator == ComparisonOperator.EQ:
            return abs(left_val - right_val) < 1e-6
        elif self.operator == ComparisonOperator.NEQ:
            return abs(left_val - right_val) >= 1e-6
        elif self.operator == ComparisonOperator.CROSSES_ABOVE:
            prev_left = self._get_val(df, current_idx - 1, self.left_operand, True)
            prev_right = self._get_val(df, current_idx - 1, str(self.right_operand), self.is_right_column)
            return prev_left <= prev_right and left_val > right_val
        elif self.operator == ComparisonOperator.CROSSES_BELOW:
            prev_left = self._get_val(df, current_idx - 1, self.left_operand, True)
            prev_right = self._get_val(df, current_idx - 1, str(self.right_operand), self.is_right_column)
            return prev_left >= prev_right and left_val < right_val

        return False


def build_ast_from_dict(data: Dict[str, Any]) -> ASTNode:
    """Recursively builds the AST from a JSON/Dict specification."""
    if "operator" in data and "children" in data:
        # It's a LogicalNode
        op = LogicalOperator(data["operator"])
        children = [build_ast_from_dict(child) for child in data["children"]]
        return LogicalNode(op, children)
    else:
        # It's a ConditionNode
        return ConditionNode(
            left_operand=data["left"],
            operator=ComparisonOperator(data["op"]),
            right_operand=data["right"],
            is_right_column=data.get("is_right_column", False)
        )
