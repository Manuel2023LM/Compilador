from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from rich import print

from model import *
from model2 import *

# ===================================================
# IR model
# ===================================================

Instruction = tuple


@dataclass
class Storage:
    """
    Describe dónde vive un símbolo durante la generación de IR.

    El objetivo es que el estudiante tenga una estructura simple para
    consultar tipo y categoría del símbolo (global, parámetro, constante).
    """
    name: str
    ty: Type
    is_global: bool = False
    is_param: bool = False
    is_const: bool = False


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

    def format(self) -> str:
        out: list[str] = []
        if self.globals:
            out.append("# Globals")
            for inst in self.globals:
                out.append(format_instruction(inst))
            out.append("")

        for fn in self.functions:
            params = ", ".join(f"{name}:{ty}" for name, ty in fn.params)
            out.append(f"function {fn.name}({params}) -> {fn.return_type}")
            for inst in fn.instructions:
                out.append(f"  {format_instruction(inst)}")
            out.append("")
        return "\n".join(out).rstrip()


# ===================================================
# Pretty printing
# ===================================================


def format_instruction(inst: Instruction) -> str:
    op = inst[0]
    if len(inst) == 1:
        return op
    args = ", ".join(
        repr(x) if isinstance(x, str) and x.startswith("L") else str(x)
        for x in inst[1:]
    )
    return f"{op} {args}"


# ===================================================
# Generator
# ===================================================


class IRCodeGen(Visitor):
    """
    Plantilla base para el proyecto de IRCode.

    Esta versión deja aproximadamente la mitad del trabajo resuelto:

    Ya implementado:
    - estructura del programa IR
    - manejo de temporales y labels
    - scopes y lookup de símbolos
    - declaración de variables y constantes
    - carga de literales enteros, booleanos y chars
    - lectura de variables (VarLoc)
    - impresión simple
    - retorno simple
    - parte de la selección de opcodes

    Pendiente para estudiantes:
    - completar BinOp
    - completar UnaryOp
    - completar Assignment compuesto
    - completar IfStmt / WhileStmt / ForStmt
    - completar FuncCall
    - arreglos y strings
    - conversiones adicionales y mejoras del IR

    Sugerencia pedagógica:
    1. Hacer primero expresiones aritméticas.
    2. Luego comparaciones.
    3. Después control de flujo.
    4. Finalmente llamadas, arreglos y extensiones.
    """


    def visit(self, node: IfStmt):
        cond = self.visit(node.test)

        label_true = self.new_label()
        label_false = self.new_label()
        label_end = self.new_label()

        self.emit("CBRANCH", cond, label_true, label_false)

        # THEN
        self.emit("LABEL", label_true)
        self.visit(node.then_block)
        self.emit("BRANCH", label_end)

        # ELSE
        self.emit("LABEL", label_false)
        if node.else_block:
            self.visit(node.else_block)

        # FIN
        self.emit("LABEL", label_end)


    def __init__(self):
        self.program = IRProgram()
        self.current_function: Optional[IRFunction] = None
        self.current_return_type: Type = VOID
        self.temp_count = 0
        self.label_count = 0
        self.scopes: list[dict[str, Storage]] = []

    @classmethod
    def generate(cls, node: Program) -> IRProgram:
        gen = cls()
        gen.visit(node)
        return gen.program

    # -------------------------------------------------
    # helpers básicos
    # -------------------------------------------------

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"R{self.temp_count}"

    def new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, *inst) -> None:
        inst = tuple(inst)
        if self.current_function is None:
            self.program.globals.append(inst)
        else:
            self.current_function.instructions.append(inst)

    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        self.scopes.pop()

    def bind(self, storage: Storage) -> None:
        if not self.scopes:
            self.push_scope()
        self.scopes[-1][storage.name] = storage

    def lookup(self, name: str) -> Storage:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"Nombre no resuelto en IRCodeGen: {name}")

    def infer_type(self, node: Optional[Node]) -> Type:
        """
        Inferencia mínima para que el generador pueda escoger opcodes.

        Nota: aquí se asume que el checker semántico ya pasó antes.
        """
        if node is None:
            return VOID

        ty = getattr(node, "type", None)
        if isinstance(ty, Type):
            return ty

        if isinstance(node, IntegerLiteral):
            return INT
        if isinstance(node, BooleanLiteral):
            return BOOL
        if isinstance(node, CharLiteral):
            return CHAR
        if isinstance(node, StringLiteral):
            return STRING
        if isinstance(node, (VarDecl, ConstDecl, Param)):
            return node.type

        # Valor por defecto conservador para no bloquear pruebas tempranas.
        return INT

    def type_suffix(self, ty: Type) -> str:
        if isinstance(ty, (IntegerType, BooleanType)):
            return "I"
        if isinstance(ty, CharType):
            return "B"
        if isinstance(ty, VoidType):
            return "V"
        raise NotImplementedError(f"Tipo aún no soportado en esta plantilla: {ty}")

    def move_opcode(self, ty: Type) -> str:
        return f"MOV{self.type_suffix(ty)}"

    def load_opcode(self, ty: Type) -> str:
        return f"LOAD{self.type_suffix(ty)}"

    def store_opcode(self, ty: Type) -> str:
        return f"STORE{self.type_suffix(ty)}"

    def alloc_opcode(self, ty: Type) -> str:
        return f"ALLOC{self.type_suffix(ty)}"

    def var_opcode(self, ty: Type) -> str:
        return f"VAR{self.type_suffix(ty)}"

    def print_opcode(self, ty: Type) -> str:
        return f"PRINT{self.type_suffix(ty)}"

    def cmp_opcode(self, ty: Type) -> str:
        return f"CMP{self.type_suffix(ty)}"

    # -------------------------------------------------
    # opcodes auxiliares
    # -------------------------------------------------

    def binary_arith_opcode(self, oper: str, ty: Type) -> str:
        suffix = self.type_suffix(ty)
        table = {
            "+": f"ADD{suffix}",
            "-": f"SUB{suffix}",
            "*": f"MUL{suffix}",
            "/": f"DIV{suffix}",
        }
        if oper not in table:
            raise NotImplementedError(f"Aritmética no soportada: {oper}")
        return table[oper]

    def binary_bit_opcode(self, oper: str, ty: Type) -> str:
        table = {
            "&": "AND",
            "|": "OR",
            "^": "XOR",
        }
        if oper not in table:
            raise NotImplementedError(f"Bitwise no soportado: {oper}")
        return table[oper]

    # -------------------------------------------------
    # programa y declaraciones
    # -------------------------------------------------

    def visit(self, node: Program):
        self.push_scope()

        # Primera pasada: registrar nombres globales.
        for decl in node.decls:
            if isinstance(decl, (VarDecl, ConstDecl)):
                self.bind(
                    Storage(
                        decl.name,
                        decl.type,
                        is_global=True,
                        is_const=isinstance(decl, ConstDecl),
                    )
                )
            elif isinstance(decl, FuncDecl):
                self.bind(Storage(decl.name, decl.type, is_global=True))

        # Segunda pasada: generar IR real.
        for decl in node.decls:
            self.visit(decl)

        self.pop_scope()
        return self.program

    def visit(self, node: VarDecl):
        if self.current_function is None:
            self.emit(self.var_opcode(node.type), node.name)
            if node.value is not None:
                src = self.visit(node.value)
                self.emit(self.store_opcode(node.type), src, node.name)
            return

        self.bind(Storage(node.name, node.type, is_const=not node.mutable))
        self.emit(self.alloc_opcode(node.type), node.name)
        if node.value is not None:
            src = self.visit(node.value)
            self.emit(self.store_opcode(node.type), src, node.name)

    def visit(self, node: ConstDecl):
        if self.current_function is None:
            self.emit(self.var_opcode(node.type), node.name)
            src = self.visit(node.value)
            self.emit(self.store_opcode(node.type), src, node.name)
            return

        self.bind(Storage(node.name, node.type, is_const=True))
        self.emit(self.alloc_opcode(node.type), node.name)
        src = self.visit(node.value)
        self.emit(self.store_opcode(node.type), src, node.name)

    def visit(self, node: FuncDecl):
        prev_fn = self.current_function
        prev_ret = self.current_return_type

        fn = IRFunction(
            name=node.name,
            params=[(p.name, p.type) for p in node.parms.params],
            return_type=node.type,
        )
        self.program.functions.append(fn)
        self.current_function = fn
        self.current_return_type = node.type

        self.push_scope()
        for p in node.parms.params:
            self.bind(Storage(p.name, p.type, is_param=True))
            self.emit(self.alloc_opcode(p.type), p.name)

        self.visit(node.body)

        # Soporte mínimo para funciones void.
        if isinstance(node.type, VoidType):
            if not fn.instructions or fn.instructions[-1][0] != "RET":
                self.emit("RET")

        self.pop_scope()
        self.current_function = prev_fn
        self.current_return_type = prev_ret

    def visit(self, node: Block):
        self.push_scope()
        for stmt in node.stmts:
            self.visit(stmt)
        self.pop_scope()

    def visit(self, node: ParamList):
        return None

    def visit(self, node: Param):
        return None

    # -------------------------------------------------
    # statements
    # -------------------------------------------------

    def visit(self, node: Assignment):
        """
        Implementación parcial.

        Ya resuelto:
        - asignación simple a variables: x = expr

        Ejercicio para estudiantes:
        - x += expr, x -= expr, ...
        - asignación a ArrayLoc
        - impedir escritura en constantes (si desean reforzarlo aquí)

        """


        if isinstance(node.loc, ArrayLoc):
            index = self.visit(node.loc.index)
            value = self.visit(node.expr)
            self.emit("STOREARR", node.loc.name, index, value)
            return
            

        if not isinstance(node.loc, VarLoc):
            raise NotImplementedError(
                "Starter: Assignment solo soporta VarLoc por ahora"
            )

        storage = self.lookup(node.loc.name)

        if storage.is_const:
            raise RuntimeError(f"No se puede modificar constante {storage.name}")   

        if node.oper == "=":
            src = self.visit(node.expr)
            self.emit(self.store_opcode(storage.ty), src, storage.name)
            return




        if node.oper in {"+=", "-=", "*=", "/="}:
            left = self.visit(node.loc)
            right = self.visit(node.expr)

            out = self.new_temp()

            oper_map = {
                "+=": "+",
                "-=": "-",
                "*=": "*",
                "/=": "/"
            }

            opcode = self.binary_arith_opcode(oper_map[node.oper], storage.ty)

            self.emit(opcode, left, right, out)
            self.emit(self.store_opcode(storage.ty), out, storage.name)
            return


        raise NotImplementedError(
            "TODO estudiante: implementar asignaciones compuestas (+=, -=, ... )"
        )

    def visit(self, node: PrintStmt):
        value = self.visit(node.expr)
        ty = self.infer_type(node.expr)

        if isinstance(ty, StringType):
            self.emit("PRINTS", value)
            return

        self.emit(self.print_opcode(ty), value)

    def visit(self, node: WhileStmt):
        label_start = self.new_label()
        label_body = self.new_label()
        label_end = self.new_label()

        self.emit("LABEL", label_start)

        cond = self.visit(node.test)
        self.emit("CBRANCH", cond, label_body, label_end)

        self.emit("LABEL", label_body)
        self.visit(node.body)
        self.emit("BRANCH", label_start)

        self.emit("LABEL", label_end)

    def visit(self, node: ForStmt):
        if node.init:
            self.visit(node.init)

        label_start = self.new_label()
        label_body = self.new_label()
        label_end = self.new_label()

        self.emit("LABEL", label_start)

        if node.test:
            cond = self.visit(node.test)
            self.emit("CBRANCH", cond, label_body, label_end)
        else:
            self.emit("BRANCH", label_body)

        self.emit("LABEL", label_body)

        self.visit(node.body)

        if node.step:
            self.visit(node.step)

        self.emit("BRANCH", label_start)
        self.emit("LABEL", label_end)

    def visit(self, node: ReturnStmt):
        if node.expr is None:
            self.emit("RET")
            return

        reg = self.visit(node.expr)
        self.emit("RET", reg)

    # -------------------------------------------------
    # expressions
    # -------------------------------------------------

    def visit(self, node: VarLoc):
        storage = self.lookup(node.name)
        tmp = self.new_temp()
        self.emit(self.load_opcode(storage.ty), storage.name, tmp)
        return tmp

    def visit(self, node: ArrayLoc):
        index = self.visit(node.index)
        out = self.new_temp()

        self.emit("LOADARR", node.name, index, out)
        return out

    def visit(self, node: FuncCall):
        args = [self.visit(arg) for arg in node.args.exprs]
        out = self.new_temp()

        self.emit("CALL", node.name, len(args), *args, out)
        return out
        
    def visit(self, node: BinOp):
        left_reg = self.visit(node.left)
        left_ty = self.infer_type(node.left)

        out = self.new_temp()

        # =========================
        # ARITMÉTICA
        # =========================
        if node.oper in {"+", "-", "*", "/"}:
            right_reg = self.visit(node.right)
            opcode = self.binary_arith_opcode(node.oper, left_ty)
            self.emit(opcode, left_reg, right_reg, out)
            return out

        # =========================
        # COMPARACIONES
        # =========================
        if node.oper in {"<", ">", "<=", ">=", "==", "!="}:
            right_reg = self.visit(node.right)
            opcode = self.cmp_opcode(left_ty)
            self.emit(opcode, node.oper, left_reg, right_reg, out)
            return out

        # =========================
        # AND (&&) CON CORTOCIRCUITO
        # =========================
        if node.oper == "&&":
            label_false = self.new_label()
            label_eval_right = self.new_label()
            label_end = self.new_label()

            # si left es falso → false directo
            self.emit("CBRANCH", left_reg, label_eval_right, label_false)

            # evaluar right
            self.emit("LABEL", label_eval_right)
            right_reg = self.visit(node.right)
            self.emit("CBRANCH", right_reg, label_eval_right + "_true", label_false)

            self.emit("LABEL", label_eval_right + "_true")
            self.emit("MOVI", 1, out)
            self.emit("BRANCH", label_end)

            # false
            self.emit("LABEL", label_false)
            self.emit("MOVI", 0, out)

            self.emit("LABEL", label_end)
            return out

        # =========================
        # OR (||) CON CORTOCIRCUITO
        # =========================
        if node.oper == "||":
            label_true = self.new_label()
            label_false = self.new_label()
            label_end = self.new_label()

            self.emit("CBRANCH", left_reg, label_true, label_false)

            # evaluar right
            self.emit("LABEL", label_false)
            right_reg = self.visit(node.right)
            self.emit("CBRANCH", right_reg, label_true, label_false + "_2")

            self.emit("LABEL", label_false + "_2")
            self.emit("MOVI", 0, out)
            self.emit("BRANCH", label_end)

            # true
            self.emit("LABEL", label_true)
            self.emit("MOVI", 1, out)

            self.emit("LABEL", label_end)
            return out

        # =========================
        # BIT A BIT
        # =========================
        if node.oper in {"&", "|", "^"}:
            right_reg = self.visit(node.right)
            opcode = self.binary_bit_opcode(node.oper, left_ty)
            self.emit(opcode, left_reg, right_reg, out)
            return out

        raise NotImplementedError(f"Operador no soportado: {node.oper}")


    def visit(self, node: UnaryOp):
        reg = self.visit(node.expr)
        out = self.new_temp()

        if node.oper == "-":
            zero = self.new_temp()
            self.emit("MOVI", 0, zero)
            self.emit("SUBI", zero, reg, out)
            return out

        if node.oper == "!":
            self.emit("CMPI", "==", reg, 0, out)
            return out

        if node.oper == "+":
            return reg

        raise NotImplementedError(f"UnaryOp no soportado: {node.oper}")

    def visit(self, node: IntegerLiteral):
        tmp = self.new_temp()
        self.emit("MOVI", int(node.value), tmp)
        return tmp

    def visit(self, node: BooleanLiteral):
        tmp = self.new_temp()
        self.emit("MOVI", 1 if node.value else 0, tmp)
        return tmp

    def visit(self, node: CharLiteral):
        tmp = self.new_temp()
        value = ord(node.value) if isinstance(node.value, str) else int(node.value)
        self.emit("MOVB", value, tmp)
        return tmp

    def visit(self, node: StringLiteral):
        label = self.new_label("str")
        self.program.globals.append(("STRING", label, node.value))
        return label


    def visit(self, node: ExprList):
        return [self.visit(expr) for expr in node.exprs]


# ===================================================
# demo
# ===================================================

if __name__ == "__main__":
    # Demo pequeña para que los estudiantes prueben la plantilla.
    ast = Program([
        FuncDecl(
            name="main",
            parms=ParamList([]),
            type=VOID,
            body=Block([
                
                VarDecl(
                    name="x",
                    type=INT,
                    value=BinOp(
                        oper="+",
                        left=IntegerLiteral(value=2),
                        right=BinOp(
                            oper="*",
                            left=IntegerLiteral(value=3),
                            right=IntegerLiteral(value=4),
                            type=INT,
                        ),
                        type=INT,
                    ),
                ),
                IfStmt(
                        test=BinOp(
                            oper="<",
                            left=IntegerLiteral(2),
                            right=IntegerLiteral(5),
                            type=INT
                        ),
                        then_block=Block([
                            PrintStmt(IntegerLiteral(1))
                        ]),
                        else_block=Block([
                            PrintStmt(IntegerLiteral(0))
                        ])
                    ),
                    PrintStmt(StringLiteral("Hola mundo")),
            
                    
            ]),
        )
    ])


    ir = IRCodeGen.generate(ast)
    print(ir.format())