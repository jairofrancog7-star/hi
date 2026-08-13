"""Pruebas del Target_Laminas: `dist/laminas.pdf` vertical de telefono (tarea 23).

Verifica que `build_laminas`:

* produce **una lamina por ficha** (una `PaginaRender` por cada Ficha_JSON real);
* usa el formato **vertical de telefono** (proporcion 9:16, alto > ancho, NO A4)
  reutilizando la plantilla `lamina_vertical`;
* conserva los **enlaces** de cada ficha (cada URL de Media_Item aparece en la
  lamina de su ficha);
* el `laminas.pdf` emitido pasa el verificador estructural `verify_pdf` con el
  conteo de laminas del modelo, y cada pagina del PDF es vertical (alto > ancho).

Usa `tempfile` para el PDF en disco y limpia al terminar. Solo libreria
estandar y `unittest`.

_Requirements: 12.6, 9.4, 9.9_
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_laminas, verify_pdf  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.layout import PaginaRender, Plantilla, TipoElemento  # noqa: E402

_RE_MEDIABOX = re.compile(rb"/MediaBox\s*\[([^\]]*)\]")
_RE_NUM = re.compile(rb"[-+]?(?:\d+\.\d*|\.\d+|\d+)")


def _mediaboxes(datos: bytes) -> list[tuple[float, float]]:
    """Devuelve (ancho, alto) de cada /MediaBox del PDF."""
    cajas: list[tuple[float, float]] = []
    for m in _RE_MEDIABOX.finditer(datos):
        nums = [float(x) for x in _RE_NUM.findall(m.group(1))]
        if len(nums) >= 4:
            cajas.append((abs(nums[2] - nums[0]), abs(nums[3] - nums[1])))
    return cajas


class TestModeloLaminas(unittest.TestCase):
    def setUp(self) -> None:
        self.crudas = cap10_fundamentos.fichas_json()
        self.paginas = build_laminas.modelo()

    def test_una_lamina_por_ficha(self) -> None:
        self.assertEqual(len(self.paginas), len(self.crudas))
        self.assertEqual(len(self.paginas), 58)
        for pagina in self.paginas:
            self.assertIsInstance(pagina, PaginaRender)
            self.assertIs(pagina.plantilla, Plantilla.LAMINA_VERTICAL)

    def test_folios_consecutivos_desde_uno(self) -> None:
        folios = [p.folio for p in self.paginas]
        self.assertEqual(folios, list(range(1, len(self.paginas) + 1)))

    def test_pagina_es_vertical(self) -> None:
        # El formato de pagina es retrato de telefono (9:16): alto > ancho.
        self.assertGreater(build_laminas.LAMINA_ALTO, build_laminas.LAMINA_ANCHO)

    def test_conserva_los_enlaces_de_cada_ficha(self) -> None:
        # Cada URL de Media_Item de una ficha aparece como texto en su lamina.
        for cruda, pagina in zip(self.crudas, self.paginas):
            textos = [
                getattr(e.datos, "texto", "")
                for e in pagina.elementos
                if e.tipo in (TipoElemento.TEXTO, TipoElemento.PARRAFO)
            ]
            blob = "\n".join(textos)
            for medio in cruda["media"]:
                with self.subTest(id=cruda["id"], url=medio["url"]):
                    self.assertIn(medio["url"], blob)


class TestPDFLaminasEstructural(unittest.TestCase):
    def test_escribir_en_disco_verificar_y_vertical(self) -> None:
        fd, ruta = tempfile.mkstemp(suffix=".pdf", prefix="laminas_")
        os.close(fd)
        try:
            paginas = build_laminas.escribir(ruta, comprimir=True)
            self.assertTrue(os.path.isfile(ruta))
            # Pasa el verificador estructural con el conteo del modelo.
            informe = verify_pdf.verificar_archivo(
                ruta, paginas_esperadas=len(paginas)
            )
            self.assertEqual(informe.paginas, len(paginas))
            # Cada pagina del PDF es vertical (alto > ancho) y no es A4.
            with open(ruta, "rb") as fh:
                datos = fh.read()
            cajas = _mediaboxes(datos)
            self.assertEqual(len(cajas), len(paginas))
            for ancho, alto in cajas:
                self.assertGreater(alto, ancho)
                self.assertEqual((ancho, alto),
                                 (build_laminas.LAMINA_ANCHO, build_laminas.LAMINA_ALTO))
        finally:
            if os.path.exists(ruta):
                os.remove(ruta)


if __name__ == "__main__":
    unittest.main()
