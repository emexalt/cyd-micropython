"""Collect touch calibration readings.

Run from your computer with the output saved:

    mpremote connect /dev/ttyUSB0 run calibrate_touch.py | tee cal.txt

Nine targets appear one at a time. Press the middle of each with a stylus and
hold still until the LED goes off. Then run fit_touch.py on cal.txt.
"""
from time import sleep, ticks_ms, ticks_diff
import board
from ili9341 import color565

d = board.init_display()
t = board.init_touch()
WHITE = color565(255, 255, 255)
RED = color565(255, 0, 0)

# A 3x3 grid of targets, 20px in from the screen edges
W, H, M = board.WIDTH, board.HEIGHT, 20
xs_t, ys_t = (M, W // 2, W - M), (M, H // 2, H - M)
targets = [("%d,%d" % (x, y), x, y) for y in ys_t for x in xs_t]


def wait_release():
    while t.raw_touch():
        sleep(0.05)


def read_touch(timeout_ms=30000, n=10, spread=40):
    """Mean of n consecutive raw samples that all agree within `spread`.

    The XPT2046 returns floating values when untouched, so only a steady
    press passes; None on timeout.
    """
    start = ticks_ms()
    xs, ys = [], []
    while ticks_diff(ticks_ms(), start) < timeout_ms:
        raw = t.raw_touch()
        if raw:
            xs.append(raw[0])
            ys.append(raw[1])
            xs, ys = xs[-n:], ys[-n:]
            if (len(xs) == n and max(xs) - min(xs) <= spread
                    and max(ys) - min(ys) <= spread):
                return sum(xs) // n, sum(ys) // n
        else:
            xs, ys = [], []
        sleep(0.02)
    return None


for name, x, y in targets:
    d.clear()
    d.draw_text8x8(60, 60, "Touch the dot (%s)" % name, WHITE)
    d.fill_circle(x, y, 8, RED)
    d.fill_circle(x, y, 2, WHITE)
    print("TARGET", name, x, y)
    board.led(1, 0, 0)
    raw = read_touch()
    board.led(0, 0, 0)
    print("RAW", name, raw)
    if raw is None:
        print("  no steady touch within 30s; this target will be skipped")
    wait_release()
    sleep(0.3)

d.clear()
d.draw_text8x8(10, 10, "Calibration done", WHITE)
print("done")
