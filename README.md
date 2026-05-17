🚀 Proyecto 4 — Generación de Código Intermedio (IR) para B-Minor
📌 Descripción

Este proyecto implementa un compilador completo para el lenguaje B-Minor, desarrollado en Python como parte del curso de Compiladores.

El compilador realiza el flujo completo de compilación:

📐 Pipeline del Compilador

Código Fuente
    ↓
Lexer
    ↓
Parser
    ↓
Checker Semántico
    ↓
AST
    ↓
Optimización de AST (O1)
    ↓
Generación de IR
    ↓
Optimización de IR (O1 / O2)
    ↓
Intérprete IR




🎯 Objetivo del Proyecto

Transformar el AST generado por el parser en un código intermedio (IR) basado en instrucciones de tres direcciones, y ejecutarlo mediante un intérprete propio con soporte de optimización y debugging avanzado.

⚙️ Funcionalidades Implementadas
🧠 Frontend del Compilador
🔹 Lexer

Convierte el código fuente en tokens.

✔ Keywords
✔ Operadores
✔ Identificadores
✔ Literales (int, float, string, char)
✔ Comentarios

🔹 Parser

Construye el AST (Abstract Syntax Tree).

✔ Expresiones
✔ Declaraciones
✔ Funciones
✔ Arreglos
✔ Control de flujo
✔ Llamadas a función

🔹 Checker Semántico

Valida el AST antes de generar IR.

✔ Variables declaradas
✔ Tipos correctos
✔ Funciones
✔ Scope léxico
✔ Retornos
✔ Arreglos
✔ Compatibilidad de tipos

🌳 AST — Visualización Mejorada

El AST ahora soporta:

✔ Impresión estructurada tipo árbol
✔ Colores por tipo de nodo
✔ Vista alternativa con rich.Tree
✔ Activación con --ast

Ejemplo:

python main.py archivo.bminor --ast


🧾 Generación de Código Intermedio (IR)

El compilador genera un IR de tres direcciones con:

✔ Registros R1, R2, R3...
✔ Labels para control de flujo
✔ Funciones
✔ Variables locales y globales
✔ Strings y arrays
✔ Instrucciones tipadas

📦 Instrucciones IR

✔ Variables y memoria
✔ Operaciones aritméticas
✔ Comparaciones
✔ Control de flujo
✔ Funciones
✔ Arrays
✔ Strings

⚡ Optimización
🔹 AST Optimization
Folding básico
Eliminación de expresiones redundantes
🔹 IR Optimization
O1: optimización local
O2: optimización más agresiva
🧠 Intérprete IR (irinterp.py)

Ejecuta el código intermedio generado.

⚙️ Características

✔ Ejecución de funciones
✔ Variables locales y globales
✔ Registros virtuales
✔ Control de flujo
✔ Recursión
✔ Arrays
✔ Strings C-style
✔ Operaciones aritméticas
✔ Comparaciones

🐞 MODO TRACE (MEJORADO)

El sistema de debugging fue completamente rediseñado.

🔥 Mejoras del TRACE

✔ Panel visual con rich
✔ Stack de llamadas (CALL STACK)
✔ Cambios de registros (diff real)
✔ Locals visibles por frame
✔ Colores por tipo de instrucción
✔ Jumps explícitos (BRANCH / CBRANCH)
✔ Estado posterior a ejecución (no previo)
✔ Menos ruido (sin spam de registros completos)

🧪 Ejemplo:


python main.py archivo.bminor --trace
python irinterp.py archivo.bminor --trace 



🏗️ Diseño del Compilador
🧭 Patrón Visitor

✔ AST recorrido con Visitor
✔ Métodos por nodo (visit_If, visit_BinaryOp, etc.)

📚 Tabla de Símbolos

✔ Scopes anidados
✔ Variables y funciones
✔ Resolución léxica
✔ Validación de redeclaración

🧬 Sistema de Tipos

✔ integer
✔ float
✔ boolean
✔ char
✔ string
✔ void
✔ array[T]

❗ Manejo de Errores

✔ Errores acumulados (no se detiene al primero)
✔ Mensajes con línea
✔ Checker semántico robusto

🗂️ Estructura del Proyecto

Compilador_Bminor/
│
├── lexer.py
├── parser.py
├── checker.py
├── ircode.py
├── irinterp.py
├── main.py
├── model.py
├── symtab.py
├── errors.py
├── typesys.py
│
├── astopt.py
├── iropt.py
├── visualizer.py
│
└── tests/
    ├── good/
    ├── bad/
    └── suprime/

    🧪 Archivos Auxiliares

✔ visualizer.py
✔ astopt.py
✔ iropt.py

Usados para debugging, optimización y pruebas experimentales.

📦 Requisitos

pip install rich multimethod

▶️ Ejecución
🔹 Compilar archivo

▶️ Ejecución
🔹 Compilar archivo

python main.py archivo.bminor

🔹 Ver AST

python main.py archivo.bminor --ast

🔹 Ver IR

python main.py archivo.bminor --ir

🔹 Comparar optimizaciones

python main.py archivo.bminor --compare


🔹 Ejecutar carpeta

python main.py tests/good
python main.py tests/bad

🐞 IR Interpreter directo

python irinterp.py archivo.bminor
python irinterp.py archivo.bminor --trace

📤 Salida
✔ Correcto
✓ Semantic check: SUCCESS


❌ Error
SEMANTIC CHECK FAILED


🚀 Estado del Proyecto
✅ Implementado

✔ Lexer
✔ Parser
✔ Checker
✔ AST
✔ IR Codegen
✔ IR Interpreter
✔ Optimización AST
✔ Optimización IR
✔ TRACE avanzado
✔ CLI completa

⚠️ En desarrollo
Debugger gráfico
Visualización AST avanzada
Optimización global IR
SSA futura


👨‍💻 Autores
Manuel Alejandro Gómez Briceño
Fernando Caicedo
Juan Fernando Pulgarín
🎓 Curso

Compiladores — Proyecto Compilador B-Minor