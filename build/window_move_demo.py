import windowMove
from tkinter import *

root = Tk()

# Demo
def run_demo():
    windowMove.setWindowPosition(100, 100, root)

    demo_moves = [
        # (x, y, duration, overshoot, curve)
        (500, 100, 800, False, False),  # straight, ease
        (100, 300, 1000, True, False),  # straight, overshoot
        (500, 500, 1000, False, True),  # curved, ease
        (100, 100, 1000, True, True),   # curved, overshoot
        (300, 300, 600, False, False),  # quick straight
        (600, 300, 1300, True, True),   # dramatic arc + overshoot
        (100, 500, 800, False, True),   # soft curved return
        (100, 100, 1000, True, False),  # final bounce-in
    ]
    """
    | Type          | Easing    | Curve  | Duration |
    | ------------- | --------- | ------ | -------- |
    | Straight line | smooth    | ❌     | medium   |
    | Straight line | overshoot | ❌     | slow     |
    | Curved arc    | smooth    | ✅     | slow     |
    | Curved arc    | overshoot | ✅     | slow     |
    | Straight line | fast      | ❌     | fast     |
    | Big curve     | overshoot | ✅     | long     |
    | Curved return | smooth    | ✅     | medium   |
    | Final bounce  | overshoot | ❌     | slow     |
    """

    def demo_content(moves):
        if not moves:
            return
        x, y, dur, ovr, crv = moves.pop(0)
        windowMove.moveWindowTo(
            root,
            x, y,
            duration=dur,
            interval=10,
            overshoot=ovr,
            curve=crv,
            on_complete=lambda: root.after(300, lambda: demo_content(moves))
        )

    root.after(500, lambda: demo_content(demo_moves.copy()))

run_demo()

root.mainloop()
