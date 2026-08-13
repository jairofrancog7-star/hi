"""Pruebas unitarias del preflight y de la jerarquia de errores (tarea 1.1)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Bootstrap de rutas: `unittest discover -s test` importa este archivo como
# modulo de nivel superior, asi que `test/__init__.py` no corre. Cada modulo de
# prueba pone `src/` en sys.path por su cuenta (convencion del proyecto).
_DIR_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'
)
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import preflight  # noqa: E402
from guia.errores import ErrorBuild, ErrorDependencia, ErrorLayout  # noqa: E402


class TestJerarquiaErrores(unittest.TestCase):
    def test_codigo_explicito_en_la_raiz(self):
        err = ErrorBuild('E_PAGINACION_INESTABLE', '251 -> 252')
        self.assertEqual(err.codigo, 'E_PAGINACION_INESTABLE')
        self.assertIn('251 -> 252', str(err))

    def test_subclase_aporta_su_codigo(self):
        err = ErrorDependencia('falta el componente: zlib')
        self.assertEqual(err.codigo, 'E_DEPENDENCIA')
        self.assertTrue(str(err).startswith('E_DEPENDENCIA: '))
        self.assertIsInstance(err, ErrorBuild)

    def test_error_layout_arrastra_contexto(self):
        err = ErrorLayout(
            'desborde de texto en la ficha',
            detalle={'folio': 12, 'ficha_id': 'del_1v1'},
            codigo='E_DESBORDE_TEXTO',
        )
        self.assertEqual(err.codigo, 'E_DESBORDE_TEXTO')
        self.assertEqual(err.detalle['folio'], 12)
        self.assertIn('ficha_id=del_1v1', str(err))
        self.assertIsInstance(err, ErrorBuild)


class TestPreflight(unittest.TestCase):
    def test_entorno_actual_pasa(self):
        reporte = preflight.ejecutar()
        self.assertGreaterEqual(reporte.archivos_analizados, 1)
        for nombre in sorted(preflight.MODULOS_BASE):
            self.assertIn(nombre, reporte.modulos_presentes)

    def test_modulos_de_fases_posteriores_se_reportan_no_revientan(self):
        _, pendientes = preflight.comprobar_modulos()
        conocidos = set(preflight.MODULOS_PIPELINE)
        self.assertTrue(set(pendientes).issubset(conocidos))
        self.assertFalse(set(pendientes) & preflight.MODULOS_BASE)

    def test_dependencia_externa_falla_con_e_dependencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / 'guia'
            raiz.mkdir()
            (raiz / '__init__.py').write_text('', encoding='utf-8')
            (raiz / 'malo.py').write_text(
                'import json\nimport reportlab\n', encoding='utf-8'
            )
            with self.assertRaises(ErrorDependencia) as caja:
                preflight.comprobar_arbol_stdlib(raiz)
        mensaje = str(caja.exception)
        self.assertEqual(caja.exception.codigo, 'E_DEPENDENCIA')
        self.assertIn('reportlab', mensaje)
        self.assertIn('malo.py:2', mensaje)

    def test_arbol_de_solo_stdlib_pasa(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / 'guia'
            raiz.mkdir()
            (raiz / '__init__.py').write_text('', encoding='utf-8')
            (raiz / 'bueno.py').write_text(
                'import zlib\nfrom . import errores\nfrom guia import preflight\n',
                encoding='utf-8',
            )
            archivos, usados = preflight.comprobar_arbol_stdlib(raiz)
        self.assertEqual(archivos, 2)
        self.assertIn('zlib', usados)


if __name__ == '__main__':
    unittest.main()
