#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 bootstrap: generate tools/w44_lib.py from the W39 live_lib.py base.

- Redirect path constants to W44's own out/ and sandbox_game/.
- Append the save/load dialog helpers from W27 live_lib.py verbatim
  (W39's library dropped them; the C-line E2E card needs Esc->SaveGame->Load).
- Keep W39's step-0 desktop precheck and the GBK-console-safe Sink.step.
"""
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W39 = RUN / "W39_mapselmd_live2"
W44 = RUN / "W44_c_line_e2e"

src = (W39 / "tools" / "live_lib.py").read_text(encoding="utf-8")

old_paths = (
    'ROOT = Path(r"D:\\Project\\ra2-campaign-forge")\n'
    'RUN = ROOT / "lead" / "next_re_20261112_r02"\n'
    'W35 = RUN / "W35_mapselmd_live"\n'
    'W39 = RUN / "W39_mapselmd_live2"\n'
    'OUT = W39 / "out"\n'
    'GAME = W35 / "sandbox_game"\n'
    'LOCK = RUN / ".game_instance.lock"'
)
new_paths = (
    'ROOT = Path(r"D:\\Project\\ra2-campaign-forge")\n'
    'RUN = ROOT / "lead" / "next_re_20261112_r02"\n'
    'W44 = RUN / "W44_c_line_e2e"\n'
    'OUT = W44 / "out"\n'
    'GAME = W44 / "sandbox_game"\n'
    'LOCK = RUN / ".game_instance.lock"'
)
assert old_paths in src, "W39 path block not found - base changed"
src = src.replace(old_paths, new_paths, 1)

old_lock = (
    'lock_claim("lead", "W39 live card finished: restored owner=lead '
    '(all game instances closed, configs restored)")'
)
new_lock = (
    'lock_claim("lead", "W44 C-line E2E card finished: restored owner=lead '
    '(all game instances closed, configs byte-restored, drops removed)")'
)
assert old_lock in src, "W39 lock text not found"
src = src.replace(old_lock, new_lock, 1)

EXTRA = r'''

# ---------------------------------------------------------------------------
# W44 additions: save/load dialog helpers (verbatim semantics from W27 live_lib)
# ---------------------------------------------------------------------------
WM_SETTEXT = 0x000C
LB_GETCOUNT = 0x018B
LB_GETITEMDATA = 0x0199
LB_SETCURSEL = 0x0186
LB_GETCURSEL = 0x0188
LB_GETTEXTLEN = 0x018A
LB_GETTEXT = 0x0189
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001


def smt(h, msg, wp=0, lp=0, timeout=2500):
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(h, msg, wp, lp, SMTO_ABORTIFHUNG, timeout,
                          ctypes.byref(r))
    return r.value


def read_utf16_ptr(hproc, ptr, max_bytes=480):
    if not ptr:
        return None
    b = rpm_partial(hproc, ptr, max_bytes)
    if not b:
        return None
    out = bytearray()
    for j in range(0, len(b) - 1, 2):
        if b[j] == 0 and b[j + 1] == 0:
            break
        out += b[j:j + 2]
    try:
        return bytes(out).decode("utf-16-le", errors="replace")
    except Exception:
        return None


def read_listbox(hproc, hwnd, sink: Sink, label, max_items=400):
    """LB_GETCOUNT + LB_GETITEMDATA -> pointer -> UTF-16LE (W7 technique)."""
    n = int(smt(hwnd, LB_GETCOUNT))
    cur = int(smt(hwnd, LB_GETCURSEL))
    items = []
    for i in range(min(n, max_items)):
        d = int(smt(hwnd, LB_GETITEMDATA, i)) & 0xFFFFFFFF
        items.append({"index": i, "itemdata": d,
                      "name": read_utf16_ptr(hproc, d)})
    sink.step("listbox", label=label, hwnd=hwnd, n_items=n, cur_sel=cur,
              items=items)
    return {"hwnd": hwnd, "n": n, "cur": cur, "items": items}


def type_ascii(sink: Sink, label: str, text: str, wait_s=0.6):
    """Type plain ASCII via keybd_event (VK code == ASCII for A-Z, 0-9)."""
    for ch in text:
        vk = ord(ch.upper())
        u.keybd_event(vk, 0, 0, 0)
        u.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)
    sink.step("type_ascii", label=label, text=text)
    time.sleep(wait_s)


def wm_settext(sink: Sink, label: str, hwnd, text: str, wait_s=0.5):
    b = ctypes.create_unicode_buffer(text)
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(hwnd, WM_SETTEXT, 0, ctypes.addressof(b),
                          SMTO_ABORTIFHUNG, 2000, ctypes.byref(r))
    sink.step("wm_settext", label=label, hwnd=hwnd, text=text,
              result=int(r.value))
    time.sleep(wait_s)


def save_inventory(sink: Sink, label: str):
    rows = []
    for p in sorted(GAME.glob("*"), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in (".sav", ".svg"):
            rows.append({"name": p.name, "size": p.stat().st_size,
                         "sha256": sha256_file(p),
                         "mtime_ns": p.stat().st_mtime_ns})
    sink.step("save_inventory", label=label, files=rows, n=len(rows))
    return rows


def post_mouse_click(sink: Sink, label: str, hwnd, x: int, y: int,
                     wait_s=1.0):
    """Send WM_LBUTTONDOWN/UP to a window at CLIENT coordinates."""
    lp = (int(y) << 16) | (int(x) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    sink.step("post_mouse_click", label=label, hwnd=hwnd, x=x, y=y,
              wait_s=wait_s)
    time.sleep(wait_s)
'''

src = src.rstrip() + "\n" + EXTRA
dst = W44 / "tools" / "w44_lib.py"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(src, encoding="utf-8")
print("wrote", dst, "bytes", len(src.encode("utf-8")))
