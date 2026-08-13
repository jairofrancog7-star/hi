# Reglas del proyecto

Reglas de trabajo obligatorias para la Guía Extensa de Entrenamiento Femenil Sub-17.

## Código

- **Python 3.11+ y solo librería estándar.** Sin `pip`, sin Node, sin
  dependencias externas de ningún tipo.
- **Nunca usar `assert` en producción.** `python -O` los borra; todo invariante
  se comprueba con `raise ErrorBuild(...)` (o su subclase adecuada).

## Terminal

- **PowerShell / Windows: el separador de comandos es `;`, nunca `&`.**

## Tests

- **Correr los tests con `python _run_tests.py`** (desde `guia-sub17/`).
- Confirmar que pasan antes de dar una tarea por terminada.

## Archivos scratch (PROHIBIDO)

- **Prohibido crear archivos scratch o temporales.** Nada de `_verif_*.py`,
  `_probe_*.py`, `_dbg.py`, `_smoke_*.py`, ni logs sueltos (`_t*.log`,
  `_grep.txt`, `_build*.txt`, `*_result.txt`, etc.), ni en la raíz de
  `guia-sub17/` ni en `.cache/`.
- **Para verificar algo, usar `python -c` inline en la terminal.** El resultado
  se lee directamente de la salida; no se deja rastro en el repositorio.
- Únicos archivos permitidos con prefijo `_`: `_run_all.py`, `_run_tests.py` y
  el reporte `.cache/_resultado.txt` que genera la corrida de pruebas.

## Flujo de trabajo

- **Una tarea a la vez.** No abrir varias tareas en paralelo.
- **Si algo falla dos veces, detente y pregunta.** No seguir reintentando
  parches incrementales; explicar el problema y esperar indicación.
