from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from rich import print

from model import *


Instruction = tuple


@dataclass
class Storage:
    name: str
    ty: Type
    is_global: bool = False
    is_param: bool = False


@dataclass
class IRFunction:
    name: str
    params: list[tuple[str, Type]]
    return_type: Type
    instructions: list[Instruction] = field(default_factory=list)


@dataclass
class IRProgram:
    globals: list[Instruction] = field(default_factory=list)
    functions: list[IRFunction] = field(default_factory=list)

    def format(self):
        out = []

        if self.globals:
            out.append("# Globals")
            for inst in self.globals:
                out.append(format_instruction(inst))
            out.append("")

        for fn in self.functions:
            params = ", ".join(f"{n}:{t}" for n, t in fn.params)
            out.append(f"function {fn.name}({params}) -> {fn.return_type}")

            for inst in fn.instructions:
                out.append(f"  {format_instruction(inst)}")

            out.append("")

        return "\n".join(out)


def format_instruction(inst):
    if len(inst) == 1:
        return inst[0]

    return f"{inst[0]} " + ", ".join(str(x) for x in inst[1:])


class IRCodeGen:

    def __init__(self):
        self.program = IRProgram()
        self.current_function = None
        self.temp_count = 0
        self.label_count = 0
        self.scopes = []

    @classmethod
    def generate(cls, node):
        gen = cls()
        gen.visit(node)
        return gen.program

    # =====================================================
    # HELPERS
    # =====================================================

    def new_temp(self):
        self.temp_count += 1
        return f"R{self.temp_count}"

    def new_label(self, base="L"):
        self.label_count += 1
        return f"{base}{self.label_count}"

    def emit(self, *inst):

        if self.current_function is None:
            self.program.globals.append(tuple(inst))
        else:
            self.current_function.instructions.append(tuple(inst))

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def bind(self, name, ty):
        self.scopes[-1][name] = Storage(name, ty)

    def lookup(self, name):

        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise NameError(name)

    # =====================================================
    # TYPES
    # =====================================================

    def suffix(self, ty):

        if ty == IntegerType or ty == BooleanType:
            return "I"

        if ty == FloatType:
            return "F"

        if ty == CharType:
            return "B"

        if ty == StringType:
            return "S"

        if isinstance(ty, ArrayType):
            return "A"

        return "I"

    def infer_type(self, node):

        if hasattr(node, "type"):
            return node.type

        if isinstance(node, Number):
            return IntegerType

        if isinstance(node, Float):
            return FloatType

        if isinstance(node, Boolean):
            return BooleanType

        if isinstance(node, Char):
            return CharType

        if isinstance(node, String):
            return StringType

        return IntegerType

    # =====================================================
    # DISPATCH
    # =====================================================

    def visit(self, node):

        method = getattr(
            self,
            f"visit_{type(node).__name__}",
            self.generic_visit
        )

        return method(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__}")

    # =====================================================
    # PROGRAM
    # =====================================================

    def visit_Program(self, node):

        self.push_scope()

        for decl in node.declarations:
            self.visit(decl)

        self.pop_scope()

    # =====================================================
    # DECLARATIONS
    # =====================================================

    def visit_VarDecl(self, node):

        if self.current_function is None:

            self.emit(f"VAR{self.suffix(node.type)}", node.name)

            self.bind(node.name, node.type)

            if node.value:
                reg = self.visit(node.value)
                self.emit(f"STORE{self.suffix(node.type)}", reg, node.name)

        else:

            self.emit(f"ALLOC{self.suffix(node.type)}", node.name)

            self.bind(node.name, node.type)

            if node.value:
                reg = self.visit(node.value)
                self.emit(f"STORE{self.suffix(node.type)}", reg, node.name)

    def visit_Function(self, node):

        fn = IRFunction(
            node.name,
            [(p.name, p.type) for p in node.params],
            node.return_type
        )

        self.program.functions.append(fn)

        prev = self.current_function
        self.current_function = fn

        self.push_scope()

        for p in node.params:
            self.bind(p.name, p.type)

        if isinstance(node.body, Block):
            for stmt in node.body.statements:
                self.visit(stmt)

        elif isinstance(node.body, list):
            for stmt in node.body:
                self.visit(stmt)

        if node.return_type == VoidType:
            self.emit("RET")

        self.pop_scope()

        self.current_function = prev

    def visit_Block(self, node):

        self.push_scope()

        for stmt in node.statements:
            self.visit(stmt)

        self.pop_scope()

    # =====================================================
    # STATEMENTS
    # =====================================================

    def visit_Print(self, node):

        for arg in node.args:

            reg = self.visit(arg)

            ty = self.infer_type(arg)

            self.emit(f"PRINT{self.suffix(ty)}", reg)

    def visit_Return(self, node):

        if node.value is None:
            self.emit("RET")
            return

        reg = self.visit(node.value)

        self.emit("RET", reg)

    def visit_Assignment(self, node):

        reg = self.visit(node.value)

        if isinstance(node.target, Identifier):

            storage = self.lookup(node.target.name)

            self.emit(
                f"STORE{self.suffix(storage.ty)}",
                reg,
                node.target.name
            )


    def visit_If(self, node):

        then_label = self.new_label("Lthen")
        else_label = self.new_label("Lelse")
        end_label = self.new_label("Lend")

        cond = self.visit(node.cond)

        # if con else
        if node.else_body:

            self.emit("CBRANCH", cond, then_label, else_label)

            self.emit("LABEL", then_label)

            for stmt in node.then_body:
                self.visit(stmt)

            self.emit("BRANCH", end_label)

            self.emit("LABEL", else_label)

            for stmt in node.else_body:
                self.visit(stmt)

            self.emit("LABEL", end_label)

        # if sin else
        else:

            self.emit("CBRANCH", cond, then_label, end_label)

            self.emit("LABEL", then_label)

            for stmt in node.then_body:
                self.visit(stmt)

            self.emit("LABEL", end_label)


    def visit_While(self, node):

        test_label = self.new_label("Lwhile_test")
        body_label = self.new_label("Lwhile_body")
        end_label = self.new_label("Lwhile_end")

        self.emit("LABEL", test_label)

        cond = self.visit(node.cond)

        self.emit("CBRANCH", cond, body_label, end_label)

        self.emit("LABEL", body_label)

        for stmt in node.body:
            self.visit(stmt)

        self.emit("BRANCH", test_label)

        self.emit("LABEL", end_label)



    def visit_For(self, node):

        test_label = self.new_label("Lfor_test")
        body_label = self.new_label("Lfor_body")
        step_label = self.new_label("Lfor_step")
        end_label = self.new_label("Lfor_end")

        if node.init:
            self.visit(node.init)

        self.emit("LABEL", test_label)

        cond = self.visit(node.cond)

        self.emit("CBRANCH", cond, body_label, end_label)

        self.emit("LABEL", body_label)

        for stmt in node.body:
            self.visit(stmt)

        self.emit("LABEL", step_label)

        if node.update:
            self.visit(node.update)

        self.emit("BRANCH", test_label)

        self.emit("LABEL", end_label)


    # =====================================================
    # EXPRESSIONS
    # =====================================================

    def visit_Identifier(self, node):

        storage = self.lookup(node.name)

        tmp = self.new_temp()

        self.emit(
            f"LOAD{self.suffix(storage.ty)}",
            node.name,
            tmp
        )

        return tmp

    def visit_Number(self, node):

        tmp = self.new_temp()

        self.emit("MOVI", int(node.value), tmp)

        return tmp

    def visit_Float(self, node):

        tmp = self.new_temp()

        self.emit("MOVF", float(node.value), tmp)

        return tmp

    def visit_Boolean(self, node):

        tmp = self.new_temp()

        self.emit("MOVI", 1 if node.value else 0, tmp)

        return tmp

    def visit_Char(self, node):

        tmp = self.new_temp()

        value = node.value[1:-1]

        escapes = {
            "\\n": "\n",
            "\\t": "\t",
            "\\r": "\r",
            "\\0": "\0",
            "\\\\": "\\",
            "\\'": "'",
            '\\"': '"',
        }

        if value in escapes:
            value = escapes[value]

        if isinstance(value, str):
            value = ord(value[0])

        self.emit("MOVB", value, tmp)

        return tmp
    

    
    def visit_String(self, node):

        value = node.value[1:-1]

        label = f".str{len(self.program.globals)}"

        codes = ", ".join(str(ord(c)) for c in value)
        codes += ", 0"

        self.program.globals.append(
            ("DATAS", label, codes)
        )

        tmp = self.new_temp()

        self.emit("ADDR", label, tmp)

        return tmp


    def visit_ArrayLiteral(self, node):

        label = f"ARR_{len(self.program.globals)}"

        self.program.globals.append(
            ("ARRAY", label, len(node.elements))
        )

        tmp = self.new_temp()

        self.emit("MOVA", label, tmp)

        return tmp

    def visit_ArrayAccess(self, node):

        index = self.visit(node.index)

        tmp = self.new_temp()

        self.emit(
            "LOADA",
            node.array.name,
            index,
            tmp
        )

        return tmp

    def visit_Call(self, node):

        args = []

        for arg in node.args:
            args.append(self.visit(arg))

        tmp = self.new_temp()

        self.emit("CALL", node.name, *args, tmp)

        return tmp

    def visit_UnaryOp(self, node):

        value = self.visit(node.operand)

        tmp = self.new_temp()

        ty = self.infer_type(node.operand)

        s = self.suffix(ty)

        if node.op == "-":
            self.emit(f"NEG{s}", value, tmp)

        elif node.op == "!":
            self.emit("NOT", value, tmp)

        else:
            self.emit(f"MOV{s}", value, tmp)

        return tmp

    def visit_BinaryOp(self, node):

        left = self.visit(node.left)
        right = self.visit(node.right)

        tmp = self.new_temp()

        ty = self.infer_type(node.left)

        s = self.suffix(ty)

        arith = {
            "+": f"ADD{s}",
            "-": f"SUB{s}",
            "*": f"MUL{s}",
            "/": f"DIV{s}",
        }

        if node.op in arith:

            self.emit(arith[node.op], left, right, tmp)

            return tmp

        if node.op == "%":

            q = self.new_temp()
            m = self.new_temp()

            self.emit(f"DIV{s}", left, right, q)
            self.emit(f"MUL{s}", q, right, m)
            self.emit(f"SUB{s}", left, m, tmp)

            return tmp

        if node.op in ["<", ">", "<=", ">=", "==", "!="]:

            self.emit(f"CMP{s}", node.op, left, right, tmp)

            return tmp

        if node.op == "&&":

            self.emit("AND", left, right, tmp)

            return tmp

        if node.op == "||":

            self.emit("OR", left, right, tmp)

            return tmp

        raise Exception(f"Operador no soportado {node.op}")