"""Bateria de pruebas validas, invalidas y de casos limite."""

import unittest
import subprocess
import sys
from pathlib import Path

from src.analizador_lexico import ErrorLexico, analizador_lexico
from src.analizador_sintactico import ErrorLimite, ErrorSintactico, analizar_texto
from src.nodos_ast import Negacion


CASOS_VALIDOS = [
    "WHEN reserva_agua < 18 THEN suspender nebulizacion;",
    "WHEN luz_exterior >= 720 THEN extender malla_sombra;",
    "WHEN bandeja_seca == TRUE THEN habilitar microgoteo;",
    "WHEN puerta_lateral == FALSE THEN avisar encargado;",
    "WHEN humedad_sustrato <= 26 AND reserva_agua > 18 THEN iniciar microgoteo;",
    "WHEN viento_techo > 45 OR lluvia_intensa == TRUE THEN recoger cubierta;",
    "WHEN NOT mantenimiento == TRUE THEN habilitar bomba_reserva;",
    "WHEN (condensacion == TRUE OR humedad_aire > 88) THEN abrir rejilla_alta;",
    "WHEN fuga_detectada == TRUE THEN cerrar valvula AND detener bomba;",
    "WHEN (luz_exterior < 90 AND horario_nocturno == FALSE) OR revision == TRUE THEN encender luz_pasillo;",
    "WHEN caudal_entrada != 12 THEN aislar circuito_riego WITH PRIORITY 9;",
    "when filtro_saturado == true then solicitar limpieza;",
]


CASOS_INVALIDOS = [
    "",
    "reserva_agua < 18 THEN suspender nebulizacion;",
    "WHEN luz_exterior 720 THEN extender malla_sombra;",
    "WHEN caudal_entrada != THEN aislar circuito;",
    "WHEN filtro_saturado == TRUE solicitar limpieza;",
    "WHEN bandeja_seca == TRUE THEN;",
    "WHEN fuga_detectada == TRUE THEN cerrar valvula",
    "WHEN reserva_agua < 18 THEN suspender nebulizacion@;",
    "WHEN (condensacion == TRUE THEN abrir rejilla_alta;",
    "WHEN humedad_sustrato < 26 AND THEN iniciar microgoteo;",
    "WHEN OR lluvia_intensa == TRUE THEN recoger cubierta;",
    "WHEN fuga_detectada == TRUE THEN detener bomba WITH PRIORITY;",
]


CASOS_LIMITE_VALIDOS = [
    "WHEN revision == TRUE THEN registrar;",
    "WHEN NOT NOT mantenimiento == FALSE THEN habilitar bomba_reserva;",
    "WHEN (((condensacion == TRUE))) THEN abrir rejilla_alta;",
    "WHEN reserva_agua<18 THEN suspender nebulizacion;WHEN fuga_detectada==TRUE THEN cerrar valvula;",
    "WHEN sensor_bandeja_2 == FALSE THEN revisar WITH PRIORITY 0;",
    "WHEN pulsos_acumulados >= 999999999 THEN reiniciar contador;",
]


class PruebasAnalizador(unittest.TestCase):
    def test_12_entradas_validas(self):
        for entrada in CASOS_VALIDOS:
            with self.subTest(entrada=entrada):
                arbol = analizar_texto(entrada)
                self.assertGreaterEqual(len(arbol.reglas), 1)

    def test_12_entradas_invalidas(self):
        for entrada in CASOS_INVALIDOS:
            with self.subTest(entrada=entrada):
                with self.assertRaises((ErrorLexico, ErrorSintactico)):
                    analizar_texto(entrada)

    def test_6_casos_limite(self):
        for entrada in CASOS_LIMITE_VALIDOS:
            with self.subTest(entrada=entrada):
                arbol = analizar_texto(entrada)
                self.assertGreaterEqual(len(arbol.reglas), 1)

    def test_ast_con_prioridad_de_operadores(self):
        entrada = (
            "WHEN fuga_detectada == TRUE OR reserva_agua < 18 AND NOT mantenimiento == TRUE "
            "THEN detener bomba;"
        )
        condicion = analizar_texto(entrada).reglas[0].condicion
        self.assertEqual(condicion.operador, "OR")
        self.assertEqual(condicion.derecha.operador, "AND")
        self.assertIsInstance(condicion.derecha.derecha, Negacion)

    def test_extension_de_prioridad_en_ast(self):
        entrada = "WHEN fuga_detectada == TRUE THEN cerrar valvula WITH PRIORITY 10;"
        arbol = analizar_texto(entrada)
        self.assertEqual(arbol.reglas[0].prioridad, 10)
        self.assertIn("Prioridad(10)", arbol.como_texto())

    def test_lexer_conserva_el_material_de_apoyo(self):
        # Este unico ejemplo se conserva a proposito para contrastar el apoyo
        # del docente Marcos Levano; no es un escenario original del proyecto.
        tokens = analizador_lexico(
            "WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;"
        )
        tipos = [token.tipo for token in tokens]
        self.assertEqual(
            tipos,
            [
                "WHEN",
                "ID",
                "OP_REL",
                "NUM",
                "AND",
                "ID",
                "OP_REL",
                "NUM",
                "THEN",
                "ID",
                "ID",
                "PUNTO_COMA",
                "EOF",
            ],
        )


    def test_parentesis_cambian_agrupacion(self):
        condicion = analizar_texto("WHEN (fuga == TRUE OR reserva < 18) AND revision == FALSE THEN detener bomba;").reglas[0].condicion
        self.assertEqual(condicion.operador, "AND")
        self.assertEqual(condicion.izquierda.operador, "OR")

    def test_acciones_y_reglas_se_conservan(self):
        arbol = analizar_texto("WHEN fuga == TRUE THEN cerrar valvula AND detener bomba WITH PRIORITY 9; WHEN revision == TRUE THEN registrar;")
        self.assertEqual(len(arbol.reglas), 2)
        self.assertEqual([(a.verbo, a.objetivo) for a in arbol.reglas[0].acciones], [("cerrar", "valvula"), ("detener", "bomba")])
        self.assertEqual(arbol.reglas[0].prioridad, 9)
        self.assertIsNone(arbol.reglas[1].prioridad)

    def test_saltos_windows(self):
        arbol = analizar_texto("WHEN fuga == TRUE THEN registrar;\r\nWHEN revision == FALSE THEN avisar;")
        self.assertEqual(len(arbol.reglas), 2)

    def test_numero_no_ascii(self):
        with self.assertRaises(ErrorLexico):
            analizar_texto("WHEN reserva < \u0661 THEN avisar;")

    def test_limites_controlados(self):
        entradas = ["WHEN " + "(" * 400 + "fuga == TRUE" + ")" * 400 + " THEN avisar;",
                    "WHEN reserva < " + "9" * 1001 + " THEN avisar;",
                    "WHEN fuga == TRUE THEN avisar WITH PRIORITY " + "9" * 1001 + ";"]
        for entrada in entradas:
            with self.subTest(longitud=len(entrada)):
                with self.assertRaises(ErrorLimite):
                    analizar_texto(entrada)

    def test_error_localizado(self):
        entrada = "WHEN caudal != THEN aislar circuito;"
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar_texto(entrada)
        self.assertIn(str(entrada.index("THEN")), str(contexto.exception))
        self.assertIn("numero", str(contexto.exception))

    def test_consola(self):
        raiz = Path(__file__).resolve().parents[1]
        casos = [("--archivo", "../datos/entradas/programa_valido.agro", 0),
                 ("--archivo", "../datos/entradas/programa_invalido.agro", 1),
                 ("--archivo", "../datos/entradas/no_existe_1148.agro", 2)]
        for opcion, entrada, codigo in casos:
            with self.subTest(entrada=entrada):
                salida = subprocess.run([sys.executable, "-m", "src.principal", opcion, entrada, "--mostrar-ast"], cwd=raiz, capture_output=True, text=True)
                self.assertEqual(salida.returncode, codigo)
                self.assertNotIn("Traceback", salida.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=2)

