"""Ejecuta los casos del equipo y guarda evidencia real, sin simular una consola."""

import csv
from pathlib import Path
import subprocess
import sys

from pruebas.test_analizador import CASOS_VALIDOS, CASOS_INVALIDOS, CASOS_LIMITE_VALIDOS
from src.analizador_sintactico import analizar_texto, ErrorSintactico
from src.analizador_lexico import ErrorLexico


OBSERVACIONES_VALIDOS = [
    "Regla simple con operador < y accion con argumento",
    "Operador >= con valor numerico grande",
    "Comparacion con valor booleano TRUE",
    "Comparacion con valor booleano FALSE y accion con argumento",
    "Condicion compuesta con AND entre dos comparaciones",
    "Condicion compuesta con OR entre dos comparaciones",
    "Uso de NOT como extension creativa (negacion de condicion)",
    "Parentesis para agrupar condicion OR (extension creativa)",
    "Multiples acciones separadas con AND (extension creativa)",
    "Parentesis con AND/OR combinados y precedencia alterada",
    "Operador != con extension WITH PRIORITY (extension creativa)",
    "Palabras reservadas en minusculas (case-insensitive)",
]

OBSERVACIONES_INVALIDOS = [
    "Entrada vacia: no hay tokens, se espera WHEN",
    "Falta WHEN al inicio de la regla",
    "Falta operador relacional entre identificador y valor",
    "Falta valor despues del operador relacional",
    "Falta THEN entre condicion y accion",
    "Falta nombre de accion despues de THEN",
    "Falta punto y coma al final de la regla",
    "Simbolo no reconocido @ detectado por el lexer",
    "Parentesis abierto sin cierre correspondiente",
    "AND sin factor a la derecha (se encontro THEN)",
    "OR al inicio de la condicion sin operando izquierdo",
    "WITH PRIORITY sin numero de prioridad",
]

OBSERVACIONES_LIMITE = [
    "Accion sin argumento (verbo solo): caso minimo",
    "Doble NOT anidado: recursion valida en <factor>",
    "Triple parentesis anidado: agrupacion profunda",
    "Dos reglas sin espacios entre ellas (PUNTO_COMA como separador)",
    "Prioridad con valor cero: limite inferior valido",
    "Numero muy grande (999999999): dentro del limite de 1000 digitos",
]


def ejecutar():
    raiz = Path(__file__).resolve().parents[2]
    carpeta = raiz / "resultados"
    carpeta.mkdir(exist_ok=True)
    filas = []
    for categoria, entradas, esperado, observaciones in [
        ("Valida", CASOS_VALIDOS, "Aceptada", OBSERVACIONES_VALIDOS),
        ("Invalida", CASOS_INVALIDOS, "Rechazada", OBSERVACIONES_INVALIDOS),
        ("Limite", CASOS_LIMITE_VALIDOS, "Aceptada", OBSERVACIONES_LIMITE),
    ]:
        for indice, entrada in enumerate(entradas):
            observacion = observaciones[indice]
            try:
                analizar_texto(entrada).como_texto()
                obtenido = "Aceptada"
            except (ErrorLexico, ErrorSintactico) as error:
                obtenido = "Rechazada"
                observacion += f" | {error}"
            filas.append([len(filas) + 1, categoria, entrada, esperado, obtenido, observacion])
    with (carpeta / "casos_prueba.csv").open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["numero", "categoria", "entrada", "resultado_esperado", "resultado_obtenido", "observacion"])
        escritor.writerows(filas)
    correcto = all(fila[3] == fila[4] for fila in filas)
    tareas = [
        ("ejecucion_pruebas.txt", ["-m", "unittest", "discover", "-v"], 0),
        ("ejecucion_valida.txt", ["-m", "src.principal", "--archivo", "../datos/entradas/programa_valido.agro", "--mostrar-ast"], 0),
        ("ejecucion_invalida.txt", ["-m", "src.principal", "--archivo", "../datos/entradas/programa_invalido.agro"], 1),
    ]
    for nombre, argumentos, codigo in tareas:
        salida = subprocess.run([sys.executable, *argumentos], cwd=raiz / "codigo", capture_output=True, text=True)
        (carpeta / nombre).write_text("python " + " ".join(argumentos) + "\n\n" + salida.stdout + salida.stderr, encoding="utf-8")
        correcto = correcto and salida.returncode == codigo
    print(f"Casos registrados: {len(filas)}. Verificacion: {'OK' if correcto else 'FALLO'}")
    return 0 if correcto else 1


if __name__ == "__main__":
    raise SystemExit(ejecutar())
