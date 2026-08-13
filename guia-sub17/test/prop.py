"""Motor de property-based testing propio sobre la librería estándar.

Hypothesis requeriría `pip`, que no está disponible en este entorno, así que
este módulo implementa un generador de propiedades minimalista (~200 líneas)
con `random.Random(semilla)` y **shrinking propio** sobre enteros (reducción
hacia 0), listas y tuplas (quitando elementos y por mitades) y strings
(acortando y simplificando caracteres).

Uso típico desde un `unittest.TestCase`::

    from prop import for_all

    ETQ = 'Feature: guia-entrenamiento-femenil-extensa, Property N: <texto>'

    class TestAlgo(unittest.TestCase):
        def test_algo(self):
            \"\"\"Feature: guia-entrenamiento-femenil-extensa, Property N: <texto>\"\"\"
            def prop(valor):
                self.assertTrue(invariante(valor))
            for_all(gen, prop, iteraciones=100, etiqueta=ETQ)

Semilla: se lee de la variable de entorno ``SEMILLA_PBT`` cuando está presente
(uso en CI); en local se elige aleatoria y se imprime en el mensaje de fallo
para poder reproducir el contraejemplo.

Nota de estilo del proyecto: nada de `assert` en el código (`python -O` los
borra); todo invariante interno se expresa con `raise`. `FalloPropiedad` sí
hereda de `AssertionError` porque es la excepción del *marco de pruebas* y debe
comportarse como un fallo de aserción ante `unittest`.
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable, Iterator
from typing import TypeVar

T = TypeVar("T")

ITERACIONES_POR_DEFECTO: int = 100
MAX_PASOS_SHRINK: int = 500

__all__ = [
    "FalloPropiedad",
    "ITERACIONES_POR_DEFECTO",
    "MAX_PASOS_SHRINK",
    "for_all",
    "semilla_activa",
]


class FalloPropiedad(AssertionError):
    """Fallo de una propiedad con contraejemplo minimizado y semilla.

    Hereda de `AssertionError` para que `unittest` lo trate como un fallo de
    prueba (y no como un error inesperado). El mensaje incluye el contraejemplo
    ya reducido por el shrinker, la causa original y la semilla necesaria para
    reproducir la ejecución.
    """


def semilla_activa(semilla: int | None) -> int:
    """Resuelve la semilla a usar.

    Precedencia: argumento explícito > variable de entorno ``SEMILLA_PBT`` >
    semilla aleatoria de 31 bits. Devuelve siempre un entero, de modo que el
    valor pueda imprimirse y reproducirse.
    """
    if semilla is not None:
        return semilla
    del_entorno: str | None = os.environ.get("SEMILLA_PBT")
    if del_entorno:
        return int(del_entorno)
    return random.randrange(2**31)


def for_all(
    gen: Callable[[random.Random], T],
    prop: Callable[[T], None],
    *,
    iteraciones: int = ITERACIONES_POR_DEFECTO,
    semilla: int | None = None,
    etiqueta: str = "",
) -> None:
    """Ejecuta ``prop`` sobre ``iteraciones`` valores producidos por ``gen``.

    ``gen`` recibe el PRNG y devuelve un caso de prueba. ``prop`` recibe ese
    caso y debe lanzar (típicamente vía ``self.assertX``) cuando el invariante
    no se cumple. Al primer fallo, el contraejemplo se minimiza con el shrinker
    y se reporta con la semilla para reproducir.
    """
    if iteraciones <= 0:
        raise ValueError(f"iteraciones debe ser positivo, no {iteraciones!r}")

    semilla_usada: int = semilla_activa(semilla)
    rnd: random.Random = random.Random(semilla_usada)

    for indice in range(iteraciones):
        valor: T = gen(rnd)
        try:
            prop(valor)
        except Exception as causa_original:
            minimo, causa = _minimizar(valor, prop)
            raise FalloPropiedad(
                _mensaje_fallo(etiqueta, indice, semilla_usada, minimo, causa)
            ) from causa_original


def _mensaje_fallo(
    etiqueta: str,
    iteracion: int,
    semilla: int,
    contraejemplo: object,
    causa: str,
) -> str:
    """Compone el mensaje de fallo sin concatenar strings en bucle."""
    lineas: list[str] = [
        etiqueta,
        f"  fallo en la iteracion {iteracion} con semilla={semilla}",
        f"  reproducir con: SEMILLA_PBT={semilla}",
        f"  contraejemplo minimizado: {contraejemplo!r}",
        f"  causa: {causa}",
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Shrinking
# --------------------------------------------------------------------------- #


def _minimizar(
    valor: object,
    prop: Callable[..., None],
    *,
    max_pasos: int = MAX_PASOS_SHRINK,
) -> tuple[object, str]:
    """Reduce ``valor`` al menor caso que sigue haciendo fallar ``prop``.

    Estrategia de shrinking: enteros hacia 0, listas y tuplas quitando
    elementos y por mitades, strings acortando y simplificando caracteres.
    Explora candidatos progresivamente más simples y adopta el primero que
    siga fallando, repitiendo hasta que ningún candidato falle o se agoten los
    pasos. Devuelve el par ``(contraejemplo, causa)``.
    """
    mejor: object = valor
    causa: str = _falla(valor, prop) or "desconocida"
    pasos: int = 0
    progreso: bool = True

    while progreso and pasos < max_pasos:
        progreso = False
        for candidato in _candidatos(mejor):
            if pasos >= max_pasos:
                break
            pasos += 1
            nueva_causa: str | None = _falla(candidato, prop)
            if nueva_causa is not None:
                mejor = candidato
                causa = nueva_causa
                progreso = True
                break

    return mejor, causa


def _falla(valor: object, prop: Callable[..., None]) -> str | None:
    """Devuelve la causa formateada si ``prop`` falla con ``valor``; si no, None."""
    try:
        prop(valor)
    except Exception as exc:  # noqa: BLE001 - el shrinker prueba cualquier fallo
        return f"{type(exc).__name__}: {exc}"
    return None


def _candidatos(valor: object) -> Iterator[object]:
    """Produce versiones más simples de ``valor`` según su tipo.

    El orden va de lo más agresivo (valor vacío / cero) a lo más fino (reducir
    un solo elemento o carácter), para que el shrinker converja rápido.
    """
    # bool antes que int: es una subclase de int y su forma simple es False.
    if isinstance(valor, bool):
        if valor:
            yield False
        return
    if isinstance(valor, int):
        yield from _candidatos_int(valor)
        return
    if isinstance(valor, str):
        yield from _candidatos_str(valor)
        return
    if isinstance(valor, (list, tuple)):
        yield from _candidatos_secuencia(valor)
        return
    # Tipos no soportados por el shrinker se dejan como están.


def _candidatos_int(valor: int) -> Iterator[int]:
    """Enteros más cercanos a 0: salto directo, mitades y paso unitario."""
    if valor == 0:
        return
    yield 0
    actual: int = valor
    while abs(actual) > 1:
        actual = int(actual / 2)
        yield actual
    yield valor - 1 if valor > 0 else valor + 1


def _candidatos_str(valor: str) -> Iterator[str]:
    """Strings: vacío, mitades, quitar un carácter y simplificar caracteres."""
    if not valor:
        return
    yield ""
    mitad: int = len(valor) // 2
    if mitad > 0:
        yield valor[:mitad]
        yield valor[mitad:]
    for i in range(len(valor)):
        yield valor[:i] + valor[i + 1 :]
    objetivo: int = ord("a")
    for i, caracter in enumerate(valor):
        if ord(caracter) > objetivo:
            partes: list[str] = [valor[:i], "a", valor[i + 1 :]]
            yield "".join(partes)


def _candidatos_secuencia(valor: list | tuple) -> Iterator[list | tuple]:
    """Listas y tuplas: vacío, mitades, quitar un elemento y reducir elementos."""
    elementos: list = list(valor)
    constructor: Callable[[list], object] = (
        tuple if isinstance(valor, tuple) else list
    )
    if not elementos:
        return
    yield constructor([])
    mitad: int = len(elementos) // 2
    if mitad > 0:
        yield constructor(elementos[:mitad])
        yield constructor(elementos[mitad:])
    for i in range(len(elementos)):
        yield constructor(elementos[:i] + elementos[i + 1 :])
    for i, elemento in enumerate(elementos):
        for reducido in _candidatos(elemento):
            copia: list = list(elementos)
            copia[i] = reducido
            yield constructor(copia)
