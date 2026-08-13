"""Paquete de pruebas de la Guia_Extensa.

Descubrimiento: `python -m unittest discover -s test` desde `guia-sub17/`.

Al importarse, este paquete pone `src/` y el propio directorio `test/` en
`sys.path`, para que las pruebas puedan hacer `from guia import ...` y
`from prop import for_all` sin instalar el proyecto ni definir `PYTHONPATH`.

Ojo: con `-s test`, `unittest` toma `test/` como directorio de nivel superior e
importa los modulos de prueba como modulos sueltos (`test_preflight`), no como
`test.test_preflight`, asi que este `__init__` **no** se ejecuta en ese caso. Por
eso cada modulo de prueba repite el bootstrap de `src/` en su cabecera. Este
archivo cubre la invocacion alternativa (`python -m unittest test.test_x`).
"""

from __future__ import annotations

import os
import sys

_DIR_TEST = os.path.dirname(os.path.abspath(__file__))
_DIR_SRC = os.path.join(os.path.dirname(_DIR_TEST), 'src')

for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
