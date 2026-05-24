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
        self.local_count = 0

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

    def bind(self, name, ty, ir_name=None):
        self.scopes[-1][name] = Storage(ir_name or name, ty)

    def new_local_name(self, name):
        self.local_count += 1
        return f"{name}${self.local_count}"

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

        if isinstance(node, list):
            return self.visit_list(node)

        method = getattr(
            self,
            f"visit_{type(node).__name__}",
            self.generic_visit
        )

        return method(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__}")


    def visit_list(self, nodes):

        for n in nodes:
            self.visit(n)


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

            local_name = self.new_local_name(node.name)

            if node.value is None:
                self.emit(f"ALLOC{self.suffix(node.type)}", local_name)

            self.bind(node.name, node.type, local_name)

            if node.value:
                reg = self.visit(node.value)
                self.emit(f"STORE{self.suffix(node.type)}", reg, local_name)

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

        if node.body:
            self.visit(node.body)

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

            if reg is None:
                return

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

        # variable normal
        if isinstance(node.target, Identifier):

            storage = self.lookup(node.target.name)

            self.emit(
                f"STORE{self.suffix(storage.ty)}",
                reg,
                storage.name
            )

            return

        # array[index]
        if isinstance(node.target, ArrayAccess):

            index = self.visit(node.target.index)
            storage = self.lookup(node.target.array.name)

            self.emit(
                "STOREA",
                reg,
                storage.name,
                index
            )

            return



    

    def visit_If(self, node):

        then_label = self.new_label("Lthen")
        else_label = self.new_label("Lelse")
        end_label = self.new_label("Lend")

        cond = self.visit(node.cond)

        if node.else_body:

            self.emit("CBRANCH", cond, then_label, else_label)

            self.emit("LABEL", then_label)

            self.visit(node.then_body)

            self.emit("BRANCH", end_label)

            self.emit("LABEL", else_label)

            self.visit(node.else_body)

            self.emit("LABEL", end_label)

        else:

            self.emit("CBRANCH", cond, then_label, end_label)

            self.emit("LABEL", then_label)

            self.visit(node.then_body)

            self.emit("LABEL", end_label)

    def visit_While(self, node):

        test_label = self.new_label("Lwhile_test")
        body_label = self.new_label("Lwhile_body")
        end_label = self.new_label("Lwhile_end")

        self.emit("LABEL", test_label)

        cond = self.visit(node.cond)

        self.emit("CBRANCH", cond, body_label, end_label)

        self.emit("LABEL", body_label)

        self.visit(node.body)

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

        self.visit(node.body)

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
            storage.name,
            tmp
        )

        return tmp

    def visit_Number(self, node):

        tmp = self.new_temp()

        value = getattr(node, "value", 0)

        if isinstance(value, list):

            if len(value) > 0:
                value = value[0]
            else:
                value = 0

        try:
            value = int(value)
        except:
            value = 0

        self.emit("MOVI", value, tmp)

        return tmp
    

    def visit_Float(self, node):

        tmp = self.new_temp()

        try:
            value = float(node.value)
        except:
            value = 0.0

        self.emit("MOVF", value, tmp)

        return tmp
    def visit_Boolean(self, node):

        tmp = self.new_temp()

        self.emit("MOVI", 1 if node.value else 0, tmp)

        return tmp

    def visit_Char(self, node):

        tmp = self.new_temp()

        value = getattr(node, "value", "'\\0'")

        if not isinstance(value, str):
            value = "'\\0'"

        try:
            value = value[1:-1]

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

            value = ord(value[0]) if value else 0

        except:
            value = 0

        self.emit("MOVB", value, tmp)

        return tmp

    
    def visit_String(self, node):

        raw = getattr(node, "value", "")

        if isinstance(raw, str):

            if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
                value = raw[1:-1]
            else:
                value = raw

        else:
            value = ""

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

        values = []

        for elem in node.elements:

            if isinstance(elem, Number):

                values.append(
                    int(getattr(elem, "value", 0))
                )

            elif isinstance(elem, Float):

                values.append(
                    float(getattr(elem, "value", 0.0))
                )

            elif isinstance(elem, Boolean):

                values.append(
                    1 if getattr(elem, "value", False) else 0
                )

            elif isinstance(elem, Char):

                raw = getattr(elem, "value", "'\\0'")

                try:

                    raw = raw[1:-1]

                    values.append(
                        ord(raw[0]) if raw else 0
                    )

                except:

                    values.append(0)

            elif isinstance(elem, Identifier):

                # placeholder
                values.append(0)

            else:

                values.append(0)

        self.program.globals.append(
            ("ARRAY", label, values)
        )

        tmp = self.new_temp()

        self.emit("MOVA", label, tmp)

        return tmp

    def visit_ArrayAccess(self, node):

        index = self.visit(node.index)

        tmp = self.new_temp()

        arr_name = getattr(node.array, "name", None)

        if arr_name is None:
            arr_name = "INVALID_ARRAY"
        else:
            arr_name = self.lookup(arr_name).name

        self.emit(
            "LOADA",
            arr_name,
            index,
            tmp
        )

        return tmp
    
    
    def visit_Call(self, node):

        args = []

        for arg in node.args:
            args.append(self.visit(arg))

        # buscar función
        fn = None

        for f in self.program.functions:
            if f.name == node.name:
                fn = f
                break

        # función void
        if fn and fn.return_type == VoidType:

            self.emit("CALL", node.name, *args)

            return None

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
            "^": f"POW{s}",
        }

        if node.op in arith:

            self.emit(arith[node.op], left, right, tmp)

            return tmp

        if node.op == "%":

            self.emit(f"MOD{s}", left, right, tmp)

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
