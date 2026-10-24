"""Fill the screen with an 8x6 grid of colour swatches.

Hue runs left to right starting at red; brightness fades top to bottom. A
quick check that colours, orientation and the screen edges are all right.
"""
import board
from ili9341 import color565

SIZE = 40
COLS, ROWS = board.WIDTH // SIZE, board.HEIGHT // SIZE


def hsv(h, s, v):
    """h in 0..1, s and v in 0..1 -> (r, g, b) 0..255."""
    i = int(h * 6)
    f = h * 6 - i
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))[i % 6]
    return int(r * 255), int(g * 255), int(b * 255)


d = board.init_display()
for row in range(ROWS):
    for col in range(COLS):
        rgb = hsv(col / COLS, 1, 1 - row * 0.15)
        d.fill_rectangle(col * SIZE, row * SIZE, SIZE - 2, SIZE - 2, color565(*rgb))
print("drew %dx%d grid" % (COLS, ROWS))
