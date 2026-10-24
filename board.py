"""Pin map and setup helpers for the ESP32-2432S028 ("Cheap Yellow Display").

Every script here starts with `import board` and calls `init_display()` and/or
`init_touch()`. The settings you might need to change for your own board are
ROTATION and the CAL_* touch calibration constants below.
"""
from machine import Pin, SPI
from ili9341 import Display
from xpt2046 import Touch

# --- Settings you may need to change ---------------------------------------

# 0 puts the picture upright with the USB port on the right; 180 flips it for
# a board mounted the other way round. 90/270 don't work on this panel: see
# the README. Recalibrate touch after changing this.
ROTATION = 0

TFT_BAUD = 20_000_000  # display SPI clock; drop to 10 MHz if you see speckles

# Touch calibration. Run calibrate_touch.py then fit_touch.py (see README) and
# paste its output over these four lines. Fitted on one board, so yours will
# be close but probably not exact.
CAL_SWAP_XY = True  # raw Y gives screen x and raw X gives screen y
CAL_X_SCALE, CAL_X_OFFSET = 0.175446, -17.005
CAL_Y_SCALE, CAL_Y_OFFSET = 0.135526, -23.913

# --- Pin map (fixed by the board) ------------------------------------------

WIDTH, HEIGHT = 320, 240

# Display (ILI9341) on SPI bus 1. Its reset line is tied to the ESP32's EN
# pin rather than a GPIO, so there is no TFT_RST.
TFT_SCK, TFT_MOSI, TFT_MISO = 14, 13, 12
TFT_CS, TFT_DC, TFT_BL = 15, 2, 21

# Touch (XPT2046) on SPI bus 2
TOUCH_SCK, TOUCH_MOSI, TOUCH_MISO = 25, 32, 39
TOUCH_CS, TOUCH_IRQ = 33, 36

# RGB LED, active low
LED_R, LED_G, LED_B = 4, 16, 17


def led(r=0, g=0, b=0):
    """Set the RGB LED; each channel is 0 (off) or 1 (on)."""
    for pin, on in ((LED_R, r), (LED_G, g), (LED_B, b)):
        Pin(pin, Pin.OUT).value(0 if on else 1)


def backlight(on=True):
    Pin(TFT_BL, Pin.OUT).value(1 if on else 0)


class _NoPin:
    """Stands in for the display reset pin the driver insists on.

    The display is reset by the ESP32's EN line and then by the driver's
    software reset command, so nothing needs to happen here.
    """
    OUT = Pin.OUT

    def init(self, *args, **kwargs):
        pass

    def __call__(self, *args):
        pass


def init_display(baudrate=TFT_BAUD):
    """Set up the display in landscape and turn the backlight on."""
    # The panel's memory is natively 320x240, so landscape needs no row/column
    # swap: rotation=90 turns it into 240x320 and loses the right-hand third.
    spi = SPI(1, baudrate=baudrate, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI), miso=Pin(TFT_MISO))
    display = Display(spi, cs=Pin(TFT_CS), dc=Pin(TFT_DC), rst=_NoPin(),
                      width=WIDTH, height=HEIGHT, rotation=ROTATION, bgr=False)
    backlight(True)
    return display


class CalibratedTouch(Touch):
    """XPT2046 touch mapped to screen pixels with the CAL_* constants."""

    def normalize(self, x, y):
        if CAL_SWAP_XY:
            x, y = y, x
        sx = x * CAL_X_SCALE + CAL_X_OFFSET
        sy = y * CAL_Y_SCALE + CAL_Y_OFFSET
        return max(0, min(WIDTH - 1, int(sx))), max(0, min(HEIGHT - 1, int(sy)))


def init_touch():
    """Set up the touch controller. `.get_touch()` returns (x, y) or None."""
    spi = SPI(2, baudrate=1_000_000, sck=Pin(TOUCH_SCK), mosi=Pin(TOUCH_MOSI), miso=Pin(TOUCH_MISO))
    # The raw range only decides which readings count as a touch at all; the
    # mapping to pixels is done by CalibratedTouch.normalize above.
    return CalibratedTouch(spi, cs=Pin(TOUCH_CS), width=WIDTH, height=HEIGHT,
                           x_min=40, x_max=1950, y_min=10, y_max=2040)
