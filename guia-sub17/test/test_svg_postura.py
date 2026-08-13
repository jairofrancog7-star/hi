"""Pruebas del Generador_SVG (`svg_postura.py`).

Feature `imagenes-reales-hero-interactivo`, bloque 4:

* **Property 5** (tarea 4.2): geometria del esqueleto parametrico.
* **Property 6** (tarea 4.4): grosor de trazo unico y escalado.
* **Property 9** (tarea 4.6): tamano de fuente efectivo a 360 pixeles.
* **Property 8** (tarea 4.9): colocacion determinista de Etiqueta_Anatomica.
* **Property 7** (tarea 4.11): colores y elementos obligatorios del SVG.
* **Property 10** (tarea 4.13): coherencia y degradacion de las Fase_Numerada.

_Requirements: 4.3, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10,
14.11, 14.15, 14.17, 15.17, 15.18, 15.19_
"""

from __future__ import annotations

import itertools
import math
import os
import random
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
from prop import for_all  # noqa: E402

#: Tolerancia relativa de las comparaciones de longitud de hueso.
TOLERANCIA = 1e-6

#: Tolerancia absoluta que introduce el propio formateo del SVG. `_num` emite
#: tres decimales, asi que cada coordenada y cada radio llegan al marcado con un
#: error de hasta 5e-4; una distancia comparada contra un radio acumula
#: `sqrt(2) * 5e-4 + 5e-4`, que se redondea a 2e-3. Sin esta holgura, un punto
#: que por construccion cae **sobre** la circunferencia (el corte del cuello en
#: el borde de la cabeza) parece caer dentro por un milesimo.
TOLERANCIA_EMISION = 2e-3


def caso_valido(caso: object) -> bool:
    """True si `caso` sigue siendo un caso bien formado.

    El shrinker de `prop.py` reduce tuplas quitando elementos, asi que puede
    ofrecer casos degenerados (la tupla vacia, dimensiones nulas) que no
    pertenecen al espacio de entrada de la propiedad. Descartarlos evita que el
    contraejemplo reportado sea `()` en vez de la pose infractora.
    """
    if not isinstance(caso, tuple) or len(caso) != 2:
        return False
    indice, declaradas = caso
    if not isinstance(indice, int) or isinstance(indice, bool):
        return False
    if not isinstance(declaradas, tuple) or len(declaradas) != 2:
        return False
    return all(isinstance(v, int) and v > 0 for v in declaradas)


# --------------------------------------------------------------------------- #
# Ayudantes de extraccion sobre el marcado emitido
# --------------------------------------------------------------------------- #

_RE_ELEMENTO = re.compile(r"<(\w+)\b([^>]*?)/?>")
_RE_ATRIBUTO = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_NUMERO = re.compile(r"-?\d+(?:\.\d+)?")
_RE_TEXTO = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.DOTALL)


def elementos(marcado: str) -> tuple[tuple[str, dict[str, str]], ...]:
    """Etiqueta y atributos de cada elemento del marcado, en orden de emision."""
    salida: list[tuple[str, dict[str, str]]] = []
    for casacion in _RE_ELEMENTO.finditer(marcado):
        atributos = dict(_RE_ATRIBUTO.findall(casacion.group(2)))
        salida.append((casacion.group(1), atributos))
    return tuple(salida)


def coordenadas(etiqueta: str, atributos: dict[str, str]) -> tuple[tuple[float, float], ...]:
    """Todos los pares `(x, y)` que declara un elemento del SVG.

    Cubre `<line>` (x1/y1, x2/y2), `<circle>` (cx/cy), `<text>` (x/y),
    `<rect>` (x/y), `<polygon>`/`<polyline>` (`points`) y `<path>` (los numeros
    del atributo `d`, tomados por pares, que en este emisor son siempre puntos
    porque el unico comando curvo es un arco con radios iguales).
    """
    puntos: list[tuple[float, float]] = []
    for par in (("x1", "y1"), ("x2", "y2"), ("cx", "cy"), ("x", "y")):
        if par[0] in atributos and par[1] in atributos:
            puntos.append((float(atributos[par[0]]), float(atributos[par[1]])))
    if "points" in atributos:
        numeros = [float(n) for n in _RE_NUMERO.findall(atributos["points"])]
        puntos.extend(zip(numeros[0::2], numeros[1::2]))
    if etiqueta == "path" and "d" in atributos:
        # `M x y A rx ry rot arco barrido x y`: los radios y las banderas se
        # descartan quedandose con el primer y el ultimo par.
        numeros = [float(n) for n in _RE_NUMERO.findall(atributos["d"])]
        if len(numeros) >= 2:
            puntos.append((numeros[0], numeros[1]))
        if len(numeros) >= 9:
            puntos.append((numeros[-2], numeros[-1]))
    return tuple(puntos)


def textos_emitidos(marcado: str) -> tuple[tuple[dict[str, str], str], ...]:
    """Atributos y contenido de cada elemento `<text>`, en orden de emision."""
    salida: list[tuple[dict[str, str], str]] = []
    for casacion in _RE_TEXTO.finditer(marcado):
        atributos = dict(_RE_ATRIBUTO.findall(casacion.group(1)))
        salida.append((atributos, casacion.group(2)))
    return tuple(salida)


def por_clase(marcado: str, clase: str) -> tuple[tuple[str, dict[str, str]], ...]:
    """Elementos cuya lista de clases contiene `clase`, en orden de emision."""
    return tuple(
        (etiqueta, atributos)
        for etiqueta, atributos in elementos(marcado)
        if clase in atributos.get("class", "").split()
    )


def circulo_de_cabeza(marcado: str) -> tuple[float, float, float]:
    """Centro y radio del circulo de la cabeza que declara el marcado."""
    for etiqueta, atributos in elementos(marcado):
        if etiqueta == "circle" and "cabeza" in atributos.get("class", ""):
            return (
                float(atributos["cx"]),
                float(atributos["cy"]),
                float(atributos["r"]),
            )
    raise AssertionError("el marcado no declara el circulo de la cabeza")


def viewbox_de(declaradas: tuple[int, int]) -> tuple[float, float]:
    """`viewBox` que corresponde a unas dimensiones declaradas."""
    return (
        declaradas[0] * sp.FACTOR_VIEWBOX,
        declaradas[1] * sp.FACTOR_VIEWBOX,
    )


def gen_pose_y_viewbox(rnd: random.Random) -> tuple[int, tuple[int, int]]:
    """Indice de una de las ocho poses y un par de dimensiones declaradas."""
    return (rnd.randrange(len(sp.POSES)), gen.gen_viewbox(rnd))


# --------------------------------------------------------------------------- #
# Property 5
# --------------------------------------------------------------------------- #

ETQ_P5 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 5: Geometria del esqueleto parametrico"
)


class TestProperty5GeometriaDelEsqueleto(unittest.TestCase):
    """Property 5: geometria del esqueleto parametrico."""

    def test_property_5_geometria_del_esqueleto(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 5: Geometria del esqueleto parametrico.

        Para toda pose de las ocho declaradas y para todo par de dimensiones
        validas de `viewBox`, el esqueleto derivado tiene el mismo conjunto de
        diecisiete articulaciones y los mismos dieciseis huesos, la distancia
        entre los extremos de cada hueso es igual a la longitud declarada de ese
        hueso (la misma en las ocho poses, con tolerancia 1e-6), todo punto
        articulado cae dentro del `viewBox`, y el marcado resultante contiene el
        grupo del cabello recogido y ningun elemento dentro del circulo de la
        cabeza.

        **Validates: Requirements 14.1, 14.4**
        """
        sp.validar_poses()

        def prop(caso: tuple[int, tuple[int, int]]) -> None:
            if not caso_valido(caso):
                return
            indice, declaradas = caso
            pose = sp.POSES[indice % len(sp.POSES)]
            ancho_vb, alto_vb = viewbox_de(declaradas)
            escala = sp.escala_figura(ancho_vb, alto_vb)

            # Diecisiete articulaciones, las mismas y en el mismo orden que
            # declara el catalogo del bloque 2, y todo punto dentro del viewBox.
            por_pose: dict[str, dict[str, tuple[float, float]]] = {}
            for otra in sp.POSES:
                puntos = sp.esqueleto(otra, ancho_vb, alto_vb)
                self.assertEqual(tuple(puntos), dp.ARTICULACIONES)
                self.assertEqual(len(puntos), 17)
                for nombre_art, (px, py) in puntos.items():
                    self.assertGreaterEqual(px, 0.0, msg=nombre_art)
                    self.assertGreaterEqual(py, 0.0, msg=nombre_art)
                    self.assertLessEqual(px, ancho_vb, msg=nombre_art)
                    self.assertLessEqual(py, alto_vb, msg=nombre_art)
                por_pose[otra.id] = puntos

            # Dieciseis huesos, cada uno con su longitud declarada (escalada al
            # viewBox) y la misma en las ocho poses.
            self.assertEqual(len(sp.HUESOS), 16)
            for origen, destino, largo in sp.HUESOS:
                nombre = f"{origen}-{destino}"
                esperado = sp.largo_hueso(nombre, ancho_vb, alto_vb)
                self.assertAlmostEqual(
                    esperado, largo * escala, delta=TOLERANCIA * max(1.0, largo)
                )
                for otra in sp.POSES:
                    ax, ay = por_pose[otra.id][origen]
                    bx, by = por_pose[otra.id][destino]
                    self.assertAlmostEqual(
                        math.hypot(bx - ax, by - ay),
                        esperado,
                        delta=TOLERANCIA * max(1.0, esperado),
                        msg=f"{otra.id}: hueso {nombre}",
                    )

            # Cabello recogido presente y rostro sin ningun rasgo: ningun
            # elemento distinto del propio circulo de la cabeza declara una
            # coordenada dentro de ese circulo.
            marcado = sp.svg_figura(pose, ancho_vb, alto_vb, float(declaradas[0]))
            self.assertIn('<g class="cabello-recogido">', marcado)
            cx, cy, radio = circulo_de_cabeza(marcado)
            for etiqueta, atributos in elementos(marcado):
                clase = atributos.get("class", "")
                if etiqueta == "circle" and "cabeza" in clase:
                    continue
                for px, py in coordenadas(etiqueta, atributos):
                    self.assertGreaterEqual(
                        math.hypot(px - cx, py - cy),
                        radio - TOLERANCIA_EMISION,
                        msg=f"{etiqueta} {clase!r} dentro del circulo de la cabeza",
                    )

        for_all(gen_pose_y_viewbox, prop, iteraciones=100, etiqueta=ETQ_P5)


# --------------------------------------------------------------------------- #
# Property 6
# --------------------------------------------------------------------------- #

ETQ_P6 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 6: Grosor de trazo unico y escalado"
)


def gen_anchos(rnd: random.Random) -> tuple[int, int]:
    """Par `(ancho_viewBox, ancho_declarado)` de enteros positivos.

    Incluye los bordes reales del catalogo (360 y 1200 declarados, con su
    `viewBox` al doble) y los extremos del rango (1 unidad).
    """
    forma: int = rnd.randrange(4)
    if forma == 0:
        return (1, 1)
    if forma == 1:
        return (720, 360)
    if forma == 2:
        return (2400, 1200)
    return (rnd.randint(1, 4000), rnd.randint(1, 2000))


def anchos_de_contorno(marcado: str) -> tuple[str, ...]:
    """Valores distintos de `stroke-width` entre los trazos de contorno.

    Se comparan como **cadenas emitidas**, que es lo que llega al navegador: dos
    trazos con el mismo grosor pero formateado distinto ya serian dos valores.
    Se conserva el orden de aparicion para que el fallo sea reproducible.
    """
    vistos: list[str] = []
    for _etiqueta, atributos in elementos(marcado):
        if "contorno" not in atributos.get("class", ""):
            continue
        grosor = atributos.get("stroke-width", "")
        if grosor not in vistos:
            vistos.append(grosor)
    return tuple(vistos)


class TestProperty6GrosorUnicoYEscalado(unittest.TestCase):
    """Property 6: grosor de trazo unico y escalado."""

    def test_property_6_grosor_unico_y_escalado(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 6: Grosor de trazo unico y escalado.

        Para todo ancho declarado positivo y todo ancho de `viewBox` positivo, el
        grosor del contorno es `2 * ancho_viewBox / ancho_declarado` y el de la
        linea guia es la mitad de ese valor; y para todo Diagrama_Postura
        emitido, el conjunto de valores distintos de `stroke-width` entre los
        trazos de contorno de su figura tiene exactamente un elemento.

        **Validates: Requirements 14.2, 14.3**
        """

        def prop(caso: tuple[int, int]) -> None:
            if not isinstance(caso, tuple) or len(caso) != 2:
                return
            if not all(isinstance(v, int) and v > 0 for v in caso):
                return
            ancho_vb, ancho_declarado = float(caso[0]), float(caso[1])

            contorno = sp.grosor_contorno(ancho_vb, ancho_declarado)
            guia = sp.grosor_guia(ancho_vb, ancho_declarado)
            self.assertAlmostEqual(contorno, 2.0 * ancho_vb / ancho_declarado)
            self.assertAlmostEqual(guia, contorno / 2.0)
            self.assertGreater(contorno, 0.0)

        for_all(gen_anchos, prop, iteraciones=100, etiqueta=ETQ_P6)

        # Segunda clausula: un unico `stroke-width` de contorno por diagrama.
        for diagrama in dp.CATALOGO:
            with self.subTest(diagrama=diagrama.id):
                ancho_vb, alto_vb = (
                    diagrama.ancho_svg * sp.FACTOR_VIEWBOX,
                    diagrama.alto_svg * sp.FACTOR_VIEWBOX,
                )
                marcado = sp.svg_figura(
                    sp.pose_de(diagrama.id),
                    ancho_vb,
                    alto_vb,
                    float(diagrama.ancho_svg),
                )
                distintos = anchos_de_contorno(marcado)
                self.assertEqual(len(distintos), 1, msg=f"{distintos!r}")
                self.assertEqual(
                    distintos[0],
                    sp._num(sp.grosor_contorno(ancho_vb, float(diagrama.ancho_svg))),
                )


# --------------------------------------------------------------------------- #
# Property 9
# --------------------------------------------------------------------------- #

ETQ_P9 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 9: Tamano de fuente efectivo a 360 pixeles"
)


def gen_ancho_viewbox(rnd: random.Random) -> int:
    """Ancho de `viewBox` positivo, con los extremos del rango incluidos."""
    forma: int = rnd.randrange(4)
    if forma == 0:
        return 1
    if forma == 1:
        return 720
    if forma == 2:
        return 2400
    return rnd.randint(1, 20000)


class TestProperty9TamanoDeFuenteEfectivo(unittest.TestCase):
    """Property 9: tamano de fuente efectivo a 360 pixeles."""

    def test_property_9_tamano_de_fuente_efectivo(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 9: Tamano de fuente efectivo a 360 pixeles.

        Para todo ancho de `viewBox` positivo, el tamano de fuente que elige el
        Generador_SVG para las Etiqueta_Anatomica cumple que su tamano efectivo,
        calculado como `tamano * 360 / ancho_viewBox`, es 12 pixeles o mas.

        **Validates: Requirements 15.17**
        """

        def prop(ancho: int) -> None:
            if not isinstance(ancho, int) or isinstance(ancho, bool) or ancho <= 0:
                return
            ancho_vb = float(ancho)
            tamano = sp.tamano_fuente_etiqueta(ancho_vb)
            efectivo = sp.tamano_efectivo_px(tamano, ancho_vb)
            self.assertGreaterEqual(
                efectivo,
                sp.TAMANO_EFECTIVO_MINIMO,
                msg=f"ancho_vb={ancho_vb!r} tamano={tamano!r}",
            )
            # El tamano es un entero de unidades del viewBox: nada de fracciones
            # que el navegador tenga que redondear por su cuenta.
            self.assertEqual(tamano, float(int(tamano)))

        for_all(gen_ancho_viewbox, prop, iteraciones=100, etiqueta=ETQ_P9)


# --------------------------------------------------------------------------- #
# Property 8
# --------------------------------------------------------------------------- #

ETQ_P8 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 8: Colocacion determinista de Etiqueta_Anatomica"
)


def viewbox_declarado(d: dp.DiagramaPostura) -> tuple[float, float]:
    """`viewBox` del modo SVG de una entrada del catalogo."""
    return (d.ancho_svg * sp.FACTOR_VIEWBOX, d.alto_svg * sp.FACTOR_VIEWBOX)


def colocacion_de(
    d: dp.DiagramaPostura, etiquetas: tuple[str, ...]
) -> tuple[sp.Etiqueta, ...]:
    """Etiquetas ya colocadas de `d`, con el factor de figura de su modo."""
    ancho_vb, alto_vb = viewbox_declarado(d)
    factor = sp.factor_figura(len(etiquetas))
    puntos = sp.esqueleto(sp.pose_de(d.id), ancho_vb, alto_vb, factor=factor)
    return sp.colocar_etiquetas(
        sp.pose_de(d.id), etiquetas, puntos, ancho_vb, alto_vb
    )


def emision_diagrama(d: dp.DiagramaPostura, etiquetas: tuple[str, ...]) -> str:
    """Marcado del diagrama tal como lo compone hoy el Generador_SVG.

    Es el **mismo orden** que ensambla `svg_diagrama` dentro del `<svg>`: figura,
    adornos, fases, etiquetas y, en modo FUERA, la Zona_Tactil de ampliacion. Se
    compone aqui para poder variar el conjunto de etiquetas (que `svg_diagrama`
    toma del catalogo), y la propiedad comprueba que con las etiquetas
    declaradas las dos emisiones coinciden.
    """
    ancho_vb, alto_vb = viewbox_declarado(d)
    factor = sp.factor_figura(len(etiquetas))
    tamano = sp.tamano_fuente_etiqueta(ancho_vb)
    colocadas = colocacion_de(d, etiquetas)
    partes: list[str] = [
        sp.svg_figura(
            sp.pose_de(d.id), ancho_vb, alto_vb, float(d.ancho_svg), factor=factor
        ),
        sp.svg_adornos(
            sp.pose_de(d.id), ancho_vb, alto_vb, float(d.ancho_svg), factor=factor
        ),
        sp.svg_fases(d, ancho_vb, alto_vb, factor=factor),
        sp.svg_etiquetas(colocadas, ancho_vb, float(d.ancho_svg), tamano),
    ]
    if len(etiquetas) > sp.MAXIMO_ETIQUETAS_DENTRO:
        partes.append(sp.svg_zona_ampliacion(d, ancho_vb, alto_vb, tamano))
    return "".join(partes)


def gen_diagrama_y_etiquetas(rnd: random.Random) -> tuple[int, tuple[str, ...]]:
    """Una entrada del catalogo y un subconjunto de las etiquetas que declara.

    Generador acotado al espacio de entrada real: las etiquetas salen siempre del
    vocabulario que declara esa entrada y conservan su orden declarado, de modo
    que el caso generado es un Diagrama_Postura legitimo con menos rotulos. Una
    de cada tres veces se ofrece la tupla declarada completa, que es el caso que
    de verdad se emite (y el unico que lleva `anatomia-base` a las dieciseis
    etiquetas del modo FUERA).
    """
    indice: int = rnd.randrange(len(dp.CATALOGO))
    declaradas: tuple[str, ...] = dp.CATALOGO[indice].etiquetas
    if rnd.randrange(3) == 0:
        return (indice, declaradas)
    cantidad: int = rnd.randint(1, len(declaradas))
    posiciones = sorted(rnd.sample(range(len(declaradas)), cantidad))
    return (indice, tuple(declaradas[i] for i in posiciones))


def caso_valido_p8(caso: object) -> bool:
    """True si `caso` sigue siendo `(indice de entrada, etiquetas declaradas)`.

    El shrinker reduce tuplas y cadenas, asi que puede ofrecer la tupla vacia de
    etiquetas o un texto que ya no pertenece al vocabulario. Esos casos no estan
    en el espacio de entrada de la propiedad y se descartan.
    """
    if not isinstance(caso, tuple) or len(caso) != 2:
        return False
    indice, etiquetas = caso
    if not isinstance(indice, int) or isinstance(indice, bool):
        return False
    if not 0 <= indice < len(dp.CATALOGO):
        return False
    if not isinstance(etiquetas, tuple) or not etiquetas:
        return False
    declaradas = dp.CATALOGO[indice].etiquetas
    if len(set(etiquetas)) != len(etiquetas):
        return False
    return all(isinstance(e, str) and e in declaradas for e in etiquetas)


class TestProperty8ColocacionDeEtiquetas(unittest.TestCase):
    """Property 8: colocacion determinista de Etiqueta_Anatomica."""

    def test_property_8_colocacion_de_etiquetas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 8: Colocacion determinista de Etiqueta_Anatomica.

        Para todo Diagrama_Postura y para toda Etiqueta_Anatomica que declara: la
        etiqueta se emite como elemento `<text>` con el color `--azul-profundo`;
        su linea guia usa `--azul-linea`, arranca del borde del texto y termina
        exactamente en la coordenada de la articulacion senalada, con un circulo
        relleno en ese extremo; ningun par de rectangulos de texto se solapa; el
        numero de etiquetas emitidas dentro del contorno de la figura es 8 o
        menos; si el diagrama declara mas de 8 etiquetas, entonces ninguna cae
        dentro del rectangulo que envuelve a la figura y el bloque emite ademas
        una Zona_Tactil de ampliacion a pantalla completa; y dos emisiones del
        mismo diagrama producen bytes identicos.

        **Validates: Requirements 14.6, 14.7, 15.18, 15.19**
        """

        def prop(caso: tuple[int, tuple[str, ...]]) -> None:
            if not caso_valido_p8(caso):
                return
            indice, etiquetas = caso
            d = dp.CATALOGO[indice]
            ancho_vb, alto_vb = viewbox_declarado(d)
            factor = sp.factor_figura(len(etiquetas))
            fuera = len(etiquetas) > sp.MAXIMO_ETIQUETAS_DENTRO

            colocadas = colocacion_de(d, etiquetas)
            self.assertEqual(
                tuple(e.texto for e in colocadas),
                etiquetas,
                msg="la colocacion no conserva el orden declarado",
            )
            marcado = emision_diagrama(d, etiquetas)
            self._revisar_texto_y_guia(marcado, colocadas, d, ancho_vb)
            self._revisar_solapes(colocadas)
            self._revisar_modo(marcado, colocadas, d, ancho_vb, alto_vb, factor, fuera)

            # Determinismo: la misma entrada da los mismos bytes.
            self.assertEqual(
                marcado.encode("utf-8"),
                emision_diagrama(d, etiquetas).encode("utf-8"),
                msg=f"{d.id}: la emision no es reproducible byte a byte",
            )
            # Con las etiquetas que el diagrama declara de verdad, la emision es
            # exactamente el cuerpo del `<svg>` que ensambla `svg_diagrama`, que
            # tambien es reproducible byte a byte.
            if etiquetas == d.etiquetas:
                completo = sp.svg_diagrama(d)
                self.assertIn(marcado, completo)
                self.assertEqual(
                    completo.encode("utf-8"), sp.svg_diagrama(d).encode("utf-8")
                )

        for_all(gen_diagrama_y_etiquetas, prop, iteraciones=100, etiqueta=ETQ_P8)

    # ---------------------------------------------------------------- #
    # Clausulas de la propiedad, separadas para que el fallo se lea solo
    # ---------------------------------------------------------------- #

    def _revisar_texto_y_guia(
        self,
        marcado: str,
        colocadas: tuple[sp.Etiqueta, ...],
        d: dp.DiagramaPostura,
        ancho_vb: float,
    ) -> None:
        """Cada etiqueta es un `<text>` en `--azul-profundo` con su linea guia."""
        emitidos = {
            contenido: atributos
            for atributos, contenido in textos_emitidos(marcado)
        }
        guias: list[tuple[float, ...]] = []
        puntos_guia: list[tuple[str, str, str]] = []
        for etiqueta_svg, atributos in elementos(marcado):
            clase = atributos.get("class", "")
            if etiqueta_svg == "polyline" and "guia" in clase.split():
                guias.append(
                    tuple(float(n) for n in _RE_NUMERO.findall(atributos["points"]))
                )
            if etiqueta_svg == "circle" and "guia-punto" in clase.split():
                puntos_guia.append(
                    (atributos["cx"], atributos["cy"], atributos.get("fill", ""))
                )

        for e in colocadas:
            self.assertIn(e.texto, emitidos, msg=f"{d.id}: {e.texto!r} sin <text>")
            atributos = emitidos[e.texto]
            self.assertEqual(
                atributos.get("fill"),
                sp.COLOR_CONTORNO,
                msg=f"{d.id}: {e.texto!r} no va en --azul-profundo",
            )
            self.assertEqual(
                sp.TOKEN_POR_COLOR[atributos["fill"]], "--azul-profundo"
            )
            self.assertEqual(atributos.get("x"), sp._num(e.x))
            self.assertEqual(atributos.get("y"), sp._num(e.y))

            # La guia arranca en un borde vertical del rectangulo del texto, a la
            # altura del texto, y termina exactamente en el punto senalado.
            x0, _y0, x1, _y1 = sp.rectangulo(e)
            arranque = (e.tramos[0][0], e.tramos[0][1])
            self.assertAlmostEqual(arranque[1], e.y, delta=TOLERANCIA_EMISION)
            self.assertTrue(
                min(abs(arranque[0] - x0), abs(arranque[0] - x1))
                <= TOLERANCIA_EMISION,
                msg=f"{d.id}: la guia de {e.texto!r} no arranca del borde del texto",
            )
            self.assertEqual(e.tramos[-1], e.punto)
            self.assertEqual(
                e.punto,
                sp.punto_de_etiqueta(
                    e.texto,
                    sp.pose_de(d.id),
                    sp.esqueleto(
                        sp.pose_de(d.id),
                        ancho_vb,
                        d.alto_svg * sp.FACTOR_VIEWBOX,
                        factor=sp.factor_figura(len(colocadas)),
                    ),
                    ancho_vb,
                    sp.escala_figura(
                        ancho_vb,
                        d.alto_svg * sp.FACTOR_VIEWBOX,
                        sp.factor_figura(len(colocadas)),
                    ),
                ),
                msg=f"{d.id}: {e.texto!r} no apunta a su articulacion",
            )

            # La polilinea emitida termina en ese mismo punto y ahi hay un
            # circulo relleno en `--azul-linea`.
            final = (sp._num(e.punto[0]), sp._num(e.punto[1]))
            self.assertTrue(
                any(
                    sp._num(g[-2]) == final[0] and sp._num(g[-1]) == final[1]
                    for g in guias
                ),
                msg=f"{d.id}: ninguna guia termina en el punto de {e.texto!r}",
            )
            self.assertIn(
                (final[0], final[1], sp.COLOR_GUIA),
                puntos_guia,
                msg=f"{d.id}: {e.texto!r} sin circulo relleno en su extremo",
            )

        for _etiqueta_svg, atributos in elementos(marcado):
            if "guia" in atributos.get("class", "").split():
                self.assertEqual(atributos.get("stroke"), sp.COLOR_GUIA)
                self.assertEqual(
                    sp.TOKEN_POR_COLOR[atributos["stroke"]], "--azul-linea"
                )

    def _revisar_solapes(self, colocadas: tuple[sp.Etiqueta, ...]) -> None:
        """Ningun par de rectangulos de texto comparte area."""
        rectangulos = [sp.rectangulo(e) for e in colocadas]
        for i, j in itertools.combinations(range(len(rectangulos)), 2):
            self.assertFalse(
                sp.se_solapan(rectangulos[i], rectangulos[j]),
                msg=(
                    f"se solapan {colocadas[i].texto!r} y {colocadas[j].texto!r}: "
                    f"{rectangulos[i]!r} vs {rectangulos[j]!r}"
                ),
            )

    def _revisar_modo(
        self,
        marcado: str,
        colocadas: tuple[sp.Etiqueta, ...],
        d: dp.DiagramaPostura,
        ancho_vb: float,
        alto_vb: float,
        factor: float,
        fuera: bool,
    ) -> None:
        """Tope de ocho dentro del contorno y Zona_Tactil del modo FUERA."""
        caja = sp.caja_figura(sp.pose_de(d.id), ancho_vb, alto_vb, factor=factor)
        dentro = [e for e in colocadas if sp.se_solapan(sp.rectangulo(e), caja)]
        self.assertLessEqual(
            len(dentro),
            sp.MAXIMO_ETIQUETAS_DENTRO,
            msg=f"{d.id}: {len(dentro)} etiquetas dentro del contorno",
        )
        self.assertLessEqual(
            sum(1 for e in colocadas if e.dentro), sp.MAXIMO_ETIQUETAS_DENTRO
        )

        if not fuera:
            self.assertNotIn(f'href="#{sp.ancla_ampliacion(d.id)}"', marcado)
            return

        # Mas de ocho etiquetas: ninguna cae dentro del rectangulo que envuelve a
        # la figura y el bloque emite la Zona_Tactil de ampliacion.
        self.assertEqual(dentro, [], msg=f"{d.id}: etiquetas dentro de la caja")
        for e in colocadas:
            self.assertFalse(e.dentro)
        self.assertIn(f'href="#{sp.ancla_ampliacion(d.id)}"', marcado)
        self.assertIn('class="zona-tactil"', marcado)
        self.assertNotIn("tabindex", marcado)


# --------------------------------------------------------------------------- #
# Property 7
# --------------------------------------------------------------------------- #

ETQ_P7 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 7: Colores y elementos obligatorios del SVG"
)


class TestProperty7ColoresYElementos(unittest.TestCase):
    """Property 7: colores y elementos obligatorios del SVG."""

    def test_property_7_colores_y_elementos(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 7: Colores y elementos obligatorios del SVG.

        Para todo Diagrama_Postura emitido: todo trazo de contorno usa el color
        `--azul-profundo`; el relleno de la silueta usa `--azul-cielo` con una
        opacidad de 0.12 o menor; toda flecha de movimiento usa `--coral-alerta`
        y declara `stroke-dasharray`; existe una linea media con las dos
        coordenadas horizontales iguales y con `stroke-dasharray`; y existe
        exactamente un punto relleno de centro de gravedad, situado sobre esa
        linea media.

        **Validates: Requirements 14.5, 14.8, 14.9**
        """

        def prop(caso: tuple[int, tuple[str, ...]]) -> None:
            if not caso_valido_p8(caso):
                return
            indice, etiquetas = caso
            d = dp.CATALOGO[indice]
            pose = sp.pose_de(d.id)
            marcado = emision_diagrama(d, etiquetas)

            self._revisar_contorno_y_silueta(marcado, d)
            self._revisar_flechas(marcado, pose, d)
            self._revisar_eje(marcado, d)

        for_all(gen_diagrama_y_etiquetas, prop, iteraciones=100, etiqueta=ETQ_P7)

    # ---------------------------------------------------------------- #
    # Clausulas de la propiedad
    # ---------------------------------------------------------------- #

    def _revisar_contorno_y_silueta(
        self, marcado: str, d: dp.DiagramaPostura
    ) -> None:
        """Contorno en `--azul-profundo` y silueta en `--azul-cielo` al 0.12."""
        trazos = por_clase(marcado, "contorno")
        self.assertGreater(len(trazos), 0, msg=f"{d.id}: sin trazos de contorno")
        for etiqueta_svg, atributos in trazos:
            self.assertEqual(
                atributos.get("stroke"),
                sp.COLOR_CONTORNO,
                msg=f"{d.id}: {etiqueta_svg} de contorno fuera de --azul-profundo",
            )
            self.assertEqual(
                sp.TOKEN_POR_COLOR[atributos["stroke"]], "--azul-profundo"
            )

        siluetas = por_clase(marcado, "silueta")
        self.assertEqual(len(siluetas), 1, msg=f"{d.id}: siluetas={len(siluetas)}")
        _etiqueta_svg, atributos = siluetas[0]
        self.assertEqual(atributos.get("fill"), sp.COLOR_SILUETA)
        self.assertEqual(sp.TOKEN_POR_COLOR[atributos["fill"]], "--azul-cielo")
        self.assertLessEqual(float(atributos["fill-opacity"]), 0.12)

    def _revisar_flechas(
        self, marcado: str, pose: sp.Pose, d: dp.DiagramaPostura
    ) -> None:
        """Una flecha por par declarado, en `--coral-alerta` y punteada."""
        astas = por_clase(marcado, "flecha")
        puntas = por_clase(marcado, "flecha-punta")
        self.assertEqual(
            len(astas),
            len(pose.flechas),
            msg=f"{d.id}: {len(astas)} astas para {len(pose.flechas)} flechas",
        )
        self.assertEqual(len(puntas), len(pose.flechas))
        for etiqueta_svg, atributos in astas + puntas:
            self.assertEqual(
                atributos.get("stroke"),
                sp.COLOR_FLECHA,
                msg=f"{d.id}: flecha fuera de --coral-alerta",
            )
            self.assertEqual(
                sp.TOKEN_POR_COLOR[atributos["stroke"]], "--coral-alerta"
            )
            self.assertTrue(
                atributos.get("stroke-dasharray", ""),
                msg=f"{d.id}: {etiqueta_svg} de flecha sin stroke-dasharray",
            )
        # La punta es una polilinea: nada de `marker` ni de `url(`, que el
        # criterio 14.15 prohibe.
        for etiqueta_svg, _atributos in puntas:
            self.assertEqual(etiqueta_svg, "polyline")
        self.assertNotIn("marker", marcado)
        self.assertNotIn("url(", marcado)

    def _revisar_eje(self, marcado: str, d: dp.DiagramaPostura) -> None:
        """Linea media vertical punteada con un unico centro de gravedad encima."""
        medias = por_clase(marcado, "linea-media")
        self.assertEqual(len(medias), 1, msg=f"{d.id}: lineas medias={len(medias)}")
        _etiqueta_svg, atributos = medias[0]
        self.assertEqual(
            atributos["x1"],
            atributos["x2"],
            msg=f"{d.id}: la linea media no es vertical",
        )
        self.assertTrue(
            atributos.get("stroke-dasharray", ""),
            msg=f"{d.id}: la linea media sin stroke-dasharray",
        )

        centros = por_clase(marcado, "centro-gravedad")
        self.assertEqual(
            len(centros), 1, msg=f"{d.id}: centros de gravedad={len(centros)}"
        )
        _etiqueta_centro, centro = centros[0]
        self.assertEqual(_etiqueta_centro, "circle")
        self.assertEqual(centro.get("fill"), sp.COLOR_CONTORNO)
        self.assertGreater(float(centro["r"]), 0.0)
        # Sobre la linea media: misma X y Y dentro del segmento.
        self.assertEqual(centro["cx"], atributos["x1"])
        arriba, abajo = sorted((float(atributos["y1"]), float(atributos["y2"])))
        self.assertGreaterEqual(float(centro["cy"]), arriba)
        self.assertLessEqual(float(centro["cy"]), abajo)


# --------------------------------------------------------------------------- #
# Property 10
# --------------------------------------------------------------------------- #

ETQ_P10 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 10: Coherencia y degradacion de las Fase_Numerada"
)

#: Indices del catalogo que declaran Fase_Numerada. Hoy solo `potencia-carrera`,
#: asi que el generador los sobremuestrea para que la propiedad no gaste sus cien
#: iteraciones en entradas sin fases.
INDICES_CON_FASES = tuple(i for i, d in enumerate(dp.CATALOGO) if d.fases)


def numeros_declarados(d: dp.DiagramaPostura) -> tuple[int, ...]:
    """Numeros de las Fase_Numerada que declara `d`, en orden declarado."""
    return tuple(f.numero for f in d.fases)


def svg_fases_declaradas(
    d: dp.DiagramaPostura, omitir: tuple[int, ...] = ()
) -> str:
    """`svg_fases` a las dimensiones del modo SVG declarado por `d`."""
    ancho_vb, alto_vb = viewbox_declarado(d)
    return sp.svg_fases(
        d,
        ancho_vb,
        alto_vb,
        factor=sp.factor_figura(len(d.etiquetas)),
        omitir=omitir,
    )


def gen_diagrama_y_fases_forzadas(rnd: random.Random) -> tuple[int, tuple[int, ...]]:
    """Una entrada del catalogo y el subconjunto de fases cuyo fallo se fuerza.

    El subconjunto vacio (nada falla) y el total (todo falla) entran en el
    espacio, que es lo que pide la clausula de degradacion.
    """
    if INDICES_CON_FASES and rnd.randrange(2) == 0:
        indice: int = rnd.choice(INDICES_CON_FASES)
    else:
        indice = rnd.randrange(len(dp.CATALOGO))
    numeros: tuple[int, ...] = numeros_declarados(dp.CATALOGO[indice])
    if not numeros:
        return (indice, ())
    forma: int = rnd.randrange(4)
    if forma == 0:
        return (indice, ())
    if forma == 1:
        return (indice, numeros)
    return (indice, tuple(n for n in numeros if rnd.randrange(2) == 0))


def caso_valido_p10(caso: object) -> bool:
    """True si `caso` sigue siendo `(indice de entrada, fases forzadas)`."""
    if not isinstance(caso, tuple) or len(caso) != 2:
        return False
    indice, forzadas = caso
    if not isinstance(indice, int) or isinstance(indice, bool):
        return False
    if not 0 <= indice < len(dp.CATALOGO):
        return False
    if not isinstance(forzadas, tuple):
        return False
    declarados = numeros_declarados(dp.CATALOGO[indice])
    if len(set(forzadas)) != len(forzadas):
        return False
    return all(
        isinstance(n, int) and not isinstance(n, bool) and n in declarados
        for n in forzadas
    )


class TestProperty10FasesNumeradas(unittest.TestCase):
    """Property 10: coherencia y degradacion de las Fase_Numerada."""

    def test_property_10_fases_numeradas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 10: Coherencia y degradacion de las Fase_Numerada.

        Para todo Diagrama_Postura que declara Fase_Numerada, el conjunto de
        numeros emitidos en el SVG es exactamente el conjunto de enteros de 1 al
        numero de fases declaradas; y para todo subconjunto de fases cuya emision
        se fuerza a fallar, el SVG emite los numeros de las fases restantes, no
        lanza excepcion y la lista de omisiones contiene el identificador del
        diagrama junto al numero de cada fase omitida.

        **Validates: Requirements 14.10, 14.11, 14.17**
        """

        def prop(caso: tuple[int, tuple[int, ...]]) -> None:
            if not caso_valido_p10(caso):
                return
            indice, forzadas = caso
            d = dp.CATALOGO[indice]
            declarados = numeros_declarados(d)

            # Clausula 1: sin nada forzado, el conjunto emitido es {1..n}.
            emitidas = sp.fases_emitidas(d)
            self.assertEqual(
                set(emitidas),
                set(range(1, len(d.fases) + 1)),
                msg=f"{d.id}: emitidas={emitidas!r} para {len(d.fases)} fases",
            )
            self.assertEqual(emitidas, declarados)
            self.assertEqual(sp.omisiones_de_fase(d), ())

            # La numeracion emitida es la de las Fase_Numerada declaradas, que es
            # la que la lista `<ol class="diagrama-fases">` replica con
            # `value="<numero>"` (criterio 14.11).
            for fase in d.fases:
                self.assertIn(fase.numero, emitidas)
                self.assertTrue(fase.texto.strip())

            # Clausula 2: con un subconjunto forzado a fallar, se emiten las
            # restantes, no se lanza y las omisiones quedan registradas.
            restantes = tuple(n for n in declarados if n not in forzadas)
            self.assertEqual(sp.fases_emitidas(d, omitir=forzadas), restantes)
            self.assertEqual(
                sp.omisiones_de_fase(d, omitir=forzadas),
                tuple((d.id, n) for n in declarados if n in forzadas),
            )
            self.assertEqual(
                len(sp.fases_emitidas(d, omitir=forzadas))
                + len(sp.omisiones_de_fase(d, omitir=forzadas)),
                len(declarados),
            )

            marcado = svg_fases_declaradas(d, forzadas)
            for numero in declarados:
                emitido = f'class="fase fase-{numero}"'
                if numero in restantes:
                    self.assertIn(emitido, marcado, msg=f"{d.id}: falta {numero}")
                else:
                    self.assertNotIn(emitido, marcado, msg=f"{d.id}: sobra {numero}")
            contenidos = tuple(
                contenido for _atributos, contenido in textos_emitidos(marcado)
            )
            self.assertEqual(contenidos, tuple(str(n) for n in restantes))
            if not restantes:
                self.assertEqual(marcado, "")

        for_all(gen_diagrama_y_fases_forzadas, prop, iteraciones=100, etiqueta=ETQ_P10)


# --------------------------------------------------------------------------- #
# Ensamblado de `svg_diagrama` (tarea 4.14)
# --------------------------------------------------------------------------- #


class TestSvgDiagramaEnsamblado(unittest.TestCase):
    """Atributos, orden de emision y prohibiciones del `<svg>` ensamblado."""

    def test_atributos_del_svg(self) -> None:
        """`viewBox` al doble, `width`/`height` del modo SVG, `role` y `aria-label`."""
        for d in dp.CATALOGO:
            with self.subTest(diagrama=d.id):
                marcado = sp.svg_diagrama(d)
                etiqueta_svg, atributos = elementos(marcado)[0]
                self.assertEqual(etiqueta_svg, "svg")
                self.assertEqual(
                    atributos["viewBox"],
                    f"0 0 {2 * d.ancho_svg} {2 * d.alto_svg}",
                )
                self.assertEqual(atributos["width"], str(d.ancho_svg))
                self.assertEqual(atributos["height"], str(d.alto_svg))
                self.assertEqual(atributos["role"], "img")
                self.assertEqual(atributos["aria-label"], d.alt)
                self.assertTrue(marcado.endswith("</svg>"))

    def test_orden_de_emision_y_bytes_reproducibles(self) -> None:
        """Figura, adornos, fases, etiquetas y zona, siempre en ese orden."""
        for d in dp.CATALOGO:
            with self.subTest(diagrama=d.id):
                marcado = sp.svg_diagrama(d)
                posiciones = [
                    marcado.index('<g class="figura">'),
                    marcado.index('<g class="eje-corporal">'),
                    marcado.index('<g class="etiquetas">'),
                ]
                self.assertEqual(posiciones, sorted(posiciones))
                if d.fases:
                    self.assertLess(
                        marcado.index('<g class="fases">'), posiciones[-1]
                    )
                    self.assertGreater(
                        marcado.index('<g class="fases">'), posiciones[1]
                    )
                else:
                    self.assertNotIn('<g class="fases">', marcado)
                if len(d.etiquetas) > sp.MAXIMO_ETIQUETAS_DENTRO:
                    self.assertGreater(
                        marcado.index('class="diagrama-ampliar"'), posiciones[-1]
                    )
                else:
                    self.assertNotIn("diagrama-ampliar", marcado)
                self.assertEqual(
                    marcado.encode("utf-8"), sp.svg_diagrama(d).encode("utf-8")
                )

    def test_marcado_sin_recursos_ni_eventos(self) -> None:
        """Cero `<image>`, `<img>`, `on*`, `url(`, `http` y `tabindex` (14.15)."""
        for d in dp.CATALOGO:
            with self.subTest(diagrama=d.id):
                marcado = sp.svg_diagrama(d)
                for prohibido in sp.PROHIBIDOS_MARCADO:
                    self.assertNotIn(prohibido, marcado)
                self.assertIsNone(re.search(r"\son[a-z]+\s*=", marcado))
                # El guardarrail de produccion tambien lo comprueba y no lanza.
                sp.validar_marcado(d.id, marcado)

    def test_validar_marcado_rechaza_lo_prohibido(self) -> None:
        """`validar_marcado` lanza `ErrorAsset` nombrando lo que encontro."""
        from guia.errores import E_ASSET_INVALIDO, ErrorAsset

        casos = (
            '<svg><image href="x.png" /></svg>',
            '<svg><rect fill="url(#g)" /></svg>',
            '<svg><a tabindex="0"></a></svg>',
            '<svg><circle onclick="ir()" /></svg>',
        )
        for marcado in casos:
            with self.subTest(marcado=marcado):
                with self.assertRaises(ErrorAsset) as capturado:
                    sp.validar_marcado("prueba", marcado)
                self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)
                self.assertIn("prueba", str(capturado.exception))

    def test_todo_texto_rinde_doce_pixeles_a_360(self) -> None:
        """Todo `<text>` emitido cumple el tamano efectivo minimo (15.17)."""
        for d in dp.CATALOGO:
            with self.subTest(diagrama=d.id):
                ancho_vb = d.ancho_svg * sp.FACTOR_VIEWBOX
                marcado = sp.svg_diagrama(d)
                textos = textos_emitidos(marcado)
                self.assertGreater(len(textos), 0)
                for atributos, _contenido in textos:
                    efectivo = sp.tamano_efectivo_px(
                        float(atributos["font-size"]), ancho_vb
                    )
                    self.assertGreaterEqual(efectivo, sp.TAMANO_EFECTIVO_MINIMO)


if __name__ == "__main__":
    unittest.main()
