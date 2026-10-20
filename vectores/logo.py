"""Logo NFConecta (fila de fichas) para impresión DTF UV.

Todo es opaco: sin sombras, brillos ni degradados que se desvanezcan a transparente,
porque en DTF UV la transparencia parcial imprime mal sobre la capa de blanco.
Uso: python3 vectores/logo.py
"""
import os

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
FONT = TTFont("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
GLYPHS, CMAP = FONT.getGlyphSet(), FONT.getBestCmap()
UPM, CAP = FONT["head"].unitsPerEm, FONT["OS/2"].sCapHeight

TILES = [("N", "1", True), ("F", "4", True), ("C", "3", True), ("O", "1", False),
         ("N", "1", False), ("E", "1", False), ("C", "3", False), ("T", "1", False), ("A", "1", False)]
S, G, R, BEVEL = 100.0, 8.0, 9.0, 5.0  # unidades: ficha de 100
W = len(TILES) * S + (len(TILES) - 1) * G
H = S


def text(t, size, cx, cy):
    s = size / UPM
    names = [CMAP[ord(c)] for c in t]
    x = cx - sum(GLYPHS[n].width for n in names) * s / 2
    pen = SVGPathPen(GLYPHS, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    for n in names:
        GLYPHS[n].draw(TransformPen(pen, (s, 0, 0, -s, x, cy + CAP * s / 2)))
        x += GLYPHS[n].width * s
    return pen.getCommands()


def svg():
    defs = """<defs>
<linearGradient id="azul" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#3A6FE0"/><stop offset="0.5" stop-color="#1F4FC2"/><stop offset="1" stop-color="#0E2F86"/></linearGradient>
<linearGradient id="azul-borde" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#6E9BFF"/><stop offset="1" stop-color="#0A2263"/></linearGradient>
<linearGradient id="marfil" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FBF1D8"/><stop offset="0.55" stop-color="#F1E2BC"/><stop offset="1" stop-color="#DDC795"/></linearGradient>
<linearGradient id="marfil-borde" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FFF9EA"/><stop offset="1" stop-color="#B89E66"/></linearGradient>
</defs>"""
    parts = []
    for i, (letra, num, azul) in enumerate(TILES):
        x = i * (S + G)
        borde, cara, tinta = ("azul-borde", "azul", "#FFFFFF") if azul else ("marfil-borde", "marfil", "#111111")
        parts.append(
            f'<g><rect x="{x}" y="0" width="{S}" height="{S}" rx="{R}" fill="url(#{borde})"/>'
            f'<rect x="{x + BEVEL}" y="{BEVEL}" width="{S - 2 * BEVEL}" height="{S - 2 * BEVEL}" '
            f'rx="{R - BEVEL / 2}" fill="url(#{cara})"/>'
            f'<path d="{text(letra, 68, x + S / 2 - 3, S / 2 - 2)}{text(num, 21, x + S - 17, S - 20)}" fill="{tinta}"/></g>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W:g} {H:g}" width="{W:g}" height="{H:g}">\n{defs}\n' + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "nfconecta_logo.svg")
    with open(src, "w") as f:
        f.write(svg())
    cairosvg.svg2pdf(url=src, write_to=os.path.join(OUT, "nfconecta_logo.pdf"))
    # PNG a 1200 ppp para 75 mm de ancho (tamaño en tarjeta) y una versión grande de 8000 px.
    for nombre, px, dpi in (("nfconecta_logo_75mm_1200ppp.png", round(75 / 25.4 * 1200), 1200),
                            ("nfconecta_logo_8000px.png", 8000, 600)):
        path = os.path.join(OUT, nombre)
        cairosvg.svg2png(url=src, write_to=path, output_width=px)
        Image.open(path).save(path, dpi=(dpi, dpi))
