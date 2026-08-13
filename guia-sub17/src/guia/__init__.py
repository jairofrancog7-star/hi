"""Pipeline de construccion de la Guia_Extensa de Entrenamiento Femenil Sub-17.

Python 3.11+ y **solo libreria estandar**: no hay `pip install`, no hay
reportlab, weasyprint, pillow ni qrcode. Si alguna dependencia externa apareciera
en el arbol de imports de este paquete, `guia.preflight` falla con
`E_DEPENDENCIA`.

Entradas:

    python -m guia.build            # build completo
    python src/build.py             # equivalente (shim)
    python src/build.py --preflight # solo las comprobaciones de entorno

Este `__init__` se mantiene vacio de logica a proposito: importar el paquete no
debe arrastrar ningun modulo del pipeline, para que el preflight pueda decidir
que es importable y que no.
"""

from __future__ import annotations

__all__ = ['VERSION', 'VERSION_PYTHON_MINIMA']

#: Version del pipeline (no del documento generado).
VERSION = '0.1.0'

#: Version minima de interprete soportada (ver Nota de portabilidad del diseno).
VERSION_PYTHON_MINIMA = (3, 11)
