"""Interfaz de consola para probar archivos o reglas escritas directamente."""

import argparse
from pathlib import Path

from src.analizador_lexico import ErrorLexico
from src.analizador_sintactico import ErrorLimite, ErrorSintactico, analizar_texto


def crear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analizador sintactico del lenguaje AgroReglas"
    )
    grupo_entrada = parser.add_mutually_exclusive_group(required=True)
    grupo_entrada.add_argument("--texto", help="Regla o programa escrito entre comillas")
    grupo_entrada.add_argument("--archivo", help="Ruta de un archivo con reglas")
    parser.add_argument(
        "--mostrar-ast",
        action="store_true",
        help="Muestra el AST cuando la entrada es valida",
    )
    return parser.parse_args()


def ejecutar() -> int:
    argumentos = crear_argumentos()

    try:
        if argumentos.archivo:
            texto_entrada = Path(argumentos.archivo).read_text(encoding="utf-8-sig")
        else:
            texto_entrada = argumentos.texto
        arbol = analizar_texto(texto_entrada)
        texto_arbol = arbol.como_texto() if argumentos.mostrar_ast else None
    except (OSError, UnicodeError) as error:
        print(f"No se pudo leer el archivo: {error}")
        return 2
    except (ErrorLimite, RecursionError) as error:
        print(f"LIMITE DE IMPLEMENTACION: {error}")
        return 2
    except (ErrorLexico, ErrorSintactico) as error:
        print(f"ENTRADA INVALIDA\n{error}")
        return 1

    print(f"ENTRADA VALIDA: se reconocieron {len(arbol.reglas)} regla(s).")
    if argumentos.mostrar_ast:
        print("\nARBOL DE SINTAXIS ABSTRACTA")
        print(texto_arbol)
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar())

