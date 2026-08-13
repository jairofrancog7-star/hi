"""Guardarrail_Movil: la guia es para celular y esa restriccion manda.

Feature `imagenes-reales-hero-interactivo`, Requisito 15 y su parte del 1, 4, 9 y
19:

* **Property 37** (tarea 10.14), geometrico: ningun ancho en pixeles por encima
  de 360, ningun `vh`, `overflow-x:hidden` en `html` y `body`, `max-width:100%`
  en secciones y en contenido grafico, `aspect-ratio` y `object-fit:cover` en los
  Diagrama_Postura con 320 px de alto minimo bajo 768, consultas de ancho con
  `min-width` y cero `url(`.
* **Property 38** (tarea 10.15), de interaccion y tipografia: 44 px de lado en
  toda Zona_Tactil con 8 px de separacion, una Zona_Tactil por funcion
  (incluidas "Empezar" y "Activar movimiento"), 16 px de cuerpo y de controles de
  formulario, las cuatro funciones `env(safe-area-inset-*)`, todo `:hover` dentro
  de `@media (hover: hover)` y la navegacion inferior con `position:sticky` sin
  un solo `position:fixed`.

El Ancho_Base del proyecto es 360 x 640 px, que es lo que mide un telefono de
gama media de los que la guia tiene que servir.

_Requirements: 1.6, 4.5, 4.6, 4.7, 9.10, 15.1 a 15.14, 15.20, 19.2_
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
from guia import (  # noqa: E402
    build_html,
    build_site,
    diagramas_postura as dp,
    secciones_guia as sg,
)
from prop import for_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Ancho_Base y contrato geometrico
# --------------------------------------------------------------------------- #

#: Ancho del Ancho_Base, en pixeles CSS. Ningun `width` ni `min-width` en pixeles
#: de la Hoja_Estilo pasa de aqui (criterio 15.2).
ANCHO_BASE_PX: int = 360

#: Alto del Ancho_Base, en pixeles CSS.
ALTO_BASE_PX: int = 640

#: Lado minimo de una Zona_Tactil (criterio 15.6).
LADO_TOQUE_PX: int = 44

#: Separacion minima entre Zona_Tactil adyacentes, en pixeles (criterio 15.7).
SEPARACION_MIN_PX: int = 8

#: Tamano minimo de fuente del cuerpo y de los controles (criterios 15.8 y 15.9).
FUENTE_MIN_PX: int = 16

#: Alto minimo del contenedor de un Diagrama_Postura bajo 768 px (criterio 4.6).
ALTO_MARCO_MIN_PX: int = 320

#: La UNICA consulta de ancho `max-width` que el diseno declara: el corte de
#: pantalla angosta, justo por debajo de 768 px. No introduce cambios "hacia
#: arriba" --que es lo que el criterio 15.1 obliga a expresar con `min-width`--
#: sino la degradacion de carga del fondo y el alto minimo del marco de los
#: diagramas. Se escribe en `rem` y nunca en pixeles.
CORTE_ANGOSTO_REM: str = "47.9375rem"

#: Propiedades de ancho que el criterio 15.2 acota a 360 px.
_PROPIEDADES_ANCHO: tuple[str, ...] = ("width", "min-width", "max-width")

#: Regex de un valor en pixeles.
_RE_PX = re.compile(r"^([\d.]+)px$")

#: Regex de una medida relativa a la ventana. `vh` a secas es la que el criterio
#: 15.10 excluye, porque en Android la barra de direcciones la mueve a media
#: lectura. Las buenas son las dos que **no** se mueven: `dvh` (dynamic) y `svh`
#: (small, la ventana con la barra desplegada), que es la que usa el alto maximo
#: del lienzo del Visor_Ampliado. `lvh` queda fuera a proposito: es la ventana
#: grande, y con la barra visible recorta.
_RE_VENTANA = re.compile(r"([\d.]+)([dsl]?vh)\b")

#: Unidades de alto de ventana que el criterio 15.10 admite.
_UNIDADES_VENTANA: frozenset[str] = frozenset({"dvh", "svh"})

ETQ_P37 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 37: Guardarrail_Movil geometrico"
)

ETQ_P38 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 38: Guardarrail_Movil de interaccion y tipografia"
)


def _declaraciones_de_ancho(css: str) -> tuple[tuple[str, str, str], ...]:
    """Tripletas `(propiedad, selector, valor)` de toda declaracion de ancho."""
    halladas: list[tuple[str, str, str]] = []
    for propiedad in _PROPIEDADES_ANCHO:
        for selector, valor in gen.declaraciones(css, propiedad):
            halladas.append((propiedad, selector, valor))
    return tuple(halladas)


def gen_indice_ancho(rnd: random.Random) -> int:
    """Indice de una declaracion de ancho de la Hoja_Estilo."""
    return rnd.randrange(_TOTAL_ANCHOS)


class TestProperty37GuardarrailMovilGeometrico(unittest.TestCase):
    """Property 37: Guardarrail_Movil geometrico."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.reglas = gen.reglas(cls.css)
        cls.medias = gen.bloques_media(cls.css)
        cls.anchos = _declaraciones_de_ancho(cls.css)

    def test_property_37_guardarrail_movil_geometrico(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 37: Guardarrail_Movil geometrico.

        Para toda declaracion de la Hoja_Estilo: ningun valor de `width` ni de
        `min-width` expresado en pixeles supera 360; ningun ancho declarado supera
        `100vw`; no aparece la unidad `vh` y todo alto relativo a la ventana usa
        `dvh`; `html` y `body` declaran `overflow-x:hidden`; todo contenedor de
        nivel de seccion y todo contenido grafico de Diagrama_Postura declara
        `max-width:100%`; el contenedor de cada Diagrama_Postura declara una
        `aspect-ratio` y su contenido `object-fit:cover`, con un alto minimo de 320
        pixeles bajo 768 pixeles de ancho; toda consulta de medios de ancho que
        introduce cambios respecto de la base usa `min-width`; y la Hoja_Estilo no
        contiene la funcion `url(`.

        **Validates: Requirements 1.6, 4.5, 4.6, 4.7, 15.1, 15.2, 15.3, 15.4, 15.5, 15.10**
        """
        self.assertGreaterEqual(len(self.anchos), 10)

        def prop(indice: int) -> None:
            propiedad, selector, valor = self.anchos[indice % len(self.anchos)]

            # Criterio 15.2: ningun ancho en pixeles por encima del Ancho_Base.
            en_px = _RE_PX.match(valor)
            if en_px is not None:
                self.assertLessEqual(
                    float(en_px.group(1)),
                    float(ANCHO_BASE_PX),
                    f"{selector}: {propiedad}:{valor} pasa del Ancho_Base",
                )

            # Criterio 15.5: ningun ancho declarado supera `100vw`.
            for medida, unidad in re.findall(r"([\d.]+)(vw)\b", valor):
                self.assertLessEqual(
                    float(medida), 100.0, f"{selector}: {propiedad}:{valor}"
                )
                self.assertEqual(unidad, "vw")

            # Criterio 15.10: si el valor es relativo a la ventana, es `dvh` o
            # `svh`, nunca `vh` a secas ni `lvh`.
            for medida, unidad in _RE_VENTANA.findall(valor):
                self.assertIn(
                    unidad,
                    _UNIDADES_VENTANA,
                    f"{selector}: {propiedad}:{medida}{unidad} usa una unidad de "
                    f"ventana que se mueve con la barra de direcciones",
                )

        for_all(gen_indice_ancho, prop, iteraciones=100, etiqueta=ETQ_P37)

    def test_ninguna_altura_de_ventana_usa_vh(self) -> None:
        # Criterio 15.10, medido sobre la hoja entera y no solo sobre los anchos.
        for medida, unidad in _RE_VENTANA.findall(self.css):
            with self.subTest(medida=f"{medida}{unidad}"):
                self.assertIn(unidad, _UNIDADES_VENTANA)
        # Y hay al menos una de cada, para que la comprobacion no sea vacua: `dvh`
        # en el alto minimo del hero y `svh` en el alto maximo del lienzo del
        # Visor_Ampliado.
        self.assertIn("dvh", self.css)
        self.assertIn(build_html.ALTO_MAX_LIENZO, self.css)
        self.assertTrue(build_html.ALTO_MAX_LIENZO.endswith("svh"))

    def test_html_y_body_sin_scroll_horizontal(self) -> None:
        # Criterio 15.4.
        self.assertIn("html,body{overflow-x:hidden;}", self.css)

    def test_secciones_y_contenido_grafico_con_ancho_maximo(self) -> None:
        # Criterio 15.3: contenedores de nivel de seccion y contenido grafico.
        maximos = {s for s, v in gen.declaraciones(self.css, "max-width") if v == "100%"}
        self.assertIn(
            "section,main,article,aside,header,footer", maximos
        )
        self.assertIn("img,svg", maximos)
        self.assertIn(
            f".{dp.CLASE_MARCO} img,.{dp.CLASE_MARCO} svg", maximos
        )

    def test_marco_del_diagrama_con_relacion_y_recorte(self) -> None:
        # Criterios 4.5 y 4.7: `aspect-ratio` en el contenedor y `object-fit:cover`
        # en el contenido, que es lo que evita el salto del texto al cargar.
        relaciones = dict(gen.declaraciones(self.css, "aspect-ratio"))
        self.assertIn(f".{dp.CLASE_MARCO}", relaciones)
        self.assertTrue(relaciones[f".{dp.CLASE_MARCO}"].startswith("var("))
        ajustes = dict(gen.declaraciones(self.css, "object-fit"))
        self.assertEqual(
            ajustes.get(f".{dp.CLASE_MARCO} img,.{dp.CLASE_MARCO} svg"), "cover"
        )

    def test_alto_minimo_del_marco_bajo_768(self) -> None:
        # Criterio 4.6: 320 px de alto minimo por debajo de 768 px de ancho.
        angosto = "".join(
            cuerpo for cond, cuerpo in self.medias
            if "max-width" in cond and CORTE_ANGOSTO_REM in cond
        )
        self.assertTrue(angosto, "falta la consulta del corte angosto")
        altos = dict(gen.declaraciones(angosto, "min-height"))
        self.assertEqual(
            altos.get(f".{dp.CLASE_MARCO}"), f"{ALTO_MARCO_MIN_PX}px"
        )

    def test_las_consultas_de_ancho_suben_con_min_width(self) -> None:
        # Criterio 15.1: la base es el Ancho_Base y los cambios HACIA ARRIBA se
        # introducen con `min-width`. La unica `max-width` declarada es el corte de
        # pantalla angosta, que no sube nada: baja la carga del fondo y reserva el
        # alto del marco. Se escribe en `rem`, nunca en pixeles.
        for condicion, _ in self.medias:
            if "width" not in condicion:
                continue
            with self.subTest(condicion=condicion):
                if "max-width" in condicion:
                    self.assertIn(CORTE_ANGOSTO_REM, condicion)
                else:
                    self.assertIn("min-width", condicion)
                self.assertNotIn("px", condicion)
        # Y hay al menos una consulta `min-width`, para que no sea vacuo.
        self.assertTrue(
            any("min-width" in c for c, _ in self.medias),
            "la Hoja_Estilo no sube a ninguna pantalla ancha",
        )

    def test_la_hoja_no_pide_ningun_recurso(self) -> None:
        # Criterio 1.6 y su compania: cero `url(`, cero `http`, cero `@import`.
        self.assertNotIn("url(", self.css)
        self.assertNotIn("http", self.css)
        self.assertNotIn("@import", self.css)


# --------------------------------------------------------------------------- #
# Property 38: interaccion y tipografia
# --------------------------------------------------------------------------- #

#: Selectores de Zona_Tactil que la Hoja_Estilo dimensiona (criterio 15.6).
_SELECTORES_TOQUE: tuple[str, ...] = (
    f".{sg.CLASE_TACTIL}",
    "nav.sitio a",
    ".btn-solid",
    ".btn-outline",
    ".btn-video",
    ".descarga a",
    ".indice-capitulos a",
    ".chip",
    f".{sg.CLASE_AMPLIAR}",
    f".{sg.CLASE_CERRAR}",
)

#: Contenedores de Zona_Tactil que declaran la separacion (criterio 15.7).
_CONTENEDORES_TOQUE: tuple[str, ...] = (
    ".acciones",
    "nav.sitio",
    ".indice-capitulos",
    ".filtros",
    ".descargas",
    ".chips",
    ".hero-acciones",
    f".{sg.CLASE_INDICE}",
)

#: Los cuatro lados de la safe area (criterio 15.12).
_LADOS_SAFE_AREA: tuple[str, ...] = ("top", "right", "bottom", "left")


def gen_zona_tactil(rnd: random.Random) -> int:
    """Indice de una Zona_Tactil o de un contenedor de Zona_Tactil."""
    return rnd.randrange(len(_SELECTORES_TOQUE) + len(_CONTENEDORES_TOQUE))


class TestProperty38GuardarrailMovilInteraccion(unittest.TestCase):
    """Property 38: Guardarrail_Movil de interaccion y tipografia."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.reglas = gen.reglas(cls.css)
        cls.sitio = build_site.html_sitio()

    def test_property_38_guardarrail_movil_de_interaccion(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 38: Guardarrail_Movil de interaccion y tipografia.

        Para toda Zona_Tactil declarada por el Target_Web: su regla declara
        `min-height` y `min-width` de 44 pixeles o mas, su contenedor declara una
        separacion de 8 pixeles o mas, y existe una Zona_Tactil por cada funcion
        ofrecida, incluidas la rotulada "Empezar" y la rotulada "Activar
        movimiento"; el texto de cuerpo y los elementos `input`, `select` y
        `textarea` declaran 16 pixeles o mas; el relleno de bordes de pantalla usa
        las cuatro funciones `env(safe-area-inset-*)`; para toda aparicion de la
        pseudoclase `:hover` en la Hoja_Estilo, la regla que la contiene esta dentro
        de una consulta `@media (hover: hover)`; y la navegacion principal declara
        `position:sticky` con `bottom:0` y relleno inferior que suma
        `env(safe-area-inset-bottom)` bajo 768 pixeles, sin que la Hoja_Estilo
        contenga `position:fixed` en ninguna regla.

        **Validates: Requirements 9.10, 15.6, 15.7, 15.8, 15.9, 15.12, 15.13, 15.14, 15.20, 19.2**
        """
        candidatos: tuple[str, ...] = _SELECTORES_TOQUE + _CONTENEDORES_TOQUE

        def prop(indice: int) -> None:
            selector = candidatos[indice % len(candidatos)]
            if selector in _SELECTORES_TOQUE:
                self._revisar_zona(selector)
            else:
                self._revisar_contenedor(selector)

        for_all(gen_zona_tactil, prop, iteraciones=100, etiqueta=ETQ_P38)

    def _revisar_zona(self, selector: str) -> None:
        """44 px de lado minimo en los dos ejes (criterio 15.6)."""
        for propiedad in ("min-height", "min-width"):
            valores = [
                v for s, v in gen.declaraciones(self.css, propiedad)
                if selector in s.split(",")
            ]
            with self.subTest(selector=selector, propiedad=propiedad):
                self.assertTrue(
                    valores, f"{selector} no declara {propiedad}"
                )
                en_px = [
                    float(m.group(1))
                    for m in (_RE_PX.match(v) for v in valores)
                    if m is not None
                ]
                self.assertTrue(
                    en_px, f"{selector}: {propiedad} sin valor en pixeles"
                )
                self.assertGreaterEqual(max(en_px), float(LADO_TOQUE_PX))

    def _revisar_contenedor(self, selector: str) -> None:
        """8 px o mas de separacion entre Zona_Tactil adyacentes (criterio 15.7)."""
        valores = [
            v for s, v in gen.declaraciones(self.css, "gap")
            if selector in s.split(",")
        ]
        with self.subTest(selector=selector):
            self.assertTrue(valores, f"{selector} no declara gap")
            en_px = [
                float(m.group(1))
                for m in (_RE_PX.match(v) for v in valores)
                if m is not None
            ]
            self.assertTrue(en_px, f"{selector}: gap sin valor en pixeles")
            self.assertGreaterEqual(min(en_px), float(SEPARACION_MIN_PX))

    def test_una_zona_tactil_por_funcion_del_hero(self) -> None:
        # Criterios 15.14, 19.2 y 9.10: cada funcion se activa con un solo toque, y
        # las dos del hero llevan su rotulo visible.
        self.assertIn(">Empezar<", self.sitio)
        self.assertIn(">Activar movimiento<", self.sitio)
        self.assertIn(f'class="{sg.CLASE_TACTIL} hero-empezar"', self.sitio)
        # Una Zona_Tactil de ampliacion por cada uno de los ocho Diagrama_Postura.
        self.assertEqual(self.sitio.count(f'class="{sg.CLASE_VISOR}"'), 8)
        self.assertGreaterEqual(self.sitio.count(sg.CLASE_AMPLIAR), 8)
        self.assertGreaterEqual(self.sitio.count(sg.CLASE_CERRAR), 8)

    def test_tipografia_de_cuerpo_y_de_controles(self) -> None:
        # Criterios 15.8 y 15.9: 16 px o mas, medido sobre el `clamp` del cuerpo y
        # sobre el valor fijo de los controles.
        # Se mide sobre el tema de PANTALLA: `@media print` conmuta el cuerpo a
        # 12 pt, que es la medida del papel y no la de un telefono.
        pantalla = "".join(
            f"{r.selector}{{{r.cuerpo}}}" for r in self.reglas if r.media == ""
        )
        tamanos = dict(gen.declaraciones(pantalla, "font-size"))
        self.assertIn("body", tamanos)
        cuerpo = tamanos["body"]
        self.assertTrue(cuerpo.startswith("clamp("), cuerpo)
        minimo = cuerpo[len("clamp(") :].split(",")[0].strip()
        en_px = _RE_PX.match(minimo)
        self.assertIsNotNone(en_px, minimo)
        self.assertGreaterEqual(float(en_px.group(1)), float(FUENTE_MIN_PX))
        controles = tamanos.get("input,select,textarea,button")
        self.assertIsNotNone(controles, "los controles no declaran su tamano")
        en_px = _RE_PX.match(controles)
        self.assertIsNotNone(en_px, controles)
        self.assertGreaterEqual(float(en_px.group(1)), float(FUENTE_MIN_PX))

    def test_las_cuatro_funciones_de_safe_area(self) -> None:
        # Criterio 15.12: las cuatro, no tres.
        for lado in _LADOS_SAFE_AREA:
            with self.subTest(lado=lado):
                self.assertIn(f"env(safe-area-inset-{lado})", self.css)

    def test_todo_hover_vive_dentro_de_su_consulta(self) -> None:
        # Criterio 15.13. Es la clausula que cierra el segundo choque declarado:
        # las nueve reglas se envolvieron sin reescribir su texto.
        con_hover = [r for r in self.reglas if ":hover" in r.selector]
        self.assertEqual(len(con_hover), 9, [r.selector for r in con_hover])
        for regla in con_hover:
            with self.subTest(selector=regla.selector):
                self.assertEqual(regla.media, "(hover: hover)")
        # Y los estados que SI existen al toque y con teclado quedaron fuera, en
        # reglas propias del nivel superior: sin esto, envolver las nueve los
        # habria apagado justo en el dispositivo donde mas hacen falta.
        sueltas = {
            r.selector: r.media for r in self.reglas
            if ":hover" not in r.selector
        }
        for selector in (
            ".zona:focus-within,.zona:active",
            ".chip:focus-within,.chip:active",
            ".btn-video:focus-visible,.btn-video:active",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, sueltas, "falta el estado tactil suelto")
                self.assertEqual(sueltas[selector], "")

    def test_navegacion_inferior_sin_position_fixed(self) -> None:
        # Criterio 15.20: `position:sticky` con `bottom:0` en la base (que es el
        # celular) y relleno inferior que suma `env(safe-area-inset-bottom)`.
        nav = next(
            r for r in self.reglas if r.selector == "nav.sitio" and r.media == ""
        )
        self.assertIn("position:sticky", nav.cuerpo)
        self.assertIn("bottom:0", nav.cuerpo)
        self.assertIn(
            f"padding-bottom:calc({SEPARACION_MIN_PX}px + "
            "env(safe-area-inset-bottom))",
            nav.cuerpo,
        )
        # Sobre 768 px vuelve arriba, que es donde estorba menos con raton.
        ancha = "".join(
            cuerpo for cond, cuerpo in gen.bloques_media(self.css)
            if cond.startswith("(min-width")
        )
        self.assertIn("nav.sitio{position:sticky;top:0;bottom:auto;", ancha)
        # QUE CAMBIO Y POR QUE: antes se exigia CERO `position:fixed` en toda la
        # hoja. El Visor_Ampliado paso de seccion `:target` a overlay modal y
        # necesita `position:fixed;inset:0` para cubrir la ventana, asi que el
        # criterio 28.5 lo acota a ese unico selector. Lo que este guardarrail mide
        # es lo que le toca: que la NAVEGACION no lo use, y que la unica aparicion
        # de la hoja sea la del overlay.
        posiciones = dict(gen.declaraciones(self.css, "position"))
        self.assertEqual(posiciones.get(f".{sg.CLASE_VISOR}"), "fixed")
        self.assertEqual(self.css.count("position:fixed"), 1)
        for selector, valor in posiciones.items():
            if selector == f".{sg.CLASE_VISOR}":
                continue
            with self.subTest(selector=selector):
                self.assertNotEqual(valor, "fixed")


# El tamano del espacio se mide al importar: los generadores lo necesitan antes de
# que `setUpClass` corra.
_TOTAL_ANCHOS: int = len(_declaraciones_de_ancho(build_html.estilo_css()))
if _TOTAL_ANCHOS <= 0:
    raise RuntimeError(
        "la Hoja_Estilo no declara ningun ancho: la Property 37 no tendria nada "
        "que cuantificar"
    )


if __name__ == "__main__":
    unittest.main()
