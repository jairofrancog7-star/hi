"""Generador del Plan_Rotacion determinista (tarea 6.1).

Construye una secuencia de `BloqueSemanal` (>= 24) en la que **ninguna semana
repite la misma combinación de Ficha_Ejercicio** (Req 5.4), con contenido
equilibrado por ejes y de forma **reproducible byte a byte** entre ejecuciones
con la misma semilla.

Decisiones de diseño (según `design.md`, sección "5. Algoritmo del
Plan_Rotacion"):

* **Ejes de contenido**: `tecnica | posicion | fisico_prevencion | juego |
  mental`. Cada semana rota su foco principal de forma cíclica y cada día toma
  fichas de un eje distinto, así no se acumulan semanas del mismo tipo.
* **Round-robin con offset por semana**: `tomar_ventana` desliza la ventana de
  selección sobre el pool de cada eje; el offset crece con la semana, de modo
  que dos semanas rara vez toman el mismo conjunto.
* **Firma canónica**: `firma_de(ficha_ids)` = ``'|'.join(sorted(set(ids)))``.
  El orden y los duplicados no cuentan: dos semanas con las mismas fichas en
  distinto orden se consideran repetidas (lectura estricta de Req 5.4).
* **Reparación**: si una firma ya existe, se sustituye la ficha **menos usada**
  de la combinación por otra de su mismo eje que no esté ya presente, hasta
  obtener una firma nueva. Al agotar `MAX_REPARACIONES` se lanza
  `E_ROTACION_SIN_COMBINACION`.
* **Determinismo (Riesgo 13)**: toda la aleatoriedad sale de un único
  `random.Random(semilla)` y **solo** de `rnd.random()` y `rnd.randrange()`.
  **No** se usan `random.shuffle` ni `random.sample` (su implementación interna
  no está garantizada entre versiones del intérprete). Cuando hay que mezclar,
  se usa el Fisher-Yates propio de `mezclar`.
* **Presupuesto de sesión fijo**: `construir_sesion` reparte un presupuesto
  cerrado, así `sum(b.minutos for b in bloques) == total_min <= 90` por
  construcción (Req 5.6, 5.7). La `version_corta` se deriva quitando el juego
  libre y recortando el calentamiento, con tope duro de 30 min (Req 5.9).
* **Tabla de seguimiento**: una fila por bloque, con fecha y las tres sesiones
  a marcar como completadas (Req 5.8).

Solo librería estándar (`random`, `re`, `dataclasses`); sin `assert`: todo
invariante se comprueba con `raise` de una subclase de `ErrorBuild`.

Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field, replace
from typing import Iterable

from .errores import E_ROTACION_SIN_COMBINACION, ErrorRotacion
from .schema import (
    LADO_ESPACIO_REDUCIDO_M,
    BloqueSemanal,
    BloqueSesion,
    Dia,
    FichaEjercicio,
    Montaje,
    Sabado,
    Sesion,
    Variante,
)

__all__ = [
    'EJES',
    'FICHAS_POR_SESION',
    'MAX_REPARACIONES',
    'TOTAL_MIN_SESION',
    'TOPE_VERSION_CORTA_MIN',
    'MIN_JUGADORAS_TABLA',
    'MAX_JUGADORAS_TABLA',
    'RANGO_TABLA_DECISION',
    'FilaSeguimiento',
    'TablaSeguimiento',
    'PlanRotacion',
    'ResolucionSesion',
    'firma_de',
    'mezclar',
    'agrupar_por_eje',
    'eje_para_dia',
    'tomar_ventana',
    'rango_jugadoras',
    'construir_sesion',
    'generar_plan',
    'sesion_admite',
    'resolver_sustituta',
    'resolver_por_jugadoras',
    'tabla_decision_jugadoras',
    'fichas_en_espacio_reducido',
]

# --------------------------------------------------------------------------- #
# Constantes de dominio
# --------------------------------------------------------------------------- #

#: Ejes de contenido sobre los que se equilibra la rotación.
EJES: tuple[str, ...] = ('tecnica', 'posicion', 'fisico_prevencion', 'juego', 'mental')

#: Número de Ficha_Ejercicio que toma cada sesión.
FICHAS_POR_SESION: int = 3

#: Tope de reparaciones por bloque antes de declarar que no queda combinación.
MAX_REPARACIONES: int = 64

#: Presupuesto de una sesión completa. La suma es exactamente el total_min y no
#: supera los 90 min (Req 5.6, 5.7). Se reparte, no se acumula libremente.
_PRESUPUESTO_SESION: tuple[tuple[str, int], ...] = (
    ('Calentamiento y activación', 15),
    ('Bloque principal', 30),
    ('Trabajo específico del día', 30),
    ('Juego libre y vuelta a la calma', 15),
)

#: Presupuesto de la versión corta (luz natural insuficiente, Req 5.9): quita el
#: juego libre y recorta el calentamiento. Tope duro de 30 min.
_PRESUPUESTO_VERSION_CORTA: tuple[tuple[str, int], ...] = (
    ('Calentamiento breve', 8),
    ('Bloque principal', 22),
)

#: Total (en minutos) de una sesión completa; derivado del presupuesto.
TOTAL_MIN_SESION: int = sum(minutos for _, minutos in _PRESUPUESTO_SESION)

#: Tope de la versión corta (Req 5.9).
TOPE_VERSION_CORTA_MIN: int = 30

#: Extremos del dominio de la tabla de decisión por número de jugadoras
#: (Req 8.2): la tabla debe resolver toda asistencia de 1 a 11 jugadoras.
MIN_JUGADORAS_TABLA: int = 1
MAX_JUGADORAS_TABLA: int = 11

#: Dominio completo de la tabla de decisión (1..11 inclusive).
RANGO_TABLA_DECISION: tuple[int, ...] = tuple(
    range(MIN_JUGADORAS_TABLA, MAX_JUGADORAS_TABLA + 1)
)

#: Frase legible de cada eje, para el objetivo de la semana (Req 5.5).
_FRASE_EJE: dict[str, str] = {
    'tecnica': 'la técnica individual con balón',
    'posicion': 'el trabajo específico por posición',
    'fisico_prevencion': 'la fuerza y la prevención de lesiones',
    'juego': 'el juego colectivo y las transiciones',
    'mental': 'la concentración y la preparación mental',
}


# --------------------------------------------------------------------------- #
# Modelo del Plan_Rotacion y su tabla de seguimiento
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class FilaSeguimiento:
    """Una fila de la tabla de seguimiento: un Bloque_Semanal (Req 5.8).

    La jugadora anota la `fecha` de inicio y marca en `sesiones_completadas`
    (martes, miércoles, jueves) las sesiones que realizó.
    """

    bloque_id: str
    semana: int
    fecha: str = ''
    sesiones_completadas: list[bool] = field(
        default_factory=lambda: [False, False, False]
    )


@dataclass(slots=True)
class TablaSeguimiento:
    """Tabla de seguimiento con una fila por Bloque_Semanal (Req 5.8)."""

    filas: list[FilaSeguimiento]


@dataclass(slots=True)
class PlanRotacion:
    """Plan de rotación completo: bloques, semilla y tabla de seguimiento."""

    bloques: list[BloqueSemanal]         # >= 24, firmas todas distintas (Req 5.1, 5.4)
    semilla: int                         # generación determinista
    seguimiento: TablaSeguimiento        # una fila por bloque (Req 5.8)


# --------------------------------------------------------------------------- #
# Utilidades deterministas (firma canónica y mezcla propia)
# --------------------------------------------------------------------------- #


def firma_de(ficha_ids: Iterable[str]) -> str:
    """Firma canónica de una combinación de fichas.

    Ordena y deduplica los ids, de modo que el orden y las repeticiones no
    cuentan: es la definición de "misma combinación" del Req 5.4.
    """
    return '|'.join(sorted(set(ficha_ids)))


def mezclar(secuencia: Iterable[object], rnd: random.Random) -> list[object]:
    """Baraja una secuencia con un Fisher-Yates propio (Riesgo 13).

    Usa **solo** `rnd.randrange`, nunca `random.shuffle` ni `random.sample`, para
    que el resultado sea estable entre versiones de CPython. Devuelve una lista
    nueva; no muta la entrada.
    """
    items: list[object] = list(secuencia)
    for i in range(len(items) - 1, 0, -1):
        j = rnd.randrange(i + 1)
        items[i], items[j] = items[j], items[i]
    return items


# --------------------------------------------------------------------------- #
# Agrupación por eje y selección round-robin
# --------------------------------------------------------------------------- #


def _eje_de_ficha(ficha: FichaEjercicio) -> str | None:
    """Eje de contenido al que pertenece una ficha, o `None` si no se sabe.

    Empareja contra `EJES` (`tecnica | posicion | fisico_prevencion | juego |
    mental`) buscando primero entre las `etiquetas` de la ficha y, si ninguna
    coincide, con su `categoria`. Devuelve `None` cuando no hay coincidencia;
    esas fichas las reparte `agrupar_por_eje` round-robin.
    """
    ejes = set(EJES)

    etiquetas = getattr(ficha, 'etiquetas', None) or []
    for etiqueta in etiquetas:
        if etiqueta in ejes:
            return etiqueta

    categoria = getattr(ficha, 'categoria', None)
    if categoria in ejes:
        return categoria

    return None


def agrupar_por_eje(fichas: Iterable[FichaEjercicio]) -> dict[str, list[FichaEjercicio]]:
    """Reparte las fichas en un pool por eje, garantizando stock mínimo.

    Una ficha se asigna a un eje si alguna de sus `etiquetas` (o su `categoria`)
    coincide con un eje; las no etiquetadas se reparten round-robin para
    equilibrar. Si algún eje queda por debajo de `FICHAS_POR_SESION`, se rellena
    tomando prestadas fichas de las demás, de modo que toda sesión pueda
    construirse.
    """
    lista: list[FichaEjercicio] = list(fichas)
    pool: dict[str, list[FichaEjercicio]] = {eje: [] for eje in EJES}
    sin_eje: list[FichaEjercicio] = []

    for ficha in lista:
        eje = _eje_de_ficha(ficha)
        if eje is not None:
            pool[eje].append(ficha)
        else:
            sin_eje.append(ficha)

    for indice, ficha in enumerate(sin_eje):
        pool[EJES[indice % len(EJES)]].append(ficha)

    # Relleno de ejes pobres: préstamo determinista desde el resto del catálogo.
    for eje in EJES:
        if len(pool[eje]) >= FICHAS_POR_SESION:
            continue
        presentes = {id(f) for f in pool[eje]}
        for ficha in lista:
            if len(pool[eje]) >= FICHAS_POR_SESION:
                break
            if id(ficha) not in presentes:
                pool[eje].append(ficha)
                presentes.add(id(ficha))

    return pool


def eje_para_dia(foco_semana: str, dia_indice: int) -> str:
    """Eje que trabaja el día `dia_indice` de una semana con foco `foco_semana`.

    El día 0 usa el foco de la semana y los siguientes avanzan cíclicamente,
    de modo que los tres días de una semana tocan ejes distintos.
    """
    base = EJES.index(foco_semana)
    return EJES[(base + dia_indice) % len(EJES)]


def tomar_ventana(
    secuencia: list[FichaEjercicio],
    inicio: int,
    cantidad: int,
) -> list[FichaEjercicio]:
    """Toma `cantidad` fichas desde `inicio`, dando la vuelta si hace falta."""
    longitud = len(secuencia)
    if longitud == 0:
        return []
    return [secuencia[(inicio + paso) % longitud] for paso in range(cantidad)]


def _offset(semana: int, dia_indice: int, longitud: int) -> int:
    """Desplazamiento de la ventana para (semana, día) sobre un pool dado."""
    if longitud == 0:
        return 0
    return (semana * FICHAS_POR_SESION + dia_indice * 5) % longitud


# --------------------------------------------------------------------------- #
# Rango de jugadoras (tolerante a tupla o texto)
# --------------------------------------------------------------------------- #


def rango_jugadoras(ficha: FichaEjercicio) -> tuple[int, int]:
    """Rango (min, max) de jugadoras de una ficha, tolerante al origen.

    El catálogo Python entrega `jugadoras` como `tuple[int, int]`; el adaptador
    del Catalogo_JSON lo entrega como texto (p.ej. ``'2 a 6 jugadoras'``). Esta
    función normaliza ambos a un par de enteros con `1 <= min <= max`, con un
    respaldo razonable cuando no hay datos.
    """
    valor = getattr(ficha, 'jugadoras', None)

    if (
        isinstance(valor, tuple)
        and len(valor) == 2
        and all(isinstance(x, int) and not isinstance(x, bool) for x in valor)
    ):
        minimo, maximo = valor
        if minimo >= 1 and minimo <= maximo:
            return (minimo, maximo)

    if isinstance(valor, str):
        numeros = [int(n) for n in re.findall(r'\d+', valor)]
        if len(numeros) >= 2:
            minimo, maximo = numeros[0], numeros[1]
            minimo = max(1, minimo)
            maximo = max(minimo, maximo)
            return (minimo, maximo)
        if len(numeros) == 1:
            unico = max(1, numeros[0])
            return (unico, unico)

    return (1, 8)


def _rango_de_seleccion(seleccion: list[FichaEjercicio]) -> tuple[int, int]:
    """Rango de jugadoras de una sesión, derivado de sus fichas."""
    rangos = [rango_jugadoras(f) for f in seleccion]
    if not rangos:
        return (1, 1)
    minimo = min(r[0] for r in rangos)
    maximo = max(r[1] for r in rangos)
    if minimo > maximo:
        minimo = maximo
    return (minimo, maximo)


def _ficha_menor_jugadoras(seleccion: list[FichaEjercicio]) -> str | None:
    """Id de la ficha que exige menos jugadoras (alimenta `sustituta_id`)."""
    if not seleccion:
        return None
    elegida = min(seleccion, key=lambda f: rango_jugadoras(f)[0])
    return elegida.id


# --------------------------------------------------------------------------- #
# Construcción de sesiones y bloques
# --------------------------------------------------------------------------- #


def construir_sesion(
    dia: Dia,
    eje: str,
    seleccion: list[FichaEjercicio],
    rnd: random.Random,
    *,
    con_version_corta: bool = True,
) -> Sesion:
    """Construye una sesión repartiendo un presupuesto fijo de minutos.

    Los bloques provienen de `_PRESUPUESTO_SESION`, así
    ``sum(b.minutos) == total_min == TOTAL_MIN_SESION <= 90`` por construcción
    (Req 5.6, 5.7). Cuando `con_version_corta` es cierto se deriva una
    `version_corta` de <= 30 min (Req 5.9). `sustituta_id` apunta a la ficha que
    exige menos jugadoras (Req 8.8).
    """
    ids = [f.id for f in seleccion]
    bloques = [BloqueSesion(nombre=nombre, minutos=minutos)
               for nombre, minutos in _PRESUPUESTO_SESION]
    total = sum(b.minutos for b in bloques)
    rango = _rango_de_seleccion(seleccion)
    sustituta = _ficha_menor_jugadoras(seleccion)

    version_corta: Sesion | None = None
    if con_version_corta:
        bloques_cortos = [BloqueSesion(nombre=nombre, minutos=minutos)
                          for nombre, minutos in _PRESUPUESTO_VERSION_CORTA]
        version_corta = Sesion(
            dia=dia,
            foco=eje,
            bloques=bloques_cortos,
            total_min=sum(b.minutos for b in bloques_cortos),
            ficha_ids=list(ids),
            jugadoras=rango,
            version_corta=None,
            sustituta_id=sustituta,
        )

    return Sesion(
        dia=dia,
        foco=eje,
        bloques=bloques,
        total_min=total,
        ficha_ids=list(ids),
        jugadoras=rango,
        version_corta=version_corta,
        sustituta_id=sustituta,
    )


def _objetivo_semana(foco_semana: str, semana: int) -> str:
    """Objetivo de la semana en una sola frase (Req 5.5)."""
    frase = _FRASE_EJE.get(foco_semana, foco_semana)
    return f'Semana {semana}: afinar {frase}.'


def _sabado_para(foco_semana: str) -> Sabado:
    """Indicaciones de sábado (calentamiento y enfoque de liga) (Req 5.3)."""
    frase = _FRASE_EJE.get(foco_semana, foco_semana)
    calentamiento = [
        'Trote suave y movilidad de tobillo, rodilla y cadera (8 min).',
        'Activación con balón en parejas o contra la pared (7 min).',
    ]
    enfoque = f'Llevar al partido {frase}; revisar la lámina de la semana antes del silbatazo.'
    return Sabado(calentamiento=calentamiento, enfoque=enfoque)


def _construir_bloque(
    indice: int,
    foco_semana: str,
    sesiones: dict[Dia, Sesion],
    firma: str,
) -> BloqueSemanal:
    """Ensambla un Bloque_Semanal a partir de sus sesiones y su firma."""
    semana = indice + 1
    return BloqueSemanal(
        id=f'S{semana:02d}',
        semana=semana,
        objetivo=_objetivo_semana(foco_semana, semana),
        sesiones=dict(sesiones),
        sabado=_sabado_para(foco_semana),
        firma=firma,
    )


def _tabla_seguimiento(bloques: list[BloqueSemanal]) -> TablaSeguimiento:
    """Tabla de seguimiento con una fila por bloque (Req 5.8)."""
    filas = [FilaSeguimiento(bloque_id=b.id, semana=b.semana) for b in bloques]
    return TablaSeguimiento(filas=filas)


# --------------------------------------------------------------------------- #
# Reparación por sustitución de la ficha menos usada
# --------------------------------------------------------------------------- #


def _sustituir_ficha_menos_usada(
    sesiones: dict[Dia, Sesion],
    ejes_por_dia: dict[Dia, str],
    pool: dict[str, list[FichaEjercicio]],
    usos: dict[str, int],
    rnd: random.Random,
) -> bool:
    """Sustituye la ficha menos usada de la combinación por otra de su eje.

    Devuelve `True` si logró cambiar una ficha (y por tanto potencialmente la
    firma), `False` si no había reemplazo posible. La elección entre candidatas
    de igual uso se rompe por orden de pool (determinista e independiente de la
    semilla), de modo que la firma resultante no dependa de la semilla.
    """
    actuales = {fid for s in sesiones.values() for fid in s.ficha_ids}

    # Ficha (y su día) usada menos globalmente. El desempate es por id de ficha,
    # nunca por la posición dentro de `ficha_ids` (ese orden lo baraja `mezclar`
    # y depende de la semilla). Así la reparación es independiente de la semilla.
    objetivo: tuple[int, str, Dia] | None = None
    for dia, sesion in sesiones.items():
        for fid in sesion.ficha_ids:
            clave = (usos.get(fid, 0), fid)
            if objetivo is None or clave < (objetivo[0], objetivo[1]):
                objetivo = (clave[0], clave[1], dia)

    if objetivo is None:
        return False

    _, fid_objetivo, dia = objetivo
    eje = ejes_por_dia[dia]
    candidatas = [f for f in pool[eje] if f.id not in actuales]
    if not candidatas:
        return False

    uso_minimo = min(usos.get(f.id, 0) for f in candidatas)
    # Desempate determinista por id (independiente de la semilla): la firma
    # resultante debe ser idéntica entre semillas; la semilla solo altera el
    # orden interno de `ficha_ids` vía `mezclar`.
    mejores = sorted(
        (f for f in candidatas if usos.get(f.id, 0) == uso_minimo),
        key=lambda f: f.id,
    )
    elegida = mejores[0]

    # Sustitución por valor: se reemplaza la ficha objetivo conservando la
    # posición del resto, de modo que el orden (barajado por semilla) siga
    # difiriendo entre semillas aunque el conjunto sea el mismo.
    nuevos = [
        elegida.id if fid == fid_objetivo else fid
        for fid in sesiones[dia].ficha_ids
    ]
    sesiones[dia].ficha_ids = nuevos
    sesiones[dia].sustituta_id = _ficha_menor_jugadoras_por_ids(nuevos, pool, eje)
    return True


def _ficha_menor_jugadoras_por_ids(
    ids: list[str],
    pool: dict[str, list[FichaEjercicio]],
    eje: str,
) -> str | None:
    """Recalcula `sustituta_id` tras una sustitución, sobre el pool del eje."""
    por_id = {f.id: f for f in pool[eje]}
    presentes = [por_id[fid] for fid in ids if fid in por_id]
    return _ficha_menor_jugadoras(presentes)


# --------------------------------------------------------------------------- #
# Punto de entrada: generación del plan
# --------------------------------------------------------------------------- #


def generar_plan(
    fichas: Iterable[FichaEjercicio],
    *,
    n_bloques: int = 26,
    semilla: int = 20260101,
) -> PlanRotacion:
    """Genera un Plan_Rotacion determinista de `n_bloques` bloques.

    Cada bloque tiene sesiones de martes, miércoles y jueves (Req 5.2), un
    objetivo de una frase (Req 5.5), indicaciones de sábado (Req 5.3) y una
    combinación de fichas distinta de la de todos los demás bloques (Req 5.4).
    Toda la aleatoriedad procede de `random.Random(semilla)` y solo de
    `rnd.random()`/`rnd.randrange()`, así que dos llamadas con la misma semilla
    producen el mismo plan (Riesgo 13). Si un bloque no encuentra combinación
    libre tras `MAX_REPARACIONES`, se lanza `E_ROTACION_SIN_COMBINACION`.
    """
    rnd = random.Random(semilla)
    pool = agrupar_por_eje(fichas)
    usadas: set[str] = set()
    usos: dict[str, int] = {}
    bloques: list[BloqueSemanal] = []

    for indice in range(n_bloques):
        foco_semana = EJES[indice % len(EJES)]

        sesiones: dict[Dia, Sesion] = {}
        ejes_por_dia: dict[Dia, str] = {}
        for dia_indice, dia in enumerate(Dia):
            eje_dia = eje_para_dia(foco_semana, dia_indice)
            ejes_por_dia[dia] = eje_dia
            ventana = tomar_ventana(
                pool[eje_dia],
                _offset(indice, dia_indice, len(pool[eje_dia])),
                FICHAS_POR_SESION,
            )
            seleccion = mezclar(ventana, rnd)
            sesiones[dia] = construir_sesion(dia, eje_dia, seleccion, rnd)

        firma = firma_de(fid for s in sesiones.values() for fid in s.ficha_ids)

        intentos = 0
        while firma in usadas:
            intentos += 1
            if intentos > MAX_REPARACIONES:
                raise ErrorRotacion(
                    f'no queda combinación libre para el bloque {indice + 1} '
                    f'tras {MAX_REPARACIONES} reparaciones',
                    codigo=E_ROTACION_SIN_COMBINACION,
                    detalle={'bloque': indice + 1, 'reparaciones': MAX_REPARACIONES},
                )
            if not _sustituir_ficha_menos_usada(
                sesiones, ejes_por_dia, pool, usos, rnd
            ):
                raise ErrorRotacion(
                    f'no hay fichas de reemplazo para el bloque {indice + 1}',
                    codigo=E_ROTACION_SIN_COMBINACION,
                    detalle={'bloque': indice + 1, 'reparaciones': intentos},
                )
            firma = firma_de(fid for s in sesiones.values() for fid in s.ficha_ids)

        usadas.add(firma)
        for sesion in sesiones.values():
            for fid in sesion.ficha_ids:
                usos[fid] = usos.get(fid, 0) + 1

        bloques.append(_construir_bloque(indice, foco_semana, sesiones, firma))

    return PlanRotacion(
        bloques=bloques,
        semilla=semilla,
        seguimiento=_tabla_seguimiento(bloques),
    )


# --------------------------------------------------------------------------- #
# Tabla de decisión por número de jugadoras y por espacio (tarea 6.3)
# --------------------------------------------------------------------------- #
#
# Tres piezas resuelven la pregunta "llegaron N jugadoras y este es el espacio,
# ¿qué entreno?" (Req 8.2, 8.6, 8.8):
#
# * `resolver_por_jugadoras(plan, n)` — a partir de 1..11 jugadoras presentes,
#   resuelve **una** sesión cuyo rango de jugadoras admite ese número. La tabla
#   es **total** sobre 1..11 por construcción (Property 14):
#     - Si alguna sesión del plan admite `n` (min <= n <= max), se elige la de
#       ajuste más ceñido (menos desperdicio de rotación).
#     - Si `n` es menor que el mínimo de todas las sesiones, se resuelve la
#       **sesión sustituta reducida** (Req 8.8), cuyo rango `(1, min-1)` admite
#       cualquier asistencia por debajo de lo planeado.
#     - Si `n` supera el máximo de todas las sesiones, se ejecuta la sesión de
#       mayor capacidad **formando grupos adicionales**; el rango efectivo se
#       ensancha hasta `n` para reflejar que las jugadoras de más rotan.
# * `resolver_sustituta(sesion, n)` — para una sesión concreta y una asistencia
#   `n` por debajo de su mínimo, construye la sesión sustituta que sí admite `n`
#   (segunda mitad de Property 14).
# * `fichas_en_espacio_reducido(fichas)` — selecciona las Ficha_Ejercicio
#   ejecutables en una franja de 10 m × 10 m o menor cuando la cancha está
#   ocupada por otros grupos (Req 8.6).
#
# Todo es determinista y sin `assert`: los argumentos fuera de dominio se
# rechazan con `ValueError` (precondición de una función pura, no un invariante
# de build), y las sesiones adaptadas se derivan con `dataclasses.replace`.


@dataclass(slots=True)
class ResolucionSesion:
    """Resultado de la tabla de decisión para una asistencia concreta.

    `sesion` es la sesión a ejecutar (posiblemente una copia adaptada del plan o
    una sustituta construida al vuelo); su rango `jugadoras` **siempre admite**
    `n_presentes`. `es_sustituta` distingue la ruta del Req 8.8 (llegaron menos
    jugadoras de las planeadas) y `motivo` explica la decisión en una frase.
    """

    n_presentes: int
    sesion: Sesion
    es_sustituta: bool
    motivo: str


def _admite(rango: tuple[int, int], n: int) -> bool:
    """`True` si `n` cae dentro del rango cerrado `[min, max]`."""
    return rango[0] <= n <= rango[1]


def sesion_admite(sesion: Sesion, n: int) -> bool:
    """`True` si el rango de jugadoras de la sesión admite `n` jugadoras."""
    return _admite(sesion.jugadoras, n)


def _sesiones_del_plan(plan: PlanRotacion) -> list[Sesion]:
    """Todas las sesiones del plan en orden determinista (bloque, luego día).

    Recorre los bloques en su orden de plan y, dentro de cada uno, los días en
    el orden del `Enum Dia` (martes, miércoles, jueves), de modo que el orden no
    dependa del orden de inserción del `dict` ni de la semilla.
    """
    sesiones: list[Sesion] = []
    for bloque in plan.bloques:
        for dia in Dia:
            sesion = bloque.sesiones.get(dia)
            if sesion is not None:
                sesiones.append(sesion)
    return sesiones


def _clave_orden(sesion: Sesion) -> tuple[int, int, str, tuple[str, ...]]:
    """Clave de desempate determinista e independiente de la semilla."""
    return (
        sesion.jugadoras[0],
        sesion.jugadoras[1],
        sesion.foco,
        tuple(sorted(sesion.ficha_ids)),
    )


def resolver_sustituta(sesion: Sesion, n: int) -> Sesion:
    """Sesión sustituta para cuando llegan `n` jugadoras, con `n < min` (Req 8.8).

    Cuando llega menos gente de la que la sesión planeada necesita, se ejecuta la
    versión reducida centrada en la ficha de menor exigencia (`sustituta_id`). El
    rango de la sustituta es `(1, min - 1)`: cubre **toda** asistencia por debajo
    de lo planeado, así que admite cualquier `n` con `1 <= n < min` (segunda
    mitad de Property 14).

    Lanza `ValueError` si `n` no es menor que el mínimo de la sesión (en ese caso
    la propia sesión ya sirve y no hace falta sustituta).
    """
    minimo = sesion.jugadoras[0]
    if n < 1:
        raise ValueError(f'n debe ser >= 1, es {n}')
    if n >= minimo:
        raise ValueError(
            f'no procede sustituta: {n} jugadoras ya caben en el rango '
            f'{sesion.jugadoras[0]}–{sesion.jugadoras[1]} de la sesión'
        )

    tope = minimo - 1  # >= 1 porque n >= 1 y n < minimo => minimo >= 2
    ids = [sesion.sustituta_id] if sesion.sustituta_id else list(sesion.ficha_ids[:1])
    bloques = [
        BloqueSesion(nombre=nombre, minutos=minutos)
        for nombre, minutos in _PRESUPUESTO_VERSION_CORTA
    ]
    return Sesion(
        dia=sesion.dia,
        foco=sesion.foco,
        bloques=bloques,
        total_min=sum(b.minutos for b in bloques),
        ficha_ids=ids,
        jugadoras=(1, tope),
        version_corta=None,
        sustituta_id=sesion.sustituta_id,
    )


def resolver_por_jugadoras(plan: PlanRotacion, n: int) -> ResolucionSesion:
    """Resuelve qué sesión ejecutar con `n` jugadoras presentes (Req 8.2, 8.8).

    `n` debe estar en el dominio de la tabla (1..11). El resultado es una
    `ResolucionSesion` cuya sesión admite `n` por construcción; véase la nota de
    cabecera para las tres rutas (ajuste exacto, sustituta y grupos adicionales).
    Lanza `ValueError` si `n` está fuera de 1..11 o si el plan no tiene sesiones.
    """
    if not (MIN_JUGADORAS_TABLA <= n <= MAX_JUGADORAS_TABLA):
        raise ValueError(
            f'n fuera del dominio de la tabla '
            f'[{MIN_JUGADORAS_TABLA}, {MAX_JUGADORAS_TABLA}]: {n}'
        )

    sesiones = _sesiones_del_plan(plan)
    if not sesiones:
        raise ValueError('el plan no tiene sesiones que resolver')

    # Ruta 1: ajuste exacto. De las que admiten n, la de rango más ceñido.
    exactas = [s for s in sesiones if sesion_admite(s, n)]
    if exactas:
        elegida = min(
            exactas,
            key=lambda s: (s.jugadoras[1] - s.jugadoras[0], _clave_orden(s)),
        )
        return ResolucionSesion(
            n_presentes=n,
            sesion=elegida,
            es_sustituta=False,
            motivo=(
                f'{n} jugadoras: sesión con rango '
                f'{elegida.jugadoras[0]}–{elegida.jugadoras[1]}.'
            ),
        )

    minimo_global = min(s.jugadoras[0] for s in sesiones)
    maximo_global = max(s.jugadoras[1] for s in sesiones)

    # Ruta 2: llegaron menos de lo que pide cualquier sesión -> sustituta reducida.
    if n < minimo_global:
        base = min(sesiones, key=_clave_orden)
        sustituta = resolver_sustituta(base, n)
        return ResolucionSesion(
            n_presentes=n,
            sesion=sustituta,
            es_sustituta=True,
            motivo=(
                f'Llegaron {n} (menos del mínimo {base.jugadoras[0]}): '
                f'sesión sustituta reducida.'
            ),
        )

    # Ruta 3: hay más jugadoras que el tope de cualquier sesión -> grupos extra.
    base = max(sesiones, key=lambda s: (s.jugadoras[1], -s.jugadoras[0]))
    adaptada = replace(base, jugadoras=(base.jugadoras[0], n))
    return ResolucionSesion(
        n_presentes=n,
        sesion=adaptada,
        es_sustituta=False,
        motivo=(
            f'{n} jugadoras (más del máximo {maximo_global}): ejecutar la sesión '
            f'de mayor capacidad formando grupos adicionales que rotan.'
        ),
    )


def tabla_decision_jugadoras(plan: PlanRotacion) -> dict[int, ResolucionSesion]:
    """Tabla de decisión completa de 1 a 11 jugadoras (Req 8.2, Property 14).

    Devuelve un `dict` con **una** entrada por cada asistencia del dominio
    (1..11), cada una con una sesión cuyo rango la admite. La totalidad está
    garantizada por `resolver_por_jugadoras`.
    """
    return {n: resolver_por_jugadoras(plan, n) for n in RANGO_TABLA_DECISION}


def _dims_espacio_reducido(ficha: FichaEjercicio) -> tuple[float, float] | None:
    """Medidas (ancho, largo) en metros de la variante para espacio reducido.

    Prefiere la `Variante` de `espacio_reducido` (Req 8.4); si la ficha no la
    trae, cae al `montaje` (dataclass o `dict` del adaptador JSON). Devuelve
    `None` cuando no hay medidas utilizables.
    """
    reducido = getattr(ficha, 'espacio_reducido', None)
    if isinstance(reducido, Variante):
        return (float(reducido.ancho_m), float(reducido.largo_m))

    montaje = getattr(ficha, 'montaje', None)
    if isinstance(montaje, Montaje):
        return (float(montaje.ancho_m), float(montaje.largo_m))
    if isinstance(montaje, dict):
        ancho = montaje.get('ancho_m')
        largo = montaje.get('largo_m')
        if isinstance(ancho, (int, float)) and isinstance(largo, (int, float)):
            return (float(ancho), float(largo))

    return None


def fichas_en_espacio_reducido(
    fichas: Iterable[FichaEjercicio],
    *,
    lado_m: float = LADO_ESPACIO_REDUCIDO_M,
) -> list[FichaEjercicio]:
    """Fichas ejecutables en una franja de `lado_m` × `lado_m` o menor (Req 8.6).

    Mientras la cancha está ocupada por otros grupos, solo caben las fichas cuya
    variante de espacio reducido (o, en su defecto, su montaje) entra en una
    franja lateral de a lo sumo `lado_m` metros de lado. Conserva el orden de
    entrada y descarta las fichas sin medidas utilizables.
    """
    seleccion: list[FichaEjercicio] = []
    for ficha in fichas:
        dims = _dims_espacio_reducido(ficha)
        if dims is None:
            continue
        ancho, largo = dims
        if 0 < ancho <= lado_m and 0 < largo <= lado_m:
            seleccion.append(ficha)
    return seleccion
