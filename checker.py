from model import *
from symtab import Symtab
from typesys import check_binop
from multimethod import multimeta
from typesys import *



class Visitor(metaclass=multimeta):
    pass


class Checker(Visitor):
    def __init__(self):
        self.env = Symtab("global")
        self.errors = []
        self.error_set = set()
        self.current_function = None
        self.loop_depth = 0




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




    def lookup(self, name, node=None):
        value = self.env.get(name)
        if value is None:
            self.error(f"símbolo '{name}' no definido", node)
        return value
    

    def define(self, name, type_):
        try:
            self.env.add(name, type_)
        except Exception as e:
            self.error(str(e))



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
        # 1. registrar funciones primero
        for d in node.declarations:
            if isinstance(d, Function):
                func_type = FunctionType(d.return_type, [p.type for p in d.params])
                if d.name in self.env.entries:
                    self.error(f"función '{d.name}' redefinida", d)
                else:
                    self.define(d.name, func_type)

        # 2. luego todo lo demás
        for d in node.declarations:
            if not isinstance(d, Function):
                self.visit(d)

        # 3. visitar cuerpos de funciones
        for d in node.declarations:
            if isinstance(d, Function):
                self.visit(d)


        '''main = self.env.get("main")

        if main is None:
            self.error("no existe función main")

        elif not isinstance(main, FunctionType):
            self.error("main no es función")

        elif main.return_type != VoidType:
            self.error("main debe retornar void")
        elif len(main.param_types) != 0:
            self.error("main no debe recibir parámetros")'''             

    # ================= DECLARACIONES =================

    def visit_VarDecl(self, node):

        if node.name in self.env.entries:
            self.error(f"variable '{node.name}' redefinida", node)
            return

        self.define(node.name, node.type)


        if node.type is VoidType:
            self.error("una variable no puede ser void", node)


        if isinstance(node.type, ArrayType):

            if node.type.base == VoidType:
                self.error("array no puede contener void", node)

            if node.type.size:

                size_type = self.visit(node.type.size)

                if size_type != IntegerType:
                    self.error("el tamaño del array debe ser integer", node)

                if isinstance(node.type.size, Number):
                    if node.type.size.value <= 0:
                        self.error("el tamaño del array debe ser positivo", node)
        
        if node.value is not None:
            val_type = self.visit(node.value)

            if isinstance(node.type, ArrayType) and isinstance(val_type, ArrayType):
                if (
                    isinstance(node.type.size, Number)
                    and isinstance(node.value, ArrayLiteral)
                ):

                    expected = node.type.size.value
                    actual = len(node.value.elements)

                    if expected != actual:
                        self.error(
                            f"array esperaba tamaño {expected} pero recibió {actual}",
                            node
                        )
                
                
                if node.type.base != val_type.base:
                    self.error(f"tipos incompatibles en array: {val_type} vs {node.type}", node)
            elif val_type != node.type:
                self.error(f"no se puede asignar {val_type} a {node.type}", node)

    def visit_Function(self, node):

        if node.body is None:
            return

        self.push()
        self.current_function = node

        for p in node.params:
            if p.type == VoidType:
                self.error(f"el parámetro '{p.name}' no puede ser void", p)
            if p.name in self.env.entries:
                self.error(f"parámetro duplicado '{p.name}'", p)
            else:
                self.define(p.name, p.type)
            


        body = node.body.statements if isinstance(node.body, Block) else node.body

        for stmt in body:
            self.visit(stmt)

        if node.return_type != VoidType:
            if not self.must_return(body):
                self.error(f"la función '{node.name}' debe retornar en todos los caminos", node)


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

        if isinstance(node.target, Identifier):
            t1 = self.lookup(node.target.name, node)

            if isinstance(t1, FunctionType):
                self.error("no se puede asignar a una función", node)
                return

        elif isinstance(node.target, ArrayAccess):
            t1 = self.visit(node.target)

        else:
            self.error("lado izquierdo inválido en asignación", node)
            return

        t2 = self.visit(node.value)

        if t2 == VoidType:
            self.error("no se puede usar void en expresión", node)
            return

        if t1 is not None and t2 is not None and t1 != t2:
            self.error(f"no se puede asignar {t2} a {t1}", node)

    def visit_Return(self, node):

        if not self.current_function:
            self.error("return fuera de función", node)
            return

        expected = self.current_function.return_type

        # return expr;
        if node.value is not None:
            val_type = self.visit(node.value)

            if val_type == VoidType:
                self.error("función void no puede retornarse como valor", node)
                return

            if expected == VoidType:
                self.error("no se debe retornar valor en función void", node)

            elif val_type is not None and val_type != expected:
                self.error(
                    f"tipo de retorno incorrecto. return {val_type} en funcion tipo {expected}",
                    node
                )

        # return;
        else:
            if expected != VoidType:
                self.error("falta valor en return", node)

    def visit_Print(self, node):
        for a in node.args:
            self.visit(a)

    def visit_If(self, node):
        cond = self.visit(node.cond)

        if cond == VoidType:
            self.error("if no puede usar void como condición", node)

        elif cond is not None and cond != BooleanType:
            self.error("la condición del if debe ser boolean", node)

        self.visit(node.then_body)

        if node.else_body:
            self.visit(node.else_body)

    def visit_While(self, node):
        cond = self.visit(node.cond)

        if cond == VoidType:
            self.error("while no puede usar void como condición", node)

        elif cond is not None and cond != BooleanType:
            self.error("la condición del while debe ser boolean", node)

        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1

    def visit_For(self, node):
        self.push()

        if node.init is not None:
            self.visit(node.init)

        cond = BooleanType

        if node.cond:
            cond = self.visit(node.cond)

        if cond == VoidType:
            self.error("for no puede usar void como condición", node)

        elif cond is not None and cond != BooleanType:
            self.error("la condición del for debe ser boolean", node)

        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1    

        if node.update is not None:
            self.visit(node.update)

        self.pop()




    def visit_Break(self, node):
        if self.loop_depth == 0:
            self.error("break fuera de loop", node)

    def visit_Continue(self, node):
        if self.loop_depth == 0:
            self.error("continue fuera de loop", node)



            
    # ================= EXPRESIONES =================

    def visit_Number(self, node):
        node.type = IntegerType
        return node.type


    def visit_Float(self, node):
        node.type = FloatType
        return node.type

    def visit_String(self, node):
        node.type = StringType
        return node.type

    def visit_Char(self, node):
        node.type = CharType
        return node.type

    def visit_Boolean(self, node):
        node.type = BooleanType
        return node.type

    def visit_Identifier(self, node):

        t = self.lookup(node.name, node)

        if isinstance(t, FunctionType):
            self.error(f"'{node.name}' es una función y no una variable", node)
            return None

        node.type = t
        return t
    # ================= ARRAYS =================

    def visit_ArrayLiteral(self, node):


        
        if not node.elements:
            node.type = ArrayType(VoidType)
            return node.type

        first_type = self.visit(node.elements[0])
        error_done = False

        for elem in node.elements[1:]:
            t = self.visit(elem)
            if t != first_type and not error_done:
                self.error(f"array literal mezcla tipos: {first_type} y {t}", node)
                error_done = True

        node.type = ArrayType(first_type)
        return node.type    

    def visit_ArrayAccess(self, node):
        arr = self.visit(node.array)
        idx = self.visit(node.index)

        if idx is not None and idx != IntegerType:
            self.error("el índice debe ser integer", node)

        if not isinstance(arr, ArrayType):
            self.error("acceso a algo que no es array", node)
            return None

        node.type = arr.base
        return node.type

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


    def must_return(self, stmts):
        if not stmts:
            return False

        last = stmts[-1]

        if isinstance(last, Return):
            return True

        if isinstance(last, If):
            if last.else_body:
                return self.must_return(last.then_body) and self.must_return(last.else_body)

        if isinstance(last, Block):
            return self.must_return(last.statements)

        return False



    def visit_Call(self, node):
        func = self.lookup(node.name, node)

        if func is None:
            self.error(f"símbolo '{node.name}' no definido", node)
            return None

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

            if t == VoidType:
                self.error("void no puede pasarse como argumento", node)

            elif t != expected:
                self.error(f"argumento de tipo {t} no coincide con {expected}", node)



        node.type = func.return_type
        return node.type
        

    # ================= OPERADORES =================

    def visit_BinaryOp(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)

        if l is None or r is None:
            return None


        if node.op == "/":

            if isinstance(node.right, Number):
                if node.right.value == 0:
                    self.error("división entre cero", node)

            elif isinstance(node.right, Float):
                if node.right.value == 0.0:
                    self.error("división entre cero", node)

            elif isinstance(node.right, Float) and node.right.value == 0.0:
                self.error("división entre cero", node)


        if l == VoidType or r == VoidType:
            self.error("void no puede usarse en operaciones", node)
            return None

        result = check_binop(node.op, l, r)

        if result is None:
            self.error(f"operación inválida: {l} {node.op} {r}", node)
            return None

        node.type = result
        return node.type

    def visit_UnaryOp(self, node):
        t = self.visit(node.operand)

        if t == VoidType:
            self.error("void no puede usarse en operación unaria", node)
            return None

        if node.op == "-" and t in (IntegerType, FloatType):
            node.type = t
            return node.type

        if node.op in ("!", "not") and t == BooleanType:
            node.type = BooleanType
            return node.type

        self.error("operador unario inválido", node)
        return None
