# Requirements Document

## Introduction

Esta feature añade tres cosas al Target_Web de la guía (`dist/index.html`, generado por `build_site.py`):

1. **Ocho diagramas de postura (Tipo A) generados como SVG line art desde Python.** Un vocabulario del cuerpo (`anatomia-base`) más siete gestos técnicos, cada uno con su explicación en pasos numerados (pie de apoyo, contacto, torso, brazos, mirada) y con texto alternativo descriptivo real. El render es **híbrido**: si existe el archivo de imagen en `assets/img/tecnica/` se usa ese archivo; si no existe, se usa el SVG que genera Python. Nunca queda un hueco vacío.
2. **Hero con fondo interactivo tipo "mundo de fútbol".** Un espacio azul claro y luminoso con entre 8 y 14 elementos de fútbol femenil flotando (balones que giran, siluetas de jugadoras, porterías, conos, líneas de campo, silbato, copa, tacos), perspectiva real de tres capas con parallax al desplazar, escala, desvanecimiento reversible, flotación en bucle e interacción táctil.
3. **Los cimientos compartidos de la guía**: la Paleta_Guia cerrada con Modo_Oscuro, la restricción de celular primero, la whitelist de assets locales, el tono del texto en segunda persona y femenino, el Bloque_Creditos y el orden de las secciones. La spec hermana `diagramas-ejercicio-pizarra` (Spec_Pizarra) reutiliza estos cimientos y aporta el contenido de las secciones reservadas.
4. **Rotación de 360 grados real de las figuras (Requisitos 21 a 30).** Un `rotateY` sobre un SVG plano no es una vuelta: al pasar los 90 grados se ve el mismo dibujo espejeado. Como el esqueleto es paramétrico, la vuelta se resuelve rotando el Esqueleto_3D y proyectándolo desde diez puntos de vista: ocho azimuts cada 45 grados más una picada de +60 grados y una contrapicada de −60 grados. Al girar se ve la espalda, la coronilla y la planta del pie de apoyo. El giro es continuo en el fondo del hero y se maneja con el dedo en el Visor_Ampliado, que la usuaria declara la interacción más importante de la guía. Sin WebGL, sin modelo 3D externo y sin salir de la librería estándar de Python.

La feature **refina el Requisito 16 de la spec `guia-entrenamiento-femenil-extensa`** (Imágenes fotorrealistas locales de jugadoras) y **aclara la regla de "cero recursos externos"**: lo prohibido son las peticiones de red (CDN, fuentes remotas, `http://`, `https://`, `//`), no los archivos binarios locales del propio repositorio ni el texto de los créditos.

**El destino es un celular.** Cuando un criterio de esta spec choque con la restricción de celular del Requisito 15, manda el Requisito 15.

Restricciones vigentes del proyecto que esta feature **conserva intactas**: Python 3.11+ solo con librería estándar; invariantes con `raise ErrorBuild(...)` y nunca `assert`; un único `<script>` global en todo el sitio; cero JavaScript en las páginas de capítulo; prohibida la subcadena `//` dentro del `<script>`; cero peticiones de red en build y en runtime; la suite completa (`python _run_tests.py`) en verde y el build estricto terminando como `[PUBLICABLE]`.

## Glossary

- **Target_Web**: el único archivo `dist/index.html` autocontenido que emite `build_site.escribir_sitio(...)` y que abre por doble clic, sin servidor y sin internet.
- **Motor_Sitio**: componente `src/guia/build_site.py`, que compone el HTML del Target_Web.
- **Hoja_Estilo**: la función `build_html.estilo_css()`, única fuente del CSS del sitio y de las páginas de capítulo.
- **Script_Unico**: el único elemento `<script>` del Target_Web, propio y embebido, sin atributo `src`.
- **Orquestador_Build**: componente `src/guia/build.py`, que ejecuta el pipeline y publica los artefactos en `dist/`.
- **Diagrama_Postura**: un diagrama Tipo A de line art que muestra la postura de un gesto técnico o el vocabulario del cuerpo, con su explicación en pasos numerados. En revisiones anteriores de esta spec este término se llamaba **Foto_Tecnica**.
- **Catalogo_Diagramas**: estructura de datos declarativa (módulo nuevo `src/guia/diagramas_postura.py`) que declara cada Diagrama_Postura con su archivo, su texto alternativo, sus dimensiones, sus pasos, sus etiquetas, sus fases y su marca Requiere_Archivo. En revisiones anteriores se llamaba **Catalogo_Fotos**.
- **Validador_Catalogo**: la función `validar_catalogo()` del Catalogo_Diagramas, que comprueba los invariantes del catálogo antes de emitir HTML.
- **Generador_SVG**: la función de Python que emite el SVG en línea de un Diagrama_Postura cuando no existe su Archivo_Diagrama.
- **Archivo_Diagrama**: el Asset_Local de un Diagrama_Postura, ubicado en `assets/img/tecnica/` y nombrado con el identificador del diagrama.
- **Requiere_Archivo**: marca booleana de una entrada del Catalogo_Diagramas que declara si su Archivo_Diagrama es obligatorio en Modo_Estricto.
- **Etiqueta_Anatomica**: rótulo de una parte del cuerpo dentro de un Diagrama_Postura, emitido como elemento `<text>` y unido a la parte señalada por una línea guía.
- **Fase_Numerada**: uno de los momentos numerados de un gesto con secuencia, dibujado en el SVG y listado en el texto con el mismo número.
- **Fundamento**: uno de los cuatro grupos temáticos de la guía: golpeo, pase, control y conducción, y cabeceo.
- **Advertencia_Cabeceo**: el texto de seguridad obligatorio de la entrada `cabeceo-frente`.
- **Mundo_Hero**: componente nuevo `src/guia/mundo_hero.py`, que declara los elementos del fondo del hero, calcula los factores de movimiento y emite su SVG, su CSS y sus constantes de JavaScript.
- **Elemento_Fondo**: una figura decorativa del fondo del hero (balón, silueta de jugadora, portería, cono, línea de campo, silbato, copa, taco, arco de cancha).
- **Capa_Lejana**, **Capa_Media**, **Capa_Cercana**: los tres grupos de parallax del Mundo_Hero, con factores de desplazamiento de 15 %, 40 % y 70 % del desplazamiento vertical.
- **Progreso_Scroll**: valor en el intervalo cerrado [0, 1] que resulta de dividir el desplazamiento vertical de la página entre la altura de la ventana, acotado a ese intervalo.
- **Gesto_Activacion**: el toque de la usuaria sobre el control rotulado "Activar movimiento", único punto desde el que se solicita el permiso de `DeviceOrientationEvent`.
- **Recurso_Externo**: cualquier referencia **cargable** que requiera una petición de red: `http://`, `https://`, `//`, CDN, fuente remota, `@import` de una URL o `<link>` a una hoja de estilo remota.
- **Asset_Local**: archivo binario que vive dentro del repositorio y se referencia con una ruta relativa (por ejemplo `assets/img/tecnica/tiro-empeine.webp`).
- **Guardarrail_Recursos**: conjunto de pruebas de `test/` que verifica que el HTML, el CSS y el Script_Unico no contienen ningún Recurso_Externo.
- **Guardarrail_Movil**: conjunto de pruebas de `test/` que verifica sobre el HTML y el CSS emitidos las reglas del Requisito 15.
- **Guardarrail_Lexico**: prueba de `test/` que verifica el tono del texto del Requisito 17 sobre los textos del Catalogo_Diagramas y de las fichas.
- **Paleta_Guia**: los siete tokens de color cerrados del Requisito 16, declarados en `src/guia/paleta.py`.
- **Contraste**: la función `contraste(color_a, color_b)` de la Paleta_Guia, que devuelve la relación de contraste WCAG 2.x.
- **Modo_Oscuro**: la condición CSS `prefers-color-scheme: dark`.
- **Ancho_Base**: la ventana de referencia de diseño, de 360 píxeles de ancho por 640 píxeles de alto.
- **Zona_Tactil**: región interactiva del Target_Web que la usuaria activa con un toque.
- **Bloque_Creditos**: la sección final del Target_Web con los créditos y las licencias de las imágenes.
- **Spec_Pizarra**: la spec hermana `diagramas-ejercicio-pizarra`, que aporta los diagramas de pizarra táctica vistos desde arriba, la leyenda de símbolos, las fichas de ejercicio y la rutina semanal.
- **Seccion_Reservada**: sección del Target_Web que esta spec emite con su ancla y su encabezado, y cuyo contenido aporta la Spec_Pizarra.
- **Modo_Estricto** y **Modo_Muestra**: los dos modos de `build.construir(...)`; solo el Modo_Estricto puede terminar como `[PUBLICABLE]`.
- **Movimiento_Reducido**: la condición CSS `prefers-reduced-motion: reduce`.
- **Esqueleto_3D**: las diecisiete articulaciones del esqueleto con tres coordenadas cada una (horizontal, vertical y profundidad), unidas por los dieciséis huesos de longitud fija. Es el espacio canónico donde se mide la longitud de hueso.
- **Proyector_Vistas**: componente nuevo `src/guia/vistas_figura.py`, que rota el Esqueleto_3D alrededor del eje vertical del cuerpo y del eje transversal, lo proyecta a dos coordenadas y decide el orden de dibujo por profundidad.
- **Escorzo**: el acortamiento de la longitud proyectada de un hueso que resulta de la rotación; es una consecuencia de la proyección, nunca un cambio de la longitud declarada del hueso.
- **Vista_Azimut**: una de las ocho vistas de una figura obtenidas rotando el Esqueleto_3D alrededor del eje vertical del cuerpo, con elevación cero.
- **Vista_Elevacion**: una de las dos vistas de una figura obtenidas con azimut cero y elevación de +60 grados (picada) o de −60 grados (contrapicada).
- **Vista_Figura**: una Vista_Azimut o una Vista_Elevacion ya emitida como elemento `<svg>` en línea.
- **Clave_Vista**: el identificador textual de una Vista_Figura, uno de `az-000`, `az-045`, `az-090`, `az-135`, `az-180`, `az-225`, `az-270`, `az-315`, `el-p60` y `el-m60`.
- **Azimuts_Declarados**: la tupla de grados `(0, 45, 90, 135, 180, 225, 270, 315)`.
- **Elevaciones_Declaradas**: la tupla de grados `(+60, −60)`.
- **Subconjunto_Azimuts_Movil**: la tupla de seis grados `(0, 45, 90, 180, 270, 315)` que el Conmutador_Vista usa en anchos de ventana menores que 768 píxeles.
- **Figura_Girable**: elemento del Target_Web que declara sus diez Vista_Figura: cada Elemento_Fondo de tipo silueta de jugadora y cada Diagrama_Postura marcado Girable.
- **Girable**: marca booleana de una entrada del Catalogo_Diagramas que declara si ese Diagrama_Postura emite sus diez Vista_Figura y admite Arrastre_Rotacion.
- **Vista_Activa**: la única Vista_Figura de una Figura_Girable con opacidad 1 y `visibility:visible` en un instante dado.
- **Conmutador_Vista**: la parte del Script_Unico que, dentro del bucle único, activa la Vista_Figura cuya Clave_Vista está más cerca del ángulo actual y desactiva las otras nueve.
- **Rotacion_Residual**: la rotación `rotateY` que el Conmutador_Vista aplica a la Vista_Activa para cubrir la diferencia entre el ángulo actual y el azimut declarado de esa vista.
- **Miembro_Trasero** y **Miembro_Delantero**: el brazo o la pierna cuya profundidad rotada queda detrás del torso, y el que queda delante.
- **Tapa_Torso**: la superficie opaca del torso que oculta los Miembro_Trasero. No es el relleno de la silueta.
- **Sombra_Contacto**: la elipse de contacto con el suelo de una Figura_Girable, cuya escala horizontal depende del azimut.
- **Balon_Esfera**: el Elemento_Fondo de tipo balón construido con Gajo_Balon en caras distintas y girado sobre un Eje_Giro_Inclinado.
- **Gajo_Balon**: una de las caras del Balon_Esfera, con su propia rotación declarada.
- **Eje_Giro_Inclinado**: el eje de `rotate3d(` de un Balon_Esfera, con sus tres componentes distintas de cero y una inclinación declarada respecto de la vertical.
- **Giro_Impulso**: la vuelta acelerada que un Balon_Esfera o una Figura_Girable completa después de un toque, antes de retomar su duración declarada.
- **Modo_Inerte**: el estado del Mundo_Hero cuando su opacidad llega a 0, con `visibility:hidden`, animaciones pausadas y `will-change` liberado.
- **Visor_Ampliado**: la sección `#<id>-ampliada` que despliega una figura o un Diagrama_Postura a pantalla completa con el selector `:target`.
- **Arrastre_Rotacion**: el gesto de arrastre dentro del Visor_Ampliado que cambia el azimut con el desplazamiento horizontal y la elevación con el desplazamiento vertical.
- **Validador_Rutas**: la función del Guardarrail_Recursos que decide si una ruta de Asset_Local es aceptable.
- **Extensiones_Permitidas**: la tupla de cuatro extensiones `(".webp", ".svg", ".png", ".avif")`.

## Requirements

### Requirement 1: Assets binarios locales permitidos sin debilitar la prohibición de red

**User Story:** Como responsable del proyecto, quiero que la regla de "cero recursos externos" quede escrita con precisión, para poder usar imágenes locales sin abrir la puerta a peticiones de red.

#### Acceptance Criteria

1. THE Target_Web SHALL referenciar cada Asset_Local con una ruta relativa que empieza por `assets/`.
2. THE Target_Web SHALL excluir toda referencia cargable a un Recurso_Externo en el HTML, en la Hoja_Estilo y en el Script_Unico.
3. THE Guardarrail_Recursos SHALL aceptar los elementos `<img>` cuyo atributo `src` es una ruta que el Validador_Rutas del Requisito 30 acepta.
4. IF un elemento `<img>` del Target_Web tiene un `src` que empieza por `http://`, por `https://`, por `//` o por `/`, THEN THE Guardarrail_Recursos SHALL fallar nombrando ese `src`.
5. THE Guardarrail_Recursos SHALL conservar la prohibición de `<link>` a hoja de estilo, de `@import`, de `src="http` y de la subcadena `//` dentro del Script_Unico.
6. THE Hoja_Estilo SHALL excluir la función CSS `url(`, de modo que ninguna imagen se cargue desde el CSS.
7. THE Orquestador_Build SHALL completar la generación de los artefactos sin abrir ninguna conexión de red.
8. THE Guardarrail_Recursos SHALL aceptar la subcadena `http` cuando aparece como texto visible dentro del Bloque_Creditos, y SHALL rechazarla en todo atributo `src`, en todo `href` de hoja de estilo y en el Script_Unico.
9. THE Guardarrail_Recursos SHALL aceptar los elementos `<svg>` en línea del Motor_Sitio, del Generador_SVG, del Proyector_Vistas y del Mundo_Hero, por no provocar ninguna petición de red.
10. THE Guardarrail_Recursos SHALL aplicar el Validador_Rutas a toda referencia de recurso del Target_Web, y no solo a los elementos `<img>`.
11. THE conjunto de extensiones que el Guardarrail_Recursos acepta SHALL ser exactamente Extensiones_Permitidas.

### Requirement 2: Catálogo de los ocho diagramas de postura

**User Story:** Como jugadora, quiero ver la postura de cada fundamento y aprender primero cómo se llaman las partes del cuerpo, para copiar la posición sin adivinar el vocabulario.

#### Acceptance Criteria

1. THE Catalogo_Diagramas SHALL declarar exactamente ocho Diagrama_Postura, con los identificadores `anatomia-base`, `tiro-empeine`, `pase-interior`, `control-balon`, `conduccion`, `potencia-carrera`, `cabeceo-frente` y `pase-largo-empeine`, en ese orden.
2. THE Catalogo_Diagramas SHALL declarar `anatomia-base` como su primera entrada.
3. THE Catalogo_Diagramas SHALL asignar a cada Diagrama_Postura un Archivo_Diagrama cuyo nombre es su identificador seguido de una de las extensiones que acepta el Guardarrail_Recursos, ubicado en `assets/img/tecnica/`.
4. THE Catalogo_Diagramas SHALL asignar a cada Diagrama_Postura un ancho declarado mayor que 0 y menor o igual que 1200 píxeles, y un alto declarado mayor que 0.
5. WHERE un Diagrama_Postura describe un gesto técnico, THE Catalogo_Diagramas SHALL asignarle un texto alternativo de 60 caracteres o más que nombra la superficie de contacto y al menos dos elementos de postura entre pie de apoyo, torso, brazos y mirada.
6. THE Catalogo_Diagramas SHALL asignar a `anatomia-base` un texto alternativo de 60 caracteres o más que nombra al menos seis de sus Etiqueta_Anatomica.
7. WHERE un Diagrama_Postura describe un gesto técnico, THE Catalogo_Diagramas SHALL asignarle exactamente cinco pasos numerados en este orden fijo: pie de apoyo, contacto, torso, brazos y mirada, cada uno de 20 caracteres o más.
8. THE Catalogo_Diagramas SHALL asignar a cada Diagrama_Postura distinto de `anatomia-base` exactamente un Fundamento, con `tiro-empeine` y `potencia-carrera` en golpeo, `pase-interior` y `pase-largo-empeine` en pase, `control-balon` y `conduccion` en control y conducción, y `cabeceo-frente` en cabeceo.
9. WHERE un Diagrama_Postura declara una postura equivalente del catálogo de `figuras.py`, THE Catalogo_Diagramas SHALL usar un identificador que existe en ese catálogo, con `tiro-potencia-empeine` para `tiro-empeine` y para `potencia-carrera`, `pase-corto-interior` para `pase-interior`, `control-orientado` para `control-balon`, `conduccion` para `conduccion` y `pase-largo-empeine` para `pase-largo-empeine`.
10. THE Catalogo_Diagramas SHALL declarar sin postura equivalente las entradas `anatomia-base` y `cabeceo-frente`.
11. THE textos del Catalogo_Diagramas SHALL excluir nombres propios de personas y nombres de clubes.
12. THE Catalogo_Diagramas SHALL declarar `pase-largo-empeine` como un pase elevado a distancia en su título y en su texto alternativo.

### Requirement 3: Presentación de cada fundamento con diagrama y pasos

**User Story:** Como jugadora, quiero leer, debajo del diagrama, qué estoy viendo paso por paso, para saber en qué fijarme.

#### Acceptance Criteria

1. THE Motor_Sitio SHALL emitir en el Target_Web una sección de técnica con el ancla `tecnica-en-imagenes`.
2. THE Motor_Sitio SHALL emitir el bloque de `anatomia-base` en su propia sección con el ancla `anatomia-base`, antes de la sección de técnica.
3. THE sección de técnica SHALL contener cuatro bloques de Fundamento, y cada bloque SHALL contener los Diagrama_Postura que el Catalogo_Diagramas le asigna, en el orden del catálogo.
4. THE bloque de cada Diagrama_Postura SHALL contener un elemento `<figure>` con el contenido gráfico del diagrama y con el texto alternativo del Catalogo_Diagramas.
5. THE bloque de cada Diagrama_Postura SHALL contener, después del elemento `<figure>`, una lista ordenada `<ol>` con un elemento `<li>` por cada paso declarado en el Catalogo_Diagramas.
6. THE bloque de cada Diagrama_Postura SHALL contener el título del diagrama como encabezado de nivel 3.
7. THE navegación en página del Target_Web SHALL incluir un enlace al ancla `anatomia-base` y un enlace al ancla `tecnica-en-imagenes`.
8. WHEN el Script_Unico se retira del documento, THE sección de técnica y la sección `anatomia-base` SHALL conservar los ocho diagramas, sus listas de pasos y sus enlaces de navegación.
9. IF el Catalogo_Diagramas declara un Fundamento distinto de los cuatro del criterio 2.8, THEN THE Motor_Sitio SHALL emitir únicamente los cuatro bloques declarados y SHALL registrar el Fundamento omitido en el reporte del Orquestador_Build.

### Requirement 4: Rendimiento y estabilidad visual de los diagramas

**User Story:** Como usuaria de un teléfono de gama media, quiero que los diagramas no muevan el texto al cargar y que no gasten datos de más, para leer la guía sin saltos.

#### Acceptance Criteria

1. WHERE el primer Diagrama_Postura del documento se rinde con un elemento `<img>`, THE Motor_Sitio SHALL asignarle el atributo `loading="eager"`.
2. THE elementos `<img>` de Diagrama_Postura distintos del primero SHALL llevar el atributo `loading="lazy"`.
3. THE contenido gráfico de cada Diagrama_Postura SHALL llevar los atributos `width` y `height` con los valores que el Catalogo_Diagramas declara para su modo de render, tanto en el elemento `<img>` como en el elemento `<svg>`.
4. THE elementos `<img>` de Diagrama_Postura SHALL llevar el atributo `decoding="async"`.
5. THE Hoja_Estilo SHALL declarar para el contenedor de cada Diagrama_Postura una propiedad `aspect-ratio` fija y para su contenido gráfico `object-fit:cover`.
6. THE Hoja_Estilo SHALL declarar para el contenedor de cada Diagrama_Postura un alto mínimo de 320 píxeles en anchos de ventana menores que 768 píxeles.
7. THE Hoja_Estilo SHALL declarar ancho máximo del 100 % para el contenido gráfico de cada Diagrama_Postura, sin ninguna propiedad `width` en píxeles superior a 360.
8. WHERE el Catalogo_Diagramas declara dimensiones distintas para el Archivo_Diagrama y para el SVG generado de un mismo Diagrama_Postura, THE Motor_Sitio SHALL emitir las dimensiones del modo de render efectivo.

### Requirement 5: Render híbrido, emisión de los assets y comportamiento cuando faltan

**User Story:** Como responsable del build, quiero que la guía se vea completa aunque no haya colocado ningún archivo de imagen, para publicar sin depender de assets externos.

#### Acceptance Criteria

1. THE Catalogo_Diagramas SHALL marcar cada Diagrama_Postura con el campo Requiere_Archivo.
2. THE Catalogo_Diagramas SHALL declarar Requiere_Archivo con el valor falso en las ocho entradas actuales.
3. WHEN existe el Archivo_Diagrama de un Diagrama_Postura en `assets/img/tecnica/`, THE Motor_Sitio SHALL emitir su `<figure>` con un elemento `<img>` que apunta a la ruta relativa de ese archivo.
4. IF falta el Archivo_Diagrama de un Diagrama_Postura, THEN THE Motor_Sitio SHALL emitir su `<figure>` con el SVG en línea que produce el Generador_SVG.
5. THE Motor_Sitio SHALL emitir un `<figure>` con contenido gráfico para cada uno de los ocho Diagrama_Postura, en Modo_Estricto y en Modo_Muestra.
6. THE Orquestador_Build SHALL copiar cada Archivo_Diagrama presente desde `assets/img/tecnica/` a `dist/assets/img/tecnica/` conservando el nombre del archivo.
7. THE Orquestador_Build SHALL publicar los archivos copiados de forma atómica desde `dist/.tmp/`.
8. WHILE el build corre en Modo_Estricto, IF falta el Archivo_Diagrama de un Diagrama_Postura marcado Requiere_Archivo, THEN THE Orquestador_Build SHALL lanzar `ErrorBuild` con el código `E_ASSET_FALTANTE` y con la ruta relativa del archivo ausente en el mensaje.
9. WHERE un Diagrama_Postura declara Requiere_Archivo con el valor falso, THE Orquestador_Build SHALL completar el build en Modo_Estricto aunque su Archivo_Diagrama falte.
10. WHILE el build corre en Modo_Muestra, IF falta un Archivo_Diagrama, THEN THE Orquestador_Build SHALL terminar la generación y registrar la ruta relativa del archivo ausente en la lista `assets_faltantes` del reporte.
11. THE reporte del Orquestador_Build SHALL mostrar el número de assets copiados, el número de assets ausentes y el número de Diagrama_Postura rendidos desde el Generador_SVG.
12. WHEN el Orquestador_Build termina de copiar un Archivo_Diagrama a `dist/.tmp/`, THE Orquestador_Build SHALL comprobar sobre la copia la firma que corresponde a su extensión antes de publicarla: `RIFF` en los bytes 0 a 3 con `WEBP` en los bytes 8 a 11 para `.webp`, los bytes `89 50 4E 47` al inicio para `.png`, `ftyp` en los bytes 4 a 7 para `.avif` y la subcadena `<svg` dentro de los primeros 512 bytes para `.svg`.
13. IF la firma de una copia no coincide con su extensión, THEN THE Orquestador_Build SHALL lanzar `ErrorBuild` con el código `E_ASSET_INVALIDO` nombrando el archivo y SHALL dejar sin publicar esa copia.
14. THE comprobación de existencia y de firma SHALL aplicarse únicamente a los Archivo_Diagrama declarados en el Catalogo_Diagramas.

### Requirement 6: Fondo base del hero azul claro con texto legible y perspectiva real

**User Story:** Como visitante, quiero que el hero se sienta luminoso, abierto y con profundidad, para tener la sensación de entrar a un mundo de fútbol y seguir leyendo el texto sin esfuerzo.

#### Acceptance Criteria

1. THE Hoja_Estilo SHALL declarar para el hero un degradado vertical desde `--azul-cielo` en la parte superior hasta `--azul-medio` en la parte inferior.
2. THE Hoja_Estilo SHALL declarar sobre ese degradado un halo blanco difuso centrado con opacidad entre 0.30 y 0.40, en el selector `.hero-velo` y conservando su declaración `linear-gradient(`.
3. THE Hoja_Estilo SHALL declarar el color `--azul-profundo` para el kicker, el título de nivel 1, el lede y la línea de ayuda del hero.
4. THE Contraste entre `--azul-profundo` y cada uno de `--azul-cielo`, `--azul-medio` y `--blanco-suave` SHALL ser 4.5 o más.
5. THE Hoja_Estilo SHALL excluir el color blanco (`#fff`, `#ffffff` y `#FFF`) como color de texto dentro del hero.
6. THE Paleta_Guia SHALL declarar `WEB_HERO_CIELO` con el valor `#DCEEFF` y `WEB_HERO_TINTA` con el valor `#0B2C4D`, y SHALL conservar sin cambios los tokens `WEB_FONDO`, `WEB_FONDO_PROFUNDO` y `WEB_AZUL_CLARO`.
7. THE Motor_Sitio SHALL conservar en el hero las capas `hero`, `hero-visor`, `hero-lienzo`, `hero-reserva`, `hero-velo`, `hero-ui` y `hero-borde` que ya existen.
8. THE Hoja_Estilo SHALL declarar para el contenedor del Mundo_Hero las propiedades `perspective:1000px` y `transform-style:preserve-3d`.
9. THE Motor_Sitio SHALL conservar en el hero los 13 elementos congelados del arte actual.

### Requirement 7: Elementos de fútbol flotando por todo el hero

**User Story:** Como visitante, quiero ver objetos de fútbol femenil repartidos por el fondo del hero, para que la portada se sienta viva y no un cuadro estático.

#### Acceptance Criteria

1. THE Mundo_Hero SHALL declarar entre 8 y 14 Elemento_Fondo para anchos de ventana de 768 píxeles o más.
2. THE Mundo_Hero SHALL declarar entre 3 y 5 Elemento_Fondo de tipo balón.
3. THE Mundo_Hero SHALL declarar entre 2 y 3 Elemento_Fondo de tipo silueta de jugadora, cada uno con opacidad entre 0.25 y 0.45.
4. THE Mundo_Hero SHALL declarar al menos un Elemento_Fondo de cada uno de los tipos portería, cono, línea de campo, silbato, copa y taco.
5. THE Mundo_Hero SHALL declarar al menos un Elemento_Fondo con centro en cada uno de los cuatro cuadrantes del hero, medido sobre sus coordenadas porcentuales.
6. THE Mundo_Hero SHALL asignar a cada Elemento_Fondo de tipo balón un giro continuo de 360 grados alrededor de su Eje_Giro_Inclinado, con una duración entre 14 y 26 segundos, y duraciones distintas entre balones.
7. THE Mundo_Hero SHALL asignar sentido de giro horario a al menos un Elemento_Fondo de tipo balón y sentido antihorario a al menos otro.
8. THE Mundo_Hero SHALL emitir cada Elemento_Fondo como SVG en línea, sin ninguna referencia a un archivo de imagen.

### Requirement 8: Parallax de tres capas, escala y desvanecimiento reversible

**User Story:** Como visitante, quiero que al bajar el scroll el fondo se mueva a distintas velocidades y se desvanezca, para sentir profundidad y dejar la lectura limpia.

#### Acceptance Criteria

1. THE Mundo_Hero SHALL asignar cada Elemento_Fondo a exactamente una de las tres capas Capa_Lejana, Capa_Media o Capa_Cercana.
2. THE factor de desplazamiento vertical SHALL ser 0.15 para la Capa_Lejana, 0.40 para la Capa_Media y 0.70 para la Capa_Cercana.
3. WHEN el Progreso_Scroll vale `p`, THE escala de la Capa_Cercana SHALL ser `1 + 0.25 * p` y la escala de la Capa_Lejana SHALL ser `1 - 0.15 * p`.
4. WHEN el Progreso_Scroll vale `p`, THE opacidad de todo Elemento_Fondo SHALL ser `1 - p`.
5. WHEN el Progreso_Scroll vale 1 o más, THE opacidad de todo Elemento_Fondo SHALL ser 0.
6. WHEN el Progreso_Scroll decrece, THE opacidad y la escala de cada Elemento_Fondo SHALL tomar el mismo valor que tenían para ese mismo Progreso_Scroll al crecer.
7. THE desplazamiento vertical de la Capa_Cercana SHALL ser mayor que el de la Capa_Media, y el de la Capa_Media mayor que el de la Capa_Lejana, para todo Progreso_Scroll mayor que 0.
8. THE Mundo_Hero SHALL declarar para cada una de las tres capas un valor propio de `translateZ`, con el valor más negativo en la Capa_Lejana y el menos negativo en la Capa_Cercana.

### Requirement 9: Flotación propia, interacción táctil y respuesta al cursor

**User Story:** Como visitante que usa un celular, quiero que el fondo respire aunque no toque nada y que reaccione a mis toques, para percibir un espacio con profundidad sin necesitar un ratón.

#### Acceptance Criteria

1. THE Mundo_Hero SHALL asignar a cada Elemento_Fondo una amplitud de vaivén entre 8 y 20 píxeles, una duración entre 5 y 9 segundos y un retraso propio.
2. THE Mundo_Hero SHALL asignar retrasos distintos a Elemento_Fondo consecutivos del mismo tipo.
3. THE animación de vaivén de cada Elemento_Fondo SHALL repetirse de forma indefinida.
4. WHERE la consulta `(hover: hover)` se cumple y el cursor se mueve dentro del hero, THE Script_Unico SHALL desplazar el conjunto del fondo hacia el lado opuesto al cursor con un máximo de 20 píxeles en cada eje.
5. WHERE la consulta `(hover: hover)` se cumple, THE Script_Unico SHALL interpolar el desplazamiento por cursor con un coeficiente de suavizado de 0.08 por fotograma.
6. WHERE la consulta `(hover: hover)` se cumple y el cursor sale del hero, THE Script_Unico SHALL llevar el desplazamiento por cursor de vuelta a cero con la misma interpolación.
7. THE Script_Unico SHALL mantener activo el parallax de scroll del Mundo_Hero en todo ancho de ventana y con toda modalidad de entrada.
8. WHEN el contenedor del hero recibe un evento de toque, THE Script_Unico SHALL identificar el Elemento_Fondo de tipo balón más cercano al punto tocado dentro de un radio declarado y SHALL aplicarle un rebote y un giro acelerado durante un intervalo declarado.
9. THE Script_Unico SHALL registrar el escuchador de toque sobre el contenedor del hero, conservando `pointer-events:none` en el Mundo_Hero y en todos sus descendientes.
10. THE Target_Web SHALL emitir una Zona_Tactil rotulada "Activar movimiento" dentro del hero.
11. THE Script_Unico SHALL solicitar el permiso de `DeviceOrientationEvent` únicamente dentro del manejador del Gesto_Activacion.
12. IF el permiso de `DeviceOrientationEvent` se deniega o el navegador carece de esa capacidad, THEN THE Target_Web SHALL conservar el parallax de scroll, la flotación y el giro de los balones con el mismo comportamiento.

### Requirement 10: Implementación del movimiento con presupuesto de rendimiento

**User Story:** Como responsable técnico, quiero que la animación use solo las propiedades baratas del compositor, para sostener 60 fotogramas por segundo en un teléfono de gama media.

#### Acceptance Criteria

1. THE Hoja_Estilo SHALL animar los Elemento_Fondo usando únicamente las propiedades `transform` y `opacity`.
2. THE Hoja_Estilo SHALL excluir de las reglas de animación y de transición del hero las propiedades `top`, `left`, `width`, `height`, `margin` y `box-shadow`.
3. THE Script_Unico SHALL escribir sobre los Elemento_Fondo y sobre las Vista_Figura únicamente las propiedades `transform`, `opacity` y `visibility` de estilo en línea.
4. THE Script_Unico SHALL registrar el escuchador del evento de desplazamiento con la opción `{passive:true}` y SHALL guardar en ese escuchador únicamente el valor de `window.scrollY`.
5. THE Script_Unico SHALL contener exactamente una llamada a `requestAnimationFrame` dentro de una única función de bucle, compartida por el visor 3D y por el Mundo_Hero.
6. THE Hoja_Estilo SHALL declarar `will-change:transform` únicamente en los selectores de las tres capas del Mundo_Hero.
7. WHEN el Progreso_Scroll alcanza 1, THE Script_Unico SHALL quitar la propiedad `will-change` de las tres capas del Mundo_Hero.
8. WHILE el hero está fuera de la ventana y el documento está oculto, THE Script_Unico SHALL detener el bucle.
9. WHILE el hero está fuera de la ventana, THE Script_Unico SHALL omitir el dibujado del visor 3D y la escritura de estilos sobre las capas del Mundo_Hero.
10. THE Script_Unico SHALL excluir la subcadena `//`, la subcadena `import `, la subcadena `require(`, el atributo `src=` y toda cadena `http`.
11. THE Script_Unico SHALL observar cada sección animada del Target_Web con `IntersectionObserver`.
12. WHILE una sección animada está fuera de la ventana, THE Script_Unico SHALL detener la animación de esa sección.
13. THE Script_Unico SHALL escribir a lo sumo una vez `transform` y una vez `opacity` por capa y por fotograma, y SHALL realizar todas esas escrituras dentro de la única función de bucle.
14. THE Script_Unico SHALL obtener la visibilidad de las secciones desde `IntersectionObserver`, sin ninguna lectura de geometría (`getBoundingClientRect`, `offsetTop`, `clientHeight`) dentro de la función de bucle.
15. IF el objetivo de fotogramas por segundo del Requisito 15 no se alcanza, THEN THE Script_Unico SHALL reducir el número de Elemento_Fondo activos y SHALL conservar sin cambios el contenido gráfico de los Diagrama_Postura.
16. THE Script_Unico SHALL pausar y reanudar las animaciones del Mundo_Hero alternando la clase de Modo_Inerte en el contenedor del Mundo_Hero, y SHALL excluir toda escritura en línea de la propiedad `animation-play-state`.
17. THE Script_Unico SHALL servir con su única función de bucle el visor 3D, el Mundo_Hero, el Conmutador_Vista de cada Figura_Girable y el Arrastre_Rotacion.

### Requirement 11: Accesibilidad del fondo y movimiento reducido

**User Story:** Como persona que usa lector de pantalla o que necesita menos movimiento, quiero que el fondo decorativo no me estorbe, para leer la guía en paz.

#### Acceptance Criteria

1. THE contenedor del Mundo_Hero SHALL llevar el atributo `aria-hidden="true"`.
2. THE Hoja_Estilo SHALL declarar `pointer-events:none` para el contenedor del Mundo_Hero y para todos sus descendientes.
3. THE Elemento_Fondo SHALL excluir el atributo `tabindex` y todo atributo de evento en línea.
4. WHILE la condición Movimiento_Reducido está activa, THE Hoja_Estilo SHALL declarar `animation:none` y `transform:none` para las capas y los Elemento_Fondo del Mundo_Hero.
5. WHILE la condición Movimiento_Reducido está activa, THE Script_Unico SHALL omitir toda escritura de `transform` y de `opacity` sobre las capas del Mundo_Hero.
6. WHILE la condición Movimiento_Reducido está activa, THE Mundo_Hero SHALL permanecer visible como fondo estático con opacidad 1.
7. THE bloque `@media print` de la Hoja_Estilo SHALL ocultar el contenedor del Mundo_Hero, incluso cuando la condición Movimiento_Reducido está activa.
8. WHILE la condición Movimiento_Reducido está activa, THE Vista_Activa de cada Figura_Girable SHALL ser la de Clave_Vista `az-000` y las otras nueve Vista_Figura SHALL permanecer con opacidad 0 y `visibility:hidden`.
9. WHILE la condición Movimiento_Reducido está activa, THE Hoja_Estilo SHALL declarar `animation:none` para las Vista_Figura, para los Gajo_Balon y para las Sombra_Contacto.

### Requirement 12: Comportamiento en pantallas angostas

**User Story:** Como usuaria de teléfono, quiero que el hero se mueva con fluidez, para que la página no se sienta pesada.

#### Acceptance Criteria

1. WHERE el ancho de la ventana es menor que 768 píxeles, THE Script_Unico SHALL mantener activos entre 5 y 7 Elemento_Fondo y ocultar los demás.
2. WHERE el ancho de la ventana es menor que 768 píxeles, THE Script_Unico SHALL omitir el desplazamiento por cursor.
3. WHERE el ancho de la ventana es menor que 768 píxeles, THE Script_Unico SHALL conservar el parallax de tres capas, la escala y el desvanecimiento por Progreso_Scroll.
4. THE Mundo_Hero SHALL marcar cada Elemento_Fondo con un atributo de datos que indica si pertenece al subconjunto de pantallas angostas.
5. THE reducción de carga en pantallas angostas SHALL afectar solo al número de Elemento_Fondo y SHALL conservar las dimensiones declaradas de cada Diagrama_Postura.
6. WHERE el ancho de la ventana es menor que 768 píxeles, THE Script_Unico SHALL animar los Elemento_Fondo de tipo balón con una rotación de dos dimensiones.
7. WHERE el ancho de la ventana es menor que 768 píxeles, THE Conmutador_Vista SHALL activar únicamente las Clave_Vista cuyo azimut pertenece a Subconjunto_Azimuts_Movil.
8. WHERE el ancho de la ventana es menor que 768 píxeles, THE reducción de carga SHALL afectar solo al número de Elemento_Fondo activos y al número de Clave_Vista activas, y SHALL conservar el número de Diagrama_Postura y sus dimensiones declaradas.

### Requirement 13: Invariantes del proyecto conservados

**User Story:** Como responsable del proyecto, quiero que esta feature no rompa ninguna regla ya vigente, para seguir publicando con confianza.

#### Acceptance Criteria

1. THE Target_Web SHALL contener exactamente un elemento `<script>`, propio y sin atributo `src`.
2. THE páginas de capítulo generadas por `build_html.py` SHALL excluir todo elemento `<script>`, todo elemento `<canvas>`, todo atributo de evento en línea y todo elemento `<img>`.
3. THE módulos nuevos SHALL importar únicamente módulos de la librería estándar de Python y módulos del paquete `guia`.
4. THE módulos nuevos SHALL comprobar sus invariantes con `raise ErrorBuild` o una de sus subclases y SHALL excluir la instrucción `assert`.
5. THE suite completa ejecutada con `python _run_tests.py` SHALL terminar sin fallos ni errores.
6. WHEN el build corre en Modo_Estricto con los Archivo_Diagrama marcados Requiere_Archivo presentes, THE Orquestador_Build SHALL emitir un reporte que contiene la cadena `PUBLICABLE`.
7. THE Target_Web SHALL conservar el buscador, los filtros, las descargas relativas, el índice de anclas y las 58 fichas que ya emite hoy.
8. WHEN el Script_Unico se retira del documento, THE Target_Web SHALL mostrar las 58 fichas, el índice de anclas y las descargas relativas.

### Requirement 14: Contenido gráfico del diagrama de postura

**User Story:** Como jugadora, quiero un dibujo limpio con las partes del cuerpo rotuladas y las flechas de movimiento marcadas, para entender el gesto sin leer dos veces.

#### Acceptance Criteria

1. THE Generador_SVG SHALL emitir cada Diagrama_Postura como elemento `<svg>` en línea con atributo `viewBox`, sin ninguna referencia a un archivo de imagen.
2. THE Generador_SVG SHALL emitir todo trazo de contorno de la figura con el color `--azul-profundo` y con un `stroke-width` que equivale a 2 píxeles al ancho declarado del diagrama.
3. THE Generador_SVG SHALL emitir un único valor de `stroke-width` para todos los trazos de contorno de la figura de un mismo Diagrama_Postura.
4. THE Generador_SVG SHALL emitir la figura como una jugadora femenil de cuerpo completo, con cabello recogido y con el rostro sin rasgos dibujados.
5. THE Generador_SVG SHALL emitir el relleno de la silueta con el color `--azul-cielo` y una opacidad de 0.12 o menor.
6. THE Generador_SVG SHALL emitir cada Etiqueta_Anatomica como elemento `<text>` con el color `--azul-profundo`.
7. THE Generador_SVG SHALL emitir para cada Etiqueta_Anatomica una línea guía con el color `--azul-linea`, con un `stroke-width` que equivale a 1 píxel al ancho declarado, y con un círculo relleno en el extremo que toca la parte señalada.
8. THE Generador_SVG SHALL emitir cada flecha de movimiento con el color `--coral-alerta` y con un `stroke-dasharray` declarado.
9. THE Generador_SVG SHALL emitir en cada Diagrama_Postura una línea media vertical con `stroke-dasharray` y un punto relleno que marca el centro de gravedad.
10. WHERE un Diagrama_Postura declara Fase_Numerada, WHILE la emisión de las fases se completa sin error, THE Generador_SVG SHALL emitir un número por fase y el conjunto de números emitidos SHALL ser exactamente el conjunto de enteros de 1 al número de fases declaradas.
11. WHERE un Diagrama_Postura declara Fase_Numerada, THE Motor_Sitio SHALL emitir una lista ordenada de fases cuya numeración coincide con los números emitidos en el SVG y cuyo texto es el de la fase con el mismo número.
12. THE Catalogo_Diagramas SHALL declarar para `potencia-carrera` tres Fase_Numerada en este orden: aproximación en diagonal, plantado y armado de la pierna de atrás, e impacto y acompañamiento del pie.
13. THE Catalogo_Diagramas SHALL declarar para `anatomia-base` estas dieciséis Etiqueta_Anatomica: frente, cuello, hombro, codo, mano, torso, línea media, centro de gravedad, cadera, rodilla, espinilla, pie, empeine, planta, parte interna y parte externa.
14. THE Catalogo_Diagramas SHALL declarar para `cabeceo-frente` la frente como punto de contacto etiquetado, el cuello contraído, los ojos abiertos, el impulso desde el tronco y los brazos abiertos.
15. THE marcado que emite el Generador_SVG SHALL excluir los elementos `<image>`, todo atributo de evento en línea y la función `url(`.
16. THE Etiqueta_Anatomica de cada Diagrama_Postura SHALL usar el vocabulario declarado por `anatomia-base`.
17. IF el Generador_SVG no logra emitir el número de una Fase_Numerada, THEN THE Generador_SVG SHALL emitir los números de las fases restantes y THE Orquestador_Build SHALL registrar en su reporte el identificador del diagrama y el número de la fase omitida.
18. THE longitud de cada hueso SHALL medirse sobre las tres coordenadas del Esqueleto_3D, y esa medida SHALL ser igual a la longitud declarada de ese hueso con una tolerancia de 1e-6, en toda pose, con todo azimut y con toda elevación.
19. THE longitud de un hueso medida sobre las dos coordenadas del SVG emitido SHALL quedar entre 0 y la longitud declarada de ese hueso, porque el Escorzo la acorta; y ninguna comprobación SHALL exigir que esa longitud proyectada sea constante.
20. THE Tapa_Torso SHALL emitirse como un elemento distinto del relleno de la silueta, con `fill-opacity` igual a 1 y con el color `--blanco-suave` en los Diagrama_Postura y `--azul-cielo` en los Elemento_Fondo.

### Requirement 15: La guía es para celular y esta restricción manda

**User Story:** Como jugadora que solo tiene un teléfono de gama media, quiero que la guía se vea y se use bien en mi pantalla, para no tener que pedir prestada una computadora.

#### Acceptance Criteria

1. THE Hoja_Estilo SHALL declarar sus valores base para el Ancho_Base y SHALL introducir los cambios para ventanas más anchas dentro de consultas de medios.
2. THE Hoja_Estilo SHALL limitar todo valor de `width` y de `min-width` expresado en píxeles a 360 o menos.
3. THE Hoja_Estilo SHALL declarar `max-width:100%` para todo contenedor de nivel de sección y para todo contenido gráfico de Diagrama_Postura.
4. THE Hoja_Estilo SHALL declarar `overflow-x:hidden` para los elementos `html` y `body`.
5. THE Hoja_Estilo SHALL limitar todo ancho declarado a `100vw` o menos.
6. THE Hoja_Estilo SHALL declarar para toda Zona_Tactil un `min-height` de 44 píxeles o más y un `min-width` de 44 píxeles o más.
7. THE Hoja_Estilo SHALL declarar una separación de 8 píxeles o más entre Zona_Tactil adyacentes.
8. THE Hoja_Estilo SHALL declarar un tamaño de fuente de 16 píxeles o más para el texto de cuerpo.
9. THE Hoja_Estilo SHALL declarar un tamaño de fuente de 16 píxeles o más para los elementos `input`, `select` y `textarea`.
10. THE Hoja_Estilo SHALL expresar todo alto relativo a la ventana con la unidad `dvh` o con la unidad `svh`, y SHALL excluir las unidades `vh` y `lvh`.
11. THE Target_Web SHALL contener el elemento `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.
12. THE Hoja_Estilo SHALL declarar el relleno de los bordes de pantalla con las funciones `env(safe-area-inset-top)`, `env(safe-area-inset-right)`, `env(safe-area-inset-bottom)` y `env(safe-area-inset-left)`.
13. THE Hoja_Estilo SHALL declarar toda regla que use la pseudoclase `:hover` dentro de una consulta `@media (hover: hover)`.
14. THE Target_Web SHALL ofrecer para cada función una Zona_Tactil que la activa con un solo toque.
15. THE presupuesto de rendimiento del Target_Web SHALL ser de 3000 milisegundos o menos hasta el estado interactivo, y de 60 fotogramas por segundo durante el desplazamiento con un piso de 30 fotogramas por segundo.
16. THE Target_Web SHALL embeber su CSS en un elemento `<style>` y su JavaScript en el Script_Unico, sin ningún recurso que bloquee el renderizado.
17. THE Etiqueta_Anatomica de cada Diagrama_Postura SHALL tener un tamaño de fuente efectivo de 12 píxeles o más cuando su SVG se escala a 360 píxeles de ancho.
18. THE número de Etiqueta_Anatomica emitidas dentro del contorno de la figura SHALL ser 8 o menos por Diagrama_Postura.
19. WHERE un Diagrama_Postura declara más de 8 Etiqueta_Anatomica, THE Motor_Sitio SHALL emitir sus etiquetas fuera del contorno de la figura, unidas a la parte señalada por una línea guía, y SHALL emitir una Zona_Tactil que amplía el diagrama a pantalla completa.
20. WHERE el ancho de la ventana es menor que 768 píxeles, THE Hoja_Estilo SHALL declarar la navegación principal anclada al borde inferior de la ventana con `position:sticky` y `bottom:0`, con un relleno inferior que suma `env(safe-area-inset-bottom)`.

### Requirement 16: Paleta cerrada con modo oscuro

**User Story:** Como lectora, quiero un color de fondo suave y un texto siempre legible, para leer largo rato sin cansarme la vista.

#### Acceptance Criteria

1. THE Paleta_Guia SHALL declarar exactamente estos siete tokens con estos valores: `--azul-cielo` con `#DCEEFF`, `--azul-medio` con `#B8DCFA`, `--azul-profundo` con `#0B2C4D`, `--azul-linea` con `#1E6FA8`, `--rosa-acento` con `#E85D9B`, `--coral-alerta` con `#D92D20` y `--blanco-suave` con `#F7FBFF`.
2. THE Paleta_Guia SHALL declarar una única constante de Python por cada token, con `WEB_HERO_CIELO` como nombre canónico de `--azul-cielo` y `WEB_HERO_TINTA` como nombre canónico de `--azul-profundo`.
3. THE Hoja_Estilo SHALL declarar el color `--azul-profundo` para todo el texto de cuerpo del Target_Web.
4. THE Hoja_Estilo SHALL declarar como fondo de sección y de tarjeta únicamente los tokens `--azul-cielo`, `--azul-medio` y `--blanco-suave`.
5. THE Hoja_Estilo SHALL excluir `#FFFFFF`, `#fff`, `white` y `#7EC8FF` como color de fondo de sección y de tarjeta.
6. THE Hoja_Estilo SHALL excluir el color blanco como color de texto sobre todo fondo de la Paleta_Guia.
7. THE Contraste de cada par de color de texto de cuerpo y color de fondo declarado por la Hoja_Estilo SHALL ser 4.5 o más, medido con la función Contraste.
8. THE Contraste de cada par de color de texto grande, de icono o de trazo y color de fondo declarado por la Hoja_Estilo SHALL ser 3.0 o más, medido con la función Contraste.
9. THE Hoja_Estilo SHALL usar `--rosa-acento` en la numeración de pasos, en el subrayado del título, en la pestaña activa y en los íconos de logro.
10. THE Hoja_Estilo SHALL usar `--rosa-acento` únicamente en elementos gráficos y en texto de 24 píxeles o más, o de 19 píxeles o más en negrita.
11. THE Hoja_Estilo SHALL excluir `--rosa-acento` como color de fondo de sección y de tarjeta.
12. THE Hoja_Estilo SHALL usar `--coral-alerta` en las flechas de movimiento de los diagramas y en el texto de error.
13. THE Hoja_Estilo SHALL pintar el texto de error en `--coral-alerta` únicamente sobre el fondo `--blanco-suave`.
14. THE Hoja_Estilo SHALL declarar toda sombra con el color `rgba(11,44,77,0.12)`.
15. WHERE la condición Modo_Oscuro se cumple, THE Hoja_Estilo SHALL declarar el fondo `#0B1F33` y el texto `#DCEEFF`.
16. WHERE la condición Modo_Oscuro se cumple, THE Contraste de cada par de texto y fondo declarado SHALL ser 4.5 o más para texto de cuerpo y 3.0 o más para texto grande, para íconos y para trazos.
17. THE Paleta_Guia SHALL conservar sin cambios los tokens `WEB_FONDO`, `WEB_FONDO_PROFUNDO` y `WEB_AZUL_CLARO`.
18. THE Hoja_Estilo SHALL usar `WEB_AZUL_CLARO` únicamente en las aristas, los acentos y el halo del visor 3D del hero.

### Requirement 17: Tono del texto en segunda persona y en femenino

**User Story:** Como jugadora, quiero que la guía me hable a mí, en femenino y de tú, para sentir que está escrita para mí y no para un jugador genérico.

#### Acceptance Criteria

1. THE textos del Catalogo_Diagramas y de las fichas SHALL dirigirse a la lectora en segunda persona del singular.
2. THE Catalogo_Diagramas SHALL declarar la lista de verbos permitidos en segunda persona del singular.
3. THE cada paso de cada Diagrama_Postura SHALL comenzar por uno de los verbos de esa lista.
4. THE Guardarrail_Lexico SHALL rechazar todo texto del Catalogo_Diagramas y de las fichas que contenga una de las expresiones de masculino genérico declaradas: "el jugador", "los jugadores", "el alumno", "los alumnos", "el niño", "los niños", "el chico" y "los chicos".
5. THE Guardarrail_Lexico SHALL rechazar todo texto del Catalogo_Diagramas y de las fichas que contenga una de las formas masculinas declaradas para referirse a la lectora: "listo", "atento", "concentrado", "cansado" y "preparado".
6. THE Guardarrail_Lexico SHALL rechazar todo texto del Catalogo_Diagramas y de las fichas que contenga una de las expresiones condescendientes declaradas: "es facilísimo", "es muy fácil", "no te compliques" y "solo tienes que".
7. THE Guardarrail_Lexico SHALL nombrar en su mensaje de fallo el identificador de la entrada y la expresión rechazada.

### Requirement 18: Créditos y licencias de las imágenes

**User Story:** Como responsable del proyecto, quiero un bloque de créditos y licencias al final de la guía, para dejar clara la procedencia de cada imagen.

#### Acceptance Criteria

1. THE Motor_Sitio SHALL emitir al final del Target_Web un Bloque_Creditos con el ancla `creditos`.
2. THE Bloque_Creditos SHALL contener una entrada por cada Diagrama_Postura del Catalogo_Diagramas.
3. THE cada entrada del Bloque_Creditos SHALL contener el autor, la fuente, la licencia y el enlace de la imagen.
4. WHERE un Diagrama_Postura se rinde desde el Generador_SVG, THE entrada correspondiente del Bloque_Creditos SHALL declarar la autoría propia del proyecto y la licencia propia del proyecto.
5. THE Bloque_Creditos SHALL emitir cada enlace como texto visible, sin elemento `<a href>` y sin ningún atributo que provoque una petición de red.
6. THE Bloque_Creditos SHALL existir aunque los ocho Diagrama_Postura se rindan desde el Generador_SVG.
7. THE navegación en página del Target_Web SHALL incluir un enlace al ancla `creditos`.
8. IF una entrada del Bloque_Creditos carece de autor, de fuente, de licencia o de enlace, THEN THE Motor_Sitio SHALL emitir la entrada con los campos disponibles y la marca "dato pendiente" en cada campo ausente.
9. WHILE una entrada del Bloque_Creditos tiene campos ausentes, THE Orquestador_Build SHALL registrar el identificador de esa entrada y el nombre de cada campo ausente en su reporte, y SHALL completar el build.

### Requirement 19: Estructura y orden de las secciones de la guía

**User Story:** Como jugadora, quiero que la guía siga siempre el mismo recorrido, para encontrar lo que busco sin perderme.

#### Acceptance Criteria

1. THE Target_Web SHALL emitir sus secciones en este orden: hero, índice, `anatomia-base`, leyenda de símbolos, los cuatro bloques de Fundamento, rutina semanal y Bloque_Creditos.
2. THE hero SHALL contener el título, el subtítulo y una Zona_Tactil rotulada "Empezar".
3. THE índice SHALL contener una Zona_Tactil por sección, cada una con un enlace al ancla de esa sección.
4. THE cada bloque de Fundamento SHALL contener, en este orden: el Diagrama_Postura, sus pasos numerados, su error frecuente y la Seccion_Reservada de los diagramas de ejercicio de ese Fundamento.
5. THE Motor_Sitio SHALL emitir los cuatro bloques de Fundamento en este orden: golpeo, pase, control y conducción, y cabeceo.
6. THE Motor_Sitio SHALL emitir como Seccion_Reservada el ancla `leyenda-simbolos`, el ancla `rutina-semanal` y, dentro de cada bloque de Fundamento, el ancla `ejercicios-<fundamento>`.
7. WHILE el contenido de una Seccion_Reservada está ausente, THE Motor_Sitio SHALL conservar su ancla y su encabezado.

### Requirement 20: Seguridad en el cabeceo

**User Story:** Como jugadora y como entrenadora, quiero la advertencia de seguridad escrita junto al cabeceo, para no aprender el gesto de una forma que lastime.

#### Acceptance Criteria

1. THE Catalogo_Diagramas SHALL declarar para la entrada `cabeceo-frente` un campo obligatorio de Advertencia_Cabeceo con 120 caracteres o más.
2. THE Advertencia_Cabeceo SHALL nombrar la frente como única superficie de contacto y SHALL nombrar la coronilla y la cara como superficies a evitar.
3. THE Advertencia_Cabeceo SHALL nombrar el cuello contraído y firme, los ojos abiertos, y la progresión con balón blando y sin salto para menores.
4. THE Motor_Sitio SHALL emitir la Advertencia_Cabeceo dentro del bloque del Fundamento de cabeceo, antes de los pasos numerados.
5. IF la entrada `cabeceo-frente` carece de Advertencia_Cabeceo o su Advertencia_Cabeceo omite uno de los conceptos exigidos, THEN THE Validador_Catalogo SHALL lanzar `ErrorBuild` con el código `E_ASSET_INVALIDO` nombrando el concepto ausente.
6. THE Advertencia_Cabeceo SHALL emitirse como texto del HTML, sin depender del Script_Unico.

### Requirement 21: Esqueleto tridimensional y proyección por vista

**User Story:** Como jugadora, quiero que al girar una figura se vea de verdad su espalda, su coronilla y la planta de su pie, para entender la postura desde el ángulo en que yo la voy a hacer.

#### Acceptance Criteria

1. THE Proyector_Vistas SHALL declarar para cada una de las diecisiete articulaciones del esqueleto una tercera coordenada de profundidad, y el conjunto resultante SHALL ser el Esqueleto_3D.
2. THE Proyector_Vistas SHALL conservar las diecisiete articulaciones y los dieciséis huesos que el Generador_SVG ya declara, con los mismos nombres y las mismas longitudes.
3. WHEN el Proyector_Vistas recibe un Esqueleto_3D y un azimut, THE Proyector_Vistas SHALL rotar cada articulación alrededor del eje vertical que pasa por la cadera media antes de proyectar.
4. WHEN el Proyector_Vistas recibe un Esqueleto_3D y una elevación, THE Proyector_Vistas SHALL rotar cada articulación alrededor del eje horizontal transversal después de aplicar el azimut.
5. THE Proyector_Vistas SHALL medir la longitud de cada hueso sobre las tres coordenadas del Esqueleto_3D rotado y SHALL obtener la longitud declarada de ese hueso con una tolerancia de 1e-6.
6. THE Proyector_Vistas SHALL obtener las dos coordenadas de dibujo descartando la coordenada de profundidad del Esqueleto_3D rotado.
7. WHERE el azimut vale `a`, THE longitud proyectada de un hueso paralelo al eje horizontal frontal SHALL ser el producto de la longitud declarada de ese hueso por el valor absoluto del coseno de `a`, con una tolerancia de 1e-6.
8. THE Proyector_Vistas SHALL mantener toda articulación proyectada dentro del `viewBox` de su Vista_Figura, con todo azimut de Azimuts_Declarados y toda elevación de Elevaciones_Declaradas.
9. THE Proyector_Vistas SHALL derivar la clasificación de cada brazo y de cada pierna en Miembro_Trasero o Miembro_Delantero del signo de la profundidad rotada del punto medio de las articulaciones de ese miembro.
10. WHERE la profundidad rotada del punto medio de un miembro vale 0, THE Proyector_Vistas SHALL clasificar ese miembro como Miembro_Delantero.
11. THE Proyector_Vistas SHALL formatear todo número con tres decimales y recorte de ceros finales, igual que el Generador_SVG.
12. WHEN el Proyector_Vistas emite dos veces la misma pose con el mismo azimut y la misma elevación, THE Proyector_Vistas SHALL producir dos secuencias de bytes idénticas.
13. THE Proyector_Vistas SHALL comprobar sus invariantes con `raise ErrorBuild` o con una de sus subclases y SHALL excluir la instrucción `assert`.

### Requirement 22: Las diez vistas de cada figura girable

**User Story:** Como visitante, quiero que la figura muestre un dibujo propio en cada ángulo del giro, para ver un cuerpo con volumen y no un recorte espejeado.

#### Acceptance Criteria

1. THE conjunto de Clave_Vista SHALL ser exactamente `az-000`, `az-045`, `az-090`, `az-135`, `az-180`, `az-225`, `az-270`, `az-315`, `el-p60` y `el-m60`.
2. THE ocho Vista_Azimut SHALL declarar los grados de Azimuts_Declarados con elevación 0.
3. THE dos Vista_Elevacion SHALL declarar azimut 0 con las elevaciones de Elevaciones_Declaradas, `el-p60` con +60 grados y `el-m60` con −60 grados.
4. THE Mundo_Hero SHALL declarar cada Elemento_Fondo de tipo silueta de jugadora como Figura_Girable.
5. THE Catalogo_Diagramas SHALL declarar el campo Girable con el valor verdadero en `anatomia-base` y con el valor falso en las otras siete entradas.
6. THE cada Figura_Girable SHALL emitir exactamente diez Vista_Figura, una por Clave_Vista, en el orden declarado en el criterio 22.1.
7. THE cada Vista_Figura SHALL llevar el atributo `data-vista` con su Clave_Vista y el atributo `data-figura` con el identificador de su Figura_Girable.
8. WHEN el Script_Unico se retira del documento, THE Target_Web SHALL conservar las diez Vista_Figura de cada Figura_Girable.
9. THE cada Figura_Girable SHALL marcar en el marcado inicial la Vista_Figura de Clave_Vista `az-000` como Vista_Activa.
10. THE Hoja_Estilo SHALL declarar `opacity:0` y `visibility:hidden` para toda Vista_Figura que carece de la clase de Vista_Activa, y `opacity:1` y `visibility:visible` para la que la lleva.
11. THE cada Vista_Figura SHALL emitirse como elemento `<svg>` en línea con `viewBox`, con `width` y con `height`, y SHALL excluir los elementos `<image>`, la función `url(`, la cadena `http`, el atributo `tabindex` y todo atributo de evento en línea.
12. THE número de Vista_Figura del Target_Web SHALL ser diez veces el número de Figura_Girable declaradas.
13. THE número de Vista_Figura del Target_Web SHALL ser 40 o menos, y el tamaño de cada Vista_Figura SHALL ser de 6144 bytes o menos.

### Requirement 23: Contenido propio de la espalda, la picada y la contrapicada

**User Story:** Como jugadora, quiero que la vista de espalda se vea de espaldas y la picada se vea desde arriba, para reconocer el ángulo sin tener que adivinarlo.

#### Acceptance Criteria

1. THE Vista_Figura de Clave_Vista `az-180` SHALL contener los grupos `omoplatos`, `coleta-trasera` y `numero-camiseta`.
2. THE Vista_Figura de Clave_Vista `az-000` SHALL contener el grupo `coleta-recogida` y SHALL excluir los grupos `omoplatos`, `coleta-trasera` y `numero-camiseta`.
3. THE cada Vista_Figura SHALL excluir el grupo `cara` y todo elemento con la clase `rasgo-facial`.
4. THE Vista_Figura de Clave_Vista `el-p60` SHALL contener los grupos `hombros-superiores` y `coronilla`.
5. THE Vista_Figura de Clave_Vista `el-p60` SHALL emitir el grupo del balón después del grupo de la figura en el orden del documento, con el centro del balón por debajo del centro de la cadera proyectada.
6. THE Vista_Figura de Clave_Vista `el-m60` SHALL contener los grupos `planta-pie-apoyo` y `suela-taco`.
7. THE ancho del rectángulo envolvente de la línea de hombros proyectada en las Clave_Vista `az-090` y `az-270` SHALL ser el 35 % o menos del ancho del mismo rectángulo en la Clave_Vista `az-000`.
8. THE ancho del rectángulo envolvente de la línea de hombros proyectada en las Clave_Vista `az-045`, `az-135`, `az-225` y `az-315` SHALL quedar entre el ancho de la Clave_Vista `az-090` y el ancho de la Clave_Vista `az-000`, sin igualar ninguno de los dos.
9. THE marcado de cada una de las diez Vista_Figura de una misma Figura_Girable SHALL diferir del marcado de las otras nueve.
10. THE Vista_Figura de Clave_Vista `az-180` SHALL diferir de la de Clave_Vista `az-000` en al menos un nombre de grupo, además de diferir en coordenadas.
11. THE número de camiseta que emite el grupo `numero-camiseta` SHALL emitirse como elemento `<text>` con el color `--azul-profundo` y con un tamaño efectivo de 12 píxeles o más a 360 píxeles de ancho.

### Requirement 24: Orden de dibujo por profundidad y volumen

**User Story:** Como visitante, quiero que el brazo y la pierna de atrás queden tapados por el torso, para percibir un cuerpo con volumen mientras gira.

#### Acceptance Criteria

1. THE cada Vista_Figura SHALL emitir sus grupos en este orden fijo del documento: `miembros-traseros`, `tapa-torso`, `torso`, `miembros-delanteros`.
2. THE todo trazo dentro del grupo `miembros-traseros` SHALL llevar el atributo `stroke-opacity` con el valor 0.55.
3. THE todo trazo dentro del grupo `miembros-delanteros` SHALL llevar el atributo `stroke-opacity` con el valor 1.
4. THE grupo `tapa-torso` SHALL emitir la Tapa_Torso con `fill-opacity` igual a 1, de modo que oculte los trazos del grupo `miembros-traseros` que quedan bajo el torso.
5. THE grupo `torso` SHALL conservar el relleno de la silueta con el color `--azul-cielo` y una opacidad de 0.12 o menor, y el contorno con el color `--azul-profundo`.
6. THE cada Vista_Figura SHALL asignar cada brazo y cada pierna a exactamente uno de los grupos `miembros-traseros` y `miembros-delanteros`, según la clasificación del Proyector_Vistas.
7. THE unión de los grupos `miembros-traseros` y `miembros-delanteros` SHALL contener los cuatro miembros en toda Vista_Figura.
8. THE Vista_Figura de Clave_Vista `az-000` SHALL asignar los cuatro miembros al grupo `miembros-delanteros`.
9. THE Vista_Figura de Clave_Vista `az-180` SHALL asignar al grupo `miembros-traseros` los miembros cuya profundidad canónica queda delante del torso.
10. THE grosor de trazo de los grupos `miembros-traseros`, `torso` y `miembros-delanteros` SHALL ser el único valor de contorno que el Generador_SVG declara para ese diagrama, sin que `stroke-opacity` lo altere.

### Requirement 25: Giro continuo de la figura y conmutación de vista

**User Story:** Como visitante, quiero ver a las jugadoras del fondo girando sin cortes, para que la portada se sienta un espacio con profundidad.

#### Acceptance Criteria

1. THE Hoja_Estilo SHALL declarar para el contenedor de cada Figura_Girable las propiedades `perspective:1000px` y `transform-style:preserve-3d`.
2. THE Mundo_Hero SHALL asignar a cada Figura_Girable una duración de vuelta completa entre 18 y 30 segundos.
3. THE Mundo_Hero SHALL asignar duraciones distintas a Figura_Girable distintas.
4. THE Mundo_Hero SHALL asignar sentido de giro horario a al menos una Figura_Girable y sentido antihorario a al menos otra.
5. THE animación de giro de cada Figura_Girable SHALL repetirse de forma indefinida.
6. WHEN el ángulo de giro de una Figura_Girable cambia, THE Conmutador_Vista SHALL activar la Clave_Vista cuyo azimut declarado está más cerca de ese ángulo y SHALL desactivar las otras nueve.
7. WHERE dos Clave_Vista quedan a la misma distancia del ángulo actual, THE Conmutador_Vista SHALL activar la de azimut declarado menor.
8. WHEN el Conmutador_Vista cambia la Vista_Activa, THE Script_Unico SHALL escribir `opacity` y `visibility` únicamente sobre la Vista_Figura que sale y sobre la Vista_Figura que entra.
9. WHILE la Clave_Vista más cercana al ángulo actual no cambia, THE Script_Unico SHALL omitir toda escritura sobre las Vista_Figura de esa Figura_Girable.
10. THE Script_Unico SHALL aplicar a la Vista_Activa una Rotacion_Residual `rotateY` cuyo valor absoluto es de 22.5 grados o menos.
11. WHERE el ángulo actual coincide con el azimut declarado de la Vista_Activa, THE Rotacion_Residual SHALL valer 0 grados.
12. THE Script_Unico SHALL excluir las subcadenas `innerHTML`, `outerHTML`, `createElement`, `appendChild`, `removeChild`, `insertAdjacentHTML` y `cloneNode`.
13. THE número de nodos de cada Figura_Girable SHALL ser el mismo antes y después de cualquier conmutación de vista.
14. THE Mundo_Hero SHALL declarar para cada Figura_Girable una Sombra_Contacto con la escala horizontal `0.40 + 0.60 * |cos(azimut)|` y escala vertical 1.
15. THE Sombra_Contacto SHALL emitirse como elemento `<ellipse>` dentro del SVG de la Figura_Girable, y THE Hoja_Estilo SHALL excluir la propiedad `box-shadow` de las reglas de la Sombra_Contacto.
16. THE Mundo_Hero SHALL declarar para cada Figura_Girable un valor propio de `translateZ`, distinto del de las otras Figura_Girable de su misma capa.

### Requirement 26: Balón como esfera con gajos y eje inclinado

**User Story:** Como visitante, quiero que los balones se vean redondos y muestren el polo de arriba y el de abajo al girar, para que parezcan balones y no discos.

#### Acceptance Criteria

1. THE Mundo_Hero SHALL emitir cada Elemento_Fondo de tipo balón como Balon_Esfera con exactamente ocho Gajo_Balon.
2. THE cada Gajo_Balon SHALL declarar su propia rotación con la función `rotate3d(`, distinta de la de los otros siete.
3. THE Hoja_Estilo SHALL declarar `transform-style:preserve-3d` para el contenedor de cada Balon_Esfera.
4. THE cada Balon_Esfera SHALL declarar un Eje_Giro_Inclinado cuyas tres componentes son distintas de cero.
5. THE inclinación del Eje_Giro_Inclinado respecto de la vertical SHALL quedar entre 15 y 45 grados.
6. THE cada Balon_Esfera SHALL emitir los grupos `polo-superior` y `polo-inferior`.
7. THE duración de vuelta de cada Balon_Esfera SHALL quedar entre 14 y 26 segundos, y las duraciones SHALL ser distintas entre balones.
8. THE duración de vuelta de cada Balon_Esfera de la Capa_Cercana SHALL ser menor que la de cada Balon_Esfera de la Capa_Lejana.
9. THE Mundo_Hero SHALL asignar sentido de giro horario a al menos un Balon_Esfera y sentido antihorario a al menos otro.
10. WHERE el ancho de la ventana es menor que 768 píxeles, THE Hoja_Estilo SHALL animar cada Balon_Esfera con la función `rotate(` de dos dimensiones y SHALL emitir un Gajo_Balon sombreado desplazado del centro.
11. THE marcado de cada Balon_Esfera SHALL excluir los elementos `<image>`, la función `url(`, la cadena `http` y todo atributo de evento en línea.

### Requirement 27: Modo inerte, un desvanecimiento que no consume GPU

**User Story:** Como usuaria de un teléfono, quiero que el fondo deje de gastar batería en cuanto desaparece, para que la lectura no me caliente el celular.

#### Acceptance Criteria

1. WHEN la opacidad del Mundo_Hero llega a 0, THE Script_Unico SHALL añadir la clase de Modo_Inerte al contenedor del Mundo_Hero.
2. THE Hoja_Estilo SHALL declarar para el Modo_Inerte las propiedades `visibility:hidden` y `animation-play-state:paused`.
3. THE regla de Modo_Inerte SHALL alcanzar las tres capas, los Elemento_Fondo, las Vista_Figura, los Gajo_Balon y las Sombra_Contacto.
4. WHILE el Modo_Inerte está activo, THE Hoja_Estilo SHALL declarar `will-change:auto` para las tres capas del Mundo_Hero.
5. WHILE el Modo_Inerte está activo, THE Script_Unico SHALL omitir toda escritura de `transform` y de `opacity` sobre las capas del Mundo_Hero y sobre las Vista_Figura.
6. WHEN el Progreso_Scroll baja por debajo de 1, THE Script_Unico SHALL quitar la clase de Modo_Inerte y las animaciones pausadas SHALL continuar desde el punto en que quedaron.
7. THE Hoja_Estilo SHALL declarar para la reaparición del Mundo_Hero una transición de `opacity` con una duración entre 200 y 600 milisegundos.
8. THE número de nodos del Mundo_Hero SHALL ser el mismo con el Modo_Inerte activo y con el Modo_Inerte inactivo.
9. THE Script_Unico SHALL alternar el Modo_Inerte con la lista de clases del contenedor, y SHALL excluir toda escritura en línea de `animation-play-state` y de `display`.

### Requirement 28: Toque, giro de impulso y ampliación con arrastre

**User Story:** Como jugadora, quiero abrir una figura a pantalla completa y girarla con el dedo, para verla desde el ángulo que necesito.

#### Acceptance Criteria

1. WHEN el contenedor del hero recibe un evento de toque, THE Script_Unico SHALL identificar el Balon_Esfera o la Figura_Girable más cercana al punto tocado dentro del radio declarado y SHALL aplicarle un rebote y un Giro_Impulso.
2. THE Giro_Impulso SHALL completar una vuelta en una duración de 1.2 segundos con una tolerancia de 0.1 segundos.
3. WHEN el Giro_Impulso termina, THE elemento tocado SHALL retomar la duración de vuelta que el Mundo_Hero le declara.
4. THE Motor_Sitio SHALL emitir para cada Diagrama_Postura y para cada Figura_Girable ampliable una Zona_Tactil de ampliación cuyo destino es el ancla `#<id>-ampliada`.
5. THE Hoja_Estilo SHALL declarar cada Visor_Ampliado como overlay con `position:fixed`, `inset:0` y un `z-index` propio, y SHALL restringir `position:fixed` a ese único selector, con exactamente una aparición en toda la Hoja_Estilo.
6. WHEN el Script_Unico se retira del documento, THE Zona_Tactil de ampliación SHALL seguir abriendo su Visor_Ampliado con un solo toque mediante el selector `:target`, y THE Zona_Tactil de cierre SHALL seguir cerrándolo con un solo toque.
7. WHILE un Visor_Ampliado de una Figura_Girable está activo, WHEN la usuaria arrastra el dedo en horizontal, THE Arrastre_Rotacion SHALL cambiar el azimut mostrado.
8. WHILE un Visor_Ampliado de una Figura_Girable está activo, WHEN la usuaria arrastra el dedo en vertical, THE Arrastre_Rotacion SHALL cambiar la elevación mostrada.
9. THE Arrastre_Rotacion SHALL convertir el desplazamiento del dedo en grados con una constante declarada de grados por píxel, y el azimut resultante SHALL quedar en el intervalo semiabierto [0, 360).
10. THE Arrastre_Rotacion SHALL acotar la elevación resultante al intervalo cerrado de −60 a +60 grados.
11. WHERE el valor absoluto de la elevación es de 30 grados o más, THE Arrastre_Rotacion SHALL activar la Vista_Elevacion del signo de esa elevación.
12. WHERE el valor absoluto de la elevación es menor que 30 grados, THE Arrastre_Rotacion SHALL activar la Vista_Azimut más cercana al azimut resultante, con el mismo desempate del criterio 25.7.
13. THE Hoja_Estilo SHALL declarar `touch-action:none` para el contenido del Visor_Ampliado, y THE Script_Unico SHALL registrar los escuchadores del Arrastre_Rotacion con la opción `{passive:true}`.
14. THE escuchadores del Arrastre_Rotacion SHALL guardar únicamente las coordenadas del puntero, y THE Arrastre_Rotacion SHALL resolver la vista dentro de la única función de bucle.
15. THE Arrastre_Rotacion SHALL escribir únicamente `transform`, `opacity` y `visibility`, y SHALL conservar el número de nodos del Visor_Ampliado.
16. THE cada Visor_Ampliado SHALL contener una Zona_Tactil de cierre con un alto y un ancho de 44 píxeles o más, de forma circular, con el icono de cierre como `<svg>` en línea y con el atributo `aria-label="Cerrar"`.
17. WHERE un Diagrama_Postura declara Girable con el valor falso, THE Visor_Ampliado SHALL mostrar su vista frontal y SHALL omitir el Arrastre_Rotacion.
18. WHILE la condición Movimiento_Reducido está activa, THE Conmutador_Vista automático SHALL detenerse y THE Arrastre_Rotacion SHALL conservar su respuesta al arrastre de la usuaria.
19. WHERE la consulta `(hover: hover)` se cumple, THE Script_Unico SHALL conservar el desplazamiento por cursor con un tope de 20 píxeles por eje y un coeficiente de suavizado de 0.08 por fotograma.
20. THE Script_Unico SHALL solicitar el permiso de `DeviceOrientationEvent` únicamente dentro del manejador del Gesto_Activacion, también con el Arrastre_Rotacion disponible.
21. THE cada Visor_Ampliado SHALL contener exactamente un encabezado `<h2>`, con un `id` propio, y SHALL declarar `role="dialog"`, `aria-modal="true"` y `aria-labelledby` con el valor de ese `id`.
22. THE cada Visor_Ampliado SHALL declarar una barra superior fija de 56 píxeles con el encabezado truncado a una línea mediante `text-overflow:ellipsis`, `white-space:nowrap` y `overflow:hidden`, y con la Zona_Tactil de cierre alineada al extremo opuesto; y THE cuerpo del Visor_Ampliado SHALL declarar `overflow-y:auto` y `overscroll-behavior:contain`.
23. THE contenedor de la ilustración de cada Visor_Ampliado SHALL declarar una `aspect-ratio` y un `max-height` relativo a la ventana, y su contenido gráfico SHALL declarar `width:100%`, `height:100%` y `object-fit:contain`.
24. WHEN la usuaria abre un Visor_Ampliado, THE Script_Unico SHALL guardar el valor de `window.scrollY`, SHALL bloquear el desplazamiento del `<body>` con `overflow:hidden` mediante una clase, SHALL mover el foco a la Zona_Tactil de cierre y SHALL atrapar la tabulación dentro del overlay; y WHEN lo cierra --con la Zona_Tactil de cierre, con la tecla Escape o con un toque en el fondo comprobando que el blanco del evento es el propio overlay-- SHALL restaurar esa posición de desplazamiento exacta y SHALL devolver el foco al elemento que lo abrió.

### Requirement 29: Presupuesto de rendimiento con diez vistas por figura

**User Story:** Como responsable técnico, quiero que el multi-vista degrade el adorno y nunca el contenido, para sostener la fluidez sin perder los diagramas técnicos.

#### Acceptance Criteria

1. THE Script_Unico SHALL contener exactamente una llamada a `requestAnimationFrame`, dentro de una única función de bucle compartida por el visor 3D, el Mundo_Hero, el Conmutador_Vista de cada Figura_Girable y el Arrastre_Rotacion.
2. THE Script_Unico SHALL escribir por fotograma y por Figura_Girable a lo sumo una vez `transform`, dos veces `opacity` y dos veces `visibility`, y SHALL realizar esas escrituras dentro de la única función de bucle.
3. THE función de bucle SHALL excluir las lecturas de geometría `getBoundingClientRect`, `offsetTop` y `clientHeight`.
4. IF el objetivo de fotogramas por segundo del criterio 15.15 no se alcanza, THEN THE Script_Unico SHALL reducir primero el número de Figura_Girable y de Elemento_Fondo activos.
5. IF el objetivo de fotogramas por segundo sigue sin alcanzarse en anchos de ventana menores que 768 píxeles, THEN THE Conmutador_Vista SHALL reducir las Clave_Vista activas a los seis azimuts de Subconjunto_Azimuts_Movil.
6. THE degradación por rendimiento SHALL conservar el número de Diagrama_Postura, sus dimensiones declaradas, sus Etiqueta_Anatomica y sus Fase_Numerada.
7. THE Hoja_Estilo SHALL animar las Vista_Figura, los Gajo_Balon y las Sombra_Contacto usando únicamente las propiedades `transform` y `opacity`.
8. THE Hoja_Estilo SHALL excluir de las reglas de animación y de transición de las Vista_Figura, de los Gajo_Balon y de las Sombra_Contacto las propiedades `top`, `left`, `width`, `height`, `margin` y `box-shadow`.
9. THE Hoja_Estilo SHALL declarar `will-change:transform` únicamente en los selectores de las tres capas del Mundo_Hero, y SHALL excluir `will-change` de los selectores de Vista_Figura.
10. THE Script_Unico SHALL obtener la visibilidad de cada sección animada desde `IntersectionObserver`.
11. THE contenedor del Mundo_Hero SHALL llevar el atributo `aria-hidden="true"`, y THE Hoja_Estilo SHALL declarar `pointer-events:none` para ese contenedor, para todos sus descendientes y para toda Vista_Figura de una Figura_Girable del fondo.
12. THE escuchador del evento de desplazamiento SHALL registrarse con la opción `{passive:true}` y SHALL guardar únicamente el valor de `window.scrollY`.
13. THE presupuesto de fotogramas por segundo del criterio 15.15 SHALL medirse con emulación de teléfono de gama media y limitación de procesador de cuatro veces, como comprobación manual de la usuaria.

### Requirement 30: Whitelist de extensiones y validador de rutas de asset

**User Story:** Como responsable del proyecto, quiero una única función que decida qué ruta de imagen es aceptable, para poder añadir formatos sin abrir la puerta a peticiones de red.

#### Acceptance Criteria

1. THE Extensiones_Permitidas SHALL contener exactamente `.webp`, `.svg`, `.png` y `.avif`, en ese orden.
2. THE Validador_Rutas SHALL aceptar una ruta cuando esa ruta empieza por `assets/` y termina en una de las Extensiones_Permitidas.
3. IF una ruta empieza por `http://`, por `https://`, por `//` o por `/`, THEN THE Validador_Rutas SHALL rechazarla y su mensaje SHALL nombrar esa ruta.
4. IF una ruta contiene el segmento `..`, THEN THE Validador_Rutas SHALL rechazarla y su mensaje SHALL nombrar esa ruta.
5. IF una ruta termina en una extensión que no pertenece a Extensiones_Permitidas, THEN THE Validador_Rutas SHALL rechazarla y su mensaje SHALL nombrar esa extensión.
6. THE Validador_Rutas SHALL comparar la extensión de la ruta convertida a minúsculas.
7. THE Validador_Rutas SHALL aceptar la ruta relativa de cada una de las ocho entradas del Catalogo_Diagramas.
8. THE Guardarrail_Recursos SHALL conservar la prohibición de `<link>` a hoja de estilo, de `@import`, de `src="http` y de la subcadena `//` dentro del Script_Unico.
9. THE Guardarrail_Recursos SHALL aceptar la subcadena `http` como texto visible únicamente dentro del Bloque_Creditos o como rótulo visible de un enlace de navegación, y SHALL rechazarla en todo otro nodo de texto del Target_Web.
10. THE Orquestador_Build SHALL comprobar la firma de la copia de cada Asset_Local según su extensión, con las firmas del criterio 5.12, antes de publicarla.
11. THE Hoja_Estilo SHALL excluir la función CSS `url(`, de modo que ninguna imagen se cargue desde el CSS.

## Notas de alcance

- **La restricción de celular manda.** El Requisito 15 gana cuando choca con cualquier otro requisito de esta spec. Si un criterio del hero, de la paleta o de los diagramas impide cumplir el Requisito 15, se ajusta el otro criterio, no el 15.
- **Lo que no se puede verificar desde Python.** Los fotogramas por segundo reales, el tiempo hasta interactivo y el comportamiento con emulación "Moto G Power" y CPU throttling 4x **no** son observables desde la suite. Son una **comprobación manual de la usuaria** en las herramientas de desarrollo del navegador. El criterio 15.15 registra el presupuesto como objetivo; lo que la suite prueba en su lugar es el **contrato del código emitido**: una sola llamada a `requestAnimationFrame` (10.5), a lo sumo una escritura de `transform` y una de `opacity` por capa y fotograma dentro del bucle (10.13), cero lecturas de geometría dentro del bucle (10.14), solo `transform` y `opacity` animados (10.1, 10.2), escuchador de scroll pasivo que solo guarda `scrollY` (10.4), `IntersectionObserver` para pausar (10.11, 10.12), cero recursos que bloqueen el renderizado (15.16) y la degradación que quita elementos de fondo antes que tocar los diagramas (10.15).
- **Renombrado de términos.** `Foto_Tecnica` pasa a `Diagrama_Postura` y `Catalogo_Fotos` pasa a `Catalogo_Diagramas`, porque ahora el contenido es line art generado y no una fotografía. El `design.md` vigente todavía nombra `fotos_tecnica.py` y `FotoTecnica`: la actualización del diseño debe renombrar el módulo a `diagramas_postura.py` y reconciliar las 17 propiedades de corrección con los requisitos 14 a 20.
- **Por qué los diagramas se generan desde Python.** El Requisito 14 exige trazo uniforme de 2 px en `--azul-profundo`, etiquetas como elementos `<text>` reales, línea guía en `--azul-linea` con punto sólido en el extremo, flechas punteadas en `--coral-alerta`, línea media con punto de centro de gravedad y fases numeradas que coinciden con los pasos del texto. Eso no se obtiene recoloreando un raster ajeno, y el proyecto es stdlib puro (no hay Pillow). Generarlo desde Python cumple todo por construcción, escala nítido a 360 px, permite que las pruebas verifiquen la geometría y deja el build con **cero red en todas las fases**.
- **Requiere_Archivo en falso hoy (criterio 5.2).** Las ocho entradas tienen respaldo del Generador_SVG, así que ninguna es obligatoria y el build estricto llega a `[PUBLICABLE]` sin que la usuaria coloque un solo archivo. El campo y el mecanismo quedan especificados para cuando se agreguen fotografías reales.
- **El Modo_Muestra ya no deja huecos.** El criterio 5.5 sustituye la conducta anterior (omitir el `<figure>` cuando faltaba el archivo): ahora siempre hay figura, porque hay respaldo generado.
- **Paleta cerrada y el degradado del hero.** El criterio 6.1 cambia el final del degradado de `#7EC8FF` a `--azul-medio` (`#B8DCFA`), porque `#7EC8FF` es un azul saturado y queda fuera de la Paleta_Guia. `WEB_AZUL_CLARO` se conserva sin cambios y se usa solo en las aristas, los acentos y el halo del visor 3D (criterios 16.17 y 16.18), nunca como fondo.
- **Unificación de tokens (criterio 16.2).** `WEB_HERO_CIELO` **es** `--azul-cielo` y `WEB_HERO_TINTA` **es** `--azul-profundo`. Hay una sola constante de Python por color; no se declara un segundo nombre con el mismo valor.
- **Contrastes medidos y sus consecuencias.** Con la función Contraste: `--azul-profundo` sobre `--azul-cielo` da 11.6:1, sobre `--azul-medio` 9.6:1 y sobre `--blanco-suave` 12.6:1, todos por encima de 4.5. `--azul-linea` sobre `--azul-cielo` da 4.6:1. En cambio `--rosa-acento` sobre `--azul-cielo` da 2.7:1 y `--coral-alerta` sobre `--azul-cielo` da 4.1:1: por eso el rosa queda restringido a elementos gráficos y texto grande (16.10) y el texto de error en coral solo va sobre `--blanco-suave`, donde da 4.7:1 (16.13). El coral sí cumple el umbral de 3:1 como flecha de diagrama. El Modo_Oscuro (`#DCEEFF` sobre `#0B1F33`) da 14.1:1.
- **Navegación fija abajo con `position:sticky` (criterio 15.20).** La navegación inferior se resuelve con `position:sticky` y `bottom:0`, nunca con `position:fixed`, que en el navegador incrustado de Android pelea con el desplazamiento de una superficie de lectura. La prohibición de `position:fixed` era global; el criterio 28.5 la acota ahora al **único** selector del overlay modal del Visor_Ampliado, y `test_arte_futurista::test_visor_por_z_index_nunca_position_fixed` lo mide por conteo y por selector.
- **`anatomia-base` y el límite de etiquetas.** Esa entrada declara 16 Etiqueta_Anatomica, por encima del límite de 8 del criterio 15.18. El criterio 15.19 es la salida: sus etiquetas se emiten fuera del contorno, unidas por línea guía, y con una Zona_Tactil que amplía el diagrama a pantalla completa. Va primera en la guía porque enseña las palabras que usan los otros siete diagramas (criterios 2.2 y 14.16).
- **Créditos como texto (criterios 1.8 y 18.5).** Los enlaces del Bloque_Creditos se emiten como texto visible, no como `<a href>`, así que la cadena `http` aparece sin provocar ninguna petición de red y el Guardarrail_Recursos la acepta en ese contexto.
- **Ajuste medido del criterio 30.9 (tarea 14.2).** Al ampliar el Guardarrail_Recursos sobre el Target_Web real apareció un tercer contexto de texto visible con `http` que la redacción anterior ("únicamente como texto visible dentro del Bloque_Creditos") dejaba fuera: los enlaces de video de las 58 fichas se **rotulan con su propia URL**, así que el `http` vive en el nodo de texto del `<a>`, no solo en su `href`. Es el mismo caso de navegación que el criterio ya acepta en el atributo, y quitarlo obligaría a esconder la dirección que la usuaria decide abrir. El criterio 30.9 pasa a aceptar el texto visible dentro del Bloque_Creditos **o** como rótulo de un enlace de navegación, y a rechazarlo en cualquier otro nodo de texto: un `http` en la prosa suelta sigue siendo un fallo.
- **Dónde más aparece `http` sin ser Recurso_Externo (criterios 1.2 y 1.8).** El Guardarrail_Recursos mide la cadena `http` **por contexto**, no por conteo global del documento: el Target_Web trae hoy 147 apariciones en el `xmlns` de los `<svg>` en línea heredados (`viz.py`, `build_html.py` del QR y `escena3d.py`), que es una declaración de espacio de nombres y no descarga nada, y 134 en el `href` de los enlaces de video de las 58 fichas, que son navegación que la usuaria decide y no un subrecurso que el documento cargue solo. Lo que el guardarraíl prohíbe es la cadena en un atributo `src`, en un `href` de hoja de estilo, en la Hoja_Estilo y en el Script_Unico. Los `<svg>` que esta spec añade (Generador_SVG, Proyector_Vistas y Mundo_Hero) no llevan `xmlns` (criterio 14.15).
- **Frontera con la Spec_Pizarra.** El punto 4 de la estructura (leyenda de símbolos), la parte de "diagramas de ejercicio con su ficha" del punto 5 y el punto 6 (rutina semanal) pertenecen a la Spec_Pizarra: diagramas de pizarra táctica vistos desde arriba, leyenda de símbolos, fichas de ejercicio y rutina semanal. Esta spec deja el ancla y el hueco de Seccion_Reservada (criterios 19.6 y 19.7) y define los cimientos compartidos: Paleta_Guia, Modo_Oscuro, restricciones de celular, whitelist de assets y CSS base. El contenido de esas secciones **no** se especifica aquí.
- **Aclaración del Requisito 16 de la spec previa.** Los criterios 16.1, 16.8, 16.9 y 16.10 siguen vigentes y esta spec los detalla. La lectura correcta de "cero recursos externos" es la del Requisito 1 de este documento: los Asset_Local con ruta relativa están permitidos; lo prohibido es cualquier petición de red.
- **Elementos del fondo del hero.** Se generan como SVG en línea desde Python, no como archivos binarios. Así el hero no depende de ningún asset que la usuaria deba colocar, y el desvanecimiento y el giro salen gratis.
- **Pausa del bucle (criterios 10.8 y 10.9).** El bucle único solo se detiene cuando el hero está fuera de la ventana **y** el documento está oculto. Para no gastar batería mientras el hero está fuera de pantalla con el documento visible, el criterio 10.9 exige que el bucle no dibuje ni escriba estilos en ese estado, que es la conducta que hoy ya tiene el visor 3D.
- **Interacción táctil sin romper la accesibilidad (criterios 9.8 y 9.9).** El escuchador de toque vive en el contenedor del hero, no en los Elemento_Fondo: así el criterio 11.2 (`pointer-events:none` en el Mundo_Hero y en todos sus descendientes) y el 11.3 quedan intactos, y el balón más cercano se resuelve con las coordenadas declaradas del catálogo.
- **Resoluciones de la revisión.** Los cuatro Fundamento son un conjunto cerrado: cualquier Fundamento extra del catálogo se omite y se registra (3.9). El catálogo puede declarar dimensiones distintas para el archivo y para el SVG generado, y se emiten las del modo de render efectivo (4.8). `will-change` se retira en cuanto el Progreso_Scroll alcanza 1 (10.7). El bloque `@media print` gana sobre Movimiento_Reducido y oculta el Mundo_Hero (11.7). El límite de 768 px parte el comportamiento sin zona gris: 768 o más para el hero completo (7.1), menos de 768 para la degradación y la navegación inferior pegada (12.1 a 12.6, 15.20). Las 58 fichas se conservan tal cual (13.7, 13.8). La numeración de fases degrada emitiendo las fases restantes y registrando la omitida en vez de abortar (14.17). Los créditos incompletos se publican con la marca "dato pendiente" y se registran (18.8, 18.9).
- **Fuera de alcance.** El árbol `publicacion/` (landing de GitHub Pages y copia del sitio multi-archivo) y el PDF no cambian: los Diagrama_Postura viven solo en el Target_Web.

## Notas de la ampliación (Requisitos 21 a 30)

- **Por qué diez vistas y no un `rotateY`.** Un `rotateY` sobre un SVG plano no gira el cuerpo: al pasar los 90 grados se ve el mismo dibujo espejeado, nunca la espalda. Como el esqueleto ya es paramétrico, la vuelta real sale de rotar el Esqueleto_3D y proyectarlo. El `rotateY` se conserva, pero solo como Rotacion_Residual de ±22.5 grados entre dos vistas contiguas, que es lo que hace imperceptible el salto (criterios 25.10 y 25.11).
- **La invariancia de hueso se mide en 3D, nunca en la proyección.** Es el punto que más fácil se rompe al implementar. El criterio 14.18 fija la medida sobre las tres coordenadas del Esqueleto_3D rotado, con tolerancia 1e-6, y el 14.19 declara explícitamente que la longitud sobre el SVG emitido **no** es constante: el Escorzo la acorta con el coseno del ángulo (criterio 21.7). La Property 5 del `design.md` sigue válida palabra por palabra si su medida se lee en el Esqueleto_3D; la actualización del diseño debe decirlo con esas palabras y añadir la propiedad del Escorzo. Cualquier prueba que mida longitudes sobre el SVG resultante y exija constancia está mal escrita.
- **El volumen sale del orden de dibujo, no de un motor 3D.** Los cuatro grupos en orden fijo (`miembros-traseros`, `tapa-torso`, `torso`, `miembros-delanteros`) con `stroke-opacity` 0.55 en los traseros son todo el truco (Requisito 24). El desempate de profundidad 0 hacia Miembro_Delantero (criterio 21.10) existe para que la emisión sea determinista byte a byte también en las vistas frontal y de espalda, donde la profundidad de los hombros vale 0.
- **La Tapa_Torso no contradice el criterio 14.5.** El relleno de la silueta sigue siendo `--azul-cielo` al 0.12; la Tapa_Torso es un elemento distinto y opaco cuyo único trabajo es ocultar los Miembro_Trasero (criterios 14.20 y 24.4). Con 0.12 de opacidad el torso no taparía nada y el volumen se perdería.
- **Cero inserción de nodos.** Las diez Vista_Figura se emiten desde Python y viven en el DOM desde el primer fotograma (criterios 22.6 y 22.8). La conmutación toca `opacity` y `visibility` de exactamente dos elementos y solo cuando el índice de vista cambia (criterios 25.8 y 25.9). El criterio 25.12 prohíbe por nombre `innerHTML`, `createElement`, `appendChild` y compañía, así que la prohibición es verificable sobre el texto del Script_Unico.
- **Presupuesto de bytes: el campo Girable.** Diez vistas por figura multiplican rápido. Con las tres siluetas del hero más `anatomia-base` el total queda en 40 Vista_Figura y en 6144 bytes por vista como techo (criterios 22.13 y 22.5). Emitir las diez vistas de los ocho diagramas serían 110 vistas y unos cientos de kilobytes en un solo archivo autocontenido, contra el presupuesto de 3000 ms hasta interactivo del criterio 15.15. La salida es declarativa: `Girable` es un campo del catálogo y activarlo en más entradas no cuesta código. **Si prefieres las diez vistas en los siete gestos técnicos desde el principio, dilo y se cambia el criterio 22.5**; el resto de los requisitos no se mueve.
- **El `visibility` y la pausa contra el criterio 10.3.** El criterio 10.3 permitía solo `transform` y `opacity` en línea. Queda actualizado para admitir `visibility`, que no dispara maquetación y se escribe una vez por cambio de vista, no por fotograma. La pausa de animaciones **no** se escribe en línea: se alterna la clase de Modo_Inerte y el `animation-play-state:paused` vive en la Hoja_Estilo (criterios 10.16 y 27.9). Así nada consume GPU con el fondo invisible y el `box-shadow` sigue prohibido (la Sombra_Contacto es un `<ellipse>` escalado por `transform`, criterio 25.15).
- **Movimiento reducido y el arrastre.** Con `prefers-reduced-motion: reduce` se congela todo el movimiento automático y la Vista_Activa queda en `az-000` (criterios 11.8 y 11.9). El Arrastre_Rotacion sí se conserva (criterio 28.18), porque ese movimiento lo inicia la usuaria con el dedo y quitarlo dejaría sin la interacción principal a quien pide menos animación. **Si quieres que también se congele, se cambia el criterio 28.18.**
- **El ancla manda, el arrastre mejora.** La ampliación sigue siendo un enlace de ancla a `#<id>-ampliada` con `:target`, sin JavaScript y sin `position:fixed` (criterios 28.4 a 28.6). El Arrastre_Rotacion es mejora progresiva encima de esa base, con `touch-action:none` en el visor y escuchadores pasivos que solo guardan coordenadas (criterios 28.13 y 28.14).
- **Los seis azimuts de móvil.** `Subconjunto_Azimuts_Movil` conserva `(0, 45, 90, 180, 270, 315)`: se cae el par de tres cuartos dorsales, que es el menos legible en pantalla pequeña, y el subconjunto queda simétrico respecto del eje frontal. La escalera de degradación es fija: primero menos figuras de fondo, después seis azimuts en móvil, y los diagramas técnicos nunca (criterios 29.4 a 29.6). El fondo es adorno; los diagramas son el contenido.
- **Whitelist de extensiones.** El Requisito 30 concentra la decisión en una sola función, el Validador_Rutas, con las cuatro Extensiones_Permitidas y el rechazo de `http://`, `https://`, `//`, `/` y `..`. El criterio 1.3 pasa a delegar en esa función y el 1.10 la extiende a toda referencia de recurso, no solo a los `<img>`. Las prohibiciones vigentes de `<link>` a hoja de estilo, `@import`, `src="http` y la subcadena `//` en el Script_Unico quedan intactas (criterios 30.8 y 30.9).
- **Lo que sigue sin ser observable desde Python.** Los fotogramas por segundo reales con limitación de procesador de cuatro veces siguen siendo comprobación manual (criterio 29.13). Lo que la suite prueba es el contrato: diez vistas por figura con sus `data-vista`, orden de los cuatro grupos, `stroke-opacity` 0.55 en los traseros, marcas propias de `az-180`, `el-p60` y `el-m60`, longitudes de hueso en 3D, Escorzo por coseno, una sola llamada a `requestAnimationFrame`, ausencia de `innerHTML` y compañía, presencia de `visibility:hidden` y de `animation-play-state:paused`, y bytes idénticos entre dos emisiones.
- **Estado del código que esta ampliación no debe romper.** La suite está en 504 pruebas en verde con `python _run_tests.py`. `svg_postura.py` ya tiene el esqueleto de 17 articulaciones, los 16 huesos, las 8 poses, los dos modos de etiqueta y la zona de ampliación; el Proyector_Vistas se añade **encima** de eso, sin cambiar la firma de `esqueleto(...)` ni las longitudes declaradas. El nombre `src/guia/rotacion.py` ya está tomado por la rotación de jugadoras del plan semanal, así que el módulo nuevo es `src/guia/vistas_figura.py`.
