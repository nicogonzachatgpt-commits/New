# -*- coding: utf-8 -*-
"""
Estructura lineal del entramado de papel.

Transcribe el tejido de la foto (urdimbre vertical que flota sobre 2 tramas
-a veces 3, a veces 1- y pasa por debajo de 1, con desfases en escalera entre
columnas y flotes horizontales de trama sobre 2 urdimbres) a un dibujo lineal:
rectangulos de contorno negro sobre blanco, a sangre completa en hoja A4,
como el PDF de referencia (estructura_lineal.pdf).

Proporciones tomadas de la foto: 18 urdimbres x 39 tramas en A4; la tira de
trama es mas angosta que la de urdimbre (alto de celda ~0.66 del ancho).

Genera: estructura_lineal_entramado.pdf / .svg / .png
"""
import random
import pymupdf

# ---------------- parametros ----------------
W, H = 595.276, 841.890          # A4 en puntos
COLS = 18                        # columnas de urdimbre (como en la foto)
CW = 34.0                        # ancho de tira de urdimbre
CH = 22.4                        # alto de tira de trama (mas angosta, como en la foto)
ROWS = 39                        # filas de trama
X0, Y0 = -8.0, -6.0              # corrimiento para que el tejido sangre los 4 bordes
SEED = 5
P_PAR = 0.26                     # prob. de aceptar un flote horizontal de 2
STROKE = (0.137, 0.122, 0.125)   # negro de la referencia (#231F20)
LINE_W = 1.1

rng = random.Random(SEED)

# ---------------- generacion de la estructura ----------------
# Columna = flotes verticales (sobre 3 tramas la mayoria, sobre 2 o 1 a veces)
# separados por exactamente 1 pasada de trama. El alto de cada flote se elige
# de modo que la proxima pasada caiga 1 fila arriba o abajo de una pasada de
# la columna anterior (escalera diagonal, como el tejido a mano de la foto);
# de vez en cuando cae en la misma fila y forma un flote horizontal de 2.


def build_column(prev_u, prev2_u):
    floats, unders = [], set()
    r = -rng.randint(1, 4)                       # arranca fuera de la hoja
    while r < ROWS + 1:
        opciones = []
        for f, w in ((3, 3.6), (2, 1.5), (1, 0.15), (4, 0.45)):
            u = r + f
            if u in prev_u and u in prev2_u:     # nunca flote horizontal de 3
                continue
            if u in prev_u:                      # formaria flote horizontal de 2
                w *= P_PAR / (1 - P_PAR)
            elif (u - 1) in prev_u or (u + 1) in prev_u:
                w *= 3.0                         # continua la escalera diagonal
            opciones.append((f, w))
        if not opciones:
            opciones = [(2, 1.0)]
        total = sum(w for _, w in opciones)
        x = rng.random() * total
        for f, w in opciones:
            x -= w
            if x <= 0:
                break
        floats.append((r, f))
        r += f
        if r < ROWS + 1:
            unders.add(r)
        r += 1
    return floats, unders


columns = []
prev_u, prev2_u = set(), set()
for c in range(COLS):
    fl, un = build_column(prev_u, prev2_u)
    columns.append((fl, un))
    prev2_u, prev_u = prev_u, un

# rectangulos de urdimbre (verticales)
rects = []
for c, (floats, _) in enumerate(columns):
    for r, f in floats:
        rects.append((X0 + c * CW, Y0 + r * CH, CW, f * CH))

# rectangulos de trama: agrupa pasadas contiguas de una misma fila (largo 1 o 2)
for r in range(-10, ROWS + 2):
    c = 0
    while c < COLS:
        if r in columns[c][1]:
            run = 1
            while c + run < COLS and r in columns[c + run][1]:
                run += 1
            rects.append((X0 + c * CW, Y0 + r * CH, run * CW, CH))
            c += run
        else:
            c += 1

# ---------------- salida PDF ----------------
doc = pymupdf.open()
page = doc.new_page(width=W, height=H)
shape = page.new_shape()
for x, y, w, h in rects:
    shape.draw_rect(pymupdf.Rect(x, y, x + w, y + h))
shape.finish(color=STROKE, fill=(1, 1, 1), width=LINE_W)
shape.commit()
doc.save("estructura_lineal_entramado.pdf")

# ---------------- salida SVG ----------------
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="white"/>']
for x, y, w, h in rects:
    svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
               f'fill="white" stroke="#231F20" stroke-width="{LINE_W}"/>')
svg.append('</svg>')
with open("estructura_lineal_entramado.svg", "w") as f:
    f.write("".join(svg))

# ---------------- vista previa PNG ----------------
pix = doc[0].get_pixmap(dpi=150)
pix.save("estructura_lineal_entramado.png")
print(f"listo: {len(rects)} piezas")
