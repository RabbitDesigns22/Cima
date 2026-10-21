"""Calca el logo original (logo_original.jpg) a curvas vectoriales con potrace -> trazado.json.

Se amplía 8x antes de calcar para que las curvas sigan el borde con precisión.
Uso: python3 vectores/rabbit/fuente/trazar.py
"""
import json
import os

import numpy as np
import potrace
from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
S, X0, Y0, X1, Y1 = 8, 160, 290, 920, 690  # zona del logo en el original de 1080 x 1080

im = Image.open(os.path.join(AQUI, "logo_original.jpg")).convert("L").crop((X0, Y0, X1, Y1))
im = im.resize((im.width * S, im.height * S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(S * 1.0))
blanco = np.asarray(im) > 128
# potracer toma los píxeles False como figura: se invierte para calcar lo blanco (el logo).
curvas = potrace.Bitmap(~blanco).trace(turdsize=200, alphamax=1.15, opticurve=True, opttolerance=0.25)


def f(p):
    return f"{p.x / S + X0:.3f},{p.y / S + Y0:.3f}"


trazos = []
for c in curvas:
    d, ys = "M" + f(c.start_point), [c.start_point.y]
    for s in c.segments:
        if s.is_corner:
            d += "L" + f(s.c) + "L" + f(s.end_point)
        else:
            d += "C" + f(s.c1) + " " + f(s.c2) + " " + f(s.end_point)
        ys.append(s.end_point.y)
    trazos.append((min(ys) / S + Y0, d + "Z"))

with open(os.path.join(AQUI, "trazado.json"), "w") as fh:
    json.dump(trazos, fh)
print(len(trazos), "trazos")
