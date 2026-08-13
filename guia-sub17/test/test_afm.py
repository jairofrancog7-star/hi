"""Pruebas de `guia.afm`: medición de texto y codificación WinAnsi.

Cubre la tarea 1.5:
* round-trip cp1252 de textos con acentos y ñ,
* anchos conocidos de Helvetica y Helvetica-Bold,
* envoltura de palabras más largas que la caja,
* `E_CARACTER_NO_CODIFICABLE` ante un carácter fuera de WinAnsiEncoding.

_Requirements: 1.6, 2.3_
"""

from __future__ import annotations

import os
import sys
import unittest

# Bootstrap de rutas: `unittest discover -s test` importa este archivo como
# modulo de nivel superior, asi que `test/__init__.py` no corre. Cada modulo de
# prueba pone `src/` en sys.path por su cuenta (convencion del proyecto).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import afm  # noqa: E402
from guia.errores import E_CARACTER_NO_CODIFICABLE, ErrorBuild  # noqa: E402


class TestCodificacionWinAnsi(unittest.TestCase):
    """Round-trip cp1252 y detección de caracteres no codificables."""

    def test_round_trip_acentos_y_enie(self) -> None:
        textos = [
            'Entrenamiento femenil',
            'canción, corazón y compañía',
            'La niña anotó un gol increíble',
            '¿Cómo estás? ¡Vamos! -- «cita»',
            'Ábaco Éxito Índice Óvalo Único',
        ]
        for texto in textos:
            with self.subTest(texto=texto):
                crudos = afm.codificar_winansi(texto, ctx='prueba')
                self.assertIsInstance(crudos, bytes)
                # El round-trip devuelve exactamente el texto original.
                self.assertEqual(crudos.decode('cp1252'), texto)

    def test_enie_es_un_solo_byte(self) -> None:
        crudos = afm.codificar_winansi('ñ', ctx='prueba')
        self.assertEqual(crudos, b'\xf1')

    def test_caracter_fuera_de_winansi_falla(self) -> None:
        # Un emoji no existe en WinAnsiEncoding.
        with self.assertRaises(ErrorBuild) as cm:
            afm.codificar_winansi('gol \U0001F600 festejo', ctx='ficha-42')
        err = cm.exception
        self.assertEqual(err.codigo, E_CARACTER_NO_CODIFICABLE)
        # El mensaje localiza el carácter, su code point y su contexto.
        self.assertIn('U+1F600', str(err))
        self.assertIn('ficha-42', str(err))
        self.assertEqual(err.detalle['posicion'], 4)
        self.assertEqual(err.detalle['caracter'], '\U0001F600')

    def test_otro_caracter_no_codificable_guion_largo_unicode(self) -> None:
        # El guion largo horizontal U+2015 no está en cp1252.
        with self.assertRaises(ErrorBuild) as cm:
            afm.codificar_winansi('rango 1\u20155', ctx='dosis')
        self.assertEqual(cm.exception.codigo, E_CARACTER_NO_CODIFICABLE)


class TestEscaparLiteralPDF(unittest.TestCase):
    """Escape de los metacaracteres de literal de cadena PDF."""

    def test_escapa_barra_y_parentesis(self) -> None:
        crudos = b'ruta\\ (a) y (b)'
        esperado = b'ruta\\\\ \\(a\\) y \\(b\\)'
        self.assertEqual(afm.escapar_literal_pdf(crudos), esperado)

    def test_texto_sin_metacaracteres_no_cambia(self) -> None:
        crudos = 'texto normal'.encode('cp1252')
        self.assertEqual(afm.escapar_literal_pdf(crudos), crudos)


class TestMedirTexto(unittest.TestCase):
    """Anchos conocidos de las métricas AFM."""

    def test_ancho_conocido_helvetica(self) -> None:
        # 'A' mide 667 unidades/1000; a 10 pt son 6.67 pt.
        self.assertAlmostEqual(afm.medir_texto('A', 'Helvetica', 10.0), 6.67, places=4)
        # espacio = 278 -> 2.78 pt a 10 pt.
        self.assertAlmostEqual(afm.medir_texto(' ', 'Helvetica', 10.0), 2.78, places=4)

    def test_ancho_conocido_helvetica_bold(self) -> None:
        # 'A' en negrita mide 722 unidades/1000; a 10 pt son 7.22 pt.
        self.assertAlmostEqual(
            afm.medir_texto('A', 'Helvetica-Bold', 10.0), 7.22, places=4
        )

    def test_ancho_palabra_es_suma_de_glifos(self) -> None:
        # 'Hola': H=722, o=556, l=222, a=556 -> 2056/1000 * 10 = 20.56 pt.
        self.assertAlmostEqual(
            afm.medir_texto('Hola', 'Helvetica', 10.0), 20.56, places=4
        )

    def test_escala_lineal_con_el_tamano(self) -> None:
        base = afm.medir_texto('Entrenamiento', 'Helvetica', 10.0)
        doble = afm.medir_texto('Entrenamiento', 'Helvetica', 20.0)
        self.assertAlmostEqual(doble, base * 2.0, places=4)

    def test_acentuada_mide_igual_que_base(self) -> None:
        # En Helvetica el acento no cambia el avance: 'á' == 'a', 'ñ' == 'n'.
        self.assertAlmostEqual(
            afm.medir_texto('á', 'Helvetica', 12.0),
            afm.medir_texto('a', 'Helvetica', 12.0),
            places=4,
        )
        self.assertAlmostEqual(
            afm.medir_texto('ñ', 'Helvetica', 12.0),
            afm.medir_texto('n', 'Helvetica', 12.0),
            places=4,
        )

    def test_texto_vacio_mide_cero(self) -> None:
        self.assertEqual(afm.medir_texto('', 'Helvetica', 10.0), 0.0)

    def test_fuente_no_soportada(self) -> None:
        with self.assertRaises(ValueError):
            afm.medir_texto('x', 'Times-Roman', 10.0)


class TestEnvolver(unittest.TestCase):
    """Envoltura de texto en líneas que caben en una caja dada."""

    def test_devuelve_tupla(self) -> None:
        resultado = afm.envolver('una dos tres', 100.0, 'Helvetica', 10.0)
        self.assertIsInstance(resultado, tuple)

    def test_toda_linea_cabe_en_la_caja(self) -> None:
        ancho = 80.0
        texto = 'La niña entrena todos los días con energía y disciplina'
        lineas = afm.envolver(texto, ancho, 'Helvetica', 10.0)
        for linea in lineas:
            with self.subTest(linea=linea):
                self.assertLessEqual(
                    afm.medir_texto(linea, 'Helvetica', 10.0), ancho + 1e-6
                )

    def test_conserva_todas_las_palabras(self) -> None:
        texto = 'pase corto y salida limpia desde el fondo'
        lineas = afm.envolver(texto, 60.0, 'Helvetica', 10.0)
        self.assertEqual(' '.join(lineas).split(), texto.split())

    def test_palabra_mas_larga_que_la_caja_se_parte(self) -> None:
        ancho = 30.0
        palabra = 'supercalifragilisticoespialidoso'
        # La palabra completa no cabe.
        self.assertGreater(afm.medir_texto(palabra, 'Helvetica', 10.0), ancho)
        lineas = afm.envolver(palabra, ancho, 'Helvetica', 10.0)
        self.assertGreater(len(lineas), 1)
        # Cada trozo cabe y juntos reconstruyen la palabra.
        for linea in lineas:
            with self.subTest(linea=linea):
                self.assertLessEqual(
                    afm.medir_texto(linea, 'Helvetica', 10.0), ancho + 1e-6
                )
        self.assertEqual(''.join(lineas), palabra)

    def test_texto_vacio_devuelve_tupla_vacia(self) -> None:
        self.assertEqual(afm.envolver('   ', 100.0, 'Helvetica', 10.0), ())

    def test_ancho_no_positivo_falla(self) -> None:
        with self.assertRaises(ValueError):
            afm.envolver('texto', 0.0, 'Helvetica', 10.0)


class TestTablasModulo(unittest.TestCase):
    """Las tablas AFM se construyen una vez con 256 entradas."""

    def test_longitud_de_las_tablas(self) -> None:
        self.assertEqual(len(afm.ANCHOS_HELV), 256)
        self.assertEqual(len(afm.ANCHOS_HELV_BOLD), 256)

    def test_indexadas_por_byte_cp1252(self) -> None:
        # 'A' es el byte 0x41 = 65; su ancho Helvetica es 667.
        self.assertAlmostEqual(afm.ANCHOS_HELV[ord('A')], 667.0, places=4)
        # 'ñ' es el byte 0xF1 = 241; su ancho Helvetica es 556 (= 'n').
        self.assertAlmostEqual(afm.ANCHOS_HELV[0xF1], 556.0, places=4)


if __name__ == '__main__':
    unittest.main()
