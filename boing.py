"""Amiga "Boing" ball demo for the CYD.

The ball is a sphere whose surface coordinates are precomputed once. Each frame
a viper loop shades only the box covering the ball's old and new positions
(ball, shadow and grid) into a small buffer, which goes out as one SPI block.
"""
import gc
import math
from array import array
from time import ticks_us, ticks_diff, sleep_ms
import micropython
import board
from ili9341 import color565

DURATION_S = 30  # how long to run; 0 = until Ctrl-C
SPI_BAUD = 40_000_000  # faster than board.TFT_BAUD; drop to 20 MHz if you see speckles

W, H = board.WIDTH, board.HEIGHT
D = 64            # ball diameter
SX, SY = 14, 10   # shadow offset
GRID = 16         # grid spacing in pixels
MAX_DT = 0.04     # cap a frame's time step so the dirty box stays bounded

# Dirty box limit: ball + shadow + the largest per-frame step
MAX_BOX_W, MAX_BOX_H = D + SX + 8, D + SY + 22
BOUNDS_X = W - D - SX
BOUNDS_Y = H - D - SY

SPEED_X = 120     # px/s
GRAVITY = 600     # px/s^2
SPIN = 110        # texture units/s (256 = one full turn)

RED = color565(220, 20, 20)
WHITE = color565(245, 245, 245)
BG = color565(170, 170, 170)
LINE = color565(150, 0, 170)
BG_SHADOW = color565(95, 95, 95)
LINE_SHADOW = color565(80, 0, 90)


def build_texture():
    """Per ball pixel: longitude and latitude (0..255) on a tilted sphere.

    Latitude 255 marks pixels outside the ball.
    """
    tex = bytearray(2 * D * D)
    tilt = math.radians(17)
    ca, sa = math.cos(tilt), math.sin(tilt)
    r = D / 2
    for j in range(D):
        for i in range(D):
            nx, ny = (i + 0.5 - r) / r, (j + 0.5 - r) / r
            k = j * D + i
            d2 = nx * nx + ny * ny
            if d2 >= 1:
                tex[D * D + k] = 255
                continue
            nz = math.sqrt(1 - d2)
            x1, y1 = nx * ca + ny * sa, -nx * sa + ny * ca
            lon = math.atan2(x1, nz)
            lat = math.asin(y1)
            tex[k] = int((lon + math.pi) / (2 * math.pi) * 255.99)
            tex[D * D + k] = min(254, int((lat + math.pi / 2) / math.pi * 256))
    return tex


@micropython.viper
def render(buf: ptr8, tex: ptr8, p: ptr32):
    """Shade the box p[0..3] = (width, height, x, y) into buf as RGB565."""
    bw = int(p[0])
    bh = int(p[1])
    bx = int(p[2])
    by = int(p[3])
    px = int(p[4])
    py = int(p[5])
    phase = int(p[6])
    c_red = int(p[7])
    c_white = int(p[8])
    c_bg = int(p[9])
    c_line = int(p[10])
    c_bg_sh = int(p[11])
    c_line_sh = int(p[12])
    shx = int(p[13])
    shy = int(p[14])
    n = 0
    for j in range(bh):
        y = by + j
        v = y - py
        v2 = v - shy
        for i in range(bw):
            x = bx + i
            u = x - px
            col = 0
            hit = 0
            if u >= 0 and u < 64 and v >= 0 and v < 64:
                k = v * 64 + u
                la = int(tex[4096 + k])
                if la != 255:
                    hit = 1
                    chk = (((int(tex[k]) + phase) & 255) >> 5) + (la >> 5)
                    if chk & 1:
                        col = c_red
                    else:
                        col = c_white
            if hit == 0:
                u2 = u - shx
                shadow = 0
                if u2 >= 0 and u2 < 64 and v2 >= 0 and v2 < 64:
                    if int(tex[4096 + v2 * 64 + u2]) != 255:
                        shadow = 1
                on_line = ((x & 15) == 0) or ((y & 15) == 0)
                if shadow == 1:
                    if on_line:
                        col = c_line_sh
                    else:
                        col = c_bg_sh
                else:
                    if on_line:
                        col = c_line
                    else:
                        col = c_bg
            buf[n] = col >> 8
            buf[n + 1] = col & 255
            n += 2


def main():
    d = board.init_display(baudrate=SPI_BAUD)
    gc.collect()
    tex = build_texture()
    buf = bytearray(MAX_BOX_W * MAX_BOX_H * 2)
    view = memoryview(buf)
    p = array('i', [0] * 15)
    p[7:15] = array('i', [RED, WHITE, BG, LINE, BG_SHADOW, LINE_SHADOW, SX, SY])

    def draw_box(x0, y0, w, h, bx, by, phase):
        """Shade one box with the ball at (bx, by) and send it to the screen.

        Returns (shading time, SPI time) in microseconds.
        """
        p[0], p[1], p[2], p[3] = w, h, x0, y0
        p[4], p[5], p[6] = bx, by, phase
        t0 = ticks_us()
        render(buf, tex, p)
        t1 = ticks_us()
        d.block(x0, y0, x0 + w - 1, y0 + h - 1, view[:w * h * 2])
        return ticks_diff(t1, t0), ticks_diff(ticks_us(), t1)

    # Background: draw the whole screen in strips with the ball parked off-screen
    strip = MAX_BOX_W * MAX_BOX_H // W
    for y in range(0, H, strip):
        draw_box(0, y, W, min(strip, H - y), -1000, -1000, 0)

    x, y = 20.0, 10.0
    vx, vy = float(SPEED_X), 0.0
    phase = 0.0
    ox, oy = int(x), int(y)
    frames = 0
    t_render = t_spi = 0
    worst = 0
    start = last = ticks_us()
    while True:
        now = ticks_us()
        dt = min(ticks_diff(now, last) / 1_000_000, MAX_DT)
        last = now

        x += vx * dt
        if x < 0:
            x, vx = 0.0, -vx
        elif x > BOUNDS_X:
            x, vx = float(BOUNDS_X), -vx
        vy += GRAVITY * dt
        y += vy * dt
        if y > BOUNDS_Y:
            y, vy = float(BOUNDS_Y), -vy
        phase += (SPIN if vx > 0 else -SPIN) * dt
        nx, ny = int(x), int(y)

        x0, y0 = min(ox, nx), min(oy, ny)
        w = max(ox, nx) + D + SX - x0
        h = max(oy, ny) + D + SY - y0
        w, h = min(w, MAX_BOX_W), min(h, MAX_BOX_H)

        render_us, spi_us = draw_box(x0, y0, w, h, nx, ny, int(phase) & 255)
        done = ticks_us()

        t_render += render_us
        t_spi += spi_us
        worst = max(worst, ticks_diff(done, now))
        ox, oy = nx, ny
        frames += 1
        if DURATION_S and ticks_diff(done, start) > DURATION_S * 1_000_000:
            break

    secs = ticks_diff(ticks_us(), start) / 1_000_000
    print("frames:", frames, "in %.1fs" % secs, "=> %.1f fps" % (frames / secs))
    print("avg per frame: render %.1f ms, spi %.1f ms, worst frame %.1f ms" % (
        t_render / frames / 1000, t_spi / frames / 1000, worst / 1000))
    print("free heap:", gc.mem_free())


main()
