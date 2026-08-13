"""Guardarrail de contenido: cero jerga interna en la superficie visible.

La guia la lee una entrenadora, no quien construye el proyecto. Nombres como
`Catalogo_JSON`, `Target_PDF` o `MODO_MUESTRA` son vocabulario de diseno: sirven
en `requirements.md` y en los docstrings, y no tienen nada que hacer en el texto
que ve la usuaria. Este archivo veta esos terminos en la **superficie visible**:

1. el `Catalogo_JSON` completo, serializado (todo el texto de las 58 fichas);
2. el Target_Web generado **en memoria** con `build_site.html_sitio()`;
3. el texto del Modelo_Paginas de `build_guia_pdf.modelo()`, recorrido igual
   que en `test_guardarrail_clubes.py` (y que `build._validar_codificacion`);
4. `dist/index.html`, si esta publicado; si no existe, la prueba se omite.

FALSOS POSITIVOS. La busqueda es case-insensitive y con **limites de palabra**,
porque varios terminos son subcadenas de prosa legitima. Comprobado por sonda
contra las cuatro superficies antes de fijar la lista:

* `gate` con `\\bgate\\b` no aparece en ninguna superficie. Sin limites de
  palabra si coincidiria dentro de conjugaciones y palabras espanolas
  (`pagate`, `apagate`, `agatearse`), que son contenido legitimo; por eso el
  patron SIEMPRE lleva `\\b` a los dos lados.
* `PUBLICABLE` tampoco aparece hoy. `\\bPUBLICABLE\\b` no coincide dentro de
  `NO_PUBLICABLE` (el `_` es caracter de palabra), asi que los dos terminos se
  vigilan por separado y ninguno enmascara al otro.
* Los identificadores con `_` admiten sufijo (`\\w*`) para que `Target_PDF`
  cace tambien `Target_PDF_Guia` o `Target_PDF_Laminas`.
* Los nombres de modulo se cazan con `\\b\\w+\\.py\\b`.

Solo libreria estandar y `unittest`.

_Requirements: 11.2, 12.4, 14.5_
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_guia_pdf, build_site, schema_json  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.layout import TipoElemento  # noqa: E402

#: Jerga interna del proyecto vetada en la superficie visible de la guia.
JERGA_VETADA: tuple[str, ...] = (
    "MODO_MUESTRA",
    "MODO MUESTRA",
    "MODO_ESTRICTO",
    "NO_PUBLICABLE",
    "PUBLICABLE",
    "Catalogo_JSON",
    "Catálogo_JSON",
    "Ficha_JSON",
    "Media_Item",
    "Plan_Rotacion",
    "Modelo_Paginas",
    "Target_Web",
    "Target_PDF",
    "Target_Laminas",
    "E_COBERTURA_MINIMA",
    "ErrorBuild",
    "__pycache__",
    "pipeline",
    "gate",
)

#: Patron para cualquier nombre de modulo con extension `.py`.
PATRON_MODULO_PY: re.Pattern[str] = re.compile(r"\b\w+\.py\b", re.IGNORECASE)


def _patron(termino: str) -> re.Pattern[str]:
    """Patron case-insensitive con limites de palabra para `termino`.

    Los terminos de varias palabras aceptan cualquier espacio en blanco entre
    ellas (`MODO MUESTRA` casa con `MODO\\nMUESTRA`). Los identificadores que
    llevan `_` admiten sufijo, para que `Target_PDF` cace `Target_PDF_Guia`.
    """
    cuerpo = r"\s+".join(re.escape(parte) for parte in termino.split())
    cola = r"\w*" if "_" in termino else r"\b"
    return re.compile(r"\b" + cuerpo + cola, re.IGNORECASE)


_PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    [(termino, _patron(termino)) for termino in JERGA_VETADA]
    + [("<modulo>.py", PATRON_MODULO_PY)]
)


def buscar_jerga(texto: str, superficie: str) -> list[str]:
    """Devuelve un hallazgo legible por cada termino interno hallado en `texto`."""
    hallazgos: list[str] = []
    for termino, patron in _PATRONES:
        encontrado = patron.search(texto)
        if encontrado is None:
            continue
        inicio = max(0, encontrado.start() - 60)
        contexto = texto[inicio : encontrado.end() + 60].replace("\n", " ")
        hallazgos.append(
            f"jerga interna '{termino}' aparece en {superficie} "
            f"(coincidencia {encontrado.group()!r}, offset {encontrado.start()}): "
            f"...{contexto}..."
        )
    return hallazgos


def _textos_del_modelo(paginas) -> list[str]:
    """Texto visible del Modelo_Paginas, como en `build._validar_codificacion`."""
    textos: list[str] = []
    for pagina in paginas:
        for cabecera in (pagina.capitulo_titulo, pagina.titulo_ficha):
            if cabecera:
                textos.append(cabecera)
        for elem in pagina.elementos:
            datos = elem.datos
            if elem.tipo in (TipoElemento.TEXTO, TipoElemento.PARRAFO):
                texto = getattr(datos, "texto", None)
                if texto:
                    textos.append(str(texto))
            elif elem.tipo is TipoElemento.TABLA:
                for celda in getattr(datos, "celdas", ()) or ():
                    textos.append(str(celda))
    return textos


def _texto_catalogo() -> str:
    """El Catalogo_JSON entero serializado, con sus acentos intactos."""
    fichas = schema_json.cargar_catalogo(cap10_fundamentos.ruta_catalogo())
    return json.dumps(fichas, ensure_ascii=False, indent=2)


class TestGuardarrailJergaEnFuentes(unittest.TestCase):
    """Superficies generadas en el momento: catalogo, sitio y modelo del PDF."""

    def test_catalogo_sin_jerga_interna(self) -> None:
        hallazgos = buscar_jerga(_texto_catalogo(), "Catalogo_JSON serializado")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_sitio_en_memoria_sin_jerga_interna(self) -> None:
        html = build_site.html_sitio()
        hallazgos = buscar_jerga(html, "build_site.html_sitio() (sitio de un archivo)")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_modelo_pdf_guia_sin_jerga_interna(self) -> None:
        textos = _textos_del_modelo(build_guia_pdf.modelo())
        self.assertTrue(textos, "el modelo del PDF de la guia no tiene texto")
        hallazgos = buscar_jerga("\n".join(textos), "build_guia_pdf.modelo()")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_el_guardarrail_detecta_una_inyeccion(self) -> None:
        """Cordura: el detector si caza `MODO_MUESTRA` inyectado en el HTML."""
        html = build_site.html_sitio()
        sucio = html.replace("</h1>", " (MODO_MUESTRA)</h1>", 1)
        hallazgos = buscar_jerga(sucio, "html inyectado")
        self.assertTrue(hallazgos, "el guardarrail no detecto la inyeccion")
        unidos = "\n".join(hallazgos)
        self.assertIn("MODO_MUESTRA", unidos)
        self.assertIn("html inyectado", unidos)


class TestGuardarrailJergaEnArtefactos(unittest.TestCase):
    """Artefacto publicado en `dist/`. Si no existe, la prueba se omite."""

    def test_dist_index_html_sin_jerga_interna(self) -> None:
        ruta = os.path.join(_DIR_RAIZ, "dist", "index.html")
        if not os.path.isfile(ruta):
            self.skipTest(f"artefacto no publicado: {ruta}")
        with open(ruta, encoding="utf-8") as manejador:
            html = manejador.read()
        hallazgos = buscar_jerga(html, "dist/index.html")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))


if __name__ == "__main__":
    unittest.main()
