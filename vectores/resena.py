"""Placa/sticker "Reseña en Google" con el logo NFConecta pequeño abajo, para impresión DTF UV.

Todo es opaco (sin brillos ni sombras semitransparentes). Genera versión con fondo blanco
y versión sin fondo. Uso: python3 vectores/resena.py
"""
import math
import os

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

import logo

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "resena")
W, H = 1000, 1040
NAVY, BLUE = "#0B1F4D", "#1E5BD8"

# Logotipo de Google (trazado de Iconify "logos:google", 512 x 168) con los colores oficiales.
GOOGLE = [
    ("#EA4335", "m496.052 102.672l14.204 9.469c-4.61 6.79-15.636 18.44-34.699 18.44c-23.672 0-41.301-18.315-41.301-41.614c0-24.793 17.816-41.613 39.308-41.613c21.616 0 32.206 17.193 35.633 26.475l1.869 4.735l-55.692 23.049c4.236 8.348 10.84 12.584 20.183 12.584c9.345 0 15.823-4.61 20.495-11.525M452.384 87.66l37.19-15.45c-2.056-5.17-8.16-8.845-15.45-8.845c-9.281 0-22.176 8.223-21.74 24.295"),
    ("#34A853", "M407.407 4.931h17.94v121.85h-17.94z"),
    ("#4285F4", "M379.125 50.593h17.318V124.6c0 30.711-18.128 43.357-39.558 43.357c-20.183 0-32.33-13.58-36.878-24.606l15.885-6.604c2.865 6.79 9.78 14.827 20.993 14.827c13.767 0 22.24-8.535 22.24-24.482v-5.98h-.623c-4.112 4.983-11.961 9.468-21.928 9.468c-20.807 0-39.87-18.128-39.87-41.488c0-23.486 19.063-41.8 39.870-41.8c9.905 0 17.816 4.423 21.928 9.282h.623zm1.245 38.499c0-14.702-9.78-25.417-22.239-25.417c-12.584 0-23.174 10.715-23.174 25.417c0 14.514 10.59 25.042 23.174 25.042c12.46.063 22.24-10.528 22.24-25.042"),
    ("#EA4335", "M218.216 88.78c0 23.984-18.688 41.613-41.613 41.613c-22.924 0-41.613-17.691-41.613-41.613c0-24.108 18.689-41.675 41.613-41.675c22.925 0 41.613 17.567 41.613 41.675m-18.19 0c0-14.95-10.84-25.23-23.423-25.23S153.18 73.830 153.18 88.78c0 14.826 10.84 25.23 23.423 25.23c12.584 0 23.423-10.404 23.423-25.23"),
    ("#FBBC05", "M309.105 88.967c0 23.984-18.689 41.613-41.613 41.613c-22.925 0-41.613-17.63-41.613-41.613c0-24.108 18.688-41.613 41.613-41.613c22.924 0 41.613 17.443 41.613 41.613m-18.253 0c0-14.95-10.839-25.23-23.423-25.23s-23.423 10.28-23.423 25.23c0 14.826 10.84 25.230 23.423 25.23c12.646 0 23.423-10.466 23.423-25.23"),
    ("#4285F4", "M66.59 112.328c-26.102 0-46.534-21.056-46.534-47.158c0-26.101 20.432-47.157 46.534-47.157c14.079 0 24.357 5.544 31.957 12.646l12.522-12.521C100.479 7.984 86.338.258 66.59.258C30.833.259.744 29.414.744 65.17s30.089 64.912 65.846 64.912c19.312 0 33.889-6.354 45.289-18.19c11.711-11.712 15.324-28.158 15.324-41.489c0-4.174-.498-8.472-1.059-11.649H66.59v17.318h42.423c-1.246 10.84-4.672 18.253-9.718 23.298c-6.105 6.168-15.76 12.958-32.705 12.958"),
]


class Font:
    def __init__(self, name):
        f = TTFont(os.path.join(BASE, "fuentes", name))
        self.glyphs, self.cmap = f.getGlyphSet(), f.getBestCmap()
        self.upm, self.cap = f["head"].unitsPerEm, f["OS/2"].sCapHeight

    def path(self, text, size, cx, cy):
        s = size / self.upm
        names = [self.cmap[ord(c)] for c in text]
        x = cx - sum(self.glyphs[n].width for n in names) * s / 2
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        for n in names:
            self.glyphs[n].draw(TransformPen(pen, (s, 0, 0, -s, x, cy + self.cap * s / 2)))
            x += self.glyphs[n].width * s
        return pen.getCommands()


BOLD, REG = Font("Poppins-Bold.ttf"), Font("Poppins-Regular.ttf")

DEFS = """<defs>
<linearGradient id="pastilla" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2D6BEA"/><stop offset="1" stop-color="#0A2E8A"/></linearGradient>
<linearGradient id="estrella" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FFD84D"/><stop offset="1" stop-color="#F5A100"/></linearGradient>
<linearGradient id="ola" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#0A2E8A"/><stop offset="1" stop-color="#2F7BF2"/></linearGradient>
</defs>"""


def estrella(cx, cy, r):
    pts = []
    for k in range(10):
        a = math.radians(-90 + 36 * k)
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return (f'<polygon points="{" ".join(pts)}" fill="url(#estrella)" stroke="#E08A00" '
            f'stroke-width="5" stroke-linejoin="round"/>')


def ondas_esquina():
    """Bandas azules en esquinas superior izquierda e inferior derecha."""
    banda = ('<path d="M0,0 H330 C220,40 90,150 0,300 Z" fill="url(#ola)"/>'
             '<path d="M0,345 C95,185 235,70 395,0 H440 C280,80 130,200 0,385 Z" fill="#8EC1FF"/>')
    return (f'<g transform="scale(0.85)">{banda}</g>'
            f'<g transform="rotate(180 {W / 2} {H / 2}) scale(0.85)">{banda}</g>')


def telefono(cx, cy):
    """Mano sosteniendo un celular, con ondas NFC (trazo lineal opaco)."""
    st = f'stroke="{NAVY}" stroke-width="11" stroke-linejoin="round" stroke-linecap="round"'
    fondo = (f'<circle cx="{cx}" cy="{cy}" r="150" fill="#E6F0FF"/>'
             f'<circle cx="{cx}" cy="{cy}" r="112" fill="#CFE2FF"/>')
    ondas = "".join(
        f'<path d="M{cx + r * math.cos(math.radians(-38)):.1f},{cy + r * math.sin(math.radians(-38)):.1f} '
        f'A{r},{r} 0 0 1 {cx + r * math.cos(math.radians(38)):.1f},{cy + r * math.sin(math.radians(38)):.1f}" '
        f'fill="none" stroke="{BLUE}" stroke-width="13" stroke-linecap="round"/>' for r in (92, 122, 152))
    g = (f'<g transform="translate({cx - 22} {cy}) rotate(-14)">'
         f'<rect x="-50" y="-95" width="100" height="185" rx="18" fill="#FFFFFF" {st}/>'
         f'<line x1="-14" y1="-76" x2="14" y2="-76" stroke="{NAVY}" stroke-width="8" stroke-linecap="round"/>'
         f'<path d="M-104,160 L-78,92 C-70,72 -58,58 -42,52 L18,40 C36,37 46,56 32,68 L-6,96 '
         f'C4,118 -4,150 -34,168 L-52,182" fill="#FFFFFF" {st}/>'
         + "".join(f'<rect x="38" y="{y}" width="34" height="24" rx="12" fill="#FFFFFF" {st}/>'
                   for y in (-10, 20, 50))
         + '</g>')
    return fondo + ondas + g


def svg(con_fondo):
    gw = 720
    gs = gw / 512
    google = "".join(f'<path fill="{c}" d="{dd}"/>' for c, dd in GOOGLE)
    estrellas = "".join(estrella(W / 2 + (k - 2) * 128, 452, 54) for k in range(5))
    px, py, pw, ph = 330, 575, 625, 170
    pastilla = (f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{ph / 2}" fill="url(#pastilla)"/>'
                f'<rect x="{px + 7}" y="{py + 7}" width="{pw - 14}" height="{ph - 14}" rx="{ph / 2 - 7}" '
                f'fill="none" stroke="#6FA4FF" stroke-width="3"/>'
                f'<path d="{BOLD.path("ACERCA TU CELULAR", 45, px + pw / 2, py + 62)}'
                f'{REG.path("y déjanos tu reseña", 43, px + pw / 2, py + 118)}" fill="#FFFFFF"/>')
    lw = 460
    ls = lw / logo.W
    marca = (f'<g transform="translate({(W - lw) / 2} {H - 150}) scale({ls:.5f})">{logo.fichas()}</g>')
    fondo = (f'<rect width="{W}" height="{H}" rx="40" fill="#FFFFFF"/>'
             f'<g clip-path="url(#recorte)">{ondas_esquina()}</g>') if con_fondo else ""
    clip = f'<clipPath id="recorte"><rect width="{W}" height="{H}" rx="40"/></clipPath>'
    defs = DEFS.replace("</defs>", clip + "</defs>") + "\n" + logo.DEFS
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n{defs}\n{fondo}\n'
            f'<g transform="translate({(W - gw) / 2} 105) scale({gs:.5f})">{google}</g>\n'
            f'{estrellas}\n{telefono(185, py + ph / 2)}\n{pastilla}\n{marca}\n</svg>\n')


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for nombre, con_fondo in (("resena_google_con_fondo", True), ("resena_google_sin_fondo", False)):
        src = os.path.join(OUT, f"{nombre}.svg")
        with open(src, "w") as f:
            f.write(svg(con_fondo))
        cairosvg.svg2pdf(url=src, write_to=os.path.join(OUT, f"{nombre}.pdf"))
        png = os.path.join(OUT, f"{nombre}.png")
        cairosvg.svg2png(url=src, write_to=png, output_width=4000)
        Image.open(png).save(png, dpi=(1000, 1000))  # 4000 px = 10 cm a 1000 ppp
