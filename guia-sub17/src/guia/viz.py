"""Renderizador SVG del Motor_Diagramas (Target_Web, Ola A).

Convierte un `DiagramaSpec` de cancha en un SVG *inline*, responsive y
accesible. El SVG:

* usa `viewBox` (en unidades del mundo escaladas por `ESCALA_PX_M`) y **no**
  lleva atributos `width`/`height` absolutos, para que fluya al 100 % del
  contenedor (`style="width:100%;height:auto"`);
* incluye `role="img"`, un `<title>` y un `<desc>` para accesibilidad;
* aplica el **flip de coordenadas**: el Mundo tiene origen abajo-izquierda con
  Y hacia arriba, y el SVG tiene Y hacia abajo. La transformación de un punto
  del mundo ``(mx, my)`` a coordenadas SVG es::

      sx = mx * ESCALA_PX_M
      sy = (alto_m - my) * ESCALA_PX_M

  Así todo punto del mundo dentro de ``[0, ancho_m] x [0, alto_m]`` cae dentro
  del `viewBox` ``0 0 (ancho_m*ESCALA) (alto_m*ESCALA)`` (invariante de la
  Propiedad 8).

Restricciones del proyecto respetadas:

* Solo biblioteca estándar (`html.escape`).
* Los fragmentos se acumulan en una `list[str]` y se unen con ``''.join(...)``;
  nunca se concatena dentro de un bucle.
* Los números se formatean con `f'{v:.3f}'` (recortando ceros sobrantes) para
  bytes estables entre corridas.
* Paleta y escala centralizadas como constantes de módulo.
"""

from __future__ import annotations

import html
from functools import lru_cache

from . import paleta
from .diagram_spec import (
    BotinSpec,
    DiagramaSpec,
    Item,
    Mundo,
    Trama,
    Vista,
    ZonaBotin,
    color_base_zona,
    offset_de_vista,
    puntos_trama,
    segmentos_trama,
)

__all__ = [
    "spec_a_svg",
    "render_svg",
    "ESCALA_PX_M",
    "ESCALA_BOTIN_PX",
    "PALETA",
    "botin_a_svg",
]

# --------------------------------------------------------------------------- #
# Escala y paleta (la paleta vive en el módulo compartido `paleta.py`)
# --------------------------------------------------------------------------- #

#: Factor de escala: píxeles del viewBox por cada metro del mundo.
ESCALA_PX_M: float = 20.0

#: Factor de escala del Diagrama_Botin: píxeles del viewBox por unidad de
#: botín. El viewBox es responsive (sin width/height), así que basta 1:1.
ESCALA_BOTIN_PX: float = 1.0

#: Paleta exacta del proyecto, re-exportada desde el módulo único `paleta.py`.
#: El rojo es solo para marcas de corrección.
PALETA: dict[str, str] = paleta.PALETA

#: Colores derivados para elementos secundarios (dentro de la paleta base).
_COLOR_GK: str = PALETA["rosa"]
_COLOR_CONO: str = PALETA["negro"]
_COLOR_LINEA: str = PALETA["negro"]

# Radios y grosores en unidades del viewBox (píxeles escalados).
_R_JUGADORA: float = 11.0
_R_BALON: float = 5.0
_LADO_CONO: float = 9.0


# --------------------------------------------------------------------------- #
# Utilidades de formato y transformación
# --------------------------------------------------------------------------- #


def _num(valor: float) -> str:
    """Formatea un número con 3 decimales, recortando ceros sobrantes."""
    texto = f"{valor:.3f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _a_svg(mx: float, my: float, mundo: Mundo) -> tuple[float, float]:
    """Aplica el flip mundo->SVG y la escala. Devuelve ``(sx, sy)``."""
    sx = mx * ESCALA_PX_M
    sy = (mundo.alto_m - my) * ESCALA_PX_M
    return sx, sy


def _esc(texto: str) -> str:
    """Escapa texto para insertarlo con seguridad en el SVG."""
    return html.escape(texto, quote=True)


# --------------------------------------------------------------------------- #
# Dibujo de cada tipo de item
# --------------------------------------------------------------------------- #


def _dib_zona(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Polígono translúcido (zone/poly)."""
    if len(item.puntos) < 3:
        return
    coords: list[str] = []
    for mx, my in item.puntos:
        sx, sy = _a_svg(mx, my, mundo)
        coords.append(f"{_num(sx)},{_num(sy)}")
    partes.append(
        f'<polygon points="{" ".join(coords)}" '
        f'fill="{PALETA["rosa"]}" fill-opacity="0.12" '
        f'stroke="{PALETA["rosa"]}" stroke-width="1.5" />'
    )
    if item.etiqueta:
        # Etiqueta en el centroide aproximado del polígono.
        cx = sum(p[0] for p in item.puntos) / len(item.puntos)
        cy = sum(p[1] for p in item.puntos) / len(item.puntos)
        sx, sy = _a_svg(cx, cy, mundo)
        partes.append(
            f'<text x="{_num(sx)}" y="{_num(sy)}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-size="10" fill="{PALETA["negro"]}">{_esc(item.etiqueta)}</text>'
        )


def _dib_cono(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Triángulo pequeño (cone)."""
    sx, sy = _a_svg(item.x, item.y, mundo)
    media = _LADO_CONO / 2.0
    p1 = f"{_num(sx)},{_num(sy - media)}"
    p2 = f"{_num(sx - media)},{_num(sy + media)}"
    p3 = f"{_num(sx + media)},{_num(sy + media)}"
    partes.append(
        f'<polygon points="{p1} {p2} {p3}" '
        f'fill="{_COLOR_CONO}" stroke="{_COLOR_CONO}" stroke-width="1" />'
    )


def _dib_flecha(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Segmento con estilo según el tipo (run/pass/dribble/shot/seg)."""
    if item.x2 is None or item.y2 is None:
        return
    x1, y1 = _a_svg(item.x, item.y, mundo)
    x2, y2 = _a_svg(item.x2, item.y2, mundo)

    tipo = item.tipo
    if tipo == "run":
        # Carrera: línea discontinua, sin punta rellena.
        partes.append(
            f'<line x1="{_num(x1)}" y1="{_num(y1)}" '
            f'x2="{_num(x2)}" y2="{_num(y2)}" '
            f'stroke="{_COLOR_LINEA}" stroke-width="2" '
            f'stroke-dasharray="6 4" marker-end="url(#punta)" />'
        )
    elif tipo == "dribble":
        # Regate: trazo ondulado aproximado con una curva cuadrática por tramos.
        partes.append(_ruta_ondulada(x1, y1, x2, y2))
    elif tipo == "shot":
        # Tiro: línea gruesa con punta.
        partes.append(
            f'<line x1="{_num(x1)}" y1="{_num(y1)}" '
            f'x2="{_num(x2)}" y2="{_num(y2)}" '
            f'stroke="{PALETA["rosa"]}" stroke-width="4" '
            f'marker-end="url(#punta)" />'
        )
    else:
        # pass / seg: línea sólida con punta.
        partes.append(
            f'<line x1="{_num(x1)}" y1="{_num(y1)}" '
            f'x2="{_num(x2)}" y2="{_num(y2)}" '
            f'stroke="{_COLOR_LINEA}" stroke-width="2" '
            f'marker-end="url(#punta)" />'
        )


def _ruta_ondulada(x1: float, y1: float, x2: float, y2: float) -> str:
    """Genera un `path` ondulado entre dos puntos (para dribble)."""
    dx = x2 - x1
    dy = y2 - y1
    largo = (dx * dx + dy * dy) ** 0.5
    if largo == 0.0:
        return (
            f'<line x1="{_num(x1)}" y1="{_num(y1)}" '
            f'x2="{_num(x2)}" y2="{_num(y2)}" '
            f'stroke="{_COLOR_LINEA}" stroke-width="2" '
            f'marker-end="url(#punta)" />'
        )
    # Vector unitario perpendicular para desplazar los puntos de control.
    nx = -dy / largo
    ny = dx / largo
    tramos = max(2, int(largo // 14))
    amplitud = 4.0
    segmentos: list[str] = [f"M {_num(x1)} {_num(y1)}"]
    for i in range(1, tramos + 1):
        t = i / tramos
        px = x1 + dx * t
        py = y1 + dy * t
        signo = 1.0 if i % 2 == 1 else -1.0
        # Punto de control a mitad del tramo, desplazado en perpendicular.
        t_ctrl = (i - 0.5) / tramos
        cxp = x1 + dx * t_ctrl + nx * amplitud * signo
        cyp = y1 + dy * t_ctrl + ny * amplitud * signo
        segmentos.append(
            f"Q {_num(cxp)} {_num(cyp)} {_num(px)} {_num(py)}"
        )
    ruta = " ".join(segmentos)
    return (
        f'<path d="{ruta}" fill="none" '
        f'stroke="{_COLOR_LINEA}" stroke-width="2" '
        f'marker-end="url(#punta)" />'
    )


def _dib_jugadora(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Círculo de jugadora (player/rival/gk) con número opcional."""
    sx, sy = _a_svg(item.x, item.y, mundo)
    if item.tipo == "player":
        relleno = PALETA["rosa"]
        contorno = PALETA["rosa"]
        color_texto = PALETA["blanco"]
    elif item.tipo == "gk":
        relleno = PALETA["blanco"]
        contorno = _COLOR_GK
        color_texto = _COLOR_GK
    else:  # rival
        relleno = PALETA["blanco"]
        contorno = PALETA["negro"]
        color_texto = PALETA["negro"]

    partes.append(
        f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="{_num(_R_JUGADORA)}" '
        f'fill="{relleno}" stroke="{contorno}" stroke-width="2" />'
    )
    texto = ""
    if item.numero is not None:
        texto = str(item.numero)
    elif item.etiqueta:
        texto = item.etiqueta
    if texto:
        partes.append(
            f'<text x="{_num(sx)}" y="{_num(sy)}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="11" '
            f'font-weight="bold" fill="{color_texto}">{_esc(texto)}</text>'
        )


def _dib_balon(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Círculo pequeño de balón (ball)."""
    sx, sy = _a_svg(item.x, item.y, mundo)
    partes.append(
        f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="{_num(_R_BALON)}" '
        f'fill="{PALETA["blanco"]}" stroke="{PALETA["negro"]}" '
        f'stroke-width="1.5" />'
    )


def _dib_texto(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Texto suelto (txt)."""
    if not item.etiqueta:
        return
    sx, sy = _a_svg(item.x, item.y, mundo)
    partes.append(
        f'<text x="{_num(sx)}" y="{_num(sy)}" font-size="10" '
        f'fill="{PALETA["negro"]}">{_esc(item.etiqueta)}</text>'
    )


def _dib_marca(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Marca de corrección (mark): círculo rojo (única excepción de paleta)."""
    sx, sy = _a_svg(item.x, item.y, mundo)
    partes.append(
        f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="{_num(_R_JUGADORA)}" '
        f'fill="none" stroke="{PALETA["rojo"]}" stroke-width="2" />'
    )


def _dib_target(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Objetivo/diana (target): dos círculos concéntricos."""
    sx, sy = _a_svg(item.x, item.y, mundo)
    partes.append(
        f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="{_num(_R_BALON * 1.8)}" '
        f'fill="none" stroke="{PALETA["negro"]}" stroke-width="1.5" />'
    )
    partes.append(
        f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="{_num(_R_BALON * 0.7)}" '
        f'fill="{PALETA["negro"]}" />'
    )


# --------------------------------------------------------------------------- #
# Ensamblado del SVG
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


def _dibujar_item(item: Item, mundo: Mundo, partes: list[str]) -> None:
    """Despacha el dibujo de un item según su tipo."""
    tipo = item.tipo
    if tipo in ("zone", "poly"):
        _dib_zona(item, mundo, partes)
    elif tipo in ("cone", "boot"):
        _dib_cono(item, mundo, partes)
    elif tipo in ("run", "pass", "dribble", "shot", "seg"):
        _dib_flecha(item, mundo, partes)
    elif tipo in ("player", "rival", "gk"):
        _dib_jugadora(item, mundo, partes)
    elif tipo == "ball":
        _dib_balon(item, mundo, partes)
    elif tipo == "txt":
        _dib_texto(item, mundo, partes)
    elif tipo == "mark":
        _dib_marca(item, mundo, partes)
    elif tipo == "target":
        _dib_target(item, mundo, partes)


@lru_cache(maxsize=4096)
def spec_a_svg(spec: DiagramaSpec) -> tuple[str, str]:
    """Renderiza `spec` a SVG. Devuelve ``(svg, view_box)``.

    El `view_box` se calcula como ``0 0 (ancho_m*ESCALA) (alto_m*ESCALA)`` y el
    SVG resultante es responsive (sin `width`/`height` absolutos), accesible
    (`role="img"`, `<title>`, `<desc>`) y determinista (números formateados).

    Acepta tanto un `DiagramaSpec` de cancha como un `BotinSpec`
    (Diagrama_Botin), despachando por el tipo del spec. El resultado se cachea
    en memoria por el spec (que es hashable), de modo que specs repetidos no se
    vuelven a renderizar dentro del mismo proceso.
    """
    if isinstance(spec, BotinSpec):
        return botin_a_svg(spec)

    mundo = spec.mundo
    ancho = mundo.ancho_m * ESCALA_PX_M
    alto = mundo.alto_m * ESCALA_PX_M
    view_box = f"0 0 {_num(ancho)} {_num(alto)}"

    titulo = spec.titulo or "Diagrama de cancha"
    desc = f"Diagrama {spec.clase.value} con {len(spec.items)} elementos"

    partes: list[str] = []
    partes.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'style="width:100%;height:auto" role="img" '
        f'preserveAspectRatio="xMidYMid meet">'
    )
    partes.append(f"<title>{_esc(titulo)}</title>")
    partes.append(f"<desc>{_esc(desc)}</desc>")

    # Definición del marcador de punta de flecha.
    partes.append(
        '<defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{PALETA["negro"]}" />'
        "</marker></defs>"
    )

    # Fondo del campo con la paleta.
    partes.append(
        f'<rect x="0" y="0" width="{_num(ancho)}" height="{_num(alto)}" '
        f'fill="{PALETA["fondo"]}" stroke="{PALETA["negro"]}" '
        f'stroke-width="1.5" />'
    )

    # Dibujo por capas para un apilado visual consistente.
    for capa in _ORDEN_CAPAS:
        for item in spec.items:
            if item.tipo in capa:
                _dibujar_item(item, mundo, partes)

    partes.append("</svg>")
    return "".join(partes), view_box


def render_svg(spec: DiagramaSpec) -> str:
    """Atajo que devuelve solo la cadena SVG de `spec`."""
    svg, _ = spec_a_svg(spec)
    return svg


# --------------------------------------------------------------------------- #
# Diagrama_Botin: siluetas Bézier + 7 zonas con gris base y trama (SVG)
# --------------------------------------------------------------------------- #
#
# El botín se dibuja en su marco local (unidades de botín). Se aplica el flip
# de Y del SVG (origen arriba-izquierda) y el desplazamiento por vista de
# `offset_de_vista`. Cada zona se rellena con su gris base y su trama recortada
# con un `<clipPath>` al polígono de la zona.


def _botin_a_svg(
    x: float, y: float, dx: float, dy: float, alto: float
) -> tuple[float, float]:
    """Transforma un punto local de una vista a coordenadas SVG (con flip)."""
    sx = (x + dx) * ESCALA_BOTIN_PX
    sy = (alto - (y + dy)) * ESCALA_BOTIN_PX
    return sx, sy


def _recortar_a_caja_svg(
    segmento: tuple[tuple[float, float], tuple[float, float]],
    caja: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Recorta un segmento contra un rectángulo (Liang-Barsky) en local.

    Igual que en `draw.py`: mantiene las coordenadas dentro del bbox de la
    zona para que nada se salga del viewBox (Property 8); el recorte fino a la
    forma lo hace el `<clipPath>`.
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
    return (
        (x0 + u1 * dx, y0 + u1 * dy),
        (x0 + u2 * dx, y0 + u2 * dy),
    )


def _contorno_svg_d(
    contorno: tuple[tuple[str, tuple[float, ...]], ...],
    dx: float,
    dy: float,
    alto: float,
) -> str:
    """Convierte un contorno (M/C/L/Z) en el atributo `d` de un `<path>`."""
    partes: list[str] = []
    for op, args in contorno:
        if op == "M":
            x, y = _botin_a_svg(args[0], args[1], dx, dy, alto)
            partes.append(f"M {_num(x)} {_num(y)}")
        elif op == "L":
            x, y = _botin_a_svg(args[0], args[1], dx, dy, alto)
            partes.append(f"L {_num(x)} {_num(y)}")
        elif op == "C":
            x1, y1 = _botin_a_svg(args[0], args[1], dx, dy, alto)
            x2, y2 = _botin_a_svg(args[2], args[3], dx, dy, alto)
            x3, y3 = _botin_a_svg(args[4], args[5], dx, dy, alto)
            partes.append(
                f"C {_num(x1)} {_num(y1)} {_num(x2)} {_num(y2)} "
                f"{_num(x3)} {_num(y3)}"
            )
        elif op == "Z":
            partes.append("Z")
    return " ".join(partes)


def _poligono_svg_puntos(
    poligono: tuple[tuple[float, float], ...],
    dx: float,
    dy: float,
    alto: float,
) -> str:
    """Devuelve el atributo `points` de un `<polygon>` de la zona."""
    coords: list[str] = []
    for x, y in poligono:
        sx, sy = _botin_a_svg(x, y, dx, dy, alto)
        coords.append(f"{_num(sx)},{_num(sy)}")
    return " ".join(coords)


def _dib_trama_botin_svg(
    zona: ZonaBotin,
    dx: float,
    dy: float,
    alto: float,
    caja: tuple[float, float, float, float],
    clip_id: str,
    partes: list[str],
) -> None:
    """Dibuja la trama de una zona recortada con su `<clipPath>`."""
    if zona.trama is Trama.SOLIDO:
        return
    partes.append(f'<g clip-path="url(#{clip_id})">')
    if zona.trama is Trama.PUNTOS:
        for x, y in puntos_trama(zona):
            sx, sy = _botin_a_svg(x, y, dx, dy, alto)
            partes.append(
                f'<circle cx="{_num(sx)}" cy="{_num(sy)}" r="0.9" '
                f'fill="{PALETA["negro"]}" />'
            )
    else:
        for segmento in segmentos_trama(zona):
            recortado = _recortar_a_caja_svg(
                segmento, (0.0, 0.0, caja[2], caja[3])
            )
            if recortado is None:
                continue
            (ax, ay), (bx, by) = recortado
            sax, say = _botin_a_svg(ax, ay, dx, dy, alto)
            sbx, sby = _botin_a_svg(bx, by, dx, dy, alto)
            partes.append(
                f'<line x1="{_num(sax)}" y1="{_num(say)}" '
                f'x2="{_num(sbx)}" y2="{_num(sby)}" '
                f'stroke="{PALETA["negro"]}" stroke-width="0.5" />'
            )
    partes.append("</g>")


def _dib_zona_botin_svg(
    zona: ZonaBotin,
    alto: float,
    caja: tuple[float, float, float, float],
    partes: list[str],
) -> None:
    """Dibuja una zona: relleno gris + trama recortada + borde + acción."""
    dx, dy = offset_de_vista(zona.vista)
    puntos = _poligono_svg_puntos(zona.poligono, dx, dy, alto)
    clip_id = f"zona-{zona.nombre}"

    # Relleno gris base.
    partes.append(
        f'<polygon points="{puntos}" '
        f'fill="{color_base_zona(zona.gris)}" '
        f'stroke="{PALETA["negro"]}" stroke-width="0.6" />'
    )
    # Trama recortada.
    _dib_trama_botin_svg(zona, dx, dy, alto, caja, clip_id, partes)

    # Texto de la acción de juego junto a la zona (Req 3.7).
    if zona.accion:
        cx = sum(p[0] for p in zona.poligono) / len(zona.poligono)
        cy = sum(p[1] for p in zona.poligono) / len(zona.poligono)
        sx, sy = _botin_a_svg(cx, cy, dx, dy, alto)
        partes.append(
            f'<text x="{_num(sx)}" y="{_num(sy)}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="6" '
            f'fill="{PALETA["negro"]}">{_esc(zona.accion)}</text>'
        )


@lru_cache(maxsize=1024)
def botin_a_svg(spec: BotinSpec) -> tuple[str, str]:
    """Renderiza un `BotinSpec` a SVG. Devuelve ``(svg, view_box)``.

    Dibuja las dos siluetas (planta y perfil) y las siete zonas con gris base +
    trama recortada, de modo que se distingan también en escala de grises
    (Req 3.9) conservando la paleta rosa/negro (Req 3.8). El SVG es responsive
    y accesible, igual que el de cancha. El resultado se cachea por el spec.
    """
    ancho = spec.mundo.ancho_m * ESCALA_BOTIN_PX
    alto_u = spec.mundo.alto_m
    alto = alto_u * ESCALA_BOTIN_PX
    view_box = f"0 0 {_num(ancho)} {_num(alto)}"
    bbox = (0.0, 0.0, spec.mundo.ancho_m, spec.mundo.alto_m)

    titulo = spec.titulo or "Diagrama del botin: zonas de contacto"
    desc = (
        f"Silueta de botin en planta y perfil con {len(spec.zonas)} zonas "
        f"de contacto etiquetadas por accion de juego"
    )

    partes: list[str] = []
    partes.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'style="width:100%;height:auto" role="img" '
        f'preserveAspectRatio="xMidYMid meet">'
    )
    partes.append(f"<title>{_esc(titulo)}</title>")
    partes.append(f"<desc>{_esc(desc)}</desc>")

    # `<clipPath>` por zona para recortar su trama al polígono.
    partes.append("<defs>")
    for zona in spec.zonas:
        dx, dy = offset_de_vista(zona.vista)
        puntos = _poligono_svg_puntos(zona.poligono, dx, dy, alto_u)
        partes.append(
            f'<clipPath id="zona-{zona.nombre}">'
            f'<polygon points="{puntos}" /></clipPath>'
        )
    partes.append("</defs>")

    # Fondo del bloque.
    partes.append(
        f'<rect x="0" y="0" width="{_num(ancho)}" height="{_num(alto)}" '
        f'fill="{PALETA["fondo"]}" />'
    )

    # Zonas (relleno + trama + acción).
    for zona in spec.zonas:
        _dib_zona_botin_svg(zona, alto_u, bbox, partes)

    # Contornos de las siluetas por encima de las zonas.
    contornos = (
        (Vista.PLANTA, spec.contorno_planta),
        (Vista.PERFIL, spec.contorno_perfil),
    )
    for vista, contorno in contornos:
        dx, dy = offset_de_vista(vista)
        d = _contorno_svg_d(contorno, dx, dy, alto_u)
        partes.append(
            f'<path d="{d}" fill="none" '
            f'stroke="{PALETA["negro"]}" stroke-width="1.5" />'
        )

    # Costura decorativa de la planta.
    dx, dy = offset_de_vista(Vista.PLANTA)
    d_costura = _contorno_svg_d(spec.costura_planta, dx, dy, alto_u)
    partes.append(
        f'<path d="{d_costura}" fill="none" '
        f'stroke="{PALETA["negro"]}" stroke-width="0.6" />'
    )

    # Banda de suela del perfil.
    if len(spec.suela_perfil) >= 3:
        dx, dy = offset_de_vista(Vista.PERFIL)
        puntos = _poligono_svg_puntos(spec.suela_perfil, dx, dy, alto_u)
        partes.append(
            f'<polygon points="{puntos}" fill="none" '
            f'stroke="{PALETA["negro"]}" stroke-width="0.6" />'
        )

    partes.append("</svg>")
    return "".join(partes), view_box
