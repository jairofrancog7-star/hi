"""Verificador independiente de unicidad del Plan_Rotacion (tarea 6.2).

Este módulo comprueba, **de forma independiente del generador**, que ningún par
de `BloqueSemanal` comparte la misma combinación de Ficha_Ejercicio (Req 5.4).
La clave del diseño (`design.md`, sección "5. Algoritmo del Plan_Rotacion") es
que la verificación **recalcula todas las firmas desde el catálogo emitido**
—recorriendo las `sesiones` de cada bloque y sus `ficha_ids`— y **no confía en
el campo `bloque.firma`** que dejó el generador en memoria. Así, un error en
`rotacion.py` (por ejemplo, una firma mal calculada o duplicada que se escapó
de la reparación) no puede pasar inadvertido: el verificador vive en un módulo
aparte y vuelve a derivar la evidencia desde los artefactos.

Estrategia:

* `firma_recalculada(bloque)` deriva la firma canónica del bloque a partir de
  sus sesiones, con la misma regla que el dominio (``'|'.join(sorted(set
  ids))``): el orden y los duplicados no cuentan. Se reimplementa aquí, sin
  importar `rotacion.firma_de`, para que la verificación sea genuinamente
  independiente del generador.
* `mapa_firmas(bloques)` construye el `dict[str, list[str]]` de firma a ids de
  bloque exigido por el diseño.
* `verificar_unicidad(bloques)` recorre ese mapa y, si alguna firma agrupa dos o
  más bloques, lanza `ErrorRotacion` con código `E_ROTACION_DUPLICADA` nombrando
  los bloques implicados (Req 5.10). Si todo es único, devuelve el mapa para que
  el orquestador lo reporte.

Solo librería estándar; sin `assert`: el fallo se expresa con `raise` de
`ErrorRotacion` (subclase de `ErrorBuild`).

Requisitos: 5.10, 5.4.
"""

from __future__ import annotations

from typing import Iterable

from .errores import E_ROTACION_DUPLICADA, ErrorRotacion
from .schema import BloqueSemanal

__all__ = [
    'firma_recalculada',
    'mapa_firmas',
    'verificar_unicidad',
]


def firma_recalculada(bloque: BloqueSemanal) -> str:
    """Recalcula la firma canónica de un bloque desde sus sesiones emitidas.

    Recorre todas las `sesiones` del bloque y reúne los `ficha_ids` que
    realmente contienen, en lugar de leer `bloque.firma`. La firma es canónica
    —ids ordenados y deduplicados— de modo que dos bloques con las mismas fichas
    en distinto orden producen la misma firma (lectura estricta del Req 5.4).
    """
    ids: list[str] = [
        fid
        for sesion in bloque.sesiones.values()
        for fid in sesion.ficha_ids
    ]
    return '|'.join(sorted(set(ids)))


def mapa_firmas(bloques: Iterable[BloqueSemanal]) -> dict[str, list[str]]:
    """Construye el mapa de firma recalculada a lista de ids de bloque.

    El valor es una `list[str]` (no un `set`) para conservar el orden de
    aparición de los bloques, lo que hace el mensaje de error reproducible.
    """
    mapa: dict[str, list[str]] = {}
    for bloque in bloques:
        firma = firma_recalculada(bloque)
        mapa.setdefault(firma, []).append(bloque.id)
    return mapa


def verificar_unicidad(bloques: Iterable[BloqueSemanal]) -> dict[str, list[str]]:
    """Verifica que ninguna combinación de fichas se repite entre bloques.

    Recalcula las firmas desde el catálogo emitido (no desde la memoria del
    generador) y, ante el primer grupo de dos o más bloques con la misma firma,
    lanza `ErrorRotacion` con código `E_ROTACION_DUPLICADA` nombrando los
    bloques implicados (Req 5.10, 5.4). Si todas las firmas son únicas, devuelve
    el `dict[str, list[str]]` de firma a ids de bloque para el reporte del build.
    """
    mapa = mapa_firmas(bloques)

    for firma, ids in mapa.items():
        if len(ids) > 1:
            nombres = ' y '.join(ids)
            raise ErrorRotacion(
                f'bloques {nombres} repiten la combinacion',
                codigo=E_ROTACION_DUPLICADA,
                detalle={'firma': firma, 'bloques': list(ids)},
            )

    return mapa
