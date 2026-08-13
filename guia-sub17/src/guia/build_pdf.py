"""Motor_PDF: escritura incremental del PDF de la Guia_Extensa (`build_pdf.py`).

Escribe un PDF **byte a byte, sin librerías externas**, consumiendo el
`Modelo_Paginas` (lista de `PaginaRender`) que produce el paginador. Ningún
motor conoce el catálogo: `build_pdf` solo sabe leer `PaginaRender`,
`ElementoRender` y `Anotacion` (ver `layout.py`).

Diseño (ver design.md, "Escritura incremental del PDF"):

* `EscritorPDF` abre el archivo con `open(ruta, 'wb')`, lleva un contador de
  `offset` y una lista `offsets` para la tabla xref, y escribe cada objeto en
  el momento con `obj(...)`. Los streams de contenido se comprimen con
  `zlib.compress(datos, 6)` y se emiten con `/Filter /FlateDecode`.
* **Sintaxis del PDF en ASCII.** Los operadores, diccionarios, la xref y el
  trailer se emiten como bytes ASCII. **Solo los literales de texto** pasan por
  `afm.codificar_winansi` (para obtener bytes `WinAnsiEncoding`) y
  `afm.escapar_literal_pdf` (para neutralizar `\\`, `(` y `)`). Separar ambos
  mundos evita el error clásico de codificar la sintaxis con la tabla de texto.
* **Fuentes Standard-14 con WinAnsiEncoding**: `/F1` = Helvetica y `/F2` =
  Helvetica-Bold, declaradas una vez y compartidas por todas las páginas.
* **XObjects de formulario** para las bandas de encabezado y pie (recurso
  repetido idéntico en cada página): se declara un único XObject `/Banda` y
  cada página lo invoca con `/Banda Do`.
* **Anotaciones `/Link`** con acción `/URI` y un rectángulo *dentro* de la
  página (Req 9.6): el rectángulo se recorta a `[0, A4_W] x [0, A4_H]`.
* `cerrar(raiz_id, info_id)` escribe la tabla `xref`, el `trailer` y
  `startxref` de forma byte-correcta para que el archivo abra y el verificador
  estructural (tarea 7.4) lo acepte.

Sin `assert` en producción: los invariantes se comprueban con
`raise ErrorPDF(...)` (subclase de `ErrorBuild`), que `python -O` no borra.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

from . import afm, draw, paleta
from .errores import E_PDF_CORRUPTO, ErrorPDF
from .layout import (
    A4_H,
    A4_W,
    BANDA_INF,
    BANDA_SUP,
    MARGEN_DER,
    MARGEN_INF,
    MARGEN_IZQ,
    MARGEN_SUP,
    Anotacion,
    ElementoRender,
    PaginaRender,
    TipoElemento,
)

__all__ = [
    "EscritorPDF",
    "escribir_pdf",
    "documento_a_bytes",
]


# --------------------------------------------------------------------------- #
# Formato numérico estable y utilidades de color / texto
# --------------------------------------------------------------------------- #


def _num(valor: float) -> str:
    """Formatea un número con 3 decimales, recortando ceros sobrantes.

    Da bytes estables entre corridas (determinismo) y evita notación
    científica en coordenadas del PDF.
    """
    texto = f"{valor:.3f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _rgb(color: str) -> tuple[float, float, float]:
    """Convierte un color hex a tripla RGB `[0, 1]`.

    Prefiere `paleta.rgb_pdf` (que restringe a la paleta declarada); si el color
    no pertenece a la paleta pero es un hex válido (p. ej. el fondo oscuro de
    una lámina), lo parsea directamente para no romper el render.
    """
    try:
        return paleta.rgb_pdf(color)
    except ValueError:
        normal = paleta.normalizar_hex(color)
        r = int(normal[1:3], 16) / 255.0
        g = int(normal[3:5], 16) / 255.0
        b = int(normal[5:7], 16) / 255.0
        return (r, g, b)


# Recurso de fuente del PDF por nombre de fuente Standard-14.
_FUENTE_RECURSO: dict[str, str] = {
    "Helvetica": "/F1",
    "Helvetica-Bold": "/F2",
}


def _recurso_fuente(fuente: str) -> str:
    """Recurso `/F1`/`/F2` para una fuente Standard-14 (Helvetica por defecto)."""
    return _FUENTE_RECURSO.get(fuente, "/F1")


def _ascii(texto: str) -> bytes:
    """Codifica un fragmento de **sintaxis** PDF (siempre ASCII) a bytes."""
    return texto.encode("ascii")


def _literal(texto: str, *, ctx: str) -> bytes:
    """Bytes de un literal de texto PDF: `(...)` ya codificado y escapado.

    Es el **único** camino por el que un texto del contenido llega al archivo:
    primero `afm.codificar_winansi` (Unicode -> bytes WinAnsi, detectando
    caracteres no codificables) y luego `afm.escapar_literal_pdf` (escape de
    `\\`, `(` y `)`). No incluye los paréntesis delimitadores.
    """
    return afm.escapar_literal_pdf(afm.codificar_winansi(texto, ctx=ctx))


def _clamp(valor: float, minimo: float, maximo: float) -> float:
    """Recorta `valor` al rango `[minimo, maximo]`."""
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor


# --------------------------------------------------------------------------- #
# EscritorPDF: escritura incremental con xref
# --------------------------------------------------------------------------- #

_CABECERA: bytes = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"


class EscritorPDF:
    """Escritor incremental de objetos PDF con tabla xref.

    Abre el archivo en binario y escribe la cabecera `%PDF-` de inmediato, de
    modo que `offset` refleje siempre la posición absoluta desde el inicio del
    archivo. Cada `obj(...)` registra en `offsets` el byte donde empieza la
    declaración `N 0 obj`, que es lo que la xref necesita apuntar.

    Para resolver referencias circulares (una página apunta a su `/Parent`
    Pages, que a su vez lista a todas las páginas en `/Kids`) se pueden
    **reservar** identificadores con `reservar_id()` y rellenarlos después con
    `obj(cuerpo, oid=...)`.
    """

    __slots__ = ("f", "offset", "offsets", "comprimir", "_cerrado")

    def __init__(self, ruta: str, *, comprimir: bool = True) -> None:
        self.f = open(ruta, "wb")  # binario, escritura incremental
        self.offset = 0
        # offsets[i] = byte de inicio del objeto i. El objeto 0 es el libre.
        self.offsets: list[int] = [0]
        self.comprimir = comprimir
        self._cerrado = False
        self.escribir(_CABECERA)

    # -- escritura de bajo nivel ------------------------------------------ #

    def escribir(self, crudos: bytes) -> None:
        """Escribe `crudos` y avanza el contador de offset."""
        self.f.write(crudos)
        self.offset += len(crudos)

    def reservar_id(self) -> int:
        """Reserva un identificador de objeto y devuelve su número.

        El offset queda como `-1` (marcador) hasta que se escriba el objeto con
        `obj(cuerpo, oid=<este id>)`.
        """
        oid = len(self.offsets)
        self.offsets.append(-1)
        return oid

    def obj(self, cuerpo: bytes, oid: int | None = None) -> int:
        """Escribe un objeto indirecto `N 0 obj ... endobj` y devuelve su id.

        Si `oid` es `None` asigna el siguiente id disponible; si se pasa un id
        (previamente reservado), rellena su offset. `cuerpo` son los bytes del
        cuerpo del objeto (sin `N 0 obj`/`endobj`), en ASCII salvo los literales
        de texto ya codificados a WinAnsi.
        """
        if oid is None:
            oid = len(self.offsets)
            self.offsets.append(self.offset)
        else:
            if not (0 < oid < len(self.offsets)):
                raise ErrorPDF(
                    f"id de objeto reservado invalido: {oid}",
                    codigo=E_PDF_CORRUPTO,
                    detalle={"oid": oid},
                )
            self.offsets[oid] = self.offset
        self.escribir(b"%d 0 obj\n" % oid + cuerpo + b"\nendobj\n")
        return oid

    def stream(self, dic: str, datos: bytes, oid: int | None = None) -> int:
        """Escribe un objeto de stream comprimido con `/FlateDecode`.

        `dic` es el interior del diccionario del stream (sin `<< >>` y sin
        `/Length` ni `/Filter`, que se añaden aquí). `datos` son los bytes del
        contenido **ya codificados** (los literales de texto ya pasaron por
        `codificar_winansi`). Si `comprimir` es `True` se comprime con
        `zlib.compress(datos, 6)` y se emite `/Filter /FlateDecode`.
        """
        if self.comprimir:
            cuerpo = zlib.compress(datos, 6)
            filtro = " /Filter /FlateDecode"
        else:
            cuerpo, filtro = datos, ""  # modo --sin-comprimir
        cab = f"<< {dic}{filtro} /Length {len(cuerpo)} >>\nstream\n".encode("ascii")
        return self.obj(cab + cuerpo + b"\nendstream", oid=oid)

    def cerrar(self, raiz_id: int, info_id: int) -> None:
        """Escribe la tabla `xref`, el `trailer` y `startxref`, y cierra.

        La xref tiene una entrada por objeto (incluido el 0, libre). Cada
        entrada ocupa exactamente 20 bytes: `nnnnnnnnnn ggggg t\\r\\n`. El
        `startxref` apunta al byte donde empieza la palabra `xref`.
        """
        if self._cerrado:
            return
        n = len(self.offsets)
        for i, off in enumerate(self.offsets):
            if i != 0 and off < 0:
                raise ErrorPDF(
                    f"el objeto {i} fue reservado pero nunca se escribio",
                    codigo=E_PDF_CORRUPTO,
                    detalle={"oid": i},
                )

        inicio_xref = self.offset
        partes: list[bytes] = [b"xref\n", b"0 %d\n" % n]
        # Objeto 0: entrada libre estandar.
        partes.append(b"0000000000 65535 f\r\n")
        for off in self.offsets[1:]:
            partes.append(b"%010d 00000 n\r\n" % off)
        self.escribir(b"".join(partes))

        trailer = (
            f"trailer\n<< /Size {n} /Root {raiz_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{inicio_xref}\n%%EOF\n"
        ).encode("ascii")
        self.escribir(trailer)

        self.f.close()
        self._cerrado = True

    # -- context manager --------------------------------------------------- #

    def __enter__(self) -> "EscritorPDF":
        return self

    def __exit__(self, *exc: object) -> None:
        # Si algo falló antes de cerrar, al menos liberamos el descriptor.
        if not self._cerrado:
            self.f.close()


# --------------------------------------------------------------------------- #
# Recursos compartidos: fuentes Standard-14 y XObject de banda
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class _Recursos:
    """Ids de los objetos compartidos por todas las páginas."""

    pages_id: int
    f1_id: int
    f2_id: int
    banda_id: int


def _dic_fuente(base: str) -> bytes:
    """Diccionario de una fuente Standard-14 con `WinAnsiEncoding`."""
    return (
        f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} "
        f"/Encoding /WinAnsiEncoding >>"
    ).encode("ascii")


def _contenido_banda() -> bytes:
    """Operadores del XObject de banda: reglas rosa de encabezado y pie.

    Es un recurso **idéntico en todas las páginas** (Req 1.5: banda de
    capítulo), así que se declara una vez como XObject de formulario y cada
    página lo invoca con `/Banda Do`. El texto variable (título de capítulo y
    folio) no va aquí: se dibuja en el contenido de cada página.
    """
    r, g, b = _rgb(paleta.ROSA)
    x0 = MARGEN_IZQ
    x1 = A4_W - MARGEN_DER
    y_sup = A4_H - MARGEN_SUP
    y_inf = MARGEN_INF + BANDA_INF
    partes: list[str] = [
        "q\n",
        f"{_num(r)} {_num(g)} {_num(b)} RG\n",
        "0.8 w\n",
        f"{_num(x0)} {_num(y_sup)} m {_num(x1)} {_num(y_sup)} l S\n",
        f"{_num(x0)} {_num(y_inf)} m {_num(x1)} {_num(y_inf)} l S\n",
        "Q\n",
    ]
    return "".join(partes).encode("ascii")


# --------------------------------------------------------------------------- #
# Render de cada tipo de ElementoRender a operadores de contenido
# --------------------------------------------------------------------------- #


def _render_texto(elem: ElementoRender, partes: list[bytes]) -> None:
    """Texto/párrafo: envuelve con `afm` y emite líneas de arriba hacia abajo."""
    datos = elem.datos
    texto = getattr(datos, "texto", None)
    if not texto:
        return
    fuente = getattr(datos, "fuente", "Helvetica")
    tam = float(getattr(datos, "tamano", 10.0))
    interlineado = float(getattr(datos, "interlineado", 1.2))
    ancho = elem.w if elem.w and elem.w > 0.0 else (A4_W - MARGEN_IZQ - MARGEN_DER)
    # Validar codificabilidad WinAnsi ANTES de medir/envolver: `afm.medir_texto`
    # haría `str.encode('cp1252')` y lanzaría un `UnicodeEncodeError` crudo ante
    # un carácter fuera de WinAnsi. Pasar primero por `codificar_winansi` lo
    # convierte en el `ErrorBuild(E_CARACTER_NO_CODIFICABLE)` esperado, con el
    # carácter, su code point y su posición.
    afm.codificar_winansi(texto, ctx="texto de pagina")
    lineas = afm.envolver(texto, ancho, fuente, tam)
    if not lineas:
        return
    recurso = _recurso_fuente(fuente)
    salto = tam * interlineado
    r, g, b = _rgb(paleta.NEGRO)
    partes.append(b"BT\n")
    partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
    partes.append(_ascii(f"{recurso} {_num(tam)} Tf\n"))
    # Primera línea: base a `tam` por debajo del borde superior de la caja.
    x = elem.x
    y0 = elem.y + elem.h - tam
    partes.append(_ascii(f"{_num(x)} {_num(y0)} Td\n"))
    partes.append(b"(")
    partes.append(_literal(lineas[0], ctx="texto de pagina"))
    partes.append(b") Tj\n")
    for linea in lineas[1:]:
        partes.append(_ascii(f"0 {_num(-salto)} Td\n"))
        partes.append(b"(")
        partes.append(_literal(linea, ctx="texto de pagina"))
        partes.append(b") Tj\n")
    partes.append(b"ET\n")


def _render_rect(elem: ElementoRender, partes: list[bytes]) -> None:
    """Rectángulo con relleno y/o borde (RectDatos)."""
    datos = elem.datos
    relleno = getattr(datos, "relleno", None)
    borde = getattr(datos, "borde", None)
    grosor = float(getattr(datos, "grosor", 0.5))
    if relleno is None and borde is None:
        return
    partes.append(b"q\n")
    if relleno is not None:
        r, g, b = _rgb(relleno)
        partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
    if borde is not None:
        r, g, b = _rgb(borde)
        partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} RG\n"))
        partes.append(_ascii(f"{_num(grosor)} w\n"))
    partes.append(
        _ascii(f"{_num(elem.x)} {_num(elem.y)} {_num(elem.w)} {_num(elem.h)} re\n")
    )
    if relleno is not None and borde is not None:
        partes.append(b"B\n")
    elif relleno is not None:
        partes.append(b"f\n")
    else:
        partes.append(b"S\n")
    partes.append(b"Q\n")


def _render_linea(elem: ElementoRender, partes: list[bytes]) -> None:
    """Segmento horizontal (LineaDatos) a la altura media de la caja."""
    datos = elem.datos
    color = getattr(datos, "color", "#111")
    grosor = float(getattr(datos, "grosor", 0.5))
    r, g, b = _rgb(color)
    y = elem.y + elem.h / 2.0
    partes.append(b"q\n")
    partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} RG\n"))
    partes.append(_ascii(f"{_num(grosor)} w\n"))
    partes.append(_ascii(f"{_num(elem.x)} {_num(y)} m {_num(elem.x + elem.w)} {_num(y)} l S\n"))
    partes.append(b"Q\n")


def _render_diagrama(elem: ElementoRender, partes: list[bytes]) -> None:
    """Diagrama vectorial: escala el bbox del spec a la caja y lo dibuja.

    Usa `draw.spec_a_operadores(spec)` (mismo spec que consume el SVG). Los
    operadores vienen como `str` con los literales ya escapados; se codifican a
    WinAnsi y se envuelven en `q ... cm ... Q` para escalar y centrar dentro de
    la caja del elemento sin tocar el sistema de coordenadas de la página.
    """
    datos = elem.datos
    spec = getattr(datos, "spec", None)
    if spec is None:
        return
    ops, bbox = draw.spec_a_operadores(spec)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    if bw <= 0.0 or bh <= 0.0 or elem.w <= 0.0 or elem.h <= 0.0:
        return
    escala = min(elem.w / bw, elem.h / bh)
    tx = elem.x + (elem.w - escala * bw) / 2.0 - bbox[0] * escala
    ty = elem.y + (elem.h - escala * bh) / 2.0 - bbox[1] * escala
    partes.append(b"q\n")
    partes.append(_ascii(f"{_num(escala)} 0 0 {_num(escala)} {_num(tx)} {_num(ty)} cm\n"))
    partes.append(afm.codificar_winansi(ops, ctx="operadores de diagrama"))
    partes.append(b"Q\n")


def _render_qr(elem: ElementoRender, partes: list[bytes]) -> None:
    """Código QR: fondo blanco y un rectángulo negro por módulo oscuro."""
    datos = elem.datos
    matriz = getattr(datos, "matriz", None)
    if matriz is None:
        url = getattr(datos, "url", None)
        if not url:
            return
        from . import qr

        matriz = qr.codificar(url)
    lado_mod = int(getattr(matriz, "lado", 0))
    if lado_mod <= 0:
        return
    caja = min(elem.w, elem.h)
    if caja <= 0.0:
        return
    paso = caja / lado_mod
    # Fondo blanco.
    wr, wg, wb = _rgb(paleta.BLANCO)
    partes.append(b"q\n")
    partes.append(_ascii(f"{_num(wr)} {_num(wg)} {_num(wb)} rg\n"))
    partes.append(_ascii(f"{_num(elem.x)} {_num(elem.y)} {_num(caja)} {_num(caja)} re f\n"))
    # Módulos oscuros en negro. Fila 0 es la superior del QR.
    nr, ng, nb = _rgb(paleta.NEGRO)
    partes.append(_ascii(f"{_num(nr)} {_num(ng)} {_num(nb)} rg\n"))
    modulo = matriz.modulo
    for fila in range(lado_mod):
        py = elem.y + caja - (fila + 1) * paso
        for col in range(lado_mod):
            if modulo(fila, col):
                px = elem.x + col * paso
                partes.append(
                    _ascii(f"{_num(px)} {_num(py)} {_num(paso)} {_num(paso)} re\n")
                )
    partes.append(b"f\n")
    partes.append(b"Q\n")


def _render_tabla(elem: ElementoRender, partes: list[bytes]) -> None:
    """Fila de tabla (FilaTablaDatos): fondo de cabecera, texto y regla inferior."""
    datos = elem.datos
    celdas = getattr(datos, "celdas", ())
    anchos = getattr(datos, "anchos", ())
    es_cabecera = bool(getattr(datos, "es_cabecera", False))
    fuente = getattr(datos, "fuente", "Helvetica")
    tam = float(getattr(datos, "tam", 10.0))
    if not celdas:
        return
    pad = 3.0
    # Fondo gris muy claro para la cabecera.
    if es_cabecera:
        r, g, b = _rgb(paleta.GRISES_TRAMA[0])
        partes.append(b"q\n")
        partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
        partes.append(
            _ascii(f"{_num(elem.x)} {_num(elem.y)} {_num(elem.w)} {_num(elem.h)} re f\n")
        )
        partes.append(b"Q\n")
    # Texto de cada celda.
    recurso = _recurso_fuente(fuente)
    tr, tg, tb = _rgb(paleta.NEGRO)
    x = elem.x
    base = elem.y + elem.h - tam - pad
    for i, celda in enumerate(celdas):
        ancho_col = float(anchos[i]) if i < len(anchos) else elem.w / len(celdas)
        util = ancho_col - 2.0 * pad
        if util <= 0.0:
            util = ancho_col
        texto = str(celda)
        lineas = afm.envolver(texto, util, fuente, tam)
        if lineas:
            partes.append(b"BT\n")
            partes.append(_ascii(f"{_num(tr)} {_num(tg)} {_num(tb)} rg\n"))
            partes.append(_ascii(f"{recurso} {_num(tam)} Tf\n"))
            partes.append(_ascii(f"{_num(x + pad)} {_num(base)} Td\n"))
            partes.append(b"(")
            partes.append(_literal(lineas[0], ctx="celda de tabla"))
            partes.append(b") Tj\n")
            partes.append(b"ET\n")
        x += ancho_col
    # Regla inferior de la fila.
    lr, lg, lb = _rgb(paleta.GRISES_TRAMA[2])
    partes.append(b"q\n")
    partes.append(_ascii(f"{_num(lr)} {_num(lg)} {_num(lb)} RG\n"))
    partes.append(b"0.4 w\n")
    partes.append(
        _ascii(f"{_num(elem.x)} {_num(elem.y)} m {_num(elem.x + elem.w)} {_num(elem.y)} l S\n")
    )
    partes.append(b"Q\n")


_RENDER_POR_TIPO = {
    TipoElemento.TEXTO: _render_texto,
    TipoElemento.PARRAFO: _render_texto,
    TipoElemento.RECT: _render_rect,
    TipoElemento.LINEA: _render_linea,
    TipoElemento.DIAGRAMA: _render_diagrama,
    TipoElemento.QR: _render_qr,
    TipoElemento.TABLA: _render_tabla,
}


# --------------------------------------------------------------------------- #
# Encabezado / pie de página y contenido completo de una página
# --------------------------------------------------------------------------- #


def _render_banda_texto(pagina: PaginaRender, partes: list[bytes]) -> None:
    """Texto de encabezado (título de capítulo) y pie (capítulo · folio)."""
    r, g, b = _rgb(paleta.NEGRO)
    # Encabezado: título de capítulo en negrita, arriba a la izquierda.
    titulo_cap = pagina.capitulo_titulo or ""
    if titulo_cap:
        y = A4_H - MARGEN_SUP + 4.0
        partes.append(b"BT\n")
        partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
        partes.append(_ascii(f"/F2 9 Tf\n"))
        partes.append(_ascii(f"{_num(MARGEN_IZQ)} {_num(y)} Td\n"))
        partes.append(b"(")
        partes.append(_literal(titulo_cap, ctx="encabezado de capitulo"))
        partes.append(b") Tj\n")
        partes.append(b"ET\n")
        # Título de ficha repetido (Req 1.7), a la derecha del encabezado.
        if pagina.titulo_ficha:
            ancho = afm.medir_texto(pagina.titulo_ficha, "Helvetica", 8.0)
            xf = A4_W - MARGEN_DER - ancho
            partes.append(b"BT\n")
            partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
            partes.append(_ascii(f"/F1 8 Tf\n"))
            partes.append(_ascii(f"{_num(xf)} {_num(y)} Td\n"))
            partes.append(b"(")
            partes.append(_literal(pagina.titulo_ficha, ctx="titulo de ficha"))
            partes.append(b") Tj\n")
            partes.append(b"ET\n")
    # Pie: "capítulo   ·   folio".
    pie = f"{titulo_cap}   \u00b7   {pagina.folio}" if titulo_cap else str(pagina.folio)
    y = MARGEN_INF
    partes.append(b"BT\n")
    partes.append(_ascii(f"{_num(r)} {_num(g)} {_num(b)} rg\n"))
    partes.append(_ascii(f"/F1 8 Tf\n"))
    partes.append(_ascii(f"{_num(MARGEN_IZQ)} {_num(y)} Td\n"))
    partes.append(b"(")
    partes.append(_literal(pie, ctx="pie de pagina"))
    partes.append(b") Tj\n")
    partes.append(b"ET\n")


def _contenido_pagina(pagina: PaginaRender, *, con_banda: bool = True) -> bytes:
    """Bytes del stream de contenido de una página completa.

    Invoca la banda compartida (`/Banda Do`), dibuja el texto de encabezado/pie
    y luego cada `ElementoRender` según su tipo. La sintaxis es ASCII; solo los
    literales de texto pasan por `codificar_winansi` + `escapar_literal_pdf`.

    `con_banda` es `False` para páginas que no usan la banda A4 (p. ej. las
    láminas verticales de teléfono, cuya geometría no es A4): en ese caso no se
    invoca `/Banda Do` ni se dibuja el encabezado/pie de capítulo.
    """
    partes: list[bytes] = []
    if con_banda:
        partes.append(b"q\n/Banda Do\nQ\n")
        _render_banda_texto(pagina, partes)
    for elem in pagina.elementos:
        render = _RENDER_POR_TIPO.get(elem.tipo)
        if render is not None:
            render(elem, partes)
    return b"".join(partes)


def _dic_anotacion(anot: Anotacion, *, ancho: float = A4_W, alto: float = A4_H) -> bytes:
    """Diccionario de una anotación `/Link` con acción `/URI`.

    El rectángulo se recorta a la página `[0, ancho] x [0, alto]` (Req 9.6: el
    enlace clicable queda dentro de la página). `ancho`/`alto` son el tamaño real
    de la página (A4 por defecto; distinto en páginas verticales de teléfono).
    El literal de la URI pasa por `codificar_winansi` + `escapar_literal_pdf`.
    """
    x0, y0, x1, y1 = anot.rect
    x0 = _clamp(min(x0, x1), 0.0, ancho)
    x1 = _clamp(max(x0, x1), 0.0, ancho)
    y0 = _clamp(min(y0, y1), 0.0, alto)
    y1 = _clamp(max(y0, y1), 0.0, alto)
    cab = (
        f"<< /Type /Annot /Subtype /Link "
        f"/Rect [{_num(x0)} {_num(y0)} {_num(x1)} {_num(y1)}] "
        f"/Border [0 0 0] /A << /Type /Action /S /URI /URI ("
    ).encode("ascii")
    uri = _literal(anot.uri, ctx="uri de anotacion")
    cola = b") >> >>"
    return cab + uri + cola


# --------------------------------------------------------------------------- #
# Ensamblado del documento completo
# --------------------------------------------------------------------------- #


def _escribir_documento(
    escritor: EscritorPDF,
    paginas: list[PaginaRender],
    *,
    titulo: str,
    ancho: float = A4_W,
    alto: float = A4_H,
    con_banda: bool = True,
) -> None:
    """Escribe todos los objetos del documento en un `EscritorPDF` ya abierto.

    `ancho`/`alto` fijan el `/MediaBox` de cada página (A4 por defecto; una
    proporción vertical de teléfono para las láminas). `con_banda` controla si
    se emite el XObject de banda A4 y su invocación por página: se pone en
    `False` para páginas cuya geometría no es A4 (láminas verticales).
    """
    if not paginas:
        raise ErrorPDF(
            "no hay paginas que escribir en el PDF",
            codigo=E_PDF_CORRUPTO,
            detalle={"paginas": 0},
        )

    # Reservar ids para los objetos con referencias circulares o tardías.
    raiz_id = escritor.reservar_id()   # Catalog
    pages_id = escritor.reservar_id()  # Pages (kids se conocen al final)

    # Recursos compartidos por todas las páginas.
    f1_id = escritor.obj(_dic_fuente("Helvetica"))
    f2_id = escritor.obj(_dic_fuente("Helvetica-Bold"))
    banda_id: int | None = None
    if con_banda:
        banda_ops = _contenido_banda()
        banda_id = escritor.stream(
            f"/Type /XObject /Subtype /Form "
            f"/BBox [0 0 {_num(A4_W)} {_num(A4_H)}] /Resources << >>",
            banda_ops,
        )

    caja_media = f"/MediaBox [0 0 {_num(ancho)} {_num(alto)}]"

    page_ids: list[int] = []
    for pagina in paginas:
        # 1. Stream de contenido de la página.
        contenido = _contenido_pagina(pagina, con_banda=con_banda)
        contenido_id = escritor.stream("", contenido)

        # 2. Anotaciones /Link de la página (recortadas al tamaño real).
        annot_ids: list[int] = []
        for anot in pagina.anotaciones:
            annot_ids.append(
                escritor.obj(_dic_anotacion(anot, ancho=ancho, alto=alto))
            )

        # 3. Objeto de página.
        if banda_id is not None:
            recursos = (
                f"<< /Font << /F1 {f1_id} 0 R /F2 {f2_id} 0 R >> "
                f"/XObject << /Banda {banda_id} 0 R >> >>"
            )
        else:
            recursos = f"<< /Font << /F1 {f1_id} 0 R /F2 {f2_id} 0 R >> >>"
        annots = ""
        if annot_ids:
            refs = " ".join(f"{aid} 0 R" for aid in annot_ids)
            annots = f" /Annots [ {refs} ]"
        cuerpo = (
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"{caja_media} "
            f"/Resources {recursos} "
            f"/Contents {contenido_id} 0 R{annots} >>"
        ).encode("ascii")
        page_ids.append(escritor.obj(cuerpo))

    # Árbol de páginas (rellena el id reservado).
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    escritor.obj(
        (
            f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_ids)} >>"
        ).encode("ascii"),
        oid=pages_id,
    )

    # Catálogo (rellena el id reservado).
    escritor.obj(
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"),
        oid=raiz_id,
    )

    # Info del documento (título como literal de texto).
    info = b"<< /Title (" + _literal(titulo, ctx="titulo del documento") + b") >>"
    info_id = escritor.obj(info)

    escritor.cerrar(raiz_id, info_id)


def escribir_pdf(
    paginas: list[PaginaRender],
    ruta: str,
    *,
    comprimir: bool = True,
    titulo: str = "Guia Extensa Sub-17",
    ancho: float = A4_W,
    alto: float = A4_H,
    con_banda: bool = True,
) -> None:
    """Escribe el Modelo_Paginas como un PDF en `ruta`.

    Punto de entrada del Motor_PDF. Abre el archivo, emite fuentes Standard-14,
    la banda compartida (si `con_banda`), una página por `PaginaRender` con sus
    anotaciones `/Link`, el árbol de páginas, el catálogo, la info y la
    xref/trailer. `ancho`/`alto` fijan el `/MediaBox` (A4 por defecto; una
    proporción vertical de teléfono para las láminas).
    """
    with EscritorPDF(ruta, comprimir=comprimir) as escritor:
        _escribir_documento(
            escritor, paginas, titulo=titulo, ancho=ancho, alto=alto,
            con_banda=con_banda,
        )


def documento_a_bytes(
    paginas: list[PaginaRender],
    *,
    comprimir: bool = True,
    titulo: str = "Guia Extensa Sub-17",
    ancho: float = A4_W,
    alto: float = A4_H,
    con_banda: bool = True,
) -> bytes:
    """Genera el PDF en un archivo temporal y devuelve sus bytes.

    Útil para pruebas y para el verificador estructural sin dejar artefactos.
    """
    import os
    import tempfile

    fd, ruta = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        escribir_pdf(
            paginas, ruta, comprimir=comprimir, titulo=titulo, ancho=ancho,
            alto=alto, con_banda=con_banda,
        )
        with open(ruta, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass
