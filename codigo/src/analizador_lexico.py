"""Analizador lexico basado en el material de apoyo entregado por el docente."""

import re
from dataclasses import dataclass

# Base: anlizador_lexico1(apoyo).ipynb, material del docente Marcos Levano.
# Se conserva la tokenizacion por expresiones regulares y la reclasificacion
# de palabras reservadas. Adaptaciones del proyecto: Token con posicion, EOF,
# WITH/PRIORITY, digitos ASCII y soporte de saltos de linea de Windows.


@dataclass(frozen=True)
class Token:
    """Representa un token junto con su posicion dentro del texto original."""

    tipo: str
    lexema: str
    posicion: int


class ErrorLexico(ValueError):
    """Error producido cuando aparece un simbolo que el lenguaje no reconoce."""


def analizador_lexico(cadena: str) -> list[Token]:
    """Convierte una cadena de SACgro en una lista de tokens.

    La estructura principal conserva el analizador lexico del material de apoyo.
    Se agrego la posicion de cada token y un token EOF para facilitar el parser.
    """

    especificacion_tokens = [
        ("NUM", r"[0-9]+"),
        ("OP_REL", r">=|<=|==|!=|>|<"),
        ("PUNTO_COMA", r";"),
        ("PARENT_IZQ", r"\("),
        ("PARENT_DER", r"\)"),
        ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
        ("ESPACIO", r"[ \t\r\n]+"),
        ("ERROR", r"."),
    ]

    patron = "|".join(
        f"(?P<{nombre}>{expresion})"
        for nombre, expresion in especificacion_tokens
    )

    palabras_reservadas = {
        "WHEN",
        "THEN",
        "AND",
        "OR",
        "NOT",
        "TRUE",
        "FALSE",
        "WITH",
        "PRIORITY",
    }

    tokens: list[Token] = []

    for coincidencia in re.finditer(patron, cadena):
        tipo = coincidencia.lastgroup
        lexema = coincidencia.group()
        posicion = coincidencia.start()

        if tipo == "ESPACIO":
            continue

        if tipo == "ID" and lexema.upper() in palabras_reservadas:
            tipo = lexema.upper()

        if tipo == "ERROR":
            raise ErrorLexico(
                f"Error lexico en la posicion {posicion}: "
                f"simbolo no reconocido '{lexema}'."
            )

        tokens.append(Token(tipo, lexema, posicion))

    tokens.append(Token("EOF", "", len(cadena)))
    return tokens

