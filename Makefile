# Shortcuts for the mpremote commands in the README. Activate the venv first.
# Override the port with e.g. `make deploy PORT=/dev/ttyUSB1`.
PORT ?= /dev/ttyUSB0
MP = mpremote connect $(PORT)

.PHONY: deploy reset repl run calibrate

deploy:  ## copy the drivers, board.py and main.py to the board, then reset it
	$(MP) cp drivers/ili9341.py drivers/xpt2046.py board.py main.py :
	$(MP) reset

reset:
	$(MP) reset

repl:    ## interactive MicroPython prompt; Ctrl-] to leave
	$(MP) repl

run:     ## run a script from this computer, e.g. `make run S=boing.py`
	$(MP) run $(S)

calibrate:  ## collect touch readings and print constants for board.py
	$(MP) run calibrate_touch.py | tee cal.txt
	python3 fit_touch.py cal.txt
