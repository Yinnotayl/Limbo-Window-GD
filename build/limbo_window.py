import math, time, random
from tkinter import *
import os
import windowMove
from PIL import Image, ImageTk, ImageEnhance
from functools import wraps

# Limbo Keys Doc: https://docs.google.com/spreadsheets/d/1zGRkD6pMkz7yvzlwYg2tb1-4BmHRPXrFRVTGdXmcaVA/edit?gid=0#gid=0

class LimboWindow:
    # load once per process
    _base_img    = None
    _overlay_img = None

    def __init__(self, key_id, manager, size=(120,84), transparent_color='magenta'):
        self.key_id = key_id
        self.manager = manager
        self.transparent_color = transparent_color

        # --- init window as before ---
        self.root = Toplevel(manager.master)
        # self.root.title(f"Limbo Key #{key_id}")
        self.root.title(f"Limbo Key")
        self.root.geometry(f"{size[0]}x{size[1]}")
        self.root.resizable(False, False)
        self.root.wm_attributes('-toolwindow', True)
        self.root.config(bg=self.transparent_color)
        self.root.wm_attributes('-transparentcolor', self.transparent_color)

        # label to show our composite
        self.label = Label(self.root,
                           bg=self.transparent_color,
                           borderwidth=0,
                           highlightthickness=0)
        self.label.place(x=0, y=0)

        # load images once
        if LimboWindow._base_img is None:
            folder = os.path.dirname(os.path.abspath(__file__))
            LimboWindow._base_img    = Image.open(os.path.join(folder, "limbo_key.png")).convert("RGBA")
            LimboWindow._overlay_img = Image.open(os.path.join(folder, "limbo_key_green.png")).convert("RGBA")

        # internal state
        self._current_alpha = 0.0    # 0.0 = no overlay, 1.0 = full overlay
        self._fade_job      = None   # after() job ID

        # draw initial frame
        self._redraw()

        # cleanup
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _composite(self, alpha):
        """Blend base + overlay at given alpha."""
        return Image.blend(LimboWindow._base_img,
                           LimboWindow._overlay_img,
                           alpha)

    def _redraw(self):
        """Render the current composite into the Tk label."""
        comp = self._composite(self._current_alpha)
        self._tk_img = ImageTk.PhotoImage(comp, master=self.root)
        self.label.config(image=self._tk_img)

    def change_colour(self, on_off: bool, duration: int = 200, steps: int = 10):
        """
        Fade overlay in (on_off=True) or out (on_off=False)
        over `duration` ms in `steps` increments.
        """
        # cancel any in-progress fade
        if self._fade_job:
            self.root.after_cancel(self._fade_job)
            self._fade_job = None

        start = self._current_alpha
        end   = 1.0 if on_off else 0.0
        delta = (end - start) / steps
        interval = duration // steps

        def step(count=0):
            nonlocal start, delta, steps
            self._current_alpha = min(1.0, max(0.0, start + delta * count))
            self._redraw()

            if count < steps:
                self._fade_job = self.root.after(interval, lambda: step(count+1))
            else:
                self._fade_job = None

        # kick off
        step(0)

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def close(self):
        if self._fade_job:
            self.root.after_cancel(self._fade_job)
        self.root.destroy()
        self.manager.unregister(self.key_id)

    def _on_close(self):
        self.close()


class KeyManager:
    def __init__(self):
        # one hidden root for all windows
        self.master = Tk()
        self.master.withdraw()
        self.windows = {}

        # 1) pre-create all 8 windows (hidden)
        for key_id in range(1, 9):
            w = LimboWindow(key_id, self)
            w.root.withdraw()
            self.windows[key_id] = w

        # 2) initialize position maps (row‑major 1…8)
        self.pos_to_key = {
            1: 1, 2: 2,
            3: 3, 4: 4,
            5: 5, 6: 6,
            7: 7, 8: 8,
        }
        self.key_to_pos = {k: p for p, k in self.pos_to_key.items()}

    def open(self, key_id):
        """Show (or re-show) a pre-created window."""
        if key_id in self.windows:
            self.windows[key_id].show()
            return self.windows[key_id]
        # fallback (shouldn't happen)
        w = LimboWindow(key_id, self)
        self.windows[key_id] = w
        w.show()
        return w

    def close(self, key_id):
        """Destroy a window and unregister it."""
        if key_id in self.windows:
            self.windows[key_id].close()

    def unregister(self, key_id):
        """Internal: call when a window is closed."""
        self.windows.pop(key_id, None)
        # also remove from position maps
        pos = self.key_to_pos.pop(key_id, None)
        if pos is not None:
            self.pos_to_key.pop(pos, None)

    def change_colour(self, key_id, on_off):
        """Fade overlay in or out."""
        if key_id in self.windows:
            self.windows[key_id].change_colour(on_off)

    def swap_keys(self, key1, key2, on_complete=None):
        """
        Swap two keys in both mappings and animate them.
        on_complete optional callback after both moves finish.
        """
        # bounds-check
        if key1 not in self.key_to_pos or key2 not in self.key_to_pos:
            return

        pos1 = self.key_to_pos[key1]
        pos2 = self.key_to_pos[key2]

        # swap the maps
        self.pos_to_key[pos1], self.pos_to_key[pos2] = key2, key1
        self.key_to_pos[key1], self.key_to_pos[key2] = pos2, pos1

        # find target coordinates
        x1, y1 = xy_positions[pos1]
        x2, y2 = xy_positions[pos2]
        w1 = self.windows[key1]
        w2 = self.windows[key2]

        # animate key1 → pos2, then key2 → pos1 (or vice versa)
        # def _move2():
        #     windowMove.moveWindowTo(w2.root, x1, y1,
        #                             curve=True, overshoot=True,
        #                             on_complete=on_complete)

        # windowMove.moveWindowTo(w1.root, x2, y2,
        #                         curve=True, overshoot=True,
        #                         on_complete=_move2)


        windowMove.moveWindowTo(w1.root, x2, y2, curve=True, overshoot=True, duration=500)
        windowMove.moveWindowTo(w2.root, x1, y1, curve=True, overshoot=True, duration=500, 
                                on_complete=on_complete)
        
        self.debug_maps()

    def move_key_to(self, key, new_pos, on_complete=None):
        """
        Move a single key to new_pos (and update mappings).
        on_complete optional callback after the move finishes.
        """
        # bounds-check
        if key not in self.key_to_pos or new_pos not in xy_positions:
            return

        old_pos = self.key_to_pos[key]
        other   = self.pos_to_key.get(new_pos)

        # update maps
        self.pos_to_key[old_pos] = other
        if other is not None:
            self.key_to_pos[other] = old_pos

        self.pos_to_key[new_pos] = key
        self.key_to_pos[key]      = new_pos

        # animate
        x, y = xy_positions[new_pos]
        windowMove.moveWindowTo(self.windows[key].root, x, y, duration=500,
                                curve=True, overshoot=True,
                                on_complete=on_complete)
        
        self.debug_maps()
        
    def rotate_keys(self, positions, clockwise=True, on_complete=None):
        """Rotate keys in the given list of positions."""
        if not positions:
            return

        keys = [self.pos_to_key.get(p) for p in positions]

        if clockwise:
            shifted_keys = keys[-1:] + keys[:-1]  # Right shift
        else:
            shifted_keys = keys[1:] + keys[:1]   # Left shift

        def _safe_move(window, x, y, on_complete):
            # current coords
            cx, cy = window.winfo_x(), window.winfo_y()
            if cx == x and cy == y:
                # no movement needed—fire callback on next idle
                if on_complete:
                    window.after(0, on_complete)
            else:
                # real move
                windowMove.moveWindowTo(window, x, y, duration=500,
                                        curve=True, overshoot=True,
                                        on_complete=on_complete)

        # inside KeyManager.rotate_keys (and analogously in swap_keys, splitRotate, etc)
        n = len(positions)
        for i, (pos, key) in enumerate(zip(positions, shifted_keys), start=1):
            if key is None: 
                continue
            
            x, y = xy_positions[pos]
            cb = on_complete if i == n else None
            # in rotate_keys, swap_keys, move_key_to...
            _safe_move(self.windows[key].root, x, y, cb)

        self.debug_maps()

        # for pos, key in zip(positions, shifted_keys):
        #     if key is not None:
        #         old_pos = self.key_to_pos[key]
        #         self.pos_to_key.pop(old_pos, None)
        #         self.pos_to_key[pos] = key
        #         self.key_to_pos[key] = pos

        #         x, y = xy_positions[pos]
        #         windowMove.moveWindowTo(self.windows[key].root, x, y, curve=True, overshoot=True, on_complete=on_complete)

    def debug_maps(self):
        print("pos_to_key:", self.pos_to_key)
        print("key_to_pos:", self.key_to_pos)


def demo():
    mgr = KeyManager()

    w8 = mgr.open(8)
    w5 = mgr.open(5)
    mgr.change_colour(8, True)

    windowMove.moveWindowTo(w8.root, 500, 500, curve=True, overshoot=True)

    mgr.master.after(2000, lambda: mgr.change_colour(8, False))

    # kick off the mainloop once
    mgr.master.mainloop()

def main_menu():
    global mgr
    mgr = KeyManager()
    # 1) Create your window at the size you want
    root = Tk()
    root.title("Limbo Windows - by Yinnotayl")
    window_width, window_height = 834, 495
    root.geometry(f"{window_width}x{window_height}")
    root.resizable(False, False)

    def onClose():
        global mgr
        """Handle window close event."""
        if mgr:
            # Close all open windows
            for key_id in list(mgr.windows.keys()):
                mgr.close(key_id)
            # Destroy the master window
            mgr.master.destroy()
            mgr = None
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", onClose)

    # 2) Force the window to realize its size
    root.update_idletasks()

    # 3) Load your source image
    folder   = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(folder, "limbo_logo.png")
    pil_img  = Image.open(img_path).convert("RGBA")

    # 4) Resize the image to exactly your window’s client area
    #    (we already know window_width & window_height)
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.LANCZOS

    resized_img = pil_img.resize((window_width, window_height),
                                 resample=resample_filter)

    # 5) Convert it into a PhotoImage bound to our root
    bg_img = ImageTk.PhotoImage(resized_img, master=root)

    # 6) Display it in a Label at (0,0)
    image_label = Label(root,
                        image=bg_img,
                        borderwidth=0,
                        highlightthickness=0)
    image_label.place(x=0, y=0)

    # 7) Keep a reference so it doesn’t get garbage‑collected
    image_label.image = bg_img

    play_button = Button(root, text="Start", font="Arial 20", command=lambda: setup())
    play_button.place(x=window_width // 2 - 50, y=window_height - 160)

    settings_button = Button(root, text="Settings", font="Arial 20", command=lambda: show_Settings())
    settings_button.place(x=window_width // 2 + 50, y=window_height - 160)

    # 8) Run the GUI
    root.mainloop()

def show_Settings():
    settings = Toplevel()
    settings.title("Settings")
    settings.geometry("400x300")
    settings.resizable(False, False)
    settings_label = Label(settings, text="Settings will be here soon!", font="Arial 16")
    settings_label.pack(pady=20)

screen = Tk()
screen.withdraw()
width  = screen.winfo_screenwidth()
height = screen.winfo_screenheight()
h_spacing = 100
v_spacing = height // 8
xy_positions = {1: (width - (h_spacing + 120) * 2, v_spacing),
                2: (width - (h_spacing + 120) * 1, v_spacing), 
                3: (width - (h_spacing + 120) * 2, (v_spacing + 84) * 2 - 84),
                4: (width - (h_spacing + 120) * 1, (v_spacing + 84) * 2 - 84), 
                5: (width - (h_spacing + 120) * 2, (v_spacing + 84) * 3 - 84),
                6: (width - (h_spacing + 120) * 1, (v_spacing + 84) * 3 - 84), 
                7: (width - (h_spacing + 120) * 2, (v_spacing + 84) * 4 - 84), 
                8: (width - (h_spacing + 120) * 1, (v_spacing + 84) * 4 - 84)}
screen.destroy()
correct_key = random.randint(1, 8)
key_positions = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8}

def moveKeyToPosition(key, position):
    windowMove.moveWindowTo(key.root, xy_positions[position][0], xy_positions[position][1], curve=True, overshoot=True)    
    
def setup():
    global mgr
    
    # Bring the keys to the correct position
    # mgr = KeyManager()
    delay = 2000  # milliseconds

    if mgr:
        w1 = mgr.open(1)
        w2 = mgr.open(2)
        w3 = mgr.open(3)
        w4 = mgr.open(4)
        w5 = mgr.open(5)
        w6 = mgr.open(6)
        w7 = mgr.open(7)
        w8 = mgr.open(8)
    else:
        w1 = w2 = w3 = w4 = w5 = w6 = w7 = w8 = None

    if any([w1, w2, w3, w4, w5, w6, w7, w8]):
        windowMove.moveWindowTo(w1.root, xy_positions[1][0], xy_positions[1][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w2.root, xy_positions[2][0], xy_positions[2][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w3.root, xy_positions[3][0], xy_positions[3][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w4.root, xy_positions[4][0], xy_positions[4][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w5.root, xy_positions[5][0], xy_positions[5][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w6.root, xy_positions[6][0], xy_positions[6][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w7.root, xy_positions[7][0], xy_positions[7][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w8.root, xy_positions[8][0], xy_positions[8][1], curve=True, overshoot=True)

    if mgr:
        mgr.master.after(delay, lambda: mgr.change_colour(correct_key, True))
        mgr.master.after(delay + 800, lambda: mgr.change_colour(correct_key, False))

        mgr.master.after(delay + 800 + 1000, lambda: game())

        mgr.master.mainloop()

class MovementsManager():
    def __init__(self, mgr):
        self.mgr = mgr
        self.moves = {
            1: self.rotateAllLeft,
            2: self.rotateAllRight,
            3: self.centerRotateLeft,
            4: self.centerRotateRight,
            5: self.rotateSegmentsLeft,
            6: self.rotateSegmentsRight,
            7: self.splitRotateSwapLeft,
            8: self.splitRotateSwapRight,
            9: self.bottomUp,
            10: self.topDown,
            11: self.spinTop,
            12: self.spinBottom,
            13: self.swapSegmentCentersLeft,
            14: self.swapSegmentCentersRight,
            15: self.swapLeftRight,
            16: self.swapRightLeft,
        }

    def rotateAllLeft(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 4, 6, 8, 7, 5, 3], clockwise=False, on_complete=oncomplete)
    def rotateAllRight(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 4, 6, 8, 7, 5, 3], clockwise=True, on_complete=oncomplete)
    def centerRotateLeft(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 4, 3], clockwise=False)
        self.mgr.rotate_keys([5, 6, 8, 7], clockwise=True, on_complete=oncomplete)
    def centerRotateRight(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 4, 3], clockwise=True)
        self.mgr.rotate_keys([5, 6, 8, 7], clockwise=False, on_complete=oncomplete)
    def rotateSegmentsLeft(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 3, 4], clockwise=False)
        self.mgr.rotate_keys([5, 6, 7, 8], clockwise=False, on_complete=oncomplete)
    def rotateSegmentsRight(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 3, 4], clockwise=True)
        self.mgr.rotate_keys([5, 6, 7, 8], clockwise=True, on_complete=oncomplete)
    def splitRotateSwapLeft(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 3], clockwise=True)
        mgr.swap_keys(4, 5)
        self.mgr.rotate_keys([6, 8, 7], clockwise=True, on_complete=oncomplete)
    def splitRotateSwapRight(self, oncomplete=None):
        self.mgr.rotate_keys([1, 2, 4], clockwise=False)
        mgr.swap_keys(3, 6)
        self.mgr.rotate_keys([5, 8, 7], clockwise=False, on_complete=oncomplete)
    def bottomUp(self, oncomplete=None):
        self.mgr.swap_keys(1, 5)
        self.mgr.swap_keys(2, 6)
        self.mgr.swap_keys(3, 7)
        self.mgr.swap_keys(4, 8, on_complete=oncomplete)
    def topDown(self, oncomplete=None):
        self.mgr.swap_keys(5, 1)
        self.mgr.swap_keys(6, 2)
        self.mgr.swap_keys(7, 3)
        self.mgr.swap_keys(8, 4, on_complete=oncomplete)
    def spinTop(self, oncomplete=None):
        self.mgr.swap_keys(1, 8)
        self.mgr.swap_keys(2, 7)
        self.mgr.swap_keys(3, 6)
        self.mgr.swap_keys(4, 5, on_complete=oncomplete)
    def spinBottom(self, oncomplete=None):
        self.mgr.swap_keys(8, 1)
        self.mgr.swap_keys(7, 2)
        self.mgr.swap_keys(6, 3)
        self.mgr.swap_keys(5, 4, on_complete=oncomplete)
    def swapSegmentCentersLeft(self, oncomplete=None):
        self.mgr.swap_keys(1, 4)
        self.mgr.swap_keys(2, 3)
        self.mgr.swap_keys(5, 8)
        self.mgr.swap_keys(6, 7, on_complete=oncomplete)
    def swapSegmentCentersRight(self, oncomplete=None):
        self.mgr.swap_keys(4, 1)
        self.mgr.swap_keys(3, 2)
        self.mgr.swap_keys(8, 5)
        self.mgr.swap_keys(7, 6, on_complete=oncomplete)
    def swapLeftRight(self, oncomplete=None):
        self.mgr.swap_keys(1, 2)
        self.mgr.swap_keys(3, 4)
        self.mgr.swap_keys(5, 6)
        self.mgr.swap_keys(7, 8, on_complete=oncomplete)
    def swapRightLeft(self, oncomplete=None):
        self.mgr.swap_keys(2, 1)
        self.mgr.swap_keys(4, 3)
        self.mgr.swap_keys(6, 5)
        self.mgr.swap_keys(8, 7, on_complete=oncomplete)

# def game():
#     global mgr
#     mm = MovementsManager(mgr)

#     mm.moves[1](oncomplete=lambda: mm.moves[1](oncomplete=lambda: mm.moves[1](oncomplete=lambda: mm.moves[1](oncomplete=lambda: mm.moves[1](oncomplete=lambda: mm.moves[1](oncomplete=lambda: mm.moves[1]()))))))

    # # 1) Pick 25 random moves
    # move_keys  = random.choices(list(mm.moves.keys()), k=25)
    # move_funcs = [mm.moves[k] for k in move_keys]

    # # 2) Helper to make a callback that only fires once
    # def once(fn):
    #     called = False
    #     @wraps(fn)
    #     def wrapper(*a, **kw):
    #         nonlocal called
    #         if not called:
    #             called = True
    #             fn(*a, **kw)
    #     return wrapper

    # # 3) Recursive runner
    # def run_next(idx=0):
    #     if idx >= len(move_funcs):
    #         print("All 25 moves done.")
    #         return

    #     # wrap run_next(idx+1) so it only fires a single time
    #     cb = once(lambda: run_next(idx+1))
    #     move_funcs[idx](oncomplete=cb)
    #     print(f"Running move {idx+1}/{len(move_funcs)}: {move_keys[idx]}")

    # # 4) start the chain
    # run_next()

def game():
    global mgr
    mm = MovementsManager(mgr)

    # pick 25 random moves
    move_funcs = [mm.moves[k] for k in random.choices(list(mm.moves), k=25)]

    # helper that runs only once
    def once(fn):
        called = False
        @wraps(fn)
        def wrapper(*a, **kw):
            nonlocal called
            if not called:
                called = True
                fn(*a, **kw)
        return wrapper

    # recursive runner
    def run_next(i=0):
        if i == len(move_funcs):
            print("All 25 moves done.")
            mgr.master.after(1000, lambda: mgr.change_colour(correct_key, True))
            mgr.master.after(1000 + 800, lambda: mgr.change_colour(correct_key, False))
            print("Shown")
            return
        cb = once(lambda: run_next(i+1))
        move_funcs[i](oncomplete=cb)

    run_next()

    # End of the game
    if mgr:
        w1 = mgr.open(1)
        w2 = mgr.open(2)
        w3 = mgr.open(3)
        w4 = mgr.open(4)
        w5 = mgr.open(5)
        w6 = mgr.open(6)
        w7 = mgr.open(7)
        w8 = mgr.open(8)
    else:
        w1 = w2 = w3 = w4 = w5 = w6 = w7 = w8 = None

    if any([w1, w2, w3, w4, w5, w6, w7, w8]):
        windowMove.moveWindowTo(w1.root, xy_positions[1][0], xy_positions[1][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w2.root, xy_positions[2][0], xy_positions[2][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w3.root, xy_positions[3][0], xy_positions[3][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w4.root, xy_positions[4][0], xy_positions[4][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w5.root, xy_positions[5][0], xy_positions[5][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w6.root, xy_positions[6][0], xy_positions[6][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w7.root, xy_positions[7][0], xy_positions[7][1], curve=True, overshoot=True)
        windowMove.moveWindowTo(w8.root, xy_positions[8][0], xy_positions[8][1], curve=True, overshoot=True)
    windowMove.moveWindowTo(w1.root, xy_positions[1][0], xy_positions[1][1], curve=True, overshoot=True)
    print("movesd")


if __name__ == "__main__":
    main_menu()
    setup()