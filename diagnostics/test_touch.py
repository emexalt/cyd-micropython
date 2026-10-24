"""Check the touch controller responds.

For 20 seconds, prints every raw reading alongside where board.py maps it on
screen, and draws a green dot there. If the dots land away from your stylus,
run calibrate_touch.py.
"""
from time import sleep, ticks_ms, ticks_diff
import board
from ili9341 import color565

d = board.init_display()
t = board.init_touch()
d.clear()
d.draw_text8x8(10, 10, "Touch the screen", color565(255, 255, 255))

print("Touch the screen now (20s)...")
start = ticks_ms()
seen = 0
while ticks_diff(ticks_ms(), start) < 20000:
    raw = t.raw_touch()
    if raw:
        x, y = t.normalize(*raw)
        print("raw", raw, "-> x,y", (x, y))
        d.fill_circle(x, y, 3, color565(0, 255, 0))
        seen += 1
    sleep(0.05)
print("samples:", seen)
