"""Proyector_Vistas: el Esqueleto_3D y las diez Vista_Figura de una Figura_Girable.

Modulo del multi-vista de la feature `imagenes-reales-hero-interactivo`
(Requisitos 21 a 25). Su trabajo: derivar el Esqueleto_3D de una `Pose` que ya
existe, rotarlo por azimut y por elevacion, proyectarlo a dos coordenadas y
emitir las diez Vista_Figura con sus cuatro grupos en orden fijo.

**Solo lee** de `svg_postura`: no cambia ninguna de sus firmas. Lo unico que la
ampliacion anadio alli son `FACTOR_VISTA` y `num` (el `_num` de siempre expuesto
en publico), de modo que haya **un solo formateo numerico** en todo el proyecto
(criterio 21.11) y dos emisiones de la misma pose y clave den bytes identicos
(criterio 21.12).

El punto delicado, registrado aqui porque es lo que se rompe al primer descuido:
**no se puede "anadir" una tercera coordenada a un punto y esperar que la
longitud del hueso no cambie**. Por eso `esqueleto_3d` **no** concatena
`PROFUNDIDAD_CANONICA` al resultado de `svg_postura.esqueleto_canonico`: hace
cinematica directa en tres dimensiones reusando los mismos dieciseis huesos, las
mismas longitudes y los mismos angulos en el plano. Para cada hueso de longitud
`L` cuyo par de profundidades declaradas da un salto `dz`::

    beta      = asin(dz / L)                 requiere |dz| <= L
    vector_3d = (L*cos(beta)*cos(theta),     theta = angulo en el plano
                 -L*cos(beta)*sin(theta),    (la Y del SVG crece hacia abajo)
                  L*sin(beta))

La norma del vector es `L*sqrt(cos^2 beta + sin^2 beta) = L`, **exacta**, con
todo `beta`. La consecuencia visible es que la componente en el plano se acorta
por `cos(beta)`: eso es Escorzo legitimo, no perdida de longitud. De ahi que las
dos medidas de longitud sean distintas **a proposito**: `largo_hueso_3d` es
invariante con tolerancia 1e-6 (criterios 14.18 y 21.5) y
`largo_hueso_proyectado` **no** lo es, y solo se garantiza que quede en `[0, L]`
(criterios 14.19 y 21.7). Ninguna prueba debe exigir constancia sobre la
proyeccion.

Reglas del proyecto: Python 3.11+, solo libreria estandar y **ningun `assert`**
(todo invariante con `raise ErrorAsset(..., codigo=E_ASSET_INVALIDO)`, para que
`python -O` no borre ningun guardarrail).

_Requirements: 12.7, 14.18, 14.19, 14.20, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6,
21.7, 21.8, 21.9, 21.10, 21.11, 21.12, 21.13, 22.1, 22.2, 22.3, 22.6, 22.7,
22.8, 22.9, 22.11, 22.12, 22.13, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.11,
24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9, 24.10, 25.6, 25.7, 25.10,
25.11, 25.14, 25.15, 28.2, 28.9, 28.11, 29.5, 29.6_
"""

from __future__ import annotations

import math
import re

from . import diagramas_postura as dp
from . import paleta
from . import svg_postura as sp
from .errores import E_ASSET_INVALIDO, ErrorAsset

__all__ = [
    "AZIMUTS_DECLARADOS",
    "ELEVACIONES_DECLARADAS",
    "AZIMUTS_MOVIL",
    "CLAVES_VISTA",
    "ROTACION_RESIDUAL_MAX",
    "OPACIDAD_TRASERO",
    "OPACIDAD_DELANTERO",
    "BYTES_MAX_VISTA",
    "VISTAS_MAX",
    "UMBRAL_ELEVACION",
    "GRADOS_POR_PIXEL",
    "GIRO_IMPULSO_MS",
    "ARTICULACIONES_AXIALES",
    "MAGNITUD_PROFUNDIDAD",
    "PROFUNDIDAD_CANONICA",
    "ADELANTO_MIEMBRO",
    "MIEMBROS",
    "NOMBRES_MIEMBROS",
    "Punto3D",
    "SUFIJO_DERECHO",
    "SUFIJO_IZQUIERDO",
    "CLASE_ACTIVA",
    "CLASE_GIRABLE",
    "CLASE_VISTA",
    "svg_figura_girable",
    "trocear_vistas",
    "vistas_de",
    "CLAVE_ACTIVA",
    "COLOR_TAPA_DIAGRAMA",
    "COLOR_TAPA_FONDO",
    "GRUPOS_CONTRAPICADA",
    "GRUPOS_ESPALDA",
    "GRUPOS_OBLIGATORIOS",
    "GRUPOS_PROHIBIDOS",
    "NUMERO_CAMISETA",
    "TOLERANCIA_LONGITUD",
    "validar_vistas",
    "validar_total_de_vistas",
    "ORDEN_TORSO",
    "svg_vista",
    "GRUPOS_PICADA",
    "GRUPO_BALON_PICADA",
    "GRUPO_COLETA_RECOGIDA",
    "TABLA_VISTAS",
    "azimut_de",
    "clasificar_miembros",
    "clave_de_azimut",
    "elevacion_de",
    "escala_sombra",
    "esqueleto_3d",
    "esqueleto_3d_rotado",
    "esqueleto_vista",
    "grupos_extra",
    "largo_hueso_3d",
    "largo_hueso_proyectado",
    "miembro_de_articulacion",
    "normalizar_giro",
    "profundidad_de",
    "profundidad_miembro",
    "proyectar",
    "punto_miembro",
    "rotacion_residual",
    "rotar_azimut",
    "rotar_elevacion",
    "salto_profundidad",
    "validar_profundidad",
    "validar_miembros",
    "vista_mas_cercana",
]


# --------------------------------------------------------------------------- #
# Angulos declarados y Clave_Vista
# --------------------------------------------------------------------------- #

#: Los ocho azimuts declarados, en grados, en el orden del criterio 22.1.
AZIMUTS_DECLARADOS: tuple[int, ...] = (0, 45, 90, 135, 180, 225, 270, 315)

#: Las dos elevaciones declaradas: picada (+60) y contrapicada (-60). El signo se
#: elige para que `+60` sea la picada: el punto que estaba delante del cuerpo baja
#: en pantalla y la coronilla queda a la vista (criterio 22.3).
ELEVACIONES_DECLARADAS: tuple[int, ...] = (60, -60)

#: Subconjunto_Azimuts_Movil: los seis azimuts que sobreviven bajo 768 px
#: (criterio 12.7). Las dos Vista_Elevacion quedan fuera, asi que en pantalla
#: angosta el giro **automatico** solo recorre azimuts; el Arrastre_Rotacion si
#: las alcanza, porque es gesto de la usuaria y no giro automatico.
AZIMUTS_MOVIL: tuple[int, ...] = (0, 45, 90, 180, 270, 315)

#: Las diez Clave_Vista, en el orden EXACTO del criterio 22.1. Este orden **es**
#: el orden de emision (criterio 22.6).
CLAVES_VISTA: tuple[str, ...] = (
    "az-000",
    "az-045",
    "az-090",
    "az-135",
    "az-180",
    "az-225",
    "az-270",
    "az-315",
    "el-p60",
    "el-m60",
)

#: Tope de la Rotacion_Residual, en grados (criterio 25.10). Es la mitad del paso
#: de 45 grados entre dos azimuts contiguos, asi que ningun angulo del circulo
#: queda a mas de esta distancia de su azimut declarado mas cercano.
ROTACION_RESIDUAL_MAX: float = 22.5

#: `stroke-opacity` de los Miembro_Trasero (criterio 24.2).
OPACIDAD_TRASERO: float = 0.55

#: `stroke-opacity` de los Miembro_Delantero (criterio 24.3).
OPACIDAD_DELANTERO: float = 1.0

#: Techo de tamano de una Vista_Figura, en bytes (criterio 22.13).
BYTES_MAX_VISTA: int = 6144

#: Techo de Vista_Figura del Target_Web (criterio 22.13). Cuatro Figura_Girable
#: por diez Vista_Figura son exactamente 40: anadir una quinta obliga a bajar el
#: numero de vistas o a subir el techo, y `validar_vistas` lo dice con
#: `ErrorAsset` en vez de dejar que el documento engorde en silencio.
VISTAS_MAX: int = 40

#: Angulo umbral que conmuta a Vista_Elevacion (criterio 28.11), en grados.
UMBRAL_ELEVACION: float = 30.0

#: Grados de giro por pixel arrastrado (criterio 28.9).
GRADOS_POR_PIXEL: float = 0.6

#: Duracion del Giro_Impulso, en milisegundos (criterio 28.2).
GIRO_IMPULSO_MS: int = 1200


# --------------------------------------------------------------------------- #
# Profundidad canonica: la tercera coordenada de las diecisiete articulaciones
# --------------------------------------------------------------------------- #

#: Un punto del Esqueleto_3D: `(x, y, z)` en unidades canonicas.
Punto3D = tuple[float, float, float]

#: Las tres articulaciones **axiales**, que viven sobre la linea media del cuerpo
#: y por tanto tienen profundidad exactamente 0 (criterio 21.2).
ARTICULACIONES_AXIALES: tuple[str, ...] = ("cabeza", "cuello", "torso")

#: Magnitud de la profundidad de cada articulacion **par**, por nombre base. La
#: magnitud crece hacia el extremo de cada cadena (hombro 22 -> codo 26 -> mano
#: 30; cadera 18 -> rodilla 16 -> tobillo 14 -> pie 20), que es lo que da grosor
#: al cuerpo sin deformarlo.
MAGNITUD_PROFUNDIDAD: dict[str, float] = {
    "hombro": 22.0,
    "codo": 26.0,
    "mano": 30.0,
    "cadera": 18.0,
    "rodilla": 16.0,
    "tobillo": 14.0,
    "pie": 20.0,
}

#: Sufijo de las articulaciones del lado **derecho** de la figura, que es el que
#: queda hacia la lectora en las ocho poses y el que lleva profundidad positiva.
SUFIJO_DERECHO: str = "_d"

#: Sufijo de las articulaciones del lado izquierdo, espejo del derecho.
SUFIJO_IZQUIERDO: str = "_i"


def _derivar_profundidad() -> dict[str, float]:
    """Construye la tabla de profundidad recorriendo las articulaciones reales.

    Se **deriva** de `diagramas_postura.ARTICULACIONES` en vez de escribirse como
    un segundo literal de diecisiete filas: asi no se puede inventar ninguna
    articulacion, no se puede olvidar ninguna y el criterio de signos queda
    escrito una sola vez (criterio 21.2). El resultado es exactamente el que
    declara la tabla del diseno: positivo en las siete del lado derecho, el mismo
    valor negado en sus siete espejos y 0 en `cabeza`, `cuello` y `torso`.
    """
    tabla: dict[str, float] = {}
    for nombre in dp.ARTICULACIONES:
        if nombre in ARTICULACIONES_AXIALES:
            tabla[nombre] = 0.0
            continue
        if nombre.endswith(SUFIJO_DERECHO):
            base: str = nombre[: -len(SUFIJO_DERECHO)]
            signo: float = 1.0
        elif nombre.endswith(SUFIJO_IZQUIERDO):
            base = nombre[: -len(SUFIJO_IZQUIERDO)]
            signo = -1.0
        else:
            raise ErrorAsset(
                f"la articulacion {nombre!r} no es axial y tampoco declara lado: "
                f"deberia terminar en {SUFIJO_DERECHO!r} o en "
                f"{SUFIJO_IZQUIERDO!r}",
                detalle={"articulacion": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        magnitud: float | None = MAGNITUD_PROFUNDIDAD.get(base)
        if magnitud is None:
            raise ErrorAsset(
                f"la articulacion {nombre!r} no tiene magnitud de profundidad "
                f"declarada para su nombre base {base!r}",
                detalle={"articulacion": nombre, "base": base},
                codigo=E_ASSET_INVALIDO,
            )
        tabla[nombre] = signo * magnitud
    return tabla


#: Tercera coordenada de cada articulacion, en unidades canonicas. Las claves son
#: EXACTAMENTE las diecisiete de `diagramas_postura.ARTICULACIONES` (criterio
#: 21.2). Positivo en las siete del lado derecho, el mismo valor negado en sus
#: siete espejos y exactamente 0 en las tres axiales.
PROFUNDIDAD_CANONICA: dict[str, float] = _derivar_profundidad()

#: Adelanto del punto de clasificacion de un miembro respecto de la linea media
#: del cuerpo, en unidades canonicas.
#:
#: **Decision de diseno registrada.** El torso no es una linea: es el bloque que
#: la Tapa_Torso dibuja, y los cuatro miembros cuelgan **por delante** de ese
#: bloque. Sin este adelanto, clasificar por el signo crudo de la profundidad
#: canonica pondria el brazo y la pierna izquierdos detras del torso ya en la
#: vista de frente, y el criterio 24.8 exige lo contrario: en `az-000` los cuatro
#: miembros son Miembro_Delantero. Con el adelanto la clasificacion queda
#: coherente en las diez vistas y sigue decidiendose por **el signo de la
#: profundidad rotada** del punto del miembro (criterios 21.9 y 21.10):
#:
#: * en `az-000` los cuatro adelantos son positivos, asi que los cuatro miembros
#:   son delanteros (criterio 24.8);
#: * en `az-180` el giro los niega, asi que los cuatro pasan a traseros, que son
#:   exactamente "los miembros cuya profundidad canonica queda delante del
#:   torso" (criterio 24.9);
#: * en `az-090` y `az-270` el azimut cambia profundidad por posicion lateral, y
#:   el reparto se hace por costado, que es lo correcto en el perfil.
#:
#: El valor se **deriva** de la propia tabla (la mayor magnitud declarada, 30),
#: de modo que sea estrictamente mayor que la profundidad de cualquier punto
#: medio de miembro y no haya un numero suelto que se pueda desincronizar.
ADELANTO_MIEMBRO: float = max(MAGNITUD_PROFUNDIDAD.values())


def profundidad_de(articulacion: str) -> float:
    """Profundidad canonica de `articulacion`, en unidades canonicas."""
    valor: float | None = PROFUNDIDAD_CANONICA.get(articulacion)
    if valor is None:
        raise ErrorAsset(
            f"articulacion sin profundidad declarada: {articulacion!r}",
            detalle={"articulacion": articulacion},
            codigo=E_ASSET_INVALIDO,
        )
    return valor


def salto_profundidad(origen: str, destino: str) -> float:
    """Salto de profundidad `dz` del hueso `origen -> destino`.

    Es la diferencia de la tabla declarada, y es lo que `esqueleto_3d` convierte
    en el angulo fuera de plano `beta = asin(dz / L)`.
    """
    return profundidad_de(destino) - profundidad_de(origen)


def validar_profundidad() -> None:
    """Comprueba la tabla de profundidad y el invariante `|dz| <= L`.

    Cuatro invariantes, todos con `raise ErrorAsset` y ningun `assert`:

    1. las claves son exactamente las diecisiete articulaciones reales;
    2. las tres axiales valen exactamente 0;
    3. cada articulacion del lado derecho es positiva y su espejo izquierdo es
       el mismo valor negado;
    4. el salto de profundidad de cada uno de los dieciseis huesos no supera en
       valor absoluto la longitud declarada de ese hueso, que es la condicion
       para que `asin(dz / L)` exista (criterio 21.13). Con la tabla declarada el
       peor caso es `cuello-hombro_d`, con `22 / 80` y `beta = 16.0` grados.
    """
    if tuple(PROFUNDIDAD_CANONICA) != dp.ARTICULACIONES:
        raise ErrorAsset(
            "la tabla de profundidad no declara exactamente las diecisiete "
            f"articulaciones reales: declara {tuple(PROFUNDIDAD_CANONICA)}",
            detalle={"declaradas": tuple(PROFUNDIDAD_CANONICA)},
            codigo=E_ASSET_INVALIDO,
        )
    for axial in ARTICULACIONES_AXIALES:
        if PROFUNDIDAD_CANONICA[axial] != 0.0:
            raise ErrorAsset(
                f"la articulacion axial {axial!r} debe tener profundidad 0 y "
                f"tiene {PROFUNDIDAD_CANONICA[axial]!r}",
                detalle={"articulacion": axial},
                codigo=E_ASSET_INVALIDO,
            )
    for nombre, valor in PROFUNDIDAD_CANONICA.items():
        if nombre in ARTICULACIONES_AXIALES:
            continue
        if nombre.endswith(SUFIJO_DERECHO):
            if valor <= 0.0:
                raise ErrorAsset(
                    f"la articulacion derecha {nombre!r} debe tener profundidad "
                    f"positiva y tiene {valor!r}",
                    detalle={"articulacion": nombre, "profundidad": valor},
                    codigo=E_ASSET_INVALIDO,
                )
            espejo: str = f"{nombre[: -len(SUFIJO_DERECHO)]}{SUFIJO_IZQUIERDO}"
            if PROFUNDIDAD_CANONICA.get(espejo) != -valor:
                raise ErrorAsset(
                    f"la articulacion {espejo!r} deberia declarar {-valor!r}, "
                    f"el espejo de {nombre!r}, y declara "
                    f"{PROFUNDIDAD_CANONICA.get(espejo)!r}",
                    detalle={"articulacion": espejo, "espejo_de": nombre},
                    codigo=E_ASSET_INVALIDO,
                )

    for origen, destino, largo in sp.HUESOS:
        dz: float = salto_profundidad(origen, destino)
        if abs(dz) > largo:
            raise ErrorAsset(
                f"el hueso {origen}-{destino} declara un salto de profundidad "
                f"de {dz} unidades y su longitud es {largo}: |dz| <= L es la "
                "condicion para que exista el angulo fuera de plano",
                detalle={
                    "hueso": f"{origen}-{destino}",
                    "salto": dz,
                    "longitud": largo,
                },
                codigo=E_ASSET_INVALIDO,
            )


# --------------------------------------------------------------------------- #
# Los cuatro miembros que se clasifican por profundidad
# --------------------------------------------------------------------------- #

#: Los cuatro miembros y las articulaciones de cada uno. El orden es **declarado**
#: para que la clasificacion sea estable y la emision deterministica (criterio
#: 21.12): se recorre esta tupla, nunca un `set` ni un diccionario sin orden.
MIEMBROS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("brazo_i", ("hombro_i", "codo_i", "mano_i")),
    ("brazo_d", ("hombro_d", "codo_d", "mano_d")),
    ("pierna_i", ("cadera_i", "rodilla_i", "tobillo_i", "pie_i")),
    ("pierna_d", ("cadera_d", "rodilla_d", "tobillo_d", "pie_d")),
)

#: Nombres de los cuatro miembros, en el orden declarado.
NOMBRES_MIEMBROS: tuple[str, ...] = tuple(nombre for nombre, _ in MIEMBROS)


def validar_miembros() -> None:
    """Comprueba que los cuatro miembros parten las articulaciones no axiales.

    La union de los cuatro miembros mas las tres axiales tiene que ser
    exactamente las diecisiete articulaciones, sin repetir ninguna: si un miembro
    olvidara una articulacion, su trazo se quedaria sin grupo y el criterio 24.6
    se rompería en silencio.
    """
    if len(MIEMBROS) != 4:
        raise ErrorAsset(
            f"se declaran {len(MIEMBROS)} miembros y deben ser cuatro",
            detalle={"cantidad": len(MIEMBROS)},
            codigo=E_ASSET_INVALIDO,
        )
    vistas: list[str] = list(ARTICULACIONES_AXIALES)
    for nombre, articulaciones in MIEMBROS:
        if not articulaciones:
            raise ErrorAsset(
                f"el miembro {nombre!r} no declara ninguna articulacion",
                detalle={"miembro": nombre},
                codigo=E_ASSET_INVALIDO,
            )
        for articulacion in articulaciones:
            if articulacion not in PROFUNDIDAD_CANONICA:
                raise ErrorAsset(
                    f"el miembro {nombre!r} nombra la articulacion inexistente "
                    f"{articulacion!r}",
                    detalle={"miembro": nombre, "articulacion": articulacion},
                    codigo=E_ASSET_INVALIDO,
                )
            if articulacion in vistas:
                raise ErrorAsset(
                    f"la articulacion {articulacion!r} aparece en dos miembros "
                    f"o es axial, y la vuelve a nombrar {nombre!r}",
                    detalle={"miembro": nombre, "articulacion": articulacion},
                    codigo=E_ASSET_INVALIDO,
                )
            vistas.append(articulacion)
    if tuple(sorted(vistas)) != tuple(sorted(dp.ARTICULACIONES)):
        raise ErrorAsset(
            "los cuatro miembros y las tres axiales no cubren las diecisiete "
            f"articulaciones: cubren {tuple(sorted(vistas))}",
            detalle={"cubiertas": tuple(sorted(vistas))},
            codigo=E_ASSET_INVALIDO,
        )


# --------------------------------------------------------------------------- #
# Esqueleto_3D por cinematica directa en tres dimensiones
# --------------------------------------------------------------------------- #
#
# Esto es el corazon del Proyector_Vistas y el sitio donde es mas facil
# equivocarse, asi que queda escrito aqui lo que **no** hace:
#
#   NO hace  ->  zip(esqueleto_canonico(pose), PROFUNDIDAD_CANONICA.values())
#
# Concatenar la profundidad a los puntos del plano cambiaria la longitud de cada
# hueso: un hueso de 80 unidades en el plano con un salto de 22 en profundidad
# mediria sqrt(80^2 + 22^2) = 82.97 en tres dimensiones, y los criterios 21.5 y
# 14.18 exigen igualdad a 1e-6. Lo que hace es cinematica directa en 3D con los
# **mismos** dieciseis huesos, las **mismas** longitudes y los **mismos** angulos
# en el plano: el salto de profundidad se convierte en un angulo fuera de plano y
# la longitud queda exacta por construccion.


def _angulo_en_plano(nombre_hueso: str, pose: sp.Pose) -> float:
    """Angulo en el plano de `nombre_hueso` en `pose`, en grados.

    Es exactamente el mismo numero que usa `svg_postura.esqueleto_canonico`:
    angulo base, mas la desviacion que la pose declara para ese hueso, mas el
    giro de tronco u hombros. Se reusa `svg_postura._giro_extra` en vez de
    copiar su regla, para que las dos cinematicas no puedan divergir; es lectura
    de `svg_postura`, que es lo que este modulo tiene permitido hacer.
    """
    desviaciones: dict[str, float] = dict(pose.angulos)
    return (
        sp.ANGULOS_BASE[nombre_hueso]
        + desviaciones.get(nombre_hueso, 0.0)
        + sp._giro_extra(nombre_hueso, pose)
    )


def _raiz_3d() -> Punto3D:
    """Arranque de la cinematica: la cadera media con profundidad 0.

    Es `svg_postura.RAIZ_CANONICA` (la articulacion `torso`) con la tercera
    coordenada en 0, que es lo que declara `PROFUNDIDAD_CANONICA["torso"]`. Por
    eso la profundidad acumulada a lo largo de cada cadena reproduce,
    articulacion por articulacion, la tabla declarada.
    """
    return (sp.RAIZ_CANONICA[0], sp.RAIZ_CANONICA[1], 0.0)


def esqueleto_3d(pose: sp.Pose) -> tuple[tuple[str, Punto3D], ...]:
    """Articulaciones de `pose` en tres dimensiones, en orden declarado.

    Un solo recorrido de `svg_postura.HUESOS`, que ya viene en orden topologico:
    cada destino se coloca sumando al origen el vector de su hueso, y ese vector
    se construye a partir de la longitud declarada `L`, del angulo en el plano
    `theta` y del angulo fuera de plano `beta = asin(dz / L)`::

        vector_3d = (L*cos(beta)*cos(theta),
                     -L*cos(beta)*sin(theta),
                      L*sin(beta))

    La Y lleva el signo negado porque la Y del SVG crece hacia abajo, igual que
    en `svg_postura`. La norma del vector es `L` **exacta** con todo `beta`
    (criterios 14.18 y 21.5); lo que se acorta es la componente en el plano, por
    el factor `cos(beta)`, y eso es Escorzo legitimo (criterios 14.19 y 21.7): el
    hombro pasa de 80 a 76.9 unidades de separacion horizontal.

    Devuelve una tupla de pares `(articulacion, (x, y, z))` en el orden de
    `diagramas_postura.ARTICULACIONES`, no un diccionario, para que el resultado
    sea inmutable y su recorrido deterministico (criterio 21.12).

    El invariante `|dz| <= L` se comprueba aqui con `raise ErrorAsset` nombrando
    el hueso, el salto y la longitud; nunca con `assert` (criterio 21.13).
    """
    puntos: dict[str, Punto3D] = {"torso": _raiz_3d()}
    for origen, destino, largo in sp.HUESOS:
        nombre: str = f"{origen}-{destino}"
        dz: float = salto_profundidad(origen, destino)
        if abs(dz) > largo:
            raise ErrorAsset(
                f"{pose.id}: el hueso {nombre} tiene un salto de profundidad de "
                f"{dz} unidades y una longitud de {largo}: |dz| <= L es la "
                "condicion para que exista el angulo fuera de plano",
                detalle={
                    "id": pose.id,
                    "hueso": nombre,
                    "salto": dz,
                    "longitud": largo,
                },
                codigo=E_ASSET_INVALIDO,
            )
        beta: float = math.asin(dz / largo)
        theta: float = math.radians(_angulo_en_plano(nombre, pose))
        plano: float = largo * math.cos(beta)
        px, py, pz = puntos[origen]
        puntos[destino] = (
            px + plano * math.cos(theta),
            py - plano * math.sin(theta),
            pz + largo * math.sin(beta),
        )
    return tuple((nombre, puntos[nombre]) for nombre in dp.ARTICULACIONES)


# --------------------------------------------------------------------------- #
# Rotaciones de cuerpo rigido, proyeccion y las dos medidas de longitud
# --------------------------------------------------------------------------- #
#
# Las dos rotaciones giran alrededor de ejes que pasan por la cadera media, que
# es la raiz de la cinematica (`svg_postura.RAIZ_CANONICA`), asi que ninguna
# altera ninguna longitud: son giros de cuerpo rigido.
#
# El azimut se aplica **antes** que la elevacion (criterios 21.3 y 21.4).


def rotar_azimut(p3: Punto3D, grados: float) -> Punto3D:
    """Gira `p3` alrededor del eje **vertical** que pasa por la cadera media.

    Es el giro que muestra la espalda y los perfiles: mezcla la coordenada
    horizontal con la profundidad y deja la vertical intacta (criterio 21.3).
    """
    xc: float = sp.RAIZ_CANONICA[0]
    x, y, z = p3
    radianes: float = math.radians(grados)
    coseno: float = math.cos(radianes)
    seno: float = math.sin(radianes)
    dx: float = x - xc
    return (xc + dx * coseno + z * seno, y, -dx * seno + z * coseno)


def rotar_elevacion(p3: Punto3D, grados: float) -> Punto3D:
    """Gira `p3` alrededor del eje horizontal **transversal** por la cadera media.

    Es el giro que muestra la coronilla y la planta del pie: mezcla la coordenada
    vertical con la profundidad y deja la horizontal intacta (criterio 21.4). El
    signo esta elegido para que `+60` sea la **picada**: el punto que estaba
    delante del cuerpo baja en pantalla y la coronilla queda a la vista.
    """
    yc: float = sp.RAIZ_CANONICA[1]
    x, y, z = p3
    radianes: float = math.radians(grados)
    coseno: float = math.cos(radianes)
    seno: float = math.sin(radianes)
    dy: float = y - yc
    return (x, yc + dy * coseno + z * seno, -dy * seno + z * coseno)


def proyectar(p3: Punto3D) -> sp.Punto:
    """Descarta la profundidad y nada mas (criterio 21.6)."""
    return (p3[0], p3[1])


def esqueleto_3d_rotado(
    pose: sp.Pose, azimut: float, elevacion: float
) -> tuple[tuple[str, Punto3D], ...]:
    """Esqueleto_3D de `pose` con el azimut aplicado antes de la elevacion.

    Es el paso intermedio que comparten `esqueleto_vista`, las dos medidas de
    longitud y `clasificar_miembros`, de modo que las cuatro vean exactamente la
    misma geometria.
    """
    salida: list[tuple[str, Punto3D]] = []
    for nombre, punto in esqueleto_3d(pose):
        girado: Punto3D = rotar_elevacion(rotar_azimut(punto, azimut), elevacion)
        salida.append((nombre, girado))
    return tuple(salida)


def esqueleto_vista(
    pose: sp.Pose,
    clave: str,
    ancho_vb: float,
    alto_vb: float,
    *,
    factor: float = sp.FACTOR_VISTA,
) -> dict[str, sp.Punto]:
    """Articulaciones proyectadas de la Vista_Figura `clave`, en el `viewBox`.

    Compone la tuberia completa y es el **unico** camino de emision:
    `esqueleto_3d` -> `rotar_azimut(azimut_de(clave))` ->
    `rotar_elevacion(elevacion_de(clave))` -> `proyectar` -> escala y traslado
    con `svg_postura.escala_figura(ancho_vb, alto_vb, factor)`.

    El `factor` por defecto es `svg_postura.FACTOR_VISTA`, que reduce la figura lo
    justo para que la envolvente **rotada** siga cayendo dentro del `viewBox` con
    los diez pares de angulos (criterio 21.8).

    El diccionario se construye en el orden de
    `diagramas_postura.ARTICULACIONES`, asi que recorrerlo es deterministico.
    """
    escala: float = sp.escala_figura(ancho_vb, alto_vb, factor)
    dx, dy = sp._traslado(ancho_vb, alto_vb, escala)
    puntos: dict[str, sp.Punto] = {}
    for nombre, punto in esqueleto_3d_rotado(
        pose, azimut_de(clave), elevacion_de(clave)
    ):
        px, py = proyectar(punto)
        puntos[nombre] = (dx + px * escala, dy + py * escala)
    return puntos


def _hueso_declarado(nombre_hueso: str) -> tuple[str, str, float]:
    """Terna `(origen, destino, longitud)` del hueso `nombre_hueso`."""
    for origen, destino, largo in sp.HUESOS:
        if f"{origen}-{destino}" == nombre_hueso:
            return (origen, destino, largo)
    raise ErrorAsset(
        f"hueso desconocido: {nombre_hueso!r}",
        detalle={"hueso": nombre_hueso},
        codigo=E_ASSET_INVALIDO,
    )


def largo_hueso_3d(
    pose: sp.Pose, nombre: str, azimut: float, elevacion: float
) -> float:
    """Longitud de `nombre` medida sobre las **tres** coordenadas del rotado.

    Es **invariante**: iguala la longitud declarada del hueso con tolerancia 1e-6
    en toda pose, todo azimut y toda elevacion (criterios 14.18 y 21.5), porque
    `esqueleto_3d` construye cada hueso con norma exacta y las dos rotaciones son
    de cuerpo rigido. Es la medida que usan las pruebas de invariancia.
    """
    origen, destino, _largo = _hueso_declarado(nombre)
    puntos: dict[str, Punto3D] = dict(
        esqueleto_3d_rotado(pose, azimut, elevacion)
    )
    ax, ay, az = puntos[origen]
    bx, by, bz = puntos[destino]
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)


def largo_hueso_proyectado(
    pose: sp.Pose, nombre: str, azimut: float, elevacion: float
) -> float:
    """Longitud de `nombre` medida sobre las **dos** coordenadas del dibujo.

    **No** es constante, y eso es correcto: el Escorzo la acorta y solo se
    garantiza que quede en `[0, L]` (criterios 14.19 y 21.7). Ninguna prueba debe
    exigir que sea constante; escribirla asi seria un error de la prueba, no del
    codigo.
    """
    origen, destino, _largo = _hueso_declarado(nombre)
    puntos: dict[str, Punto3D] = dict(
        esqueleto_3d_rotado(pose, azimut, elevacion)
    )
    ax, ay = proyectar(puntos[origen])
    bx, by = proyectar(puntos[destino])
    return math.hypot(bx - ax, by - ay)


# --------------------------------------------------------------------------- #
# Tabla declarativa de las diez Clave_Vista
# --------------------------------------------------------------------------- #
#
# Una sola tabla, no una cadena de condicionales dispersa por el emisor: el
# azimut, la elevacion y los grupos extra de cada clave viven aqui, y
# `svg_vista` los lee. Anadir una vista es anadir una fila.

#: Grupo extra de la vista de frente (criterio 23.2).
GRUPO_COLETA_RECOGIDA: str = "coleta-recogida"

#: Los tres grupos extra de la vista de espalda (criterio 23.1).
GRUPOS_ESPALDA: tuple[str, ...] = (
    "omoplatos",
    "coleta-trasera",
    "numero-camiseta",
)

#: Grupo del balon de la picada. Se emite **despues** del grupo de la figura, con
#: el centro por debajo del centro de la cadera proyectada (criterio 23.5).
GRUPO_BALON_PICADA: str = "balon-picada"

#: Los grupos extra de la picada (criterios 23.4 y 23.5).
GRUPOS_PICADA: tuple[str, ...] = (
    "hombros-superiores",
    "coronilla",
    GRUPO_BALON_PICADA,
)

#: Los grupos extra de la contrapicada (criterio 23.6).
GRUPOS_CONTRAPICADA: tuple[str, ...] = ("planta-pie-apoyo", "suela-taco")

#: La tabla de las diez Clave_Vista: `clave -> (azimut, elevacion, grupos extra)`.
#: El orden de las filas **es** el de `CLAVES_VISTA` y el de emision (22.1, 22.6).
TABLA_VISTAS: dict[str, tuple[int, int, tuple[str, ...]]] = {
    "az-000": (0, 0, (GRUPO_COLETA_RECOGIDA,)),
    "az-045": (45, 0, ()),
    "az-090": (90, 0, ()),
    "az-135": (135, 0, ()),
    "az-180": (180, 0, GRUPOS_ESPALDA),
    "az-225": (225, 0, ()),
    "az-270": (270, 0, ()),
    "az-315": (315, 0, ()),
    "el-p60": (0, 60, GRUPOS_PICADA),
    "el-m60": (0, -60, GRUPOS_CONTRAPICADA),
}


def _fila(clave: str) -> tuple[int, int, tuple[str, ...]]:
    """Fila de `clave` en la tabla, o `ErrorAsset` si la clave es desconocida."""
    fila: tuple[int, int, tuple[str, ...]] | None = TABLA_VISTAS.get(clave)
    if fila is None:
        raise ErrorAsset(
            f"Clave_Vista desconocida: {clave!r}; las declaradas son "
            f"{CLAVES_VISTA}",
            detalle={"clave": clave},
            codigo=E_ASSET_INVALIDO,
        )
    return fila


def azimut_de(clave: str) -> int:
    """Azimut declarado de `clave`, en grados. 0 en las dos Vista_Elevacion."""
    return _fila(clave)[0]


def elevacion_de(clave: str) -> int:
    """Elevacion declarada de `clave`, en grados. 0 en las ocho Vista_Azimut."""
    return _fila(clave)[1]


def grupos_extra(clave: str) -> tuple[str, ...]:
    """Grupos que `clave` anade a los cuatro obligatorios, en orden declarado."""
    return _fila(clave)[2]


def clave_de_azimut(azimut: int) -> str:
    """Clave_Vista de la Vista_Azimut con ese azimut declarado."""
    for clave in CLAVES_VISTA:
        fila: tuple[int, int, tuple[str, ...]] = TABLA_VISTAS[clave]
        if fila[1] == 0 and fila[0] == azimut:
            return clave
    raise ErrorAsset(
        f"no hay Vista_Azimut declarada para {azimut!r} grados; los declarados "
        f"son {AZIMUTS_DECLARADOS}",
        detalle={"azimut": azimut},
        codigo=E_ASSET_INVALIDO,
    )


# --------------------------------------------------------------------------- #
# Conmutador_Vista: eleccion de vista, Rotacion_Residual y Sombra_Contacto
# --------------------------------------------------------------------------- #


def normalizar_giro(angulo: float) -> float:
    """Lleva `angulo` al intervalo `[0, 360)`."""
    return float(angulo) % 360.0


def _distancia_circular(a: float, b: float) -> float:
    """Distancia **circular** entre dos angulos, en grados: siempre en `[0, 180]`."""
    bruta: float = abs(normalizar_giro(a) - normalizar_giro(b)) % 360.0
    return min(bruta, 360.0 - bruta)


def vista_mas_cercana(angulo: float, *, movil: bool = False) -> str:
    """Clave_Vista cuyo azimut declarado esta mas cerca de `angulo` (criterio 25.6).

    Normaliza el angulo a `[0, 360)`, mide la distancia **circular** a cada azimut
    candidato y devuelve la clave del minimo. Cuando dos quedan a la misma
    distancia gana el **azimut declarado menor** (criterio 25.7: a 22.5 grados
    exactos gana `az-000` sobre `az-045`), y eso sale gratis de recorrer los
    candidatos en orden ascendente y quedarse con el primer minimo estricto.

    Con `movil=True` los candidatos se reducen a `AZIMUTS_MOVIL`, los seis del
    criterio 12.7, de modo que la degradacion de pantalla angosta elija siempre
    una vista que sobrevive.
    """
    candidatos: tuple[int, ...] = AZIMUTS_MOVIL if movil else AZIMUTS_DECLARADOS
    elegido: int = candidatos[0]
    mejor: float = _distancia_circular(angulo, elegido)
    for azimut in candidatos[1:]:
        distancia: float = _distancia_circular(angulo, azimut)
        if distancia < mejor:
            mejor = distancia
            elegido = azimut
    return clave_de_azimut(elegido)


def rotacion_residual(angulo: float, clave: str) -> float:
    """Rotacion_Residual `rotateY` que la Vista_Activa aplica, en grados.

    Diferencia con signo entre `angulo` y el azimut de `clave`, normalizada al
    intervalo `(-180, 180]` y **acotada** a `[-22.5, +22.5]`: vale exactamente 0
    cuando el angulo coincide con el azimut declarado (criterio 25.11) y satura en
    el tope cuando el subconjunto movil deja huecos de 90 grados, de modo que el
    criterio 25.10 se cumple tambien degradado.
    """
    diferencia: float = (float(angulo) - azimut_de(clave)) % 360.0
    if diferencia > 180.0:
        diferencia -= 360.0
    if diferencia > ROTACION_RESIDUAL_MAX:
        return ROTACION_RESIDUAL_MAX
    if diferencia < -ROTACION_RESIDUAL_MAX:
        return -ROTACION_RESIDUAL_MAX
    return diferencia


def escala_sombra(azimut: float) -> float:
    """Escala **horizontal** de la Sombra_Contacto (criterio 25.14).

    `0.40 + 0.60 * |cos(azimut)|`: la sombra es mas ancha de frente y se estrecha
    de perfil, sin salirse nunca de `[0.40, 1.00]`. La escala vertical es fija en
    1, asi que no hay una segunda funcion que la calcule.
    """
    return 0.40 + 0.60 * abs(math.cos(math.radians(float(azimut))))


# --------------------------------------------------------------------------- #
# Clasificacion de Miembro_Trasero y Miembro_Delantero
# --------------------------------------------------------------------------- #


def punto_miembro(
    pose: sp.Pose, miembro: str, azimut: float, elevacion: float
) -> Punto3D:
    """Punto que decide la clasificacion de `miembro`, ya rotado.

    Es el **punto medio** de las articulaciones del miembro en el Esqueleto_3D,
    adelantado `ADELANTO_MIEMBRO` unidades respecto de la linea media del cuerpo,
    y despues rotado por el azimut y por la elevacion, en ese orden.

    El adelanto se aplica **antes** de rotar, porque es una propiedad del cuerpo
    (el miembro cuelga por delante del bloque del torso) y no de la camara: asi el
    giro lo arrastra igual que arrastra cualquier otra coordenada, y el signo de
    la profundidad resultante es el que describe de verdad quien queda delante.
    """
    articulaciones: tuple[str, ...] | None = None
    for nombre, lista in MIEMBROS:
        if nombre == miembro:
            articulaciones = lista
            break
    if articulaciones is None:
        raise ErrorAsset(
            f"miembro desconocido: {miembro!r}; los declarados son "
            f"{NOMBRES_MIEMBROS}",
            detalle={"miembro": miembro},
            codigo=E_ASSET_INVALIDO,
        )

    puntos: dict[str, Punto3D] = dict(esqueleto_3d(pose))
    suma_x: float = 0.0
    suma_y: float = 0.0
    suma_z: float = 0.0
    for articulacion in articulaciones:
        px, py, pz = puntos[articulacion]
        suma_x += px
        suma_y += py
        suma_z += pz
    cuantas: float = float(len(articulaciones))
    medio: Punto3D = (
        suma_x / cuantas,
        suma_y / cuantas,
        suma_z / cuantas + ADELANTO_MIEMBRO,
    )
    return rotar_elevacion(rotar_azimut(medio, azimut), elevacion)


def profundidad_miembro(
    pose: sp.Pose, miembro: str, azimut: float, elevacion: float
) -> float:
    """Profundidad rotada de `miembro`: el numero **cuyo signo** decide el grupo.

    Se expone en publico porque es lo que la Property 43 compara contra el
    reparto: la prueba no adivina el criterio, lee el mismo numero que lo decide.
    """
    return punto_miembro(pose, miembro, azimut, elevacion)[2]


def clasificar_miembros(
    pose: sp.Pose, azimut: float, elevacion: float
) -> tuple[frozenset[str], frozenset[str]]:
    """Reparte los cuatro miembros en `(traseros, delanteros)`.

    Recorre `MIEMBROS` en su **orden declarado**, mira el signo de
    `profundidad_miembro` y reparte: negativo a `traseros`, positivo a
    `delanteros` y **exactamente 0 a `delanteros`** (criterio 21.10, el desempate
    que evita que un miembro quede sin grupo al pasar por el perfil).

    La union de los dos conjuntos son siempre los cuatro miembros y su
    interseccion es siempre vacia (criterios 24.6 y 24.7). En `az-000` los cuatro
    quedan en `delanteros` (criterio 24.8), porque el adelanto del torso los pone
    a todos por delante de su bloque; en `az-180` el giro niega la profundidad y
    pasan a `traseros` los miembros cuya profundidad canonica queda delante del
    torso (criterio 24.9).
    """
    traseros: list[str] = []
    delanteros: list[str] = []
    for miembro in NOMBRES_MIEMBROS:
        if profundidad_miembro(pose, miembro, azimut, elevacion) < 0.0:
            traseros.append(miembro)
        else:
            delanteros.append(miembro)
    return (frozenset(traseros), frozenset(delanteros))


def miembro_de_articulacion(articulacion: str) -> str | None:
    """Miembro al que pertenece `articulacion`, o `None` si es axial."""
    for nombre, articulaciones in MIEMBROS:
        if articulacion in articulaciones:
            return nombre
    return None


# --------------------------------------------------------------------------- #
# Emision de una Vista_Figura
# --------------------------------------------------------------------------- #
#
# Orden del documento exacto y unico (criterio 24.1):
#
#   1. miembros-traseros   con stroke-opacity 0.55
#   2. tapa-torso          poligono opaco, distinto del relleno de la silueta
#   3. torso               relleno --azul-cielo a 0.12 y contorno --azul-profundo
#   4. miembros-delanteros con stroke-opacity 1
#   5. los grupos extra que la Clave_Vista declare, en orden de tabla
#   6. la Sombra_Contacto, como <ellipse> dentro del propio SVG
#
# El `stroke-width` de los tres grupos de trazo es el **mismo** y unico valor de
# contorno del diagrama: `stroke-opacity` cambia la opacidad, nunca el grosor
# (criterio 24.10).

#: Clase CSS de toda Vista_Figura.
CLASE_VISTA: str = "figura-vista"

#: Clase CSS que marca la Vista_Activa (criterio 22.9).
CLASE_ACTIVA: str = "activa"

#: Clave_Vista que arranca activa en el marcado inicial (criterio 22.9).
CLAVE_ACTIVA: str = CLAVES_VISTA[0]

#: Los cuatro grupos obligatorios, en el orden exacto del documento (24.1).
GRUPOS_OBLIGATORIOS: tuple[str, ...] = (
    "miembros-traseros",
    "tapa-torso",
    "torso",
    "miembros-delanteros",
)

#: Color de la Tapa_Torso en un Diagrama_Postura: `--blanco-suave` (14.20).
COLOR_TAPA_DIAGRAMA: str = paleta.WEB_HERO_BLANCO

#: Color de la Tapa_Torso en un Elemento_Fondo: `--azul-cielo` (14.20).
COLOR_TAPA_FONDO: str = paleta.WEB_HERO_CIELO

#: Articulaciones que recorre el poligono del torso, en orden. Arranca y cierra
#: en `cuello` y **nunca** pasa por `cabeza`, igual que `ORDEN_SILUETA` del
#: Generador_SVG: asi ningun relleno entra en el circulo de la cabeza.
ORDEN_TORSO: tuple[str, ...] = (
    "cuello",
    "hombro_d",
    "cadera_d",
    "cadera_i",
    "hombro_i",
)

#: Numero de camiseta que emite el grupo `numero-camiseta` (criterio 23.11).
NUMERO_CAMISETA: str = "10"

#: Radio del Balon_Esfera de la picada, en unidades canonicas (criterio 23.5).
RADIO_BALON_CANONICO: float = 54.0

#: Separacion vertical del balon respecto del centro de la cadera proyectada, en
#: unidades canonicas. Positiva: el balon queda **por debajo** (criterio 23.5).
SEPARACION_BALON_CANONICO: float = 150.0

#: Semiejes de la Sombra_Contacto en unidades canonicas (criterio 25.14). El
#: horizontal se multiplica por `escala_sombra(azimut)`; el vertical es fijo.
RADIO_SOMBRA_X_CANONICO: float = 140.0
RADIO_SOMBRA_Y_CANONICO: float = 21.0

#: Separacion de la Sombra_Contacto respecto del pie mas bajo, en canonicas.
SEPARACION_SOMBRA_CANONICA: float = 10.0

#: Opacidad del relleno de la Sombra_Contacto.
OPACIDAD_SOMBRA: float = 0.12

#: Largo de cada trazo de omoplato, en unidades canonicas.
LARGO_OMOPLATO_CANONICO: float = 70.0

#: Radio del mono del cabello recogido, en unidades canonicas. Es el mismo que
#: usa el Generador_SVG, leido de alli para que no haya dos numeros.
RADIO_MONO_CANONICO: float = sp.RADIO_MONO

#: Largo de la coleta trasera, en unidades canonicas.
LARGO_COLETA_CANONICO: float = 95.0

#: Semiejes de la planta del pie de apoyo, en unidades canonicas.
RADIO_PLANTA_X_CANONICO: float = 34.0
RADIO_PLANTA_Y_CANONICO: float = 52.0

#: Cuantos tacos dibuja el grupo `suela-taco`.
TACOS: int = 3


def _linea(
    clase: str,
    a: sp.Punto,
    b: sp.Punto,
    grosor: float,
    opacidad: float,
) -> str:
    """Un trazo de contorno con su grosor unico y su `stroke-opacity` explicito.

    La opacidad va **tambien** en cada trazo, no solo en el grupo: asi el
    criterio 24.2 ("todo trazo dentro del grupo lleva `stroke-opacity` con el
    valor 0.55") se lee directamente del elemento y no depende de la herencia.
    """
    return (
        f'<line class="{clase}" x1="{sp.num(a[0])}" y1="{sp.num(a[1])}" '
        f'x2="{sp.num(b[0])}" y2="{sp.num(b[1])}" '
        f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
        f'stroke-opacity="{sp.num(opacidad)}" stroke-linecap="round" />'
    )


def _puntos_poligono(
    puntos: dict[str, sp.Punto], orden: tuple[str, ...]
) -> str:
    """Atributo `points` de un poligono, recorriendo `orden`."""
    partes: list[str] = []
    for nombre in orden:
        px, py = puntos[nombre]
        partes.append(f"{sp.num(px)},{sp.num(py)}")
    return " ".join(partes)


def _centro(a: sp.Punto, b: sp.Punto) -> sp.Punto:
    """Punto medio de dos puntos del dibujo."""
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _unitario(desde: sp.Punto, hasta: sp.Punto) -> sp.Punto:
    """Vector unitario `desde -> hasta`, o `(0, -1)` si los dos coinciden."""
    dx: float = hasta[0] - desde[0]
    dy: float = hasta[1] - desde[1]
    largo: float = math.hypot(dx, dy)
    if largo <= 0.0:
        return (0.0, -1.0)
    return (dx / largo, dy / largo)


def _grupo_miembros(
    clase: str,
    miembros: frozenset[str],
    puntos: dict[str, sp.Punto],
    grosor: float,
    opacidad: float,
) -> str:
    """Grupo de trazos de los miembros de `miembros`, en orden de `HUESOS`."""
    partes: list[str] = [
        f'<g class="{clase}" stroke-opacity="{sp.num(opacidad)}">'
    ]
    for origen, destino, _largo in sp.HUESOS:
        miembro: str | None = miembro_de_articulacion(destino)
        if miembro is None or miembro not in miembros:
            continue
        partes.append(
            _linea(
                f"contorno hueso-{origen}-{destino}",
                puntos[origen],
                puntos[destino],
                grosor,
                opacidad,
            )
        )
    partes.append("</g>")
    return "".join(partes)


def _grupo_tapa_torso(
    puntos: dict[str, sp.Punto], color_tapa: str
) -> str:
    """Tapa_Torso: poligono **opaco**, distinto del relleno de la silueta (14.20).

    Es lo que tapa de verdad los trazos traseros que caen bajo el torso, y por eso
    lleva `fill-opacity="1"` y **ningun** trazo: si tuviera contorno se veria como
    un segundo borde encima del del torso.
    """
    return "".join(
        (
            '<g class="tapa-torso">',
            f'<polygon class="tapa" points="{_puntos_poligono(puntos, ORDEN_TORSO)}" '
            f'fill="{color_tapa}" fill-opacity="1" stroke="none" />',
            "</g>",
        )
    )


def _grupo_torso(
    puntos: dict[str, sp.Punto], grosor: float, escala: float
) -> str:
    """Grupo `torso`: silueta translucida, huesos axiales y circulo de la cabeza.

    Conserva el relleno `--azul-cielo` con `fill-opacity` 0.12 y el contorno
    `--azul-profundo` (criterio 24.5). Los dos huesos axiales
    (`torso-cuello` y `cuello-cabeza`) viven aqui porque no pertenecen a ningun
    miembro, y el hueso del cuello se corta en el borde del circulo de la cabeza
    para que ningun trazo entre en el rostro. Ningun rasgo facial: ni un elemento
    dentro del circulo (criterio 23.3).
    """
    radio: float = sp.radio_cabeza(escala)
    partes: list[str] = ['<g class="torso">']
    partes.append(
        f'<polygon class="silueta" '
        f'points="{_puntos_poligono(puntos, ORDEN_TORSO)}" '
        f'fill="{sp.COLOR_SILUETA}" '
        f'fill-opacity="{sp.num(sp.OPACIDAD_SILUETA)}" '
        f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
        f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
    )
    for origen, destino, _largo in sp.HUESOS:
        if miembro_de_articulacion(destino) is not None:
            continue
        a: sp.Punto = puntos[origen]
        b: sp.Punto = puntos[destino]
        if destino == "cabeza":
            ux, uy = _unitario(a, b)
            b = (b[0] - radio * ux, b[1] - radio * uy)
        partes.append(
            _linea(
                f"contorno hueso-{origen}-{destino}",
                a,
                b,
                grosor,
                OPACIDAD_DELANTERO,
            )
        )
    cabeza: sp.Punto = puntos["cabeza"]
    partes.append(
        f'<circle class="contorno cabeza" cx="{sp.num(cabeza[0])}" '
        f'cy="{sp.num(cabeza[1])}" r="{sp.num(radio)}" fill="none" '
        f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
        f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
    )
    partes.append("</g>")
    return "".join(partes)


def _grupo_extra(
    grupo: str,
    pose: sp.Pose,
    puntos: dict[str, sp.Punto],
    grosor: float,
    escala: float,
    ancho_vb: float,
    alto_vb: float,
) -> str:
    """Contenido del grupo extra `grupo`, en el marcado que le corresponde.

    Cada rama es un dibujo pequeno y deterministico anclado a articulaciones
    reales: nada aleatorio, nada fuera de la Paleta_Guia y ningun rasgo facial.
    """
    cabeza: sp.Punto = puntos["cabeza"]
    cuello: sp.Punto = puntos["cuello"]
    radio_cabeza: float = sp.radio_cabeza(escala)
    eje_x, eje_y = _unitario(cuello, cabeza)
    partes: list[str] = [f'<g class="{grupo}">']

    if grupo == GRUPO_COLETA_RECOGIDA:
        radio_mono: float = RADIO_MONO_CANONICO * escala
        distancia: float = radio_cabeza + radio_mono
        centro: sp.Punto = (
            cabeza[0] - distancia * eje_x,
            cabeza[1] - distancia * eje_y,
        )
        partes.append(
            f'<circle class="contorno mono" cx="{sp.num(centro[0])}" '
            f'cy="{sp.num(centro[1])}" r="{sp.num(radio_mono)}" fill="none" '
            f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
            f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
        )

    elif grupo == "omoplatos":
        largo: float = LARGO_OMOPLATO_CANONICO * escala
        for lado in ("hombro_i", "hombro_d"):
            hombro: sp.Punto = puntos[lado]
            hacia_x, hacia_y = _unitario(hombro, puntos["torso"])
            partes.append(
                _linea(
                    f"contorno omoplato-{lado}",
                    hombro,
                    (hombro[0] + largo * hacia_x, hombro[1] + largo * hacia_y),
                    grosor,
                    OPACIDAD_DELANTERO,
                )
            )

    elif grupo == "coleta-trasera":
        largo = LARGO_COLETA_CANONICO * escala
        arranque: sp.Punto = (
            cabeza[0] - radio_cabeza * eje_x,
            cabeza[1] - radio_cabeza * eje_y,
        )
        punta: sp.Punto = (
            arranque[0] - largo * eje_x,
            arranque[1] - largo * eje_y,
        )
        partes.append(
            _linea("contorno coleta", arranque, punta, grosor, OPACIDAD_DELANTERO)
        )

    elif grupo == "numero-camiseta":
        centro = _centro(puntos["cuello"], puntos["torso"])
        tamano: float = sp.tamano_fuente_etiqueta(ancho_vb)
        partes.append(
            f'<text class="numero" x="{sp.num(centro[0])}" '
            f'y="{sp.num(centro[1])}" text-anchor="middle" '
            f'dominant-baseline="middle" font-size="{sp.num(tamano)}" '
            f'font-family="sans-serif" fill="{sp.COLOR_CONTORNO}">'
            f"{NUMERO_CAMISETA}</text>"
        )

    elif grupo == "hombros-superiores":
        partes.append(
            _linea(
                "contorno linea-hombros",
                puntos["hombro_i"],
                puntos["hombro_d"],
                grosor,
                OPACIDAD_DELANTERO,
            )
        )

    elif grupo == "coronilla":
        radio_arco: float = radio_cabeza + RADIO_MONO_CANONICO * escala / 2.0
        inicio: sp.Punto = (
            cabeza[0] + radio_arco * eje_y,
            cabeza[1] - radio_arco * eje_x,
        )
        fin: sp.Punto = (
            cabeza[0] - radio_arco * eje_y,
            cabeza[1] + radio_arco * eje_x,
        )
        partes.append(
            f'<path class="contorno arco-coronilla" d="M {sp.num(inicio[0])} '
            f"{sp.num(inicio[1])} A {sp.num(radio_arco)} {sp.num(radio_arco)} "
            f'0 0 1 {sp.num(fin[0])} {sp.num(fin[1])}" fill="none" '
            f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
            f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
        )

    elif grupo == "planta-pie-apoyo":
        apoyo: sp.Punto = puntos[pose.apoyo]
        partes.append(
            f'<ellipse class="contorno planta" cx="{sp.num(apoyo[0])}" '
            f'cy="{sp.num(apoyo[1])}" '
            f'rx="{sp.num(RADIO_PLANTA_X_CANONICO * escala)}" '
            f'ry="{sp.num(RADIO_PLANTA_Y_CANONICO * escala)}" fill="none" '
            f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
            f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
        )

    elif grupo == "suela-taco":
        apoyo = puntos[pose.apoyo]
        paso: float = 2.0 * RADIO_PLANTA_Y_CANONICO * escala / float(TACOS + 1)
        ancho_taco: float = RADIO_PLANTA_X_CANONICO * escala / 2.0
        borde: float = apoyo[1] - RADIO_PLANTA_Y_CANONICO * escala
        for indice in range(TACOS):
            y: float = borde + paso * float(indice + 1)
            partes.append(
                _linea(
                    f"contorno taco-{indice + 1}",
                    (apoyo[0] - ancho_taco, y),
                    (apoyo[0] + ancho_taco, y),
                    grosor,
                    OPACIDAD_DELANTERO,
                )
            )

    elif grupo == GRUPO_BALON_PICADA:
        cadera: sp.Punto = _centro(puntos["cadera_i"], puntos["cadera_d"])
        radio_balon: float = RADIO_BALON_CANONICO * escala
        centro_y: float = cadera[1] + SEPARACION_BALON_CANONICO * escala
        limite: float = alto_vb - radio_balon
        if centro_y > limite:
            centro_y = limite
        partes.append(
            f'<circle class="contorno balon" cx="{sp.num(cadera[0])}" '
            f'cy="{sp.num(centro_y)}" r="{sp.num(radio_balon)}" '
            f'fill="{sp.COLOR_SILUETA}" '
            f'fill-opacity="{sp.num(sp.OPACIDAD_SILUETA)}" '
            f'stroke="{sp.COLOR_CONTORNO}" stroke-width="{sp.num(grosor)}" '
            f'stroke-opacity="{sp.num(OPACIDAD_DELANTERO)}" />'
        )

    else:
        raise ErrorAsset(
            f"grupo extra sin contenido declarado: {grupo!r}",
            detalle={"grupo": grupo},
            codigo=E_ASSET_INVALIDO,
        )

    partes.append("</g>")
    return "".join(partes)


def _sombra_contacto(
    clave: str,
    puntos: dict[str, sp.Punto],
    escala: float,
    alto_vb: float,
) -> str:
    """Sombra_Contacto como `<ellipse>` dentro del SVG (criterios 25.14 y 25.15).

    La escala horizontal es `escala_sombra(azimut)` y la vertical es fija en 1: la
    sombra es mas ancha de frente y se estrecha de perfil. Se emite dentro del
    propio SVG, no con `box-shadow`.
    """
    cadera: sp.Punto = _centro(puntos["cadera_i"], puntos["cadera_d"])
    radio_y: float = RADIO_SOMBRA_Y_CANONICO * escala
    radio_x: float = (
        RADIO_SOMBRA_X_CANONICO * escala * escala_sombra(azimut_de(clave))
    )
    mas_bajo: float = max(puntos["pie_i"][1], puntos["pie_d"][1])
    centro_y: float = mas_bajo + SEPARACION_SOMBRA_CANONICA * escala
    limite: float = alto_vb - radio_y
    if centro_y > limite:
        centro_y = limite
    if centro_y < radio_y:
        centro_y = radio_y
    return (
        f'<ellipse class="sombra-contacto" cx="{sp.num(cadera[0])}" '
        f'cy="{sp.num(centro_y)}" rx="{sp.num(radio_x)}" '
        f'ry="{sp.num(radio_y)}" fill="{sp.COLOR_CONTORNO}" '
        f'fill-opacity="{sp.num(OPACIDAD_SOMBRA)}" />'
    )


def svg_vista(
    pose: sp.Pose,
    clave: str,
    d: dp.DiagramaPostura,
    *,
    color_tapa: str = COLOR_TAPA_DIAGRAMA,
) -> str:
    """`<svg>` en linea completo de una Vista_Figura.

    Lleva `viewBox`, `width`, `height`, `role="img"`, `aria-label` con el `alt` del
    catalogo y `focusable="false"`, mas `data-vista` con su Clave_Vista y
    `data-figura` con el identificador de su Figura_Girable (criterios 22.7 y
    22.11). La de `az-000` arranca con la clase de Vista_Activa (criterio 22.9).

    Cero `<image>`, cero `url(`, cero `http`, cero `tabindex` y cero atributos de
    evento: lo comprueba `svg_postura.validar_marcado` sobre el marcado final.

    Todo numero pasa por `svg_postura.num`, asi que dos llamadas con la misma pose
    y la misma clave devuelven **bytes identicos** (criterios 21.11 y 21.12).
    """
    ancho_vb: float = d.ancho_svg * sp.FACTOR_VIEWBOX
    alto_vb: float = d.alto_svg * sp.FACTOR_VIEWBOX
    escala: float = sp.escala_figura(ancho_vb, alto_vb, sp.FACTOR_VISTA)
    grosor: float = sp.grosor_contorno(ancho_vb, float(d.ancho_svg))
    puntos: dict[str, sp.Punto] = esqueleto_vista(pose, clave, ancho_vb, alto_vb)
    traseros, delanteros = clasificar_miembros(
        pose, azimut_de(clave), elevacion_de(clave)
    )

    clases: str = CLASE_VISTA
    if clave == CLAVE_ACTIVA:
        clases = f"{CLASE_VISTA} {CLASE_ACTIVA}"

    partes: list[str] = [
        f'<svg class="{clases}" data-vista="{clave}" '
        f'data-figura="{sp._esc(d.id)}" '
        f'viewBox="0 0 {sp.num(ancho_vb)} {sp.num(alto_vb)}" '
        f'width="{sp.num(float(d.ancho_svg))}" '
        f'height="{sp.num(float(d.alto_svg))}" role="img" '
        f'aria-label="{sp._esc(d.alt)}" focusable="false">',
        _grupo_miembros("miembros-traseros", traseros, puntos, grosor,
                        OPACIDAD_TRASERO),
        _grupo_tapa_torso(puntos, color_tapa),
        _grupo_torso(puntos, grosor, escala),
        _grupo_miembros("miembros-delanteros", delanteros, puntos, grosor,
                        OPACIDAD_DELANTERO),
    ]
    for grupo in grupos_extra(clave):
        partes.append(
            _grupo_extra(
                grupo, pose, puntos, grosor, escala, ancho_vb, alto_vb
            )
        )
    partes.append(_sombra_contacto(clave, puntos, escala, alto_vb))
    partes.append("</svg>")

    marcado: str = "".join(partes)
    sp.validar_marcado(f"{d.id}/{clave}", marcado)
    return marcado


# --------------------------------------------------------------------------- #
# Marcado de una Figura_Girable: las diez vistas en el DOM desde el principio
# --------------------------------------------------------------------------- #

#: Clase CSS del contenedor de una Figura_Girable.
CLASE_GIRABLE: str = "figura-girable"


def svg_figura_girable(
    pose: sp.Pose,
    d: dp.DiagramaPostura,
    *,
    color_tapa: str = COLOR_TAPA_DIAGRAMA,
) -> str:
    """Contenedor con las **diez** Vista_Figura de `d`, en el orden declarado.

    Las diez viven en el DOM desde el primer fotograma, asi que retirar el
    `<script>` las conserva todas (criterio 22.8) y `az-000` sigue siendo la
    Vista_Activa (criterio 22.9). El JavaScript no crea ni destruye nada: solo
    enciende una y apaga otra, de modo que el numero de nodos de la Figura_Girable
    es el mismo antes y despues de cualquier conmutacion (criterio 25.13).
    """
    partes: list[str] = [
        f'<div class="{CLASE_GIRABLE}" data-figura="{sp._esc(d.id)}" '
        f'data-girable="1">'
    ]
    for clave in CLAVES_VISTA:
        partes.append(svg_vista(pose, clave, d, color_tapa=color_tapa))
    partes.append("</div>")
    return "".join(partes)


def vistas_de(marcado: str) -> tuple[str, ...]:
    """Clave_Vista de cada Vista_Figura que `marcado` declara, en orden.

    Ayudante de extraccion para las pruebas y para el reporte del build: lee los
    valores de `data-vista` en orden de documento, sin comparar cadenas enteras.
    """
    return tuple(_RE_DATA_VISTA.findall(marcado))


#: `data-vista="..."` de una Vista_Figura.
_RE_DATA_VISTA = re.compile(r'data-vista="([^"]+)"')

#: Un elemento `<svg ...>` de apertura, para trocear un contenedor en vistas.
_RE_APERTURA_SVG = re.compile(r"<svg\b")


def trocear_vistas(marcado: str) -> tuple[str, ...]:
    """Marcado de cada Vista_Figura de `marcado`, en orden de documento.

    Se usa para medir el tamano de cada vista contra `BYTES_MAX_VISTA` sin tener
    que reemitirla, y para que el contraejemplo de una prueba sea la vista
    infractora y no el contenedor entero.
    """
    inicios: list[int] = [c.start() for c in _RE_APERTURA_SVG.finditer(marcado)]
    trozos: list[str] = []
    for indice, inicio in enumerate(inicios):
        fin: int = inicios[indice + 1] if indice + 1 < len(inicios) else len(marcado)
        cierre: int = marcado.rfind("</svg>", inicio, fin)
        if cierre < 0:
            raise ErrorAsset(
                "una Vista_Figura no cierra su elemento <svg>",
                detalle={"posicion": inicio},
                codigo=E_ASSET_INVALIDO,
            )
        trozos.append(marcado[inicio : cierre + len("</svg>")])
    return tuple(trozos)


# --------------------------------------------------------------------------- #
# Validador del Proyector_Vistas
# --------------------------------------------------------------------------- #

#: Tolerancia de la longitud de hueso en 3D (criterios 14.18 y 21.5).
TOLERANCIA_LONGITUD: float = 1e-6

#: Grupos que ninguna Vista_Figura puede emitir: la figura es line art **sin
#: rostro** en los diez angulos (criterio 23.3).
GRUPOS_PROHIBIDOS: tuple[str, ...] = ("cara", "rasgo-facial")


def _validar_angulos_declarados(d: dp.DiagramaPostura) -> None:
    """Azimut y elevacion de las diez claves dentro de las tuplas declaradas."""
    if tuple(TABLA_VISTAS) != CLAVES_VISTA:
        raise ErrorAsset(
            f"{d.id}: la tabla de vistas declara {tuple(TABLA_VISTAS)} y las "
            f"Clave_Vista son {CLAVES_VISTA}",
            detalle={"id": d.id, "tabla": tuple(TABLA_VISTAS)},
            codigo=E_ASSET_INVALIDO,
        )
    azimutales: list[int] = []
    elevaciones: list[int] = []
    for clave in CLAVES_VISTA:
        azimut: int = azimut_de(clave)
        elevacion: int = elevacion_de(clave)
        if elevacion == 0:
            if azimut not in AZIMUTS_DECLARADOS:
                raise ErrorAsset(
                    f"{d.id}/{clave}: azimut {azimut} fuera de "
                    f"{AZIMUTS_DECLARADOS}",
                    detalle={"id": d.id, "clave": clave, "azimut": azimut},
                    codigo=E_ASSET_INVALIDO,
                )
            azimutales.append(azimut)
            continue
        if elevacion not in ELEVACIONES_DECLARADAS:
            raise ErrorAsset(
                f"{d.id}/{clave}: elevacion {elevacion} fuera de "
                f"{ELEVACIONES_DECLARADAS}",
                detalle={"id": d.id, "clave": clave, "elevacion": elevacion},
                codigo=E_ASSET_INVALIDO,
            )
        if azimut != 0:
            raise ErrorAsset(
                f"{d.id}/{clave}: una Vista_Elevacion declara azimut 0 y esta "
                f"declara {azimut}",
                detalle={"id": d.id, "clave": clave, "azimut": azimut},
                codigo=E_ASSET_INVALIDO,
            )
        elevaciones.append(elevacion)
    if tuple(azimutales) != AZIMUTS_DECLARADOS:
        raise ErrorAsset(
            f"{d.id}: las Vista_Azimut declaran {tuple(azimutales)} y deben "
            f"declarar {AZIMUTS_DECLARADOS}",
            detalle={"id": d.id, "azimuts": tuple(azimutales)},
            codigo=E_ASSET_INVALIDO,
        )
    if tuple(elevaciones) != ELEVACIONES_DECLARADAS:
        raise ErrorAsset(
            f"{d.id}: las Vista_Elevacion declaran {tuple(elevaciones)} y deben "
            f"declarar {ELEVACIONES_DECLARADAS}",
            detalle={"id": d.id, "elevaciones": tuple(elevaciones)},
            codigo=E_ASSET_INVALIDO,
        )


def _validar_longitudes(pose: sp.Pose, d: dp.DiagramaPostura) -> None:
    """Longitud 3D dentro de 1e-6 en los diez pares de angulos, hueso a hueso."""
    for clave in CLAVES_VISTA:
        azimut: int = azimut_de(clave)
        elevacion: int = elevacion_de(clave)
        for origen, destino, largo in sp.HUESOS:
            nombre: str = f"{origen}-{destino}"
            medida: float = largo_hueso_3d(pose, nombre, azimut, elevacion)
            if abs(medida - largo) > TOLERANCIA_LONGITUD * max(1.0, largo):
                raise ErrorAsset(
                    f"{d.id}/{clave}: el hueso {nombre} de la pose {pose.id} "
                    f"mide {medida} en tres dimensiones con azimut {azimut} y "
                    f"elevacion {elevacion}, y declara {largo}",
                    detalle={
                        "id": d.id,
                        "clave": clave,
                        "hueso": nombre,
                        "pose": pose.id,
                        "azimut": azimut,
                        "elevacion": elevacion,
                        "declarada": largo,
                        "medida": medida,
                    },
                    codigo=E_ASSET_INVALIDO,
                )


def _validar_dentro_del_viewbox(pose: sp.Pose, d: dp.DiagramaPostura) -> None:
    """Toda articulacion proyectada dentro del `viewBox` (criterio 21.8).

    Cuando esto falla, la solucion es **bajar `svg_postura.FACTOR_VISTA`**, nunca
    recortar el punto: recortarlo deformaria el hueso y romperia la invariancia de
    longitud. El mensaje lo dice, para que quien lo lea no se equivoque de arreglo.
    """
    ancho_vb: float = d.ancho_svg * sp.FACTOR_VIEWBOX
    alto_vb: float = d.alto_svg * sp.FACTOR_VIEWBOX
    for clave in CLAVES_VISTA:
        puntos: dict[str, sp.Punto] = esqueleto_vista(
            pose, clave, ancho_vb, alto_vb
        )
        for nombre, (px, py) in puntos.items():
            if px < 0.0 or px > ancho_vb or py < 0.0 or py > alto_vb:
                raise ErrorAsset(
                    f"{d.id}/{clave}: la articulacion {nombre!r} cae en "
                    f"({round(px, 3)}, {round(py, 3)}), fuera del viewBox de "
                    f"{sp.num(ancho_vb)}x{sp.num(alto_vb)}: se resuelve bajando "
                    f"svg_postura.FACTOR_VISTA (hoy {sp.FACTOR_VISTA}), nunca "
                    "recortando el punto",
                    detalle={
                        "id": d.id,
                        "clave": clave,
                        "articulacion": nombre,
                        "punto": (px, py),
                        "factor": sp.FACTOR_VISTA,
                    },
                    codigo=E_ASSET_INVALIDO,
                )


def _validar_particion(pose: sp.Pose, d: dp.DiagramaPostura) -> None:
    """Cada miembro en exactamente un grupo, en las diez vistas (24.6 y 24.7)."""
    todos: frozenset[str] = frozenset(NOMBRES_MIEMBROS)
    for clave in CLAVES_VISTA:
        traseros, delanteros = clasificar_miembros(
            pose, azimut_de(clave), elevacion_de(clave)
        )
        comunes: frozenset[str] = traseros & delanteros
        if comunes:
            raise ErrorAsset(
                f"{d.id}/{clave}: los miembros {tuple(sorted(comunes))} estan "
                "en los dos grupos a la vez",
                detalle={"id": d.id, "clave": clave, "miembros": tuple(sorted(comunes))},
                codigo=E_ASSET_INVALIDO,
            )
        sueltos: frozenset[str] = todos - (traseros | delanteros)
        if sueltos:
            raise ErrorAsset(
                f"{d.id}/{clave}: los miembros {tuple(sorted(sueltos))} se "
                "quedaron sin grupo",
                detalle={"id": d.id, "clave": clave, "miembros": tuple(sorted(sueltos))},
                codigo=E_ASSET_INVALIDO,
            )


def _validar_grupos(marcado: str, clave: str, d: dp.DiagramaPostura) -> None:
    """Grupos exigidos y prohibidos de una Vista_Figura, en su orden fijo."""
    presentes: tuple[str, ...] = tuple(
        casacion.split()[0] for casacion in _RE_CLASE_GRUPO.findall(marcado)
    )
    esperados: tuple[str, ...] = GRUPOS_OBLIGATORIOS + grupos_extra(clave)
    if presentes != esperados:
        raise ErrorAsset(
            f"{d.id}/{clave}: emite los grupos {presentes} y debe emitir "
            f"{esperados}, en ese orden del documento",
            detalle={"id": d.id, "clave": clave, "grupos": presentes},
            codigo=E_ASSET_INVALIDO,
        )
    for prohibido in GRUPOS_PROHIBIDOS:
        if prohibido in presentes or f'class="{prohibido}"' in marcado:
            raise ErrorAsset(
                f"{d.id}/{clave}: emite {prohibido!r}, y ninguna Vista_Figura "
                "puede llevar rostro",
                detalle={"id": d.id, "clave": clave, "prohibido": prohibido},
                codigo=E_ASSET_INVALIDO,
            )


#: `class="..."` de un elemento `<g>`.
_RE_CLASE_GRUPO = re.compile(r'<g class="([^"]+)"')


def validar_vistas(pose: sp.Pose, d: dp.DiagramaPostura) -> None:
    """Todos los invariantes del Proyector_Vistas para la Figura_Girable `d`.

    Cada uno con `raise ErrorAsset(..., codigo=E_ASSET_INVALIDO)` y mensaje en
    espanol que nombra la figura, la Clave_Vista o el hueso infractor; **ningun
    `assert`** en ninguna rama (criterio 21.13):

    * la tabla de profundidad y la particion de miembros son coherentes, y
      `|dz| <= L` en los dieciseis huesos;
    * azimut y elevacion de las diez claves estan dentro de las tuplas
      declaradas, con las ocho azimutales a elevacion 0 y las dos de elevacion a
      azimut 0;
    * la longitud 3D de cada hueso no se desvia mas de 1e-6 en ninguno de los
      diez pares de angulos;
    * toda articulacion proyectada cae dentro del `viewBox`;
    * los cuatro miembros quedan repartidos en exactamente un grupo cada uno;
    * cada Vista_Figura emite los grupos exigidos por su clave, en orden, y
      ninguno de los prohibidos;
    * la Figura_Girable emite exactamente diez Vista_Figura, con las diez
      Clave_Vista en su orden, una sola activa y esa es `az-000`;
    * cada Vista_Figura pesa `BYTES_MAX_VISTA` bytes o menos y el total del
      documento no pasa de `VISTAS_MAX`.
    """
    validar_profundidad()
    validar_miembros()
    _validar_angulos_declarados(d)
    _validar_longitudes(pose, d)
    _validar_dentro_del_viewbox(pose, d)
    _validar_particion(pose, d)

    marcado: str = svg_figura_girable(pose, d)
    claves: tuple[str, ...] = vistas_de(marcado)
    if claves != CLAVES_VISTA:
        raise ErrorAsset(
            f"{d.id}: emite las Clave_Vista {claves} y debe emitir "
            f"{CLAVES_VISTA}, en ese orden",
            detalle={"id": d.id, "claves": claves},
            codigo=E_ASSET_INVALIDO,
        )
    trozos: tuple[str, ...] = trocear_vistas(marcado)
    if len(trozos) != len(CLAVES_VISTA):
        raise ErrorAsset(
            f"{d.id}: emite {len(trozos)} Vista_Figura y debe emitir "
            f"{len(CLAVES_VISTA)}",
            detalle={"id": d.id, "cantidad": len(trozos)},
            codigo=E_ASSET_INVALIDO,
        )

    activas: tuple[str, ...] = tuple(
        clave
        for clave, trozo in zip(claves, trozos)
        if f'class="{CLASE_VISTA} {CLASE_ACTIVA}"' in trozo
    )
    if activas != (CLAVE_ACTIVA,):
        raise ErrorAsset(
            f"{d.id}: las Vista_Activa son {activas} y debe ser solo "
            f"{(CLAVE_ACTIVA,)}",
            detalle={"id": d.id, "activas": activas},
            codigo=E_ASSET_INVALIDO,
        )

    for clave, trozo in zip(claves, trozos):
        _validar_grupos(trozo, clave, d)
        tamano: int = len(trozo.encode("utf-8"))
        if tamano > BYTES_MAX_VISTA:
            raise ErrorAsset(
                f"{d.id}/{clave}: la Vista_Figura pesa {tamano} bytes y el "
                f"techo es {BYTES_MAX_VISTA}",
                detalle={"id": d.id, "clave": clave, "bytes": tamano},
                codigo=E_ASSET_INVALIDO,
            )


def validar_total_de_vistas(figuras_girables: int) -> None:
    """Comprueba el techo de Vista_Figura del Target_Web (criterio 22.13).

    `figuras_girables` es el numero de Figura_Girable del documento: las tres
    siluetas del Mundo_Hero mas `anatomia-base`. Diez vistas por figura dan
    exactamente 40, que es `VISTAS_MAX` sin margen de sobra: anadir una quinta
    obliga a bajar el numero de vistas o a subir el techo, y esto lo dice con
    `ErrorAsset` en vez de dejar que el documento engorde en silencio.
    """
    if figuras_girables < 0:
        raise ErrorAsset(
            f"el numero de Figura_Girable no puede ser negativo: "
            f"{figuras_girables}",
            detalle={"figuras": figuras_girables},
            codigo=E_ASSET_INVALIDO,
        )
    total: int = figuras_girables * len(CLAVES_VISTA)
    if total > VISTAS_MAX:
        raise ErrorAsset(
            f"{figuras_girables} Figura_Girable dan {total} Vista_Figura y el "
            f"techo del Target_Web es {VISTAS_MAX}",
            detalle={"figuras": figuras_girables, "vistas": total},
            codigo=E_ASSET_INVALIDO,
        )
