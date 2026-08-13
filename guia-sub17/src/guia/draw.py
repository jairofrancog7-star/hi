"""Renderizador a operadores de contenido PDF del Motor_Diagramas.

Convierte un `DiagramaSpec` (definido en `diagram_spec.py`) en la cadena de
operadores de contenido de un stream PDF junto con su *bounding box*. Contrato
único de entrada:

    spec -> (operadores_pdf, bbox)

donde ``operadores_pdf`` es un `str` (ASCII de sintaxis PDF, con los literales
de texto ya escapados) y ``bbox`` es ``(x0, y0, x1, y1)`` en puntos.

Sistema de coordenadas
----------------------
El Mundo del diagrama está en **metros con origen abajo-izquierda y Y hacia
arriba**. El espacio de usuario del PDF **también** tiene su origen
abajo-izquierda con Y hacia arriba, así que —a diferencia de `viz.py` (SVG),
que sí voltea el eje Y— aquí **no hay flip**: solo se escala por
``ESCALA_PT_M`` (puntos por metro)::

    sx = mx * ESCALA_PT_M
    sy = my * ESCALA_PT_M

Por tanto todo punto del mundo en ``[0, ancho_m] x [0, alto_m]`` cae dentro del
``bbox`` ``(0, 0, ancho_m*ESCALA, alto_m*ESCALA)`` (invariante de la
Property 8).

Restricciones del proyecto respetadas
--------------------------------------
* Python 3.11+ y **solo biblioteca estándar**.
* Sin `assert` en producción.
* Los fragmentos se acumulan en una `list[str]` y se unen con ``''.join(...)``;
  nunca se concatena con ``+=`` dentro de un bucle.
* Los números se formatean con `f'{v:.3f}'` recortando ceros sobrantes, para
  obtener bytes estables entre corridas (determinismo).
* La paleta vive en un único módulo (`paleta.py`); aquí se consume vía
  `paleta.rgb_pdf(...)`, de modo que todo color emitido pertenece a la paleta
  (Property 12).
* Caché en memoria por el spec mismo (que es hashable) con `functools.lru_cache`
  y `clave_spec(spec)` para la caché en disco entre procesos.

Convención de fuentes: los operadores de texto referencian ``/F1``
(Helvetica) y ``/F2`` (Helvetica-Bold); el Motor_PDF declara esos recursos en
el diccionario de la página.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from hashlib import blake2b

from . import paleta
from .afm import medir_texto
from .diagram_spec import (
    BotinSpec,
    ClaseDiagrama,
    DiagramaSpec,
    Item,
    Mundo,
    Trama,
    Vista,
    ZonaBotin,
    color_base_zona,
    contorno_de_vista,
    offset_de_vista,
    puntos_trama,
    segmentos_trama,
)

__all__ = [
    "spec_a_operadores",
    "operadores_de",
    "bbox_de",
    "clave_spec",
    "ESCALA_PT_M",
    "ESCALA_BOTIN_PT",
    "botin_a_operadores",
    "bbox_botin",
]

# --------------------------------------------------------------------------- #
# Escala y medidas (en puntos del espacio de usuario del PDF)
# --------------------------------------------------------------------------- #

#: Factor de escala: puntos del PDF por cada metro del mundo.
ESCALA_PT_M: float = 8.0

#: Factor de escala del Diagrama_Botin: puntos del PDF por unidad de botín.
#: El mundo del botín mide 520 x 380 unidades, así que a 1.0 pt/u ocupa
#: 520 x 380 pt (más de media página A4, Req 3.6) sin desbordarla.
ESCALA_BOTIN_PT: float = 1.0

#: Tamaño de fuente del texto de acción de juego de cada zona (puntos).
_FS_ACCION: float = 4.2

#: Grosor de las líneas de trama de las zonas del botín (puntos).
_GROSOR_TRAMA: float = 0.35

#: Radio de los puntos de la trama de puntos (puntos).
_R_PUNTO_TRAMA: float = 0.7

#: Constante de Bézier para aproximar un cuarto de círculo.
_KAPPA: float = 0.5522847498307936

# Radios y grosores en puntos.
_R_JUGADORA: float = 4.4
_R_BALON: float = 2.0
_LADO_CONO: float = 3.6
_GROSOR_LINEA: float = 0.8
_GROSOR_TRAZO: float = 0.6
_LARGO_PUNTA: float = 3.2

# Tamaños de fuente (puntos).
_FS_NUMERO: float = 4.5
_FS_ETIQUETA: float = 4.0

# Nombres de recurso de fuente que declara el Motor_PDF.
_FUENTE_REGULAR: str = "/F1"
_FUENTE_NEGRITA: str = "/F2"


# --------------------------------------------------------------------------- #
# Utilidades de formato, color y transformación
# --------------------------------------------------------------------------- #


def _num(valor: float) -> str:
    """Formatea un número con 3 decimales, recortando ceros sobrantes."""
    texto = f"{valor:.3f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _a_pdf(mx: float, my: float) -> tuple[float, float]:
    """Escala un punto del mundo (metros) a puntos del PDF. Sin flip de Y."""
    return mx * ESCALA_PT_M, my * ESCALA_PT_M


def _op_relleno(color: str) -> str:
    """Operador de color de relleno no-trazo (`r g b rg`) desde la paleta."""
    r, g, b = paleta.rgb_pdf(color)
    return f"{_num(r)} {_num(g)} {_num(b)} rg\n"


def _op_trazo(color: str) -> str:
    """Operador de color de trazo (`r g b RG`) desde la paleta."""
    r, g, b = paleta.rgb_pdf(color)
    return f"{_num(r)} {_num(g)} {_num(b)} RG\n"


def _esc_texto(texto: str) -> str:
    """Escapa `\\`, `(` y `)` de un literal de cadena PDF (a nivel de str).

    El stream completo se codifica a WinAnsi en el Motor_PDF; aquí solo hace
    falta neutralizar los delimitadores de literal para no romper la sintaxis.
    """
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _camino_circulo(cx: float, cy: float, r: float, partes: list[str]) -> None:
    """Emite el camino (sin pintar) de un círculo con cuatro Béziers."""
    k = r * _KAPPA
    partes.append(f"{_num(cx + r)} {_num(cy)} m\n")
    partes.append(
        f"{_num(cx + r)} {_num(cy + k)} "
        f"{_num(cx + k)} {_num(cy + r)} "
        f"{_num(cx)} {_num(cy + r)} c\n"
    )
    partes.append(
        f"{_num(cx - k)} {_num(cy + r)} "
        f"{_num(cx - r)} {_num(cy + k)} "
        f"{_num(cx - r)} {_num(cy)} c\n"
    )
    partes.append(
        f"{_num(cx - r)} {_num(cy - k)} "
        f"{_num(cx - k)} {_num(cy - r)} "
        f"{_num(cx)} {_num(cy - r)} c\n"
    )
    partes.append(
        f"{_num(cx + k)} {_num(cy - r)} "
        f"{_num(cx + r)} {_num(cy - k)} "
        f"{_num(cx + r)} {_num(cy)} c\n"
    )


def _texto_centrado(
    texto: str,
    cx: float,
    cy: float,
    *,
    tamano: float,
    color: str,
    fuente: str,
    negrita: bool,
) -> str:
    """Devuelve los operadores de un texto centrado en ``(cx, cy)``.

    Centra horizontalmente midiendo el ancho con `afm.medir_texto` y baja media
    altura de mayúscula para centrar en vertical de forma aproximada.
    """
    ancho = medir_texto(texto, fuente, tamano)
    x = cx - ancho / 2.0
    y = cy - tamano * 0.35
    recurso = _FUENTE_NEGRITA if negrita else _FUENTE_REGULAR
    partes: list[str] = ["BT\n", _op_relleno(color)]
    partes.append(f"{recurso} {_num(tamano)} Tf\n")
    partes.append(f"{_num(x)} {_num(y)} Td\n")
    partes.append(f"({_esc_texto(texto)}) Tj\n")
    partes.append("ET\n")
    return "".join(partes)


# --------------------------------------------------------------------------- #
# Dibujo de cada tipo de item (cada uno aislado en su propio q/Q)
# --------------------------------------------------------------------------- #


def _dib_zona(item: Item, partes: list[str]) -> None:
    """Polígono de zona: relleno gris claro translúcido + borde rosa."""
    if len(item.puntos) < 3:
        return
    partes.append("q\n")
    partes.append(_op_relleno(paleta.GRISES_TRAMA[0]))
    partes.append(_op_trazo(paleta.ROSA))
    partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
    px, py = _a_pdf(*item.puntos[0])
    partes.append(f"{_num(px)} {_num(py)} m\n")
    for mx, my in item.puntos[1:]:
        sx, sy = _a_pdf(mx, my)
        partes.append(f"{_num(sx)} {_num(sy)} l\n")
    partes.append("h B\n")  # cierra, rellena y traza
    partes.append("Q\n")
    if item.etiqueta:
        cx = sum(p[0] for p in item.puntos) / len(item.puntos)
        cy = sum(p[1] for p in item.puntos) / len(item.puntos)
        sx, sy = _a_pdf(cx, cy)
        partes.append(
            _texto_centrado(
                item.etiqueta,
                sx,
                sy,
                tamano=_FS_ETIQUETA,
                color=paleta.NEGRO,
                fuente="Helvetica",
                negrita=False,
            )
        )


def _dib_cono(item: Item, partes: list[str]) -> None:
    """Triángulo pequeño (cone/boot)."""
    sx, sy = _a_pdf(item.x, item.y)
    media = _LADO_CONO / 2.0
    partes.append("q\n")
    partes.append(_op_relleno(paleta.NEGRO))
    partes.append(f"{_num(sx)} {_num(sy + media)} m\n")
    partes.append(f"{_num(sx - media)} {_num(sy - media)} l\n")
    partes.append(f"{_num(sx + media)} {_num(sy - media)} l\n")
    partes.append("h f\n")
    partes.append("Q\n")


def _dib_flecha(item: Item, partes: list[str]) -> None:
    """Segmento con estilo según el tipo (run/pass/dribble/shot/seg)."""
    if item.x2 is None or item.y2 is None:
        return
    x1, y1 = _a_pdf(item.x, item.y)
    x2, y2 = _a_pdf(item.x2, item.y2)

    tipo = item.tipo
    if tipo == "shot":
        color = paleta.ROSA
        grosor = _GROSOR_LINEA * 2.0
        guion = ""
    elif tipo == "run":
        color = paleta.NEGRO
        grosor = _GROSOR_LINEA
        guion = "[2 1.5] 0 d\n"
    else:  # pass / dribble / seg
        color = paleta.NEGRO
        grosor = _GROSOR_LINEA
        guion = ""

    partes.append("q\n")
    partes.append(_op_trazo(color))
    partes.append(f"{_num(grosor)} w\n")
    if guion:
        partes.append(guion)
    partes.append(f"{_num(x1)} {_num(y1)} m\n")
    partes.append(f"{_num(x2)} {_num(y2)} l\n")
    partes.append("S\n")
    partes.append("Q\n")
    _dib_punta(x1, y1, x2, y2, color, partes)


def _dib_punta(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    partes: list[str],
) -> None:
    """Punta de flecha rellena en el extremo ``(x2, y2)``."""
    dx = x2 - x1
    dy = y2 - y1
    largo = (dx * dx + dy * dy) ** 0.5
    if largo == 0.0:
        return
    ux = dx / largo
    uy = dy / largo
    # Base de la punta, retrocediendo desde el extremo.
    bx = x2 - ux * _LARGO_PUNTA
    by = y2 - uy * _LARGO_PUNTA
    # Vector perpendicular unitario.
    px = -uy
    py = ux
    ala = _LARGO_PUNTA * 0.5
    partes.append("q\n")
    partes.append(_op_relleno(color))
    partes.append(f"{_num(x2)} {_num(y2)} m\n")
    partes.append(f"{_num(bx + px * ala)} {_num(by + py * ala)} l\n")
    partes.append(f"{_num(bx - px * ala)} {_num(by - py * ala)} l\n")
    partes.append("h f\n")
    partes.append("Q\n")


def _dib_jugadora(item: Item, partes: list[str]) -> None:
    """Círculo de jugadora (player/rival/gk) con número opcional."""
    sx, sy = _a_pdf(item.x, item.y)
    if item.tipo == "player":
        relleno = paleta.ROSA
        contorno = paleta.ROSA
        color_texto = paleta.BLANCO
    elif item.tipo == "gk":
        relleno = paleta.BLANCO
        contorno = paleta.ROSA
        color_texto = paleta.ROSA
    else:  # rival
        relleno = paleta.BLANCO
        contorno = paleta.NEGRO
        color_texto = paleta.NEGRO

    partes.append("q\n")
    partes.append(_op_relleno(relleno))
    partes.append(_op_trazo(contorno))
    partes.append(f"{_num(_GROSOR_LINEA)} w\n")
    _camino_circulo(sx, sy, _R_JUGADORA, partes)
    partes.append("B\n")
    partes.append("Q\n")

    texto = ""
    if item.numero is not None:
        texto = str(item.numero)
    elif item.etiqueta:
        texto = item.etiqueta
    if texto:
        partes.append(
            _texto_centrado(
                texto,
                sx,
                sy,
                tamano=_FS_NUMERO,
                color=color_texto,
                fuente="Helvetica-Bold",
                negrita=True,
            )
        )


def _dib_balon(item: Item, partes: list[str]) -> None:
    """Círculo pequeño de balón (ball)."""
    sx, sy = _a_pdf(item.x, item.y)
    partes.append("q\n")
    partes.append(_op_relleno(paleta.BLANCO))
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
    _camino_circulo(sx, sy, _R_BALON, partes)
    partes.append("B\n")
    partes.append("Q\n")


def _dib_texto(item: Item, partes: list[str]) -> None:
    """Texto suelto (txt), anclado por su esquina inferior izquierda."""
    if not item.etiqueta:
        return
    sx, sy = _a_pdf(item.x, item.y)
    partes.append("BT\n")
    partes.append(_op_relleno(paleta.NEGRO))
    partes.append(f"{_FUENTE_REGULAR} {_num(_FS_ETIQUETA)} Tf\n")
    partes.append(f"{_num(sx)} {_num(sy)} Td\n")
    partes.append(f"({_esc_texto(item.etiqueta)}) Tj\n")
    partes.append("ET\n")


def _dib_marca(item: Item, partes: list[str]) -> None:
    """Marca de corrección (mark): círculo rojo (única excepción de paleta)."""
    sx, sy = _a_pdf(item.x, item.y)
    partes.append("q\n")
    partes.append(_op_trazo(paleta.ROJO))
    partes.append(f"{_num(_GROSOR_LINEA * 1.6)} w\n")
    _camino_circulo(sx, sy, _R_JUGADORA, partes)
    partes.append("S\n")
    partes.append("Q\n")


def _dib_target(item: Item, partes: list[str]) -> None:
    """Objetivo/diana (target): dos círculos concéntricos."""
    sx, sy = _a_pdf(item.x, item.y)
    partes.append("q\n")
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
    _camino_circulo(sx, sy, _R_BALON * 1.8, partes)
    partes.append("S\n")
    partes.append(_op_relleno(paleta.NEGRO))
    _camino_circulo(sx, sy, _R_BALON * 0.7, partes)
    partes.append("f\n")
    partes.append("Q\n")


# --------------------------------------------------------------------------- #
# Ensamblado de los operadores
# --------------------------------------------------------------------------- #

# Orden de dibujo por capas: zonas al fondo, jugadoras/balón al frente.
_ORDEN_CAPAS: tuple[tuple[str, ...], ...] = (
    ("zone", "poly"),
    ("cone", "boot", "target"),
    ("run", "pass", "dribble", "shot", "seg"),
    ("player", "rival", "gk"),
    ("ball",),
    ("txt", "mark"),
)


def _dibujar_item(item: Item, partes: list[str]) -> None:
    """Despacha el dibujo de un item según su tipo."""
    tipo = item.tipo
    if tipo in ("zone", "poly"):
        _dib_zona(item, partes)
    elif tipo in ("cone", "boot"):
        _dib_cono(item, partes)
    elif tipo in ("run", "pass", "dribble", "shot", "seg"):
        _dib_flecha(item, partes)
    elif tipo in ("player", "rival", "gk"):
        _dib_jugadora(item, partes)
    elif tipo == "ball":
        _dib_balon(item, partes)
    elif tipo == "txt":
        _dib_texto(item, partes)
    elif tipo == "mark":
        _dib_marca(item, partes)
    elif tipo == "target":
        _dib_target(item, partes)


def bbox_de(spec: DiagramaSpec) -> tuple[float, float, float, float]:
    """Devuelve el bbox ``(x0, y0, x1, y1)`` del `spec` en puntos del PDF."""
    mundo: Mundo = spec.mundo
    return (0.0, 0.0, mundo.ancho_m * ESCALA_PT_M, mundo.alto_m * ESCALA_PT_M)


@lru_cache(maxsize=4096)
def spec_a_operadores(
    spec: DiagramaSpec,
) -> tuple[str, tuple[float, float, float, float]]:
    """Renderiza `spec` a operadores PDF. Devuelve ``(operadores_pdf, bbox)``.

    Punto de entrada único del renderizador PDF. Acepta tanto un
    `DiagramaSpec` de cancha como un `BotinSpec` (Diagrama_Botin), despachando
    al renderizador que corresponda por el tipo del spec. El resultado se
    cachea en memoria por el spec (hashable), lo que evita recalcular diagramas
    repetidos dentro de un mismo proceso. Para la caché en disco entre
    procesos, usar `clave_spec(spec)`.
    """
    if isinstance(spec, BotinSpec):
        return botin_a_operadores(spec)

    bbox = bbox_de(spec)

    partes: list[str] = []
    # Fondo del campo con la paleta (dentro del bbox).
    partes.append("q\n")
    partes.append(_op_relleno(paleta.FONDO))
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_LINEA)} w\n")
    partes.append(
        f"0 0 {_num(bbox[2])} {_num(bbox[3])} re\n"
    )
    partes.append("B\n")
    partes.append("Q\n")

    # Dibujo por capas para un apilado visual consistente.
    for capa in _ORDEN_CAPAS:
        for item in spec.items:
            if item.tipo in capa:
                _dibujar_item(item, partes)

    return "".join(partes), bbox


def operadores_de(spec: DiagramaSpec) -> str:
    """Atajo que devuelve solo la cadena de operadores PDF de `spec`."""
    operadores, _ = spec_a_operadores(spec)
    return operadores


# --------------------------------------------------------------------------- #
# Diagrama_Botin: siluetas Bézier + 7 zonas con gris base y trama
# --------------------------------------------------------------------------- #
#
# El botín se dibuja en su marco local (unidades de botín, no metros) sin flip
# de Y, igual que la cancha en el espacio de usuario del PDF. Cada vista se
# desplaza por `offset_de_vista`. El orden de pintado es: fondo -> por cada
# zona (relleno gris, trama recortada al polígono, borde, texto de acción) ->
# contornos de las siluetas y sus adornos por encima.


def bbox_botin(spec: BotinSpec) -> tuple[float, float, float, float]:
    """Devuelve el bbox ``(x0, y0, x1, y1)`` del Diagrama_Botin en puntos."""
    return (
        0.0,
        0.0,
        spec.mundo.ancho_m * ESCALA_BOTIN_PT,
        spec.mundo.alto_m * ESCALA_BOTIN_PT,
    )


def _botin_a_pdf(x: float, y: float, dx: float, dy: float) -> tuple[float, float]:
    """Transforma un punto del marco local de una vista a puntos del PDF."""
    return (x + dx) * ESCALA_BOTIN_PT, (y + dy) * ESCALA_BOTIN_PT


def _recortar_a_caja(
    segmento: tuple[tuple[float, float], tuple[float, float]],
    caja: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Recorta un segmento contra un rectángulo (Liang-Barsky).

    Devuelve el segmento recortado o ``None`` si queda por completo fuera.
    Mantiene los extremos dentro de la caja, de modo que ninguna coordenada
    emitida se sale del bbox del diagrama (invariante de la Property 8), aunque
    el recorte fino a la forma de la zona lo haga después el operador `W n`.
    """
    (x0, y0), (x1, y1) = segmento
    min_x, min_y, max_x, max_y = caja
    dx = x1 - x0
    dy = y1 - y0
    p = (-dx, dx, -dy, dy)
    q = (x0 - min_x, max_x - x0, y0 - min_y, max_y - y0)
    u1 = 0.0
    u2 = 1.0
    for pi, qi in zip(p, q):
        if pi == 0.0:
            if qi < 0.0:
                return None
            continue
        t = qi / pi
        if pi < 0.0:
            if t > u2:
                return None
            if t > u1:
                u1 = t
        else:
            if t < u1:
                return None
            if t < u2:
                u2 = t
    nx0 = x0 + u1 * dx
    ny0 = y0 + u1 * dy
    nx1 = x0 + u2 * dx
    ny1 = y0 + u2 * dy
    return ((nx0, ny0), (nx1, ny1))


def _camino_contorno_pdf(
    contorno: tuple[tuple[str, tuple[float, ...]], ...],
    dx: float,
    dy: float,
    partes: list[str],
) -> None:
    """Emite el camino (M/C/L/Z) de un contorno Bézier con `m`/`c`/`l`/`h`."""
    for op, args in contorno:
        if op == "M":
            x, y = _botin_a_pdf(args[0], args[1], dx, dy)
            partes.append(f"{_num(x)} {_num(y)} m\n")
        elif op == "L":
            x, y = _botin_a_pdf(args[0], args[1], dx, dy)
            partes.append(f"{_num(x)} {_num(y)} l\n")
        elif op == "C":
            x1, y1 = _botin_a_pdf(args[0], args[1], dx, dy)
            x2, y2 = _botin_a_pdf(args[2], args[3], dx, dy)
            x3, y3 = _botin_a_pdf(args[4], args[5], dx, dy)
            partes.append(
                f"{_num(x1)} {_num(y1)} {_num(x2)} {_num(y2)} "
                f"{_num(x3)} {_num(y3)} c\n"
            )
        elif op == "Z":
            partes.append("h\n")


def _camino_poligono_pdf(
    poligono: tuple[tuple[float, float], ...],
    dx: float,
    dy: float,
    partes: list[str],
) -> None:
    """Emite el camino cerrado de un polígono con `m`/`l`/`h`."""
    if len(poligono) < 3:
        return
    px, py = _botin_a_pdf(poligono[0][0], poligono[0][1], dx, dy)
    partes.append(f"{_num(px)} {_num(py)} m\n")
    for x, y in poligono[1:]:
        sx, sy = _botin_a_pdf(x, y, dx, dy)
        partes.append(f"{_num(sx)} {_num(sy)} l\n")
    partes.append("h\n")


def _dib_trama_botin(
    zona: ZonaBotin,
    dx: float,
    dy: float,
    caja: tuple[float, float, float, float],
    partes: list[str],
) -> None:
    """Dibuja la trama de una zona (ya recortada al polígono por el `W n`).

    Los segmentos de línea se recortan además al bbox de la zona para que
    ninguna coordenada emitida se salga del diagrama. `SOLIDO` no añade trama
    (basta el gris base).
    """
    if zona.trama is Trama.SOLIDO:
        return
    if zona.trama is Trama.PUNTOS:
        puntos = puntos_trama(zona)
        if not puntos:
            return
        partes.append(_op_relleno(paleta.NEGRO))
        for x, y in puntos:
            cx, cy = _botin_a_pdf(x, y, dx, dy)
            _camino_circulo(cx, cy, _R_PUNTO_TRAMA, partes)
            partes.append("f\n")
        return
    # Tramas de líneas (45, 135, 90) y cuadrícula (0 + 90).
    segmentos = segmentos_trama(zona)
    if not segmentos:
        return
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_TRAMA)} w\n")
    hubo = False
    for segmento in segmentos:
        recortado = _recortar_a_caja(segmento, (0.0, 0.0, caja[2], caja[3]))
        if recortado is None:
            continue
        (ax, ay), (bx, by) = recortado
        pax, pay = _botin_a_pdf(ax, ay, dx, dy)
        pbx, pby = _botin_a_pdf(bx, by, dx, dy)
        partes.append(f"{_num(pax)} {_num(pay)} m\n")
        partes.append(f"{_num(pbx)} {_num(pby)} l\n")
        hubo = True
    if hubo:
        partes.append("S\n")


def _dib_zona_botin(
    zona: ZonaBotin,
    caja: tuple[float, float, float, float],
    partes: list[str],
) -> None:
    """Dibuja una zona: relleno gris + trama recortada + borde + acción."""
    dx, dy = offset_de_vista(zona.vista)

    # 1. Relleno gris base (color de la paleta más cercano al nivel de gris).
    partes.append("q\n")
    partes.append(_op_relleno(color_base_zona(zona.gris)))
    _camino_poligono_pdf(zona.poligono, dx, dy, partes)
    partes.append("f\n")
    partes.append("Q\n")

    # 2. Trama recortada al polígono con `W n`.
    partes.append("q\n")
    _camino_poligono_pdf(zona.poligono, dx, dy, partes)
    partes.append("W n\n")
    _dib_trama_botin(zona, dx, dy, caja, partes)
    partes.append("Q\n")

    # 3. Borde de la zona (negro fino, dentro de la paleta).
    partes.append("q\n")
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
    _camino_poligono_pdf(zona.poligono, dx, dy, partes)
    partes.append("S\n")
    partes.append("Q\n")

    # 4. Texto de la acción de juego junto a la zona (Req 3.7). Se ancla en el
    #    centroide del polígono; la colocación externa con líneas guía es la
    #    tarea 3.6.
    if zona.accion:
        cx = sum(p[0] for p in zona.poligono) / len(zona.poligono)
        cy = sum(p[1] for p in zona.poligono) / len(zona.poligono)
        sx, sy = _botin_a_pdf(cx, cy, dx, dy)
        partes.append(
            _texto_centrado(
                zona.accion,
                sx,
                sy,
                tamano=_FS_ACCION,
                color=paleta.NEGRO,
                fuente="Helvetica",
                negrita=False,
            )
        )


@lru_cache(maxsize=1024)
def botin_a_operadores(
    spec: BotinSpec,
) -> tuple[str, tuple[float, float, float, float]]:
    """Renderiza un `BotinSpec` a operadores PDF. Devuelve ``(ops, bbox)``.

    Punto de entrada del Diagrama_Botin para el Motor_PDF. Dibuja las dos
    siluetas (planta y perfil) y las siete zonas con gris base + trama, de modo
    que se distingan también en escala de grises (Req 3.9), conservando la
    paleta rosa/negro (Req 3.8). El resultado se cachea por el spec.
    """
    bbox = bbox_botin(spec)

    partes: list[str] = []

    # Fondo del bloque con la paleta.
    partes.append("q\n")
    partes.append(_op_relleno(paleta.FONDO))
    partes.append(f"0 0 {_num(bbox[2])} {_num(bbox[3])} re\n")
    partes.append("f\n")
    partes.append("Q\n")

    # Zonas (relleno + trama + borde + acción).
    for zona in spec.zonas:
        _dib_zona_botin(zona, bbox, partes)

    # Contornos de las siluetas y adornos por encima de las zonas.
    contornos = (
        (Vista.PLANTA, spec.contorno_planta),
        (Vista.PERFIL, spec.contorno_perfil),
    )
    for vista, contorno in contornos:
        dx, dy = offset_de_vista(vista)
        partes.append("q\n")
        partes.append(_op_trazo(paleta.NEGRO))
        partes.append(f"{_num(_GROSOR_LINEA)} w\n")
        _camino_contorno_pdf(contorno, dx, dy, partes)
        partes.append("S\n")
        partes.append("Q\n")

    # Costura decorativa de la planta (línea de cordones).
    dx, dy = offset_de_vista(Vista.PLANTA)
    partes.append("q\n")
    partes.append(_op_trazo(paleta.NEGRO))
    partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
    _camino_contorno_pdf(spec.costura_planta, dx, dy, partes)
    partes.append("S\n")
    partes.append("Q\n")

    # Banda de suela del perfil (polígono cerrado, negro fino).
    dx, dy = offset_de_vista(Vista.PERFIL)
    if len(spec.suela_perfil) >= 3:
        partes.append("q\n")
        partes.append(_op_trazo(paleta.NEGRO))
        partes.append(f"{_num(_GROSOR_TRAZO)} w\n")
        _camino_poligono_pdf(spec.suela_perfil, dx, dy, partes)
        partes.append("S\n")
        partes.append("Q\n")

    return "".join(partes), bbox


def clave_spec(spec: DiagramaSpec) -> str:
    """Clave estable entre procesos para la caché en disco de un diagrama.

    Serializa el spec de forma canónica (`sort_keys=True`, separadores
    compactos) y devuelve un digest `blake2b` de 16 bytes en hexadecimal. Al
    ordenar las claves, la clave es independiente del orden de declaración de
    los campos del dataclass.
    """
    crudo = json.dumps(
        asdict(spec),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return blake2b(crudo.encode("utf-8"), digest_size=16).hexdigest()
