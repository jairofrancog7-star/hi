"""Motor de ilustraciones didacticas: figura esquematica + tecnica de golpeo.

Este modulo produce **Diagrama_Postura** (`ClaseDiagrama.POSTURA`) como
`DiagramaSpec` normales, de modo que los dos renderizadores ya existentes los
dibujan sin cambio alguno: `viz.py` los saca a SVG inline y `draw.py` a
operadores PDF. No se toca ninguno de los dos.

Por que se construye sobre el vocabulario de `Item` en vez de un renderizador
nuevo: los tipos `seg`, `mark`, `zone`, `txt`, `ball`, `run`, `pass` y `shot`
alcanzan para una figura humana esquematica con su pie de apoyo, su zona de
contacto, sus lineas de orientacion y la trayectoria del balon. Reusar el motor
mantiene la paridad web/PDF y la Property 12 (todo color de la paleta) sin
codigo duplicado.

Encuadre del contenido (importante): estas ilustraciones ensenan **tecnica de
futbol**. No son diagnostico medico ni rehabilitacion, y no se presentan como
tales. La comparacion "asi si / asi no" senala un error de ejecucion frecuente,
igual que se senala golpear con la punta en vez del empeine.

Convenciones del proyecto respetadas:

* Solo biblioteca estandar.
* Specs `frozen=True, slots=True` con tuplas: hashables y cacheables.
* Sin `assert` en produccion: los invariantes se comprueban con `raise`.
* Todo texto codificable en WinAnsi (cp1252): acentos si, guion largo no.
"""

from __future__ import annotations

import math
from typing import Literal

from . import paleta
from .diagram_spec import ClaseDiagrama, DiagramaSpec, Item, Leyenda, Mundo

__all__ = [
    "MUNDO_FIGURA",
    "ANCHO_PANEL",
    "ALTO_PANEL",
    "Lado",
    "figura_jugadora",
    "panel",
    "FIGURAS",
    "figura",
    "ids_figuras",
    "contar_posturas",
    "todas_las_figuras",
    "pase_corto_interior",
    "pase_largo_empeine",
    "tiro_potencia_empeine",
    "tiro_colocado_interior",
    "golpeo_exterior",
    "control_orientado",
    "bajar_balon_aereo",
    "conduccion",
    "regate_cambio_direccion",
    "aterrizaje_seguro",
    "REGLAS_FIGURA",
    "id_figura_para",
    "para_ficha",
]

# --------------------------------------------------------------------------- #
# Lienzo
# --------------------------------------------------------------------------- #
#
# El "mundo" de una figura no es una cancha: es un lienzo de dibujo en unidades
# arbitrarias. Se usan dos paneles del mismo tamano lado a lado para la
# comparacion "asi si" / "asi no", igual que el Diagrama_Botin coloca planta y
# perfil una junto a la otra.

#: Ancho de un panel del lienzo, en unidades de mundo.
ANCHO_PANEL: float = 12.0

#: Alto de un panel del lienzo, en unidades de mundo.
ALTO_PANEL: float = 12.0

#: Mundo de una ilustracion de dos paneles (correcto | error).
MUNDO_FIGURA: Mundo = Mundo(ANCHO_PANEL * 2.0, ALTO_PANEL)

#: Lado del cuerpo. `der` = pierna derecha ejecuta, `izq` = la izquierda.
Lado = Literal["izq", "der"]

#: Altura del suelo dentro de un panel.
_SUELO: float = 1.4

#: Proporciones de la figura, en unidades de mundo (figura de ~7.4 de alto).
_R_CABEZA: float = 0.62
_Y_HOMBROS: float = 7.0
_Y_CADERA: float = 4.9
_SEMI_HOMBROS: float = 0.82
_SEMI_CADERA: float = 0.66


# --------------------------------------------------------------------------- #
# Ayudantes de construccion de items
# --------------------------------------------------------------------------- #


def _seg(
    x1: float, y1: float, x2: float, y2: float, *, etiqueta: str = ""
) -> Item:
    """Segmento recto (hueso o linea de orientacion)."""
    return Item(tipo="seg", x=x1, y=y1, x2=x2, y2=y2, etiqueta=etiqueta)


def _marca(x: float, y: float, *, etiqueta: str = "", color: str | None = None) -> Item:
    """Marca puntual: articulacion, pie de apoyo o senalamiento de error."""
    return Item(tipo="mark", x=x, y=y, etiqueta=etiqueta, color=color)


def _texto(x: float, y: float, texto: str) -> Item:
    """Rotulo corto dentro del panel."""
    return Item(tipo="txt", x=x, y=y, etiqueta=texto)


def _zona(
    puntos: tuple[tuple[float, float], ...], *, etiqueta: str = ""
) -> Item:
    """Zona resaltada (superficie de contacto, area de apoyo)."""
    return Item(tipo="zone", puntos=puntos, etiqueta=etiqueta)


def _balon(x: float, y: float) -> Item:
    """Balon."""
    return Item(tipo="ball", x=x, y=y)


def _flecha(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    tipo: str = "pass",
    etiqueta: str = "",
) -> Item:
    """Flecha de trayectoria del balon (`pass`/`shot`) o de movimiento (`run`)."""
    return Item(tipo=tipo, x=x1, y=y1, x2=x2, y2=y2, etiqueta=etiqueta)


def _circulo_zona(
    cx: float, cy: float, radio: float, *, lados: int = 12, etiqueta: str = ""
) -> Item:
    """Aproxima un circulo con un poligono, para resaltar una zona redonda."""
    if lados < 3:
        raise ValueError(f"zona circular con {lados} lados: se necesitan al menos 3")
    puntos = tuple(
        (
            cx + radio * math.cos(2.0 * math.pi * i / lados),
            cy + radio * math.sin(2.0 * math.pi * i / lados),
        )
        for i in range(lados)
    )
    return _zona(puntos, etiqueta=etiqueta)


# --------------------------------------------------------------------------- #
# Figura humana esquematica
# --------------------------------------------------------------------------- #


def figura_jugadora(
    dx: float,
    *,
    lado_ejecutor: Lado = "der",
    flexion_rodilla: float = 20.0,
    valgo: float = 0.0,
    inclinacion_tronco: float = 8.0,
    apertura_pies: float = 1.5,
) -> tuple[Item, ...]:
    """Construye la figura esquematica de una jugadora dentro de un panel.

    `dx` desplaza el panel en X. Los angulos van en grados:

    * `flexion_rodilla`: flexion de la rodilla de apoyo (0 = pierna recta).
    * `valgo`: desviacion de la rodilla de apoyo hacia dentro (positivo) o
      hacia fuera (negativo). Es el parametro que distingue el aterrizaje
      alineado del colapso de rodilla.
    * `inclinacion_tronco`: inclinacion del tronco hacia el balon.
    * `apertura_pies`: separacion entre los pies.

    La figura es deliberadamente esquematica y deportiva: cabeza, linea de
    hombros, tronco, linea de cadera, dos piernas y dos brazos. Sin rasgos ni
    detalles anatomicos.
    """
    if apertura_pies <= 0.0:
        raise ValueError(f"apertura de pies invalida: {apertura_pies}")

    signo = 1.0 if lado_ejecutor == "der" else -1.0
    cx = dx + ANCHO_PANEL / 2.0

    # Tronco inclinado: la cabeza se adelanta segun `inclinacion_tronco`.
    rad_tronco = math.radians(inclinacion_tronco)
    alto_tronco = _Y_HOMBROS - _Y_CADERA
    x_hombros = cx + math.sin(rad_tronco) * alto_tronco * signo
    y_hombros = _Y_CADERA + math.cos(rad_tronco) * alto_tronco

    items: list[Item] = []

    # Cabeza y cuello.
    x_cabeza = x_hombros + math.sin(rad_tronco) * (_R_CABEZA + 0.5) * signo
    y_cabeza = y_hombros + _R_CABEZA + 0.5
    items.append(_marca(x_cabeza, y_cabeza, etiqueta="cabeza"))
    items.append(_seg(x_hombros, y_hombros, x_cabeza, y_cabeza - _R_CABEZA))

    # Linea de hombros (orientacion del torso).
    items.append(
        _seg(
            x_hombros - _SEMI_HOMBROS,
            y_hombros,
            x_hombros + _SEMI_HOMBROS,
            y_hombros,
            etiqueta="linea de hombros",
        )
    )

    # Tronco y linea de cadera (orientacion de la cadera).
    items.append(_seg(x_hombros, y_hombros, cx, _Y_CADERA))
    items.append(
        _seg(
            cx - _SEMI_CADERA,
            _Y_CADERA,
            cx + _SEMI_CADERA,
            _Y_CADERA,
            etiqueta="linea de cadera",
        )
    )

    # Brazos abiertos para equilibrio.
    items.append(
        _seg(x_hombros - _SEMI_HOMBROS, y_hombros, x_hombros - _SEMI_HOMBROS - 1.0, y_hombros - 1.3)
    )
    items.append(
        _seg(x_hombros + _SEMI_HOMBROS, y_hombros, x_hombros + _SEMI_HOMBROS + 1.0, y_hombros - 1.1)
    )

    # Pierna de apoyo: cadera -> rodilla -> tobillo. El valgo desvia la rodilla.
    x_cadera_apoyo = cx - _SEMI_CADERA * signo
    x_tobillo_apoyo = x_cadera_apoyo - (apertura_pies / 2.0) * signo
    rad_flexion = math.radians(flexion_rodilla)
    y_rodilla = _SUELO + (_Y_CADERA - _SUELO) * 0.52
    x_rodilla = (
        (x_cadera_apoyo + x_tobillo_apoyo) / 2.0
        + math.sin(rad_flexion) * 0.55 * signo
        + math.radians(valgo) * 2.2 * signo
    )
    items.append(_seg(x_cadera_apoyo, _Y_CADERA, x_rodilla, y_rodilla))
    items.append(_seg(x_rodilla, y_rodilla, x_tobillo_apoyo, _SUELO))
    items.append(_marca(x_rodilla, y_rodilla, etiqueta="rodilla de apoyo"))

    # Pierna ejecutora: cadera -> rodilla -> tobillo, adelantada hacia el balon.
    x_cadera_ejec = cx + _SEMI_CADERA * signo
    x_tobillo_ejec = x_cadera_ejec + (apertura_pies / 2.0 + 0.5) * signo
    x_rodilla_ejec = (x_cadera_ejec + x_tobillo_ejec) / 2.0
    items.append(_seg(x_cadera_ejec, _Y_CADERA, x_rodilla_ejec, y_rodilla))
    items.append(_seg(x_rodilla_ejec, y_rodilla, x_tobillo_ejec, _SUELO + 0.15))

    return tuple(items)


def _suelo(dx: float) -> tuple[Item, ...]:
    """Linea de suelo del panel."""
    return (_seg(dx + 0.7, _SUELO, dx + ANCHO_PANEL - 0.7, _SUELO),)


def panel(
    dx: float,
    rotulo: str,
    items: tuple[Item, ...],
) -> tuple[Item, ...]:
    """Envuelve `items` con la linea de suelo y el rotulo del panel."""
    return (
        *_suelo(dx),
        _texto(dx + ANCHO_PANEL / 2.0, ALTO_PANEL - 0.7, rotulo),
        *items,
    )


# --------------------------------------------------------------------------- #
# Ilustracion 1: pase corto con interior del pie
# --------------------------------------------------------------------------- #

#: Rotulo del panel correcto. Sin acento: pasa por WinAnsi igual que el resto.
ROTULO_CORRECTO: str = "ASI SI"

#: Rotulo del panel del error frecuente.
ROTULO_ERROR: str = "ASI NO"


def pase_corto_interior() -> DiagramaSpec:
    """Pase corto con interior del pie: postura correcta frente al error comun.

    Panel izquierdo (correcto): pie de apoyo junto al balon, tobillo firme,
    cadera orientada al objetivo, contacto con la parte interna del pie y balon
    que sale raso.

    Panel derecho (error): pie de apoyo lejos del balon y contacto con la punta,
    que es lo que manda el balon alto y desviado.
    """
    izq = 0.0
    der = ANCHO_PANEL

    # --- Panel correcto -----------------------------------------------------
    fig_ok = figura_jugadora(
        izq, lado_ejecutor="der", flexion_rodilla=18.0, inclinacion_tronco=8.0
    )
    cx_ok = izq + ANCHO_PANEL / 2.0
    # El balon va junto al pie de apoyo, no adelante.
    x_balon_ok = cx_ok + 1.35
    y_balon_ok = _SUELO + 0.42
    x_apoyo_ok = cx_ok - 1.41

    ok: list[Item] = list(fig_ok)
    ok.append(_balon(x_balon_ok, y_balon_ok))
    # Pie de apoyo resaltado, a la altura del balon.
    ok.append(_circulo_zona(x_apoyo_ok, _SUELO + 0.2, 0.62, etiqueta="pie de apoyo"))
    ok.append(_marca(x_apoyo_ok, _SUELO + 0.2, etiqueta="pie de apoyo junto al balon"))
    # Zona de contacto: parte interna del pie ejecutor.
    ok.append(
        _circulo_zona(
            x_balon_ok - 0.72, y_balon_ok, 0.42, etiqueta="contacto con el interior"
        )
    )
    # Orientacion de la cadera hacia el objetivo.
    ok.append(
        _flecha(
            cx_ok,
            _Y_CADERA,
            izq + ANCHO_PANEL - 1.1,
            _Y_CADERA,
            tipo="run",
            etiqueta="cadera al objetivo",
        )
    )
    # Trayectoria del balon: rasa.
    ok.append(
        _flecha(
            x_balon_ok + 0.45,
            y_balon_ok,
            izq + ANCHO_PANEL - 0.9,
            y_balon_ok,
            tipo="pass",
            etiqueta="balon raso",
        )
    )
    ok.append(_texto(cx_ok, _SUELO - 0.75, "Tobillo firme, balon raso"))

    # --- Panel del error ----------------------------------------------------
    fig_mal = figura_jugadora(
        der, lado_ejecutor="der", flexion_rodilla=4.0, inclinacion_tronco=-6.0,
        apertura_pies=2.6,
    )
    cx_mal = der + ANCHO_PANEL / 2.0
    x_balon_mal = cx_mal + 2.05
    y_balon_mal = _SUELO + 0.42
    x_apoyo_mal = cx_mal - 1.9

    mal: list[Item] = list(fig_mal)
    mal.append(_balon(x_balon_mal, y_balon_mal))
    mal.append(
        _marca(
            x_apoyo_mal,
            _SUELO + 0.2,
            etiqueta="pie de apoyo lejos",
            color=paleta.ROJO,
        )
    )
    # Contacto con la punta: el error.
    mal.append(
        _marca(
            x_balon_mal - 0.55,
            y_balon_mal + 0.2,
            etiqueta="contacto con la punta",
            color=paleta.ROJO,
        )
    )
    # Trayectoria alta y desviada.
    mal.append(
        _flecha(
            x_balon_mal + 0.45,
            y_balon_mal + 0.3,
            der + ANCHO_PANEL - 0.9,
            _Y_CADERA + 1.4,
            tipo="shot",
            etiqueta="balon alto y desviado",
        )
    )
    mal.append(_texto(cx_mal, _SUELO - 0.75, "Corrige: apoyo junto al balon"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Pase corto con interior: pie de apoyo, contacto y trayectoria",
        leyenda=(
            Leyenda(texto="Pie de apoyo", simbolo="circulo resaltado"),
            Leyenda(texto="Superficie de contacto", simbolo="zona sobre el pie"),
            Leyenda(texto="Orientacion de cadera", simbolo="flecha de movimiento"),
            Leyenda(texto="Trayectoria del balon", simbolo="flecha de pase"),
            Leyenda(texto="Error frecuente", simbolo="marca roja"),
        ),
    )


# --------------------------------------------------------------------------- #
# Utileria de escena (conos, companeras, rival, portera, porteria, objetivo)
# --------------------------------------------------------------------------- #
#
# Todos estos tipos ya existen en el vocabulario de `Item` y los dos
# renderizadores los dibujan sin cambios: `cone`, `player`, `rival`, `gk` y
# `target`. Se envuelven en ayudantes cortos para que las escenas se lean.


def _cono(x: float, y: float, *, etiqueta: str = "") -> Item:
    """Cono de referencia en el piso."""
    return Item(tipo="cone", x=x, y=y, etiqueta=etiqueta)


def _companera(x: float, y: float, *, etiqueta: str = "") -> Item:
    """Companera que recibe o apoya."""
    return Item(tipo="player", x=x, y=y, etiqueta=etiqueta)


def _rival(x: float, y: float, *, etiqueta: str = "") -> Item:
    """Rival que marca o presiona."""
    return Item(tipo="rival", x=x, y=y, etiqueta=etiqueta)


def _portera(x: float, y: float, *, etiqueta: str = "portera") -> Item:
    """Portera del panel."""
    return Item(tipo="gk", x=x, y=y, etiqueta=etiqueta)


def _objetivo(x: float, y: float, *, etiqueta: str = "") -> Item:
    """Punto de mira dentro de la porteria."""
    return Item(tipo="target", x=x, y=y, etiqueta=etiqueta)


#: Ancho de la porteria esquematica dentro de un panel.
_ANCHO_PORTERIA: float = 1.4

#: Alto de la porteria esquematica dentro de un panel.
_ALTO_PORTERIA: float = 1.7


def _porteria(dx: float, *, etiqueta: str = "porteria") -> tuple[Item, ...]:
    """Porteria esquematica pegada al borde derecho del panel `dx`."""
    x0 = dx + ANCHO_PANEL - 1.9
    x1 = x0 + _ANCHO_PORTERIA
    techo = _SUELO + _ALTO_PORTERIA
    return (
        _seg(x0, _SUELO, x0, techo, etiqueta=etiqueta),
        _seg(x1, _SUELO, x1, techo),
        _seg(x0, techo, x1, techo),
    )


#: Altura donde se nombra el error frecuente con texto (no solo con color).
_Y_ROTULO_ERROR: float = ALTO_PANEL - 1.6

#: Altura del pie de panel donde va la correccion o la clave de ejecucion.
_Y_PIE_PANEL: float = _SUELO - 0.75


# --------------------------------------------------------------------------- #
# Ilustracion 2: pase largo con empeine
# --------------------------------------------------------------------------- #


def pase_largo_empeine() -> DiagramaSpec:
    """Pase largo con empeine: aproximacion, apoyo, contacto y vuelo del balon.

    Panel correcto: carrera de aproximacion en diagonal, pie de apoyo al lado y
    ligeramente atras del balon, tronco estable, contacto con el empeine y
    trayectoria aerea larga hasta la companera de la banda contraria.

    Panel del error: apoyo encima del balon y tronco vencido hacia atras, que es
    lo que deja el envio corto y sin altura.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.5
    x_apoyo = cx - 1.6

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=22.0, inclinacion_tronco=6.0, apertura_pies=1.8
        )
    )
    ok.append(
        _flecha(
            izq + 1.0,
            _SUELO + 1.2,
            cx - 2.4,
            _SUELO + 0.6,
            tipo="run",
            etiqueta="carrera de aproximacion en diagonal",
        )
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(
        _circulo_zona(
            x_apoyo,
            _SUELO + 0.2,
            0.62,
            etiqueta="pie de apoyo al lado y atras del balon",
        )
    )
    ok.append(_marca(x_apoyo, _SUELO + 0.2, etiqueta="pie de apoyo firme"))
    ok.append(
        _circulo_zona(
            x_balon - 0.62, y_balon - 0.16, 0.44, etiqueta="contacto con el empeine"
        )
    )
    ok.append(_marca(cx + 0.2, _Y_CADERA + 1.3, etiqueta="tronco estable"))
    # La trayectoria aerea se arma con dos tramos: subida y caida.
    ok.append(
        _flecha(
            x_balon + 0.5,
            y_balon + 0.2,
            cx + 3.4,
            ALTO_PANEL - 3.0,
            tipo="pass",
            etiqueta="el balon sube por el aire",
        )
    )
    ok.append(
        _flecha(
            cx + 3.4,
            ALTO_PANEL - 3.0,
            izq + ANCHO_PANEL - 1.4,
            _SUELO + 1.2,
            tipo="pass",
            etiqueta="envio largo a la banda contraria",
        )
    )
    ok.append(
        _companera(izq + ANCHO_PANEL - 1.0, _SUELO + 0.7, etiqueta="companera lejana")
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Empeine completo y distancia amplia"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 0.9
    x_apoyo_mal = cxm - 0.75

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=6.0, inclinacion_tronco=-14.0, apertura_pies=1.2
        )
    )
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            x_apoyo_mal,
            _SUELO + 0.2,
            etiqueta="pie de apoyo encima del balon",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            cxm - 0.4,
            _Y_CADERA + 1.4,
            etiqueta="tronco vencido hacia atras",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.5,
            y_balon + 0.2,
            cxm + 2.6,
            _SUELO + 0.9,
            tipo="pass",
            etiqueta="envio corto y sin altura",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: apoyo encima del balon"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: apoyo al lado y atras"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Pase largo con empeine: apoyo, contacto y trayectoria aerea",
        leyenda=(
            Leyenda(texto="Pie de apoyo", simbolo="circulo resaltado"),
            Leyenda(texto="Contacto con el empeine", simbolo="zona sobre el pie"),
            Leyenda(texto="Carrera de aproximacion", simbolo="flecha de movimiento"),
            Leyenda(texto="Trayectoria aerea del balon", simbolo="flecha de pase"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 3: tiro con potencia usando el empeine
# --------------------------------------------------------------------------- #


def tiro_potencia_empeine() -> DiagramaSpec:
    """Tiro de potencia: preparacion, apoyo, empeine, tronco y terminacion.

    Panel correcto: ultimo paso de preparacion, pie de apoyo estable al lado del
    balon, pecho ligeramente sobre el balon, contacto con el empeine completo,
    terminacion de la pierna hacia adelante y disparo fuerte y raso.

    Panel del error: tronco echado hacia atras y contacto debajo del balon, que
    manda el disparo por encima del travesano.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.45
    x_apoyo = cx - 1.55

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=24.0, inclinacion_tronco=14.0, apertura_pies=1.7
        )
    )
    ok.extend(_porteria(izq))
    ok.append(
        _flecha(
            izq + 1.0,
            _SUELO + 1.1,
            cx - 2.3,
            _SUELO + 0.6,
            tipo="run",
            etiqueta="preparacion y ultimo paso",
        )
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(
        _circulo_zona(x_apoyo, _SUELO + 0.2, 0.62, etiqueta="pie de apoyo estable")
    )
    ok.append(_marca(x_apoyo, _SUELO + 0.2, etiqueta="pie de apoyo estable"))
    ok.append(
        _circulo_zona(
            x_balon - 0.6, y_balon - 0.12, 0.44, etiqueta="contacto con el empeine"
        )
    )
    ok.append(
        _marca(cx + 0.35, _Y_CADERA + 1.5, etiqueta="tronco inclinado sobre el balon")
    )
    ok.append(
        _flecha(
            x_balon + 0.3,
            y_balon + 0.1,
            cx + 3.0,
            _SUELO + 1.9,
            tipo="run",
            etiqueta="terminacion de la pierna",
        )
    )
    ok.append(
        _flecha(
            x_balon + 0.5,
            y_balon,
            izq + ANCHO_PANEL - 2.1,
            _SUELO + 0.7,
            tipo="shot",
            etiqueta="potencia hacia la porteria, balon raso",
        )
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Empeine completo, disparo fuerte"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 1.9

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=8.0, inclinacion_tronco=-16.0, apertura_pies=2.4
        )
    )
    mal.extend(_porteria(der))
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            cxm - 0.5,
            _Y_CADERA + 1.5,
            etiqueta="tronco echado hacia atras",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            x_balon_mal - 0.5,
            y_balon + 0.35,
            etiqueta="contacto debajo del balon",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.4,
            y_balon + 0.3,
            der + ANCHO_PANEL - 1.2,
            ALTO_PANEL - 2.2,
            tipo="shot",
            etiqueta="balon por encima del travesano",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: tronco echado hacia atras"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: pecho sobre el balon"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Tiro con potencia: empeine, apoyo estable y terminacion",
        leyenda=(
            Leyenda(texto="Pie de apoyo", simbolo="circulo resaltado"),
            Leyenda(texto="Contacto con el empeine", simbolo="zona sobre el pie"),
            Leyenda(texto="Terminacion de la pierna", simbolo="flecha de movimiento"),
            Leyenda(texto="Disparo con potencia", simbolo="flecha gruesa de tiro"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 4: tiro colocado con interior
# --------------------------------------------------------------------------- #


def tiro_colocado_interior() -> DiagramaSpec:
    """Tiro colocado: cuerpo abierto, contacto lateral y zona objetivo.

    Se distingue del tiro de potencia a proposito: aqui no hay flecha gruesa de
    disparo sino una trayectoria curva de tramos finos que termina en una zona
    objetivo marcada con punto de mira. La clave visual es *precision*, no
    fuerza.

    Panel del error: cadera cerrada y contacto al centro del balon, que manda el
    tiro al centro de la porteria.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.4
    x_apoyo = cx - 1.9
    x_palo = izq + ANCHO_PANEL - 1.9

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=18.0, inclinacion_tronco=4.0, apertura_pies=2.2
        )
    )
    ok.extend(_porteria(izq))
    ok.append(
        _zona(
            (
                (x_palo, _SUELO),
                (x_palo + 0.5, _SUELO),
                (x_palo + 0.5, _SUELO + _ALTO_PORTERIA),
                (x_palo, _SUELO + _ALTO_PORTERIA),
            ),
            etiqueta="zona objetivo: palo lejano",
        )
    )
    ok.append(_objetivo(x_palo + 0.25, _SUELO + 1.3, etiqueta="punto de mira"))
    ok.append(_balon(x_balon, y_balon))
    ok.append(
        _circulo_zona(
            x_apoyo, _SUELO + 0.2, 0.62, etiqueta="pie de apoyo abierto al objetivo"
        )
    )
    ok.append(_marca(x_apoyo, _SUELO + 0.2, etiqueta="pie de apoyo abierto"))
    ok.append(
        _circulo_zona(
            x_balon - 0.55,
            y_balon + 0.1,
            0.42,
            etiqueta="contacto lateral con el interior",
        )
    )
    ok.append(
        _flecha(
            cx,
            _Y_CADERA,
            izq + ANCHO_PANEL - 2.4,
            _Y_CADERA + 0.4,
            tipo="run",
            etiqueta="cuerpo abierto al palo lejano",
        )
    )
    # Trayectoria curva: tres tramos finos de pase, no una recta de potencia.
    ok.append(
        _flecha(
            x_balon + 0.45,
            y_balon + 0.1,
            cx + 2.4,
            _SUELO + 1.5,
            tipo="pass",
            etiqueta="salida con comba",
        )
    )
    ok.append(
        _flecha(
            cx + 2.4,
            _SUELO + 1.5,
            cx + 3.6,
            _SUELO + 1.9,
            tipo="pass",
            etiqueta="trayectoria curva",
        )
    )
    ok.append(
        _flecha(
            cx + 3.6,
            _SUELO + 1.9,
            x_palo + 0.15,
            _SUELO + 1.35,
            tipo="pass",
            etiqueta="entra por el palo lejano",
        )
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Menos fuerza y mas precision"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 1.1

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=6.0, inclinacion_tronco=2.0, apertura_pies=1.2
        )
    )
    mal.extend(_porteria(der))
    mal.append(_portera(der + ANCHO_PANEL - 1.2, _SUELO + 0.75))
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            cxm - 0.2,
            _Y_CADERA,
            etiqueta="cadera cerrada, sin abrir al palo",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            x_balon_mal - 0.45,
            y_balon + 0.1,
            etiqueta="contacto al centro del balon",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.45,
            y_balon + 0.1,
            der + ANCHO_PANEL - 1.5,
            _SUELO + 0.75,
            tipo="pass",
            etiqueta="balon al centro, comodo para la portera",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: cadera cerrada"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: abre la cadera al palo lejano"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Tiro colocado con interior: cuerpo abierto y zona objetivo",
        leyenda=(
            Leyenda(texto="Pie de apoyo", simbolo="circulo resaltado"),
            Leyenda(texto="Contacto lateral con el interior", simbolo="zona sobre el pie"),
            Leyenda(texto="Zona objetivo", simbolo="franja del palo lejano"),
            Leyenda(texto="Trayectoria curva", simbolo="flechas finas de pase"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 5: golpeo con el exterior
# --------------------------------------------------------------------------- #


def golpeo_exterior() -> DiagramaSpec:
    """Golpeo con el exterior: zona de contacto, cadera, tobillo y salida.

    Panel correcto: cadera cerrada hacia dentro, tobillo firme y girado, la zona
    de contacto marcada en la parte de fuera del pie y el balon saliendo hacia
    fuera en diagonal.

    Panel del error: contacto con la punta y tobillo suelto, con el balon sin
    control.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.4
    x_apoyo = cx - 1.5

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=16.0, inclinacion_tronco=6.0, apertura_pies=1.6
        )
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(_circulo_zona(x_apoyo, _SUELO + 0.2, 0.62, etiqueta="pie de apoyo firme"))
    ok.append(_marca(x_apoyo, _SUELO + 0.2, etiqueta="pie de apoyo firme"))
    ok.append(
        _circulo_zona(
            x_balon + 0.6,
            y_balon - 0.1,
            0.44,
            etiqueta="contacto con el exterior del pie",
        )
    )
    ok.append(_marca(cx + 0.7, _Y_CADERA, etiqueta="cadera cerrada hacia dentro"))
    ok.append(_marca(x_balon + 0.35, _SUELO + 0.12, etiqueta="tobillo firme y girado"))
    ok.append(
        _flecha(
            x_balon + 0.5,
            y_balon,
            izq + ANCHO_PANEL - 1.2,
            _SUELO + 2.4,
            tipo="pass",
            etiqueta="direccion de salida: hacia fuera",
        )
    )
    ok.append(_cono(izq + ANCHO_PANEL - 1.6, _SUELO + 0.3, etiqueta="referencia"))
    ok.append(_texto(cx, _Y_PIE_PANEL, "Exterior: salida abierta y rapida"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 1.9

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=6.0, inclinacion_tronco=-4.0, apertura_pies=2.4
        )
    )
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            x_balon_mal - 0.5,
            y_balon + 0.25,
            etiqueta="contacto con la punta",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(cxm + 0.9, _SUELO + 0.12, etiqueta="tobillo suelto", color=paleta.ROJO)
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.45,
            y_balon + 0.25,
            der + ANCHO_PANEL - 1.0,
            _Y_CADERA + 1.0,
            tipo="shot",
            etiqueta="balon sin control",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: contacto con la punta"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: gira el tobillo, usa el exterior"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Golpeo con el exterior: zona de contacto y salida del balon",
        leyenda=(
            Leyenda(texto="Pie de apoyo", simbolo="circulo resaltado"),
            Leyenda(texto="Contacto con el exterior", simbolo="zona sobre el pie"),
            Leyenda(texto="Cadera y tobillo", simbolo="marcas de orientacion"),
            Leyenda(texto="Direccion de salida", simbolo="flecha de pase"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 6: control orientado
# --------------------------------------------------------------------------- #


def control_orientado() -> DiagramaSpec:
    """Control orientado: recibir perfilada, cabeza arriba y primer toque.

    Panel correcto: cuerpo perfilado antes de que llegue el pase, cabeza
    levantada mirando el espacio libre y primer toque que deja el balon lejos de
    la marca.

    Panel del error: control detenido con el balon debajo del cuerpo y cabeza
    abajo, con la rival encima.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.3
    x_espacio = izq + ANCHO_PANEL - 3.6

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=18.0, inclinacion_tronco=6.0, apertura_pies=1.9
        )
    )
    ok.append(
        _zona(
            (
                (x_espacio, _SUELO + 0.2),
                (izq + ANCHO_PANEL - 0.9, _SUELO + 0.2),
                (izq + ANCHO_PANEL - 0.9, _SUELO + 2.0),
                (x_espacio, _SUELO + 2.0),
            ),
            etiqueta="espacio libre",
        )
    )
    ok.append(
        _flecha(
            izq + 1.0,
            _SUELO + 1.5,
            x_balon - 1.1,
            y_balon + 0.25,
            tipo="pass",
            etiqueta="llega el pase",
        )
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(
        _circulo_zona(cx - 1.6, _SUELO + 0.2, 0.62, etiqueta="pie de apoyo perfilado")
    )
    ok.append(_marca(cx - 1.6, _SUELO + 0.2, etiqueta="cuerpo perfilado, medio giro"))
    ok.append(
        _circulo_zona(
            x_balon - 0.55, y_balon, 0.42, etiqueta="primer toque con el interior"
        )
    )
    ok.append(
        _marca(cx + 0.6, _Y_CADERA + 2.5, etiqueta="cabeza levantada antes de recibir")
    )
    ok.append(
        _flecha(
            cx + 1.1,
            _Y_CADERA + 2.9,
            izq + ANCHO_PANEL - 1.2,
            _Y_CADERA + 2.9,
            tipo="run",
            etiqueta="mira el espacio antes del control",
        )
    )
    ok.append(
        _flecha(
            x_balon + 0.5,
            y_balon,
            izq + ANCHO_PANEL - 2.4,
            _SUELO + 0.9,
            tipo="pass",
            etiqueta="primer toque hacia el espacio libre",
        )
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Control orientado: el juego sigue"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 0.8

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=8.0, inclinacion_tronco=16.0, apertura_pies=1.2
        )
    )
    mal.append(
        _flecha(
            der + 1.0,
            _SUELO + 1.5,
            x_balon_mal - 1.0,
            y_balon + 0.25,
            tipo="pass",
            etiqueta="llega el pase",
        )
    )
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            x_balon_mal,
            y_balon + 0.6,
            etiqueta="control detenido: balon debajo del cuerpo",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            cxm + 1.2,
            _Y_CADERA + 2.1,
            etiqueta="cabeza abajo, no vio el espacio",
            color=paleta.ROJO,
        )
    )
    mal.append(_rival(cxm + 2.6, _SUELO + 0.9, etiqueta="rival llega a presionar"))
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: control detenido"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: primer toque al espacio"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Control orientado: perfil, cabeza arriba y primer toque",
        leyenda=(
            Leyenda(texto="Pie de apoyo perfilado", simbolo="circulo resaltado"),
            Leyenda(texto="Primer toque", simbolo="zona sobre el pie"),
            Leyenda(texto="Espacio libre", simbolo="zona sombreada"),
            Leyenda(texto="Mirada antes de recibir", simbolo="flecha de movimiento"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 7: bajar balon aereo
# --------------------------------------------------------------------------- #


def bajar_balon_aereo() -> DiagramaSpec:
    """Bajar balon aereo con planta, muslo y pecho, amortiguando el contacto.

    Panel correcto: las tres superficies marcadas (pecho, muslo y planta) y las
    flechas de amortiguacion que retiran suavemente la superficie en el momento
    del contacto, hasta dejar el balon muerto en el piso.

    Panel del error: superficie rigida, el balon rebota hacia arriba y se pierde.
    """
    izq = 0.0
    der = ANCHO_PANEL

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=20.0, inclinacion_tronco=-4.0, apertura_pies=1.8
        )
    )
    ok.append(
        _flecha(
            izq + 1.3,
            ALTO_PANEL - 1.9,
            cx + 1.2,
            _Y_CADERA + 2.2,
            tipo="pass",
            etiqueta="balon que cae del aire",
        )
    )
    ok.append(_balon(cx + 1.4, _Y_CADERA + 1.9))
    ok.append(
        _circulo_zona(
            cx + 0.35, _Y_CADERA + 1.6, 0.5, etiqueta="control con el pecho"
        )
    )
    ok.append(
        _circulo_zona(cx + 1.2, _Y_CADERA - 1.1, 0.5, etiqueta="control con el muslo")
    )
    ok.append(
        _circulo_zona(cx + 1.9, _SUELO + 0.28, 0.5, etiqueta="control con la planta")
    )
    ok.append(
        _flecha(
            cx + 0.9,
            _Y_CADERA + 1.6,
            cx - 0.2,
            _Y_CADERA + 1.2,
            tipo="run",
            etiqueta="retira el pecho para amortiguar",
        )
    )
    ok.append(
        _flecha(
            cx + 1.6,
            _Y_CADERA - 1.0,
            cx + 0.9,
            _Y_CADERA - 1.7,
            tipo="run",
            etiqueta="baja el muslo para amortiguar",
        )
    )
    ok.append(
        _flecha(
            cx + 2.3,
            _SUELO + 0.5,
            cx + 3.1,
            _SUELO + 0.2,
            tipo="pass",
            etiqueta="el balon queda muerto en el piso",
        )
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Amortigua y deja el balon listo"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=4.0, inclinacion_tronco=-12.0, apertura_pies=1.5
        )
    )
    mal.append(
        _flecha(
            der + 1.3,
            ALTO_PANEL - 1.9,
            cxm + 1.0,
            _Y_CADERA + 1.6,
            tipo="pass",
            etiqueta="balon que cae del aire",
        )
    )
    mal.append(_balon(cxm + 1.3, _Y_CADERA + 1.3))
    mal.append(
        _marca(
            cxm + 0.5,
            _Y_CADERA + 1.5,
            etiqueta="superficie rigida: golpea el balon",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            cxm + 1.6,
            _Y_CADERA + 1.6,
            cxm + 3.4,
            ALTO_PANEL - 1.4,
            tipo="shot",
            etiqueta="el balon rebota hacia arriba",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: balon rebota hacia arriba"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: retira la superficie al contacto"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Bajar balon aereo: planta, muslo y pecho con amortiguacion",
        leyenda=(
            Leyenda(texto="Control con el pecho", simbolo="zona resaltada"),
            Leyenda(texto="Control con el muslo", simbolo="zona resaltada"),
            Leyenda(texto="Control con la planta", simbolo="zona resaltada"),
            Leyenda(texto="Amortiguacion", simbolo="flecha de movimiento"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 8: conduccion
# --------------------------------------------------------------------------- #


def conduccion() -> DiagramaSpec:
    """Conduccion: toques cortos, balon cerca del cuerpo y mirada alterna.

    Panel correcto: el balon dentro del circulo de control junto al cuerpo,
    toques cortos y seguidos, zonas de contacto de interior y exterior, y las dos
    miradas alternadas (al balon y al espacio).

    Panel del error: toque largo que deja el balon lejos y cabeza abajo, con la
    rival robando.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.2

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=20.0, inclinacion_tronco=8.0, apertura_pies=1.6
        )
    )
    ok.append(
        _circulo_zona(x_balon, y_balon, 0.95, etiqueta="balon cerca del cuerpo")
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(
        _circulo_zona(
            x_balon - 0.6, y_balon - 0.1, 0.4, etiqueta="toque con el interior"
        )
    )
    ok.append(
        _circulo_zona(
            x_balon + 0.7, y_balon - 0.1, 0.4, etiqueta="toque con el exterior"
        )
    )
    ok.append(
        _flecha(
            x_balon + 0.45,
            y_balon,
            x_balon + 1.5,
            y_balon,
            tipo="dribble",
            etiqueta="toques cortos y seguidos",
        )
    )
    ok.append(
        _flecha(
            x_balon + 1.7,
            y_balon,
            x_balon + 2.8,
            y_balon,
            tipo="dribble",
            etiqueta="toques cortos y seguidos",
        )
    )
    ok.append(
        _marca(cx + 0.7, _Y_CADERA + 2.5, etiqueta="miradas alternadas: balon y espacio")
    )
    ok.append(
        _flecha(
            cx + 0.9,
            _Y_CADERA + 2.4,
            x_balon + 0.2,
            y_balon + 1.3,
            tipo="run",
            etiqueta="mirada al balon",
        )
    )
    ok.append(
        _flecha(
            cx + 1.1,
            _Y_CADERA + 2.9,
            izq + ANCHO_PANEL - 1.0,
            _Y_CADERA + 2.9,
            tipo="run",
            etiqueta="mirada al espacio",
        )
    )
    ok.append(_cono(izq + ANCHO_PANEL - 2.2, _SUELO + 0.3, etiqueta="referencia"))
    ok.append(_cono(izq + ANCHO_PANEL - 1.0, _SUELO + 0.3, etiqueta="referencia"))
    ok.append(_texto(cx, _Y_PIE_PANEL, "Toques cortos, balon controlado"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 3.2

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=6.0, inclinacion_tronco=20.0, apertura_pies=1.4
        )
    )
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            x_balon_mal - 1.2,
            y_balon + 0.35,
            etiqueta="balon lejos del cuerpo",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            cxm + 1.2,
            _Y_CADERA + 2.1,
            etiqueta="cabeza abajo, no ve el juego",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.5,
            y_balon,
            der + ANCHO_PANEL - 1.0,
            y_balon,
            tipo="dribble",
            etiqueta="toque largo, pierde el balon",
        )
    )
    mal.append(
        _rival(der + ANCHO_PANEL - 1.5, _SUELO + 0.9, etiqueta="rival roba el balon")
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: balon lejos y cabeza abajo"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: toques cortos y mirada alterna"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Conduccion: toques cortos, balon cerca y mirada alterna",
        leyenda=(
            Leyenda(texto="Balon cerca del cuerpo", simbolo="circulo de control"),
            Leyenda(texto="Toque con interior y exterior", simbolo="zonas sobre el pie"),
            Leyenda(texto="Toques cortos", simbolo="flechas de conduccion"),
            Leyenda(texto="Miradas alternadas", simbolo="flechas de movimiento"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 9: regate con cambio de direccion
# --------------------------------------------------------------------------- #


def regate_cambio_direccion() -> DiagramaSpec:
    """Regate con cambio de direccion: frenado, engano, apoyo y salida.

    Panel correcto: frenado con la planta, centro de gravedad bajo, engano de
    hombro y cadera, cambio de apoyo y salida explosiva en el primer paso.

    Panel del error: cambio lento, tronco erguido y sin frenado previo, con la
    rival recuperando la posicion.
    """
    izq = 0.0
    der = ANCHO_PANEL
    y_balon = _SUELO + 0.42

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_balon = cx + 1.2

    ok: list[Item] = list(
        figura_jugadora(
            izq, flexion_rodilla=34.0, inclinacion_tronco=10.0, apertura_pies=2.0
        )
    )
    ok.append(_rival(cx + 3.0, _SUELO + 1.0, etiqueta="rival"))
    ok.append(
        _flecha(
            izq + 1.0,
            _SUELO + 0.9,
            cx - 2.3,
            _SUELO + 0.6,
            tipo="run",
            etiqueta="llega conduciendo",
        )
    )
    ok.append(_balon(x_balon, y_balon))
    ok.append(_circulo_zona(cx - 1.7, _SUELO + 0.2, 0.62, etiqueta="frena con la planta"))
    ok.append(_marca(cx - 1.7, _SUELO + 0.2, etiqueta="frenado y cambio de apoyo"))
    ok.append(_marca(cx - 0.2, _Y_CADERA - 1.4, etiqueta="centro de gravedad bajo"))
    ok.append(_marca(cx + 0.9, _Y_CADERA + 2.0, etiqueta="engano de hombro"))
    ok.append(
        _flecha(
            cx + 1.0,
            _Y_CADERA + 1.6,
            cx + 2.6,
            _Y_CADERA + 1.2,
            tipo="run",
            etiqueta="engano de hombro y cadera",
        )
    )
    ok.append(
        _flecha(
            x_balon + 0.45,
            y_balon,
            cx + 2.2,
            _SUELO + 0.25,
            tipo="dribble",
            etiqueta="cambio de direccion con el exterior",
        )
    )
    ok.append(
        _flecha(
            cx + 2.4,
            _SUELO + 0.5,
            izq + ANCHO_PANEL - 1.0,
            _SUELO + 1.9,
            tipo="run",
            etiqueta="salida explosiva en el primer paso",
        )
    )
    ok.append(_texto(cx, _Y_PIE_PANEL, "Frena, engana y sale acelerando"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_balon_mal = cxm + 1.4

    mal: list[Item] = list(
        figura_jugadora(
            der, flexion_rodilla=6.0, inclinacion_tronco=4.0, apertura_pies=1.3
        )
    )
    mal.append(_rival(cxm + 2.6, _SUELO + 1.0, etiqueta="rival recupera la posicion"))
    mal.append(_balon(x_balon_mal, y_balon))
    mal.append(
        _marca(
            cxm - 0.3,
            _Y_CADERA + 0.4,
            etiqueta="tronco erguido, centro de gravedad alto",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            cxm - 1.0,
            _SUELO + 0.2,
            etiqueta="no frena ni cambia el apoyo",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _flecha(
            x_balon_mal + 0.45,
            y_balon,
            cxm + 3.4,
            _SUELO + 0.45,
            tipo="dribble",
            etiqueta="cambio lento y previsible",
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: cambio lento sin frenado"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: baja el centro y sal fuerte"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Regate con cambio de direccion: frenado, engano y salida",
        leyenda=(
            Leyenda(texto="Frenado con la planta", simbolo="circulo resaltado"),
            Leyenda(texto="Engano de hombro y cadera", simbolo="flecha de movimiento"),
            Leyenda(texto="Cambio de direccion del balon", simbolo="flecha ondulada"),
            Leyenda(texto="Salida explosiva", simbolo="flecha de movimiento"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Ilustracion 10: aterrizaje seguro
# --------------------------------------------------------------------------- #
#
# Encuadre obligatorio: esto es **tecnica de salto y caida**, igual que el resto
# del catalogo de ilustraciones. La comparacion senala un error de ejecucion
# frecuente, como se senala golpear con la punta en vez del empeine. La leyenda y
# los rotulos se redactan solo en terminos de gesto tecnico.


def aterrizaje_seguro() -> DiagramaSpec:
    """Aterrizaje seguro despues del salto: alineacion cadera-rodilla-pie.

    Panel correcto: cadera flexionada, rodilla alineada con el pie y la cadera,
    apoyo con toda la planta y linea de alineacion vertical de referencia.

    Panel del error: rodilla que se va hacia adentro y cadera casi sin flexionar,
    el error de ejecucion mas frecuente al caer.
    """
    izq = 0.0
    der = ANCHO_PANEL
    flexion = 42.0
    apertura = 2.0

    # Se reproduce la geometria de la pierna de apoyo de `figura_jugadora` para
    # poder senalar exactamente la rodilla en cada panel.
    y_rodilla = _SUELO + (_Y_CADERA - _SUELO) * 0.52
    desvio_flexion = math.sin(math.radians(flexion)) * 0.55

    # --- Panel correcto -----------------------------------------------------
    cx = izq + ANCHO_PANEL / 2.0
    x_cadera = cx - _SEMI_CADERA
    x_tobillo = x_cadera - apertura / 2.0
    x_rodilla = (x_cadera + x_tobillo) / 2.0 + desvio_flexion

    ok: list[Item] = list(
        figura_jugadora(
            izq,
            flexion_rodilla=flexion,
            valgo=0.0,
            inclinacion_tronco=12.0,
            apertura_pies=apertura,
        )
    )
    ok.append(
        _seg(
            x_tobillo,
            _SUELO,
            x_tobillo,
            _Y_CADERA + 0.3,
            etiqueta="linea de alineacion cadera-rodilla-pie",
        )
    )
    ok.append(
        _circulo_zona(x_tobillo, _SUELO + 0.2, 0.6, etiqueta="apoyo con toda la planta")
    )
    ok.append(
        _marca(x_rodilla, y_rodilla, etiqueta="rodilla alineada con el pie y la cadera")
    )
    ok.append(_marca(cx, _Y_CADERA + 0.35, etiqueta="cadera flexionada"))
    ok.append(
        _flecha(
            cx + 2.4,
            ALTO_PANEL - 1.9,
            cx + 1.2,
            _Y_CADERA + 1.4,
            tipo="run",
            etiqueta="cae del salto",
        )
    )
    ok.append(
        _flecha(
            cx - 3.4,
            _SUELO + 1.7,
            cx - 2.5,
            _SUELO + 0.6,
            tipo="run",
            etiqueta="amortigua flexionando cadera y rodilla",
        )
    )
    ok.append(_texto(cx, _Y_ROTULO_ERROR, "Gesto tecnico de salto y caida"))
    ok.append(_texto(cx, _Y_PIE_PANEL, "Rodilla sobre la punta del pie"))

    # --- Panel del error ----------------------------------------------------
    cxm = der + ANCHO_PANEL / 2.0
    x_cadera_mal = cxm - _SEMI_CADERA
    x_tobillo_mal = x_cadera_mal - apertura / 2.0
    x_rodilla_mal = (
        (x_cadera_mal + x_tobillo_mal) / 2.0
        + desvio_flexion
        + math.radians(22.0) * 2.2
    )

    mal: list[Item] = list(
        figura_jugadora(
            der,
            flexion_rodilla=flexion,
            valgo=22.0,
            inclinacion_tronco=4.0,
            apertura_pies=apertura,
        )
    )
    mal.append(
        _seg(
            x_tobillo_mal,
            _SUELO,
            x_tobillo_mal,
            _Y_CADERA + 0.3,
            etiqueta="linea de alineacion cadera-rodilla-pie",
        )
    )
    mal.append(
        _marca(
            x_rodilla_mal,
            y_rodilla,
            etiqueta="rodilla se va hacia adentro",
            color=paleta.ROJO,
        )
    )
    mal.append(
        _marca(
            cxm,
            _Y_CADERA + 0.35,
            etiqueta="cadera casi sin flexionar",
            color=paleta.ROJO,
        )
    )
    mal.append(_texto(cxm, _Y_ROTULO_ERROR, "Error: rodilla hacia adentro"))
    mal.append(_texto(cxm, _Y_PIE_PANEL, "Corrige: rodilla sobre la punta del pie"))

    return DiagramaSpec(
        clase=ClaseDiagrama.POSTURA,
        mundo=MUNDO_FIGURA,
        items=(
            *panel(izq, ROTULO_CORRECTO, tuple(ok)),
            *panel(der, ROTULO_ERROR, tuple(mal)),
        ),
        titulo="Aterrizaje seguro: rodilla alineada con el pie y la cadera",
        leyenda=(
            Leyenda(texto="Apoyo con toda la planta", simbolo="circulo resaltado"),
            Leyenda(
                texto="Alineacion cadera-rodilla-pie", simbolo="linea vertical de referencia"
            ),
            Leyenda(texto="Cadera flexionada", simbolo="marca en la cadera"),
            Leyenda(texto="Amortiguacion de la caida", simbolo="flecha de movimiento"),
            Leyenda(texto="Error frecuente", simbolo="marca roja con texto"),
        ),
    )


# --------------------------------------------------------------------------- #
# Registro
# --------------------------------------------------------------------------- #

#: Registro de ilustraciones por id estable. Diez ilustraciones de tecnica.
FIGURAS: dict[str, object] = {
    "aterrizaje-seguro": aterrizaje_seguro,
    "bajar-balon-aereo": bajar_balon_aereo,
    "conduccion": conduccion,
    "control-orientado": control_orientado,
    "golpeo-exterior": golpeo_exterior,
    "pase-corto-interior": pase_corto_interior,
    "pase-largo-empeine": pase_largo_empeine,
    "regate-cambio-direccion": regate_cambio_direccion,
    "tiro-colocado-interior": tiro_colocado_interior,
    "tiro-potencia-empeine": tiro_potencia_empeine,
}


def ids_figuras() -> tuple[str, ...]:
    """Ids de las ilustraciones registradas, en orden estable."""
    return tuple(sorted(FIGURAS))


def figura(fid: str) -> DiagramaSpec:
    """Devuelve el `DiagramaSpec` de la ilustracion `fid`.

    Un id inexistente es un error de programacion, no del build: se reporta con
    `ValueError` (nunca con `assert`), igual que `paleta.rgb_pdf` ante un color
    ajeno a la paleta.
    """
    constructor = FIGURAS.get(fid)
    if constructor is None:
        raise ValueError(
            f"ilustracion desconocida: {fid!r}; disponibles: {ids_figuras()}"
        )
    return constructor()  # type: ignore[operator]


def todas_las_figuras() -> tuple[DiagramaSpec, ...]:
    """Construye todas las ilustraciones registradas."""
    return tuple(figura(fid) for fid in ids_figuras())


def contar_posturas() -> int:
    """Cuenta las ilustraciones de clase POSTURA registradas.

    Ojo: esto cuenta el **catalogo de ilustraciones**, no las fichas que la
    llevan. El reporte del build publica como `posturas` el numero de fichas con
    `postura` distinta de None, que es lo que resuelve `para_ficha`.
    """
    return sum(
        1 for spec in todas_las_figuras() if spec.clase is ClaseDiagrama.POSTURA
    )


# --------------------------------------------------------------------------- #
# Mapeo tecnica -> ilustracion
# --------------------------------------------------------------------------- #
#
# El adaptador `schema_json.ficha_json_a_ficha` llama a `para_ficha(...)` para
# colgar la ilustracion correspondiente de cada Ficha_JSON. El mapeo se hace por
# palabras clave del titulo y del id, no por numero de ficha: asi sigue valiendo
# si el catalogo se reordena.

#: Reglas de mapeo: (id_figura, palabras que deben aparecer todas juntas).
#: Se evalua en orden y gana la primera regla que coincide.
#:
#: El orden importa y esta pensado contra el catalogo real. Dos ejemplos de por
#: que las reglas no son ingenuas:
#:
#: * la ficha de golpeo con el exterior tambien dice "pase" y "conduccion", asi
#:   que su regla va antes que la de conduccion;
#: * una regla suelta de "regate" tambien casaria con "sin regatear" de otra
#:   ficha, asi que se exige ademas "direccion".
#:
#: Las palabras van sin acento porque el `id` en kebab-case siempre los pierde y
#: es la parte mas estable del texto de la ficha.
REGLAS_FIGURA: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Tecnica de salto y caida.
    ("aterrizaje-seguro", ("aterrizaje",)),
    # Golpeo con el exterior: antes que conduccion, porque su ficha dice ambas.
    ("golpeo-exterior", ("golpeo", "exterior")),
    # Tiro colocado: precision antes que potencia.
    ("tiro-colocado-interior", ("tiro", "colocado")),
    ("tiro-colocado-interior", ("tiro", "media")),
    # Tiro de potencia.
    ("tiro-potencia-empeine", ("tiro", "potencia")),
    ("tiro-potencia-empeine", ("empeine", "potencia")),
    # Pase largo.
    ("pase-largo-empeine", ("pase", "largo")),
    # Control y recepcion.
    ("control-orientado", ("control", "orientado")),
    ("bajar-balon-aereo", ("bajar", "balon")),
    # Regate y cambio de direccion.
    ("regate-cambio-direccion", ("regate", "direccion")),
    ("regate-cambio-direccion", ("finta",)),
    # Conduccion.
    ("conduccion", ("conduccion",)),
    # Pase corto con interior (lote 1).
    ("pase-corto-interior", ("pase", "interior")),
    ("pase-corto-interior", ("pase", "corto")),
    ("pase-corto-interior", ("postura", "pasar")),
)


def _texto_de_ficha(ficha: object) -> str:
    """Texto en minusculas donde buscar las palabras clave del mapeo.

    Acepta tanto una Ficha_JSON (`dict`) como una `FichaEjercicio`, para que la
    funcion sirva desde el adaptador y desde una prueba.
    """
    if isinstance(ficha, dict):
        partes = [
            str(ficha.get("id") or ""),
            str(ficha.get("titulo") or ""),
            str(ficha.get("subtitulo") or ""),
            str(ficha.get("categoria") or ""),
        ]
    else:
        partes = [
            str(getattr(ficha, "id", "") or ""),
            str(getattr(ficha, "titulo", "") or ""),
            str(getattr(ficha, "subtitulo", "") or ""),
            str(getattr(ficha, "categoria", "") or ""),
        ]
    return " ".join(partes).lower()


def id_figura_para(ficha: object) -> str | None:
    """Id de la ilustracion que corresponde a `ficha`, o `None` si ninguna.

    Devolver `None` es un resultado legitimo: no toda ficha es de golpeo, y no
    se le cuelga una ilustracion que no le toca.
    """
    texto = _texto_de_ficha(ficha)
    for fid, palabras in REGLAS_FIGURA:
        if all(palabra in texto for palabra in palabras):
            return fid
    return None


def para_ficha(ficha: object) -> DiagramaSpec | None:
    """Ilustracion de tecnica que corresponde a `ficha`, o `None`.

    Es el punto de entrada que usa el adaptador Ficha_JSON -> FichaEjercicio.
    """
    fid = id_figura_para(ficha)
    return None if fid is None else figura(fid)
