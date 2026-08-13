"""Pruebas del Orquestador_Build en MODO MUESTRA (tarea 13.1).

Construye la guia en un directorio temporal usando solo el contenido disponible
(portada + 15 fichas reales) y comprueba que:

* el build produce `dist/guia.pdf` y `dist/web/index.html`;
* el PDF emitido pasa el verificador estructural (`verify_pdf.verificar_archivo`)
  con el numero de paginas del Modelo_Paginas;
* el `index.html` existe y **no** contiene `<script>` (HTML estatico, Req 2.4);
* el reporte se marca como NO_PUBLICABLE en modo muestra y enumera los umbrales
  de cobertura omitidos, y sus conteos coinciden con el contenido disponible.

El directorio temporal se limpia al terminar. Solo librería estándar y
`unittest`; sin `assert` fuera de las aserciones del propio framework de test.

_Requirements: 1.8, 2.1, 2.4, 2.6, 10.4, 10.5_
"""

from __future__ import annotations

import dataclasses
import os
import sys
import tempfile
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build, diagramas_postura, verify_pdf  # noqa: E402
from guia.errores import (  # noqa: E402
    E_ASSET_FALTANTE,
    E_ASSET_INVALIDO,
    ErrorAsset,
)


class TestBuildMuestra(unittest.TestCase):
    def test_construye_artefactos_en_dir_temporal(self):
        with tempfile.TemporaryDirectory(prefix="guia_muestra_") as tmp:
            dir_dist = os.path.join(tmp, "dist")
            reporte = build.construir(
                modo=build.MODO_MUESTRA,
                dir_dist=dir_dist,
                con_preflight=False,  # ya lo cubre test_preflight; agiliza el test
            )

            ruta_pdf = os.path.join(dir_dist, build.NOMBRE_PDF)
            ruta_index = os.path.join(dir_dist, build.NOMBRE_WEB, "index.html")

            # Los artefactos existen donde el reporte dice.
            self.assertTrue(os.path.isfile(ruta_pdf))
            self.assertTrue(os.path.isfile(ruta_index))
            self.assertEqual(reporte.ruta_pdf, ruta_pdf)
            self.assertEqual(reporte.ruta_web_index, ruta_index)

            # El PDF pasa el verificador estructural con el conteo del modelo.
            informe = verify_pdf.verificar_archivo(
                ruta_pdf, paginas_esperadas=reporte.paginas_totales
            )
            self.assertEqual(informe.paginas, reporte.paginas_totales)

            # El index es HTML estatico: sin <script>.
            with open(ruta_index, encoding="utf-8") as fh:
                html = fh.read()
            self.assertNotIn("<script", html.lower())
            # Enlaza al PDF descargable (Req 2.7).
            self.assertIn(build.NOMBRE_PDF, html)

        # Al salir del with, el temporal (y todos los artefactos) se limpia.
        self.assertFalse(os.path.exists(dir_dist))

    def test_reporte_muestra_no_publicable_y_conteos(self):
        with tempfile.TemporaryDirectory(prefix="guia_muestra_") as tmp:
            reporte = build.construir(
                modo=build.MODO_MUESTRA,
                dir_dist=os.path.join(tmp, "dist"),
                con_preflight=False,
            )
            # Modo muestra: nunca publicable y con umbrales de cobertura omitidos.
            self.assertFalse(reporte.publicable)
            self.assertEqual(reporte.modo, build.MODO_MUESTRA)
            self.assertTrue(reporte.umbrales_omitidos)

            # Conteos del contenido disponible: 58 fichas reales, todas con QR.
            self.assertEqual(reporte.fichas, 58)
            self.assertEqual(reporte.qr, 58)
            self.assertEqual(reporte.bloques, build.N_BLOQUES_MUESTRA)
            self.assertGreater(reporte.paginas_totales, 0)
            self.assertGreaterEqual(reporte.diagramas, 1)

            # Ejecuta las validaciones estructurales de siempre.
            for etiqueta in (
                "esquema_json",
                "codificacion_winansi",
                "unicidad_rotacion",
                "qr_round_trip",
                "verify_pdf",
                "pdf_control",
                "indice_coherente",
            ):
                self.assertIn(etiqueta, reporte.validaciones)

    def test_main_muestra_retorna_cero(self):
        with tempfile.TemporaryDirectory(prefix="guia_muestra_") as tmp:
            codigo = build.main(["--dir", os.path.join(tmp, "dist")])
            self.assertEqual(codigo, 0)


# --------------------------------------------------------------------------- #
# Assets de los Diagrama_Postura: firma por extension y copia atomica (13.1)
# --------------------------------------------------------------------------- #


def _bytes_validos(extension: str) -> bytes:
    """Carga sintetica minima que cumple la firma de `extension`."""
    if extension == ".webp":
        return b"RIFF" + b"\x20\x00\x00\x00" + b"WEBP" + b"VP8 relleno"
    if extension == ".png":
        return bytes.fromhex("89504E47") + b"\r\n\x1a\n" + b"IHDR"
    if extension == ".avif":
        return b"\x00\x00\x00\x20" + b"ftyp" + b"avif" + b"relleno"
    return b"<?xml version='1.0'?>\n<svg viewBox='0 0 1 1'></svg>"


class TestFirmasAssets(unittest.TestCase):
    """Firma declarada por extension (criterios 5.12, 5.13, 30.10)."""

    def test_las_cuatro_extensiones_declaran_firma(self):
        # Toda Extensiones_Permitidas tiene firma, y no hay firmas de sobra.
        self.assertEqual(
            frozenset(build.FIRMAS),
            frozenset(diagramas_postura.EXTENSIONES_PERMITIDAS),
        )
        self.assertEqual(build.NOMBRE_ASSETS, diagramas_postura.DIR_ASSETS)

    def test_carga_valida_cumple_su_firma(self):
        for extension in (".webp", ".png", ".avif", ".svg"):
            with self.subTest(extension=extension):
                self.assertTrue(
                    build.cumple_firma(_bytes_validos(extension), extension)
                )

    def test_carga_de_otra_extension_no_cumple(self):
        # Un PNG valido no pasa por webp, ni un webp por png, etc.
        for extension in (".webp", ".png", ".avif"):
            for ajena in (".webp", ".png", ".avif"):
                if ajena == extension:
                    continue
                with self.subTest(extension=extension, ajena=ajena):
                    self.assertFalse(
                        build.cumple_firma(_bytes_validos(ajena), extension)
                    )

    def test_webp_exige_las_dos_marcas(self):
        # RIFF en 0 pero sin WEBP en 8: no cumple.
        self.assertFalse(
            build.cumple_firma(b"RIFF" + b"\x20\x00\x00\x00" + b"AVI ", ".webp")
        )

    def test_svg_fuera_de_la_ventana_no_cumple(self):
        relleno = b" " * build.BYTES_FIRMA
        self.assertFalse(build.cumple_firma(relleno + b"<svg", ".svg"))
        self.assertTrue(build.cumple_firma(b" " * 100 + b"<svg", ".svg"))

    def test_extension_sin_firma_declarada_es_error(self):
        with self.assertRaises(ErrorAsset) as ctx:
            build.firma_esperada(".gif")
        self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO)
        self.assertIn(".gif", str(ctx.exception))


class TestCopiaAssetsAtomica(unittest.TestCase):
    """`_copiar_assets_atomico` (criterios 5.6 a 5.10, 5.13, 5.14)."""

    def setUp(self):
        self._raiz_original = diagramas_postura._raiz_proyecto
        self._catalogo_original = diagramas_postura.CATALOGO

    def tearDown(self):
        diagramas_postura._raiz_proyecto = self._raiz_original
        diagramas_postura.CATALOGO = self._catalogo_original

    def _redirigir_fuente(self, raiz: str) -> str:
        """Hace que `ruta_fuente` lea de `raiz` y devuelve el directorio fuente."""
        diagramas_postura._raiz_proyecto = lambda: raiz
        fuente = os.path.join(raiz, *diagramas_postura.DIR_ASSETS.split("/"))
        os.makedirs(fuente, exist_ok=True)
        return fuente

    def test_sin_ningun_asset_termina_y_no_crea_dist_assets(self):
        with tempfile.TemporaryDirectory(prefix="guia_assets_") as tmp:
            self._redirigir_fuente(os.path.join(tmp, "repo"))
            dir_dist = os.path.join(tmp, "dist")
            dir_tmp = os.path.join(dir_dist, ".tmp")
            os.makedirs(dir_tmp)

            for estricto in (False, True):
                with self.subTest(estricto=estricto):
                    copiados, faltantes = build._copiar_assets_atomico(
                        dir_dist, dir_tmp, estricto=estricto
                    )
                    self.assertEqual(copiados, ())
                    self.assertEqual(
                        len(faltantes), len(diagramas_postura.CATALOGO)
                    )
                    self.assertFalse(
                        os.path.exists(build.dir_assets_dist(dir_dist))
                    )

    def test_copia_publica_y_solo_mira_lo_declarado(self):
        with tempfile.TemporaryDirectory(prefix="guia_assets_") as tmp:
            fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
            declarados = diagramas_postura.CATALOGO[:2]
            for diagrama in declarados:
                extension = os.path.splitext(diagrama.archivo)[1].lower()
                with open(os.path.join(fuente, diagrama.archivo), "wb") as fh:
                    fh.write(_bytes_validos(extension))
            # Archivo no declarado en el catalogo: se ignora por completo (5.14).
            with open(os.path.join(fuente, "sobrante.png"), "wb") as fh:
                fh.write(b"esto no es un png")

            dir_dist = os.path.join(tmp, "dist")
            dir_tmp = os.path.join(dir_dist, ".tmp")
            os.makedirs(dir_tmp)
            copiados, faltantes = build._copiar_assets_atomico(
                dir_dist, dir_tmp, estricto=True
            )

            esperados = tuple(
                diagramas_postura.ruta_relativa(d) for d in declarados
            )
            self.assertEqual(copiados, esperados)
            self.assertEqual(
                len(faltantes), len(diagramas_postura.CATALOGO) - len(declarados)
            )
            destino = build.dir_assets_dist(dir_dist)
            for diagrama in declarados:
                self.assertTrue(
                    os.path.isfile(os.path.join(destino, diagrama.archivo))
                )
            self.assertFalse(os.path.exists(os.path.join(destino, "sobrante.png")))
            # Nada queda a medias en dist/.tmp/.
            self.assertEqual(os.listdir(dir_tmp), [])

    def test_firma_invalida_aborta_y_no_publica(self):
        with tempfile.TemporaryDirectory(prefix="guia_assets_") as tmp:
            fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
            diagrama = diagramas_postura.CATALOGO[0]
            with open(os.path.join(fuente, diagrama.archivo), "wb") as fh:
                fh.write(b"contenido que no cumple ninguna firma")

            dir_dist = os.path.join(tmp, "dist")
            dir_tmp = os.path.join(dir_dist, ".tmp")
            os.makedirs(dir_tmp)
            with self.assertRaises(ErrorAsset) as ctx:
                build._copiar_assets_atomico(dir_dist, dir_tmp, estricto=False)

            self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO)
            self.assertIn(diagrama.archivo, str(ctx.exception))
            # Ni se publica ni queda la copia temporal.
            self.assertFalse(os.path.exists(build.dir_assets_dist(dir_dist)))
            self.assertEqual(os.listdir(dir_tmp), [])

    def test_faltante_requerido_en_estricto_lanza_e_asset_faltante(self):
        with tempfile.TemporaryDirectory(prefix="guia_assets_") as tmp:
            self._redirigir_fuente(os.path.join(tmp, "repo"))
            exigente = dataclasses.replace(
                diagramas_postura.CATALOGO[0], requiere_archivo=True
            )
            diagramas_postura.CATALOGO = (exigente,)

            dir_dist = os.path.join(tmp, "dist")
            dir_tmp = os.path.join(dir_dist, ".tmp")
            os.makedirs(dir_tmp)
            with self.assertRaises(ErrorAsset) as ctx:
                build._copiar_assets_atomico(dir_dist, dir_tmp, estricto=True)

            self.assertEqual(ctx.exception.codigo, E_ASSET_FALTANTE)
            self.assertIn(
                diagramas_postura.ruta_relativa(exigente), str(ctx.exception)
            )
            # En Modo_Muestra el mismo catalogo termina sin abortar (5.10).
            copiados, faltantes = build._copiar_assets_atomico(
                dir_dist, dir_tmp, estricto=False
            )
            self.assertEqual(copiados, ())
            self.assertEqual(
                faltantes, (diagramas_postura.ruta_relativa(exigente),)
            )


# --------------------------------------------------------------------------- #
# Build estricto de punta a punta, con y sin Archivo_Diagrama (tarea 14.4)
# --------------------------------------------------------------------------- #


class TestBuildEstrictoConYSinAssets(unittest.TestCase):
    """El build estricto llega a `[PUBLICABLE]` por los dos caminos de render.

    Las Propiedades 15 y 16 miden la copia de assets aislada. Aqui se ejercita el
    pipeline completo en Modo_Estricto sobre un `dist` temporal, que es lo que
    cierra el criterio 5.5: las ocho entradas llevan `requiere_archivo=False`, asi
    que con el directorio fuente vacio los ocho diagramas se rinden con el
    Generador_SVG y el veredicto no cambia; con los ocho archivos colocados se
    copian y el veredicto sigue siendo el mismo.

    La fuente de assets se redirige sustituyendo `diagramas_postura._raiz_proyecto`
    igual que en `TestCopiaAssetsAtomica`: cero escrituras en el repositorio. El
    build estricto es caro (del orden de segundos), asi que se corre exactamente
    dos veces, una por camino, con `con_preflight=False` porque el preflight ya lo
    cubre `test_preflight`.

    _Requirements: 5.5, 13.6_
    """

    def setUp(self):
        self._raiz_original = diagramas_postura._raiz_proyecto

    def tearDown(self):
        diagramas_postura._raiz_proyecto = self._raiz_original

    def _redirigir_fuente(self, raiz: str) -> str:
        """Hace que `ruta_fuente` lea de `raiz` y devuelve el directorio fuente."""
        diagramas_postura._raiz_proyecto = lambda: raiz
        fuente = os.path.join(raiz, *diagramas_postura.DIR_ASSETS.split("/"))
        os.makedirs(fuente, exist_ok=True)
        return fuente

    def test_estricto_sin_ningun_asset_publica_los_ocho_por_svg(self):
        with tempfile.TemporaryDirectory(prefix="guia_estricto_") as tmp:
            # Directorio fuente creado y vacio: ni un byte de Archivo_Diagrama.
            fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
            self.assertEqual(os.listdir(fuente), [])

            dir_dist = os.path.join(tmp, "dist")
            reporte = build.construir(
                modo=build.MODO_ESTRICTO,
                dir_dist=dir_dist,
                con_preflight=False,
            )

            # Veredicto publicable, tambien en el texto del reporte. Se mide con
            # los corchetes: la subcadena "PUBLICABLE" tambien esta dentro de
            # "NO_PUBLICABLE", asi que buscarla suelta no distingue nada.
            self.assertTrue(reporte.publicable)
            self.assertEqual(reporte.modo, build.MODO_ESTRICTO)
            self.assertIn("[PUBLICABLE]", reporte.texto())
            self.assertEqual(reporte.umbrales_omitidos, ())

            # Los ocho se rindieron con el Generador_SVG y no se copio ninguno.
            self.assertEqual(reporte.diagramas_svg, len(diagramas_postura.CATALOGO))
            self.assertEqual(reporte.assets_copiados, 0)
            self.assertEqual(
                len(reporte.assets_faltantes), len(diagramas_postura.CATALOGO)
            )

            # `dist/assets/` no se crea vacio (criterio 5.10).
            self.assertFalse(os.path.exists(build.dir_assets_dist(dir_dist)))
            # Los artefactos de siempre siguen en su sitio.
            self.assertTrue(os.path.isfile(reporte.ruta_pdf))
            self.assertTrue(os.path.isfile(reporte.ruta_web_index))

    def test_estricto_con_los_ocho_archivos_los_copia_y_sigue_publicable(self):
        with tempfile.TemporaryDirectory(prefix="guia_estricto_") as tmp:
            fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
            # Cargas sinteticas con la firma que exige cada extension. Se reusa el
            # ayudante deterministico de este archivo en vez de `gen_bytes_asset`,
            # que sortea extension y validez: un ejemplo no quiere azar.
            for diagrama in diagramas_postura.CATALOGO:
                extension = os.path.splitext(diagrama.archivo)[1].lower()
                with open(os.path.join(fuente, diagrama.archivo), "wb") as fh:
                    fh.write(_bytes_validos(extension))

            dir_dist = os.path.join(tmp, "dist")
            reporte = build.construir(
                modo=build.MODO_ESTRICTO,
                dir_dist=dir_dist,
                con_preflight=False,
            )

            self.assertTrue(reporte.publicable)
            self.assertIn("[PUBLICABLE]", reporte.texto())

            # Camino contrario al de la prueba anterior: todo por archivo.
            self.assertEqual(
                reporte.assets_copiados, len(diagramas_postura.CATALOGO)
            )
            self.assertEqual(reporte.diagramas_svg, 0)
            self.assertEqual(reporte.assets_faltantes, ())

            # Los ocho quedan publicados en `dist/assets/img/tecnica/`.
            destino = build.dir_assets_dist(dir_dist)
            for diagrama in diagramas_postura.CATALOGO:
                with self.subTest(diagrama=diagrama.id):
                    self.assertTrue(
                        os.path.isfile(os.path.join(destino, diagrama.archivo))
                    )
            self.assertIn("firma_assets", reporte.validaciones)


if __name__ == "__main__":
    unittest.main()
