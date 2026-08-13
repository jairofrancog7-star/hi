"""Pruebas de la tabla de decisión por jugadoras y por espacio (tarea 6.3).

Cubre por ejemplo (la prueba de propiedad formal es la tarea 6.7):
* totalidad de la tabla: para 1..11 jugadoras siempre hay una sesión cuyo rango
  admite ese número (Req 8.2);
* sesión sustituta: cuando llegan menos jugadoras del mínimo, la sustituta
  admite ese número (Req 8.8);
* selección por espacio: fichas ejecutables en franja de 10 m × 10 m o menor
  (Req 8.6).

_Requirements: 8.2, 8.6, 8.8_
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
from guia.schema import FichaEjercicio, Variante  # noqa: E402


def _ficha(fid: str, eje: str, minimo: int, maximo: int) -> FichaEjercicio:
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
    fichas: list[FichaEjercicio] = []
    for eje in rotacion.EJES:
        for k in range(por_eje):
            minimo = 1 + (k % 3)
            maximo = minimo + 3
            fichas.append(_ficha(f'{eje}_{k:02d}', eje, minimo, maximo))
    return fichas


class TestTablaDecisionJugadoras(unittest.TestCase):
    """La tabla resuelve toda asistencia de 1 a 11 (Req 8.2, Property 14)."""

    def setUp(self) -> None:
        self.plan = rotacion.generar_plan(_catalogo(), n_bloques=26)

    def test_dominio_completo_1_a_11(self) -> None:
        tabla = rotacion.tabla_decision_jugadoras(self.plan)
        self.assertEqual(sorted(tabla.keys()), list(range(1, 12)))

    def test_cada_resolucion_admite_su_numero(self) -> None:
        # Req 8.2: la sesión resuelta admite el número de jugadoras presentes.
        for n in range(1, 12):
            with self.subTest(n=n):
                resolucion = rotacion.resolver_por_jugadoras(self.plan, n)
                self.assertEqual(resolucion.n_presentes, n)
                self.assertTrue(rotacion.sesion_admite(resolucion.sesion, n))

    def test_fuera_de_dominio_falla(self) -> None:
        for n in (0, -1, 12, 20):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    rotacion.resolver_por_jugadoras(self.plan, n)

    def test_muchas_jugadoras_forman_grupos(self) -> None:
        # El tope de rango del catálogo sintético es 6; 7..11 se resuelven
        # ensanchando la sesión de mayor capacidad (grupos adicionales).
        resolucion = rotacion.resolver_por_jugadoras(self.plan, 11)
        self.assertFalse(resolucion.es_sustituta)
        self.assertTrue(rotacion.sesion_admite(resolucion.sesion, 11))


class TestResolverSustituta(unittest.TestCase):
    """La sustituta admite toda asistencia por debajo del mínimo (Req 8.8)."""

    def test_sustituta_admite_n_menor_que_minimo(self) -> None:
        plan = rotacion.generar_plan(_catalogo(), n_bloques=26)
        for sesion in rotacion._sesiones_del_plan(plan):
            minimo = sesion.jugadoras[0]
            for n in range(1, minimo):
                with self.subTest(foco=sesion.foco, minimo=minimo, n=n):
                    sustituta = rotacion.resolver_sustituta(sesion, n)
                    self.assertTrue(rotacion.sesion_admite(sustituta, n))

    def test_sustituta_no_procede_si_ya_cabe(self) -> None:
        plan = rotacion.generar_plan(_catalogo(), n_bloques=26)
        sesion = rotacion._sesiones_del_plan(plan)[0]
        # n dentro del rango no necesita sustituta.
        with self.assertRaises(ValueError):
            rotacion.resolver_sustituta(sesion, sesion.jugadoras[1])


class TestFichasEspacioReducido(unittest.TestCase):
    """Selección de fichas ejecutables en franja de 10 m × 10 m o menor (Req 8.6)."""

    def _con_reducido(self, fid: str, ancho: float, largo: float) -> FichaEjercicio:
        ficha = _ficha(fid, 'tecnica', 1, 2)
        ficha.espacio_reducido = Variante(ancho_m=ancho, largo_m=largo, ajuste='—')
        return ficha

    def test_incluye_las_que_caben_y_excluye_las_grandes(self) -> None:
        cabe = self._con_reducido('cabe', 8.0, 10.0)
        justo = self._con_reducido('justo', 10.0, 10.0)
        ancha = self._con_reducido('ancha', 12.0, 8.0)
        larga = self._con_reducido('larga', 6.0, 15.0)
        sin_dims = _ficha('sin', 'tecnica', 1, 2)  # montaje=None, sin reducido

        seleccion = rotacion.fichas_en_espacio_reducido(
            [cabe, justo, ancha, larga, sin_dims]
        )
        ids = [f.id for f in seleccion]
        self.assertEqual(ids, ['cabe', 'justo'])

    def test_respeta_lado_personalizado(self) -> None:
        f5 = self._con_reducido('cinco', 5.0, 5.0)
        f8 = self._con_reducido('ocho', 8.0, 8.0)
        seleccion = rotacion.fichas_en_espacio_reducido([f5, f8], lado_m=6.0)
        self.assertEqual([f.id for f in seleccion], ['cinco'])


if __name__ == '__main__':
    unittest.main()
