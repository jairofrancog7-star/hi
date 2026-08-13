"""Mundo_Hero: los Elemento_Fondo del hero, su matematica y su emision.

Modulo del bloque 8 de la feature `imagenes-reales-hero-interactivo`. Su
trabajo, en cuatro piezas bien separadas:

1. **Declarar** los Elemento_Fondo (catalogo congelado de la tabla del diseno,
   mas `silueta-3` que anade la ampliacion), las Figura_Girable del hero y el
   Eje_Giro_Inclinado de cada Balon_Esfera.
2. **La matematica**, en funciones puras y sin estado: el Progreso_Scroll, el
   desplazamiento de parallax por capa, la escala, el desvanecimiento, el
   desplazamiento por cursor con su interpolacion y la resolucion del balon mas
   cercano al toque. Que sean puras es lo que hace que la reversibilidad del
   criterio 8.6 salga **por construccion** y no por un ajuste.
3. **La emision**: el SVG en linea de cada Elemento_Fondo, la capa `.hero-mundo`
   con sus tres Capa_Parallax y el bloque CSS del mundo.
4. **La serializacion**: `datos_json()`, el unico puente hacia el JavaScript. El
   Script_Unico no repite ninguna constante a mano; las lee de este literal.

Python es la fuente de verdad de todos los numeros. Ninguna constante de este
modulo se vuelve a escribir en el CSS ni en el JavaScript: el CSS las recibe como
variables en linea (`--vaiven`, `--amplitud`, `--giro`, `--vuelta`, `--retraso`,
`--eje`, `--z-figura`) y el JavaScript como el literal JSON de `datos_json()`.

Reglas del proyecto: Python 3.11+, solo libreria estandar y **ningun `assert`**
(todo invariante con `raise ErrorAsset(..., codigo=E_ASSET_INVALIDO)`, para que
`python -O` no borre ningun guardarrail).

_Requirements: 6.8, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4,
8.5, 8.6, 8.7, 8.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8, 10.1, 10.2, 10.6, 10.10,
11.1, 11.2, 11.3, 12.1, 12.4, 12.5, 12.6, 12.7, 22.1, 22.4, 25.1, 25.2, 25.3,
25.4, 25.5, 25.10, 25.14, 25.15, 25.16, 26.1, 26.2, 26.3, 26.4, 26.5, 26.6,
26.7, 26.8, 26.9, 26.10, 26.11, 27.1, 27.2, 27.7, 28.2, 28.9, 28.11_
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from . import diagramas_postura as dp
from . import svg_postura as sp
from . import vistas_figura as vf
from .errores import E_ASSET_INVALIDO, ErrorAsset

__all__ = [
    "ALT_SILUETA",
    "ANGULOS_GAJO",
    "CAPAS",
    "CAPA_CERCANA",
    "CAPA_LEJANA",
    "CAPA_MEDIA",
    "CLASE_BALON",
    "CLASE_CAPA",
    "CLASE_GAJO",
    "CLASE_GAJO_SOMBREADO",
    "CLASE_GIRO",
    "CLASE_MUNDO",
    "CLASE_OBJETO",
    "CLASE_INERTE",
    "CLASE_SOMBRA",
    "CORTE_ANGOSTO_PX",
    "CORTE_ANGOSTO_REM",
    "CUADRANTES",
    "EJES_BALON",
    "ELEMENTOS",
    "ELEMENTOS_ANGOSTO",
    "ESCALA_FINAL",
    "ElementoFondo",
    "FACTOR_PARALLAX",
    "FIGURAS_GIRABLES",
    "FiguraGirable",
    "GAJOS",
    "GAJO_SOMBREADO",
    "ID_MUNDO",
    "INCLINACION_MAX",
    "INCLINACION_MIN",
    "ORIGEN_DIAGRAMA",
    "ORIGEN_FONDO",
    "PERSPECTIVA_PX",
    "RADIO_TOQUE_PCT",
    "REBOTE_MS",
    "SUAVIZADO_CURSOR",
    "TIPOS",
    "TIPOS_EXIGIDOS",
    "TIPO_ARCO",
    "TIPO_BALON",
    "TIPO_CONO",
    "TIPO_COPA",
    "TIPO_LINEA",
    "TIPO_PORTERIA",
    "TIPO_SILBATO",
    "TIPO_SILUETA",
    "TIPO_TACO",
    "TOPE_CURSOR_PX",
    "TRANSICION_REAPARICION_MS",
    "TRANSICION_VISTA_MS",
    "TRASLADO_Z_PX",
    "VAIVEN_PX_MAX",
    "VAIVEN_PX_MIN",
    "VAIVEN_S_MAX",
    "VAIVEN_S_MIN",
    "VUELTA_FIGURA_MAX",
    "VUELTA_FIGURA_MIN",
    "activos_angostos",
    "balon_mas_cercano",
    "balones",
    "bloque_css",
    "css_balon_esfera",
    "css_figura_girable",
    "css_impresion",
    "css_reduccion_cuerpo",
    "css_sin_modos",
    "cuadrante_de",
    "cursor_objetivo",
    "datos_json",
    "datos_mundo",
    "desplazamiento",
    "diagrama_de_figura",
    "eje_css",
    "eje_de",
    "elemento_de",
    "escala",
    "figura_girable_de",
    "figuras_de_capa",
    "id_de_capa",
    "inclinacion_eje",
    "inerte",
    "marcado_girable",
    "marcado_mundo",
    "marcado_objeto",
    "opacidad",
    "por_capa",
    "por_tipo",
    "pose_de_figura",
    "profundidad",
    "progreso",
    "render_mundo",
    "siluetas_girables",
    "suavizar",
    "svg_balon_esfera",
    "svg_elemento",
    "validar_elementos",
]


# --------------------------------------------------------------------------- #
# Las tres capas y sus constantes de movimiento
# --------------------------------------------------------------------------- #

CAPA_LEJANA: str = "lejana"
CAPA_MEDIA: str = "media"
CAPA_CERCANA: str = "cercana"

#: Las tres capas, en el orden **lejana, media, cercana**. Ese orden es el de los
#: arreglos de `datos_json()` y el que el JavaScript resuelve por indice, asi que
#: no se reordena nunca (criterio 8.1).
CAPAS: tuple[str, ...] = (CAPA_LEJANA, CAPA_MEDIA, CAPA_CERCANA)

#: Factor de desplazamiento vertical de cada capa (criterio 8.2). El orden
#: `0.15 < 0.40 < 0.70` es lo que garantiza el orden de velocidades del criterio
#: 8.7 sin que ninguna prueba tenga que mirar el CSS.
FACTOR_PARALLAX: dict[str, float] = {
    CAPA_LEJANA: 0.15,
    CAPA_MEDIA: 0.40,
    CAPA_CERCANA: 0.70,
}

#: Escala que alcanza cada capa con Progreso_Scroll 1 (criterio 8.3): la cercana
#: crece un 25 % y la lejana se encoge un 15 %, que es lo que da la sensacion de
#: entrar en el plano.
ESCALA_FINAL: dict[str, float] = {
    CAPA_LEJANA: 0.85,
    CAPA_MEDIA: 1.00,
    CAPA_CERCANA: 1.25,
}

#: `translateZ` propio de cada capa, en pixeles (criterio 8.8). El orden
#: `-320 < -160 < -40` pone la lejana al fondo del espacio en perspectiva.
TRASLADO_Z_PX: dict[str, float] = {
    CAPA_LEJANA: -320.0,
    CAPA_MEDIA: -160.0,
    CAPA_CERCANA: -40.0,
}

#: Tope del desplazamiento por cursor, en pixeles y por eje (criterio 9.4).
TOPE_CURSOR_PX: float = 20.0

#: Coeficiente de interpolacion del desplazamiento por cursor, por fotograma
#: (criterio 9.5).
SUAVIZADO_CURSOR: float = 0.08

#: Ancho de ventana por debajo del cual el hero entra en pantalla angosta, en
#: pixeles (Requisito 12).
CORTE_ANGOSTO_PX: int = 768

#: Numero minimo y maximo de Elemento_Fondo activos en pantalla angosta
#: (criterio 12.1).
ELEMENTOS_ANGOSTO: tuple[int, int] = (5, 7)

#: Radio de captura del toque, en porcentaje del hero (criterio 9.8).
RADIO_TOQUE_PCT: float = 18.0

#: Duracion del rebote y del giro acelerado del toque, en milisegundos
#: (criterio 9.8).
REBOTE_MS: int = 900

#: Perspectiva del espacio del Mundo_Hero, en pixeles (criterio 6.8).
PERSPECTIVA_PX: int = 1000


# --------------------------------------------------------------------------- #
# Tipos de Elemento_Fondo
# --------------------------------------------------------------------------- #

TIPO_BALON: str = "balon"
TIPO_SILUETA: str = "silueta"
TIPO_PORTERIA: str = "porteria"
TIPO_CONO: str = "cono"
TIPO_LINEA: str = "linea"
TIPO_SILBATO: str = "silbato"
TIPO_COPA: str = "copa"
TIPO_TACO: str = "taco"
TIPO_ARCO: str = "arco"

#: Los nueve tipos de Elemento_Fondo, en orden declarado.
TIPOS: tuple[str, ...] = (
    TIPO_BALON,
    TIPO_SILUETA,
    TIPO_PORTERIA,
    TIPO_CONO,
    TIPO_LINEA,
    TIPO_SILBATO,
    TIPO_COPA,
    TIPO_TACO,
    TIPO_ARCO,
)

#: Los seis tipos que el criterio 7.4 exige que aparezcan al menos una vez.
TIPOS_EXIGIDOS: tuple[str, ...] = (
    TIPO_PORTERIA,
    TIPO_CONO,
    TIPO_LINEA,
    TIPO_SILBATO,
    TIPO_COPA,
    TIPO_TACO,
)

#: Los cuatro cuadrantes del hero, en orden declarado (criterio 7.5).
CUADRANTES: tuple[str, ...] = (
    "superior-izquierdo",
    "superior-derecho",
    "inferior-izquierdo",
    "inferior-derecho",
)

#: Rangos declarados del vaiven (criterios 9.1 y 9.3).
VAIVEN_PX_MIN: float = 8.0
VAIVEN_PX_MAX: float = 20.0
VAIVEN_S_MIN: float = 5.0
VAIVEN_S_MAX: float = 9.0

#: Rango declarado de la duracion de vuelta de un Balon_Esfera, en segundos
#: (criterios 7.6 y 26.7).
VUELTA_BALON_MIN: float = 14.0
VUELTA_BALON_MAX: float = 26.0

#: Cotas de los conteos del catalogo (criterios 7.1, 7.2 y 7.3).
TOTAL_MIN: int = 8
TOTAL_MAX: int = 14
BALONES_MIN: int = 3
BALONES_MAX: int = 5
SILUETAS_MIN: int = 2
SILUETAS_MAX: int = 3
OPACIDAD_SILUETA_MIN: float = 0.25
OPACIDAD_SILUETA_MAX: float = 0.45


# --------------------------------------------------------------------------- #
# Elemento_Fondo
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ElementoFondo:
    """Un objeto del fondo del hero.

    `x_pct` y `y_pct` son el **centro** del elemento en porcentaje del hero, y
    `ancho_pct` su ancho como porcentaje del hero: son posicion inicial estatica,
    nunca animada (criterios 10.1 y 10.2).

    `giro_s` y `sentido` valen 0 en los elementos que no giran; los que giran son
    los de tipo balon, cuyo Balon_Esfera recorre una vuelta completa alrededor de
    su Eje_Giro_Inclinado (criterios 7.6 y 7.7).

    `angosto` marca el subconjunto que sobrevive por debajo de
    `CORTE_ANGOSTO_PX` (criterios 12.1 y 12.4).
    """

    id: str
    tipo: str
    capa: str
    x_pct: float
    y_pct: float
    ancho_pct: float
    opacidad: float
    giro_s: float
    sentido: int
    vaiven_px: float
    vaiven_s: float
    retraso_s: float
    angosto: bool


#: Catalogo de Elemento_Fondo del Mundo_Hero.
#:
#: Las trece primeras filas son la tabla **congelada** del diseno y ninguna
#: cambia. La ampliacion **anade** `silueta-3` (Capa_Cercana, x 62 %, y 52 %,
#: ancho 19 %, opacidad 0.31, vaiven 17 px / 6.6 s / retraso 1.8 s, marcada
#: `angosto`), de modo que el total pasa a **14 Elemento_Fondo y 3 siluetas**, los
#: dos dentro de los rangos que la Property 25 verifica (8-14 elementos y 2-3
#: siluetas con opacidad en [0.25, 0.45]).
#:
#: `silueta-3` se coloca **detras de `silueta-2`** a proposito: asi los retrasos
#: de las tres siluetas consecutivas (0.3, 1.1 y 1.8 s) siguen siendo distintos
#: entre elementos contiguos del mismo tipo (criterio 9.2). El orden de la tupla
#: es tambien el orden de emision y el que rompe los empates de
#: `balon_mas_cercano`, asi que no se reordena.
ELEMENTOS: tuple[ElementoFondo, ...] = (
    ElementoFondo(
        id="arco-1",
        tipo=TIPO_ARCO,
        capa=CAPA_LEJANA,
        x_pct=12.0,
        y_pct=16.0,
        ancho_pct=26.0,
        opacidad=0.16,
        giro_s=0.0,
        sentido=0,
        vaiven_px=10.0,
        vaiven_s=8.5,
        retraso_s=0.0,
        angosto=False,
    ),
    ElementoFondo(
        id="linea-1",
        tipo=TIPO_LINEA,
        capa=CAPA_LEJANA,
        x_pct=78.0,
        y_pct=22.0,
        ancho_pct=30.0,
        opacidad=0.14,
        giro_s=0.0,
        sentido=0,
        vaiven_px=9.0,
        vaiven_s=9.0,
        retraso_s=1.2,
        angosto=False,
    ),
    ElementoFondo(
        id="arco-2",
        tipo=TIPO_ARCO,
        capa=CAPA_LEJANA,
        x_pct=60.0,
        y_pct=82.0,
        ancho_pct=24.0,
        opacidad=0.15,
        giro_s=0.0,
        sentido=0,
        vaiven_px=8.0,
        vaiven_s=8.0,
        retraso_s=2.1,
        angosto=False,
    ),
    ElementoFondo(
        id="porteria-1",
        tipo=TIPO_PORTERIA,
        capa=CAPA_LEJANA,
        x_pct=22.0,
        y_pct=78.0,
        ancho_pct=28.0,
        opacidad=0.20,
        giro_s=0.0,
        sentido=0,
        vaiven_px=11.0,
        vaiven_s=7.5,
        retraso_s=0.8,
        angosto=True,
    ),
    ElementoFondo(
        id="balon-1",
        tipo=TIPO_BALON,
        capa=CAPA_MEDIA,
        x_pct=18.0,
        y_pct=34.0,
        ancho_pct=12.0,
        opacidad=0.55,
        giro_s=16.0,
        sentido=1,
        vaiven_px=14.0,
        vaiven_s=6.0,
        retraso_s=0.0,
        angosto=True,
    ),
    ElementoFondo(
        id="balon-2",
        tipo=TIPO_BALON,
        capa=CAPA_MEDIA,
        x_pct=84.0,
        y_pct=44.0,
        ancho_pct=9.0,
        opacidad=0.45,
        giro_s=21.0,
        sentido=-1,
        vaiven_px=12.0,
        vaiven_s=7.0,
        retraso_s=1.5,
        angosto=True,
    ),
    ElementoFondo(
        id="balon-3",
        tipo=TIPO_BALON,
        capa=CAPA_MEDIA,
        x_pct=46.0,
        y_pct=88.0,
        ancho_pct=10.0,
        opacidad=0.50,
        giro_s=25.0,
        sentido=1,
        vaiven_px=16.0,
        vaiven_s=6.5,
        retraso_s=2.6,
        angosto=False,
    ),
    ElementoFondo(
        id="cono-1",
        tipo=TIPO_CONO,
        capa=CAPA_MEDIA,
        x_pct=8.0,
        y_pct=62.0,
        ancho_pct=8.0,
        opacidad=0.40,
        giro_s=0.0,
        sentido=0,
        vaiven_px=13.0,
        vaiven_s=5.5,
        retraso_s=0.6,
        angosto=True,
    ),
    ElementoFondo(
        id="silbato-1",
        tipo=TIPO_SILBATO,
        capa=CAPA_MEDIA,
        x_pct=70.0,
        y_pct=12.0,
        ancho_pct=8.0,
        opacidad=0.35,
        giro_s=0.0,
        sentido=0,
        vaiven_px=10.0,
        vaiven_s=6.8,
        retraso_s=1.9,
        angosto=False,
    ),
    ElementoFondo(
        id="taco-1",
        tipo=TIPO_TACO,
        capa=CAPA_MEDIA,
        x_pct=90.0,
        y_pct=74.0,
        ancho_pct=11.0,
        opacidad=0.35,
        giro_s=0.0,
        sentido=0,
        vaiven_px=12.0,
        vaiven_s=7.2,
        retraso_s=3.0,
        angosto=False,
    ),
    ElementoFondo(
        id="silueta-1",
        tipo=TIPO_SILUETA,
        capa=CAPA_CERCANA,
        x_pct=30.0,
        y_pct=58.0,
        ancho_pct=20.0,
        opacidad=0.34,
        giro_s=0.0,
        sentido=0,
        vaiven_px=18.0,
        vaiven_s=5.0,
        retraso_s=0.3,
        angosto=True,
    ),
    ElementoFondo(
        id="silueta-2",
        tipo=TIPO_SILUETA,
        capa=CAPA_CERCANA,
        x_pct=76.0,
        y_pct=64.0,
        ancho_pct=18.0,
        opacidad=0.28,
        giro_s=0.0,
        sentido=0,
        vaiven_px=20.0,
        vaiven_s=5.8,
        retraso_s=1.1,
        angosto=True,
    ),
    ElementoFondo(
        id="silueta-3",
        tipo=TIPO_SILUETA,
        capa=CAPA_CERCANA,
        x_pct=62.0,
        y_pct=52.0,
        ancho_pct=19.0,
        opacidad=0.31,
        giro_s=0.0,
        sentido=0,
        vaiven_px=17.0,
        vaiven_s=6.6,
        retraso_s=1.8,
        angosto=True,
    ),
    ElementoFondo(
        id="copa-1",
        tipo=TIPO_COPA,
        capa=CAPA_CERCANA,
        x_pct=54.0,
        y_pct=24.0,
        ancho_pct=9.0,
        opacidad=0.30,
        giro_s=0.0,
        sentido=0,
        vaiven_px=15.0,
        vaiven_s=6.2,
        retraso_s=2.4,
        angosto=False,
    ),
)


# --------------------------------------------------------------------------- #
# Consultas del catalogo
# --------------------------------------------------------------------------- #


def _capa_declarada(capa: str) -> str:
    """Devuelve `capa` si pertenece a las tres declaradas; si no, falla."""
    if capa not in FACTOR_PARALLAX:
        raise ErrorAsset(
            f"capa desconocida: {capa!r}; las declaradas son {CAPAS}",
            detalle={"capa": capa},
            codigo=E_ASSET_INVALIDO,
        )
    return capa


def _acotar(valor: float, minimo: float, maximo: float) -> float:
    """Acota `valor` al intervalo cerrado `[minimo, maximo]`."""
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor


def progreso(scroll_y: float, alto_ventana: float) -> float:
    """Progreso_Scroll del hero, acotado a `[0, 1]` (criterios 8.4 y 8.5).

    Es el cociente entre el desplazamiento vertical y el alto de la ventana,
    recortado a los dos lados. Con un alto no positivo (una ventana que todavia
    no se ha medido) devuelve 0, que es el estado de reposo: el fondo se ve
    entero y nada esta desvanecido.
    """
    if alto_ventana <= 0.0:
        return 0.0
    return _acotar(scroll_y / alto_ventana, 0.0, 1.0)


def desplazamiento(capa: str, scroll_y: float) -> float:
    """Desplazamiento vertical de `capa` para `scroll_y`, en pixeles.

    Es `-scroll_y * FACTOR_PARALLAX[capa]`: la capa se mueve **en contra** del
    desplazamiento de la pagina y lo hace mas despacio, que es lo que produce la
    sensacion de profundidad. El signo negativo comun a las tres deja intacto el
    orden de magnitudes del criterio 8.7.
    """
    return -scroll_y * FACTOR_PARALLAX[_capa_declarada(capa)]


def escala(capa: str, p: float) -> float:
    """Escala de `capa` con Progreso_Scroll `p` (criterio 8.3).

    `1 + (ESCALA_FINAL[capa] - 1) * p`, es decir `1 + 0.25p` en la Capa_Cercana y
    `1 - 0.15p` en la Capa_Lejana. Es una interpolacion lineal pura, sin recorte:
    `p` ya viene acotado por `progreso`, y dejarla sin acotar mantiene la formula
    del diseno tal cual y hace que la reversibilidad sea trivial.
    """
    return 1.0 + (ESCALA_FINAL[_capa_declarada(capa)] - 1.0) * p


def opacidad(p: float) -> float:
    """Opacidad de todo Elemento_Fondo con Progreso_Scroll `p` (criterios 8.4, 8.5).

    `1 - p` acotado a `[0, 1]`: vale exactamente 0 con `p` de 1 o mas y
    exactamente 1 con `p` de 0 o menos.
    """
    return _acotar(1.0 - p, 0.0, 1.0)


def profundidad(capa: str) -> float:
    """`translateZ` declarado de `capa`, en pixeles (criterio 8.8)."""
    return TRASLADO_Z_PX[_capa_declarada(capa)]


# --------------------------------------------------------------------------- #
# Desplazamiento por cursor y su interpolacion
# --------------------------------------------------------------------------- #


def _componente_cursor(relativa: float) -> float:
    """Componente del desplazamiento objetivo para una posicion relativa.

    Signo **opuesto** al de la posicion del cursor, porque el fondo se aparta del
    puntero, y modulo acotado a `TOPE_CURSOR_PX`: una posicion relativa fuera del
    hero (modulo mayor que 1) satura en el tope en vez de dispararse.
    """
    return _acotar(-relativa * TOPE_CURSOR_PX, -TOPE_CURSOR_PX, TOPE_CURSOR_PX)


def cursor_objetivo(rel_x: float, rel_y: float) -> tuple[float, float]:
    """Desplazamiento objetivo del fondo para el cursor en `(rel_x, rel_y)`.

    `rel_x` y `rel_y` son la posicion del cursor dentro del hero en `[-1, 1]`, con
    el centro en `(0, 0)`. El resultado es
    `(-rel_x * TOPE_CURSOR_PX, -rel_y * TOPE_CURSOR_PX)` con cada componente
    acotada a 20 px (criterio 9.4). Al salir del hero el objetivo pasa a ser
    `(0, 0)` y la misma interpolacion lo devuelve al centro (criterio 9.6).
    """
    return (_componente_cursor(rel_x), _componente_cursor(rel_y))


def suavizar(actual: float, objetivo: float) -> float:
    """Un paso de la interpolacion del desplazamiento por cursor (criterio 9.5).

    `actual + (objetivo - actual) * SUAVIZADO_CURSOR`, con el coeficiente 0.08 por
    fotograma. Con un coeficiente en `(0, 1)` la sucesion se acerca al objetivo de
    forma estrictamente monotona y **nunca lo sobrepasa**, asi que sirve igual
    para perseguir un objetivo nuevo y para volver al cero de la salida del hero.
    """
    return actual + (objetivo - actual) * SUAVIZADO_CURSOR


def elemento_de(id_: str) -> ElementoFondo:
    """Elemento_Fondo con identificador `id_`."""
    for elemento in ELEMENTOS:
        if elemento.id == id_:
            return elemento
    raise ErrorAsset(
        f"Elemento_Fondo desconocido: {id_!r}",
        detalle={"id": id_},
        codigo=E_ASSET_INVALIDO,
    )


def por_tipo(tipo: str) -> tuple[ElementoFondo, ...]:
    """Elemento_Fondo de `tipo`, en el orden del catalogo."""
    return tuple(e for e in ELEMENTOS if e.tipo == tipo)


def por_capa(capa: str) -> tuple[ElementoFondo, ...]:
    """Elemento_Fondo de `capa`, en el orden del catalogo."""
    return tuple(e for e in ELEMENTOS if e.capa == capa)


def balones() -> tuple[ElementoFondo, ...]:
    """Los Elemento_Fondo de tipo balon, en el orden del catalogo."""
    return por_tipo(TIPO_BALON)


def cuadrante_de(elemento: ElementoFondo) -> str:
    """Cuadrante del hero donde cae el centro de `elemento` (criterio 7.5)."""
    arriba: bool = elemento.y_pct < 50.0
    izquierda: bool = elemento.x_pct < 50.0
    if arriba and izquierda:
        return CUADRANTES[0]
    if arriba:
        return CUADRANTES[1]
    if izquierda:
        return CUADRANTES[2]
    return CUADRANTES[3]


def balon_mas_cercano(x_pct: float, y_pct: float) -> str | None:
    """Identificador del Balon_Esfera mas cercano a `(x_pct, y_pct)`, o `None`.

    Funcion **pura sobre las coordenadas declaradas del catalogo**: no lee
    geometria del DOM ni recibe medida alguna del navegador (criterios 9.8 y
    10.14). El punto llega en porcentaje del hero, igual que las coordenadas
    declaradas, asi que la distancia euclidea se mide en la misma unidad.

    Devuelve el balon que minimiza la distancia siempre que esa distancia no pase
    de `RADIO_TOQUE_PCT`; si ningun balon cae dentro del radio devuelve `None`, y
    nunca devuelve un elemento que no sea de tipo balon. Los empates se rompen por
    el **orden del catalogo** (comparacion estricta, asi que gana el primero), de
    modo que el resultado sea deterministico.
    """
    mejor: str | None = None
    menor: float | None = None
    for elemento in ELEMENTOS:
        if elemento.tipo != TIPO_BALON:
            continue
        distancia: float = math.hypot(
            x_pct - elemento.x_pct, y_pct - elemento.y_pct
        )
        if distancia > RADIO_TOQUE_PCT:
            continue
        if menor is None or distancia < menor:
            mejor = elemento.id
            menor = distancia
    return mejor


def activos_angostos() -> tuple[str, ...]:
    """Identificadores del subconjunto de pantalla angosta (criterios 12.1, 12.5).

    Son los Elemento_Fondo marcados `angosto`, en el orden del catalogo. Su
    numero cae dentro de `ELEMENTOS_ANGOSTO`, que es la ventana de 5 a 7 que el
    JavaScript respeta al reducir carga: la reduccion toca **solo** el numero de
    Elemento_Fondo activos y jamas las dimensiones de un Diagrama_Postura.
    """
    return tuple(e.id for e in ELEMENTOS if e.angosto)


# --------------------------------------------------------------------------- #
# Validador del catalogo
# --------------------------------------------------------------------------- #


def _fallo(mensaje: str, detalle: dict[str, object]) -> ErrorAsset:
    """Construye el `ErrorAsset` de un invariante del Mundo_Hero."""
    return ErrorAsset(mensaje, detalle=detalle, codigo=E_ASSET_INVALIDO)


def _validar_conteos() -> None:
    """Conteos y cotas del catalogo (criterios 7.1, 7.2, 7.3 y 12.1)."""
    total: int = len(ELEMENTOS)
    if not TOTAL_MIN <= total <= TOTAL_MAX:
        raise _fallo(
            f"el Mundo_Hero declara {total} Elemento_Fondo y el rango es "
            f"[{TOTAL_MIN}, {TOTAL_MAX}]",
            {"total": total},
        )
    cuantos_balones: int = len(balones())
    if not BALONES_MIN <= cuantos_balones <= BALONES_MAX:
        raise _fallo(
            f"el Mundo_Hero declara {cuantos_balones} Elemento_Fondo de tipo "
            f"balon y el rango es [{BALONES_MIN}, {BALONES_MAX}]",
            {"balones": cuantos_balones},
        )
    siluetas: tuple[ElementoFondo, ...] = por_tipo(TIPO_SILUETA)
    if not SILUETAS_MIN <= len(siluetas) <= SILUETAS_MAX:
        raise _fallo(
            f"el Mundo_Hero declara {len(siluetas)} Elemento_Fondo de tipo "
            f"silueta y el rango es [{SILUETAS_MIN}, {SILUETAS_MAX}]",
            {"siluetas": len(siluetas)},
        )
    for silueta in siluetas:
        if not OPACIDAD_SILUETA_MIN <= silueta.opacidad <= OPACIDAD_SILUETA_MAX:
            raise _fallo(
                f"la silueta {silueta.id!r} declara opacidad "
                f"{silueta.opacidad} y el rango es "
                f"[{OPACIDAD_SILUETA_MIN}, {OPACIDAD_SILUETA_MAX}]",
                {"id": silueta.id, "opacidad": silueta.opacidad},
            )
    angostos: tuple[str, ...] = activos_angostos()
    minimo, maximo = ELEMENTOS_ANGOSTO
    if not minimo <= len(angostos) <= maximo:
        raise _fallo(
            f"el Mundo_Hero marca {len(angostos)} Elemento_Fondo para pantalla "
            f"angosta y el rango es [{minimo}, {maximo}]: {angostos}",
            {"angostos": angostos},
        )


def _validar_cobertura() -> None:
    """Cobertura de tipos y de cuadrantes (criterios 7.4 y 7.5)."""
    for tipo in TIPOS_EXIGIDOS:
        if not por_tipo(tipo):
            raise _fallo(
                f"el Mundo_Hero no declara ningun Elemento_Fondo de tipo "
                f"{tipo!r}, y el criterio 7.4 exige al menos uno",
                {"tipo": tipo},
            )
    cubiertos: list[str] = []
    for elemento in ELEMENTOS:
        cuadrante: str = cuadrante_de(elemento)
        if cuadrante not in cubiertos:
            cubiertos.append(cuadrante)
    for cuadrante in CUADRANTES:
        if cuadrante not in cubiertos:
            raise _fallo(
                f"ningun Elemento_Fondo tiene su centro en el cuadrante "
                f"{cuadrante!r}",
                {"cuadrante": cuadrante},
            )


def _validar_cada_elemento() -> None:
    """Identificador, capa, coordenadas, ancho y opacidad de cada elemento."""
    vistos: list[str] = []
    for elemento in ELEMENTOS:
        if elemento.id in vistos:
            raise _fallo(
                f"el identificador {elemento.id!r} se repite en el catalogo",
                {"id": elemento.id},
            )
        vistos.append(elemento.id)
        if elemento.tipo not in TIPOS:
            raise _fallo(
                f"{elemento.id!r} declara el tipo {elemento.tipo!r}, que no "
                f"pertenece a los declarados {TIPOS}",
                {"id": elemento.id, "tipo": elemento.tipo},
            )
        if elemento.capa not in CAPAS:
            raise _fallo(
                f"{elemento.id!r} declara la capa {elemento.capa!r}, que no "
                f"pertenece a las tres declaradas {CAPAS}",
                {"id": elemento.id, "capa": elemento.capa},
            )
        for nombre, valor in (("x_pct", elemento.x_pct), ("y_pct", elemento.y_pct)):
            if not 0.0 <= valor <= 100.0:
                raise _fallo(
                    f"{elemento.id!r} declara {nombre}={valor} y el hero mide "
                    "de 0 a 100 por ciento",
                    {"id": elemento.id, nombre: valor},
                )
        if elemento.ancho_pct <= 0.0:
            raise _fallo(
                f"{elemento.id!r} declara un ancho de {elemento.ancho_pct} por "
                "ciento y debe ser positivo",
                {"id": elemento.id, "ancho_pct": elemento.ancho_pct},
            )
        if not 0.0 < elemento.opacidad <= 1.0:
            raise _fallo(
                f"{elemento.id!r} declara opacidad {elemento.opacidad} y debe "
                "vivir en (0, 1]",
                {"id": elemento.id, "opacidad": elemento.opacidad},
            )


def _validar_vaiven() -> None:
    """Amplitud, duracion y retrasos del vaiven (criterios 9.1, 9.2 y 9.3)."""
    for elemento in ELEMENTOS:
        if not VAIVEN_PX_MIN <= elemento.vaiven_px <= VAIVEN_PX_MAX:
            raise _fallo(
                f"{elemento.id!r} declara un vaiven de {elemento.vaiven_px} px "
                f"y el rango es [{VAIVEN_PX_MIN}, {VAIVEN_PX_MAX}]",
                {"id": elemento.id, "vaiven_px": elemento.vaiven_px},
            )
        if not VAIVEN_S_MIN <= elemento.vaiven_s <= VAIVEN_S_MAX:
            raise _fallo(
                f"{elemento.id!r} declara un vaiven de {elemento.vaiven_s} s y "
                f"el rango es [{VAIVEN_S_MIN}, {VAIVEN_S_MAX}]",
                {"id": elemento.id, "vaiven_s": elemento.vaiven_s},
            )
        if elemento.retraso_s < 0.0:
            raise _fallo(
                f"{elemento.id!r} declara un retraso negativo de "
                f"{elemento.retraso_s} s",
                {"id": elemento.id, "retraso_s": elemento.retraso_s},
            )

    # Retrasos distintos entre Elemento_Fondo **consecutivos del mismo tipo**
    # (criterio 9.2): asi dos objetos iguales no laten al unisono.
    for tipo in TIPOS:
        del_tipo: tuple[ElementoFondo, ...] = por_tipo(tipo)
        for anterior, siguiente in zip(del_tipo, del_tipo[1:]):
            if anterior.retraso_s == siguiente.retraso_s:
                raise _fallo(
                    f"{anterior.id!r} y {siguiente.id!r} son del mismo tipo "
                    f"{tipo!r} y consecutivos, y comparten el retraso "
                    f"{anterior.retraso_s} s",
                    {
                        "tipo": tipo,
                        "anterior": anterior.id,
                        "siguiente": siguiente.id,
                        "retraso_s": anterior.retraso_s,
                    },
                )


def _validar_giros() -> None:
    """Giro de los balones y quietud del resto (criterios 7.6, 7.7 y 26.7)."""
    duraciones: list[float] = []
    sentidos: list[int] = []
    for elemento in ELEMENTOS:
        if elemento.tipo != TIPO_BALON:
            if elemento.giro_s != 0.0 or elemento.sentido != 0:
                raise _fallo(
                    f"{elemento.id!r} no es de tipo balon y declara giro "
                    f"({elemento.giro_s} s, sentido {elemento.sentido})",
                    {
                        "id": elemento.id,
                        "giro_s": elemento.giro_s,
                        "sentido": elemento.sentido,
                    },
                )
            continue
        if not VUELTA_BALON_MIN <= elemento.giro_s <= VUELTA_BALON_MAX:
            raise _fallo(
                f"el balon {elemento.id!r} declara una vuelta de "
                f"{elemento.giro_s} s y el rango es "
                f"[{VUELTA_BALON_MIN}, {VUELTA_BALON_MAX}]",
                {"id": elemento.id, "giro_s": elemento.giro_s},
            )
        if elemento.sentido not in (1, -1):
            raise _fallo(
                f"el balon {elemento.id!r} declara el sentido "
                f"{elemento.sentido} y debe ser +1 u -1",
                {"id": elemento.id, "sentido": elemento.sentido},
            )
        if elemento.giro_s in duraciones:
            raise _fallo(
                f"el balon {elemento.id!r} repite la duracion de vuelta "
                f"{elemento.giro_s} s, que ya declara otro balon",
                {"id": elemento.id, "giro_s": elemento.giro_s},
            )
        duraciones.append(elemento.giro_s)
        sentidos.append(elemento.sentido)

    for sentido in (1, -1):
        if sentido not in sentidos:
            raise _fallo(
                f"ningun balon declara el sentido de giro {sentido}, y el "
                "criterio 7.7 exige los dos",
                {"sentidos": tuple(sentidos)},
            )


def validar_elementos() -> None:
    """Todos los invariantes declarativos del Mundo_Hero.

    Cada uno con `raise ErrorAsset(..., codigo=E_ASSET_INVALIDO)` y mensaje en
    espanol que nombra el elemento infractor y el valor que falla; **ningun
    `assert`** en ninguna rama.

    Cubre los conteos y sus cotas, la cobertura de tipos y de cuadrantes, la
    unicidad de identificadores, la pertenencia de la capa al conjunto de tres,
    las coordenadas y el ancho, el vaiven con sus rangos y sus retrasos
    distintos entre elementos consecutivos del mismo tipo, el giro de los
    balones con sus duraciones distintas y sus dos sentidos, el catalogo de
    Figura_Girable con su duracion de vuelta, sus sentidos, su animacion
    infinita y su `translateZ` propio por capa, y el Balon_Esfera con sus ocho
    angulos de gajo, su Eje_Giro_Inclinado y la regla de que la vuelta crece con
    la lejania de la capa.
    """
    _validar_conteos()
    _validar_cobertura()
    _validar_cada_elemento()
    _validar_vaiven()
    _validar_giros()
    _validar_figuras_girables()
    _validar_balon_esfera()


# --------------------------------------------------------------------------- #
# Clases CSS del Mundo_Hero
# --------------------------------------------------------------------------- #

#: Contenedor del Mundo_Hero, primer hijo de `.hero` (criterio 11.1).
CLASE_MUNDO: str = "hero-mundo"

#: Cada una de las tres Capa_Parallax.
CLASE_CAPA: str = "hero-capa"

#: Envoltorio de un Elemento_Fondo: lleva el vaiven (criterios 10.1 y 10.2).
CLASE_OBJETO: str = "hero-objeto"

#: Envoltorio interno que lleva **solo** el giro, para que el vaiven del
#: envoltorio externo y la vuelta del interno no se pisen.
CLASE_GIRO: str = "hero-giro"


# --------------------------------------------------------------------------- #
# Figura_Girable del hero (Requisito 25)
# --------------------------------------------------------------------------- #

#: Origen de una Figura_Girable que sale del catalogo de Elemento_Fondo.
ORIGEN_FONDO: str = "elemento-fondo"

#: Origen de una Figura_Girable que sale del Catalogo_Diagramas y gira dentro de
#: su Visor_Ampliado, no en una capa del fondo.
ORIGEN_DIAGRAMA: str = "diagrama-postura"

#: Rango declarado de la duracion de vuelta de una Figura_Girable, en segundos
#: (criterio 25.2).
VUELTA_FIGURA_MIN: float = 18.0
VUELTA_FIGURA_MAX: float = 30.0


@dataclass(frozen=True, slots=True)
class FiguraGirable:
    """Una figura que da la vuelta completa y conmuta entre sus diez Vista_Figura.

    `capa` es la Capa_Parallax donde vive, o `None` cuando la figura no vive en el
    fondo: `anatomia-base` gira dentro de su Visor_Ampliado, asi que su
    `translateZ` propio es 0 y no compite con nadie (criterio 25.16).

    `infinita` es siempre verdadero: la animacion de giro se repite de forma
    indefinida (criterio 25.5). Se declara como campo, y no como constante
    global, para que `validar_elementos` pueda nombrar la figura infractora si
    alguna vez alguien la pone en falso.
    """

    id: str
    origen: str
    capa: str | None
    vuelta_s: float
    sentido: int
    z_figura_px: float
    infinita: bool


#: Las cuatro Figura_Girable del Target_Web, en orden declarado.
#:
#: Las tres siluetas comparten la Capa_Cercana y declaran cada una un
#: `--z-figura` propio y distinto que se suma al `translateZ` de la capa
#: (criterio 25.16). Las cuatro duraciones caen en `[18, 30]`, son distintas
#: entre si y aparecen los dos sentidos (criterios 25.2, 25.3 y 25.4).
#:
#: Cuatro Figura_Girable por diez Vista_Figura dan **exactamente** 40, que es
#: `vistas_figura.VISTAS_MAX` sin margen de sobra: anadir una quinta obliga a
#: bajar el numero de vistas o a subir el techo, y `validar_elementos` lo dice
#: con `ErrorAsset` en vez de dejar que el documento engorde en silencio.
FIGURAS_GIRABLES: tuple[FiguraGirable, ...] = (
    FiguraGirable(
        id="silueta-1",
        origen=ORIGEN_FONDO,
        capa=CAPA_CERCANA,
        vuelta_s=19.0,
        sentido=1,
        z_figura_px=-18.0,
        infinita=True,
    ),
    FiguraGirable(
        id="silueta-2",
        origen=ORIGEN_FONDO,
        capa=CAPA_CERCANA,
        vuelta_s=24.0,
        sentido=-1,
        z_figura_px=-42.0,
        infinita=True,
    ),
    FiguraGirable(
        id="silueta-3",
        origen=ORIGEN_FONDO,
        capa=CAPA_CERCANA,
        vuelta_s=28.0,
        sentido=1,
        z_figura_px=-6.0,
        infinita=True,
    ),
    FiguraGirable(
        id="anatomia-base",
        origen=ORIGEN_DIAGRAMA,
        capa=None,
        vuelta_s=22.0,
        sentido=-1,
        z_figura_px=0.0,
        infinita=True,
    ),
)

#: Identificador del Diagrama_Postura cuya `Pose` presta la silueta del fondo. Es
#: la figura de pie del vocabulario anatomico: la unica pose neutra del catalogo,
#: y la que el Proyector_Vistas ya sabe girar en los diez angulos.
ID_POSE_SILUETA: str = "anatomia-base"

#: Texto alternativo de las siluetas del fondo. El Mundo_Hero lleva
#: `aria-hidden="true"`, asi que es decorativo, pero el `<svg>` de cada
#: Vista_Figura declara `role="img"` y necesita su `aria-label`.
ALT_SILUETA: str = (
    "Silueta de una jugadora de pie, dibujada solo con líneas, que gira "
    "despacio en el fondo de la portada."
)

#: Error frecuente y credito de las siluetas del fondo: son dibujo propio del
#: proyecto, igual que los ocho Diagrama_Postura.
_ERROR_SILUETA: str = (
    "No la mires como referencia técnica: es un adorno del fondo, no un modelo "
    "de postura."
)


def figura_girable_de(id_: str) -> FiguraGirable:
    """Figura_Girable con identificador `id_`."""
    for figura in FIGURAS_GIRABLES:
        if figura.id == id_:
            return figura
    raise ErrorAsset(
        f"Figura_Girable desconocida: {id_!r}",
        detalle={"id": id_},
        codigo=E_ASSET_INVALIDO,
    )


def figuras_de_capa(capa: str | None) -> tuple[FiguraGirable, ...]:
    """Figura_Girable de `capa`, en orden declarado.

    Con `capa=None` devuelve las que no viven en ninguna Capa_Parallax, que es la
    unica entrada del Visor_Ampliado.
    """
    return tuple(f for f in FIGURAS_GIRABLES if f.capa == capa)


def siluetas_girables() -> tuple[FiguraGirable, ...]:
    """Las Figura_Girable que salen del catalogo de Elemento_Fondo."""
    return tuple(f for f in FIGURAS_GIRABLES if f.origen == ORIGEN_FONDO)


def diagrama_de_figura(figura: FiguraGirable) -> dp.DiagramaPostura:
    """Entrada de catalogo que el Proyector_Vistas necesita para `figura`.

    Para `anatomia-base` es la entrada **real** del Catalogo_Diagramas. Para las
    tres siluetas del fondo se construye una entrada equivalente: el
    Proyector_Vistas solo lee de ella el identificador, el texto alternativo y
    las dimensiones del modo SVG, y esas tres son las que distinguen una silueta
    del fondo de un Diagrama_Postura del cuerpo de la guia.

    Las siluetas heredan las dimensiones de `anatomia-base`, de modo que su
    `viewBox` y la escala de su esqueleto son las mismas y el dibujo sale
    identico salvo el identificador.
    """
    base: dp.DiagramaPostura = dp.por_id(ID_POSE_SILUETA)
    if figura.origen == ORIGEN_DIAGRAMA:
        return dp.por_id(figura.id)
    return dp.DiagramaPostura(
        id=figura.id,
        titulo="Silueta del fondo",
        archivo="",
        alt=ALT_SILUETA,
        ancho_archivo=base.ancho_archivo,
        alto_archivo=base.alto_archivo,
        ancho_svg=base.ancho_svg,
        alto_svg=base.alto_svg,
        pasos=(),
        etiquetas=(),
        fases=(),
        fundamento=None,
        postura_id=None,
        requiere_archivo=False,
        girable=True,
        advertencia=None,
        error_frecuente=_ERROR_SILUETA,
        credito=dp.CREDITO_PROPIO,
    )


def pose_de_figura(figura: FiguraGirable) -> sp.Pose:
    """`Pose` que dibuja `figura`.

    Las tres siluetas del fondo comparten la pose neutra de `anatomia-base`;
    `anatomia-base` usa la suya, que es la misma. Una sola fuente de verdad, sin
    ninguna pose nueva declarada para el fondo.
    """
    if figura.origen == ORIGEN_DIAGRAMA:
        return sp.pose_de(figura.id)
    return sp.pose_de(ID_POSE_SILUETA)


def marcado_girable(figura: FiguraGirable) -> str:
    """Contenedor con las **diez** Vista_Figura de `figura`.

    Sale entero de `vistas_figura.svg_figura_girable`, asi que la Sombra_Contacto
    de cada vista es un `<ellipse>` dentro del propio SVG con escala horizontal
    `vistas_figura.escala_sombra(azimut)` y escala vertical 1 (criterios 25.14 y
    25.15). Las siluetas del fondo usan `COLOR_TAPA_FONDO` para su Tapa_Torso
    (criterio 14.20); `anatomia-base` usa el color de los Diagrama_Postura.
    """
    d: dp.DiagramaPostura = diagrama_de_figura(figura)
    pose: sp.Pose = pose_de_figura(figura)
    if figura.origen == ORIGEN_FONDO:
        return vf.svg_figura_girable(pose, d, color_tapa=vf.COLOR_TAPA_FONDO)
    return vf.svg_figura_girable(pose, d)


def _validar_figuras_girables() -> None:
    """Invariantes del catalogo de Figura_Girable (criterios 25.2 a 25.5 y 25.16).

    Duracion de vuelta en `[18, 30]`, duraciones distintas entre figuras, los dos
    sentidos presentes, animacion infinita y `translateZ` propio y distinto entre
    figuras de la misma capa. Todo con `ErrorAsset` nombrando las figuras y el
    valor repetido; **ningun `assert`**.
    """
    vistos: list[str] = []
    duraciones: list[float] = []
    sentidos: list[int] = []
    for figura in FIGURAS_GIRABLES:
        if figura.id in vistos:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} se repite en el catalogo",
                {"id": figura.id},
            )
        vistos.append(figura.id)
        if figura.origen not in (ORIGEN_FONDO, ORIGEN_DIAGRAMA):
            raise _fallo(
                f"la Figura_Girable {figura.id!r} declara el origen "
                f"{figura.origen!r}, que no es ni {ORIGEN_FONDO!r} ni "
                f"{ORIGEN_DIAGRAMA!r}",
                {"id": figura.id, "origen": figura.origen},
            )
        if figura.capa is not None and figura.capa not in CAPAS:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} declara la capa "
                f"{figura.capa!r}, que no pertenece a las tres declaradas "
                f"{CAPAS}",
                {"id": figura.id, "capa": figura.capa},
            )
        if not VUELTA_FIGURA_MIN <= figura.vuelta_s <= VUELTA_FIGURA_MAX:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} declara una vuelta de "
                f"{figura.vuelta_s} s y el rango es "
                f"[{VUELTA_FIGURA_MIN}, {VUELTA_FIGURA_MAX}]",
                {"id": figura.id, "vuelta_s": figura.vuelta_s},
            )
        if figura.vuelta_s in duraciones:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} repite la duracion de vuelta "
                f"{figura.vuelta_s} s, que ya declara otra figura",
                {"id": figura.id, "vuelta_s": figura.vuelta_s},
            )
        duraciones.append(figura.vuelta_s)
        if figura.sentido not in (1, -1):
            raise _fallo(
                f"la Figura_Girable {figura.id!r} declara el sentido "
                f"{figura.sentido} y debe ser +1 u -1",
                {"id": figura.id, "sentido": figura.sentido},
            )
        sentidos.append(figura.sentido)
        if not figura.infinita:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} no declara la animacion de "
                "giro como infinita, y el criterio 25.5 la exige indefinida",
                {"id": figura.id},
            )

    for sentido in (1, -1):
        if sentido not in sentidos:
            raise _fallo(
                f"ninguna Figura_Girable declara el sentido de giro {sentido}, "
                "y el criterio 25.4 exige los dos",
                {"sentidos": tuple(sentidos)},
            )

    # `translateZ` propio y distinto **dentro de cada capa** (criterio 25.16).
    for capa in CAPAS:
        de_la_capa: tuple[FiguraGirable, ...] = figuras_de_capa(capa)
        zetas: list[float] = []
        for figura in de_la_capa:
            if figura.z_figura_px in zetas:
                repetida: str = next(
                    otra.id
                    for otra in de_la_capa
                    if otra.z_figura_px == figura.z_figura_px
                    and otra.id != figura.id
                )
                raise _fallo(
                    f"la Figura_Girable {figura.id!r} y {repetida!r} comparten "
                    f"la capa {capa!r} y el mismo translateZ de "
                    f"{figura.z_figura_px} px",
                    {
                        "capa": capa,
                        "figuras": (repetida, figura.id),
                        "z_figura_px": figura.z_figura_px,
                    },
                )
            zetas.append(figura.z_figura_px)

    # Toda silueta del fondo tiene su Elemento_Fondo, y todo Elemento_Fondo de
    # tipo silueta tiene su Figura_Girable: los dos catalogos no se desincronizan.
    for figura in siluetas_girables():
        elemento: ElementoFondo = elemento_de(figura.id)
        if elemento.tipo != TIPO_SILUETA:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} apunta a un Elemento_Fondo de "
                f"tipo {elemento.tipo!r} y no a una silueta",
                {"id": figura.id, "tipo": elemento.tipo},
            )
        if figura.capa != elemento.capa:
            raise _fallo(
                f"la Figura_Girable {figura.id!r} declara la capa "
                f"{figura.capa!r} y su Elemento_Fondo vive en "
                f"{elemento.capa!r}",
                {"id": figura.id, "figura": figura.capa, "elemento": elemento.capa},
            )
    for elemento in por_tipo(TIPO_SILUETA):
        if elemento.id not in vistos:
            raise _fallo(
                f"el Elemento_Fondo de tipo silueta {elemento.id!r} no tiene "
                "Figura_Girable declarada",
                {"id": elemento.id},
            )

    # Techo de Vista_Figura del Target_Web (criterio 22.13): lo dice el
    # Proyector_Vistas, que es quien declara `VISTAS_MAX`.
    vf.validar_total_de_vistas(len(FIGURAS_GIRABLES))


# --------------------------------------------------------------------------- #
# CSS de la Figura_Girable y de su Sombra_Contacto
# --------------------------------------------------------------------------- #

#: Duracion de la transicion de `opacity` entre dos Vista_Figura, en
#: milisegundos. Es lo unico que se anima al conmutar: ni `transform`, ni
#: `display`, ni geometria.
TRANSICION_VISTA_MS: int = 320

#: Clase CSS de la Sombra_Contacto, la misma que emite el Proyector_Vistas.
CLASE_SOMBRA: str = "sombra-contacto"


def css_figura_girable() -> str:
    """Reglas de la Figura_Girable, de sus Vista_Figura y de su Sombra_Contacto.

    Contrato del diseno, atado a su criterio:

    * `.figura-girable` declara `perspective` y `transform-style:preserve-3d`
      (criterio 25.1), con la perspectiva leida de `PERSPECTIVA_PX`: un solo
      numero en todo el proyecto.
    * La Vista_Activa se distingue **solo** por la clase: sin ella `opacity:0` y
      `visibility:hidden`; con ella `opacity:1` y `visibility:visible`
      (criterio 22.10). Nada toca `display`.
    * `.sombra-contacto` solo declara `transform-origin`: **ninguna regla de la
      Sombra_Contacto declara `box-shadow`** (criterio 25.15), ni `top`, `left`,
      `width`, `height` ni `margin` (criterios 29.7 y 29.8).
    * `will-change` no aparece en ningun selector de Vista_Figura: sigue siendo
      exclusivo de las tres capas (criterio 29.9).
    """
    return "".join(
        (
            f".{vf.CLASE_GIRABLE}{{position:relative;"
            f"perspective:{PERSPECTIVA_PX}px;transform-style:preserve-3d;}}",
            f".{vf.CLASE_VISTA}{{position:absolute;inset:0;opacity:0;"
            f"visibility:hidden;transition:opacity {TRANSICION_VISTA_MS}ms "
            f"linear;}}",
            f".{vf.CLASE_VISTA}.{vf.CLASE_ACTIVA}"
            "{opacity:1;visibility:visible;}",
            f".{CLASE_MUNDO} .{vf.CLASE_VISTA}{{pointer-events:none;}}",
            f".{CLASE_SOMBRA}{{transform-origin:50% 100%;}}",
        )
    )


# --------------------------------------------------------------------------- #
# Balon_Esfera: ocho Gajo_Balon, dos polos y un Eje_Giro_Inclinado (Requisito 26)
# --------------------------------------------------------------------------- #

#: Cuantos Gajo_Balon lleva cada Balon_Esfera (criterio 26.1).
GAJOS: int = 8

#: Rotacion propia de cada Gajo_Balon alrededor del eje polar, en grados. Ocho
#: meridianos repartidos cada 22.5 grados: media vuelta basta, porque el gajo es
#: simetrico y el de 180 grados coincidiria con el de 0 (criterio 26.2).
ANGULOS_GAJO: tuple[float, ...] = (
    0.0,
    22.5,
    45.0,
    67.5,
    90.0,
    112.5,
    135.0,
    157.5,
)

#: Numero (1..8) del Gajo_Balon que se emite **sombreado**. Bajo 768 px la esfera
#: degrada a una rotacion de dos dimensiones y este gajo, desplazado del centro,
#: es lo que sostiene la ilusion de volumen sin `preserve-3d` (criterios 26.10 y
#: 12.6). Se elige el de 45 grados: lo bastante lejos del meridiano frontal para
#: leerse como sombra propia y lo bastante lejos del de perfil para no
#: desaparecer al degradar.
GAJO_SOMBREADO: int = 3

#: Eje_Giro_Inclinado de cada Balon_Esfera, en el sistema de `rotate3d(x,y,z,·)`
#: (criterios 26.4 y 26.5). Las tres componentes son distintas de cero y la
#: inclinacion respecto de la vertical cae en `[15, 45]` grados: 21.5, 35.1 y
#: 16.3 grados respectivamente.
EJES_BALON: dict[str, tuple[float, float, float]] = {
    "balon-1": (0.26, 0.93, 0.26),
    "balon-2": (0.42, 0.82, 0.39),
    "balon-3": (0.18, 0.96, 0.21),
}

#: Rango declarado de la inclinacion del Eje_Giro_Inclinado, en grados
#: (criterio 26.5).
INCLINACION_MIN: float = 15.0
INCLINACION_MAX: float = 45.0

#: Clase CSS del contenedor de un Balon_Esfera.
CLASE_BALON: str = "balon-esfera"

#: Clase CSS de un Gajo_Balon.
CLASE_GAJO: str = "gajo-balon"

#: Clase CSS del Gajo_Balon sombreado de la degradacion de dos dimensiones.
CLASE_GAJO_SOMBREADO: str = "gajo-sombreado"

#: Desplazamiento del Gajo_Balon sombreado respecto del centro, en porcentaje
#: (criterio 26.10). En porcentaje, y no en pixeles, para que escale con el ancho
#: declarado del Elemento_Fondo.
DESPLAZAMIENTO_SOMBREADO_PCT: int = 12

#: Corte de pantalla angosta expresado en `rem`, que es la unidad de las
#: `@media` del proyecto: `768 / 16 = 48`, y el ultimo pixel por debajo del corte
#: es `47.9375rem`.
CORTE_ANGOSTO_REM: str = "47.9375rem"

#: Lienzo canonico de un Elemento_Fondo: cuadrado de 100 unidades, para que el
#: `viewBox` sea el mismo en los nueve tipos y el `width` en porcentaje del hero
#: sea lo unico que fije su tamano real.
LIENZO_FONDO: float = 100.0

#: Centro y radio de la esfera en el lienzo canonico.
CENTRO_FONDO: float = 50.0
RADIO_BALON: float = 44.0

#: Semieje horizontal de un Gajo_Balon en el lienzo canonico. Los ocho comparten
#: la misma silueta de meridiano: lo que los distingue es su `rotate3d`.
SEMIEJE_GAJO: float = 14.0

#: Semiejes del casquete de cada polo en el lienzo canonico.
POLO_RX: float = 17.0
POLO_RY: float = 5.5

#: Grosor de trazo de los Elemento_Fondo en el lienzo canonico.
GROSOR_FONDO: float = 2.0


def eje_de(id_balon: str) -> tuple[float, float, float]:
    """Eje_Giro_Inclinado declarado de `id_balon`."""
    eje: tuple[float, float, float] | None = EJES_BALON.get(id_balon)
    if eje is None:
        raise _fallo(
            f"el Elemento_Fondo {id_balon!r} no declara Eje_Giro_Inclinado",
            {"id": id_balon},
        )
    return eje


def inclinacion_eje(eje: tuple[float, float, float]) -> float:
    """Inclinacion de `eje` respecto de la vertical, en grados (criterio 26.5).

    `acos(|y| / |(x, y, z)|)`: 0 grados es el eje perfectamente vertical y 90 el
    horizontal. El valor absoluto de `y` hace que el resultado no dependa de si el
    eje apunta hacia arriba o hacia abajo, que es la misma inclinacion.
    """
    x, y, z = eje
    norma: float = math.sqrt(x * x + y * y + z * z)
    if norma <= 0.0:
        raise _fallo(
            f"el Eje_Giro_Inclinado {eje} tiene norma nula y no define ninguna "
            "direccion de giro",
            {"eje": eje},
        )
    coseno: float = _acotar(abs(y) / norma, -1.0, 1.0)
    return math.degrees(math.acos(coseno))


def eje_css(eje: tuple[float, float, float]) -> str:
    """Las tres componentes de `eje` como valor de la variable `--eje`.

    Se emite tal cual dentro de `rotate3d(var(--eje), var(--vuelta))`, asi que va
    sin parentesis y separado por comas.
    """
    return ",".join(sp.num(componente) for componente in eje)


def _validar_balon_esfera() -> None:
    """Invariantes del Balon_Esfera (criterios 26.1 a 26.9).

    Un Eje_Giro_Inclinado por balon y ninguno de sobra; las tres componentes
    distintas de cero; inclinacion en `[15, 45]` grados; duracion de vuelta en
    `[14, 26]` y distinta entre balones; los dos sentidos; ocho angulos de gajo
    distintos y el gajo sombreado dentro de rango; y la regla fuerte **la duracion
    de vuelta crece con la lejania de la capa**, que hoy se cumple de forma vacia
    porque los tres balones viven en la Capa_Media, pero queda comprobada para el
    dia en que uno cambie de capa.
    """
    if len(ANGULOS_GAJO) != GAJOS:
        raise _fallo(
            f"el Balon_Esfera declara {len(ANGULOS_GAJO)} angulos de Gajo_Balon "
            f"y el criterio 26.1 exige exactamente {GAJOS}",
            {"angulos": ANGULOS_GAJO},
        )
    if len(set(ANGULOS_GAJO)) != GAJOS:
        raise _fallo(
            f"dos Gajo_Balon comparten el mismo angulo en {ANGULOS_GAJO}, y el "
            "criterio 26.2 exige que los ocho sean distintos",
            {"angulos": ANGULOS_GAJO},
        )
    if not 1 <= GAJO_SOMBREADO <= GAJOS:
        raise _fallo(
            f"el Gajo_Balon sombreado es el numero {GAJO_SOMBREADO} y solo hay "
            f"{GAJOS}",
            {"gajo": GAJO_SOMBREADO},
        )

    ids_balon: tuple[str, ...] = tuple(b.id for b in balones())
    for id_declarado in EJES_BALON:
        if id_declarado not in ids_balon:
            raise _fallo(
                f"se declara un Eje_Giro_Inclinado para {id_declarado!r}, que no "
                "es un Elemento_Fondo de tipo balon",
                {"id": id_declarado},
            )

    for balon in balones():
        eje: tuple[float, float, float] = eje_de(balon.id)
        for indice, componente in enumerate(eje):
            if componente == 0.0:
                raise _fallo(
                    f"el Eje_Giro_Inclinado de {balon.id!r} tiene la componente "
                    f"{'xyz'[indice]} en cero, y el criterio 26.4 exige las tres "
                    "distintas de cero",
                    {"id": balon.id, "eje": eje, "componente": "xyz"[indice]},
                )
        grados: float = inclinacion_eje(eje)
        if not INCLINACION_MIN <= grados <= INCLINACION_MAX:
            raise _fallo(
                f"el Eje_Giro_Inclinado de {balon.id!r} forma "
                f"{round(grados, 2)} grados con la vertical y el rango es "
                f"[{INCLINACION_MIN}, {INCLINACION_MAX}]",
                {"id": balon.id, "eje": eje, "inclinacion": grados},
            )

    # Regla fuerte del criterio 26.8: cuanto mas lejana la capa, mas lenta la
    # vuelta. `CAPAS` va de la mas lejana a la mas cercana, asi que el indice
    # menor es la capa mas lejana.
    for uno in balones():
        for otro in balones():
            if CAPAS.index(uno.capa) >= CAPAS.index(otro.capa):
                continue
            if uno.giro_s <= otro.giro_s:
                raise _fallo(
                    f"el balon {uno.id!r} vive en la capa {uno.capa!r}, mas "
                    f"lejana que la de {otro.id!r} ({otro.capa!r}), y su vuelta "
                    f"de {uno.giro_s} s no es mas lenta que la de "
                    f"{otro.giro_s} s",
                    {
                        "lejano": uno.id,
                        "cercano": otro.id,
                        "vuelta_lejano": uno.giro_s,
                        "vuelta_cercano": otro.giro_s,
                    },
                )


# --------------------------------------------------------------------------- #
# Marcado del Balon_Esfera
# --------------------------------------------------------------------------- #


def _apertura_svg_fondo(elemento: ElementoFondo, clases: str) -> str:
    """`<svg>` de apertura de un Elemento_Fondo, con su lienzo canonico.

    Sin `role` ni `aria-label`: el Mundo_Hero entero lleva `aria-hidden="true"`,
    asi que sus dibujos son decorativos y no deben anunciarse. `focusable="false"`
    los saca del orden de tabulacion tambien en los navegadores viejos, sin
    necesidad de `tabindex` (criterio 11.3).
    """
    lado: str = sp.num(LIENZO_FONDO)
    return (
        f'<svg class="{clases}" data-tipo="{elemento.tipo}" '
        f'viewBox="0 0 {lado} {lado}" width="100%" height="100%" '
        f'focusable="false" aria-hidden="true">'
    )


def _gajo(numero: int, angulo: float) -> str:
    """Un Gajo_Balon: el meridiano y su `rotate3d` propio.

    Los ocho comparten la silueta de meridiano (una lente vertical centrada en la
    esfera) y se distinguen **solo** por su rotacion alrededor del eje polar
    (criterio 26.2). El sombreado lleva ademas su clase y un relleno propio, que
    es lo que se lee como volumen cuando la esfera degrada a dos dimensiones
    (criterio 26.10).
    """
    clases: str = f"{CLASE_GAJO} gajo-{numero}"
    relleno: str = "none"
    opacidad: float = 0.0
    if numero == GAJO_SOMBREADO:
        clases = f"{clases} {CLASE_GAJO_SOMBREADO}"
        relleno = sp.COLOR_CONTORNO
        opacidad = 0.14
    partes: list[str] = [
        f'<g class="{clases}" style="transform:rotate3d(0,1,0,'
        f'{sp.num(angulo)}deg)">',
        f'<ellipse cx="{sp.num(CENTRO_FONDO)}" cy="{sp.num(CENTRO_FONDO)}" '
        f'rx="{sp.num(SEMIEJE_GAJO)}" ry="{sp.num(RADIO_BALON)}" '
        f'fill="{relleno}"',
    ]
    if opacidad > 0.0:
        partes.append(f' fill-opacity="{sp.num(opacidad)}"')
    partes.append(
        f' stroke="{sp.COLOR_GUIA}" stroke-width="{sp.num(GROSOR_FONDO)}" />'
    )
    partes.append("</g>")
    return "".join(partes)


def _polos() -> str:
    """Los dos casquetes polares del Balon_Esfera (criterio 26.6).

    Son los que hacen que la esfera se lea redonda al inclinarse el eje: al girar
    alrededor de un eje que no es vertical, el polo de arriba y el de abajo entran
    y salen de la vista.
    """
    partes: list[str] = []
    for clase, centro_y in (
        ("polo-superior", CENTRO_FONDO - RADIO_BALON * 0.72),
        ("polo-inferior", CENTRO_FONDO + RADIO_BALON * 0.72),
    ):
        partes.append(
            f'<g class="{clase}">'
            f'<ellipse cx="{sp.num(CENTRO_FONDO)}" cy="{sp.num(centro_y)}" '
            f'rx="{sp.num(POLO_RX)}" ry="{sp.num(POLO_RY)}" '
            f'fill="{sp.COLOR_SILUETA}" fill-opacity="0.35" '
            f'stroke="{sp.COLOR_CONTORNO}" '
            f'stroke-width="{sp.num(GROSOR_FONDO)}" /></g>'
        )
    return "".join(partes)


def svg_balon_esfera(elemento: ElementoFondo) -> str:
    """Balon_Esfera de `elemento`: ocho Gajo_Balon y los dos polos.

    El `<svg>` es el contenedor `.balon-esfera`, que es quien declara
    `transform-style:preserve-3d` y quien lleva la animacion de vuelta alrededor
    del Eje_Giro_Inclinado (criterios 26.3 y 7.6). Su marcado no lleva `<image>`,
    ni `url(`, ni `http`, ni ningun atributo de evento (criterio 26.11): lo
    comprueba `svg_postura.validar_marcado` sobre el resultado.
    """
    if elemento.tipo != TIPO_BALON:
        raise _fallo(
            f"{elemento.id!r} es de tipo {elemento.tipo!r} y solo los balones se "
            "emiten como Balon_Esfera",
            {"id": elemento.id, "tipo": elemento.tipo},
        )
    partes: list[str] = [
        _apertura_svg_fondo(elemento, CLASE_BALON),
        f'<circle class="balon-contorno" cx="{sp.num(CENTRO_FONDO)}" '
        f'cy="{sp.num(CENTRO_FONDO)}" r="{sp.num(RADIO_BALON)}" '
        f'fill="{sp.COLOR_ZONA}" fill-opacity="0.55" '
        f'stroke="{sp.COLOR_CONTORNO}" '
        f'stroke-width="{sp.num(GROSOR_FONDO)}" />',
    ]
    for numero, angulo in enumerate(ANGULOS_GAJO, start=1):
        partes.append(_gajo(numero, angulo))
    partes.append(_polos())
    partes.append("</svg>")

    marcado: str = "".join(partes)
    sp.validar_marcado(elemento.id, marcado)
    return marcado


# --------------------------------------------------------------------------- #
# CSS del Balon_Esfera y de su degradacion de dos dimensiones
# --------------------------------------------------------------------------- #


def css_balon_esfera() -> str:
    """Reglas del Balon_Esfera, de sus gajos y de la degradacion a dos dimensiones.

    Contrato del diseno, atado a su criterio:

    * `.balon-esfera` declara `transform-style:preserve-3d` (criterio 26.3).
    * `@keyframes hero-rueda` gira alrededor del Eje_Giro_Inclinado con
      `rotate3d(var(--eje), var(--vuelta))`: el eje y el sentido llegan por
      variable en linea, uno por balon, asi que un solo par de fotogramas sirve a
      los tres (criterios 7.6 y 7.7).
    * Bajo `47.9375rem` la animacion pasa a `hero-rueda-2d`, que es una rotacion
      de dos dimensiones con `rotate(`, y el Gajo_Balon sombreado se desplaza del
      centro (criterios 26.10 y 12.6).
    * Ni `box-shadow`, ni `top`, ni `left`, ni `width`, ni `height`, ni `margin`
      en ninguna regla animada (criterio 10.2).
    """
    return "".join(
        (
            f".{CLASE_BALON}{{display:block;transform-style:preserve-3d;}}",
            f".{CLASE_GAJO}{{transform-origin:50% 50%;}}",
            "@keyframes hero-rueda{from{transform:rotate3d(var(--eje),0deg);}"
            "to{transform:rotate3d(var(--eje),var(--vuelta));}}",
            "@keyframes hero-rueda-2d{from{transform:rotate(0deg);}"
            "to{transform:rotate(var(--vuelta));}}",
            f"@media (max-width:{CORTE_ANGOSTO_REM})"
            f"{{.{CLASE_GIRO}{{animation-name:hero-rueda-2d;}}"
            f".{CLASE_GAJO_SOMBREADO}"
            f"{{transform:translate({DESPLAZAMIENTO_SOMBREADO_PCT}%,0);}}}}",
        )
    )


# --------------------------------------------------------------------------- #
# Serializacion: el unico puente hacia el Script_Unico
# --------------------------------------------------------------------------- #

#: Separadores del literal JSON: compacto, sin un solo espacio de sobra. El
#: Script_Unico lo lleva embebido, asi que cada byte cuenta.
_SEPARADORES: tuple[str, str] = (",", ":")

#: Subcadenas que el literal JSON no puede contener. `//` porque
#: `test_build_site::test_script_propio_y_unico` la prohibe en todo el cuerpo del
#: `<script>` (criterio 10.10), y `http` porque el Target_Web es autocontenido.
_PROHIBIDOS_JSON: tuple[str, ...] = ("//", "http")


def _por_capa_en_orden(tabla: dict[str, float]) -> list[float]:
    """Valores de `tabla` en el orden **lejana, media, cercana**.

    Ese orden es el de `CAPAS` y el que el JavaScript resuelve por indice, asi que
    se deriva de la tupla y no se vuelve a escribir a mano.
    """
    return [tabla[capa] for capa in CAPAS]


def datos_mundo() -> dict[str, object]:
    """Constantes del Mundo_Hero y del multi-vista, como mapa serializable.

    Se expone aparte de `datos_json()` para que las pruebas comparen contra las
    constantes de Python sin volver a parsear el literal, y para que el orden de
    las claves quede declarado en un solo sitio.

    Claves del mundo (Requisitos 8, 9 y 12): `f` los factores de parallax, `e` las
    escalas finales, `z` los `translateZ` de capa, `tope` el tope del cursor, `k`
    el coeficiente de suavizado, `corte` el ancho de pantalla angosta, `minA` y
    `maxA` la ventana de Elemento_Fondo activos, `radio` el radio del toque,
    `rebote` la duracion del rebote y `balones` los identificadores con sus
    coordenadas declaradas.

    Claves de la ampliacion (Requisitos 22, 25 y 28): `vistas` las diez
    Clave_Vista en su orden --su indice **es** el indice de la Vista_Figura dentro
    de su contenedor, asi que el Conmutador_Vista resuelve la vista con un entero
    y nunca con una busqueda en el DOM--, `residual` el tope de la
    Rotacion_Residual, `azMovil` los azimuts que sobreviven bajo el corte,
    `umbralEl` el umbral de conmutacion a Vista_Elevacion, `figuras` cada
    Figura_Girable como `[id, duracion s, sentido, translateZ px]`, `girarMs` la
    duracion del Giro_Impulso y `dragDeg` los grados por pixel del
    Arrastre_Rotacion.
    """
    return {
        "f": _por_capa_en_orden(FACTOR_PARALLAX),
        "e": _por_capa_en_orden(ESCALA_FINAL),
        "z": _por_capa_en_orden(TRASLADO_Z_PX),
        "tope": TOPE_CURSOR_PX,
        "k": SUAVIZADO_CURSOR,
        "corte": CORTE_ANGOSTO_PX,
        "minA": ELEMENTOS_ANGOSTO[0],
        "maxA": ELEMENTOS_ANGOSTO[1],
        "radio": RADIO_TOQUE_PCT,
        "rebote": REBOTE_MS,
        "balones": [[b.id, b.x_pct, b.y_pct] for b in balones()],
        "vistas": list(vf.CLAVES_VISTA),
        "residual": vf.ROTACION_RESIDUAL_MAX,
        "azMovil": list(vf.AZIMUTS_MOVIL),
        "umbralEl": vf.UMBRAL_ELEVACION,
        "figuras": [
            [f.id, f.vuelta_s, f.sentido, f.z_figura_px]
            for f in FIGURAS_GIRABLES
        ],
        "girarMs": vf.GIRO_IMPULSO_MS,
        "dragDeg": vf.GRADOS_POR_PIXEL,
    }


def datos_json() -> str:
    """Las constantes del Mundo_Hero como literal JSON compacto.

    Es el **unico** puente hacia el JavaScript: el Script_Unico no repite ninguna
    constante a mano, las lee de aqui. `json.loads(datos_json())` reproduce
    exactamente lo que devuelve `datos_mundo()`, que son las constantes de Python.

    El literal no contiene la subcadena `//` ni la cadena `http`, y se comprueba
    con `raise ErrorAsset` antes de devolverlo: si algun identificador nuevo las
    introdujera, el build se detiene en vez de emitir un `<script>` que rompe el
    guardarrail vigente.
    """
    literal: str = json.dumps(
        datos_mundo(), separators=_SEPARADORES, ensure_ascii=True
    )
    for prohibido in _PROHIBIDOS_JSON:
        if prohibido in literal:
            raise _fallo(
                f"el literal JSON del Mundo_Hero contiene {prohibido!r}, que el "
                "criterio 10.10 prohibe en el cuerpo del script",
                {"prohibido": prohibido},
            )
    return literal


# --------------------------------------------------------------------------- #
# SVG en linea de los nueve tipos de Elemento_Fondo
# --------------------------------------------------------------------------- #

#: `id` del contenedor del Mundo_Hero. El Script_Unico lo resuelve con
#: `getElementById`, asi que el nombre vive en Python y no se escribe dos veces.
ID_MUNDO: str = "gb-mundo"

#: Prefijo del `id` de cada Capa_Parallax: `gb-capa-lejana` y sus dos hermanas.
PREFIJO_ID_CAPA: str = "gb-capa-"


def id_de_capa(capa: str) -> str:
    """`id` del contenedor de `capa` en el documento."""
    return f"{PREFIJO_ID_CAPA}{_capa_declarada(capa)}"


def _trazo(datos: str, color: str, *, relleno: str = "none") -> str:
    """Un `<path>` de contorno con el grosor comun de los Elemento_Fondo."""
    return (
        f'<path d="{datos}" fill="{relleno}" stroke="{color}" '
        f'stroke-width="{sp.num(GROSOR_FONDO)}" stroke-linejoin="round" '
        f'stroke-linecap="round" />'
    )


def _svg_porteria() -> str:
    """Porteria: los dos postes, el travesano y tres hilos de red."""
    partes: list[str] = [_trazo("M14 80 V26 H86 V80", sp.COLOR_CONTORNO)]
    for x in (32.0, 50.0, 68.0):
        partes.append(_trazo(f"M{sp.num(x)} 26 V80", sp.COLOR_GUIA))
    for y in (44.0, 62.0):
        partes.append(_trazo(f"M14 {sp.num(y)} H86", sp.COLOR_GUIA))
    return "".join(partes)


def _svg_cono() -> str:
    """Cono de entrenamiento: el triangulo, su franja y la base elíptica."""
    return "".join(
        (
            _trazo(
                "M50 20 L74 78 H26 Z",
                sp.COLOR_CONTORNO,
                relleno=sp.COLOR_SILUETA,
            ),
            _trazo("M35 56 H65", sp.COLOR_GUIA),
            f'<ellipse cx="50" cy="80" rx="30" ry="7" '
            f'fill="{sp.COLOR_SILUETA}" fill-opacity="0.45" '
            f'stroke="{sp.COLOR_CONTORNO}" '
            f'stroke-width="{sp.num(GROSOR_FONDO)}" />',
        )
    )


def _svg_linea() -> str:
    """Linea de campo: la banda, el arco de esquina y la marca de area."""
    return "".join(
        (
            _trazo("M6 72 H94", sp.COLOR_CONTORNO),
            _trazo("M6 72 A 34 34 0 0 1 40 38", sp.COLOR_GUIA),
            _trazo("M60 72 V50 H94", sp.COLOR_GUIA),
        )
    )


def _svg_silbato() -> str:
    """Silbato: el cuerpo, la boquilla, el agujero y el cordon."""
    return "".join(
        (
            _trazo(
                "M22 42 H62 A 18 18 0 0 1 62 78 H40 A 18 18 0 0 1 22 60 Z",
                sp.COLOR_CONTORNO,
                relleno=sp.COLOR_SILUETA,
            ),
            _trazo("M22 48 H10 V60 H22", sp.COLOR_CONTORNO),
            f'<circle cx="56" cy="60" r="6" fill="{sp.COLOR_ZONA}" '
            f'stroke="{sp.COLOR_GUIA}" '
            f'stroke-width="{sp.num(GROSOR_FONDO)}" />',
            _trazo("M42 42 Q 52 22 74 20", sp.COLOR_GUIA),
        )
    )


def _svg_copa() -> str:
    """Copa: el cuenco, las dos asas, el pie y la base."""
    return "".join(
        (
            _trazo(
                "M32 18 H68 V40 A 18 18 0 0 1 32 40 Z",
                sp.COLOR_CONTORNO,
                relleno=sp.COLOR_SILUETA,
            ),
            _trazo("M32 22 H20 V34 A 12 12 0 0 0 32 46", sp.COLOR_GUIA),
            _trazo("M68 22 H80 V34 A 12 12 0 0 1 68 46", sp.COLOR_GUIA),
            _trazo("M50 58 V74", sp.COLOR_CONTORNO),
            _trazo("M32 82 H68", sp.COLOR_CONTORNO),
            _trazo("M38 74 H62 V82 H38 Z", sp.COLOR_CONTORNO),
        )
    )


def _svg_taco() -> str:
    """Taco: la suela del botin vista de perfil y sus tres tacos."""
    partes: list[str] = [
        _trazo(
            "M12 62 Q 26 44 52 44 Q 78 44 88 62 Z",
            sp.COLOR_CONTORNO,
            relleno=sp.COLOR_SILUETA,
        ),
        _trazo("M12 62 H88", sp.COLOR_CONTORNO),
    ]
    for x in (26.0, 50.0, 74.0):
        partes.append(
            f'<rect x="{sp.num(x - 5.0)}" y="62" width="10" height="12" '
            f'rx="3" fill="{sp.COLOR_GUIA}" fill-opacity="0.45" '
            f'stroke="{sp.COLOR_CONTORNO}" '
            f'stroke-width="{sp.num(GROSOR_FONDO)}" />'
        )
    return "".join(partes)


def _svg_arco() -> str:
    """Arco: la curva del circulo central y su cuerda."""
    return "".join(
        (
            _trazo("M8 74 A 42 42 0 0 1 92 74", sp.COLOR_CONTORNO),
            _trazo("M20 74 H80", sp.COLOR_GUIA),
            _trazo("M50 32 V74", sp.COLOR_GUIA),
        )
    )


#: Dibujo de cada tipo de Elemento_Fondo que no es balon ni silueta. Es una tabla
#: declarativa: `svg_elemento` la consulta y no encadena condicionales.
FIGURAS_FONDO: dict[str, object] = {
    TIPO_PORTERIA: _svg_porteria,
    TIPO_CONO: _svg_cono,
    TIPO_LINEA: _svg_linea,
    TIPO_SILBATO: _svg_silbato,
    TIPO_COPA: _svg_copa,
    TIPO_TACO: _svg_taco,
    TIPO_ARCO: _svg_arco,
}


def svg_elemento(elemento: ElementoFondo) -> str:
    """Dibujo en linea de `elemento`, sin ninguna referencia a archivo (7.8).

    Tres caminos, uno por familia:

    * **balon**: el Balon_Esfera de `svg_balon_esfera`, con sus ocho Gajo_Balon y
      sus dos polos.
    * **silueta**: la Figura_Girable de `marcado_girable`, con sus diez
      Vista_Figura ya en el DOM y `az-000` activa.
    * **los otros siete tipos**: un `<svg>` propio del lienzo canonico, con los
      colores de la Paleta_Guia y nada mas.

    Todo el marcado pasa por `svg_postura.validar_marcado`: cero `<image>`, cero
    `url(`, cero `http`, cero `tabindex` y cero atributos de evento (criterios
    11.3 y 14.15).
    """
    if elemento.tipo == TIPO_BALON:
        return svg_balon_esfera(elemento)
    if elemento.tipo == TIPO_SILUETA:
        marcado_silueta: str = marcado_girable(figura_girable_de(elemento.id))
        sp.validar_marcado(elemento.id, marcado_silueta)
        return marcado_silueta
    dibujo = FIGURAS_FONDO.get(elemento.tipo)
    if dibujo is None:
        raise _fallo(
            f"{elemento.id!r} es de tipo {elemento.tipo!r} y el Mundo_Hero no "
            "declara ningun dibujo para ese tipo",
            {"id": elemento.id, "tipo": elemento.tipo},
        )
    marcado: str = "".join(
        (
            _apertura_svg_fondo(elemento, f"hero-figura hero-{elemento.tipo}"),
            dibujo(),  # type: ignore[operator]
            "</svg>",
        )
    )
    sp.validar_marcado(elemento.id, marcado)
    return marcado


# --------------------------------------------------------------------------- #
# Emision de la capa .hero-mundo
# --------------------------------------------------------------------------- #

#: Eje neutro de los Elemento_Fondo que no giran: el vertical. Se emite igual en
#: todos para que `--eje` exista siempre y el CSS no dependa de que la variable
#: este declarada o no.
EJE_NEUTRO: tuple[float, float, float] = (0.0, 1.0, 0.0)


def _estilo_objeto(elemento: ElementoFondo) -> str:
    """`style` en linea de un Elemento_Fondo.

    `left`, `top` y `width` son **posicion inicial estatica**, nunca animados: lo
    que se anima es `transform` y `opacity` (criterios 10.1 y 10.2). El resto son
    variables que el CSS lee: la duracion y la amplitud del vaiven, su retraso, la
    duracion y el sentido de la vuelta, el Eje_Giro_Inclinado y el `translateZ`
    propio de la Figura_Girable.

    Las once declaraciones se emiten en **todos** los objetos, giren o no: asi el
    marcado es uniforme, `--giro` vale 0 s donde no hay vuelta y el CSS nunca
    depende de que una variable exista.
    """
    eje: tuple[float, float, float] = EJE_NEUTRO
    if elemento.tipo == TIPO_BALON:
        eje = eje_de(elemento.id)
    z_figura: float = 0.0
    if elemento.tipo == TIPO_SILUETA:
        z_figura = figura_girable_de(elemento.id).z_figura_px
    vuelta: float = 360.0 * float(elemento.sentido)
    return ";".join(
        (
            f"left:{sp.num(elemento.x_pct)}%",
            f"top:{sp.num(elemento.y_pct)}%",
            f"width:{sp.num(elemento.ancho_pct)}%",
            f"opacity:{sp.num(elemento.opacidad)}",
            f"--vaiven:{sp.num(elemento.vaiven_s)}s",
            f"--amplitud:{sp.num(elemento.vaiven_px)}px",
            f"--retraso:{sp.num(elemento.retraso_s)}s",
            f"--giro:{sp.num(elemento.giro_s)}s",
            f"--vuelta:{sp.num(vuelta)}deg",
            f"--eje:{eje_css(eje)}",
            f"--z-figura:{sp.num(z_figura)}px",
        )
    )


def marcado_objeto(elemento: ElementoFondo) -> str:
    """Un Elemento_Fondo entero: su envoltorio, su estilo y su dibujo.

    Los balones llevan un `<span class="hero-giro">` interno cuya animacion es la
    unica que rota, de modo que el vaiven del envoltorio externo y la vuelta del
    interno no se pisan. Los demas tipos van directos, sin envoltorio de giro.
    """
    partes: list[str] = [
        f'<span class="{CLASE_OBJETO}" data-tipo="{elemento.tipo}" '
        f'data-id="{elemento.id}" '
        f'data-angosto="{1 if elemento.angosto else 0}" '
        f'style="{_estilo_objeto(elemento)}">'
    ]
    if elemento.tipo == TIPO_BALON:
        partes.append(f'<span class="{CLASE_GIRO}">')
        partes.append(svg_elemento(elemento))
        partes.append("</span>")
    else:
        partes.append(svg_elemento(elemento))
    partes.append("</span>")
    return "".join(partes)


def render_mundo(partes: list[str]) -> None:
    """Emite la capa `.hero-mundo` con sus tres Capa_Parallax.

    Se inserta como **primer hijo** de `.hero`, antes de `.hero-visor`, que es lo
    que la deja detras del modelo dentro del mismo plano `z-index:0`. El
    contenedor lleva `aria-hidden="true"` porque es decoracion (criterio 11.1), y
    cada capa su `id` y su `data-capa` para que el Script_Unico la resuelva por
    identificador y no por recorrido del DOM.

    El orden de emision es el de `CAPAS` --lejana, media, cercana-- y dentro de
    cada capa el del catalogo, que es el mismo orden que rompe los empates de
    `balon_mas_cercano`. Determinista de punta a punta: dos llamadas dejan los
    mismos bytes.
    """
    validar_elementos()
    partes.append(
        f'<div class="{CLASE_MUNDO}" id="{ID_MUNDO}" aria-hidden="true">'
    )
    for capa in CAPAS:
        partes.append(
            f'<div class="{CLASE_CAPA}" data-capa="{capa}" '
            f'id="{id_de_capa(capa)}">'
        )
        for elemento in por_capa(capa):
            partes.append(marcado_objeto(elemento))
        partes.append("</div>")
    partes.append("</div>")


def marcado_mundo() -> str:
    """El Mundo_Hero entero como una cadena, para las pruebas y el reporte."""
    partes: list[str] = []
    render_mundo(partes)
    return "".join(partes)


# --------------------------------------------------------------------------- #
# CSS del Mundo_Hero
# --------------------------------------------------------------------------- #

#: Duracion de la transicion de `opacity` con la que el Mundo_Hero reaparece, en
#: milisegundos. Dentro de la ventana de 200 a 600 que pide el criterio 27.7.
TRANSICION_REAPARICION_MS: int = 380

#: Clase que pone el Mundo_Hero en Modo_Inerte (Requisito 27). El Script_Unico la
#: alterna con la lista de clases del contenedor y **nunca** escribe
#: `animation-play-state` ni `display` en linea (criterios 10.16 y 27.9).
CLASE_INERTE: str = "inerte"


def inerte(p: float) -> bool:
    """True si el Mundo_Hero debe estar en Modo_Inerte con Progreso_Scroll `p`.

    La clase esta puesta **exactamente cuando** la opacidad vale 0, que es cuando
    no hay nada que ver y por tanto nada que valga la pena animar (criterios 27.1
    y 27.6). Funcion pura sobre la misma curva de `opacidad`, asi que las dos no
    pueden desincronizarse.

    Reparto de responsabilidades del Modo_Inerte, para que quede escrito donde se
    lee el codigo y no solo en el plan:

    * **Aqui (bloque 8):** este predicado, la clase `CLASE_INERTE`, la regla
      declarativa de `_css_modo_inerte` y la transicion de reaparicion de
      `_css_capas`. Todo eso ya se prueba en la Property 51.
    * **Tarea 10.6:** cablear `bloque_css()` a `build_html.estilo_css()`, para que
      estas reglas viajen al artefacto publicado.
    * **Tarea 12.6:** el Script_Unico alterna la clase con la lista de clases del
      contenedor y, mientras esta activa, omite toda escritura de `transform` y de
      `opacity` sobre las capas y sobre las Vista_Figura (criterios 27.5 y 27.9 en
      su parte imperativa). El predicado que decide esa omision es **este**: el
      bucle solo tiene que consultarlo.
    """
    return opacidad(p) == 0.0


def _css_capas() -> str:
    """`.hero-mundo`, `.hero-capa`, `.hero-objeto`, `.hero-giro` y `hero-flota`.

    * `.hero-mundo` es `position:absolute` --**jamas** `position:fixed`, que pelea
      con el desplazamiento en el navegador incrustado de Android--, no recibe
      punteros ni los deja pasar a ningun descendiente (criterio 11.2), y declara
      el espacio en perspectiva del criterio 6.8.
    * `will-change:transform` aparece **solo** en el selector de las tres capas
      (criterios 10.6 y 29.9).
    * `.hero-objeto` lleva el vaiven y `.hero-giro` la vuelta, separados para que
      las dos animaciones no compitan por la misma propiedad.
    * `@keyframes hero-flota` toca **solo** `transform` (criterios 10.1 y 10.2).
    """
    return "".join(
        (
            f".{CLASE_MUNDO}{{position:absolute;inset:0;z-index:0;"
            f"overflow:hidden;pointer-events:none;"
            f"perspective:{PERSPECTIVA_PX}px;transform-style:preserve-3d;"
            f"transition:opacity {TRANSICION_REAPARICION_MS}ms linear;}}",
            f".{CLASE_MUNDO} *{{pointer-events:none;}}",
            f".{CLASE_CAPA}{{position:absolute;inset:0;"
            "will-change:transform;transform-origin:50% 50%;"
            "transform-style:preserve-3d;}",
            f".{CLASE_OBJETO}{{position:absolute;display:block;"
            "max-width:100%;transform:translate(-50%,-50%);"
            "animation:hero-flota var(--vaiven) ease-in-out var(--retraso) "
            "infinite alternate;}",
            f".{CLASE_GIRO}{{display:block;"
            "animation:hero-rueda var(--giro) linear infinite;}",
            "@keyframes hero-flota"
            "{from{transform:translate(-50%,-50%) translate3d(0,0,0);}"
            "to{transform:translate(-50%,-50%) "
            "translate3d(0,var(--amplitud),0);}}",
        )
    )


def _css_modo_inerte() -> str:
    """Reglas del Modo_Inerte (criterios 27.2, 27.3 y 27.4).

    Es **una clase en el contenedor** y su regla alcanza las tres capas, los
    Elemento_Fondo, las Vista_Figura, los Gajo_Balon y las Sombra_Contacto; libera
    `will-change` a `auto`; y conserva el numero de nodos, porque nada se crea ni
    se borra. La reaparicion la resuelve la transicion de `opacity` que
    `.hero-mundo` ya declara en `_css_capas`.

    Pendiente de la costura del bloque 12: el Script_Unico es quien alterna la
    clase con la lista de clases del contenedor (criterios 10.16, 27.1, 27.6 y
    27.9). Aqui vive **solo** la mitad declarativa.
    """
    alcanzados: str = ",".join(
        (
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{CLASE_CAPA}",
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{CLASE_OBJETO}",
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{vf.CLASE_VISTA}",
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{CLASE_GAJO}",
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{CLASE_SOMBRA}",
        )
    )
    return "".join(
        (
            f".{CLASE_MUNDO}.{CLASE_INERTE}"
            "{visibility:hidden;animation-play-state:paused;}",
            f"{alcanzados}{{visibility:hidden;animation-play-state:paused;}}",
            f".{CLASE_MUNDO}.{CLASE_INERTE} .{CLASE_CAPA}"
            "{will-change:auto;}",
        )
    )


def css_sin_modos() -> str:
    """Las cuatro piezas del Mundo_Hero que NO son una consulta de medios final.

    Capas y vaiven, Figura_Girable con sus vistas y su Sombra_Contacto,
    Balon_Esfera con su degradacion de dos dimensiones y Modo_Inerte.

    Es lo que `build_html.estilo_css()` inserta en su sitio de la cascada (tareas
    10.4 a 10.6). Movimiento_Reducido e impresion **no** van aqui: la Hoja_Estilo
    los emite al final, en el orden obligado del criterio 11.7, y para eso lee
    `css_reduccion_cuerpo()` y `css_impresion()`.
    """
    return "".join(
        (
            _css_capas(),
            css_figura_girable(),
            css_balon_esfera(),
            _css_modo_inerte(),
        )
    )


def css_reduccion_cuerpo() -> str:
    """Declaraciones del Mundo_Hero **dentro** de Movimiento_Reducido, sin envolver.

    Se devuelve el cuerpo pelado (sin el `@media` ni sus llaves) para que
    `build_html.estilo_css()` lo funda con el bloque de Movimiento_Reducido que ya
    tiene, en vez de emitir dos consultas iguales. Con eso el orden obligado del
    criterio 11.7 se conserva: un solo bloque de movimiento reducido y, despues,
    un solo `@media print`.

    Contenido, criterio por criterio: el Mundo_Hero se queda **visible** como fondo
    estatico con opacidad 1 (11.6), se congelan las animaciones de capas, objetos,
    vistas, gajos y sombras (11.4 y 11.9) y queda visible exactamente la
    Vista_Activa `az-000` (11.8).
    """
    return "".join(
        (
            f".{CLASE_MUNDO}{{opacity:1;}}",
            f".{CLASE_MUNDO} .{CLASE_CAPA},.{CLASE_MUNDO} .{CLASE_OBJETO},"
            f".{CLASE_MUNDO} .{CLASE_GIRO}"
            "{animation:none !important;transform:none !important;"
            "opacity:1 !important;}",
            f".{vf.CLASE_VISTA},.{CLASE_GAJO},.{CLASE_SOMBRA},"
            f".{CLASE_BALON}{{animation:none !important;}}",
            f".{vf.CLASE_VISTA}{{opacity:0;visibility:hidden;}}",
            f'.{vf.CLASE_VISTA}[data-vista="{vf.CLAVE_ACTIVA}"]'
            "{opacity:1;visibility:visible;}",
        )
    )


def css_impresion() -> str:
    """`@media print` del Mundo_Hero: el fondo decorativo no se imprime (11.7)."""
    return f"@media print{{.{CLASE_MUNDO}{{display:none;}}}}"


def _css_movimiento_reducido() -> str:
    """Movimiento_Reducido y `@media print` (criterios 11.4, 11.6 a 11.9 y 11.7).

    Envuelve `css_reduccion_cuerpo()` en su consulta y le pega `css_impresion()`
    detras, para que la impresion gane por cascada y oculte el Mundo_Hero incluso
    con movimiento reducido activo (criterio 11.7).
    """
    return "".join(
        (
            "@media (prefers-reduced-motion: reduce){",
            css_reduccion_cuerpo(),
            "}",
            css_impresion(),
        )
    )


def bloque_css() -> str:
    """Todo el CSS del Mundo_Hero, en el orden en que la Hoja_Estilo lo inserta.

    Cinco piezas, cada una con su propia funcion para poder probarlas por
    separado: las capas y su vaiven, la Figura_Girable con sus vistas y su
    Sombra_Contacto, el Balon_Esfera con su degradacion de dos dimensiones, el
    Modo_Inerte y, al final, Movimiento_Reducido seguido de impresion.

    `build_html.estilo_css()` **no** llama a esta funcion: llama a `css_sin_modos`,
    `css_reduccion_cuerpo` y `css_impresion` por separado, porque los dos bloques
    finales tienen que caer en su lugar del orden obligado (criterio 11.7) y no en
    medio de la hoja. Esta funcion se conserva como la vista completa del bloque,
    que es lo que verifican las pruebas del Mundo_Hero, y su salida es byte a byte
    la concatenacion de las cinco piezas.

    Cero `url(`, cero `http`, cero `position:fixed`, cero `tabindex` y ningun
    `width` ni `min-width` en pixeles: lo comprueban las pruebas del bloque.
    """
    return "".join((css_sin_modos(), _css_movimiento_reducido()))
