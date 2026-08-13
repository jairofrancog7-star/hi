# -*- coding: utf-8 -*-
"""Contenido de la guía: fichas de entrenamiento, láminas y enlaces."""

YT = 'https://youtu.be/'
BUSCA = 'https://www.youtube.com/results?search_query='

V = {
    'fifa': YT + 't8h12fy3aAw',
    'fifa2': YT + 'RSJIp7e7fyY',
    'sola': YT + 'bPqqiwOdK8w',
    'crono': YT + 'Ds4oK9H3qz8',
    'pared': YT + 'UB3oV92oYmw',
    'control': YT + 'sa5OgNkDlWo',
    'pases7': YT + 'QpLZ2VbBN0o',
    'pasesEq': YT + 'B54zwtpqTc0',
    'uno': YT + 'c7FKovc68rE',
    'cond': YT + '8sM1Dg1SfRo',
    'tiro': YT + '7G50ToIfd7Q',
    'rondo1': YT + 'dKsjSQ3ICzs',
    'rondo2': YT + 'h3dz4PftVq0',
    'rondo3': BUSCA + 'rondos+y+juegos+de+posicion+futbol+entrenamiento',
    'linea': YT + 'wmW6KpKlHLU',
    'bloque': YT + 'sWDo_Ald7hg',
    'portera': YT + 'sW7Z7gwrjoc',
    'casa5': YT + '6yUeQeOZkAE',
    'regate': YT + 'S2sJSbZwwq4',
    'fifaweb': 'https://inside.fifa.com/es/health-and-medical/injury-prevention',
    'uwcl': 'https://www.uefa.com/womenschampionsleague/',
    'barca': 'https://www.fcbarcelona.es/es/futbol/futbol-femenino',
    'bpos': 'https://www.jlmartinsaez.com/ejercicios/conservacion/juego-de-posicion/',
    'porteras': 'https://porterasdefutbol.com/',
    'bcabeceo': BUSCA + 'como+cabecear+bien+el+balon+tecnica+futbol+tutorial',
    'bdefensa': BUSCA + 'como+defender+1+contra+1+futbol+tecnica+defensiva',
    'bcorner': BUSCA + 'jugadas+ensayadas+de+corner+futbol+entrenamiento',
    'bsalida': BUSCA + 'salida+de+balon+desde+portera+futbol+entrenamiento',
    'btrans': BUSCA + 'transiciones+rapidas+contraataque+futbol+entrenamiento',
    'bpresion': BUSCA + 'presion+tras+perdida+6+segundos+futbol+entrenamiento',
    'bcentro': BUSCA + 'ejercicios+de+centros+y+remate+futbol+femenino',
    'bfuerza': BUSCA + 'fuerza+en+casa+para+futbolistas+sin+material+piernas',
}

# ------------------------------------------------------------------ diagramas
D = {}

D['fifa'] = dict(kind='grid', w=34, h=14, pad=3.2, pr=1.5, items=[
    ('c', 3, 2), ('c', 11, 2), ('c', 19, 2), ('c', 27, 2),
    ('c', 3, 12), ('c', 11, 12), ('c', 19, 12), ('c', 27, 12),
    ('p', 3, 7, ''), ('run', 4.6, 7, 10.4, 11.4), ('run', 11.6, 11.4, 18.4, 2.6),
    ('run', 19.6, 2.6, 26.4, 11.4),
    ('t', 17, -1.7, 'ida y vuelta entre las marcas: nunca la rodilla hacia adentro', 1.05),
])

D['rondo'] = dict(kind='grid', w=18, h=18, pad=2.6, pr=1.6, items=[
    ('p', 2.6, 2.6, 1), ('p', 15.4, 2.6, 2), ('p', 15.4, 15.4, 3), ('p', 2.6, 15.4, 4),
    ('r', 9, 9), ('b', 4.6, 2.6),
    ('pass', 4.6, 2.6, 13.6, 2.6), ('pass', 15.4, 4.4, 15.4, 13.6),
    ('pass', 14.2, 14.2, 3.8, 3.8),
    ('t', 9, -1.5, 'la que la pierde se va al centro', 1.15),
])

D['posicion'] = dict(kind='grid', w=26, h=16, pad=2.6, pr=1.5, items=[
    ('p', 2.6, 2.6, 1), ('p', 23.4, 2.6, 2), ('p', 23.4, 13.4, 3), ('p', 2.6, 13.4, 4),
    ('p', 13, 8, 'C'), ('r', 9, 6), ('r', 17, 10.5), ('b', 4.4, 2.6),
    ('pass', 4.4, 3.4, 11.6, 7.4), ('pass', 14.4, 8.6, 22.2, 12.6),
    ('t', 13, -1.5, 'la comodín juega siempre con quien tiene el balón', 1.05),
])

D['salida'] = dict(kind='own', w=68, h=46, pad=3.4, pr=1.9, items=[
    ('gk', 34, 3.5, 1), ('p', 21, 12, 5), ('p', 47, 12, 4),
    ('p', 6, 26, 3), ('p', 62, 26, 2), ('p', 34, 21, 6),
    ('p', 24, 36, 8), ('p', 46, 36, 10),
    ('r', 28, 29), ('r', 40, 29), ('r', 34, 40), ('b', 34, 5.6),
    ('pass', 32.6, 5.4, 22.6, 11.2), ('pass', 20, 13.6, 7.4, 24.4),
    ('t', 34, -2.1, 'si presionan alto: largo a la BANDA, nunca al centro', 1.5),
])

D['transicion'] = dict(kind='half', w=68, h=56, pad=3.4, pr=1.9, items=[
    ('p', 24, 8, 8), ('p', 34, 17, 9), ('p', 58, 22, 7), ('p', 46, 34, 10),
    ('r', 29, 12), ('r', 41, 19), ('r', 30, 44), ('r', 41, 44), ('r', 34, 53, 'P'),
    ('b', 25.6, 8.8),
    ('pass', 25.6, 9.4, 32.6, 16), ('pass', 35.6, 17.8, 56.2, 21.4),
    ('run', 59.4, 23.6, 61, 41), ('pass', 60.4, 43, 48, 35),
    ('shot', 46, 36, 36, 54),
    ('t', 13, 10, 'máximo 3 toques', 1.5),
    ('t', 52, 46, '10 pica a la espalda', 1.5),
])

D['presion'] = dict(kind='grid', w=30, h=22, pad=2.8, pr=1.6, items=[
    ('r', 15, 16), ('b', 16.6, 15.4),
    ('p', 15, 10, 8), ('p', 8, 13, 11), ('p', 22, 13, 7), ('p', 15, 4, 6),
    ('run', 15, 11.6, 15, 14.2), ('run', 9.4, 13.6, 11.6, 15),
    ('run', 20.6, 13.6, 18.4, 15),
    ('t', 15, -1.6, 'seis segundos: si no la recuperamos, todas atrás', 1.15),
])

D['centro'] = dict(kind='half', w=68, h=40, pad=3.4, pr=1.9, items=[
    ('zone', 27, 21, 41, 28, 'zona del rechace'),
    ('p', 59, 25, 7), ('p', 38, 35, 9), ('p', 33, 30, 10), ('p', 27, 35, 11),
    ('p', 34, 24, 8),
    ('r', 34, 38, 'P'), ('r', 30, 36), ('r', 41, 36), ('r', 45, 32),
    ('b', 59, 26.6),
    ('drib', 60, 26.6, 62, 33), ('pass', 61.4, 34.4, 40, 35),
    ('shot', 38, 36.4, 34.6, 39.6),
    ('t', 14, 30, 'hasta línea de fondo', 1.5),
])

D['corner'] = dict(kind='half', w=68, h=36, pad=3.4, pr=1.9, items=[
    ('p', 66, 34.4, 6), ('b', 67, 35.4),
    ('p', 48, 25, 9), ('p', 46, 22, 10), ('p', 51, 20, 4),
    ('p', 28, 33, 11), ('p', 34, 24, 8),
    ('r', 34, 34.4, 'P'), ('r', 31, 32), ('r', 37, 32), ('r', 34, 29), ('r', 27, 31),
    ('run', 47.4, 26.4, 40, 31.4), ('run', 45.4, 23.4, 38, 30.4),
    ('run', 50, 21.4, 42, 32),
    ('pass', 64.4, 34.4, 41, 32),
    ('t', 53, 15, 'las 3 arrancan al mismo tiempo', 1.5),
    ('t', 16, 22, 'fija en el 2º palo', 1.5),
])

D['corner_c'] = dict(kind='own', w=68, h=28, pad=3.4, pr=1.8, items=[
    ('r', 67, 1.4, 'K'), ('b', 66, 2.4),
    ('gk', 34, 2.6, 1), ('p', 38, 3.6, 4), ('p', 34, 5.8, 5), ('p', 30, 5.4, 3),
    ('p', 26, 6, 2), ('p', 41, 7.6, 6), ('p', 24, 9.6, 11), ('p', 57, 4.6, 7),
    ('p', 33, 13.4, 8), ('p', 34, 23, 9),
    ('r', 36.6, 6), ('r', 31, 7.4), ('r', 28, 10.6), ('r', 45, 12),
    ('pass', 64.4, 2.2, 37, 5.6),
    ('run', 34, 24.6, 32, 27),
    ('t', 55, 20, 'despejar y salir: la 9 se queda arriba', 1.4),
])

D['uno'] = dict(kind='grid', w=20, h=26, pad=2.8, pr=1.7, items=[
    ('c', 7, 1.2), ('c', 13, 1.2),
    ('r', 10, 20), ('b', 11.4, 19),
    ('p', 10, 13, 5), ('p', 15, 8, 4),
    ('drib', 11, 18.4, 10.4, 15.4),
    ('run', 14.4, 8.8, 12.2, 11.6),
    ('t', 10, -1.7, 'de perfil y frena a dos pasos', 1.15),
])

D['basculacion'] = dict(kind='grid', w=44, h=16, pad=2.8, pr=1.5, items=[
    ('r', 40, 13), ('b', 41.4, 12.2),
    ('p', 8, 7, 3), ('p', 18, 7, 5), ('p', 28, 7, 4), ('p', 38, 7, 2),
    ('run', 9.6, 7, 13.4, 7), ('run', 19.6, 7, 23.4, 7),
    ('run', 29.6, 7, 33.4, 7), ('run', 39.4, 8.4, 40, 11),
    ('t', 22, -1.7, 'todas al lado del balón, como amarradas con una cuerda', 1.15),
])

D['cabeceo'] = dict(kind='grid', w=18, h=14, pad=2.8, pr=1.7, items=[
    ('p', 4, 5, 'A'), ('p', 14, 5, 'B'), ('b', 5.6, 6),
    ('pass', 5.8, 6.4, 12.2, 6.4), ('shot', 12.4, 3.6, 5.8, 3.6),
    ('t', 9, 11.6, 'frente, nunca la coronilla', 1.2),
    ('t', 9, -1.7, 'ojos abiertos hasta el contacto', 1.2),
])

D['tiro'] = dict(kind='wall', w=24, h=16, pad=3.4, pr=1.7, items=[
    ('target', 2.5, 16.2, 5, 2.0), ('target', 16.5, 16.2, 5, 2.0),
    ('p', 12, 3, 9), ('b', 12, 4.8),
    ('shot', 11.6, 5.2, 5.4, 16.2), ('shot', 12.6, 5.2, 18.6, 16.2),
    ('t', 12, -1.8, '10 con cada pie, a 12 pasos', 1.15),
])

D['pared'] = dict(kind='wall', w=20, h=14, pad=3.4, pr=1.7, items=[
    ('p', 10, 3.4, 'L'), ('b', 10, 5.2),
    ('pass', 8.8, 5.4, 8.8, 13.6), ('pass', 11.4, 13.6, 11.4, 5.6),
    ('t', 4.4, 9, '3 pasos', 1.2),
    ('t', 10, -1.8, 'pie relajado al recibir', 1.15),
])

D['sombra'] = dict(kind='grid', w=24, h=16, pad=2.8, pr=1.7, items=[
    ('c', 4, 3), ('c', 20, 3),
    ('p', 12, 8, 4),
    ('run', 10.4, 8, 5.4, 8), ('run', 13.6, 8, 18.6, 8),
    ('t', 12, -1.7, '5 metros de lado a lado, sin cruzar los pies', 1.15),
])

D['dos'] = dict(kind='grid', w=20, h=12, pad=2.8, pr=1.7, items=[
    ('p', 4, 6, 'A'), ('p', 16, 6, 'B'), ('b', 5.6, 6),
    ('pass', 5.8, 7, 14.2, 7), ('pass', 14.2, 5, 5.8, 5),
    ('t', 10, -1.7, 'devuelve a un toque y muévete', 1.15),
])

D['botin'] = dict(kind='blank', w=40, h=34, pad=1.5, items=[
    ('boot', 20, 17, 11, 26),
    ('mark', 15.4, 18, 8.6, 20.4, 'PASE', 1.35),
    ('mark', 16.4, 24.6, 8.6, 27.6, 'EFECTO', 1.35),
    ('mark', 20, 22, 31.4, 24.4, 'CAÑONAZO', 1.35),
    ('mark', 23.6, 26, 30, 29.4, 'TRES DEDOS', 1.35),
    ('mark', 20, 14.4, 31.4, 15.4, 'PLANTA', 1.35),
    ('mark', 20, 6.4, 28.6, 4.6, 'TACÓN', 1.35),
    ('mark', 20.6, 29.2, 9.6, 31.4, 'PUNTA: NO', 1.35),
])

# ------------------------------------------------------------------ fichas
DRILLS = [
    dict(n='01', cat='Prevención', team='Lo que usan las selecciones', dia='fifa',
         title='Calentar sin romperse',
         sub='FIFA 11+ · 15 a 20 minutos antes de cada sesión',
         idea='Las jugadoras se lesionan la rodilla mucho más seguido que los hombres, '
              'y este programa gratuito de la FIFA baja el riesgo cuando se hace siempre. '
              'No es opcional: es la ficha más importante de toda la guía.',
         steps=[
             'Seis marcas en dos hileras. Botellas con tierra, piedras o mochilas, separadas 5 o 6 pasos.',
             'Ocho minutos de carrera lenta: recta, cadera abierta, cadera cerrada, alrededor de la compañera, saltando y frenando.',
             'Diez minutos de fuerza: plancha, plancha lateral, nórdico de isquiotibiales asistido, equilibrio a una pierna, sentadilla y saltos.',
             'Dos minutos de carreras rápidas con giros y frenadas.',
         ],
         watch='La rodilla nunca se mete hacia adentro: al caer, al frenar y al girar. '
               'Al aterrizar de un salto no debe hacer ruido.',
         dose=[('Cuándo', 'Antes de todo'), ('Duración', '15 a 20 min'),
               ('Jugadoras', '1 o más'), ('Material', '6 botellas')],
         links=[('Video', 'FIFA 11+ explicado en español', V['fifa']),
                ('Video', 'Serie oficial de la FIFA, sin voz', V['fifa2']),
                ('Web', 'FIFA · prevención de lesiones', V['fifaweb'])],
         qr=V['fifa']),

    dict(n='02', cat='Posesión', team='Como abre cada entrenamiento el Barça', dia='rondo',
         title='Rondo 4 contra 1',
         sub='Cuatro afuera, una en el centro, cuadrado de 8 pasos',
         idea='El rondo es el ejercicio con el que los mejores equipos del mundo empiezan '
              'todos los días. Enseña las tres cosas que le faltan a una jugadora sin '
              'confianza: mirar antes, decidir rápido y pedir el balón.',
         steps=[
             'Cuadrado de 8 pasos. Una en cada lado y una en el centro.',
             'Primera ronda con toques libres. Segunda a dos toques. Tercera a un toque.',
             'Las de fuera se mueven sobre su línea para abrir el ángulo. No se quedan paradas.',
             'Se grita: nombre, sola, atrás, mía. La que pierde el balón pasa al centro.',
         ],
         watch='Que el primer toque salga hacia el espacio libre y no hacia los pies. '
               'Que la cabeza gire antes de que llegue el balón.',
         dose=[('Cuándo', 'Al inicio'), ('Duración', '12 a 15 min'),
               ('Jugadoras', '5 (o 3 y 4)'), ('Meta', '10 pases seguidos')],
         links=[('Video', 'Rondos en espacios reducidos', V['rondo2']),
                ('Video', 'Rondos y juegos de posición', V['rondo3']),
                ('Web', 'Banco de ejercicios de juego de posición', V['bpos'])],
         qr=V['rondo2']),

    dict(n='03', cat='Posesión', team='Juego de posición', dia='posicion',
         title='Cuatro contra dos con comodín',
         sub='Rectángulo de 12 × 8 pasos',
         idea='Cuando ya salen los 10 pases seguidos, se sube la presión. La comodín juega '
              'siempre con quien tiene el balón, así que siempre hay superioridad: se aprende '
              'a buscar a la que está libre en lugar de reventar el balón.',
         steps=[
             'Cuatro afuera, dos en el centro y una comodín que juega con quien tenga el balón.',
             'Un punto por cada seis pases seguidos.',
             'Si roban las del centro, entran las dos que perdieron el balón.',
             'Después de cinco minutos se limita a dos toques.',
         ],
         watch='Que nadie se esconda detrás de una rival. El pase corto casi nunca falla; '
               'el pase largo de apuro casi siempre se pierde.',
         dose=[('Cuándo', 'Martes'), ('Duración', '4 rondas de 4 min'),
               ('Jugadoras', '6 o 7'), ('Meta', '6 pases seguidos')],
         links=[('Video', 'Rondos 4v2 y 5v2', V['rondo1']),
                ('Video', 'Pase y recepción en equipo', V['pasesEq'])],
         qr=V['rondo1']),

    dict(n='04', cat='Salida', team='Salida jugada', dia='salida',
         title='Salir jugando desde la portera',
         sub='Portera corto, centrales abiertas, laterales arriba',
         idea='Una portera que juega con los pies es una ventaja enorme y casi ningún equipo '
              'de esta categoría la aprovecha. El primer pase siempre al piso y a la que está sola.',
         steps=[
             'Las centrales se abren a los vértices del área grande. Las laterales suben a la altura del mediocampo.',
             'La 6 se ofrece entre líneas, de perfil, nunca de espaldas a la portería rival.',
             'Portera a central, central a la 6 o a la lateral. Dos toques y sale.',
             'Si Roque presiona alto, la portera manda largo a la banda, nunca al centro.',
         ],
         watch='Que la que recibe voltee antes. Que la portera no reviente el balón por miedo.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '15 min'),
               ('Jugadoras', '6 a 11'), ('Meta', '8 salidas limpias de 10')],
         links=[('Video', 'Guía completa de portera', V['portera']),
                ('Web', 'Porteras de fútbol', V['porteras']),
                ('Buscar', 'Salida de balón desde la portera', V['bsalida'])],
         qr=V['portera']),

    dict(n='05', cat='Transición', team='La especialidad del Lyon', dia='transicion',
         title='Tres toques y a la banda',
         sub='Lo que se hace en los primeros segundos tras robar',
         idea='En esta categoría los espacios tras pérdida son enormes y ahí caen la mitad de '
              'los goles. El equipo que recupera y sale rápido gana partidos que no merecía.',
         steps=[
             'Al robar: máximo tres toques antes de que el balón vaya hacia adelante.',
             'Una delantera viene de cara a recibir y la otra pica a la espalda de las centrales.',
             'El balón sale a la banda y la volante corre con él hasta el fondo.',
             'Centro raso al primer poste. Nadie se queda mirando.',
         ],
         watch='Que la que roba levante la cabeza antes de controlar. Que las delanteras arranquen '
               'en el momento del robo, no después.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '20 min'),
               ('Jugadoras', '6 a 11'), ('Meta', '10 salidas en 12 segundos')],
         links=[('Buscar', 'Transiciones rápidas y contraataque', V['btrans']),
                ('Web', 'Women\u2019s Champions League', V['uwcl'])],
         qr=V['btrans']),

    dict(n='06', cat='Presión', team='Los seis segundos', dia='presion',
         title='Presión de seis segundos',
         sub='Qué hacer justo después de perder el balón',
         idea='Perder el balón no es el problema: el problema es lo que se hace en los seis '
              'segundos siguientes. Una va al balón y las demás tapan los pases, no persiguen.',
         steps=[
             'La más cercana va al balón y lo orienta hacia la banda.',
             'Las dos de al lado no corren detrás: tapan el pase hacia adelante y hacia atrás.',
             'Se cuenta hasta seis en voz alta. Si no se recupera, todas atrás al bloque.',
             'Se ensaya con la rival empezando en distintas zonas del campo.',
         ],
         watch='Que nadie se lance al piso. Que la presión sea de dos, no de una sola corriendo sola.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '15 min'),
               ('Jugadoras', '5 a 10'), ('Meta', 'Recuperar 6 de 10')],
         links=[('Buscar', 'Presión tras pérdida', V['bpresion']),
                ('Video', 'Bloque bajo y defensa del área', V['bloque'])],
         qr=V['bpresion']),

    dict(n='07', cat='Ataque', team='Centro y rechace', dia='centro',
         title='Centro al área y rechace',
         sub='Tres entran, una se queda para el rebote',
         idea='Cuando la volante llega a línea de fondo quiere ver tres: primer poste, punto de '
              'penal y segundo palo. Y una rezagada al borde del área, porque ahí cae la mitad '
              'de los goles de esta categoría.',
         steps=[
             'La volante conduce hasta línea de fondo, no antes.',
             'Centro raso y fuerte al primer poste. Los centros altos al centro los toma la portera.',
             'Tres rematadoras entran a la vez a primer poste, punto de penal y segundo palo.',
             'Una espera fuera del área para el rechace. Ahí se marca sin oposición.',
         ],
         watch='Que nadie entre antes que el balón. Que la del rechace no entre al área.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '20 min'),
               ('Jugadoras', '5 a 11'), ('Meta', '15 centros por lado')],
         links=[('Buscar', 'Centros y remate en fútbol femenino', V['bcentro']),
                ('Video', 'Conducción, pase y finalización', V['cond'])],
         qr=V['bcentro']),

    dict(n='08', cat='Balón parado', team='Como Arsenal y Chelsea', dia='corner',
         title='Córner ensayado a favor',
         sub='Tres juntas arrancan al primer poste',
         idea='Casi ningún equipo de esta categoría ensaya el balón parado. El que lo hace roba '
              'goles gratis. Es el arma más segura que tienen y sale de memoria, no de talento.',
         steps=[
             'Nadie se mueve hasta que la que cobra levanta la mano.',
             'Tres arrancan al mismo tiempo desde el punto de penal hacia el primer poste.',
             'Una queda fija en el segundo palo y otra fuera del área para el rechace.',
             'Dos se quedan atrás por si el rechace se convierte en contragolpe.',
         ],
         watch='Que las tres arranquen juntas, no en fila. Que el centro vaya al primer poste, '
               'a la altura de la cabeza.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '15 min'),
               ('Jugadoras', '7 a 11'), ('Meta', '10 córners ensayados')],
         links=[('Buscar', 'Jugadas ensayadas de córner', V['bcorner']),
                ('Video', 'Trabajo de línea defensiva', V['linea'])],
         qr=V['bcorner']),

    dict(n='09', cat='Balón parado', team='Marca en zona', dia='corner_c',
         title='Córner en contra',
         sub='Cada una tiene un sitio, no una rival',
         idea='En zona nadie se pierde persiguiendo. Cada una defiende un espacio, la más alta '
              'va al primer poste y siempre hay una fuera del área para el rechace.',
         steps=[
             'La más alta al primer poste. Una tapa el córner corto.',
             'Cuatro reparten la línea del área chica y no se mueven de su zona.',
             'Una espera en el borde del área: el rechace es nuestro.',
             'Al despejar, salimos rápido. La 9 se queda arriba de referencia.',
         ],
         watch='Que nadie mire el balón de espaldas a su zona. Que la portera grite «mía» fuerte.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '10 min'),
               ('Jugadoras', '8 a 11'), ('Meta', '10 córners defendidos')],
         links=[('Video', 'Bloque bajo y defensa del área', V['bloque']),
                ('Buscar', 'Jugadas de córner', V['bcorner'])],
         qr=V['bloque']),

    dict(n='10', cat='Defensa', team='Uno contra uno', dia='uno',
         title='Uno contra uno con cobertura',
         sub='Pasillo de 10 × 8 pasos',
         idea='Defender es una técnica, no valentía. De frente te ganan la carrera siempre; '
              'de perfil mandas tú. Y nunca estás sola: detrás hay una compañera cubriendo.',
         steps=[
             'La atacante intenta cruzar la línea final. La defensora la espera, no la va a buscar.',
             'Últimos pasos cortos y frenando. Cuerpo de lado, nunca de frente.',
             'Se orienta hacia la línea, no hacia el centro.',
             'La tercera jugadora hace la cobertura en diagonal, dos pasos por detrás.',
         ],
         watch='Que no se tire al piso. Que entre solo cuando la rival toca el balón largo o baja la mirada.',
         dose=[('Cuándo', 'Jueves'), ('Duración', '20 min'),
               ('Jugadoras', '2 a 6'), ('Meta', 'Ganar 5 de 10 duelos')],
         links=[('Video', 'Ejercicios para mejorar el 1 contra 1', V['uno']),
                ('Buscar', 'Cómo defender el 1 contra 1', V['bdefensa'])],
         qr=V['uno']),

    dict(n='11', cat='Defensa', team='Línea de cuatro', dia='basculacion',
         title='Basculación de la línea',
         sub='Todas al lado del balón',
         idea='La central no corre sin sentido: la central piensa, ordena y bascula. Si la línea '
              'se mueve junta, no hacen falta piernas rápidas, hace falta cabeza.',
         steps=[
             'Las cuatro se mueven juntas hacia el lado del balón, como amarradas con una cuerda.',
             'La central del lado del balón sale a presionar; la otra cierra el centro.',
             'Nunca más de 15 metros entre la línea de atrás y la de medio.',
             'Se empieza caminando, luego trotando y solo al final a velocidad.',
         ],
         watch='Que nadie se quede rezagada regalando el fuera de juego. Que la central hable en todo momento.',
         dose=[('Cuándo', 'Martes'), ('Duración', '15 min'),
               ('Jugadoras', '4 a 8'), ('Meta', '10 basculaciones limpias')],
         links=[('Video', 'Trabajo de línea defensiva', V['linea']),
                ('Video', 'Bloque bajo', V['bloque'])],
         qr=V['linea']),

    dict(n='12', cat='Técnica', team='Cabeceo', dia='cabeceo',
         title='Cabeceo progresivo',
         sub='La parte que da miedo y por eso nadie entrena',
         idea='Medir 1.50 o 1.60 no descalifica de nada: en el balón aéreo gana quien salta antes '
              'y quien se coloca mejor, no quien es más alta. Se aprende en tres sesiones.',
         steps=[
             'Sentadas, balón poco inflado, solo el gesto de la frente. 15 repeticiones. No duele.',
             'De pie, la compañera lanza suave con las manos. 15 repeticiones.',
             'Balón normal de pie, 15. Después saltando con impulso de un pie, 15.',
             'Por último con una compañera al lado haciendo oposición ligera, 10.',
         ],
         watch='Frente y nunca la coronilla. Ojos abiertos hasta el contacto. Tú le pegas al balón, '
               'no el balón a ti.',
         dose=[('Cuándo', 'Martes'), ('Duración', '15 min'),
               ('Jugadoras', '2'), ('Meta', '60 cabeceos limpios')],
         links=[('Buscar', 'Técnica de cabeceo', V['bcabeceo']),
                ('Video', 'Salto y prevención', V['fifa2'])],
         qr=V['bcabeceo']),

    dict(n='13', cat='Técnica', team='Definición', dia='tiro',
         title='Tiro al cuadro',
         sub='Con una barda y un gis, sin portería',
         idea='Casi ninguna jugadora de este nivel ha recibido una sola corrección de tiro en su '
              'vida. Es donde más rápido se ve la mejora, y los goles son de colocación, no de fuerza.',
         steps=[
             'Marcar dos cuadros de un metro en la barda, en las esquinas de abajo.',
             'Pie de apoyo al lado del balón apuntando al cuadro. Cuerpo ligeramente encima.',
             'Golpe con el empeine, donde van las agujetas. Nunca con la punta.',
             '20 tiros: 10 con la derecha y 10 con la izquierda, desde 12 pasos. Anotar cuántos entran.',
         ],
         watch='Que la pierna acompañe el golpe hacia adelante y no se frene. Si la manda al cielo, '
               'el pie de apoyo iba atrás.',
         dose=[('Cuándo', 'Diario'), ('Duración', '15 min'),
               ('Jugadoras', '1 o más'), ('Meta', '10 de 20 al cuadro')],
         links=[('Video', 'Ejercicios para mejorar los disparos', V['tiro']),
                ('Video', '5 ejercicios de técnica en casa', V['casa5'])],
         qr=V['tiro']),

    dict(n='14', cat='Técnica', team='La pared', dia='pared',
         title='Técnica con la pared',
         sub='Veinte minutos valen más que una reta entera',
         idea='La pared nunca falla, nunca se cansa y siempre devuelve el balón. Es la mejor '
              'compañera de entrenamiento que existe y no cobra nada.',
         steps=[
             'A 3 pasos de la pared: pase con la parte interna y recepción con el pie relajado. 3 series de 20 por pie.',
             'Un solo toque: pasa y devuelve sin controlar. 2 series de 15 por pie.',
             'Control orientado: recibe y en el mismo toque llévalo a la derecha; repite a la izquierda. 3 series de 10 por lado.',
             'Voltea antes: gira la cabeza a un lado antes de que el balón te llegue. 20 repeticiones.',
         ],
         watch='Pie tieso al recibir es el error número uno. Mirar solo el balón es el número dos.',
         dose=[('Cuándo', 'Diario'), ('Duración', '20 min'),
               ('Jugadoras', '1'), ('Meta', '45 pases en un minuto')],
         links=[('Video', 'Solo necesitas una pared', V['pared']),
                ('Video', 'Control orientado', V['control']),
                ('Video', 'Guía completa para entrenar sola', V['sola'])],
         qr=V['pared']),

    dict(n='15', cat='Técnica', team='Zonas del pie', dia='botin',
         title='Con qué parte le pegas',
         sub='El mismo balón, siete resultados distintos',
         idea='Casi todos los errores de pase y de tiro son de superficie de contacto: le pegan '
              'con la punta. Esta lámina es para pegarla en la pared del cuarto y verla todos los días.',
         steps=[
             'Interior (PASE): la superficie más segura. Firme, raso y al pie. Es el 80% de los pases del partido.',
             'Empeine (CAÑONAZO): donde van las agujetas. Para tiro y pase largo. Se acompaña el movimiento.',
             'Tres dedos: pase largo cruzado y centro con caída. Contacto abajito del balón.',
             'Interior alto (EFECTO): para rodearla en un tiro libre o un centro que se cierra.',
             'Planta: para frenar el balón y para el pase de tacón hacia atrás en el área.',
             'Punta: nunca. No hay control ninguno. Es el error más común de esta categoría.',
         ],
         watch='Antes de pegarle, el pie de apoyo apunta a donde va el balón. Ese detalle solo '
               'arregla la mitad de los pases malos.',
         dose=[('Cuándo', 'Siempre'), ('Duración', '5 min de lectura'),
               ('Jugadoras', '1'), ('Meta', 'Saber cuál usar sin pensar')],
         links=[('Video', '7 ejercicios de pases y controles', V['pases7']),
                ('Video', 'Técnica individual y regate', V['regate'])],
         qr=V['pases7']),
]

# ------------------------------------------------------------------ semana
SEMANA = [
    ('Lunes', 'Descanso o rutina suave en casa', 'Ligera'),
    ('Martes', 'Ficha 01 · 02 · 12: técnica y posesión', 'Media alta'),
    ('Miércoles', 'Casa: fuerza y core 25 min · ficha 14', 'Media'),
    ('Jueves', 'Ficha 01 · 05 · 07 · 10 · 13: duelos y gol', 'Alta'),
    ('Viernes', 'Activación corta. Nada de fuerza pesada', 'Muy ligera'),
    ('Sábado', 'PARTIDO', 'Competencia'),
    ('Domingo', 'Caminar, estirar, dormir', 'Nula'),
]

MENU = [
    ('1', 'Fichas 13, 14 y 15 · fuerza en casa', 'Pared, botellas y 20 tiros'),
    ('2', 'Fichas 12 y 14 · duelos', 'Pared humana y 10 duelos cada una'),
    ('3', 'Rondo 2v1 y tercer hombre', 'Ficha 02 reducida'),
    ('4', 'Rondo 3v1 y 2 contra 2', 'Fichas 02 y 10'),
    ('5', 'Rondo 4v1 completo', 'Fichas 02, 10 y 13'),
    ('6 a 8', 'Fichas 03, 06 y 07', '4v2, presión y centros'),
    ('9 a 11', 'Fichas 04, 05, 08 y 09', 'Partido y balón parado'),
]

CORRECCION = [
    ('1', 'Recibir', 'Pie relajado y balón cerca'),
    ('2', 'Mirar', 'Girar la cabeza antes de recibir'),
    ('3', 'Hablar', 'Sola, atrás, mía, sube, baja, cierra'),
    ('4', 'Moverse', 'Pasar y volver a ofrecerse'),
    ('5', 'Defender', 'Perfil, freno, banda, no barrerse'),
    ('6', 'Definir', 'Apoyo al lado, cuerpo encima, tiro bajo'),
]

# ------------------------------------------------------------------ láminas
POSTERS = [
    dict(tag='GUÍA VISUAL', title='ENTRENA COMO\nLAS GRANDES', kind='cover',
         sub='Sub-17 femenil · 15 ejercicios con dibujo',
         index=[d['n'] + ' · ' + d['title'] for d in DRILLS],
         qr=V['sola'], qrlabel='Empieza por este video'),

    dict(tag='LÁMINA 01', title='RONDO 4 CONTRA 1', dia='rondo',
         sub='Con lo que abre cada entrenamiento el Barça',
         points=[('Cuadrado de 8 pasos.', 'Una en cada lado y una en el centro.'),
                 ('Primero libre, luego dos toques, luego uno.', 'En ese orden.'),
                 ('Muévete sobre tu línea.', 'Parada no te llega el balón.'),
                 ('Grita.', 'Sola, atrás, mía. La defensa que habla vale doble.'),
                 ('La que la pierde', 'se va al centro.')],
         qr=V['rondo2'], qrlabel='Rondos en espacios reducidos'),

    dict(tag='LÁMINA 02', title='SALIR JUGANDO', dia='salida',
         sub='La portera con los pies es una ventaja enorme',
         points=[('Centrales a los vértices del área.', 'Bien abiertas.'),
                 ('La 6 se ofrece entre líneas.', 'De perfil, nunca de espaldas.'),
                 ('Primer pase al piso', 'y a la que está sola.'),
                 ('Si presionan alto:', 'largo a la BANDA, nunca al centro.'),
                 ('Dos toques y sale.', 'No la reventamos por miedo.')],
         qr=V['portera'], qrlabel='Guía completa de portera'),

    dict(tag='LÁMINA 03', title='TRES TOQUES\nY A LA BANDA', dia='transicion',
         sub='Lo que se hace justo después de robar',
         points=[('Máximo tres toques', 'antes de que el balón vaya adelante.'),
                 ('Una viene de cara,', 'la otra pica a la espalda de las centrales.'),
                 ('El balón a la banda', 'y a correr con él hasta el fondo.'),
                 ('Centro raso al primer poste.', 'Nadie se queda mirando.'),
                 ('Aquí caen la mitad', 'de los goles de la categoría.')],
         qr=V['btrans'], qrlabel='Transiciones y contraataque'),

    dict(tag='LÁMINA 04', title='SEIS SEGUNDOS', dia='presion',
         sub='Perder el balón no es el problema',
         points=[('Una va al balón', 'y lo orienta a la banda.'),
                 ('Las de al lado no persiguen:', 'tapan los pases.'),
                 ('Contamos hasta seis en voz alta.', 'Si no sale, todas atrás.'),
                 ('Nadie se tira al piso.', 'De pie se roba más.'),
                 ('Presión de dos,', 'nunca de una sola corriendo sola.')],
         qr=V['bpresion'], qrlabel='Presión tras pérdida'),

    dict(tag='LÁMINA 05', title='CÓRNER A FAVOR', dia='corner',
         sub='Casi nadie lo ensaya. El que lo hace, roba goles',
         points=[('Nadie se mueve', 'hasta que la que cobra levanta la mano.'),
                 ('Tres arrancan juntas', 'al primer poste. Juntas, no en fila.'),
                 ('Una fija en el segundo palo.', 'No se mueve de ahí.'),
                 ('Una fuera del área', 'para el rechace.'),
                 ('Dos se quedan atrás', 'por si nos contragolpean.')],
         qr=V['bcorner'], qrlabel='Jugadas ensayadas de córner'),

    dict(tag='LÁMINA 06', title='CÓRNER EN CONTRA', dia='corner_c',
         sub='Cada una tiene un sitio, no una rival',
         points=[('La más alta al primer poste.', 'Ahí llega el 70% de los centros.'),
                 ('Una tapa el córner corto.', 'Siempre.'),
                 ('Cuatro reparten el área chica', 'y no se mueven de su zona.'),
                 ('Una en el borde del área:', 'el rechace es nuestro.'),
                 ('Al despejar salimos.', 'La 9 se queda arriba.')],
         qr=V['bloque'], qrlabel='Defensa del área'),

    dict(tag='LÁMINA 07', title='DEFENSA CENTRAL\nSOLA', dia='sombra',
         sub='Se manda con la cabeza, no con las piernas',
         points=[('Sombra defensiva:', '5 metros de lado a lado sin cruzar los pies. 4×30 s.'),
                 ('Cono enemigo:', 'acércate en zigzag frenando el último paso. 10 veces.'),
                 ('Postura:', 'rodillas semiflexionadas, peso en la punta de los pies.'),
                 ('De lado, nunca de frente.', 'De frente te ganan la carrera.'),
                 ('Esto se entrena sin balón', 'y sin nadie.')],
         qr=V['bdefensa'], qrlabel='Cómo defender el 1 contra 1'),

    dict(tag='LÁMINA 08', title='TÉCNICA\nCON LA PARED', dia='pared',
         sub='Tu mejor compañera de entrenamiento',
         points=[('Pase y recepción:', 'a 3 pasos, 3 series de 20 con cada pie.'),
                 ('Un solo toque:', 'pasa y devuelve sin controlar. 2×15.'),
                 ('Control orientado:', 'recibe y llévalo a un lado. 3×10 por lado.'),
                 ('Voltea antes:', 'gira la cabeza antes de que llegue. 20 veces.'),
                 ('Errores:', 'pie tieso, mirar solo el balón, pegarle con la punta.')],
         qr=V['pared'], qrlabel='Solo necesitas una pared'),

    dict(tag='LÁMINA 09', title='ENTRENAR DE A DOS', dia='dos',
         sub='Con tu prima o una amiga basta',
         points=[('Calentar 10 min:', 'trote, movilidad y 50 pases suaves.'),
                 ('Pared humana:', 'una pasa, la otra devuelve a un toque. 3×20.'),
                 ('1 contra 1:', 'portería de botellas, 30 segundos cada una, 6 rondas.'),
                 ('Duelos de cabeceo:', 'una lanza con las manos, la otra cabecea. 10 cada una.'),
                 ('Remates con asistencia:', 'una centra raso, la otra remata. 15 cada una.')],
         qr=V['casa5'], qrlabel='5 ejercicios de técnica'),

    dict(tag='LÁMINA 10', title='CON QUÉ PARTE\nLE PEGAS', dia='botin',
         sub='El mismo balón, siete resultados distintos',
         points=[('PASE, interior:', 'firme, raso y al pie. El 80% de los pases.'),
                 ('CAÑONAZO, empeine:', 'donde van las agujetas. Tiro y pase largo.'),
                 ('TRES DEDOS:', 'pase cruzado y centro con caída.'),
                 ('EFECTO:', 'para rodearla en un tiro libre.'),
                 ('PLANTA y TACÓN:', 'para frenar y para el pase atrás en el área.'),
                 ('PUNTA: nunca.', 'Cero control. El error más común.')],
         qr=V['pases7'], qrlabel='Pases y controles'),

    dict(tag='LÁMINA 11', title='TIRO AL CUADRO', dia='tiro',
         sub='Con una barda y un gis',
         points=[('Pie de apoyo al lado del balón', 'apuntando a donde va.'),
                 ('Cuerpo ligeramente encima.', 'Si te echas atrás, la mandas al cielo.'),
                 ('Empeine, nunca la punta.', 'Donde van las agujetas.'),
                 ('No le pegues con toda tu fuerza:', 'el gol es colocación.'),
                 ('20 tiros diarios:', '10 derecha, 10 izquierda. Anota cuántos entran.')],
         qr=V['tiro'], qrlabel='Ejercicios de disparo'),

    dict(tag='LÁMINA 12', title='LO QUE SE HACE\nTODOS LOS DÍAS', kind='list',
         sub='15 a 20 minutos, sola, sin cancha',
         points=[('100 toques', 'empeine, muslo, planta y cabeza.'),
                 ('50 pases a la pared', 'con cada pie.'),
                 ('20 tiros al cuadro', '10 con cada pie.'),
                 ('5 vueltas entre botellas', 'interior y exterior, sin mirar el balón.'),
                 ('3×15 sentadillas y 3×30 s de plancha.', 'La rodilla nunca hacia adentro.'),
                 ('5 minutos mentalizándote:', 'yo puedo, yo mando atrás, cada día soy mejor.')],
         qr=V['crono'], qrlabel='Rutina de 20 min con cronómetro'),
]
