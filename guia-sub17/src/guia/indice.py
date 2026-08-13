"""Paginador del índice en dos pasadas con `Mapa_Paginas` (tarea 5.4).

El problema del índice es que ocupa páginas y su tamaño depende de cuántas
entradas tiene, lo que desplaza todos los folios posteriores. La solución del
diseño es **fijar el tamaño del índice antes de conocer los folios**:

1. Se reserva el número de páginas del índice con
   ``math.ceil(len(entradas) / ENTRADAS_POR_PAGINA)`` (ver
   `guia.plantillas.ENTRADAS_POR_PAGINA`). La plantilla `indice` ocupa
   exactamente ese número de páginas con independencia de los folios impresos,
   porque cada entrada es de una sola línea y el folio va en una **columna de
   ancho fijo** (el del placeholder ``"000"``).
2. **Primera pasada**: se renderiza el documento con el índice relleno de
   placeholders (``folios=None``). De las páginas resultantes se extrae el
   `Mapa_Paginas`: ``capitulo_id -> folio de su portadilla``.
3. **Segunda pasada**: mismo documento, mismo número de páginas de índice, pero
   ahora con los folios reales. Como el layout del índice es idéntico por
   construcción, las portadillas no se mueven y el mapa coincide.

Sobre esa idea se itera a un **punto fijo** (máximo `MAX_PASADAS` pasadas): se
repite mientras el mapa o el conteo de páginas cambien de una pasada a la
siguiente. Al converger se verifica la alineación del índice. Si no converge,
se falla con `E_PAGINACION_INESTABLE`; si el índice quedara desalineado con las
portadillas reales, con `E_INDICE_DESALINEADO`. Nunca se usa `assert`
(`python -O` los borra): todo invariante se comprueba con `raise ErrorBuild`
(subclase `ErrorLayout`).

Este módulo no conoce el catálogo ni las plantillas de contenido: recibe un
`renderizar(IndiceCtx) -> list[PaginaRender]` que produce el Modelo_Paginas
completo (incluido el índice) para un contexto de índice dado. Así el algoritmo
de dos pasadas es verificable de forma aislada y reutilizable por el
Orquestador_Build (tarea 13.1).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from . import afm
from .errores import E_INDICE_DESALINEADO, E_PAGINACION_INESTABLE, ErrorLayout
from .layout import PaginaRender, Plantilla
from .plantillas import ENTRADAS_POR_PAGINA, FOLIO_PLACEHOLDER, EntradaIndice

__all__ = [
    "MAX_PASADAS",
    "MapaPaginas",
    "IndiceCtx",
    "Paginacion",
    "paginas_indice_para",
    "extraer_mapa_paginas",
    "paginar_con_indice",
]


#: Máximo de pasadas del punto fijo antes de declarar la paginación inestable.
MAX_PASADAS: int = 4

#: Mapa_Paginas: capítulo -> folio (1..N) donde inicia su portadilla.
MapaPaginas = dict[str, int]


@dataclass(frozen=True, slots=True)
class IndiceCtx:
    """Contexto que el renderizador recibe para dibujar el índice.

    `paginas` es el número de páginas reservado para el índice (estable entre
    pasadas). `folios` es el `Mapa_Paginas` con los folios reales, o `None` en
    la primera pasada (el índice usa entonces el placeholder).
    """

    paginas: int
    folios: Mapping[str, int] | None = None


@dataclass(slots=True)
class Paginacion:
    """Resultado del paginador: Modelo_Paginas final más metadatos del índice."""

    paginas: list[PaginaRender]
    mapa: MapaPaginas
    pasadas: int
    paginas_indice: int


def paginas_indice_para(entradas: Sequence[EntradaIndice]) -> int:
    """Páginas que ocupará el índice: ``ceil(len(entradas) / ENTRADAS_POR_PAGINA)``."""
    n = len(entradas)
    if n <= 0:
        return 0
    return math.ceil(n / ENTRADAS_POR_PAGINA)


def extraer_mapa_paginas(paginas: Sequence[PaginaRender]) -> MapaPaginas:
    """Construye el `Mapa_Paginas` desde las portadillas del Modelo_Paginas.

    Asocia cada `capitulo_id` con el folio de la **primera** página de plantilla
    `PORTADILLA_CAPITULO` que lo declara (donde inicia el capítulo, Req 10.3).
    """
    mapa: MapaPaginas = {}
    for pagina in paginas:
        if (
            pagina.plantilla is Plantilla.PORTADILLA_CAPITULO
            and pagina.capitulo_id not in mapa
        ):
            mapa[pagina.capitulo_id] = pagina.folio
    return mapa


def _verificar_alineacion(
    entradas: Sequence[EntradaIndice],
    mapa: MapaPaginas,
    folios_mostrados: Mapping[str, int] | None,
) -> None:
    """Comprueba que el índice apunta al folio real donde inicia cada capítulo.

    Falla con `E_INDICE_DESALINEADO` si:
    * una entrada apunta a un capítulo sin portadilla en el Modelo_Paginas,
    * el folio que mostró el índice no coincide con el folio real, o
    * un folio real es más ancho que la columna de ancho fijo del placeholder
      (rompería la alineación de la columna de folios).
    """
    ancho_columna = afm.medir_texto(FOLIO_PLACEHOLDER)
    for entrada in entradas:
        cap = entrada.capitulo_id
        if cap not in mapa:
            raise ErrorLayout(
                f"el índice referencia el capítulo {cap!r} que no tiene "
                f"portadilla en el documento",
                codigo=E_INDICE_DESALINEADO,
                detalle={"capitulo_id": cap},
            )
        real = mapa[cap]
        mostrado = None if folios_mostrados is None else folios_mostrados.get(cap)
        if mostrado != real:
            raise ErrorLayout(
                f"índice: {cap} indica el folio {mostrado}, pero el capítulo "
                f"inicia en el folio {real}",
                codigo=E_INDICE_DESALINEADO,
                detalle={"capitulo_id": cap, "mostrado": mostrado, "real": real},
            )
        if afm.medir_texto(str(real)) > ancho_columna + 1e-6:
            raise ErrorLayout(
                f"el folio {real} del capítulo {cap!r} excede la columna de "
                f"folio de ancho fijo ('{FOLIO_PLACEHOLDER}')",
                codigo=E_INDICE_DESALINEADO,
                detalle={"capitulo_id": cap, "folio": real},
            )


def paginar_con_indice(
    entradas: Sequence[EntradaIndice],
    renderizar: Callable[[IndiceCtx], list[PaginaRender]],
    *,
    max_pasadas: int = MAX_PASADAS,
) -> Paginacion:
    """Pagina el documento con índice de dos pasadas iterando a un punto fijo.

    `renderizar(ctx)` debe producir el Modelo_Paginas completo (portada, índice
    de `ctx.paginas` páginas usando `ctx.folios`, y el resto de capítulos) con
    folios consecutivos desde 1. El algoritmo:

    * Reserva las páginas de índice con `paginas_indice_para`.
    * Pasada 1 con `folios=None` (placeholders) y extrae el `Mapa_Paginas`.
    * Pasadas siguientes con los folios reales de la pasada anterior.
    * Converge cuando el mapa y el conteo de páginas se repiten entre dos
      pasadas consecutivas; entonces verifica la alineación y devuelve la
      última pasada (la que muestra los folios reales).
    * Si no converge en `max_pasadas`, lanza `E_PAGINACION_INESTABLE`.
    """
    if max_pasadas < 2:
        raise ErrorLayout(
            f"el punto fijo del índice necesita al menos 2 pasadas, "
            f"se pidieron {max_pasadas}",
            codigo=E_PAGINACION_INESTABLE,
            detalle={"max_pasadas": max_pasadas},
        )

    n_paginas_indice = paginas_indice_para(entradas)

    folios_entrada: Mapping[str, int] | None = None
    mapa_prev: MapaPaginas | None = None
    conteo_prev: int | None = None

    for pasada in range(1, max_pasadas + 1):
        ctx = IndiceCtx(paginas=n_paginas_indice, folios=folios_entrada)
        paginas = renderizar(ctx)
        mapa = extraer_mapa_paginas(paginas)
        conteo = len(paginas)

        if mapa_prev is not None and mapa == mapa_prev and conteo == conteo_prev:
            # Convergió: la pasada actual imprimió `folios_entrada` (== mapa) y
            # las portadillas siguen en esos folios. Verifica y devuelve.
            _verificar_alineacion(entradas, mapa, folios_entrada)
            return Paginacion(
                paginas=paginas,
                mapa=mapa,
                pasadas=pasada,
                paginas_indice=n_paginas_indice,
            )

        mapa_prev = mapa
        conteo_prev = conteo
        folios_entrada = mapa

    raise ErrorLayout(
        f"la paginación no convergió tras {max_pasadas} pasadas: el conteo de "
        f"páginas o los folios de capítulo siguen cambiando",
        codigo=E_PAGINACION_INESTABLE,
        detalle={
            "max_pasadas": max_pasadas,
            "conteo": conteo_prev,
            "paginas_indice": n_paginas_indice,
        },
    )
