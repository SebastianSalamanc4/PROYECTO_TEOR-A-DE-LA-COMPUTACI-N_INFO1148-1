# Gramática formal de AgroReglas

Especificación formal que usa `codigo/herramientas/verificar_gramatica.py` para
comprobar FIRST/FOLLOW y la tabla LL(1) frente al cálculo por punto fijo.
`epsilon` es la secuencia vacía y `EOF` el marcador interno de fin de entrada.
Símbolo inicial: `<programa>`.

### Producciones

```text
<programa>          -> <regla> <lista_reglas>
<lista_reglas>      -> <regla> <lista_reglas> | epsilon
<regla>             -> WHEN <expresion> THEN <lista_acciones> <prioridad> PUNTO_COMA
<expresion>         -> <termino> <expresion_r>
<expresion_r>       -> OR <termino> <expresion_r> | epsilon
<termino>           -> <factor> <termino_r>
<termino_r>         -> AND <factor> <termino_r> | epsilon
<factor>            -> NOT <factor>
                     | PARENT_IZQ <expresion> PARENT_DER
                     | <comparacion>
<comparacion>       -> ID OP_REL <valor>
<valor>             -> NUM | TRUE | FALSE
<lista_acciones>    -> <accion> <lista_acciones_r>
<lista_acciones_r>  -> AND <accion> <lista_acciones_r> | epsilon
<accion>            -> ID <argumento_accion>
<argumento_accion>  -> ID | epsilon
<prioridad>         -> WITH PRIORITY NUM | epsilon
```

### Análisis de la gramática

#### Terminales y no terminales

**No terminales** (15): `<programa>`, `<lista_reglas>`, `<regla>`, `<expresion>`,
`<expresion_r>`, `<termino>`, `<termino_r>`, `<factor>`, `<comparacion>`,
`<valor>`, `<lista_acciones>`, `<lista_acciones_r>`, `<accion>`,
`<argumento_accion>`, `<prioridad>`.

**Terminales** (15): `WHEN`, `THEN`, `AND`, `OR`, `NOT`, `TRUE`, `FALSE`, `WITH`,
`PRIORITY`, `ID`, `NUM`, `OP_REL`, `PARENT_IZQ`, `PARENT_DER`, `PUNTO_COMA`.

`EOF` es un marcador interno de fin de entrada que usa el parser para saber
cuándo terminó el texto; no es un terminal del lenguaje propiamente tal, sino
una convención de implementación.

**Símbolo inicial**: `<programa>`.

#### Recursión izquierda

La gramática **no contiene recursión izquierda**. Durante el diseño se consideró
la forma natural de expresar listas y repeticiones, que suele producir recursión
izquierda. Por ejemplo, una primera versión de las reglas de un programa podría
haber sido:

```text
<programa> -> <programa> <regla> | <regla>
```

Esta producción es recursiva por la izquierda, porque `<programa>` aparece como
primer símbolo del lado derecho. Se eliminó introduciendo un no terminal auxiliar
`<lista_reglas>` que usa recursión por la **derecha**:

```text
<programa>      -> <regla> <lista_reglas>
<lista_reglas>  -> <regla> <lista_reglas> | epsilon
```

El mismo patrón se aplicó en todos los casos donde aparecía repetición:

- `<expresion>` / `<expresion_r>`: la operación OR podría generar recursión
  izquierda (`<expresion> -> <expresion> OR <termino>`). Se separó en
  `<expresion> -> <termino> <expresion_r>` y `<expresion_r> -> OR <termino> <expresion_r> | epsilon`.
- `<termino>` / `<termino_r>`: mismo tratamiento para AND.
- `<lista_acciones>` / `<lista_acciones_r>`: las múltiples acciones separadas
  por AND se manejan con el auxiliar `<lista_acciones_r>`.

En ninguna producción final el no terminal de la izquierda aparece como primer
símbolo de alguna alternativa del lado derecho, por lo que no hay recursión
izquierda directa ni indirecta.

#### Factorización por la izquierda

Se revisó cada no terminal para verificar que no existan dos alternativas cuyo
lado derecho comience con el mismo terminal o no terminal:

- `<factor>` tiene tres alternativas que comienzan con símbolos distintos: `NOT`,
  `PARENT_IZQ` e `ID` (a través de `<comparacion>`). No hay prefijo común.
- `<valor>` tiene tres alternativas: `NUM`, `TRUE`, `FALSE`. Todas distintas.
- Los no terminales con `epsilon` (`<lista_reglas>`, `<expresion_r>`,
  `<termino_r>`, `<lista_acciones_r>`, `<argumento_accion>`, `<prioridad>`)
  tienen su alternativa no vacía iniciando con un terminal distinto a los de
  FOLLOW, por lo que el parser puede decidir sin ambigüedad.

La gramática final no requiere factorización adicional. Una forma alternativa
como `<accion> -> ID ID | ID` compartiría el prefijo `ID`, lo que impediría al
parser decidir con un solo token de anticipación; la gramática entregada evita
ese problema mediante `<accion> -> ID <argumento_accion>` y
`<argumento_accion> -> ID | epsilon`, donde el parser consulta si el siguiente
token es `ID` para decidir si hay argumento o no.

#### Ambigüedad

La gramática **no es ambigua**. La separación de expresiones lógicas en tres
niveles de precedencia (`<expresion>` para OR, `<termino>` para AND, `<factor>`
para NOT y agrupación con paréntesis) garantiza que cada entrada válida tiene
exactamente un árbol de derivación. La precedencia queda implícita en la
estructura de las producciones:

1. NOT tiene la mayor precedencia (se resuelve en `<factor>`).
2. AND tiene precedencia intermedia (se resuelve en `<termino>`).
3. OR tiene la menor precedencia (se resuelve en `<expresion>`).

Los paréntesis permiten al usuario alterar esta precedencia de forma explícita
mediante la producción `<factor> -> PARENT_IZQ <expresion> PARENT_DER`.

Tampoco hay ambigüedad en la zona de acciones: `AND` después de `THEN` siempre
conecta acciones (no condiciones), porque la gramática separa claramente la
sección de condiciones (`<expresion>`) de la de acciones (`<lista_acciones>`).

### FIRST y FOLLOW

| No terminal | FIRST | FOLLOW |
|---|---|---|
| `<programa>` | `{ WHEN }` | `{ EOF }` |
| `<lista_reglas>` | `{ WHEN, epsilon }` | `{ EOF }` |
| `<regla>` | `{ WHEN }` | `{ WHEN, EOF }` |
| `<expresion>` | `{ NOT, PARENT_IZQ, ID }` | `{ THEN, PARENT_DER }` |
| `<expresion_r>` | `{ OR, epsilon }` | `{ THEN, PARENT_DER }` |
| `<termino>` | `{ NOT, PARENT_IZQ, ID }` | `{ OR, THEN, PARENT_DER }` |
| `<termino_r>` | `{ AND, epsilon }` | `{ OR, THEN, PARENT_DER }` |
| `<factor>` | `{ NOT, PARENT_IZQ, ID }` | `{ AND, OR, THEN, PARENT_DER }` |
| `<comparacion>` | `{ ID }` | `{ AND, OR, THEN, PARENT_DER }` |
| `<valor>` | `{ NUM, TRUE, FALSE }` | `{ AND, OR, THEN, PARENT_DER }` |
| `<lista_acciones>` | `{ ID }` | `{ WITH, PUNTO_COMA }` |
| `<lista_acciones_r>` | `{ AND, epsilon }` | `{ WITH, PUNTO_COMA }` |
| `<accion>` | `{ ID }` | `{ AND, WITH, PUNTO_COMA }` |
| `<argumento_accion>` | `{ ID, epsilon }` | `{ AND, WITH, PUNTO_COMA }` |
| `<prioridad>` | `{ WITH, epsilon }` | `{ PUNTO_COMA }` |

## Tabla LL(1)

| No terminal | Lookahead | Produccion aplicada |
|---|---|---|
| `<programa>` | `WHEN` | `<regla> <lista_reglas>` |
| `<lista_reglas>` | `WHEN` | `<regla> <lista_reglas>` |
| `<lista_reglas>` | `EOF` | `epsilon` |
| `<regla>` | `WHEN` | `WHEN <expresion> THEN <lista_acciones> <prioridad> PUNTO_COMA` |
| `<expresion>` | `NOT`, `PARENT_IZQ`, `ID` | `<termino> <expresion_r>` |
| `<expresion_r>` | `OR` | `OR <termino> <expresion_r>` |
| `<expresion_r>` | `THEN`, `PARENT_DER` | `epsilon` |
| `<termino>` | `NOT`, `PARENT_IZQ`, `ID` | `<factor> <termino_r>` |
| `<termino_r>` | `AND` | `AND <factor> <termino_r>` |
| `<termino_r>` | `OR`, `THEN`, `PARENT_DER` | `epsilon` |
| `<factor>` | `NOT` | `NOT <factor>` |
| `<factor>` | `PARENT_IZQ` | `PARENT_IZQ <expresion> PARENT_DER` |
| `<factor>` | `ID` | `<comparacion>` |
| `<comparacion>` | `ID` | `ID OP_REL <valor>` |
| `<valor>` | `NUM` | `NUM` |
| `<valor>` | `TRUE` | `TRUE` |
| `<valor>` | `FALSE` | `FALSE` |
| `<lista_acciones>` | `ID` | `<accion> <lista_acciones_r>` |
| `<lista_acciones_r>` | `AND` | `AND <accion> <lista_acciones_r>` |
| `<lista_acciones_r>` | `WITH`, `PUNTO_COMA` | `epsilon` |
| `<accion>` | `ID` | `ID <argumento_accion>` |
| `<argumento_accion>` | `ID` | `ID` |
| `<argumento_accion>` | `AND`, `WITH`, `PUNTO_COMA` | `epsilon` |
| `<prioridad>` | `WITH` | `WITH PRIORITY NUM` |
| `<prioridad>` | `PUNTO_COMA` | `epsilon` |

### Verificación de la tabla LL(1)

La tabla contiene **35 celdas** ocupadas y **0 conflictos**. Esto confirma que la
gramática es LL(1): para cada par (no terminal, terminal de anticipación) existe
a lo sumo una producción aplicable.

La ausencia de conflictos se debe a tres decisiones de diseño:

1. **Eliminación de recursión izquierda**: se usaron no terminales auxiliares con
   recursión derecha y `epsilon`, de modo que FIRST de la alternativa no vacía
   nunca se solapa con FOLLOW.
2. **Precedencia de operadores por niveles**: OR, AND y NOT se resuelven en no
   terminales distintos (`<expresion>`, `<termino>`, `<factor>`), evitando que
   AND y OR compitan por la misma celda.
3. **Separación de AND en condiciones y acciones**: después de THEN, AND conecta
   acciones (producción de `<lista_acciones_r>`); antes de THEN, AND conecta
   factores (producción de `<termino_r>`). El parser sabe en qué contexto está
   porque las producciones de `<regla>` separan ambas zonas con el terminal THEN.

El script `codigo/herramientas/verificar_gramatica.py` calcula FIRST y FOLLOW
por punto fijo, construye la tabla, verifica que coincida con esta documentación,
y compara un reconocedor de pila con el parser manual en los 30 casos de prueba
sin encontrar diferencias.

## Fin
