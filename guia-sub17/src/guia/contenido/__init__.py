"""Catalogo_Contenido: datos puros, un modulo por capitulo.

Este `__init__` **no contiene contenido propio**. Su unico trabajo es:

* importar los modulos de capitulo `capNN_*.py` en **orden explicito**,
* declarar el **orden de capitulos** (`ORDEN_CAPITULOS`) y la tupla de modulos
  (`CAPITULOS`) para que el orquestador los recorra,
* declarar el **presupuesto de paginas por capitulo** (`PRESUPUESTO_PAGINAS`),
  segun la tabla de escalado del diseno, y ofrecer `desvios_presupuesto` para
  reportar cuanto se aleja cada capitulo de su objetivo,
* **concatenar** las paginas de todos los capitulos en un solo Modelo_Paginas
  con folios consecutivos (`concatenar`).

Los modulos de capitulo llevan prefijo `cap` porque un modulo de Python no
puede empezar por digito: `cap00_portada.py`, `cap10_fundamentos.py`,
`cap20_pos_portera.py` ... `cap80_apendices.py`. El numero sigue ordenando el
documento. De momento solo esta escrito `cap00_portada` (tarea 9.1); los demas
se anaden en las tareas 9 a 12 y se importan aqui, en orden, conforme existan.
"""

from __future__ import annotations

from ..layout import PaginaRender
from ..plantillas import CtxPlantilla
from . import (
    cap00_portada,
    cap10_fundamentos,
    cap20_posiciones,
    cap30_colectivo,
    cap40_prevencion,
    cap50_mental,
    cap60_periodizacion,
    cap80_apendices,
)

__all__ = [
    "CAPITULOS",
    "ORDEN_CAPITULOS",
    "PRESUPUESTO_PAGINAS",
    "concatenar",
    "desvios_presupuesto",
]

#: Modulos de capitulo en orden de aparicion en el documento. Se amplia con
#: cada nuevo `capNN_*` conforme se escriba (tareas 9 a 12).
CAPITULOS: tuple[object, ...] = (
    cap00_portada,
    cap10_fundamentos,
    cap20_posiciones,
    cap30_colectivo,
    cap40_prevencion,
    cap50_mental,
    cap60_periodizacion,
    cap80_apendices,
)

#: Orden explicito de los capitulos por su identificador, derivado de CAPITULOS.
ORDEN_CAPITULOS: tuple[str, ...] = tuple(cap.CAPITULO_ID for cap in CAPITULOS)

#: Paginas objetivo por capitulo, segun la tabla de escalado del diseno. Sirve
#: para detectar desvios temprano (ver `desvios_presupuesto`).
PRESUPUESTO_PAGINAS: dict[str, int] = {
    'cap00_portada': 8,
    'cap10_fundamentos': 51,
    'cap20_posiciones': 18,
    'cap30_colectivo': 12,
    'cap40_prevencion': 20,
    'cap50_mental': 14,
    'cap60_periodizacion': 16,
    'cap80_apendices': 10,
}


def concatenar(
    *, folio_inicial: int = 1, ctx: CtxPlantilla | None = None
) -> list[PaginaRender]:
    """Concatena los capitulos en orden con folios consecutivos.

    Recorre `CAPITULOS` en orden, pide a cada modulo su Modelo_Paginas con el
    folio de inicio que le corresponde y los une en una sola lista. No anade
    contenido: solo enlaza lo que cada capitulo produce.
    """
    paginas: list[PaginaRender] = []
    folio = folio_inicial
    for cap in CAPITULOS:
        del_cap = cap.paginas(folio_inicial=folio, ctx=ctx)
        paginas.extend(del_cap)
        folio += len(del_cap)
    return paginas


def desvios_presupuesto(
    ctx: CtxPlantilla | None = None,
) -> dict[str, tuple[int, int | None, int | None]]:
    """Reporta, por capitulo, `(paginas_reales, objetivo, desvio)`.

    `objetivo` y `desvio` son `None` si el capitulo no tiene presupuesto
    declarado. `desvio = paginas_reales - objetivo`; positivo si el capitulo se
    paso de su presupuesto, negativo si se quedo corto.
    """
    reporte: dict[str, tuple[int, int | None, int | None]] = {}
    for cap in CAPITULOS:
        reales = len(cap.paginas(ctx=ctx))
        objetivo = PRESUPUESTO_PAGINAS.get(cap.CAPITULO_ID)
        desvio = None if objetivo is None else reales - objetivo
        reporte[cap.CAPITULO_ID] = (reales, objetivo, desvio)
    return reporte
