"""Genera una imagen del arbol de sintaxis abstracta usando Graphviz.

Uso desde la carpeta codigo/:

    python -m herramientas.generar_grafico_ast --texto "WHEN reserva_agua < 18 THEN suspender nebulizacion;"
    python -m herramientas.generar_grafico_ast --archivo ../datos/entradas/programa_valido.agro

El resultado se guarda en resultados/ast.png (por defecto) o en la ruta
indicada con --salida. Requiere Graphviz instalado en el sistema
(https://graphviz.org/) y el paquete graphviz de Python:

    pip install graphviz
"""

import argparse
from pathlib import Path

from src.analizador_lexico import ErrorLexico
from src.analizador_sintactico import ErrorSintactico, ErrorLimite, analizar_texto
from src.nodos_ast import (
    Accion,
    Comparacion,
    Negacion,
    NodoAST,
    OperacionLogica,
    Programa,
    Regla,
)

try:
    import graphviz
except ImportError:
    graphviz = None


_contador = 0


def _nuevo_id() -> str:
    """Devuelve un identificador unico para cada nodo del grafo."""
    global _contador
    _contador += 1
    return f"n{_contador}"


def _agregar_nodo(grafo: "graphviz.Digraph", nodo: NodoAST) -> str:
    """Recorre el AST y agrega nodos y aristas al grafo Graphviz."""

    nodo_id = _nuevo_id()

    if isinstance(nodo, Programa):
        grafo.node(nodo_id, "Programa", shape="box", style="filled",
                   fillcolor="#2D2D2D", fontcolor="white", fontname="Arial Bold")
        for regla in nodo.reglas:
            hijo_id = _agregar_nodo(grafo, regla)
            grafo.edge(nodo_id, hijo_id)

    elif isinstance(nodo, Regla):
        grafo.node(nodo_id, "Regla", shape="box", style="filled",
                   fillcolor="#4D4D4D", fontcolor="white", fontname="Arial Bold")

        # Condicion
        cond_id = _nuevo_id()
        grafo.node(cond_id, "Condicion", shape="ellipse", style="filled",
                   fillcolor="#707070", fontcolor="white", fontname="Arial")
        grafo.edge(nodo_id, cond_id)
        hijo_cond = _agregar_nodo(grafo, nodo.condicion)
        grafo.edge(cond_id, hijo_cond)

        # Acciones
        acc_id = _nuevo_id()
        grafo.node(acc_id, "Acciones", shape="ellipse", style="filled",
                   fillcolor="#707070", fontcolor="white", fontname="Arial")
        grafo.edge(nodo_id, acc_id)
        for accion in nodo.acciones:
            hijo_acc = _agregar_nodo(grafo, accion)
            grafo.edge(acc_id, hijo_acc)

        # Prioridad
        if nodo.prioridad is not None:
            prio_id = _nuevo_id()
            grafo.node(prio_id, f"Prioridad({nodo.prioridad})", shape="diamond",
                       style="filled", fillcolor="#707070", fontcolor="white",
                       fontname="Arial")
            grafo.edge(nodo_id, prio_id)

    elif isinstance(nodo, OperacionLogica):
        grafo.node(nodo_id, nodo.operador, shape="circle", style="filled",
                   fillcolor="#5A5A5A", fontcolor="white", fontname="Arial Bold",
                   width="0.6")
        izq_id = _agregar_nodo(grafo, nodo.izquierda)
        der_id = _agregar_nodo(grafo, nodo.derecha)
        grafo.edge(nodo_id, izq_id)
        grafo.edge(nodo_id, der_id)

    elif isinstance(nodo, Negacion):
        grafo.node(nodo_id, "NOT", shape="circle", style="filled",
                   fillcolor="#5A5A5A", fontcolor="white", fontname="Arial Bold",
                   width="0.6")
        hijo_id = _agregar_nodo(grafo, nodo.expresion)
        grafo.edge(nodo_id, hijo_id)

    elif isinstance(nodo, Comparacion):
        valor_mostrado = str(nodo.valor).lower() if isinstance(nodo.valor, bool) else nodo.valor
        etiqueta = f"{nodo.identificador} {nodo.operador} {valor_mostrado}"
        grafo.node(nodo_id, etiqueta, shape="box", style="rounded,filled",
                   fillcolor="#E0E0E0", fontcolor="#2D2D2D", fontname="Arial")

    elif isinstance(nodo, Accion):
        contenido = nodo.verbo
        if nodo.objetivo is not None:
            contenido += f" {nodo.objetivo}"
        grafo.node(nodo_id, contenido, shape="box", style="rounded,filled",
                   fillcolor="#E0E0E0", fontcolor="#2D2D2D", fontname="Arial")

    return nodo_id


def generar_grafico(arbol: Programa, ruta_salida: str = "ast") -> str:
    """Crea el archivo grafico del AST y devuelve la ruta generada.

    Args:
        arbol: AST producido por el parser.
        ruta_salida: ruta sin extension; Graphviz agrega .png automaticamente.

    Returns:
        Ruta completa del archivo generado.
    """
    if graphviz is None:
        raise ImportError(
            "Se requiere el paquete graphviz. Instalar con: pip install graphviz"
        )

    global _contador
    _contador = 0

    grafo = graphviz.Digraph(
        "AST",
        format="png",
        graph_attr={
            "rankdir": "TB",
            "bgcolor": "white",
            "dpi": "150",
            "margin": "0.3",
        },
        node_attr={"fontsize": "11"},
        edge_attr={"color": "#999999", "arrowsize": "0.7"},
    )

    _agregar_nodo(grafo, arbol)
    grafo.render(ruta_salida, cleanup=False)
    # Eliminar el archivo fuente .gv que Graphviz deja junto al .png.
    archivo_fuente = Path(ruta_salida)
    if archivo_fuente.exists():
        try:
            archivo_fuente.unlink()
        except OSError:
            pass  # En algunos entornos el borrado no esta permitido.
    return f"{ruta_salida}.png"


def main():
    parser = argparse.ArgumentParser(
        description="Genera una imagen PNG del AST de SACgro"
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--texto", help="Regla o programa entre comillas")
    grupo.add_argument("--archivo", help="Ruta de un archivo .agro")
    parser.add_argument(
        "--salida",
        default=None,
        help="Ruta de salida sin extension (por defecto: resultados/ast)",
    )
    args = parser.parse_args()

    try:
        if args.archivo:
            texto = Path(args.archivo).read_text(encoding="utf-8-sig")
        else:
            texto = args.texto

        arbol = analizar_texto(texto)
    except (OSError, UnicodeError) as error:
        print(f"No se pudo leer el archivo: {error}")
        raise SystemExit(2)
    except (ErrorLexico, ErrorSintactico) as error:
        print(f"ENTRADA INVALIDA\n{error}")
        raise SystemExit(1)
    except ErrorLimite as error:
        print(f"LIMITE DE IMPLEMENTACION: {error}")
        raise SystemExit(2)

    raiz = Path(__file__).resolve().parents[2]
    ruta = args.salida or str(raiz / "resultados" / "ast")

    try:
        archivo = generar_grafico(arbol, ruta)
        print(f"AST generado en: {archivo}")
    except ImportError as error:
        print(f"Error: {error}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
