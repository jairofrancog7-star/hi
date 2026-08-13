"""Periodización práctica del ciclo de 12 semanas (tarea 26).

Este módulo rinde **únicamente el contenido práctico** de la periodización de 12
semanas (cómo se organiza el mesociclo: foco, carga, progresión, prevención e
indicadores medibles). Es **contenido práctico**, no fichas: no crea ninguna
`Ficha_Ejercicio` (esas siguen viniendo solo del `Catalogo_JSON`) ni altera el
umbral de publicación; la guía sigue en MODO MUESTRA / NO_PUBLICABLE.

La metodología queda **destilada internamente** en esta periodización: las
fuentes de metodología son **referencia interna de diseño**, documentadas en
`design.md`, y **NUNCA** se imprimen en la guía (Target_Web, PDF, láminas ni
`publicacion/`). Los únicos enlaces visibles de la guía son los videos útiles de
las fichas del `Catalogo_JSON`, nunca fuentes de metodología.

Contiene:

* un modelo de datos inmutable (`BloquePeriodizacion`, `PlanPeriodizacion`) y la
  constante `PLAN_12_SEMANAS` con los tres bloques de 4 semanas (Base 1–4,
  Desarrollo 5–8, Competición 9–12) que cubren el mesociclo completo, con foco,
  carga, nivel FIFA 11+ e indicadores medibles;
* un validador puro `validar_plan(...)` que verifica la cobertura consecutiva de
  las 12 semanas y la presencia de foco e indicadores en cada bloque, fallando
  con `ErrorBuild(E_COBERTURA_MINIMA, ...)` (nunca `assert`);
* un render HTML puro `render_html(...)` que emite un `<section>` con la tabla de
  bloques y la microestructura de sesión, reutilizando la estética CONGELADA
  (escapado y clases CSS de `build_html`), sin recursos externos.

Convenciones del proyecto: solo librería estándar; sin `assert` (los invariantes
se comprueban con `raise ErrorBuild`); `from __future__ import annotations`; type
hints; acumulación en `list[str]` unida con `''.join(...)`.

_Requirements: 5.1, 5.5, 5.6, 6.1_
"""

from __future__ import annotations

from dataclasses import dataclass

from . import build_html
from .errores import E_COBERTURA_MINIMA, ErrorBuild

__all__ = [
    "BloquePeriodizacion",
    "PlanPeriodizacion",
    "PLAN_12_SEMANAS",
    "validar_plan",
    "render_html",
]

#: Total de semanas del mesociclo (tres bloques de 4 semanas).
_SEMANAS_TOTALES: int = 12


# --------------------------------------------------------------------------- #
# Modelo de datos inmutable
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class BloquePeriodizacion:
    """Un bloque de 4 semanas del mesociclo (macro → meso → micro).

    Declara su rango de semanas (`semana_inicio`..`semana_fin`, ambos inclusive),
    su foco, la carga prevista, el nivel de prevención FIFA 11+ y los indicadores
    medibles con que se verifica el progreso semana a semana.
    """

    numero: int
    nombre: str
    semana_inicio: int
    semana_fin: int
    foco: tuple[str, ...]
    carga: str
    nivel_prevencion: str
    indicadores: tuple[str, ...]

    @property
    def semanas(self) -> int:
        """Cantidad de semanas que abarca el bloque (ambos extremos inclusive)."""
        return self.semana_fin - self.semana_inicio + 1

    @property
    def rango(self) -> str:
        """Rango legible de semanas, p. ej. ``"1–4"`` (guion largo)."""
        return f"{self.semana_inicio}\u2013{self.semana_fin}"


@dataclass(frozen=True, slots=True)
class PlanPeriodizacion:
    """Plan de periodización completo: bloques + microestructura + notas."""

    bloques: tuple[BloquePeriodizacion, ...]
    microestructura: tuple[str, ...]
    notas: tuple[str, ...]


# --------------------------------------------------------------------------- #
# Datos del plan de 12 semanas (paráfrasis propia de la tabla de design.md)
# --------------------------------------------------------------------------- #

PLAN_12_SEMANAS: PlanPeriodizacion = PlanPeriodizacion(
    bloques=(
        BloquePeriodizacion(
            numero=1,
            nombre="Base",
            semana_inicio=1,
            semana_fin=4,
            foco=(
                "Técnica individual",
                "Base aeróbica",
                "Adaptación a la carga",
            ),
            carga="Volumen medio, intensidad baja-media",
            nivel_prevencion="Nivel 1 (control rodilla-punta)",
            indicadores=(
                "Test de dominio y conducción",
                "Adherencia de 3 sesiones por semana",
                "Registro del esfuerzo percibido (RPE)",
            ),
        ),
        BloquePeriodizacion(
            numero=2,
            nombre="Desarrollo",
            semana_inicio=5,
            semana_fin=8,
            foco=(
                "Técnica con oposición",
                "Juego por posición",
                "Fuerza sin gimnasio",
                "Escaneo y lectura del juego",
            ),
            carga="Intensidad y complejidad al alza (espacio reducido, más jugadoras)",
            nivel_prevencion="Nivel 2 (pliometría de bajo impacto)",
            indicadores=(
                "Indicadores por posición",
                "Test de pase y definición",
                "Registro de progreso en escala 1 a 5",
            ),
        ),
        BloquePeriodizacion(
            numero=3,
            nombre="Competición",
            semana_inicio=9,
            semana_fin=12,
            foco=(
                "Juego colectivo (presión, salida y transición)",
                "Toma de decisión",
                "Ritmo de partido",
                "Preparación mental previa al partido",
            ),
            carga="Intensidad alta; la semana 12 baja a descarga (afinamiento)",
            nivel_prevencion="Nivel 3 (aterrizaje y frenado)",
            indicadores=(
                "Indicadores de partido",
                "Autoevaluación",
                "Adherencia al plan",
            ),
        ),
    ),
    microestructura=(
        "Calentamiento dinámico: circulación → movilidad → activación → "
        "neuromuscular → específico",
        "Parte principal: trabajo técnico y táctico según el bloque",
        "Vuelta a la calma: estiramientos suaves y respiración",
        "Duración objetivo por sesión: hasta 90 minutos",
        "Versión corta cuando el tiempo apremia: hasta 30 minutos",
    ),
    notas=(
        "La activación neuromuscular preventiva aparece en todas las sesiones y "
        "escala de nivel con el bloque, cuidando la carga según el ciclo menstrual.",
        "Las fichas se ordenan de menor a mayor complejidad y se etiquetan por "
        "posición; el juego por posiciones gana peso en los bloques 2 y 3.",
        "Cada bloque declara indicadores observables para que el progreso sea "
        "verificable semana a semana y no subjetivo.",
        "Si una semana se cae por lluvia, examenes o falta de jugadoras, se "
        "repite esa semana antes de pasar al bloque siguiente: el orden importa "
        "mas que la prisa.",
    ),
)


# --------------------------------------------------------------------------- #
# Validación (sin assert: raise ErrorBuild)
# --------------------------------------------------------------------------- #


def validar_plan(plan: PlanPeriodizacion) -> None:
    """Valida que el plan cubra 12 semanas consecutivas con bloques completos.

    Comprueba que:

    * hay al menos un bloque;
    * cada bloque tiene un rango de semanas coherente y foco e indicadores no
      vacíos, además de carga y nivel de prevención;
    * los bloques, ordenados por semana de inicio, encadenan sin huecos ni
      solapes desde la semana 1 hasta la 12.

    Ante cualquier incumplimiento lanza `ErrorBuild(E_COBERTURA_MINIMA, ...)`.
    No usa `assert` (los invariantes viajan como excepción del build).
    """
    bloques = plan.bloques
    if not bloques:
        raise ErrorBuild(
            E_COBERTURA_MINIMA,
            "el plan de periodización no tiene bloques",
        )

    ordenados = sorted(bloques, key=lambda b: b.semana_inicio)
    esperado = 1
    for bloque in ordenados:
        if bloque.semana_inicio > bloque.semana_fin:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "un bloque de periodización tiene un rango de semanas inválido",
                detalle={
                    "bloque": bloque.numero,
                    "inicio": bloque.semana_inicio,
                    "fin": bloque.semana_fin,
                },
            )
        if not bloque.foco:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "un bloque de periodización no declara foco",
                detalle={"bloque": bloque.numero},
            )
        if not bloque.indicadores:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "un bloque de periodización no declara indicadores",
                detalle={"bloque": bloque.numero},
            )
        if not bloque.carga:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "un bloque de periodización no declara carga",
                detalle={"bloque": bloque.numero},
            )
        if not bloque.nivel_prevencion:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "un bloque de periodización no declara nivel de prevención",
                detalle={"bloque": bloque.numero},
            )
        if bloque.semana_inicio != esperado:
            raise ErrorBuild(
                E_COBERTURA_MINIMA,
                "los bloques de periodización no cubren las semanas de forma "
                "consecutiva (hueco o solape)",
                detalle={
                    "esperado": esperado,
                    "encontrado": bloque.semana_inicio,
                    "bloque": bloque.numero,
                },
            )
        esperado = bloque.semana_fin + 1

    cubiertas = esperado - 1
    if cubiertas != _SEMANAS_TOTALES:
        raise ErrorBuild(
            E_COBERTURA_MINIMA,
            "el plan de periodización no cubre exactamente 12 semanas",
            detalle={"semanas_cubiertas": cubiertas, "esperadas": _SEMANAS_TOTALES},
        )


# --------------------------------------------------------------------------- #
# Render HTML (estética CONGELADA: escapado y clases de build_html)
# --------------------------------------------------------------------------- #


def render_html(plan: PlanPeriodizacion | None = None) -> str:
    """Rinde el plan de 12 semanas como fragmento HTML (`<section>`).

    Emite una `<section id="plan-12-semanas">` con un `<h2>`, una tabla de los
    tres bloques (envuelta en `div.scroll-x` como el resto del sitio) y la
    microestructura de sesión como lista. Todo el texto se escapa con
    `build_html._esc`. Sin recursos externos, sin `<style>` inline (reutiliza el
    CSS CONGELADO) y sin `<script>`.
    """
    if plan is None:
        plan = PLAN_12_SEMANAS
    validar_plan(plan)

    partes: list[str] = []
    partes.append('<section id="plan-12-semanas">')
    partes.append("<h2>Periodización del ciclo de 12 semanas</h2>")
    partes.append(
        "<p>El ciclo se divide en tres bloques de cuatro semanas, cada uno con "
        "su objetivo, su carga y su foco. Se avanza de volumen a intensidad y la "
        "semana 12 es de afinamiento para llegar enteras al partido.</p>"
    )

    partes.append('<div class="scroll-x">')
    partes.append("<table>")
    partes.append("<thead><tr>")
    for encabezado in (
        "Bloque",
        "Semanas",
        "Foco",
        "Carga",
        "Prevención (FIFA 11+)",
        "Medición",
    ):
        partes.append(f"<th>{build_html._esc(encabezado)}</th>")
    partes.append("</tr></thead>")
    partes.append("<tbody>")
    for bloque in plan.bloques:
        nombre = f"{bloque.numero} {bloque.nombre}"
        partes.append("<tr>")
        partes.append(f"<td>{build_html._esc(nombre)}</td>")
        partes.append(f"<td>{build_html._esc(bloque.rango)}</td>")
        partes.append(f"<td>{build_html._esc(', '.join(bloque.foco))}</td>")
        partes.append(f"<td>{build_html._esc(bloque.carga)}</td>")
        partes.append(f"<td>{build_html._esc(bloque.nivel_prevencion)}</td>")
        partes.append(
            f"<td>{build_html._esc('; '.join(bloque.indicadores))}</td>"
        )
        partes.append("</tr>")
    partes.append("</tbody>")
    partes.append("</table>")
    partes.append("</div>")

    partes.append("<h3>Microestructura de la sesión</h3>")
    partes.append("<ul>")
    for paso in plan.microestructura:
        partes.append(f"<li>{build_html._esc(paso)}</li>")
    partes.append("</ul>")

    if plan.notas:
        partes.append("<h3>Notas para la entrenadora</h3>")
        partes.append("<ul>")
        for nota in plan.notas:
            partes.append(f"<li>{build_html._esc(nota)}</li>")
        partes.append("</ul>")

    partes.append("</section>")
    return "".join(partes)
