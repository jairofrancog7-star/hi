"""Guardarrail de contenido: ninguna ficha del Catalogo_JSON queda a medias.

Una ficha sirve a la entrenadora solo si trae los CINCO campos que la vuelven
aplicable en una sesion real. Este archivo veta que alguna de las 58 fichas de
`contenido/ejercicios.json` se publique sin:

1. **dosis completa**: `dosis` es un objeto y sus cinco claves (`cuando`,
   `duracion`, `jugadoras`, `material`, `meta`) existen y no vienen vacias;
2. **progresion**: alguna linea de `pasos` arranca con el prefijo de progresion;
3. **metrica de mejora**: alguna linea de `pasos` arranca con ese prefijo;
4. **diagrama de cancha**: `cancha` existe, es objeto y NO esta vacio;
5. **variante para 1-8 jugadoras**: alguna linea de `pasos` arranca con el
   prefijo de variante.

DOS GRAFIAS, LAS DOS VALIDAS. El catalogo escribe el prefijo de progresion de
dos maneras: las fichas 1-15 y 51-58 lo escriben sin acento y las fichas 16-50
lo escriben con acento en la "o". Ninguna de las dos es un error y el JSON no se
toca, asi que el verificador **no** compara texto crudo: normaliza cada linea
quitando las marcas diacriticas (`unicodedata.normalize('NFD', ...)` filtrando
la categoria `Mn`) y pasando a minusculas, y solo entonces busca `progresion:`,
`metrica de mejora:` y `variante 1-8`.

Cuando una ficha falla, el mensaje nombra su `numero`, su `id` y el campo que
falta, para que la correccion sea directa.

Solo libreria estandar y `unittest`.

_Requirements: 11.2, 11.3, 12.4_
"""

from __future__ import annotations

import copy
import os
import sys
import unicodedata
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import schema_json  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402

#: Claves obligatorias dentro de `dosis` (se reutiliza la lista del schema).
CLAVES_DOSIS: tuple[str, ...] = schema_json.CLAVES_DOSIS

#: Prefijo normalizado (sin acentos, en minusculas) de la linea de progresion.
PREFIJO_PROGRESION = "progresion:"

#: Prefijo normalizado de la linea con la metrica de mejora.
PREFIJO_METRICA = "metrica de mejora:"

#: Prefijo normalizado de la linea con la variante para 1-8 jugadoras.
PREFIJO_VARIANTE = "variante 1-8"


def normalizar(texto: str) -> str:
    """Devuelve `texto` sin marcas diacriticas y en minusculas.

    Asi `Progresion:` y `Progresión:` colapsan en la misma cadena y el
    guardarrail acepta las dos grafias que hoy conviven en el catalogo.
    """
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )
    return sin_acentos.lower()


def _tiene_paso_con_prefijo(ficha: dict, prefijo: str) -> bool:
    """`True` si alguna linea de `pasos` empieza por `prefijo` normalizado."""
    pasos = ficha.get("pasos")
    if not isinstance(pasos, list):
        return False
    return any(
        isinstance(paso, str) and normalizar(paso.strip()).startswith(prefijo)
        for paso in pasos
    )


def _faltantes_de_dosis(ficha: dict) -> list[str]:
    """Claves de `dosis` ausentes o vacias en `ficha`."""
    dosis = ficha.get("dosis")
    if not isinstance(dosis, dict):
        return ["dosis (no es un objeto)"]
    ausentes: list[str] = []
    for clave in CLAVES_DOSIS:
        valor = dosis.get(clave)
        if not isinstance(valor, str) or not valor.strip():
            ausentes.append(f"dosis.{clave}")
    return ausentes


def campos_faltantes(ficha: dict) -> list[str]:
    """Lista legible de los cinco campos obligatorios que le faltan a `ficha`."""
    faltantes: list[str] = list(_faltantes_de_dosis(ficha))

    if not _tiene_paso_con_prefijo(ficha, PREFIJO_PROGRESION):
        faltantes.append("progresion (ninguna linea de 'pasos' la declara)")
    if not _tiene_paso_con_prefijo(ficha, PREFIJO_METRICA):
        faltantes.append("metrica de mejora (ninguna linea de 'pasos' la declara)")
    if not _tiene_paso_con_prefijo(ficha, PREFIJO_VARIANTE):
        faltantes.append("variante 1-8 jugadoras (ninguna linea de 'pasos' la declara)")

    cancha = ficha.get("cancha")
    if not isinstance(cancha, dict) or not cancha:
        faltantes.append("cancha (diagrama ausente o vacio)")

    return faltantes


def buscar_fichas_incompletas(fichas: list[dict]) -> list[str]:
    """Devuelve un hallazgo accionable por cada ficha incompleta."""
    hallazgos: list[str] = []
    for ficha in fichas:
        faltantes = campos_faltantes(ficha)
        if not faltantes:
            continue
        hallazgos.append(
            f"ficha numero {ficha.get('numero')!r} (id {ficha.get('id')!r}) "
            f"incompleta: falta {', '.join(faltantes)}"
        )
    return hallazgos


def _catalogo() -> list[dict]:
    """Carga el Catalogo_JSON real, ya validado por el schema."""
    return schema_json.cargar_catalogo(cap10_fundamentos.ruta_catalogo())


class TestCompletitudDeFichas(unittest.TestCase):
    """Las 58 fichas del Catalogo_JSON traen los cinco campos obligatorios."""

    def test_catalogo_sin_fichas_incompletas(self) -> None:
        hallazgos = buscar_fichas_incompletas(_catalogo())
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_las_dos_grafias_de_progresion_se_aceptan(self) -> None:
        """`Progresion:` y `Progresión:` valen igual: el catalogo usa ambas."""
        self.assertTrue(normalizar("Progresion: sube el ritmo").startswith(
            PREFIJO_PROGRESION
        ))
        self.assertTrue(normalizar("Progresión: sube el ritmo").startswith(
            PREFIJO_PROGRESION
        ))

    def test_el_guardarrail_detecta_una_ficha_sin_metrica(self) -> None:
        """Cordura: si a una ficha se le quita la metrica, el verificador la caza."""
        fichas = copy.deepcopy(_catalogo())
        victima = fichas[0]
        victima["pasos"] = [
            paso
            for paso in victima["pasos"]
            if not normalizar(paso.strip()).startswith(PREFIJO_METRICA)
        ]

        hallazgos = buscar_fichas_incompletas(fichas)
        self.assertEqual(
            len(hallazgos), 1, f"se esperaba un solo hallazgo: {hallazgos}"
        )
        self.assertIn("metrica de mejora", hallazgos[0])
        self.assertIn(repr(victima["id"]), hallazgos[0])
        self.assertIn(repr(victima["numero"]), hallazgos[0])

    def test_el_guardarrail_detecta_dosis_y_cancha_incompletas(self) -> None:
        """Cordura: dosis vacia y cancha vacia tambien son hallazgos."""
        fichas = copy.deepcopy(_catalogo())
        fichas[0]["dosis"]["meta"] = "   "
        fichas[1]["cancha"] = {}

        hallazgos = buscar_fichas_incompletas(fichas)
        self.assertEqual(len(hallazgos), 2, f"hallazgos: {hallazgos}")
        self.assertIn("dosis.meta", hallazgos[0])
        self.assertIn("cancha", hallazgos[1])


if __name__ == "__main__":
    unittest.main()
