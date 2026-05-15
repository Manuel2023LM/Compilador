# 🚀 Proyecto 4 — Generación de Código Intermedio (IR) para B-Minor

---

# 📌 **Descripción**

Este proyecto implementa un **compilador para el lenguaje B-Minor**, desarrollado en Python como parte del curso de Compiladores.

El compilador realiza el flujo completo de compilación:

## 📐 **Estructura del Proyecto**

```text
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
Generación de IR
    ↓
Intérprete IR


## 🎯 **Objetivo del Proyecto**

El objetivo principal consiste en transformar el AST generado por el parser en un Código Intermedio (IR) basado en instrucciones de tres direcciones, para posteriormente ejecutarlo mediante un intérprete propio.

---

## ⚙️ **Funcionalidades Implementadas**

### 🧠 **Frontend del Compilador**

#### 🔹 **Lexer**

Convierte el código fuente en tokens válidos del lenguaje B-Minor.

**Características:**
- Reconocimiento de keywords
- Operadores
- Identificadores
- Números
- Strings
- Caracteres
- Comentarios

#### 🔹 **Parser**

Construye el AST (Abstract Syntax Tree) utilizando la gramática del lenguaje.

**Soporta:**
- Expresiones
- Declaraciones
- Funciones
- Arreglos
- Ciclos
- Condicionales
- Llamadas a función

#### 🔹 **Checker Semántico**

Realiza validaciones semánticas sobre el AST.

✔️ **Validaciones Implementadas:**
- Variables declaradas
- Redeclaraciones
- Tipos compatibles
- Funciones
- Parámetros
- Retornos
- Scope léxico
- Arreglos
- Expresiones válidas

---

### 🧾 **Generación de Código Intermedio (IR)**

El compilador transforma el AST en un IR de bajo nivel.

✨ **Características del IR:**
- Código de tres direcciones
- Registros temporales (R1, R2, R3, ...)
- Labels para control de flujo
- Soporte para funciones
- Soporte para arreglos
- Strings globales
- Variables locales y globales
- Instrucciones tipadas

#### 🧩 **Instrucciones IR Implementadas**

##### 📦 **Variables y Memoria**
- ALLOCI
- ALLOCF
- ALLOCB
- ALLOCS
- LOADI
- LOADF
- LOADB
- LOADS
- STOREI
- STOREF
- STOREB
- STORES

##### 🔢 **Literales**
- MOVI
- MOVF
- MOVB
- MOVS
- MOVA

##### ➗ **Operaciones Aritméticas**
- ADDI
- SUBI
- MULI
- DIVI
- ADDF
- SUBF
- MULF
- DIVF

##### ⚖️ **Comparaciones**
- CMPI
- CMPF
- CMPB
- CMPS

##### 🔀 **Control de Flujo**
- LABEL
- BRANCH
- CBRANCH
- PHI

##### 📞 **Funciones**
- CALL
- RET

##### 📊 **Arreglos**
- ARRAY
- LOADARR
- STOREARR
- LOADA
- STOREA

##### 🧵 **Strings**
- DATAS
- ADDR
- PRINTS

---

### 🧠 **Intérprete IR**

El archivo irinterp.py ejecuta el código intermedio generado por el compilador.

⚙️ **Funcionalidades del Intérprete:**
- Ejecución de funciones
- Manejo de registros
- Variables locales y globales
- Control de flujo
- Llamadas recursivas
- Operaciones aritméticas
- Comparaciones
- Manejo de arreglos
- Soporte para strings
- Impresión en consola
- Modo debug (--trace)

#### 🐞 **Modo TRACE**

El intérprete incluye un modo de depuración que permite visualizar:

- Instrucciones ejecutadas
- Registros
- Flujo de ejecución
- Labels
- Llamadas a funciones

Ejemplo:

python irinterp.py tests/suprime/suma.bminor --trace

---

## 🏗️ **Diseño del Compilador**

### 🧭 **Patrón Visitor**

El AST se recorre utilizando el patrón Visitor mediante multimethod.

**Ejemplo:**
- `visit_If()`
- `visit_Assignment()`
- `visit_BinaryOp()`
- `visit_FunctionCall()`

### 📚 **Tabla de Símbolos**

La tabla de símbolos (Symtab) maneja:

- Scopes anidados
- Variables
- Funciones
- Búsqueda léxica
- Redeclaraciones

**Cada símbolo almacena:**
- Nombre
- Tipo
- Contexto de declaración
- Scope

### 🧬 **Sistema de Tipos**

El lenguaje es fuertemente tipado.

✔️ **Tipos Soportados:**
- `integer`
- `float`
- `boolean`
- `char`
- `string`
- `void`
- `array[T]`

### ❗ **Manejo de Errores**

El compilador acumula errores y no se detiene en el primero.

**Cada error incluye:**
- Descripción clara
- Línea del código

**Ejemplo:**
```
error: variable 'x' no definida en línea 8
error: tipo incompatible en línea 12
```

---

## 🗂️ **Estructura del Proyecto**

Compilador_Bminor/
│
├── lexer.py
├── parser.py
├── checker.py
├── ircode.py
├── irinterp.py
├── main.py
├── model.py
├── model2.py
├── symtab.py
├── errors.py
├── typesys.py
├── visualizer.py
│
└── tests/
    ├── good/
    ├── bad/
    └── suprime/

---

## 🧪 **Archivos Auxiliares**

### ⚠️ **Archivos no oficiales del Proyecto 4**

Estos archivos fueron utilizados para pruebas, depuración o mejoras experimentales:

- `interpreter.py`
- `visualizer.py`
- `typesys.py`

Actualmente no forman parte del núcleo obligatorio del proyecto, pero se mantienen para futuras mejoras y siguientes proyectos.

---

## 📦 **Requisitos**

### 🐍 **Python**
- Python 3.x

### 📚 **Librerías Necesarias**

```bash
pip install multimethod rich graphviz
```

### 🧪 **Entorno Virtual**

El proyecto fue ejecutado utilizando venv.

**Crear entorno virtual:**

```bash
python -m venv venv
```

**Activar entorno virtual (Windows):**

```bash
venv\Scripts\activate
```

---

## ▶️ **Ejecución**

### ✅ **Ejecutar todos los tests GOOD**
```bash
python main.py tests/good
```

### ❌ **Ejecutar todos los tests BAD**
```bash
python main.py tests/bad
```

### 🚀 **Ejecutar tests del Proyecto 4**
```bash
python main.py tests/suprime
```

### 📄 **Ejecutar un archivo individual**
```bash
python main.py tests/good/good0.bminor
python main.py tests/bad/bad3.bminor
```

### 🔬 **Ejecutar intérprete IR directamente**
```bash
python irinterp.py tests/suprime/suma.bminor
python irinterp.py "tests/suprime/primes (1).bminor" 
```

### 🐛 **Ejecutar con TRACE**
```bash
python irinterp.py tests/suprime/suma.bminor --trace
python irinterp.py "tests/suprime/primes (1).bminor" --trace
```

---

## 📤 **Salida Esperada**

### ✔️ **Programa Correcto**
```
✓ Semantic check: SUCCESS
```

### ❌ **Programa con Errores**
```
SEMANTIC CHECK FAILED
```

---

## 🧪 **Estado Actual del Proyecto**

### ✅ **Implementado**
- Lexer
- Parser
- Checker Semántico
- AST
- Generación de IR
- Intérprete IR
- Funciones
- Recursión
- Ciclos
- Condicionales
- Arreglos
- Strings básicos
- Debug TRACE

### ⚠️ **En Desarrollo**
- Optimización IR
- Mejoras del intérprete
- Strings avanzados
- Debugger avanzado
- Visualización gráfica del AST
- Optimizaciones de registros

---

## 👨‍💻 **Autores**
- Manuel Alejandro Gómez Briceño
- Fernando Caicedo
- Juan Fernando Pulgarín

## 🎓 **Curso**
**Compiladores**




















