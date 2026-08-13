# -*- coding: utf-8 -*-
"""Genera la guía en PDF, las láminas en PDF y la página HTML de enlaces."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
import pdfkit as pk
import diagram as dg
import content as C

OUT = os.path.dirname(os.path.abspath(__file__))

# paleta clara (guía imprimible)
BG = '#fffafc'
INK = '#231318'
MUT = '#7a626c'
PINK = '#e5296b'
PINKD = '#a01048'
CARD = '#fff0f5'
DARK = '#1b0f14'
LIME = '#eef7d6'
LIMED = '#4c6b12'

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
    p.rect(0, 0, W, 26, fill=CARD)
    p.text(M, 8.5, left, 7.6, True, color=PINKD)
    p.text(W - M, 8.5, right, 7.6, color=MUT, align='right')


def footer(p, n, total):
    p.line(M, H - 34, W - M, H - 34, '#f0dae3', 0.8)
    p.text(M, H - 28, 'Guía de entrenamiento · fútbol femenil sub-17', 7.2, color=MUT)
    p.text(W - M, H - 28, '%d / %d' % (n, total), 7.2, True, color=PINKD, align='right')


def cover(doc, total):
    p = doc.page(W, H)
    p.rect(0, 0, W, H, fill=DARK)
    p.rect(0, 0, W, 6, fill=PINK)
    y = 96
    p.text(M, y, 'SUB-17 FEMENIL · GUÍA DE TRABAJO', 9.5, True, color='#ff8ab0')
    y += 34
    p.text(M, y, 'ENTRENA COMO', 44, True, color='#ffffff')
    y += 48
    p.text(M, y, 'LAS GRANDES', 44, True, color=PINK)
    y += 66
    p.para(M, y, 'Quince ejercicios dibujados, con los videos de cada uno. Lo que hacen los '
                 'mejores equipos femeniles del mundo, adaptado a una cancha compartida, '
                 'botellas de refresco y una pared.', 11.5, CW - 150, 17, color='#e7cdd6')
    y += 76
    p.line(M, y, W - M, y, '#3a222c', 1)
    y += 22
    p.text(M, y, 'LO QUE HAY ADENTRO', 9, True, color='#ff8ab0')
    y += 20
    col = (CW - 20) / 2
    n = len(C.DRILLS)
    per = (n + 1) // 2
    for i, d in enumerate(C.DRILLS):
        cx = M + (0 if i < per else col + 20)
        cy = y + (i if i < per else i - per) * 19
        p.text(cx, cy, d['n'], 8.5, True, color=PINK)
        p.text(cx + 20, cy, d['title'], 10, color='#f3e6ea')
    y += per * 19 + 26
    p.line(M, y, W - M, y, '#3a222c', 1)
    y += 20
    facts = [('Fichas', '%d con dibujo' % n), ('Videos', '%d enlaces' % nlinks()),
             ('Jugadoras', 'de 1 a 11'), ('Material', 'balón, botellas, pared')]
    fw = CW / 4
    for i, (k, v) in enumerate(facts):
        p.text(M + i * fw, y, k.upper(), 7.4, True, color='#a97f8e')
        p.text(M + i * fw, y + 13, v, 10.5, True, color='#ffffff')
    qy = H - 190
    p.text(M, qy - 16, 'ESCANEA Y EMPIEZA POR AQUÍ', 8.4, True, color='#ff8ab0')
    pk.draw_qr(p, C.V['sola'], M, qy, 92, fg=DARK, bg='#ffffff')
    p.text(M + 104, qy + 16, 'Guía completa para', 10, color='#e7cdd6')
    p.text(M + 104, qy + 32, 'entrenar sola', 10, color='#e7cdd6')
    p.text(M + 104, qy + 54, 'Todos los nombres de video', 9, color='#a97f8e')
    p.text(M + 104, qy + 68, 'de esta guía se pueden picar.', 9, color='#a97f8e')
    p.link(M, qy, 92, 92, C.V['sola'])
    p.text(M, H - 62, 'Se imprime en hojas tamaño carta o A4 · cada ficha en una hoja',
           9, color='#8a6472')
    return p


def nlinks():
    n = 0
    for d in C.DRILLS:
        n += len(d['links'])
    return n * 2 + 40


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
        p.text(M, y + 1, '%02d' % (i + 1), 11, True, color=PINK)
        yy = p.rich(M + 26, y, [(a + ' ', 'b'), (b, 'r')], 10.4, CW - 26, 15, INK)
        p.line(M, yy + 4, W - M, yy + 4, '#f2dde5', 0.7)
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
    ley = [('Nosotras (rosa)', PINK), ('Rival (negro)', '#1c1c22'), ('Balón', '#8a6472'),
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
    p.text(M, y, d['sub'], 11, italic=True, color=PINK, maxw=CW)
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
    p.roundrect(M, y, CW, dh + 20, 8, fill='#f6e3ea')
    dg.render(p, D_of(d), M + 10, y + 10, CW - 20, dh)
    y += dh + 32

    # pasos
    p.text(M, y, 'PASO A PASO', 8.6, True, color=PINKD)
    yy = y + 18
    for i, s in enumerate(d['steps']):
        p.circle(M + 6, yy + 5, 6.6, fill=PINK)
        p.text(M + 6, yy + 0.6, str(i + 1), 8, True, color='#ffffff', align='center')
        yy = p.rich(M + 22, yy, lead_split(s), 9.9, lcol - 22, 14, INK) + 7

    # dosis
    rx = M + lcol + 18
    p.roundrect(rx, y - 6, rcol, dose_h, 7, fill=DARK)
    p.text(rx + 12, y + 6, 'DOSIS', 8.4, True, color='#ff8ab0')
    for i, (k, v) in enumerate(d['dose']):
        p.text(rx + 12, y + 24 + i * 22, k.upper(), 7.2, color='#a97f8e')
        p.text(rx + 12, y + 34 + i * 22, v, 9.4, True, color='#ffffff')
    wy = y - 6 + dose_h + 12
    p.roundrect(rx, wy, rcol, watch_h, 7, fill=LIME)
    p.text(rx + 12, wy + 10, 'QUÉ MIRA LA COMPAÑERA', 7.6, True, color=LIMED)
    p.para(rx + 12, wy + 26, d['watch'], 9.6, rcol - 24, 13.4, color='#3d5410')

    # enlaces + QR
    ly = H - 46 - links_h
    p.line(M, ly - 10, W - M, ly - 10, '#f0dae3', 0.8)
    p.text(M, ly, 'VE EL VIDEO ANTES DE BAJAR AL CAMPO', 8.6, True, color=PINKD)
    for i, (tag, tit, url) in enumerate(d['links']):
        yy = ly + 20 + i * 21
        p.roundrect(M, yy - 1, 40, 13, 3, fill=PINK)
        p.text(M + 20, yy + 1.4, tag.upper(), 6.8, True, color='#ffffff', align='center')
        w = p.text(M + 48, yy, tit, 10, True, color='#1b4a8f')
        p.line(M + 48, yy + 12.5, M + 48 + w, yy + 12.5, '#1b4a8f', 0.6)
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
        p.text(cx, y + 6, t, 7.6, True, color='#ff8ab0')
    y += 20
    for i, (dia, qué, carga) in enumerate(C.SEMANA):
        h = 26
        if i % 2 == 0:
            p.rect(M, y, CW, h, fill=CARD)
        p.text(M + 10, y + 8, dia, 10, True, color=INK)
        p.text(M + 100, y + 8, qué, 9.8, color=INK)
        p.text(W - M - 80, y + 8, carga, 9.4, True, color=PINKD)
        y += h
    y += 26
    p.text(M, y, 'Según cuántas lleguen', 20, True, color=INK)
    y += 28
    p.para(M, y, 'Nunca se cancela un entrenamiento por falta de gente: se cambia el menú.',
           10.2, CW, 14, color=MUT)
    y += 22
    p.rect(M, y, CW, 20, fill=DARK)
    for cx, t in ((M + 10, 'LLEGARON'), (M + 90, 'QUÉ FICHAS'), (M + 320, 'EJERCICIO ESTRELLA')):
        p.text(cx, y + 6, t, 7.6, True, color='#ff8ab0')
    y += 20
    for i, (n, f, e) in enumerate(C.MENU):
        if i % 2 == 0:
            p.rect(M, y, CW, 24, fill=CARD)
        p.text(M + 10, y + 7, n, 10, True, color=PINK)
        p.text(M + 90, y + 7, f, 9.6, color=INK)
        p.text(M + 320, y + 7, e, 9.6, color=MUT)
        y += 24
    y += 26
    p.text(M, y, 'Una corrección por semana', 20, True, color=INK)
    y += 28
    p.rect(M, y, CW, 20, fill=DARK)
    for cx, t in ((M + 10, 'SEMANA'), (M + 90, 'PALABRA'), (M + 220, 'QUÉ SE OBSERVA')):
        p.text(cx, y + 6, t, 7.6, True, color='#ff8ab0')
    y += 20
    for i, (n, w2, q) in enumerate(C.CORRECCION):
        if i % 2 == 0:
            p.rect(M, y, CW, 22, fill=CARD)
        p.text(M + 10, y + 6, n, 9.8, True, color=PINK)
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
        p.text(cx + 6, y + 7, t, 7, True, color='#ff8ab0')
        cx += w
    y += 22
    for r in range(18):
        p.rect(M, y, CW, 30, stroke='#e9cfd9', lw=0.7)
        cx = M
        for t, w in cols[:-1]:
            cx += w
            p.line(cx, y, cx, y + 30, '#e9cfd9', 0.7)
        y += 30
    y += 24
    p.roundrect(M, y, CW, 46, 8, fill=CARD)
    p.text(M + 16, y + 15, 'Ver, copiar, repetir, grabarse y corregir. Eso es tener entrenador.',
           13, True, color=PINKD)
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
        p.text(cx + cwid / 2, cy + 74, 'FICHA ' + fn, 6.8, True, color=PINK, align='center')
        for j, ln in enumerate(p.wrap(tit, 8.4, cwid - 14, True)[:3]):
            p.text(cx + cwid / 2, cy + 86 + j * 10.5, ln, 8.4, True, color=INK, align='center')
        p.link(cx, cy, cwid, ch, url)
    footer(p, num, TOTAL)


# ---------------------------------------------------------------- láminas
PW, PH = 340.0, 604.0
PBG = '#150810'
PCARD = '#25101b'


def poster(doc, po, idx, total):
    p = doc.page(PW, PH)
    p.rect(0, 0, PW, PH, fill=PBG)
    p.rect(0, 0, PW, 5, fill=PINK)
    m = 20.0
    cw = PW - m * 2
    y = 26.0
    tw = pk.width(po['tag'], 7.6, True)
    p.roundrect(m, y, tw + 16, 15, 7.5, fill=PINK)
    p.text(m + 8, y + 3.2, po['tag'], 7.6, True, color='#ffffff')
    y += 26
    lines = po['title'].split('\n')
    ts = 30 if max(len(l) for l in lines) <= 15 else 24
    for l in lines:
        p.text(m, y, l, ts, True, color='#ffffff', maxw=cw)
        y += ts * 1.06
    y += 4
    p.text(m, y, po['sub'], 9.6, italic=True, color='#ff8ab0', maxw=cw)
    y += 22

    if po.get('kind') == 'cover':
        p.line(m, y, PW - m, y, '#3a222c', 1)
        y += 14
        p.text(m, y, 'LO QUE HAY ADENTRO', 8, True, color='#ff8ab0')
        y += 16
        for it in po['index']:
            p.text(m, y, it, 9.2, color='#f0e2e7', maxw=cw)
            y += 13.4
        y += 8
    else:
        pts_h = sum(p.rich_h(lead_split(a + ' ' + b), 9.4, cw - 22, 13) + 9
                    for a, b in po['points'])
        qbase = PH - 108
        if po.get('dia'):
            avail = qbase - y - pts_h - 18
            dh = min(dg.height_for(C.D[po['dia']], cw - 16), max(96, avail))
            p.roundrect(m, y, cw, dh + 16, 7, fill=PCARD)
            dg.render(p, C.D[po['dia']], m + 8, y + 8, cw - 16, dh)
            y += dh + 24
        for a, b in po['points']:
            p.rect(m, y + 1, 2.6, 11, fill=PINK)
            y = p.rich(m + 11, y, [(a + ' ', 'b'), (b, 'r')], 9.4, cw - 22, 13, '#f3e6ea') + 9

    qs = 62
    qy = PH - 84
    p.line(m, qy - 14, PW - m, qy - 14, '#3a222c', 1)
    pk.draw_qr(p, po['qr'], m, qy, qs, fg=PBG, bg='#ffffff')
    p.link(m, qy, qs, qs, po['qr'])
    p.text(m + qs + 12, qy + 6, 'ESCANEA Y VE EL VIDEO', 7.6, True, color=PINK)
    for j, ln in enumerate(p.wrap(po['qrlabel'], 9, cw - qs - 16)[:2]):
        p.text(m + qs + 12, qy + 20 + j * 12, ln, 9, color='#e7cdd6')
    p.text(m + qs + 12, qy + 48, 'SUB-17 FEMENIL · %d de %d' % (idx, total), 7.2, color='#8a6472')


# ---------------------------------------------------------------- HTML
def html():
    def esc(s):
        return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    fichas = []
    for d in C.DRILLS:
        pasos = ''.join('<li>%s</li>' % esc(s) for s in d['steps'])
        dosis = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v)) for k, v in d['dose'])
        links = ''.join(
            '<a class="v" href="%s" target="_blank" rel="noopener">'
            '<b>%s</b><span>%s</span><i>ver &rsaquo;</i></a>' % (u, esc(t.upper()), esc(ti))
            for (t, ti, u) in d['links'])
        fichas.append(
            '<article id="f%s"><header><span class="n">FICHA %s</span>'
            '<span class="cat">%s</span><span class="team">%s</span></header>'
            '<h2>%s</h2><p class="sub">%s</p><p class="idea">%s</p>'
            '<h3>Paso a paso</h3><ol>%s</ol>'
            '<div class="watch"><b>Qué mira la compañera</b>%s</div>'
            '<dl class="dose">%s</dl><div class="links">%s</div></article>'
            % (d['n'], d['n'], esc(d['cat']), esc(d['team']), esc(d['title']),
               esc(d['sub']), esc(d['idea']), pasos, esc(d['watch']), dosis, links))

    toc = ''.join('<a href="#f%s"><b>%s</b>%s</a>' % (d['n'], d['n'], esc(d['title']))
                  for d in C.DRILLS)

    css = """
*{box-sizing:border-box}body{margin:0;background:#150810;color:#f3e6ea;
font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:860px;margin:auto;padding:0 20px 60px}
header.top{padding:48px 0 28px;border-bottom:1px solid #3a222c}
.kick{color:#ff8ab0;font-size:12px;letter-spacing:.18em;font-weight:700}
h1{font-size:clamp(34px,9vw,60px);line-height:1.02;margin:14px 0 10px;letter-spacing:-.02em}
h1 em{color:#e5296b;font-style:normal}
.lede{color:#c9b1ba;max-width:52ch}
.dl{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0 6px}
.dl a{flex:1 1 240px;background:#e5296b;color:#fff;text-decoration:none;padding:16px 18px;
border-radius:12px;font-weight:700;display:block}
.dl a span{display:block;font-weight:400;font-size:13px;opacity:.85;margin-top:3px}
.dl a.alt{background:#25101b;color:#ff8ab0;border:1px solid #3a222c}
nav{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:0 20px;
padding:26px 0;border-bottom:1px solid #3a222c}
nav a{display:flex;gap:10px;padding:7px 0;color:#c9b1ba;text-decoration:none;font-size:14px}
nav a b{color:#e5296b}
article{padding:34px 0;border-bottom:1px solid #3a222c}
article header{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:11px;
letter-spacing:.12em;font-weight:700}
.n{background:#e5296b;color:#fff;padding:3px 8px;border-radius:4px}
.cat{color:#ff8ab0}.team{color:#8a6472;font-weight:400;letter-spacing:0}
h2{font-size:27px;margin:12px 0 4px;letter-spacing:-.01em}
.sub{color:#ff8ab0;font-style:italic;margin:0 0 12px}
.idea{color:#c9b1ba}
h3{font-size:12px;letter-spacing:.14em;color:#ff8ab0;margin:22px 0 8px}
ol{padding-left:22px;margin:0}ol li{margin-bottom:8px}
.watch{background:#1e2a10;border-left:3px solid #a8c94a;padding:12px 14px;border-radius:0 8px 8px 0;
margin:18px 0;color:#dcecc0;font-size:15px}
.watch b{display:block;font-size:11px;letter-spacing:.12em;color:#a8c94a;margin-bottom:4px}
.dose{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;
background:#25101b;padding:14px;border-radius:10px;margin:0 0 18px}
.dose dt{font-size:10px;letter-spacing:.12em;color:#8a6472}
.dose dd{margin:2px 0 0;font-weight:700}
.links{display:grid;gap:8px}
a.v{display:flex;align-items:center;gap:12px;background:#25101b;border:1px solid #3a222c;
border-radius:10px;padding:13px 15px;color:#f3e6ea;text-decoration:none}
a.v b{background:#e5296b;color:#fff;font-size:10px;padding:3px 7px;border-radius:4px;
letter-spacing:.1em}
a.v span{flex:1;font-weight:600}
a.v i{color:#ff8ab0;font-style:normal;font-size:13px}
footer{padding:44px 0;text-align:center;color:#8a6472;font-size:13px}
footer p{color:#e5296b;font-size:22px;font-weight:700;max-width:22ch;margin:0 auto 14px}
"""
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Entrena como las grandes · sub-17 femenil</title>'
            '<style>%s</style></head><body><div class="wrap">'
            '<header class="top"><div class="kick">SUB-17 FEMENIL · GUÍA DE TRABAJO</div>'
            '<h1>Entrena como <em>las grandes</em></h1>'
            '<p class="lede">Quince ejercicios con dibujo de cancha y el video de cada uno. '
            'Toca cualquier nombre de video y se abre en YouTube. Para los dibujos, '
            'descarga el PDF.</p>'
            '<div class="dl">'
            '<a href="guia-entrena-como-las-grandes.pdf">Descargar la guía en PDF'
            '<span>%d hojas con los dibujos, la dosis y los códigos QR</span></a>'
            '<a class="alt" href="posters-para-el-grupo.pdf">Descargar las láminas'
            '<span>%d láminas verticales para mandar al grupo</span></a>'
            '</div></header><nav>%s</nav>%s'
            '<footer><p>Ver, copiar, repetir, corregir.</p>'
            'Guía de entrenamiento · fútbol femenil sub-17</footer>'
            '</div></body></html>' % (css, TOTAL, len(C.POSTERS), toc, ''.join(fichas)))


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
    n1 = guia.save(os.path.join(OUT, 'guia-entrena-como-las-grandes.pdf'))
    links1 = sum(len(p.links) for p in guia.pages)

    lam = pk.Doc()
    for i, po in enumerate(C.POSTERS, 1):
        poster(lam, po, i, len(C.POSTERS))
    probs += check(lam, 'laminas', PW, PH)
    n2 = lam.save(os.path.join(OUT, 'posters-para-el-grupo.pdf'))
    links2 = sum(len(p.links) for p in lam.pages)

    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html())

    print('guia   : %d paginas, %d KB, %d enlaces' % (len(guia.pages), n1 // 1024, links1))
    print('laminas: %d paginas, %d KB, %d enlaces' % (len(lam.pages), n2 // 1024, links2))
    print('html   : %d KB' % (os.path.getsize(os.path.join(OUT, 'index.html')) // 1024))
    if probs:
        print('\n%d PROBLEMAS DE MAQUETACION:' % len(probs))
        for x in probs[:40]:
            print(' -', x)
        sys.exit(1)
    print('\nmaquetacion sin desbordes')
