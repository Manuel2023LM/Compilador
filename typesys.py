from model import *

def check_binop(op, left, right):

    # 🔥 ARITMÉTICOS
    numeric = (IntegerType, FloatType)

    # ARITMÉTICOS
    if op in ("+", "-", "*", "/", "^"):

        if left in numeric and right in numeric:

            if left == FloatType or right == FloatType:
                return FloatType

            return IntegerType

        return None

    # MOD
    if op == "%":
        if left == IntegerType and right == IntegerType:
            return IntegerType
        return None

    # 🔥 RELACIONALES
    if op in ("<", ">", "<=", ">="):
        if left == IntegerType and right == IntegerType:
            return BooleanType
        if left == FloatType and right == FloatType:
            return BooleanType
        return None

    # 🔥 IGUALDAD
    if op in ("==", "!="):
        if left == right:
            return BooleanType
        return None

    # 🔥 LÓGICOS
    if op in ("&&", "||", "and", "or"):
        if left == BooleanType and right == BooleanType:
            return BooleanType
        return None

    return None
