"""Nodos del arbol de sintaxis abstracta de AgroReglas."""

from __future__ import annotations

from dataclasses import dataclass


class NodoAST:
    """Clase base para los nodos que pueden mostrarse en forma jerarquica."""

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        raise NotImplementedError

    def como_texto(self) -> str:
        return "\n".join(self.lineas_arbol())


@dataclass
class Programa(NodoAST):
    reglas: list[Regla]

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        lineas = [f"{'  ' * nivel}Programa"]
        for regla in self.reglas:
            lineas.extend(regla.lineas_arbol(nivel + 1))
        return lineas


@dataclass
class Regla(NodoAST):
    condicion: NodoAST
    acciones: list[Accion]
    prioridad: int | None = None

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        sangria = "  " * nivel
        lineas = [f"{sangria}Regla", f"{sangria}  Condicion"]
        lineas.extend(self.condicion.lineas_arbol(nivel + 2))
        lineas.append(f"{sangria}  Acciones")
        for accion in self.acciones:
            lineas.extend(accion.lineas_arbol(nivel + 2))
        if self.prioridad is not None:
            lineas.append(f"{sangria}  Prioridad({self.prioridad})")
        return lineas


@dataclass
class OperacionLogica(NodoAST):
    operador: str
    izquierda: NodoAST
    derecha: NodoAST

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        lineas = [f"{'  ' * nivel}OperacionLogica({self.operador})"]
        lineas.extend(self.izquierda.lineas_arbol(nivel + 1))
        lineas.extend(self.derecha.lineas_arbol(nivel + 1))
        return lineas


@dataclass
class Negacion(NodoAST):
    expresion: NodoAST

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        lineas = [f"{'  ' * nivel}Negacion(NOT)"]
        lineas.extend(self.expresion.lineas_arbol(nivel + 1))
        return lineas


@dataclass
class Comparacion(NodoAST):
    identificador: str
    operador: str
    valor: int | bool

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        valor_mostrado = str(self.valor).lower() if isinstance(self.valor, bool) else self.valor
        return [
            f"{'  ' * nivel}Comparacion({self.identificador} {self.operador} {valor_mostrado})"
        ]


@dataclass
class Accion(NodoAST):
    verbo: str
    objetivo: str | None = None

    def lineas_arbol(self, nivel: int = 0) -> list[str]:
        contenido = self.verbo
        if self.objetivo is not None:
            contenido += f" {self.objetivo}"
        return [f"{'  ' * nivel}Accion({contenido})"]

