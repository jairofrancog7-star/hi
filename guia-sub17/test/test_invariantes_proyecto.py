"""Invariantes del proyecto conservados por la feature (Requisito 13).

Feature `imagenes-reales-hero-interactivo`, tarea 14.3:

* **Property 39**, guardarraíles de código de los cinco módulos nuevos
  (`diagramas_postura.py`, `svg_postura.py`, `vistas_figura.py`,
  `secciones_guia.py` y `mundo_hero.py`): su árbol de sintaxis no contiene
  ninguna instrucción `assert` y sus importaciones se limitan a la librería
  estándar y al paquete `guia`; y ningún documento de capítulo emitido por
  `build_html` contiene `<script`, `<canvas`, `<img` ni un atributo de evento en
  línea.

La comprobación es **estática**: se lee el archivo, se parsea con `ast` y se
recorre el árbol. Nada se importa ni se ejecuta, así que un `assert` dentro de
una rama que nunca corre también se ve. Es la misma técnica que usa
`preflight.comprobar_arbol_stdlib` para el árbol de imports, extendida a la
instrucción `assert`, que es la mitad del criterio 13.4: `python -O` borra los
`assert`, de modo que un invariante escrito así desaparece justo cuando más
falta hace. Todo invariante viaja como `raise ErrorBuild(...)` o
`raise ErrorAsset(...)` con un código de `errores.CODIGOS`.

Las dos orillas de la prohibición: la propiedad inyecta la violación sobre una
copia **en memoria** del árbol (o del marcado) y exige que el detector la
encuentre y la nombre, e inyecta el casi-fallo (un `import` de la stdlib, un
`from . import`, una cadena que dice "assert", un `role="img"`) y exige que no
invente nada. En `src/guia/` no se escribe nunca.

_Requirements: 13.2, 13.3, 13.4_
"""

from __future__ import annotations

import ast
import os
import re
import sys
import unittest
from pathlib import Path

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
from guia import build_html, errores  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from prop import ITERACIONES_POR_DEFECTO, for_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Contrato del guardarrail
# --------------------------------------------------------------------------- #

#: Directorio del paquete de produccion. El detector lee de aqui y nunca escribe.
DIR_PAQUETE: Path = Path(_DIR_SRC) / "guia"

#: Nombres de nivel superior admitidos en un import de `src/guia/`: la libreria
#: estandar de este interprete y el paquete propio (criterio 13.3). Es el mismo
#: conjunto que `preflight.comprobar_arbol_stdlib` consulta.
PERMITIDOS: frozenset[str] = frozenset(sys.stdlib_module_names) | {"guia"}

#: Elementos prohibidos en un documento de capitulo (criterio 13.2). Se buscan en
#: minusculas, asi que `<SCRIPT` tambien cae.
PROHIBIDOS_MARCADO: tuple[str, ...] = ("<script", "<canvas", "<img")

#: Atributo de evento en linea: espacio (o salto de linea), `on`, letras y el
#: igual. Misma expresion que el guardarrail vigente de `test_mundo_hero`.
_RE_EVENTO = re.compile(r"\son[a-z]+\s*=")

ETQ_P39 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 39: Guardarrailes de codigo de los modulos nuevos"
)


def ruta_de_modulo(nombre: str) -> Path:
    """Ruta del archivo de `src/guia/` que implementa `nombre`."""
    return DIR_PAQUETE / f"{nombre}.py"


def archivos_del_paquete() -> tuple[Path, ...]:
    """Todo archivo `.py` de `src/guia/`, en orden estable y sin `__pycache__`."""
    return tuple(
        ruta
        for ruta in sorted(DIR_PAQUETE.rglob("*.py"))
        if "__pycache__" not in ruta.parts
    )


# --------------------------------------------------------------------------- #
# Detector estatico
# --------------------------------------------------------------------------- #


def violaciones_de_codigo(nombre: str, arbol: ast.AST) -> tuple[str, ...]:
    """Instrucciones `assert` e imports ajenos hallados en `arbol`.

    Devuelve un mensaje por violacion, nombrando el modulo, la linea y la marca
    (la palabra `assert` o el nombre de nivel superior del import). Los imports
    relativos (`from . import x`) se omiten: por definicion apuntan dentro del
    paquete. El orden es el del recorrido, que es estable para un mismo arbol.
    """
    halladas: list[str] = []
    for nodo in ast.walk(arbol):
        linea: int = getattr(nodo, "lineno", 0)
        if isinstance(nodo, ast.Assert):
            halladas.append(f"{nombre}:{linea}: instruccion assert")
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                raiz: str = alias.name.split(".")[0]
                if raiz not in PERMITIDOS:
                    halladas.append(f"{nombre}:{linea}: import ajeno {raiz}")
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                continue
            raiz = (nodo.module or "").split(".")[0]
            if raiz not in PERMITIDOS:
                halladas.append(f"{nombre}:{linea}: from ajeno {raiz}")
    return tuple(halladas)


def violaciones_de_marcado(nombre: str, marcado: str) -> tuple[str, ...]:
    """Elementos y atributos prohibidos por el criterio 13.2 en `marcado`."""
    bajo: str = marcado.lower()
    halladas: list[str] = []
    for prohibido in PROHIBIDOS_MARCADO:
        if prohibido in bajo:
            halladas.append(f"{nombre}: elemento prohibido {prohibido}")
    hallado = _RE_EVENTO.search(bajo)
    if hallado is not None:
        halladas.append(
            f"{nombre}: atributo de evento en linea {hallado.group(0).strip()}"
        )
    return tuple(halladas)


# --------------------------------------------------------------------------- #
# Inyeccion en memoria
# --------------------------------------------------------------------------- #


def _funciones_de(arbol: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Definiciones de funcion del arbol, en orden de recorrido."""
    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _indice(posicion: float, largo: int) -> int:
    """Indice de insercion en `[0, largo]` a partir de una posicion relativa."""
    return min(largo, int(posicion * (largo + 1)))


def injertar_en_arbol(arbol: ast.Module, caso: gen.ViolacionCodigo) -> ast.Module:
    """Clava el fragmento de `caso` en una copia en memoria de `arbol`.

    `arbol` es el resultado de parsear el archivo real, nunca el archivo: la
    mutacion vive en la memoria de esta prueba y `src/guia/` queda intacto. Las
    familias `*_en_funcion` inyectan dentro del cuerpo de una funcion, elegida
    por la posicion relativa del caso; las demas, en el cuerpo del modulo.
    """
    injerto: list[ast.stmt] = ast.parse(caso.fragmento).body

    if caso.familia.endswith("_en_funcion"):
        funciones = _funciones_de(arbol)
        if not funciones:
            raise ValueError(f"{caso.objetivo} no declara ninguna funcion")
        elegida = funciones[min(len(funciones) - 1, int(caso.posicion * len(funciones)))]
        cuerpo: list[ast.stmt] = elegida.body
    else:
        cuerpo = arbol.body

    indice: int = _indice(caso.posicion, len(cuerpo))
    ancla: ast.stmt = cuerpo[min(indice, len(cuerpo) - 1)]
    for nodo in injerto:
        ast.copy_location(nodo, ancla)
        ast.fix_missing_locations(nodo)
    cuerpo[indice:indice] = injerto
    return arbol


def cortes_del_cuerpo(marcado: str) -> tuple[int, ...]:
    """Posiciones de salto de linea dentro del `<body>` de `marcado`.

    Se calcula una sola vez por documento (los capitulos pesan megabytes) y la
    propiedad elige de aqui el punto del injerto.
    """
    bajo: str = marcado.lower()
    inicio: int = bajo.find("<body")
    fin: int = bajo.find("</body>")
    if inicio < 0 or fin < 0:
        raise ValueError("el documento no declara <body>")

    cortes: list[int] = []
    posicion: int = marcado.find("\n", inicio)
    while 0 <= posicion < fin:
        cortes.append(posicion)
        posicion = marcado.find("\n", posicion + 1)
    if not cortes:
        cortes.append(fin)
    return tuple(cortes)


def injertar_en_marcado(
    marcado: str, caso: gen.ViolacionCodigo, cortes: tuple[int, ...]
) -> str:
    """Clava el fragmento de `caso` en una copia en memoria de `marcado`.

    El corte cae en un salto de linea dentro del `<body>`, elegido por la
    posicion relativa del caso, de modo que el injerto quede en el cuerpo del
    documento y no dentro de una etiqueta partida por la mitad.
    """
    corte: int = cortes[min(len(cortes) - 1, int(caso.posicion * len(cortes)))]
    return "".join((marcado[:corte], "\n", caso.fragmento, marcado[corte:]))


#: Cache de los documentos de `build_html`: el render completo del capitulo pesa
#: casi ocho segundos, asi que se paga una vez por corrida y no una por clase.
_DOCUMENTOS: dict[str, str] = {}


def documentos() -> dict[str, str]:
    """Documentos emitidos por `build_html` para el capitulo de fundamentos."""
    if not _DOCUMENTOS:
        _DOCUMENTOS.update(build_html.documento_a_html(cap10_fundamentos.paginas()))
    return _DOCUMENTOS


# --------------------------------------------------------------------------- #
# Property 39
# --------------------------------------------------------------------------- #


class TestGuardarrailesDeCodigo(unittest.TestCase):
    """Los cinco módulos nuevos y los capítulos, medidos por análisis estático."""

    @classmethod
    def setUpClass(cls) -> None:
        # Fuentes en memoria: se parsean por iteracion para que cada caso trabaje
        # sobre un arbol propio y la mutacion de uno no contamine al siguiente.
        cls.fuentes: dict[str, str] = {
            nombre: ruta_de_modulo(nombre).read_text(encoding="utf-8")
            for nombre in gen.MODULOS_NUEVOS
        }
        docs: dict[str, str] = documentos()
        cls.capitulos: dict[str, str] = {
            nombre: contenido
            for nombre, contenido in docs.items()
            if nombre.endswith(".html") and nombre != "index.html"
        }
        cls.nombres_capitulo: tuple[str, ...] = tuple(sorted(cls.capitulos))
        cls.cortes: dict[str, tuple[int, ...]] = {
            nombre: cortes_del_cuerpo(contenido)
            for nombre, contenido in cls.capitulos.items()
        }

    def test_property_39_guardarrailes_de_codigo(self) -> None:
        # ruff: noqa: E501
        """Feature: imagenes-reales-hero-interactivo, Property 39: Guardarrailes de codigo de los modulos nuevos.

        *Para todo* archivo de `src/guia/`, su árbol de sintaxis no contiene
        ninguna instrucción `assert` y sus importaciones se limitan a módulos de
        la librería estándar y a módulos del paquete `guia`; y *para todo*
        documento de capítulo generado por `build_html`, el documento no contiene
        `<script`, `<canvas`, `<img` ni ningún atributo de evento en línea.

        **Validates: Requirements 13.2, 13.3, 13.4**
        """

        def prop(caso: gen.ViolacionCodigo) -> None:
            if caso.dominio == "modulo":
                self._revisar_modulo(caso)
            else:
                self._revisar_capitulo(caso)

        for_all(
            gen.gen_violacion_codigo,
            prop,
            iteraciones=ITERACIONES_POR_DEFECTO,
            etiqueta=ETQ_P39,
        )

    def _revisar_modulo(self, caso: gen.ViolacionCodigo) -> None:
        """Criterios 13.3 y 13.4 sobre uno de los cinco módulos nuevos."""
        nombre: str = caso.objetivo
        arbol: ast.Module = ast.parse(self.fuentes[nombre], filename=f"{nombre}.py")

        # Orilla limpia: el codigo real no trae ni un `assert` ni un import ajeno.
        self.assertEqual(
            violaciones_de_codigo(nombre, arbol),
            (),
            msg=f"{nombre}.py: el codigo real ya incumple el guardarrail",
        )

        # Orilla sucia: el injerto vive solo en esta copia en memoria.
        mutado: ast.Module = injertar_en_arbol(arbol, caso)
        halladas: tuple[str, ...] = violaciones_de_codigo(nombre, mutado)

        if not caso.hostil:
            self.assertEqual(
                halladas,
                (),
                msg=(
                    f"{nombre}.py: el detector inventa una violacion con el "
                    f"casi-fallo {caso.familia}: {caso.fragmento!r}"
                ),
            )
            return

        self.assertEqual(
            len(halladas),
            1,
            msg=(
                f"{nombre}.py: el injerto {caso.familia} ({caso.fragmento!r}) "
                f"tenia que dar exactamente una violacion, dio {halladas}"
            ),
        )
        mensaje: str = halladas[0]
        self.assertIn(nombre, mensaje)
        self.assertIn(caso.marca, mensaje)

    def _revisar_capitulo(self, caso: gen.ViolacionCodigo) -> None:
        """Criterio 13.2 sobre un documento de capítulo de `build_html`."""
        indice: int = min(
            len(self.nombres_capitulo) - 1,
            int(caso.posicion * len(self.nombres_capitulo)),
        )
        nombre: str = self.nombres_capitulo[indice]
        documento: str = self.capitulos[nombre]

        self.assertEqual(
            violaciones_de_marcado(nombre, documento),
            (),
            msg=f"{nombre}: el capitulo real ya incumple el criterio 13.2",
        )

        mutado: str = injertar_en_marcado(documento, caso, self.cortes[nombre])
        halladas: tuple[str, ...] = violaciones_de_marcado(nombre, mutado)

        if not caso.hostil:
            self.assertEqual(
                halladas,
                (),
                msg=(
                    f"{nombre}: el detector inventa una violacion con el "
                    f"casi-fallo {caso.familia}: {caso.fragmento!r}"
                ),
            )
            return

        self.assertEqual(
            len(halladas),
            1,
            msg=(
                f"{nombre}: el injerto {caso.familia} ({caso.fragmento!r}) "
                f"tenia que dar exactamente una violacion, dio {halladas}"
            ),
        )
        self.assertIn(caso.marca, halladas[0])


class TestGuardarrailDeTodoElPaquete(unittest.TestCase):
    """El guardarraíl medido sobre `src/guia/` entero, no solo sobre lo nuevo."""

    def test_ningun_archivo_de_produccion_usa_assert(self) -> None:
        # Criterio 13.4: `python -O` borra los `assert`, asi que ningun invariante
        # puede viajar en uno. La comprobacion es estatica y cubre las ramas que
        # nunca se ejecutan.
        for ruta in archivos_del_paquete():
            with self.subTest(archivo=ruta.name):
                arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
                lineas = [
                    nodo.lineno
                    for nodo in ast.walk(arbol)
                    if isinstance(nodo, ast.Assert)
                ]
                self.assertEqual(lineas, [], msg=f"{ruta.name}: assert en {lineas}")

    def test_ningun_archivo_de_produccion_importa_fuera_de_la_stdlib(self) -> None:
        # Criterio 13.3, y los cinco modulos nuevos estan dentro del barrido.
        for ruta in archivos_del_paquete():
            with self.subTest(archivo=ruta.name):
                arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
                self.assertEqual(violaciones_de_codigo(ruta.name, arbol), ())

    def test_los_cinco_modulos_nuevos_existen_y_estan_barridos(self) -> None:
        barridos = {ruta.name for ruta in archivos_del_paquete()}
        for nombre in gen.MODULOS_NUEVOS:
            with self.subTest(modulo=nombre):
                self.assertTrue(ruta_de_modulo(nombre).is_file())
                self.assertIn(f"{nombre}.py", barridos)

    def test_los_codigos_de_asset_estan_declarados(self) -> None:
        # Criterio 13.4, segunda mitad: el invariante viaja como `raise` con un
        # codigo de `CODIGOS`, y `ErrorAsset` es la subclase que lo lleva.
        self.assertTrue(issubclass(errores.ErrorAsset, errores.ErrorBuild))
        for codigo in sorted(errores.ErrorAsset.CODIGOS_PERMITIDOS):
            with self.subTest(codigo=codigo):
                self.assertIn(codigo, errores.CODIGOS)


class TestCapitulosSinJavaScript(unittest.TestCase):
    """El criterio 13.2, además, sobre el índice y con el `<svg>` en línea vivo."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.docs: dict[str, str] = documentos()

    def test_ningun_documento_html_trae_script_canvas_ni_img(self) -> None:
        for nombre, contenido in self.docs.items():
            if not nombre.endswith(".html"):
                continue
            with self.subTest(archivo=nombre):
                self.assertEqual(violaciones_de_marcado(nombre, contenido), ())

    def test_el_svg_en_linea_sigue_llevando_su_rol_de_imagen(self) -> None:
        # El detector prohibe `<img`, no `role="img"`: el dibujo en linea de los
        # capitulos tiene que seguir ahi.
        capitulo = self.docs["10-fundamentos.html"]
        self.assertIn('role="img"', capitulo)
        self.assertIn("<svg", capitulo)


if __name__ == "__main__":
    unittest.main()
