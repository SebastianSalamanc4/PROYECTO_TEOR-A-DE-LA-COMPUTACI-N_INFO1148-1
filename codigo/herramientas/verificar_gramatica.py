"""Contrasta el documento formal con FIRST/FOLLOW calculados por punto fijo.

Es una comprobacion independiente: el parser del proyecto sigue siendo manual.
No genera ni sustituye su codigo.
"""

from pathlib import Path
import re


def verificar():
    raiz = Path(__file__).resolve().parents[2]
    documento = (raiz / "docs/gramatica.md").read_text(encoding="utf-8")
    bloque = documento.split("### Producciones")[1].split("```text")[1].split("```")[0]
    gramatica = {}
    for linea in bloque.splitlines():
        if "->" in linea:
            izquierda, derecha = linea.split("->")
            izquierda = izquierda.strip()
            gramatica[izquierda] = []
        elif linea.strip().startswith("|"):
            derecha = linea.strip()[1:]
        else:
            continue
        gramatica[izquierda].extend(
            [] if alternativa.strip() == "epsilon" else alternativa.split()
            for alternativa in derecha.split("|")
        )
    primeros = {simbolo: set() for simbolo in gramatica}
    siguientes = {simbolo: set() for simbolo in gramatica}
    siguientes["<programa>"].add("EOF")

    def primero_secuencia(secuencia):
        resultado = set()
        for simbolo in secuencia:
            conjunto = primeros[simbolo] if simbolo in gramatica else {simbolo}
            resultado.update(conjunto - {"epsilon"})
            if "epsilon" not in conjunto:
                return resultado
        return resultado | {"epsilon"}

    cambios = True
    while cambios:
        anterior = {simbolo: conjunto.copy() for simbolo, conjunto in primeros.items()}
        for izquierda, alternativas in gramatica.items():
            for derecha in alternativas:
                primeros[izquierda].update(primero_secuencia(derecha))
        cambios = anterior != primeros

    cambios = True
    while cambios:
        anterior = {simbolo: conjunto.copy() for simbolo, conjunto in siguientes.items()}
        for izquierda, alternativas in gramatica.items():
            for derecha in alternativas:
                for indice, simbolo in enumerate(derecha):
                    if simbolo not in gramatica:
                        continue
                    primero_resto = primero_secuencia(derecha[indice + 1:])
                    siguientes[simbolo].update(primero_resto - {"epsilon"})
                    if "epsilon" in primero_resto:
                        siguientes[simbolo].update(siguientes[izquierda])
        cambios = anterior != siguientes

    revisados = set()
    for linea in documento.split("\n### FIRST y FOLLOW")[1].split("\n## Tabla LL(1)")[0].splitlines():
        if not linea.startswith("| `<"):
            continue
        columnas = linea.split("|")
        simbolo = columnas[1].strip().strip("`")
        conjuntos = [set(re.findall(r"[A-Z_]+|epsilon", columna)) for columna in columnas[2:4]]
        assert conjuntos == [primeros[simbolo], siguientes[simbolo]], simbolo
        revisados.add(simbolo)
    assert revisados == set(gramatica)

    tabla = {}
    for izquierda, alternativas in gramatica.items():
        for derecha in alternativas:
            seleccion = primero_secuencia(derecha)
            anticipaciones = seleccion - {"epsilon"}
            if "epsilon" in seleccion:
                anticipaciones |= siguientes[izquierda]
            for anticipacion in anticipaciones:
                clave = (izquierda, anticipacion)
                assert clave not in tabla, f"Conflicto LL(1): {clave}"
                tabla[clave] = derecha
    tabla_documentada = {}
    for linea in documento.split("\n## Tabla LL(1)")[1].split("\n## Fin")[0].splitlines():
        if not linea.startswith("| `<"):
            continue
        columnas = linea.split("|")
        simbolo = columnas[1].strip().strip("`")
        produccion = columnas[3].strip().strip("`")
        for anticipacion in re.findall(r"`([^`]+)`", columnas[2]):
            clave = (simbolo, anticipacion)
            assert clave not in tabla_documentada
            tabla_documentada[clave] = [] if produccion == "epsilon" else produccion.split()
    assert tabla == tabla_documentada, "La tabla de docs/gramatica.md no coincide"

    # Contraste con un reconocedor de pila, construido solo para esta auditoria.
    from pruebas.test_analizador import CASOS_VALIDOS, CASOS_INVALIDOS, CASOS_LIMITE_VALIDOS
    from src.analizador_lexico import analizador_lexico, ErrorLexico
    from src.analizador_sintactico import analizar_texto, ErrorSintactico

    def reconoce(entrada):
        try:
            tokens = analizador_lexico(entrada)
        except ErrorLexico:
            return False
        pila = ["EOF", "<programa>"]
        indice = 0
        while pila:
            simbolo = pila.pop()
            actual = tokens[indice].tipo
            if simbolo in gramatica:
                produccion = tabla.get((simbolo, actual))
                if produccion is None:
                    return False
                pila.extend(reversed(produccion))
            elif simbolo == actual:
                indice += 1
            else:
                return False
        return indice == len(tokens)

    casos = CASOS_VALIDOS + CASOS_INVALIDOS + CASOS_LIMITE_VALIDOS
    for entrada in casos:
        try:
            analizar_texto(entrada)
            aceptada = True
        except (ErrorLexico, ErrorSintactico):
            aceptada = False
        assert reconoce(entrada) == aceptada, entrada
    resultado = (f"No terminales comprobados: {len(gramatica)}\n"
                 f"Celdas LL(1) ocupadas: {len(tabla)}\n"
                 "FIRST/FOLLOW: coinciden con docs/gramatica.md\n"
                 "Tabla documentada: coincide con el calculo\n"
                 "Conflictos LL(1): 0\n"
                 f"Comparaciones tabla/parser: {len(casos)}, sin diferencias\n")
    (raiz / "resultados/verificacion_gramatica.txt").write_text(resultado, encoding="utf-8")
    print(resultado)


if __name__ == "__main__":
    verificar()
