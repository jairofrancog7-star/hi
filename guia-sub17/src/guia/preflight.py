"""Preflight: comprobaciones de entorno previas a cualquier fase del build.

Es la validacion 1 del diseno y la primera fase del Orquestador_Build. Comprueba
cuatro cosas y falla con `E_DEPENDENCIA` nombrando el componente afectado:

a) `sys.version_info >= (3, 11)`.
b) `import zlib` funciona (el Motor_PDF comprime todo stream con FlateDecode).
c) Cada modulo del pipeline es importable. Los modulos de fases posteriores que
   todavia no existen se **reportan como pendientes**, no revientan el preflight:
   durante la construccion del pipeline el arbol esta incompleto por diseno.
d) El arbol de imports del paquete `guia` no contiene ningun modulo fuera de
   `sys.stdlib_module_names`. Esto cubre el riesgo de que alguien meta una
   dependencia externa (reportlab, pillow, qrcode...) que aqui no se puede
   instalar, y es parte de la Property 3.

La comprobacion (d) es estatica (`ast`), no por ejecucion: asi detecta tambien
los imports de modulos que aun no son importables y no depende de que el arbol
este completo.

Uso:

    python -m guia.preflight        # o: python src/build.py --preflight

Requisitos: 2.2, 2.8, 2.9.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .errores import ErrorDependencia

__all__ = [
    'VERSION_MINIMA',
    'MODULOS_PIPELINE',
    'MODULOS_BASE',
    'ReportePreflight',
    'ejecutar',
    'main',
]

#: Version minima de interprete. La maquina de trabajo tiene 3.14.6.
VERSION_MINIMA = (3, 11)

#: Modulos del pipeline en orden de dependencia, tal como los lista el diseno.
MODULOS_PIPELINE = (
    'errores',
    'preflight',
    'contenido',
    'afm',
    'schema',
    'layout',
    'rotacion',
    'verify_rotacion',
    'diagram_spec',
    'draw',
    'viz',
    'qr',
    'qr_decode',
    'build_pdf',
    'build_html',
    'verify_pdf',
    'build',
)

#: Modulos que ya deben existir en esta fase (tarea 1.1). El resto se reporta
#: como pendiente hasta que su tarea los escriba.
MODULOS_BASE = frozenset({'errores', 'preflight', 'contenido'})

#: Nombres de nivel superior admitidos en el arbol de imports, ademas de la stdlib.
PAQUETES_PROPIOS = frozenset({'guia'})

_PAQUETE = 'guia'


@dataclass(slots=True)
class ReportePreflight:
    """Resultado de un preflight exitoso, para el Reporte_Build."""

    version_python: str
    zlib_version: str
    modulos_presentes: tuple[str, ...] = ()
    modulos_pendientes: tuple[str, ...] = ()
    archivos_analizados: int = 0
    modulos_stdlib_usados: tuple[str, ...] = ()
    lineas: list[str] = field(default_factory=list)

    def texto(self) -> str:
        return '\n'.join(self.lineas)


def comprobar_version() -> str:
    """(a) Version de interprete."""
    if sys.version_info < VERSION_MINIMA:
        actual = '.'.join(str(n) for n in sys.version_info[:3])
        minima = '.'.join(str(n) for n in VERSION_MINIMA)
        raise ErrorDependencia(
            f'falta el componente: Python >= {minima} '
            f'(este interprete es {actual})'
        )
    return '.'.join(str(n) for n in sys.version_info[:3])


def comprobar_zlib() -> str:
    """(b) `zlib`, que usa el Motor_PDF para los streams FlateDecode."""
    try:
        import zlib
    except ImportError as exc:                     # pragma: no cover - depende del build de CPython
        raise ErrorDependencia(
            f'falta el componente: zlib ({exc})'
        ) from exc

    try:
        prueba = zlib.compress(b'preflight', 6)
        if zlib.decompress(prueba) != b'preflight':
            raise ErrorDependencia(
                'falta el componente: zlib (compress/decompress no hace round-trip)'
            )
    except ErrorDependencia:
        raise
    except Exception as exc:
        raise ErrorDependencia(
            f'falta el componente: zlib ({type(exc).__name__}: {exc})'
        ) from exc

    return str(zlib.ZLIB_VERSION)


def comprobar_modulos() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(c) Importabilidad de cada modulo del pipeline.

    Devuelve (presentes, pendientes). Un modulo ausente que pertenece a
    `MODULOS_BASE` es un fallo; ausente de una fase posterior es un pendiente.
    Un modulo que existe pero no importa es siempre un fallo.
    """
    presentes: list[str] = []
    pendientes: list[str] = []

    for nombre in MODULOS_PIPELINE:
        completo = f'{_PAQUETE}.{nombre}'
        try:
            spec = importlib.util.find_spec(completo)
        except ImportError as exc:
            # El paquete padre no importa, o el modulo importa algo inexistente.
            raise ErrorDependencia(
                f'falta el componente: {completo} ({exc})'
            ) from exc

        if spec is None:
            if nombre in MODULOS_BASE:
                raise ErrorDependencia(f'falta el componente: {completo}')
            pendientes.append(nombre)
            continue

        try:
            importlib.import_module(completo)
        except ModuleNotFoundError as exc:
            faltante = exc.name or completo
            if faltante.split('.')[0] not in PAQUETES_PROPIOS:
                raise ErrorDependencia(
                    f'falta el componente: {faltante} '
                    f'(dependencia externa importada por {completo})'
                ) from exc
            raise ErrorDependencia(
                f'falta el componente: {faltante} (lo importa {completo})'
            ) from exc
        except Exception as exc:
            raise ErrorDependencia(
                f'falta el componente: {completo} no importa '
                f'({type(exc).__name__}: {exc})'
            ) from exc

        presentes.append(nombre)

    return tuple(presentes), tuple(pendientes)


def _importados(arbol: ast.AST):
    """Nombres de nivel superior importados por un arbol de sintaxis.

    Los imports relativos (`from . import x`) se omiten: por definicion apuntan
    dentro del paquete.
    """
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split('.')[0], nodo.lineno
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                continue
            if nodo.module:
                yield nodo.module.split('.')[0], nodo.lineno


def comprobar_arbol_stdlib(
    raiz: Path | None = None,
) -> tuple[int, tuple[str, ...]]:
    """(d) Todo import del paquete `guia` cae en la stdlib o en `guia`.

    Devuelve (archivos_analizados, modulos_stdlib_usados). Lanza
    `E_DEPENDENCIA` nombrando la dependencia externa, el archivo y la linea.
    """
    if raiz is None:
        raiz = Path(__file__).resolve().parent

    permitidos = set(sys.stdlib_module_names) | set(PAQUETES_PROPIOS)
    usados: set[str] = set()
    archivos = 0

    for ruta in sorted(raiz.rglob('*.py')):
        if '__pycache__' in ruta.parts:
            continue
        archivos += 1
        fuente = ruta.read_text(encoding='utf-8')
        try:
            arbol = ast.parse(fuente, filename=str(ruta))
        except SyntaxError as exc:
            raise ErrorDependencia(
                f'falta el componente: {ruta.name} no compila '
                f'(linea {exc.lineno}: {exc.msg})'
            ) from exc

        for nombre, linea in _importados(arbol):
            if nombre in permitidos:
                if nombre not in PAQUETES_PROPIOS:
                    usados.add(nombre)
                continue
            relativa = ruta.relative_to(raiz.parent)
            raise ErrorDependencia(
                f'falta el componente: {nombre} no pertenece a la libreria '
                f'estandar (importado en {relativa.as_posix()}:{linea})'
            )

    return archivos, tuple(sorted(usados))


def ejecutar(*, silencioso: bool = True) -> ReportePreflight:
    """Corre las cuatro comprobaciones en orden y devuelve el reporte.

    Lanza `ErrorDependencia` (codigo `E_DEPENDENCIA`) en el primer fallo.
    """
    version = comprobar_version()
    zlib_version = comprobar_zlib()
    presentes, pendientes = comprobar_modulos()
    archivos, stdlib_usados = comprobar_arbol_stdlib()

    minima = '.'.join(str(n) for n in VERSION_MINIMA)
    lineas = [
        f'preflight: Python {version} (minimo {minima}) OK',
        f'preflight: zlib {zlib_version} OK',
        f'preflight: modulos presentes ({len(presentes)}): {", ".join(presentes)}',
    ]
    if pendientes:
        lineas.append(
            f'preflight: modulos pendientes de fases posteriores '
            f'({len(pendientes)}): {", ".join(pendientes)}'
        )
    lineas.append(
        f'preflight: arbol de imports OK, {archivos} archivo(s) del paquete '
        f'{_PAQUETE}, solo stdlib ({", ".join(stdlib_usados) or "sin imports"})'
    )

    reporte = ReportePreflight(
        version_python=version,
        zlib_version=zlib_version,
        modulos_presentes=presentes,
        modulos_pendientes=pendientes,
        archivos_analizados=archivos,
        modulos_stdlib_usados=stdlib_usados,
        lineas=lineas,
    )

    if not silencioso:
        print(reporte.texto())

    return reporte


def main(argv: list[str] | None = None) -> int:
    """Entrada de linea de comandos. 0 si el entorno sirve, 1 si no."""
    del argv
    try:
        ejecutar(silencioso=False)
    except ErrorDependencia as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print('preflight: OK')
    return 0


if __name__ == '__main__':                          # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
