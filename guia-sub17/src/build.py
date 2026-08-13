"""Shim de entrada: `python src/build.py [--preflight] [...]`.

Inserta su propio directorio (`src/`) en `sys.path` para que el paquete `guia`
sea importable sin instalar nada, y delega en `guia.build.main()`.

Este archivo se mantiene deliberadamente en sintaxis conservadora y sin imports
del paquete a nivel de modulo: es el unico punto del pipeline que puede
ejecutarse en un interprete demasiado viejo, y su trabajo en ese caso es dar el
mensaje `E_DEPENDENCIA` en lugar de un `SyntaxError`.

Equivalente canonico: `python -m guia.build` (con `src/` en `PYTHONPATH`).
"""

import os
import sys

VERSION_MINIMA = (3, 11)

_DIR_SRC = os.path.dirname(os.path.abspath(__file__))


def _asegurar_ruta():
    if _DIR_SRC not in sys.path:
        sys.path.insert(0, _DIR_SRC)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if sys.version_info < VERSION_MINIMA:
        actual = '.'.join(str(n) for n in sys.version_info[:3])
        minima = '.'.join(str(n) for n in VERSION_MINIMA)
        sys.stderr.write(
            'E_DEPENDENCIA: falta el componente: Python >= %s '
            '(este interprete es %s)\n' % (minima, actual)
        )
        return 1

    _asegurar_ruta()

    if '--preflight' in argv:
        from guia import preflight
        return preflight.main([a for a in argv if a != '--preflight'])

    try:
        import guia.build as orquestador
    except ImportError as exc:
        # `import guia.build` con el submodulo ausente lanza ModuleNotFoundError
        # con name='guia.build'; cualquier otro ImportError es un fallo real y se
        # deja propagar para no esconder la causa.
        if getattr(exc, 'name', None) not in ('guia.build', 'guia'):
            raise
        sys.stderr.write(
            'E_DEPENDENCIA: falta el componente: guia.build '
            '(el Orquestador_Build se escribe en la tarea 13.1; '
            'de momento usa: python src/build.py --preflight)\n'
        )
        return 1

    return orquestador.main(argv)


if __name__ == '__main__':
    raise SystemExit(main())
