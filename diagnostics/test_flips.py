"""Show the four landscape flip options, 8 seconds each.

Use this if test_corners.py shows the picture mirrored or sideways. Each
stage fills the screen with a colour, marks the top-left corner with a white
square and prints a label. Note which stage looks right and set its MADCTL
value: ROTATION = 0 in board.py gives stage A (0x80) and ROTATION = 180 gives
stage B (0x40). Stages C and D need `mirror=True` passed to Display() in
board.init_display().
"""
from time import sleep
from machine import Pin, SPI
import board
from ili9341 import Display, color565

spi = SPI(1, baudrate=20_000_000, sck=Pin(board.TFT_SCK), mosi=Pin(board.TFT_MOSI), miso=Pin(board.TFT_MISO))
board.backlight(True)

W, H = board.WIDTH, board.HEIGHT
WHITE = color565(255, 255, 255)
# Stage letter, mirror, rotation (no row/column swap in any of these), fill
stages = (("A", False, 0, "RED", (255, 0, 0)),
          ("B", False, 180, "GREEN", (0, 255, 0)),
          ("C", True, 0, "BLUE", (0, 0, 255)),
          ("D", True, 180, "YELLOW", (255, 255, 0)))

for letter, mirror, rot, name, rgb in stages:
    d = Display(spi, cs=Pin(board.TFT_CS), dc=Pin(board.TFT_DC), rst=board._NoPin(),
                width=W, height=H, rotation=rot, mirror=mirror, bgr=False)
    fill = color565(*rgb)
    d.fill_rectangle(0, 0, W, H, fill)
    d.fill_rectangle(0, 0, 30, 30, WHITE)  # marks the top-left corner
    d.draw_text8x8(40, 10, "%s: should be %s" % (letter, name), WHITE, background=fill)
    d.draw_text8x8(40, 30, "mirror=%s rotation=%d" % (mirror, rot), WHITE, background=fill)
    print(letter, "mirror=%s rotation=%d MADCTL=%s" % (mirror, rot, hex(d.rotation)))
    sleep(8)
