# astopt.py
# ---------------------------------------------------
# Optimizador O1 para TU AST de B-Minor
#
# PIPELINE:
#
# source
#   ↓
# lexer
#   ↓
# parser
#   ↓
# checker
#   ↓
# astopt      ← ESTE ARCHIVO
#   ↓
# ircode
#
# ---------------------------------------------------

from model import *


# ===================================================
# UTILIDADES
# ===================================================

def is_int(node):
    return isinstance(node, Number)


def is_float(node):
    return isinstance(node, Float)


def is_bool(node):
    return isinstance(node, Boolean)


def is_char(node):
    return isinstance(node, Char)


def is_string(node):
    return isinstance(node, String)


def is_number(node):
    return is_int(node) or is_float(node)


def value_of(node):
    return getattr(node, "value", None)


def is_zero(node):
    return is_number(node) and node.value == 0


def is_one(node):
    return is_number(node) and node.value == 1


def make_number(value, template):
    if isinstance(template, Float):
        return Float(float(value))
    return Number(int(value))


def has_side_effect(node):

    if isinstance(node, Call):
        return True

    if isinstance(node, BinaryOp):
        return (
            has_side_effect(node.left)
            or has_side_effect(node.right)
        )

    if isinstance(node, UnaryOp):
        return has_side_effect(node.operand)

    return False


# ===================================================
# OPTIMIZADOR
# ===================================================

class ASTOptimizer:

    def __init__(self):
        self.changed = False

    def mark_changed(self):
        self.changed = True


    

    # ===================================================
    # DISPATCH
    # ===================================================

    def visit(self, node):

        if isinstance(node, list):

            new_nodes = []

            for item in node:

                if hasattr(item, "accept"):
                    optimized = item.accept(self)
                else:
                    optimized = item

                if optimized is not None:
                    new_nodes.append(optimized)

            return new_nodes

        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)

        return method(node)

    # ===================================================
    # GENERIC
    # ===================================================

    def generic_visit(self, node):
        return node

    # ===================================================
    # PROGRAM
    # ===================================================

    def visit_Program(self, node):

        new_decls = []

        for decl in node.declarations:

            optimized = self.visit(decl)

            if optimized is None:
                self.mark_changed()
                continue

            new_decls.append(optimized)

        node.declarations = new_decls

        return node

    # ===================================================
    # DECLARATIONS
    # ===================================================

    def visit_VarDecl(self, node):

        if node.value:
            node.value = node.value.accept(self)

        return node

    
    
    def optimize_body(self, body):

        if body is None:
            return None

        # Caso lista de statements
        if isinstance(body, list):

            new_body = []

            for stmt in body:

                optimized = self.visit(stmt)

                if optimized is None:
                    self.mark_changed()
                    continue

                new_body.append(optimized)

            return new_body

        # Caso Block
        return self.visit(body)



    def visit_Function(self, node):

        node.body = self.optimize_body(node.body)

        return node










    def visit_Param(self, node):
        return node

    # ===================================================
    # BLOCK
    # ===================================================

    def visit_Block(self, node):

        new_statements = []

        for stmt in node.statements:

            optimized = self.visit(stmt)

            if optimized is None:
                self.mark_changed()
                continue

            new_statements.append(optimized)

        node.statements = new_statements

        return node

    # ===================================================
    # STATEMENTS
    # ===================================================

    def visit_Assignment(self, node):

        node.target = self.visit(node.target)
        node.value = self.visit(node.value)

        return node

    def visit_Print(self, node):

        new_args = []

        for arg in node.args:
            new_args.append(self.visit(arg))

        node.args = new_args

        return node

    def visit_Return(self, node):

        if node.value:
            node.value = self.visit(node.value)

        return node

    def visit_If(self, node):

        node.cond = self.visit(node.cond)

        node.then_body = self.optimize_body(node.then_body)

        if node.else_body:
            node.else_body = self.optimize_body(node.else_body)

        if is_bool(node.cond):

            self.mark_changed()

            if node.cond.value:

                if isinstance(node.then_body, list):
                    return Block(node.then_body)

                return node.then_body

            if isinstance(node.else_body, list):
                return Block(node.else_body)

            return node.else_body

        return node

    def visit_While(self, node):

        node.cond = self.visit(node.cond)
        node.body = self.optimize_body(node.body)

        if is_bool(node.cond) and node.cond.value is False:
            self.mark_changed()
            return None

        return node

    def visit_For(self, node):

        if node.init:
            node.init = self.visit(node.init)

        if node.cond:
            node.cond = self.visit(node.cond)

        if node.update:
            node.update = self.visit(node.update)

        node.body = self.optimize_body(node.body)

        if is_bool(node.cond) and node.cond.value is False:
            self.mark_changed()
            if isinstance(node.init, list):
                return Block(node.init)

            return node.init

        return node

    # ===================================================
    # EXPRESSIONS
    # ===================================================

    def visit_Identifier(self, node):
        return node

    def visit_Number(self, node):
        return node

    def visit_Float(self, node):
        return node

    def visit_Boolean(self, node):
        return node

    def visit_String(self, node):
        return node

    def visit_Char(self, node):
        return node

    # ===================================================
    # BINARY OP
    # ===================================================

    def visit_BinaryOp(self, node):

        node.left = self.visit(node.left)
        node.right = self.visit(node.right)

        left = node.left
        right = node.right
        op = node.op

        # ===================================================
        # CONSTANT FOLDING
        # ===================================================

        if is_number(left) and is_number(right):

            lv = left.value
            rv = right.value

            try:

                if op == "+":
                    self.mark_changed()
                    return make_number(lv + rv, left)

                elif op == "-":
                    self.mark_changed()
                    return make_number(lv - rv, left)

                elif op == "*":
                    self.mark_changed()
                    return make_number(lv * rv, left)

                elif op == "/" and rv != 0:

                    self.mark_changed()

                    if is_int(left) and is_int(right):
                        return Number(lv // rv)

                    return Float(lv / rv)

                elif op == "%" and rv != 0:

                    self.mark_changed()
                    return Number(lv % rv)

                elif op == "^":
                    self.mark_changed()

                    if is_int(left) and is_int(right) and rv >= 0:
                        return Number(lv ** rv)

                    return Float(lv ** rv)

            except:
                pass

        # ===================================================
        # RELACIONALES
        # ===================================================

        if (
            (is_number(left) and is_number(right))
            or (is_bool(left) and is_bool(right))
            or (is_char(left) and is_char(right))
            or (is_string(left) and is_string(right))
        ):

            lv = value_of(left)
            rv = value_of(right)

            if op == "==":
                self.mark_changed()
                return Boolean(lv == rv)

            elif op == "!=":
                self.mark_changed()
                return Boolean(lv != rv)

            elif op == "<":
                self.mark_changed()
                return Boolean(lv < rv)

            elif op == "<=":
                self.mark_changed()
                return Boolean(lv <= rv)

            elif op == ">":
                self.mark_changed()
                return Boolean(lv > rv)

            elif op == ">=":
                self.mark_changed()
                return Boolean(lv >= rv)

        # ===================================================
        # SIMPLIFICACION ALGEBRAICA
        # ===================================================

        if op == "+":

            if is_zero(right):
                self.mark_changed()
                return left

            if is_zero(left):
                self.mark_changed()
                return right

        elif op == "-":

            if is_zero(right):
                self.mark_changed()
                return left

        elif op == "*":

            if is_one(right):
                self.mark_changed()
                return left

            if is_one(left):
                self.mark_changed()
                return right

            if is_zero(right) and not has_side_effect(left):
                self.mark_changed()
                return Number(0)

            if is_zero(left) and not has_side_effect(right):
                self.mark_changed()
                return Number(0)

        elif op == "/":

            if is_one(right):
                self.mark_changed()
                return left

        # ===================================================
        # BOOLEANOS
        # ===================================================

        elif op in ("&&", "and"):

            if is_bool(left):

                if left.value is False:
                    self.mark_changed()
                    return Boolean(False)

                if left.value is True:
                    self.mark_changed()
                    return right

            if is_bool(right):

                if right.value is False:
                    self.mark_changed()
                    return Boolean(False)

                if right.value is True:
                    self.mark_changed()
                    return left

        elif op in ("||", "or"):

            if is_bool(left):

                if left.value is True:
                    self.mark_changed()
                    return Boolean(True)

                if left.value is False:
                    self.mark_changed()
                    return right

            if is_bool(right):

                if right.value is True:
                    self.mark_changed()
                    return Boolean(True)

                if right.value is False:
                    self.mark_changed()
                    return left

        return node

    # ===================================================
    # UNARY OP
    # ===================================================

    def visit_UnaryOp(self, node):

        node.operand = self.visit(node.operand)

        expr = node.operand
        op = node.op

        if is_int(expr):

            if op == "-":
                self.mark_changed()
                return Number(-expr.value)

            elif op == "+":
                self.mark_changed()
                return expr

        elif is_float(expr):

            if op == "-":
                self.mark_changed()
                return Float(-expr.value)

            elif op == "+":
                self.mark_changed()
                return expr

        elif is_bool(expr):

            if op in ("!", "not"):
                self.mark_changed()
                return Boolean(not expr.value)

        return node

    # ===================================================
    # CALL
    # ===================================================

    def visit_Call(self, node):

        new_args = []

        for arg in node.args:
            new_args.append(self.visit(arg))

        node.args = new_args

        return node

    # ===================================================
    # ARRAYS
    # ===================================================

    def visit_ArrayLiteral(self, node):

        new_elements = []

        for elem in node.elements:
            new_elements.append(self.visit(elem))

        node.elements = new_elements

        return node

    def visit_ArrayAccess(self, node):

        node.array = self.visit(node.array)
        node.index = self.visit(node.index)

        return node


# ===================================================
# API PUBLICA
# ===================================================

def optimize_ast_o1(ast, max_passes=10, verbose=False):

    current = ast

    for i in range(max_passes):

        optimizer = ASTOptimizer()

        current = optimizer.visit(current)

        if verbose:
            print(f"[O1] pasada {i + 1} changed={optimizer.changed}")

        if not optimizer.changed:
            break

    return current
