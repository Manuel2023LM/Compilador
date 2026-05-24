import sys
import os

from rich import print
from lexer import tokenize
from parser import parse
from checker import Checker
from ircode import IRCodeGen
from astopt import optimize_ast_o1
from iropt import optimize_ir_o1, optimize_ir_o2
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.console import Console
from rich.tree import Tree
from rich.align import Align

console = Console()
import time


def print_banner():

    print()

    console.print(
        Panel.fit(
            "[bold bright_cyan]**B-MINOR COMPILADOR**[/bold bright_cyan]\n"
            "[yellow] **Lexer • Parser • Checker • IRcode • Optimizer • Irinterpreter**[/yellow]",
            border_style="bright_magenta",
            padding=(1, 8)
        ),
        justify="center"
    )

    print()

def format_instruction(instr):

    op = instr[0]

    pieces = [f"[bold bright_cyan]{op:<10}[/bold bright_cyan]"]

    for x in instr[1:]:

        # registros
        if isinstance(x, str) and x.startswith("R"):
            pieces.append(f"[bold bright_yellow]{x}[/bold bright_yellow]")

        # labels
        elif isinstance(x, str) and x.startswith("L"):
            pieces.append(f"[bold bright_green]{x}[/bold bright_green]")

        # constantes
        elif isinstance(x, (int, float)):
            pieces.append(f"[bold bright_magenta]{x}[/bold bright_magenta]")

        else:
            pieces.append(str(x))

    return "  " + ", ".join(pieces)


def compare_optimizations(
    path,
    show_ast=False,
    show_ir=False,
    quiet=False
):

    print_banner()

    print(
        Panel.fit(
            f"[bold yellow]{path}[/bold yellow]",
            title="Archivo",
            border_style="yellow"
        )
    )

    for level in [0, 1, 2]:

        print("\n")

        print(
            Rule(
                f"[bold cyan]OPTIMIZACION O{level}[/bold cyan]"
            )
        )

        run_file(
            path,
            opt_level=level,
            run_interpreter=True,
            show_ast=show_ast,
            show_ir=show_ir,
            quiet=quiet
        )

# ================= INTERPRETER =================

try:
    from irinterp import IRInterpreter
    HAS_INTERPRETER = True
except:
    HAS_INTERPRETER = False


# ================= LEER ARCHIVO =================

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()
# ================= OPT LEVEL =================

def parse_opt_level(argv):

    level = 0

    i = 0

    while i < len(argv):

        arg = argv[i]

        # -O2
        if arg.startswith("-O") and len(arg) > 2:

            try:
                level = int(arg[2:])
            except:
                pass

        # -O 2
        elif arg == "-O":

            if i + 1 < len(argv):

                try:
                    level = int(argv[i + 1])
                except:
                    pass

                i += 1

        # -o 2
        elif arg == "-o":

            if i + 1 < len(argv):

                try:
                    level = int(argv[i + 1])
                except:
                    pass

                i += 1

        i += 1

    if level < 0 or level > 4:
        raise ValueError(
            "El nivel de optimización debe estar entre 0 y 4"
        )    

    return level





def build_ast_tree(node, tree):

    if isinstance(node, list):

        list_branch = tree.add(
            "[bold bright_white]LIST[/bold bright_white]"
        )

        for item in node:
            build_ast_tree(item, list_branch)

        return

    if isinstance(node, bool):

        tree.add(
            f"[bold bright_red]{node}[/bold bright_red]"
        )
        return

    if isinstance(node, int):

        tree.add(
            f"[bold bright_magenta]{node}[/bold bright_magenta]"
        )
        return

    if isinstance(node, float):

        tree.add(
            f"[bold bright_magenta]{node}[/bold bright_magenta]"
        )
        return

    if isinstance(node, str):

        tree.add(
            f"[bold bright_green]\"{node}\"[/bold bright_green]"
        )
        return

    if node is None:

        tree.add("[dim italic]None[/dim italic]")
        return

    node_branch = tree.add(
        f"[bold bright_cyan]{type(node).__name__}[/bold bright_cyan]"
    )

    for key, value in vars(node).items():

        child = node_branch.add(
            f"[bold yellow]{key}[/bold yellow]"
        )

        build_ast_tree(value, child)



# ================= EJECUTAR 1 ARCHIVO =================

def run_file(
    path,
    opt_level=0,
    run_interpreter=True,
    show_ast=False,
    show_ir=False,
    quiet=False,
    runtime_errors_ok=False
):
    start = time.perf_counter()
    if not quiet:
        print(
            Rule(
                "[bold bright_blue] COMPILACION [/bold bright_blue]",
                style="dark_magenta"
            )
        )
        
        print(f"\n[bold cyan]>>> Ejecutando:[/bold cyan] [yellow]{path}[/yellow]")
    
    


    try:

        source = read_file(path)

        # ========= PARSER =========
        ast = parse(source)

        if getattr(ast, "errors", None):
            print("\n[bold red]✗ Error de sintaxis[/bold red]")
            for err in ast.errors:
                print(f"[red]error:[/red] {err}")
            return False

        # ========= CHECKER =========
        checker = Checker()
        checker.visit(ast)

        if checker.errors:


            print()

            console.print(
                Panel.fit(
                    "[bold bright_white]SEMANTIC CHECK FAILED[/bold bright_white]",
                    border_style="bright_red",
                    style="on dark_red",
                    padding=(0, 6)
                ),
                justify="center"
            )
            print()
            print("\n[bold red]Errores semánticos:[/bold red]")

            for err in checker.errors:
                print(f"[bold red]• {err}[/bold red]")

            return False
        if not quiet:
            print("[bold bright_green]✓ Semantic check: SUCCESS[/bold bright_green]")

        # ========= AST OPTIMIZATION =========

        if opt_level >= 1:

            ast = optimize_ast_o1(ast, verbose=not quiet)

            print("[bold green]✓ AST Optimization: SUCCESS[/bold green]")

        else:
            if not quiet:
                print("[bold yellow]• O0: AST sin optimizar[/bold yellow]")
        
        if show_ast and not quiet:

            print(
                Rule(
                    "[bold bright_cyan]AST OPTIMIZADO[/bold bright_cyan]",
                    style="bright_magenta"
                )
            )

            tree = Tree(
                "[bold bright_magenta]AST[/bold bright_magenta]",
                guide_style="bright_blue"
            )

            build_ast_tree(ast, tree)

            console.print(tree)

    
        # ========= IR =========
        ir = IRCodeGen.generate(ast)

        if not quiet:
            for fn in ir.functions:

                print(
                    f"\n[bold yellow]Instrucciones:[/bold yellow] "
                    f"{len(fn.instructions)}"
                )

    # ========= IR OPTIMIZATION =========

        # ========= IR OPTIMIZATION =========

        if opt_level >= 2:

            ir = optimize_ir_o2(ir, verbose=not quiet)

        elif opt_level >= 1:

            ir = optimize_ir_o1(ir, verbose=not quiet)

        else:
            if not quiet:
                print("[bold yellow]• O0: IR sin optimizar[/bold yellow]")




        
        if show_ir and not quiet:

            print(
                Rule(
                    "[bold bright_blue]CODIGO INTERMEDIO (IR)[/bold bright_blue]",
                    style="dark_magenta"
                )
            )

            for fn in ir.functions:

                print(
                    Panel.fit(
                        f"[bold bright_green]{fn.name}[/bold bright_green]",
                        title="Funcion",
                        border_style="bright_green"
                    )
                )

                for instr in fn.instructions:
                    print(f"    {format_instruction(instr)}")

            table = Table(
                title="[bold bright_cyan]Resumen IR[/bold bright_cyan]",
                show_lines=True,
                border_style="bright_magenta"
            )

            table.add_column("Funcion", style="bright_cyan")
            table.add_column("Instruciones", style="bright_green")

            for fn in ir.functions:
                table.add_row(
                    fn.name,
                    str(len(fn.instructions))
                )

            print()
            print(table)

        # ========= INTERPRETER =========
        if run_interpreter and HAS_INTERPRETER:

            TRACE = "--trace" in sys.argv

            if TRACE:
                print("\n[bold yellow]=== TRACE MODE ACTIVADO ===[/bold yellow]\n")
            else:
                print()
                
                print(
                    Panel.fit(
                        "[bold bright_green]EJECUTANDO PROGRAMA[/bold bright_green]",
                        border_style="green"
                    )
                )

            interpreter = IRInterpreter(ir, trace=TRACE)
            interpreter.run("main")

        end = time.perf_counter()

        if not quiet:

            print(
                f"\n[bold green]Tiempo total:[/bold green] "
                f"{end-start:.4f}s"
            )

        return True

    except SyntaxError as e:

        print("\n[bold red]✗ Error de sintaxis[/bold red]")
        print(f"[red]error:[/red] {e}")

        return False

    except Exception as e:

        print("\n[bold yellow]⚠ Error de ejecución[/bold yellow]")
        message = str(e)

        if "Division por cero" in message or ("Divisi" in message and "por cero" in message):
            first_line = message.splitlines()[0]
            print(f"[bold yellow]{first_line}[/bold yellow]")
            print("[yellow]Revisa la expresion de division: el valor a la derecha de '/' llego como 0.[/yellow]")
            if "--trace" in sys.argv:
                print(f"[dim]{message}[/dim]")
        else:
            print(f"[yellow]{message} \n operacion invalia para ejecutar [/yellow]")

        # El checker y el IR fueron exitosos
        return True if runtime_errors_ok else False


# ================= EJECUTAR CARPETA =================

def run_folder(
    folder,
    opt_level=0,
    show_ast=False,
    show_ir=False,
    quiet=False
):

    if not os.path.isdir(folder):

        print(f"[bold red]error:[/bold red] '{folder}' no es una carpeta válida")

        return

    files = sorted(os.listdir(folder))

    total = 0
    passed = 0

    is_good = "bad" not in folder.lower()

    mode = "GOOD TESTS" if is_good else "BAD TESTS"

    panel_color = "bright_green" if is_good else "bright_red"

    print()

    console.print(
        Panel.fit(
            f"[bold {panel_color}]{mode}[/bold {panel_color}]\n"
            f"[bright_white]{folder}[/bright_white]",
            border_style=panel_color,
            style="on black",
            padding=(1, 6)
        ),
        justify="center"
    )

    print()

    for f in files:

        if f.startswith("._"):
            continue

        if not f.endswith(".bminor"):
            continue

        total += 1

        path = os.path.join(folder, f)

        ok = run_file(
                path,
                opt_level=opt_level,
                run_interpreter=True,
                show_ast=show_ast,
                show_ir=show_ir,
                quiet=quiet,
                runtime_errors_ok=is_good
            )

        if is_good:
            if ok:
                passed += 1
        else:
            if not ok:
                passed += 1

    print("\n[bold  purple]==========================[/bold  purple]")

    if is_good:

        if passed == total:
            color = "bright_green"

        elif passed > 0:
            color = "bright_yellow"

        else:
            color = "bright_red"

    else:

        # BAD TESTS
        if passed == total:
            color = "bright_red"

        elif passed > 0:
            color = "bright_yellow"

        else:
            color = "bright_green"
    print()

    console.print(
        Panel.fit(
            f"[bold {color}]RESULTADO FINAL[/bold {color}]\n\n"
            f"[bold {color}]{passed}/{total} correctos[/bold {color}]",
            border_style=color,
            style="on black",
            padding=(1, 8)
        ),
        justify="center"
    )

    print("[bold  purple]==========================[/bold  purple]\n")


# ================= MAIN =================

def main():

    if len(sys.argv) < 2:

        print("[bold yellow]Uso:[/bold yellow]")
        print("[cyan]python main.py archivo.bminor[/cyan]")
        print("[cyan]python main.py carpeta/[/cyan]")
        print("\n[bold yellow]Opciones:[/bold yellow]")
        print("[cyan]--ast[/cyan]       Mostrar AST")
        print("[cyan]--ir[/cyan]        Mostrar IR")
        print("[cyan]--compare[/cyan]   Comparar O0/O1/O2")
        print("[cyan]-O0 -O1 -O2[/cyan] Nivel de optimizacion")
        print("[cyan]-q --quiet[/cyan]  Solo ejecutar programa")

        return

    path = sys.argv[1]
    compare_mode = "--compare" in sys.argv
    show_ast = "--ast" in sys.argv
    show_ir = "--ir" in sys.argv
    quiet = "--quiet" in sys.argv or "-q" in sys.argv

    try:
        opt_level = parse_opt_level(sys.argv)

    except ValueError as e:

        print(f"[bold red]error:[/bold red] {e}")
        return

    # ========= CARPETA =========
    if os.path.isdir(path):
        run_folder(
            path,
            opt_level=opt_level,
            show_ast=show_ast,
            show_ir=show_ir,
            quiet=quiet
        )
        return

    # ========= ARCHIVO =========
    print("\n")
    print(f"[bold cyan]Nivel de optimizacion:[/bold cyan] O{opt_level}")


    if os.path.isfile(path):

        if compare_mode:
            compare_optimizations(
                path,
                show_ast=show_ast,
                show_ir=show_ir,
                quiet=quiet
            )
        else:
                if not quiet:
                    print_banner()

                run_file(
                    path,
                    opt_level=opt_level,
                    show_ast=show_ast,
                    show_ir=show_ir,
                    quiet=quiet
                )
        return

    print(f"[bold red]error:[/bold red] ruta inválida '{path}'")


# ================= ENTRY =================

if __name__ == "__main__":
    main()

    
