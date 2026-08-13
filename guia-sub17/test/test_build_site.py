"""Pruebas del Motor del sitio de un solo archivo (`build_site.py`, tarea 19).

Verifican que `escribir_sitio(...)` produce un unico `index.html`
**autocontenido** que cumple el Addendum A (Target_Web, decision C3):

* un solo archivo, sin `<link>` a hojas de estilo externas y sin Recurso_Externo:
  desde la tarea 14.2 el Guardarrail_Recursos ya **no** prohibe `<img>` a ciegas,
  porque el render hibrido de los Diagrama_Postura emite uno por cada
  Archivo_Diagrama presente; lo que exige es que todo `src` sea una ruta relativa
  que el Validador_Rutas de `diagramas_postura` acepte;
* CSS embebido con la paleta oscura CONGELADA (reutiliza `build_html.estilo_css`
  y `paleta`), y `<meta viewport>` para uso en celular;
* diagramas de cancha como SVG inline con `viewBox`;
* las 15 fichas reales del `Catalogo_JSON`, cada una con su ancla `#ficha-<id>`;
* los enlaces de video de cada Media_Item, clicables y con `target="_blank"`,
  acompanados de un codigo QR (SVG de rectangulos).

Se escribe el sitio en un directorio temporal que se limpia al final. Solo
libreria estandar y `unittest`.

_Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 1.10, 1.11, 12.2, 12.4, 14.1,
14.2, 14.3, 14.4, 14.5, 14.6, 30.8, 30.9, 30.11_
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

from guia import build_html, build_site, paleta  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.errores import ErrorAsset  # noqa: E402
from guia.schema_json import cargar_catalogo  # noqa: E402
from lector_recursos import (  # noqa: E402
    ATRIBUTOS_RECURSO,
    CONTEXTOS_HTTP_PERMITIDOS,
    LectorRecursos,
    leer,
)


def _fichas() -> list[dict]:
    return cargar_catalogo(cap10_fundamentos.ruta_catalogo())


def _todas_las_rutas() -> frozenset[str]:
    """Las ocho rutas relativas del Catalogo_Diagramas, como si existieran.

    Sirve para ejercitar el modo de render por archivo sin colocar ni un byte en
    el repositorio: `html_sitio(presentes=...)` acepta cualquier subconjunto.
    """
    return frozenset(dp.ruta_relativa(d) for d in dp.CATALOGO)


class GuardarrailRecursos(unittest.TestCase):
    """Ayudante del Guardarrail_Recursos: mide el marcado **por contexto**.

    Hasta la tarea 14.2 el guardarrail se apoyaba en `assertNotIn("<img", ...)` y
    en `assertNotIn('src="http', ...)`. La primera asercion quedo incoherente con
    el render hibrido de los Diagrama_Postura, que emite un `<img>` por cada
    Archivo_Diagrama presente (criterio 5.3), y la segunda mira una subcadena en
    lugar de un atributo. Las dos se sustituyen por una lectura con `HTMLParser`
    que extrae todos los `src` y los pasa por `diagramas_postura.ruta_aceptable`,
    el Validador_Rutas del Requisito 30.

    Medir por contexto no es un lujo: el Target_Web real trae 348 apariciones de
    la cadena `http`, todas fuera de una peticion de red (147 en el `xmlns` de los
    `<svg>` en linea heredados y 134 en el `href` de los enlaces de video de las
    58 fichas, que son navegacion, no subrecursos). Un conteo global de la
    subcadena no distingue esos casos del `src` remoto que si esta prohibido.

    Las prohibiciones vigentes se conservan tal cual: `<link>` a hoja de estilo,
    `@import`, `src="http` y la subcadena `//` dentro del Script_Unico.
    """

    def afirmar_srcs_aceptables(self, lector: LectorRecursos) -> None:
        """Todo `src` es una ruta relativa que el Validador_Rutas acepta.

        Criterios 1.1, 1.3, 1.4, 1.10 y 1.11: el `src` que empieza por `http://`,
        `https://`, `//` o `/` hace fallar la prueba **nombrando ese `src`**, y el
        veredicto de la extension lo da `EXTENSIONES_PERMITIDAS`, no esta prueba.
        """
        for etiqueta, valor in lector.srcs:
            for prefijo in dp.PREFIJOS_RECHAZADOS:
                self.assertFalse(
                    valor.lower().startswith(prefijo),
                    msg=f"<{etiqueta} src={valor!r}> empieza por {prefijo!r}",
                )
            try:
                aceptada: bool = dp.ruta_aceptable(valor)
            except ErrorAsset as exc:
                self.fail(f"<{etiqueta} src={valor!r}> rechazado: {exc.mensaje}")
            self.assertTrue(aceptada, msg=f"<{etiqueta} src={valor!r}>")

    def afirmar_sin_hoja_externa(self, lector: LectorRecursos, bajo: str) -> None:
        """Cero `<link>`, cero `@import` y cero `src="http` (criterios 1.5, 30.8)."""
        self.assertEqual(lector.etiquetas.get("link", 0), 0)
        self.assertNotIn("<link", bajo)
        self.assertNotIn("@import", bajo)
        self.assertNotIn('src="http', bajo)
        for etiqueta, atributo, valor in lector.recursos:
            self.assertNotIn(
                "http",
                valor.lower(),
                msg=f"<{etiqueta} {atributo}={valor!r}> pide red",
            )

    def afirmar_script_unico_limpio(self, lector: LectorRecursos) -> None:
        """Un solo `<script>`, propio, sin `src=`, sin `http` y sin `//`."""
        self.assertEqual(lector.etiquetas.get("script", 0), 1)
        cuerpo_js: str = "".join(lector.scripts).lower()
        self.assertNotIn("src=", cuerpo_js)
        self.assertNotIn("http", cuerpo_js)
        self.assertNotIn("//", cuerpo_js)

    def afirmar_http_por_contexto(self, lector: LectorRecursos) -> None:
        """La cadena `http` solo vive donde no descarga nada (1.2, 1.8, 30.9).

        En atributos: unicamente en los contextos declarados, nunca en un atributo
        de recurso y nunca dentro del Bloque_Creditos. En texto visible: solo
        dentro del Bloque_Creditos, que es la excepcion del criterio 1.8 y donde
        no hay ningun `<a href>`, o como rotulo de un enlace de navegacion (los
        enlaces de video de las 58 fichas se rotulan con su propia URL, dentro del
        `<a>` y en el `<span class="enlace-visible">` que la imprime para
        teclearla a mano). Un `http` en la prosa suelta si es un fallo.
        """
        for etiqueta, atributo, valor, en_creditos in lector.atributos_http:
            self.assertIn(
                (etiqueta, atributo),
                CONTEXTOS_HTTP_PERMITIDOS,
                msg=f"<{etiqueta} {atributo}={valor[:60]!r}> trae http",
            )
            self.assertNotIn(atributo, ATRIBUTOS_RECURSO, msg=valor[:60])
            self.assertFalse(en_creditos, msg=f"{etiqueta}@{atributo}")
        self.assertEqual(lector.enlaces_en_creditos, 0)
        for texto, en_creditos, es_rotulo in lector.texto_http_ctx:
            self.assertTrue(en_creditos or es_rotulo, msg=texto[:60])

    def afirmar_svg_en_linea(self, lector: LectorRecursos) -> None:
        """Los `<svg>` en linea se aceptan; `<image>` no existe (criterio 1.9).

        El Motor_Sitio, el Generador_SVG, el Proyector_Vistas y el Mundo_Hero
        emiten su dibujo dentro del documento, asi que no provocan ninguna
        peticion de red. Lo que no puede haber es un `<image>`, que si la provoca.
        """
        self.assertGreater(lector.etiquetas.get("svg", 0), 0)
        self.assertEqual(lector.etiquetas.get("image", 0), 0)

    def afirmar_css_sin_red(self, lector: LectorRecursos) -> None:
        """La Hoja_Estilo no carga nada: sin `url(`, sin `http` y sin `@import`.

        Criterios 1.6 y 30.11. Se mide sobre el `<style>` embebido del documento y
        sobre `build_html.estilo_css()`, que es su unica fuente.
        """
        for estilo in lector.estilos:
            self.assertNotIn("url(", estilo)
            self.assertNotIn("http", estilo.lower())
            self.assertNotIn("@import", estilo.lower())
        css: str = build_html.estilo_css()
        self.assertNotIn("url(", css)
        self.assertNotIn("http", css.lower())
        self.assertNotIn("@import", css.lower())

    def afirmar_sin_recursos_externos(self, documento: str) -> None:
        """Las seis comprobaciones del Guardarrail_Recursos sobre un documento."""
        lector: LectorRecursos = leer(documento)
        bajo: str = documento.lower()
        self.afirmar_srcs_aceptables(lector)
        self.afirmar_sin_hoja_externa(lector, bajo)
        self.afirmar_script_unico_limpio(lector)
        self.afirmar_http_por_contexto(lector)
        self.afirmar_svg_en_linea(lector)
        self.afirmar_css_sin_red(lector)


class TestBuildSite(GuardarrailRecursos):
    def test_index_autocontenido_15_fichas_con_qr_y_enlaces(self):
        with tempfile.TemporaryDirectory(prefix="guia_sitio_") as tmp:
            dir_dist = os.path.join(tmp, "dist")
            ruta = build_site.escribir_sitio(dir_dist=dir_dist)

            # Devuelve la ruta del unico index.html y el archivo existe.
            self.assertEqual(ruta, os.path.join(dir_dist, "index.html"))
            self.assertTrue(os.path.isfile(ruta))

            with open(ruta, encoding="utf-8") as manejador:
                html = manejador.read()
            bajo = html.lower()

            # Un solo documento HTML.
            self.assertEqual(bajo.count("<html"), 1)
            self.assertEqual(bajo.count("</html>"), 1)

            # Autocontenido: sin hoja de estilo externa y sin ningun
            # Recurso_Externo. El Guardarrail_Recursos mide por contexto, no por
            # subcadena: todo `src` pasa por el Validador_Rutas, los `<svg>` en
            # linea se aceptan y `http` solo vive donde no descarga nada.
            self.afirmar_sin_recursos_externos(html)
            # Exactamente un <script> propio, embebido (sin atributo src).
            self.assertEqual(bajo.count("<script"), 1)
            self.assertNotIn("<script src", bajo)
            self.assertNotIn("src=", html[html.lower().index("<script") :].split("</script>")[0])

            # CSS embebido con la paleta oscura CONGELADA y meta viewport.
            self.assertIn("<style>", bajo)
            self.assertIn(paleta.WEB_FONDO, html)
            self.assertIn("width=device-width", bajo)

            # Diagramas de cancha como SVG inline con viewBox.
            self.assertIn("<svg", html)
            self.assertIn("viewBox", html)

            # Las 15 fichas reales, cada una con su ancla `#ficha-<id>`.
            fichas = _fichas()
            self.assertEqual(len(fichas), 58)
            for ficha in fichas:
                fid = ficha["id"]
                self.assertIn(f'id="ficha-{fid}"', html)
                self.assertIn(f'href="#ficha-{fid}"', html)  # indice de anclas

            # Enlaces de video/busqueda clicables con target=_blank.
            self.assertIn('target="_blank"', html)
            for ficha in fichas:
                for item in ficha["media"]:
                    self.assertIn(item["url"], html)

        # Al salir del with, el temporal (y el artefacto) se limpia.
        self.assertFalse(os.path.exists(dir_dist))


class TestDegradacionSinJS(unittest.TestCase):
    """Tarea 20.2: mejora progresiva del buscador/filtros del sitio.

    Sin JavaScript (o con el `<script>` retirado), el HTML debe seguir mostrando
    TODAS las fichas: ninguna arranca con `hidden`, el indice de anclas queda
    intacto y el `<script>` es propio y no referencia recursos externos.

    _Requirements: 12.3, 13.5_
    """

    def setUp(self) -> None:
        self.html = build_site.html_sitio()
        self.bajo = self.html.lower()
        self.fichas = _fichas()

    def _sin_script(self) -> str:
        """Devuelve el HTML con el contenido de `<script>...</script>` retirado."""
        inicio = self.bajo.index("<script")
        fin = self.bajo.index("</script>") + len("</script>")
        return self.html[:inicio] + self.html[fin:]

    def test_script_propio_y_unico(self) -> None:
        # Un solo <script>, embebido (sin src), sin librerias ni recursos remotos.
        self.assertEqual(self.bajo.count("<script"), 1)
        cuerpo_js = self.html[self.bajo.index("<script") :]
        cuerpo_js = cuerpo_js[: cuerpo_js.lower().index("</script>")]
        self.assertNotIn("src=", cuerpo_js.lower())
        self.assertNotIn("http://", cuerpo_js.lower())
        self.assertNotIn("https://", cuerpo_js.lower())
        self.assertNotIn("import", cuerpo_js.lower())
        for cdn in ("cdn", "jquery", "unpkg", "googleapis", "//"):
            self.assertNotIn(cdn, cuerpo_js.lower())

    def test_sin_js_todas_las_fichas_visibles(self) -> None:
        html_sin_js = self._sin_script()
        bajo = html_sin_js.lower()

        # Retirado el <script>, no queda nada ejecutable.
        self.assertNotIn("<script", bajo)

        # Ninguna ficha arranca oculta: no hay atributo `hidden` en los articles,
        # asi que sin JS todas se ven.
        for ficha in self.fichas:
            fid = ficha["id"]
            marca = f'id="ficha-{fid}"'
            self.assertIn(marca, html_sin_js)
            article = html_sin_js[html_sin_js.index(marca) :]
            apertura = article[: article.index(">")]
            self.assertNotIn("hidden", apertura.lower())

        # Las 15 fichas siguen presentes con su ancla en el indice.
        self.assertEqual(len(self.fichas), 58)
        for ficha in self.fichas:
            fid = ficha["id"]
            self.assertIn(f'href="#ficha-{fid}"', html_sin_js)

        # Enlaces de cada Media_Item siguen accesibles sin JS.
        for ficha in self.fichas:
            for item in ficha["media"]:
                self.assertIn(item["url"], html_sin_js)

    def test_buscador_presente_pero_inerte_sin_js(self) -> None:
        # Los controles de busqueda/filtro existen en el HTML estatico.
        self.assertIn('type="search"', self.bajo)
        self.assertIn('id="gb-q"', self.bajo)
        self.assertIn('id="gb-cat"', self.bajo)
        self.assertIn('id="gb-niv"', self.bajo)
        # El mensaje "sin resultados" arranca oculto: sin JS nunca se muestra.
        self.assertIn('id="gb-vacio" hidden', self.bajo)


class TestDescargasYBotones(GuardarrailRecursos):
    """Tarea 24: descargas y botones principales del Target_Web.

    El `index.html` incluye los tres enlaces de descarga con rutas RELATIVAS
    (`guia.pdf`, `laminas.pdf`, `ejercicios.json`), dos botones principales en el
    header (`.btn-solid` magenta + `.btn-outline`) y **cero recursos externos**
    (sin `src="http"`, sin `<link>` de hoja de estilo, sin `@import`). Los
    enlaces de video de las fichas (contenido, no recursos) siguen permitidos.

    _Requirements: 13.1, 13.2_
    """

    def setUp(self) -> None:
        self.html = build_site.html_sitio()
        self.bajo = self.html.lower()

    def _sin_script(self) -> str:
        """HTML con el contenido de `<script>...</script>` retirado (sin JS)."""
        inicio = self.bajo.index("<script")
        fin = self.bajo.index("</script>") + len("</script>")
        return self.html[:inicio] + self.html[fin:]

    def test_tres_enlaces_de_descarga_relativos(self) -> None:
        # Los tres artefactos, con rutas relativas (no absolutas ni con http).
        self.assertIn('href="guia.pdf"', self.bajo)
        self.assertIn('href="laminas.pdf"', self.bajo)
        self.assertIn('href="ejercicios.json"', self.bajo)
        # Los PDF se ofrecen con el atributo `download`.
        self.assertIn('href="guia.pdf" download', self.bajo)
        self.assertIn('href="laminas.pdf" download', self.bajo)

    def test_dos_botones_principales_en_el_header(self) -> None:
        # Boton solido (guia) y boton outline (laminas), enlaces relativos.
        self.assertIn('class="btn-solid" href="guia.pdf"', self.bajo)
        self.assertIn('class="btn-outline" href="laminas.pdf"', self.bajo)
        # Los estilos minimos de ambos botones estan en el CSS embebido.
        self.assertIn(".btn-solid", self.bajo)
        self.assertIn(".btn-outline", self.bajo)

    def test_sin_recursos_externos(self) -> None:
        # Ni hoja de estilo externa, ni `src` remoto, ni @import, ni CSS que
        # cargue imagenes. Los `<img>` de Diagrama_Postura si estan permitidos
        # cuando su `src` es una ruta relativa que el Validador_Rutas acepta.
        self.afirmar_sin_recursos_externos(self.html)
        # El unico <script> es propio y embebido (sin atributo src).
        self.assertEqual(self.bajo.count("<script"), 1)
        self.assertNotIn("<script src", self.bajo)

    def test_acceso_al_json_crudo_relativo(self) -> None:
        # El Catalogo_JSON crudo se ofrece con ruta relativa y `download`,
        # sin `http` ni ruta absoluta: se baja del mismo `dist/`.
        self.assertIn('href="ejercicios.json" download', self.bajo)
        self.assertNotIn('href="http', self.bajo.split("ejercicios.json")[0][-64:])

    def test_descargas_funcionan_sin_js(self) -> None:
        # Mejora progresiva: retirado el `<script>`, los tres enlaces de
        # descarga (guia.pdf, laminas.pdf, ejercicios.json crudo) siguen
        # presentes y funcionales, y los dos botones del header persisten.
        html_sin_js = self._sin_script()
        bajo = html_sin_js.lower()

        self.assertNotIn("<script", bajo)

        # Los tres artefactos con ruta relativa siguen enlazados.
        self.assertIn('href="guia.pdf" download', bajo)
        self.assertIn('href="laminas.pdf" download', bajo)
        self.assertIn('href="ejercicios.json" download', bajo)

        # Los dos botones principales del header sobreviven sin JS.
        self.assertIn('class="btn-solid" href="guia.pdf"', bajo)
        self.assertIn('class="btn-outline" href="laminas.pdf"', bajo)

    def test_sin_script_de_terceros(self) -> None:
        # No hay `<script>` de terceros (src remoto, CDN ni modulos remotos).
        self.assertNotIn("<script src", self.bajo)
        cuerpo_js = self.html[self.bajo.index("<script") :]
        cuerpo_js = cuerpo_js[: cuerpo_js.lower().index("</script>")].lower()
        for externo in ("http://", "https://", "//", "cdn", "jquery", "unpkg", "googleapis"):
            self.assertNotIn(externo, cuerpo_js)


class TestPeriodizacionYFuentesEnSitio(GuardarrailRecursos):
    """Tarea 26.3: la periodizacion practica se rinde en el sitio, sin fuentes.

    El `index.html` incluye la seccion de periodizacion (`id="plan-12-semanas"`)
    y NO incluye ninguna seccion de fuentes/bibliografia ni URLs de metodologia.
    Se mantienen los invariantes del Target_Web: exactamente un `<script>` (el
    buscador), sin `<link>` y sin `src="http"`.

    _Requirements: 5.1, 5.5, 5.6, 6.1_
    """

    def setUp(self) -> None:
        self.html = build_site.html_sitio()
        self.bajo = self.html.lower()

    def test_secciones_presentes(self) -> None:
        self.assertIn('id="plan-12-semanas"', self.html)

    def test_sin_fuentes_ni_bibliografia_en_el_sitio(self) -> None:
        # Regla de contenido: la guia solo muestra contenido practico y los
        # enlaces de video utiles de las fichas; nunca fuentes, bibliografia,
        # referencias ni las URLs de metodologia (esas son referencia interna).
        for prohibido in (
            'id="fuentes"',
            "fuentes y referencias",
            "bibliograf",
            "scribd.com",
            "efficientfootball",
            "soccercoachlab",
            "dgb.unam.mx",
            "kingperformanceideology",
            "educacioncontinua.ufd.mx",
            "soccerinteraction",
        ):
            self.assertNotIn(prohibido, self.bajo)

    def test_invariantes_intactos(self) -> None:
        # Exactamente un <script> (el buscador), sin <link> ni src remoto.
        self.assertEqual(self.bajo.count("<script"), 1)
        self.afirmar_sin_recursos_externos(self.html)


class TestGuardarrailRecursosRenderHibrido(GuardarrailRecursos):
    """Tarea 14.2: el Guardarrail_Recursos con los ocho `<img>` del render hibrido.

    El modo de render por archivo no se puede ejercitar con el documento por
    defecto: `assets/img/tecnica/` esta vacio, asi que los ocho Diagrama_Postura
    salen por el Generador_SVG y el documento no trae ni un `<img>`. Aqui se
    inyecta el subconjunto completo de presentes para que el Motor_Sitio emita los
    ocho `<img>`, y se comprueba que el guardarrail los **acepta** por tener una
    ruta relativa bajo `assets/` con una de las Extensiones_Permitidas, y que
    **falla nombrando el `src`** en cuanto uno apunta a la red o a la raiz.

    _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 1.10, 1.11, 30.8, 30.9, 30.11_
    """

    @classmethod
    def setUpClass(cls) -> None:
        # El Target_Web con los ocho Archivo_Diagrama presentes, una sola vez:
        # componerlo cuesta del orden de un decimo de segundo.
        cls.html: str = build_site.html_sitio(presentes=_todas_las_rutas())
        cls.lector: LectorRecursos = leer(cls.html)

    def test_ocho_img_con_ruta_relativa_aceptada(self) -> None:
        # Un `<img>` por entrada del catalogo, todos con `src` bajo `assets/` y
        # todos aceptados por el Validador_Rutas (criterios 1.1, 1.3 y 1.10).
        self.assertEqual(len(self.lector.srcs), len(dp.CATALOGO))
        self.assertEqual(self.lector.etiquetas.get("img", 0), len(dp.CATALOGO))
        esperadas: frozenset[str] = _todas_las_rutas()
        for etiqueta, valor in self.lector.srcs:
            self.assertEqual(etiqueta, "img")
            self.assertIn(valor, esperadas)
            self.assertTrue(valor.startswith("assets/"), msg=valor)
            self.assertIn(os.path.splitext(valor)[1], dp.EXTENSIONES_PERMITIDAS)
        self.afirmar_srcs_aceptables(self.lector)

    def test_sigue_sin_recursos_externos_con_los_ocho_img(self) -> None:
        # Con `<img>` en el documento, el resto del guardarrail no se mueve.
        self.afirmar_sin_recursos_externos(self.html)

    def test_un_src_remoto_o_absoluto_hace_fallar_nombrandolo(self) -> None:
        # Criterio 1.4: los cuatro prefijos rechazados hacen fallar el
        # guardarrail, y el mensaje del fallo **nombra el `src`** culpable.
        for prefijo in dp.PREFIJOS_RECHAZADOS:
            intruso: str = f"{prefijo}ejemplo.invalid/assets/img/tecnica/x.webp"
            documento: str = f'<html><body><img src="{intruso}"></body></html>'
            with self.assertRaises(AssertionError) as ctx:
                self.afirmar_srcs_aceptables(leer(documento))
            self.assertIn(intruso, str(ctx.exception))

    def test_una_extension_ajena_hace_fallar_nombrandola(self) -> None:
        # Criterio 1.11: el conjunto de extensiones aceptadas es exactamente
        # Extensiones_Permitidas, asi que un `.jpg` local tampoco pasa.
        ajena: str = "assets/img/tecnica/anatomia-base.jpg"
        self.assertNotIn(".jpg", dp.EXTENSIONES_PERMITIDAS)
        documento: str = f'<html><body><img src="{ajena}"></body></html>'
        with self.assertRaises(AssertionError) as ctx:
            self.afirmar_srcs_aceptables(leer(documento))
        self.assertIn(".jpg", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
