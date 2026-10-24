"""Check the display works and its colours are right.

Fills the screen red, green, blue then white, lighting the RGB LED the same
colour each time, so a swapped red/blue channel is obvious. Ends with a
"Hello CYD" caption and a red box.
"""
from time import sleep
import board
from ili9341 import color565

d = board.init_display()

for name, rgb, led in (("RED", (255, 0, 0), (1, 0, 0)),
                       ("GREEN", (0, 255, 0), (0, 1, 0)),
                       ("BLUE", (0, 0, 255), (0, 0, 1)),
                       ("WHITE", (255, 255, 255), (1, 1, 1))):
    board.led(*led)
    d.fill_rectangle(0, 0, board.WIDTH, board.HEIGHT, color565(*rgb))
    print(name)
    sleep(1)

board.led(0, 0, 0)
d.clear()
d.draw_text8x8(10, 10, "Hello CYD", color565(255, 255, 255))
d.fill_rectangle(10, 30, 100, 50, color565(255, 0, 0))
print("done")
