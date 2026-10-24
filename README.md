# MicroPython on the ESP32 "Cheap Yellow Display" (CYD)

Working MicroPython setup for the ESP32-2432S028 "Cheap Yellow Display": a 2.8"
320×240 colour touchscreen with an ESP32 on the back. It has a pin map, a
display and touch setup that works, a touch calibration tool, and a few demos,
including a clone of the Amiga "Boing" ball.

Everything here was worked out on one board (ESP32-D0WD-V3, 4 MB flash, CH340
USB-serial chip, ILI9341 display, XPT2046 touch) running MicroPython v1.29.0.
If yours looks the same, it should just work; see [Gotchas](#gotchas) for what
bit us.

## What's in here

| File | What it does |
|---|---|
| `board.py` | Pin map plus `init_display()`, `init_touch()`, `led()` and `backlight()`. Everything else imports this. The settings you might need to change are at the top. |
| `main.py` | Runs at boot: clears the screen and draws a green dot wherever you touch. |
| `boing.py` | The Boing ball demo. Runs for 30 s and prints its frame rate (about 63 fps). |
| `color_grid.py` | Draws an 8×6 grid of colour swatches. Handy for checking red/blue order and the screen edges. |
| `calibrate_touch.py` | Shows nine targets, one at a time, and prints the raw touch reading for each. |
| `fit_touch.py` | Turns the calibration output into constants for `board.py` (runs on your computer). |
| `diagnostics/` | Quick hardware checks: `test_display.py` (colour fills with the LED), `test_touch.py` (raw readings), `test_corners.py` (is the picture the right way up?) and `test_flips.py` (the four landscape options, if it isn't). |
| `drivers/` | `ili9341.py` and `xpt2046.py` from [rdagger/micropython-ili9341](https://github.com/rdagger/micropython-ili9341) (MIT), unmodified. |
| `Makefile` | Shortcuts for the `mpremote` commands below. |

## Hardware

| Part | Pins |
|---|---|
| Display (ILI9341), SPI bus 1 | SCK 14, MOSI 13, MISO 12, CS 15, DC 2, backlight 21 |
| Touch (XPT2046), SPI bus 2 | SCK 25, MOSI 32, MISO 39, CS 33, IRQ 36 |
| RGB LED (active low) | R 4, G 16, B 17 |

The display's reset line isn't on a GPIO (it's tied to the ESP32's EN pin), so
`board.py` gives the driver a dummy pin in its place.

## Setup (Linux)

You need Python 3 with venv support, a USB data cable, and permission to use the
serial port.

```sh
# Debian/Ubuntu: venv needs its own package, and the serial port needs a group
sudo apt install python3-venv
sudo usermod -aG dialout $USER      # then log out and back in

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt     # esptool and mpremote
```

Use esptool from pip. The one in Debian/Ubuntu's apt repository (v4.7.0) is
missing files it needs and crashes after connecting.

Plug the board in. It should appear as `/dev/ttyUSB0` (the CH340 chip, USB ID
`1a86:7523`). On macOS or Windows the port is named differently, and you may need
to install a CH340 driver. The commands below name the port explicitly; if the
board is the only serial device plugged in, you can leave out
`connect /dev/ttyUSB0` and `mpremote` will find it.

### 1. Back up the original firmware (optional, but cheap)

Boards ship with demo firmware. Take a copy before overwriting it:

```sh
mkdir -p backup
esptool --port /dev/ttyUSB0 --baud 460800 read-flash 0 0x400000 backup/original-4MB.bin
# restore later with: esptool --port /dev/ttyUSB0 write-flash 0 backup/original-4MB.bin
```

### 2. Flash MicroPython

Download the `ESP32_GENERIC` firmware from
<https://micropython.org/download/ESP32_GENERIC/> (we used
`ESP32_GENERIC-20260824-v1.29.0.bin`), then:

```sh
mkdir -p firmware   # put the .bin here
esptool --port /dev/ttyUSB0 --baud 460800 erase-flash
esptool --port /dev/ttyUSB0 --baud 460800 write-flash 0x1000 firmware/ESP32_GENERIC-20260824-v1.29.0.bin
```

Check it works:

```sh
mpremote connect /dev/ttyUSB0 exec "import os; print(os.uname().machine)"
```

### 3. Copy the code onto the board

```sh
make deploy
```

That runs these two commands, which you can also use directly:

```sh
mpremote connect /dev/ttyUSB0 cp drivers/ili9341.py drivers/xpt2046.py board.py main.py :
mpremote connect /dev/ttyUSB0 reset
```

After the reset the screen should clear and draw a green dot under your finger
or stylus. If the picture is upside down, set `ROTATION = 180` in `board.py`
and deploy again. If the dots don't land under your stylus, see
[Calibrating the touchscreen](#calibrating-the-touchscreen).

## Running the demos

`mpremote run` sends a script from your computer to the board and runs it, so
you don't need to copy the demos over (they only need `board.py` and the drivers
on the board):

```sh
mpremote connect /dev/ttyUSB0 run boing.py        # or: make run S=boing.py
mpremote connect /dev/ttyUSB0 run color_grid.py
```

`main.py` loops forever, but `mpremote` interrupts it when it connects, so the
screen stops updating while you're connected. Press the board's reset button, or
run `make reset`, to get back to the drawing screen. To stop it running at boot,
run `mpremote connect /dev/ttyUSB0 rm main.py`.

## Calibrating the touchscreen

The calibration in `board.py` came from one unit, so your touch will be close but
probably not exact. Recalibrating takes about a minute:

```sh
make calibrate
```

or, by hand:

```sh
mpremote connect /dev/ttyUSB0 run calibrate_touch.py | tee cal.txt
python3 fit_touch.py cal.txt
```

Press the middle of each red dot with a stylus (a fingertip works but is less
precise) and hold still until the LED goes off. `fit_touch.py` prints the error
at each target and the lines to paste over the `CAL_*` constants in `board.py`.
It works out for itself whether your panel's axes are swapped or mirrored
relative to the screen, so it copes with boards that differ from ours. Run
`make deploy` afterwards. If the worst error is over about 10 px, a target was
probably mis-tapped, so run it again.

## Gotchas

These cost us the most time.

**The panel is natively 320×240, so don't rotate it.** The usual way to get
landscape on an ILI9341 is the driver's `rotation=90`, but on this board that
makes the controller treat the screen as 240×320. Anything past x=240 is lost, a
third of the screen keeps stale or noisy pixels, and colours look wrong. The
fix is `rotation=0` with `width=320, height=240`, which is what `board.py` does.
With the USB port on the right, that gives an upright picture; `ROTATION = 180`
turns it round for a board mounted the other way. `diagnostics/test_flips.py`
shows all four landscape options if yours is mirrored.

**Red and blue are swapped by default.** The driver assumes BGR order. This panel
wants `bgr=False`.

**Touch axes are swapped relative to the screen.** Raw touch Y gives screen x and
raw X gives screen y, and each is close to a straight line. That's the
`CAL_SWAP_XY` setting in `board.py`; `fit_touch.py` detects it for you.

**Display bus speed.** `board.py` defaults to 20 MHz. `boing.py` runs it at
40 MHz and looked fine on our board, but if you see speckles or stray pixels,
drop it back to 20 MHz.

**The USB cable matters a lot.** Our first cable made the board appear for a
moment and then fail with `device descriptor read/64, error -71` in `dmesg`. A
different, shorter cable fixed it. If `/dev/ttyUSB0` never appears or vanishes
partway through a session, suspect the cable first. A loose connection will drop
it too.

**Memory.** A full frame is 150 KB (320×240×2 bytes) and there is only about
165 KB of free heap, so there is no full-screen framebuffer. `boing.py` instead
redraws just the small box around the ball into a ~16 KB buffer. It shades that
box in a `@micropython.viper` loop, then sends it as a single SPI block. The
shading takes about 10 ms a frame and the SPI transfer about 5 ms.

## License and credits

MIT licensed; see `LICENSE`.

The display and touch drivers in `drivers/` come from
[rdagger/micropython-ili9341](https://github.com/rdagger/micropython-ili9341),
used under its own MIT license (see `drivers/LICENSE`).
