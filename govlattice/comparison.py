from enum import Enum


class ComparisonOperator(str, Enum):
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
