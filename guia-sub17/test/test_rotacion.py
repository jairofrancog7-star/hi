"""Pruebas de `guia.rotacion`: determinismo, unicidad y coherencia (tarea 6.1).

Cubre por ejemplo (la prueba de propiedad formal es la tarea 6.4):
* determinismo: dos corridas con la misma semilla dan el mismo plan;
* unicidad de la firma canónica entre bloques (Req 5.4);
* estructura del bloque: martes/miércoles/jueves, objetivo, sábado (Req 5.2, 5.3, 5.5);
* presupuesto de sesión: sum(bloques) == total_min <= 90 y versión corta <= 30
  (Req 5.6, 5.7, 5.9);
* una fila de seguimiento por bloque (Req 5.8).

_Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_
"""

from __future__ import annotations

import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import rotacion  # noqa: E402
from guia.errores import E_ROTACION_SIN_COMBINACION, ErrorRotacion  # noqa: E402
from guia.schema import Dia, FichaEjercicio  # noqa: E402


def _ficha(fid: str, eje: str, minimo: int, maximo: int) -> FichaEjercicio:
    """Ficha mínima suficiente para el generador (id, eje, rango de jugadoras)."""
    return FichaEjercicio(
        id=fid,
        titulo=f'Ejercicio {fid}',
        objetivo='Mejorar un gesto técnico concreto.',
        pasos=['Preparar el espacio.', 'Ejecutar el gesto.'],
        observacion='Qué mira la compañera.',
        jugadoras=(minimo, maximo),
        montaje=None,
        diagrama=None,
        etiquetas=[eje],
    )


def _catalogo(por_eje: int = 12) -> list[FichaEjercicio]:
    """Catálogo sintético con `por_eje` fichas etiquetadas por cada eje."""
    fichas: list[FichaEjercicio] = []
    for eje in rotacion.EJES:
        for k in range(por_eje):
            minimo = 1 + (k % 3)
            maximo = minimo + 3
            fichas.append(_ficha(f'{eje}_{k:02d}', eje, minimo, maximo))
    return fichas


class TestGenerarPlan(unittest.TestCase):
    """Estructura, unicidad y presupuesto del Plan_Rotacion."""

    def setUp(self) -> None:
        self.fichas = _catalogo()
        self.plan = rotacion.generar_plan(self.fichas, n_bloques=26)

    def test_numero_de_bloques(self) -> None:
        self.assertEqual(len(self.plan.bloques), 26)
        self.assertGreaterEqual(len(self.plan.bloques), 24)  # Req 5.1

    def test_firmas_unicas(self) -> None:
        # Req 5.4: ninguna combinación de fichas se repite.
        firmas = [b.firma for b in self.plan.bloques]
        self.assertEqual(len(firmas), len(set(firmas)))

    def test_firma_es_canonica(self) -> None:
        for bloque in self.plan.bloques:
            ids = [
                fid
                for sesion in bloque.sesiones.values()
                for fid in sesion.ficha_ids
            ]
            self.assertEqual(bloque.firma, rotacion.firma_de(ids))

    def test_cada_bloque_tiene_tres_dias(self) -> None:
        # Req 5.2: martes, miércoles y jueves presentes.
        for bloque in self.plan.bloques:
            self.assertEqual(
                set(bloque.sesiones.keys()),
                {Dia.MARTES, Dia.MIERCOLES, Dia.JUEVES},
            )

    def test_objetivo_una_frase_y_sabado(self) -> None:
        for bloque in self.plan.bloques:
            self.assertTrue(bloque.objetivo.strip())          # Req 5.5
            self.assertEqual(bloque.objetivo.count('.'), 1)   # una sola frase
            self.assertTrue(bloque.sabado.calentamiento)      # Req 5.3
            self.assertTrue(bloque.sabado.enfoque.strip())

    def test_presupuesto_de_sesion(self) -> None:
        # Req 5.6 y 5.7: la suma de bloques es el total y no supera 90 min.
        for bloque in self.plan.bloques:
            for sesion in bloque.sesiones.values():
                self.assertEqual(
                    sum(b.minutos for b in sesion.bloques), sesion.total_min
                )
                self.assertLessEqual(sesion.total_min, 90)

    def test_version_corta(self) -> None:
        # Req 5.9: cada sesión tiene una versión corta de <= 30 min.
        for bloque in self.plan.bloques:
            for sesion in bloque.sesiones.values():
                self.assertIsNotNone(sesion.version_corta)
                corta = sesion.version_corta
                self.assertLessEqual(corta.total_min, 30)
                self.assertEqual(
                    sum(b.minutos for b in corta.bloques), corta.total_min
                )
                self.assertIsNone(corta.version_corta)

    def test_sustituta_definida(self) -> None:
        # Req 8.8: cada sesión resuelve una sustituta con menos jugadoras.
        for bloque in self.plan.bloques:
            for sesion in bloque.sesiones.values():
                self.assertIn(sesion.sustituta_id, sesion.ficha_ids)

    def test_una_fila_de_seguimiento_por_bloque(self) -> None:
        # Req 5.8.
        filas = self.plan.seguimiento.filas
        self.assertEqual(len(filas), len(self.plan.bloques))
        for fila, bloque in zip(filas, self.plan.bloques):
            self.assertEqual(fila.bloque_id, bloque.id)
            self.assertEqual(len(fila.sesiones_completadas), 3)


class TestDeterminismo(unittest.TestCase):
    """Dos corridas con la misma semilla producen el mismo plan (Riesgo 13)."""

    def test_mismo_plan_con_misma_semilla(self) -> None:
        fichas = _catalogo()
        plan_a = rotacion.generar_plan(fichas, n_bloques=26, semilla=20260101)
        plan_b = rotacion.generar_plan(fichas, n_bloques=26, semilla=20260101)
        huella_a = [
            (b.id, b.firma, tuple(sorted(s.foco for s in b.sesiones.values())))
            for b in plan_a.bloques
        ]
        huella_b = [
            (b.id, b.firma, tuple(sorted(s.foco for s in b.sesiones.values())))
            for b in plan_b.bloques
        ]
        self.assertEqual(huella_a, huella_b)

    def test_orden_interno_depende_de_la_semilla(self) -> None:
        # La selección base es round-robin determinista (independiente de la
        # semilla); la semilla afecta el orden interno de las fichas en cada
        # sesión vía el Fisher-Yates propio. La firma canónica no cambia.
        fichas = _catalogo()
        a = rotacion.generar_plan(fichas, n_bloques=26, semilla=1)
        b = rotacion.generar_plan(fichas, n_bloques=26, semilla=99999)
        orden_a = [
            tuple(s.ficha_ids)
            for bloque in a.bloques
            for s in bloque.sesiones.values()
        ]
        orden_b = [
            tuple(s.ficha_ids)
            for bloque in b.bloques
            for s in bloque.sesiones.values()
        ]
        self.assertNotEqual(orden_a, orden_b)
        # Pero el conjunto (firma) de cada sesión es el mismo.
        conj_a = [frozenset(o) for o in orden_a]
        conj_b = [frozenset(o) for o in orden_b]
        self.assertEqual(conj_a, conj_b)


class TestReparacionAgotada(unittest.TestCase):
    """Con muy pocas fichas no hay combinaciones libres suficientes."""

    def test_sin_combinacion_libre(self) -> None:
        # Solo 3 fichas por eje => cada eje tiene una sola ventana posible;
        # pedir muchos bloques agota las combinaciones y debe fallar limpio.
        fichas = _catalogo(por_eje=3)
        with self.assertRaises(ErrorRotacion) as cm:
            rotacion.generar_plan(fichas, n_bloques=26)
        self.assertEqual(cm.exception.codigo, E_ROTACION_SIN_COMBINACION)


if __name__ == '__main__':
    unittest.main()
