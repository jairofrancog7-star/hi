# -*- coding: utf-8 -*-
"""Genera la guía en PDF, las láminas en PDF y la página HTML de enlaces."""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
import pdfkit as pk
import diagram as dg
import content as C
import webstyle as WS
import webassets as WA

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(SOURCE_DIR)

# Sistema visual: cielo como identidad, azul profundo para contraste y rosa como acento.
# Nunca se usa texto blanco sobre SKY: no alcanza el contraste necesario.
PAPER = '#f7fcff'
BG = PAPER
INK = '#102a3a'
MUT = '#486476'
SKY = '#bfe9ff'
BLUE = '#0b6fa4'
BLUED = '#06496e'
ROSE = '#a52357'
ROSE_SOFT = '#ffe3ed'
CARD = '#eef8fd'
DARK = '#073b59'
LIME = '#eef8df'
LIMED = '#385b12'

W, H = 595.28, 841.89
M = 42.0
CW = W - M * 2


def short(url):
    if 'youtu.be/' in url:
        return 'youtu.be/' + url.rsplit('/', 1)[1]
    if 'search_query' in url:
        return 'YouTube · búsqueda'
    return url.split('//')[-1].split('/')[0]


def lead_split(s):
    m = re.match(r'^([^:]{3,36}):\s*(.+)$', s)
    if m:
        return [(m.group(1) + ': ', 'b'), (m.group(2), 'r')]
    m = re.match(r'^(.{3,30}?\.)\s+(.+)$', s)
    if m:
        return [(m.group(1) + ' ', 'b'), (m.group(2), 'r')]
    return [(s, 'r')]


# ---------------------------------------------------------------- guía
def header(p, left, right):
    p.rect(0, 0, W, 26, fill=SKY)
    p.text(M, 8.5, left, 7.6, True, color=BLUED)
    p.text(W - M, 8.5, right, 7.6, color=MUT, align='right')


def footer(p, n, total):
    p.line(M, H - 34, W - M, H - 34, '#c5dfeb', 0.8)
    p.text(M, H - 28, 'Guía de entrenamiento · fútbol femenil sub-17', 7.2, color=MUT)
    p.text(W - M, H - 28, '%d / %d' % (n, total), 7.2, True, color=BLUED, align='right')


def cover(doc, total):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=DARK)
    p.rect(0, 0, W, 6, fill=SKY)
    y = 96
    p.text(M, y, 'SUB-17 FEMENIL · GUÍA DE TRABAJO', 9.5, True, color=ROSE_SOFT)
    y += 34
    p.text(M, y, 'ENTRENA COMO', 44, True, color='#ffffff')
    y += 48
    p.text(M, y, 'LAS GRANDES', 44, True, color=SKY)
    y += 66
    p.para(M, y, 'Quince ejercicios dibujados, con los videos de cada uno. Lo que hacen los '
                 'mejores equipos femeniles del mundo, adaptado a una cancha compartida, '
                 'botellas de refresco y una pared.', 11.5, CW - 150, 17, color='#d9edf7')
    y += 76
    p.line(M, y, W - M, y, '#2a6582', 1)
    y += 22
    p.text(M, y, 'LO QUE HAY ADENTRO', 9, True, color=ROSE_SOFT)
    y += 20
    col = (CW - 20) / 2
    n = len(C.DRILLS)
    per = (n + 1) // 2
    for i, d in enumerate(C.DRILLS):
        cx = M + (0 if i < per else col + 20)
        cy = y + (i if i < per else i - per) * 19
        p.text(cx, cy, d['n'], 8.5, True, color=SKY)
        p.text(cx + 20, cy, d['title'], 10, color='#edf8fc')
    y += per * 19 + 26
    p.line(M, y, W - M, y, '#2a6582', 1)
    y += 20
    facts = [('Fichas', '%d con dibujo' % n), ('Recursos', '%d accesos' % resource_count()),
             ('Jugadoras', 'de 1 a 11'), ('Material', 'balón, botellas, pared')]
    fw = CW / 4
    for i, (k, v) in enumerate(facts):
        p.text(M + i * fw, y, k.upper(), 7.4, True, color='#acd4e6')
        p.text(M + i * fw, y + 13, v, 10.5, True, color='#ffffff')
    qy = H - 190
    p.text(M, qy - 16, 'ESCANEA Y EMPIEZA POR AQUÍ', 8.4, True, color=ROSE_SOFT)
    pk.draw_qr(p, C.V['sola'], M, qy, 92, fg=DARK, bg='#ffffff')
    p.text(M + 104, qy + 16, 'Guía completa para', 10, color='#d9edf7')
    p.text(M + 104, qy + 32, 'entrenar sola', 10, color='#d9edf7')
    p.text(M + 104, qy + 54, 'Todos los nombres de video', 9, color='#acd4e6')
    p.text(M + 104, qy + 68, 'de esta guía se pueden picar.', 9, color='#acd4e6')
    p.link(M, qy, 92, 92, C.V['sola'])
    p.text(M, H - 62, 'Se imprime en hojas tamaño carta o A4 · cada ficha en una hoja',
           9, color='#acd4e6')
    return p


def resource_count():
    """Número de tarjetas de recurso en las fichas, sin duplicar anotaciones PDF."""
    return sum(len(d['links']) for d in C.DRILLS)


def page_uso(doc):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=BG)
    header(p, 'CÓMO SE USA', 'antes de bajar al campo')
    y = 62
    p.text(M, y, 'Cómo se usa esta guía', 26, True, color=INK)
    y += 40
    reglas = [
        ('Una ficha por sesión, no cinco.', 'El error es querer aprender todo el martes. '
         'Un tema, muchas repeticiones.'),
        ('Se ve el video antes.', 'Una jugadora es la encargada: el día anterior abre el '
         'enlace y llega sabiendo qué se va a hacer. Rota cada semana.'),
        ('En el campo, dos minutos de celular.', 'Se ve el fragmento, se pausa en la '
         'posición correcta y se guarda el teléfono.'),
        ('Primero lento, luego con presión.', 'Primera ronda despacio para que todas '
         'entiendan. Segunda a media velocidad. Tercera de verdad.'),
        ('Una observadora por turno.', 'Mira una sola cosa: pie, cabeza, perfil o '
         'movimiento. No corrige todo junto.'),
        ('Grábense 30 segundos.', 'Comparen su video con el del tutorial. Ahí se ve la '
         'diferencia sin que nadie tenga que decírsela.'),
    ]
    for i, (a, b) in enumerate(reglas):
        p.text(M, y + 1, '%02d' % (i + 1), 11, True, color=BLUE)
        yy = p.rich(M + 26, y, [(a + ' ', 'b'), (b, 'r')], 10.4, CW - 26, 15, INK)
        p.line(M, yy + 4, W - M, yy + 4, '#d4e8f1', 0.7)
        y = yy + 14

    y += 12
    p.text(M, y, 'Cómo se leen los dibujos', 18, True, color=INK)
    y += 28
    box_h = 150
    p.roundrect(M, y, CW, box_h, 8, fill=CARD)
    inner = {'kind': 'grid', 'w': 30, 'h': 15, 'pad': 1.4, 'pr': 1.7, 'items': [
        ('p', 5, 11, 4), ('r', 12, 11), ('b', 19, 11), ('c', 25, 11),
        ('pass', 4, 5, 10, 5), ('run', 12, 5, 18, 5), ('drib', 20, 5, 26, 5),
    ]}
    dg.render(p, inner, M + 12, y + 10, CW - 24, box_h - 46)
    ley = [('Nosotras (azul)', BLUE), ('Rival (negro)', '#1c1c22'), ('Balón', MUT),
           ('Cono o botella', '#c97a00')]
    cw2 = (CW - 24) / 4
    for i, (t, c) in enumerate(ley):
        p.text(M + 12 + i * cw2, y + box_h - 32, t, 8.6, True, color=c)
    ley2 = ['- - -  pase', '——>  carrera', '~~~>  conducción']
    for i, t in enumerate(ley2):
        p.text(M + 12 + i * cw2, y + box_h - 18, t, 8.6, color=MUT)
    y += box_h + 20
    p.roundrect(M, y, CW, 52, 8, fill=LIME)
    p.rich(M + 14, y + 12, [('Seguridad. ', 'b'),
                            ('Si el balón puede cruzar hacia niños u otros grupos, se cambia a '
                             'pared, rondo pequeño o fuerza. Si algo duele, se para. '
                             'Nadie entrena lesionada para demostrar nada.', 'r')],
           10, CW - 28, 14.5, LIMED)
    footer(p, 2, TOTAL)


def drill_page(p, d, num):
    p.rect(0, 0, W, H, fill=BG)
    header(p, 'FICHA %s · %s' % (d['n'], d['cat'].upper()), d['team'])
    y = 54
    p.text(M, y, d['title'], 25, True, color=INK, maxw=CW)
    y += 32
    p.text(M, y, d['sub'], 11, italic=True, color=BLUE, maxw=CW)
    y += 22
    ih = p.para_h(d['idea'], 10.2, CW, 14.6)
    p.para(M, y, d['idea'], 10.2, CW, 14.6, color=MUT)
    y += ih + 14

    # ---- columnas de texto: alto necesario
    lcol = CW * 0.58
    rcol = CW - lcol - 18
    steps_h = 0
    for s in d['steps']:
        steps_h += p.rich_h(lead_split(s), 9.9, lcol - 22, 14) + 7
    dose_h = 26 + len(d['dose']) * 22
    watch_h = 26 + p.para_h(d['watch'], 9.6, rcol - 24, 13.4)
    right_h = dose_h + 12 + watch_h
    text_h = max(steps_h + 22, right_h)

    links_h = 30 + max(len(d['links']) * 21, 84)
    avail = (H - 46) - y - text_h - links_h - 26
    dw = CW
    dh = min(dg.height_for(D_of(d), dw - 20), 248.0, max(120.0, avail))
    p.roundrect(M, y, CW, dh + 20, 8, fill='#e3f5fd')
    dg.render(p, D_of(d), M + 10, y + 10, CW - 20, dh)
    y += dh + 32

    # pasos
    p.text(M, y, 'PASO A PASO', 8.6, True, color=BLUED)
    yy = y + 18
    for i, s in enumerate(d['steps']):
        p.circle(M + 6, yy + 5, 6.6, fill=BLUE)
        p.text(M + 6, yy + 0.6, str(i + 1), 8, True, color='#ffffff', align='center')
        yy = p.rich(M + 22, yy, lead_split(s), 9.9, lcol - 22, 14, INK) + 7

    # dosis
    rx = M + lcol + 18
    p.roundrect(rx, y - 6, rcol, dose_h, 7, fill=DARK)
    p.text(rx + 12, y + 6, 'DOSIS', 8.4, True, color=SKY)
    for i, (k, v) in enumerate(d['dose']):
        p.text(rx + 12, y + 24 + i * 22, k.upper(), 7.2, color='#b8dcea')
        p.text(rx + 12, y + 34 + i * 22, v, 9.4, True, color='#ffffff')
    wy = y - 6 + dose_h + 12
    p.roundrect(rx, wy, rcol, watch_h, 7, fill=LIME)
    p.text(rx + 12, wy + 10, 'QUÉ MIRA LA COMPAÑERA', 7.6, True, color=LIMED)
    p.para(rx + 12, wy + 26, d['watch'], 9.6, rcol - 24, 13.4, color='#3d5410')

    # enlaces + QR
    ly = H - 46 - links_h
    p.line(M, ly - 10, W - M, ly - 10, '#c5dfeb', 0.8)
    p.text(M, ly, 'VE EL VIDEO ANTES DE BAJAR AL CAMPO', 8.6, True, color=BLUED)
    for i, (tag, tit, url) in enumerate(d['links']):
        yy = ly + 20 + i * 21
        p.roundrect(M, yy - 1, 40, 13, 3, fill=BLUE)
        p.text(M + 20, yy + 1.4, tag.upper(), 6.8, True, color='#ffffff', align='center')
        w = p.text(M + 48, yy, tit, 10, True, color=BLUED)
        p.line(M + 48, yy + 12.5, M + 48 + w, yy + 12.5, BLUED, 0.6)
        p.link(M + 48, yy - 2, w + 4, 16, url)
        p.text(M + 48 + w + 8, yy + 1.2, short(url), 7, color=MUT,
               maxw=max(30.0, (W - M - 96) - (M + 48 + w + 8)))
    qs = 84
    pk.draw_qr(p, d['qr'], W - M - qs, ly + 8, qs, fg=INK, bg='#ffffff')
    p.link(W - M - qs, ly + 8, qs, qs, d['qr'])
    p.text(W - M - qs / 2, ly + qs + 12, 'escanea con la cámara', 7, color=MUT, align='center')
    footer(p, num, TOTAL)


def D_of(d):
    return C.D[d['dia']]


def page_semana(doc, num):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=BG)
    header(p, 'CÓMO SE REPARTE LA SEMANA', 'partido el sábado')
    y = 58
    p.text(M, y, 'Semana tipo', 25, True, color=INK)
    y += 34
    p.para(M, y, 'Entre semana se entrena, el fin de semana se juega. El día antes del partido '
                 'nunca hay fuerza pesada ni sprints máximos: solo balón y descanso.',
           10.4, CW, 14.6, color=MUT)
    y += 44
    p.rect(M, y, CW, 20, fill=DARK)
    for cx, t in ((M + 10, 'DÍA'), (M + 100, 'QUÉ TOCA'), (W - M - 80, 'CARGA')):
        p.text(cx, y + 6, t, 7.6, True, color=SKY)
    y += 20
    for i, (dia, qué, carga) in enumerate(C.SEMANA):
        h = 26
        if i % 2 == 0:
            p.rect(M, y, CW, h, fill=CARD)
        p.text(M + 10, y + 8, dia, 10, True, color=INK)
        p.text(M + 100, y + 8, qué, 9.8, color=INK)
        p.text(W - M - 80, y + 8, carga, 9.4, True, color=BLUED)
        y += h
    y += 26
    p.text(M, y, 'Según cuántas lleguen', 20, True, color=INK)
    y += 28
    p.para(M, y, 'Nunca se cancela un entrenamiento por falta de gente: se cambia el menú.',
           10.2, CW, 14, color=MUT)
    y += 22
    p.rect(M, y, CW, 20, fill=DARK)
    for cx, t in ((M + 10, 'LLEGARON'), (M + 90, 'QUÉ FICHAS'), (M + 320, 'EJERCICIO ESTRELLA')):
        p.text(cx, y + 6, t, 7.6, True, color=SKY)
    y += 20
    for i, (n, f, e) in enumerate(C.MENU):
        if i % 2 == 0:
            p.rect(M, y, CW, 24, fill=CARD)
        p.text(M + 10, y + 7, n, 10, True, color=BLUE)
        p.text(M + 90, y + 7, f, 9.6, color=INK)
        p.text(M + 320, y + 7, e, 9.6, color=MUT)
        y += 24
    y += 26
    p.text(M, y, 'Una corrección por semana', 20, True, color=INK)
    y += 28
    p.rect(M, y, CW, 20, fill=DARK)
    for cx, t in ((M + 10, 'SEMANA'), (M + 90, 'PALABRA'), (M + 220, 'QUÉ SE OBSERVA')):
        p.text(cx, y + 6, t, 7.6, True, color=SKY)
    y += 20
    for i, (n, w2, q) in enumerate(C.CORRECCION):
        if i % 2 == 0:
            p.rect(M, y, CW, 22, fill=CARD)
        p.text(M + 10, y + 6, n, 9.8, True, color=BLUE)
        p.text(M + 90, y + 6, w2, 9.8, True, color=INK)
        p.text(M + 220, y + 6, q, 9.6, color=MUT)
        y += 22
    footer(p, num, TOTAL)


def page_hoja(doc, num):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=BG)
    header(p, 'HOJA DE CONTROL', 'para la libreta')
    y = 58
    p.text(M, y, 'Hoja de control', 25, True, color=INK)
    y += 34
    p.para(M, y, 'Lo que no se anota no se sostiene. Imprime esta hoja o cópiala en una libreta '
                 'y anota cada entrenamiento.', 10.4, CW, 14.6, color=MUT)
    y += 40
    cols = [('FECHA', 60), ('LLEGARON', 58), ('FICHA', 46), ('VIDEO VISTO', 120),
            ('LO QUE SALIÓ BIEN', 110), ('UNA CORRECCIÓN', CW - 394)]
    p.rect(M, y, CW, 22, fill=DARK)
    cx = M
    for t, w in cols:
        p.text(cx + 6, y + 7, t, 7, True, color=SKY)
        cx += w
    y += 22
    for r in range(18):
        p.rect(M, y, CW, 30, stroke='#c9e0eb', lw=0.7)
        cx = M
        for t, w in cols[:-1]:
            cx += w
            p.line(cx, y, cx, y + 30, '#c9e0eb', 0.7)
        y += 30
    y += 24
    p.roundrect(M, y, CW, 46, 8, fill=CARD)
    p.text(M + 16, y + 15, 'Ver, copiar, repetir, grabarse y corregir. Eso es tener entrenador.',
           13, True, color=BLUED)
    footer(p, num, TOTAL)


def page_anexo(doc, num):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=BG)
    header(p, 'ANEXO · TODOS LOS VIDEOS', 'escanea desde la hoja impresa')
    y = 58
    p.text(M, y, 'Todos los enlaces', 25, True, color=INK)
    y += 34
    p.para(M, y, 'Un PDF no puede reproducir video adentro: ningún lector de celular lo hace. '
                 'Lo que sí funciona es esto. Escanea el cuadro con la cámara del celular y se '
                 'abre el video, incluso desde la hoja impresa.', 10.4, CW, 14.6, color=MUT)
    y += 52
    seen, cards = set(), []
    for d in C.DRILLS:
        for (tag, tit, url) in d['links']:
            if url in seen:
                continue
            seen.add(url)
            cards.append((d['n'], tit, url))
    perrow, gap = 3, 14
    cwid = (CW - gap * (perrow - 1)) / perrow
    ch = 118
    for i, (fn, tit, url) in enumerate(cards):
        r, c = divmod(i, perrow)
        cx = M + c * (cwid + gap)
        cy = y + r * (ch + gap)
        if cy + ch > H - 56:
            break
        p.roundrect(cx, cy, cwid, ch, 7, fill=CARD)
        pk.draw_qr(p, url, cx + (cwid - 62) / 2, cy + 8, 62, fg=INK, bg='#ffffff')
        p.text(cx + cwid / 2, cy + 74, 'FICHA ' + fn, 6.8, True, color=BLUE, align='center')
        for j, ln in enumerate(p.wrap(tit, 8.4, cwid - 14, True)[:3]):
            p.text(cx + cwid / 2, cy + 86 + j * 10.5, ln, 8.4, True, color=INK, align='center')
        p.link(cx, cy, cwid, ch, url)
    footer(p, num, TOTAL)


# ---------------------------------------------------------------- láminas
PW, PH = 340.0, 604.0
PBG = PAPER
PCARD = '#e7f6fd'


def poster(doc, po, idx, total):
    p = doc.page(PW, PH)
    p.rect(0, 0, PW, PH, fill=PBG)
    p.rect(0, 0, PW, 5, fill=SKY)
    m = 20.0
    cw = PW - m * 2
    y = 26.0
    tw = pk.width(po['tag'], 7.6, True)
    p.roundrect(m, y, tw + 16, 15, 7.5, fill=BLUE)
    p.text(m + 8, y + 3.2, po['tag'], 7.6, True, color='#ffffff')
    y += 26
    lines = po['title'].split('\n')
    ts = 30 if max(len(l) for l in lines) <= 15 else 24
    for l in lines:
        p.text(m, y, l, ts, True, color=INK, maxw=cw)
        y += ts * 1.06
    y += 4
    p.text(m, y, po['sub'], 9.8, italic=True, color=ROSE, maxw=cw)
    y += 22

    if po.get('kind') == 'cover':
        p.line(m, y, PW - m, y, '#bdddea', 1)
        y += 14
        p.text(m, y, 'LO QUE HAY ADENTRO', 8, True, color=BLUED)
        y += 16
        for it in po['index']:
            p.text(m, y, it, 9.4, color=INK, maxw=cw)
            y += 13.4
        y += 8
    else:
        pts_h = sum(p.rich_h(lead_split(a + ' ' + b), 9.8, cw - 22, 13.5) + 9
                    for a, b in po['points'])
        qbase = PH - 108
        if po.get('dia'):
            avail = qbase - y - pts_h - 18
            dh = min(dg.height_for(C.D[po['dia']], cw - 16), max(96, avail))
            p.roundrect(m, y, cw, dh + 16, 7, fill=PCARD)
            dg.render(p, C.D[po['dia']], m + 8, y + 8, cw - 16, dh)
            y += dh + 24
        for a, b in po['points']:
            p.rect(m, y + 1, 2.6, 11, fill=BLUE)
            y = p.rich(m + 11, y, [(a + ' ', 'b'), (b, 'r')], 9.8, cw - 22, 13.5, INK) + 9

    qs = 62
    qy = PH - 84
    p.line(m, qy - 14, PW - m, qy - 14, '#bdddea', 1)
    pk.draw_qr(p, po['qr'], m, qy, qs, fg=INK, bg='#ffffff')
    p.link(m, qy, qs, qs, po['qr'])
    p.text(m + qs + 12, qy + 6, 'ESCANEA Y VE EL VIDEO', 7.6, True, color=BLUE)
    for j, ln in enumerate(p.wrap(po['qrlabel'], 9, cw - qs - 16)[:2]):
        p.text(m + qs + 12, qy + 20 + j * 12, ln, 9, color=INK)
    p.text(m + qs + 12, qy + 48, 'SUB-17 FEMENIL · %d de %d' % (idx, total), 7.2, color=MUT)


# ---------------------------------------------------------------- HTML
def html():
    def esc(s):
        return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                .replace('"', '&quot;').replace("'", '&#39;'))

    fichas = []
    for d in C.DRILLS:
        spec = C.D[d['dia']]
        diagram_w, diagram_h = WA.diagram_dimensions(spec)
        diagram = (
            '<figure class="diagram-card"><img class="exercise-diagram" '
            'src="%s" alt="Diagrama táctico: %s" width="%d" height="%d" '
            'loading="lazy" decoding="async"><figcaption>%s</figcaption></figure>'
            % (WA.diagram_data_uri(spec, d['title']), esc(d['title']), diagram_w,
               diagram_h, esc(d['sub'])))
        qr = (
            '<img class="qr" src="%s" alt="Código QR para %s" width="256" '
            'height="256" loading="lazy" decoding="async">'
            % (WA.qr_data_uri(d['qr'], 'Código QR · ' + d['title']), esc(d['title'])))
        pasos = ''.join('<li><span>%s</span></li>' % esc(s) for s in d['steps'])
        dosis = ''.join(
            '<div class="dose-item"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v))
            for k, v in d['dose'])
        links = ''.join(
            '<a class="video-card" href="%s" target="_blank" rel="noopener noreferrer" '
            'aria-label="Abrir recurso: %s; requiere internet y abre otra pestaña">'
            '<span class="video-tag">%s</span>'
            '<span class="video-copy"><strong>%s</strong>'
            '<small>%s · requiere internet</small></span>'
            '<span class="external" aria-hidden="true">↗</span></a>'
            % (esc(u), esc(ti), esc(t.upper()), esc(ti),
               'YouTube' if ('youtu.be/' in u or 'youtube.com/' in u) else esc(short(u)))
            for (t, ti, u) in d['links'])
        title_id = 'titulo-f%s' % d['n']
        steps_id = 'pasos-f%s' % d['n']
        fichas.append(
            '<article class="training-card" id="f%s" aria-labelledby="%s">'
            '<header class="card-heading"><span class="number">FICHA %s</span>'
            '<span class="category">%s</span><span class="team">%s</span></header>'
            '<h2 id="%s">%s</h2><p class="subtitle">%s</p><p class="idea">%s</p>'
            '%s<div class="lesson-grid"><section aria-labelledby="%s">'
            '<h3 id="%s">Paso a paso</h3><ol class="steps">%s</ol></section>'
            '<aside class="coach-note"><h3>Qué mira la compañera</h3><p>%s</p>'
            '<dl class="dose">%s</dl></aside></div>'
            '<section class="media-section" aria-label="Videos y código QR de la ficha %s">'
            '<div class="section-title"><h3>Videos para preparar la sesión</h3>'
            '<span>Abren en otra pestaña</span></div>'
            '<div class="media-grid"><div class="video-list">%s</div>'
            '<a class="qr-card" href="%s" target="_blank" rel="noopener noreferrer" '
            'aria-label="Abrir recurso QR de la ficha %s; requiere internet">%s'
            '<span><strong>Escanea en la cancha</strong><small>La guía funciona sin conexión; '
            'el video necesita internet.</small></span></a></div></section>'
            '<a class="back-link" href="#indice">Volver al índice ↑</a></article>'
            % (d['n'], title_id, d['n'], esc(d['cat']), esc(d['team']), title_id,
               esc(d['title']), esc(d['sub']), esc(d['idea']), diagram, steps_id, steps_id, pasos,
               esc(d['watch']), dosis, d['n'], links, esc(d['qr']), d['n'],
               qr))

    toc = ''.join(
        '<a class="toc-link" href="#f%s"><span>%s</span><strong>%s</strong></a>'
        % (d['n'], d['n'], esc(d['title'])) for d in C.DRILLS)

    css = WS.CSS
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="theme-color" content="#bfe9ff" media="(prefers-color-scheme:light)">'
            '<meta name="theme-color" content="#183f53" media="(prefers-color-scheme:dark)">'
            '<meta name="description" content="Guía didáctica de entrenamiento de fútbol femenil '
            'sub-17: 15 fichas, PDF imprimible, láminas y videos.">'
            '<title>Entrena como las grandes · fútbol femenil sub-17</title>'
            '<style>%s</style></head><body>'
            '<a class="skip-link" href="#contenido">Saltar al contenido</a>'
            '<header class="site-header"><div class="shell">'
            '<nav class="top-nav" aria-label="Navegación principal">'
            '<a class="brand" href="#inicio" aria-label="Entrena como las grandes, inicio">'
            '<span class="brand-mark" aria-hidden="true"><svg class="brand-ball" viewBox="0 0 24 24" '
            'focusable="false"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" '
            'stroke-width="1.8"/><path d="m12 7 3 2.2-1.1 3.5h-3.8L9 9.2 12 7Z'
            'M9 9.2 5.9 8M15 9.2 18.1 8M10.1 12.7 8.4 16M13.9 12.7 15.6 16" '
            'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
            '</svg></span>'
            '<span>Entrena como las grandes</span></a>'
            '<div class="top-links"><a href="#descargas">Descargas</a>'
            '<a href="#indice">Fichas</a></div></nav>'
            '<div class="hero" id="inicio"><div><p class="eyebrow">Fútbol femenil · Sub-17</p>'
            '<h1>Entrena como <em>las grandes</em></h1>'
            '<p class="lede">Quince ejercicios explicados paso a paso, con dosis, puntos de '
            'observación, videos y códigos QR. Diseñada para leerse rápido en el celular y '
            'llevarse a la cancha.</p>'
            '<div class="hero-actions"><a class="button" '
            'href="guia-entrena-como-las-grandes.pdf" download>Descargar guía PDF</a>'
            '<a class="button secondary" href="#f01">Empezar con la ficha 01</a></div></div>'
            '<aside class="hero-card" aria-label="Resumen de la guía">'
            '<h2>Todo el material, en una vista</h2><dl class="facts">'
            '<div><dt>Fichas</dt><dd>%d</dd></div><div><dt>Guía A4</dt><dd>%d pág.</dd></div>'
            '<div><dt>Láminas</dt><dd>%d</dd></div><div><dt>Dependencias</dt><dd>0</dd></div>'
            '</dl><p class="offline-note"><strong>Lista para usar sin internet.</strong> '
            'Guarda el HTML o los PDF antes de salir. Solo los videos necesitan conexión.</p>'
            '</aside></div></div></header>'
            '<main id="contenido"><div class="shell">'
            '<section class="downloads" id="descargas" aria-labelledby="titulo-descargas">'
            '<div class="section-heading"><div><p class="eyebrow">Acceso rápido</p>'
            '<h2 id="titulo-descargas">Descargas claras y directas</h2></div>'
            '<p>Elige el formato según el momento: imprimir, compartir con el equipo o '
            'consultar desde el teléfono.</p></div>'
            '<div class="download-table-wrap"><table class="download-table">'
            '<thead><tr><th>Recurso</th><th>Formato</th><th>Ideal para</th><th>Acción</th></tr></thead>'
            '<tbody><tr><td data-label="Recurso"><strong>Guía completa</strong>'
            '<small>15 fichas y anexos</small></td><td data-label="Formato">PDF · %d páginas</td>'
            '<td data-label="Ideal para">Imprimir y llevar a la cancha</td>'
            '<td data-label="Acción"><a class="button" '
            'href="guia-entrena-como-las-grandes.pdf" download>Descargar PDF</a></td></tr>'
            '<tr><td data-label="Recurso"><strong>Láminas del grupo</strong>'
            '<small>Verticales y compartibles</small></td><td data-label="Formato">PDF · %d láminas</td>'
            '<td data-label="Ideal para">WhatsApp y consulta rápida</td>'
            '<td data-label="Acción"><a class="button secondary" '
            'href="posters-para-el-grupo.pdf" download>Ver láminas</a></td></tr>'
            '<tr><td data-label="Recurso"><strong>Guía web offline</strong>'
            '<small>Sin JavaScript ni archivos externos</small></td><td data-label="Formato">HTML único</td>'
            '<td data-label="Ideal para">Guardar en Android, iPhone o computadora</td>'
            '<td data-label="Acción"><a class="button secondary" href="index.html" '
            'download="guia-futbol-offline.html">Guardar HTML</a></td></tr></tbody></table></div>'
            '</section><details class="contents" id="indice" open>'
            '<summary>Índice de las 15 fichas</summary>'
            '<nav class="toc" aria-label="Índice de fichas">%s</nav></details>'
            '<section aria-labelledby="titulo-guia"><header class="guide-heading">'
            '<h2 id="titulo-guia">Fichas de entrenamiento</h2>'
            '<p>Abre una ficha, revisa un solo objetivo y repítelo. Los enlaces de video '
            'están claramente marcados porque necesitan conexión.</p></header>%s</section>'
            '</div></main><footer class="site-footer"><div class="shell">'
            '<strong>Ver, copiar, repetir, corregir.</strong>'
            '<span>Guía de entrenamiento · fútbol femenil sub-17</span>'
            '</div></footer></body></html>'
            % (css, len(C.DRILLS), TOTAL, len(C.POSTERS), TOTAL, len(C.POSTERS), toc,
               ''.join(fichas)))


# ---------------------------------------------------------------- comprobaciones
def check_diagrams():
    """Comprueba que ninguna etiqueta se salga del recuadro del diagrama."""
    bad = []
    for key, spec in C.D.items():
        pad = spec.get('pad', 2.0)
        x0, x1 = -pad, spec['w'] + pad
        y0, y1 = -pad, spec['h'] + pad
        for it in spec['items']:
            if it[0] == 't':
                txt, size, align = it[3], (it[4] if len(it) > 4 else 1.0), \
                    (it[5] if len(it) > 5 else 'center')
                cx, cy = it[1], it[2]
            elif it[0] == 'mark':
                txt, size = it[5], (it[6] if len(it) > 6 else 0.95)
                cx, cy = it[3], it[4]
                align = 'left' if it[3] > it[1] else 'right'
            else:
                continue
            wd = pk.width(txt, size, True) + size * 0.84
            if align == 'center':
                a, b = cx - wd / 2, cx + wd / 2
            elif align == 'right':
                a, b = cx - wd, cx
            else:
                a, b = cx, cx + wd
            if a < x0 - 0.2 or b > x1 + 0.2:
                bad.append('%s: etiqueta %r de %.1f a %.1f (marco %.1f a %.1f)'
                           % (key, txt[:34], a, b, x0, x1))
            if cy - size < y0 - 0.4 or cy + size > y1 + 0.4:
                bad.append('%s: etiqueta %r fuera en vertical (y=%.1f)' % (key, txt[:24], cy))
    return bad


def check(doc, name, pw, ph):
    problems = []
    for i, p in enumerate(doc.pages, 1):
        for op in p.ops:
            t = op.split()
            if not t:
                continue
            for tok in t:
                if tok in ('nan', 'inf', '-inf'):
                    problems.append('%s p%d: numero invalido' % (name, i))
            if t[-1] == 're':
                x, y, w, h = (float(v) for v in t[-5:-1])
                if x < -1 or y < -1 or x + w > pw + 1 or y + h > ph + 1:
                    if not (abs(w - pw) < 2 and abs(h - ph) < 2):
                        problems.append('%s p%d: rect fuera de pagina (%.0f,%.0f %.0fx%.0f)'
                                        % (name, i, x, y, w, h))
        for (tx, ty, tw, ts, s) in getattr(p, 'texts', []):
            if tx < -0.5 or tx + tw > pw + 0.5 or ty < -0.5 or ty + ts * 1.2 > ph + 0.5:
                problems.append('%s p%d: texto desbordado (%.0f..%.0f de %.0f) %r'
                                % (name, i, tx, tx + tw, pw, s[:44]))
        for m in re.finditer(r'1 0 0 1 (-?[\d.]+) (-?[\d.]+) Tm', '\n'.join(p.ops)):
            x, y = float(m.group(1)), float(m.group(2))
            if x < -1 or y < -1 or x > pw + 1 or y > ph + 1:
                problems.append('%s p%d: texto fuera de pagina en %.0f,%.0f' % (name, i, x, y))
    return problems


# ---------------------------------------------------------------- main
TOTAL = 4 + len(C.DRILLS) + 1

if __name__ == '__main__':
    guia = pk.Doc()
    cover(guia, TOTAL)
    page_uso(guia)
    for i, d in enumerate(C.DRILLS):
        drill_page(guia.page(W, H), d, 3 + i)
    page_semana(guia, 3 + len(C.DRILLS))
    page_hoja(guia, 4 + len(C.DRILLS))
    page_anexo(guia, 5 + len(C.DRILLS))
    probs = check_diagrams() + check(guia, 'guia', W, H)
    links1 = sum(len(p.links) for p in guia.pages)

    lam = pk.Doc()
    for i, po in enumerate(C.POSTERS, 1):
        poster(lam, po, i, len(C.POSTERS))
    probs += check(lam, 'laminas', PW, PH)
    links2 = sum(len(p.links) for p in lam.pages)

    site = html()
    if site.count('<article') != len(C.DRILLS):
        probs.append('html: faltan fichas')
    if site.count('class="exercise-diagram"') != len(C.DRILLS):
        probs.append('html: faltan diagramas offline')
    if site.count('class="qr"') != len(C.DRILLS):
        probs.append('html: faltan códigos QR offline')
    if site.count('loading="lazy"') != len(C.DRILLS) * 2:
        probs.append('html: la carga diferida no cubre las 30 imágenes')
    if '<script' in site.lower():
        probs.append('html: no debe depender de JavaScript')
    if probs:
        print('\n%d PROBLEMAS DE MAQUETACION:' % len(probs))
        for x in probs[:40]:
            print(' -', x)
        sys.exit(1)

    names = ('guia-entrena-como-las-grandes.pdf', 'posters-para-el-grupo.pdf',
             'index.html')
    with tempfile.TemporaryDirectory(prefix='.guia-build-', dir=OUT) as build_dir:
        n1 = guia.save(os.path.join(build_dir, names[0]))
        n2 = lam.save(os.path.join(build_dir, names[1]))
        with open(os.path.join(build_dir, names[2]), 'w', encoding='utf-8') as f:
            f.write(site)
        for name in names:
            os.replace(os.path.join(build_dir, name), os.path.join(OUT, name))

    print('guia   : %d paginas, %d KB, %d enlaces' % (len(guia.pages), n1 // 1024, links1))
    print('laminas: %d paginas, %d KB, %d enlaces' % (len(lam.pages), n2 // 1024, links2))
    print('html   : %d KB' % (os.path.getsize(os.path.join(OUT, names[2])) // 1024))
    print('\nmaquetacion sin desbordes')
