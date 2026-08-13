"""Pruebas de integracion de los tres targets y del guardarrail de fichas (25.1).

Cubren la orquestacion de una sola corrida (Req 12.1, 13.5, 15.*):

* una corrida de `build.construir(...)` en un directorio temporal emite los tres
  artefactos de la feature: `dist/index.html` (Target_Web, un solo archivo),
  `dist/guia.pdf` (Target_PDF_Guia) y `dist/laminas.pdf` (Target_Laminas), ademas
  del `dist/ejercicios.json` crudo descargable;
* el `index.html` es autocontenido: sin CDN ni `<script src=...>` externo;
* el guardarrail `verificar_sin_fichas_en_modulos()` PASA con los modulos de
  contenido actuales (`cap00_portada`, `cap10_fundamentos`) y FALLA con
  `E_FICHA_EN_MODULO` ante un modulo `capNN_*.py` de prueba que construye una
  `FichaEjercicio` literal;
* el gate de publicacion REVISADO rechaza el contenido de muestra (15 fichas <
  45) en modo estricto con `E_COBERTURA_MINIMA`, y en modo muestra el reporte es
  NO_PUBLICABLE y enumera los umbrales revisados omitidos (100 paginas, 45-60
  fichas, 12 semanas).

Solo libreria estandar y `unittest`; sin `assert` fuera del framework de test.

_Requirements: 12.1, 13.5, 15.1, 15.2, 15.4_
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build  # noqa: E402
from guia.errores import (  # noqa: E402
    E_COBERTURA_MINIMA,
    E_FICHA_EN_MODULO,
    ErrorBuild,
    ErrorFuenteFichas,
)


# Modulo de contenido de prueba que SI construye una FichaEjercicio literal: el
# guardarrail debe rechazarlo. Se escribe en un directorio temporal para no
# tocar el paquete real de contenido.
_MODULO_INFRACTOR = '''\
"""Modulo de prueba que declara una ficha (prohibido, Req 15.2)."""
from guia.schema import FichaEjercicio

CAPITULO_ID = "cap20_pos_prueba"

MALA = FichaEjercicio(
    id="prueba",
    titulo="t",
    objetivo="o",
    pasos=["a", "b"],
    observacion="obs",
    jugadoras=(1, 2),
    montaje={},
    diagrama=None,
)
'''

# Modulo de contenido de prueba "limpio": solo narrativa, ninguna ficha.
_MODULO_LIMPIO = '''\
"""Modulo de prueba solo narrativo (permitido)."""
CAPITULO_ID = "cap30_colectivo"
TITULO = "Juego colectivo"
PARRAFOS = ("texto narrativo", "mas texto")
'''


class TestTresTargetsUnaCorrida(unittest.TestCase):
    def test_una_corrida_emite_los_tres_targets(self):
        with tempfile.TemporaryDirectory(prefix="guia_targets_") as tmp:
            dir_dist = os.path.join(tmp, "dist")
            reporte = build.construir(
                modo=build.MODO_MUESTRA,
                dir_dist=dir_dist,
                con_preflight=False,
            )

            # Los tres targets de la feature, en una sola corrida.
            ruta_web = os.path.join(dir_dist, "index.html")
            ruta_pdf = os.path.join(dir_dist, build.NOMBRE_PDF)
            ruta_laminas = os.path.join(dir_dist, build.NOMBRE_LAMINAS)
            ruta_json = os.path.join(dir_dist, build.NOMBRE_JSON)

            self.assertTrue(os.path.isfile(ruta_web), "falta dist/index.html")
            self.assertTrue(os.path.isfile(ruta_pdf), "falta dist/guia.pdf")
            self.assertTrue(os.path.isfile(ruta_laminas), "falta dist/laminas.pdf")
            self.assertTrue(os.path.isfile(ruta_json), "falta dist/ejercicios.json")

            self.assertEqual(reporte.ruta_sitio, ruta_web)
            self.assertEqual(reporte.ruta_pdf, ruta_pdf)
            self.assertEqual(reporte.ruta_laminas, ruta_laminas)
            self.assertEqual(reporte.ruta_json, ruta_json)
            self.assertGreater(reporte.laminas, 0)

            # El Target_Web es autocontenido: sin recursos externos (CDN).
            with open(ruta_web, encoding="utf-8") as fh:
                html = fh.read()
            self.assertNotIn("https://cdn", html)
            self.assertNotIn("src=\"http", html)
            self.assertNotIn("<link", html)

    def test_guardarrail_pasa_con_modulos_actuales(self):
        # Los modulos reales de contenido no declaran fichas: pasa y devuelve la
        # lista de modulos revisados (incluye cap00 y cap10).
        revisados = build.verificar_sin_fichas_en_modulos()
        self.assertIn("cap00_portada.py", revisados)
        self.assertIn("cap10_fundamentos.py", revisados)

    def test_guardarrail_pasa_con_dir_solo_narrativo(self):
        with tempfile.TemporaryDirectory(prefix="guia_narr_") as tmp:
            ruta = os.path.join(tmp, "cap30_colectivo.py")
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(_MODULO_LIMPIO)
            revisados = build.verificar_sin_fichas_en_modulos(tmp)
            self.assertEqual(revisados, ("cap30_colectivo.py",))

    def test_guardarrail_falla_ante_modulo_con_ficha(self):
        with tempfile.TemporaryDirectory(prefix="guia_infractor_") as tmp:
            ruta = os.path.join(tmp, "cap20_pos_prueba.py")
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(_MODULO_INFRACTOR)
            with self.assertRaises(ErrorFuenteFichas) as ctx:
                build.verificar_sin_fichas_en_modulos(tmp)
            self.assertEqual(ctx.exception.codigo, E_FICHA_EN_MODULO)
            self.assertIn("cap20_pos_prueba.py", str(ctx.exception))

    def test_gate_publicable_en_estricto_con_catalogo_completo(self):
        # El catalogo completo (>=45 fichas, >=12 semanas y >=100 paginas del
        # modelo paginado) hace que el build estricto sea PUBLICABLE.
        with tempfile.TemporaryDirectory(prefix="guia_estricto_") as tmp:
            reporte = build.construir(
                modo=build.MODO_ESTRICTO,
                dir_dist=os.path.join(tmp, "dist"),
                con_preflight=False,
            )
            self.assertTrue(reporte.publicable)
            self.assertEqual(reporte.umbrales_omitidos, ())
            self.assertGreaterEqual(reporte.fichas, 45)
            self.assertLessEqual(reporte.fichas, 60)
            self.assertGreaterEqual(reporte.bloques, 12)
            self.assertIn("PUBLICABLE", reporte.texto())

    def test_reporte_muestra_lista_umbrales_revisados(self):
        with tempfile.TemporaryDirectory(prefix="guia_umbrales_") as tmp:
            reporte = build.construir(
                modo=build.MODO_MUESTRA,
                dir_dist=os.path.join(tmp, "dist"),
                con_preflight=False,
            )
            self.assertFalse(reporte.publicable)
            texto = reporte.texto()
            self.assertIn("NO_PUBLICABLE / MUESTRA", texto)

            # Los umbrales omitidos reflejan los NUEVOS numeros, no los viejos.
            omitidos = " ".join(reporte.umbrales_omitidos)
            self.assertIn("paginas>=100", omitidos)
            self.assertIn("fichas en [45, 60]", omitidos)
            self.assertIn("12", omitidos)
            # No deben quedar rastros de los umbrales antiguos.
            self.assertNotIn("120", omitidos)
            self.assertNotIn("200, 300", omitidos)

            # El guardarrail figura entre las validaciones que se ejecutan.
            self.assertIn("sin_fichas_en_modulos", reporte.validaciones)


if __name__ == "__main__":
    unittest.main()
