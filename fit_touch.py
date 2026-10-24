"""Fit touch calibration constants from the output of calibrate_touch.py.

Run it on your computer, not the board:

    mpremote connect /dev/ttyUSB0 run calibrate_touch.py | tee cal.txt
    python3 fit_touch.py cal.txt

It reads the "TARGET" and "RAW" lines, works out whether the touch panel's
axes are swapped relative to the screen, fits a straight line to each axis,
and prints the lines to paste into board.py.
"""
import re
import sys


def fit_line(xs, ys):
    """Least-squares y = scale * x + offset; None if xs are all the same."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    var = sum((x - mx) ** 2 for x in xs)
    if var == 0:
        return None
    scale = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var
    return scale, my - scale * mx


def fit_axes(screen, raw, swap):
    """Fit both axes. Returns (x_fit, y_fit, per-target errors, worst error)."""
    rx = [r[1] if swap else r[0] for r in raw]  # raw value that drives screen x
    ry = [r[0] if swap else r[1] for r in raw]  # raw value that drives screen y
    x_fit = fit_line(rx, [s[0] for s in screen])
    y_fit = fit_line(ry, [s[1] for s in screen])
    if x_fit is None or y_fit is None:
        return None
    errors = [(x * x_fit[0] + x_fit[1] - sx, y * y_fit[0] + y_fit[1] - sy)
              for x, y, (sx, sy) in zip(rx, ry, screen)]
    worst = max(max(abs(ex), abs(ey)) for ex, ey in errors)
    return x_fit, y_fit, errors, worst


def main(path):
    targets, raws = {}, {}
    for line in open(path):
        m = re.match(r"TARGET (\S+) (\d+) (\d+)", line)
        if m:
            targets[m[1]] = (int(m[2]), int(m[3]))
        m = re.match(r"RAW (\S+) \((\d+), (\d+)\)", line)
        if m:
            raws[m[1]] = (int(m[2]), int(m[3]))
    names = [n for n in targets if n in raws]
    if len(names) < 4:
        sys.exit("need at least 4 touched targets, found %d" % len(names))

    screen = [targets[n] for n in names]
    raw = [raws[n] for n in names]
    fits = {swap: fit_axes(screen, raw, swap) for swap in (False, True)}
    fits = {swap: f for swap, f in fits.items() if f is not None}
    if not fits:
        sys.exit("targets need to cover more than one row and one column")
    swap = min(fits, key=lambda s: fits[s][3])
    (x_scale, x_off), (y_scale, y_off), errors, worst = fits[swap]

    for n, (sx, sy), (ex, ey) in zip(names, screen, errors):
        print("%-8s target (%3d,%3d)  error (%+.0f,%+.0f) px" % (n, sx, sy, ex, ey))
    print("\nworst error: %.0f px" % worst)
    if worst > 10:
        print("That is large. A target was probably mis-tapped; run the calibration again.")
    print("\nPaste into board.py:")
    print("CAL_SWAP_XY = %s" % swap)
    print("CAL_X_SCALE, CAL_X_OFFSET = %.6f, %.3f" % (x_scale, x_off))
    print("CAL_Y_SCALE, CAL_Y_OFFSET = %.6f, %.3f" % (y_scale, y_off))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
