# Entradas del analizador

- entradas/programa_valido.agro: tres reglas válidas con condiciones, acciones
  y prioridades. Se espera aceptación y un AST con tres reglas.
- entradas/programa_invalido.agro: falta una condición después de AND. Se
  espera un error sintáctico; se conserva así para demostrar el rechazo.

Para agregar casos propios, crear un archivo de texto aquí y pasar su ruta con
--archivo. No hace falta instalar una base de datos. Los casos automatizados
están definidos en codigo/pruebas/test_analizador.py.
