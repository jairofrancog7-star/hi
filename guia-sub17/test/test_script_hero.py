"""Pruebas del contrato de animacion y de accesibilidad del hero.

Feature `imagenes-reales-hero-interactivo`, bloque 10 (Hoja_Estilo):

* **Property 31** (tarea 10.11): toda `@keyframes` y toda `transition` del hero
  animan solo `transform` y `opacity`; `will-change:transform` vive unicamente en
  el selector de las tres Capa_Parallax; el hero declara su degradado vertical y
  el halo de `.hero-velo`; el contenedor del Mundo_Hero declara su perspectiva; y
  el documento conserva las siete capas y los 13 Elemento_Fondo congelados.
* **Property 33** (tarea 10.12): el contenedor del Mundo_Hero lleva
  `aria-hidden="true"` y no recibe punteros; el bloque de Movimiento_Reducido
  congela capas y Elemento_Fondo con opacidad 1; y `@media print` va **despues**
  de Movimiento_Reducido, para que gane por cascada.

Feature `imagenes-reales-hero-interactivo`, bloque 12 (Script_Unico):

* **Property 29** (tarea 12.7): una sola llamada a `requestAnimationFrame` dentro
  de una sola funcion de bucle, presupuesto de escrituras por capa, ninguna
  lectura de geometria en el bucle y visibilidad **solo** por
  `IntersectionObserver`.
* **Property 30** (tarea 12.8): higiene del Script_Unico, escuchador de
  desplazamiento pasivo que solo guarda `scrollY`, toque en el contenedor del
  hero y permiso de orientacion en un solo lugar.
* **Property 32** (tarea 12.9): pantallas angostas, con una degradacion que toca
  solo el numero de Elemento_Fondo activos y de Clave_Vista candidatas.
* **Property 48** (tarea 12.10): higiene del Conmutador_Vista, con cero
  escrituras mientras la Clave_Vista no cambia.
* **Property 52** (tarea 12.11): Arrastre_Rotacion, Giro_Impulso y Visor_Ampliado.

_Requirements: 6.1, 6.2, 6.7, 6.8, 6.9, 9.7, 9.9, 9.11, 9.12, 10.1, 10.2, 10.3,
10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 10.14, 10.15,
11.1, 11.2, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 12.1, 12.2, 12.3, 12.5, 12.6,
13.1, 15.16, 25.8, 25.9, 25.12, 25.13, 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7,
28.8, 28.9, 28.10, 28.11, 28.12, 28.13, 28.14, 28.15, 28.16, 28.18, 29.1, 29.2,
29.3_
"""

from __future__ import annotations

import os
import random
import re
import sys
import unittest

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
from guia import build_html, build_site, mundo_hero as mh  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia import secciones_guia as sg  # noqa: E402
from guia import svg_postura as sp  # noqa: E402
from guia import vistas_figura as vf  # noqa: E402
from prop import for_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Contrato compartido
# --------------------------------------------------------------------------- #

#: Las UNICAS dos propiedades que el hero tiene permitido animar (criterio 10.1).
#: Las dos se resuelven en el compositor, sin recalcular maquetacion.
ANIMABLES: frozenset[str] = frozenset({"transform", "opacity", "visibility"})

#: Propiedades cuya animacion obliga al navegador a rehacer la maquetacion o a
#: repintar en la CPU (criterio 10.2). Ninguna aparece en una `@keyframes` ni en
#: una `transition` del hero.
PROHIBIDAS: tuple[str, ...] = (
    "top",
    "left",
    "right",
    "bottom",
    "width",
    "height",
    "margin",
    "padding",
    "box-shadow",
)

#: Las siete capas del hero que el criterio 6.7 conserva.
CAPAS_HERO: tuple[str, ...] = (
    "hero",
    "hero-visor",
    "hero-lienzo",
    "hero-reserva",
    "hero-velo",
    "hero-ui",
    "hero-borde",
)

#: Prefijos de selector que pertenecen al hero: sus capas, el Mundo_Hero, las
#: Figura_Girable con sus Vista_Figura, los Balon_Esfera con sus Gajo_Balon y las
#: Sombra_Contacto. Es el alcance de la Property 31.
PREFIJOS_HERO: tuple[str, ...] = (
    ".hero",
    ".figura-",
    ".balon-",
    ".gajo-",
    ".sombra-",
)

#: Selectores que tienen permitido declarar `will-change` (criterios 10.6 y 29.9).
#: Son exactamente los de las tres Capa_Parallax: el de la capa animada y el que
#: la libera cuando el Modo_Inerte entra.
SELECTORES_WILL_CHANGE: frozenset[str] = frozenset(
    {
        f".{mh.CLASE_CAPA}",
        f".{mh.CLASE_MUNDO}.{mh.CLASE_INERTE} .{mh.CLASE_CAPA}",
    }
)


def _es_del_hero(selector: str) -> bool:
    """True si `selector` pertenece al hero, al Mundo_Hero o a sus figuras."""
    return any(prefijo in selector for prefijo in PREFIJOS_HERO)


def _propiedades_animadas(cuerpo: str) -> tuple[str, ...]:
    """Propiedades que declara el cuerpo de una `@keyframes`, sin duplicados.

    El cuerpo de una `@keyframes` llega ya troceado por `gen.reglas`, asi que aqui
    solo hay que leer los nombres de propiedad de cada fotograma.
    """
    halladas: list[str] = []
    for trozo in cuerpo.split(";"):
        nombre, _, valor = trozo.partition(":")
        limpio = nombre.strip().lstrip("{}").split("{")[-1].strip()
        if limpio and valor and limpio not in halladas:
            halladas.append(limpio)
    return tuple(halladas)


def _propiedades_de_transicion(valor: str) -> tuple[str, ...]:
    """Propiedades que enumera una declaracion `transition`.

    `transition:transform .25s ease,border-color .25s ease` -> `("transform",
    "border-color")`. La palabra `all` se devuelve tal cual, porque es
    precisamente lo que una propiedad de presupuesto debe rechazar.
    """
    partes: list[str] = []
    for tramo in valor.split(","):
        piezas = tramo.strip().split()
        if piezas:
            partes.append(piezas[0])
    return tuple(partes)


ETQ_P31 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 31: Propiedades animadas y capas del hero"
)

ETQ_P33 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 33: Accesibilidad del fondo, movimiento reducido e impresion"
)


def gen_indice_animacion(rnd: random.Random) -> int:
    """Indice de una regla animada de la Hoja_Estilo: `@keyframes` o `transition`.

    El generador recorre el espacio real de reglas animadas del artefacto, que es
    lo que la Property 31 cuantifica. Devolver un entero deja que el shrinker lo
    reduzca hacia 0 y que el contraejemplo sea una regla concreta.
    """
    return rnd.randrange(_TOTAL_ANIMADAS)


class TestProperty31AnimacionDelHero(unittest.TestCase):
    """Property 31: propiedades animadas y capas del hero."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.sitio = build_site.html_sitio()
        cls.reglas = gen.reglas(cls.css)
        cls.keyframes = tuple(
            r for r in cls.reglas if r.selector.startswith("@keyframes")
        )
        cls.transiciones = gen.declaraciones(cls.css, "transition")

    def test_property_31_propiedades_animadas_y_capas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 31: Propiedades animadas y capas del hero.

        Para toda regla `@keyframes` y para toda declaracion de `transition` del
        bloque del hero en la Hoja_Estilo, el conjunto de propiedades animadas esta
        contenido en `{transform, opacity}` y no contiene `top`, `left`, `width`,
        `height`, `margin` ni `box-shadow`; `will-change:transform` aparece
        unicamente en el selector de las tres capas del Mundo_Hero; el hero declara
        el degradado vertical de `--azul-cielo` a `--azul-medio`, el halo de
        `.hero-velo` con opacidad en [0.30, 0.40] conservando su
        `linear-gradient(`, y el contenedor del Mundo_Hero declara
        `perspective:1000px` y `transform-style:preserve-3d`; y el documento
        conserva las siete capas del hero y las cadenas congeladas de los 13
        elementos del arte actual.

        **Validates: Requirements 6.1, 6.2, 6.7, 6.8, 6.9, 10.1, 10.2, 10.6**
        """
        # Hay algo que revisar: si la Hoja_Estilo perdiera sus `@keyframes` la
        # propiedad seria vacuamente cierta y no diria nada.
        self.assertGreaterEqual(len(self.keyframes), 4)
        self.assertGreaterEqual(len(self.transiciones), 4)

        animadas: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
            (r.selector, _propiedades_animadas(r.cuerpo)) for r in self.keyframes
        ) + tuple(
            (selector, _propiedades_de_transicion(valor))
            for selector, valor in self.transiciones
            if _es_del_hero(selector)
        )

        def prop(indice: int) -> None:
            selector, propiedades = animadas[indice % len(animadas)]
            self.assertTrue(propiedades, f"{selector}: no anima nada")
            for propiedad in propiedades:
                with self.subTest(selector=selector, propiedad=propiedad):
                    # `all` anima cualquier cosa, incluida la geometria: prohibido.
                    self.assertNotEqual(propiedad, "all", selector)
                    self.assertIn(
                        propiedad,
                        ANIMABLES,
                        f"{selector} anima {propiedad}, fuera de "
                        f"{sorted(ANIMABLES)}",
                    )
                    for prohibida in PROHIBIDAS:
                        self.assertFalse(
                            propiedad == prohibida
                            or propiedad.endswith(f"-{prohibida}"),
                            f"{selector} anima {propiedad}",
                        )

        for_all(gen_indice_animacion, prop, iteraciones=100, etiqueta=ETQ_P31)

    def test_will_change_solo_en_las_tres_capas(self) -> None:
        # Criterios 10.6 y 29.9: `will-change` no aparece en ningun selector de
        # Vista_Figura, de Gajo_Balon ni de Sombra_Contacto.
        declaradas = gen.declaraciones(self.css, "will-change")
        self.assertTrue(declaradas)
        for selector, valor in declaradas:
            with self.subTest(selector=selector, valor=valor):
                self.assertIn(selector, SELECTORES_WILL_CHANGE)
        transform = [s for s, v in declaradas if v == "transform"]
        self.assertEqual(transform, [f".{mh.CLASE_CAPA}"])

    def test_degradado_del_hero_y_halo_del_velo(self) -> None:
        # Criterio 6.1: degradado vertical de `--azul-cielo` a `--azul-medio`. Se
        # mide sobre el tema de pantalla, no sobre `@media print`, que conmuta al
        # tema claro de alto contraste del papel.
        pantalla = "".join(
            f"{r.selector}{{{r.cuerpo}}}" for r in self.reglas if r.media == ""
        )
        fondos = dict(gen.declaraciones(pantalla, "background"))
        self.assertIn(".hero", fondos)
        self.assertEqual(
            fondos[".hero"],
            "linear-gradient(180deg,var(--azul-cielo),var(--azul-medio))",
        )
        # Criterio 6.2: halo blanco difuso con opacidad en [0.30, 0.40] y su
        # `linear-gradient(` conservado.
        velo = next(r for r in self.reglas if r.selector == ".hero-velo")
        self.assertIn("linear-gradient(", velo.cuerpo)
        opacidades = [
            float(v) for s, v in gen.declaraciones(self.css, "opacity")
            if s == ".hero-velo"
        ]
        self.assertEqual(len(opacidades), 1)
        self.assertGreaterEqual(opacidades[0], 0.30)
        self.assertLessEqual(opacidades[0], 0.40)

    def test_perspectiva_del_contenedor_del_mundo(self) -> None:
        # Criterio 6.8: `perspective:1000px` y `transform-style:preserve-3d`.
        mundo = next(r for r in self.reglas if r.selector == f".{mh.CLASE_MUNDO}")
        self.assertIn(f"perspective:{mh.PERSPECTIVA_PX}px", mundo.cuerpo)
        self.assertEqual(mh.PERSPECTIVA_PX, 1000)
        self.assertIn("transform-style:preserve-3d", mundo.cuerpo)

    def test_las_siete_capas_y_los_elementos_congelados(self) -> None:
        # Criterio 6.7: las siete capas siguen en el documento.
        for capa in CAPAS_HERO:
            with self.subTest(capa=capa):
                self.assertIn(f'class="{capa}"', self.sitio)
        # Criterio 6.9: los 13 Elemento_Fondo del arte congelado siguen ahi, mas
        # `silueta-3`, que la ampliacion anade sin tocar ninguna de las trece.
        self.assertEqual(len(mh.ELEMENTOS), 14)
        for elemento in mh.ELEMENTOS:
            with self.subTest(elemento=elemento.id):
                self.assertIn(f'data-id="{elemento.id}"', self.sitio)


class TestProperty33AccesibilidadDelFondo(unittest.TestCase):
    """Property 33: accesibilidad del fondo, movimiento reducido e impresion."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.medias = gen.bloques_media(cls.css)

    def test_property_33_accesibilidad_movimiento_reducido_e_impresion(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 33: Accesibilidad del fondo, movimiento reducido e impresion.

        Para todo documento emitido, el contenedor del Mundo_Hero lleva
        `aria-hidden="true"` y la Hoja_Estilo declara `pointer-events:none` para el
        y para todos sus descendientes; dentro del bloque de Movimiento_Reducido
        las capas y los Elemento_Fondo declaran `animation:none`, `transform:none` y
        opacidad 1; y el bloque `@media print` que oculta el contenedor del
        Mundo_Hero aparece despues del bloque de Movimiento_Reducido en el orden del
        CSS.

        **Validates: Requirements 11.1, 11.2, 11.4, 11.6, 11.7**
        """
        # El orden de la cascada no depende del documento: se mide una vez.
        condiciones = [c for c, _ in self.medias]
        self.assertIn("(prefers-reduced-motion: reduce)", condiciones)
        self.assertIn("print", condiciones)
        reducido = condiciones.index("(prefers-reduced-motion: reduce)")
        # El PRIMER `@media print` ya va detras del bloque de movimiento reducido:
        # asi gana por cascada y el fondo no se imprime ni con movimiento reducido
        # activo (criterio 11.7).
        impresion = condiciones.index("print")
        self.assertLess(
            reducido,
            impresion,
            "el bloque de impresion tiene que ir DESPUES del de movimiento "
            f"reducido para ganar por cascada: {condiciones}",
        )
        cuerpo_print = "".join(c for cond, c in self.medias if cond == "print")
        self.assertIn(f".{mh.CLASE_MUNDO}{{display:none;}}", cuerpo_print)

        cuerpo_reducido = next(
            c for cond, c in self.medias
            if cond == "(prefers-reduced-motion: reduce)"
        )
        congeladas = gen.reglas(cuerpo_reducido)
        alcanzadas = {r.selector: r.cuerpo for r in congeladas}
        selector_capas = (
            f".{mh.CLASE_MUNDO} .{mh.CLASE_CAPA},"
            f".{mh.CLASE_MUNDO} .{mh.CLASE_OBJETO},"
            f".{mh.CLASE_MUNDO} .{mh.CLASE_GIRO}"
        )
        self.assertIn(selector_capas, alcanzadas)
        for declaracion in (
            "animation:none !important",
            "transform:none !important",
            "opacity:1 !important",
        ):
            with self.subTest(declaracion=declaracion):
                self.assertIn(declaracion, alcanzadas[selector_capas])
        # Criterio 11.6: el Mundo_Hero se queda visible como fondo estatico.
        self.assertIn("opacity:1", alcanzadas[f".{mh.CLASE_MUNDO}"])

        def prop(presentes: tuple[str, ...]) -> None:
            documento = build_site.html_sitio(presentes=frozenset(presentes))

            # Criterio 11.1: el fondo decorativo esta oculto al lector de pantalla.
            apertura = documento[documento.index(f'class="{mh.CLASE_MUNDO}"') :]
            apertura = apertura[: apertura.index(">") + 1]
            self.assertIn('aria-hidden="true"', apertura)

            # Criterio 11.3: ningun Elemento_Fondo lleva `tabindex` ni evento. El
            # Mundo_Hero es el primer hijo de `.hero` y `.hero-visor` es el
            # siguiente, asi que el tramo entre los dos es el fondo entero.
            inicio = documento.index(f'class="{mh.CLASE_MUNDO}"')
            fin = documento.index('class="hero-visor"', inicio)
            mundo = documento[inicio:fin]
            self.assertGreater(len(mundo), 1000, "el Mundo_Hero llego vacio")
            self.assertNotIn("tabindex", mundo)
            for evento in (" onclick", " onload", " ontouchstart", " onpointerdown"):
                self.assertNotIn(evento, mundo.lower())

        for_all(gen.gen_presentes, prop, iteraciones=100, etiqueta=ETQ_P33)

    def test_el_mundo_no_recibe_punteros_ni_los_pasa(self) -> None:
        # Criterio 11.2: `pointer-events:none` en el contenedor Y en todos sus
        # descendientes, para que el fondo no robe un solo toque al texto.
        punteros = dict(gen.declaraciones(self.css, "pointer-events"))
        self.assertEqual(punteros.get(f".{mh.CLASE_MUNDO}"), "none")
        self.assertEqual(punteros.get(f".{mh.CLASE_MUNDO} *"), "none")

    def test_ninguna_regla_del_hero_usa_position_fixed(self) -> None:
        # `position:fixed` pelea con el desplazamiento en el navegador incrustado
        # de Android, asi que ninguna regla de LECTURA lo declara: el hero va por
        # `z-index` y la navegacion por `position:sticky`.
        #
        # QUE CAMBIO Y POR QUE: el criterio 28.5 lo prohibia en toda la hoja. El
        # Visor_Ampliado paso de seccion `:target` a overlay modal, que por
        # definicion tiene que cubrir la ventana, asi que ahora esta permitido
        # **solo** en `.visor-ampliado`. Se mide por conteo y por selector, igual
        # que ya se hacia con `touch-action:none`.
        self.assertEqual(self.css.count("position:fixed"), 1)
        posiciones = dict(gen.declaraciones(self.css, "position"))
        self.assertEqual(posiciones.get(f".{sg.CLASE_VISOR}"), "fixed")
        for selector, valor in posiciones.items():
            if selector == f".{sg.CLASE_VISOR}":
                continue
            with self.subTest(selector=selector):
                self.assertNotEqual(valor, "fixed")


# El total de reglas animadas se mide una sola vez, al importar el modulo: el
# generador necesita el tamano del espacio antes de que `setUpClass` corra.
_CSS_INICIAL: str = build_html.estilo_css()
_TOTAL_ANIMADAS: int = len(
    [r for r in gen.reglas(_CSS_INICIAL) if r.selector.startswith("@keyframes")]
) + len(
    [
        (s, v)
        for s, v in gen.declaraciones(_CSS_INICIAL, "transition")
        if _es_del_hero(s)
    ]
)
if _TOTAL_ANIMADAS <= 0:
    raise RuntimeError(
        "la Hoja_Estilo no declara ninguna regla animada: la Property 31 no "
        "tendria nada que cuantificar"
    )


# --------------------------------------------------------------------------- #
# Bloque 12: utileria compartida de las cinco propiedades del Script_Unico
# --------------------------------------------------------------------------- #

#: Las UNICAS propiedades de estilo en linea que el Script_Unico escribe. Son las
#: tres del criterio 10.3 mas `willChange`, que el criterio 10.7 obliga a devolver
#: a `auto` cuando la opacidad llega a 0. Ninguna de las cuatro provoca
#: maquetacion: las tres primeras las resuelve el compositor y la cuarta es una
#: pista para el navegador.
ESCRIBIBLES: frozenset[str] = frozenset(
    {"transform", "opacity", "visibility", "willChange"}
)

#: Lecturas de geometria que el cuerpo del bucle no tiene permitido hacer
#: (criterios 10.14 y 29.3). La visibilidad viene **solo** de
#: `IntersectionObserver`.
LECTURAS_PROHIBIDAS: tuple[str, ...] = (
    "getBoundingClientRect",
    "offsetTop",
    "clientHeight",
)

#: Interfaces que crean o destruyen nodos. El Script_Unico no usa ninguna: el
#: numero de nodos de cada Figura_Girable y de cada Visor_Ampliado no cambia nunca
#: (criterios 25.12, 25.13 y 28.15).
MUTADORES_DOM: tuple[str, ...] = (
    "innerHTML",
    "outerHTML",
    "createElement",
    "appendChild",
    "removeChild",
    "insertAdjacentHTML",
    "cloneNode",
)

#: Subcadenas que el cuerpo del `<script>` no puede contener (criterios 10.10 y
#: 13.1). `//` porque abriria un comentario de linea o una URL de protocolo
#: relativo; las otras porque el Target_Web es autocontenido.
PROHIBIDAS_JS: tuple[str, ...] = ("//", "import", "require(", "src=", "http")

#: Nombre de la unica funcion de bucle del Script_Unico.
NOMBRE_BUCLE: str = "bucle"

#: Funcion que escribe sobre las tres Capa_Parallax.
NOMBRE_CAPAS: str = "aplicarMundo"

#: Funcion que conmuta la Vista_Activa de cada Figura_Girable.
NOMBRE_VISTAS: str = "aplicarVistas"

#: `function <nombre>(` de cada funcion declarada en el script.
_RE_DECLARADA = re.compile(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

#: Llamada a una funcion por su nombre.
_RE_LLAMADA = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")

#: Escritura de estilo en linea, con su posicion en el script.
_RE_ESCRITURA = re.compile(r"\.style\.([A-Za-z]+)\s*=")

#: `setProperty('<prop>'` de una escritura de propiedad personalizada.
_RE_SET_PROPERTY = re.compile(r"\.style\.setProperty\(\s*['\"]([^'\"]+)['\"]")

#: Registro de escuchador, con el receptor y el nombre del evento.
_RE_ESCUCHADOR = re.compile(
    r"([A-Za-z_][A-Za-z0-9_.\[\]]*)\.addEventListener\(\s*'([a-zA-Z]+)'"
)


def funciones_declaradas(js: str) -> tuple[str, ...]:
    """Nombres de las funciones con nombre que `js` declara, en orden."""
    return tuple(_RE_DECLARADA.findall(js))


def tramo_de_funcion(js: str, nombre: str) -> tuple[int, int]:
    """Posiciones `(inicio, fin)` del cuerpo de `nombre` dentro de `js`.

    Devuelve `(-1, -1)` cuando la funcion no existe, para que una propiedad pueda
    afirmar su ausencia sin reventar con un error de indice.
    """
    coincidencia = re.search(
        r"function\s+" + re.escape(nombre) + r"\s*\(", js
    )
    if coincidencia is None:
        return (-1, -1)
    abre: int = js.find("{", coincidencia.end())
    if abre < 0:
        return (-1, -1)
    nivel: int = 1
    fin: int = abre + 1
    while fin < len(js) and nivel > 0:
        if js[fin] == "{":
            nivel += 1
        elif js[fin] == "}":
            nivel -= 1
        fin += 1
    return (abre + 1, fin - 1)


def funciones_del_bucle(js: str) -> tuple[str, ...]:
    """Funciones declaradas que el cuerpo del bucle invoca, en orden declarado.

    Es el alcance real del criterio 10.13: "dentro de la unica funcion de bucle"
    significa dentro de su cuerpo o del de las funciones que ese cuerpo llama, que
    es lo que el esbozo del diseno separa en `aplicarMundo()` y compania.
    """
    cuerpo: str = gen.cuerpo_de_funcion(js, NOMBRE_BUCLE)
    declaradas: tuple[str, ...] = funciones_declaradas(js)
    llamadas: list[str] = []
    for nombre in _RE_LLAMADA.findall(cuerpo):
        if nombre in declaradas and nombre not in llamadas:
            llamadas.append(nombre)
    return tuple(llamadas)


def escrituras_con_posicion(js: str) -> tuple[tuple[str, int], ...]:
    """Pares `(propiedad, posicion)` de cada escritura de estilo en linea de `js`."""
    halladas: list[tuple[str, int]] = []
    for coincidencia in _RE_ESCRITURA.finditer(js):
        halladas.append((coincidencia.group(1), coincidencia.start()))
    for coincidencia in _RE_SET_PROPERTY.finditer(js):
        halladas.append((coincidencia.group(1), coincidencia.start()))
    halladas.sort(key=lambda par: par[1])
    return tuple(halladas)


def cuenta_por_propiedad(fragmento: str) -> dict[str, int]:
    """Cuantas veces `fragmento` escribe cada propiedad de estilo en linea."""
    cuenta: dict[str, int] = {}
    for propiedad, _ in gen.escrituras_de_estilo(fragmento):
        cuenta[propiedad] = cuenta.get(propiedad, 0) + 1
    return cuenta


def escuchadores(js: str) -> tuple[tuple[str, str], ...]:
    """Pares `(receptor, evento)` de cada `addEventListener` de `js`."""
    return tuple(_RE_ESCUCHADOR.findall(js))


def activos_en_ancho(ancho: int) -> tuple[str, ...]:
    """Elemento_Fondo activos con la ventana de `ancho` pixeles.

    Reproduce en Python, paso por paso, lo que hace `aplicarAngosto()` en el
    Script_Unico: por encima del corte estan los catorce; por debajo sobreviven
    los marcados `data-angosto="1"` hasta el maximo declarado y, si no llegaran al
    minimo, se rellenan con los demas. El orden de recorrido es el mismo:
    marcados primero.
    """
    minimo, maximo = mh.ELEMENTOS_ANGOSTO
    if ancho >= mh.CORTE_ANGOSTO_PX:
        return tuple(e.id for e in mh.ELEMENTOS)
    orden = [e for e in mh.ELEMENTOS if e.angosto]
    orden += [e for e in mh.ELEMENTOS if not e.angosto]
    vivos: int = 0
    activos: list[str] = []
    for elemento in orden:
        cupo: int = maximo if elemento.angosto else minimo
        if vivos < cupo:
            vivos += 1
            activos.append(elemento.id)
    return tuple(activos)


def indice_mas_cercano_js(angulo: float, *, angosto: bool) -> int:
    """El `indiceMasCercano` del Script_Unico, transcrito a Python.

    Se transcribe a proposito, linea por linea, para poder comparar su resultado
    con `vistas_figura.vista_mas_cercana`, que es la fuente de verdad. Si las dos
    dejaran de coincidir, la propiedad falla y senala el angulo exacto.
    """
    azimuts: list[int] = []
    indices: list[int] = []
    for indice, clave in enumerate(vf.CLAVES_VISTA):
        if clave[0] == "a":
            azimuts.append(int(clave[3:]))
            indices.append(indice)
    mejor: int = -1
    dmin: float = 1e9
    for posicion, azimut in enumerate(azimuts):
        if angosto and azimut not in vf.AZIMUTS_MOVIL:
            continue
        distancia: float = abs(angulo - azimut) % 360.0
        if distancia > 180.0:
            distancia = 360.0 - distancia
        if distancia < dmin - 1e-9:
            dmin = distancia
            mejor = posicion
    return 0 if mejor < 0 else indices[mejor]


def clave_de_elevacion(elevacion: int) -> str:
    """Clave_Vista de la Vista_Elevacion con esa elevacion declarada."""
    for clave in vf.CLAVES_VISTA:
        if vf.elevacion_de(clave) == elevacion:
            return clave
    raise RuntimeError(
        f"no hay Vista_Elevacion declarada para {elevacion!r} grados"
    )


def clave_arrastre(dx: float, dy: float, *, angosto: bool) -> tuple[str, float, float]:
    """Clave_Vista, azimut y elevacion que el Arrastre_Rotacion resuelve.

    Transcripcion del `indiceArrastre()` del Script_Unico: azimut modulo 360 en
    `[0, 360)`, elevacion **acotada** al cerrado `[-topeEl, +topeEl]` con `topeEl`
    leido de la clave `el-p60`, y umbral `UMBRAL_ELEVACION` para decidir entre
    Vista_Elevacion y Vista_Azimut.
    """
    tope: int = max(vf.ELEVACIONES_DECLARADAS)
    azimut: float = (dx * vf.GRADOS_POR_PIXEL) % 360.0
    elevacion: float = dy * vf.GRADOS_POR_PIXEL
    if elevacion > tope:
        elevacion = float(tope)
    if elevacion < -tope:
        elevacion = float(-tope)
    if elevacion >= vf.UMBRAL_ELEVACION:
        return (clave_de_elevacion(tope), azimut, elevacion)
    if elevacion <= -vf.UMBRAL_ELEVACION:
        return (clave_de_elevacion(-tope), azimut, elevacion)
    return (
        vf.CLAVES_VISTA[indice_mas_cercano_js(azimut, angosto=angosto)],
        azimut,
        elevacion,
    )


#: Script_Unico del hero y el documento por defecto, medidos una sola vez: el
#: cuerpo del script no depende del subconjunto de Archivo_Diagrama presentes.
_JS_HERO: str = build_site._js_hero()
_SITIO: str = build_site.html_sitio()


def cuerpo_script(documento: str) -> str:
    """Cuerpo del unico `<script>` de `documento`, sin sus etiquetas."""
    bajo: str = documento.lower()
    cuerpo: str = documento[bajo.index("<script") :]
    return cuerpo[: cuerpo.lower().index("</script>")]


def sin_script(documento: str) -> str:
    """`documento` con su unico `<script>` retirado por completo."""
    bajo: str = documento.lower()
    inicio: int = bajo.index("<script")
    fin: int = bajo.index("</script>") + len("</script>")
    return documento[:inicio] + documento[fin:]


if not funciones_declaradas(_JS_HERO):
    raise RuntimeError(
        "el Script_Unico del hero no declara ninguna funcion: las propiedades "
        "del bloque 12 no tendrian nada que cuantificar"
    )

#: Todas las escrituras de estilo en linea del Script_Unico. Es el espacio que la
#: Property 29 cuantifica: el generador devuelve un indice sobre esta tupla, de
#: modo que el shrinker lo reduzca hacia 0 y el contraejemplo sea **la escritura**
#: infractora y no el script entero.
_ESCRITURAS: tuple[tuple[str, int], ...] = escrituras_con_posicion(_JS_HERO)
if not _ESCRITURAS:
    raise RuntimeError(
        "el Script_Unico no escribe ni un estilo en linea: la Property 29 no "
        "tendria nada que cuantificar"
    )


ETQ_P29 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 29: Bucle único y presupuesto de escrituras"
)


def gen_indice_escritura(rnd: random.Random) -> int:
    """Indice de una escritura de estilo en linea del Script_Unico."""
    return rnd.randrange(len(_ESCRITURAS))


class TestProperty29BucleUnico(unittest.TestCase):
    """Property 29: bucle unico y presupuesto de escrituras."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _JS_HERO
        cls.sitio = _SITIO
        cls.cuerpo = cuerpo_script(cls.sitio)
        cls.cuerpo_bucle = gen.cuerpo_de_funcion(cls.js, NOMBRE_BUCLE)
        cls.llamadas = funciones_del_bucle(cls.js)
        cls.tramos = tuple(
            (nombre,) + tramo_de_funcion(cls.js, nombre)
            for nombre in (NOMBRE_BUCLE,) + cls.llamadas
        )

    def test_property_29_bucle_unico_y_presupuesto(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 29: Bucle único y presupuesto de escrituras.

        Para todo Script_Unico emitido, el codigo contiene exactamente una llamada
        a `requestAnimationFrame`, situada dentro de una unica funcion de bucle
        compartida por el visor 3D y por el Mundo_Hero; dentro del cuerpo de esa
        funcion hay a lo sumo una asignacion a `transform` y a lo sumo una a
        `opacity` por capa del Mundo_Hero, todas las escrituras de estilo del
        Mundo_Hero ocurren dentro de ella, las unicas propiedades de estilo en
        linea que se escriben son `transform`, `opacity`, `visibility` y
        `willChange`, y el cuerpo no contiene ninguna lectura de geometria
        (`getBoundingClientRect`, `offsetTop`, `clientHeight`); la visibilidad de
        cada seccion animada proviene de un `IntersectionObserver` que observa
        todas las secciones animadas emitidas; el dibujado y las escrituras estan
        guardados por esa visibilidad y por la guarda de Movimiento_Reducido, y la
        detencion del bucle exige a la vez hero fuera de la ventana y documento
        oculto.

        **Validates: Requirements 10.3, 10.5, 10.8, 10.9, 10.11, 10.12, 10.13, 10.14, 11.5**
        """
        # Criterio 10.5: exactamente UNA llamada, y dentro de `bucle`.
        self.assertEqual(self.js.count("requestAnimationFrame("), 1)
        self.assertEqual(self.js.count(f"function {NOMBRE_BUCLE}("), 1)
        self.assertIn("requestAnimationFrame(bucle)", self.cuerpo_bucle)

        # Criterio 10.17: el mismo bucle sirve al visor, al Mundo_Hero, al
        # Conmutador_Vista y al Arrastre_Rotacion.
        for servido in ("dibujar", NOMBRE_CAPAS, NOMBRE_VISTAS):
            with self.subTest(servido=servido):
                self.assertIn(servido, self.llamadas)

        # Criterio 10.13: una `transform` y una `opacity` por capa y fotograma.
        cuenta = cuenta_por_propiedad(gen.cuerpo_de_funcion(self.js, NOMBRE_CAPAS))
        self.assertEqual(cuenta.get("transform"), 1)
        self.assertEqual(cuenta.get("opacity"), 1)
        self.assertEqual(cuenta.get("willChange"), 1)

        # Criterios 10.14 y 29.3: ni una lectura de geometria en el bucle ni en
        # las dos funciones que escriben sobre el Mundo_Hero.
        for nombre in (NOMBRE_BUCLE, NOMBRE_CAPAS, NOMBRE_VISTAS):
            cuerpo = gen.cuerpo_de_funcion(self.js, nombre)
            self.assertTrue(cuerpo, nombre)
            for lectura in LECTURAS_PROHIBIDAS:
                with self.subTest(funcion=nombre, lectura=lectura):
                    self.assertNotIn(lectura, cuerpo)

        # Criterios 10.8 y 10.9: el bucle se detiene solo con las DOS condiciones,
        # y con el hero fuera de la ventana no dibuja ni escribe.
        self.assertIn(
            "function debeParar(){return !enPantalla&&document.hidden;}", self.js
        )
        guarda = self.cuerpo_bucle.index("if(enPantalla){")
        for llamada in ("dibujar()", f"{NOMBRE_CAPAS}()", f"{NOMBRE_VISTAS}("):
            with self.subTest(llamada=llamada):
                self.assertLess(guarda, self.cuerpo_bucle.index(llamada))

        # Criterio 11.5: la guarda de Movimiento_Reducido esta en el bucle y en la
        # funcion que escribe las capas.
        self.assertIn("if(reducido)", self.cuerpo_bucle)
        self.assertIn(
            "reducido", gen.cuerpo_de_funcion(self.js, NOMBRE_CAPAS)
        )

        # Criterios 10.11, 10.12 y 29.10: UN `IntersectionObserver` que observa
        # cada seccion animada emitida, y ninguna otra fuente de visibilidad.
        self.assertEqual(self.js.count("new IntersectionObserver("), 1)
        self.assertIn("var SEL_ANIMADAS='.hero,.'+CL_VISOR;", self.js)
        self.assertIn("document.querySelectorAll(SEL_ANIMADAS)", self.js)
        self.assertIn("obs.observe(animadas[si])", self.js)
        self.assertIn('class="hero"', self.sitio)
        self.assertEqual(
            self.sitio.count(f'class="{sg.CLASE_VISOR}"'), len(dp.CATALOGO)
        )

        def prop(indice: int) -> None:
            propiedad, posicion = _ESCRITURAS[indice % len(_ESCRITURAS)]

            # Criterio 10.3 mas 10.7: solo cuatro propiedades escribibles.
            self.assertIn(
                propiedad,
                ESCRIBIBLES,
                f"el Script_Unico escribe {propiedad!r} en linea, fuera de "
                f"{sorted(ESCRIBIBLES)}",
            )

            # Criterio 10.13: TODA escritura vive dentro del bucle o de una de las
            # funciones que el bucle llama.
            dentro = [
                nombre
                for nombre, inicio, fin in self.tramos
                if inicio <= posicion < fin
            ]
            self.assertTrue(
                dentro,
                f"la escritura de {propiedad!r} en la posicion {posicion} cae "
                f"fuera del bucle y de {self.llamadas}",
            )

        for_all(gen_indice_escritura, prop, iteraciones=100, etiqueta=ETQ_P29)

    def test_will_change_vuelve_a_auto_con_opacidad_cero(self) -> None:
        # Criterio 10.7: `will-change` pasa a `auto` en las tres capas en cuanto
        # la opacidad llega a 0, que es cuando `frio` vale verdadero.
        cuerpo = gen.cuerpo_de_funcion(self.js, NOMBRE_CAPAS)
        self.assertIn("var frio=(op===0);", cuerpo)
        self.assertIn("willChange=frio?'auto':'transform'", cuerpo)


# --------------------------------------------------------------------------- #
# Property 30: higiene del Script_Unico
# --------------------------------------------------------------------------- #

ETQ_P30 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 30: Higiene del Script_Unico"
)

#: Nombre del manejador del Gesto_Activacion: el UNICO sitio donde se pide el
#: permiso de `DeviceOrientationEvent` (criterios 9.11 y 28.20).
NOMBRE_GESTO: str = "activarMovimiento"

#: Marcas del permiso de orientacion. Ninguna puede aparecer fuera del manejador
#: del Gesto_Activacion, y ninguna puede envolver el parallax de scroll (9.12).
MARCAS_PERMISO: tuple[str, ...] = (
    "DeviceOrientationEvent",
    "requestPermission",
    "granted",
)


class TestProperty30HigieneDelScript(unittest.TestCase):
    """Property 30: higiene del Script_Unico."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _JS_HERO
        cls.css = build_html.estilo_css()

    def test_property_30_higiene_del_script_unico(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 30: Higiene del Script_Unico.

        Para todo documento emitido, contiene exactamente un elemento `<script>`,
        propio y sin atributo `src`, con el CSS embebido en un elemento `<style>` y
        ningun recurso que bloquee el renderizado; el cuerpo del script registra el
        escuchador de desplazamiento con `{passive:true}` y en el guarda unicamente
        el valor de `window.scrollY`; registra el escuchador de toque sobre el
        contenedor del hero y no sobre ningun Elemento_Fondo; contiene la solicitud
        de permiso de `DeviceOrientationEvent` en un solo lugar, dentro del
        manejador del Gesto_Activacion, y ninguna guarda de ese permiso envuelve el
        parallax de scroll; contiene la rama que devuelve `will-change` a `auto`
        cuando la opacidad llega a 0; y no contiene la subcadena `//`, ni
        `import `, ni `require(`, ni `src=`, ni ninguna cadena `http`.

        **Validates: Requirements 9.7, 9.9, 9.11, 9.12, 10.4, 10.7, 10.10, 13.1, 15.16**
        """
        # Criterio 10.4: el escuchador de desplazamiento es pasivo y guarda SOLO
        # `window.scrollY`. Se afirma la cadena entera, que es corta y explicita.
        self.assertIn(
            "window.addEventListener('scroll',function(){"
            "scrollActual=window.scrollY;},{passive:true});",
            self.js,
        )
        self.assertEqual(self.js.count("'scroll'"), 1)

        # Criterio 9.9: el toque vive en el CONTENEDOR del hero. Ningun receptor de
        # escuchador es un Elemento_Fondo ni una capa del Mundo_Hero.
        registrados = escuchadores(self.js)
        self.assertIn(("hero", "touchstart"), registrados)
        receptores = {receptor for receptor, _ in registrados}
        # QUE CAMBIO Y POR QUE: la lista blanca gana tres receptores con el overlay
        # modal del Visor_Ampliado (`nodoAmp` la Zona_Tactil de ampliacion,
        # `nodoCer` la de cierre y `nodoOverlay` el propio overlay para el toque en
        # el fondo). Ninguno es un Elemento_Fondo ni una capa del Mundo_Hero, que
        # es lo que el criterio 9.9 protege y lo que las dos comprobaciones de
        # abajo siguen midiendo.
        self.assertLessEqual(
            receptores,
            {
                "cv",
                "visor",
                "hero",
                "btnMov",
                "nodoDrag",
                "nodoAmp",
                "nodoCer",
                "nodoOverlay",
                "window",
                "document",
            },
            f"receptores inesperados de escuchador: {sorted(receptores)}",
        )
        for receptor in receptores:
            with self.subTest(receptor=receptor):
                self.assertNotIn("objetos", receptor)
                self.assertNotIn("capas", receptor)

        # Criterios 9.11 y 28.20: el permiso se pide en UN SOLO sitio, y ese sitio
        # es el manejador del Gesto_Activacion, enganchado a la Zona_Tactil.
        inicio_gesto, fin_gesto = tramo_de_funcion(self.js, NOMBRE_GESTO)
        self.assertGreater(inicio_gesto, 0)
        self.assertIn(
            f"btnMov.addEventListener('click',{NOMBRE_GESTO},{{passive:true}})",
            self.js,
        )
        self.assertEqual(self.js.count("DeviceOrientationEvent"), 1)
        for marca in MARCAS_PERMISO:
            for coincidencia in re.finditer(re.escape(marca), self.js):
                with self.subTest(marca=marca, posicion=coincidencia.start()):
                    self.assertTrue(
                        inicio_gesto <= coincidencia.start() < fin_gesto,
                        f"{marca!r} aparece fuera de {NOMBRE_GESTO}()",
                    )

        # Criterio 9.12: ninguna guarda del permiso envuelve el parallax de
        # scroll, la flotacion, el giro ni el Arrastre_Rotacion.
        for nombre in (
            NOMBRE_BUCLE,
            NOMBRE_CAPAS,
            NOMBRE_VISTAS,
            "suavizarCursor",
            "indiceArrastre",
            "progresoHero",
        ):
            cuerpo = gen.cuerpo_de_funcion(self.js, nombre)
            self.assertTrue(cuerpo, nombre)
            for marca in MARCAS_PERMISO + ("deviceorientation",):
                with self.subTest(funcion=nombre, marca=marca):
                    self.assertNotIn(marca, cuerpo)

        # Criterio 10.7: la rama que devuelve `will-change` a `auto`.
        self.assertIn("willChange=frio?'auto':'transform'", self.js)

        def prop(presentes: tuple[str, ...]) -> None:
            documento = build_site.html_sitio(presentes=frozenset(presentes))
            bajo = documento.lower()

            # Criterio 13.1: exactamente un `<script>`, propio y sin `src`.
            self.assertEqual(bajo.count("<script"), 1)
            self.assertNotIn("<script src", bajo)

            # Criterio 15.16: la Hoja_Estilo va embebida en un elemento `<style>`
            # y no hay ni un recurso que bloquee el renderizado. El sitio emite
            # dos `<style>`, el de la hoja y el propio del buscador; los dos son
            # embebidos, que es lo que el criterio pide.
            self.assertIn(f"<style>{self.css}</style>", documento)
            self.assertNotIn("<link", bajo)
            self.assertNotIn("@import", bajo)

            # Criterio 10.10: el cuerpo del script no trae ninguna prohibida.
            cuerpo = cuerpo_script(documento).lower()
            for prohibida in PROHIBIDAS_JS:
                with self.subTest(prohibida=prohibida):
                    self.assertNotIn(prohibida, cuerpo)

        for_all(gen.gen_presentes, prop, iteraciones=100, etiqueta=ETQ_P30)


# --------------------------------------------------------------------------- #
# Property 32: pantallas angostas y degradacion que preserva los diagramas
# --------------------------------------------------------------------------- #

ETQ_P32 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 32: Pantallas angostas y degradación que preserva los diagramas"
)


def gen_ancho_ventana(rnd: random.Random) -> int:
    """Ancho de ventana en pixeles, con el corte de 768 forzado por los dos lados.

    Los bordes son los que importan: `corte - 1` tiene que degradar y `corte` no,
    asi que un `<=` mal puesto se cae aqui. El resto reparte anchos reales de
    telefono, de tableta y de escritorio.
    """
    corte: int = mh.CORTE_ANGOSTO_PX
    forma: int = rnd.randrange(5)
    if forma == 0:
        return corte - 1
    if forma == 1:
        return corte
    if forma == 2:
        return rnd.randrange(240, corte)
    if forma == 3:
        return rnd.randrange(corte, 2560)
    return rnd.randrange(240, 2560)


class TestProperty32PantallasAngostas(unittest.TestCase):
    """Property 32: pantallas angostas y degradacion que preserva los diagramas."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _JS_HERO
        cls.css = build_html.estilo_css()
        cls.medias = gen.bloques_media(cls.css)
        cls.marcados = {d.id: sp.svg_diagrama(d) for d in dp.CATALOGO}

    def test_property_32_pantallas_angostas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 32: Pantallas angostas y degradación que preserva los diagramas.

        Para todo ancho de ventana menor que 768 pixeles, el numero de
        Elemento_Fondo activos esta entre 5 y 7 y coincide con el subconjunto
        marcado para pantalla angosta, el desplazamiento por cursor queda omitido,
        el parallax de tres capas con su escala y su desvanecimiento sigue activo,
        y los balones se animan con una rotacion de dos dimensiones; y para todo
        nivel de degradacion por rendimiento, la reduccion afecta unicamente al
        numero de Elemento_Fondo activos y al de Clave_Vista candidatas, mientras
        el contenido grafico de los ocho Diagrama_Postura y sus dimensiones
        declaradas permanecen identicos.

        **Validates: Requirements 10.15, 12.1, 12.2, 12.3, 12.5, 12.6**
        """
        # Criterio 12.2: el desvio por cursor se omite bajo el corte, y la
        # decision vive en la funcion de suavizado, no en el parallax.
        self.assertIn("var mx=angosto?0:curMetaX;", self.js)
        self.assertIn("var my=angosto?0:curMetaY;", self.js)

        # Criterio 12.3: el parallax de tres capas, su escala y su desvanecimiento
        # NO consultan el ancho: la funcion que los escribe ignora `angosto`.
        cuerpo_capas = gen.cuerpo_de_funcion(self.js, NOMBRE_CAPAS)
        self.assertNotIn("angosto", cuerpo_capas)
        self.assertIn("MUNDO.f[i]", cuerpo_capas)
        self.assertIn("MUNDO.e[i]", cuerpo_capas)
        self.assertIn("MUNDO.z[i]", cuerpo_capas)

        # Criterios 12.6 y 26.10: bajo el corte los balones giran en dos
        # dimensiones, y esa rotacion usa `rotate(` y no `rotate3d(`.
        cuerpo_angosto = "".join(
            cuerpo
            for condicion, cuerpo in self.medias
            if f"max-width:{mh.CORTE_ANGOSTO_REM}" in condicion
        )
        self.assertIn(f".{mh.CLASE_GIRO}{{animation-name:hero-rueda-2d;}}", cuerpo_angosto)
        self.assertIn(
            "@keyframes hero-rueda-2d{from{transform:rotate(0deg);}", self.css
        )

        # Criterio 12.5: la degradacion no toca ni el marcado ni las clases de los
        # Diagrama_Postura. El Script_Unico no nombra ninguna de sus clases.
        for clase in (dp.CLASE_BLOQUE, dp.CLASE_MARCO, dp.CLASE_PASOS):
            with self.subTest(clase=clase):
                self.assertNotIn(clase, self.js)

        def prop(ancho: int) -> None:
            activos = activos_en_ancho(ancho)
            minimo, maximo = mh.ELEMENTOS_ANGOSTO

            if ancho >= mh.CORTE_ANGOSTO_PX:
                # Por encima del corte no se degrada nada.
                self.assertEqual(len(activos), len(mh.ELEMENTOS))
                return

            # Criterio 12.1: entre 5 y 7 activos, y son EXACTAMENTE los marcados.
            self.assertGreaterEqual(len(activos), minimo)
            self.assertLessEqual(len(activos), maximo)
            self.assertEqual(activos, mh.activos_angostos())

            # Criterios 12.7 y 29.5: los candidatos del Conmutador_Vista se
            # reducen a los seis azimuts de Subconjunto_Azimuts_Movil, y ninguna
            # otra Clave_Vista automatica queda activa.
            for angulo in (0.0, 22.5, 100.0, 200.0, 359.9):
                elegida = vf.CLAVES_VISTA[
                    indice_mas_cercano_js(angulo, angosto=True)
                ]
                with self.subTest(angulo=angulo):
                    self.assertIn(vf.azimut_de(elegida), vf.AZIMUTS_MOVIL)
                    self.assertEqual(
                        elegida, vf.vista_mas_cercana(angulo, movil=True)
                    )

            # Criterios 12.5, 12.8 y 29.6: el contenido grafico de los ocho
            # Diagrama_Postura y sus dimensiones declaradas no cambian.
            for d in dp.CATALOGO:
                with self.subTest(diagrama=d.id):
                    self.assertEqual(self.marcados[d.id], sp.svg_diagrama(d))
                    self.assertEqual(
                        dp.dimensiones(d, dp.MODO_SVG), (d.ancho_svg, d.alto_svg)
                    )
                    self.assertEqual(
                        dp.dimensiones(d, dp.MODO_ARCHIVO),
                        (d.ancho_archivo, d.alto_archivo),
                    )

        for_all(gen_ancho_ventana, prop, iteraciones=100, etiqueta=ETQ_P32)


# --------------------------------------------------------------------------- #
# Property 48: higiene del Conmutador_Vista en el Script_Unico
# --------------------------------------------------------------------------- #

ETQ_P48 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 48: Higiene del Conmutador_Vista en el Script_Unico"
)

#: Presupuesto por fotograma y por Figura_Girable (criterio 29.2).
PRESUPUESTO_FIGURA: dict[str, int] = {
    "transform": 1,
    "opacity": 2,
    "visibility": 2,
}


class TestProperty48HigieneConmutadorVista(unittest.TestCase):
    """Property 48: higiene del Conmutador_Vista en el Script_Unico."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _JS_HERO
        cls.cuerpo_vistas = gen.cuerpo_de_funcion(cls.js, NOMBRE_VISTAS)
        cls.cuerpo_bucle = gen.cuerpo_de_funcion(cls.js, NOMBRE_BUCLE)

    def test_property_48_higiene_del_conmutador_vista(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 48: Higiene del Conmutador_Vista en el Script_Unico.

        Para todo Script_Unico emitido, el codigo no contiene las subcadenas
        `innerHTML`, `outerHTML`, `createElement`, `appendChild`, `removeChild`,
        `insertAdjacentHTML` ni `cloneNode`; las unicas propiedades de estilo que
        escribe sobre las Vista_Figura son `transform`, `opacity` y `visibility`;
        por fotograma y por Figura_Girable hay a lo sumo una asignacion a
        `transform`, dos a `opacity` y dos a `visibility`, y todas ocurren dentro
        de la unica funcion de bucle, que tambien sirve al visor 3D, al Mundo_Hero
        y al Arrastre_Rotacion; mientras la Clave_Vista mas cercana al angulo
        actual no cambia no hay ninguna escritura sobre las Vista_Figura de esa
        figura, y cuando cambia las escrituras alcanzan solo a la vista que sale y
        a la que entra; el codigo contiene exactamente una llamada a
        `requestAnimationFrame`; y el cuerpo de la funcion de bucle no contiene
        `getBoundingClientRect`, `offsetTop` ni `clientHeight`.

        **Validates: Requirements 10.3, 25.8, 25.9, 25.12, 25.13, 29.1, 29.2, 29.3**
        """
        # Criterios 25.12 y 25.13: cero interfaces que creen o destruyan nodos.
        for mutador in MUTADORES_DOM:
            with self.subTest(mutador=mutador):
                self.assertNotIn(mutador, self.js)

        # Criterio 29.2: presupuesto exacto por figura y por fotograma.
        cuenta = cuenta_por_propiedad(self.cuerpo_vistas)
        self.assertEqual(cuenta, PRESUPUESTO_FIGURA)

        # Criterio 25.8: las escrituras alcanzan SOLO la vista que sale y la que
        # entra, y las dos se resuelven por indice, no por busqueda en el DOM.
        self.assertIn("var sale=fg.vistas[fg.activa];", self.cuerpo_vistas)
        self.assertIn("var entra=fg.vistas[idx];", self.cuerpo_vistas)
        receptores = set(
            re.findall(r"([A-Za-z_][A-Za-z0-9_.]*)\.style\.", self.cuerpo_vistas)
        )
        self.assertEqual(receptores, {"sale", "entra"})

        # Criterio 25.9: mientras la clave no cambia no hay ninguna escritura. El
        # `continue` de la igualdad va ANTES de la primera escritura.
        corte = self.cuerpo_vistas.index("if(idx===fg.activa){continue;}")
        self.assertLess(corte, self.cuerpo_vistas.index(".style."))

        # Criterios 29.1 y 10.17: una sola llamada a `requestAnimationFrame`, y el
        # bucle sirve tambien al Conmutador_Vista y al Arrastre_Rotacion.
        self.assertEqual(self.js.count("requestAnimationFrame("), 1)
        self.assertIn(f"{NOMBRE_VISTAS}(t);", self.cuerpo_bucle)
        self.assertIn("indiceArrastre()", self.cuerpo_vistas)

        # Criterio 29.3: ni una lectura de geometria en el bucle.
        for lectura in LECTURAS_PROHIBIDAS:
            with self.subTest(lectura=lectura):
                self.assertNotIn(lectura, self.cuerpo_bucle)
                self.assertNotIn(lectura, self.cuerpo_vistas)

        def prop(secuencia: tuple[float, ...]) -> None:
            if not secuencia:
                return
            activa: str = vf.CLAVE_ACTIVA
            for angulo in secuencia:
                # El algoritmo transcrito del Script_Unico y la fuente de verdad
                # de Python eligen la MISMA Clave_Vista, incluido el desempate al
                # azimut declarado menor (criterios 25.6 y 25.7).
                elegida = vf.CLAVES_VISTA[
                    indice_mas_cercano_js(angulo, angosto=False)
                ]
                self.assertEqual(elegida, vf.vista_mas_cercana(angulo))

                # Criterio 25.10: la Rotacion_Residual vive en [-22.5, +22.5].
                residual = vf.rotacion_residual(angulo, elegida)
                self.assertLessEqual(abs(residual), vf.ROTACION_RESIDUAL_MAX)

                # Las escrituras que el Script_Unico hace en este fotograma se
                # leen del CODIGO EMITIDO, no de una constante: si la clave no
                # cambia solo corre el tramo anterior al `continue`, y si cambia
                # corre el tramo posterior.
                hechas = escrituras_de_conmutacion(
                    self.cuerpo_vistas, cambia=elegida != activa
                )
                if elegida == activa:
                    # Criterio 25.9: cero escrituras sobre las vistas de la figura.
                    self.assertEqual(hechas, {})
                else:
                    # Criterios 25.8 y 29.2: exactamente el presupuesto declarado.
                    self.assertEqual(hechas, PRESUPUESTO_FIGURA)
                    activa = elegida

        for_all(gen.gen_secuencia_angulos, prop, iteraciones=100, etiqueta=ETQ_P48)


def escrituras_de_conmutacion(cuerpo: str, *, cambia: bool) -> dict[str, int]:
    """Escrituras que el Conmutador_Vista emitido hace en un fotograma de una figura.

    Se leen del cuerpo real de `aplicarVistas()`: el `continue` de la igualdad de
    indices parte la funcion en dos. Sin cambio de Clave_Vista solo se ejecuta el
    tramo **anterior** al corte; con cambio, el **posterior**. Contar sobre el
    codigo emitido es lo que hace que la propiedad pueda fallar de verdad: si
    alguien moviera una escritura antes del corte, el mapa del caso "sin cambio"
    deja de estar vacio.
    """
    corte: int = cuerpo.index("if(idx===fg.activa){continue;}")
    tramo: str = cuerpo[:corte] if not cambia else cuerpo[corte:]
    return cuenta_por_propiedad(tramo)


# --------------------------------------------------------------------------- #
# Property 52: Arrastre_Rotacion y ampliacion
# --------------------------------------------------------------------------- #

ETQ_P52 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 52: Arrastre_Rotacion y ampliación"
)

#: Nombres de los tres manejadores del Arrastre_Rotacion.
MANEJADORES_ARRASTRE: tuple[str, ...] = (
    "alTocarVisor",
    "alArrastrar",
    "alSoltarVisor",
)

#: Las UNICAS variables que los manejadores del arrastre tienen permitido tocar:
#: las cuatro coordenadas del puntero (criterio 28.14).
COORDENADAS_ARRASTRE: frozenset[str] = frozenset(
    {"dragX0", "dragY0", "dragX", "dragY"}
)

#: Tolerancia del Giro_Impulso, en segundos (criterio 28.2).
TOLERANCIA_IMPULSO_S: float = 0.1


def gen_arrastre(rnd: random.Random) -> tuple[float, float, int]:
    """Desplazamiento del dedo y ancho de ventana del Arrastre_Rotacion.

    El desplazamiento sale de `gen.gen_desplazamiento_dedo`, que ya trae el
    `(0, 0)` exacto y valores que **saturan** la elevacion en +-60 grados. El
    ancho se anade para cubrir las dos tablas de candidatos: la de los ocho
    azimuts y la de los seis de Subconjunto_Azimuts_Movil.
    """
    dx, dy = gen.gen_desplazamiento_dedo(rnd)
    return (dx, dy, gen_ancho_ventana(rnd))


class TestProperty52ArrastreRotacion(unittest.TestCase):
    """Property 52: Arrastre_Rotacion y ampliacion."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _JS_HERO
        cls.css = build_html.estilo_css()
        cls.sitio = _SITIO
        cls.sin_js = sin_script(cls.sitio)
        cls.cuerpo_vistas = gen.cuerpo_de_funcion(cls.js, NOMBRE_VISTAS)

    def test_property_52_arrastre_rotacion_y_ampliacion(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 52: Arrastre_Rotacion y ampliación.

        Para todo desplazamiento de dedo en los dos ejes, el azimut resultante
        queda en el intervalo semiabierto de 0 a 360 grados y la elevacion
        resultante queda acotada al intervalo cerrado de -60 a +60 grados, las dos
        derivadas del desplazamiento por la constante declarada de grados por
        pixel; cuando el valor absoluto de la elevacion es de 30 grados o mas la
        vista activa es la Vista_Elevacion del signo de esa elevacion, y cuando es
        menor que 30 grados es la Vista_Azimut mas cercana al azimut resultante con
        el mismo desempate de la conmutacion automatica; para todo documento
        emitido, el contenido del Visor_Ampliado declara `touch-action:none`, los
        escuchadores del Arrastre_Rotacion se registran con la opcion
        `{passive:true}` y guardan unicamente las coordenadas del puntero, la
        resolucion de la vista ocurre dentro de la unica funcion de bucle, las
        unicas propiedades escritas son `transform`, `opacity` y `visibility`, el
        numero de nodos del Visor_Ampliado no cambia, cada Visor_Ampliado contiene
        una Zona_Tactil de cierre de 44 pixeles o mas de alto y de ancho, cada
        Diagrama_Postura y cada Figura_Girable ampliable emite una Zona_Tactil de
        ampliacion cuyo destino es el ancla `#<id>-ampliada` que abre su
        Visor_Ampliado con un solo toque tras retirar el elemento `<script>` y sin
        que la Hoja_Estilo declare `position:fixed`, el Giro_Impulso completa una
        vuelta en 1.2 segundos con una tolerancia de 0.1 segundos y al terminar el
        elemento retoma la duracion de vuelta declarada, y bajo la condicion
        Movimiento_Reducido la Vista_Activa de cada Figura_Girable es la de
        Clave_Vista `az-000` con las otras nueve en opacidad 0 y `visibility:hidden`
        mientras el Arrastre_Rotacion conserva su respuesta.

        **Validates: Requirements 11.8, 11.9, 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7, 28.8, 28.9, 28.10, 28.11, 28.12, 28.13, 28.14, 28.15, 28.16, 28.18**
        """
        # Criterio 28.13: `touch-action:none` en el contenido del Visor_Ampliado, y
        # los escuchadores del arrastre son `{passive:true}`.
        acciones = dict(gen.declaraciones(self.css, "touch-action"))
        self.assertEqual(acciones.get(f".{sg.CLASE_VISOR}"), "none")
        for evento in ("touchstart", "touchmove", "touchend", "touchcancel"):
            with self.subTest(evento=evento):
                self.assertIn(
                    f"nodoDrag.addEventListener('{evento}',", self.js
                )
        self.assertIn(("nodoDrag", "touchmove"), escuchadores(self.js))

        # Criterio 28.14: los manejadores guardan SOLO coordenadas del puntero, y
        # la resolucion de la vista ocurre dentro del bucle.
        for manejador in MANEJADORES_ARRASTRE:
            cuerpo = gen.cuerpo_de_funcion(self.js, manejador)
            self.assertTrue(cuerpo, manejador)
            asignadas = set(
                re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=[^=]", cuerpo)
            )
            with self.subTest(manejador=manejador):
                self.assertLessEqual(
                    asignadas - {"ts"},
                    COORDENADAS_ARRASTRE,
                    f"{manejador} toca algo que no es una coordenada: "
                    f"{sorted(asignadas)}",
                )
                self.assertNotIn(".style.", cuerpo)
                self.assertNotIn("indiceArrastre", cuerpo)
        self.assertIn("indiceArrastre()", self.cuerpo_vistas)

        # Criterio 28.15: solo `transform`, `opacity` y `visibility` sobre las
        # vistas, y cero interfaces que muevan nodos del Visor_Ampliado.
        self.assertEqual(
            set(cuenta_por_propiedad(self.cuerpo_vistas)),
            set(PRESUPUESTO_FIGURA),
        )
        for mutador in MUTADORES_DOM:
            with self.subTest(mutador=mutador):
                self.assertNotIn(mutador, self.js)

        # Criterios 28.2 y 28.3: el Giro_Impulso dura 1.2 s con 0.1 s de tolerancia
        # y al terminar se retoma la duracion de vuelta declarada.
        self.assertLessEqual(
            abs(vf.GIRO_IMPULSO_MS / 1000.0 - 1.2), TOLERANCIA_IMPULSO_S
        )
        self.assertIn("var per=datos[1]*1000;", self.js)
        self.assertIn(
            "if(fila===impFig&&(t-impT0)<MUNDO.girarMs){per=MUNDO.girarMs;}",
            self.js,
        )

        # Criterios 11.8, 11.9 y 28.18: con Movimiento_Reducido el giro automatico
        # se detiene, queda visible `az-000` y el arrastre sigue respondiendo.
        self.assertIn("if(reducido&&!arr){continue;}", self.cuerpo_vistas)
        cuerpo_reducido = next(
            cuerpo
            for condicion, cuerpo in gen.bloques_media(self.css)
            if condicion == "(prefers-reduced-motion: reduce)"
        )
        self.assertIn(f".{vf.CLASE_VISTA}{{opacity:0;visibility:hidden;}}", cuerpo_reducido)
        self.assertIn(
            f'.{vf.CLASE_VISTA}[data-vista="{vf.CLAVE_ACTIVA}"]'
            "{opacity:1;visibility:visible;}",
            cuerpo_reducido,
        )

        # Criterios 28.4, 28.5, 28.6 y 28.16: una Zona_Tactil por diagrama, su
        # Visor_Ampliado con ancla propia y cierre de 44 px, todo sin `<script>`.
        #
        # QUE CAMBIO Y POR QUE: la clausula "sin `position:fixed`" era global. El
        # Visor_Ampliado es ahora un overlay modal y el criterio 28.5 acota la
        # prohibicion: `position:fixed` aparece exactamente una vez y es la del
        # overlay. Cualquier otra sigue siendo un fallo.
        self.assertEqual(self.css.count("position:fixed"), 1)
        posiciones = dict(gen.declaraciones(self.css, "position"))
        self.assertEqual(posiciones.get(f".{sg.CLASE_VISOR}"), "fixed")
        cierres = dict(gen.declaraciones(self.css, "min-height"))
        self.assertEqual(
            cierres.get(f".{sg.CLASE_CERRAR}"), f"{build_html.LADO_TOQUE_PX}px"
        )
        self.assertGreaterEqual(build_html.LADO_TOQUE_PX, 44)
        anchos = dict(gen.declaraciones(self.css, "min-width"))
        self.assertEqual(
            anchos.get(f".{sg.CLASE_CERRAR}"), f"{build_html.LADO_TOQUE_PX}px"
        )
        self.assertNotIn("<script", self.sin_js.lower())
        for d in dp.CATALOGO:
            ancla = sp.ancla_ampliacion(d.id)
            with self.subTest(diagrama=d.id):
                self.assertIn(f'href="#{ancla}"', self.sin_js)
                self.assertIn(f'id="{ancla}"', self.sin_js)
                self.assertIn(f'class="{sg.CLASE_TACTIL} {sg.CLASE_CERRAR}"', self.sin_js)
        # La unica entrada Girable lleva sus diez Vista_Figura en el visor; las
        # otras siete solo su vista frontal, asi que no admiten arrastre (22.5).
        girables = [d for d in dp.CATALOGO if d.girable]
        self.assertEqual([d.id for d in girables], ["anatomia-base"])

        def prop(caso: tuple[float, float, int]) -> None:
            dx, dy, ancho = caso
            angosto: bool = ancho < mh.CORTE_ANGOSTO_PX
            clave, azimut, elevacion = clave_arrastre(dx, dy, angosto=angosto)
            tope: int = max(vf.ELEVACIONES_DECLARADAS)

            # Criterio 28.9: el azimut vive en el semiabierto [0, 360).
            self.assertGreaterEqual(azimut, 0.0)
            self.assertLess(azimut, 360.0)

            # Criterio 28.10: la elevacion queda ACOTADA al cerrado [-60, +60].
            self.assertGreaterEqual(elevacion, -float(tope))
            self.assertLessEqual(elevacion, float(tope))

            # Los dos vienen del desplazamiento por la constante declarada.
            self.assertAlmostEqual(
                azimut, (dx * vf.GRADOS_POR_PIXEL) % 360.0, places=9
            )

            self.assertIn(clave, vf.CLAVES_VISTA)
            if abs(elevacion) >= vf.UMBRAL_ELEVACION:
                # Criterio 28.11: gana la Vista_Elevacion del signo.
                signo: int = tope if elevacion > 0 else -tope
                self.assertEqual(clave, clave_de_elevacion(signo))
                self.assertEqual(vf.elevacion_de(clave), signo)
            else:
                # Criterio 28.12: la Vista_Azimut mas cercana, con el MISMO
                # desempate de la conmutacion automatica.
                self.assertEqual(
                    clave, vf.vista_mas_cercana(azimut, movil=angosto)
                )
                self.assertEqual(vf.elevacion_de(clave), 0)
                if angosto:
                    self.assertIn(vf.azimut_de(clave), vf.AZIMUTS_MOVIL)

        for_all(gen_arrastre, prop, iteraciones=100, etiqueta=ETQ_P52)


if __name__ == "__main__":
    unittest.main()
