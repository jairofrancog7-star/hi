"""Pruebas del Motor_HTML (`build_html.py`, tarea 7.5).

Verifican que el sitio estático generado cumple lo exigido por el diseño y los
requisitos 2.1, 2.4, 2.5, 2.7 y 9.10:

* HTML estático: sin `<script>` ni atributos de evento `on*`.
* `<meta name="viewport">` con `width=device-width` en cada página.
* Un archivo por capítulo con nombres numéricos y con guiones
  (`00-portada.html` … `80-apendices.html`), más `index.html` y `estilo.css`.
* SVG inline con `viewBox` y `role="img"` (diagramas y QR de rectángulos).
* Tablas anchas envueltas en `div.scroll-x`.
* Texto del catálogo escapado con `html.escape(quote=True)`.
* Banda de descarga del PDF con el tamaño en MB desde `os.stat`.

Se escribe el sitio en un directorio temporal que se limpia al final.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_DIR_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"
)
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_html  # noqa: E402
from guia.diagram_spec import ClaseDiagrama, DiagramaSpec, Item, Mundo  # noqa: E402
from guia.layout import (  # noqa: E402
    ElementoRender,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
)
from guia.plantillas import DiagramaDatos, FilaTablaDatos, QRDatos  # noqa: E402


def _spec_cancha() -> DiagramaSpec:
    """Un diagrama de cancha mínimo pero válido."""
    return DiagramaSpec(
        clase=ClaseDiagrama.CANCHA,
        mundo=Mundo(20.0, 15.0),
        items=(
            Item(tipo="player", x=5.0, y=5.0, numero=7),
            Item(tipo="ball", x=6.0, y=6.0),
        ),
        titulo="Rondo 4 contra 1",
    )


def _modelo_ejemplo() -> list[PaginaRender]:
    """Modelo_Paginas de ejemplo con dos capítulos y varios tipos de elemento."""
    # Capítulo 1: portada con texto que necesita escaparse.
    p0 = PaginaRender(
        folio=1,
        capitulo_id="cap00_portada",
        capitulo_titulo="Portada & guía",
        plantilla=Plantilla.PORTADA,
        elementos=[
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                datos=TextoDatos(
                    texto='Cómo usar <esta> guía & "entrenar"',
                    fuente="Helvetica-Bold",
                    tamano=20.0,
                ),
            ),
            ElementoRender(
                tipo=TipoElemento.PARRAFO,
                datos=TextoDatos(texto="Entrena de martes a jueves."),
            ),
        ],
    )
    # Capítulo 2: fundamentos con diagrama, tabla y QR.
    p1 = PaginaRender(
        folio=2,
        capitulo_id="cap10_fundamentos",
        capitulo_titulo="Fundamentos técnicos",
        plantilla=Plantilla.FICHA,
        elementos=[
            ElementoRender(
                tipo=TipoElemento.DIAGRAMA,
                datos=DiagramaDatos(spec=_spec_cancha(), titulo="Rondo"),
            ),
            ElementoRender(
                tipo=TipoElemento.TABLA,
                datos=FilaTablaDatos(
                    celdas=("Serie", "Repes"),
                    anchos=(50.0, 50.0),
                    es_cabecera=True,
                ),
            ),
            ElementoRender(
                tipo=TipoElemento.TABLA,
                datos=FilaTablaDatos(
                    celdas=("3", "10"),
                    anchos=(50.0, 50.0),
                ),
            ),
            ElementoRender(
                tipo=TipoElemento.QR,
                datos=QRDatos(url="https://example.com/video?a=1&b=2"),
            ),
        ],
    )
    return [p0, p1]


class TestNombreArchivoCapitulo(unittest.TestCase):
    def test_nombres_numericos_con_guiones(self):
        casos = {
            "cap00_portada": "00-portada.html",
            "cap10_fundamentos": "10-fundamentos.html",
            "cap20_pos_portera": "20-posiciones-portera.html",
            "cap30_colectivo": "30-colectivo.html",
            "cap80_apendices": "80-apendices.html",
        }
        for cid, esperado in casos.items():
            with self.subTest(capitulo=cid):
                self.assertEqual(build_html.nombre_archivo_capitulo(cid), esperado)

    def test_id_sin_patron_degrada_a_slug(self):
        nombre = build_html.nombre_archivo_capitulo("intro rara_x")
        self.assertTrue(nombre.endswith(".html"))
        self.assertNotIn("_", nombre)
        self.assertNotIn(" ", nombre)


class TestDocumentoAHtml(unittest.TestCase):
    def setUp(self):
        self.paginas = _modelo_ejemplo()
        self.docs = build_html.documento_a_html(self.paginas)

    def test_incluye_indice_css_y_un_archivo_por_capitulo(self):
        self.assertIn("index.html", self.docs)
        self.assertIn("estilo.css", self.docs)
        self.assertIn("00-portada.html", self.docs)
        self.assertIn("10-fundamentos.html", self.docs)
        # index + css + 2 capítulos.
        self.assertEqual(len(self.docs), 4)

    def test_sin_javascript(self):
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            with self.subTest(archivo=nombre):
                self.assertNotIn("<script", contenido.lower())
                # Ningún atributo de evento on*.
                self.assertNotIn(" onclick", contenido.lower())
                self.assertNotIn(" onload", contenido.lower())

    def test_meta_viewport_en_cada_pagina(self):
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            with self.subTest(archivo=nombre):
                self.assertIn('name="viewport"', contenido)
                self.assertIn("width=device-width", contenido)

    def test_css_responsive_una_columna(self):
        css = self.docs["estilo.css"]
        self.assertIn("clamp(16px, 4.2vw, 19px)", css)
        self.assertIn("max-width:44rem", css)
        self.assertIn("@media print", css)
        self.assertIn("overflow-x:auto", css)

    def test_svg_diagrama_con_viewbox_y_role(self):
        cap = self.docs["10-fundamentos.html"]
        self.assertIn("<svg", cap)
        self.assertIn("viewBox=", cap)
        self.assertIn('role="img"', cap)

    def test_qr_como_svg_de_rectangulos(self):
        cap = self.docs["10-fundamentos.html"]
        self.assertIn('class="qr"', cap)
        self.assertIn("<rect", cap)
        # El QR es SVG, nunca una imagen de mapa de bits.
        self.assertNotIn("<img", cap)

    def test_tabla_en_scroll_x(self):
        cap = self.docs["10-fundamentos.html"]
        self.assertIn('<div class="scroll-x">', cap)
        self.assertIn("<table>", cap)
        self.assertIn("<thead>", cap)
        self.assertIn("<th>Serie</th>", cap)
        self.assertIn("<td>3</td>", cap)

    def test_texto_escapado(self):
        portada = self.docs["00-portada.html"]
        # El texto crudo tiene <, > y &; debe aparecer escapado, nunca crudo.
        self.assertIn("&lt;esta&gt;", portada)
        self.assertIn("&amp;", portada)
        self.assertNotIn("<esta>", portada)
        # La URL del QR con & se escapa como &amp; en el atributo href.
        cap = self.docs["10-fundamentos.html"]
        self.assertIn("a=1&amp;b=2", cap)

    def test_enlace_de_descarga_al_pdf(self):
        index = self.docs["index.html"]
        self.assertIn('href="../Guia_Extensa_Sub17.pdf"', index)
        self.assertIn("download", index)

    def test_paridad_de_ids_de_capitulo(self):
        ids = build_html.ids_capitulos(self.paginas)
        self.assertEqual(ids, ("cap00_portada", "cap10_fundamentos"))

    def test_svg_sin_dimensiones_absolutas(self):
        # El SVG del diagrama fluye al 100% del contenedor, sin width/height fijos.
        cap = self.docs["10-fundamentos.html"]
        self.assertIn("width:100%", cap)
        self.assertNotIn('<svg width=', cap)
        self.assertNotIn('height:auto"' + " width", cap)

    def test_css_declara_variables_de_paleta(self):
        # Tema WEB oscuro: fondo casi negro y acento magenta como variables CSS.
        css = self.docs["estilo.css"]
        self.assertIn("--fondo:#0A0A0F", css)
        self.assertIn("--magenta:#FF2E88", css)
        self.assertIn("--coral:#FF7A59", css)
        self.assertIn("--texto:#F4F4FA", css)

    def test_css_tarjetas_de_vidrio_y_degradados(self):
        # Estética glass: borde fino 1px, desenfoque y degradados de acento.
        css = self.docs["estilo.css"]
        self.assertIn("backdrop-filter:blur", css)
        self.assertIn("1px solid var(--borde)", css)
        self.assertIn("linear-gradient(", css)

    def test_css_font_stack_del_sistema_sin_fuentes_externas(self):
        css = self.docs["estilo.css"]
        self.assertIn("system-ui", css)
        # Nada de fuentes remotas ni @import de URLs.
        self.assertNotIn("@import", css)
        self.assertNotIn("http", css)

    def test_css_microanimaciones_desactivables(self):
        # Animaciones solo CSS y su interruptor de accesibilidad.
        css = self.docs["estilo.css"]
        self.assertIn("@keyframes", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_css_media_print_es_claro(self):
        # Al imprimir se conmuta a la versión CLARA de alto contraste.
        css = self.docs["estilo.css"]
        self.assertIn("@media print", css)
        idx = css.index("@media print")
        bloque_print = css[idx:]
        self.assertIn("#FFF8FB", bloque_print)
        self.assertIn("#111111", bloque_print)

    def test_css_sin_script(self):
        # El propio CSS no introduce nada ejecutable.
        css = self.docs["estilo.css"]
        self.assertNotIn("<script", css.lower())
        self.assertNotIn("javascript:", css.lower())

    def test_html_sin_atributos_de_evento(self):
        # Refuerza que ninguna página emite atributos on* ni <script>.
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            bajo = contenido.lower()
            with self.subTest(archivo=nombre):
                self.assertNotIn("<script", bajo)
                for evento in (" onclick", " onload", " onerror", " onmouseover"):
                    self.assertNotIn(evento, bajo)

    def test_index_navega_a_cada_capitulo(self):
        index = self.docs["index.html"]
        self.assertIn('href="00-portada.html"', index)
        self.assertIn('href="10-fundamentos.html"', index)

    def test_capitulo_marca_data_capitulo(self):
        cap = self.docs["00-portada.html"]
        self.assertIn('data-capitulo="cap00_portada"', cap)


class TestBandaDescargaTamano(unittest.TestCase):
    def test_tamano_en_mb_desde_os_stat(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = os.path.join(tmp, "Guia_Extensa_Sub17.pdf")
            with open(pdf, "wb") as fh:
                fh.write(b"x" * (2 * 1024 * 1024))  # 2 MB exactos
            docs = build_html.documento_a_html(_modelo_ejemplo(), pdf_ruta=pdf)
            self.assertIn("2.0 MB", docs["index.html"])

    def test_tolera_pdf_inexistente(self):
        docs = build_html.documento_a_html(
            _modelo_ejemplo(), pdf_ruta="/no/existe/guia.pdf"
        )
        # La banda de descarga sigue presente, solo sin el tamaño.
        self.assertIn("Descargar el PDF completo", docs["index.html"])
        self.assertNotIn("MB", docs["index.html"])


class TestEscribirHtml(unittest.TestCase):
    def test_escribe_utf8_newline_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "web")
            rutas = build_html.escribir_html(_modelo_ejemplo(), destino)
            nombres = {os.path.basename(r) for r in rutas}
            self.assertIn("index.html", nombres)
            self.assertIn("estilo.css", nombres)
            self.assertIn("00-portada.html", nombres)
            self.assertIn("10-fundamentos.html", nombres)
            # Escritura con newline='\n': sin CRLF en el archivo.
            with open(
                os.path.join(destino, "index.html"), "rb"
            ) as fh:
                crudo = fh.read()
            self.assertNotIn(b"\r\n", crudo)
            # UTF-8: los acentos se decodifican sin error.
            texto = crudo.decode("utf-8")
            self.assertIn("Índice", texto)


if __name__ == "__main__":
    unittest.main()
