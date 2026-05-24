# 🚀 Proyecto 4 — Generación de Código Intermedio (IR) para B-Minor

## 📌 Descripción

Este proyecto implementa un compilador completo para el lenguaje B-Minor, desarrollado en Python como parte del curso de Compiladores.

El compilador realiza el flujo completo de compilación:

## 📐 Pipeline del Compilador

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




## 🎯 Objetivo del Proyecto

Transformar el AST generado por el parser en un código intermedio (IR) basado en instrucciones de tres direcciones, y ejecutarlo mediante un intérprete propio con soporte de optimización y debugging avanzado.

## ⚙️ Funcionalidades Implementadas

### 🧠 Frontend del Compilador

#### 🔹 Lexer

Convierte el código fuente en tokens.

✔ Keywords
✔ Operadores
✔ Identificadores
✔ Literales (int, float, string, char)
✔ Comentarios

#### 🔹 Parser

Construye el AST (Abstract Syntax Tree).

✔ Expresiones
✔ Declaraciones
✔ Funciones
✔ Arreglos
✔ Control de flujo
✔ Llamadas a función

#### 🔹 Checker Semántico

Valida el AST antes de generar IR.

✔ Variables declaradas
✔ Tipos correctos
✔ Funciones
✔ Scope léxico
✔ Retornos
✔ Arreglos
✔ Compatibilidad de tipos

## 🌳 AST — Visualización Mejorada

El AST ahora soporta:

✔ Impresión estructurada tipo árbol
✔ Colores por tipo de nodo
✔ Vista alternativa con rich.Tree
✔ Activación con --ast

Ejemplo:

```bash
python main.py archivo.bminor --ast
```

## 🧾 Generación de Código Intermedio (IR)

El compilador genera un IR de tres direcciones con:

✔ Registros R1, R2, R3...
✔ Labels para control de flujo
✔ Funciones
✔ Variables locales y globales
✔ Strings y arrays
✔ Instrucciones tipadas

### 📦 Instrucciones IR

✔ Variables y memoria
✔ Operaciones aritméticas
✔ Comparaciones
✔ Control de flujo
✔ Funciones
✔ Arrays
✔ Strings

## ⚡ Optimización

### 🔹 AST Optimization
- Folding básico
- Eliminación de expresiones redundantes

### 🔹 IR Optimization
- O1: optimización local
- O2: optimización más agresiva

## 🧠 Intérprete IR (irinterp.py)

Ejecuta el código intermedio generado.

## ⚙️ Características

✔ Ejecución de funciones
✔ Variables locales y globales
✔ Registros virtuales
✔ Control de flujo
✔ Recursión
✔ Arrays
✔ Strings C-style
✔ Operaciones aritméticas
✔ Comparaciones

## 🐞 MODO TRACE (MEJORADO)

El sistema de debugging fue completamente rediseñado.

### 🔥 Mejoras del TRACE

✔ Panel visual con rich
✔ Stack de llamadas (CALL STACK)
✔ Cambios de registros (diff real)
✔ Locals visibles por frame
✔ Colores por tipo de instrucción
✔ Jumps explícitos (BRANCH / CBRANCH)
✔ Estado posterior a ejecución (no previo)
✔ Menos ruido (sin spam de registros completos)

🧪 Ejemplo:

```bash
python main.py archivo.bminor --trace
python irinterp.py archivo.bminor --trace
```



## ## 🏗️ Diseño del Compilador

### 🧭 Patrón Visitor

✔ AST recorrido con Visitor
✔ Métodos por nodo (visit_If, visit_BinaryOp, etc.)

### 📚 Tabla de Símbolos

✔ Scopes anidados
✔ Variables y funciones
✔ Resolución léxica
✔ Validación de redeclaración

### 🧬 Sistema de Tipos

✔ integer
✔ float
✔ boolean
✔ char
✔ string
✔ void
✔ array[T]

### ❗ Manejo de Errores

✔ Errores acumulados (no se detiene al primero)
✔ Mensajes con línea
✔ Checker semántico robusto

## 🗂️ Estructura del Proyecto

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


# 🔄 Flujo Interno

1. Lexer genera tokens
2. Parser construye AST
3. Checker valida semántica
4. AST se optimiza
5. IRCodeGen genera IR
6. IR se optimiza
7. IRInterpreter ejecuta instrucciones

# ✨ Features

- 🌳 AST visual interactivo
- ⚡ Optimizaciones O1/O2
- 🐞 TRACE avanzado
- 🎨 Consola coloreada con Rich
- 🧠 Intérprete IR completo
- 📦 Soporte para arrays y strings
- 🔀 Control de flujo
- 📞 Funciones y recursión


## 📦 Requisitos

```bash
pip install rich multimethod
```

## 🧪 Crear entorno virtual

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```
### Linux / Mac
```bash
python3 -m venv venv
source venv/bin/activate
```
## 🚀 Activación del Entorno Virtual (Windows)

Para activar el entorno virtual en **PowerShell**, primero debes habilitar los permisos
de ejecución en tu sesión actual y luego llamar al script correspondiente según la estructura de tu carpeta `venv`:

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

.\venv\Scripts\Activate.ps1

. .\venv\bin\Activate.ps1

> 💡 **Nota:** Usa la segunda línea si tu entorno tiene la carpeta estándar `Scripts`.
> Si se generó con la carpeta `bin` (estilo Linux/Git Bash), usa la tercera línea reemplazando el comando anterior. 
>Verás el indicador `(venv)` al inicio de la terminal una vez completado con éxito.

Instalación de Dependencias
Una vez que el entorno esté activo (venv), instala los paquetes necesarios ejecutando:

PowerShell
pip install multimethod rich


# ⚡ Niveles de Optimización

| Nivel | Descripción |
|-------|-------------|
| O0 | Sin optimización |
| O1 | Optimización AST + IR local |
| O2 | Optimización agresiva IR |

## O1
- Constant folding
- Simplificación algebraica
- Eliminación de redundancias

## O2
- Propagación de constantes
- Eliminación de código muerto
- Simplificación de branches




# 🧪 Suite de Tests

El proyecto incluye múltiples categorías de pruebas.

## 📂 tests/good
Programas válidos que deben compilar y ejecutarse correctamente.

## 📂 tests/bad
Programas inválidos diseñados para producir errores semánticos o sintácticos.

## 📂 tests/optimizer
Pruebas específicas para optimizaciones AST e IR.

## 📂 tests/suprime
Pruebas completas del Proyecto 4:
- loops
- funciones
- recursión
- arreglos
- strings
- optimización






## ▶️ Ejecución

### 🔹 Compilar archivo

```bash
python main.py archivo.bminor
```

### 🔹 Ver AST

```bash
python main.py archivo.bminor --ast
```

### 🔹 Ver IR

```bash
python main.py archivo.bminor --ir
```

### 🔹 Comparar optimizaciones

```bash
python main.py archivo.bminor --compare
```


# 🧩 Flags Disponibles

| Flag          | Descripción |
|-------------  |-------------|
| `--ast`       | Muestra el AST visual |
| `--ir`        | Muestra el código IR |
| `--trace`     | Activa el modo debug del intérprete |
| `--compare`   | Compara O0, O1 y O2 |
| `-O0`         | Sin optimización |
| `-O1`         | Optimización básica |
| `-O2`         | Optimización avanzada |
| `-q`/`--quiet`| Ejecuta sin logs extra |

---

## Ejemplos

## 🔹 Ejecutar archivo individual

```bash
python main.py tests/good/good0.bminor
```
## 🔹 Mostrar AST

```bash
python main.py tests/good/good0.bminor --ast
```

```bash
python main.py tests/suprime/test_o1.bminor --ast
```

---

## 🔹 Mostrar IR

```bash
python main.py tests/good/good0.bminor --ir
```
```bash
python main.py tests/suprime/test_o1.bminor --ir
```

## 🔹 Ejecutar con optimización

```bash
python main.py tests/suprime/test_o1.bminor -O0
python main.py tests/suprime/test_o1.bminor -O1
python main.py tests/suprime/test_o1.bminor -O2
```

```bash
python main.py tests/suprime/test_o1.bminor --trace
```

## 🔹 Comparar optimizaciones
```bash
python main.py tests/suprime/test_o1.bminor --compare
```
si se quiere ver los resultados del codigo intermedio y optimización
se combinan los flags
```bash
python main.py tests/suprime/test_o1.bminor -O0 --ir
python main.py tests/suprime/test_o1.bminor -O1 --ir
python main.py tests/suprime/test_o1.bminor -O2 --ir
```

## 🔹 Ejecutar todos los GOOD y los BAD

```bash
python main.py tests/good
python main.py tests/bad
```


## 🐞 IR Interpreter directo
```bash
python irinterp.py tests/suprime/suma.bminor
```


## 🔹 TRACE Mode

```bash
python main.py tests/suprime/suma.bminor --trace
```

# 🐞 TRACE Interno

>El modo TRACE muestra el estado posterior a cada instrucción ejecutada.

Incluye:
- ✅ Program Counter (PC)
- ✅ Instrucción actual
- ✅ Cambios en registros
- ✅ Variables locales
- ✅ Saltos de flujo
- ✅ Stack de llamadas

Ejemplo:

```text
PC: 0010
Instr: CBRANCH, R5, Ltrue, Lfalse
R5 = 0
Jump → Lfalse
```


## 📤 Salida
- ✔ Correcto
- ✓ Semantic check: SUCCESS


## ❌ Error
- SEMANTIC CHECK FAILED

---

## 🎨 Características Visuales

>El compilador utiliza la librería `rich` para mostrar:

- 🎨 AST coloreado
- 🧾 IR coloreado
- 🖥️ Panels visuales
- 🐞 Trace interactivo
- ⚡ Resumen de optimizaciones
- 📊 Estadísticas de compilación
- 📚 Call stack visual
- 🔁 Cambios de registros en tiempo real

---

## 🚀 Estado del Proyecto

### ✅ Implementado
- Lexer
- Parser
- Checker
- AST
- IR Codegen
- IR Interpreter
- Optimización AST
- Optimización IR
- TRACE avanzado
- CLI completa

### ⚠️ En desarrollo
- Debugger gráfico
- Visualización AST avanzada
- Optimización global IR
- SSA futura


# 🏆 Logros en el proyecto

✔ Implementación completa de un compilador end-to-end para B-Minor  
✔ Pipeline completo: Lexer → Parser → Checker → AST → IR → Interpreter  
✔ Generación de Código Intermedio (IR) basado en tres direcciones  
✔ Diseño de un intérprete virtual propio para ejecución del IR  
✔ Sistema de registros virtuales (R1, R2, R3...)  
✔ Manejo de variables locales, globales y scopes léxicos  
✔ Soporte para funciones, parámetros y llamadas recursivas  
✔ Implementación de control de flujo mediante LABEL, BRANCH y CBRANCH  
✔ Soporte para arrays y strings estilo C  
✔ Sistema de tipos fuertemente tipado  
✔ Checker semántico con acumulación de errores  
✔ Optimización de AST (constant folding y simplificación)  
✔ Optimización IR multinivel (O1 / O2)  
✔ Visualización avanzada del AST utilizando rich.Tree  
✔ Sistema TRACE avanzado para debugging del IR  
✔ Visualización de registros y cambios de estado en tiempo real  
✔ CLI completa con múltiples flags de compilación y debugging  
✔ Suite de pruebas separada para GOOD / BAD / OPTIMIZER / SUPRIME  
✔ Arquitectura modular y extensible para futuros proyectos  
✔ Uso del patrón Visitor para recorrido y análisis del AST  
✔ Base preparada para futuras optimizaciones SSA y backend assembly  



## 👨‍💻 Autores
>Manuel Alejandro Gómez Briceño
>Fernando Caicedo
>Juan Fernando Pulgarín

## 🎓 Curso
Compiladores — Proyecto Compilador B-Minor

## ✨💖 agradecimientos a:
```bash >
     EL Profesor 
Angel Augusto Agudelo Zapata

``` 
