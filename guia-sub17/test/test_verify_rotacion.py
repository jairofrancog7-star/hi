"""Pruebas de `guia.verify_rotacion`: unicidad independiente (tarea 6.2).

Cubre por ejemplo (la prueba de propiedad formal es la tarea 6.4):
* un plan real recién generado pasa la verificación y devuelve el mapa (Req 5.4);
* la firma se recalcula desde las sesiones, **no** desde `bloque.firma`: un
  campo `firma` corrupto no engaña al verificador (Req 5.10);
* dos bloques con la misma combinación (en distinto orden) se detectan y el
  error nombra los bloques con código `E_ROTACION_DUPLICADA` (Req 5.10, 5.4).

_Requirements: 5.10, 5.4_
"""

from __future__ import annotations

import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import rotacion, verify_rotacion  # noqa: E402
from guia.errores import E_ROTACION_DUPLICADA, ErrorRotacion  # noqa: E402
from guia.schema import (  # noqa: E402
    BloqueSemanal,
    Dia,
    FichaEjercicio,
    Sabado,
    Sesion,
)


def _ficha(fid: str, eje: str, minimo: int = 1, maximo: int = 4) -> FichaEjercicio:
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
            fichas.append(_ficha(f'{eje}_{k:02d}', eje))
    return fichas


def _sesion(dia: Dia, ficha_ids: list[str]) -> Sesion:
    return Sesion(
        dia=dia,
        foco='tecnica',
        bloques=[],
        total_min=0,
        ficha_ids=list(ficha_ids),
        jugadoras=(1, 4),
    )


def _bloque(bloque_id: str, semana: int, ids_por_dia: dict[Dia, list[str]],
            *, firma: str = 'FIRMA_FALSA') -> BloqueSemanal:
    """Bloque mínimo con una `firma` deliberadamente falsa por defecto.

    Así las pruebas verifican que el verificador recalcula desde las sesiones y
    no confía en el campo `firma`.
    """
    sesiones = {dia: _sesion(dia, ids) for dia, ids in ids_por_dia.items()}
    return BloqueSemanal(
        id=bloque_id,
        semana=semana,
        objetivo=f'Semana {semana}: objetivo.',
        sesiones=sesiones,
        sabado=Sabado(calentamiento=['Trote suave.'], enfoque='Enfocar.'),
        firma=firma,
    )


class TestVerificacionExitosa(unittest.TestCase):
    """Un plan bien formado pasa la verificación."""

    def test_plan_real_es_unico(self) -> None:
        plan = rotacion.generar_plan(_catalogo(), n_bloques=26)
        mapa = verify_rotacion.verificar_unicidad(plan.bloques)
        # Cada firma agrupa exactamente un bloque.
        self.assertEqual(len(mapa), len(plan.bloques))
        for ids in mapa.values():
            self.assertEqual(len(ids), 1)

    def test_recalcula_no_confia_en_firma(self) -> None:
        # Req 5.10: aunque `bloque.firma` esté corrupto, la firma real proviene
        # de las sesiones y la unicidad se conserva.
        plan = rotacion.generar_plan(_catalogo(), n_bloques=26)
        for bloque in plan.bloques:
            bloque.firma = 'FIRMA_CORRUPTA_IGUAL_PARA_TODOS'
        mapa = verify_rotacion.verificar_unicidad(plan.bloques)
        self.assertEqual(len(mapa), len(plan.bloques))

    def test_firma_recalculada_es_canonica(self) -> None:
        bloque = _bloque(
            'S01', 1,
            {
                Dia.MARTES: ['b', 'a'],
                Dia.MIERCOLES: ['a', 'c'],
                Dia.JUEVES: ['d'],
            },
        )
        # Orden y duplicados no cuentan.
        self.assertEqual(verify_rotacion.firma_recalculada(bloque), 'a|b|c|d')


class TestVerificacionDetectaDuplicados(unittest.TestCase):
    """Dos bloques con la misma combinación se detectan y se nombran."""

    def test_duplicado_lanza_error(self) -> None:
        # Mismas fichas en distinto orden => misma firma canónica (Req 5.4),
        # a pesar de tener campos `firma` distintos y falsos.
        b1 = _bloque('S01', 1, {Dia.MARTES: ['x', 'y', 'z']}, firma='A')
        b2 = _bloque('S02', 2, {Dia.MARTES: ['z', 'y', 'x']}, firma='B')
        with self.assertRaises(ErrorRotacion) as cm:
            verify_rotacion.verificar_unicidad([b1, b2])
        self.assertEqual(cm.exception.codigo, E_ROTACION_DUPLICADA)
        # El mensaje nombra ambos bloques.
        self.assertIn('S01', cm.exception.mensaje)
        self.assertIn('S02', cm.exception.mensaje)
        self.assertEqual(cm.exception.detalle['bloques'], ['S01', 'S02'])

    def test_mapa_firmas_agrupa(self) -> None:
        b1 = _bloque('S01', 1, {Dia.MARTES: ['x', 'y']})
        b2 = _bloque('S02', 2, {Dia.MARTES: ['y', 'x']})
        b3 = _bloque('S03', 3, {Dia.MARTES: ['p', 'q']})
        mapa = verify_rotacion.mapa_firmas([b1, b2, b3])
        self.assertEqual(mapa['x|y'], ['S01', 'S02'])
        self.assertEqual(mapa['p|q'], ['S03'])


if __name__ == '__main__':
    unittest.main()
