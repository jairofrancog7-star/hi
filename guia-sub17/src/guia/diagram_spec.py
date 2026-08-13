"""Modelos inmutables del Motor_Diagramas y puente `cancha` -> `DiagramaSpec`.

Este módulo define los specs de diagrama de cancha como `dataclass`
`frozen=True, slots=True` que usan **tuplas** (nunca listas) en sus campos de
colección. De este modo los specs son *hashables* y se pueden usar como clave
de caché o argumento de `functools.lru_cache` sin necesidad de serializarlos.

El sistema de coordenadas del Mundo tiene su **origen abajo-izquierda** y el
eje Y apunta **hacia arriba** (convención de cancha, como en un plano). El
flip a coordenadas SVG (Y hacia abajo) lo hace el renderizador en `viz.py`.

Convenciones del proyecto respetadas aquí:

* `from __future__ import annotations` al inicio.
* Sin `assert` en producción: la validación se hace con `raise` de
  `ErrorLayout(codigo=E_COORDENADA_INVALIDA, ...)`.
* Sin concatenación de strings dentro de bucles.

Esquema del campo `cancha` de una Ficha_JSON que entiende `desde_cancha_json`::

    {
      "mundo":     {"ancho_m": float, "alto_m": float},   # opcional
      "jugadores": [ {"x", "y", "numero"?, "equipo"?, "etiqueta"?}, ... ],
      "conos":     [ {"x", "y"}, ... ],
      "flechas":   [ {"tipo"?, "x", "y", "x2", "y2", "etiqueta"?}, ... ],
      "balon":     {"x", "y"} | null,
      "zonas":     [ {"puntos": [[x, y], ...], "etiqueta"?}, ... ],
      "titulo":    str,                                    # opcional
    }

Donde:

* ``jugadores[].equipo`` es uno de ``"propio"`` (por defecto, item ``player``),
  ``"rival"`` (item ``rival``) o ``"gk"`` (item ``gk``, portera).
* ``flechas[].tipo`` es uno de ``"run"``, ``"pass"`` (por defecto),
  ``"dribble"`` o ``"shot"``.
* Si ``mundo`` falta, se usa media cancha: ``Mundo(40.0, 30.0)``.

Si ``cancha`` viene vacío (``{}`` o falsy), `desde_cancha_json` devuelve
``None`` (la ficha no tiene diagrama).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from . import paleta
from .errores import E_COORDENADA_INVALIDA, ErrorLayout

__all__ = [
    "ClaseDiagrama",
    "Mundo",
    "Item",
    "Leyenda",
    "DiagramaSpec",
    "desde_cancha_json",
    "MUNDO_POR_DEFECTO",
    "TIPOS_ITEM",
    "TIPOS_FLECHA",
    # --- Diagrama_Botin (tarea 3.5) ---
    "Vista",
    "Trama",
    "ZonaBotin",
    "BotinSpec",
    "BOTIN_PLANTA_CONTORNO",
    "BOTIN_PERFIL_CONTORNO",
    "BOTIN_PLANTA_COSTURA",
    "BOTIN_PERFIL_SUELA",
    "ZONAS_BOTIN",
    "ADYACENTES",
    "MARGEN_DISTINGUIBLE",
    "BOTIN_VISTA_ANCHO",
    "BOTIN_VISTA_ALTO",
    "BOTIN_GAP_VISTAS",
    "aplanar_bezier",
    "contorno_a_poligono",
    "punto_en_poligono",
    "bbox_poligono",
    "contorno_de_vista",
    "poligono_contorno",
    "offset_de_vista",
    "zona_dentro_de_contorno",
    "validar_zonas_en_contorno",
    "zonas_por_nombre",
    "color_base_zona",
    "son_distinguibles",
    "pares_no_distinguibles",
    "verificar_distinguibilidad",
    "segmentos_trama",
    "puntos_trama",
    "botin_por_defecto",
]

# --------------------------------------------------------------------------- #
# Constantes de módulo
# --------------------------------------------------------------------------- #

#: Tipos de item permitidos en el campo `tipo` de un `Item`.
TIPOS_ITEM: frozenset[str] = frozenset(
    {
        "player",
        "rival",
        "gk",
        "ball",
        "cone",
        "run",
        "pass",
        "dribble",
        "shot",
        "txt",
        "zone",
        "poly",
        "mark",
        "seg",
        "boot",
        "target",
    }
)

#: Tipos de item que representan un segmento o flecha (usan `x2`, `y2`).
TIPOS_SEGMENTO: frozenset[str] = frozenset(
    {"run", "pass", "dribble", "shot", "seg"}
)

#: Tipos de item que se dibujan como polígono (usan `puntos`).
TIPOS_POLIGONO: frozenset[str] = frozenset({"zone", "poly"})

#: Tipos de flecha válidos en el campo `cancha`.
TIPOS_FLECHA: frozenset[str] = frozenset({"run", "pass", "dribble", "shot"})

#: Mapa de `equipo` (en el JSON) al `tipo` de item correspondiente.
_EQUIPO_A_TIPO: dict[str, str] = {
    "propio": "player",
    "rival": "rival",
    "gk": "gk",
}


# --------------------------------------------------------------------------- #
# Modelos inmutables
# --------------------------------------------------------------------------- #


class ClaseDiagrama(str, Enum):
    """Clase de diagrama que produce el Motor_Diagramas."""

    CANCHA = "cancha"
    BOTIN = "botin"
    POSTURA = "postura"


@dataclass(frozen=True, slots=True)
class Mundo:
    """Dimensiones del mundo en metros (origen abajo-izquierda, Y arriba)."""

    ancho_m: float
    alto_m: float


#: Mundo por defecto cuando la ficha no declara `mundo`: media cancha.
MUNDO_POR_DEFECTO: Mundo = Mundo(40.0, 30.0)


@dataclass(frozen=True, slots=True)
class Item:
    """Un elemento del diagrama, con coordenadas en metros del Mundo.

    Todos los campos de colección son tuplas para que el `Item` sea hashable.
    Según el `tipo` se usan unos campos u otros:

    * puntuales (``player``, ``rival``, ``gk``, ``ball``, ``cone``, ``txt``,
      ``mark``, ``boot``, ``target``): usan ``x``, ``y``.
    * segmentos/flechas (``run``, ``pass``, ``dribble``, ``shot``, ``seg``):
      usan ``x``, ``y`` (origen) y ``x2``, ``y2`` (destino).
    * polígonos (``zone``, ``poly``): usan ``puntos``.
    """

    tipo: str
    x: float = 0.0
    y: float = 0.0
    x2: float | None = None
    y2: float | None = None
    puntos: tuple[tuple[float, float], ...] = ()
    etiqueta: str = ""
    numero: int | None = None
    equipo: str | None = None
    color: str | None = None


@dataclass(frozen=True, slots=True)
class Leyenda:
    """Entrada mínima de leyenda: un símbolo y su texto explicativo."""

    texto: str
    simbolo: str


@dataclass(frozen=True, slots=True)
class DiagramaSpec:
    """Spec inmutable y hashable de un diagrama de cancha."""

    clase: ClaseDiagrama
    mundo: Mundo
    items: tuple[Item, ...]
    titulo: str | None = None
    leyenda: tuple[Leyenda, ...] = ()


# --------------------------------------------------------------------------- #
# Validación de coordenadas (sin `assert`)
# --------------------------------------------------------------------------- #


def _validar_coord(
    valor: Any,
    *,
    limite: float,
    eje: str,
    contexto: str,
) -> float:
    """Valida que `valor` sea un número finito dentro de `[0, limite]`.

    Devuelve el valor convertido a `float`. Si no es finito o cae fuera del
    rango, lanza `ErrorLayout` con `E_COORDENADA_INVALIDA`. No usa `assert`.
    """
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ErrorLayout(
            f"diagrama {contexto}: coordenada invalida {valor!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": contexto, "eje": eje, "valor": repr(valor)},
        ) from None

    if not math.isfinite(numero):
        raise ErrorLayout(
            f"diagrama {contexto}: coordenada invalida {numero}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": contexto, "eje": eje, "valor": numero},
        )

    if numero < 0.0 or numero > limite:
        raise ErrorLayout(
            f"diagrama {contexto}: coordenada invalida {numero}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={
                "contexto": contexto,
                "eje": eje,
                "valor": numero,
                "limite": limite,
            },
        )

    return numero


def _validar_punto(
    x: Any,
    y: Any,
    *,
    mundo: Mundo,
    contexto: str,
) -> tuple[float, float]:
    """Valida un par ``(x, y)`` contra las dimensiones del mundo."""
    vx = _validar_coord(x, limite=mundo.ancho_m, eje="x", contexto=contexto)
    vy = _validar_coord(y, limite=mundo.alto_m, eje="y", contexto=contexto)
    return vx, vy


# --------------------------------------------------------------------------- #
# Puente `cancha` (JSON) -> DiagramaSpec
# --------------------------------------------------------------------------- #


def _mundo_desde_json(cancha: dict[str, Any]) -> Mundo:
    """Lee el sub-objeto `mundo` o devuelve el mundo por defecto."""
    crudo = cancha.get("mundo")
    if not isinstance(crudo, dict):
        return MUNDO_POR_DEFECTO

    ancho = crudo.get("ancho_m", MUNDO_POR_DEFECTO.ancho_m)
    alto = crudo.get("alto_m", MUNDO_POR_DEFECTO.alto_m)

    try:
        ancho_f = float(ancho)
        alto_f = float(alto)
    except (TypeError, ValueError):
        raise ErrorLayout(
            f"diagrama mundo: coordenada invalida {crudo!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "mundo", "valor": repr(crudo)},
        ) from None

    if not (math.isfinite(ancho_f) and math.isfinite(alto_f)):
        raise ErrorLayout(
            f"diagrama mundo: coordenada invalida {crudo!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "mundo", "valor": repr(crudo)},
        )

    if ancho_f <= 0.0 or alto_f <= 0.0:
        raise ErrorLayout(
            f"diagrama mundo: coordenada invalida {crudo!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "mundo", "ancho_m": ancho_f, "alto_m": alto_f},
        )

    return Mundo(ancho_f, alto_f)


def _jugadores_a_items(
    jugadores: Any,
    *,
    mundo: Mundo,
) -> list[Item]:
    """Convierte la lista `jugadores` del JSON en items player/rival/gk."""
    if not jugadores:
        return []
    if not isinstance(jugadores, (list, tuple)):
        raise ErrorLayout(
            f"diagrama jugadores: coordenada invalida {jugadores!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "jugadores", "valor": repr(jugadores)},
        )

    items: list[Item] = []
    for indice, jugador in enumerate(jugadores):
        contexto = f"jugador[{indice}]"
        if not isinstance(jugador, dict):
            raise ErrorLayout(
                f"diagrama {contexto}: coordenada invalida {jugador!r}",
                codigo=E_COORDENADA_INVALIDA,
                detalle={"contexto": contexto, "valor": repr(jugador)},
            )

        x, y = _validar_punto(
            jugador.get("x"), jugador.get("y"), mundo=mundo, contexto=contexto
        )

        equipo = jugador.get("equipo", "propio")
        tipo = _EQUIPO_A_TIPO.get(str(equipo), "player")

        numero_crudo = jugador.get("numero")
        numero = int(numero_crudo) if isinstance(numero_crudo, int) else None

        items.append(
            Item(
                tipo=tipo,
                x=x,
                y=y,
                etiqueta=str(jugador.get("etiqueta", "")),
                numero=numero,
                equipo=str(equipo),
            )
        )
    return items


def _conos_a_items(conos: Any, *, mundo: Mundo) -> list[Item]:
    """Convierte la lista `conos` del JSON en items cone."""
    if not conos:
        return []
    if not isinstance(conos, (list, tuple)):
        raise ErrorLayout(
            f"diagrama conos: coordenada invalida {conos!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "conos", "valor": repr(conos)},
        )

    items: list[Item] = []
    for indice, cono in enumerate(conos):
        contexto = f"cono[{indice}]"
        if not isinstance(cono, dict):
            raise ErrorLayout(
                f"diagrama {contexto}: coordenada invalida {cono!r}",
                codigo=E_COORDENADA_INVALIDA,
                detalle={"contexto": contexto, "valor": repr(cono)},
            )
        x, y = _validar_punto(
            cono.get("x"), cono.get("y"), mundo=mundo, contexto=contexto
        )
        items.append(Item(tipo="cone", x=x, y=y))
    return items


def _flechas_a_items(flechas: Any, *, mundo: Mundo) -> list[Item]:
    """Convierte la lista `flechas` del JSON en items de segmento."""
    if not flechas:
        return []
    if not isinstance(flechas, (list, tuple)):
        raise ErrorLayout(
            f"diagrama flechas: coordenada invalida {flechas!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "flechas", "valor": repr(flechas)},
        )

    items: list[Item] = []
    for indice, flecha in enumerate(flechas):
        contexto = f"flecha[{indice}]"
        if not isinstance(flecha, dict):
            raise ErrorLayout(
                f"diagrama {contexto}: coordenada invalida {flecha!r}",
                codigo=E_COORDENADA_INVALIDA,
                detalle={"contexto": contexto, "valor": repr(flecha)},
            )

        tipo = str(flecha.get("tipo", "pass"))
        if tipo not in TIPOS_FLECHA:
            tipo = "pass"

        x, y = _validar_punto(
            flecha.get("x"), flecha.get("y"), mundo=mundo, contexto=contexto
        )
        x2, y2 = _validar_punto(
            flecha.get("x2"),
            flecha.get("y2"),
            mundo=mundo,
            contexto=f"{contexto}.destino",
        )
        items.append(
            Item(
                tipo=tipo,
                x=x,
                y=y,
                x2=x2,
                y2=y2,
                etiqueta=str(flecha.get("etiqueta", "")),
            )
        )
    return items


def _balon_a_items(balon: Any, *, mundo: Mundo) -> list[Item]:
    """Convierte el sub-objeto `balon` (o null) en un item ball."""
    if balon is None:
        return []
    if not isinstance(balon, dict):
        raise ErrorLayout(
            f"diagrama balon: coordenada invalida {balon!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "balon", "valor": repr(balon)},
        )
    x, y = _validar_punto(
        balon.get("x"), balon.get("y"), mundo=mundo, contexto="balon"
    )
    return [Item(tipo="ball", x=x, y=y)]


def _zonas_a_items(zonas: Any, *, mundo: Mundo) -> list[Item]:
    """Convierte la lista `zonas` del JSON en items zone (polígonos)."""
    if not zonas:
        return []
    if not isinstance(zonas, (list, tuple)):
        raise ErrorLayout(
            f"diagrama zonas: coordenada invalida {zonas!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "zonas", "valor": repr(zonas)},
        )

    items: list[Item] = []
    for indice, zona in enumerate(zonas):
        contexto = f"zona[{indice}]"
        if not isinstance(zona, dict):
            raise ErrorLayout(
                f"diagrama {contexto}: coordenada invalida {zona!r}",
                codigo=E_COORDENADA_INVALIDA,
                detalle={"contexto": contexto, "valor": repr(zona)},
            )

        puntos_crudos = zona.get("puntos", ())
        if not isinstance(puntos_crudos, (list, tuple)) or len(puntos_crudos) < 3:
            raise ErrorLayout(
                f"diagrama {contexto}: coordenada invalida {puntos_crudos!r}",
                codigo=E_COORDENADA_INVALIDA,
                detalle={"contexto": contexto, "valor": repr(puntos_crudos)},
            )

        validos: list[tuple[float, float]] = []
        for j, par in enumerate(puntos_crudos):
            if not isinstance(par, (list, tuple)) or len(par) != 2:
                raise ErrorLayout(
                    f"diagrama {contexto}[{j}]: coordenada invalida {par!r}",
                    codigo=E_COORDENADA_INVALIDA,
                    detalle={"contexto": f"{contexto}[{j}]", "valor": repr(par)},
                )
            vx, vy = _validar_punto(
                par[0], par[1], mundo=mundo, contexto=f"{contexto}[{j}]"
            )
            validos.append((vx, vy))

        items.append(
            Item(
                tipo="zone",
                puntos=tuple(validos),
                etiqueta=str(zona.get("etiqueta", "")),
            )
        )
    return items


def desde_cancha_json(cancha: dict[str, Any]) -> DiagramaSpec | None:
    """Construye un `DiagramaSpec` desde el campo `cancha` de una Ficha_JSON.

    `schema_json.py` busca esta función por nombre (`getattr`), así que el
    nombre y la firma son parte del contrato entre módulos.

    Devuelve ``None`` cuando `cancha` viene vacío (``{}`` o falsy): la ficha no
    tiene diagrama asociado. En otro caso mapea cada entrada a su `Item` con el
    `tipo` correcto (propio->player, rival->rival, gk->gk, cono->cone,
    balón->ball, zona->zone, flecha->run/pass/dribble/shot) y valida que toda
    coordenada sea finita y caiga dentro del mundo, lanzando `ErrorLayout` con
    `E_COORDENADA_INVALIDA` si no.
    """
    if not cancha:
        return None
    if not isinstance(cancha, dict):
        raise ErrorLayout(
            f"diagrama cancha: coordenada invalida {cancha!r}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "cancha", "valor": repr(cancha)},
        )

    mundo = _mundo_desde_json(cancha)

    items: list[Item] = []
    items.extend(_zonas_a_items(cancha.get("zonas"), mundo=mundo))
    items.extend(_conos_a_items(cancha.get("conos"), mundo=mundo))
    items.extend(_flechas_a_items(cancha.get("flechas"), mundo=mundo))
    items.extend(_jugadores_a_items(cancha.get("jugadores"), mundo=mundo))
    items.extend(_balon_a_items(cancha.get("balon"), mundo=mundo))

    titulo_crudo = cancha.get("titulo")
    titulo = str(titulo_crudo) if titulo_crudo else None

    return DiagramaSpec(
        clase=ClaseDiagrama.CANCHA,
        mundo=mundo,
        items=tuple(items),
        titulo=titulo,
    )


# =========================================================================== #
# Diagrama_Botin (tarea 3.5): siluetas Bézier + 7 zonas con trama
# =========================================================================== #
#
# El Diagrama_Botin muestra dos siluetas de botín (vista de planta y vista de
# perfil) sobre las que se recortan siete zonas de contacto, cada una con un
# gris base y una trama vectorial que garantiza que se distingan también en
# monocromo (Req 3.9, Property 11). Las siluetas se describen con curvas Bézier
# cúbicas en un mundo local de 240 x 380 unidades por vista; el aplanado a
# polígono (`aplanar_bezier` / `contorno_a_poligono`) se usa tanto para el
# recorte punto-en-polígono de las pruebas como para validar que toda zona cae
# dentro de su contorno.
#
# Cada vista vive en su propio marco local con origen abajo-izquierda y Y hacia
# arriba (igual convención que el Mundo de cancha). El renderizador desplaza la
# vista de perfil a la derecha con `offset_de_vista`.


class Vista(str, Enum):
    """Vista del botín: planta (desde arriba) o perfil (lateral externa)."""

    PLANTA = "planta"
    PERFIL = "perfil"


class Trama(str, Enum):
    """Patrón de trama de una zona. El ángulo va embebido en las líneas para
    que dos zonas con líneas a distinta orientación cuenten como *tramas
    distintas* en la regla de distinguibilidad (Property 11)."""

    LINEAS_45 = "lineas_45"
    LINEAS_135 = "lineas_135"
    LINEAS_90 = "lineas_90"
    PUNTOS = "puntos"
    CUADRICULA = "cuadricula"
    SOLIDO = "solido"


#: Ancho/alto del marco local de cada vista, en unidades del botín.
BOTIN_VISTA_ANCHO: float = 240.0
BOTIN_VISTA_ALTO: float = 380.0

#: Separación horizontal entre la vista de planta y la de perfil.
BOTIN_GAP_VISTAS: float = 40.0

#: Umbral de diferencia de gris para considerar dos zonas distinguibles en
#: monocromo cuando comparten patrón de trama (Property 11).
MARGEN_DISTINGUIBLE: float = 0.18


# --------------------------------------------------------------------------- #
# Contornos Bézier (tuplas de tuplas -> hashables y cacheables)
# --------------------------------------------------------------------------- #
#
# Cada contorno es una tupla de comandos; cada comando es ``(op, args)`` con:
#   ('M', (x, y))                       -> mover a
#   ('C', (x1, y1, x2, y2, x3, y3))     -> Bézier cúbica (control1, control2, fin)
#   ('L', (x, y))                       -> línea a
#   ('Z', ())                           -> cerrar
# El punto inicial de cada 'C'/'L' es el punto actual del recorrido.

# Vista superior (planta): contorno cerrado con 6 Bézier cúbicas.
# Origen local: talón centrado abajo (120, 18), punta hacia arriba.
BOTIN_PLANTA_CONTORNO: tuple[tuple[str, tuple[float, ...]], ...] = (
    ("M", (120.0, 18.0)),
    ("C", (78.0, 20.0, 56.0, 58.0, 52.0, 118.0)),      # borde interior del talón
    ("C", (48.0, 190.0, 60.0, 258.0, 78.0, 306.0)),    # interior del arco -> pase
    ("C", (92.0, 344.0, 118.0, 362.0, 140.0, 360.0)),  # punta
    ("C", (168.0, 358.0, 186.0, 330.0, 190.0, 292.0)), # exterior delantero -> tres dedos
    ("C", (196.0, 232.0, 192.0, 150.0, 180.0, 104.0)), # exterior medio -> efecto
    ("C", (170.0, 56.0, 152.0, 18.0, 120.0, 18.0)),    # exterior del talón
    ("Z", ()),
)

# Línea decorativa de cordones (dos Bézier suaves por el centro de la planta).
BOTIN_PLANTA_COSTURA: tuple[tuple[str, tuple[float, ...]], ...] = (
    ("M", (120.0, 150.0)),
    ("C", (110.0, 195.0, 110.0, 250.0, 120.0, 296.0)),
)

# Vista de perfil (lateral externa): contorno cerrado con 4 Bézier + suela recta.
BOTIN_PERFIL_CONTORNO: tuple[tuple[str, tuple[float, ...]], ...] = (
    ("M", (28.0, 24.0)),
    ("C", (24.0, 76.0, 34.0, 112.0, 62.0, 130.0)),     # caña / talón
    ("C", (104.0, 152.0, 150.0, 148.0, 186.0, 128.0)), # empeine -> cañonazo
    ("C", (214.0, 112.0, 230.0, 86.0, 232.0, 52.0)),   # punta alta
    ("C", (232.0, 32.0, 220.0, 24.0, 200.0, 24.0)),    # punta baja
    ("L", (28.0, 24.0)),                               # suela = planta
    ("Z", ()),
)

# Banda de suela con altura fija bajo el perfil (decorativa, dientes de taco).
BOTIN_PERFIL_SUELA: tuple[tuple[float, float], ...] = (
    (28.0, 24.0),
    (200.0, 24.0),
    (200.0, 14.0),
    (28.0, 14.0),
)


# --------------------------------------------------------------------------- #
# Geometría: aplanado de Bézier y punto-en-polígono
# --------------------------------------------------------------------------- #


def aplanar_bezier(
    controles: tuple[tuple[float, float], ...],
    segmentos: int = 12,
) -> tuple[tuple[float, float], ...]:
    """Aplana una Bézier cúbica a ``segmentos`` tramos rectos.

    ``controles`` es la tupla de los 4 puntos de control
    ``((x0, y0), (x1, y1), (x2, y2), (x3, y3))``. Devuelve ``segmentos + 1``
    puntos, incluyendo ambos extremos. No usa `assert`.
    """
    if len(controles) != 4:
        raise ErrorLayout(
            f"aplanar_bezier: se esperaban 4 puntos de control, no {len(controles)}",
            codigo=E_COORDENADA_INVALIDA,
            detalle={"contexto": "aplanar_bezier", "n": len(controles)},
        )
    if segmentos < 1:
        segmentos = 1
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = controles
    puntos: list[tuple[float, float]] = []
    for i in range(segmentos + 1):
        t = i / segmentos
        u = 1.0 - t
        a = u * u * u
        b = 3.0 * u * u * t
        c = 3.0 * u * t * t
        d = t * t * t
        px = a * x0 + b * x1 + c * x2 + d * x3
        py = a * y0 + b * y1 + c * y2 + d * y3
        puntos.append((px, py))
    return tuple(puntos)


def contorno_a_poligono(
    contorno: tuple[tuple[str, tuple[float, ...]], ...],
    segmentos: int = 12,
) -> tuple[tuple[float, float], ...]:
    """Aplana un contorno (M/C/L/Z) a un polígono cerrado de puntos.

    Cada 'C' se aplana con `aplanar_bezier` a ``segmentos`` tramos. Los puntos
    duplicados consecutivos (extremo compartido entre comandos) se colapsan.
    """
    puntos: list[tuple[float, float]] = []
    actual: tuple[float, float] | None = None

    def _agregar(p: tuple[float, float]) -> None:
        if puntos and puntos[-1] == p:
            return
        puntos.append(p)

    for op, args in contorno:
        if op == "M":
            actual = (float(args[0]), float(args[1]))
            _agregar(actual)
        elif op == "L":
            destino = (float(args[0]), float(args[1]))
            _agregar(destino)
            actual = destino
        elif op == "C":
            if actual is None:
                raise ErrorLayout(
                    "contorno_a_poligono: 'C' sin punto inicial",
                    codigo=E_COORDENADA_INVALIDA,
                    detalle={"contexto": "contorno_a_poligono"},
                )
            controles = (
                actual,
                (float(args[0]), float(args[1])),
                (float(args[2]), float(args[3])),
                (float(args[4]), float(args[5])),
            )
            for p in aplanar_bezier(controles, segmentos)[1:]:
                _agregar(p)
            actual = controles[3]
        elif op == "Z":
            if puntos and puntos[0] != puntos[-1]:
                _agregar(puntos[0])
        # otros comandos se ignoran
    # No dejar el punto de cierre repetido al final para un polígono limpio.
    if len(puntos) >= 2 and puntos[0] == puntos[-1]:
        puntos.pop()
    return tuple(puntos)


def punto_en_poligono(
    punto: tuple[float, float],
    poligono: tuple[tuple[float, float], ...],
) -> bool:
    """Test punto-en-polígono por lanzamiento de rayo (regla par-impar).

    Devuelve ``True`` si ``punto`` está dentro de ``poligono`` (los puntos
    exactamente sobre un borde pueden dar cualquiera de los dos resultados; las
    zonas del botín se diseñan estrictamente en el interior).
    """
    x, y = punto
    dentro = False
    n = len(poligono)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = poligono[i]
        xj, yj = poligono[j]
        if (yi > y) != (yj > y):
            corte_x = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < corte_x:
                dentro = not dentro
        j = i
    return dentro


def bbox_poligono(
    poligono: tuple[tuple[float, float], ...],
) -> tuple[float, float, float, float]:
    """Devuelve ``(min_x, min_y, max_x, max_y)`` del polígono."""
    if not poligono:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------- #
# Las 7 zonas con gris base + trama + acción de juego
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ZonaBotin:
    """Una zona de contacto del botín, recortada contra su contorno.

    ``gris`` es el nivel de gris base (luminancia en ``[0, 1]``) que usa la
    regla de distinguibilidad en monocromo. ``trama`` es el patrón vectorial
    superpuesto (Property 11). ``poligono`` está en el marco local de ``vista``.
    """

    nombre: str
    vista: Vista
    gris: float
    trama: Trama
    accion: str
    poligono: tuple[tuple[float, float], ...]
    angulo: int | None = None
    paso: float | None = None


#: Las siete zonas del botín. Los polígonos están diseñados en el interior del
#: contorno de su vista (verificado por `validar_zonas_en_contorno`) y no se
#: solapan dentro de una misma vista.
ZONAS_BOTIN: tuple[ZonaBotin, ...] = (
    ZonaBotin(
        nombre="pase",
        vista=Vista.PLANTA,
        gris=0.88,
        trama=Trama.LINEAS_45,
        accion="Pase raso, control orientado",
        poligono=((84.0, 128.0), (118.0, 128.0), (118.0, 292.0), (84.0, 292.0)),
        angulo=45,
        paso=4.0,
    ),
    ZonaBotin(
        nombre="efecto",
        vista=Vista.PLANTA,
        gris=0.70,
        trama=Trama.LINEAS_135,
        accion="Pase con comba, recorte",
        poligono=((124.0, 128.0), (176.0, 128.0), (176.0, 285.0), (124.0, 285.0)),
        angulo=135,
        paso=4.0,
    ),
    ZonaBotin(
        nombre="tres_dedos",
        vista=Vista.PLANTA,
        gris=0.78,
        trama=Trama.PUNTOS,
        accion="Centro con rosca, pase largo",
        poligono=((92.0, 296.0), (172.0, 296.0), (156.0, 338.0), (110.0, 338.0)),
        paso=5.0,
    ),
    ZonaBotin(
        nombre="punta",
        vista=Vista.PLANTA,
        gris=0.44,
        trama=Trama.SOLIDO,
        accion="Puntera de urgencia, definición corta",
        poligono=((120.0, 340.0), (150.0, 340.0), (140.0, 356.0), (126.0, 352.0)),
    ),
    ZonaBotin(
        nombre="canonazo",
        vista=Vista.PERFIL,
        gris=0.62,
        trama=Trama.SOLIDO,
        accion="Disparo fuerte, despeje largo",
        poligono=((82.0, 56.0), (176.0, 56.0), (158.0, 130.0), (98.0, 130.0)),
    ),
    ZonaBotin(
        nombre="planta",
        vista=Vista.PERFIL,
        gris=0.92,
        trama=Trama.CUADRICULA,
        accion="Frenar el balón, suela",
        poligono=((44.0, 28.0), (196.0, 28.0), (196.0, 46.0), (44.0, 46.0)),
        angulo=0,
        paso=6.0,
    ),
    ZonaBotin(
        nombre="tacon",
        vista=Vista.PERFIL,
        gris=0.55,
        trama=Trama.LINEAS_90,
        accion="Pase atrás, sorpresa",
        poligono=((40.0, 52.0), (72.0, 52.0), (72.0, 116.0), (48.0, 116.0)),
        angulo=90,
        paso=3.0,
    ),
)


#: Grafo de adyacencia (anatómica) entre zonas. La regla de distinguibilidad
#: se aplica a cada par para que ninguna pareja se confunda en monocromo.
ADYACENTES: tuple[tuple[str, str], ...] = (
    ("pase", "planta"),
    ("pase", "punta"),
    ("punta", "tres_dedos"),
    ("tres_dedos", "efecto"),
    ("efecto", "pase"),
    ("canonazo", "punta"),
    ("canonazo", "tacon"),
    ("tacon", "planta"),
    ("planta", "canonazo"),
)


@dataclass(frozen=True, slots=True)
class BotinSpec:
    """Spec inmutable y hashable del Diagrama_Botin.

    Reúne los dos contornos Bézier, las siete zonas y el grafo de adyacencia.
    Como todos los campos son tuplas / dataclasses `frozen`, el spec es
    hashable y sirve de clave de caché o argumento de `functools.lru_cache`.
    """

    clase: ClaseDiagrama = ClaseDiagrama.BOTIN
    mundo: Mundo = Mundo(
        BOTIN_VISTA_ANCHO * 2.0 + BOTIN_GAP_VISTAS, BOTIN_VISTA_ALTO
    )
    titulo: str | None = None
    contorno_planta: tuple[tuple[str, tuple[float, ...]], ...] = BOTIN_PLANTA_CONTORNO
    contorno_perfil: tuple[tuple[str, tuple[float, ...]], ...] = BOTIN_PERFIL_CONTORNO
    costura_planta: tuple[tuple[str, tuple[float, ...]], ...] = BOTIN_PLANTA_COSTURA
    suela_perfil: tuple[tuple[float, float], ...] = BOTIN_PERFIL_SUELA
    zonas: tuple[ZonaBotin, ...] = ZONAS_BOTIN
    adyacentes: tuple[tuple[str, str], ...] = ADYACENTES


# --------------------------------------------------------------------------- #
# Utilidades sobre contornos y vistas
# --------------------------------------------------------------------------- #


def contorno_de_vista(
    vista: Vista,
    spec: BotinSpec | None = None,
) -> tuple[tuple[str, tuple[float, ...]], ...]:
    """Devuelve el contorno Bézier de la vista indicada."""
    spec = spec or botin_por_defecto()
    return spec.contorno_planta if vista is Vista.PLANTA else spec.contorno_perfil


def poligono_contorno(
    vista: Vista,
    segmentos: int = 12,
    spec: BotinSpec | None = None,
) -> tuple[tuple[float, float], ...]:
    """Aplana el contorno de una vista a polígono (para punto-en-polígono)."""
    return contorno_a_poligono(contorno_de_vista(vista, spec), segmentos)


def offset_de_vista(vista: Vista) -> tuple[float, float]:
    """Desplazamiento ``(dx, dy)`` del marco local de la vista en el mundo.

    La planta va pegada al origen; el perfil se desplaza a la derecha por el
    ancho de una vista más el hueco entre ambas.
    """
    if vista is Vista.PLANTA:
        return (0.0, 0.0)
    return (BOTIN_VISTA_ANCHO + BOTIN_GAP_VISTAS, 0.0)


def zonas_por_nombre(
    spec: BotinSpec | None = None,
) -> dict[str, ZonaBotin]:
    """Índice ``nombre -> ZonaBotin`` de las zonas del spec."""
    spec = spec or botin_por_defecto()
    return {z.nombre: z for z in spec.zonas}


def zona_dentro_de_contorno(
    zona: ZonaBotin,
    segmentos: int = 12,
    spec: BotinSpec | None = None,
) -> bool:
    """Indica si todos los vértices de la zona caen dentro de su contorno."""
    poligono = poligono_contorno(zona.vista, segmentos, spec)
    return all(punto_en_poligono(v, poligono) for v in zona.poligono)


def validar_zonas_en_contorno(
    spec: BotinSpec | None = None,
    segmentos: int = 12,
) -> None:
    """Valida que toda zona esté recortada dentro de su contorno.

    Lanza `ErrorLayout` con `E_COORDENADA_INVALIDA` nombrando la zona y el
    vértice fuera de la silueta. No usa `assert`.
    """
    spec = spec or botin_por_defecto()
    for zona in spec.zonas:
        poligono = poligono_contorno(zona.vista, segmentos, spec)
        for indice, vertice in enumerate(zona.poligono):
            if not punto_en_poligono(vertice, poligono):
                raise ErrorLayout(
                    f"Diagrama_Botin: la zona {zona.nombre} sale de su silueta",
                    codigo=E_COORDENADA_INVALIDA,
                    detalle={
                        "contexto": "botin",
                        "zona": zona.nombre,
                        "vista": zona.vista.value,
                        "vertice": indice,
                        "valor": repr(vertice),
                    },
                )


# --------------------------------------------------------------------------- #
# Distinguibilidad en monocromo (Property 11)
# --------------------------------------------------------------------------- #


def _lum_hex(color: str) -> float:
    """Luminancia aproximada (canal, ya que son grises) de un hex de paleta."""
    normal = paleta.normalizar_hex(color)
    r = int(normal[1:3], 16) / 255.0
    g = int(normal[3:5], 16) / 255.0
    b = int(normal[5:7], 16) / 255.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def color_base_zona(gris: float) -> str:
    """Devuelve el gris de la paleta más cercano al nivel ``gris`` de la zona.

    Así el relleno emitido pertenece siempre a la paleta declarada
    (Property 12) sin depender del color para transmitir la información.
    """
    return min(paleta.GRISES_TRAMA, key=lambda h: abs(_lum_hex(h) - gris))


def son_distinguibles(za: ZonaBotin, zb: ZonaBotin) -> bool:
    """Regla de distinguibilidad: distinta trama o gris que difiere >= 0.18."""
    if za.trama != zb.trama:
        return True
    return abs(za.gris - zb.gris) >= MARGEN_DISTINGUIBLE - 1e-9


def pares_no_distinguibles(
    spec: BotinSpec | None = None,
) -> list[tuple[str, str]]:
    """Lista los pares adyacentes que NO cumplen la regla de distinguibilidad."""
    spec = spec or botin_por_defecto()
    indice = zonas_por_nombre(spec)
    fallos: list[tuple[str, str]] = []
    for a, b in spec.adyacentes:
        za = indice.get(a)
        zb = indice.get(b)
        if za is None or zb is None:
            raise ValueError(f"adyacencia con zona inexistente: {(a, b)!r}")
        if not son_distinguibles(za, zb):
            fallos.append((a, b))
    return fallos


def verificar_distinguibilidad(spec: BotinSpec | None = None) -> None:
    """Comprueba la regla de distinguibilidad para todo par adyacente.

    Es un invariante estático de las constantes del módulo, no una entrada de
    usuario, así que un fallo indica un error de programación y se reporta con
    `ValueError` (no con `assert`, que `python -O` borraría).
    """
    fallos = pares_no_distinguibles(spec)
    if fallos:
        raise ValueError(
            f"zonas adyacentes indistinguibles en monocromo: {fallos!r}"
        )


# --------------------------------------------------------------------------- #
# Generadores de trama (geometría pura; el renderizador recorta a la zona)
# --------------------------------------------------------------------------- #


def _lineas_hatch(
    bbox: tuple[float, float, float, float],
    angulo_grados: float,
    paso: float,
) -> tuple[tuple[tuple[float, float], tuple[float, float]], ...]:
    """Genera segmentos de líneas paralelas que cubren el ``bbox``.

    Las líneas llevan la orientación ``angulo_grados`` y se separan ``paso`` en
    la dirección perpendicular. Se extienden más allá del bbox para que, al
    recortarse contra el polígono de la zona en el renderizador, cubran toda su
    superficie.
    """
    min_x, min_y, max_x, max_y = bbox
    if paso <= 0.0:
        paso = 4.0
    ang = math.radians(angulo_grados)
    dx = math.cos(ang)
    dy = math.sin(ang)
    nx = -dy  # normal unitaria
    ny = dx
    esquinas = (
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
    )
    proyecciones = [cx * nx + cy * ny for cx, cy in esquinas]
    p_min = min(proyecciones)
    p_max = max(proyecciones)
    largo = math.hypot(max_x - min_x, max_y - min_y) + paso
    segmentos: list[tuple[tuple[float, float], tuple[float, float]]] = []
    # Arranca en un múltiplo de `paso` por debajo de p_min (determinista).
    inicio = math.floor(p_min / paso) * paso
    o = inicio
    while o <= p_max + 1e-9:
        px = nx * o
        py = ny * o
        segmentos.append(
            (
                (px - dx * largo, py - dy * largo),
                (px + dx * largo, py + dy * largo),
            )
        )
        o += paso
    return tuple(segmentos)


def segmentos_trama(
    zona: ZonaBotin,
) -> tuple[tuple[tuple[float, float], tuple[float, float]], ...]:
    """Segmentos de la trama de líneas de una zona (vacío si no lleva líneas).

    Para `SOLIDO` y `PUNTOS` devuelve una tupla vacía (esas tramas no son de
    líneas). Para `CUADRICULA` combina líneas a 0° y 90°. Los segmentos están
    en el marco local de la vista de la zona; el renderizador los recorta al
    polígono de la zona.
    """
    bbox = bbox_poligono(zona.poligono)
    paso = zona.paso if zona.paso else 4.0
    if zona.trama is Trama.LINEAS_45:
        return _lineas_hatch(bbox, 45.0, paso)
    if zona.trama is Trama.LINEAS_135:
        return _lineas_hatch(bbox, 135.0, paso)
    if zona.trama is Trama.LINEAS_90:
        return _lineas_hatch(bbox, 90.0, paso)
    if zona.trama is Trama.CUADRICULA:
        return _lineas_hatch(bbox, 0.0, paso) + _lineas_hatch(bbox, 90.0, paso)
    return ()


def puntos_trama(zona: ZonaBotin) -> tuple[tuple[float, float], ...]:
    """Rejilla de puntos interiores al polígono (trama `PUNTOS`); vacío si no.

    Solo devuelve puntos que caen dentro del polígono, de modo que el
    renderizador puede dibujarlos como pequeños discos sin recortar.
    """
    if zona.trama is not Trama.PUNTOS:
        return ()
    paso = zona.paso if zona.paso else 5.0
    min_x, min_y, max_x, max_y = bbox_poligono(zona.poligono)
    puntos: list[tuple[float, float]] = []
    y = math.floor(min_y / paso) * paso
    while y <= max_y + 1e-9:
        x = math.floor(min_x / paso) * paso
        while x <= max_x + 1e-9:
            if punto_en_poligono((x, y), zona.poligono):
                puntos.append((x, y))
            x += paso
        y += paso
    return tuple(puntos)


# --------------------------------------------------------------------------- #
# Constructor
# --------------------------------------------------------------------------- #


def botin_por_defecto(titulo: str | None = None) -> BotinSpec:
    """Construye el `BotinSpec` estándar con las siete zonas y sus contornos.

    Es el punto de enganche que consumirán los renderizadores (`draw.py`,
    `viz.py`) y la plantilla de página del Diagrama_Botin (tarea 3.6, que añade
    la colocación de etiquetas externas con líneas guía).
    """
    return BotinSpec(titulo=titulo)
