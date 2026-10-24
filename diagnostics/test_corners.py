"""Check the screen orientation set in board.py.

With the board the way you'll use it, you should see a white square top-left,
red top-right, green bottom-left, blue bottom-right, yellow in the centre,
and "TOP" and "BOTTOM" the right way up. If the picture is upside down, set
ROTATION = 180 in board.py. If it's sideways, see test_flips.py.
"""
import board
from ili9341 import color565

d = board.init_display()
WHITE, RED = color565(255, 255, 255), color565(255, 0, 0)
GREEN, BLUE = color565(0, 255, 0), color565(0, 0, 255)
YELLOW = color565(255, 255, 0)
W, H, S = board.WIDTH, board.HEIGHT, 40

d.clear()
d.fill_rectangle(0, 0, S, S, WHITE)
d.fill_rectangle(W - S, 0, S, S, RED)
d.fill_rectangle(0, H - S, S, S, GREEN)
d.fill_rectangle(W - S, H - S, S, S, BLUE)
d.fill_rectangle(W // 2 - 10, H // 2 - 10, 20, 20, YELLOW)
d.draw_text8x8(50, 10, "TOP", WHITE)
d.draw_text8x8(50, H - 20, "BOTTOM", WHITE)
print("drawn", d.width, d.height, "MADCTL", hex(d.rotation))
