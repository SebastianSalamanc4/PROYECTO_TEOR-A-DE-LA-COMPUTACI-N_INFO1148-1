"""Parser predictivo por descenso recursivo para SACgro."""

from __future__ import annotations

from src.analizador_lexico import Token, analizador_lexico
from src.nodos_ast import (
    Accion,
    Comparacion,
    Negacion,
    NodoAST,
    OperacionLogica,
    Programa,
    Regla,
)


class ErrorSintactico(ValueError):
    """Error con informacion del token y la posicion donde fallo el parser."""


class ErrorLimite(ValueError):
    """Entrada que supera la capacidad de esta implementacion, no de la GLC."""


class AnalizadorSintactico:
    """Implementa manualmente la gramatica LL(1) de SACgro."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.indice_actual = 0
        self.regla_actual = 0
        self.contexto = ""

    @property
    def token_actual(self) -> Token:
        return self.tokens[self.indice_actual]

    def avanzar(self) -> Token:
        token_consumido = self.token_actual
        if self.indice_actual < len(self.tokens) - 1:
            self.indice_actual += 1
        return token_consumido

    def consumir(self, tipo_esperado: str, descripcion: str | None = None) -> Token:
        if self.token_actual.tipo == tipo_esperado:
            return self.avanzar()

        esperado = descripcion or tipo_esperado
        encontrado = self.token_actual.lexema or "fin de entrada"
        ctx = ""
        if self.regla_actual > 0:
            ctx = f" [regla {self.regla_actual}"
            if self.contexto:
                ctx += f", {self.contexto}"
            ctx += "]"
        raise ErrorSintactico(
            f"Error sintactico en la posicion {self.token_actual.posicion}{ctx}: "
            f"se esperaba {esperado}, pero se encontro '{encontrado}'."
        )

    def analizar(self) -> Programa:
        try:
            programa = self.programa()
            self.consumir("EOF", "el fin de la entrada")
            return programa
        except RecursionError as error:
            raise ErrorLimite("Entrada demasiado anidada para esta implementacion.") from error

    def numero(self, token: Token) -> int:
        # Un limite explicito evita depender de la version de Python instalada.
        if len(token.lexema) > 1000:
            raise ErrorLimite(
                f"Numero demasiado largo en la posicion {token.posicion}: maximo 1000 digitos."
            )
        return int(token.lexema)

    def programa(self) -> Programa:
        # <programa> -> <regla> <lista_reglas>
        if self.token_actual.tipo != "WHEN":
            self.consumir("WHEN", "la palabra reservada WHEN")

        reglas = [self.regla()]
        while self.token_actual.tipo == "WHEN":
            reglas.append(self.regla())
        return Programa(reglas)

    def regla(self) -> Regla:
        # <regla> -> WHEN <expresion> THEN <lista_acciones> <prioridad> PUNTO_COMA
        self.regla_actual += 1
        self.contexto = "condicion"
        self.consumir("WHEN", "la palabra reservada WHEN")
        condicion = self.expresion()
        self.consumir("THEN", "la palabra reservada THEN")
        self.contexto = "acciones"
        acciones = self.lista_acciones()
        self.contexto = "prioridad"
        prioridad = self.prioridad()
        self.consumir("PUNTO_COMA", "un punto y coma ';'")
        return Regla(condicion, acciones, prioridad)

    def expresion(self) -> NodoAST:
        # <expresion> -> <termino> <expresion_r>
        nodo = self.termino()
        while self.token_actual.tipo == "OR":
            operador = self.avanzar().lexema.upper()
            nodo_derecho = self.termino()
            nodo = OperacionLogica(operador, nodo, nodo_derecho)
        return nodo

    def termino(self) -> NodoAST:
        # <termino> -> <factor> <termino_r>
        nodo = self.factor()
        while self.token_actual.tipo == "AND":
            operador = self.avanzar().lexema.upper()
            nodo_derecho = self.factor()
            nodo = OperacionLogica(operador, nodo, nodo_derecho)
        return nodo

    def factor(self) -> NodoAST:
        # <factor> -> NOT <factor> | ( <expresion> ) | <comparacion>
        if self.token_actual.tipo == "NOT":
            self.avanzar()
            return Negacion(self.factor())

        if self.token_actual.tipo == "PARENT_IZQ":
            self.avanzar()
            nodo = self.expresion()
            self.consumir("PARENT_DER", "un parentesis de cierre ')'")
            return nodo

        return self.comparacion()

    def comparacion(self) -> Comparacion:
        # <comparacion> -> ID OP_REL <valor>
        identificador = self.consumir("ID", "un identificador")
        operador = self.consumir("OP_REL", "un operador relacional")
        valor = self.valor()
        return Comparacion(identificador.lexema, operador.lexema, valor)

    def valor(self) -> int | bool:
        # <valor> -> NUM | TRUE | FALSE
        if self.token_actual.tipo == "NUM":
            return self.numero(self.avanzar())
        if self.token_actual.tipo == "TRUE":
            self.avanzar()
            return True
        if self.token_actual.tipo == "FALSE":
            self.avanzar()
            return False
        self.consumir("NUM", "un numero o un valor booleano TRUE/FALSE")
        raise AssertionError("El metodo consumir siempre genera una excepcion")

    def lista_acciones(self) -> list[Accion]:
        # <lista_acciones> -> <accion> <lista_acciones_r>
        acciones = [self.accion()]
        while self.token_actual.tipo == "AND":
            self.avanzar()
            acciones.append(self.accion())
        return acciones

    def accion(self) -> Accion:
        # <accion> -> ID <argumento_accion>
        verbo = self.consumir("ID", "el nombre de una accion")
        objetivo = None
        if self.token_actual.tipo == "ID":
            objetivo = self.avanzar().lexema
        return Accion(verbo.lexema, objetivo)

    def prioridad(self) -> int | None:
        # <prioridad> -> WITH PRIORITY NUM | epsilon
        if self.token_actual.tipo != "WITH":
            return None

        self.avanzar()
        self.consumir("PRIORITY", "la palabra reservada PRIORITY")
        numero = self.consumir("NUM", "un numero de prioridad")
        return self.numero(numero)


def analizar_texto(cadena: str) -> Programa:
    """Funcion de uso directo: ejecuta el lexer y luego el parser."""

    tokens = analizador_lexico(cadena)
    return AnalizadorSintactico(tokens).analizar()

