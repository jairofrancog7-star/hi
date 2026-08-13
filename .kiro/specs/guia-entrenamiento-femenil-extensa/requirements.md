# Requirements Document

## Introduction

Esta funcionalidad amplía la guía de entrenamiento existente (21 páginas A4, 15 fichas de ejercicio y 13 láminas verticales) hasta convertirla en una **Guía Extensa de Entrenamiento de Fútbol Femenil Sub-17** de 200 a 300 páginas A4, publicada simultáneamente en PDF y en HTML estático, lista para subirse al repositorio de GitHub `jairofrancog7-star/hi` con enlace de descarga directo.

La guía está dirigida al equipo femenil sub-17 de Rincón de Centeno: asistencia variable de 1 a 8 jugadoras, cancha compartida con niños y béisbol, entrenamiento de martes a jueves de 4:00 pm hasta antes de oscurecer, partido de liga los sábados, sin entrenador remunerado y con material mínimo (balón, botellas de refresco, una pared y gis).

El alcance incluye: rotación de entrenamientos por semanas para que ninguna semana se repita, cobertura de las siete posiciones de campo (portera, lateral, central, contención/pivote, media, extremo, delantera), prevención de lesiones específica del cuerpo femenino (LCA/rodilla, cadera, FIFA 11+, fuerza de glúteo e isquiotibiales, ciclo menstrual, alimentación e hierro), preparación mental y visual, variantes por número de jugadoras presentes y por tamaño de espacio disponible, y el rediseño del diagrama de zonas de contacto del botín para que sea legible sin ambigüedad.

La generación se realiza con el pipeline propio en **Python 3.11+ usando exclusivamente la librería estándar** (`qr.py`, `viz.py`, `draw.py`, `contenido/` como paquete, `build_pdf.py`, `build_html.py`, `build.py`), sin librerías externas, sin `pip`, sin navegador headless y sin acceso a internet. (Portado desde el pipeline original en Node/Bun; ver la Nota de portabilidad de `design.md`. Resuelto como **C7**.)

## Glossary

- **Guia_Extensa**: documento final de entrenamiento de 200 a 300 páginas A4, entregado en formato PDF y en formato HTML.
- **Ficha_Ejercicio**: unidad de contenido de la Guia_Extensa que contiene título, objetivo, diagrama de cancha, pasos numerados, dosis (series, repeticiones, tiempo), criterio de observación ("qué mira la compañera"), variante para espacio reducido, variante por número de jugadoras y enlace de video con código QR.
- **Bloque_Semanal**: conjunto de sesiones de entrenamiento (martes, miércoles, jueves) más indicaciones de partido del sábado, correspondiente a una semana concreta del plan.
- **Plan_Rotacion**: secuencia ordenada de Bloque_Semanal que cubre el ciclo completo de la Guia_Extensa sin repetir la misma combinación de Ficha_Ejercicio en dos Bloque_Semanal distintos.
- **Modulo_Posicion**: capítulo de la Guia_Extensa dedicado a una posición específica: portera, lateral, central, contención/pivote, media, extremo o delantera.
- **Modulo_Prevencion**: capítulo de la Guia_Extensa dedicado a prevención de lesiones y cuidado del cuerpo femenino.
- **Modulo_Mental**: capítulo de la Guia_Extensa dedicado a confianza, rutina pre-partido, gestión del error, visualización y comunicación en cancha.
- **Diagrama_Botin**: ilustración vectorial de la silueta de un botín que identifica y etiqueta las zonas de contacto con el balón: pase (interior), cañonazo (empeine), tres dedos, efecto (exterior), planta, tacón y punta.
- **Diagrama_Cancha**: ilustración vectorial generada por el Motor_Diagramas que representa un espacio de juego con jugadoras, conos/botellas, balón, trayectorias de pase, de conducción y de desmarque.
- **Lamina_Vertical**: página de formato vertical con estilo infografía rosa/negro, diseñada para compartirse por WhatsApp.
- **Motor_Diagramas**: componente del pipeline (`viz.py` + `draw.py`) que dibuja Diagrama_Cancha, Diagrama_Botin y Diagrama_Postura en SVG y en operadores de contenido PDF.
- **Diagrama_Postura**: ilustración vectorial que muestra la ejecución correcta y la ejecución incorrecta de un gesto técnico o de un ejercicio de fuerza, con marcas señalando el punto a corregir.
- **Generador_QR**: componente del pipeline (`qr.py`) que codifica una URL en un código QR y verifica el resultado con su propio decodificador.
- **Motor_PDF**: componente del pipeline (`build_pdf.py`) que escribe el archivo PDF de la Guia_Extensa sin librerías externas, usando las 14 fuentes estándar de PDF y anotaciones de enlace clicables.
- **Motor_HTML**: componente del pipeline (`build_html.py`) que escribe la versión HTML estática de la Guia_Extensa sin JavaScript.
- **Orquestador_Build**: componente del pipeline (`build.py`) que ejecuta la generación completa y las validaciones de salida.
- **Catalogo_Contenido**: estructura de datos (paquete `contenido/`, un módulo por capítulo) que declara todas las Ficha_Ejercicio, Bloque_Semanal, Modulo_Posicion, Modulo_Prevencion, Modulo_Mental y Lamina_Vertical de la Guia_Extensa.
- **Espacio_Reducido**: superficie de entrenamiento de 10 m × 10 m o menor, o cualquier franja disponible cuando la cancha está ocupada por otros grupos.
- **Espacio_Completo**: cancha o media cancha disponible sin restricción de otros grupos.
- **Imagen_Fotorrealista**: imagen en formato WebP de una jugadora juvenil genérica generada por IA, almacenada localmente en `assets/img/`, que muestra posturas técnicas reales con fondo azul claro, utilizada en el hero del sitio HTML con efectos de parallax y zoom.

## Requirements

### Requirement 1: Extensión y estructura del documento

**User Story:** Como jugadora sub-17 sin entrenador, quiero una guía muy amplia y ordenada, para tener material suficiente para entrenar durante toda la temporada sin quedarme sin ejercicios.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL contener entre 200 y 300 páginas en formato A4.
2. THE Guia_Extensa SHALL contener un índice general que liste cada capítulo y cada Modulo_Posicion con su número de página.
3. THE Guia_Extensa SHALL contener al menos 120 Ficha_Ejercicio distintas.
4. THE Guia_Extensa SHALL numerar todas las páginas de forma consecutiva empezando en 1.
5. THE Guia_Extensa SHALL incluir en cada página un encabezado o pie que indique el capítulo al que pertenece la página.
6. THE Guia_Extensa SHALL estar redactada íntegramente en español de México con lenguaje directo dirigido a jugadoras adolescentes.
7. WHERE una Ficha_Ejercicio ocupa más de una página, THE Guia_Extensa SHALL mantener el título de la Ficha_Ejercicio visible en cada página de esa ficha.
8. THE Orquestador_Build SHALL reportar el número total de páginas generadas al finalizar la construcción.
9. IF el número de páginas generadas es menor que 200 o mayor que 300, THEN THE Orquestador_Build SHALL terminar con código de error e indicar el conteo obtenido.

### Requirement 2: Doble formato de entrega y publicación

**User Story:** Como responsable del equipo, quiero la guía en PDF y en HTML dentro del repositorio de GitHub, para imprimirla o compartirla por enlace según la situación.

#### Acceptance Criteria

1. THE Orquestador_Build SHALL generar un archivo PDF de la Guia_Extensa y un conjunto de archivos HTML de la Guia_Extensa en la misma ejecución.
2. THE Motor_PDF SHALL escribir el archivo PDF sin usar librerías externas de terceros.
3. THE Motor_PDF SHALL usar únicamente las 14 fuentes estándar de PDF.
4. THE Motor_HTML SHALL generar HTML estático que se muestre completo sin ejecutar JavaScript.
5. THE Motor_HTML SHALL generar la Guia_Extensa con estilos que la hagan legible en pantalla de teléfono con ancho de 360 px.
6. THE Orquestador_Build SHALL colocar los archivos generados en la estructura de carpetas del repositorio `jairofrancog7-star/hi`.
7. THE Guia_Extensa en HTML SHALL incluir un enlace de descarga directa al archivo PDF.
8. THE Orquestador_Build SHALL completar la generación completa usando solo Python 3.11+ con la librería estándar, sin `pip`, sin navegador headless y sin acceso a internet. (Actualizado de Node/Bun a Python; resuelto como **C7**.)
9. IF una dependencia externa no está disponible en el entorno, THEN THE Orquestador_Build SHALL terminar con código de error e indicar el nombre del componente faltante.

### Requirement 3: Rediseño del diagrama del botín

**User Story:** Como jugadora, quiero ver claramente con qué parte del pie se golpea el balón en cada caso, para dejar de golpear con la zona equivocada.

#### Acceptance Criteria

1. THE Motor_Diagramas SHALL dibujar el Diagrama_Botin con una silueta de botín vista desde arriba y una segunda silueta vista de perfil.
2. THE Diagrama_Botin SHALL identificar por separado las zonas de pase (interior), cañonazo (empeine), tres dedos, efecto (exterior), planta, tacón y punta.
3. THE Diagrama_Botin SHALL asignar a cada zona un relleno visualmente distinguible de las zonas adyacentes.
4. THE Diagrama_Botin SHALL colocar la etiqueta de cada zona fuera de la silueta y unirla a su zona con una línea guía.
5. THE Diagrama_Botin SHALL mantener todas las etiquetas sin solaparse entre sí.
6. THE Diagrama_Botin SHALL ocupar al menos media página A4 en la Guia_Extensa.
7. THE Diagrama_Botin SHALL indicar, junto a cada zona, para qué acción de juego se usa esa zona.
8. THE Diagrama_Botin SHALL conservar la paleta rosa/negro del estilo visual establecido.
9. WHERE la Guia_Extensa se imprime en escala de grises, THE Diagrama_Botin SHALL mantener las zonas distinguibles mediante tramas o niveles de gris diferentes.

### Requirement 4: Cobertura de todas las posiciones

**User Story:** Como jugadora que puede jugar en distintas posiciones, quiero entrenamientos específicos para cada puesto, para mejorar en el que me toque.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL incluir un Modulo_Posicion para portera, lateral, central, contención/pivote, media, extremo y delantera.
2. THE Guia_Extensa SHALL incluir al menos 12 Ficha_Ejercicio dentro de cada Modulo_Posicion.
3. THE Guia_Extensa SHALL describir en cada Modulo_Posicion las responsabilidades de esa posición en fase defensiva y en fase ofensiva.
4. THE Guia_Extensa SHALL incluir en cada Modulo_Posicion al menos 3 Ficha_Ejercicio ejecutables por una sola jugadora.
5. THE Guia_Extensa SHALL incluir en el Modulo_Posicion de delantera Ficha_Ejercicio de definición ante portera, remate de primera, remate de cabeza y penal.
6. THE Guia_Extensa SHALL incluir en el Modulo_Posicion de portera Ficha_Ejercicio de colocación, blocaje, salida por alto, uno contra uno y saque.
7. THE Guia_Extensa SHALL incluir en cada Modulo_Posicion una lista de indicadores medibles de progreso con su valor objetivo.
8. THE Guia_Extensa SHALL incluir un capítulo de juego colectivo que explique cómo se conectan las posiciones en presión, salida y transición.

### Requirement 5: Rotación semanal de entrenamientos

**User Story:** Como jugadora, quiero que cada semana el entrenamiento sea diferente, para no aburrirme y seguir mejorando.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL incluir un Plan_Rotacion de al menos 24 Bloque_Semanal.
2. THE Guia_Extensa SHALL definir en cada Bloque_Semanal una sesión para martes, una para miércoles y una para jueves.
3. THE Guia_Extensa SHALL definir en cada Bloque_Semanal las indicaciones de calentamiento y de enfoque para el partido de liga del sábado.
4. THE Plan_Rotacion SHALL asignar a cada Bloque_Semanal una combinación de Ficha_Ejercicio distinta de la de todos los demás Bloque_Semanal.
5. THE Guia_Extensa SHALL indicar en cada Bloque_Semanal el objetivo principal de la semana en una sola frase.
6. THE Guia_Extensa SHALL indicar en cada sesión la duración total y la duración de cada bloque de la sesión.
7. THE Guia_Extensa SHALL limitar la duración total de cada sesión a 90 minutos.
8. THE Guia_Extensa SHALL incluir una tabla de seguimiento donde la jugadora registre la fecha y las sesiones completadas de cada Bloque_Semanal.
9. IF la sesión planeada requiere luz natural que ya no está disponible, THEN THE Guia_Extensa SHALL ofrecer una versión corta de esa sesión de 30 minutos o menos.
10. THE Orquestador_Build SHALL verificar que no existan dos Bloque_Semanal con la misma combinación de Ficha_Ejercicio y terminar con código de error si encuentra una repetición.

### Requirement 6: Prevención de lesiones y cuidado del cuerpo femenino

**User Story:** Como jugadora, quiero saber cómo cuidar mis rodillas y mi cuerpo, para no lesionarme y poder seguir jugando.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL incluir un Modulo_Prevencion dedicado a prevención de lesiones en la jugadora femenina.
2. THE Modulo_Prevencion SHALL explicar por qué el riesgo de lesión del ligamento cruzado anterior es mayor en mujeres, cubriendo ángulo de cadera, control de rodilla y fuerza relativa de isquiotibiales.
3. THE Modulo_Prevencion SHALL incluir el programa FIFA 11+ completo con sus tres partes y su progresión por niveles.
4. THE Modulo_Prevencion SHALL incluir al menos 20 ejercicios de fuerza de glúteo, isquiotibiales, aductores y core ejecutables sin gimnasio y sin pesas.
5. THE Modulo_Prevencion SHALL incluir para cada ejercicio de fuerza un Diagrama_Postura con la ejecución correcta y la ejecución incorrecta.
6. THE Modulo_Prevencion SHALL incluir una técnica de aterrizaje y de frenado con marcas visuales de la alineación correcta de rodilla respecto a la punta del pie.
7. THE Modulo_Prevencion SHALL explicar cómo adaptar la carga de entrenamiento según la fase del ciclo menstrual.
8. THE Modulo_Prevencion SHALL incluir recomendaciones de alimentación e hidratación con alimentos ricos en hierro y en calcio disponibles localmente y de bajo costo.
9. THE Modulo_Prevencion SHALL incluir una rutina de movilidad y estiramiento posterior a la sesión de 10 minutos.
10. IF una jugadora presenta dolor articular persistente, hinchazón o inestabilidad de rodilla, THEN THE Modulo_Prevencion SHALL indicar suspender el entrenamiento de impacto y acudir a valoración médica.
11. THE Modulo_Prevencion SHALL declarar que el contenido es informativo y no sustituye la valoración de un profesional de la salud.

### Requirement 7: Preparación mental y visual

**User Story:** Como jugadora con poca confianza, quiero herramientas mentales y visuales, para jugar sin miedo y leer mejor el juego.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL incluir un Modulo_Mental dedicado a confianza, concentración y gestión del error.
2. THE Modulo_Mental SHALL incluir una rutina pre-partido paso a paso con tiempos, aplicable desde 60 minutos antes del silbatazo.
3. THE Modulo_Mental SHALL incluir un protocolo de reacción después de un error, ejecutable en menos de 10 segundos dentro del partido.
4. THE Modulo_Mental SHALL incluir al menos 8 ejercicios de visualización con guion escrito y duración indicada.
5. THE Modulo_Mental SHALL incluir al menos 10 ejercicios de comunicación en cancha con las frases exactas que debe gritar cada posición.
6. THE Modulo_Mental SHALL incluir al menos 10 ejercicios de escaneo visual y toma de decisiones ejecutables con balón y una pared.
7. THE Modulo_Mental SHALL incluir un registro semanal de autoevaluación con escala de 1 a 5 para confianza, concentración y comunicación.
8. WHERE la jugadora entrena sola, THE Modulo_Mental SHALL indicar la variante individual de cada ejercicio de comunicación.
9. THE Modulo_Mental SHALL incluir un capítulo de liderazgo para la jugadora que dirige el grupo cuando no hay entrenador.

### Requirement 8: Variantes por número de jugadoras y por espacio

**User Story:** Como jugadora que a veces llega sola y a veces con siete compañeras, quiero saber qué entrenar en cada caso, para no perder la tarde decidiendo.

#### Acceptance Criteria

1. THE Guia_Extensa SHALL indicar en cada Ficha_Ejercicio el número mínimo y máximo de jugadoras necesarias.
2. THE Guia_Extensa SHALL incluir una tabla de decisión que, a partir del número de jugadoras presentes de 1 a 11, indique qué sesión ejecutar.
3. THE Guia_Extensa SHALL incluir al menos 30 Ficha_Ejercicio ejecutables por una sola jugadora.
4. THE Guia_Extensa SHALL incluir para cada Ficha_Ejercicio una variante para Espacio_Reducido y una variante para Espacio_Completo.
5. WHERE la Ficha_Ejercicio requiere material, THE Guia_Extensa SHALL limitar el material a balón, botellas de refresco, una pared y gis.
6. WHILE la cancha está ocupada por otros grupos, THE Guia_Extensa SHALL indicar las Ficha_Ejercicio ejecutables en una franja lateral de 10 m × 10 m o menor.
7. THE Guia_Extensa SHALL incluir un protocolo de seguridad para entrenar en cancha compartida con niños y con béisbol.
8. IF llegan menos jugadoras de las que requiere la sesión planeada, THEN THE Guia_Extensa SHALL indicar la sesión sustituta para el número de jugadoras presentes.
9. THE Guia_Extensa SHALL indicar en cada sesión el trazado del espacio con gis y con botellas, con distancias en metros.

### Requirement 9: Contenido visual, estilo y enlaces verificados

**User Story:** Como jugadora, quiero dibujos claros y videos de ejemplo, para ver cómo se hace el ejercicio y corregir mi postura.

#### Acceptance Criteria

1. THE Motor_Diagramas SHALL generar un Diagrama_Cancha para cada Ficha_Ejercicio.
2. THE Guia_Extensa SHALL incluir al menos 40 Diagrama_Postura que muestren la ejecución correcta junto a la ejecución incorrecta.
3. THE Guia_Extensa SHALL marcar en cada Diagrama_Postura el punto exacto a corregir y el texto de la corrección.
4. THE Guia_Extensa SHALL reutilizar las 13 Lamina_Vertical existentes y añadir Lamina_Vertical adicionales con el mismo estilo infografía rosa/negro.
5. THE Guia_Extensa SHALL conservar las 15 Ficha_Ejercicio existentes de la guía de 21 páginas.
6. WHERE una Ficha_Ejercicio tiene video de referencia, THE Motor_PDF SHALL incluir una anotación de enlace clicable y un código QR impreso hacia ese video.
7. THE Generador_QR SHALL verificar cada código QR generado con su propio decodificador antes de incluirlo en la Guia_Extensa.
8. IF la verificación de un código QR no reproduce la URL de origen, THEN THE Orquestador_Build SHALL terminar con código de error e indicar la Ficha_Ejercicio afectada.
9. THE Guia_Extensa SHALL usar la paleta rosa/negro con acentos rosa sobre fondo claro en el cuerpo del documento.
10. THE Guia_Extensa SHALL generar todas las ilustraciones como gráficos vectoriales dibujados por el Motor_Diagramas.
11. THE Guia_Extensa SHALL incluir un apéndice con la lista completa de enlaces de video en texto plano para copiarlos a mano.

### Requirement 10: Validación de la construcción

**User Story:** Como responsable del repositorio, quiero que la construcción falle si algo quedó mal, para no publicar una guía incompleta.

#### Acceptance Criteria

1. THE Orquestador_Build SHALL validar que cada Ficha_Ejercicio del Catalogo_Contenido tenga título, objetivo, pasos numerados, dosis, criterio de observación, rango de jugadoras y variante de espacio.
2. IF una Ficha_Ejercicio carece de alguno de los campos obligatorios, THEN THE Orquestador_Build SHALL terminar con código de error e indicar el identificador de la Ficha_Ejercicio y el campo faltante.
3. THE Orquestador_Build SHALL validar que las referencias del índice apunten a la página donde inicia cada capítulo.
4. THE Orquestador_Build SHALL validar que ningún texto de la Guia_Extensa en PDF se desborde del área imprimible de la página A4.
5. IF un bloque de texto se desborda del área imprimible, THEN THE Orquestador_Build SHALL terminar con código de error e indicar el número de página afectado.
6. THE Orquestador_Build SHALL reportar al finalizar el conteo de Ficha_Ejercicio, de Bloque_Semanal, de Diagrama_Postura y de códigos QR incluidos.
7. THE Orquestador_Build SHALL completar la construcción completa en 120 segundos o menos.

---

## Addendum A: Feature "Entrena como las grandes" — sitio JSON-driven, escalable a 200+ fichas

> **Nota de integración (no elimina nada):** Esta sección se SUMA a los Requisitos 1–10. No reemplaza ni borra ninguno. Donde un requisito nuevo choca con uno previo, se marca con **⚠ CONFLICTO** y queda pendiente de decisión del usuario (ver "Conflictos abiertos" al final de este addendum). Hasta que se resuelvan, los requisitos previos siguen vigentes.

### Glossary (adiciones)

- **Catalogo_JSON**: archivo único `contenido/ejercicios.json` que declara todas las Ficha_Ejercicio de forma serializable. Es la fuente de verdad de contenido para el generador.
- **Ficha_JSON**: objeto del Catalogo_JSON con los campos: `id`, `numero`, `titulo`, `subtitulo`, `categoria`, `equipo_referencia`, `nivel`, `contexto`, `pasos[]`, `que_mira_la_companera[]`, `dosis {cuando, duracion, jugadoras, material, meta}`, `cancha` (datos del diagrama), y `media[]` con objetos `{tipo, url, titulo}`.
- **Media_Item**: enlace de una Ficha_JSON con `tipo` en el conjunto cerrado `{youtube, tiktok, instagram_reel, facebook_reel, web, busqueda}`.
- **Target_Web**: salida `dist/index.html`, sitio estático de un solo archivo con índice navegable, buscador y filtros por categoría y nivel.
- **Target_PDF_Guia**: salida `dist/guia.pdf`, imprimible, una Ficha por hoja, con Diagrama_Cancha, dosis y un código QR por cada Media_Item.
- **Target_Laminas**: salida `dist/laminas.pdf`, láminas verticales formato celular para WhatsApp.
- **Tema_Oscuro**: paleta de la referencia visual del usuario: fondo `#150810`, texto `#f3e6ea`, acento magenta `#e5296b`, rosa secundario `#ff8ab0`, superficies `#25101b`, bordes `#3a222c`, ancho máximo 860 px centrado.

### Requirement 11: Contenido dirigido por un único Catalogo_JSON

**User Story:** Como responsable del contenido, quiero que todas las fichas vivan en un solo `ejercicios.json` y que el HTML se genere desde ahí, para escalar a 200+ fichas sin escribir HTML a mano.

#### Acceptance Criteria

1. THE Catalogo_JSON SHALL residir en `contenido/ejercicios.json` como archivo único serializable.
2. THE Catalogo_JSON SHALL declarar cada Ficha_JSON con los campos `id`, `numero`, `titulo`, `subtitulo`, `categoria`, `equipo_referencia`, `nivel`, `contexto`, `pasos`, `que_mira_la_companera`, `dosis` y `media`.
3. THE campo `dosis` de cada Ficha_JSON SHALL contener las claves `cuando`, `duracion`, `jugadoras`, `material` y `meta`.
4. THE campo `media` de cada Ficha_JSON SHALL ser una lista de Media_Item, cada uno con `tipo`, `url` y `titulo`.
5. THE campo `tipo` de cada Media_Item SHALL pertenecer al conjunto `{youtube, tiktok, instagram_reel, facebook_reel, web, busqueda}`.
6. THE generador SHALL producir todo el HTML de cada ficha a partir del Catalogo_JSON, sin HTML escrito a mano por ficha.
7. IF una Ficha_JSON carece de un campo obligatorio o `tipo` de Media_Item está fuera del conjunto permitido, THEN THE generador SHALL terminar con código de error e indicar el `id` de la ficha y el campo o valor inválido.
8. THE arquitectura de contenido SHALL admitir al menos 200 Ficha_JSON sin cambios estructurales.

### Requirement 12: Tres salidas desde el mismo Catalogo_JSON

**User Story:** Como responsable del equipo, quiero un sitio web, una guía imprimible y láminas para WhatsApp generadas del mismo origen, para no mantener contenidos duplicados.

#### Acceptance Criteria

1. THE generador SHALL producir Target_Web, Target_PDF_Guia y Target_Laminas en la misma ejecución y desde el mismo Catalogo_JSON.
2. THE Target_Web SHALL ser un único archivo `dist/index.html` sin CDN ni dependencias externas y funcional offline, acompañado únicamente de assets binarios locales referenciados con rutas relativas (por ejemplo `assets/img/tecnica/*.webp`), que **no** cuentan como dependencias externas porque no requieren ninguna petición de red. Ver Requisito 1 de la spec `imagenes-reales-hero-interactivo`.
3. THE Target_Web SHALL incluir un índice navegable, un buscador y filtros por categoría y por nivel.
4. THE Target_Web SHALL mostrar en cada ficha su Diagrama_Cancha, su bloque de dosis y sus Media_Item como enlaces que abren en pestaña nueva.
5. THE Target_PDF_Guia SHALL imprimir una Ficha por hoja con su Diagrama_Cancha, su dosis y un código QR por cada Media_Item, con el QR generado offline sin API externa.
6. THE Target_Laminas SHALL producir láminas verticales de formato adecuado para pantalla de teléfono.
7. THE Diagrama_Cancha SHALL generarse por código como SVG desde el campo `cancha` de la Ficha_JSON y reutilizarse sin cambios en Target_Web y en Target_PDF_Guia.
8. THE generador SHALL NOT usar imágenes de mapa de bits sueltas para los diagramas de cancha.

### Requirement 13: Descargas y migración del contenido existente

**User Story:** Como jugadora, quiero botones para bajar la guía, las láminas y el JSON crudo, y no perder las fichas que ya existían, para tener todo a mano y sin retrocesos.

#### Acceptance Criteria

1. THE Target_Web SHALL incluir botones de descarga para `dist/guia.pdf`, para `dist/laminas.pdf` y para `contenido/ejercicios.json` crudo.
2. THE Target_Web SHALL presentar dos botones de descarga principales en el encabezado: uno de estilo sólido magenta y uno de estilo contorno (outline).
3. THE migración SHALL cargar las 15 Ficha_Ejercicio actuales del `index.html` vigente dentro del Catalogo_JSON sin perder texto.
4. WHERE una ficha migrada tenía enlaces de video, THE migración SHALL conservarlos como Media_Item con su `tipo` correspondiente.
5. THE generador SHALL funcionar completo sin acceso a internet y sin JavaScript de terceros.

### Requirement 14: Estilo visual de la referencia (Tema_Oscuro)

**User Story:** Como usuario, quiero que el sitio se vea como mi index.html actual, para conservar la identidad visual que ya diseñé.

#### Acceptance Criteria

1. THE Target_Web SHALL usar la paleta Tema_Oscuro: fondo `#150810`, texto `#f3e6ea`, acento `#e5296b`, rosa secundario `#ff8ab0`, superficies `#25101b`, bordes `#3a222c`.
2. THE Target_Web SHALL limitar el ancho del contenido a un máximo de 860 px centrado y ser mobile-first.
3. THE encabezado del Target_Web SHALL incluir un kicker en mayúsculas con espaciado de letras, un H1 fluido con una palabra en color acento, y un lede.
4. THE índice del Target_Web SHALL usar una cuadrícula `auto-fill` de columnas de 230 px con el número de ficha en color acento.
5. THE ficha del Target_Web SHALL renderizarse como un `<article>` separado por línea con: badge de número más categoría más equipo de referencia, H2, subtítulo en itálica rosa, párrafo de contexto, sección "Paso a paso" numerada, bloque "Qué mira la compañera" en verde oliva (fondo `#1e2a10`, borde izquierdo `#a8c94a`), cuadrícula de dosis (Cuándo, Duración, Jugadoras, Material, Meta) y lista de enlaces con badge de tipo (VIDEO, WEB, BUSCAR).
6. THE Target_Web SHALL usar solo CSS propio sin frameworks de terceros.

### Conflictos resueltos (decisiones del usuario; nada se borró de los Requisitos 1–10)

- **✅ C1 — Formato del catálogo.** El Catalogo_JSON (`ejercicios.json`) es la **fuente única para las Ficha_Ejercicio**. Los módulos `contenido/capNN_*.py` se conservan para el **contenido narrativo de capítulos** (prevención, mental, liderazgo, apéndices, textos introductorios). Ninguna ficha vive en los dos lados. Las fichas que hoy estén declaradas en módulos Python se migran al JSON (ver Req 15).
- **✅ C2 — JavaScript en el sitio.** Se permite **JavaScript propio embebido, cero terceros**, con degradación sin-JS: sin JS se ven todas las fichas sin filtrar; con JS se activan buscador y filtros. Esto **relaja el Req 2.4 solo para Target_Web**; el PDF y el resto de la Guia_Extensa siguen sin JavaScript.
- **✅ C3 — Un archivo vs. varios.** Target_Web es **un solo `index.html`** que abre con doble clic desde una USB, sin servidor. El sitio multi-archivo por capítulo (diseño previo Sección 7) **se conserva como salida aparte** para la Guia_Extensa.
- **✅ C4 — Paleta.** **Target_Web en Tema_Oscuro; PDF en fondo claro.** El Req 9.9 (acentos rosa sobre fondo claro) **sigue vigente solo para el PDF**.
- **✅ C5 — Esquema de Ficha.** El **JSON es el formato de entrada**; la dataclass `FichaEjercicio` sigue siendo el **modelo interno**. Un adaptador `ficha_json_a_ficha(...)` mapea Ficha_JSON → `FichaEjercicio`.
- **✅ C6 — Nombres de artefactos.** Los targets de esta feature son **`dist/guia.pdf`** y **`dist/laminas.pdf`**. El artefacto de 200–300 páginas conserva su nombre **`Guia_Extensa_Sub17.pdf`**.
- **✅ C7 — Inconsistencia Node/Bun → Python.** La Introduction y el Req 2.8 se actualizaron de "Node/Bun / archivos `.mjs`" a **Python 3.11+ solo stdlib**, coherente con la Nota de portabilidad de `design.md`. No se borró nada más.

### Requirement 15: Fuente única de fichas y migración desde módulos Python

**User Story:** Como responsable del contenido, quiero que ninguna ficha esté duplicada entre el JSON y los módulos Python, para tener una sola fuente de verdad de ejercicios.

#### Acceptance Criteria

1. THE Catalogo_JSON SHALL ser la única fuente de las Ficha_Ejercicio de la Guia_Extensa.
2. THE módulos `contenido/capNN_*.py` SHALL contener únicamente contenido narrativo de capítulos y SHALL NOT declarar Ficha_Ejercicio.
3. WHERE una Ficha_Ejercicio esté hoy declarada en un módulo `contenido/capNN_*.py`, THE proceso de migración SHALL trasladarla al Catalogo_JSON conservando todos sus campos y texto.
4. THE Orquestador_Build SHALL verificar que ningún módulo `contenido/capNN_*.py` declare Ficha_Ejercicio y terminar con código de error nombrando el módulo infractor si encuentra alguna.
5. THE adaptador `ficha_json_a_ficha` SHALL convertir cada Ficha_JSON en una instancia válida de la dataclass `FichaEjercicio` usada por el paginador y el Motor_PDF.

### Requirement 16: Imágenes fotorrealistas locales de jugadoras

**User Story:** Como jugadora, quiero ver imágenes reales de posturas técnicas en lugar de dibujos esquemáticos, para entender mejor cómo colocar el cuerpo, el pie de apoyo y la superficie de contacto al pegarle al balón.

#### Acceptance Criteria

1. THE Target_Web SHALL incluir imágenes fotorrealistas de jugadoras en formato WebP almacenadas localmente en el directorio `assets/img/` dentro del proyecto.
2. THE imágenes fotorrealistas SHALL ser de jugadoras juveniles genéricas generadas por IA, sin nombres impresos y sin personas reales identificables.
3. THE Motor_HTML SHALL integrar las imágenes fotorrealistas como fondo del hero del sitio HTML con efecto parallax al hacer scroll.
4. THE Target_Web SHALL permitir interactividad de zoom (hacer más grandes o más pequeñas) y mover las imágenes fotorrealistas.
5. THE imágenes fotorrealistas SHALL mostrar posturas técnicas reales con énfasis en la posición del pie de apoyo, la superficie de contacto al pegarle al balón y la inclinación del cuerpo.
6. THE imágenes fotorrealistas SHALL usar fondo azul claro coherente con la paleta visual de la Guia_Extensa.
7. THE imágenes fotorrealistas SHALL presentar estilo femenil en las jugadoras genéricas representadas.
8. THE Orquestador_Build SHALL validar que todas las imágenes fotorrealistas referenciadas en el HTML existen como archivos locales en `assets/img/` y terminar con código de error indicando la imagen faltante si alguna no existe.
9. THE Orquestador_Build SHALL validar que todas las imágenes fotorrealistas sean archivos locales con extensión `.webp` y terminar con código de error si encuentra referencias a URLs externas o a CDNs.
10. THE generación completa SHALL mantener el requisito de funcionamiento 100% offline sin descargar imágenes de internet ni en tiempo de build ni en runtime.
11. THE lectura correcta de "cero recursos externos" SHALL ser: lo prohibido son las peticiones de red (`http://`, `https://`, `//`, CDN, fuentes remotas, `@import` de URL, `<link>` remoto y `url(` en CSS); los archivos binarios locales del repositorio referenciados con rutas relativas están permitidos.
12. THE detalle de esta feature (catálogo de las cuatro fotos de técnica, hero con fondo interactivo, comportamiento del build cuando faltan los `.webp` y guardarraíl ampliado) SHALL vivir en la spec `imagenes-reales-hero-interactivo`, que refina este requisito sin contradecirlo.
