#!/usr/bin/env python3
"""Retrato ASCII animado a partir de una foto con el fondo ya quitado (PNG con alfa).

Solo se ejecuta en local, cuando cambia la foto (necesita Pillow):
  uvx --python 3.11 --from "rembg[cpu,cli]" rembg i -m u2net_human_seg foto.png recorte.png
  uv run --with pillow scripts/portrait.py recorte.png
STATIC=1 emite el retrato ya impreso.
"""
import html
import os
import sys

from PIL import Image, ImageOps

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ascii-portrait.svg")
STATIC = bool(os.environ.get("STATIC"))
USER = "anthonygrullona"

COLS, ART = 128, 800                    # más columnas = más detalle; el arte siempre mide ART px
CW = ART / COLS
CH = CW * 15 / 8                        # proporción de un carácter monoespaciado
ROWS = round(ART / CH)
RAMP = " .`:-=+*cs#%@"                  # tinta clara sobre fondo oscuro: piel clara -> carácter denso
GAMMA = 0.9                             # <1 aclara los medios
W, H, PAD, TOP = 840, 880, 20, 40
INK, MUTED, FRAME, BG, BG2 = "#c9d1d9", "#7d8590", "#30363d", "#0d1117", "#111722"

im = Image.open(SRC).convert("RGBA")
white = Image.new("RGBA", im.size, "white")
gray = Image.alpha_composite(white, im).convert("L")
gray = ImageOps.equalize(gray, mask=im.getchannel("A").point(lambda a: 255 if a > 128 else 0))
gray = gray.resize((COLS, ROWS), Image.LANCZOS)
px = gray.load()
alpha = im.getchannel("A").resize((COLS, ROWS), Image.LANCZOS).load()  # fuera del recorte, espacio

rows = []
for y in range(ROWS):
    line = ""
    for x in range(COLS):
        lum = (px[x, y] / 255) ** GAMMA
        line += " " if alpha[x, y] < 128 else RAMP[max(1, round(lum * (len(RAMP) - 1)))]
    rows.append(line)

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
       f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
       f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
       f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
       f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
       f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="{FRAME}"/>']
out += [f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>' for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])]
out.append(f'<text x="{W/2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">{USER}@github: ~$ ./retrato.sh</text>')

row_dur = 5.5 / ROWS                    # todo el retrato se imprime en ~5,5 s, una fila tras otra
for r, line in enumerate(rows):
    if not line.strip():
        continue
    y = TOP + r * CH
    txt = (f'<text xml:space="preserve" x="{PAD}" y="{y + CH*.74:.1f}" fill="{INK}" font-size="{CH*.86:.1f}" '
           f'textLength="{ART}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC:
        out.append(txt)
        continue
    t = r * row_dur
    out.append(f'<clipPath id="r{r}"><rect x="{PAD}" y="{y:.1f}" height="{CH:.2f}" width="0"><animate '
               f'attributeName="width" from="0" to="{ART}" begin="{t:.3f}s" dur="{row_dur:.3f}s" fill="freeze"/>'
               f'</rect></clipPath><g clip-path="url(#r{r})">{txt}</g>')

sy = TOP + ROWS * CH + 18
out.append(f'<line x1="0" y1="{sy - 18:.1f}" x2="{W}" y2="{sy - 18:.1f}" stroke="{FRAME}"/>')
out.append(f'<text x="{PAD}" y="{sy + 4:.1f}" fill="{MUTED}" font-size="13">{USER}@github:~$ whoami '
           f'<tspan fill="{INK}">Anthony Grullón</tspan></text>')
assert sy + 12 < H, "el retrato no cabe en el lienzo"
out.append("</svg>")
open(OUT, "w").write("".join(out))
print(f"ascii-portrait.svg: {ROWS} filas x {COLS} columnas")
