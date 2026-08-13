"""Pruebas del ensamblador de la estructura de publicacion (tarea 15.2).

Verifican que `build_publicacion.ensamblar_publicacion(...)` produce un arbol
publicable (para GitHub Pages) completo y autocontenido a partir de los
artefactos de `dist/`:

* estan presentes todos los archivos y carpetas esperados: `index.html`,
  `README.md`, `.nojekyll`, `Guia_Extensa_Sub17.pdf`, `guia/index.html` y al
  menos una `laminas/lamina-NN.svg` (tantas como devuelve el resultado);
* `.nojekyll` existe y esta vacio;
* los enlaces de recursos propios de la landing (`Guia_Extensa_Sub17.pdf` para
  descargar y `guia/index.html` para leer en linea) resuelven a archivos que
  existen bajo `dir_salida`;
* la landing es autocontenida: sin CDN, sin `src="http"` y sin `<link>` a hoja
  de estilo externa (mismo criterio que `test_sin_recursos_externos`);
* el `README.md` contiene la URL de descarga cruda, la URL de Pages y los tres
  conteos del ultimo build (paginas/fichas/laminas);
* cada `lamina-NN.svg` es un SVG bien formado (`<svg` raiz con `xmlns` de SVG y
  `viewBox`).

La corrida se realiza UNA sola vez en un `tempfile.TemporaryDirectory` (con
`dir_salida` y `dir_dist` dentro del temporal) para no tocar los directorios
`publicacion/` ni `dist/` reales del proyecto. Solo libreria estandar y
`unittest`; sin `assert` fuera del framework de test. Deterministico y offline.

_Requirements: 2.6, 2.7_
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from html.parser import HTMLParser

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_publicacion  # noqa: E402


class _RecolectorEnlaces(HTMLParser):
    """Recolecta los `href` de cada `<a>` y detecta `<link>` externos."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.tiene_link: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "link":
            self.tiene_link = True
        if tag == "a":
            for nombre, valor in attrs:
                if nombre == "href" and valor is not None:
                    self.hrefs.append(valor)


class TestEnsamblarPublicacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Una sola corrida, en directorios temporales, para no tocar los
        # `publicacion/` ni `dist/` reales del proyecto.
        cls._tmp = tempfile.TemporaryDirectory(prefix="guia_publicacion_")
        base = cls._tmp.name
        cls.dir_salida = os.path.join(base, "publicacion")
        cls.resultado = build_publicacion.ensamblar_publicacion(
            dir_salida=cls.dir_salida,
            dir_dist=os.path.join(base, "dist"),
        )
        with open(cls.resultado["index_html"], encoding="utf-8") as fh:
            cls.index_html = fh.read()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _laminas_en_disco(self) -> list[str]:
        dir_laminas = os.path.join(self.dir_salida, build_publicacion.NOMBRE_LAMINAS)
        return sorted(
            n
            for n in os.listdir(dir_laminas)
            if n.startswith("lamina-") and n.endswith(".svg")
        )

    # 1. Estructura de archivos y carpetas esperados.
    def test_estructura_de_archivos_presente(self) -> None:
        d = self.dir_salida
        self.assertTrue(os.path.isfile(os.path.join(d, "index.html")))
        self.assertTrue(os.path.isfile(os.path.join(d, "README.md")))
        self.assertTrue(os.path.exists(os.path.join(d, ".nojekyll")))
        self.assertTrue(
            os.path.isfile(
                os.path.join(d, build_publicacion.NOMBRE_PDF_PUBLICADO)
            )
        )
        dir_guia = os.path.join(d, build_publicacion.NOMBRE_GUIA)
        self.assertTrue(os.path.isdir(dir_guia))
        self.assertTrue(os.path.isfile(os.path.join(dir_guia, "index.html")))
        dir_laminas = os.path.join(d, build_publicacion.NOMBRE_LAMINAS)
        self.assertTrue(os.path.isdir(dir_laminas))

        laminas = self._laminas_en_disco()
        self.assertGreater(len(laminas), 0)
        # El numero de SVG en disco coincide con lo reportado.
        self.assertEqual(len(laminas), len(self.resultado["laminas"]))
        self.assertGreater(len(self.resultado["laminas"]), 0)

    # 2. `.nojekyll` presente y vacio.
    def test_nojekyll_vacio(self) -> None:
        ruta = os.path.join(self.dir_salida, ".nojekyll")
        self.assertTrue(os.path.exists(ruta))
        with open(ruta, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "")

    # 3. Enlaces de recursos propios de la landing resuelven a archivos reales.
    def test_enlaces_de_recursos_resuelven(self) -> None:
        recolector = _RecolectorEnlaces()
        recolector.feed(self.index_html)
        hrefs = recolector.hrefs

        href_pdf = build_publicacion.NOMBRE_PDF_PUBLICADO
        href_guia = f"{build_publicacion.NOMBRE_GUIA}/index.html"

        # El boton de descarga apunta al PDF emitido y el de lectura al sitio.
        self.assertIn(href_pdf, hrefs)
        self.assertIn(href_guia, hrefs)

        # Ambos recursos existen como archivos bajo dir_salida.
        self.assertTrue(
            os.path.isfile(os.path.join(self.dir_salida, href_pdf))
        )
        self.assertTrue(
            os.path.isfile(os.path.join(self.dir_salida, href_guia))
        )

    # 4. Landing autocontenida (mismo criterio que test_sin_recursos_externos).
    def test_landing_autocontenida(self) -> None:
        bajo = self.index_html.lower()
        self.assertNotIn("https://cdn", bajo)
        self.assertNotIn('src="http', bajo)
        self.assertNotIn("<link ", bajo)

    # 5. README con URLs y los tres conteos del ultimo build.
    def test_readme_urls_y_conteos(self) -> None:
        with open(self.resultado["readme"], encoding="utf-8") as fh:
            readme = fh.read()
        self.assertIn(build_publicacion.URL_DESCARGA_CRUDA, readme)
        self.assertIn(build_publicacion.URL_PAGES, readme)

        conteos = self.resultado["conteos"]
        self.assertIn(str(conteos["paginas"]), readme)
        self.assertIn(str(conteos["fichas"]), readme)
        self.assertIn(str(conteos["laminas"]), readme)

    # 6. Los anclas `guia/index.html#ficha-<id>` resuelven al archivo destino.
    def test_anclas_de_fichas_resuelven_al_sitio(self) -> None:
        recolector = _RecolectorEnlaces()
        recolector.feed(self.index_html)
        anclas = [
            h
            for h in recolector.hrefs
            if h.startswith(f"{build_publicacion.NOMBRE_GUIA}/index.html#ficha-")
        ]
        self.assertGreater(len(anclas), 0)
        # La resolucion del enlace relativo depende de que exista el archivo
        # destino (guia/index.html); el fragmento #ficha-<id> es interno.
        for ancla in anclas:
            ruta_relativa = ancla.split("#", 1)[0]
            self.assertTrue(
                os.path.isfile(os.path.join(self.dir_salida, ruta_relativa))
            )

    # 7. Cada lamina SVG es un SVG bien formado.
    def test_laminas_svg_bien_formadas(self) -> None:
        dir_laminas = os.path.join(self.dir_salida, build_publicacion.NOMBRE_LAMINAS)
        for nombre in self._laminas_en_disco():
            with open(os.path.join(dir_laminas, nombre), encoding="utf-8") as fh:
                svg = fh.read()
            self.assertIn("<svg", svg)
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
            self.assertIn("viewBox", svg)
            # La raiz es un elemento <svg> (primer tag del documento).
            self.assertTrue(svg.lstrip().startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
