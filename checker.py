from model import *
from symtab import Symtab
from typesys import check_binop


class Checker:
    def __init__(self):
        self.env = Symtab("global")
        self.errors = []
        self.error_set = set()
        self.current_function = None

    # ================= ERROR =================

    def error(self, msg, node=None):
        if node and hasattr(node, "line"):
            full = f"error: {msg} en la línea {node.line}"
        else:
            full = f"error: {msg}"

        if full not in self.error_set:
            self.error_set.add(full)
            self.errors.append(full)

    # ================= SCOPE =================

    def push(self, name="scope"):
        self.env = Symtab(name, self.env)

    def pop(self):
        self.env = self.env.parent

    # ================= SYMBOLS =================

    def define(self, name, type_):
        try:
            self.env.add(name, type_)
        except Exception as e:
            self.error(str(e))

    def lookup(self, name):
        value = self.env.get(name)
        if value is None:
            self.error(f"símbolo '{name}' no definido")
        return value

    # ================= VISITOR =================

    def visit_list(self, nodes):
            result = None
            for n in nodes:
                result = self.visit(n)
            return result

        
    def visit(self, node):
            if isinstance(node, list):
                return self.visit_list(node)

            method = f"visit_{type(node).__name__}"
            return getattr(self, method, self.generic_visit)(node)


    def generic_visit(self, node):
            return None
    # ================= PROGRAM =================

    def visit_Program(self, node):
        for d in node.declarations:
            self.visit(d)

    # ================= DECLARACIONES =================

    def visit_VarDecl(self, node):
        self.define(node.name, node.type)

        if node.value:
            val_type = self.visit(node.value)

            if isinstance(node.type, ArrayType) and isinstance(val_type, ArrayType):
                if node.type.base != val_type.base:
                    self.error(f"tipos incompatibles en array: {val_type} vs {node.type}", node)
            elif val_type != node.type:
                self.error(f"no se puede asignar {val_type} a {node.type}", node)

    def visit_Function(self, node):
        func_type = FunctionType(node.return_type, [p.type for p in node.params])
        self.define(node.name, func_type)

        self.push()
        self.current_function = node

        for p in node.params:
            self.define(p.name, p.type)

        has_return = False

        if node.body:
            for stmt in node.body:
                if isinstance(stmt, Return):
                    has_return = True
                self.visit(stmt)

        if node.return_type != VoidType and not self.has_return_stmt(node.body):
            self.error(f"la función '{node.name}' debe retornar un valor", node)

        self.pop()
        self.current_function = None

    # ================= BLOQUES =================

    def visit_Block(self, node):
        self.push()
        for s in node.statements:
            self.visit(s)
        self.pop()

    # ================= STATEMENTS =================

    def visit_Assignment(self, node):
        t1 = self.visit(node.target)
        t2 = self.visit(node.value)

        if t1 and t2 and t1 != t2:
            self.error(f"no se puede asignar {t2} a {t1}", node)

    def visit_Return(self, node):
        if not self.current_function:
            self.error("return fuera de función", node)
            return

        expected = self.current_function.return_type

        if node.value:
            val_type = self.visit(node.value)
            if val_type and val_type != expected:
                self.error("tipo de retorno incorrecto", node)
        else:
            if expected != VoidType:
                self.error("falta valor en return", node)

    def visit_Print(self, node):
        for a in node.args:
            self.visit(a)

    def visit_If(self, node):
        cond = self.visit(node.cond)
        if cond != BooleanType:
            self.error("la condición del if debe ser boolean", node)

        self.visit(node.then_body)

        if node.else_body:
            self.visit(node.else_body)

    def visit_While(self, node):
        cond = self.visit(node.cond)
        if cond != BooleanType:
            self.error("la condición del while debe ser boolean", node)

        self.visit(node.body)

    def visit_For(self, node):
        self.push()

        if node.init:
            self.visit(node.init)

        cond = self.visit(node.cond)
        if cond != BooleanType:
            self.error("la condición del for debe ser boolean", node)

        if node.update:
            self.visit(node.update)

        self.visit(node.body)
        self.pop()

    # ================= EXPRESIONES =================

    def visit_Number(self, node): return IntegerType
    def visit_Float(self, node): return FloatType
    def visit_String(self, node): return StringType
    def visit_Char(self, node): return CharType
    def visit_Boolean(self, node): return BooleanType

    def visit_Identifier(self, node):
        return self.lookup(node.name)

    # ================= ARRAYS =================

    def visit_ArrayLiteral(self, node):
        if not node.elements:
            return None

        first_type = self.visit(node.elements[0])
        error_done = False

        for elem in node.elements[1:]:
            t = self.visit(elem)
            if t != first_type and not error_done:
                self.error(f"array literal mezcla tipos: {first_type} y {t}", node)
                error_done = True

        return ArrayType(first_type)

    def visit_ArrayAccess(self, node):
        arr = self.visit(node.array)
        idx = self.visit(node.index)

        if idx != IntegerType:
            self.error("el índice debe ser integer", node)

        if not isinstance(arr, ArrayType):
            self.error("acceso a algo que no es array", node)
            return None

        return arr.base

    # ================= FUNCIONES =================




    def has_return_stmt(self, stmts):
        for s in stmts:
            if isinstance(s, Return):
                return True

            if isinstance(s, Block):
                if self.has_return_stmt(s.statements):
                    return True

            if isinstance(s, If):
                if self.has_return_stmt(s.then_body):
                    return True
                if s.else_body and self.has_return_stmt(s.else_body):
                    return True

            if isinstance(s, While):
                if self.has_return_stmt(s.body):
                    return True

            if isinstance(s, For):
                if self.has_return_stmt(s.body):
                    return True

        return False



    def visit_Call(self, node):
        func = self.lookup(node.name)

        if not isinstance(func, FunctionType):
            self.error(f"'{node.name}' no es una función", node)
            return None

        if len(node.args) != len(func.param_types):
            self.error(
                f"la función '{node.name}' espera {len(func.param_types)} argumentos pero recibió {len(node.args)}",
                node
            )

        for arg, expected in zip(node.args, func.param_types):
            t = self.visit(arg)
            if t != expected:
                self.error(f"tipo de argumento incorrecto en '{node.name}'", node)

        return func.return_type

    # ================= OPERADORES =================

    def visit_BinaryOp(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)

        if l is None or r is None:
            return None

        result = check_binop(node.op, l, r)

        if result is None:
            self.error(f"operación inválida: {l} {node.op} {r}", node)
            return None

        return result

    def visit_UnaryOp(self, node):
        t = self.visit(node.operand)

        if node.op == "-" and t == IntegerType:
            return IntegerType

        if node.op == "!" and t == BooleanType:
            return BooleanType

        self.error("operador unario inválido", node)
        return None