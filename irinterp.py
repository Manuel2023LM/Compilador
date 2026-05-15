from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from rich import print

class IRRuntimeError(RuntimeError):
	pass
	
	
@dataclass
class Frame:
	name: str
	instructions: list[tuple]
	params: list[tuple[str, Any]] = field(default_factory=list)
	locals: dict[str, Any] = field(default_factory=dict)
	regs: dict[str, Any] = field(default_factory=dict)
	labels: dict[str, int] = field(default_factory=dict)
	pc: int = 0
	
	def __post_init__(self):
		self.labels = {
			inst[1]: i
			for i, inst in enumerate(self.instructions)
			if inst and inst[0] == "LABEL"
		}
		
		
class IRInterpreter:
	'''
	Intérprete para el IR generado por ircode_strings_bytes.py.
	
	Soporta:
	- enteros, flotantes, bytes/chars y booleanos como enteros 0/1
	- variables globales y locales
	- funciones, CALL y RET
	- flujo de control: LABEL, BRANCH, CBRANCH
	- strings como arreglos globales de bytes: DATAS + ADDR + PRINTS
	- PHI simple: toma el primer registro existente entre sus entradas
	'''
	
	def __init__(self, program, trace: bool = False):
		self.program = program
		self.trace = trace
		self.globals: dict[str, Any] = {}
		self.global_regs: dict[str, Any] = {}
		self.global_regs = {}
		self.data: dict[str, list[int]] = {}
		self.functions = {fn.name: fn for fn in getattr(program, "functions", [])}
		self.output: list[str] = []
		self._load_globals()
		
	# -------------------------------------------------
	# API pública
	# -------------------------------------------------
	
	def run(self, name: str = "main", *args):

		if name not in self.functions:
			print(f"[yellow]Warning:[/yellow] función '{name}' no encontrada")
			return None

		fn = self.functions[name]

		expected = len(getattr(fn, "params", []))

		if len(args) < expected:
			args = list(args) + [0] * (expected - len(args))

		return self.call(name, list(args))


	def call(self, name: str, args: list[Any]):
		if name not in self.functions:
			raise IRRuntimeError(f"Función no encontrada: {name}")
			
		fn = self.functions[name]
		params = getattr(fn, "params", [])
		if len(args) != len(params):
			raise IRRuntimeError(
				f"La función {name} espera {len(params)} argumento(s), recibió {len(args)}"
			)
			
		frame = Frame(
			name=name,
			instructions=list(getattr(fn, "instructions", [])),
			params=list(params),
		)
		
		# Los parámetros se modelan como variables locales ya inicializadas.
		for (pname, _pty), value in zip(params, args):
			frame.locals[pname] = value
			
		return self._execute_frame(frame)
		
	# -------------------------------------------------
	# Carga de datos globales
	# -------------------------------------------------
	
	def _load_globals(self):
		for inst in getattr(self.program, "globals", []):
			self._exec_global(inst)
			
	def _exec_global(self, inst: tuple):
		op = inst[0]

		# ---------------------------------
		# DATAS
		# ---------------------------------
		if op == "DATAS":
			_, name, *values = inst

			parsed = []

			for v in values:

				if isinstance(v, str) and "," in v:
					parts = v.split(",")
					parsed.extend(int(x.strip()) for x in parts)
				else:
					parsed.append(int(v))

			self.data[name] = parsed
			return

		# ---------------------------------
		# Variables globales
		# ---------------------------------
		if op in {"VARI", "VARF", "VARB", "VARS", "VARA"}:
			_, name = inst

			if op == "ARRAY":
				_, name, size = inst
				self.globals[name] = [0] * int(size)
				return None

			if op == "VARF":
				self.globals.setdefault(name, 0.0)

			elif op == "VARS":
				self.globals.setdefault(name, None)

			elif op == "VARA":
				self.globals.setdefault(name, [])

			else:
				self.globals.setdefault(name, 0)

			return

		# ---------------------------------
		# Arrays
		# ---------------------------------
		if op == "ARRAY":
			_, name, size = inst
			self.globals[name] = [0] * int(size)
			return

		# ---------------------------------
		# MOV
		# ---------------------------------
		if op in {"MOVI", "MOVF", "MOVB", "MOVS"}:
			_, value, target = inst

			if op == "MOVF":
				value = float(value)

			elif op in {"MOVI", "MOVB"}:
				value = int(value)

			self.global_regs[target] = value
			return

		# ---------------------------------
		# NEG
		# ---------------------------------
		if op in {"NEGI", "NEGF"}:
			_, source, target = inst

			value = self.global_regs.get(source, 0)

			if op == "NEGI":
				self.global_regs[target] = -int(value)
			else:
				self.global_regs[target] = -float(value)

			return


		# ---------------------------------
		# ADDR
		# ---------------------------------
		if op == "ADDR":
			_, name, target = inst

			if name not in self.data:
				raise IRRuntimeError(f"Bloque de datos no encontrado: {name}")

			self.global_regs[target] = name
			return

		# ---------------------------------
		# MOVA
		# ---------------------------------
		if op == "MOVA":
			_, arrname, target = inst

			if arrname not in self.globals:
				raise IRRuntimeError(f"Array no encontrado: {arrname}")

			self.global_regs[target] = self.globals[arrname]
			return

		# ---------------------------------
		# STORE
		# ---------------------------------
		if op in {"STOREI", "STOREF", "STOREB", "STORES", "STOREA"}:
			_, source, name = inst

			if source in self.global_regs:
				value = self.global_regs[source]
			else:
				value = source

			self.globals[name] = value
			return

		# ---------------------------------
		# LOAD
		# ---------------------------------
		if op in {"LOADI", "LOADF", "LOADB", "LOADS", "LOADA"}:
			_, name, target = inst

			if name not in self.globals:
				raise IRRuntimeError(f"Global no definido: {name}")

			self.global_regs[target] = self.globals[name]
			return

		raise IRRuntimeError(f"Instrucción global no soportada: {inst}")


	def _default_for_op(self, op: str):
		if op.endswith("F"):
			return 0.0
		if op.endswith("S"):
			return None
		return 0
		
	# -------------------------------------------------
	# Ejecución
	# -------------------------------------------------
	
	def _execute_frame(self, frame: Frame):
		insts = frame.instructions
		
		while frame.pc < len(insts):
			inst = insts[frame.pc]
			current_pc = frame.pc
			frame.pc += 1
			
			if self.trace:
				print(f"[TRACE] {frame.name}:{current_pc:04d} {inst}")
				
			try:
				result = self._dispatch(frame, inst)
			except IRRuntimeError as exc:
				raise IRRuntimeError(
					f"{exc}\n"
					f"  función: {frame.name}\n"
					f"  pc: {current_pc}\n"
					f"  instrucción: {inst}\n"
					f"  locals: {frame.locals}\n"
					f"  regs: {frame.regs}"
				) from None
			if isinstance(result, _Return):
				return result.value
				
		return None
		
	def _dispatch(self, frame: Frame, inst: tuple):
		if not inst:
			return None
			
		op = inst[0]

		if op in {"NEGI", "NEGF"}:
			_, source, target = inst

			value = self._value(frame, source)

			if op == "NEGI":
				frame.regs[target] = -int(value)
			else:
				frame.regs[target] = -float(value)

			return None
		
		# -------------------------
		# Datos y direcciones
		# -------------------------
		if op == "DATAS":
			_, name, *values = inst

			parsed = []

			for v in values:

				if isinstance(v, str) and "," in v:

					parts = v.split(",")

					parsed.extend(int(x.strip()) for x in parts)

				else:
					parsed.append(int(v))

			self.data[name] = parsed
			return None
			
		if op == "ADDR":
			_, name, target = inst
			if name not in self.data:
				raise IRRuntimeError(f"Bloque de datos no encontrado: {name}")
			frame.regs[target] = name
			return None
			
		# -------------------------
		# Variables locales/globales
		# -------------------------
		# -------------------------
		# Variables locales/globales
		# -------------------------
		if op in {"ALLOCI", "ALLOCF", "ALLOCB", "ALLOCS"}:
			_, name = inst

			frame.locals.setdefault(name, self._default_for_op(op))

			return None

		if op in {"VARI", "VARF", "VARB", "VARS"}:
			_, name = inst

			self.globals.setdefault(name, self._default_for_op(op))

			return None

		# ---------------------------------
		# LOAD normales
		# ---------------------------------
		if op in {"LOADI", "LOADF", "LOADB", "LOADS"}:

			_, name, target = inst

			frame.regs[target] = self._load_var(frame, name)

			return None

		# ---------------------------------
		# LOADA
		# ---------------------------------
		if op == "LOADA":

			# LOADA arr, index, target
			if len(inst) == 4:

				_, name, index, target = inst

				idx = self._value(frame, index)

				arr = self._load_var(frame, name)

				frame.regs[target] = arr[idx]

				return None

			# LOADA var, target
			elif len(inst) == 3:

				_, name, target = inst

				frame.regs[target] = self._load_var(frame, name)

				return None

		if op in {"STOREI", "STOREF", "STOREB", "STORES", "STOREA"}:

			_, source, name = inst

			self._store_var(frame, name, self._value(frame, source))

			return None





		# -------------------------
		# Literales
		# -------------------------
		if op in {"MOVI", "MOVF", "MOVB", "MOVS", "MOVA"}:

			if op == "MOVA":
				_, arrname, target = inst

				frame.regs[target] = self.globals[arrname]
				return None
			_, value, target = inst
			if op == "MOVF":
				value = float(value)
			elif op in {"MOVI", "MOVB"}:
				value = int(value)
			frame.regs[target] = value
			return None
			
		# -------------------------
		# Aritmética
		# -------------------------
		if op in {"ADDI", "SUBI", "MULI", "DIVI", "ADDF", "SUBF", "MULF", "DIVF"}:
			_, r1, r2, target = inst
			a = self._value(frame, r1)
			b = self._value(frame, r2)
			if op.startswith("ADD"):
				out = a + b
			elif op.startswith("SUB"):
				out = a - b
			elif op.startswith("MUL"):
				out = a * b
			elif op.startswith("DIV"):
				if b == 0:
					raise IRRuntimeError(
						f"División por cero en {op}: divisor {r2} vale 0; "
						f"dividendo {r1} vale {a}"
					)
				if op.endswith("I"):
					out = int(a / b)   # truncamiento hacia cero
				else:
					out = a / b
			frame.regs[target] = out
			return None
			
		# -------------------------
		# Bitwise / booleanos 0-1
		# -------------------------
		if op in {"AND", "OR", "XOR"}:
			_, r1, r2, target = inst
			a = int(self._value(frame, r1))
			b = int(self._value(frame, r2))
			if op == "AND":
				out = a & b
			elif op == "OR":
				out = a | b
			else:
				out = a ^ b
			frame.regs[target] = out
			return None
			
		# -------------------------
		# Comparaciones
		# -------------------------
		if op in {"CMPI", "CMPF", "CMPB", "CMPS"}:
			_, cmp_op, r1, r2, target = inst
			a = self._value(frame, r1)
			b = self._value(frame, r2)
			frame.regs[target] = 1 if self._compare(cmp_op, a, b) else 0
			return None
			
		# -------------------------
		# Conversiones
		# -------------------------
		if op == "ITOF":
			_, r1, target = inst
			frame.regs[target] = float(self._value(frame, r1))
			return None
			
		if op == "FTOI":
			_, r1, target = inst
			frame.regs[target] = int(self._value(frame, r1))
			return None
			
		if op == "BTOI":
			_, r1, target = inst
			frame.regs[target] = int(self._value(frame, r1))
			return None
			
		if op == "ITOB":
			_, r1, target = inst
			frame.regs[target] = int(self._value(frame, r1)) & 0xFF
			return None
			
		# -------------------------
		# Print
		# -------------------------
		if op in {"PRINTI", "PRINTF", "PRINTB", "PRINTS"}:
			_, source = inst
			value = self._value(frame, source)
			if op == "PRINTB":
				text = chr(value) if isinstance(value, int) else str(value)
			elif op == "PRINTS":
				text = self._read_c_string(value)
			else:
				text = str(value)
			print(text)
			self.output.append(text)
			return None
			
		# -------------------------
		# Control de flujo
		# -------------------------
		if op == "LABEL":
			return None
			
		if op == "BRANCH":
			_, label = inst
			frame.pc = self._label_pc(frame, label)
			return None
			
		if op == "CBRANCH":
			_, test, label_true, label_false = inst
			value = self._value(frame, test)
			frame.pc = self._label_pc(frame, label_true if value != 0 else label_false)
			return None
			
		# PHI simple: útil para expresiones ternarias.
		# Como solo se ejecuta una rama, normalmente solo uno de los registros existe.
		if op == "PHI":
			*sources, target = inst[1:]
			for src in sources:
				if isinstance(src, str) and src in frame.regs:
					frame.regs[target] = frame.regs[src]
					return None
			# Fallback: evaluar el primer operando si existe.
			if sources:
				frame.regs[target] = self._value(frame, sources[0])
			else:
				frame.regs[target] = None
			return None
			
		# -------------------------
		# Funciones
		# -------------------------
		if op == "CALL":
			_, fname, *rest = inst
			if fname not in self.functions:
				raise IRRuntimeError(f"Función no encontrada: {fname}")
				
			expected = len(getattr(self.functions[fname], "params", []))
			arg_regs = rest[:expected]
			target = rest[expected] if len(rest) > expected else None
			arg_values = [self._value(frame, r) for r in arg_regs]
			ret = self.call(fname, arg_values)
			if target is not None:
				frame.regs[target] = ret
			return None
			
		if op == "RET":
			if len(inst) == 1:
				return _Return(None)
			_, source = inst
			return _Return(self._value(frame, source))
			
		raise IRRuntimeError(f"Instrucción no soportada: {inst}")
		
	# ------------------------------------------------------------
	# Helpers
	# ------------------------------------------------------------
	
	def _value(self, frame: Frame, operand):
		if isinstance(operand, str):
			if operand in frame.regs:
				return frame.regs[operand]
			if operand in frame.locals:
				return frame.locals[operand]
			if operand in self.globals:
				return self.globals[operand]
			if operand in self.data:
				return operand
		return operand
		
	def _load_var(self, frame: Frame, name: str):
		if name in frame.locals:
			return frame.locals[name]
		if name in self.globals:
			return self.globals[name]
		raise IRRuntimeError(f"Variable no definida: {name}")
		
	def _store_var(self, frame: Frame, name: str, value):
		if name in frame.locals:
			frame.locals[name] = value
		elif name in self.globals:
			self.globals[name] = value
		else:
			# Si no existe, asumimos local para tolerar IR sencillo.
			frame.locals[name] = value
			
	def _label_pc(self, frame: Frame, label: str) -> int:
		if label not in frame.labels:
			raise IRRuntimeError(f"Label no encontrado en {frame.name}: {label}")
		return frame.labels[label]
		
	def _compare(self, op: str, a, b) -> bool:
		if op == "==":
			return a == b
		if op == "!=":
			return a != b
		if op == "<":
			return a < b
		if op == "<=":
			return a <= b
		if op == ">":
			return a > b
		if op == ">=":
			return a >= b
		raise IRRuntimeError(f"Comparador no soportado: {op}")
		
	def _read_c_string(self, name_or_values) -> str:

		if isinstance(name_or_values, str):

			if name_or_values not in self.data:
				raise IRRuntimeError(
					f"Cadena no encontrada: {name_or_values}"
				)

			values = self.data[name_or_values]

		else:
			values = name_or_values

		chars = []

		i = 0

		while i < len(values):

			b = int(values[i])

			if b == 0:
				break

			# \n
			if b == 92 and i + 1 < len(values):

				nxt = int(values[i + 1])

				if nxt == 110:
					chars.append("\n")
					i += 2
					continue

				elif nxt == 116:
					chars.append("\t")
					i += 2
					continue

			chars.append(chr(b))

			i += 1

		return "".join(chars)
		
@dataclass
class _Return:
	value: Any = None
	
	
# Alias corto opcional
IRInterp = IRInterpreter


if __name__ == "__main__":
	import sys
	
	from parser  import parse
	from checker import Checker
	from errors  import errors_detected
	from ircode  import IRCodeGen
	
	if sys.platform != 'ios':
		if len(sys.argv) < 2:
			raise SystemExit("Usage: python irinterp.py <filename> [--trace]")

		filename = sys.argv[1]	
	else:
		from file_picker import file_picker_dialog
		filename = file_picker_dialog(
			title='Seleccionar un archivo',
			root_dir='./test/',
			file_pattern='^.*[.](bpp|bminor)'
		)
		
	if filename:
		txt = open(filename, encoding="utf-8").read()
		ast = parse(txt)
	
		if errors_detected():
			raise SystemExit("Hay errores de análisis; no se ejecuta IR.")
		
		# ============================================================
		# CHECKER
		# ============================================================

		checker = Checker()
		checker.visit(ast)

		if checker.errors:

			print("\n[bold white on red] SEMANTIC CHECK FAILED [/bold white on red]\n")

			for err in checker.errors:
				print(f"[bold red]• {err}[/bold red]")

			raise SystemExit(
				"El checker reportó errores; no se ejecuta IR."
			)

		print("[bold green]✓ Semantic check: SUCCESS[/bold green]")


		ir = IRCodeGen.generate(ast)
		
		DEBUG = "--trace" in sys.argv

		interp = IRInterpreter(ir, trace=DEBUG)
		if any(fn.name == "main" for fn in ir.functions):
			interp.run("main")
		else:
			print("[yellow]Warning:[/yellow] función 'main' no encontrada")	
