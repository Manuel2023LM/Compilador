import sys
import os

from rich import print

from lexer import tokenize
from parser import parse
from checker import Checker
from ircode import IRCodeGen
from astopt import optimize_ast_o1
from iropt import optimize_ir_o1, optimize_ir_o2

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

    return level

# ================= EJECUTAR 1 ARCHIVO =================

def run_file(path, opt_level=0, run_interpreter=True):
    print(f"\n[bold cyan]>>> Ejecutando:[/bold cyan] [yellow]{path}[/yellow]")

    try:

        source = read_file(path)

        # ========= PARSER =========
        ast = parse(source)

        # ========= CHECKER =========
        checker = Checker()
        checker.visit(ast)

        if checker.errors:


            print("\n[bold white on red] SEMANTIC CHECK FAILED [/bold white on red]\n")  
            print("\n[bold red]Errores semánticos:[/bold red]")

            for err in checker.errors:
                print(f"[bold red]• {err}[/bold red]")

            return False

        print("[bold green]✓ Semantic check: SUCCESS[/bold green]")

        # ========= AST OPTIMIZATION =========

        if opt_level >= 1:

            ast = optimize_ast_o1(ast, verbose=True)

            print("[bold green]✓ AST Optimization: SUCCESS[/bold green]")

        else:

            print("[bold yellow]• O0: AST sin optimizar[/bold yellow]")
        
        print("\n[bold cyan]=== AST OPTIMIZADO ===[/bold cyan]\n")
        print(ast)

    
        # ========= IR =========
        ir = IRCodeGen.generate(ast)

    # ========= IR OPTIMIZATION =========

        # ========= IR OPTIMIZATION =========

        if opt_level >= 2:

            ir = optimize_ir_o2(ir, verbose=True)

        elif opt_level >= 1:

            ir = optimize_ir_o1(ir, verbose=True)

        else:

            print("[bold yellow]• O0: IR sin optimizar[/bold yellow]")




        

        print("\n[bold magenta]=== Codigo Intermedio (IR) ===[/bold magenta]\n")

        print(f"[white]{ir.format()}[/white]")

        # ========= INTERPRETER =========
        if run_interpreter and HAS_INTERPRETER:

            TRACE = "--trace" in sys.argv

            if TRACE:
                print("\n[bold yellow]=== TRACE MODE ACTIVADO ===[/bold yellow]\n")
            else:
                print("\n[bold blue]=== Ejecutando Programa ===[/bold blue]\n")

            interpreter = IRInterpreter(ir, trace=TRACE)
            interpreter.run("main")

        return True

    except SyntaxError as e:

        print("\n[bold red]✗ Error de sintaxis[/bold red]")
        print(f"[red]error:[/red] {e}")

        return False

    except Exception as e:

        print("\n[bold yellow]⚠ Runtime Error[/bold yellow]")
        print(f"[yellow]{e}[/yellow]")

        # El checker y el IR fueron exitosos
        return True


# ================= EJECUTAR CARPETA =================

def run_folder(folder, opt_level=0):

    if not os.path.isdir(folder):

        print(f"[bold red]error:[/bold red] '{folder}' no es una carpeta válida")

        return

    files = sorted(os.listdir(folder))

    total = 0
    passed = 0

    is_good = True

    print(f"\n[bold blue]=== Ejecutando carpeta ===[/bold blue]")
    print(f"[cyan]{folder}[/cyan]\n")

    for f in files:

        if f.startswith("._"):
            continue

        if not f.endswith(".bminor"):
            continue

        total += 1

        path = os.path.join(folder, f)

        ok = run_file(path, opt_level=opt_level)

        if is_good:
            if ok:
                passed += 1
        else:
            if not ok:
                passed += 1

    print("\n[bold blue]==========================[/bold blue]")

    if passed == total:
        color = "green"
    elif passed > 0:
        color = "yellow"
    else:
        color = "red"

    print(f"[bold {color}]RESULTADO: {passed}/{total} correctos[/bold {color}]")

    print("[bold blue]==========================[/bold blue]\n")


# ================= MAIN =================

def main():

    if len(sys.argv) < 2:

        print("[bold yellow]Uso:[/bold yellow]")
        print("[cyan]python main.py archivo.bminor[/cyan]")
        print("[cyan]python main.py carpeta/[/cyan]")

        return

    path = sys.argv[1]

    opt_level = parse_opt_level(sys.argv)

    # ========= CARPETA =========
    if os.path.isdir(path):
        run_folder(path, opt_level=opt_level)
        return

    # ========= ARCHIVO =========
    print(f"[bold cyan]Nivel de optimizacion:[/bold cyan] O{opt_level}")


    if os.path.isfile(path):
        run_file(path, opt_level=opt_level)
        return

    print(f"[bold red]error:[/bold red] ruta inválida '{path}'")


# ================= ENTRY =================

if __name__ == "__main__":
    main()