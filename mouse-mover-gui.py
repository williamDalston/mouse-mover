#!/usr/bin/env python3
"""
Mouse Mover - GUI Version
Cross-platform (Mac/Windows) mouse activity simulator.
"""

import os
import sys
import math
import random
import threading
import time
import tkinter as tk
from datetime import datetime
from typing import Optional

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
except ImportError:
    root = tk.Tk()
    root.withdraw()
    from tkinter import messagebox
    messagebox.showerror(
        "Missing Dependency",
        "pyautogui is not installed.\n\nRun: pip install pyautogui"
    )
    sys.exit(1)

# Mouse behavior
SCREEN_MARGIN = 50
MOVE_DURATION_MIN = 0.5
MOVE_DURATION_MAX = 2.0
DELAY_MIN = 2.0
DELAY_MAX = 8.0
SECONDARY_MOVE_CHANCE = 0.7
SECONDARY_MOVE_OFFSET = 20
PAUSE_CHECK_INTERVAL = 0.5

# Theme
BG = "#0e0e1a"
SURFACE = "#181830"
SURFACE_LIGHT = "#222244"
GREEN = "#00e09e"
GREEN_DIM = "#00a070"
RED = "#ff4f6e"
RED_DIM = "#c0374e"
YELLOW = "#ffc64d"
WHITE = "#f0f0f5"
DIM = "#6b7394"
FONT = "Helvetica"


class RingIndicator:
    """Animated arc ring drawn on a canvas."""

    def __init__(self, parent: tk.Frame, size: int = 160) -> None:
        self.size = size
        self.canvas = tk.Canvas(
            parent, width=size, height=size,
            bg=BG, highlightthickness=0
        )
        self.angle = 0.0
        self.animating = False
        self._color = DIM
        self._draw_static()

    def _draw_static(self) -> None:
        pad = 12
        self.canvas.delete("ring")
        # Background ring
        self.canvas.create_oval(
            pad, pad, self.size - pad, self.size - pad,
            outline=SURFACE_LIGHT, width=5, tags="ring"
        )

    def _draw_arc(self) -> None:
        pad = 12
        self.canvas.delete("arc")
        # Spinning arc — 90 degree sweep
        start = self.angle % 360
        self.canvas.create_arc(
            pad, pad, self.size - pad, self.size - pad,
            start=start, extent=90, style="arc",
            outline=self._color, width=5, tags="arc"
        )

    def start_animation(self, color: str = GREEN) -> None:
        self._color = color
        self.animating = True
        self._animate()

    def stop_animation(self) -> None:
        self.animating = False
        self.canvas.delete("arc")
        self._draw_static()

    def set_color(self, color: str) -> None:
        self._color = color

    def _animate(self) -> None:
        if not self.animating:
            return
        self.angle += 4
        self._draw_static()
        self._draw_arc()
        self.canvas.after(30, self._animate)


class PowerButton:
    """Large circular power button drawn on canvas."""

    def __init__(self, parent: tk.Frame, size: int = 100, command=None) -> None:
        self.size = size
        self.on = False
        self._command = command
        self.canvas = tk.Canvas(
            parent, width=size, height=size,
            bg=BG, highlightthickness=0, cursor="hand2"
        )
        self.canvas.bind("<Button-1>", lambda e: self._click())
        self.canvas.bind("<Enter>", lambda e: self._hover(True))
        self.canvas.bind("<Leave>", lambda e: self._hover(False))
        self._hovering = False
        self._draw()

    def _draw(self) -> None:
        self.canvas.delete("all")
        c = self.size / 2
        r = self.size / 2 - 6

        # Outer circle
        color = RED if self.on else GREEN
        dim_color = RED_DIM if self.on else GREEN_DIM
        fill = dim_color if self._hovering else SURFACE
        self.canvas.create_oval(
            c - r, c - r, c + r, c + r,
            outline=color, width=3, fill=fill
        )

        # Power icon — circle arc
        icon_r = 18
        self.canvas.create_arc(
            c - icon_r, c - icon_r + 4, c + icon_r, c + icon_r + 4,
            start=50, extent=260, style="arc",
            outline=color, width=3
        )
        # Power icon — vertical line
        self.canvas.create_line(
            c, c - icon_r + 2, c, c + 2,
            fill=color, width=3
        )

        # Label below icon
        label = "STOP" if self.on else "START"
        self.canvas.create_text(
            c, c + icon_r + 16,
            text=label, fill=color,
            font=(FONT, 10, "bold")
        )

    def _click(self) -> None:
        if self._command:
            self._command()

    def _hover(self, state: bool) -> None:
        self._hovering = state
        self._draw()

    def set_on(self, on: bool) -> None:
        self.on = on
        self._draw()


class MouseMoverApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.is_running = False
        self.is_paused = False
        self.mouse_thread: Optional[threading.Thread] = None
        self._state_lock = threading.Lock()
        self.start_time: Optional[datetime] = None
        self.move_count = 0
        self.screen_width: Optional[int] = None
        self.screen_height: Optional[int] = None

        self._load_screen_size()
        self._set_icon()
        self._build_ui()
        self._update_timer()

    def _set_icon(self) -> None:
        try:
            # When bundled with PyInstaller, files are in _MEIPASS or app bundle
            if getattr(sys, 'frozen', False):
                base = sys._MEIPASS
            else:
                base = os.path.dirname(os.path.abspath(__file__))

            if sys.platform == "darwin":
                # macOS uses the .icns set in the Info.plist — nothing to do here
                pass
            else:
                ico_path = os.path.join(base, "icon.ico")
                if os.path.exists(ico_path):
                    self.root.iconbitmap(ico_path)
        except Exception:
            pass

    def _load_screen_size(self) -> None:
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception:
            self.screen_width, self.screen_height = 1920, 1080

    def _build_ui(self) -> None:
        self.root.title("Mouse Mover")
        self.root.geometry("360x520")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Center window on screen
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 360) // 2
        y = (sh - 520) // 2
        self.root.geometry(f"360x520+{x}+{y}")

        # ── Title ──
        tk.Label(
            self.root, text="Mouse Mover",
            font=(FONT, 20, "bold"), fg=WHITE, bg=BG
        ).pack(pady=(28, 2))

        tk.Label(
            self.root, text="keep your computer awake",
            font=(FONT, 11), fg=DIM, bg=BG
        ).pack()

        # ── Ring + Power Button (layered) ──
        ring_frame = tk.Frame(self.root, bg=BG)
        ring_frame.pack(pady=(24, 0))

        self.ring = RingIndicator(ring_frame, size=170)
        self.ring.canvas.place(x=0, y=0)

        self.power_btn = PowerButton(ring_frame, size=110, command=self._toggle)
        self.power_btn.canvas.place(x=30, y=30)

        # Need to set frame size to contain both
        ring_frame.config(width=170, height=170)

        # ── Status Label ──
        self.status_label = tk.Label(
            self.root, text="Ready",
            font=(FONT, 13, "bold"), fg=DIM, bg=BG
        )
        self.status_label.pack(pady=(20, 0))

        # ── Stats Card ──
        card = tk.Frame(self.root, bg=SURFACE, padx=0, pady=16)
        card.pack(padx=30, pady=(16, 0), fill="x")

        # Use grid for even columns
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)
        card.columnconfigure(2, weight=1)

        # Time column
        tk.Label(
            card, text="TIME", font=(FONT, 9, "bold"),
            fg=DIM, bg=SURFACE
        ).grid(row=0, column=0)
        self.time_label = tk.Label(
            card, text="00:00:00",
            font=(FONT, 20, "bold"), fg=WHITE, bg=SURFACE
        )
        self.time_label.grid(row=1, column=0, padx=16)

        # Divider
        div = tk.Frame(card, bg=SURFACE_LIGHT, width=1, height=40)
        div.grid(row=0, column=1, rowspan=2, sticky="ns", pady=4)

        # Moves column
        tk.Label(
            card, text="MOVES", font=(FONT, 9, "bold"),
            fg=DIM, bg=SURFACE
        ).grid(row=0, column=2)
        self.moves_label = tk.Label(
            card, text="0",
            font=(FONT, 20, "bold"), fg=WHITE, bg=SURFACE
        )
        self.moves_label.grid(row=1, column=2, padx=16)

        # ── Pause Button ──
        self.pause_btn = tk.Label(
            self.root, text="", font=(FONT, 11),
            fg=DIM, bg=BG, cursor="hand2"
        )
        self.pause_btn.bind("<Button-1>", lambda e: self._pause())
        # Hidden initially — packed when running

        # ── Footer ──
        tk.Label(
            self.root, text="move mouse to any corner to emergency stop",
            font=(FONT, 9), fg="#3d3d5c", bg=BG
        ).pack(side="bottom", pady=(0, 14))

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _toggle(self) -> None:
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        if sys.platform == "darwin":
            try:
                pyautogui.position()
            except Exception:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Permissions Required",
                    "Mouse Mover needs Accessibility permissions.\n\n"
                    "Go to: System Settings > Privacy & Security > Accessibility\n\n"
                    "Add this app, then restart."
                )
                return

        with self._state_lock:
            self.is_running = True
            self.is_paused = False
            self.start_time = datetime.now()
            self.move_count = 0

        self.mouse_thread = threading.Thread(target=self._move_loop, daemon=True)
        self.mouse_thread.start()

        self.power_btn.set_on(True)
        self.ring.start_animation(GREEN)
        self.status_label.config(text="Running", fg=GREEN)
        self.time_label.config(text="00:00:00")
        self.moves_label.config(text="0")

        self.pause_btn.config(text="pause", fg=DIM)
        self.pause_btn.pack(pady=(8, 0))

    def _stop(self) -> None:
        with self._state_lock:
            self.is_running = False
            self.is_paused = False

        self.power_btn.set_on(False)
        self.ring.stop_animation()
        self.status_label.config(text="Stopped", fg=DIM)
        self.pause_btn.pack_forget()

    def _pause(self) -> None:
        with self._state_lock:
            if not self.is_running:
                return
            self.is_paused = not self.is_paused
            paused = self.is_paused

        if paused:
            self.ring.set_color(YELLOW)
            self.status_label.config(text="Paused", fg=YELLOW)
            self.pause_btn.config(text="resume", fg=YELLOW)
        else:
            self.ring.set_color(GREEN)
            self.status_label.config(text="Running", fg=GREEN)
            self.pause_btn.config(text="pause", fg=DIM)

    def _move_loop(self) -> None:
        while True:
            with self._state_lock:
                if not self.is_running:
                    break
                if self.is_paused:
                    time.sleep(PAUSE_CHECK_INTERVAL)
                    continue

            try:
                sw = self.screen_width or 1920
                sh = self.screen_height or 1080

                x = random.randint(SCREEN_MARGIN, max(SCREEN_MARGIN + 1, sw - SCREEN_MARGIN))
                y = random.randint(SCREEN_MARGIN, max(SCREEN_MARGIN + 1, sh - SCREEN_MARGIN))
                duration = random.uniform(MOVE_DURATION_MIN, MOVE_DURATION_MAX)
                pyautogui.moveTo(x, y, duration=duration)

                if random.random() > SECONDARY_MOVE_CHANCE:
                    ox = random.randint(-SECONDARY_MOVE_OFFSET, SECONDARY_MOVE_OFFSET)
                    oy = random.randint(-SECONDARY_MOVE_OFFSET, SECONDARY_MOVE_OFFSET)
                    pyautogui.moveRel(ox, oy, duration=0.3)

                with self._state_lock:
                    self.move_count += 1

                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                time.sleep(delay)

            except pyautogui.FailSafeException:
                self.root.after(0, self._failsafe_stop)
                break
            except Exception:
                time.sleep(1)

    def _failsafe_stop(self) -> None:
        self._stop()
        from tkinter import messagebox
        messagebox.showinfo(
            "Emergency Stop",
            "Mouse moved to a screen corner.\nMouse Mover has been stopped."
        )

    def _update_timer(self) -> None:
        if self.is_running and self.start_time:
            elapsed = datetime.now() - self.start_time
            total_secs = int(elapsed.total_seconds())
            h, remainder = divmod(total_secs, 3600)
            m, s = divmod(remainder, 60)
            self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

        with self._state_lock:
            self.moves_label.config(text=str(self.move_count))

        self.root.after(1000, self._update_timer)

    def _on_close(self) -> None:
        with self._state_lock:
            self.is_running = False
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    MouseMoverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
