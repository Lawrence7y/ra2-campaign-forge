#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_zero_touch_bg.py — 零干扰真后台点击与跨遮挡抓窗实测（绝不抢焦点/不移动鼠标/不写INI）。

严禁调用:
  SetForegroundWindow / BringWindowToTop / focus_game / raise_win /
  SetCursorPos / SendInput / keybd_event / configure_ddraw_for_screen
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import win_display_helper as WDH  # noqa: E402

_INITIAL_MONITORS = WDH.list_monitors()

os.environ["RA2_SCREEN_MODE"] = "secondary"
os.environ["RA2_MUTE_AUDIO"] = "1"
os.environ["RA2_NO_MINIMIZE_PRIMARY"] = "1"
os.environ["RA2_RESTORE_CURSOR"] = "1"

import bench_replay as B  # noqa: E402

GAME_DIR = B.PROJECT / "ra2bench"
OUT_DIR = B.SHOTS / "zero_touch_test"

SW_SHOWNOACTIVATE = 4
SW_MINIMIZE = 6
STARTF_USESHOWWINDOW = 0x00000001
HWND_BOTTOM = wt.HWND(1)
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010

WM_ACTIVATE = 0x0006
WA_ACTIVE = 1
WM_SETFOCUS = 0x0007
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
PW_RENDERFULLCONTENT = 2


def _get_cursor_pos() -> tuple[int, int] | None:
    pt = wt.POINT()
    if B.user32.GetCursorPos(ctypes.byref(pt)):
        return int(pt.x), int(pt.y)
    return None


def grab_printwindow(hwnd: int, path: Path) -> dict:
    """使用 PrintWindow 抓取指定 HWND 渲染内容，即使被用户窗口遮挡也能取图。"""
    import ctypes as c2
    from PIL import Image

    gdi32 = c2.WinDLL("gdi32")
    path.parent.mkdir(parents=True, exist_ok=True)
    l, t, r, b = B.window_bbox(hwnd)
    w, h = max(r - l, 8), max(b - t, 8)
    sdc = B.user32.GetDC(0)
    mdc = gdi32.CreateCompatibleDC(sdc)
    hbmp = gdi32.CreateCompatibleBitmap(sdc, w, h)
    gdi32.SelectObject(mdc, hbmp)

    used_flag = PW_RENDERFULLCONTENT
    ok = B.user32.PrintWindow(wt.HWND(hwnd), mdc, PW_RENDERFULLCONTENT)
    if not ok:
        used_flag = 0
        ok = B.user32.PrintWindow(wt.HWND(hwnd), mdc, 0)

    class BMIH(c2.Structure):
        _fields_ = [
            ("biSize", c2.c_ulong), ("biWidth", c2.c_long), ("biHeight", c2.c_long),
            ("biPlanes", c2.c_ushort), ("biBitCount", c2.c_ushort), ("biCompression", c2.c_ulong),
            ("biSizeImage", c2.c_ulong), ("biXPPM", c2.c_long), ("biYPPM", c2.c_long),
            ("biClrUsed", c2.c_ulong), ("biClrImportant", c2.c_ulong),
        ]

    bmi = BMIH(c2.sizeof(BMIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = c2.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, hbmp, 0, h, buf, c2.byref(bmi), 0)
    img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
    img.save(path)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(mdc)
    B.user32.ReleaseDC(0, sdc)

    raw = path.read_bytes()
    small = img.resize((min(w, 256), min(h, 256)))
    _get_px = small.get_flattened_data if hasattr(small, "get_flattened_data") else small.getdata
    colors = len(set(_get_px()))
    gray_im = small.convert("L")
    _get_gray = gray_im.get_flattened_data if hasattr(gray_im, "get_flattened_data") else gray_im.getdata
    gray = list(_get_gray())
    mean = sum(gray) / len(gray)
    var = sum((x - mean) ** 2 for x in gray) / len(gray)
    return {
        "path": str(path),
        "printwindow_ok": bool(ok),
        "pw_flag": used_flag,
        "width": w,
        "height": h,
        "bytes": len(raw),
        "md5": hashlib.md5(raw).hexdigest(),
        "unique_colors_256": colors,
        "luma_variance": round(var, 1),
        "plausible": bool(colors > 64 and var > 100 and len(raw) > 100_000),
    }


def sidebar_red_buttons_from_png(png_path: Path) -> list[int]:
    """从 PrintWindow PNG 计算侧边栏(x>=640)红钮 y 中心（折算回 800x600 逻辑坐标）。"""
    import numpy as np
    from PIL import Image

    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    a = np.asarray(img).astype(int)
    sx0 = int(640 / 800 * w)
    sub = a[:, sx0:, :]
    if sub.size == 0:
        return []
    rf = ((sub[:, :, 0] > sub[:, :, 1] + 40) & (sub[:, :, 0] > sub[:, :, 2] + 40)).mean(axis=1)
    out, inb, y0 = [], False, 0
    for y in range(h):
        v = rf[y] > 0.25
        if v and not inb:
            inb, y0 = True, y
        elif not v and inb:
            inb = False
            if y - y0 >= 8:
                out.append(int(round((y0 + y - 1) / 2 / h * 600)))
    return out


def banner_mad_from_pngs(p1: Path, p2: Path) -> float:
    """比较两张 PNG 右上纯标题区 (670,4,780,30) 的平均像素绝对差 MAD。"""
    import numpy as np
    from PIL import Image

    def _crop(p: Path):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        box = (int(670 / 800 * w), int(4 / 600 * h), int(780 / 800 * w), int(30 / 600 * h))
        return np.asarray(im.crop(box)).astype(float)

    a, b = _crop(p1), _crop(p2)
    if a.shape != b.shape or a.size == 0:
        return 999.0
    return round(float(np.abs(a - b).mean()), 2)


def _client_size(hwnd: int) -> tuple[int, int]:
    cr = wt.RECT()
    if B.user32.GetClientRect(wt.HWND(hwnd), ctypes.byref(cr)) and cr.right > 0 and cr.bottom > 0:
        return int(cr.right), int(cr.bottom)
    l, t, r, b = B.window_bbox(hwnd)
    return max(1, r - l), max(1, b - t)


def post_click(hwnd: int, lx: int, ly: int, *, lw: int = 800, lh: int = 600, hold: float = 0.10, send_wm_activate: bool = False) -> dict:
    """无鼠标、无焦点投递 WM_MOUSEMOVE + WM_LBUTTONDOWN + WM_LBUTTONUP。"""
    cw, ch = _client_size(hwnd)
    cx = int(lx / lw * cw)
    cy = int(ly / lh * ch)
    lparam = ((cy & 0xFFFF) << 16) | (cx & 0xFFFF)
    c_before = _get_cursor_pos()

    if send_wm_activate:
        B.user32.PostMessageW(wt.HWND(hwnd), WM_ACTIVATE, WA_ACTIVE, 0)
        time.sleep(0.05)
        B.user32.PostMessageW(wt.HWND(hwnd), WM_SETFOCUS, 0, 0)
        time.sleep(0.05)

    ok_move = bool(B.user32.PostMessageW(wt.HWND(hwnd), WM_MOUSEMOVE, 0, lparam))
    time.sleep(0.08)
    ok_down = bool(B.user32.PostMessageW(wt.HWND(hwnd), WM_LBUTTONDOWN, MK_LBUTTON, lparam))
    time.sleep(hold)
    ok_up = bool(B.user32.PostMessageW(wt.HWND(hwnd), WM_LBUTTONUP, 0, lparam))
    c_after = _get_cursor_pos()

    return {
        "lx": lx,
        "ly": ly,
        "client_xy": [cx, cy],
        "send_wm_activate": send_wm_activate,
        "post_ok": bool(ok_move and ok_down and ok_up),
        "cursor_before": list(c_before) if c_before else None,
        "cursor_after": list(c_after) if c_after else None,
        "cursor_untouched": (c_before == c_after),
    }


def _match_buttons(got: list[int], variants: list[list[int]], tol: int = 4) -> list[int] | None:
    for want in variants:
        if len(got) == len(want) and all(abs(g - w) <= tol for g, w in zip(got, want)):
            return want
    return None


def _place_secondary_bottom(hwnd: int, sec_mon: dict) -> dict:
    wx0, wy0, _, _ = sec_mon["work"]
    x = wx0 + 60
    y = wy0 + 60
    ok = bool(B.user32.SetWindowPos(wt.HWND(hwnd), HWND_BOTTOM, x, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE))
    return {"ok": ok, "x": x, "y": y, "z_order": "HWND_BOTTOM", "bbox": list(B.window_bbox(hwnd))}


def _cleanup() -> dict:
    B.kill_game()
    subprocess.run(["taskkill", "/IM", "ra2loader.exe", "/F"], capture_output=True)
    time.sleep(0.4)
    return {
        "gamemd_pid": B.find_pid("gamemd.exe"),
        "ra2loader_pid": B.find_pid("ra2loader.exe"),
        "clean": (B.find_pid("gamemd.exe") is None and B.find_pid("ra2loader.exe") is None),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUT_DIR / "report.json"

    prim_mon = WDH.get_target_monitor("primary")
    sec_mon = WDH.get_target_monitor("secondary")
    report: dict = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "monitors": _INITIAL_MONITORS,
        "phase1_silent_launch": {},
        "phase2_postmessage_nav": {},
        "phase3_background": {},
        "phase3b_minimized": {},
        "focus_watcher": {},
        "cleanup": {},
    }

    stop_watch = threading.Event()
    watch_stats = {"samples": 0, "focus_stolen_hits": 0, "hwnd_target": 0}
    watch_thread = None
    proc = None

    def _watch_fg(game_hwnd: int):
        watch_stats["hwnd_target"] = int(game_hwnd)
        while not stop_watch.is_set():
            fg = int(B.user32.GetForegroundWindow())
            watch_stats["samples"] += 1
            if fg == int(game_hwnd):
                watch_stats["focus_stolen_hits"] += 1
            time.sleep(0.1)

    try:
        _cleanup()
        si = subprocess.STARTUPINFO()
        si.dwFlags |= STARTF_USESHOWWINDOW
        si.wShowWindow = SW_SHOWNOACTIVATE

        t0 = time.time()
        exe = (GAME_DIR / "ra2loader.exe").resolve()
        subprocess.Popen(
            [str(exe)],
            cwd=str(GAME_DIR),
            startupinfo=si,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        pid = None
        t_pid_end = time.time() + 25.0
        while time.time() < t_pid_end and not pid:
            pid = B.find_pid("gamemd.exe")
            if not pid:
                time.sleep(0.4)
        if not pid:
            report["phase1_silent_launch"] = {"ok": False, "error": "gamemd.exe did not start in 25s"}
            return 1

        WDH.start_mute_watcher(pid, mute=True)

        hwnd = None
        t_hw_end = time.time() + 20.0
        while time.time() < t_hw_end and not hwnd:
            hwnd = B.find_game_hwnd(pid)
            if not hwnd:
                time.sleep(0.4)
        if not hwnd:
            report["phase1_silent_launch"] = {"ok": False, "pid": pid, "error": "hwnd not found in 20s"}
            return 1

        watch_thread = threading.Thread(target=_watch_fg, args=(hwnd,), daemon=True)
        watch_thread.start()

        placed = _place_secondary_bottom(hwnd, sec_mon) if sec_mon else {"ok": False}

        # 等最多 45s 用 PrintWindow 检测主菜单出现（不发按键也不抢焦）
        pw_main_path = OUT_DIR / "01_pw_mainmenu.png"
        shot1 = None
        menu_btns: list[int] = []
        rb_all: list[int] = []
        t_mm_end = time.time() + 45.0
        while time.time() < t_mm_end:
            shot1 = grab_printwindow(hwnd, pw_main_path)
            rb_all = sidebar_red_buttons_from_png(pw_main_path)
            menu_btns = [y for y in rb_all if y >= 150]
            if shot1["plausible"] and len(menu_btns) >= 3:
                time.sleep(2.0)
                shot1 = grab_printwindow(hwnd, pw_main_path)
                rb_all = sidebar_red_buttons_from_png(pw_main_path)
                menu_btns = [y for y in rb_all if y >= 150]
                break
            time.sleep(2.0)

        mute_p1 = WDH.get_pid_mute_state(pid)
        if not mute_p1.get("muted"):
            WDH.mute_pid_audio(pid, mute=True)
            mute_p1 = WDH.get_pid_mute_state(pid)

        report["phase1_silent_launch"] = {
            "ok": bool(shot1 and shot1["plausible"] and len(menu_btns) >= 3),
            "pid": pid,
            "hwnd": int(hwnd),
            "elapsed_s": round(time.time() - t0, 2),
            "placed_secondary_bottom": placed,
            "audio_mute_state": mute_p1,
            "rb_all": rb_all,
            "menu_buttons": menu_btns,
            "shot_01_pw_mainmenu": shot1,
        }

        # Phase 2: PostMessageW 无鼠标/无焦点点击测试
        sp_variants = [[220, 262, 304, 556], [220, 262, 556]]
        phase1_on_mainmenu = bool(report["phase1_silent_launch"]["ok"])
        click_sp_pure = post_click(hwnd, 700, 218, send_wm_activate=False)
        time.sleep(3.5)
        p2a_path = OUT_DIR / "02_pw_after_sp_click.png"
        shot2a = grab_printwindow(hwnd, p2a_path)
        mad2a = banner_mad_from_pngs(pw_main_path, p2a_path)
        rb2a = sidebar_red_buttons_from_png(p2a_path)
        btns2a = [y for y in rb2a if y >= 150]
        sp_entered = bool(phase1_on_mainmenu and mad2a > 5.0 and _match_buttons(btns2a, sp_variants) is not None)

        click_sp_wmact = None
        shot2b = None
        mad2b = None
        btns2b: list[int] = []
        active_sp_path = p2a_path
        active_sp_btns = btns2a
        used_wm_activate = False

        if not sp_entered:
            click_sp_wmact = post_click(hwnd, 700, 218, send_wm_activate=True)
            time.sleep(3.5)
            p2b_path = OUT_DIR / "02b_pw_after_sp_wmact.png"
            shot2b = grab_printwindow(hwnd, p2b_path)
            mad2b = banner_mad_from_pngs(pw_main_path, p2b_path)
            rb2b = sidebar_red_buttons_from_png(p2b_path)
            btns2b = [y for y in rb2b if y >= 150]
            if phase1_on_mainmenu and mad2b > 5.0 and _match_buttons(btns2b, sp_variants) is not None:
                sp_entered = True
                used_wm_activate = True
                active_sp_path = p2b_path
                active_sp_btns = btns2b

        nav_rec: dict = {
            "postmessage_sp_entered": sp_entered,
            "used_wm_activate_fallback": used_wm_activate,
            "click_sp_pure": click_sp_pure,
            "shot_02_after_sp_click": shot2a,
            "mad_02": mad2a,
            "btns_02": btns2a,
            "click_sp_wmact": click_sp_wmact,
            "shot_02b_after_sp_wmact": shot2b,
            "mad_02b": mad2b,
            "btns_02b": btns2b,
            "skirmish_entered": False,
            "battle_ready": False,
        }

        proc = B.open_proc(pid)
        mon = B.BattleMonitor(proc)
        battle_ready = False

        if sp_entered:
            skirmish_y = 262 if len(active_sp_btns) == 3 else 304
            click_sk = post_click(hwnd, 700, skirmish_y, send_wm_activate=used_wm_activate)
            time.sleep(6.0)
            p3_path = OUT_DIR / "03_pw_skirmish.png"
            shot3 = grab_printwindow(hwnd, p3_path)
            mad3 = banner_mad_from_pngs(active_sp_path, p3_path)
            rb3 = sidebar_red_buttons_from_png(p3_path)
            btns3 = [y for y in rb3 if y >= 150]
            sk_match = _match_buttons(btns3, [[220, 262, 556], [262, 304, 556]])
            sk_ok = (mad3 > 5.0 and sk_match is not None and not any(y < 150 for y in rb3))
            nav_rec.update({
                "skirmish_y": skirmish_y,
                "click_sk": click_sk,
                "shot_03_pw_skirmish": shot3,
                "mad_03": mad3,
                "rb3_all": rb3,
                "btns_03": btns3,
                "skirmish_entered": sk_ok,
            })

            if sk_ok:
                custom_y = btns3[1] if len(btns3) >= 2 else 262
                post_click(hwnd, 700, custom_y, send_wm_activate=used_wm_activate)
                time.sleep(2.5)
                p3b_path = OUT_DIR / "03b_pw_map_browser.png"
                shot3b = grab_printwindow(hwnd, p3b_path)
                btns3b = [y for y in sidebar_red_buttons_from_png(p3b_path) if y >= 150]
                if any(abs(y - 178) <= 6 for y in btns3b):
                    post_click(hwnd, 260, 113, send_wm_activate=used_wm_activate)
                    time.sleep(0.8)
                    post_click(hwnd, 720, 178, send_wm_activate=used_wm_activate)
                    time.sleep(2.5)
                p3c_path = OUT_DIR / "03c_pw_after_map.png"
                shot3c = grab_printwindow(hwnd, p3c_path)
                btns3c = [y for y in sidebar_red_buttons_from_png(p3c_path) if y >= 150]
                start_y = btns3c[0] if btns3c else 220

                click_start = post_click(hwnd, 700, start_y, send_wm_activate=used_wm_activate)
                battle_ready = B.wait_battle_ready(mon, hwnd, timeout=60.0, min_fps=3.0, use_screen=False)
                shot4 = grab_printwindow(hwnd, OUT_DIR / "04_pw_battle_0.png")
                nav_rec.update({
                    "shot_03b_map_browser": shot3b,
                    "shot_03c_after_map": shot3c,
                    "start_y": start_y,
                    "click_start": click_start,
                    "battle_ready": battle_ready,
                    "frame_entry": mon.frame(),
                    "units_entry": mon.mobile_counts(),
                    "shot_04_pw_battle_0": shot4,
                })

        report["phase2_postmessage_nav"] = nav_rec

        if battle_ready:
            frame_bg0 = mon.frame()
            t_bg0 = time.perf_counter()
            sample_ok = True
            sample_error = None
            try:
                sw_res = B.sample_window(pid, proc, seconds=5.0, hz=100.0, require_match=True)
            except Exception as exc:
                sample_ok = False
                sample_error = str(exc)
                sw_res = B.sample_window(pid, proc, seconds=5.0, hz=100.0, require_match=False)
            elapsed_bg = time.perf_counter() - t_bg0
            if elapsed_bg < 6.0:
                time.sleep(6.0 - elapsed_bg)
                elapsed_bg = time.perf_counter() - t_bg0
            frame_bg1 = mon.frame()
            shot5 = grab_printwindow(hwnd, OUT_DIR / "05_pw_battle_1.png")
            mute_p3 = WDH.get_pid_mute_state(pid)
            report["phase3_background"] = {
                "ok": bool(sample_ok and frame_bg1 > frame_bg0 and shot5["md5"] != nav_rec["shot_04_pw_battle_0"]["md5"]),
                "frame_bg0": frame_bg0,
                "frame_bg1": frame_bg1,
                "delta_frames": frame_bg1 - frame_bg0,
                "elapsed_s": round(elapsed_bg, 2),
                "avg_fps": round((frame_bg1 - frame_bg0) / max(elapsed_bg, 0.1), 2),
                "sample_require_match_ok": sample_ok,
                "sample_error": sample_error,
                "sample_window": sw_res,
                "shot_05_pw_battle_1": shot5,
                "pw_md5_changed": shot5["md5"] != nav_rec["shot_04_pw_battle_0"]["md5"],
                "audio_mute_state": mute_p3,
            }

            B.user32.ShowWindow(wt.HWND(hwnd), SW_MINIMIZE)
            time.sleep(0.5)
            f_min0 = mon.frame()
            t_m0 = time.perf_counter()
            time.sleep(3.0)
            t_m1 = time.perf_counter()
            f_min1 = mon.frame()
            dt_m = t_m1 - t_m0
            report["phase3b_minimized"] = {
                "is_iconic": bool(B.user32.IsIconic(wt.HWND(hwnd))),
                "f_min0": f_min0,
                "f_min1": f_min1,
                "minimized_delta_frames": f_min1 - f_min0,
                "minimized_fps": round((f_min1 - f_min0) / max(dt_m, 0.1), 2),
                "keeps_advancing": (f_min1 > f_min0),
            }

        return 0 if (report["phase1_silent_launch"].get("ok") and sp_entered) else 1
    finally:
        stop_watch.set()
        if watch_thread:
            watch_thread.join(timeout=1.5)
        report["focus_watcher"] = watch_stats
        if proc:
            try:
                B.kernel32.CloseHandle(proc)
            except Exception:
                pass
        report["cleanup"] = _cleanup()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
