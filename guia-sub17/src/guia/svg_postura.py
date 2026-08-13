"""Generador_SVG: line art parametrico de los ocho Diagrama_Postura.

Modulo emisor de la feature `imagenes-reales-hero-interactivo`. Ninguna figura
se dibuja a mano: las ocho salen de **un solo esqueleto parametrico** de
diecisiete articulaciones y dieciseis huesos de longitud fija, mas un conjunto
de angulos por pose.

Convenciones de emision que reutiliza de `viz.py`:

* formateo numerico con `_num` (tres decimales, recorte de ceros) para bytes
  reproducibles;
* escapado con `html.escape`;
* acumulacion de fragmentos en `list[str]` y union final con `''.join`.

Convenciones de datos que reutiliza de `diagramas_postura.py` (**no** las
duplica): `ARTICULACIONES`, `ETIQUETAS_ANATOMIA`, `ETIQUETAS_DERIVADAS` y
`ARTICULACION_POR_ETIQUETA`.

Determinismo total (criterio de la Property 8): la misma pose y las mismas
etiquetas producen **bytes identicos**. En el camino de emision no hay
aleatoriedad, ni `set`, ni recorrido de diccionario sin orden declarado: se
itera siempre sobre tuplas (`HUESOS`, `ARTICULACIONES`, `d.etiquetas`,
`d.fases`) y los diccionarios se usan solo como tablas de consulta.

Decision geometrica registrada (esqueleto y `viewBox`): las longitudes de
`HUESOS` estan declaradas en el **lienzo canonico** de `ANCHO_CANONICO` x
`ALTO_CANONICO` unidades. `esqueleto()` proyecta ese lienzo al `viewBox` pedido
con una escala **uniforme** (`escala_figura`) y lo centra, de modo que todo
punto articulado cae dentro del `viewBox` para cualquier par de dimensiones
validas -- incluido el caso degenerado de 1x1 declarado. La consecuencia
probada es doble: la longitud de cada hueso es la declarada multiplicada por esa
escala, **igual en las ocho poses** (tolerancia 1e-6), y exactamente la
declarada cuando el `viewBox` es el canonico.

Prohibiciones del marcado (criterio 14.15): cero `<image>`, cero `<img>`, cero
atributos de evento (`on*`), cero `url(`, cero `http` y cero `tabindex`. Por eso
el `<svg>` **no** lleva `xmlns`: su valor es una URL y el SVG siempre viaja en
linea dentro del HTML, donde el espacio de nombres es implicito.

Reglas del proyecto: Python 3.11+, solo libreria estandar y **ningun `assert`**
(todo invariante con `raise ErrorAsset(...)`).

_Requirements: 4.3, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9,
14.10, 14.15, 14.17, 15.17, 15.18, 15.19_
"""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, get_args

from . import afm
from . import diagramas_postura as dp
from . import paleta
from .errores import E_ASSET_INVALIDO, ErrorAsset

__all__ = [
    "FACTOR_VIEWBOX",
    "FACTOR_VISTA",
    "ANCHO_REFERENCIA_PX",
    "ANCHO_CANONICO",
    "ALTO_CANONICO",
    "num",
    "Articulacion",
    "Punto",
    "HUESOS",
    "ANGULOS_BASE",
    "Pose",
    "POSES",
    "pose_de",
    "escala_figura",
    "esqueleto",
    "esqueleto_canonico",
    "largo_hueso",
    "validar_poses",
    "COLOR_CONTORNO",
    "COLOR_SILUETA",
    "COLOR_GUIA",
    "COLOR_FLECHA",
    "OPACIDAD_SILUETA",
    "grosor_contorno",
    "grosor_guia",
    "tamano_efectivo_px",
    "tamano_fuente_etiqueta",
    "radio_cabeza",
    "svg_figura",
    "GUIONES_LINEA_MEDIA",
    "GUIONES_FLECHA",
    "RADIO_CENTRO_GRAVEDAD",
    "LARGO_PUNTA_FLECHA",
    "APERTURA_PUNTA_FLECHA",
    "punto_centro_gravedad",
    "extremos_linea_media",
    "svg_linea_media",
    "svg_flechas",
    "svg_adornos",
    "Etiqueta",
    "MAXIMO_ETIQUETAS_DENTRO",
    "ancho_texto",
    "rectangulo",
    "se_solapan",
    "eje_vertical",
    "punto_de_etiqueta",
    "factor_figura",
    "colocar_etiquetas",
    "svg_etiquetas",
    "ANCLAS_FASE",
    "DESPLAZAMIENTO_FASE",
    "ancla_fase",
    "punto_fase",
    "svg_fases",
    "fases_emitidas",
    "omisiones_de_fase",
    "ancla_ampliacion",
    "svg_zona_ampliacion",
    "caja_figura",
    "PROHIBIDOS_MARCADO",
    "validar_marcado",
    "svg_diagrama",
]

# --------------------------------------------------------------------------- #
# Constantes de escala
# --------------------------------------------------------------------------- #

#: Unidades del `viewBox` por pixel CSS declarado. viewBox = 2 * dimension
#: declarada, para que el line art tenga margen de detalle sin pesar mas.
FACTOR_VIEWBOX: float = 2.0

#: Ancho de referencia al que se escala el SVG en el celular (criterio 15.17).
ANCHO_REFERENCIA_PX: float = 360.0

#: Reduccion de la figura en las Vista_Figura del Proyector_Vistas (21.8).
#:
#: Es la **unica** constante que la ampliacion multi-vista anade a este modulo.
#: Reduce la figura lo justo para que su envolvente **rotada** siga cayendo
#: dentro del `viewBox` con los diez pares de angulos declarados: el azimut mete
#: la profundidad (hasta 30 unidades canonicas por lado en las manos) dentro de
#: la coordenada horizontal, y la elevacion la mete dentro de la vertical, asi
#: que la envolvente crece respecto de la figura de frente. Cuando una
#: articulacion proyectada se sale, este factor **baja**; el punto nunca se
#: recorta (criterio 21.8).
#:
#: No afecta a ninguna emision vigente: `esqueleto`, `escala_figura`,
#: `caja_figura` y `svg_diagrama` conservan su `factor` por defecto de 1.0 y su
#: `factor_figura`, y solo `vistas_figura.esqueleto_vista` lee esta constante.
FACTOR_VISTA: float = 0.86

#: Ancho del lienzo canonico donde viven las longitudes de `HUESOS`.
ANCHO_CANONICO: float = 720.0

#: Alto del lienzo canonico donde viven las longitudes de `HUESOS`.
ALTO_CANONICO: float = 1080.0

#: Margen libre que toda articulacion respeta dentro del lienzo canonico. Es lo
#: que garantiza `validar_poses()` y, por la escala uniforme, lo que hace que
#: todo punto caiga dentro del `viewBox` real.
MARGEN_CANONICO: float = 20.0

#: Punto de arranque de la cinematica directa: la **cadera media**, que en el
#: esqueleto es la articulacion `torso`. Centrada en el lienzo canonico.
RAIZ_CANONICA: tuple[float, float] = (360.0, 620.0)

#: Radio del circulo de la cabeza, en unidades canonicas.
RADIO_CABEZA: float = 52.0

#: Separacion del arco del cabello recogido respecto del circulo de la cabeza.
#: Es positiva a proposito: asi ningun elemento del cabello cae **dentro** del
#: circulo de la cabeza (criterio 14.4 y Property 5).
HOLGURA_CABELLO: float = 5.0

#: Radio del mono del cabello recogido, detras del cuello.
RADIO_MONO: float = 22.0

#: Holgura total que la cabeza necesita a su alrededor: su radio mas el mono
#: tangente (que anade su diametro). Es lo que `validar_poses()` reserva.
HOLGURA_CABEZA: float = RADIO_CABEZA + 2.0 * RADIO_MONO


# --------------------------------------------------------------------------- #
# Articulaciones y huesos
# --------------------------------------------------------------------------- #

#: Las diecisiete articulaciones del esqueleto. La tupla canonica vive en
#: `diagramas_postura.ARTICULACIONES`; este `Literal` existe solo para el tipado
#: y `validar_poses()` comprueba que los dos no puedan desincronizarse.
Articulacion = Literal[
    "cabeza",
    "cuello",
    "hombro_i",
    "hombro_d",
    "codo_i",
    "codo_d",
    "mano_i",
    "mano_d",
    "torso",
    "cadera_i",
    "cadera_d",
    "rodilla_i",
    "rodilla_d",
    "tobillo_i",
    "tobillo_d",
    "pie_i",
    "pie_d",
]

#: Un punto del plano, en unidades del `viewBox`.
Punto = tuple[float, float]

#: Los dieciseis huesos, como `(origen, destino, longitud_canonica)`. El orden es
#: **topologico**: todo origen ya esta resuelto cuando le toca el turno a su
#: hueso, de modo que la cinematica directa sea un solo recorrido de la tupla.
#: La longitud es fija: es la misma en las ocho poses (invariante de Property 5).
HUESOS: tuple[tuple[str, str, float], ...] = (
    ("torso", "cuello", 250.0),
    ("cuello", "cabeza", 70.0),
    ("cuello", "hombro_i", 80.0),
    ("cuello", "hombro_d", 80.0),
    ("hombro_i", "codo_i", 150.0),
    ("hombro_d", "codo_d", 150.0),
    ("codo_i", "mano_i", 130.0),
    ("codo_d", "mano_d", 130.0),
    ("torso", "cadera_i", 70.0),
    ("torso", "cadera_d", 70.0),
    ("cadera_i", "rodilla_i", 180.0),
    ("cadera_d", "rodilla_d", 180.0),
    ("rodilla_i", "tobillo_i", 170.0),
    ("rodilla_d", "tobillo_d", 170.0),
    ("tobillo_i", "pie_i", 60.0),
    ("tobillo_d", "pie_d", 60.0),
)

#: Nombre de cada hueso, `"origen-destino"`, en el orden de `HUESOS`. Es la clave
#: que usan `ANGULOS_BASE` y `Pose.angulos`.
NOMBRES_HUESOS: tuple[str, ...] = tuple(f"{o}-{d}" for o, d, _ in HUESOS)

#: Angulo absoluto de cada hueso en la pose neutra, en grados medidos en sentido
#: antihorario desde el eje +X **visual** (90 apunta hacia arriba en pantalla).
#: La conversion a coordenadas SVG niega el seno, porque la Y del SVG crece
#: hacia abajo.
ANGULOS_BASE: dict[str, float] = {
    "torso-cuello": 90.0,
    "cuello-cabeza": 90.0,
    "cuello-hombro_i": 175.0,
    "cuello-hombro_d": 5.0,
    "hombro_i-codo_i": 255.0,
    "hombro_d-codo_d": 285.0,
    "codo_i-mano_i": 258.0,
    "codo_d-mano_d": 282.0,
    "torso-cadera_i": 178.0,
    "torso-cadera_d": 2.0,
    "cadera_i-rodilla_i": 268.0,
    "cadera_d-rodilla_d": 272.0,
    "rodilla_i-tobillo_i": 269.0,
    "rodilla_d-tobillo_d": 271.0,
    "tobillo_i-pie_i": 250.0,
    "tobillo_d-pie_d": 290.0,
}

#: Huesos que giran con la inclinacion del tronco.
HUESOS_TRONCO: tuple[str, ...] = ("torso-cuello", "cuello-cabeza")

#: Huesos que giran con la inclinacion del tronco **y** con la rotacion de la
#: linea de hombros.
HUESOS_HOMBROS: tuple[str, ...] = ("cuello-hombro_i", "cuello-hombro_d")


# --------------------------------------------------------------------------- #
# Pose
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Pose:
    """Los angulos que derivan una de las ocho figuras del catalogo.

    `angulos` son **desviaciones** en grados sobre `ANGULOS_BASE`, una por hueso
    articulado: con la tupla vacia sale la figura neutra de pie. Declararlas como
    desviaciones deja `anatomia-base` sin ningun numero suelto y hace que cada
    pose se lea como "que cambia respecto de estar de pie".

    `centro_gravedad_x` es la fraccion del ancho del `viewBox` donde cae el eje
    vertical de la pose (0.5 es el centro). `balon` es la posicion del balon en
    fracciones del `viewBox`, o `None` cuando la pose no lo muestra. `flechas`
    son pares `(articulacion_origen, articulacion_destino)`.
    """

    id: str
    inclinacion_tronco: float
    rotacion_hombros: float
    angulos: tuple[tuple[str, float], ...]
    apoyo: str
    centro_gravedad_x: float
    balon: tuple[float, float] | None
    flechas: tuple[tuple[str, str], ...]


#: Las ocho poses, una por entrada del Catalogo_Diagramas y en su mismo orden.
POSES: tuple[Pose, ...] = (
    Pose(
        id="anatomia-base",
        inclinacion_tronco=0.0,
        rotacion_hombros=0.0,
        angulos=(),
        apoyo="pie_i",
        centro_gravedad_x=0.5,
        balon=None,
        flechas=(),
    ),
    Pose(
        id="tiro-empeine",
        inclinacion_tronco=9.0,
        rotacion_hombros=-6.0,
        angulos=(
            ("cadera_d-rodilla_d", 26.0),
            ("rodilla_d-tobillo_d", 14.0),
            ("tobillo_d-pie_d", 22.0),
            ("cadera_i-rodilla_i", -6.0),
            ("hombro_i-codo_i", -34.0),
            ("codo_i-mano_i", -30.0),
            ("hombro_d-codo_d", 26.0),
            ("codo_d-mano_d", 22.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.47,
        balon=(0.63, 0.90),
        flechas=(("rodilla_d", "pie_d"),),
    ),
    Pose(
        id="pase-interior",
        inclinacion_tronco=5.0,
        rotacion_hombros=-4.0,
        angulos=(
            ("cadera_d-rodilla_d", 16.0),
            ("rodilla_d-tobillo_d", 8.0),
            ("tobillo_d-pie_d", 34.0),
            ("hombro_i-codo_i", -26.0),
            ("codo_i-mano_i", -22.0),
            ("hombro_d-codo_d", 18.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.48,
        balon=(0.61, 0.92),
        flechas=(("cadera_d", "pie_d"),),
    ),
    Pose(
        id="control-balon",
        inclinacion_tronco=-6.0,
        rotacion_hombros=6.0,
        angulos=(
            ("cadera_d-rodilla_d", 20.0),
            ("rodilla_d-tobillo_d", -24.0),
            ("tobillo_d-pie_d", 40.0),
            ("cadera_i-rodilla_i", -8.0),
            ("hombro_i-codo_i", -30.0),
            ("codo_i-mano_i", -26.0),
            ("hombro_d-codo_d", 30.0),
            ("codo_d-mano_d", 26.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.49,
        balon=(0.59, 0.86),
        flechas=(("pie_d", "cadera_d"),),
    ),
    Pose(
        id="conduccion",
        inclinacion_tronco=7.0,
        rotacion_hombros=-8.0,
        angulos=(
            ("cadera_d-rodilla_d", 22.0),
            ("rodilla_d-tobillo_d", 10.0),
            ("tobillo_d-pie_d", 26.0),
            ("cadera_i-rodilla_i", -18.0),
            ("rodilla_i-tobillo_i", 16.0),
            ("hombro_i-codo_i", -40.0),
            ("codo_i-mano_i", -34.0),
            ("hombro_d-codo_d", 34.0),
            ("codo_d-mano_d", 28.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.48,
        balon=(0.66, 0.90),
        flechas=(("pie_d", "tobillo_d"),),
    ),
    Pose(
        id="potencia-carrera",
        inclinacion_tronco=13.0,
        rotacion_hombros=-11.0,
        angulos=(
            ("cadera_d-rodilla_d", 34.0),
            ("rodilla_d-tobillo_d", 20.0),
            ("tobillo_d-pie_d", 18.0),
            ("cadera_i-rodilla_i", -10.0),
            ("rodilla_i-tobillo_i", 8.0),
            ("hombro_i-codo_i", -48.0),
            ("codo_i-mano_i", -40.0),
            ("hombro_d-codo_d", 18.0),
            ("codo_d-mano_d", 14.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.46,
        balon=(0.68, 0.90),
        flechas=(("cadera_d", "rodilla_d"), ("rodilla_d", "pie_d")),
    ),
    Pose(
        id="cabeceo-frente",
        inclinacion_tronco=-11.0,
        rotacion_hombros=0.0,
        angulos=(
            ("hombro_i-codo_i", -125.0),
            ("codo_i-mano_i", -148.0),
            ("hombro_d-codo_d", 125.0),
            ("codo_d-mano_d", 148.0),
            ("cadera_d-rodilla_d", 12.0),
            ("rodilla_d-tobillo_d", -8.0),
            ("cadera_i-rodilla_i", -12.0),
            ("rodilla_i-tobillo_i", 8.0),
        ),
        apoyo="pie_d",
        centro_gravedad_x=0.5,
        balon=(0.5, 0.2),
        flechas=(("cuello", "cabeza"),),
    ),
    Pose(
        id="pase-largo-empeine",
        inclinacion_tronco=-9.0,
        rotacion_hombros=-6.0,
        angulos=(
            ("cadera_d-rodilla_d", 28.0),
            ("rodilla_d-tobillo_d", 16.0),
            ("tobillo_d-pie_d", 14.0),
            ("cadera_i-rodilla_i", -6.0),
            ("hombro_i-codo_i", -24.0),
            ("codo_i-mano_i", -20.0),
            ("hombro_d-codo_d", 24.0),
            ("codo_d-mano_d", 20.0),
        ),
        apoyo="pie_i",
        centro_gravedad_x=0.48,
        balon=(0.64, 0.92),
        flechas=(("rodilla_d", "pie_d"),),
    ),
)


def pose_de(id_: str) -> Pose:
    """Pose declarada para el Diagrama_Postura `id_`."""
    for pose in POSES:
        if pose.id == id_:
            return pose
    raise ErrorAsset(
        f"no hay pose declarada para el diagrama {id_!r}",
        detalle={"id": id_},
        codigo=E_ASSET_INVALIDO,
    )


# --------------------------------------------------------------------------- #
# Cinematica directa
# --------------------------------------------------------------------------- #


def _giro_extra(nombre_hueso: str, pose: Pose) -> float:
    """Grados que la pose anade a `nombre_hueso` por inclinacion y rotacion.

    La inclinacion positiva echa el tronco hacia el lado que mira la jugadora (la
    derecha del dibujo), asi que **resta** angulo respecto del eje vertical.
    """
    if nombre_hueso in HUESOS_TRONCO:
        return -pose.inclinacion_tronco
    if nombre_hueso in HUESOS_HOMBROS:
        return -pose.inclinacion_tronco - pose.rotacion_hombros
    return 0.0


@lru_cache(maxsize=None)
def esqueleto_canonico(pose: Pose) -> tuple[tuple[str, Punto], ...]:
    """Articulaciones de `pose` en el lienzo canonico, en orden declarado.

    Cinematica directa de un solo recorrido de `HUESOS`: cada destino se coloca
    a la longitud declarada de su hueso desde su origen, en la direccion
    `ANGULOS_BASE + desviacion de la pose + giro de tronco u hombros`. Devuelve
    una tupla (no un diccionario) para que el resultado cacheado sea inmutable.
    """
    desviaciones: dict[str, float] = dict(pose.angulos)
    puntos: dict[str, Punto] = {"torso": RAIZ_CANONICA}
    for origen, destino, largo in HUESOS:
        nombre: str = f"{origen}-{destino}"
        grados: float = (
            ANGULOS_BASE[nombre]
            + desviaciones.get(nombre, 0.0)
            + _giro_extra(nombre, pose)
        )
        radianes: float = math.radians(grados)
        px, py = puntos[origen]
        puntos[destino] = (
            px + largo * math.cos(radianes),
            py - largo * math.sin(radianes),
        )
    return tuple((nombre, puntos[nombre]) for nombre in dp.ARTICULACIONES)


def escala_figura(ancho_vb: float, alto_vb: float, factor: float = 1.0) -> float:
    """Escala **uniforme** del lienzo canonico al `viewBox` pedido.

    Uniforme (el mismo factor en X y en Y) para que la figura no se deforme y
    para que la razon entre longitudes de hueso se conserve. `factor` la reduce
    todavia mas: el modo FUERA de las etiquetas lo usa para liberar los margenes.
    """
    if ancho_vb <= 0.0 or alto_vb <= 0.0:
        raise ErrorAsset(
            "el viewBox exige ancho y alto positivos, no "
            f"({ancho_vb!r}, {alto_vb!r})",
            detalle={"ancho": ancho_vb, "alto": alto_vb},
            codigo=E_ASSET_INVALIDO,
        )
    if factor <= 0.0:
        raise ErrorAsset(
            f"el factor de reduccion de la figura debe ser positivo, no {factor!r}",
            detalle={"factor": factor},
            codigo=E_ASSET_INVALIDO,
        )
    return min(ancho_vb / ANCHO_CANONICO, alto_vb / ALTO_CANONICO) * factor


def _traslado(
    ancho_vb: float, alto_vb: float, escala: float
) -> tuple[float, float]:
    """Desplazamiento que centra el lienzo canonico escalado en el `viewBox`."""
    return (
        (ancho_vb - ANCHO_CANONICO * escala) / 2.0,
        (alto_vb - ALTO_CANONICO * escala) / 2.0,
    )


def esqueleto(
    pose: Pose, ancho_vb: float, alto_vb: float, *, factor: float = 1.0
) -> dict[str, Punto]:
    """Articulaciones de `pose` en unidades del `viewBox`.

    El diccionario se construye en el orden de `diagramas_postura.ARTICULACIONES`,
    asi que recorrerlo es deterministico. Todo punto cae dentro del `viewBox`,
    porque el lienzo canonico se escala de forma uniforme y se centra, y porque
    `validar_poses()` garantiza que ninguna articulacion sale del lienzo.
    """
    escala: float = escala_figura(ancho_vb, alto_vb, factor)
    dx, dy = _traslado(ancho_vb, alto_vb, escala)
    puntos: dict[str, Punto] = {}
    for nombre, (cx, cy) in esqueleto_canonico(pose):
        puntos[nombre] = (dx + cx * escala, dy + cy * escala)
    return puntos


def largo_hueso(
    nombre_hueso: str, ancho_vb: float, alto_vb: float, *, factor: float = 1.0
) -> float:
    """Longitud de `nombre_hueso` en unidades del `viewBox`.

    Es la longitud canonica declarada multiplicada por `escala_figura`, asi que
    en el lienzo canonico (`720 x 1080`) coincide exactamente con la declarada.
    """
    for origen, destino, largo in HUESOS:
        if f"{origen}-{destino}" == nombre_hueso:
            return largo * escala_figura(ancho_vb, alto_vb, factor)
    raise ErrorAsset(
        f"hueso desconocido: {nombre_hueso!r}",
        detalle={"hueso": nombre_hueso},
        codigo=E_ASSET_INVALIDO,
    )


# --------------------------------------------------------------------------- #
# Validador del esqueleto y de las poses
# --------------------------------------------------------------------------- #


def validar_poses() -> None:
    """Comprueba el esqueleto parametrico y las ocho poses (criterios 14.1, 14.4).

    Todo con `raise ErrorAsset`, ningun `assert`:

    1. El `Literal` `Articulacion` y `diagramas_postura.ARTICULACIONES` declaran
       las mismas diecisiete articulaciones, en el mismo orden.
    2. `HUESOS` tiene dieciseis huesos de longitud positiva, con nombres unicos,
       origen ya resuelto (orden topologico) y un destino distinto cada uno, de
       modo que las diecisiete articulaciones queden cubiertas por la raiz mas
       los dieciseis destinos.
    3. `ANGULOS_BASE` cubre exactamente los dieciseis huesos.
    4. `POSES` tiene ocho entradas, con los identificadores del catalogo y en su
       orden; sus desviaciones nombran huesos reales sin repetir; su apoyo, sus
       flechas y su articulacion de anclaje existen; su centro de gravedad vive
       en (0, 1) y su balon, cuando lo declara, tambien.
    5. Toda articulacion de toda pose cae dentro del lienzo canonico con
       `MARGEN_CANONICO` de holgura, contando el circulo de la cabeza y el
       cabello recogido.
    """
    esperadas: tuple[str, ...] = dp.ARTICULACIONES
    if tuple(get_args(Articulacion)) != esperadas:
        raise ErrorAsset(
            "el Literal Articulacion no coincide con "
            "diagramas_postura.ARTICULACIONES",
            detalle={"literal": tuple(get_args(Articulacion))},
            codigo=E_ASSET_INVALIDO,
        )
    if len(esperadas) != 17:
        raise ErrorAsset(
            f"el esqueleto exige 17 articulaciones, no {len(esperadas)}",
            detalle={"cantidad": len(esperadas)},
            codigo=E_ASSET_INVALIDO,
        )

    if len(HUESOS) != 16:
        raise ErrorAsset(
            f"el esqueleto exige 16 huesos, no {len(HUESOS)}",
            detalle={"cantidad": len(HUESOS)},
            codigo=E_ASSET_INVALIDO,
        )
    if len(set(NOMBRES_HUESOS)) != len(NOMBRES_HUESOS):
        raise ErrorAsset("HUESOS repite algun hueso", codigo=E_ASSET_INVALIDO)

    resueltas: list[str] = ["torso"]
    for origen, destino, largo in HUESOS:
        nombre: str = f"{origen}-{destino}"
        if origen not in esperadas or destino not in esperadas:
            raise ErrorAsset(
                f"hueso {nombre!r} nombra una articulacion inexistente",
                detalle={"hueso": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        if largo <= 0.0:
            raise ErrorAsset(
                f"hueso {nombre!r} con longitud no positiva: {largo!r}",
                detalle={"hueso": nombre, "largo": largo},
                codigo=E_ASSET_INVALIDO,
            )
        if origen not in resueltas:
            raise ErrorAsset(
                f"hueso {nombre!r} rompe el orden topologico: su origen "
                "todavia no esta colocado",
                detalle={"hueso": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        if destino in resueltas:
            raise ErrorAsset(
                f"hueso {nombre!r} vuelve a colocar {destino!r}",
                detalle={"hueso": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        resueltas.append(destino)
    if tuple(sorted(resueltas)) != tuple(sorted(esperadas)):
        raise ErrorAsset(
            "los dieciseis huesos no cubren las diecisiete articulaciones",
            detalle={"cubiertas": tuple(sorted(resueltas))},
            codigo=E_ASSET_INVALIDO,
        )

    if tuple(sorted(ANGULOS_BASE)) != tuple(sorted(NOMBRES_HUESOS)):
        raise ErrorAsset(
            "ANGULOS_BASE no cubre exactamente los dieciseis huesos",
            detalle={"declarados": tuple(sorted(ANGULOS_BASE))},
            codigo=E_ASSET_INVALIDO,
        )

    if len(POSES) != len(dp.CATALOGO):
        raise ErrorAsset(
            f"se declaran {len(POSES)} poses y {len(dp.CATALOGO)} diagramas",
            detalle={"poses": len(POSES), "diagramas": len(dp.CATALOGO)},
            codigo=E_ASSET_INVALIDO,
        )
    for indice, pose in enumerate(POSES):
        _validar_pose(pose, indice, esperadas)


def _validar_pose(pose: Pose, indice: int, articulaciones: tuple[str, ...]) -> None:
    """Invariantes de una sola pose. Extraida para que el fallo nombre la pose."""
    esperado: str = dp.IDS[indice]
    if pose.id != esperado:
        raise ErrorAsset(
            f"la pose {indice} deberia ser {esperado!r} y es {pose.id!r}",
            detalle={"indice": indice, "id": pose.id, "esperado": esperado},
            codigo=E_ASSET_INVALIDO,
        )

    vistos: list[str] = []
    for nombre, _grados in pose.angulos:
        if nombre not in NOMBRES_HUESOS:
            raise ErrorAsset(
                f"{pose.id}: desviacion sobre un hueso inexistente: {nombre!r}",
                detalle={"id": pose.id, "hueso": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        if nombre in vistos:
            raise ErrorAsset(
                f"{pose.id}: desviacion repetida para el hueso {nombre!r}",
                detalle={"id": pose.id, "hueso": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        vistos.append(nombre)

    if pose.apoyo not in articulaciones:
        raise ErrorAsset(
            f"{pose.id}: apoyo en una articulacion inexistente: {pose.apoyo!r}",
            detalle={"id": pose.id, "apoyo": pose.apoyo},
            codigo=E_ASSET_INVALIDO,
        )
    if not 0.0 < pose.centro_gravedad_x < 1.0:
        raise ErrorAsset(
            f"{pose.id}: centro de gravedad fuera de (0, 1): "
            f"{pose.centro_gravedad_x!r}",
            detalle={"id": pose.id, "centro": pose.centro_gravedad_x},
            codigo=E_ASSET_INVALIDO,
        )
    if pose.balon is not None:
        bx, by = pose.balon
        if not (0.0 < bx < 1.0 and 0.0 < by < 1.0):
            raise ErrorAsset(
                f"{pose.id}: balon fuera del viewBox: {pose.balon!r}",
                detalle={"id": pose.id, "balon": pose.balon},
                codigo=E_ASSET_INVALIDO,
            )
    for origen, destino in pose.flechas:
        if origen not in articulaciones or destino not in articulaciones:
            raise ErrorAsset(
                f"{pose.id}: flecha entre articulaciones inexistentes: "
                f"{(origen, destino)!r}",
                detalle={"id": pose.id, "flecha": (origen, destino)},
                codigo=E_ASSET_INVALIDO,
            )
        if origen == destino:
            raise ErrorAsset(
                f"{pose.id}: flecha de {origen!r} a si misma",
                detalle={"id": pose.id, "flecha": (origen, destino)},
                codigo=E_ASSET_INVALIDO,
            )

    for nombre, (cx, cy) in esqueleto_canonico(pose):
        radio: float = HOLGURA_CABEZA if nombre == "cabeza" else 0.0
        if (
            cx - radio < MARGEN_CANONICO
            or cx + radio > ANCHO_CANONICO - MARGEN_CANONICO
            or cy - radio < MARGEN_CANONICO
            or cy + radio > ALTO_CANONICO - MARGEN_CANONICO
        ):
            raise ErrorAsset(
                f"{pose.id}: la articulacion {nombre!r} sale del lienzo "
                f"canonico en {(round(cx, 3), round(cy, 3))!r}",
                detalle={"id": pose.id, "articulacion": nombre},
                codigo=E_ASSET_INVALIDO,
            )


# --------------------------------------------------------------------------- #
# Colores: solo Paleta_Guia, siempre por `paleta.py`
# --------------------------------------------------------------------------- #
#
# Se emite el **hex** de la Paleta_Guia, no `var(--token)`: el SVG debe verse
# igual aunque se extraiga del HTML, y el Guardarrail_Recursos exige que todo
# color pertenezca a `paleta.COLORES_PALETA`. La correspondencia con los tokens
# CSS del Requisito 16 queda registrada en `TOKEN_POR_COLOR`.

#: Contorno de la figura y texto de las Etiqueta_Anatomica (`--azul-profundo`).
COLOR_CONTORNO: str = paleta.WEB_HERO_TINTA

#: Relleno de la silueta (`--azul-cielo`).
COLOR_SILUETA: str = paleta.WEB_HERO_CIELO

#: Lineas guia, linea media y trazos secundarios (`--azul-linea`).
COLOR_GUIA: str = paleta.WEB_HERO_LINEA

#: Flechas de movimiento (`--coral-alerta`).
COLOR_FLECHA: str = paleta.WEB_HERO_CORAL

#: Token CSS del Requisito 16 al que corresponde cada color emitido.
TOKEN_POR_COLOR: dict[str, str] = {
    COLOR_CONTORNO: "--azul-profundo",
    COLOR_SILUETA: "--azul-cielo",
    COLOR_GUIA: "--azul-linea",
    COLOR_FLECHA: "--coral-alerta",
}

#: Opacidad del relleno de la silueta (criterio 14.5: 0.12 o menor).
OPACIDAD_SILUETA: float = 0.12

#: Patron de guiones de la linea media y de las flechas de movimiento.
GUIONES_LINEA_MEDIA: str = "14 10"
GUIONES_FLECHA: str = "16 10"


# --------------------------------------------------------------------------- #
# Grosores de trazo (criterios 14.2, 14.3 y 14.7)
# --------------------------------------------------------------------------- #

#: Pixeles equivalentes del trazo de contorno al ancho declarado (criterio 14.2).
PIXELES_CONTORNO: float = 2.0

#: Pixeles equivalentes de la linea guia al ancho declarado (criterio 14.7).
PIXELES_GUIA: float = 1.0


def _validar_anchos(ancho_vb: float, ancho_declarado: float) -> None:
    """Comprueba que los dos anchos son positivos antes de dividir."""
    if ancho_vb <= 0.0:
        raise ErrorAsset(
            f"el ancho del viewBox debe ser positivo, no {ancho_vb!r}",
            detalle={"ancho_vb": ancho_vb},
            codigo=E_ASSET_INVALIDO,
        )
    if ancho_declarado <= 0.0:
        raise ErrorAsset(
            f"el ancho declarado debe ser positivo, no {ancho_declarado!r}",
            detalle={"ancho_declarado": ancho_declarado},
            codigo=E_ASSET_INVALIDO,
        )


def grosor_contorno(ancho_vb: float, ancho_declarado: float) -> float:
    """Grosor del trazo de contorno: dos pixeles al ancho declarado (14.2).

    Funcion pura. Con `ancho_vb = 720` y `ancho_declarado = 360` vale `4`.
    Todos los trazos de contorno de un mismo diagrama comparten este **unico**
    valor (criterio 14.3), porque todos lo piden a esta funcion con los mismos
    dos argumentos.
    """
    _validar_anchos(ancho_vb, ancho_declarado)
    return PIXELES_CONTORNO * ancho_vb / ancho_declarado


def grosor_guia(ancho_vb: float, ancho_declarado: float) -> float:
    """Grosor de la linea guia de una Etiqueta_Anatomica: un pixel (14.7).

    Es exactamente la mitad de `grosor_contorno` con los mismos argumentos.
    """
    _validar_anchos(ancho_vb, ancho_declarado)
    return PIXELES_GUIA * ancho_vb / ancho_declarado


# --------------------------------------------------------------------------- #
# Tipografia de las etiquetas (criterio 15.17)
# --------------------------------------------------------------------------- #

#: Tamano efectivo minimo de una Etiqueta_Anatomica, en pixeles CSS (15.17).
TAMANO_EFECTIVO_MINIMO: float = 12.0


def tamano_efectivo_px(font_size_vb: float, ancho_vb: float) -> float:
    """Pixeles CSS que rinde `font_size_vb` cuando el SVG se escala a 360 px.

    El SVG fluye al ancho del contenedor, que en el celular es el Ancho_Base de
    360 px, asi que el factor de escala es `360 / ancho_vb`.
    """
    if ancho_vb <= 0.0:
        raise ErrorAsset(
            f"el ancho del viewBox debe ser positivo, no {ancho_vb!r}",
            detalle={"ancho_vb": ancho_vb},
            codigo=E_ASSET_INVALIDO,
        )
    return font_size_vb * ANCHO_REFERENCIA_PX / ancho_vb


def tamano_fuente_etiqueta(ancho_vb: float) -> float:
    """Tamano de fuente, en unidades del `viewBox`, de toda Etiqueta_Anatomica.

    `ceil(12 * ancho_vb / 360) + 2`: el techo cubre la division inexacta y el
    `+2` deja margen, de modo que `tamano_efectivo_px(tamano_fuente_etiqueta(w),
    w) >= 12` para **todo** `w` positivo (criterio 15.17). Con `ancho_vb = 720`
    vale 26 unidades, que rinden 13 px efectivos.
    """
    if ancho_vb <= 0.0:
        raise ErrorAsset(
            f"el ancho del viewBox debe ser positivo, no {ancho_vb!r}",
            detalle={"ancho_vb": ancho_vb},
            codigo=E_ASSET_INVALIDO,
        )
    exacto: float = TAMANO_EFECTIVO_MINIMO * ancho_vb / ANCHO_REFERENCIA_PX
    return float(math.ceil(exacto) + 2)


# --------------------------------------------------------------------------- #
# Utilidades de emision (convenciones de `viz.py`)
# --------------------------------------------------------------------------- #


def _num(valor: float) -> str:
    """Formatea un numero con 3 decimales, recortando ceros sobrantes."""
    texto: str = f"{valor:.3f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


#: `_num` expuesto en publico: **un solo formateo** en todo el proyecto (21.11).
#:
#: El Proyector_Vistas emite numeros y tiene que hacerlo con exactamente el mismo
#: criterio que el Generador_SVG (tres decimales, recorte de ceros finales), no
#: con una copia paralela que pueda divergir. Es un alias del mismo objeto
#: funcion, no una segunda definicion: `num is _num` es verdadero.
num = _num


def _esc(texto: str) -> str:
    """Escapa texto para insertarlo con seguridad en el SVG."""
    return html.escape(texto, quote=True)


def _direccion(grados: float) -> tuple[float, float]:
    """Vector unitario de `grados`, con la Y del SVG (que crece hacia abajo)."""
    radianes: float = math.radians(grados)
    return (math.cos(radianes), -math.sin(radianes))


def _angulo_entre(desde: Punto, hasta: Punto) -> float:
    """Grados del vector `desde -> hasta`, en la misma convencion visual."""
    return math.degrees(math.atan2(-(hasta[1] - desde[1]), hasta[0] - desde[0]))


def _linea(clase: str, a: Punto, b: Punto, color: str, grosor: float,
           guiones: str = "") -> str:
    """Emite un `<line>` con clase, color y grosor explicitos."""
    partes: list[str] = [
        f'<line class="{clase}" x1="{_num(a[0])}" y1="{_num(a[1])}"',
        f' x2="{_num(b[0])}" y2="{_num(b[1])}"',
        f' stroke="{color}" stroke-width="{_num(grosor)}" stroke-linecap="round"',
    ]
    if guiones:
        partes.append(f' stroke-dasharray="{guiones}"')
    partes.append(" />")
    return "".join(partes)


# --------------------------------------------------------------------------- #
# Cabeza, cabello recogido y silueta
# --------------------------------------------------------------------------- #

#: Semiapertura del arco del cabello recogido, en grados sobre el eje de la
#: cabeza. 95 grados por lado deja el arco por encima de las orejas.
APERTURA_CABELLO: float = 95.0

#: Angulo del mono del cabello respecto del eje de la cabeza: detras y abajo.
ANGULO_MONO: float = 145.0

#: Orden de las articulaciones que recorre el poligono de la silueta. Va por el
#: costado derecho de la figura hacia abajo, cruza por los pies y vuelve por el
#: izquierdo. Arranca y cierra en `cuello`, **nunca** pasa por `cabeza`: asi el
#: relleno no entra en el circulo de la cabeza (criterio 14.4).
ORDEN_SILUETA: tuple[str, ...] = (
    "cuello",
    "hombro_d",
    "codo_d",
    "mano_d",
    "cadera_d",
    "rodilla_d",
    "tobillo_d",
    "pie_d",
    "pie_i",
    "tobillo_i",
    "rodilla_i",
    "cadera_i",
    "mano_i",
    "codo_i",
    "hombro_i",
)


def radio_cabeza(escala: float) -> float:
    """Radio del circulo de la cabeza en unidades del `viewBox`."""
    return RADIO_CABEZA * escala


def _svg_cabeza(
    puntos: dict[str, Punto], escala: float, grosor: float, partes: list[str]
) -> None:
    """Emite el circulo de la cabeza y el grupo del cabello recogido.

    El rostro va **sin ningun rasgo** (criterio 14.4): dentro del circulo no se
    emite ni un elemento. El cabello recogido son dos trazos que viven fuera del
    circulo: un arco a `HOLGURA_CABELLO` unidades por encima y un mono tangente
    por detras del cuello.
    """
    cabeza: Punto = puntos["cabeza"]
    cuello: Punto = puntos["cuello"]
    radio: float = radio_cabeza(escala)
    eje: float = _angulo_entre(cuello, cabeza)

    partes.append(
        f'<circle class="contorno cabeza" cx="{_num(cabeza[0])}" '
        f'cy="{_num(cabeza[1])}" r="{_num(radio)}" fill="none" '
        f'stroke="{COLOR_CONTORNO}" stroke-width="{_num(grosor)}" />'
    )

    radio_pelo: float = radio + HOLGURA_CABELLO * escala
    dx1, dy1 = _direccion(eje + APERTURA_CABELLO)
    dx2, dy2 = _direccion(eje - APERTURA_CABELLO)
    inicio: Punto = (cabeza[0] + radio_pelo * dx1, cabeza[1] + radio_pelo * dy1)
    fin: Punto = (cabeza[0] + radio_pelo * dx2, cabeza[1] + radio_pelo * dy2)

    radio_mono: float = RADIO_MONO * escala
    dxm, dym = _direccion(eje + ANGULO_MONO)
    distancia: float = radio + radio_mono
    mono: Punto = (cabeza[0] + distancia * dxm, cabeza[1] + distancia * dym)

    partes.append('<g class="cabello-recogido">')
    partes.append(
        f'<path class="contorno cabello" d="M {_num(inicio[0])} '
        f"{_num(inicio[1])} A {_num(radio_pelo)} {_num(radio_pelo)} 0 0 1 "
        f'{_num(fin[0])} {_num(fin[1])}" fill="none" '
        f'stroke="{COLOR_CONTORNO}" stroke-width="{_num(grosor)}" />'
    )
    partes.append(
        f'<circle class="contorno mono" cx="{_num(mono[0])}" '
        f'cy="{_num(mono[1])}" r="{_num(radio_mono)}" fill="none" '
        f'stroke="{COLOR_CONTORNO}" stroke-width="{_num(grosor)}" />'
    )
    partes.append("</g>")


def _svg_silueta(puntos: dict[str, Punto], partes: list[str]) -> None:
    """Emite el poligono cerrado de la silueta con su relleno translucido."""
    coordenadas: list[str] = []
    for nombre in ORDEN_SILUETA:
        px, py = puntos[nombre]
        coordenadas.append(f"{_num(px)},{_num(py)}")
    partes.append(
        f'<polygon class="silueta" points="{" ".join(coordenadas)}" '
        f'fill="{COLOR_SILUETA}" fill-opacity="{_num(OPACIDAD_SILUETA)}" '
        f'stroke="none" />'
    )


def _svg_contorno(
    puntos: dict[str, Punto], escala: float, grosor: float, partes: list[str]
) -> None:
    """Emite un trazo de contorno por hueso, todos con el **mismo** grosor.

    El hueso `cuello-cabeza` no se dibuja completo: se corta en el borde del
    circulo de la cabeza, para que ningun trazo entre en el rostro (14.4).
    """
    radio: float = radio_cabeza(escala)
    for origen, destino, _largo in HUESOS:
        a: Punto = puntos[origen]
        b: Punto = puntos[destino]
        if destino == "cabeza":
            eje: float = _angulo_entre(a, b)
            dx, dy = _direccion(eje)
            b = (b[0] - radio * dx, b[1] - radio * dy)
        partes.append(
            _linea(f"contorno hueso-{origen}-{destino}", a, b, COLOR_CONTORNO, grosor)
        )


def svg_figura(
    pose: Pose,
    ancho_vb: float,
    alto_vb: float,
    ancho_declarado: float,
    *,
    factor: float = 1.0,
) -> str:
    """Marcado de la figura de `pose`: silueta, contorno, cabeza y cabello.

    Es la parte del SVG que depende solo del esqueleto. Las Etiqueta_Anatomica,
    la linea media, el centro de gravedad, las flechas y las Fase_Numerada se
    montan encima en `svg_diagrama`.

    Orden de emision fijo (relleno, contorno, cabeza) para que dos llamadas con
    los mismos argumentos devuelvan **bytes identicos**.
    """
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    escala: float = escala_figura(ancho_vb, alto_vb, factor)
    grosor: float = grosor_contorno(ancho_vb, ancho_declarado)
    partes: list[str] = ['<g class="figura">']
    _svg_silueta(puntos, partes)
    _svg_contorno(puntos, escala, grosor, partes)
    _svg_cabeza(puntos, escala, grosor, partes)
    partes.append("</g>")
    return "".join(partes)


# --------------------------------------------------------------------------- #
# Linea media, centro de gravedad y flechas de movimiento (14.8 y 14.9)
# --------------------------------------------------------------------------- #
#
# Por que estos tres adornos **no** viven dentro de `svg_figura`: el criterio
# 14.4 exige que el circulo de la cabeza quede sin ningun elemento dentro, y la
# Property 5 lo comprueba sobre el marcado que devuelve `svg_figura`. La linea
# media cruza el cuerpo de arriba abajo y `cabeceo-frente` declara la flecha
# `cuello -> cabeza`, que termina justo en el centro de la cabeza: si estas
# piezas se emitieran ahi, el rostro dejaria de estar vacio. Viven, por tanto,
# como grupos hermanos que `svg_diagrama` monta encima de la figura.

#: Radio del punto relleno del centro de gravedad, en unidades del `viewBox`.
RADIO_CENTRO_GRAVEDAD: float = 9.0

#: Largo de cada tramo de la punta de flecha, en unidades del `viewBox`.
LARGO_PUNTA_FLECHA: float = 26.0

#: Semiapertura de la punta de flecha respecto de su eje, en grados.
APERTURA_PUNTA_FLECHA: float = 26.0


def extremos_linea_media(
    pose: Pose, puntos: dict[str, Punto], ancho_vb: float
) -> tuple[Punto, Punto]:
    """Extremos de la linea media vertical de `pose` (criterio 14.9).

    Las dos X son **la misma**: el eje declarado por la pose. Va del cuello al
    apoyo mas bajo, de modo que cubre el punto medio del tronco (donde se ancla
    la Etiqueta_Anatomica "linea media") y el centro de gravedad.
    """
    eje: float = eje_vertical(pose, ancho_vb)
    arriba: float = puntos["cuello"][1]
    abajo: float = max(puntos["pie_i"][1], puntos["pie_d"][1])
    if abajo <= arriba:
        raise ErrorAsset(
            f"{pose.id}: la linea media queda degenerada entre "
            f"{round(arriba, 3)} y {round(abajo, 3)}",
            detalle={"id": pose.id, "arriba": arriba, "abajo": abajo},
            codigo=E_ASSET_INVALIDO,
        )
    return ((eje, arriba), (eje, abajo))


def punto_centro_gravedad(
    pose: Pose, puntos: dict[str, Punto], ancho_vb: float
) -> Punto:
    """Punto del centro de gravedad: sobre la linea media, a la altura del torso.

    Es el mismo punto al que `punto_de_etiqueta` ancla la Etiqueta_Anatomica
    "centro de gravedad", asi que el rotulo y el punto relleno nunca se separan.
    """
    return (eje_vertical(pose, ancho_vb), puntos["torso"][1])


def svg_linea_media(
    pose: Pose,
    ancho_vb: float,
    alto_vb: float,
    ancho_declarado: float,
    *,
    factor: float = 1.0,
) -> str:
    """Linea media punteada y el **unico** punto de centro de gravedad (14.9).

    La linea lleva `x1 == x2` por construccion y su `stroke-dasharray` viene
    declarado. El punto de centro de gravedad se emite una sola vez y cae
    exactamente sobre esa linea, porque comparte su X y su Y esta entre las dos
    de la linea.
    """
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    grosor: float = grosor_guia(ancho_vb, ancho_declarado)
    arriba, abajo = extremos_linea_media(pose, puntos, ancho_vb)
    centro: Punto = punto_centro_gravedad(pose, puntos, ancho_vb)
    partes: list[str] = ['<g class="eje-corporal">']
    partes.append(
        _linea(
            "linea-media", arriba, abajo, COLOR_GUIA, grosor, GUIONES_LINEA_MEDIA
        )
    )
    partes.append(
        f'<circle class="centro-gravedad" cx="{_num(centro[0])}" '
        f'cy="{_num(centro[1])}" r="{_num(RADIO_CENTRO_GRAVEDAD)}" '
        f'fill="{COLOR_CONTORNO}" />'
    )
    partes.append("</g>")
    return "".join(partes)


def _punta_flecha(desde: Punto, hasta: Punto) -> tuple[Punto, ...]:
    """Los tres puntos de la polilinea que forma la punta de una flecha.

    Punta como **polilinea**, nunca con `marker`: un `marker` obliga a
    `url(#...)` en el atributo, y el criterio 14.15 prohibe `url(` en el marcado.
    """
    largo: float = math.hypot(hasta[0] - desde[0], hasta[1] - desde[1])
    if largo <= 0.0:
        raise ErrorAsset(
            f"flecha degenerada: sus dos extremos coinciden en {hasta!r}",
            detalle={"punto": hasta},
            codigo=E_ASSET_INVALIDO,
        )
    eje: float = _angulo_entre(hasta, desde)
    tramo: float = min(LARGO_PUNTA_FLECHA, largo / 2.0)
    dxi, dyi = _direccion(eje + APERTURA_PUNTA_FLECHA)
    dxd, dyd = _direccion(eje - APERTURA_PUNTA_FLECHA)
    return (
        (hasta[0] + tramo * dxi, hasta[1] + tramo * dyi),
        hasta,
        (hasta[0] + tramo * dxd, hasta[1] + tramo * dyd),
    )


def svg_flechas(
    pose: Pose,
    ancho_vb: float,
    alto_vb: float,
    ancho_declarado: float,
    *,
    factor: float = 1.0,
) -> str:
    """Una flecha de movimiento por par declarado en `Pose.flechas` (14.8).

    Cada flecha son dos elementos, los dos en `--coral-alerta` y los dos con
    `stroke-dasharray` declarado: el asta como `<line>` y la punta como
    `<polyline>` de dos tramos. Sin `marker` y sin `url(`.
    """
    if not pose.flechas:
        return ""
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    grosor: float = grosor_contorno(ancho_vb, ancho_declarado)
    partes: list[str] = ['<g class="flechas">']
    for origen, destino in pose.flechas:
        if origen not in puntos or destino not in puntos:
            raise ErrorAsset(
                f"{pose.id}: la flecha {(origen, destino)!r} nombra una "
                "articulacion que el esqueleto no tiene",
                detalle={"id": pose.id, "flecha": (origen, destino)},
                codigo=E_ASSET_INVALIDO,
            )
        a: Punto = puntos[origen]
        b: Punto = puntos[destino]
        partes.append(
            _linea(
                f"flecha flecha-{origen}-{destino}",
                a,
                b,
                COLOR_FLECHA,
                grosor,
                GUIONES_FLECHA,
            )
        )
        coordenadas: list[str] = [
            f"{_num(px)},{_num(py)}" for px, py in _punta_flecha(a, b)
        ]
        partes.append(
            f'<polyline class="flecha-punta" points="{" ".join(coordenadas)}" '
            f'fill="none" stroke="{COLOR_FLECHA}" '
            f'stroke-width="{_num(grosor)}" stroke-linecap="round" '
            f'stroke-dasharray="{GUIONES_FLECHA}" />'
        )
    partes.append("</g>")
    return "".join(partes)


def svg_adornos(
    pose: Pose,
    ancho_vb: float,
    alto_vb: float,
    ancho_declarado: float,
    *,
    factor: float = 1.0,
) -> str:
    """Linea media, centro de gravedad y flechas, en orden de emision fijo.

    Se monta **encima** de `svg_figura` y **debajo** de las etiquetas, de modo
    que los rotulos queden siempre legibles.
    """
    return "".join(
        (
            svg_linea_media(
                pose, ancho_vb, alto_vb, ancho_declarado, factor=factor
            ),
            svg_flechas(pose, ancho_vb, alto_vb, ancho_declarado, factor=factor),
        )
    )


# --------------------------------------------------------------------------- #
# Etiqueta_Anatomica: puntos, cajas y colocacion determinista
# --------------------------------------------------------------------------- #

#: Maximo de Etiqueta_Anatomica que se emiten junto al contorno (criterio 15.18).
MAXIMO_ETIQUETAS_DENTRO: int = 8

#: Distancia del texto al punto senalado en modo DENTRO, en unidades del
#: `viewBox` (algoritmo del diseno).
DESPLAZAMIENTO_ETIQUETA: float = 34.0

#: Radio del circulo relleno con que termina toda linea guia (criterio 14.7).
RADIO_PUNTO_GUIA: float = 5.0

#: Margen que las cajas de texto respetan respecto del borde del `viewBox`.
MARGEN_ETIQUETA: float = 8.0

#: Alto de la caja de texto como multiplo del tamano de fuente.
ALTURA_LINEA: float = 1.2

#: Separacion vertical minima entre dos cajas de texto contiguas.
SEPARACION_ETIQUETAS: float = 4.0

#: Largo del tramo horizontal con que arranca la polilinea guia en modo FUERA.
GANCHO_GUIA: float = 18.0

#: Holgura sobre el ancho medido del texto. Las metricas son de `Helvetica` y el
#: navegador usa su propia sans-serif, asi que la caja se declara un 8 % mas
#: ancha para que el reparto siga siendo valido con otra fuente.
HOLGURA_TEXTO: float = 1.08

#: Desplazamiento de los puntos derivados del pie (`parte interna`, `parte
#: externa`, `planta`), en unidades canonicas.
DESPLAZAMIENTO_PIE: float = 12.0

#: Angulo de la frente respecto del eje de la cabeza: al frente y arriba.
ANGULO_FRENTE: float = 35.0

#: Reduccion de la figura cuando las etiquetas van junto al contorno. Libera el
#: espacio lateral que necesitan las cajas de texto sin salir del `viewBox`.
FACTOR_FIGURA_DENTRO: float = 0.80

#: Reduccion de la figura cuando las etiquetas van en las dos columnas de los
#: margenes (criterio 15.19). Mas agresiva: las columnas necesitan mas ancho.
FACTOR_FIGURA_FUERA: float = 0.60

#: Banda inferior del `viewBox` que el modo FUERA reserva para la Zona_Tactil de
#: ampliacion. Ninguna caja de texto entra en ella.
BANDA_ZONA_TACTIL: float = 120.0


@dataclass(frozen=True, slots=True)
class Etiqueta:
    """Una Etiqueta_Anatomica ya colocada, lista para emitir.

    `x`/`y` son el punto de anclaje del `<text>` (con `dominant-baseline` al
    centro, asi que `y` es el centro vertical de la caja). `tramos` es la
    polilinea de la linea guia, **del borde del texto al punto senalado**: dos
    puntos en modo DENTRO y tres en modo FUERA.
    """

    texto: str
    articulacion: str
    punto: Punto
    x: float
    y: float
    ancla: str
    ancho: float
    alto: float
    tramos: tuple[Punto, ...]
    dentro: bool


def ancho_texto(texto: str, tamano: float) -> float:
    """Ancho de la caja de `texto` a `tamano` unidades, con su holgura.

    Reutiliza las metricas Core-14 de `afm.py` en vez de estimar con un ancho
    medio por caracter: el reparto de las columnas del modo FUERA depende de que
    esta medida no se quede corta.
    """
    return afm.medir_texto(texto, "Helvetica", tamano) * HOLGURA_TEXTO


def rectangulo(e: Etiqueta) -> tuple[float, float, float, float]:
    """Caja `(x0, y0, x1, y1)` que ocupa el texto de `e`."""
    x0: float = e.x if e.ancla == "start" else e.x - e.ancho
    return (x0, e.y - e.alto / 2.0, x0 + e.ancho, e.y + e.alto / 2.0)


def se_solapan(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    """True si los dos rectangulos comparten area (los bordes no cuentan)."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def eje_vertical(pose: Pose, ancho_vb: float) -> float:
    """Coordenada X de la linea media de `pose` en el `viewBox`."""
    return pose.centro_gravedad_x * ancho_vb


def punto_de_etiqueta(
    etiqueta: str,
    pose: Pose,
    puntos: dict[str, Punto],
    ancho_vb: float,
    escala: float,
) -> Punto:
    """Punto exacto que senala `etiqueta`.

    Las etiquetas de articulacion apuntan a su articulacion. Las de
    `ETIQUETAS_DERIVADAS` apuntan a un punto **derivado** de ella: la frente al
    borde del circulo de la cabeza, la espinilla al medio de rodilla y tobillo,
    el empeine al medio de tobillo y pie, la planta debajo del pie, las partes
    interna y externa a los costados del pie, y la linea media y el centro de
    gravedad al eje vertical de la pose.
    """
    base: str = dp.articulacion_de(etiqueta)
    px, py = puntos[base]
    eje: float = eje_vertical(pose, ancho_vb)
    desplazamiento: float = DESPLAZAMIENTO_PIE * escala

    if etiqueta == "frente":
        cabeza: Punto = puntos["cabeza"]
        angulo: float = _angulo_entre(puntos["cuello"], cabeza) + ANGULO_FRENTE
        dx, dy = _direccion(angulo)
        radio: float = radio_cabeza(escala)
        return (cabeza[0] + radio * dx, cabeza[1] + radio * dy)
    if etiqueta == "espinilla":
        rx, ry = puntos["rodilla_d"]
        tx, ty = puntos["tobillo_d"]
        return ((rx + tx) / 2.0, (ry + ty) / 2.0)
    if etiqueta == "empeine":
        tx, ty = puntos["tobillo_d"]
        return ((tx + px) / 2.0, (ty + py) / 2.0)
    if etiqueta == "planta":
        return (px, py + desplazamiento)
    if etiqueta == "parte interna":
        return (px - desplazamiento if px >= eje else px + desplazamiento, py)
    if etiqueta == "parte externa":
        return (px + desplazamiento if px >= eje else px - desplazamiento, py)
    if etiqueta == "línea media":
        cy: float = (puntos["cuello"][1] + puntos["torso"][1]) / 2.0
        return (eje, cy)
    if etiqueta == "centro de gravedad":
        return (eje, puntos["torso"][1])
    return (px, py)


def factor_figura(cantidad_etiquetas: int) -> float:
    """Reduccion de la figura segun el modo de colocacion de las etiquetas."""
    if cantidad_etiquetas > MAXIMO_ETIQUETAS_DENTRO:
        return FACTOR_FIGURA_FUERA
    return FACTOR_FIGURA_DENTRO


def _repartir_vertical(
    deseadas: list[float], paso: float, limite_alto: float, limite_bajo: float
) -> list[float]:
    """Separa `deseadas` al menos `paso` sin salirse de los limites.

    Pasada hacia abajo (empuja lo que se solapa), pasada hacia arriba (recoge lo
    que se salio por abajo) y comprobacion final. Es el algoritmo clasico de
    reparto de etiquetas: deterministico, sin iteracion abierta y estable
    respecto del orden de entrada.
    """
    if not deseadas:
        return []
    necesario: float = paso * (len(deseadas) - 1)
    if limite_bajo - limite_alto < necesario:
        raise ErrorAsset(
            f"no caben {len(deseadas)} etiquetas con paso {paso!r} en "
            f"[{limite_alto!r}, {limite_bajo!r}]",
            detalle={"cantidad": len(deseadas), "paso": paso},
            codigo=E_ASSET_INVALIDO,
        )
    ys: list[float] = [min(max(y, limite_alto), limite_bajo) for y in deseadas]
    for i in range(1, len(ys)):
        if ys[i] < ys[i - 1] + paso:
            ys[i] = ys[i - 1] + paso
    if ys[-1] > limite_bajo:
        ys[-1] = limite_bajo
        for i in range(len(ys) - 2, -1, -1):
            if ys[i] > ys[i + 1] - paso:
                ys[i] = ys[i + 1] - paso
    return ys


def _clavar_en_lado(
    x: float, ancho: float, ancla: str, eje: float, ancho_vb: float, texto: str
) -> float:
    """Recorta `x` para que la caja quepa **y** no cruce el eje vertical."""
    if ancla == "start":
        x = min(x, ancho_vb - MARGEN_ETIQUETA - ancho)
        x = max(x, eje + DESPLAZAMIENTO_ETIQUETA)
        borde_final: float = x + ancho
        cabe: bool = borde_final <= ancho_vb - MARGEN_ETIQUETA
    else:
        x = max(x, MARGEN_ETIQUETA + ancho)
        x = min(x, eje - DESPLAZAMIENTO_ETIQUETA)
        borde_final = x - ancho
        cabe = borde_final >= MARGEN_ETIQUETA
    if not cabe:
        raise ErrorAsset(
            f"la etiqueta {texto!r} no cabe en su lado del viewBox "
            f"(ancho de caja {round(ancho, 3)} en un viewBox de {ancho_vb})",
            detalle={"etiqueta": texto, "ancho_caja": ancho, "ancho_vb": ancho_vb},
            codigo=E_ASSET_INVALIDO,
        )
    return x


def _guia_dentro(x: float, y: float, punto: Punto) -> tuple[Punto, ...]:
    """Linea guia del modo DENTRO: del borde del texto al punto, en un tramo."""
    return ((x, y), punto)


def _guia_fuera(
    x: float, y: float, ancho: float, ancla: str, punto: Punto
) -> tuple[Punto, ...]:
    """Linea guia del modo FUERA: tramo horizontal y luego recta al punto."""
    if ancla == "start":
        borde: float = x + ancho
        codo: float = borde + GANCHO_GUIA
    else:
        borde = x - ancho
        codo = borde - GANCHO_GUIA
    return ((borde, y), (codo, y), punto)


def _colocar_dentro(
    pose: Pose,
    etiquetas: tuple[str, ...],
    puntos: dict[str, Punto],
    ancho_vb: float,
    alto_vb: float,
    escala: float,
    tamano: float,
) -> tuple[Etiqueta, ...]:
    """Modo DENTRO: texto a 34 unidades del punto, del lado contrario al eje."""
    eje: float = eje_vertical(pose, ancho_vb)
    alto_caja: float = tamano * ALTURA_LINEA
    paso: float = alto_caja + SEPARACION_ETIQUETAS

    # Se acumula (indice declarado, etiqueta, punto, ancho de caja, lado). El
    # indice viaja para que el desempate del reparto sea el orden declarado.
    crudas: list[tuple[int, str, Punto, float, str]] = []
    for indice, texto in enumerate(etiquetas):
        punto: Punto = punto_de_etiqueta(texto, pose, puntos, ancho_vb, escala)
        ancla: str = "start" if punto[0] >= eje else "end"
        crudas.append((indice, texto, punto, ancho_texto(texto, tamano), ancla))

    colocadas: dict[int, Etiqueta] = {}
    for ancla in ("start", "end"):
        del_lado = [c for c in crudas if c[4] == ancla]
        del_lado.sort(key=lambda c: (c[2][1], c[0]))
        ys = _repartir_vertical(
            [c[2][1] for c in del_lado],
            paso,
            MARGEN_ETIQUETA + alto_caja / 2.0,
            alto_vb - MARGEN_ETIQUETA - alto_caja / 2.0,
        )
        for (indice, texto, punto, ancho, _lado), y in zip(del_lado, ys):
            lado: float = 1.0 if ancla == "start" else -1.0
            x: float = _clavar_en_lado(
                punto[0] + lado * DESPLAZAMIENTO_ETIQUETA,
                ancho,
                ancla,
                eje,
                ancho_vb,
                texto,
            )
            colocadas[indice] = Etiqueta(
                texto=texto,
                articulacion=dp.articulacion_de(texto),
                punto=punto,
                x=x,
                y=y,
                ancla=ancla,
                ancho=ancho,
                alto=alto_caja,
                tramos=_guia_dentro(x, y, punto),
                dentro=True,
            )
    return tuple(colocadas[i] for i in range(len(etiquetas)))


def _colocar_fuera(
    pose: Pose,
    etiquetas: tuple[str, ...],
    puntos: dict[str, Punto],
    ancho_vb: float,
    alto_vb: float,
    escala: float,
    tamano: float,
) -> tuple[Etiqueta, ...]:
    """Modo FUERA: dos columnas fijas en los margenes (criterio 15.19).

    Las etiquetas se ordenan de arriba abajo por la Y de su articulacion y se
    reparten alternando columna, de modo que las dos queden equilibradas y cada
    una conserve el orden vertical. La banda inferior queda libre para la
    Zona_Tactil de ampliacion.
    """
    alto_caja: float = tamano * ALTURA_LINEA
    paso: float = alto_caja + SEPARACION_ETIQUETAS

    crudas: list[tuple[int, str, Punto, float]] = []
    for indice, texto in enumerate(etiquetas):
        punto: Punto = punto_de_etiqueta(texto, pose, puntos, ancho_vb, escala)
        crudas.append((indice, texto, punto, ancho_texto(texto, tamano)))
    por_altura = sorted(crudas, key=lambda c: (c[2][1], c[0]))

    columnas: dict[str, list[tuple[int, str, Punto, float]]] = {
        "start": [],
        "end": [],
    }
    for posicion, cruda in enumerate(por_altura):
        columnas["start" if posicion % 2 == 0 else "end"].append(cruda)

    colocadas: dict[int, Etiqueta] = {}
    for ancla in ("start", "end"):
        del_lado = columnas[ancla]
        ys = _repartir_vertical(
            [c[2][1] for c in del_lado],
            paso,
            MARGEN_ETIQUETA + alto_caja / 2.0,
            alto_vb - BANDA_ZONA_TACTIL - alto_caja / 2.0,
        )
        for (indice, texto, punto, ancho), y in zip(del_lado, ys):
            x: float = (
                MARGEN_ETIQUETA
                if ancla == "start"
                else ancho_vb - MARGEN_ETIQUETA
            )
            colocadas[indice] = Etiqueta(
                texto=texto,
                articulacion=dp.articulacion_de(texto),
                punto=punto,
                x=x,
                y=y,
                ancla=ancla,
                ancho=ancho,
                alto=alto_caja,
                tramos=_guia_fuera(x, y, ancho, ancla, punto),
                dentro=False,
            )
    return tuple(colocadas[i] for i in range(len(etiquetas)))


def colocar_etiquetas(
    pose: Pose,
    etiquetas: tuple[str, ...],
    puntos: dict[str, Punto],
    ancho_vb: float,
    alto_vb: float,
) -> tuple[Etiqueta, ...]:
    """Coloca las Etiqueta_Anatomica de `pose` de forma **determinista**.

    El modo lo decide la cantidad de etiquetas: hasta ocho van junto al contorno
    (criterio 15.18) y mas de ocho van a las dos columnas de los margenes
    (criterio 15.19). En los dos modos las cajas de texto se reparten con una
    separacion vertical minima de una linea, de modo que ningun par se solape, y
    el resultado se devuelve en el **orden declarado** de las etiquetas.

    Sin aleatoriedad, sin `set` y sin recorrer ningun diccionario sin orden: los
    diccionarios locales se indexan por el numero de etiqueta y se leen en ese
    orden al final.
    """
    if ancho_vb <= 0.0 or alto_vb <= 0.0:
        raise ErrorAsset(
            f"viewBox invalido: ({ancho_vb!r}, {alto_vb!r})",
            detalle={"ancho": ancho_vb, "alto": alto_vb},
            codigo=E_ASSET_INVALIDO,
        )
    if not etiquetas:
        return ()
    for texto in etiquetas:
        if texto not in dp.ETIQUETAS_ANATOMIA:
            raise ErrorAsset(
                f"etiqueta fuera del vocabulario anatomico: {texto!r}",
                detalle={"etiqueta": texto},
                codigo=E_ASSET_INVALIDO,
            )

    factor: float = factor_figura(len(etiquetas))
    escala: float = escala_figura(ancho_vb, alto_vb, factor)
    tamano: float = tamano_fuente_etiqueta(ancho_vb)
    if len(etiquetas) > MAXIMO_ETIQUETAS_DENTRO:
        return _colocar_fuera(
            pose, etiquetas, puntos, ancho_vb, alto_vb, escala, tamano
        )
    return _colocar_dentro(
        pose, etiquetas, puntos, ancho_vb, alto_vb, escala, tamano
    )


# --------------------------------------------------------------------------- #
# Emision de las Etiqueta_Anatomica
# --------------------------------------------------------------------------- #


def svg_etiquetas(
    colocadas: tuple[Etiqueta, ...],
    ancho_vb: float,
    ancho_declarado: float,
    tamano: float,
) -> str:
    """Marcado de las etiquetas: linea guia, punto solido y `<text>`.

    Orden por etiqueta: primero su guia (para que el texto quede encima) y luego
    el texto. Las guias van en `--azul-linea` con el grosor de un pixel y
    terminan en un circulo relleno sobre el punto senalado (criterio 14.7); los
    textos van en `--azul-profundo` (criterio 14.6).
    """
    grosor: float = grosor_guia(ancho_vb, ancho_declarado)
    partes: list[str] = ['<g class="etiquetas">']
    for e in colocadas:
        puntos_guia: list[str] = [f"{_num(px)},{_num(py)}" for px, py in e.tramos]
        partes.append(
            f'<polyline class="guia" points="{" ".join(puntos_guia)}" '
            f'fill="none" stroke="{COLOR_GUIA}" '
            f'stroke-width="{_num(grosor)}" stroke-linecap="round" />'
        )
        partes.append(
            f'<circle class="guia-punto" cx="{_num(e.punto[0])}" '
            f'cy="{_num(e.punto[1])}" r="{_num(RADIO_PUNTO_GUIA)}" '
            f'fill="{COLOR_GUIA}" />'
        )
        partes.append(
            f'<text class="etiqueta" x="{_num(e.x)}" y="{_num(e.y)}" '
            f'text-anchor="{e.ancla}" dominant-baseline="middle" '
            f'font-size="{_num(tamano)}" font-family="sans-serif" '
            f'fill="{COLOR_CONTORNO}">{_esc(e.texto)}</text>'
        )
    partes.append("</g>")
    return "".join(partes)


# --------------------------------------------------------------------------- #
# Fase_Numerada con degradacion registrada (criterios 14.10 y 14.17)
# --------------------------------------------------------------------------- #
#
# Regla dura de esta seccion: una fase que no se puede emitir **no aborta el
# build**. Se emiten las demas y la omision queda registrada como
# `(id_diagrama, numero)` para el reporte del Orquestador_Build. Por eso aqui no
# hay ni un `raise` en el camino de emision: los invariantes de forma se
# comprueban en `validar_catalogo` (numeros de 1 a n, sin huecos) y lo que aqui
# puede fallar es solo la colocacion.

#: Articulacion a la que se ancla el numero de cada Fase_Numerada, en el orden
#: de las fases declaradas. Hoy solo `potencia-carrera` declara fases, y sus
#: tres anclas siguen la cadena del gesto: la aproximacion se marca en el pie de
#: apoyo, el armado en la rodilla de la pierna de atras y el impacto en el pie
#: que golpea. Tabla declarativa: un diagrama sin entrada aqui no emite ningun
#: numero y todas sus fases quedan registradas como omisiones.
ANCLAS_FASE: dict[str, tuple[str, ...]] = {
    "potencia-carrera": ("pie_i", "rodilla_d", "pie_d"),
}

#: Separacion del numero de fase respecto de su punto de anclaje, en unidades
#: del `viewBox`. Se aplica hacia afuera del eje y hacia arriba, para que el
#: numero no se monte sobre el trazo del hueso.
DESPLAZAMIENTO_FASE: float = 26.0

#: Semilado de la caja que ocupa un numero de fase, como multiplo del tamano de
#: fuente. Con una o dos cifras, 0.6 la cubre de sobra.
SEMILADO_FASE: float = 0.6


def ancla_fase(id_diagrama: str, numero: int) -> str | None:
    """Articulacion de anclaje de la fase `numero`, o `None` si no hay ninguna.

    Devolver `None` en vez de lanzar es deliberado: la falta de ancla es una
    fase **no emitible**, y el criterio 14.17 exige degradar y registrar, no
    abortar.
    """
    anclas: tuple[str, ...] = ANCLAS_FASE.get(id_diagrama, ())
    if 1 <= numero <= len(anclas):
        return anclas[numero - 1]
    return None


def punto_fase(
    pose: Pose, puntos: dict[str, Punto], articulacion: str, ancho_vb: float
) -> Punto:
    """Posicion del numero de fase junto a `articulacion`.

    Hacia el lado contrario al eje vertical (como las etiquetas del modo DENTRO)
    y un poco por encima, de modo que el numero quede junto al punto de anclaje
    sin taparlo.
    """
    px, py = puntos[articulacion]
    lado: float = 1.0 if px >= eje_vertical(pose, ancho_vb) else -1.0
    return (px + lado * DESPLAZAMIENTO_FASE, py - DESPLAZAMIENTO_FASE)


def _cabe_numero(punto: Punto, tamano: float, ancho_vb: float, alto_vb: float) -> bool:
    """True si la caja del numero cae entera dentro del `viewBox`."""
    semilado: float = SEMILADO_FASE * tamano
    return (
        punto[0] - semilado >= MARGEN_ETIQUETA
        and punto[0] + semilado <= ancho_vb - MARGEN_ETIQUETA
        and punto[1] - semilado >= MARGEN_ETIQUETA
        and punto[1] + semilado <= alto_vb - MARGEN_ETIQUETA
    )


def _plan_fases(
    d: dp.DiagramaPostura,
    ancho_vb: float,
    alto_vb: float,
    factor: float,
    omitir: tuple[int, ...],
) -> tuple[tuple[tuple[int, Punto], ...], tuple[tuple[str, int], ...]]:
    """Reparte las fases de `d` en emitibles y omitidas, en orden declarado.

    Una fase se omite cuando no tiene ancla declarada, cuando su ancla no existe
    en el esqueleto, cuando el numero no cabe dentro del `viewBox` o cuando
    `omitir` la nombra. `omitir` es el punto de inyeccion con el que la prueba de
    la Property 10 fuerza el fallo de un subconjunto cualquiera de fases.
    """
    if not d.fases:
        return ((), ())
    pose: Pose = pose_de(d.id)
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    tamano: float = tamano_fuente_etiqueta(ancho_vb)
    emitibles: list[tuple[int, Punto]] = []
    omitidas: list[tuple[str, int]] = []
    for fase in d.fases:
        articulacion: str | None = ancla_fase(d.id, fase.numero)
        if (
            fase.numero in omitir
            or articulacion is None
            or articulacion not in puntos
        ):
            omitidas.append((d.id, fase.numero))
            continue
        punto: Punto = punto_fase(pose, puntos, articulacion, ancho_vb)
        if not _cabe_numero(punto, tamano, ancho_vb, alto_vb):
            omitidas.append((d.id, fase.numero))
            continue
        emitibles.append((fase.numero, punto))
    return (tuple(emitibles), tuple(omitidas))


def _viewbox_svg(d: dp.DiagramaPostura) -> tuple[float, float, float]:
    """`(ancho_vb, alto_vb, factor)` del modo SVG declarado por `d`."""
    return (
        d.ancho_svg * FACTOR_VIEWBOX,
        d.alto_svg * FACTOR_VIEWBOX,
        factor_figura(len(d.etiquetas)),
    )


def svg_fases(
    d: dp.DiagramaPostura,
    ancho_vb: float,
    alto_vb: float,
    *,
    factor: float = 1.0,
    omitir: tuple[int, ...] = (),
) -> str:
    """Un `<text>` con el numero de cada Fase_Numerada emitible (criterio 14.10).

    Devuelve la cadena vacia cuando el diagrama no declara fases o cuando
    ninguna es emitible: la ausencia del grupo es la degradacion, y el detalle
    viaja en `omisiones_de_fase`.
    """
    emitibles, _omitidas = _plan_fases(d, ancho_vb, alto_vb, factor, omitir)
    if not emitibles:
        return ""
    tamano: float = tamano_fuente_etiqueta(ancho_vb)
    partes: list[str] = ['<g class="fases">']
    for numero, (px, py) in emitibles:
        partes.append(
            f'<text class="fase fase-{numero}" x="{_num(px)}" y="{_num(py)}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-size="{_num(tamano)}" font-family="sans-serif" '
            f'fill="{COLOR_CONTORNO}">{_esc(str(numero))}</text>'
        )
    partes.append("</g>")
    return "".join(partes)


def fases_emitidas(
    d: dp.DiagramaPostura, *, omitir: tuple[int, ...] = ()
) -> tuple[int, ...]:
    """Numeros de Fase_Numerada que el SVG de `d` emite de verdad.

    Con todas las fases emitibles el conjunto es exactamente `{1..n}` (criterio
    14.10), que es lo que la lista `<ol class="diagrama-fases">` del HTML replica
    con `value="<numero>"` (criterio 14.11).
    """
    ancho_vb, alto_vb, factor = _viewbox_svg(d)
    emitibles, _omitidas = _plan_fases(d, ancho_vb, alto_vb, factor, omitir)
    return tuple(numero for numero, _punto in emitibles)


def omisiones_de_fase(
    d: dp.DiagramaPostura, *, omitir: tuple[int, ...] = ()
) -> tuple[tuple[str, int], ...]:
    """Pares `(id_diagrama, numero)` de las fases que no se pudieron emitir.

    Es lo que alimenta `fases_omitidas` en el reporte del Orquestador_Build
    (criterio 14.17). Nunca lanza: la degradacion se registra, no se aborta.
    """
    ancho_vb, alto_vb, factor = _viewbox_svg(d)
    _emitibles, omitidas = _plan_fases(d, ancho_vb, alto_vb, factor, omitir)
    return omitidas


# --------------------------------------------------------------------------- #
# Zona_Tactil de ampliacion del modo FUERA (criterio 15.19)
# --------------------------------------------------------------------------- #

#: Sufijo del ancla del Visor_Ampliado de un diagrama. `anatomia-base` produce
#: `#anatomia-base-ampliada`, que es el `id` del overlay modal: sin JavaScript lo
#: destapa el selector `:target`, y con el Script_Unico vivo lo abre `abrirModal`
#: alternando el atributo `hidden`. El `position:fixed` de ese overlay es el unico
#: de toda la Hoja_Estilo (criterio 28.5).
SUFIJO_AMPLIACION: str = "-ampliada"

#: Lado minimo de una Zona_Tactil, en pixeles CSS (criterio 15.6).
LADO_TACTIL_PX: float = 44.0

#: Ancho de la Zona_Tactil de ampliacion, en pixeles CSS.
ANCHO_TACTIL_PX: float = 176.0

#: Radio de las esquinas de la Zona_Tactil, en pixeles CSS.
RADIO_TACTIL_PX: float = 10.0

#: Fondo de la Zona_Tactil de ampliacion (`--blanco-suave`).
COLOR_ZONA: str = paleta.WEB_HERO_BLANCO

#: Texto visible de la Zona_Tactil de ampliacion.
TEXTO_AMPLIACION: str = "Ver en grande"


def ancla_ampliacion(id_diagrama: str) -> str:
    """Ancla de la seccion ampliada de `id_diagrama`, sin la almohadilla."""
    if not id_diagrama:
        raise ErrorAsset(
            "ancla_ampliacion exige el identificador del diagrama",
            codigo=E_ASSET_INVALIDO,
        )
    return f"{id_diagrama}{SUFIJO_AMPLIACION}"


def svg_zona_ampliacion(
    d: dp.DiagramaPostura, ancho_vb: float, alto_vb: float, tamano: float
) -> str:
    """Zona_Tactil que amplia el diagrama a pantalla completa (criterio 15.19).

    Es un **enlace de ancla** a `#<id>-ampliada`: un solo toque, cero JavaScript
    obligatorio y cero `tabindex` (el `<a>` del SVG ya es enfocable con teclado
    por si mismo). Vive en la banda inferior que el modo FUERA reserva, asi que
    nunca se cruza con una caja de texto.
    """
    unidades_por_px: float = ancho_vb / float(d.ancho_svg)
    alto: float = LADO_TACTIL_PX * unidades_por_px
    ancho: float = min(
        ANCHO_TACTIL_PX * unidades_por_px, ancho_vb - 2.0 * MARGEN_ETIQUETA
    )
    if alto > BANDA_ZONA_TACTIL - 2.0 * MARGEN_ETIQUETA:
        raise ErrorAsset(
            f"{d.id}: la Zona_Tactil de ampliacion ({round(alto, 3)} unidades) "
            f"no cabe en la banda reservada de {BANDA_ZONA_TACTIL}",
            detalle={"id": d.id, "alto": alto},
            codigo=E_ASSET_INVALIDO,
        )
    if ancho < alto:
        raise ErrorAsset(
            f"{d.id}: la Zona_Tactil de ampliacion queda mas angosta "
            f"({round(ancho, 3)}) que su lado minimo ({round(alto, 3)})",
            detalle={"id": d.id, "ancho": ancho, "alto": alto},
            codigo=E_ASSET_INVALIDO,
        )

    x: float = (ancho_vb - ancho) / 2.0
    y: float = alto_vb - MARGEN_ETIQUETA - alto
    radio: float = RADIO_TACTIL_PX * unidades_por_px
    grosor: float = grosor_guia(ancho_vb, float(d.ancho_svg))
    etiqueta_accesible: str = f"Ampliar el diagrama {d.titulo} a pantalla completa"

    partes: list[str] = [
        f'<a class="diagrama-ampliar" href="#{_esc(ancla_ampliacion(d.id))}" '
        f'aria-label="{_esc(etiqueta_accesible)}">',
        f'<rect class="zona-tactil" x="{_num(x)}" y="{_num(y)}" '
        f'width="{_num(ancho)}" height="{_num(alto)}" rx="{_num(radio)}" '
        f'fill="{COLOR_ZONA}" stroke="{COLOR_CONTORNO}" '
        f'stroke-width="{_num(grosor)}" />',
        f'<text class="zona-tactil-texto" x="{_num(ancho_vb / 2.0)}" '
        f'y="{_num(y + alto / 2.0)}" text-anchor="middle" '
        f'dominant-baseline="middle" font-size="{_num(tamano)}" '
        f'font-family="sans-serif" fill="{COLOR_CONTORNO}">'
        f"{_esc(TEXTO_AMPLIACION)}</text>",
        "</a>",
    ]
    return "".join(partes)


def caja_figura(
    pose: Pose, ancho_vb: float, alto_vb: float, *, factor: float = 1.0
) -> tuple[float, float, float, float]:
    """Rectangulo `(x0, y0, x1, y1)` que envuelve a la figura.

    Incluye la holgura de la cabeza (su circulo mas el mono del cabello), que es
    la parte que mas sobresale del esqueleto.
    """
    escala: float = escala_figura(ancho_vb, alto_vb, factor)
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    xs: list[float] = []
    ys: list[float] = []
    for nombre, (px, py) in puntos.items():
        radio: float = HOLGURA_CABEZA * escala if nombre == "cabeza" else 0.0
        xs.extend((px - radio, px + radio))
        ys.extend((py - radio, py + radio))
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------- #
# Ensamblado del `<svg>` (criterios 4.3, 14.1 y 14.15)
# --------------------------------------------------------------------------- #

#: Subcadenas que el marcado emitido **nunca** puede contener (criterio 14.15).
#: `<img>` y `<image>` traerian un archivo de imagen, `url(` y `http` una
#: peticion de red, y `tabindex` una trampa de foco. Los atributos de evento en
#: linea se buscan con `_RE_EVENTO`, que no cabe en una lista de subcadenas.
PROHIBIDOS_MARCADO: tuple[str, ...] = (
    "<image",
    "<img",
    "url(",
    "http",
    "tabindex",
)

#: Atributo de evento en linea: un espacio, `on`, letras y el igual.
_RE_EVENTO = re.compile(r"\son[a-z]+\s*=")


def validar_marcado(id_diagrama: str, marcado: str) -> None:
    """Comprueba las prohibiciones del criterio 14.15 sobre `marcado`.

    Con `raise ErrorAsset`, nunca con `assert`: el guardarrail tiene que seguir
    vivo con `python -O`.
    """
    for prohibido in PROHIBIDOS_MARCADO:
        if prohibido in marcado:
            raise ErrorAsset(
                f"{id_diagrama}: el SVG emitido contiene {prohibido!r}, que el "
                "criterio 14.15 prohibe",
                detalle={"id": id_diagrama, "prohibido": prohibido},
                codigo=E_ASSET_INVALIDO,
            )
    evento = _RE_EVENTO.search(marcado)
    if evento is not None:
        raise ErrorAsset(
            f"{id_diagrama}: el SVG emitido declara el atributo de evento "
            f"{evento.group(0).strip()!r}",
            detalle={"id": id_diagrama, "atributo": evento.group(0).strip()},
            codigo=E_ASSET_INVALIDO,
        )


def svg_diagrama(d: dp.DiagramaPostura) -> str:
    """`<svg>` en linea completo de un Diagrama_Postura.

    `viewBox` es `0 0 (FACTOR_VIEWBOX * ancho_svg) (FACTOR_VIEWBOX * alto_svg)`,
    mientras `width` y `height` son las dimensiones declaradas del **modo SVG**
    (criterio 4.3). Lleva `role="img"` y `aria-label` con el `alt` del catalogo,
    de modo que el lector de pantalla lea la misma descripcion que leeria del
    `<img>` del modo archivo.

    Orden de emision unico y estable -- figura, adornos, fases, etiquetas y, en
    modo FUERA, la Zona_Tactil de ampliacion -- con todos los numeros por `_num`:
    dos llamadas con el mismo diagrama devuelven **bytes identicos**.
    """
    ancho_vb: float = d.ancho_svg * FACTOR_VIEWBOX
    alto_vb: float = d.alto_svg * FACTOR_VIEWBOX
    ancho_declarado: float = float(d.ancho_svg)
    factor: float = factor_figura(len(d.etiquetas))
    tamano: float = tamano_fuente_etiqueta(ancho_vb)
    pose: Pose = pose_de(d.id)
    puntos: dict[str, Punto] = esqueleto(pose, ancho_vb, alto_vb, factor=factor)
    colocadas: tuple[Etiqueta, ...] = colocar_etiquetas(
        pose, d.etiquetas, puntos, ancho_vb, alto_vb
    )

    partes: list[str] = [
        f'<svg class="diagrama-svg" viewBox="0 0 {_num(ancho_vb)} '
        f'{_num(alto_vb)}" width="{_num(ancho_declarado)}" '
        f'height="{_num(float(d.alto_svg))}" role="img" '
        f'aria-label="{_esc(d.alt)}">',
        svg_figura(pose, ancho_vb, alto_vb, ancho_declarado, factor=factor),
        svg_adornos(pose, ancho_vb, alto_vb, ancho_declarado, factor=factor),
        svg_fases(d, ancho_vb, alto_vb, factor=factor),
        svg_etiquetas(colocadas, ancho_vb, ancho_declarado, tamano),
    ]
    if len(d.etiquetas) > MAXIMO_ETIQUETAS_DENTRO:
        partes.append(svg_zona_ampliacion(d, ancho_vb, alto_vb, tamano))
    partes.append("</svg>")

    marcado: str = "".join(partes)
    validar_marcado(d.id, marcado)
    return marcado
