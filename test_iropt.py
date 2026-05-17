from iropt import optimize_ir_o1, optimize_ir_o2
from ircode import IRProgram, IRFunction


def optimize(insts, level):

    fn = IRFunction(
        name="main",
        params=[],
        return_type=None,
        instructions=insts
    )

    ir = IRProgram([], [fn])

    if level == 1:
        ir = optimize_ir_o1(ir)

    elif level == 2:
        ir = optimize_ir_o2(ir)

    return ir.functions[0].instructions


def test_add_fold():

    insts = [
        ("MOVI", 2, "R1"),
        ("MOVI", 3, "R2"),
        ("ADDI", "R1", "R2", "R3"),
    ]

    out = optimize(insts, 1)

    assert ("MOVI", 5, "R3") in out


def test_dead_temp():

    insts = [
        ("MOVI", 99, "R1"),
        ("MOVI", 5, "R2"),
        ("PRINTI", "R2"),
    ]

    out = optimize(insts, 2)

    assert ("MOVI", 99, "R1") not in out


def test_constant_branch():

    insts = [
        ("MOVI", 1, "R1"),
        ("CBRANCH", "R1", "L1", "L2"),
    ]

    out = optimize(insts, 1)

    assert ("BRANCH", "L1") in out


def test_unreachable():

    insts = [
        ("BRANCH", "L1"),
        ("MOVI", 99, "R1"),
        ("LABEL", "L1"),
    ]

    out = optimize(insts, 1)

    assert ("MOVI", 99, "R1") not in out