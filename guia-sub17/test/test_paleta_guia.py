"""Pruebas de la Paleta_Guia: tokens, unicidad de constantes y contraste.

Feature `imagenes-reales-hero-interactivo`, cimientos del Requisito 16:

* **Property 35** (tarea 1.4): los siete tokens de la Paleta_Guia existen con su
  valor declarado, cada color se declara con **un solo** literal de Python, el
  mapa de constantes a colores es inyectivo y los tokens del tema oscuro
  (`WEB_FONDO`, `WEB_FONDO_PROFUNDO`, `WEB_AZUL_CLARO`) conservan su valor.
* **Property 34** (tarea 1.5): la funcion de contraste es simetrica y vive en
  `[1, 21]`, y todo par `(texto, fondo, clase)` que declara la Hoja_Estilo
  —incluidos los del Modo_Oscuro— alcanza su umbral.
* **Property 36** (tarea 10.13): las reglas de uso del color en la Hoja_Estilo.
  Todo color de texto de cuerpo es `--azul-profundo`, todo fondo de seccion y de
  tarjeta sale del conjunto de tres, ningun texto es blanco, el rosa y el coral
  aparecen donde les toca, toda sombra usa `rgba(11,44,77,0.12)`, el Modo_Oscuro
  declara sus dos colores y `#7EC8FF` solo pinta el filo del visor 3D.

_Requirements: 6.3, 6.4, 6.5, 6.6, 16.1 a 16.18_
"""

from __future__ import annotations

import inspect
import os
import random
import sys
import unittest

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path
# por su cuenta (convencion del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
from guia import build_html, paleta  # noqa: E402
from prop import for_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Tabla congelada del criterio 16.1: token CSS -> (valor, constante canonica)
# --------------------------------------------------------------------------- #

_ESPERADOS: dict[str, tuple[str, str]] = {
    "--azul-cielo": ("#DCEEFF", "WEB_HERO_CIELO"),
    "--azul-medio": ("#B8DCFA", "WEB_HERO_MEDIO"),
    "--azul-profundo": ("#0B2C4D", "WEB_HERO_TINTA"),
    "--azul-linea": ("#1E6FA8", "WEB_HERO_LINEA"),
    "--rosa-acento": ("#E85D9B", "WEB_HERO_ROSA"),
    "--coral-alerta": ("#D92D20", "WEB_HERO_CORAL"),
    "--blanco-suave": ("#F7FBFF", "WEB_HERO_BLANCO"),
}

# Tokens del tema oscuro que el criterio 16.17 congela.
_CONSERVADOS: dict[str, str] = {
    "WEB_FONDO": "#0A0A0F",
    "WEB_FONDO_PROFUNDO": "#050508",
    "WEB_AZUL_CLARO": "#7EC8FF",
}

_TOKENS: tuple[str, ...] = tuple(_ESPERADOS)
_FUENTE_PALETA: str = inspect.getsource(paleta)


def _literales(valor: str) -> int:
    """Cuenta las veces que `valor` aparece como literal de string en la paleta.

    Cuenta las dos formas de literal que admite el estilo del proyecto (comilla
    doble y comilla simple), de modo que un segundo literal del mismo color se
    detecte aunque cambie de comilla.
    """
    return _FUENTE_PALETA.count(f'"{valor}"') + _FUENTE_PALETA.count(f"'{valor}'")


def gen_token(rnd: random.Random) -> str:
    """Token CSS de la Paleta_Guia (uno de los siete del criterio 16.1)."""
    return rnd.choice(_TOKENS)


ETQ_P35 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 35: Tokens de la Paleta_Guia y unicidad de las constantes"
)


class TestProperty35Tokens(unittest.TestCase):
    """Property 35: tokens de la Paleta_Guia y unicidad de las constantes."""

    def test_property_35_tokens_y_unicidad(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 35: Tokens de la Paleta_Guia y unicidad de las constantes.

        Para todo token de la Paleta_Guia existe exactamente una constante de
        Python que lo declara, con el valor del criterio 16.1 y con
        `WEB_HERO_CIELO` y `WEB_HERO_TINTA` como nombres canonicos; ningun color
        tiene dos nombres con literales distintos.
        """

        def prop(token: str) -> None:
            valor_esperado, constante = _ESPERADOS[token]

            # El token existe en el mapa y vale lo que manda el criterio 16.1.
            self.assertIn(token, paleta.PALETA_GUIA)
            self.assertEqual(paleta.PALETA_GUIA[token], valor_esperado)

            # La constante canonica existe, es la del token y es un hex valido.
            self.assertTrue(hasattr(paleta, constante))
            self.assertEqual(getattr(paleta, constante), valor_esperado)
            self.assertRegex(valor_esperado, r"^#[0-9A-Fa-f]{6}$")
            self.assertTrue(paleta.es_color_valido(valor_esperado))

            # Una sola constante de Python declara el color: el literal aparece
            # exactamente una vez en el codigo de la paleta (criterio 16.2).
            self.assertEqual(
                _literales(valor_esperado),
                1,
                f"{token}: el color {valor_esperado} se declara mas de una vez",
            )

            # El token no se cuela en los conservados ni al reves.
            for nombre, congelado in _CONSERVADOS.items():
                self.assertNotEqual(
                    valor_esperado,
                    congelado,
                    f"{token} pisa el token conservado {nombre}",
                )

        for_all(gen_token, prop, iteraciones=100, etiqueta=ETQ_P35)

    def test_exactamente_siete_tokens(self) -> None:
        # Criterio 16.1: la Paleta_Guia es cerrada, ni uno mas ni uno menos.
        self.assertEqual(len(paleta.PALETA_GUIA), 7)
        self.assertEqual(set(paleta.PALETA_GUIA), set(_ESPERADOS))

    def test_mapa_de_constantes_inyectivo(self) -> None:
        # Criterio 16.2: ningun color de la Paleta_Guia tiene dos nombres.
        valores = [paleta.normalizar_hex(v) for v in paleta.PALETA_GUIA.values()]
        self.assertEqual(len(set(valores)), len(valores))
        # El fondo del Modo_Oscuro es un color propio, no un alias de los siete.
        self.assertNotIn(paleta.normalizar_hex(paleta.OSCURO_FONDO), set(valores))

    def test_oscuro_texto_es_alias_de_azul_cielo(self) -> None:
        # Criterio 16.2: `OSCURO_TEXTO` reusa la constante, no un segundo literal.
        self.assertEqual(paleta.OSCURO_TEXTO, paleta.WEB_HERO_CIELO)
        self.assertEqual(_literales(paleta.OSCURO_TEXTO), 1)
        self.assertIn("OSCURO_TEXTO: str = WEB_HERO_CIELO", _FUENTE_PALETA)

    def test_tokens_conservados_intactos(self) -> None:
        # Criterio 16.17: los tokens del tema oscuro no cambian de valor.
        for nombre, valor in _CONSERVADOS.items():
            with self.subTest(token=nombre):
                self.assertEqual(getattr(paleta, nombre), valor)

    def test_sombra_y_fondo_oscuro_declarados(self) -> None:
        # Criterios 16.14 y 16.15.
        self.assertEqual(paleta.SOMBRA_GUIA, "rgba(11,44,77,0.12)")
        self.assertEqual(paleta.OSCURO_FONDO, "#0B1F33")

    def test_los_siete_tokens_llegan_al_css(self) -> None:
        # Cierre de la Property 35: los siete tokens llegan al CSS emitido. La
        # Hoja_Estilo los declara en la tarea 9.2 (`estilo_css()`); hasta
        # entonces esta comprobacion se omite de forma visible en la suite.
        css = build_html.estilo_css()
        if not any(token in css for token in _ESPERADOS):
            self.skipTest(
                "la Hoja_Estilo emite los tokens de la Paleta_Guia en la tarea 9.2"
            )
        for token, (valor, _) in _ESPERADOS.items():
            with self.subTest(token=token):
                self.assertIn(f"{token}:{valor}", css)


# --------------------------------------------------------------------------- #
# Property 34: contraste de todos los pares declarados
# --------------------------------------------------------------------------- #

_HEX_DIGITOS: str = "0123456789ABCDEF"

# Colores con los que se ejercita la funcion de contraste: los de la paleta y
# los extremos, mas hex arbitrarios generados al vuelo.
_COLORES_CONOCIDOS: tuple[str, ...] = (
    "#000000",
    "#FFFFFF",
    *sorted(paleta.COLORES_PALETA),
)


def _hex_arbitrario(rnd: random.Random) -> str:
    """Color hex de seis digitos elegido al azar."""
    digitos = [rnd.choice(_HEX_DIGITOS) for _ in range(6)]
    return "#" + "".join(digitos)


def gen_caso_contraste(rnd: random.Random) -> tuple[str, str, int]:
    """Dos colores validos y el indice de un par declarado por la Hoja_Estilo.

    El generador mezcla colores de la paleta, los extremos negro y blanco y hex
    arbitrarios, de modo que la simetria y el rango `[1, 21]` se ejerciten en
    todo el espacio y no solo sobre los pares del producto.
    """
    def color() -> str:
        if rnd.random() < 0.5:
            return rnd.choice(_COLORES_CONOCIDOS)
        return _hex_arbitrario(rnd)

    indice = rnd.randrange(len(paleta.pares_declarados()))
    return (color(), color(), indice)


ETQ_P34 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 34: Contraste de todos los pares declarados"
)


class TestProperty34Contraste(unittest.TestCase):
    """Property 34: contraste de todos los pares declarados."""

    def test_property_34_contraste_de_los_pares_declarados(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 34: Contraste de todos los pares declarados.

        Para todo par de colores validos la funcion de contraste es simetrica y
        vive en `[1, 21]`; para todo par de texto y fondo declarado por la
        Hoja_Estilo, incluidos los del Modo_Oscuro, el contraste alcanza 4.5 en
        texto de cuerpo y 3.0 en texto grande, icono o trazo; `--rosa-acento`
        nunca pinta texto de cuerpo y `--coral-alerta` como texto de cuerpo solo
        aparece sobre `--blanco-suave`.
        """
        pares = paleta.pares_declarados()

        def prop(caso: tuple[str, str, int]) -> None:
            color_a, color_b, indice = caso

            # Simetria y rango sobre el par arbitrario.
            valor = paleta.contraste(color_a, color_b)
            self.assertEqual(valor, paleta.contraste(color_b, color_a))
            self.assertGreaterEqual(valor, 1.0)
            self.assertLessEqual(valor, 21.0)

            # Par declarado por la Hoja_Estilo: umbral segun su clase.
            texto, fondo, clase = pares[indice % len(pares)]
            self.assertIn(clase, paleta.CLASES_TEXTO)
            umbral = paleta.UMBRAL_CONTRASTE[clase]
            medido = paleta.contraste(texto, fondo)
            self.assertGreaterEqual(
                medido,
                umbral,
                f"texto {texto} sobre fondo {fondo} ({clase}): "
                f"{medido:.3f} < {umbral}",
            )

            # Criterio 16.10: el rosa nunca pinta texto de cuerpo.
            if texto == paleta.WEB_HERO_ROSA:
                self.assertEqual(
                    clase,
                    "grande",
                    "--rosa-acento solo pinta texto grande, iconos y trazos",
                )

            # Criterio 16.13: el coral como texto de cuerpo va sobre blanco.
            if texto == paleta.WEB_HERO_CORAL and clase == "cuerpo":
                self.assertEqual(
                    fondo,
                    paleta.WEB_HERO_BLANCO,
                    "el texto de error en --coral-alerta va sobre --blanco-suave",
                )

            # Criterio 6.4: la tinta contra los tres fondos claros.
            for claro in (
                paleta.WEB_HERO_CIELO,
                paleta.WEB_HERO_MEDIO,
                paleta.WEB_HERO_BLANCO,
            ):
                self.assertGreaterEqual(
                    paleta.contraste(paleta.WEB_HERO_TINTA, claro), 4.5
                )

        for_all(gen_caso_contraste, prop, iteraciones=100, etiqueta=ETQ_P34)

    def test_extremos_de_la_funcion_de_contraste(self) -> None:
        # El maximo lo da el par negro/blanco; el minimo, un color contra si mismo.
        self.assertAlmostEqual(paleta.contraste("#000000", "#FFFFFF"), 21.0, places=9)
        self.assertAlmostEqual(paleta.contraste("#1E6FA8", "#1E6FA8"), 1.0, places=9)
        self.assertAlmostEqual(paleta.luminancia_relativa("#000"), 0.0, places=9)
        self.assertAlmostEqual(paleta.luminancia_relativa("#FFFFFF"), 1.0, places=9)

    def test_hex_invalido_se_reporta_con_valueerror(self) -> None:
        # Sin `assert` en produccion: un color ilegible es un ValueError.
        for malo in ("azul", "#12", "#GGGGGG", ""):
            with self.subTest(color=malo):
                with self.assertRaises(ValueError):
                    paleta.luminancia_relativa(malo)

    def test_los_pares_declarados_cubren_el_modo_oscuro(self) -> None:
        # Criterio 16.16: el bloque de Modo_Oscuro tambien declara sus pares.
        oscuros = [
            (t, f, c) for t, f, c in paleta.pares_declarados() if f == paleta.OSCURO_FONDO
        ]
        self.assertGreaterEqual(len(oscuros), 1)
        self.assertIn(
            (paleta.OSCURO_TEXTO, paleta.OSCURO_FONDO, "cuerpo"),
            paleta.pares_declarados(),
        )

    def test_los_pares_declarados_estan_bien_formados(self) -> None:
        for texto, fondo, clase in paleta.pares_declarados():
            with self.subTest(texto=texto, fondo=fondo):
                self.assertTrue(paleta.es_color_valido(texto))
                self.assertTrue(paleta.es_color_valido(fondo))
                self.assertIn(clase, paleta.CLASES_TEXTO)


# --------------------------------------------------------------------------- #
# Property 36: reglas de uso del color en la Hoja_Estilo
# --------------------------------------------------------------------------- #
#
# ALCANCE, dicho sin rodeos. El Requisito 16 gobierna el TEMA DE PANTALLA del
# Target_Web. La Hoja_Estilo lleva ademas dos temas que no son ese y que estan
# congelados por pruebas vigentes:
#
# * `@media print` conmuta al tema CLARO de alto contraste del papel (`#FFF8FB`
#   de fondo, `#111111` de tinta, `#E5197F` en titulos), y
#   `test_build_html::test_css_media_print_es_claro` afirma esas cadenas.
# * `@media (prefers-color-scheme: dark)` declara el fondo `#0B1F33` y el texto
#   `#DCEEFF` porque el criterio 16.15 lo EXIGE con esos literales, que no son
#   tokens de los siete.
#
# Las clausulas de color de cuerpo y de fondo se miden por tanto sobre el tema de
# pantalla, y los dos bloques de modo tienen su propia clausula. Lo que si se mide
# sobre la hoja ENTERA, sin excepcion ninguna, es lo prohibido: ningun texto
# blanco en ninguna parte y ninguna sombra que no sea `rgba(11,44,77,0.12)`.

#: Los tres fondos que el criterio 16.4 permite en seccion y en tarjeta.
_FONDOS_PERMITIDOS: frozenset[str] = frozenset(
    {"var(--azul-cielo)", "var(--azul-medio)", "var(--blanco-suave)"}
)

#: Selectores de seccion y de tarjeta del Target_Web. Es la lista explicita del
#: contrato: un fondo de pagina, las tarjetas de contenido, las bandas y los
#: contenedores con marco. No entra ningun `::before` ni ningun adorno de unos
#: pocos pixeles, que son elementos graficos y no tarjetas.
_SELECTORES_TARJETA: tuple[str, ...] = (
    "body",
    ".hero",
    ".hero-ui",
    "figure",
    ".scroll-x",
    ".zona",
    ".chip",
    ".indice-capitulos a",
    ".descarga",
    "nav.sitio",
    "th",
    ".diagrama-postura",
    ".diagrama-marco",
    # QUE CAMBIO Y POR QUE: antes la superficie del Visor_Ampliado era
    # `.visor-ampliado:target`, la seccion que crecia con el selector `:target`.
    # Ahora el visor es un overlay modal y su superficie de lectura son dos
    # elementos: la barra superior y el cuerpo desplazable. El velo del overlay no
    # entra en esta lista porque no es una tarjeta: es un `color-mix` de
    # `--fondo-modal` con transparente, que es un elemento grafico.
    ".visor-barra",
    ".visor-cuerpo",
)

#: Formas de escribir el blanco que el criterio 16.6 excluye como color de texto,
#: y el criterio 16.5 como fondo de seccion y de tarjeta.
_BLANCOS: tuple[str, ...] = ("#fff", "#ffffff", "white", "var(--blanco-suave)")

#: Selectores que el criterio 16.9 exige pintados con `--rosa-acento`.
_USOS_ROSA: tuple[str, ...] = (
    "h1::after",
    "h2::before",
    ".pasos li::before",
    ".numero-ficha",
    ".diagrama-pasos li::marker",
)

#: Selectores que el criterio 16.12 exige pintados con `--coral-alerta`.
_USOS_CORAL: tuple[str, ...] = (
    ".diagrama-error",
    ".marca-error",
    ".zona-errores .lista-zona li::before",
    ".diagrama-aviso",
)


def _reglas_de_pantalla(css: str) -> str:
    """El CSS del tema de pantalla: sin `@media print` y sin Modo_Oscuro.

    Se reconstruye a partir de las reglas troceadas, conservando las que viven en
    el nivel superior y las de las consultas de ancho y de `hover`, que son el
    mismo tema con otro tamano de pantalla.
    """
    fuera: tuple[str, ...] = ("print", "(prefers-color-scheme: dark)")
    return "".join(
        f"{r.selector}{{{r.cuerpo}}}"
        for r in gen.reglas(css)
        if r.media not in fuera
    )


ETQ_P36 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 36: Reglas de uso del color en la Hoja_Estilo"
)


def gen_declaracion_de_color(rnd: random.Random) -> int:
    """Indice de una declaracion de color del tema de pantalla de la Hoja_Estilo.

    Devolver un entero deja que el shrinker lo reduzca hacia 0, de modo que el
    contraejemplo que se reporta es una sola declaracion `selector -> valor` y no
    los veinte mil bytes de la hoja.
    """
    return rnd.randrange(_TOTAL_COLORES)


class TestProperty36UsoDelColor(unittest.TestCase):
    """Property 36: reglas de uso del color en la Hoja_Estilo."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.pantalla = _reglas_de_pantalla(cls.css)
        cls.colores = gen.declaraciones(cls.pantalla, "color")
        cls.fondos = gen.declaraciones(cls.pantalla, "background")

    def test_property_36_reglas_de_uso_del_color(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 36: Reglas de uso del color en la Hoja_Estilo.

        Para toda declaracion de color de la Hoja_Estilo: todo color de texto de
        cuerpo es `--azul-profundo`, y en el hero el kicker, el titulo de nivel 1,
        el lede y la linea de ayuda tambien; todo fondo de seccion y de tarjeta
        pertenece al conjunto `{--azul-cielo, --azul-medio, --blanco-suave}` y por
        tanto ninguna declara blanco, `#7EC8FF` ni `--rosa-acento` como fondo;
        ningun color de texto es blanco en ninguna parte del documento;
        `--rosa-acento` aparece en la numeracion de pasos, en el subrayado del
        titulo, en la pestana activa y en los iconos de logro; `--coral-alerta`
        aparece en las flechas de los diagramas y en el texto de error; toda sombra
        usa `rgba(11,44,77,0.12)`; el bloque de Modo_Oscuro declara el fondo
        `#0B1F33` y el texto `#DCEEFF`; y `#7EC8FF` aparece unicamente en las
        aristas, los acentos y el halo del visor 3D.

        **Validates: Requirements 6.3, 6.5, 16.3, 16.4, 16.5, 16.6, 16.9, 16.11, 16.12, 16.14, 16.15, 16.18**
        """
        declaradas: tuple[tuple[str, str, str], ...] = tuple(
            ("color", s, v) for s, v in self.colores
        ) + tuple(("background", s, v) for s, v in self.fondos)
        # Si la hoja se quedara sin declaraciones de color la propiedad seria
        # vacuamente cierta: eso tambien es un fallo.
        self.assertGreaterEqual(len(declaradas), 40)

        tokens = frozenset(paleta.PALETA_GUIA)
        permitidos_color = frozenset(f"var({t})" for t in tokens) | {
            "transparent",
            "currentColor",
            "inherit",
        }

        def prop(indice: int) -> None:
            propiedad, selector, valor = declaradas[indice % len(declaradas)]

            # Ningun color de texto es blanco, en ninguna parte (criterio 16.6).
            if propiedad == "color":
                for blanco in _BLANCOS:
                    self.assertNotEqual(
                        valor.lower(),
                        blanco.lower(),
                        f"{selector} pinta texto en blanco ({valor})",
                    )
                # Todo color de texto del tema de pantalla sale de la Paleta_Guia:
                # ninguna regla escribe un hex a mano (criterios 16.3 y 16.6).
                self.assertIn(
                    valor,
                    permitidos_color,
                    f"{selector} usa el color {valor}, ajeno a la Paleta_Guia",
                )

            # Fondo de seccion y de tarjeta: los tres tokens y ninguno mas
            # (criterios 16.4, 16.5 y 16.11).
            if propiedad == "background" and selector in _SELECTORES_TARJETA:
                if valor.startswith("linear-gradient("):
                    # El degradado del hero solo mezcla tokens permitidos.
                    for token in ("--azul-cielo", "--azul-medio"):
                        self.assertIn(token, valor, selector)
                else:
                    self.assertIn(
                        valor,
                        _FONDOS_PERMITIDOS,
                        f"{selector} usa el fondo {valor}, fuera de "
                        f"{sorted(_FONDOS_PERMITIDOS)}",
                    )

                # Ningun fondo de seccion ni de tarjeta declara blanco, el azul
                # saturado del visor ni el rosa de acento (criterios 16.5 y
                # 16.11). El alcance es el que dicen los dos criterios: seccion y
                # tarjeta. Un filete de 3 px o un marcador de lista son elementos
                # GRAFICOS, y ahi el rosa es precisamente lo que el criterio 16.9
                # pide.
                for prohibido in ("#fff", "#ffffff", "white", "#7ec8ff",
                                  "var(--azul)", "var(--rosa-acento)"):
                    self.assertNotIn(
                        prohibido,
                        valor.lower(),
                        f"{selector} usa {prohibido} como fondo de tarjeta",
                    )

        for_all(gen_declaracion_de_color, prop, iteraciones=100, etiqueta=ETQ_P36)

    def test_el_rosa_y_el_coral_aparecen_donde_les_toca(self) -> None:
        # Criterios 16.9 y 16.12: no basta con que el token exista; tiene que
        # pintar los elementos que el requisito nombra. Cada uno lo hace con la
        # propiedad que le corresponde: el numero de ficha y el marcador de la
        # lista con `color`, y los dos filetes de subrayado con `background`,
        # porque son barras de tres pixeles y no letras.
        for selector in _USOS_ROSA:
            with self.subTest(selector=selector):
                self.assertTrue(
                    self._pinta_con(selector, "var(--rosa-acento)"),
                    f"{selector} no usa --rosa-acento",
                )
        for selector in _USOS_CORAL:
            with self.subTest(selector=selector):
                self.assertTrue(
                    self._pinta_con(selector, "var(--coral-alerta)"),
                    f"{selector} no usa --coral-alerta",
                )
        # Criterio 16.13: el texto de error en coral SOLO sobre `--blanco-suave`.
        fondos = dict(self.fondos)
        for selector in (".diagrama-error", ".marca-error"):
            with self.subTest(selector=selector):
                self.assertEqual(fondos.get(selector), "var(--blanco-suave)")

    def _pinta_con(self, selector: str, token: str) -> bool:
        """True si alguna regla que alcanza `selector` declara `token`.

        Compara por inclusion de subcadena en el selector, para que una regla
        agrupada como `.diagrama-pasos li::marker,.diagrama-fases li::marker`
        cuente para las dos listas que pinta.
        """
        for regla in gen.reglas(self.pantalla):
            if selector in regla.selector and token in regla.cuerpo:
                return True
        return False

    def test_toda_sombra_usa_el_color_declarado(self) -> None:
        # Criterio 16.14, medido sobre la hoja ENTERA, modos incluidos.
        sombras = gen.declaraciones(self.css, "box-shadow")
        self.assertTrue(sombras)
        for selector, valor in sombras:
            with self.subTest(selector=selector, valor=valor):
                if valor == "none":
                    continue
                self.assertNotIn("rgba(139", valor)
                self.assertNotIn("rgba(59", valor)
                self.assertNotIn("rgba(126", valor)
                usa_token = "var(--sombra)" in valor or "var(--halo)" in valor
                self.assertTrue(
                    usa_token or paleta.SOMBRA_GUIA in valor,
                    f"{selector}: la sombra {valor} no usa {paleta.SOMBRA_GUIA}",
                )
        self.assertIn(f"--sombra:{paleta.SOMBRA_GUIA}", self.css)
        self.assertIn("--halo:0 0 0 1px var(--sombra)", self.css)

    def test_el_modo_oscuro_declara_sus_dos_colores(self) -> None:
        # Criterio 16.15: fondo `#0B1F33` y texto `#DCEEFF`.
        oscuro = "".join(
            cuerpo for cond, cuerpo in gen.bloques_media(self.css)
            if cond == "(prefers-color-scheme: dark)"
        )
        self.assertTrue(oscuro, "falta el bloque de Modo_Oscuro")
        self.assertIn(f"background:{paleta.OSCURO_FONDO}", oscuro)
        self.assertIn(f"color:{paleta.OSCURO_TEXTO}", oscuro)
        self.assertEqual(paleta.OSCURO_FONDO, "#0B1F33")
        self.assertEqual(paleta.OSCURO_TEXTO, "#DCEEFF")

    def test_el_azul_del_visor_solo_pinta_su_filo(self) -> None:
        # Criterio 16.18: `#7EC8FF` unicamente en las aristas, los acentos y el
        # halo del visor 3D. En la Hoja_Estilo eso es exactamente una regla: el
        # contorno de foco del lienzo del visor.
        usos = [
            r for r in gen.reglas(self.css)
            if "var(--azul)" in r.cuerpo and not r.selector.startswith(":root")
        ]
        self.assertEqual(
            [r.selector for r in usos],
            [".hero-lienzo:focus-visible"],
            "el azul del visor se escapo de las aristas del visor 3D",
        )
        # Y el token sigue declarado con su valor congelado (criterio 16.17).
        self.assertIn(f"--azul:{paleta.WEB_AZUL_CLARO}", self.css)

    def test_el_texto_de_cuerpo_y_el_del_hero_van_en_tinta(self) -> None:
        # Criterios 16.3 y 6.3: el texto de lectura y el del hero, en
        # `--azul-profundo`. Ninguno hereda un color de otro tema.
        colores = dict(self.colores)
        for selector in (
            "body",
            "p,li,dd,dt,td,th,figcaption,blockquote,label,summary",
            ".hero-ui p,.hero-ui h1,.hero-ui .destacado,.hero-ui .hero-lede",
            ".hero-ayuda",
            "h1",
            "h2",
        ):
            with self.subTest(selector=selector):
                self.assertEqual(colores.get(selector), "var(--azul-profundo)")


# El tamano del espacio de declaraciones se mide al importar: el generador lo
# necesita antes de que `setUpClass` corra.
_CSS_INICIAL: str = build_html.estilo_css()
_PANTALLA_INICIAL: str = _reglas_de_pantalla(_CSS_INICIAL)
_TOTAL_COLORES: int = len(gen.declaraciones(_PANTALLA_INICIAL, "color")) + len(
    gen.declaraciones(_PANTALLA_INICIAL, "background")
)
if _TOTAL_COLORES <= 0:
    raise RuntimeError(
        "la Hoja_Estilo no declara ningun color: la Property 36 no tendria nada "
        "que cuantificar"
    )


if __name__ == "__main__":
    unittest.main()
