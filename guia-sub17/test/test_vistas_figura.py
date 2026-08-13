"""Pruebas del Proyector_Vistas (`vistas_figura.py`).

Feature `imagenes-reales-hero-interactivo`, bloque 5:

* **Property 40** (tarea 5.7): invariancia de hueso en el Esqueleto_3D.
* **Property 41** (tarea 5.9): Escorzo por coseno en la proyeccion.
* **Property 42** (tarea 5.10): puntos dentro del `viewBox` en las diez vistas.
* **Property 43** (tarea 5.12): clasificacion de miembros y determinismo.
* **Property 45** (tarea 5.16): orden de los cuatro grupos y opacidad.
* **Property 46** (tarea 5.17): contenido propio de cada vista especial.
* **Property 44** (tarea 5.19): tabla de las diez vistas de cada Figura_Girable.
* **Property 47** (tarea 5.14): conmutacion de vista y escalera de degradacion.

Las dos medidas de longitud son distintas **a proposito** y esta suite lo
respeta: la Property 40 exige que `largo_hueso_3d` sea invariante a 1e-6, y la
Property 41 exige que `largo_hueso_proyectado` quede en `[0, L]` **sin** exigir
que sea constante. Escribir la segunda como si fuera constante seria un error de
la prueba, no del codigo.

_Requirements: 12.7, 14.18, 14.19, 14.20, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6,
21.7, 21.8, 21.9, 21.10, 21.11, 21.12, 22.1, 22.2, 22.3, 22.6, 22.7, 22.8, 22.9,
22.10, 22.11, 22.12, 22.13, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8,
23.9, 23.10, 23.11, 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9, 24.10,
25.6, 25.7, 25.10, 25.11, 29.5, 29.6_
"""

from __future__ import annotations

import math
import os
import re
import sys
import unittest

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia import svg_postura as sp  # noqa: E402
from guia import vistas_figura as vf  # noqa: E402
from guia.errores import ErrorAsset  # noqa: E402
from prop import for_all  # noqa: E402

#: Tolerancia de las comparaciones de longitud de hueso (criterios 14.18, 21.5).
TOLERANCIA = 1e-6


def pose_de_id(pose_id: str) -> sp.Pose:
    """Pose declarada para `pose_id`, resuelta por el Generador_SVG."""
    return sp.pose_de(pose_id)


# --------------------------------------------------------------------------- #
# Property 40
# --------------------------------------------------------------------------- #

ETQ_P40 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 40: Invariancia de hueso en el Esqueleto_3D"
)


def gen_pose_azimut_elevacion(rnd) -> tuple[str, int, int]:
    """Terna `(pose, azimut declarado, elevacion declarada)` del dominio valido."""
    return (
        rnd.choice(gen.IDS_POSE),
        gen.gen_azimut_declarado(rnd),
        gen.gen_elevacion_declarada(rnd),
    )


class TestProperty40InvarianciaDeHueso3D(unittest.TestCase):
    """Property 40: invariancia de hueso en el Esqueleto_3D."""

    def test_property_40_invariancia_de_hueso_3d(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 40: Invariancia de hueso en el Esqueleto_3D.

        Para toda pose de las declaradas, para todo azimut de
        Azimuts_Declarados, para toda elevacion de Elevaciones_Declaradas y para
        todo hueso de los dieciseis, la longitud medida sobre las tres
        coordenadas del Esqueleto_3D rotado es igual a la longitud declarada de
        ese hueso con una tolerancia de 1e-6; el conjunto de claves de
        profundidad declaradas es exactamente el de las diecisiete
        articulaciones, con valor positivo en las siete del lado derecho, el
        mismo valor negado en las siete del lado izquierdo y exactamente 0 en las
        tres axiales; y el salto de profundidad de cada hueso no supera en valor
        absoluto la longitud declarada de ese hueso.

        **Validates: Requirements 14.18, 21.1, 21.2, 21.3, 21.4, 21.5**
        """
        # La tabla de profundidad y la particion de miembros son declarativas:
        # sus invariantes se comprueban una vez, no una por iteracion.
        vf.validar_profundidad()
        vf.validar_miembros()

        self.assertEqual(tuple(vf.PROFUNDIDAD_CANONICA), dp.ARTICULACIONES)
        self.assertEqual(len(vf.PROFUNDIDAD_CANONICA), 17)
        derechas = tuple(
            n for n in dp.ARTICULACIONES if n.endswith(vf.SUFIJO_DERECHO)
        )
        izquierdas = tuple(
            n for n in dp.ARTICULACIONES if n.endswith(vf.SUFIJO_IZQUIERDO)
        )
        self.assertEqual(len(derechas), 7)
        self.assertEqual(len(izquierdas), 7)
        self.assertEqual(len(vf.ARTICULACIONES_AXIALES), 3)
        for axial in vf.ARTICULACIONES_AXIALES:
            self.assertEqual(vf.PROFUNDIDAD_CANONICA[axial], 0.0, msg=axial)
        for derecha in derechas:
            espejo = f"{derecha[: -len(vf.SUFIJO_DERECHO)]}{vf.SUFIJO_IZQUIERDO}"
            self.assertGreater(vf.PROFUNDIDAD_CANONICA[derecha], 0.0, msg=derecha)
            self.assertEqual(
                vf.PROFUNDIDAD_CANONICA[espejo],
                -vf.PROFUNDIDAD_CANONICA[derecha],
                msg=espejo,
            )

        # `|dz| <= L` en los dieciseis huesos: la condicion para que exista el
        # angulo fuera de plano `beta = asin(dz / L)`.
        self.assertEqual(len(sp.HUESOS), 16)
        for origen, destino, largo in sp.HUESOS:
            salto = vf.salto_profundidad(origen, destino)
            self.assertLessEqual(
                abs(salto), largo, msg=f"{origen}-{destino}: |dz| > L"
            )

        def prop(caso: tuple[str, int, int]) -> None:
            pose_id, azimut, elevacion = caso
            pose = pose_de_id(pose_id)

            puntos = dict(vf.esqueleto_3d(pose))
            self.assertEqual(tuple(puntos), dp.ARTICULACIONES)

            # La profundidad acumulada reproduce la tabla declarada articulacion
            # por articulacion, porque la raiz arranca con profundidad 0.
            for nombre, (_x, _y, z) in puntos.items():
                self.assertAlmostEqual(
                    z,
                    vf.PROFUNDIDAD_CANONICA[nombre],
                    delta=TOLERANCIA,
                    msg=f"{pose_id}: profundidad de {nombre}",
                )

            for origen, destino, largo in sp.HUESOS:
                nombre = f"{origen}-{destino}"
                medida = vf.largo_hueso_3d(pose, nombre, azimut, elevacion)
                self.assertAlmostEqual(
                    medida,
                    largo,
                    delta=TOLERANCIA * max(1.0, largo),
                    msg=(
                        f"{pose_id}: hueso {nombre} mide {medida} en 3D con "
                        f"azimut {azimut} y elevacion {elevacion}, y declara "
                        f"{largo}"
                    ),
                )
                # Sin rotar mide lo mismo: las dos rotaciones son de cuerpo
                # rigido y no alteran ninguna longitud.
                sin_rotar = vf.largo_hueso_3d(pose, nombre, 0.0, 0.0)
                self.assertAlmostEqual(
                    sin_rotar, largo, delta=TOLERANCIA * max(1.0, largo)
                )

        for_all(
            gen_pose_azimut_elevacion,
            prop,
            iteraciones=100,
            etiqueta=ETQ_P40,
        )


# --------------------------------------------------------------------------- #
# Property 41
# --------------------------------------------------------------------------- #

ETQ_P41 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 41: Escorzo por coseno en la proyeccion"
)

#: Longitud del hueso sintetico paralelo al eje horizontal frontal, en unidades
#: canonicas. Se construye a proposito en vez de tomar uno de los dieciseis: en
#: el esqueleto real ningun hueso es **exactamente** paralelo a ese eje (el mas
#: cercano, `cuello-hombro_d`, va a 5 grados en el plano y a 16 fuera de el), asi
#: que medir sobre uno de ellos comprobaria otra cosa.
LARGO_SINTETICO = 200.0


def gen_azimut_real_y_pose_clave(rnd) -> tuple[float, str, str]:
    """Terna `(azimut real, pose, Clave_Vista)` para las dos mitades de la 41."""
    par = gen.gen_pose_clave(rnd)
    return (gen.gen_angulo_giro(rnd), par.pose_id, par.clave)


class TestProperty41EscorzoPorCoseno(unittest.TestCase):
    """Property 41: Escorzo por coseno en la proyeccion."""

    def test_property_41_escorzo_por_coseno(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 41: Escorzo por coseno en la proyeccion.

        Para todo azimut real, la longitud proyectada de un hueso paralelo al eje
        horizontal frontal es el producto de su longitud declarada por el valor
        absoluto del coseno de ese azimut, con una tolerancia de 1e-6; y para
        toda pose, toda Clave_Vista y todo hueso, la longitud proyectada queda en
        el intervalo cerrado de 0 a la longitud declarada de ese hueso, sin que
        ninguna comprobacion exija que sea constante.

        **Validates: Requirements 14.19, 21.6, 21.7**
        """
        xc, yc = sp.RAIZ_CANONICA

        def prop(caso: tuple[float, str, str]) -> None:
            azimut, pose_id, clave = caso
            pose = pose_de_id(pose_id)

            # Primera mitad: el Escorzo de un hueso paralelo al eje horizontal
            # frontal es exactamente el coseno del azimut.
            extremo_a = vf.rotar_azimut((xc - LARGO_SINTETICO / 2.0, yc, 0.0), azimut)
            extremo_b = vf.rotar_azimut((xc + LARGO_SINTETICO / 2.0, yc, 0.0), azimut)
            ax, ay = vf.proyectar(extremo_a)
            bx, by = vf.proyectar(extremo_b)
            esperado = LARGO_SINTETICO * abs(math.cos(math.radians(azimut)))
            self.assertAlmostEqual(
                math.hypot(bx - ax, by - ay),
                esperado,
                delta=TOLERANCIA * max(1.0, LARGO_SINTETICO),
                msg=f"Escorzo a {azimut} grados",
            )
            # `proyectar` descarta la profundidad y nada mas (criterio 21.6).
            self.assertEqual(vf.proyectar(extremo_a), (extremo_a[0], extremo_a[1]))

            # Segunda mitad: la longitud proyectada de todo hueso real queda en
            # `[0, L]`. NO se exige que sea constante: el Escorzo la acorta y eso
            # es lo correcto (criterio 21.7).
            az, el = vf.azimut_de(clave), vf.elevacion_de(clave)
            for origen, destino, largo in sp.HUESOS:
                nombre = f"{origen}-{destino}"
                proyectada = vf.largo_hueso_proyectado(pose, nombre, az, el)
                self.assertGreaterEqual(
                    proyectada, 0.0, msg=f"{pose_id}/{clave}/{nombre}"
                )
                self.assertLessEqual(
                    proyectada,
                    largo + TOLERANCIA * max(1.0, largo),
                    msg=f"{pose_id}/{clave}/{nombre}",
                )
                # Y nunca supera a la medida en tres dimensiones, que si es la
                # longitud declarada.
                self.assertLessEqual(
                    proyectada,
                    vf.largo_hueso_3d(pose, nombre, az, el)
                    + TOLERANCIA * max(1.0, largo),
                    msg=f"{pose_id}/{clave}/{nombre}",
                )

        for_all(
            gen_azimut_real_y_pose_clave,
            prop,
            iteraciones=100,
            etiqueta=ETQ_P41,
        )


# --------------------------------------------------------------------------- #
# Property 42
# --------------------------------------------------------------------------- #

ETQ_P42 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 42: Puntos dentro del viewBox en las diez vistas"
)


def viewbox_de(d: dp.DiagramaPostura) -> tuple[float, float]:
    """`(ancho_vb, alto_vb)` del modo SVG de `d`, que es el doble de lo declarado."""
    return (d.ancho_svg * sp.FACTOR_VIEWBOX, d.alto_svg * sp.FACTOR_VIEWBOX)


class TestProperty42PuntosDentroDelViewBox(unittest.TestCase):
    """Property 42: puntos dentro del viewBox en las diez vistas."""

    def test_property_42_puntos_dentro_del_viewbox(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 42: Puntos dentro del viewBox en las diez vistas.

        Para toda pose de las declaradas y para toda Clave_Vista, toda
        articulacion proyectada de la Vista_Figura resultante cae dentro del
        `viewBox` que esa vista declara, con las dos coordenadas en el intervalo
        cerrado que el `viewBox` define.

        **Validates: Requirements 21.8**
        """

        def prop(caso: gen.PoseClave) -> None:
            pose = pose_de_id(caso.pose_id)
            d = dp.por_id(caso.pose_id)
            ancho_vb, alto_vb = viewbox_de(d)

            puntos = vf.esqueleto_vista(pose, caso.clave, ancho_vb, alto_vb)
            self.assertEqual(tuple(puntos), dp.ARTICULACIONES)
            for nombre, (px, py) in puntos.items():
                self.assertGreaterEqual(
                    px, 0.0, msg=f"{caso.pose_id}/{caso.clave}/{nombre}"
                )
                self.assertLessEqual(
                    px, ancho_vb, msg=f"{caso.pose_id}/{caso.clave}/{nombre}"
                )
                self.assertGreaterEqual(
                    py, 0.0, msg=f"{caso.pose_id}/{caso.clave}/{nombre}"
                )
                self.assertLessEqual(
                    py, alto_vb, msg=f"{caso.pose_id}/{caso.clave}/{nombre}"
                )

        for_all(gen.gen_pose_clave, prop, iteraciones=100, etiqueta=ETQ_P42)


# --------------------------------------------------------------------------- #
# Ayudantes de extraccion sobre el marcado de una Vista_Figura
# --------------------------------------------------------------------------- #

_RE_GRUPO = re.compile(r'<g class="([^"]+)"([^>]*)>')
_RE_ELEMENTO = re.compile(r"<(\w+)\b([^>]*?)/?>")
_RE_ATRIBUTO = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_DECIMAL = re.compile(r'="(-?\d+\.(\d+))"')
_RE_SCRIPT = re.compile(r"<script\b.*?</script>", re.DOTALL)


def grupos_en_orden(marcado: str) -> tuple[str, ...]:
    """Primer nombre de clase de cada `<g>`, en orden del documento."""
    return tuple(casacion.group(1).split()[0] for casacion in _RE_GRUPO.finditer(marcado))


def cuerpo_de_grupo(marcado: str, grupo: str) -> str:
    """Marcado interior del grupo `grupo`, o cadena vacia si no lo emite.

    Se recorta desde la apertura del `<g>` con esa clase hasta su `</g>`, que en
    este emisor nunca esta anidado: cada grupo es plano.
    """
    for casacion in _RE_GRUPO.finditer(marcado):
        if casacion.group(1).split()[0] != grupo:
            continue
        inicio = casacion.end()
        fin = marcado.find("</g>", inicio)
        return marcado[inicio:fin] if fin >= 0 else marcado[inicio:]
    return ""


def elementos(marcado: str) -> tuple[tuple[str, dict[str, str]], ...]:
    """Etiqueta y atributos de cada elemento, en orden de emision."""
    salida: list[tuple[str, dict[str, str]]] = []
    for casacion in _RE_ELEMENTO.finditer(marcado):
        salida.append((casacion.group(1), dict(_RE_ATRIBUTO.findall(casacion.group(2)))))
    return tuple(salida)


def anchos_de_contorno(marcado: str) -> tuple[str, ...]:
    """Valores distintos de `stroke-width` entre los trazos de contorno.

    Se comparan como **cadenas emitidas**, que es lo que llega al navegador: dos
    trazos con el mismo grosor formateado distinto ya serian dos valores.
    """
    vistos: list[str] = []
    for _etiqueta, atributos in elementos(marcado):
        grosor = atributos.get("stroke-width")
        if grosor is not None and grosor not in vistos:
            vistos.append(grosor)
    return tuple(vistos)


def ancho_de_hombros(pose: sp.Pose, clave: str, d: dp.DiagramaPostura) -> float:
    """Ancho del rectangulo envolvente de la linea de hombros proyectada."""
    ancho_vb, alto_vb = viewbox_de(d)
    puntos = vf.esqueleto_vista(pose, clave, ancho_vb, alto_vb)
    return abs(puntos["hombro_i"][0] - puntos["hombro_d"][0])


# --------------------------------------------------------------------------- #
# Property 43
# --------------------------------------------------------------------------- #

ETQ_P43 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 43: Clasificacion de miembros y determinismo de la emision"
)


def gen_clasificacion(rnd) -> tuple[str, int, int, str]:
    """Cuarteto `(pose, azimut, elevacion, Clave_Vista)` para las dos mitades."""
    par = gen.gen_pose_clave(rnd)
    return (
        par.pose_id,
        gen.gen_azimut_declarado(rnd),
        gen.gen_elevacion_declarada(rnd),
        par.clave,
    )


class TestProperty43ClasificacionYDeterminismo(unittest.TestCase):
    """Property 43: clasificacion de miembros y determinismo de la emision."""

    def test_property_43_clasificacion_y_determinismo(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 43: Clasificacion de miembros y determinismo de la emision.

        Para toda pose, todo azimut y toda elevacion, la clasificacion reparte los
        cuatro miembros entre Miembro_Trasero y Miembro_Delantero de modo que la
        union es exactamente los cuatro y la interseccion es vacia, y el signo que
        decide es el de la profundidad rotada del punto medio de las
        articulaciones del miembro, con el valor exactamente 0 clasificado como
        Miembro_Delantero; la Vista_Figura de Clave_Vista `az-000` asigna los
        cuatro miembros a Miembro_Delantero y la de Clave_Vista `az-180` asigna a
        Miembro_Trasero los miembros cuya profundidad canonica queda delante del
        torso; y para toda pose y toda Clave_Vista, dos emisiones producen
        secuencias de bytes identicas y ningun numero del marcado lleva mas de
        tres decimales.

        **Validates: Requirements 21.9, 21.10, 21.11, 21.12, 24.6, 24.7, 24.8, 24.9**
        """
        todos = frozenset(vf.NOMBRES_MIEMBROS)
        self.assertEqual(len(todos), 4)

        def prop(caso: tuple[str, int, int, str]) -> None:
            pose_id, azimut, elevacion, clave = caso
            pose = pose_de_id(pose_id)
            d = dp.por_id(pose_id)

            traseros, delanteros = vf.clasificar_miembros(pose, azimut, elevacion)
            self.assertEqual(traseros | delanteros, todos)
            self.assertEqual(traseros & delanteros, frozenset())

            # El signo que decide es el de la profundidad rotada, y el 0 exacto
            # se clasifica como Miembro_Delantero.
            for miembro in vf.NOMBRES_MIEMBROS:
                profundidad = vf.profundidad_miembro(
                    pose, miembro, azimut, elevacion
                )
                if profundidad < 0.0:
                    self.assertIn(miembro, traseros, msg=miembro)
                else:
                    self.assertIn(miembro, delanteros, msg=miembro)

            # `az-000`: los cuatro delante. `az-180`: los cuatro atras, que son
            # exactamente los que la profundidad canonica pone delante del torso.
            frente_t, frente_d = vf.clasificar_miembros(
                pose, vf.azimut_de("az-000"), vf.elevacion_de("az-000")
            )
            self.assertEqual(frente_t, frozenset(), msg=f"{pose_id}: az-000")
            self.assertEqual(frente_d, todos, msg=f"{pose_id}: az-000")

            espalda_t, espalda_d = vf.clasificar_miembros(
                pose, vf.azimut_de("az-180"), vf.elevacion_de("az-180")
            )
            delante_del_torso = frozenset(
                miembro
                for miembro in vf.NOMBRES_MIEMBROS
                if vf.profundidad_miembro(pose, miembro, 0.0, 0.0) > 0.0
            )
            self.assertEqual(espalda_t, delante_del_torso, msg=f"{pose_id}: az-180")
            self.assertEqual(espalda_d, todos - delante_del_torso)

            # Determinismo: dos emisiones, los mismos bytes.
            primera = vf.svg_vista(pose, clave, d)
            segunda = vf.svg_vista(pose, clave, d)
            self.assertEqual(primera, segunda, msg=f"{pose_id}/{clave}")
            self.assertEqual(
                primera.encode("utf-8"),
                segunda.encode("utf-8"),
                msg=f"{pose_id}/{clave}",
            )

            # Ningun numero con mas de tres decimales: todo pasa por `num`.
            for casacion in _RE_DECIMAL.finditer(primera):
                self.assertLessEqual(
                    len(casacion.group(2)),
                    3,
                    msg=f"{pose_id}/{clave}: {casacion.group(1)}",
                )

        for_all(gen_clasificacion, prop, iteraciones=100, etiqueta=ETQ_P43)


# --------------------------------------------------------------------------- #
# Property 45
# --------------------------------------------------------------------------- #

ETQ_P45 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 45: Orden de los cuatro grupos y opacidad de profundidad"
)


class TestProperty45OrdenDeGruposYOpacidad(unittest.TestCase):
    """Property 45: orden de los cuatro grupos y opacidad de profundidad."""

    def test_property_45_orden_de_grupos_y_opacidad(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 45: Orden de los cuatro grupos y opacidad de profundidad.

        Para toda pose y para toda Clave_Vista, la Vista_Figura emite sus grupos
        en el orden fijo del documento `miembros-traseros`, `tapa-torso`, `torso`,
        `miembros-delanteros`; todo trazo del grupo `miembros-traseros` lleva
        `stroke-opacity` con el valor 0.55 y todo trazo del grupo
        `miembros-delanteros` lo lleva con el valor 1; el grupo `tapa-torso` emite
        un elemento distinto del relleno de la silueta, con `fill-opacity` igual a
        1 y con el color declarado para su fuente; el grupo `torso` conserva el
        relleno `--azul-cielo` con opacidad de 0.12 o menor y el contorno
        `--azul-profundo`; y el conjunto de valores distintos de `stroke-width`
        entre los trazos de contorno de los tres grupos de trazo tiene exactamente
        un elemento, sin que `stroke-opacity` lo altere.

        **Validates: Requirements 14.20, 24.1, 24.2, 24.3, 24.4, 24.5, 24.10**
        """
        self.assertEqual(
            vf.GRUPOS_OBLIGATORIOS,
            ("miembros-traseros", "tapa-torso", "torso", "miembros-delanteros"),
        )

        def prop(caso: gen.PoseClave) -> None:
            pose = pose_de_id(caso.pose_id)
            d = dp.por_id(caso.pose_id)
            marcado = vf.svg_vista(pose, caso.clave, d)

            # Orden fijo de los cuatro grupos obligatorios.
            grupos = grupos_en_orden(marcado)
            self.assertEqual(
                grupos[:4],
                vf.GRUPOS_OBLIGATORIOS,
                msg=f"{caso.pose_id}/{caso.clave}: {grupos}",
            )

            # Opacidad de cada trazo de los dos grupos de miembros.
            for grupo, esperada in (
                ("miembros-traseros", vf.OPACIDAD_TRASERO),
                ("miembros-delanteros", vf.OPACIDAD_DELANTERO),
            ):
                cuerpo = cuerpo_de_grupo(marcado, grupo)
                for etiqueta, atributos in elementos(cuerpo):
                    if etiqueta != "line":
                        continue
                    self.assertIn("stroke-opacity", atributos, msg=grupo)
                    self.assertAlmostEqual(
                        float(atributos["stroke-opacity"]),
                        esperada,
                        delta=TOLERANCIA,
                        msg=f"{caso.pose_id}/{caso.clave}/{grupo}",
                    )

            # Tapa_Torso: elemento distinto del relleno de la silueta, opaco.
            tapa = cuerpo_de_grupo(marcado, "tapa-torso")
            elementos_tapa = elementos(tapa)
            self.assertEqual(len(elementos_tapa), 1, msg=tapa)
            _etiqueta_tapa, atributos_tapa = elementos_tapa[0]
            self.assertEqual(atributos_tapa.get("fill-opacity"), "1")
            self.assertEqual(atributos_tapa.get("fill"), vf.COLOR_TAPA_DIAGRAMA)
            self.assertNotIn("class=\"silueta\"", tapa)

            # Grupo `torso`: relleno --azul-cielo a 0.12 o menos y contorno
            # --azul-profundo.
            cuerpo_torso = cuerpo_de_grupo(marcado, "torso")
            siluetas = [
                atributos
                for etiqueta, atributos in elementos(cuerpo_torso)
                if etiqueta == "polygon"
            ]
            self.assertEqual(len(siluetas), 1, msg=cuerpo_torso)
            self.assertEqual(siluetas[0].get("fill"), sp.COLOR_SILUETA)
            self.assertLessEqual(float(siluetas[0]["fill-opacity"]), 0.12)
            self.assertEqual(siluetas[0].get("stroke"), sp.COLOR_CONTORNO)

            # Un solo valor de `stroke-width` en los tres grupos de trazo.
            trazos = "".join(
                cuerpo_de_grupo(marcado, grupo)
                for grupo in ("miembros-traseros", "torso", "miembros-delanteros")
            )
            self.assertEqual(len(anchos_de_contorno(trazos)), 1, msg=trazos[:200])
            esperado = sp.num(
                sp.grosor_contorno(viewbox_de(d)[0], float(d.ancho_svg))
            )
            self.assertEqual(anchos_de_contorno(trazos), (esperado,))

        for_all(gen.gen_pose_clave, prop, iteraciones=100, etiqueta=ETQ_P45)


# --------------------------------------------------------------------------- #
# Property 46
# --------------------------------------------------------------------------- #

ETQ_P46 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 46: Contenido propio de cada vista especial"
)

#: Fraccion maxima del ancho de hombros de `az-000` que admiten los dos perfiles
#: (criterio 23.7).
FRACCION_PERFIL = 0.35


class TestProperty46ContenidoDeVistasEspeciales(unittest.TestCase):
    """Property 46: contenido propio de cada vista especial."""

    def test_property_46_contenido_de_vistas_especiales(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 46: Contenido propio de cada vista especial.

        Para toda pose: la Vista_Figura de Clave_Vista `az-180` contiene los
        grupos `omoplatos`, `coleta-trasera` y `numero-camiseta`, con el numero de
        camiseta emitido como elemento `<text>` en `--azul-profundo` y con un
        tamano efectivo de 12 pixeles o mas a 360 pixeles de ancho; la de
        Clave_Vista `az-000` contiene `coleta-recogida` y excluye esos tres; la de
        Clave_Vista `el-p60` contiene `hombros-superiores` y `coronilla` y emite
        el grupo del balon despues del grupo de la figura, con el centro del balon
        por debajo del centro de la cadera proyectada; la de Clave_Vista `el-m60`
        contiene `planta-pie-apoyo` y `suela-taco`; ninguna de las diez contiene
        el grupo `cara` ni ningun elemento con la clase `rasgo-facial`; el ancho
        del rectangulo envolvente de la linea de hombros proyectada es el 35 % o
        menos del de `az-000` en `az-090` y en `az-270`, y queda estrictamente
        entre el de `az-090` y el de `az-000` en `az-045`, `az-135`, `az-225` y
        `az-315`; y el marcado de cada una de las diez difiere del de las otras
        nueve, con `az-180` difiriendo de `az-000` en al menos un nombre de grupo
        ademas de en coordenadas.

        **Validates: Requirements 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9, 23.10, 23.11**
        """

        def prop(pose_id: str) -> None:
            pose = pose_de_id(pose_id)
            d = dp.por_id(pose_id)
            ancho_vb, _alto_vb = viewbox_de(d)
            por_clave = {
                clave: vf.svg_vista(pose, clave, d) for clave in vf.CLAVES_VISTA
            }

            # az-180: los tres grupos de la espalda y el numero de camiseta.
            espalda = por_clave["az-180"]
            grupos_espalda = grupos_en_orden(espalda)
            for grupo in ("omoplatos", "coleta-trasera", "numero-camiseta"):
                self.assertIn(grupo, grupos_espalda, msg=pose_id)
            numero = cuerpo_de_grupo(espalda, "numero-camiseta")
            self.assertIn("<text", numero)
            self.assertIn(f'fill="{sp.COLOR_CONTORNO}"', numero)
            tamano = float(dict(_RE_ATRIBUTO.findall(numero))["font-size"])
            self.assertGreaterEqual(
                sp.tamano_efectivo_px(tamano, ancho_vb), 12.0, msg=pose_id
            )

            # az-000: coleta recogida y ninguno de los tres de la espalda.
            frente = por_clave["az-000"]
            grupos_frente = grupos_en_orden(frente)
            self.assertIn("coleta-recogida", grupos_frente, msg=pose_id)
            for grupo in ("omoplatos", "coleta-trasera", "numero-camiseta"):
                self.assertNotIn(grupo, grupos_frente, msg=pose_id)

            # el-p60: hombros superiores, coronilla y el balon **despues** de la
            # figura, con su centro por debajo del centro de la cadera.
            picada = por_clave["el-p60"]
            grupos_picada = grupos_en_orden(picada)
            for grupo in ("hombros-superiores", "coronilla"):
                self.assertIn(grupo, grupos_picada, msg=pose_id)
            self.assertIn(vf.GRUPO_BALON_PICADA, grupos_picada, msg=pose_id)
            self.assertGreater(
                grupos_picada.index(vf.GRUPO_BALON_PICADA),
                grupos_picada.index("miembros-delanteros"),
                msg=pose_id,
            )
            balon = dict(
                _RE_ATRIBUTO.findall(cuerpo_de_grupo(picada, vf.GRUPO_BALON_PICADA))
            )
            puntos_picada = vf.esqueleto_vista(
                pose, "el-p60", *viewbox_de(d)
            )
            cadera_y = (
                puntos_picada["cadera_i"][1] + puntos_picada["cadera_d"][1]
            ) / 2.0
            self.assertGreater(float(balon["cy"]), cadera_y, msg=pose_id)

            # el-m60: planta del pie de apoyo y tacos de la suela.
            grupos_contra = grupos_en_orden(por_clave["el-m60"])
            for grupo in ("planta-pie-apoyo", "suela-taco"):
                self.assertIn(grupo, grupos_contra, msg=pose_id)

            # Ninguna de las diez lleva rostro.
            for clave, marcado in por_clave.items():
                for prohibido in vf.GRUPOS_PROHIBIDOS:
                    self.assertNotIn(prohibido, marcado, msg=f"{pose_id}/{clave}")

            # Escorzo de la linea de hombros.
            base = ancho_de_hombros(pose, "az-000", d)
            perfil = ancho_de_hombros(pose, "az-090", d)
            for clave in ("az-090", "az-270"):
                self.assertLessEqual(
                    ancho_de_hombros(pose, clave, d),
                    FRACCION_PERFIL * base,
                    msg=f"{pose_id}/{clave}",
                )
            for clave in ("az-045", "az-135", "az-225", "az-315"):
                intermedio = ancho_de_hombros(pose, clave, d)
                self.assertGreater(intermedio, perfil, msg=f"{pose_id}/{clave}")
                self.assertLess(intermedio, base, msg=f"{pose_id}/{clave}")

            # Las diez difieren entre si, y az-180 difiere de az-000 en al menos
            # un nombre de grupo, no solo en coordenadas.
            self.assertEqual(len(set(por_clave.values())), 10, msg=pose_id)
            self.assertNotEqual(
                frozenset(grupos_frente), frozenset(grupos_espalda), msg=pose_id
            )

        for_all(
            lambda rnd: rnd.choice(gen.IDS_POSE),
            prop,
            iteraciones=100,
            etiqueta=ETQ_P46,
        )


# --------------------------------------------------------------------------- #
# Property 44
# --------------------------------------------------------------------------- #

ETQ_P44 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 44: Tabla de las diez vistas de cada Figura_Girable"
)

#: Figura_Girable declaradas por el diseno: las tres siluetas del Mundo_Hero mas
#: `anatomia-base`. El Mundo_Hero llega en un bloque posterior, asi que aqui se
#: comprueba el techo con ese numero y se verifica que una quinta lo rompe.
FIGURAS_GIRABLES_DECLARADAS = 4


class TestProperty44TablaDeLasDiezVistas(unittest.TestCase):
    """Property 44: tabla de las diez vistas de cada Figura_Girable."""

    def test_property_44_tabla_de_las_diez_vistas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 44: Tabla de las diez vistas de cada Figura_Girable.

        Para toda Figura_Girable declarada, el conjunto de Clave_Vista que emite
        es exactamente el de las diez claves y en el orden declarado, con los ocho
        azimuts de Azimuts_Declarados a elevacion 0 y las dos elevaciones de
        Elevaciones_Declaradas a azimut 0; cada Vista_Figura lleva el atributo
        `data-vista` con su Clave_Vista y el atributo `data-figura` con el
        identificador de su figura, y se emite como elemento `<svg>` con
        `viewBox`, `width` y `height`; exactamente una lleva la clase de
        Vista_Activa y es la de Clave_Vista `az-000`, mientras las otras nueve
        quedan sin ella; retirar el elemento `<script>` del documento conserva las
        diez; el numero total de Vista_Figura del documento es diez veces el
        numero de Figura_Girable, es 40 o menos, y el tamano de cada Vista_Figura
        es de 6144 bytes o menos.

        **Validates: Requirements 22.1, 22.2, 22.3, 22.6, 22.7, 22.8, 22.9, 22.10, 22.11, 22.12, 22.13**
        """
        # La tabla declarativa: ocho azimuts a elevacion 0 y dos elevaciones a
        # azimut 0, en el orden exacto del criterio 22.1.
        self.assertEqual(len(vf.CLAVES_VISTA), 10)
        azimutales = tuple(
            vf.azimut_de(c) for c in vf.CLAVES_VISTA if vf.elevacion_de(c) == 0
        )
        elevaciones = tuple(
            vf.elevacion_de(c) for c in vf.CLAVES_VISTA if vf.elevacion_de(c) != 0
        )
        self.assertEqual(azimutales, vf.AZIMUTS_DECLARADOS)
        self.assertEqual(elevaciones, vf.ELEVACIONES_DECLARADAS)
        for clave in vf.CLAVES_VISTA:
            if vf.elevacion_de(clave) != 0:
                self.assertEqual(vf.azimut_de(clave), 0, msg=clave)

        # Girable verdadero solo en `anatomia-base` (criterio 22.5).
        self.assertEqual(tuple(d.id for d in dp.girables()), ("anatomia-base",))

        # El techo del documento: cuatro Figura_Girable dan exactamente 40.
        vf.validar_total_de_vistas(FIGURAS_GIRABLES_DECLARADAS)
        self.assertEqual(
            FIGURAS_GIRABLES_DECLARADAS * len(vf.CLAVES_VISTA), vf.VISTAS_MAX
        )
        with self.assertRaises(ErrorAsset):
            vf.validar_total_de_vistas(FIGURAS_GIRABLES_DECLARADAS + 1)

        def prop(_caso: int) -> None:
            girables = dp.girables()
            emitidas = 0
            for d in girables:
                pose = pose_de_id(d.id)
                marcado = vf.svg_figura_girable(pose, d)

                self.assertEqual(vf.vistas_de(marcado), vf.CLAVES_VISTA, msg=d.id)
                trozos = vf.trocear_vistas(marcado)
                self.assertEqual(len(trozos), len(vf.CLAVES_VISTA), msg=d.id)
                emitidas += len(trozos)

                activas = []
                for clave, trozo in zip(vf.CLAVES_VISTA, trozos):
                    atributos = dict(_RE_ATRIBUTO.findall(trozo[: trozo.find(">")]))
                    self.assertTrue(trozo.startswith("<svg"), msg=clave)
                    self.assertEqual(atributos.get("data-vista"), clave)
                    self.assertEqual(atributos.get("data-figura"), d.id)
                    for obligatorio in ("viewBox", "width", "height"):
                        self.assertIn(obligatorio, atributos, msg=f"{clave}")
                    if f"{vf.CLASE_VISTA} {vf.CLASE_ACTIVA}" == atributos.get("class"):
                        activas.append(clave)
                    # Prohibiciones del marcado (criterio 22.11).
                    for prohibido in sp.PROHIBIDOS_MARCADO:
                        self.assertNotIn(prohibido, trozo, msg=f"{clave}")
                    self.assertLessEqual(
                        len(trozo.encode("utf-8")),
                        vf.BYTES_MAX_VISTA,
                        msg=f"{d.id}/{clave}",
                    )
                self.assertEqual(activas, [vf.CLAVE_ACTIVA], msg=d.id)

                # Retirar el `<script>` conserva las diez: las vistas viven en el
                # DOM desde el primer fotograma, no las crea el JavaScript.
                sin_script = _RE_SCRIPT.sub("", marcado)
                self.assertEqual(vf.vistas_de(sin_script), vf.CLAVES_VISTA, msg=d.id)

            # El total es diez veces el numero de Figura_Girable, y cabe en el
            # techo de 40 del Target_Web.
            self.assertEqual(emitidas, 10 * len(girables))
            self.assertLessEqual(emitidas, vf.VISTAS_MAX)
            vf.validar_total_de_vistas(len(girables))

        for_all(
            lambda rnd: rnd.randrange(len(vf.CLAVES_VISTA)),
            prop,
            iteraciones=100,
            etiqueta=ETQ_P44,
        )


# --------------------------------------------------------------------------- #
# Property 47
# --------------------------------------------------------------------------- #

ETQ_P47 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 47: Conmutacion de vista y escalera de degradacion"
)


class TestProperty47ConmutacionYDegradacion(unittest.TestCase):
    """Property 47: conmutacion de vista y escalera de degradacion."""

    def test_property_47_conmutacion_y_degradacion(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 47: Conmutacion de vista y escalera de degradacion.

        Para todo angulo de giro real, la Clave_Vista que elige el
        Conmutador_Vista es la que minimiza la distancia circular entre ese angulo
        y su azimut declarado, y cuando dos quedan a la misma distancia es la de
        azimut declarado menor; la Rotacion_Residual de esa clave tiene un valor
        absoluto de 22.5 grados o menos y vale exactamente 0 cuando el angulo
        coincide con el azimut declarado; para todo angulo bajo el corte de 768
        pixeles, el azimut de la clave elegida pertenece al
        Subconjunto_Azimuts_Movil de seis grados; y la degradacion conserva el
        numero de Diagrama_Postura, sus dimensiones declaradas, sus
        Etiqueta_Anatomica y sus Fase_Numerada.

        **Validates: Requirements 12.7, 25.6, 25.7, 25.10, 25.11, 29.5, 29.6**
        """
        # Foto del catalogo antes de degradar: la escalera del Requisito 29 no
        # toca ningun Diagrama_Postura.
        antes = tuple(
            (d.id, dp.dimensiones(d, dp.MODO_SVG), d.etiquetas, d.fases)
            for d in dp.CATALOGO
        )

        def prop(angulo: float) -> None:
            for movil in (False, True):
                candidatos = vf.AZIMUTS_MOVIL if movil else vf.AZIMUTS_DECLARADOS
                clave = vf.vista_mas_cercana(angulo, movil=movil)
                self.assertIn(clave, vf.CLAVES_VISTA)
                azimut = vf.azimut_de(clave)
                self.assertIn(azimut, candidatos)

                # Minimiza la distancia circular, y el empate va al menor.
                distancias = tuple(
                    min(
                        abs(angulo % 360.0 - c) % 360.0,
                        360.0 - abs(angulo % 360.0 - c) % 360.0,
                    )
                    for c in candidatos
                )
                minima = min(distancias)
                propia = distancias[candidatos.index(azimut)]
                self.assertAlmostEqual(propia, minima, delta=1e-9, msg=str(angulo))
                empatados = tuple(
                    c
                    for c, dist in zip(candidatos, distancias)
                    if abs(dist - minima) <= 1e-9
                )
                self.assertEqual(azimut, min(empatados), msg=str(angulo))

                # Rotacion_Residual acotada, y exactamente 0 sobre el azimut.
                residual = vf.rotacion_residual(angulo, clave)
                self.assertLessEqual(
                    abs(residual), vf.ROTACION_RESIDUAL_MAX + 1e-9, msg=str(angulo)
                )
                if abs(vf.normalizar_giro(angulo) - azimut) <= 1e-12:
                    self.assertEqual(residual, 0.0, msg=str(angulo))

            # En el subconjunto movil el azimut elegido siempre sobrevive.
            movil_clave = vf.vista_mas_cercana(angulo, movil=True)
            self.assertIn(vf.azimut_de(movil_clave), vf.AZIMUTS_MOVIL)

            # La degradacion no toca los Diagrama_Postura.
            despues = tuple(
                (d.id, dp.dimensiones(d, dp.MODO_SVG), d.etiquetas, d.fases)
                for d in dp.CATALOGO
            )
            self.assertEqual(despues, antes)
            self.assertEqual(len(dp.CATALOGO), 8)

        for_all(gen.gen_angulo_giro, prop, iteraciones=100, etiqueta=ETQ_P47)


# --------------------------------------------------------------------------- #
# Ejemplo del techo de Vista_Figura sobre el documento real (tarea 14.4)
# --------------------------------------------------------------------------- #

from guia import build_site  # noqa: E402

#: Apertura del contenedor de una Figura_Girable, con su identificador.
_RE_ABRE_GIRABLE = re.compile(
    r'<div class="' + vf.CLASE_GIRABLE + r'" data-figura="([^"]+)"[^>]*>'
)


def contenedores_girables(documento: str) -> tuple[tuple[str, str], ...]:
    """Pares `(id de figura, marcado interior)` de cada Figura_Girable.

    El contenedor que emite `svg_figura_girable` no anida ningun `<div>`, asi que
    su cierre es el primer `</div>` que aparece tras la apertura.
    """
    salida: list[tuple[str, str]] = []
    for casacion in _RE_ABRE_GIRABLE.finditer(documento):
        inicio: int = casacion.end()
        fin: int = documento.index("</div>", inicio)
        salida.append((casacion.group(1), documento[inicio:fin]))
    return tuple(salida)


class TestEjemploCuarentaVistasEnElDocumento(unittest.TestCase):
    """Las cuarenta Vista_Figura del Target_Web, medidas sobre el documento.

    La Property 44 mide una Figura_Girable a la vez y comprueba el techo con el
    numero declarado de figuras. Este ejemplo lo mide donde importa: el documento
    emitido de verdad trae cuatro Figura_Girable (las tres siluetas del Mundo_Hero
    mas `anatomia-base`), diez Vista_Figura cada una, cuarenta en total, que es
    exactamente `VISTAS_MAX`, y ninguna vista pasa de `BYTES_MAX_VISTA`.

    _Requirements: 22.12, 22.13_
    """

    @classmethod
    def setUpClass(cls) -> None:
        # Componer el Target_Web cuesta del orden de un segundo: una sola vez.
        cls.documento: str = build_site.html_sitio()
        cls.girables: tuple[tuple[str, str], ...] = contenedores_girables(
            cls.documento
        )

    def test_cuatro_figuras_girables_con_diez_vistas_cada_una(self) -> None:
        self.assertEqual(len(self.girables), 4)
        # Los cuatro identificadores son distintos.
        ids = tuple(figura for figura, _ in self.girables)
        self.assertEqual(len(frozenset(ids)), len(ids))
        for figura, cuerpo in self.girables:
            with self.subTest(figura=figura):
                # Las diez Clave_Vista, en su orden declarado, y `az-000` activa.
                self.assertEqual(vf.vistas_de(cuerpo), vf.CLAVES_VISTA)
                self.assertEqual(
                    cuerpo.count(f'class="{vf.CLASE_VISTA} {vf.CLASE_ACTIVA}"'), 1
                )

    def test_cuarenta_vistas_en_total_y_es_el_techo(self) -> None:
        total = sum(len(vf.vistas_de(cuerpo)) for _, cuerpo in self.girables)
        self.assertEqual(total, 40)
        self.assertEqual(total, vf.VISTAS_MAX)
        # El techo lo dice el Proyector_Vistas: cuatro figuras caben, cinco no.
        vf.validar_total_de_vistas(len(self.girables))
        with self.assertRaises(ErrorAsset):
            vf.validar_total_de_vistas(len(self.girables) + 1)

    def test_ninguna_vista_pasa_del_techo_de_bytes(self) -> None:
        for figura, cuerpo in self.girables:
            trozos = vf.trocear_vistas(cuerpo)
            self.assertEqual(len(trozos), len(vf.CLAVES_VISTA), msg=figura)
            for clave, trozo in zip(vf.CLAVES_VISTA, trozos):
                with self.subTest(figura=figura, vista=clave):
                    self.assertLessEqual(
                        len(trozo.encode("utf-8")), vf.BYTES_MAX_VISTA
                    )


if __name__ == "__main__":  # pragma: no cover - ejecucion directa del modulo
    unittest.main()
