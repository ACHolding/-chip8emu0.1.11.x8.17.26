#!/usr/bin/env python3.14
"""
AC's CHIP-8 EMU 0.1.1
Single-file Python 3.14 CHIP-8 emulator with:
- 600x400 mGBA-inspired GUI
- Menu strip: File / Emulation / Built-in ROMs / Help
- files = on: load ROMs from disk (File > Load ROM, Ctrl+O, drag-and-drop, argv)
- Built-in Pong + Tetris ROMs embedded as bytes
- Play / Pause / Reset / Exit
- Keyboard controls

Requires: pygame-ce or pygame
"""

import sys
import os
import random
import subprocess
import ctypes
from ctypes import wintypes

import pygame

APP_NAME = "AC's CHIP-8 EMU 0.1.1"
WINDOW_W, WINDOW_H = 600, 400
DISPLAY_W, DISPLAY_H = 64, 32
SCALE = 8
VIEW_W, VIEW_H = DISPLAY_W * SCALE, DISPLAY_H * SCALE
TOP_BAR_H = 28
STATUS_H = 34

BG = (14, 20, 28)
PANEL = (22, 32, 45)
MENU = (40, 44, 50)
MENU_HOVER = (66, 74, 84)
TEXT = (225, 235, 245)
CYAN = (90, 205, 255)
PIXEL_ON = (102, 220, 255)
PIXEL_OFF = (4, 10, 18)
BORDER = (75, 100, 120)

FONTSET = bytes([
    0xF0,0x90,0x90,0x90,0xF0, 0x20,0x60,0x20,0x20,0x70,
    0xF0,0x10,0xF0,0x80,0xF0, 0xF0,0x10,0xF0,0x10,0xF0,
    0x90,0x90,0xF0,0x10,0x10, 0xF0,0x80,0xF0,0x10,0xF0,
    0xF0,0x80,0xF0,0x90,0xF0, 0xF0,0x10,0x20,0x40,0x40,
    0xF0,0x90,0xF0,0x90,0xF0, 0xF0,0x90,0xF0,0x10,0xF0,
    0xF0,0x90,0xF0,0x90,0x90, 0xE0,0x90,0xE0,0x90,0xE0,
    0xF0,0x80,0x80,0x80,0xF0, 0xE0,0x90,0x90,0x90,0xE0,
    0xF0,0x80,0xF0,0x80,0xF0, 0xF0,0x80,0xF0,0x80,0x80,
])

# ---------------------------------------------------------------------------
# Built-in ROMs
# ---------------------------------------------------------------------------
# Original, legal CHIP-8 homebrew assembled directly into the program.  These
# bytes are copied into emulated RAM at 0x200; no ROM files are extracted or
# written to disk.

# Two-player Pong: Q/A moves the left paddle, E/D moves the right paddle.
# Jump targets: 0x220 skips only the bounce (not paddle input); 0x25E/0x262
# use SNE so the ball resets on the left/right edge instead of every frame.
PONG_ROM = bytes.fromhex("""
    00 e0 60 02 61 0c 62 3d 63 0c 64 20 65 10 66 01
    67 01 00 e0 a2 7c d0 15 d2 35 a2 81 d4 51 4f 00
    12 26 68 00 86 87 69 04 e9 9e 12 30 31 00 71 ff
    69 07 e9 9e 12 3a 31 1b 71 01 69 06 e9 9e 12 44
    33 00 73 ff 69 09 e9 9e 12 4e 33 1b 73 01 84 64
    85 74 35 00 12 58 67 01 35 1f 12 5e 67 ff 44 00
    12 68 44 3f 12 68 12 70 64 20 65 10 66 01 67 01
    6a 02 fa 15 fa 07 3a 00 12 74 12 12 80 80 80 80
    80 80
""")

# Original tetromino Tetris (I/O/T/S/Z/J/L): Q/E move, W rotate, S drop.
# 10x20 well with gravity, rotation, and line clears. CHIP-8 homebrew.
TETRIS_ROM = bytes.fromhex("""
    00 e0 24 00 12 06 c4 07 34 07 12 0e 12 06 65 00
    62 17 63 05 23 14 4f 01 12 20 67 0c f7 15 12 26
    00 e0 f0 0a 12 00 60 04 e0 9e 12 3c a4 f8 f0 65
    40 00 22 94 60 01 a4 f8 f0 55 12 42 60 00 a4 f8
    f0 55 60 06 e0 9e 12 58 a4 f9 f0 65 40 00 22 9c
    60 01 a4 f9 f0 55 12 5e 60 00 a4 f9 f0 55 60 05
    e0 9e 12 74 a4 fa f0 65 40 00 22 d2 60 01 a4 fa
    f0 55 12 7a 60 00 a4 fa f0 55 f0 07 30 00 12 26
    22 a4 3e 01 12 88 12 ee 67 0c 60 08 e0 a1 67 01
    f7 15 12 26 68 ff 69 00 22 ae 00 ee 68 01 69 00
    22 ae 00 ee 68 00 69 01 6e 00 22 ae 00 ee 6e 00
    23 14 82 84 83 94 23 14 4f 01 12 be 00 ee 23 14
    80 20 80 85 82 00 80 30 80 95 83 00 23 14 6e 01
    00 ee 8a 50 23 14 75 01 35 04 12 de 65 00 23 14
    4f 01 12 e6 00 ee 23 14 85 a0 23 14 00 ee 23 3a
    23 78 3e 00 12 f8 12 06 23 d0 12 06 80 40 80 0e
    80 0e 80 0e 80 0e 81 50 81 0e 81 0e 80 14 a4 4a
    f0 1e 00 ee 22 fc d2 34 00 ee 38 00 13 20 00 ee
    80 60 80 06 81 f0 86 00 87 06 31 00 13 32 60 80
    87 01 78 ff 38 00 13 20 00 ee 6b 00 22 fc fb 1e
    f0 65 86 00 67 00 88 20 60 14 88 05 23 1a 80 30
    61 05 80 15 80 b4 61 14 81 05 3f 01 13 70 80 0e
    a4 d0 f0 1e 8d 60 8c 70 f1 65 80 d1 81 c1 f1 55
    7b 01 3b 04 13 3c 00 ee 6e 00 69 00 39 14 13 82
    00 ee 80 90 80 0e a4 d0 f0 1e f1 65 30 ff 13 a0
    82 10 63 c0 82 32 32 c0 13 a0 23 a4 7e 01 13 7c
    79 01 13 7c 88 90 38 00 13 ac 13 c6 80 80 70 ff
    80 0e a4 d0 f0 1e f1 65 82 80 82 0e a4 d0 f2 1e
    f1 55 78 ff 13 a6 60 00 61 00 a4 d0 f1 55 00 ee
    00 e0 24 16 23 d8 00 ee 63 05 6c 00 80 c0 80 0e
    a4 d0 f0 1e f1 65 a4 fb f1 55 62 14 a4 fb d2 31
    62 1c a4 fc d2 31 73 01 7c 01 3c 14 13 dc 00 ee
    6e 2d a4 d0 60 00 f0 55 60 01 f0 1e 7e ff 3e 00
    14 04 24 16 00 ee 62 13 63 05 a4 ba d2 3f 63 14
    60 0f a4 ba f0 1e d2 35 62 1e 63 05 a4 ba d2 3f
    63 14 60 0f a4 ba f0 1e d2 35 62 13 63 19 a4 ce
    d2 31 62 1b a4 cf d2 31 00 ee 00 f0 00 00 40 40
    40 40 00 f0 00 00 40 40 40 40 60 60 00 00 60 60
    00 00 60 60 00 00 60 60 00 00 e0 40 00 00 40 c0
    40 00 40 e0 00 00 40 60 40 00 60 c0 00 00 40 60
    20 00 60 c0 00 00 40 60 20 00 c0 60 00 00 20 60
    40 00 c0 60 00 00 20 60 40 00 80 e0 00 00 60 40
    40 00 e0 20 00 00 40 40 c0 00 20 e0 00 00 40 40
    60 00 e0 80 00 00 c0 40 40 00 80 80 80 80 80 80
    80 80 80 80 80 80 80 80 80 80 80 80 80 80 ff f0
""")

# Visible Built-in ROMs catalog. The menu strip is generated from this list.
ROM_CATALOG = [
    ("Pong", PONG_ROM, "F2", "Q/A left paddle, E/D right paddle"),
    ("Tetris", TETRIS_ROM, "F3", "Q/E move, W rotate, S drop"),
]

BUILTINS = {name: data for name, data, _shortcut, _controls in ROM_CATALOG}
BUILTIN_CONTROLS = {
    name: controls for name, _data, _shortcut, controls in ROM_CATALOG
}
CATALOG_FKEYS = {
    pygame.K_F2: "Pong",
    pygame.K_F3: "Tetris",
}

KEYMAP = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}

ROM_FILTER_TK = [
    ("All files", "*.*"),
    ("CHIP-8 ROM", "*.ch8 *.c8 *.rom *.bin *.chip8"),
]


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", wintypes.LPARAM),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", ctypes.c_void_p),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


def windows_open_filename(title, initial_dir, hwnd=None):
    """In-process Win32 picker. Owns the pygame HWND so the dialog stays on top."""
    OFN_EXPLORER = 0x00080000
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800
    OFN_NOCHANGEDIR = 0x00000008
    OFN_HIDEREADONLY = 0x00000004
    filter_str = (
        "All files (*.*)\0*.*\0"
        "CHIP-8 ROM (*.ch8;*.c8;*.rom;*.bin;*.chip8)\0*.ch8;*.c8;*.rom;*.bin;*.chip8\0\0"
    )
    buf = ctypes.create_unicode_buffer(32768)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.hwndOwner = hwnd or None
    ofn.lpstrFilter = filter_str
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = len(buf)
    ofn.lpstrInitialDir = initial_dir or None
    ofn.lpstrTitle = title
    ofn.Flags = (
        OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST
        | OFN_NOCHANGEDIR | OFN_HIDEREADONLY
    )
    if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return buf.value or None
    err = ctypes.windll.comdlg32.CommDlgExtendedError()
    if err:
        raise OSError(f"GetOpenFileName failed ({err})")
    return None


def tk_open_filename(title, initial_dir):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    try:
        root.wm_attributes("-topmost", 1)
    except tk.TclError:
        pass
    path = filedialog.askopenfilename(
        parent=root,
        title=title,
        initialdir=initial_dir or os.getcwd(),
        filetypes=ROM_FILTER_TK,
    )
    root.destroy()
    return path or None

class Chip8:
    def __init__(self):
        self.memory = bytearray(4096)
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay = 0
        self.sound = 0
        self.keys = [0] * 16
        self.display = [0] * (DISPLAY_W * DISPLAY_H)
        self.wait_reg = None
        self.load_font()

    def load_font(self):
        self.memory[0x50:0x50+len(FONTSET)] = FONTSET

    def reset(self):
        self.memory = bytearray(4096)
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay = 0
        self.sound = 0
        self.keys = [0] * 16
        self.display = [0] * (DISPLAY_W * DISPLAY_H)
        self.wait_reg = None
        self.load_font()

    def load_rom(self, data: bytes):
        self.reset()
        if len(data) > 4096 - 0x200:
            raise ValueError("ROM is too large for CHIP-8 memory.")
        self.memory[0x200:0x200+len(data)] = data

    def key_down(self, chip_key):
        self.keys[chip_key] = 1
        if self.wait_reg is not None:
            self.V[self.wait_reg] = chip_key
            self.wait_reg = None

    def key_up(self, chip_key):
        self.keys[chip_key] = 0

    def tick_timers(self):
        if self.delay > 0:
            self.delay -= 1
        if self.sound > 0:
            self.sound -= 1

    def _skip(self):
        self.pc = (self.pc + 2) & 0xFFF

    def cycle(self):
        if self.wait_reg is not None:
            return
        op = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc = (self.pc + 2) & 0xFFF

        nnn = op & 0x0FFF
        nn = op & 0x00FF
        n = op & 0x000F
        x = (op >> 8) & 0xF
        y = (op >> 4) & 0xF

        if op == 0x00E0:
            self.display = [0] * (DISPLAY_W * DISPLAY_H)
        elif op == 0x00EE:
            if self.stack:
                self.pc = self.stack.pop() & 0xFFF
        elif op & 0xF000 == 0x1000:
            self.pc = nnn
        elif op & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
        elif op & 0xF000 == 0x3000:
            if self.V[x] == nn:
                self._skip()
        elif op & 0xF000 == 0x4000:
            if self.V[x] != nn:
                self._skip()
        elif op & 0xF00F == 0x5000:
            if self.V[x] == self.V[y]:
                self._skip()
        elif op & 0xF000 == 0x6000:
            self.V[x] = nn
        elif op & 0xF000 == 0x7000:
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif op & 0xF00F == 0x8000:
            self.V[x] = self.V[y]
        elif op & 0xF00F == 0x8001:
            self.V[x] |= self.V[y]
        elif op & 0xF00F == 0x8002:
            self.V[x] &= self.V[y]
        elif op & 0xF00F == 0x8003:
            self.V[x] ^= self.V[y]
        elif op & 0xF00F == 0x8004:
            s = self.V[x] + self.V[y]
            self.V[x] = s & 0xFF
            self.V[0xF] = 1 if s > 255 else 0
        elif op & 0xF00F == 0x8005:
            flag = 1 if self.V[x] >= self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            self.V[0xF] = flag
        elif op & 0xF00F == 0x8006:
            flag = self.V[x] & 1
            self.V[x] >>= 1
            self.V[0xF] = flag
        elif op & 0xF00F == 0x8007:
            flag = 1 if self.V[y] >= self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            self.V[0xF] = flag
        elif op & 0xF00F == 0x800E:
            flag = (self.V[x] >> 7) & 1
            self.V[x] = (self.V[x] << 1) & 0xFF
            self.V[0xF] = flag
        elif op & 0xF00F == 0x9000:
            if self.V[x] != self.V[y]:
                self._skip()
        elif op & 0xF000 == 0xA000:
            self.I = nnn
        elif op & 0xF000 == 0xB000:
            self.pc = (nnn + self.V[0]) & 0xFFF
        elif op & 0xF000 == 0xC000:
            self.V[x] = random.randint(0, 255) & nn
        elif op & 0xF000 == 0xD000:
            vx = self.V[x] % DISPLAY_W
            vy = self.V[y] % DISPLAY_H
            self.V[0xF] = 0
            for row in range(n):
                py = vy + row
                if py >= DISPLAY_H:
                    break
                sprite = self.memory[(self.I + row) & 0xFFF]
                for bit in range(8):
                    if not (sprite & (0x80 >> bit)):
                        continue
                    px = vx + bit
                    if px >= DISPLAY_W:
                        continue
                    idx = py * DISPLAY_W + px
                    if self.display[idx]:
                        self.V[0xF] = 1
                    self.display[idx] ^= 1
        elif op & 0xF0FF == 0xE09E:
            if self.keys[self.V[x] & 0xF]:
                self._skip()
        elif op & 0xF0FF == 0xE0A1:
            if not self.keys[self.V[x] & 0xF]:
                self._skip()
        elif op & 0xF0FF == 0xF007:
            self.V[x] = self.delay
        elif op & 0xF0FF == 0xF00A:
            self.wait_reg = x
        elif op & 0xF0FF == 0xF015:
            self.delay = self.V[x]
        elif op & 0xF0FF == 0xF018:
            self.sound = self.V[x]
        elif op & 0xF0FF == 0xF01E:
            self.I = (self.I + self.V[x]) & 0xFFF
        elif op & 0xF0FF == 0xF029:
            self.I = 0x50 + (self.V[x] & 0xF) * 5
        elif op & 0xF0FF == 0xF033:
            v = self.V[x]
            addr = self.I & 0xFFF
            self.memory[addr] = v // 100
            self.memory[(addr + 1) & 0xFFF] = (v // 10) % 10
            self.memory[(addr + 2) & 0xFFF] = v % 10
        elif op & 0xF0FF == 0xF055:
            for i in range(x + 1):
                self.memory[(self.I + i) & 0xFFF] = self.V[i]
        elif op & 0xF0FF == 0xF065:
            for i in range(x + 1):
                self.V[i] = self.memory[(self.I + i) & 0xFFF]

class MenuItem:
    def __init__(self, text, action=None, submenu=None):
        self.text = text
        self.action = action
        self.submenu = submenu or []

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(APP_NAME)
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16) or pygame.font.Font(None, 18)
        self.small = pygame.font.SysFont("Arial", 14) or pygame.font.Font(None, 16)
        self.title_font = pygame.font.SysFont("Arial", 18) or pygame.font.Font(None, 20)
        self.chip = Chip8()
        self.running = True
        self.paused = True
        self.current_rom_name = "No ROM loaded"
        self.current_rom = b""
        self.chip.reset()
        self.cpu_hz = 700
        self.cycles_accum = 0.0
        self.timer_accum = 0.0
        self.active_menu = None
        self.menu_rects = {}
        self.drop_rects = []
        self.drop_panel = None
        self.status = "Ready — File > Load ROM, Ctrl+O, or drop a .ch8 file"
        self.rom_dir = os.path.dirname(os.path.abspath(__file__))
        self.make_menus()

    def make_menus(self):
        self.menus = [
            ("File", [
                MenuItem("Load ROM... (Ctrl+O)", self.load_external),
                MenuItem("Exit", self.quit),
            ]),
            ("Emulation", [
                MenuItem("Play", self.play),
                MenuItem("Pause", self.pause),
                MenuItem("Reset", self.reset),
            ]),
            ("Built-in ROMs", [
                MenuItem(
                    f"{name} ({shortcut})",
                    lambda n=name: self.load_builtin(n),
                )
                for name, _data, shortcut, _controls in ROM_CATALOG
            ]),
            ("Help", [
                MenuItem("Controls", self.show_controls),
                MenuItem("About", self.show_about),
            ]),
        ]

    def pygame_hwnd(self):
        try:
            info = pygame.display.get_wm_info()
        except pygame.error:
            return None
        return info.get("window") or info.get("hwnd") or None

    def native_open_dialog(self):
        """Pick a ROM path. files=on: all files are visible.

        Windows: Win32 GetOpenFileName owned by the pygame window
        macOS: AppleScript chooser (avoids Tk/SDL NSApplication collision)
        Linux: zenity, then Tk
        Fallback: Tk filedialog
        """
        title = "Load CHIP-8 ROM"
        initial = self.rom_dir if os.path.isdir(self.rom_dir) else os.getcwd()
        try:
            if os.name == "nt":
                hwnd = self.pygame_hwnd()
                if not hwnd:
                    hwnd = (
                        ctypes.windll.user32.GetActiveWindow()
                        or ctypes.windll.user32.GetForegroundWindow()
                    )
                try:
                    return windows_open_filename(title, initial, hwnd)
                except OSError:
                    return tk_open_filename(title, initial)

            if sys.platform == "darwin":
                script = f'POSIX path of (choose file with prompt "{title}")'
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True, check=False
                )
                path = result.stdout.strip()
                return path or None

            result = subprocess.run(
                ["zenity", "--file-selection", f"--title={title}",
                 "--file-filter=All files | *",
                 "--file-filter=CHIP-8 ROM | *.ch8 *.c8 *.rom *.bin *.chip8",
                 f"--filename={initial}/"],
                capture_output=True, text=True, check=False
            )
            path = result.stdout.strip()
            if path:
                return path
            return tk_open_filename(title, initial)
        except (OSError, subprocess.SubprocessError, Exception):
            try:
                return tk_open_filename(title, initial)
            except Exception:
                return None

    def load_rom_from_path(self, path):
        if not path:
            self.status = "Load cancelled"
            return False
        path = os.path.normpath(str(path).strip().strip('"'))
        try:
            with open(path, "rb") as f:
                data = f.read()
            if not data:
                raise ValueError("File is empty.")
            self.current_rom = data
            self.current_rom_name = os.path.basename(path)
            self.rom_dir = os.path.dirname(path) or self.rom_dir
            self.chip.load_rom(data)
            self.paused = False
            self.status = f"Loaded {self.current_rom_name} ({len(data)} bytes)"
            return True
        except Exception as exc:
            self.paused = True
            self.status = f"Load error: {exc}"
            return False

    def load_external(self):
        path = self.native_open_dialog()
        pygame.event.clear()
        self.chip.keys = [0] * 16
        self.load_rom_from_path(path)

    def load_builtin(self, name):
        self.current_rom = BUILTINS[name]
        self.current_rom_name = f"{name} (built-in)"
        self.chip.load_rom(self.current_rom)
        self.paused = False
        self.status = f"{name}: {BUILTIN_CONTROLS[name]}"

    def play(self):
        self.paused = False
        self.status = "Running"

    def pause(self):
        self.paused = True
        self.status = "Paused"

    def reset(self):
        if self.current_rom:
            self.chip.load_rom(self.current_rom)
            self.paused = False
            self.status = "Reset"
        else:
            self.chip.reset()
            self.paused = True
            self.status = "Blank — no ROM loaded"

    def quit(self):
        self.running = False

    def show_controls(self):
        games = " | ".join(
            f"{name} {controls} ({shortcut})"
            for name, _data, shortcut, controls in ROM_CATALOG
        )
        self.status = f"Load: Ctrl+O or drop a file | {games}"

    def show_about(self):
        names = " + ".join(name for name, *_rest in ROM_CATALOG)
        self.status = (
            f"AC's CHIP-8 EMU 0.1.1 — Python 3.14 — {names} built in"
        )

    def menu_hit(self, pos):
        for name, rect in self.menu_rects.items():
            if rect.collidepoint(pos):
                return name
        return None

    def draw_text(self, text, x, y, color=TEXT, font=None):
        surf = (font or self.font).render(text, True, color)
        self.screen.blit(surf, (x, y))
        return surf.get_rect(topleft=(x, y))

    def draw_menu(self):
        pygame.draw.rect(self.screen, MENU, (0, 0, WINDOW_W, TOP_BAR_H))
        pygame.draw.line(self.screen, BORDER, (0, TOP_BAR_H - 1), (WINDOW_W, TOP_BAR_H - 1))
        x = 8
        self.menu_rects = {}
        label_y = max(0, (TOP_BAR_H - self.font.get_height()) // 2)
        for name, items in self.menus:
            w = self.font.size(name)[0] + 22
            rect = pygame.Rect(x, 0, w, TOP_BAR_H)
            if self.active_menu == name:
                pygame.draw.rect(self.screen, MENU_HOVER, rect)
            self.draw_text(name, x + 10, label_y)
            self.menu_rects[name] = rect
            x += w

        self.drop_rects = []
        self.drop_panel = None
        if self.active_menu:
            items = dict(self.menus)[self.active_menu]
            base = self.menu_rects[self.active_menu]
            width = max(self.font.size(i.text)[0] for i in items) + 36
            height = len(items) * 24 + 6
            panel = pygame.Rect(base.x, TOP_BAR_H, width, height)
            pygame.draw.rect(self.screen, (44, 48, 54), panel)
            pygame.draw.rect(self.screen, BORDER, panel, 1)
            self.drop_panel = panel
            for idx, item in enumerate(items):
                rect = pygame.Rect(panel.x + 2, panel.y + 3 + idx * 24, width - 4, 24)
                mouse = pygame.mouse.get_pos()
                if rect.collidepoint(mouse):
                    pygame.draw.rect(self.screen, MENU_HOVER, rect)
                self.draw_text(item.text, rect.x + 8, rect.y + 4)
                self.drop_rects.append((rect, item))

    def draw_chip8(self):
        x0 = (WINDOW_W - VIEW_W) // 2
        avail = WINDOW_H - TOP_BAR_H - STATUS_H
        y0 = TOP_BAR_H + max(6, (avail - VIEW_H) // 2)
        pygame.draw.rect(self.screen, BORDER, (x0-2, y0-2, VIEW_W+4, VIEW_H+4), 2)
        pygame.draw.rect(self.screen, PIXEL_OFF, (x0, y0, VIEW_W, VIEW_H))
        for y in range(DISPLAY_H):
            row = y * DISPLAY_W
            for x in range(DISPLAY_W):
                if self.chip.display[row+x]:
                    pygame.draw.rect(
                        self.screen, PIXEL_ON,
                        (x0 + x*SCALE, y0 + y*SCALE, SCALE, SCALE)
                    )

    def draw_status(self):
        y = WINDOW_H - STATUS_H
        pygame.draw.rect(self.screen, PANEL, (0, y, WINDOW_W, STATUS_H))
        self.draw_text(self.current_rom_name, 10, y + 5, CYAN, self.small)
        state = "PAUSED" if self.paused else "RUNNING"
        self.draw_text(f"{state}  |  {self.status}", 10, y + 19, TEXT, self.small)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active_menu = None
                return
            if event.key == pygame.K_o and (event.mod & pygame.KMOD_CTRL):
                self.active_menu = None
                self.load_external()
                return
            if event.key in CATALOG_FKEYS:
                self.active_menu = None
                self.load_builtin(CATALOG_FKEYS[event.key])
                return
            if event.key in KEYMAP:
                self.chip.key_down(KEYMAP[event.key])
        elif event.type == pygame.KEYUP:
            if event.key in KEYMAP:
                self.chip.key_up(KEYMAP[event.key])
        elif getattr(pygame, "DROPFILE", None) is not None and event.type == pygame.DROPFILE:
            self.load_rom_from_path(getattr(event, "file", None))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.active_menu:
                for rect, item in self.drop_rects:
                    if rect.collidepoint(event.pos):
                        self.active_menu = None
                        if item.action:
                            item.action()
                        return
                if self.drop_panel and self.drop_panel.collidepoint(event.pos):
                    return
            hit = self.menu_hit(event.pos)
            if hit:
                self.active_menu = None if self.active_menu == hit else hit
            else:
                self.active_menu = None

    def emulate(self, dt):
        if self.paused or not self.current_rom:
            return
        self.cycles_accum += self.cpu_hz * dt
        cycles = min(int(self.cycles_accum), 50)
        self.cycles_accum -= cycles
        for _ in range(cycles):
            try:
                self.chip.cycle()
            except Exception as exc:
                self.paused = True
                self.status = f"Emulation error: {exc}"
                break
        self.timer_accum += 60.0 * dt
        while self.timer_accum >= 1.0:
            self.chip.tick_timers()
            self.timer_accum -= 1.0

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.emulate(dt)

            self.screen.fill(BG)
            self.draw_chip8()
            self.draw_status()
            self.draw_menu()
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    app = App()
    if len(sys.argv) > 1:
        app.load_rom_from_path(sys.argv[1])
    app.run()
