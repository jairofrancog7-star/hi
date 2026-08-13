"""Guardarrail de contenido: ningun nombre de club aparece en la guia.

La guia es material practico para las jugadoras: nada de "entrena como el
Olympique" ni referencias a equipos profesionales. Este archivo veta esos
nombres en la **superficie visible** de la guia, no solo en el codigo fuente:

1. el `Catalogo_JSON` (`contenido/ejercicios.json`), leido como texto crudo;
2. el Target_Web generado **en memoria** con `build_site.html_sitio()` (no se
   lee `dist/`, que puede estar obsoleto);
3. el Modelo_Paginas del Target_PDF_Guia (`build_guia_pdf.modelo()`),
   recorriendo el texto de cada elemento igual que `build._validar_codificacion`.

Ademas, si existen los artefactos publicados se revisan tambien:

4. `dist/index.html` como texto UTF-8;
5. `dist/guia.pdf` en binario, tanto en los bytes crudos (diccionarios,
   valores `/URI`, metadatos, streams sin comprimir) como en el texto de los
   streams FlateDecode **descomprimidos** con `zlib`; los streams de contenido
   van comprimidos, asi que una busqueda solo sobre bytes crudos no veria nada.
   Si un artefacto no existe, la prueba se omite con `skipTest`.

La comparacion es case-insensitive y con **limites de palabra**: sin ellos,
`Inter` daria falso positivo en 87 lugares del JSON ("interior del pie") y en
208 del HTML ("intermedio"), que son contenido practico legitimo. Los nombres
de varias palabras admiten cualquier espacio en blanco entre ellas, porque el
salto de linea del HTML puede caer en medio.

Solo libreria estandar y `unittest`.

_Requirements: 11.2, 12.4, 14.5_
"""

from __future__ import annotations

import os
import re
import sys
import unittest
import zlib

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_guia_pdf, build_site  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.layout import TipoElemento  # noqa: E402

#: Nombres de club / equipo profesional vetados en la superficie visible.
#:
#: Comprobado por sonda contra las tres superficies antes de fijar la lista:
#: con limites de palabra ninguno de estos terminos aparece hoy, incluidos
#: "America"/"America" (no hay prosa que los use), asi que se conservan todos.
#: El unico termino que exigio cuidado es "Inter": como subcadena aparece en
#: "interior", "intermedio" e "internacional"; con `\b...\b` no coincide con
#: ninguno, por eso se queda en la lista pero SIEMPRE con limites de palabra.
CLUBES_VETADOS: tuple[str, ...] = (
    "Olympique",
    "Lyonnais",
    "Lyon",
    "Barcelona",
    "Barcelona Femeni",
    "Barca",
    "Barça",
    "Chelsea",
    "Arsenal",
    "Tigres",
    "Rayadas",
    "Monterrey",
    "Bayern",
    "Wolfsburg",
    "Portland",
    "Thorns",
    "Manchester",
    "Real Madrid",
    "Juventus",
    "Atletico",
    "Atlético",
    "America",
    "América",
    "Houston",
    "North Carolina",
    "PSG",
    "Paris Saint",
    "Roma",
    "Milan",
    "Inter",
    "Liverpool",
)


def _patron(club: str) -> re.Pattern[str]:
    """Patron case-insensitive con limites de palabra para `club`.

    Los nombres de varias palabras aceptan cualquier espacio en blanco entre
    ellas (`Real Madrid` casa con `Real\\nMadrid`).
    """
    cuerpo = r"\s+".join(re.escape(parte) for parte in club.split())
    return re.compile(r"\b" + cuerpo + r"\b", re.IGNORECASE)


_PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (club, _patron(club)) for club in CLUBES_VETADOS
)


def buscar_clubes(texto: str, superficie: str) -> list[str]:
    """Devuelve un hallazgo legible por cada club encontrado en `texto`."""
    hallazgos: list[str] = []
    for club, patron in _PATRONES:
        encontrado = patron.search(texto)
        if encontrado is None:
            continue
        inicio = max(0, encontrado.start() - 60)
        contexto = texto[inicio : encontrado.end() + 60].replace("\n", " ")
        hallazgos.append(
            f"club '{club}' aparece en {superficie} "
            f"(offset {encontrado.start()}): ...{contexto}..."
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


def _streams_pdf(datos: bytes) -> list[tuple[int, int]]:
    """Rangos `(inicio, fin)` del cuerpo de cada `stream ... endstream`."""
    rangos: list[tuple[int, int]] = []
    pos = 0
    while True:
        ini = datos.find(b"stream", pos)
        if ini < 0:
            break
        arranque = ini + len(b"stream")
        if datos[arranque : arranque + 2] == b"\r\n":
            arranque += 2
        elif datos[arranque : arranque + 1] in (b"\n", b"\r"):
            arranque += 1
        fin = datos.find(b"endstream", arranque)
        if fin < 0:
            break
        rangos.append((arranque, fin))
        pos = fin + len(b"endstream")
    return rangos


def _texto_streams_descomprimidos(datos: bytes) -> str:
    """Concatena los streams FlateDecode que `zlib` logra descomprimir."""
    partes: list[str] = []
    for inicio, fin in _streams_pdf(datos):
        try:
            plano = zlib.decompress(datos[inicio:fin])
        except zlib.error:
            continue  # no es FlateDecode (o esta truncado): se omite
        partes.append(plano.decode("latin-1", errors="replace"))
    return "\n".join(partes)


def _texto_crudo_sin_comprimidos(datos: bytes) -> str:
    """Bytes del PDF con los cuerpos FlateDecode neutralizados.

    El resto se conserva tal cual: cabeceras de objeto, diccionarios, valores
    `/URI` de las anotaciones, metadatos, tabla xref y cualquier stream que NO
    este comprimido (ahi si viviria texto legible en crudo). Los cuerpos
    comprimidos se sustituyen por espacios porque su ruido binario, leido como
    latin-1, produce coincidencias fortuitas de tokens cortos ("PSG", "Roma");
    ese contenido ya se revisa descomprimido en `_texto_streams_descomprimidos`.
    """
    salida = bytearray(datos)
    for inicio, fin in _streams_pdf(datos):
        try:
            zlib.decompress(datos[inicio:fin])
        except zlib.error:
            continue  # no comprimido: se deja intacto para buscar en el
        salida[inicio:fin] = b" " * (fin - inicio)
    return bytes(salida).decode("latin-1", errors="replace")


class TestGuardarrailClubesEnFuentes(unittest.TestCase):
    """Superficies generadas en el momento: JSON, sitio en memoria y modelo PDF."""

    def test_catalogo_json_sin_nombres_de_club(self) -> None:
        ruta = cap10_fundamentos.ruta_catalogo()
        with open(ruta, encoding="utf-8") as manejador:
            crudo = manejador.read()
        hallazgos = buscar_clubes(crudo, "contenido/ejercicios.json")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_sitio_en_memoria_sin_nombres_de_club(self) -> None:
        html = build_site.html_sitio()
        hallazgos = buscar_clubes(html, "build_site.html_sitio() (Target_Web)")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_modelo_pdf_guia_sin_nombres_de_club(self) -> None:
        textos = _textos_del_modelo(build_guia_pdf.modelo())
        self.assertTrue(textos, "el modelo del Target_PDF_Guia no tiene texto")
        hallazgos = buscar_clubes(
            "\n".join(textos), "build_guia_pdf.modelo() (Target_PDF_Guia)"
        )
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_el_guardarrail_detecta_una_inyeccion(self) -> None:
        """Cordura: el detector si encuentra un club inyectado en el HTML."""
        html = build_site.html_sitio()
        sucio = html.replace("</h1>", " del Olympique Lyonnais</h1>", 1)
        hallazgos = buscar_clubes(sucio, "html inyectado")
        self.assertTrue(hallazgos, "el guardarrail no detecto la inyeccion")
        unidos = "\n".join(hallazgos)
        self.assertIn("Olympique", unidos)
        self.assertIn("Lyonnais", unidos)
        self.assertIn("html inyectado", unidos)


class TestGuardarrailClubesEnArtefactos(unittest.TestCase):
    """Artefactos publicados en `dist/`. Si no existen, la prueba se omite."""

    def test_dist_index_html_sin_nombres_de_club(self) -> None:
        ruta = os.path.join(_DIR_RAIZ, "dist", "index.html")
        if not os.path.isfile(ruta):
            self.skipTest(f"artefacto no publicado: {ruta}")
        with open(ruta, encoding="utf-8") as manejador:
            html = manejador.read()
        hallazgos = buscar_clubes(html, "dist/index.html")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_dist_guia_pdf_sin_nombres_de_club(self) -> None:
        ruta = os.path.join(_DIR_RAIZ, "dist", "guia.pdf")
        if not os.path.isfile(ruta):
            self.skipTest(f"artefacto no publicado: {ruta}")
        with open(ruta, "rb") as manejador:
            datos = manejador.read()

        crudo = _texto_crudo_sin_comprimidos(datos)
        hallazgos = buscar_clubes(crudo, "dist/guia.pdf (bytes crudos)")

        plano = _texto_streams_descomprimidos(datos)
        self.assertTrue(plano, "ningun stream de dist/guia.pdf descomprimio")
        hallazgos += buscar_clubes(plano, "dist/guia.pdf (streams FlateDecode)")

        self.assertEqual(hallazgos, [], "\n".join(hallazgos))


if __name__ == "__main__":
    unittest.main()
