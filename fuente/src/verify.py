# -*- coding: utf-8 -*-
"""Verificación final: estructura de los PDF y lectura de todos los QR."""
import os
import re
import sys
import zlib

sys.path.insert(0, '/projects/sandbox/fuente/src')
sys.path.insert(0, '/projects/sandbox/fuente')
import pdfkit as pk
import content as C
from test_pdfkit import decode

fails = []
OUT = '/projects/sandbox'

for name in ('guia-entrena-como-las-grandes.pdf', 'posters-para-el-grupo.pdf'):
    path = os.path.join(OUT, name)
    raw = open(path, 'rb').read()
    if not raw.startswith(b'%PDF-1.4'):
        fails.append(name + ': cabecera')
    if not raw.rstrip().endswith(b'%%EOF'):
        fails.append(name + ': sin %%EOF')
    sx = int(re.search(rb'startxref\s+(\d+)', raw).group(1))
    if raw[sx:sx + 4] != b'xref':
        fails.append(name + ': startxref')
    offs = [int(m.group(1)) for m in re.finditer(rb'^(\d{10}) 00000 n $', raw[sx:], re.M)]
    for i, off in enumerate(offs, 1):
        if not raw[off:off + 30].startswith(b'%d 0 obj' % i):
            fails.append('%s: offset del objeto %d' % (name, i))
    npages = int(re.search(rb'/Type /Pages /Count (\d+)', raw).group(1))
    nreal = len(re.findall(rb'/Type /Page /Parent', raw))
    if npages != nreal:
        fails.append('%s: Count %d != %d paginas' % (name, npages, nreal))
    nlinks = len(re.findall(rb'/Subtype /Link', raw))

    # descomprimir los streams y revisar operadores
    bt = et = 0
    nbad = 0
    for m in re.finditer(rb'<< /Length \d+ /Filter /FlateDecode >>\nstream\n(.*?)\nendstream',
                         raw, re.S):
        try:
            txt = zlib.decompress(m.group(1)).decode('latin-1')
        except Exception as e:
            fails.append('%s: stream ilegible (%s)' % (name, e))
            continue
        bt += txt.count('BT ')
        et += txt.count(' ET')
        for tok in re.findall(r'(?<![\w./])(nan|inf|-inf)(?![\w.])', txt):
            nbad += 1
    if bt != et:
        fails.append('%s: BT/ET descompensados (%d/%d)' % (name, bt, et))
    if nbad:
        fails.append('%s: %d numeros invalidos' % (name, nbad))
    print('%-38s %2d paginas · %3d KB · %3d enlaces · BT=ET=%d'
          % (name, npages, len(raw) // 1024, nlinks, bt))

# ---- todos los QR
urls = set()
for d in C.DRILLS:
    urls.add(d['qr'])
    for (_, _, u) in d['links']:
        urls.add(u)
for po in C.POSTERS:
    urls.add(po['qr'])
ok = 0
for u in sorted(urls):
    try:
        size, m = pk.qr_matrix(u)
        back = decode(size, m)
    except Exception as e:
        fails.append('QR %s: %s' % (u, e))
        continue
    if back == u:
        ok += 1
    else:
        fails.append('QR mal: %r != %r' % (back, u))
print('\nQR verificados con decodificador independiente: %d/%d' % (ok, len(urls)))

html = open(os.path.join(OUT, 'index.html'), encoding='utf-8').read()
if html.count('<article') != len(C.DRILLS):
    fails.append('html: fichas incompletas')
if '<script' in html:
    fails.append('html: contiene JavaScript')
for tag in ('div', 'article', 'ol', 'dl', 'nav'):
    a, b = html.count('<%s' % tag), html.count('</%s>' % tag)
    if a != b:
        fails.append('html: <%s> %d abiertas / %d cerradas' % (tag, a, b))
print('index.html: %d fichas, sin JavaScript, etiquetas balanceadas' % html.count('<article'))

print()
if fails:
    print('%d FALLAS:' % len(fails))
    for f in fails[:30]:
        print(' -', f)
    sys.exit(1)
print('TODO VERIFICADO')
