"""Pruebas de la direccion de arte futurista y la composicion editorial (33.4).

Todo lo que se comprueba aqui es **mecanico**: se mide sobre el artefacto
generado en memoria, no por inspeccion visual.

1. Tokens de neon nuevos (cian, violeta, verde) presentes en `paleta.py` y en el
   CSS, **sin** haber quitado los anteriores (`#FF2E88`, `#F4F4FA`, el fondo).
2. Fondo oscuro profundo pero nunca negro absoluto.
3. Profundidad simulada solo con CSS: `perspective`, `preserve-3d`, `rotateX`,
   `rotateY`, `translateZ`, y cada estado de `hover` con equivalente tactil
   (`:focus-visible` / `:focus-within` / `:active`).
4. Bloque `@media (prefers-reduced-motion: reduce)` que apaga animaciones,
   transiciones y transformaciones.
5. Objetivos tactiles de 44 px y medida de linea de ~65 caracteres.
6. **Cero URLs externas** en todo el HTML generado: ninguna `http(s)` que no sea
   el namespace de SVG o un enlace de video de `media[]` del catalogo.
7. Las **nueve zonas** presentes en cada una de las 58 fichas del sitio.
8. Conteo de ilustraciones de postura renderizadas en los dos destinos web.

_Requirements: 2.4, 2.5, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
"""

from __future__ import annotations

import os
import re
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.dirname(os.path.abspath(__file__))
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402

from guia import build_html, build_site, escena3d, figuras, paleta, zonas  # noqa: E402
from guia import secciones_guia as sg  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402

#: Namespace de SVG: es un identificador, no un recurso que se descargue.
_XMLNS_SVG = "http://www.w3.org/2000/svg"

#: Patrones que delatan un recurso externo real.
_PATRONES_EXTERNOS = (
    'src="http',
    "@import",
    "//cdn",
    "fonts.googleapis",
    "cdnjs",
    "unpkg",
    "jsdelivr",
    '<link rel="stylesheet"',
)


def _fichas() -> list[dict]:
    return cap10_fundamentos.fichas_json()


def _urls_media(fichas: list[dict]) -> set[str]:
    """Todas las URLs declaradas en `media[]` del catalogo."""
    urls: set[str] = set()
    for ficha in fichas:
        for item in ficha.get("media") or []:
            url = item.get("url")
            if url:
                urls.add(str(url))
    return urls


class TestTokensDeNeon(unittest.TestCase):
    """Los tokens nuevos se AÑADEN; los anteriores siguen exactos."""

    def setUp(self) -> None:
        self.css = build_html.estilo_css()

    def test_tokens_nuevos_en_la_paleta(self) -> None:
        for nombre in ("WEB_CIAN", "WEB_VIOLETA", "WEB_VERDE"):
            with self.subTest(token=nombre):
                valor = getattr(paleta, nombre)
                self.assertRegex(valor, r"^#[0-9A-Fa-f]{6}$")
                self.assertTrue(paleta.es_color_valido(valor))
                self.assertIn(nombre.lower(), paleta.PALETA_WEB)

    def test_tokens_anteriores_intactos(self) -> None:
        # `test_build_html` y `test_build_site` afirman estas cadenas exactas.
        self.assertEqual(paleta.WEB_MAGENTA, "#FF2E88")
        self.assertEqual(paleta.WEB_TEXTO, "#F4F4FA")
        self.assertEqual(paleta.WEB_CORAL, "#FF7A59")
        self.assertEqual(paleta.WEB_FONDO, "#0A0A0F")
        for color in (
            paleta.WEB_MAGENTA,
            paleta.WEB_TEXTO,
            paleta.WEB_CORAL,
            paleta.WEB_FONDO,
        ):
            with self.subTest(color=color):
                self.assertIn(color, self.css)

    def test_tokens_nuevos_en_el_css(self) -> None:
        self.assertIn(f"--cian:{paleta.WEB_CIAN}", self.css)
        self.assertIn(f"--violeta:{paleta.WEB_VIOLETA}", self.css)
        self.assertIn(f"--verde:{paleta.WEB_VERDE}", self.css)
        # Y se usan de verdad, no solo se declaran.
        for uso in ("var(--cian)", "var(--violeta)", "var(--verde)"):
            with self.subTest(uso=uso):
                self.assertIn(uso, self.css)

    def test_fondo_oscuro_profundo_pero_no_negro_absoluto(self) -> None:
        r, g, b = paleta.rgb_pdf(paleta.WEB_FONDO)
        self.assertGreater(r + g + b, 0.0, "el fondo no puede ser negro absoluto")
        self.assertLess(max(r, g, b), 0.20, "el fondo debe ser oscuro profundo")


class TestProfundidadSoloCss(unittest.TestCase):
    """Profundidad simulada con CSS, con equivalente tactil y apagable."""

    def setUp(self) -> None:
        self.css = build_html.estilo_css()

    def test_propiedades_de_profundidad(self) -> None:
        for propiedad in (
            "perspective:",
            "transform-style:preserve-3d",
            "rotateX(",
            "rotateY(",
            "translateZ(",
        ):
            with self.subTest(propiedad=propiedad):
                self.assertIn(propiedad, self.css)

    def test_hover_con_equivalente_tactil(self) -> None:
        # El estado elevado de las tarjetas se activa igual sin raton.
        self.assertIn(".zona:hover,.zona:focus-within,.zona:active", self.css)
        self.assertIn(".chip:hover,.chip:focus-within,.chip:active", self.css)
        self.assertIn(".btn-video:hover,.btn-video:focus-visible,.btn-video:active", self.css)

    def test_foco_visible_para_teclado(self) -> None:
        self.assertIn("a:focus-visible", self.css)
        self.assertIn("outline:2px solid var(--cian)", self.css)

    def test_bloque_de_movimiento_reducido_apaga_todo(self) -> None:
        marca = "@media (prefers-reduced-motion: reduce)"
        self.assertIn(marca, self.css)
        inicio = self.css.index(marca)
        bloque = self.css[inicio : self.css.index("@media print")]
        self.assertIn("animation-duration:0.001ms !important", bloque)
        self.assertIn("transition-duration:0.001ms !important", bloque)
        self.assertIn("transform:none !important", bloque)
        self.assertIn("perspective:none", bloque)

    def test_objetivos_tactiles_y_medida_de_linea(self) -> None:
        self.assertIn(f"--toque:{build_html.LADO_TOQUE_PX}px", self.css)
        self.assertEqual(build_html.LADO_TOQUE_PX, 44)
        self.assertIn("min-height:var(--toque)", self.css)
        self.assertIn(f"--medida:{build_html.MEDIDA_MAX_CH}ch", self.css)
        self.assertIn("max-width:var(--medida)", self.css)

    def test_dos_columnas_en_escritorio(self) -> None:
        self.assertIn("@media (min-width: 64rem)", self.css)
        self.assertIn(".ficha-columnas{display:grid", self.css)


class TestSinRecursosExternos(unittest.TestCase):
    """Cero URLs externas en el HTML generado (salvo los videos de `media[]`)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fichas = _fichas()
        cls.permitidas = _urls_media(cls.fichas)
        cls.sitio = build_site.html_sitio()
        cls.docs = build_html.documento_a_html(cap10_fundamentos.paginas())

    def _revisar(self, nombre: str, html: str) -> None:
        bajo = html.lower()
        for patron in _PATRONES_EXTERNOS:
            with self.subTest(archivo=nombre, patron=patron):
                self.assertNotIn(patron, bajo)
        # Toda aparicion de http(s) es el namespace de SVG o una URL de media.
        for hallazgo in re.findall(r"https?://[^\s\"'<>)]+", html):
            limpio = hallazgo.rstrip('",;')
            if limpio == _XMLNS_SVG or limpio in self.permitidas:
                continue
            self.fail(f"{nombre}: URL externa no permitida: {limpio}")

    def test_sitio_de_un_archivo(self) -> None:
        self._revisar("index.html", self.sitio)

    def test_paginas_por_capitulo(self) -> None:
        for nombre, contenido in self.docs.items():
            self._revisar(nombre, contenido)

    def test_css_sin_fuentes_ni_recursos_remotos(self) -> None:
        css = build_html.estilo_css()
        self.assertNotIn("http", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)


class TestNueveZonasPorFicha(unittest.TestCase):
    """Cada ficha del sitio trae las nueve zonas, en orden."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fichas = _fichas()
        cls.sitio = build_site.html_sitio()

    def _articulo(self, fid: str) -> str:
        marca = f'id="ficha-{fid}"'
        inicio = self.sitio.index(marca)
        resto = self.sitio[inicio:]
        fin = resto.find("</article>")
        return resto[: fin if fin > 0 else len(resto)]

    def test_nueve_zonas_declaradas(self) -> None:
        self.assertEqual(len(zonas.ZONAS), 9)

    def test_cada_ficha_trae_las_nueve_zonas_en_orden(self) -> None:
        for ficha in self.fichas:
            fid = ficha["id"]
            articulo = self._articulo(fid)
            posiciones: list[int] = []
            for zona in zonas.ZONAS:
                marca = f'data-zona="{zona}"'
                with self.subTest(ficha=fid, zona=zona):
                    self.assertIn(marca, articulo)
                posiciones.append(articulo.index(marca))
            with self.subTest(ficha=fid):
                self.assertEqual(
                    posiciones,
                    sorted(posiciones),
                    "las zonas deben aparecer en el orden de lectura",
                )

    def test_conteo_global_de_zonas(self) -> None:
        total = len(self.fichas)
        for zona in zonas.ZONAS:
            with self.subTest(zona=zona):
                self.assertEqual(self.sitio.count(f'data-zona="{zona}"'), total)

    def test_rotulos_exactos_de_las_zonas(self) -> None:
        self.assertIn(f"<h3>{zonas.TITULO_HAZLO_ASI}</h3>", self.sitio)
        self.assertIn(f"<h3>{zonas.TITULO_PUNTOS_CLAVE}</h3>", self.sitio)
        self.assertIn(f"<h3>{zonas.TITULO_ERRORES}</h3>", self.sitio)
        self.assertIn(f"<h3>{zonas.TITULO_DOSIS}</h3>", self.sitio)
        self.assertIn(f"<h3>{zonas.TITULO_PROGRESION}</h3>", self.sitio)
        self.assertIn(f"<h3>{zonas.TITULO_MEDICION}</h3>", self.sitio)
        # Titulo y boton EXACTOS de la zona de video (Req 14.6).
        self.assertEqual(zonas.TITULO_VIDEO, "Video de ejemplo")
        self.assertEqual(zonas.ETIQUETA_DEMOSTRACION, "Ver demostracion")
        self.assertEqual(
            self.sitio.count(f"<h3>{zonas.TITULO_VIDEO}</h3>"), len(self.fichas)
        )
        self.assertIn(f">{zonas.ETIQUETA_DEMOSTRACION}</a>", self.sitio)

    def test_qr_visible_con_su_enlace_debajo(self) -> None:
        # Nada importante detras de un hover: la URL se imprime en texto.
        for ficha in self.fichas:
            fid = ficha["id"]
            articulo = self._articulo(fid)
            for item in ficha.get("media") or []:
                with self.subTest(ficha=fid, url=item["url"]):
                    self.assertIn('class="enlace-visible"', articulo)
                    self.assertIn(item["url"], articulo)

    def test_botones_tactiles_de_video(self) -> None:
        self.assertIn('class="btn-video"', self.sitio)


class TestIlustracionRenderizada(unittest.TestCase):
    """La ilustracion de postura se ve en los dos destinos web, y es accesible."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fichas = _fichas()
        cls.con_postura = [f for f in cls.fichas if figuras.para_ficha(f) is not None]
        cls.sitio = build_site.html_sitio()
        cls.docs = build_html.documento_a_html(cap10_fundamentos.paginas())

    def test_veintiuna_fichas_llevan_ilustracion(self) -> None:
        self.assertEqual(len(self.con_postura), 21)

    def test_sitio_de_un_archivo_rinde_las_21(self) -> None:
        self.assertEqual(self.sitio.count('data-postura="1"'), 21)
        for ficha in self.con_postura:
            postura = figuras.para_ficha(ficha)
            with self.subTest(ficha=ficha["id"]):
                self.assertIn(f"<title>{postura.titulo}</title>", self.sitio)

    def test_paginas_por_capitulo_rinden_las_21(self) -> None:
        cap = self.docs["10-fundamentos.html"]
        self.assertEqual(cap.count('data-postura="1"'), 21)

    def test_svg_de_postura_accesible_y_sin_dimensiones_absolutas(self) -> None:
        from guia import viz

        for ficha in self.con_postura:
            svg = viz.render_svg(figuras.para_ficha(ficha))
            apertura = svg[: svg.index(">") + 1]
            with self.subTest(ficha=ficha["id"]):
                self.assertIn('role="img"', apertura)
                self.assertIn("viewBox=", apertura)
                self.assertNotIn(" width=", apertura)
                self.assertNotIn(" height=", apertura)
                self.assertIn("<title>", svg)
                self.assertIn("<desc>", svg)

    def test_texto_alternativo_por_ilustracion(self) -> None:
        for ficha in self.con_postura:
            alternativo = zonas.texto_alternativo(ficha, figuras.para_ficha(ficha))
            with self.subTest(ficha=ficha["id"]):
                self.assertTrue(alternativo.strip())
                self.assertIn(alternativo, self.sitio)

    def test_el_pdf_de_la_guia_coloca_la_ilustracion(self) -> None:
        from guia import build_guia_pdf
        from guia.layout import AREA_Y, TipoElemento

        modelo = build_guia_pdf.modelo()
        self.assertEqual(len(modelo), len(self.fichas))
        con_postura = 0
        for pagina in modelo:
            especies = [
                getattr(getattr(e, "datos", None), "spec", None)
                for e in pagina.elementos
                if e.tipo is TipoElemento.DIAGRAMA
            ]
            if any(
                str(getattr(getattr(s, "clase", None), "value", "")) == "postura"
                for s in especies
            ):
                con_postura += 1
            # Nada se sale por abajo del area imprimible.
            for elemento in pagina.elementos:
                self.assertGreaterEqual(round(elemento.y, 3), AREA_Y - 0.001)
        self.assertEqual(con_postura, 21)


class TestZonasDelCatalogo(unittest.TestCase):
    """El reparto de contenido por zona sale del catalogo, sin inventar nada."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fichas = _fichas()

    def test_hazlo_asi_deja_fuera_progresion_metrica_y_variante(self) -> None:
        for ficha in self.fichas:
            pasos = zonas.pasos_hazlo_asi(ficha)
            with self.subTest(ficha=ficha["id"]):
                self.assertTrue(pasos)
                for paso in pasos:
                    bajo = paso.lower()
                    self.assertFalse(bajo.startswith("progresion"))
                    self.assertFalse(bajo.startswith("metrica de mejora"))
                    self.assertFalse(bajo.startswith("variante"))

    def test_medicion_y_progresion_de_todas_las_fichas(self) -> None:
        for ficha in self.fichas:
            with self.subTest(ficha=ficha["id"]):
                self.assertTrue(zonas.medicion(ficha))
                self.assertTrue(zonas.progresion(ficha))
                self.assertTrue(zonas.dosis_chips(ficha))

    def test_errores_de_la_ilustracion_traen_su_correccion(self) -> None:
        con_figura = [f for f in self.fichas if figuras.para_ficha(f) is not None]
        self.assertEqual(len(con_figura), 21)
        for ficha in con_figura:
            errores = zonas.errores_comunes(ficha, figuras.para_ficha(ficha))
            with self.subTest(ficha=ficha["id"]):
                self.assertTrue(errores)
                self.assertTrue(
                    any(e.lower().startswith("corrige") for e in errores),
                    "el panel de error debe traer su correccion corta",
                )

    def test_puntos_clave_y_errores_no_dicen_lo_mismo(self) -> None:
        for ficha in self.fichas:
            postura = figuras.para_ficha(ficha)
            clave = set(zonas.puntos_clave(ficha, postura))
            errores = set(zonas.errores_comunes(ficha, postura))
            with self.subTest(ficha=ficha["id"]):
                self.assertTrue(clave)
                self.assertTrue(errores)
                self.assertEqual(clave & errores, set())

    def test_ficha_que_no_es_mapeo_es_error_de_api(self) -> None:
        with self.assertRaises(ValueError):
            zonas.pasos_hazlo_asi("no soy una ficha")


# --------------------------------------------------------------------------- #
# LOTE 5 (tarea 34): visor 3D propio, glassmorphism del hero y movil
# --------------------------------------------------------------------------- #


class TestTokenDelVisor(unittest.TestCase):
    """El azul claro del visor sale de `paleta.py` y llega al artefacto."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.sitio = build_site.html_sitio()

    def test_token_azul_claro_valido(self) -> None:
        self.assertRegex(paleta.WEB_AZUL_CLARO, r"^#[0-9A-Fa-f]{6}$")
        self.assertTrue(paleta.es_color_valido(paleta.WEB_AZUL_CLARO))
        self.assertIn("web_azul_claro", paleta.PALETA_WEB)

    def test_token_fondo_profundo_anadido_sin_tocar_el_anterior(self) -> None:
        self.assertRegex(paleta.WEB_FONDO_PROFUNDO, r"^#[0-9A-Fa-f]{6}$")
        self.assertTrue(paleta.es_color_valido(paleta.WEB_FONDO_PROFUNDO))
        self.assertIn("web_fondo_profundo", paleta.PALETA_WEB)
        # El token viejo NO cambia: hay pruebas que afirman esta cadena exacta.
        self.assertEqual(paleta.WEB_FONDO, "#0A0A0F")

    def test_los_tokens_llegan_al_css_y_se_usan(self) -> None:
        self.assertIn(f"--azul:{paleta.WEB_AZUL_CLARO}", self.css)
        self.assertIn(f"--fondo-profundo:{paleta.WEB_FONDO_PROFUNDO}", self.css)
        self.assertIn("var(--azul)", self.css)
        self.assertIn("var(--fondo-profundo)", self.css)

    def test_el_azul_claro_aparece_en_el_sitio(self) -> None:
        # Tanto en el JS del visor como en el SVG de reserva.
        self.assertIn(paleta.WEB_AZUL_CLARO, self.sitio)

    def test_tokens_anteriores_siguen_exactos(self) -> None:
        self.assertEqual(paleta.WEB_MAGENTA, "#FF2E88")
        self.assertEqual(paleta.WEB_TEXTO, "#F4F4FA")
        self.assertEqual(paleta.WEB_CORAL, "#FF7A59")
        self.assertEqual(paleta.WEB_CIAN, "#3BE8F0")
        self.assertEqual(paleta.WEB_VIOLETA, "#8B5CF6")
        self.assertEqual(paleta.WEB_VERDE, "#2EF2A0")


class TestVisorEnElSitio(unittest.TestCase):
    """El visor 3D existe, es propio y respeta el unico `<script>` del sitio."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sitio = build_site.html_sitio()
        cls.bajo = cls.sitio.lower()
        cls.cuerpo_js = cls.sitio[cls.bajo.index("<script") :]
        cls.cuerpo_js = cls.cuerpo_js[: cls.cuerpo_js.lower().index("</script>")]

    def test_exactamente_un_script_sin_src(self) -> None:
        self.assertEqual(self.bajo.count("<script"), 1)
        self.assertNotIn("<script src", self.bajo)
        self.assertNotIn("src=", self.cuerpo_js.lower())

    def test_el_cuerpo_del_js_no_trae_nada_remoto_ni_comentarios_de_linea(
        self,
    ) -> None:
        bajo = self.cuerpo_js.lower()
        for prohibido in (
            "http://",
            "https://",
            "//",
            "cdn",
            "jquery",
            "unpkg",
            "googleapis",
            "jsdelivr",
            "spline",
            "three.",
            "fetch(",
            "import",
        ):
            with self.subTest(prohibido=prohibido):
                self.assertNotIn(prohibido, bajo)

    def test_canvas_accesible(self) -> None:
        self.assertIn("<canvas", self.bajo)
        self.assertEqual(self.bajo.count("<canvas"), 1)
        apertura = self.sitio[self.bajo.index("<canvas") :]
        apertura = apertura[: apertura.index(">") + 1]
        self.assertIn('role="img"', apertura)
        self.assertIn("aria-label=", apertura)
        # La etiqueta describe la escena en espanol de Mexico.
        self.assertIn("jugadora", apertura.lower())

    def test_marcas_tecnicas_del_visor(self) -> None:
        for marca in (
            "requestAnimationFrame",
            "cancelAnimationFrame",
            "devicePixelRatio",
            "setTransform",
            "shadowBlur",
            "shadowColor",
            "performance",
            "getContext",
        ):
            with self.subTest(marca=marca):
                self.assertIn(marca, self.cuerpo_js)

    def test_listeners_con_passive_y_preventdefault_solo_en_pinza(self) -> None:
        self.assertIn("addEventListener", self.cuerpo_js)
        self.assertIn("{passive:true}", self.cuerpo_js)
        self.assertIn("{passive:false}", self.cuerpo_js)
        # QUE CAMBIO Y POR QUE: antes se exigia UN solo `preventDefault` en todo
        # el script, el de la rama de pinza. El rediseño del Visor_Ampliado (de
        # seccion `:target` a overlay modal) anade tres, y los tres cuelgan de
        # `click` o de `keydown`: abrir el overlay sin que el ancla salte, cerrarlo
        # sin que salte y atrapar la tabulacion dentro del dialogo. Lo que la
        # prueba mide ahora es lo que de verdad importa: que ninguno de los cuatro
        # viva fuera de su funcion, y que el unico que cuelga de un `touchmove`
        # siga detras de la comprobacion de dos dedos.
        permitidas = ("alMover", "alAbrirVisor", "alCerrarVisor", "atraparFoco")
        total = 0
        for nombre in permitidas:
            cuerpo = gen.cuerpo_de_funcion(self.cuerpo_js, nombre)
            self.assertTrue(cuerpo, f"{nombre} no existe en el Script_Unico")
            total += cuerpo.count("preventDefault")
        self.assertEqual(self.cuerpo_js.count("preventDefault"), total)
        cuerpo_mover = gen.cuerpo_de_funcion(self.cuerpo_js, "alMover")
        self.assertEqual(cuerpo_mover.count("preventDefault"), 1)
        antes = cuerpo_mover[: cuerpo_mover.index("preventDefault")]
        self.assertIn("ts.length>1", antes)
        # Ninguno de los tres del overlay se registra sobre un evento de toque, asi
        # que el desplazamiento vertical de la pagina nunca pasa por ellos.
        for evento in ("touchstart", "touchmove", "touchend", "touchcancel"):
            for nombre in ("alAbrirVisor", "alCerrarVisor", "atraparFoco"):
                with self.subTest(evento=evento, manejador=nombre):
                    self.assertNotIn(f"'{evento}',{nombre}", self.cuerpo_js)

    def test_respeta_prefers_reduced_motion(self) -> None:
        self.assertIn("matchMedia", self.cuerpo_js)
        self.assertIn("prefers-reduced-motion: reduce", self.cuerpo_js)
        # Bajo movimiento reducido dibuja una vez y no arranca el bucle.
        self.assertIn("if(reducido)", self.cuerpo_js)

    def test_pausa_cuando_no_esta_visible(self) -> None:
        self.assertIn("IntersectionObserver", self.cuerpo_js)
        self.assertIn("document.hidden", self.cuerpo_js)
        self.assertIn("visibilitychange", self.cuerpo_js)

    def test_un_solo_bucle_y_ningun_temporizador(self) -> None:
        self.assertNotIn("setInterval", self.cuerpo_js)
        self.assertNotIn("setTimeout", self.cuerpo_js)
        # Un solo punto de arranque del bucle dentro del propio bucle.
        self.assertEqual(self.cuerpo_js.count("function bucle("), 1)

    def test_la_malla_viaja_como_datos_y_cuadra_con_python(self) -> None:
        # La geometria se genera en Python: el JS solo la proyecta.
        self.assertIn(escena3d.datos_json(), self.cuerpo_js)
        for nombre in escena3d.NOMBRES_GRUPOS:
            with self.subTest(grupo=nombre):
                self.assertIn(f'"{nombre}"', self.cuerpo_js)

    def test_touch_action_no_bloquea_el_scroll_vertical(self) -> None:
        css = build_html.estilo_css()
        self.assertIn("touch-action:pan-y pinch-zoom", css)
        self.assertIn("touch-action:pan-y;", css)
        # El hero NUNCA se queda con el gesto vertical: sus dos capas tactiles
        # declaran `pan-y`, asi que el desplazamiento de la pagina sigue pasando.
        for selector in (".hero-visor{", ".hero-lienzo{"):
            with self.subTest(selector=selector):
                regla = css[css.index(selector) :]
                regla = regla[: regla.index("}") + 1]
                self.assertIn("touch-action:pan-y", regla)
                self.assertNotIn("touch-action:none", regla)
        # `touch-action:none` existe en la Hoja_Estilo, y solo en un sitio: el
        # Visor_Ampliado, donde el criterio 28.13 lo exige para que el
        # Arrastre_Rotacion pueda leer el gesto de la usuaria en los dos ejes.
        # Ese visor no envuelve el documento: es un overlay modal aparte, y
        # mientras esta abierto el `<body>` lleva `overflow:hidden`, asi que no hay
        # scroll detras al que robarle el gesto.
        self.assertEqual(css.count("touch-action:none"), 1)
        antes = css[: css.index("touch-action:none")]
        self.assertTrue(antes.endswith(".visor-ampliado{"), antes[-40:])

    def test_sin_atributos_de_evento_en_el_html(self) -> None:
        for evento in (
            " onclick",
            " onload",
            " onerror",
            " onmouseover",
            " onfocus",
            " ontouchstart",
            " ontouchmove",
            " onpointerdown",
        ):
            with self.subTest(evento=evento):
                self.assertNotIn(evento, self.bajo)


class TestGlassmorphismDelHero(unittest.TestCase):
    """El hero superpone la interfaz de vidrio al modelo, con contraste."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.sitio = build_site.html_sitio()

    def test_capas_del_hero_en_el_marcado(self) -> None:
        for clase in (
            'class="hero"',
            'class="hero-visor"',
            'class="hero-lienzo"',
            'class="hero-reserva"',
            'class="hero-velo"',
            'class="hero-ui"',
            'class="hero-borde"',
        ):
            with self.subTest(clase=clase):
                self.assertIn(clase, self.sitio)

    def test_vidrio_con_prefijo_para_el_webview_de_android(self) -> None:
        bloque = self.css[self.css.index(".hero-ui{") :]
        bloque = bloque[: bloque.index("}") + 1]
        self.assertIn("backdrop-filter:blur(", bloque)
        self.assertIn("-webkit-backdrop-filter:blur(", bloque)

    def test_el_canvas_va_detras_de_la_interfaz_sin_position_fixed(self) -> None:
        self.assertIn(".hero-visor{position:absolute;inset:0;z-index:0", self.css)
        self.assertIn(".hero-ui{position:relative;z-index:2", self.css)
        bloque = self.css[self.css.index(".hero{") : self.css.index("@keyframes hero-giro")]
        self.assertNotIn("position:fixed", bloque)

    def test_capa_de_oscurecimiento_para_el_contraste(self) -> None:
        self.assertIn(".hero-velo{", self.css)
        bloque = self.css[self.css.index(".hero-velo{") :]
        bloque = bloque[: bloque.index("}") + 1]
        self.assertIn("linear-gradient(", bloque)
        self.assertIn("pointer-events:none", bloque)

    def test_bordes_neon_cian_y_violeta(self) -> None:
        self.assertIn("border:1px solid var(--cian)", self.css)
        self.assertIn("border-top:1px solid var(--violeta)", self.css)

    def test_profundidad_y_animacion_solo_con_css(self) -> None:
        self.assertIn("@keyframes hero-giro", self.css)
        self.assertIn("translateZ(26px)", self.css)
        self.assertIn("rotateY(-13deg)", self.css)
        self.assertIn(".hero-visor{position:absolute;inset:0;z-index:0", self.css)
        self.assertIn("perspective:var(--profundidad)", self.css)

    def test_el_hero_no_depende_de_recursos_externos(self) -> None:
        self.assertNotIn("http", self.css)
        self.assertNotIn("@import", self.css)
        self.assertNotIn("url(", self.css)

    def test_movimiento_reducido_apaga_el_hero(self) -> None:
        marca = "@media (prefers-reduced-motion: reduce)"
        bloque = self.css[self.css.index(marca) : self.css.index("@media print")]
        self.assertIn(".hero-visor{perspective:none;}", bloque)
        self.assertIn(".hero-reserva .hero-svg{animation:none !important;}", bloque)


class TestOptimizacionMovil(unittest.TestCase):
    """Viewport exacto, sin zoom bloqueado y sin scroll horizontal fantasma."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = build_html.estilo_css()
        cls.sitio = build_site.html_sitio()
        cls.docs = build_html.documento_a_html(cap10_fundamentos.paginas())

    def test_viewport_exacto_en_los_dos_destinos(self) -> None:
        # Ajuste declarado (tarea 14.1 de `imagenes-reales-hero-interactivo`): el
        # Target_Web pasa a `META_VIEWPORT_SITIO` con `viewport-fit=cover`
        # (criterio 15.11), porque es lo que deja al relleno de
        # `env(safe-area-inset-*)` alcanzar la muesca. Las paginas de capitulo y
        # la publicacion conservan `META_VIEWPORT` sin cambiar un byte.
        # `test_nunca_se_bloquea_el_zoom` no cambia: quitar `maximum-scale`
        # amplia el zoom, no lo bloquea.
        self.assertEqual(
            build_html.META_VIEWPORT,
            "width=device-width, initial-scale=1, maximum-scale=5",
        )
        self.assertEqual(
            build_html.META_VIEWPORT_SITIO,
            "width=device-width, initial-scale=1, viewport-fit=cover",
        )

        esperado_sitio = (
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1, viewport-fit=cover">'
        )
        esperado_capitulo = (
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1, maximum-scale=5">'
        )

        self.assertIn(esperado_sitio, self.sitio)
        self.assertNotIn(esperado_capitulo, self.sitio)
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            with self.subTest(archivo=nombre):
                self.assertIn(esperado_capitulo, contenido)
                self.assertNotIn(esperado_sitio, contenido)

    def test_la_meta_viewport_del_sitio_sale_de_la_constante(self) -> None:
        # Ejemplo declarado (tarea 14.4 de `imagenes-reales-hero-interactivo`,
        # criterio 15.11): la cadena exacta que viaja al Target_Web se compone
        # desde `build_html.META_VIEWPORT_SITIO`, no desde un literal repetido en
        # la prueba. Asi, cambiar la constante y olvidarse del cableado hace
        # fallar esta prueba, no solo la de arriba.
        esperado = (
            f'<meta name="viewport" content="{build_html.META_VIEWPORT_SITIO}">'
        )
        self.assertIn(esperado, self.sitio)
        # Una sola meta viewport en todo el documento: dos se contradicen.
        self.assertEqual(self.sitio.count('name="viewport"'), 1)

    def test_nunca_se_bloquea_el_zoom(self) -> None:
        self.assertNotIn("user-scalable", self.sitio.lower())
        for nombre, contenido in self.docs.items():
            with self.subTest(archivo=nombre):
                self.assertNotIn("user-scalable", contenido.lower())

    def test_sin_scroll_horizontal_fantasma(self) -> None:
        self.assertIn("html,body{overflow-x:hidden;}", self.css)
        self.assertIn("min-width:0", self.css)
        self.assertIn("max-width:100%", self.css)

    def test_ningun_ancho_fijo_mayor_que_el_viewport(self) -> None:
        # Ningun `width:` ni `min-width:` en pixeles por encima de 360.
        for propiedad, valor in re.findall(
            r"(width|min-width):\s*(\d+)px", self.css
        ):
            with self.subTest(regla=f"{propiedad}:{valor}px"):
                self.assertLessEqual(int(valor), 360)


class TestHeroSinJavaScriptEnCapitulos(unittest.TestCase):
    """Las paginas por capitulo llevan el hero, pero NUNCA JavaScript (Req 2.4).

    Desviacion honesta y deliberada: el visor interactivo con canvas, swipe y
    pinch **no** puede vivir aqui. `test_build_html::test_sin_javascript` y
    `::test_html_sin_atributos_de_evento` prohiben cualquier `<script>` y
    cualquier atributo `on*` en estas paginas, y esas pruebas defienden el
    Req 2.4 ("HTML estatico que se muestre completo sin ejecutar JavaScript").
    Lo que si viaja es la MISMA malla proyectada a SVG inline, animada solo con
    CSS. Esas pruebas se dejaron intactas y este codigo se escribio para pasarlas.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.docs = build_html.documento_a_html(cap10_fundamentos.paginas())

    def test_ningun_capitulo_trae_script(self) -> None:
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            with self.subTest(archivo=nombre):
                self.assertNotIn("<script", contenido.lower())
                self.assertNotIn("<canvas", contenido.lower())

    def test_cada_capitulo_trae_el_hero_con_su_svg(self) -> None:
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html") or nombre == "index.html":
                continue
            with self.subTest(archivo=nombre):
                self.assertIn('class="hero"', contenido)
                self.assertIn('class="hero-reserva"', contenido)
                self.assertIn('class="hero-svg"', contenido)
                self.assertIn('role="img"', contenido)
                self.assertIn("<desc>", contenido)

    def test_el_hero_del_capitulo_es_el_mismo_modelo(self) -> None:
        cap = self.docs["10-fundamentos.html"]
        self.assertIn(escena3d.svg_estatico(), cap)


class TestMejoraProgresivaDelHero(unittest.TestCase):
    """Retirado el `<script>`, el hero sigue mostrando su contenido de reserva."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sitio = build_site.html_sitio()
        cls.bajo = cls.sitio.lower()
        cls.fichas = _fichas()

    def _sin_script(self) -> str:
        inicio = self.bajo.index("<script")
        fin = self.bajo.index("</script>") + len("</script>")
        return self.sitio[:inicio] + self.sitio[fin:]

    def test_el_hero_se_ve_sin_js(self) -> None:
        sin_js = self._sin_script()
        self.assertNotIn("<script", sin_js.lower())
        # El dibujo de reserva y su descripcion siguen ahi.
        self.assertIn('class="hero-reserva"', sin_js)
        self.assertIn(escena3d.svg_estatico(), sin_js)
        self.assertIn("<desc>", sin_js)
        # Y el texto del hero no depende de JS.
        self.assertIn('class="hero-ui"', sin_js)
        self.assertIn("<h1>", sin_js)
        self.assertIn('class="hero-ayuda"', sin_js)

    def test_el_canvas_arranca_oculto_para_no_dejar_un_hueco(self) -> None:
        apertura = self.sitio[self.bajo.index("<canvas") :]
        apertura = apertura[: apertura.index(">") + 1]
        self.assertIn("hidden", apertura)
        # El JS es quien lo destapa cuando el visor esta listo de verdad.
        self.assertIn("cv.removeAttribute('hidden')", self.sitio)

    def test_las_58_fichas_y_el_indice_siguen_visibles_sin_js(self) -> None:
        sin_js = self._sin_script()
        self.assertEqual(len(self.fichas), 58)
        for ficha in self.fichas:
            fid = ficha["id"]
            with self.subTest(ficha=fid):
                self.assertIn(f'id="ficha-{fid}"', sin_js)
                self.assertIn(f'href="#ficha-{fid}"', sin_js)

    def test_las_descargas_siguen_sin_js(self) -> None:
        sin_js = self._sin_script().lower()
        self.assertIn('href="guia.pdf" download', sin_js)
        self.assertIn('href="laminas.pdf" download', sin_js)
        self.assertIn('href="ejercicios.json" download', sin_js)


class TestVisor3DPropio(unittest.TestCase):
    """Visor 3D propio con JS vanilla, offline, cero CDN (tarea 34.2/34.3)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sitio = build_site.html_sitio()
        cls.bajo = cls.sitio.lower()
        cls.css = build_html.estilo_css()

    def test_token_azul_claro_valido_y_presente(self) -> None:
        self.assertEqual(paleta.WEB_AZUL_CLARO, "#7EC8FF")
        self.assertTrue(paleta.es_color_valido(paleta.WEB_AZUL_CLARO))
        self.assertIn(paleta.WEB_AZUL_CLARO, self.css)
        self.assertIn(f"--azul:{paleta.WEB_AZUL_CLARO}", self.css)

    def test_token_fondo_profundo_valido_y_presente(self) -> None:
        self.assertEqual(paleta.WEB_FONDO_PROFUNDO, "#050508")
        self.assertTrue(paleta.es_color_valido(paleta.WEB_FONDO_PROFUNDO))
        self.assertIn(paleta.WEB_FONDO_PROFUNDO, self.css)
        self.assertIn(f"--fondo-profundo:{paleta.WEB_FONDO_PROFUNDO}", self.css)

    def test_token_fondo_anterior_intacto(self) -> None:
        # Test_build_html afirma esta cadena exacta; no se toca.
        self.assertEqual(paleta.WEB_FONDO, "#0A0A0F")
        self.assertIn(f"--fondo:{paleta.WEB_FONDO}", self.css)

    def test_exactamente_un_script_sin_src_ni_doble_barra(self) -> None:
        self.assertEqual(self.bajo.count("<script"), 1)
        self.assertNotIn("<script src", self.bajo)
        inicio = self.bajo.index("<script")
        fin = self.bajo.index("</script>") + len("</script>")
        cuerpo_script = self.sitio[inicio:fin]
        # Prohibida la subcadena `//` por test_build_site::test_sin_script_de_terceros
        self.assertNotIn("//", cuerpo_script)

    def test_presencia_de_canvas_con_marcas_de_accesibilidad(self) -> None:
        self.assertIn("<canvas", self.bajo)
        self.assertIn('id="gb-lienzo"', self.bajo)
        self.assertIn('role="img"', self.bajo)
        self.assertIn('aria-label="', self.bajo)
        self.assertIn(escena3d.ETIQUETA_ACCESIBLE.lower(), self.bajo)

    def test_touch_action_en_el_visor(self) -> None:
        self.assertIn("touch-action:pan-y pinch-zoom", self.css)
        self.assertIn('touch-action:pan-y', self.bajo)

    def test_apis_nativas_sin_cdn_ni_terceros(self) -> None:
        cuerpo_script = self.sitio[
            self.bajo.index("<script") : self.bajo.index("</script>") + len("</script>")
        ]
        # Presencia de APIs nativas del navegador (cero librerías)
        self.assertIn("requestAnimationFrame", cuerpo_script)
        self.assertIn("devicePixelRatio", cuerpo_script)
        self.assertIn("matchMedia", cuerpo_script)
        self.assertIn("IntersectionObserver", cuerpo_script)
        self.assertIn("performance.now", cuerpo_script)
        # Prohibidos CDN, import, terceros
        for patron in ("http://", "https://", "cdn", "import ", "require("):
            with self.subTest(patron=patron):
                self.assertNotIn(patron, cuerpo_script)

    def test_listeners_con_passive_y_sin_atributos_on(self) -> None:
        cuerpo_script = self.sitio[
            self.bajo.index("<script") : self.bajo.index("</script>")
        ]
        self.assertIn("{passive:true}", cuerpo_script)
        self.assertIn("{passive:false}", cuerpo_script)
        # Nunca atributos de evento inline
        for atributo in ("onclick", "onload", "onmousemove", "ontouchstart"):
            with self.subTest(atributo=atributo):
                self.assertNotIn(atributo, self.bajo)

    def test_presencia_de_svg_estatico_de_reserva(self) -> None:
        self.assertIn('id="gb-reserva"', self.bajo)
        svg_estatico = escena3d.svg_estatico()
        self.assertIn(svg_estatico, self.sitio)
        self.assertIn('class="hero-svg"', svg_estatico)
        self.assertIn("viewBox", svg_estatico)
        self.assertIn('role="img"', svg_estatico)

    def test_glassmorphism_del_hero(self) -> None:
        self.assertIn('class="hero-ui"', self.bajo)
        self.assertIn("backdrop-filter:blur(18px)", self.css)
        self.assertIn("-webkit-backdrop-filter:blur(18px)", self.css)
        self.assertIn('class="hero-velo"', self.bajo)
        self.assertIn('class="hero-borde"', self.bajo)

    def test_visor_por_z_index_nunca_position_fixed(self) -> None:
        # El visor del hero va DETRÁS por z-index, nunca con position:fixed que
        # pelea con el scroll en el WebView de Android.
        self.assertIn(".hero-visor{position:absolute;inset:0;z-index:0;", self.css)
        self.assertIn(".hero-velo{position:absolute;inset:0;z-index:1;", self.css)
        self.assertIn(".hero-ui{position:relative;z-index:2;", self.css)
        # QUE CAMBIO Y POR QUE: la prohibicion de `position:fixed` era GLOBAL sobre
        # la hoja entera. El rediseño del Visor_Ampliado la necesita para que el
        # overlay modal cubra la ventana, asi que el criterio 28.5 queda acotado:
        # `position:fixed` esta permitido **solo** en el overlay y prohibido en
        # todo lo demas. Se mide por conteo y por posicion, igual que ya se hacia
        # con `touch-action:none`, para que un `position:fixed` nuevo en cualquier
        # otra regla siga siendo un fallo.
        self.assertEqual(self.css.count("position:fixed"), 1)
        antes = self.css[: self.css.index("position:fixed")]
        self.assertTrue(
            antes.endswith(f".{sg.CLASE_VISOR}{{touch-action:none;"),
            antes[-60:],
        )
        # Y ninguna regla del hero ni de la navegacion la declara.
        posiciones = dict(gen.declaraciones(self.css, "position"))
        self.assertEqual(posiciones.get(f".{sg.CLASE_VISOR}"), "fixed")
        for selector, valor in posiciones.items():
            if selector == f".{sg.CLASE_VISOR}":
                continue
            with self.subTest(selector=selector):
                self.assertNotEqual(valor, "fixed")

    def test_movimiento_reducido_apaga_el_visor(self) -> None:
        marca = "@media (prefers-reduced-motion: reduce)"
        bloque = self.css[self.css.index(marca) : self.css.index("@media print")]
        self.assertIn(".hero-visor{perspective:none;}", bloque)


if __name__ == "__main__":
    unittest.main()
