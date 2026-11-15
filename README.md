# SACgro

Analizador sintáctico predictivo (descenso recursivo, gramática LL(1)) para un
lenguaje pequeño de reglas de automatización de un invernadero.
Proyecto de Teoría de la Computación (INFO1148).

El programa valida la estructura de las reglas y construye un árbol de sintaxis
abstracta (AST). No controla equipos ni ejecuta las acciones.

## Requisitos

- Python 3.10 o superior.
- No hay dependencias externas: todo usa la biblioteca estándar.
- Para la visualización gráfica del AST (opcional): `pip install graphviz` y
  [Graphviz](https://graphviz.org/) instalado en el sistema.

## Estructura

```text
codigo/
  src/             Analizador léxico, parser, AST y consola
  pruebas/         Pruebas automatizadas (unittest)
  herramientas/    Verificadores y generador gráfico del AST
datos/
  entradas/        Programas de ejemplo (.agro, archivos de texto)
docs/
  gramatica.md     Producciones, análisis, FIRST/FOLLOW y tabla LL(1)
resultados/        Matriz CSV de casos, registros de ejecución e imágenes del AST
```

## Ejecución

Todos los comandos se ejecutan desde la carpeta `codigo/`:

```powershell
cd codigo
python -m src.principal --archivo ../datos/entradas/programa_valido.agro --mostrar-ast
python -m src.principal --archivo ../datos/entradas/programa_invalido.agro
python -m src.principal --texto "WHEN reserva_agua < 18 THEN suspender nebulizacion;" --mostrar-ast
```

Se debe usar `python -m src.principal`; ejecutar `python src/principal.py`
directamente no encuentra el paquete `src`.

Código de salida: 0 si la entrada es válida, 1 si hay error léxico o sintáctico
y 2 si hay problemas de lectura del archivo o se supera un límite de la
implementación.

## Formato de entrada

La entrada es texto con una o más reglas. Cada regla termina en `;`:

```text
WHEN <condicion> THEN <accion> [AND <accion> ...] [WITH PRIORITY <entero>];
```

- Condición: comparaciones `ID operador valor`, con operadores
  `>  <  >=  <=  ==  !=`, combinadas con `AND`, `OR`, `NOT` y paréntesis.
  `NOT` liga más fuerte que `AND`, y `AND` más fuerte que `OR`.
- Valor: entero no negativo, `TRUE` o `FALSE`.
- Acción: un verbo y, opcionalmente, un objetivo (`cerrar valvula`).
- Las palabras reservadas no distinguen mayúsculas de minúsculas.
- Identificadores: letras ASCII, dígitos y guion bajo, sin empezar con dígito.
- No hay decimales, negativos, comentarios, cadenas ni letras con tilde o ñ.

## Ejemplos válidos

```text
WHEN reserva_agua < 18 THEN suspender nebulizacion;
WHEN luz_exterior >= 720 THEN extender malla_sombra;
WHEN bandeja_seca == TRUE THEN habilitar microgoteo;
WHEN fuga_detectada == TRUE THEN cerrar valvula AND detener bomba WITH PRIORITY 9;
WHEN (condensacion == TRUE OR humedad_aire > 88) THEN abrir rejilla_alta;
WHEN NOT mantenimiento == TRUE THEN habilitar bomba_reserva;
WHEN humedad_sustrato <= 26 AND reserva_agua > 18 THEN iniciar microgoteo;
```

## Ejemplos inválidos (con el motivo)

```text
reserva_agua < 18 THEN suspender nebulizacion;      Falta WHEN al inicio
WHEN luz_exterior 720 THEN extender malla_sombra;   Falta operador relacional
WHEN caudal_entrada != THEN aislar circuito;         Falta valor después del operador
WHEN fuga_detectada == TRUE THEN cerrar valvula      Falta punto y coma al final
WHEN bandeja_seca == TRUE THEN;                      Falta el nombre de la acción
WHEN (condensacion == TRUE THEN abrir rejilla_alta;  Falta paréntesis de cierre
WHEN OR lluvia_intensa == TRUE THEN recoger cubierta; OR sin condición izquierda
```

Los errores indican la posición (índice de carácter desde 0), lo esperado y lo
encontrado:

```text
ENTRADA INVALIDA
Error sintactico en la posicion 31 [regla 1, condicion]: se esperaba un identificador, pero se encontro 'THEN'.
```

## Visualización gráfica del AST

Para generar una imagen PNG del árbol de sintaxis abstracta:

```powershell
pip install graphviz
python -m herramientas.generar_grafico_ast --archivo ../datos/entradas/programa_valido.agro
python -m herramientas.generar_grafico_ast --texto "WHEN reserva_agua < 18 THEN suspender nebulizacion;"
python -m herramientas.generar_grafico_ast --archivo ../datos/entradas/programa_valido.agro --salida ../resultados/mi_ast
```

El resultado se guarda en `resultados/ast.png` por defecto. Requiere Graphviz
instalado en el sistema operativo además del paquete de Python.

## Pruebas y verificación

Desde `codigo/`:

```powershell
python -m unittest discover -v
python -m herramientas.ejecutar_casos
python -m herramientas.verificar_gramatica
```

- `unittest` ejecuta las pruebas automatizadas.
- `ejecutar_casos` ejecuta los 30 casos (12 válidos, 12 inválidos y 6 límite)
  y actualiza `resultados/`.
- `verificar_gramatica` calcula FIRST/FOLLOW y la tabla LL(1) por punto fijo, los
  contrasta con `docs/gramatica.md` y comprueba que no hay conflictos.

`resultados/casos_prueba.csv` es una salida de la verificación, no una entrada
del parser.

## Límites conocidos

- Números de hasta 1000 dígitos.
- El anidamiento muy profundo (cientos de paréntesis o `NOT` seguidos) se informa
  como límite de implementación, no como error de la gramática.
- El análisis léxico se hace completo antes del sintáctico: un símbolo no
  reconocido se informa aunque haya un error sintáctico anterior.
- El análisis se detiene en el primer error.

## Créditos

El analizador léxico parte del material de apoyo entregado por el docente
Marcos Levano. El parser, el AST y la gramática son propios del proyecto.
