"""Pruebas del Mundo_Hero (`mundo_hero.py`).

Feature `imagenes-reales-hero-interactivo`, bloque 8:

* **Property 25** (tarea 8.2): forma del catalogo de Elemento_Fondo.
* **Property 22** (tarea 8.4): curvas de parallax, escala y opacidad.
* **Property 23** (tarea 8.5): reversibilidad del desvanecimiento y de la escala.
* **Property 24** (tarea 8.6): orden de las velocidades y de la profundidad.
* **Property 26** (tarea 8.8): interpolacion del desplazamiento por cursor.
* **Property 27** (tarea 8.10): resolucion del balon mas cercano al toque.
* **Property 49** (tarea 8.12): giro de la Figura_Girable y Sombra_Contacto.
* **Property 50** (tarea 8.14): Balon_Esfera con gajos y eje inclinado.
* **Property 28** (tarea 8.16): round trip de las constantes a JSON.
* **Property 11** (tarea 8.18): marcado SVG seguro.
* **Property 51** (tarea 8.19): Modo_Inerte, **completa**. Las dos clausulas
  imperativas --que el Script_Unico alterne la clase con la lista de clases del
  contenedor y que omita las escrituras mientras esta activa-- se cerraron con la
  tarea **12.6** y se afirman sobre el cuerpo del `<script>` emitido; el cableado
  del CSS al artefacto llego con la tarea **10.6**.

_Requirements: 1.9, 6.8, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2, 8.3,
8.4, 8.5, 8.6, 8.7, 8.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8, 10.10, 10.16, 11.3,
12.1, 12.4, 12.6, 14.15, 22.1, 25.1, 25.2, 25.3, 25.4, 25.5, 25.10, 25.14,
25.15, 25.16, 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.8, 26.9, 26.10,
26.11, 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7, 27.8, 27.9_
"""

from __future__ import annotations

import json
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
from guia import build_site  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia import mundo_hero as mh  # noqa: E402
from guia import svg_postura as sp  # noqa: E402
from guia import vistas_figura as vf  # noqa: E402
from prop import for_all  # noqa: E402


# --------------------------------------------------------------------------- #
# Property 25: forma del catalogo de Elemento_Fondo
# --------------------------------------------------------------------------- #

ETQ_P25 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 25: Forma del catálogo de Elemento_Fondo"
)


def gen_indice_elemento(rnd) -> int:
    """Indice de un Elemento_Fondo del catalogo, con los bordes forzados.

    Los bordes importan: el primero y el ultimo del catalogo son los que mas
    facil se quedan fuera de un recorrido mal escrito, y el orden del catalogo es
    justo lo que rompe los empates de `balon_mas_cercano`.
    """
    forma: int = rnd.randrange(4)
    if forma == 0:
        return 0
    if forma == 1:
        return len(mh.ELEMENTOS) - 1
    return rnd.randrange(len(mh.ELEMENTOS))


class TestProperty25CatalogoElementoFondo(unittest.TestCase):
    """Property 25: forma del catalogo de Elemento_Fondo."""

    def test_property_25_forma_del_catalogo_de_elemento_fondo(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 25: Forma del catálogo de Elemento_Fondo.

        Para todo catalogo de Elemento_Fondo del Mundo_Hero, el numero total de
        elementos esta entre 8 y 14, el de balones entre 3 y 5, el de siluetas
        entre 2 y 3 con opacidad en [0.25, 0.45]; existe al menos un elemento de
        cada uno de los tipos porteria, cono, linea de campo, silbato, copa y
        taco; existe al menos un elemento con centro en cada cuadrante; todo
        balon gira 360 grados con una duracion en [14, 26] segundos, esas
        duraciones son distintas entre si y aparecen los dos sentidos de giro;
        toda capa declarada pertenece al conjunto de tres y cada elemento
        pertenece a exactamente una; todo vaiven esta en [8, 20] pixeles y [5, 9]
        segundos, se repite de forma indefinida y los retrasos de elementos
        consecutivos del mismo tipo son distintos.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.1, 9.1, 9.2, 9.3**
        """
        # El catalogo es declarativo: su validador recorre todos los invariantes
        # de golpe y no depende de ninguna entrada, asi que se comprueba una vez.
        mh.validar_elementos()

        self.assertGreaterEqual(len(mh.ELEMENTOS), 8)
        self.assertLessEqual(len(mh.ELEMENTOS), 14)
        self.assertEqual(len(mh.ELEMENTOS), 14)
        self.assertEqual(len(mh.por_tipo(mh.TIPO_SILUETA)), 3)

        cuantos_balones = len(mh.balones())
        self.assertGreaterEqual(cuantos_balones, 3)
        self.assertLessEqual(cuantos_balones, 5)

        for tipo in mh.TIPOS_EXIGIDOS:
            with self.subTest(tipo=tipo):
                self.assertTrue(mh.por_tipo(tipo))

        cubiertos = {mh.cuadrante_de(e) for e in mh.ELEMENTOS}
        self.assertEqual(cubiertos, set(mh.CUADRANTES))

        duraciones = tuple(b.giro_s for b in mh.balones())
        self.assertEqual(len(set(duraciones)), len(duraciones))
        sentidos = {b.sentido for b in mh.balones()}
        self.assertIn(1, sentidos)
        self.assertIn(-1, sentidos)

        # Los angostos caen dentro de la ventana declarada del criterio 12.1.
        minimo, maximo = mh.ELEMENTOS_ANGOSTO
        self.assertGreaterEqual(len(mh.activos_angostos()), minimo)
        self.assertLessEqual(len(mh.activos_angostos()), maximo)

        def prop(indice: int) -> None:
            elemento = mh.ELEMENTOS[indice]

            # Cada elemento pertenece a exactamente una de las tres capas.
            self.assertIn(elemento.capa, mh.CAPAS)
            cuantas = sum(
                1 for capa in mh.CAPAS if elemento in mh.por_capa(capa)
            )
            self.assertEqual(cuantas, 1)

            # Vaiven en rango, indefinido (no hay conteo de repeticiones) y con
            # retraso propio no negativo.
            self.assertGreaterEqual(elemento.vaiven_px, 8.0)
            self.assertLessEqual(elemento.vaiven_px, 20.0)
            self.assertGreaterEqual(elemento.vaiven_s, 5.0)
            self.assertLessEqual(elemento.vaiven_s, 9.0)
            self.assertGreaterEqual(elemento.retraso_s, 0.0)

            # El retraso es distinto del de su vecino del mismo tipo.
            del_tipo = mh.por_tipo(elemento.tipo)
            posicion = del_tipo.index(elemento)
            if posicion + 1 < len(del_tipo):
                self.assertNotEqual(
                    elemento.retraso_s, del_tipo[posicion + 1].retraso_s
                )

            # Silueta: opacidad en el rango declarado.
            if elemento.tipo == mh.TIPO_SILUETA:
                self.assertGreaterEqual(elemento.opacidad, 0.25)
                self.assertLessEqual(elemento.opacidad, 0.45)

            # Balon: vuelta completa con duracion en rango y sentido declarado.
            if elemento.tipo == mh.TIPO_BALON:
                self.assertGreaterEqual(elemento.giro_s, 14.0)
                self.assertLessEqual(elemento.giro_s, 26.0)
                self.assertIn(elemento.sentido, (1, -1))
            else:
                self.assertEqual(elemento.giro_s, 0.0)
                self.assertEqual(elemento.sentido, 0)

            # El centro cae dentro del hero y su cuadrante es uno de los cuatro.
            self.assertGreaterEqual(elemento.x_pct, 0.0)
            self.assertLessEqual(elemento.x_pct, 100.0)
            self.assertGreaterEqual(elemento.y_pct, 0.0)
            self.assertLessEqual(elemento.y_pct, 100.0)
            self.assertIn(mh.cuadrante_de(elemento), mh.CUADRANTES)

        for_all(gen_indice_elemento, prop, iteraciones=100, etiqueta=ETQ_P25)


# --------------------------------------------------------------------------- #
# Property 22: curvas de parallax, escala y opacidad
# --------------------------------------------------------------------------- #

ETQ_P22 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 22: Curvas de parallax, escala y opacidad"
)

#: Tolerancia de las comparaciones de punto flotante de las curvas.
TOLERANCIA = 1e-9


def gen_scroll_y_alto(rnd) -> tuple[float, float]:
    """Par `(scroll_y, alto_ventana)` con los casos limite forzados.

    Incluye el alto 0 y negativo (ventana sin medir, donde el progreso es 0), el
    desplazamiento negativo del rebote elastico de iOS, el desplazamiento exacto
    de una ventana completa y desplazamientos muy por encima del alto, que es
    donde se comprueba el acotado del criterio 8.5.
    """
    forma: int = rnd.randrange(6)
    if forma == 0:
        return (rnd.uniform(-500.0, 5000.0), 0.0)
    if forma == 1:
        return (rnd.uniform(0.0, 5000.0), rnd.uniform(-1000.0, -1.0))
    alto: float = rnd.uniform(320.0, 1400.0)
    if forma == 2:
        return (0.0, alto)
    if forma == 3:
        return (alto, alto)
    if forma == 4:
        return (rnd.uniform(-800.0, 0.0), alto)
    return (rnd.uniform(0.0, 4.0) * alto, alto)


class TestProperty22Curvas(unittest.TestCase):
    """Property 22: curvas de parallax, escala y opacidad."""

    def test_property_22_curvas_de_parallax_escala_y_opacidad(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 22: Curvas de parallax, escala y opacidad.

        Para todo valor real de desplazamiento vertical y de alto de ventana, el
        progreso resultante cae en el intervalo [0, 1]; y para todo progreso, la
        escala de cada capa es `1 + (escala_final - 1) * p` (es decir `1 + 0.25p`
        en la Capa_Cercana y `1 - 0.15p` en la Capa_Lejana) y la opacidad es
        `1 - p`, valiendo exactamente 0 cuando el progreso es 1 o mayor y
        exactamente 1 cuando es 0 o menor.

        **Validates: Requirements 8.3, 8.4, 8.5**
        """

        def prop_progreso(caso: tuple[float, float]) -> None:
            scroll_y, alto = caso
            p = mh.progreso(scroll_y, alto)
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)
            if alto <= 0.0:
                self.assertEqual(p, 0.0)

        for_all(gen_scroll_y_alto, prop_progreso, iteraciones=100, etiqueta=ETQ_P22)

        def prop_curvas(p: float) -> None:
            # Escala: interpolacion lineal exacta hacia la escala final.
            for capa in mh.CAPAS:
                esperada = 1.0 + (mh.ESCALA_FINAL[capa] - 1.0) * p
                self.assertAlmostEqual(mh.escala(capa, p), esperada, delta=TOLERANCIA)
            self.assertAlmostEqual(
                mh.escala(mh.CAPA_CERCANA, p), 1.0 + 0.25 * p, delta=TOLERANCIA
            )
            self.assertAlmostEqual(
                mh.escala(mh.CAPA_LEJANA, p), 1.0 - 0.15 * p, delta=TOLERANCIA
            )

            # Opacidad: 1 - p acotado, con los dos bordes exactos.
            valor = mh.opacidad(p)
            self.assertGreaterEqual(valor, 0.0)
            self.assertLessEqual(valor, 1.0)
            if p >= 1.0:
                self.assertEqual(valor, 0.0)
            elif p <= 0.0:
                self.assertEqual(valor, 1.0)
            else:
                self.assertAlmostEqual(valor, 1.0 - p, delta=TOLERANCIA)

        for_all(gen.gen_progreso, prop_curvas, iteraciones=100, etiqueta=ETQ_P22)


# --------------------------------------------------------------------------- #
# Property 23: reversibilidad del desvanecimiento y de la escala
# --------------------------------------------------------------------------- #

ETQ_P23 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 23: Reversibilidad del desvanecimiento y de la escala"
)


class TestProperty23Reversibilidad(unittest.TestCase):
    """Property 23: reversibilidad del desvanecimiento y de la escala."""

    def test_property_23_reversibilidad(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 23: Reversibilidad del desvanecimiento y de la escala.

        Para toda secuencia de progresos de scroll, recorrerla en orden creciente
        y luego en orden decreciente produce, para cada progreso, exactamente el
        mismo valor de opacidad y de escala en las tres capas.

        **Validates: Requirements 8.6**
        """

        def prop(secuencia: tuple[float, ...]) -> None:
            if not secuencia:
                return
            creciente = tuple(sorted(secuencia))
            decreciente = tuple(reversed(creciente))

            # Recorrido de ida: se anota el valor de cada progreso.
            ida: dict[float, tuple[float, ...]] = {}
            for p in creciente:
                ida[p] = (mh.opacidad(p),) + tuple(
                    mh.escala(capa, p) for capa in mh.CAPAS
                )

            # Recorrido de vuelta: mismo progreso, mismo valor, bit a bit. Sale
            # gratis porque las curvas son funciones puras y sin estado.
            for p in decreciente:
                vuelta = (mh.opacidad(p),) + tuple(
                    mh.escala(capa, p) for capa in mh.CAPAS
                )
                self.assertEqual(vuelta, ida[p])

        for_all(
            gen.gen_secuencia_progresos, prop, iteraciones=100, etiqueta=ETQ_P23
        )


# --------------------------------------------------------------------------- #
# Property 24: orden de las velocidades y de la profundidad
# --------------------------------------------------------------------------- #

ETQ_P24 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 24: Orden de las velocidades y de la profundidad"
)


def gen_scroll_positivo(rnd) -> float:
    """Desplazamiento vertical estrictamente mayor que 0, con el borde forzado."""
    forma: int = rnd.randrange(3)
    if forma == 0:
        return 1e-6
    if forma == 1:
        return rnd.uniform(0.0001, 1.0)
    return rnd.uniform(1.0, 12000.0)


class TestProperty24OrdenDeVelocidades(unittest.TestCase):
    """Property 24: orden de las velocidades y de la profundidad."""

    def test_property_24_orden_de_velocidades_y_profundidad(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 24: Orden de las velocidades y de la profundidad.

        Para todo desplazamiento vertical mayor que 0, el desplazamiento aplicado
        a la Capa_Cercana es mayor en valor absoluto que el de la Capa_Media y el
        de la Capa_Media mayor que el de la Capa_Lejana, con los factores 0.70,
        0.40 y 0.15; y el valor de `translateZ` declarado para cada capa es
        propio y estrictamente creciente de la Capa_Lejana a la Capa_Cercana, con
        el mas negativo en la lejana.

        **Validates: Requirements 8.2, 8.7, 8.8**
        """
        # Factores declarados, exactos.
        self.assertEqual(mh.FACTOR_PARALLAX[mh.CAPA_LEJANA], 0.15)
        self.assertEqual(mh.FACTOR_PARALLAX[mh.CAPA_MEDIA], 0.40)
        self.assertEqual(mh.FACTOR_PARALLAX[mh.CAPA_CERCANA], 0.70)

        # translateZ propio de cada capa y estrictamente creciente.
        zetas = tuple(mh.profundidad(capa) for capa in mh.CAPAS)
        self.assertEqual(len(set(zetas)), len(zetas))
        for anterior, siguiente in zip(zetas, zetas[1:]):
            self.assertLess(anterior, siguiente)
        self.assertEqual(min(zetas), mh.profundidad(mh.CAPA_LEJANA))
        self.assertEqual(max(zetas), mh.profundidad(mh.CAPA_CERCANA))
        for z in zetas:
            self.assertLess(z, 0.0)

        def prop(scroll_y: float) -> None:
            lejana = abs(mh.desplazamiento(mh.CAPA_LEJANA, scroll_y))
            media = abs(mh.desplazamiento(mh.CAPA_MEDIA, scroll_y))
            cercana = abs(mh.desplazamiento(mh.CAPA_CERCANA, scroll_y))
            self.assertGreater(cercana, media)
            self.assertGreater(media, lejana)
            for capa in mh.CAPAS:
                self.assertAlmostEqual(
                    mh.desplazamiento(capa, scroll_y),
                    -scroll_y * mh.FACTOR_PARALLAX[capa],
                    delta=TOLERANCIA,
                )

        for_all(gen_scroll_positivo, prop, iteraciones=100, etiqueta=ETQ_P24)


# --------------------------------------------------------------------------- #
# Property 26: interpolacion del desplazamiento por cursor
# --------------------------------------------------------------------------- #

ETQ_P26 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 26: Interpolación del desplazamiento por cursor"
)

#: Fotogramas que se simulan de la interpolacion en cada iteracion.
FOTOGRAMAS = 60

#: Por debajo de esta distancia la resta de flotantes deja de tener resolucion
#: para seguir acercandose: el paso `(objetivo - actual) * 0.08` cae por debajo
#: del ULP del valor y la sucesion se queda quieta, que es lo correcto. La
#: monotonia **estricta** solo se exige por encima de este umbral.
RESOLUCION = 1e-9


def gen_caso_cursor(rnd) -> tuple[float, float, float, float]:
    """Posicion relativa del cursor y estado inicial del desplazamiento.

    El estado inicial incluye el cero (arranque en reposo), el objetivo exacto (la
    sucesion ya llego) y valores saturados en los dos topes, que es donde la
    interpolacion podria sobrepasar el objetivo si el coeficiente estuviera mal.
    """
    rel_x, rel_y = gen.gen_cursor_relativo(rnd)
    tope = mh.TOPE_CURSOR_PX

    def inicial() -> float:
        forma: int = rnd.randrange(4)
        if forma == 0:
            return 0.0
        if forma == 1:
            return rnd.choice((-tope, tope))
        if forma == 2:
            return rnd.uniform(-tope, tope)
        return rnd.uniform(-3.0 * tope, 3.0 * tope)

    return (rel_x, rel_y, inicial(), inicial())


class TestProperty26Cursor(unittest.TestCase):
    """Property 26: interpolacion del desplazamiento por cursor."""

    def test_property_26_interpolacion_del_cursor(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 26: Interpolación del desplazamiento por cursor.

        Para toda posicion relativa del cursor dentro del hero, el desplazamiento
        objetivo tiene signo opuesto al de la posicion del cursor en cada eje y su
        modulo no supera 20 pixeles; y para todo estado inicial, iterar la
        interpolacion con coeficiente 0.08 hacia ese objetivo produce una sucesion
        cuya distancia al objetivo decrece de forma estricta y que nunca lo
        sobrepasa, incluido el objetivo cero al que se vuelve cuando el cursor
        sale del hero.

        **Validates: Requirements 9.4, 9.5, 9.6**
        """
        self.assertEqual(mh.TOPE_CURSOR_PX, 20.0)
        self.assertEqual(mh.SUAVIZADO_CURSOR, 0.08)

        def paso_no_sobrepasa(actual: float, objetivo: float) -> float:
            """Un paso que ni sobrepasa el objetivo ni se aleja de el."""
            siguiente = mh.suavizar(actual, objetivo)
            distancia_antes = abs(objetivo - actual)
            distancia_despues = abs(objetivo - siguiente)

            # Nunca sobrepasa: el signo de la diferencia no cambia.
            if objetivo > actual:
                self.assertLessEqual(siguiente, objetivo)
                self.assertGreaterEqual(siguiente, actual)
            elif objetivo < actual:
                self.assertGreaterEqual(siguiente, objetivo)
                self.assertLessEqual(siguiente, actual)
            else:
                self.assertEqual(siguiente, objetivo)

            # La distancia nunca crece, y decrece de forma estricta mientras el
            # paso tenga resolucion en punto flotante.
            self.assertLessEqual(distancia_despues, distancia_antes)
            if distancia_antes > RESOLUCION:
                self.assertLess(distancia_despues, distancia_antes)
            return siguiente

        def prop(caso: tuple[float, float, float, float]) -> None:
            rel_x, rel_y, inicial_x, inicial_y = caso
            objetivo_x, objetivo_y = mh.cursor_objetivo(rel_x, rel_y)

            # Modulo acotado a 20 px por eje y signo opuesto al del cursor.
            for relativa, objetivo in (
                (rel_x, objetivo_x),
                (rel_y, objetivo_y),
            ):
                self.assertLessEqual(abs(objetivo), mh.TOPE_CURSOR_PX)
                if relativa > 0.0:
                    self.assertLess(objetivo, 0.0)
                elif relativa < 0.0:
                    self.assertGreater(objetivo, 0.0)
                else:
                    self.assertEqual(objetivo, 0.0)

            # Persecucion del objetivo declarado y vuelta al cero de la salida
            # del hero: la misma interpolacion sirve para los dos.
            for objetivo in (objetivo_x, 0.0):
                actual = inicial_x
                for _ in range(FOTOGRAMAS):
                    actual = paso_no_sobrepasa(actual, objetivo)
            for objetivo in (objetivo_y, 0.0):
                actual = inicial_y
                for _ in range(FOTOGRAMAS):
                    actual = paso_no_sobrepasa(actual, objetivo)

        for_all(gen_caso_cursor, prop, iteraciones=100, etiqueta=ETQ_P26)


# --------------------------------------------------------------------------- #
# Property 27: resolucion del balon mas cercano al toque
# --------------------------------------------------------------------------- #

ETQ_P27 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 27: Resolución del balón más cercano al toque"
)


def gen_toque(rnd) -> tuple[float, float]:
    """Punto de toque, con los centros de balon y los empates forzados.

    Ademas de los puntos del generador comun, incluye el centro exacto de cada
    balon (distancia 0), puntos justo dentro y justo fuera del radio declarado y
    el **punto equidistante** de dos balones, que es el unico sitio donde el
    desempate por orden del catalogo se puede observar.
    """
    lista = mh.balones()
    forma: int = rnd.randrange(5)
    if forma == 0:
        elegido = rnd.choice(lista)
        return (elegido.x_pct, elegido.y_pct)
    if forma == 1:
        elegido = rnd.choice(lista)
        radio = mh.RADIO_TOQUE_PCT * rnd.choice((0.999, 1.001))
        return (elegido.x_pct + radio, elegido.y_pct)
    if forma == 2 and len(lista) >= 2:
        uno, otro = rnd.sample(list(lista), 2)
        return ((uno.x_pct + otro.x_pct) / 2.0, (uno.y_pct + otro.y_pct) / 2.0)
    return gen.gen_punto_toque(rnd)


class TestProperty27BalonMasCercano(unittest.TestCase):
    """Property 27: resolucion del balon mas cercano al toque."""

    def test_property_27_balon_mas_cercano(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 27: Resolución del balón más cercano al toque.

        Para todo punto de toque expresado en coordenadas porcentuales del hero,
        la resolucion devuelve el identificador del Elemento_Fondo de tipo balon
        que minimiza la distancia a ese punto entre los que estan dentro del radio
        declarado, devuelve nulo cuando ningun balon esta dentro del radio, nunca
        devuelve un elemento que no sea de tipo balon, rompe los empates por el
        orden del catalogo, y usa unicamente las coordenadas declaradas del
        catalogo.

        **Validates: Requirements 9.8**
        """
        lista = mh.balones()
        ids_balon = tuple(b.id for b in lista)
        ids_no_balon = tuple(
            e.id for e in mh.ELEMENTOS if e.tipo != mh.TIPO_BALON
        )

        def prop(punto: tuple[float, float]) -> None:
            x_pct, y_pct = punto
            resultado = mh.balon_mas_cercano(x_pct, y_pct)

            # Distancias medidas con las coordenadas DECLARADAS del catalogo.
            distancias = tuple(
                math.hypot(x_pct - b.x_pct, y_pct - b.y_pct) for b in lista
            )
            dentro = tuple(
                indice
                for indice, d in enumerate(distancias)
                if d <= mh.RADIO_TOQUE_PCT
            )

            if not dentro:
                self.assertIsNone(resultado)
                return

            self.assertIsNotNone(resultado)
            self.assertIn(resultado, ids_balon)
            self.assertNotIn(resultado, ids_no_balon)

            # Minimiza la distancia, y el empate lo gana el primero del catalogo.
            minima = min(distancias[i] for i in dentro)
            esperado = ids_balon[
                next(i for i in dentro if distancias[i] == minima)
            ]
            self.assertEqual(resultado, esperado)
            self.assertLessEqual(
                distancias[ids_balon.index(resultado)], mh.RADIO_TOQUE_PCT
            )

            # Pura: dos llamadas con el mismo punto dan el mismo resultado.
            self.assertEqual(resultado, mh.balon_mas_cercano(x_pct, y_pct))

        for_all(gen_toque, prop, iteraciones=100, etiqueta=ETQ_P27)


# --------------------------------------------------------------------------- #
# Property 49: giro de la Figura_Girable y Sombra_Contacto
# --------------------------------------------------------------------------- #

ETQ_P49 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 49: Giro de la Figura_Girable y Sombra_Contacto"
)

#: `<ellipse class="sombra-contacto" ...>` de una Vista_Figura.
_RE_SOMBRA = re.compile(r'<ellipse class="sombra-contacto"[^>]*>')

#: Un atributo `nombre="valor"` de un elemento SVG.
_RE_ATRIBUTO = re.compile(r'([a-z-]+)="([^"]*)"')


def atributos_de(elemento: str) -> dict[str, str]:
    """Atributos de un elemento SVG suelto, como mapa nombre -> valor."""
    return dict(_RE_ATRIBUTO.findall(elemento))


def gen_figura_azimut(rnd) -> tuple[int, float]:
    """Par `(indice de Figura_Girable, azimut real)` con los bordes forzados.

    El azimut recorre los ocho declarados (donde `|cos|` vale 1 o `sqrt(2)/2`),
    los cuatro multiplos de 90 (donde vale exactamente 1 o exactamente 0, que son
    los dos extremos de la escala), angulos negativos, angulos por encima de una
    vuelta y continuos cualesquiera.
    """
    indice: int = rnd.randrange(len(mh.FIGURAS_GIRABLES))
    forma: int = rnd.randrange(5)
    if forma == 0:
        return (indice, float(rnd.choice(vf.AZIMUTS_DECLARADOS)))
    if forma == 1:
        return (indice, float(rnd.choice((0, 90, 180, 270))))
    if forma == 2:
        return (indice, rnd.uniform(-1080.0, 0.0))
    if forma == 3:
        return (indice, rnd.uniform(360.0, 4000.0))
    return (indice, rnd.uniform(0.0, 360.0))


class TestProperty49FiguraGirable(unittest.TestCase):
    """Property 49: giro de la Figura_Girable y Sombra_Contacto."""

    @classmethod
    def setUpClass(cls) -> None:
        # El marcado de las cuatro figuras se emite una vez: son 40 Vista_Figura
        # y reemitirlas en cada iteracion no anadiria ninguna cobertura.
        cls.marcado = {
            figura.id: mh.marcado_girable(figura)
            for figura in mh.FIGURAS_GIRABLES
        }
        cls.css = mh.css_figura_girable()

    def test_property_49_giro_de_la_figura_girable_y_sombra_contacto(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 49: Giro de la Figura_Girable y Sombra_Contacto.

        Para todo catalogo de Figura_Girable, cada figura declara una duracion de
        vuelta completa en el intervalo cerrado de 18 a 30 segundos, las
        duraciones son distintas entre figuras distintas, aparece al menos un
        sentido horario y al menos uno antihorario, cada animacion de giro se
        repite de forma indefinida, y cada figura declara un valor de `translateZ`
        propio distinto del de las otras figuras de su misma capa; y para todo
        azimut real, la escala horizontal de la Sombra_Contacto es
        `0.40 + 0.60 * |cos(azimut)|` con escala vertical 1, la sombra se emite
        como elemento `<ellipse>` dentro del SVG de su figura, y ninguna regla de
        la Sombra_Contacto declara `box-shadow`.

        **Validates: Requirements 25.1, 25.2, 25.3, 25.4, 25.5, 25.14, 25.15, 25.16**
        """
        # El catalogo es declarativo: su validador lo recorre entero de golpe.
        mh.validar_elementos()

        # Cuatro Figura_Girable por diez Vista_Figura: exactamente el techo.
        self.assertEqual(len(mh.FIGURAS_GIRABLES), 4)
        vf.validar_total_de_vistas(len(mh.FIGURAS_GIRABLES))
        self.assertEqual(
            len(mh.FIGURAS_GIRABLES) * len(vf.CLAVES_VISTA), vf.VISTAS_MAX
        )

        duraciones = tuple(f.vuelta_s for f in mh.FIGURAS_GIRABLES)
        self.assertEqual(len(set(duraciones)), len(duraciones))
        sentidos = {f.sentido for f in mh.FIGURAS_GIRABLES}
        self.assertIn(1, sentidos)
        self.assertIn(-1, sentidos)

        # `perspective` y `preserve-3d` del contenedor (criterio 25.1), y la
        # Vista_Activa distinguida SOLO por la clase (criterio 22.10).
        self.assertIn(f"perspective:{mh.PERSPECTIVA_PX}px", self.css)
        self.assertIn("transform-style:preserve-3d", self.css)
        self.assertIn("opacity:0;visibility:hidden", self.css)
        self.assertIn("opacity:1;visibility:visible", self.css)
        self.assertNotIn("display:", self.css)

        # Ninguna regla de la Sombra_Contacto declara `box-shadow`, ni geometria
        # animada (criterios 25.15, 29.7 y 29.8).
        self.assertIn(f".{mh.CLASE_SOMBRA}{{", self.css)
        for prohibida in ("box-shadow", "top:", "left:", "width:", "height:",
                          "margin", "will-change"):
            with self.subTest(prohibida=prohibida):
                regla = self.css[self.css.index(f".{mh.CLASE_SOMBRA}{{") :]
                self.assertNotIn(prohibida, regla)

        def prop(caso: tuple[int, float]) -> None:
            indice, azimut = caso
            figura = mh.FIGURAS_GIRABLES[indice]

            # Duracion, sentido, animacion infinita y translateZ propio.
            self.assertGreaterEqual(figura.vuelta_s, 18.0)
            self.assertLessEqual(figura.vuelta_s, 30.0)
            self.assertIn(figura.sentido, (1, -1))
            self.assertTrue(figura.infinita)
            hermanas = tuple(
                otra
                for otra in mh.figuras_de_capa(figura.capa)
                if otra.id != figura.id
            )
            for otra in hermanas:
                self.assertNotEqual(figura.z_figura_px, otra.z_figura_px)
                self.assertNotEqual(figura.vuelta_s, otra.vuelta_s)

            # Escala horizontal de la Sombra_Contacto: la formula, para todo
            # azimut real, con la vertical fija en 1.
            esperada = 0.40 + 0.60 * abs(math.cos(math.radians(azimut)))
            self.assertAlmostEqual(
                vf.escala_sombra(azimut), esperada, delta=TOLERANCIA
            )
            self.assertGreaterEqual(vf.escala_sombra(azimut), 0.40)
            self.assertLessEqual(vf.escala_sombra(azimut), 1.00)

            # La sombra es un `<ellipse>` dentro del SVG de cada Vista_Figura, y
            # su semieje vertical no depende del azimut: la escala vertical es 1.
            marcado = self.marcado[figura.id]
            trozos = vf.trocear_vistas(marcado)
            self.assertEqual(len(trozos), len(vf.CLAVES_VISTA))
            verticales: set[str] = set()
            for clave, trozo in zip(vf.CLAVES_VISTA, trozos):
                hallados = _RE_SOMBRA.findall(trozo)
                self.assertEqual(len(hallados), 1)
                atributos = atributos_de(hallados[0])
                verticales.add(atributos["ry"])
                factor = vf.escala_sombra(vf.azimut_de(clave))
                base = float(atributos["ry"]) / vf.RADIO_SOMBRA_Y_CANONICO
                self.assertAlmostEqual(
                    float(atributos["rx"]),
                    vf.RADIO_SOMBRA_X_CANONICO * base * factor,
                    delta=1e-3,
                )
                self.assertNotIn("box-shadow", trozo)
            self.assertEqual(len(verticales), 1)

        for_all(gen_figura_azimut, prop, iteraciones=100, etiqueta=ETQ_P49)


# --------------------------------------------------------------------------- #
# Property 50: Balon_Esfera con gajos y eje inclinado
# --------------------------------------------------------------------------- #

ETQ_P50 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 50: Balon_Esfera con gajos y eje inclinado"
)

#: `<g class="gajo-balon ...">` de un Gajo_Balon, con su `style` en linea.
_RE_GAJO = re.compile(r'<g class="(gajo-balon[^"]*)" style="([^"]*)">')

#: Atributo de evento en linea: un espacio, `on`, letras y el igual.
_RE_EVENTO = re.compile(r"\son[a-z]+\s*=")


def cuerpos_de_keyframes(css: str) -> tuple[str, ...]:
    """Cuerpo de cada `@keyframes` del CSS, hasta su llave de cierre.

    Recorta contando llaves, porque un `@keyframes` anida los bloques `from` y
    `to`. Es lo que permite exigir las prohibiciones del criterio 10.2 sobre las
    reglas **animadas** sin confundirlas con el `max-width` de una consulta de
    medios.
    """
    cuerpos: list[str] = []
    for coincidencia in re.finditer(r"@keyframes\s+[\w-]+\{", css):
        profundidad: int = 1
        indice: int = coincidencia.end()
        while indice < len(css) and profundidad > 0:
            if css[indice] == "{":
                profundidad += 1
            elif css[indice] == "}":
                profundidad -= 1
            indice += 1
        cuerpos.append(css[coincidencia.start() : indice])
    return tuple(cuerpos)


def gen_indice_balon(rnd) -> int:
    """Indice de un Elemento_Fondo de tipo balon, con los bordes forzados."""
    lista = mh.balones()
    forma: int = rnd.randrange(3)
    if forma == 0:
        return 0
    if forma == 1:
        return len(lista) - 1
    return rnd.randrange(len(lista))


class TestProperty50BalonEsfera(unittest.TestCase):
    """Property 50: Balon_Esfera con gajos y eje inclinado."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.marcado = {
            balon.id: mh.svg_balon_esfera(balon) for balon in mh.balones()
        }
        cls.css = mh.css_balon_esfera()

    def test_property_50_balon_esfera_con_gajos_y_eje_inclinado(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 50: Balon_Esfera con gajos y eje inclinado.

        Para todo Elemento_Fondo de tipo balon, el Balon_Esfera emite exactamente
        ocho Gajo_Balon y cada uno declara su propia rotacion con la funcion
        `rotate3d(`, distinta de la de los otros siete; su Eje_Giro_Inclinado
        tiene las tres componentes distintas de cero y una inclinacion respecto de
        la vertical en el intervalo cerrado de 15 a 45 grados; emite los grupos
        `polo-superior` y `polo-inferior`; su duracion de vuelta cae en el
        intervalo cerrado de 14 a 26 segundos, las duraciones son distintas entre
        balones, y la de todo balon de la Capa_Cercana es menor que la de todo
        balon de la Capa_Lejana; aparece al menos un sentido horario y al menos
        uno antihorario; bajo 768 pixeles de ancho la animacion usa la funcion
        `rotate(` de dos dimensiones y existe un Gajo_Balon sombreado desplazado
        del centro; y el marcado no contiene ningun elemento `<image>`, ninguna
        funcion `url(`, ninguna cadena `http` ni ningun atributo de evento en
        linea.

        **Validates: Requirements 7.6, 12.6, 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.8, 26.9, 26.10, 26.11**
        """
        mh.validar_elementos()

        lista = mh.balones()
        duraciones = tuple(b.giro_s for b in lista)
        self.assertEqual(len(set(duraciones)), len(duraciones))
        sentidos = {b.sentido for b in lista}
        self.assertIn(1, sentidos)
        self.assertIn(-1, sentidos)

        # `transform-style:preserve-3d` del contenedor (criterio 26.3).
        self.assertIn(
            f".{mh.CLASE_BALON}{{display:block;transform-style:preserve-3d;}}",
            self.css,
        )

        # Degradacion de dos dimensiones bajo el corte de pantalla angosta: la
        # animacion pasa a `rotate(` y el gajo sombreado se desplaza del centro.
        marca = f"@media (max-width:{mh.CORTE_ANGOSTO_REM})"
        self.assertIn(marca, self.css)
        bloque_angosto = self.css[self.css.index(marca) :]
        self.assertIn("animation-name:hero-rueda-2d", bloque_angosto)
        self.assertIn(f".{mh.CLASE_GAJO_SOMBREADO}{{transform:translate(", bloque_angosto)
        self.assertIn("@keyframes hero-rueda-2d", self.css)
        self.assertIn("transform:rotate(0deg)", self.css)
        self.assertIn("transform:rotate3d(var(--eje)", self.css)
        # Ninguna regla animada del balon toca geometria ni sombra (10.2). Se
        # mide sobre los cuerpos de `@keyframes`, que son las reglas animadas:
        # `max-width` de la consulta de medios no es una declaracion animada.
        for cuerpo in cuerpos_de_keyframes(self.css):
            for prohibida in (
                "box-shadow",
                "top:",
                "left:",
                "width:",
                "height:",
                "margin",
            ):
                with self.subTest(prohibida=prohibida, cuerpo=cuerpo[:24]):
                    self.assertNotIn(prohibida, cuerpo)
        self.assertNotIn("box-shadow", self.css)

        def prop(indice: int) -> None:
            balon = lista[indice]
            marcado = self.marcado[balon.id]

            # Exactamente ocho Gajo_Balon, cada uno con su `rotate3d(` propio y
            # distinto de los otros siete.
            gajos = _RE_GAJO.findall(marcado)
            self.assertEqual(len(gajos), mh.GAJOS)
            self.assertEqual(len(gajos), 8)
            rotaciones = [estilo for _clases, estilo in gajos]
            for rotacion in rotaciones:
                self.assertIn("rotate3d(", rotacion)
            self.assertEqual(len(set(rotaciones)), len(rotaciones))
            # Los angulos emitidos son los ocho declarados, en su orden.
            self.assertEqual(
                rotaciones,
                [
                    f"transform:rotate3d(0,1,0,{sp.num(a)}deg)"
                    for a in mh.ANGULOS_GAJO
                ],
            )

            # Un Gajo_Balon sombreado, y solo uno.
            sombreados = [
                clases
                for clases, _estilo in gajos
                if mh.CLASE_GAJO_SOMBREADO in clases
            ]
            self.assertEqual(len(sombreados), 1)
            self.assertIn(f"gajo-{mh.GAJO_SOMBREADO}", sombreados[0])

            # Los dos casquetes polares.
            self.assertIn('<g class="polo-superior">', marcado)
            self.assertIn('<g class="polo-inferior">', marcado)

            # Eje_Giro_Inclinado: tres componentes no nulas e inclinacion en
            # [15, 45] grados.
            eje = mh.eje_de(balon.id)
            self.assertEqual(len(eje), 3)
            for componente in eje:
                self.assertNotEqual(componente, 0.0)
            grados = mh.inclinacion_eje(eje)
            self.assertGreaterEqual(grados, 15.0)
            self.assertLessEqual(grados, 45.0)
            x, y, z = eje
            self.assertAlmostEqual(
                grados,
                math.degrees(
                    math.acos(abs(y) / math.sqrt(x * x + y * y + z * z))
                ),
                delta=TOLERANCIA,
            )

            # Duracion de vuelta, sentido y la regla de la lejania de la capa.
            self.assertGreaterEqual(balon.giro_s, 14.0)
            self.assertLessEqual(balon.giro_s, 26.0)
            self.assertIn(balon.sentido, (1, -1))
            for otro in lista:
                if otro.id == balon.id:
                    continue
                self.assertNotEqual(balon.giro_s, otro.giro_s)
                indice_balon = mh.CAPAS.index(balon.capa)
                indice_otro = mh.CAPAS.index(otro.capa)
                if indice_balon > indice_otro:
                    self.assertLess(balon.giro_s, otro.giro_s)

            # Marcado seguro (criterio 26.11).
            for prohibido in ("<image", "<img", "url(", "http", "tabindex"):
                with self.subTest(prohibido=prohibido):
                    self.assertNotIn(prohibido, marcado)
            self.assertIsNone(_RE_EVENTO.search(marcado))

            # Emision determinista: dos llamadas dan bytes identicos.
            self.assertEqual(marcado, mh.svg_balon_esfera(balon))

        for_all(gen_indice_balon, prop, iteraciones=100, etiqueta=ETQ_P50)


# --------------------------------------------------------------------------- #
# Property 28: round trip de las constantes a JSON
# --------------------------------------------------------------------------- #

ETQ_P28 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 28: Round trip de las constantes a JSON"
)

#: Las once claves del mundo y las siete de la ampliacion, en el orden declarado.
CLAVES_MUNDO = (
    "f",
    "e",
    "z",
    "tope",
    "k",
    "corte",
    "minA",
    "maxA",
    "radio",
    "rebote",
    "balones",
)
CLAVES_AMPLIACION = (
    "vistas",
    "residual",
    "azMovil",
    "umbralEl",
    "figuras",
    "girarMs",
    "dragDeg",
)


def gen_clave_json(rnd) -> str:
    """Una de las claves del literal, con las dos familias equilibradas.

    Cada iteracion se queda con una clave y comprueba **esa** contra su constante
    de Python, de modo que el contraejemplo de un fallo sea el nombre de la clave
    que se desincronizo y no el literal entero.
    """
    if rnd.randrange(2) == 0:
        return rnd.choice(CLAVES_MUNDO)
    return rnd.choice(CLAVES_AMPLIACION)


class TestProperty28RoundTripJson(unittest.TestCase):
    """Property 28: round trip de las constantes a JSON."""

    def test_property_28_round_trip_de_las_constantes_a_json(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 28: Round trip de las constantes a JSON.

        Para todo catalogo de Elemento_Fondo valido, deserializar el literal que
        produce la serializacion de constantes reproduce exactamente los factores
        de parallax, las escalas finales, los valores de `translateZ`, el tope del
        cursor, el coeficiente de suavizado, el corte de pantalla angosta, los
        limites de elementos activos, el radio del toque, la duracion del rebote y
        las coordenadas de los balones declaradas en Python; y el literal no
        contiene la subcadena `//` ni la cadena `http`.

        **Validates: Requirements 8.2, 9.5, 10.10, 12.1**
        """
        mh.validar_elementos()

        literal = mh.datos_json()
        leido = json.loads(literal)

        # Compacto: sin un solo espacio de separacion entre claves y valores.
        self.assertNotIn(", ", literal)
        self.assertNotIn(": ", literal)

        # Prohibiciones del cuerpo del script.
        self.assertNotIn("//", literal)
        self.assertNotIn("http", literal)

        # Las dieciocho claves, y ninguna de sobra, en el orden declarado.
        self.assertEqual(tuple(leido), CLAVES_MUNDO + CLAVES_AMPLIACION)

        # Round trip exacto contra el mapa de constantes de Python.
        self.assertEqual(leido, mh.datos_mundo())

        esperado = {
            "f": [mh.FACTOR_PARALLAX[c] for c in mh.CAPAS],
            "e": [mh.ESCALA_FINAL[c] for c in mh.CAPAS],
            "z": [mh.TRASLADO_Z_PX[c] for c in mh.CAPAS],
            "tope": mh.TOPE_CURSOR_PX,
            "k": mh.SUAVIZADO_CURSOR,
            "corte": mh.CORTE_ANGOSTO_PX,
            "minA": mh.ELEMENTOS_ANGOSTO[0],
            "maxA": mh.ELEMENTOS_ANGOSTO[1],
            "radio": mh.RADIO_TOQUE_PCT,
            "rebote": mh.REBOTE_MS,
            "balones": [[b.id, b.x_pct, b.y_pct] for b in mh.balones()],
            "vistas": list(vf.CLAVES_VISTA),
            "residual": vf.ROTACION_RESIDUAL_MAX,
            "azMovil": list(vf.AZIMUTS_MOVIL),
            "umbralEl": vf.UMBRAL_ELEVACION,
            "figuras": [
                [f.id, f.vuelta_s, f.sentido, f.z_figura_px]
                for f in mh.FIGURAS_GIRABLES
            ],
            "girarMs": vf.GIRO_IMPULSO_MS,
            "dragDeg": vf.GRADOS_POR_PIXEL,
        }

        def prop(clave: str) -> None:
            self.assertIn(clave, leido)
            self.assertEqual(leido[clave], esperado[clave])

            # El orden de los arreglos por capa es siempre lejana, media, cercana.
            if clave in ("f", "e", "z"):
                self.assertEqual(len(leido[clave]), len(mh.CAPAS))
                self.assertEqual(
                    leido[clave][0],
                    esperado[clave][mh.CAPAS.index(mh.CAPA_LEJANA)],
                )
                self.assertEqual(
                    leido[clave][-1],
                    esperado[clave][mh.CAPAS.index(mh.CAPA_CERCANA)],
                )

            # El indice de `vistas` ES el indice de la Vista_Figura dentro de su
            # contenedor: el Conmutador_Vista resuelve con un entero.
            if clave == "vistas":
                self.assertEqual(len(leido[clave]), 10)
                for indice, nombre in enumerate(leido[clave]):
                    self.assertEqual(vf.CLAVES_VISTA[indice], nombre)

            # Cada balon lleva su identificador y sus coordenadas declaradas.
            if clave == "balones":
                for fila, balon in zip(leido[clave], mh.balones()):
                    self.assertEqual(fila, [balon.id, balon.x_pct, balon.y_pct])

            # Cada figura lleva id, duracion, sentido y translateZ propio.
            if clave == "figuras":
                self.assertEqual(len(leido[clave]), len(mh.FIGURAS_GIRABLES))
                for fila in leido[clave]:
                    self.assertEqual(len(fila), 4)
                    figura = mh.figura_girable_de(fila[0])
                    self.assertEqual(fila[1], figura.vuelta_s)
                    self.assertEqual(fila[2], figura.sentido)
                    self.assertEqual(fila[3], figura.z_figura_px)

            # El literal es estable: dos emisiones dan el mismo texto.
            self.assertEqual(literal, mh.datos_json())

        for_all(gen_clave_json, prop, iteraciones=100, etiqueta=ETQ_P28)


# --------------------------------------------------------------------------- #
# Property 11: marcado SVG seguro
# --------------------------------------------------------------------------- #

ETQ_P11 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 11: Marcado SVG seguro"
)

#: Prohibiciones comunes a **todo** SVG en linea que emite Python (criterios 1.9,
#: 11.3 y 14.15).
PROHIBIDOS_SVG = ("<image", "<img", "http", "url(", "tabindex")

#: Prohibiciones adicionales del Mundo_Hero: ninguna referencia a un archivo de
#: imagen ni a ningun recurso (criterio 7.8). El Generador_SVG queda fuera porque
#: `anatomia-base` emite su Zona_Tactil de ampliacion como enlace de ancla.
PROHIBIDOS_FONDO = ("href", "xlink:")


def gen_fuente_svg(rnd) -> tuple[str, str]:
    """Una fuente de SVG en linea: `(familia, identificador)`.

    Cubre las cuatro familias que emiten marcado hoy: los ocho Diagrama_Postura
    del Generador_SVG, las diez Vista_Figura de cada Figura_Girable, el dibujo
    suelto de cada Elemento_Fondo y el objeto completo del Mundo_Hero con su
    envoltorio. El identificador viaja como cadena para que el contraejemplo diga
    exactamente qué se emitió mal.
    """
    familia: str = rnd.choice(("diagrama", "vista", "elemento", "objeto", "mundo"))
    if familia == "diagrama":
        return (familia, rnd.choice(dp.CATALOGO).id)
    if familia == "vista":
        figura = rnd.choice(mh.FIGURAS_GIRABLES)
        return (familia, f"{figura.id}/{rnd.choice(vf.CLAVES_VISTA)}")
    if familia == "mundo":
        return (familia, "")
    return (familia, rnd.choice(mh.ELEMENTOS).id)


def marcado_de_fuente(familia: str, identificador: str) -> str:
    """Marcado que emite `familia` para `identificador`."""
    if familia == "diagrama":
        return sp.svg_diagrama(dp.por_id(identificador))
    if familia == "vista":
        id_figura, clave = identificador.split("/", 1)
        figura = mh.figura_girable_de(id_figura)
        return vf.svg_vista(
            mh.pose_de_figura(figura),
            clave,
            mh.diagrama_de_figura(figura),
            color_tapa=vf.COLOR_TAPA_FONDO,
        )
    if familia == "elemento":
        return mh.svg_elemento(mh.elemento_de(identificador))
    if familia == "objeto":
        return mh.marcado_objeto(mh.elemento_de(identificador))
    return mh.marcado_mundo()


class TestProperty11MarcadoSvgSeguro(unittest.TestCase):
    """Property 11: marcado SVG seguro."""

    def test_property_11_marcado_svg_seguro(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 11: Marcado SVG seguro.

        Para todo SVG en linea que emite Python (Generador_SVG y Mundo_Hero), el
        marcado contiene un elemento `<svg>`, contiene el atributo de datos
        declarado por su fuente cuando corresponde (`data-angosto` con el valor de
        la marca de pantalla angosta en los Elemento_Fondo), y no contiene ningun
        elemento `<image>`, ningun elemento `<img>`, ninguna cadena `http`,
        ninguna funcion `url(`, ningun atributo `tabindex` ni ningun atributo de
        evento en linea.

        **Validates: Requirements 1.9, 7.8, 11.3, 12.4, 14.15**
        """

        def prop(fuente: tuple[str, str]) -> None:
            familia, identificador = fuente
            marcado = marcado_de_fuente(familia, identificador)

            self.assertIn("<svg", marcado)
            for prohibido in PROHIBIDOS_SVG:
                with self.subTest(fuente=fuente, prohibido=prohibido):
                    self.assertNotIn(prohibido, marcado)
            self.assertIsNone(
                _RE_EVENTO.search(marcado),
                msg=f"{familia}/{identificador}: atributo de evento en linea",
            )

            # El Mundo_Hero no referencia ningun archivo ni recurso externo.
            if familia in ("elemento", "objeto", "mundo"):
                for prohibido in PROHIBIDOS_FONDO:
                    with self.subTest(fuente=fuente, prohibido=prohibido):
                        self.assertNotIn(prohibido, marcado)

            # `data-angosto` con el valor de la marca de pantalla angosta.
            if familia == "objeto":
                elemento = mh.elemento_de(identificador)
                esperado = "1" if elemento.angosto else "0"
                self.assertIn(f'data-angosto="{esperado}"', marcado)
                self.assertEqual(marcado.count("data-angosto="), 1)
                self.assertIn(f'data-tipo="{elemento.tipo}"', marcado)
            if familia == "mundo":
                # Un `data-angosto` por Elemento_Fondo, ninguno de sobra, y el
                # valor de cada uno es el de su marca declarada.
                self.assertEqual(
                    marcado.count("data-angosto="), len(mh.ELEMENTOS)
                )
                for elemento in mh.ELEMENTOS:
                    esperado = "1" if elemento.angosto else "0"
                    self.assertIn(
                        f'data-id="{elemento.id}" data-angosto="{esperado}"',
                        marcado,
                    )
                # El contenedor es decorativo y las tres capas se identifican.
                self.assertIn(f'id="{mh.ID_MUNDO}" aria-hidden="true"', marcado)
                for capa in mh.CAPAS:
                    self.assertIn(f'data-capa="{capa}"', marcado)
                    self.assertIn(f'id="{mh.id_de_capa(capa)}"', marcado)

            # Emision determinista: dos llamadas dan bytes identicos.
            self.assertEqual(
                marcado, marcado_de_fuente(familia, identificador)
            )

        for_all(gen_fuente_svg, prop, iteraciones=100, etiqueta=ETQ_P11)


# --------------------------------------------------------------------------- #
# Property 51: Modo_Inerte
# --------------------------------------------------------------------------- #

ETQ_P51 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 51: Modo_Inerte"
)

#: Apertura de un elemento cualquiera, para contar nodos sin parsear el arbol.
_RE_NODO = re.compile(r"<[a-zA-Z]")


def nodos(marcado: str) -> int:
    """Numero de nodos que `marcado` declara, contando aperturas de elemento."""
    return len(_RE_NODO.findall(marcado))


class TestProperty51ModoInerte(unittest.TestCase):
    """Property 51: Modo_Inerte.

    Esta propiedad tiene tres mitades y **las tres** existen ya en el codigo:

    * **El catalogo y las curvas** (`mundo_hero.inerte`, `mundo_hero.opacidad`) y
      **el marcado** (`marcado_mundo`): se verifican aqui, enteros.
    * **La mitad declarativa del CSS** (`mundo_hero.bloque_css`), cableada a
      `build_html.estilo_css()` por la tarea 10.6.
    * **La mitad imperativa** (tarea 12.6): que el Script_Unico alterne la clase
      con la **lista de clases** del contenedor y que, mientras el Modo_Inerte esta
      activo, omita toda escritura de `transform` y de `opacity` sobre las capas y
      sobre las Vista_Figura (criterios 27.5, 27.6 y 27.9 en su parte de
      JavaScript). Se afirma sobre el cuerpo del `<script>` emitido, troceado por
      `gen.cuerpo_de_funcion` para que el contraejemplo sea la funcion infractora
      y no el script entero.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = mh.bloque_css()
        cls.marcado = mh.marcado_mundo()
        cls.js = build_site._js_hero()
        cls.cuerpo_mundo = gen.cuerpo_de_funcion(cls.js, "aplicarMundo")
        cls.cuerpo_vistas = gen.cuerpo_de_funcion(cls.js, "aplicarVistas")

    def test_property_51_modo_inerte(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 51: Modo_Inerte.

        Para toda secuencia de progresos de scroll, la clase de Modo_Inerte esta
        presente en el contenedor del Mundo_Hero exactamente cuando su opacidad
        vale 0, y se retira en cuanto el progreso baja por debajo de 1 sin
        reiniciar las animaciones pausadas; la regla de Modo_Inerte declara
        `visibility:hidden` y `animation-play-state:paused` y alcanza las tres
        capas, los Elemento_Fondo, las Vista_Figura, los Gajo_Balon y las
        Sombra_Contacto, y declara `will-change:auto` para las tres capas;
        mientras esta activo no hay ninguna escritura de `transform` ni de
        `opacity` sobre las capas ni sobre las Vista_Figura; el numero de nodos del
        Mundo_Hero es el mismo con la clase y sin ella; la reaparicion declara una
        transicion de `opacity` con una duracion entre 200 y 600 milisegundos; y el
        Script_Unico alterna el estado con la lista de clases del contenedor, sin
        ninguna escritura en linea de `animation-play-state` ni de `display`.

        **Validates: Requirements 10.16, 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7, 27.8, 27.9**
        """
        selector = f".{mh.CLASE_MUNDO}.{mh.CLASE_INERTE}"

        # La regla declara las dos propiedades del criterio 27.2.
        self.assertIn(
            f"{selector}{{visibility:hidden;animation-play-state:paused;}}",
            self.css,
        )

        # Y alcanza las tres capas, los Elemento_Fondo, las Vista_Figura, los
        # Gajo_Balon y las Sombra_Contacto (criterio 27.3).
        for alcanzada in (
            mh.CLASE_CAPA,
            mh.CLASE_OBJETO,
            vf.CLASE_VISTA,
            mh.CLASE_GAJO,
            mh.CLASE_SOMBRA,
        ):
            with self.subTest(alcanzada=alcanzada):
                self.assertIn(f"{selector} .{alcanzada}", self.css)

        # `will-change:auto` para las tres capas (criterio 27.4).
        self.assertIn(
            f"{selector} .{mh.CLASE_CAPA}{{will-change:auto;}}", self.css
        )

        # La reaparicion: transicion de `opacity` entre 200 y 600 ms (27.7).
        self.assertIn(
            f"transition:opacity {mh.TRANSICION_REAPARICION_MS}ms linear",
            self.css,
        )
        self.assertGreaterEqual(mh.TRANSICION_REAPARICION_MS, 200)
        self.assertLessEqual(mh.TRANSICION_REAPARICION_MS, 600)

        # El marcado no lleva `animation-play-state` ni `display` en linea: el
        # Modo_Inerte es una clase y nada mas (criterios 10.16 y 27.9).
        self.assertNotIn("animation-play-state", self.marcado)
        self.assertNotIn("display:", self.marcado)
        self.assertIn(f'class="{mh.CLASE_MUNDO}"', self.marcado)

        # Tarea 12.6, primera clausula: el Script_Unico alterna la clase con la
        # LISTA DE CLASES del contenedor, y no escribe en linea ni
        # `animation-play-state` ni `display` (criterios 10.16, 27.1, 27.6, 27.9).
        self.assertIn(f"var CL_INERTE='{mh.CLASE_INERTE}';", self.js)
        self.assertIn("classList.add(CL_INERTE)", self.cuerpo_mundo)
        self.assertIn("classList.remove(CL_INERTE)", self.cuerpo_mundo)
        self.assertNotIn("animation-play-state", self.js)
        escritas = {propiedad for propiedad, _ in gen.escrituras_de_estilo(self.js)}
        self.assertTrue(escritas)
        for prohibida in ("display", "animationPlayState", "animation"):
            with self.subTest(prohibida=prohibida):
                self.assertNotIn(prohibida, escritas)

        # Tarea 12.6, segunda clausula: mientras el Modo_Inerte esta activo se
        # omite TODA escritura de `transform` y de `opacity` sobre las capas y
        # sobre las Vista_Figura (criterio 27.5). La guarda va ANTES de la primera
        # escritura de cada funcion, que es lo que hace la omision efectiva.
        self.assertIn("inerteActivo", self.cuerpo_mundo)
        guarda_mundo = self.cuerpo_mundo.index("if(frio||reducido){continue;}")
        for propiedad in ("transform", "opacity"):
            with self.subTest(capa=propiedad):
                self.assertLess(
                    guarda_mundo,
                    self.cuerpo_mundo.index(f".style.{propiedad}="),
                    f"la escritura de {propiedad} sobre las capas no queda "
                    "detras de la guarda de Modo_Inerte",
                )
        self.assertLess(
            self.cuerpo_vistas.index("if(inerteActivo){return;}"),
            self.cuerpo_vistas.index(".style."),
            "la guarda de Modo_Inerte del Conmutador_Vista no va antes de su "
            "primera escritura",
        )

        # El numero de nodos no depende de la clase (criterio 27.8): poner la
        # clase es una sustitucion de texto en el atributo del contenedor, no una
        # creacion ni un borrado de nodos.
        con_clase = self.marcado.replace(
            f'class="{mh.CLASE_MUNDO}"',
            f'class="{mh.CLASE_MUNDO} {mh.CLASE_INERTE}"',
            1,
        )
        self.assertNotEqual(con_clase, self.marcado)
        self.assertEqual(nodos(con_clase), nodos(self.marcado))
        self.assertEqual(
            nodos(self.marcado),
            con_clase.count("<span") + con_clase.count("<div")
            + con_clase.count("<svg") + con_clase.count("<g ")
            + con_clase.count("<path") + con_clase.count("<ellipse")
            + con_clase.count("<circle") + con_clase.count("<rect")
            + con_clase.count("<text") + con_clase.count("<polyline")
            + con_clase.count("<polygon") + con_clase.count("<line"),
        )

        def prop(secuencia: tuple[float, ...]) -> None:
            if not secuencia:
                return
            creciente = tuple(sorted(secuencia))
            recorrido = creciente + tuple(reversed(creciente))

            for p in recorrido:
                activo = mh.inerte(p)

                # La clase esta puesta EXACTAMENTE cuando la opacidad vale 0.
                self.assertEqual(activo, mh.opacidad(p) == 0.0)
                if p >= 1.0:
                    self.assertTrue(activo)
                if p < 1.0:
                    # Se retira en cuanto el progreso baja por debajo de 1.
                    self.assertFalse(activo)

                # Tarea 12.6: el predicado que el bucle consulta para omitir las
                # escrituras es EXACTAMENTE este, y el bucle lo calcula con la
                # misma curva (`op === 0` sobre `1 - progreso`). Se comprueba que
                # el Script_Unico deriva el estado de esa curva y no de un
                # segundo umbral escrito a mano.
                self.assertEqual(activo, mh.inerte(p))
                self.assertEqual(activo, mh.opacidad(p) == 0.0)
                self.assertIn("var frio=(op===0);", self.cuerpo_mundo)
                self.assertIn("var op=1-p;", self.cuerpo_mundo)

            # Recorrer la secuencia en los dos sentidos da el mismo estado para el
            # mismo progreso: el Modo_Inerte no tiene memoria, sale de la curva.
            for p in creciente:
                self.assertEqual(mh.inerte(p), mh.inerte(p))

        for_all(
            gen.gen_secuencia_progresos, prop, iteraciones=100, etiqueta=ETQ_P51
        )


if __name__ == "__main__":
    unittest.main()
