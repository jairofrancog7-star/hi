"""Pruebas de `guia.qr` + `guia.qr_decode`: round-trip del código QR.

Cubre las tareas 2.2 y 2.3:
* Property 4 (round-trip): decodificar la matriz producida por el codificador
  devuelve exactamente la URL de origen, byte por byte.
* Casos unitarios de versiones 1..6, contenido multibyte UTF-8, lectura de la
  máscara y verificación de round-trip (`E_QR_NO_VERIFICA`).

_Requirements: 9.6, 9.7, 9.8_
"""

from __future__ import annotations

import os
import random
import sys
import unittest

# Bootstrap de rutas: cada módulo de prueba pone `src/` y `test/` en sys.path
# por su cuenta (convención del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

from guia import qr, qr_decode  # noqa: E402
from guia.errores import E_QR_NO_VERIFICA, ErrorBuild  # noqa: E402
from prop import for_all  # noqa: E402

# Capacidad de datos en byte mode para v1..6 nivel L (bytes de la URL):
# _DATOS_CW_L[v] - 2 (indicador de modo + contador). El máximo es v6 = 134.
_MAX_BYTES_URL = qr._DATOS_CW_L[6] - 2

_URL_ALFABETO = "abcdefghijklmnopqrstuvwxyz0123456789-_/."
_ESQUEMAS = ("http://", "https://")
_DOMINIOS = ("v.club", "sub17.mx", "video.ejemplo.org")


def gen_url_qr(rnd: random.Random) -> str:
    """URL http/https cuya longitud en bytes cabe en un QR v1..6 nivel L.

    Cubre todo el rango de versiones: entre 8 y 134 bytes UTF-8, con esquema y
    dominio realistas y una ruta de relleno. El corte final garantiza que
    `len(url.encode('utf-8')) <= 134`.
    """
    objetivo = rnd.randint(8, _MAX_BYTES_URL)
    prefijo = f"{rnd.choice(_ESQUEMAS)}{rnd.choice(_DOMINIOS)}/"
    restante = max(1, objetivo - len(prefijo))
    ruta = [rnd.choice(_URL_ALFABETO) for _ in range(restante)]
    url = prefijo + "".join(ruta)
    # Recorte a la capacidad exacta en bytes (ASCII => 1 byte por carácter).
    crudos = url.encode("utf-8")
    if len(crudos) > _MAX_BYTES_URL:
        url = crudos[:_MAX_BYTES_URL].decode("utf-8")
    return url


ETQ_P4 = (
    "Feature: guia-entrenamiento-femenil-extensa, "
    "Property 4: Todo QR decodifica a su URL de origen"
)


class TestRoundTripPropiedad(unittest.TestCase):
    """Property 4: todo QR decodifica a su URL de origen."""

    def setUp(self) -> None:
        qr.limpiar_cache()

    def test_property_4_round_trip(self) -> None:
        """Feature: guia-entrenamiento-femenil-extensa, Property 4: Todo QR decodifica a su URL de origen.

        **Validates: Requirements 9.7, 9.6**
        """

        def propiedad(url: str) -> None:
            matriz = qr.codificar(url)
            self.assertEqual(qr_decode.decodificar(matriz), url)

        for_all(gen_url_qr, propiedad, iteraciones=200, etiqueta=ETQ_P4)


class TestRoundTripUnitario(unittest.TestCase):
    """Ejemplos y casos borde del round-trip codificar -> decodificar."""

    def setUp(self) -> None:
        qr.limpiar_cache()

    def test_urls_de_ejemplo(self) -> None:
        urls = (
            "http://a.b/c",
            "http://v.club/abc",
            "https://sub17.mx/definicion-remate",
            "https://video.ejemplo.org/watch/1234567890",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(qr_decode.decodificar(qr.codificar(url)), url)

    def test_cubre_versiones_1_a_6(self) -> None:
        vistas: set[int] = set()
        for n in range(1, _MAX_BYTES_URL + 1):
            url = "http://v.club/" + "a" * n
            if len(url.encode("utf-8")) > _MAX_BYTES_URL:
                break
            matriz = qr.codificar(url)
            vistas.add(matriz.version)
            self.assertEqual(qr_decode.decodificar(matriz), url)
        # El barrido de longitudes debe tocar todas las versiones 1..6.
        self.assertEqual(vistas, {1, 2, 3, 4, 5, 6})

    def test_contenido_multibyte_utf8(self) -> None:
        url = "https://sub17.mx/ñáéíóú-señalización-área"
        self.assertEqual(qr_decode.decodificar(qr.codificar(url)), url)

    def test_lee_la_misma_mascara_que_eligio_el_codificador(self) -> None:
        matriz = qr.codificar("https://video.ejemplo.org/tecnica")
        self.assertEqual(qr_decode._leer_mascara(matriz), matriz.mascara)

    def test_version_deducida_del_lado(self) -> None:
        for url_len in (5, 40, 90):
            url = "http://v.club/" + "z" * url_len
            matriz = qr.codificar(url)
            with self.subTest(version=matriz.version):
                self.assertEqual((matriz.lado - 17) // 4, matriz.version)


class TestVerificarQR(unittest.TestCase):
    """Verificación de round-trip que lanza `E_QR_NO_VERIFICA`."""

    def setUp(self) -> None:
        qr.limpiar_cache()

    def test_round_trip_correcto_no_lanza(self) -> None:
        url = "https://video.ejemplo.org/pase-corto"
        # No debe lanzar.
        qr_decode.verificar_qr(url, qr.codificar(url), id_ficha="ficha-ok")

    def test_matriz_corrupta_lanza_con_id_y_url(self) -> None:
        url = "http://v.club/abc"
        matriz = qr.codificar(url)
        # Corromper suficientes módulos para exceder la corrección Reed-Solomon.
        modulos = matriz.modulos()
        for i in range(0, len(modulos), 2):
            modulos[i] ^= 1
        with self.assertRaises(ErrorBuild) as cm:
            qr_decode.verificar_qr(url, matriz, id_ficha="ficha-77")
        err = cm.exception
        self.assertEqual(err.codigo, E_QR_NO_VERIFICA)
        self.assertIn("ficha-77", str(err))
        self.assertIn(url, str(err))
        self.assertEqual(err.detalle["id"], "ficha-77")
        self.assertEqual(err.detalle["url"], url)

    def test_reporta_url_leida_distinta(self) -> None:
        # Verificar contra una URL distinta de la codificada debe fallar y
        # reportar la URL leída realmente.
        codificada = "http://v.club/abc"
        esperada = "http://v.club/xyz"
        matriz = qr.codificar(codificada)
        with self.assertRaises(ErrorBuild) as cm:
            qr_decode.verificar_qr(esperada, matriz, id_ficha="ficha-9")
        self.assertEqual(cm.exception.codigo, E_QR_NO_VERIFICA)
        self.assertEqual(cm.exception.detalle["leida"], codificada)


if __name__ == "__main__":
    unittest.main()
