"""Genera los vectores (SVG, texto convertido a trazos) de la tarjeta NFConecta.

Tamaño tarjeta CR80: 85.6 x 54 mm, radio de esquina 3.18 mm. Unidades en mm.
Capas por color (convención láser):
  - Rojo  #FF0000 hairline : CORTE (contorno de la tarjeta)
  - Negro #000000 relleno  : GRABADO
  - Azul  #1E3F8A relleno  : GRABADO + RELLENO DE COLOR
Uso: python3 vectores/generar.py
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = TTFont("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()
UPM = FONT["head"].unitsPerEm
CAP = FONT["OS/2"].sCapHeight

W, H, R = 85.6, 54.0, 3.18
BLUE, BLACK, CUT = "#1E3F8A", "#000000", "#FF0000"


def text_path(text, size, cx, cy):
    """Texto centrado (horizontal y por altura de mayúscula) como path SVG."""
    s = size / UPM
    names = [CMAP[ord(c)] for c in text]
    width = sum(GLYPHS[n].width for n in names) * s
    x = cx - width / 2
    base = cy + CAP * s / 2
    pen = SVGPathPen(GLYPHS, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
    for n in names:
        GLYPHS[n].draw(TransformPen(pen, (s, 0, 0, -s, x, base)))
        x += GLYPHS[n].width * s
    return pen.getCommands()


def rrect(x, y, w, h, r):
    return (f"M{x+r:.3f},{y:.3f}H{x+w-r:.3f}A{r},{r} 0 0 1 {x+w:.3f},{y+r:.3f}"
            f"V{y+h-r:.3f}A{r},{r} 0 0 1 {x+w-r:.3f},{y+h:.3f}H{x+r:.3f}"
            f"A{r},{r} 0 0 1 {x:.3f},{y+h-r:.3f}V{y+r:.3f}A{r},{r} 0 0 1 {x+r:.3f},{y:.3f}Z")


def arc_band(cx, cy, r, t, a0, a1):
    """Banda de arco (grosor t) con extremos redondeados, como trazo cerrado."""
    ro, ri, rc = r + t / 2, r - t / 2, t / 2
    p = lambda rr, a: (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
    large = 1 if abs(a1 - a0) > 180 else 0
    o0, o1, i1, i0 = p(ro, a0), p(ro, a1), p(ri, a1), p(ri, a0)
    return (f"M{o0[0]:.3f},{o0[1]:.3f}A{ro:.3f},{ro:.3f} 0 {large} 1 {o1[0]:.3f},{o1[1]:.3f}"
            f"A{rc},{rc} 0 0 1 {i1[0]:.3f},{i1[1]:.3f}"
            f"A{ri:.3f},{ri:.3f} 0 {large} 0 {i0[0]:.3f},{i0[1]:.3f}"
            f"A{rc},{rc} 0 0 1 {o0[0]:.3f},{o0[1]:.3f}Z")


def svg(body, wood):
    bg = f'<path d="{rrect(0, 0, W, H, R)}" fill="#D9B27C"/>' if wood else ""
    cut = f'<path id="corte" d="{rrect(0, 0, W, H, R)}" fill="none" stroke="{CUT}" stroke-width="0.01"/>'
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
            f'{bg}\n{body}\n{cut}\n</svg>\n')


def frente():
    tiles = [("N", "1", True), ("F", "4", True), ("C", "3", True), ("O", "1", False),
             ("N", "1", False), ("E", "1", False), ("C", "3", False), ("T", "1", False), ("A", "1", False)]
    s, g, r = 7.6, 0.5, 0.8
    x0 = (W - (len(tiles) * s + (len(tiles) - 1) * g)) / 2
    y0 = H / 2 - s / 2 + 1.0
    color, grabado = [], []
    for i, (letra, num, azul) in enumerate(tiles):
        x = x0 + i * (s + g)
        glyph = text_path(letra, 6.2, x + s / 2 - 0.25, y0 + s / 2 - 0.2)
        numero = text_path(num, 1.7, x + s - 1.25, y0 + s - 1.4)
        if azul:
            # Ficha grabada y rellena en azul; letra y número quedan en madera (calado).
            color.append(f'<path d="{rrect(x, y0, s, s, r)}{glyph}{numero}" fill-rule="evenodd"/>')
        else:
            inner = rrect(x + 0.25, y0 + 0.25, s - 0.5, s - 0.5, r - 0.25)
            grabado.append(f'<path d="{rrect(x, y0, s, s, r)}{inner}" fill-rule="evenodd"/>')
            grabado.append(f'<path d="{glyph}{numero}"/>')
    return (f'<g id="relleno-azul" fill="{BLUE}">{"".join(color)}</g>\n'
            f'<g id="grabado" fill="{BLACK}">{"".join(grabado)}</g>')


def reverso():
    cx, cy = W / 2, H / 2
    parts = []
    # Marca N: cuadro redondeado grabado con la N calada (madera).
    b, t = 15.0, 2.4
    x0, y0 = cx - b / 2, cy - b / 2
    m = 3.2
    l, rr, top, bot = x0 + m, x0 + b - m, y0 + m, y0 + b - m
    n = (f"M{l:.3f},{bot:.3f}V{top:.3f}H{l+t:.3f}L{rr-t:.3f},{bot-t*1.6:.3f}V{top:.3f}H{rr:.3f}"
         f"V{bot:.3f}H{rr-t:.3f}L{l+t:.3f},{top+t*1.6:.3f}V{bot:.3f}Z")
    parts.append(f'<path d="{rrect(x0, y0, b, b, 2.6)}{n}" fill-rule="evenodd"/>')
    # Ondas: 3 por lado.
    for radio, ang in ((12.0, 46), (16.6, 40), (21.2, 34)):
        parts.append(f'<path d="{arc_band(cx, cy, radio, 2.2, -ang, ang)}"/>')
        parts.append(f'<path d="{arc_band(cx, cy, radio, 2.2, 180 - ang, 180 + ang)}"/>')
    return f'<g id="grabado" fill="{BLACK}">{"".join(parts)}</g>'


if __name__ == "__main__":
    import cairosvg

    for nombre, fn in (("frente", frente), ("reverso", reverso)):
        body = fn()
        for sufijo, wood in (("", False), ("_preview", True)):
            path = os.path.join(OUT, f"nfconecta_{nombre}{sufijo}.svg")
            with open(path, "w") as f:
                f.write(svg(body, wood))
        cairosvg.svg2pdf(url=os.path.join(OUT, f"nfconecta_{nombre}.svg"),
                         write_to=os.path.join(OUT, f"nfconecta_{nombre}.pdf"))
        cairosvg.svg2png(url=os.path.join(OUT, f"nfconecta_{nombre}_preview.svg"),
                         write_to=os.path.join(OUT, f"nfconecta_{nombre}_preview.png"),
                         output_width=1712)
