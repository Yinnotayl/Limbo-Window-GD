import math, time
from tkinter import *

def setWindowPosition(x, y, window):
    window.geometry(f"+{x}+{y}")

def moveSmooth(base_window, from_x, from_y, to_x, to_y,
               duration=1000, interval=10,
               overshoot=False, curve=False,
               on_complete=None):
    """
    Animate window from (from_x,from_y) → (to_x,to_y) over `duration` ms,
    updating every `interval` ms.
      - overshoot=True  → use back-easing (shoot past & settle)
      - curve=True      → follow a quadratic Bézier arc
    """
    dx, dy = to_x - from_x, to_y - from_y
    start = time.time()

    # standard ease-in-out
    def ease_io(t):
        return 0.5 * (1 - math.cos(math.pi * t))

    # back-easing for overshoot
    def ease_io_back(t, s=0.7):
        s *= 1.525
        if t < 0.5:
            return ((2*t)**2 * ((s+1)*(2*t) - s)) / 2
        p = 2*t - 2
        return ((p**2 * ((s+1)*p + s) + 2)) / 2

    # if curve=True, build a quadratic Bézier: P0→P1→P2
    # P1 is midpoint shifted perpendicular by 0.2*length
    if curve:
        mid_x, mid_y = (from_x + to_x)/2, (from_y + to_y)/2
        # perpendicular unit vector
        length = math.hypot(dx, dy)
        if length == 0:
            ux, uy = 0, 0
        else:
            ux, uy = -dy/length, dx/length
        # control point offset 20% of total distance
        ctrl_x = mid_x + ux * (length * 0.2)
        ctrl_y = mid_y + uy * (length * 0.2)

    def _step():
        now = time.time()
        t_raw = (now - start) / (duration/1000)
        t = min(max(t_raw, 0.0), 1.0)

        # pick easing function
        e = (ease_io_back(t) if overshoot else ease_io(t))

        if curve:
            # quadratic Bézier at parameter e:
            # B(e) = (1−e)^2 P0 + 2(1−e)e P1 + e^2 P2
            inv = 1 - e
            new_x = int(inv*inv*from_x + 2*inv*e*ctrl_x + e*e*to_x)
            new_y = int(inv*inv*from_y + 2*inv*e*ctrl_y + e*e*to_y)
        else:
            # straight line interpolation
            new_x = int(from_x + dx * e)
            new_y = int(from_y + dy * e)

        setWindowPosition(new_x, new_y, base_window)

        if t < 1.0:
            base_window.after(interval, _step)
        elif on_complete:
            on_complete()

    _step()

def moveWindowTo(window, x, y, **kwargs):
    cx, cy = window.winfo_x(), window.winfo_y()
    moveSmooth(window, cx, cy, x, y, **kwargs)