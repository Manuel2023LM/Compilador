# iropt.py
# ---------------------------------------------------------
# O2 Optimizer sobre IR para B-Minor
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
# astopt (O1)
#   ↓
# ircode
#   ↓
# iropt (O2)   ← ESTE ARCHIVO
#   ↓
# irinterp
#
# ---------------------------------------------------------


# =========================================================
# UTILIDADES
# =========================================================

from rich import print
from rich.table import Table



def is_register(x):
    return isinstance(x, str) and x.startswith("R")


def is_number(x):
    return (
        isinstance(x, (int, float))
        and not isinstance(x, bool)
    )

def replace_operand(value, constants):
    """
    Reemplaza registros conocidos por constantes.
    """

    if is_register(value) and value in constants:
        return constants[value]

    return value


# =========================================================
# PEEPHOLE OPTIMIZATION
# =========================================================

def peephole(instrs):

    optimized = []

    for instr in instrs:

        op = instr[0]

        # -------------------------------------------------
        # ELIMINAR MOVI R1, R1
        # -------------------------------------------------

        if op == "MOVI":

            src = instr[1]
            dst = instr[2]

            if src == dst:
                continue

        # -------------------------------------------------
        # ADDI Rx, 0 -> MOVI Rx
        # -------------------------------------------------

        elif op in ("ADDI", "ADDF"):

            a = instr[1]
            b = instr[2]
            target = instr[3]

            if b == 0:
                movop = "MOVF" if op.endswith("F") else "MOVI"
                optimized.append((movop, a, target))    
                continue

            if a == 0:
                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, b, target))
                continue

        # -------------------------------------------------
        # SUBI Rx, 0 -> MOVI Rx
        # -------------------------------------------------

        elif op in ("SUBI", "SUBF"):

            a = instr[1]
            b = instr[2]
            target = instr[3]

            if b == 0:

                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, a, target))
                continue

        # -------------------------------------------------
        # MULI Rx, 1 -> MOVI Rx
        # -------------------------------------------------

        elif op in ("MULI", "MULF"):

            a = instr[1]
            b = instr[2]
            target = instr[3]

            if b == 1:

                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, a, target))
                continue

            if a == 1:

                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, b, target))
                continue
            # x * 0 -> 0
            if a == 0 or b == 0:
                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, 0, target))
                continue

        # -------------------------------------------------
        # DIVI Rx, 1 -> MOVI Rx
        # -------------------------------------------------

        elif op in ("DIVI", "DIVF"):

            a = instr[1]
            b = instr[2]
            target = instr[3]

            if b == 1:

                movop = "MOVF" if op.endswith("F") else "MOVI"

                optimized.append((movop, a, target))
                continue

        optimized.append(instr)

    return optimized


# =========================================================
# CONSTANT PROPAGATION
# =========================================================

def constant_propagation(instrs):

    constants = {}

    optimized = []

    for instr in instrs:

        op = instr[0]

        # -------------------------------------------------
        # MOVI constante
        # -------------------------------------------------

        if op in ("MOVI", "MOVF", "MOVB"):

            value = instr[1]
            target = instr[2]

            value = replace_operand(value, constants)

            optimized.append((op, value, target))

            if is_number(value):
                constants[target] = value
            else:
                constants.pop(target, None)

            continue

        # -------------------------------------------------
        # OPERACIONES BINARIAS
        # -------------------------------------------------

        elif op in (
            "ADDI", "SUBI", "MULI", "DIVI",
            "ADDF", "SUBF", "MULF", "DIVF",
            "AND", "OR", "XOR"
        ):

            a = replace_operand(instr[1], constants)
            b = replace_operand(instr[2], constants)
            target = instr[3]

            # ---------------------------------------------
            # CONSTANT FOLDING SOBRE IR
            # ---------------------------------------------

            if is_number(a) and is_number(b):

                try:

                    result = None

                    if op.startswith("ADD"):
                        result = a + b

                    elif op.startswith("SUB"):
                        result = a - b

                    elif op.startswith("MUL"):
                        result = a * b

                    elif op.startswith("DIV") and b != 0:

                        if op.endswith("I"):
                            result = a // b
                        else:
                            result = a / b

                    elif op == "AND":
                        result = a & b

                    elif op == "OR":
                        result = a | b

                    elif op == "XOR":
                        result = a ^ b

                    if result is not None:

                        movop = "MOVF" if op.endswith("F") else "MOVI"

                        optimized.append((movop, result, target))
                        constants[target] = result
                        continue

                except:
                    pass

            optimized.append((op, a, b, target))

            constants.pop(target, None)

            continue

        # -------------------------------------------------
        # COMPARACIONES
        # -------------------------------------------------

        elif op in ("CMPI", "CMPF", "CMPB"):

            cmpop = instr[1]

            a = replace_operand(instr[2], constants)
            b = replace_operand(instr[3], constants)

            target = instr[4]

            if is_number(a) and is_number(b):

                result = False

                if cmpop == "==":
                    result = a == b

                elif cmpop == "!=":
                    result = a != b

                elif cmpop == "<":
                    result = a < b

                elif cmpop == "<=":
                    result = a <= b

                elif cmpop == ">":
                    result = a > b

                elif cmpop == ">=":
                    result = a >= b

                optimized.append(("MOVI", int(result), target))

                constants[target] = int(result)

                continue

            optimized.append((op, cmpop, a, b, target))

            constants.pop(target, None)

            continue

        # -------------------------------------------------
        # LOAD invalida constantes
        # -------------------------------------------------

        elif op.startswith("LOAD"):

            target = instr[-1]

            optimized.append(instr)

            constants.pop(target, None)

            continue

        # -------------------------------------------------
        # STORE invalida
        # -------------------------------------------------

        elif op.startswith("STORE"):

            optimized.append(instr)

            continue

        # -------------------------------------------------
        # CALL invalida target
        # -------------------------------------------------

        elif op == "CALL":

            target = instr[-1]

            optimized.append(instr)

            constants.pop(target, None)

            continue


        # -------------------------------------------------
        # CBRANCH constante
        # -------------------------------------------------

        elif op == "CBRANCH":

            test = replace_operand(instr[1], constants)

            true_label = instr[2]
            false_label = instr[3]

            # si test es constante
            if is_number(test):

                if test != 0:
                    optimized.append(("BRANCH", true_label))
                else:
                    optimized.append(("BRANCH", false_label))

                continue

            optimized.append(
                ("CBRANCH", test, true_label, false_label)
            )

            continue






        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        optimized.append(instr)

    return optimized

# =========================================================
# UNREACHABLE CODE ELIMINATION
# =========================================================

def remove_unreachable_code(instrs):

    optimized = []

    unreachable = False

    for instr in instrs:

        op = instr[0]

        # un LABEL revive el código
        if op == "LABEL":

            unreachable = False
            optimized.append(instr)
            continue

        # si estamos en código muerto, ignorar
        if unreachable:
            continue

        optimized.append(instr)

        # después de BRANCH o RET
        if op in ("BRANCH", "RET"):

            unreachable = True

    return optimized





# =========================================================
# REMOVE USELESS BRANCHES
# =========================================================

def remove_useless_branches(instrs):

    optimized = []

    i = 0

    while i < len(instrs):

        instr = instrs[i]

        # BRANCH L1
        if (
            instr[0] == "BRANCH"
            and i + 1 < len(instrs)
        ):

            next_instr = instrs[i + 1]

            # LABEL L1
            if (
                next_instr[0] == "LABEL"
                and next_instr[1] == instr[1]
            ):

                i += 1
                continue

        optimized.append(instr)

        i += 1

    return optimized






# =========================================================
# DEAD CODE ELIMINATION
# =========================================================

# =========================================================
# DEAD TEMP ELIMINATION (REAL O2)
# =========================================================

def is_pure_instruction(op):

    return (
        op in (
            "MOVI", "MOVF", "MOVB",
            "ADDR",

            "ADDI", "SUBI", "MULI", "DIVI",
            "ADDF", "SUBF", "MULF", "DIVF",

            "CMPI", "CMPF", "CMPB",

            "AND", "OR", "XOR"
        )

        or op.startswith("LOAD")
    )


def get_defined_register(instr):

    op = instr[0]

    # instrucciones de 3 operandos
    if op in (
        "MOVI", "MOVF", "MOVB",
        "LOADI", "LOADF", "LOADB", "LOADS"
    ):

        target = instr[-1]

        if is_register(target):
            return target

    # instrucciones de 4 operandos
    elif op in (
        "ADDR",
        "ADDI", "SUBI", "MULI", "DIVI",
        "ADDF", "SUBF", "MULF", "DIVF",
        "AND", "OR", "XOR"
    ):

    


        target = instr[-1]

        if is_register(target):
            return target

    # comparaciones
    elif op in ("CMPI", "CMPF", "CMPB"):

        target = instr[-1]

        if is_register(target):
            return target

    return None

    

def get_used_registers(instr):

    used = set()

    for value in instr[1:]:

        if is_register(value):
            used.add(value)

    return used


def dead_code_elimination(instrs):

    used = set()

    optimized_reversed = []

    # recorrido HACIA ATRAS
    for instr in reversed(instrs):

        op = instr[0]

        dst = get_defined_register(instr)

        args = get_used_registers(instr)

        # ---------------------------------------------
        # eliminar temporal muerto
        # ---------------------------------------------

        if (
            dst is not None
            and dst not in used
            and is_pure_instruction(op)
        ):

            continue

        # ---------------------------------------------
        # actualizar usados
        # ---------------------------------------------

        if dst is not None:

            used.discard(dst)

        used.update(args)

        optimized_reversed.append(instr)

    optimized_reversed.reverse()

    return optimized_reversed

# =========================================================
# REDUNDANT LOAD/STORE ELIMINATION
# =========================================================

def remove_redundant_load_store(instrs):

    optimized = []

    i = 0

    while i < len(instrs):

        # patrón:
        #
        # LOADI x, R1
        # STOREI R1, y
        #
        # =>
        #
        # STOREI x, y

        if i + 1 < len(instrs):

            a = instrs[i]
            b = instrs[i + 1]

            if (
                a[0].startswith("LOAD")
                and b[0].startswith("STORE")
            ):

                load_src = a[1]
                reg = a[2]

                store_reg = b[1]
                store_dst = b[2]

                if reg == store_reg:

                    suffix = a[0][-1]

                    storeop = f"STORE{suffix}"

                    optimized.append(
                        (storeop, load_src, store_dst)
                    )

                    i += 2
                    continue

        optimized.append(instrs[i])

        i += 1

    return optimized


# =========================================================
# DEAD STORE ELIMINATION
# =========================================================

def remove_dead_stores(instrs):

    used_vars = set()

    # buscar variables realmente usadas
    for instr in instrs:

        op = instr[0]

        if op.startswith("LOAD"):

            used_vars.add(instr[1])

    optimized = []

    for instr in instrs:

        op = instr[0]

        # STOREI R1, x
        if op.startswith("STORE"):

            varname = instr[2]

            if isinstance(varname, str):

                if varname not in used_vars:
                    continue

        optimized.append(instr)

    return optimized

# =========================================================
# DEAD ALLOCATION ELIMINATION
# =========================================================

def remove_dead_alloc(instrs):

    used_vars = set()

    # buscar variables usadas
    for instr in instrs:

        op = instr[0]

        if op.startswith("LOAD"):

            used_vars.add(instr[1])

    

    optimized = []

    for instr in instrs:

        op = instr[0]

        if op.startswith("ALLOC"):

            varname = instr[1]

            if varname not in used_vars:
                continue

        optimized.append(instr)

    return optimized


# =========================================================
# OPTIMIZAR FUNCION
# =========================================================

def optimize_function(fn, verbose=False):

    old_len = len(fn.instructions)

    instrs = fn.instructions

    # -----------------------------------------
    # O1
    # -----------------------------------------

    instrs = constant_propagation(instrs)

    instrs = peephole(instrs)

    instrs = remove_unreachable_code(instrs)

    instrs = remove_useless_branches(instrs)

    # -----------------------------------------
    # O2
    # -----------------------------------------

    instrs = remove_redundant_load_store(instrs)

    instrs = dead_code_elimination(instrs)

    instrs = remove_dead_stores(instrs)

    instrs = remove_dead_alloc(instrs)

    fn.instructions = instrs

    if verbose:

        new_len = len(instrs)

        if old_len > 0:
            reduction = 100 * (old_len - new_len) / old_len
        else:
            reduction = 0

        table = Table(
            title="[bold cyan]Optimizacion O2[/bold cyan]",
            show_lines=True,
            border_style="bright_blue"
        )

        table.add_column("Funcion", style="cyan")
        table.add_column("Antes", style="yellow")
        table.add_column("Despues", style="green")
        table.add_column("Reducidas", style="red")
        table.add_column("Reduccion", style="magenta")

        table.add_row(
            fn.name,
            str(old_len),
            str(new_len),
            str(old_len - new_len),
            f"{reduction:.1f}%"
        )

        print(table)

    return fn
# =========================================================
# API PUBLICA
# =========================================================

def optimize_ir_o2(ir, verbose=False):

    # ir es IRProgram
    for fn in ir.functions:

        optimize_function(fn, verbose=verbose)

    return ir


# =========================================================
# O1
# =========================================================

# =========================================================
# O1
# =========================================================

def optimize_ir_o1(ir, verbose=False):

    for fn in ir.functions:

        instrs = fn.instructions

        instrs = constant_propagation(instrs)

        instrs = peephole(instrs)

        instrs = remove_unreachable_code(instrs)

        instrs = remove_useless_branches(instrs)

        fn.instructions = instrs

        if verbose:

            print(
                f"[O1] {fn.name}: "
                f"{len(instrs)} instrucciones"
            )

    return ir