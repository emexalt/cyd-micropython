"""Runs at boot: clears the screen and draws a green dot wherever you touch.

Press the reset button to clear the screen. To stop this running at boot,
delete it from the board: mpremote connect /dev/ttyUSB0 rm main.py
"""
from time import sleep
import board
from ili9341 import color565

WHITE = color565(255, 255, 255)
GREEN = color565(0, 255, 0)

d = board.init_display()
t = board.init_touch()
d.clear()
d.draw_text8x8(10, 10, "CYD ready - touch to draw", WHITE)
board.led(0, 1, 0)
sleep(0.3)
board.led(0, 0, 0)

while True:
    raw = t.raw_touch()
    if raw:
        x, y = t.normalize(*raw)
        d.fill_circle(x, y, 3, GREEN)
    sleep(0.02)
