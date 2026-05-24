import re
from model import *

# ================= TOKENIZER =================

def tokenize(src):
    token_spec = [
        ("COMMENT1", r'//.*'),
        ("COMMENT2", r'/\*[\s\S]*?\*/'),
        ("INC", r'\+\+'),
        ("DEC", r'--'),
        ("OP", r'\+=|-=|\*=|/=|==|!=|<=|>=|<|>|\+|-|\*|/|\^|=|!|%'),
        ("LOGIC", r'&&|\|\|'),
        ("NUMBER", r'\d+(\.\d+)?'),
        ("STRING", r'"[^"]*"'),
        ("CHAR", r"'(\\.|[^\\'])+'"),
        ("ID", r'[A-Za-z_][A-Za-z0-9_]*'),
        ("SYM", r'[{}()\[\],;:]'),
        ("SKIP", r'[ \t]+'),
        ("NEWLINE", r'\n'),
        ("MISMATCH", r'.'),
    ]

    tok_regex = "|".join(f"(?P<{n}>{r})" for n, r in token_spec)

    tokens = []
    line = 1

    for m in re.finditer(tok_regex, src):
        kind = m.lastgroup
        value = m.group()

        if kind == "NEWLINE":
            line += 1
            continue

        if kind in ("SKIP", "COMMENT1", "COMMENT2"):
            continue


                
        if kind == "MISMATCH":
                    raise SyntaxError(f"Caracter ilegal '{value}' en línea {line}")

        tokens.append((value, line))

        
    return tokens


# ================= PARSER =================

def parse(source):
    tokens = tokenize(source)
    pos = 0
    errors = []

    def peek():
        return tokens[pos][0] if pos < len(tokens) else None

    def line():
        return tokens[pos][1] if pos < len(tokens) else None

    def peek2():
        return tokens[pos+1][0] if pos+1 < len(tokens) else None

    def peek3():
        return tokens[pos+2][0] if pos+2 < len(tokens) else None
    


    

    def syntax_error(msg):
        errors.append(f"[Línea {line()}] {msg}")

    def synchronize():

        nonlocal pos

        sync_tokens = {
            ";",
            "}",
            "{",
            "if",
            "else",
            "while",
            "for",
            "return",
            "print",
            "break",
            "continue"
        }

        while pos < len(tokens):

            tok = peek()

            if tok in sync_tokens:

                # consumir ; para no quedar pegado
                if tok == ";":
                    pos += 1

                return

            pos += 1


    def consume(expected=None):

        nonlocal pos

        tok = tokens[pos] if pos < len(tokens) else None

        if tok is None:
            syntax_error("EOF inesperado")
            return ("ERROR", line())

        value, ln = tok

        if expected and value != expected:

            syntax_error(
                f"Se esperaba '{expected}' pero se encontró '{value}'"
            )
            pos += 1
            synchronize()

            return ("ERROR", ln)

        pos += 1
        return value, ln

    # ================= TYPES =================

    def parse_type():
        if peek() == "array":
            consume("array")
            consume("[")
            size = None
            if peek() != "]":
                size = parse_expr()
            consume("]")
            base = parse_type()
            return ArrayType(base, size)

        tok = peek()

        types = {
            "integer": IntegerType,
            "float": FloatType,
            "boolean": BooleanType,
            "string": StringType,
            "char": CharType,
            "void": VoidType
        }

        if tok in types:
            consume()
            return types[tok]

        # 🔥 CLAVE: no consumir si no es tipo válido
        syntax_error(f"Tipo desconocido: {tok} en la línea {line()}")
        return IntegerType

    # ================= EXPRESSIONS =================

    def parse_primary():
        tok = peek()

        if tok == "(":
            consume("(")
            e = parse_expr()
            consume(")")
            return e

        if tok in ("true", "false"):
            v, ln = consume()
            n = Boolean(v == "true")
            n.line = ln
            return n

        if re.match(r'^\d+\.\d+$', tok):
            v, ln = consume()
            n = Float(float(v))
            n.line = ln
            return n

        if tok and tok.isdigit():
            v, ln = consume()
            n = Number(int(v))
            n.line = ln
            return n

        if tok and tok.startswith('"'):
            v, ln = consume()
            n = String(v)
            n.line = ln
            return n

        if tok and tok.startswith("'"):
            v, ln = consume()
            n = Char(v)
            n.line = ln
            return n

        if tok == "{":
            _, ln = consume("{")
            elems = []

            while peek() not in (None, "}"):
                elems.append(parse_expr())
                if peek() == ",":
                    consume(",")

            consume("}")
            n = ArrayLiteral(elems)
            n.line = ln
            return n

        if tok and tok.isidentifier():
            name, ln = consume()

            # call
            if peek() == "(":
                consume("(")
                args = []
                while peek() != ")":
                    args.append(parse_expr())
                    if peek() == ",":
                        consume(",")
                consume(")")
                n = Call(name, args)
                n.line = ln
                return n

            n = Identifier(name)
            n.line = ln

            while peek() == "[":
                consume("[")
                idx = parse_expr()
                consume("]")
                n = ArrayAccess(n, idx)
                n.line = ln

            return n

        syntax_error(f"Token inesperado '{tok}' en la línea {line()}")

        _, ln = consume()

        n = Number(0)
        n.line = ln

        return n

    def parse_unary():
        if peek() in ("-", "!", "not"):
            op, ln = consume()
            n = UnaryOp(op, parse_unary())
            n.line = ln
            return n
        return parse_primary()

    def bin_layer(parse_next, ops):
        def f():
            node = parse_next()
            while peek() in ops:
                op, ln = consume()
                node = BinaryOp(op, node, parse_next())
                node.line = ln
            return node
        return f

    def parse_power():
        node = parse_unary()
        if peek() == "^":
            op, ln = consume()
            node = BinaryOp(op, node, parse_power())
            node.line = ln
        return node

    parse_mul = bin_layer(parse_power, ("*", "/", "%"))
    parse_add = bin_layer(parse_mul, ("+", "-"))
    parse_rel = bin_layer(parse_add, ("<", ">", "<=", ">="))
    parse_eq  = bin_layer(parse_rel, ("==", "!="))
    parse_logic = bin_layer(parse_eq, ("&&", "||", "and", "or"))

    def parse_expr():
        return parse_logic()

    # ================= STATEMENTS =================






    def parse_block():
        _, ln = consume("{")
        stmts = []

        while peek() is not None and peek() != "}":
            stmt = parse_statement()
            if stmt is not None:
                stmts.append(stmt)

        consume("}")
        b = Block(stmts)
        b.line = ln
        return b


    def parse_vardecl(require_semicolon=True):
        name, ln = consume()

        if peek() != ":":
            syntax_error(f"Se esperaba ':' después de '{name}' en la línea {ln}")

        consume(":")
        t = parse_type()

        val = None
        if peek() == "=":
            consume("=")
            val = parse_expr()

        if require_semicolon and peek() != ";":
            syntax_error("faltó ';' en declaración")
            synchronize()
        elif require_semicolon:
            consume(";")

        n = VarDecl(name, t, val)
        n.line = ln
        return n

    def parse_assignment():
        target = parse_primary()

        # =  +=  -=
        if peek() in ("=", "+=", "-=", "*=", "/="):

            op, ln = consume()

            val = parse_expr()
            consume(";")

            if op == "=":
                n = Assignment(target, val)

            elif op == "+=":
                binop = BinaryOp("+", target, val)
                binop.line = ln
                n = Assignment(target, binop)

            elif op == "-=":
                binop = BinaryOp("-", target, val)
                binop.line = ln
                n = Assignment(target, binop)

            elif op == "*=":
                binop = BinaryOp("*", target, val)
                binop.line = ln
                n = Assignment(target, binop)

            elif op == "/=":
                binop = BinaryOp("/", target, val)
                binop.line = ln
                n = Assignment(target, binop)

            n.line = ln
            return n

        # ++
        if peek() == "++":
            _, ln = consume("++")
            consume(";")

            one = Number(1)
            one.line = ln

            binop = BinaryOp("+", target, one)
            binop.line = ln

            n = Assignment(target, binop)
            n.line = ln
            return n

        # --
        if peek() == "--":
            _, ln = consume("--")
            consume(";")

            one = Number(1)
            one.line = ln

            binop = BinaryOp("-", target, one)
            binop.line = ln

            n = Assignment(target, binop)
            n.line = ln
            return n

        syntax_error(f"Asignación inválida en la línea {line()}")
        synchronize()
        return None


    def parse_if():

        _, ln = consume("if")
        consume("(")
        cond = parse_expr()
        consume(")")

        # THEN
        if peek() == "{":
            then_b = parse_block().statements
        else:
            then_b = [parse_statement()]

        # ELSE
        else_b = None

        if peek() == "else":
            consume("else")

            if peek() == "if":
                else_b = [parse_if()]

            elif peek() == "{":
                else_b = parse_block().statements

            else:
                else_b = [parse_statement()]

        n = If(cond, then_b, else_b)
        n.line = ln
        return n

    def parse_while():
        
        _, ln = consume("while")
        consume("(")
        cond = parse_expr()
        consume(")")

        if peek() == "{":
            body = parse_block().statements
        else:
            body = [parse_statement()]

        n = While(cond, body)
        n.line = ln
        return n

    def parse_for():
        _, ln = consume("for")
        consume("(")

        init = None
        if peek() != ";":
            if peek2() == ":":
                init = parse_vardecl(require_semicolon=False)
            else:
                target = parse_primary()
                consume("=")
                val = parse_expr()
                init = Assignment(target, val)
                init.line = ln
        consume(";")

        cond = None

        if peek() != ";":
            cond = parse_expr()

        consume(";")

        
        update = None
        if peek() != ")":
            target = parse_primary()

            if peek() in ("=", "+=", "-=", "*=", "/="):

                op = consume()[0]
                val = parse_expr()

                if op == "=":
                    update = Assignment(target, val)

                elif op == "+=":
                    binop = BinaryOp("+", target, val)
                    binop.line = ln

                    update = Assignment(target, binop)

                elif op == "-=":
                    binop = BinaryOp("-", target, val)
                    binop.line = ln
                    update = Assignment(target, binop)
                elif op == "*=":
                    binop = BinaryOp("*", target, val)
                    binop.line = ln
                    update = Assignment(target, binop)

                elif op == "/=":
                    binop = BinaryOp("/", target, val)
                    binop.line = ln
                    update = Assignment(target, binop)    

                    update = Assignment(target, binop)

                update.line = ln

            elif peek() == "++":
                consume("++")
                one = Number(1)
                one.line = ln
                one = Number(1)
                one.line = ln

                binop = BinaryOp("+", target, one)
                binop.line = ln

                update = Assignment(target, binop)
                update.line = ln


            elif peek() == "--":
                consume("--")
                one = Number(1)
                one.line = ln

                binop = BinaryOp("-", target, one)
                binop.line = ln

                update = Assignment(target, binop)
                update.line = ln

            elif peek() == "+=":
                consume("+=")
                val = parse_expr()

                binop = BinaryOp("+", target, val)
                binop.line = ln

                update = Assignment(target, binop)
                update.line = ln   

            elif peek() == "-=":
                consume("-=")
                val = parse_expr()

                binop = BinaryOp("-", target, val)
                binop.line = ln

                update = Assignment(target, binop)
                update.line = ln
            

        consume(")")

        # 🔥 FLEXIBLE
        if peek() == "{":
            body = parse_block().statements
        else:
            body = [parse_statement()]

        n = For(init, cond, update, body)
        n.line = ln
        return n

    
    def parse_return():
        _, ln = consume("return")
        
        val = None
        if peek() != ";":
            try:
                val = parse_expr()
            except SyntaxError:
                syntax_error(f"línea {ln} Expresión inválida en return")
        
        if peek() != ";":
            tok = peek()
            syntax_error(f"línea {ln} Se esperaba ';' después del return")
        
        consume(";")
        
        n = Return(val)
        n.line = ln
        return n

    def parse_print():
        _, ln = consume("print")
        args = []
        while peek() is not None and peek() != ";":
            args.append(parse_expr())
            if peek() == ",":
                consume(",")
        consume(";")
        n = Print(args)
        n.line = ln
        return n


    def parse_break():
        _, ln = consume("break")
        consume(";")

        n = Break()
        n.line = ln
        return n



    def parse_continue():
        _, ln = consume("continue")
        consume(";")

        n = Continue()
        n.line = ln
        return n

    def starts_assignment():
        if not (peek() and peek().isidentifier()):
            return False

        depth = 0
        i = pos + 1
        assignment_ops = {"=", "+=", "-=", "*=", "/=", "++", "--"}

        while i < len(tokens):
            tok = tokens[i][0]

            if tok in (";", None):
                return False

            if tok in ("[", "("):
                depth += 1
            elif tok in ("]", ")"):
                depth -= 1
            elif depth == 0 and tok in assignment_ops:
                return True

            i += 1

        return False


    def parse_statement():

        try:

            tok = peek()

            if tok == ";":
                consume(";")
                return None

            if tok == "{":
                return parse_block()

            if tok == "if":
                return parse_if()

            if tok == "while":
                return parse_while()

            if tok == "for":
                return parse_for()

            if tok == "return":
                return parse_return()

            if tok == "print":
                return parse_print()

            if tok == "break":
                return parse_break()

            if tok == "continue":
                return parse_continue()

            if peek2() == ":" and peek3() != "function":
                return parse_vardecl()

            if tok in ("integer", "float", "boolean", "string", "char"):
                syntax_error("Declaración inválida")
                synchronize()
                return None

            if starts_assignment():
                return parse_assignment()

            if tok and tok.isidentifier() and peek2() == "(":
                expr = parse_expr()
                consume(";")
                return expr

            expr = parse_expr()
            consume(";")
            return expr

        except SyntaxError as e:

            syntax_error(str(e))

            synchronize()

            return None






    # ================= FUNCTION =================

    def parse_function():
        name, ln = consume()
        consume(":")
        consume("function")

        ret = parse_type()

        consume("(")
        params = []
        while peek() not in (None, ")"):
            pname, _ = consume()
            consume(":")
            ptype = parse_type()
            params.append(Param(pname, ptype))
            if peek() == ",":
                consume(",")
        consume(")")

        if peek() == ";":
            consume(";")
            n = Function(name, ret, params, Block([]))
            n.line = ln
            return n

        consume("=")
        body = parse_block()

        n = Function(name, ret, params, body)
        n.line = ln
        return n

    # ================= PROGRAM =================

    decls = []

    while peek():

        try:

            if peek2() == ":" and peek3() == "function":

                node = parse_function()

            else:

                node = parse_vardecl()

            if node:
                decls.append(node)

        except SyntaxError as e:

            syntax_error(str(e))

            synchronize()

    program = Program(decls)

    program.errors = errors

    return program
