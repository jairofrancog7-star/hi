"""Códigos de error y jerarquía de excepciones del build.

Este módulo centraliza los códigos de error `E_*` usados por todas las etapas
del build (preflight, validación de contenido, layout, generación de PDF,
verificación de QR, control de tiempos) y define la jerarquía de excepciones
que los transporta. Cualquier fallo del build se reporta como un
`ErrorBuild` (o una de sus subclases) con un código perteneciente a
`CODIGOS`, un mensaje legible en español y un `detalle` opcional con datos
estructurados para diagnóstico.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Códigos de error
# --------------------------------------------------------------------------- #

E_DEPENDENCIA: str = "E_DEPENDENCIA"
E_FICHA_INCOMPLETA: str = "E_FICHA_INCOMPLETA"
E_COBERTURA_MINIMA: str = "E_COBERTURA_MINIMA"
E_CARACTER_NO_CODIFICABLE: str = "E_CARACTER_NO_CODIFICABLE"
E_DESBORDE_TEXTO: str = "E_DESBORDE_TEXTO"
E_ETIQUETAS_NO_CABEN: str = "E_ETIQUETAS_NO_CABEN"
E_COORDENADA_INVALIDA: str = "E_COORDENADA_INVALIDA"
E_QR_NO_VERIFICA: str = "E_QR_NO_VERIFICA"
E_QR_CAPACIDAD: str = "E_QR_CAPACIDAD"
E_PDF_CORRUPTO: str = "E_PDF_CORRUPTO"
E_OPERADORES_DESBALANCEADOS: str = "E_OPERADORES_DESBALANCEADOS"
E_INDICE_DESALINEADO: str = "E_INDICE_DESALINEADO"
E_ROTACION_DUPLICADA: str = "E_ROTACION_DUPLICADA"
E_ROTACION_SIN_COMBINACION: str = "E_ROTACION_SIN_COMBINACION"
E_TIEMPO_EXCEDIDO: str = "E_TIEMPO_EXCEDIDO"
E_PAGINACION_INESTABLE: str = "E_PAGINACION_INESTABLE"

# Addendum A — pipeline JSON-driven del Catalogo_JSON (feature "Entrena como
# las grandes"). Se suman a la tabla de Error Handling sin borrar nada.
E_JSON_NO_PARSEA: str = "E_JSON_NO_PARSEA"
E_FICHA_JSON_INVALIDA: str = "E_FICHA_JSON_INVALIDA"

# Guardarrail de fuente unica de fichas (Req 15.2, 15.4): ningun modulo de
# contenido `capNN_*.py` puede construir una `FichaEjercicio`; las fichas viven
# solo en el Catalogo_JSON. Si el Orquestador_Build detecta una construccion de
# FichaEjercicio dentro de un modulo de capitulo, falla con este codigo.
E_FICHA_EN_MODULO: str = "E_FICHA_EN_MODULO"

# Feature "imagenes-reales-hero-interactivo" — Asset_Local de los
# Diagrama_Postura (`assets/img/tecnica/`). `E_ASSET_FALTANTE` cuando falta el
# Archivo_Diagrama de una entrada marcada Requiere_Archivo en Modo_Estricto
# (Req 5.8); `E_ASSET_INVALIDO` cuando la firma de la copia no corresponde a su
# extension (Req 5.13) o cuando una estructura declarativa de la feature
# (Catalogo_Diagramas, Advertencia_Cabeceo, catalogo de Elemento_Fondo,
# registro de Seccion_Reservada) no cumple su invariante.
E_ASSET_FALTANTE: str = "E_ASSET_FALTANTE"
E_ASSET_INVALIDO: str = "E_ASSET_INVALIDO"

CODIGOS: frozenset[str] = frozenset(
    {
        E_DEPENDENCIA,
        E_FICHA_INCOMPLETA,
        E_COBERTURA_MINIMA,
        E_CARACTER_NO_CODIFICABLE,
        E_DESBORDE_TEXTO,
        E_ETIQUETAS_NO_CABEN,
        E_COORDENADA_INVALIDA,
        E_QR_NO_VERIFICA,
        E_QR_CAPACIDAD,
        E_PDF_CORRUPTO,
        E_OPERADORES_DESBALANCEADOS,
        E_INDICE_DESALINEADO,
        E_ROTACION_DUPLICADA,
        E_ROTACION_SIN_COMBINACION,
        E_TIEMPO_EXCEDIDO,
        E_PAGINACION_INESTABLE,
        E_JSON_NO_PARSEA,
        E_FICHA_JSON_INVALIDA,
        E_FICHA_EN_MODULO,
        E_ASSET_FALTANTE,
        E_ASSET_INVALIDO,
    }
)


# --------------------------------------------------------------------------- #
# Excepción base
# --------------------------------------------------------------------------- #


class ErrorBuild(Exception):
    """Error del build con código estable, mensaje y detalle opcional."""

    def __init__(
        self,
        codigo: str,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
    ) -> None:
        if codigo not in CODIGOS:
            raise ValueError(f"código de error desconocido: {codigo!r}")
        self.codigo: str = codigo
        self.mensaje: str = mensaje
        self.detalle: dict[str, object] = {} if detalle is None else dict(detalle)
        super().__init__(codigo, mensaje)

    def __str__(self) -> str:
        partes: list[str] = [self.codigo, ": ", self.mensaje]
        if self.detalle:
            pares: list[str] = [
                f"{clave}={self.detalle[clave]}" for clave in sorted(self.detalle)
            ]
            partes.append(" (")
            partes.append(", ".join(pares))
            partes.append(")")
        return "".join(partes)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(codigo={self.codigo!r}, "
            f"mensaje={self.mensaje!r}, detalle={self.detalle!r})"
        )


# --------------------------------------------------------------------------- #
# Subclases de un solo código
# --------------------------------------------------------------------------- #


class ErrorDependencia(ErrorBuild):
    """Falta una dependencia o su versión no es la esperada."""

    CODIGO_POR_DEFECTO: str = E_DEPENDENCIA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset({E_DEPENDENCIA})

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
    ) -> None:
        super().__init__(self.CODIGO_POR_DEFECTO, mensaje, detalle=detalle)


class ErrorCobertura(ErrorBuild):
    """El contenido no alcanza la cobertura mínima exigida."""

    CODIGO_POR_DEFECTO: str = E_COBERTURA_MINIMA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset({E_COBERTURA_MINIMA})

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
    ) -> None:
        super().__init__(self.CODIGO_POR_DEFECTO, mensaje, detalle=detalle)


class ErrorQR(ErrorBuild):
    """Un código QR no supera la verificación o la URL no cabe en el símbolo.

    Transporta dos códigos: `E_QR_NO_VERIFICA` (el round-trip del decodificador
    no reproduce la URL de origen) y `E_QR_CAPACIDAD` (la URL excede la
    capacidad de la versión máxima soportada por `qr.py`, de modo que ni
    siquiera puede codificarse; se usa para no colgar el pipeline con un
    `ValueError` crudo).
    """

    CODIGO_POR_DEFECTO: str = E_QR_NO_VERIFICA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_QR_NO_VERIFICA, E_QR_CAPACIDAD}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorRotacion(ErrorBuild):
    """Fallo del Plan_Rotacion: combinaciones duplicadas o sin combinación libre.

    Transporta dos códigos: `E_ROTACION_DUPLICADA` (el verificador independiente
    halló dos Bloque_Semanal con la misma combinación de fichas) y
    `E_ROTACION_SIN_COMBINACION` (el generador agotó `MAX_REPARACIONES` sin
    lograr una firma nueva para un bloque).
    """

    CODIGO_POR_DEFECTO: str = E_ROTACION_DUPLICADA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_ROTACION_DUPLICADA, E_ROTACION_SIN_COMBINACION}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorTiempo(ErrorBuild):
    """Una etapa del build excedió su presupuesto de tiempo."""

    CODIGO_POR_DEFECTO: str = E_TIEMPO_EXCEDIDO
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset({E_TIEMPO_EXCEDIDO})

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
    ) -> None:
        super().__init__(self.CODIGO_POR_DEFECTO, mensaje, detalle=detalle)


# --------------------------------------------------------------------------- #
# Subclases con varios códigos posibles
# --------------------------------------------------------------------------- #


class ErrorEsquema(ErrorBuild):
    """El contenido no cumple el esquema o no es codificable."""

    CODIGO_POR_DEFECTO: str = E_FICHA_INCOMPLETA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_FICHA_INCOMPLETA, E_CARACTER_NO_CODIFICABLE}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorLayout(ErrorBuild):
    """Fallo de maquetación: desborde, coordenadas o paginación."""

    CODIGO_POR_DEFECTO: str = E_DESBORDE_TEXTO
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {
            E_DESBORDE_TEXTO,
            E_ETIQUETAS_NO_CABEN,
            E_COORDENADA_INVALIDA,
            E_INDICE_DESALINEADO,
            E_PAGINACION_INESTABLE,
        }
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorPDF(ErrorBuild):
    """El PDF generado está corrupto o mal formado."""

    CODIGO_POR_DEFECTO: str = E_PDF_CORRUPTO
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_PDF_CORRUPTO, E_OPERADORES_DESBALANCEADOS}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorCatalogoJSON(ErrorBuild):
    """El Catalogo_JSON no parsea o una Ficha_JSON no cumple el esquema.

    Transporta los códigos del Addendum A: `E_JSON_NO_PARSEA` cuando
    `ejercicios.json` no es JSON válido (con offset/línea) y
    `E_FICHA_JSON_INVALIDA` cuando una Ficha_JSON carece de un campo
    obligatorio o un Media_Item tiene un `tipo` fuera del conjunto permitido
    (con el `id` de la ficha y el campo o valor inválido).
    """

    CODIGO_POR_DEFECTO: str = E_FICHA_JSON_INVALIDA
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_JSON_NO_PARSEA, E_FICHA_JSON_INVALIDA}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


class ErrorFuenteFichas(ErrorBuild):
    """Un módulo de contenido `capNN_*.py` construye una `FichaEjercicio`.

    Transporta el código `E_FICHA_EN_MODULO` del guardarraíl de fuente única
    (Req 15.2, 15.4): las Ficha_Ejercicio deben vivir solo en el Catalogo_JSON,
    no incrustadas en módulos de contenido. El detalle nombra el `modulo`
    infractor.
    """

    CODIGO_POR_DEFECTO: str = E_FICHA_EN_MODULO
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset({E_FICHA_EN_MODULO})

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
    ) -> None:
        super().__init__(self.CODIGO_POR_DEFECTO, mensaje, detalle=detalle)


class ErrorAsset(ErrorBuild):
    """Falta un Archivo_Diagrama o un asset declarado no es valido.

    Transporta los dos codigos de la feature "imagenes-reales-hero-interactivo":
    `E_ASSET_FALTANTE` (falta el Archivo_Diagrama de una entrada marcada
    Requiere_Archivo mientras el build corre en Modo_Estricto, Req 5.8) y
    `E_ASSET_INVALIDO` (la firma de la copia no corresponde a su extension,
    Req 5.13, o una estructura declarativa de la feature rompe un invariante:
    Catalogo_Diagramas, Advertencia_Cabeceo, catalogo de Elemento_Fondo,
    registro de Seccion_Reservada). El codigo por defecto es
    `E_ASSET_INVALIDO`; el mensaje nombra la ruta relativa o el identificador
    afectado.
    """

    CODIGO_POR_DEFECTO: str = E_ASSET_INVALIDO
    CODIGOS_PERMITIDOS: frozenset[str] = frozenset(
        {E_ASSET_FALTANTE, E_ASSET_INVALIDO}
    )

    def __init__(
        self,
        mensaje: str,
        *,
        detalle: dict[str, object] | None = None,
        codigo: str | None = None,
    ) -> None:
        elegido: str = self.CODIGO_POR_DEFECTO if codigo is None else codigo
        if elegido not in self.CODIGOS_PERMITIDOS:
            raise ValueError(
                f"código {elegido!r} no permitido para {type(self).__name__}"
            )
        super().__init__(elegido, mensaje, detalle=detalle)


__all__ = [
    "CODIGOS",
    "E_ASSET_FALTANTE",
    "E_ASSET_INVALIDO",
    "E_CARACTER_NO_CODIFICABLE",
    "E_COBERTURA_MINIMA",
    "E_COORDENADA_INVALIDA",
    "E_DEPENDENCIA",
    "E_DESBORDE_TEXTO",
    "E_ETIQUETAS_NO_CABEN",
    "E_FICHA_EN_MODULO",
    "E_FICHA_INCOMPLETA",
    "E_FICHA_JSON_INVALIDA",
    "E_INDICE_DESALINEADO",
    "E_JSON_NO_PARSEA",
    "E_OPERADORES_DESBALANCEADOS",
    "E_PAGINACION_INESTABLE",
    "E_PDF_CORRUPTO",
    "E_QR_CAPACIDAD",
    "E_QR_NO_VERIFICA",
    "E_ROTACION_DUPLICADA",
    "E_ROTACION_SIN_COMBINACION",
    "E_TIEMPO_EXCEDIDO",
    "ErrorAsset",
    "ErrorBuild",
    "ErrorCatalogoJSON",
    "ErrorCobertura",
    "ErrorDependencia",
    "ErrorEsquema",
    "ErrorFuenteFichas",
    "ErrorLayout",
    "ErrorPDF",
    "ErrorQR",
    "ErrorRotacion",
    "ErrorTiempo",
]
