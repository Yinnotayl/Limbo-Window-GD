import math, time, random
from tkinter import *
import os
import windowMove
from PIL import Image, ImageTk, ImageEnhance

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

        # pre-create all 8 windows, but keep them hidden
        for key_id in range(1, 9):
            w = LimboWindow(key_id, self)
            w.root.withdraw()         # start hidden
            self.windows[key_id] = w

    def open(self, key_id):
        """Show (or re-show) a pre-created window."""
        if key_id in self.windows:
            self.windows[key_id].show()
        else:
            # fallback, though in this setup you’ll never hit this
            w = LimboWindow(key_id, self)
            self.windows[key_id] = w
            w.show()
        return self.windows[key_id]

    def close(self, key_id):
        """Hide and unregister (optional) window."""
        if key_id in self.windows:
            self.windows[key_id].close()

    def unregister(self, key_id):
        """Remove from tracking (called when a window is destroyed)."""
        self.windows.pop(key_id, None)

    def change_colour(self, key_id, on_off):
        if key_id in self.windows:
            self.windows[key_id].change_colour(on_off)


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

    play_button = Button(root, text="Start", command=lambda: setup())
    play_button.place(x=window_width // 2 - 100, y=window_height - 150)

    # 8) Run the GUI
    root.mainloop()
    
def setup():
    global mgr
    correct_key = random.randint(1, 8)
    key_positions = [1, 2, 3, 4, 5, 6, 7, 8]

    # Bring the keys to the correct position
    # mgr = KeyManager()
    delay = 2000  # milliseconds
    width  = mgr.master.winfo_screenwidth()
    height = mgr.master.winfo_screenheight()
    h_spacing = 100
    v_spacing = height // 8

    w1 = mgr.open(1)
    w2 = mgr.open(2)
    w3 = mgr.open(3)
    w4 = mgr.open(4)
    w5 = mgr.open(5)
    w6 = mgr.open(6)
    w7 = mgr.open(7)
    w8 = mgr.open(8)

    windowMove.moveWindowTo(w1.root, width - (h_spacing + 120) * 2, v_spacing, curve=True, overshoot=True)
    windowMove.moveWindowTo(w2.root, width - (h_spacing + 120) * 1, v_spacing, curve=True, overshoot=True)
    windowMove.moveWindowTo(w3.root, width - (h_spacing + 120) * 2, (v_spacing + 84) * 2 - 84, curve=True, overshoot=True)
    windowMove.moveWindowTo(w4.root, width - (h_spacing + 120) * 1, (v_spacing + 84) * 2 - 84, curve=True, overshoot=True)
    windowMove.moveWindowTo(w5.root, width - (h_spacing + 120) * 2, (v_spacing + 84) * 3 - 84, curve=True, overshoot=True)
    windowMove.moveWindowTo(w6.root, width - (h_spacing + 120) * 1, (v_spacing + 84) * 3 - 84, curve=True, overshoot=True)
    windowMove.moveWindowTo(w7.root, width - (h_spacing + 120) * 2, (v_spacing + 84) * 4 - 84, curve=True, overshoot=True)
    windowMove.moveWindowTo(w8.root, width - (h_spacing + 120) * 1, (v_spacing + 84) * 4 - 84, curve=True, overshoot=True)

    mgr.master.after(delay, lambda: mgr.change_colour(correct_key, True))
    mgr.master.after(delay + 800, lambda: mgr.change_colour(correct_key, False))

    mgr.master.mainloop()




if __name__ == "__main__":
    main_menu()
    setup()