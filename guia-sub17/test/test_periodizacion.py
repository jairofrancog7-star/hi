"""Pruebas de la periodización práctica de 12 semanas (tarea 26).

Verifican el modelo de datos inmutable, el validador `validar_plan` y el render
HTML del plan del módulo `periodizacion`. La guía solo muestra contenido
práctico: el módulo ya no expone fuentes ni referencias.

_Requirements: 5.1, 5.5, 5.6, 6.1_
"""

from __future__ import annotations

import dataclasses
import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import periodizacion  # noqa: E402
from guia.errores import ErrorBuild  # noqa: E402


class TestPlan12Semanas(unittest.TestCase):
    def test_tres_bloques(self) -> None:
        self.assertEqual(len(periodizacion.PLAN_12_SEMANAS.bloques), 3)

    def test_cobertura_consecutiva_1_a_12(self) -> None:
        bloques = periodizacion.PLAN_12_SEMANAS.bloques
        rangos = [(b.semana_inicio, b.semana_fin) for b in bloques]
        self.assertEqual(rangos, [(1, 4), (5, 8), (9, 12)])
        # Sin huecos ni solapes: cada bloque empieza donde termina el anterior.
        esperado = 1
        total = 0
        for inicio, fin in rangos:
            self.assertEqual(inicio, esperado)
            self.assertLessEqual(inicio, fin)
            total += fin - inicio + 1
            esperado = fin + 1
        self.assertEqual(total, 12)

    def test_suma_de_semanas_es_12(self) -> None:
        total = sum(b.semanas for b in periodizacion.PLAN_12_SEMANAS.bloques)
        self.assertEqual(total, 12)

    def test_cada_bloque_completo(self) -> None:
        for bloque in periodizacion.PLAN_12_SEMANAS.bloques:
            self.assertTrue(bloque.foco, "foco vacío")
            self.assertTrue(bloque.indicadores, "indicadores vacíos")
            self.assertTrue(bloque.carga, "carga vacía")
            self.assertTrue(bloque.nivel_prevencion, "nivel de prevención vacío")

    def test_microestructura_presente(self) -> None:
        self.assertTrue(periodizacion.PLAN_12_SEMANAS.microestructura)


class TestValidarPlan(unittest.TestCase):
    def test_plan_valido_no_lanza(self) -> None:
        # No debe lanzar.
        periodizacion.validar_plan(periodizacion.PLAN_12_SEMANAS)

    def test_bloque_removido_lanza(self) -> None:
        base = periodizacion.PLAN_12_SEMANAS
        mutado = dataclasses.replace(base, bloques=base.bloques[:2])
        with self.assertRaises(ErrorBuild) as ctx:
            periodizacion.validar_plan(mutado)
        self.assertEqual(ctx.exception.codigo, "E_COBERTURA_MINIMA")

    def test_semanas_rotas_lanza(self) -> None:
        base = periodizacion.PLAN_12_SEMANAS
        b0, b1, b2 = base.bloques
        # Rompe la continuidad: el tercer bloque salta a la semana 11.
        roto = dataclasses.replace(b2, semana_inicio=11)
        mutado = dataclasses.replace(base, bloques=(b0, b1, roto))
        with self.assertRaises(ErrorBuild) as ctx:
            periodizacion.validar_plan(mutado)
        self.assertEqual(ctx.exception.codigo, "E_COBERTURA_MINIMA")

    def test_sin_bloques_lanza(self) -> None:
        base = periodizacion.PLAN_12_SEMANAS
        mutado = dataclasses.replace(base, bloques=())
        with self.assertRaises(ErrorBuild):
            periodizacion.validar_plan(mutado)

    def test_bloque_sin_indicadores_lanza(self) -> None:
        base = periodizacion.PLAN_12_SEMANAS
        b0, b1, b2 = base.bloques
        sin_ind = dataclasses.replace(b1, indicadores=())
        mutado = dataclasses.replace(base, bloques=(b0, sin_ind, b2))
        with self.assertRaises(ErrorBuild):
            periodizacion.validar_plan(mutado)


class TestRenderHtml(unittest.TestCase):
    def setUp(self) -> None:
        self.html = periodizacion.render_html()
        self.bajo = self.html.lower()

    def test_contiene_id_y_h2(self) -> None:
        self.assertIn('id="plan-12-semanas"', self.html)
        self.assertIn("<h2>", self.bajo)

    def test_contiene_los_tres_nombres(self) -> None:
        self.assertIn("Base", self.html)
        self.assertIn("Desarrollo", self.html)
        self.assertIn("Competición", self.html)

    def test_sin_recursos_externos(self) -> None:
        self.assertNotIn('src="http', self.bajo)
        self.assertNotIn("<link", self.bajo)
        self.assertNotIn("<script", self.bajo)


if __name__ == "__main__":
    unittest.main()
