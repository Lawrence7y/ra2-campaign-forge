#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_secondary_bg.py — 副屏 + 后台无感真机（ra2bench/gamemd.exe）实测验证。

用法:
  python tools/test_secondary_bg.py                 # 全量实测（启动 -> 导航进遭遇战 -> 真后台失焦采样 -> 最小化对比 -> 清理）
  python tools/test_secondary_bg.py --quick-launch  # 仅校验副屏启动、坐标定位、不干扰主屏、截图与清理
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

# 必须在导入 bench_replay 前初始化 Per-Monitor DPI Awareness，防止与 SetProcessDPIAware 冲突
import win_display_helper as WDH  # noqa: E402

_INITIAL_MONITORS = WDH.list_monitors()

os.environ["RA2_SCREEN_MODE"] = "secondary"
os.environ["RA2_MUTE_AUDIO"] = "1"
os.environ["RA2_NO_MINIMIZE_PRIMARY"] = "1"
os.environ["RA2_RESTORE_CURSOR"] = "1"

import bench_replay as B  # noqa: E402

B.GAME_DIR = B.PROJECT / "ra2bench"
OUT_DIR = B.SHOTS / "secondary_test"
SW_MINIMIZE = 6


def _get_win_title(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    B.user32.GetWindowTextW(wt.HWND(hwnd), buf, 256)
    return buf.value


def _get_win_rect(hwnd: int) -> list[int]:
    r = wt.RECT()
    B.user32.GetWindowRect(wt.HWND(hwnd), ctypes.byref(r))
    return [r.left, r.top, r.right, r.bottom]


def _get_desktop_name() -> str:
    try:
        hdesk = B.user32.GetThreadDesktop(B.kernel32.GetCurrentThreadId())
        if not hdesk:
            return "unknown"
        buf = ctypes.create_unicode_buffer(128)
        needed = ctypes.c_ulong(0)
        ok = B.user32.GetUserObjectInformationW(hdesk, 2, buf, ctypes.sizeof(buf), ctypes.byref(needed))
        return buf.value if ok and buf.value else "unknown"
    except Exception:
        return "unknown"


def _get_cursor_pos() -> tuple[int, int] | None:
    pt = wt.POINT()
    if B.user32.GetCursorPos(ctypes.byref(pt)):
        return int(pt.x), int(pt.y)
    return None


def _list_primary_visible_windows(prim_bounds: list[int], exclude_hwnd: int | None = None) -> list[dict]:
    px0, py0, px1, py1 = prim_bounds
    wins: list[dict] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _cb(h, _):
        if exclude_hwnd and int(h) == int(exclude_hwnd):
            return True
        if not B.user32.IsWindowVisible(h) or B.user32.IsIconic(h):
            return True
        cls_buf = ctypes.create_unicode_buffer(256)
        B.user32.GetClassNameW(h, cls_buf, 256)
        if cls_buf.value in ("Shell_TrayWnd", "Progman", "WorkerW", "Windows.UI.Core.CoreWindow"):
            return True
        rect = _get_win_rect(h)
        w, ht = rect[2] - rect[0], rect[3] - rect[1]
        if w < 50 or ht < 50:
            return True
        cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        if px0 <= cx < px1 and py0 <= cy < py1:
            wins.append({"hwnd": int(h), "title": _get_win_title(h), "rect": rect})
        return True

    B.user32.EnumWindows(_cb, 0)
    return wins


def _restore_foreground(target_hwnd: int | None, prim_bounds: list[int], game_hwnd: int) -> dict:
    """将系统前台焦点切回主屏窗口或桌面，绝不激活 game_hwnd。"""
    candidates: list[int] = []
    if target_hwnd and B.user32.IsWindow(target_hwnd) and int(target_hwnd) != int(game_hwnd):
        candidates.append(int(target_hwnd))
    for w in _list_primary_visible_windows(prim_bounds, exclude_hwnd=game_hwnd):
        if w["hwnd"] not in candidates:
            candidates.append(w["hwnd"])
    shell_hw = B.user32.GetShellWindow()
    if shell_hw:
        candidates.append(int(shell_hw))

    cur_tid = B.kernel32.GetCurrentThreadId()
    for cand in candidates:
        tgt_tid = B.user32.GetWindowThreadProcessId(wt.HWND(cand), None)
        B.user32.AttachThreadInput(cur_tid, tgt_tid, True)
        B.user32.BringWindowToTop(wt.HWND(cand))
        B.user32.SetForegroundWindow(wt.HWND(cand))
        B.user32.AttachThreadInput(cur_tid, tgt_tid, False)
        time.sleep(0.15)
        fg = int(B.user32.GetForegroundWindow())
        if fg and fg != int(game_hwnd):
            return {"ok": True, "fg_hwnd": fg, "fg_title": _get_win_title(fg)}

    # Alt-key bypass fallback targeting shell/primary candidate
    if candidates:
        cand = candidates[0]
        B.user32.keybd_event(0x12, 0, 0, 0)
        B.user32.keybd_event(0x12, 0, 2, 0)
        B.user32.SetForegroundWindow(wt.HWND(cand))
        time.sleep(0.2)
    fg = int(B.user32.GetForegroundWindow())
    return {"ok": fg != int(game_hwnd), "fg_hwnd": fg, "fg_title": _get_win_title(fg)}


def _bbox_in_bounds(bbox: tuple[int, int, int, int] | list[int], bounds: list[int]) -> bool:
    l, t, r, b = bbox
    bx0, by0, bx1, by1 = bounds
    return l >= bx0 and t >= by0 and r <= bx1 and b <= by1 and r > l and b > t


_MENU_BUTTONS_NO_RADAR = {
    "mainmenu": [[220, 262, 304, 346, 388, 556], [220, 262, 304, 556]],
    "sp_submenu": [[220, 262, 304, 556], [220, 262, 556]],
    "skirmish_setup": [[220, 262, 556], [262, 304, 556]],
    "map_browser": [[178, 556], [178, 220, 556]],
}


def _match_buttons(got: list[int], want: list[int], tol: int = 4) -> bool:
    return len(got) == len(want) and all(abs(g - w) <= tol for g, w in zip(got, want))


def _banner_crop_arr(hwnd: int):
    """截取右上角纯标题文字区 (670,4,780,30)，避开 y>=37 的雷达动态动画。"""
    import numpy as np
    from PIL import Image
    l, t, r, b = B.window_bbox(hwnd)
    x0 = l + int(670 / 800 * (r - l))
    x1 = l + int(780 / 800 * (r - l))
    y0 = t + int(4 / 600 * (b - t))
    y1 = t + int(30 / 600 * (b - t))
    res = B.grab_region(hwnd, x0, y0, max(4, x1 - x0), max(4, y1 - y0))
    if not res or not res.get("path"):
        return None
    return np.asarray(Image.open(res["path"]).convert("RGB")).astype(float)


def _banner_mad(arr_a, arr_b) -> float:
    import numpy as np
    if arr_a is None or arr_b is None or arr_a.shape != arr_b.shape:
        return 999.0
    return float(np.abs(arr_a - arr_b).mean())


def _verify_menu_buttons(hwnd: int, expect: str, tol: int = 4) -> dict:
    """仅比对菜单区(y>=150)红钮；skirmish_setup 额外要求无顶部雷达红条(y<150)。"""
    rb_all = B.sidebar_red_buttons(hwnd)
    got = [y for y in rb_all if y >= 150]
    variants = _MENU_BUTTONS_NO_RADAR[expect]
    matched_want = None
    for want in variants:
        if _match_buttons(got, want, tol=tol):
            matched_want = want
            break
    ok = matched_want is not None
    extra_ok = True
    if expect == "skirmish_setup" and any(y < 150 for y in rb_all):
        ok = False
        extra_ok = False
    return {
        "ok": bool(ok),
        "expect": expect,
        "got_buttons": got,
        "got_all": rb_all,
        "matched_want": matched_want,
        "want_variants": variants,
        "no_top_radar_ok": extra_ok,
        "reason": f"menu_buttons got={got} got_all={rb_all} want={variants} tol=±{tol}",
    }


def _click_with_verify(
    hwnd: int,
    lx: int,
    ly: int,
    expect_screen: str,
    *,
    retries: int = 3,
    wait: float = 3.5,
    shot_prefix: str = "nav",
) -> dict:
    """导航点击并校验标题横幅切换 + 菜单按钮指纹，每次尝试均落盘截图。"""
    attempts = []
    before_buttons = [y for y in B.sidebar_red_buttons(hwnd) if y >= 150]
    before_banner = _banner_crop_arr(hwnd)
    for i in range(retries):
        c_before = _get_cursor_pos()
        B.focus_game(hwnd)
        B.send_click(hwnd, lx, ly, lw=800, lh=600)
        c_after = _get_cursor_pos()
        restored = False
        delta = None
        if c_before and c_after:
            dx = abs(c_after[0] - c_before[0])
            dy = abs(c_after[1] - c_before[1])
            delta = [dx, dy]
            restored = (dx <= 2 and dy <= 2)
        time.sleep(wait)
        attempt_shot = B.grab(hwnd, OUT_DIR / f"{shot_prefix}_a{i + 1}.png")
        v = _verify_menu_buttons(hwnd, expect_screen)
        after_banner = _banner_crop_arr(hwnd)
        mad = round(_banner_mad(before_banner, after_banner), 2)
        banner_changed = mad > 5.0
        attempts.append({
            "attempt": i + 1,
            "cursor_before": list(c_before) if c_before else None,
            "cursor_after": list(c_after) if c_after else None,
            "cursor_delta": delta,
            "cursor_restored": restored,
            "banner_mad": mad,
            "banner_changed": banner_changed,
            "shot": attempt_shot,
            "verify": v,
        })
        if v["ok"] and banner_changed:
            return {"ok": True, "attempts": attempts, "verify": v, "cursor_restored_all": all(a["cursor_restored"] for a in attempts)}
        # 若标题区已明确切换或按钮指纹已变，停止重点击以免连跳进下一级菜单
        if banner_changed or v["got_buttons"] != before_buttons:
            break
        time.sleep(1.0)
    return {"ok": False, "attempts": attempts, "verify": attempts[-1]["verify"] if attempts else None, "cursor_restored_all": all(a["cursor_restored"] for a in attempts)}


def _cleanup_processes() -> dict:
    B.set_esc_locked(False)
    B.kill_game()
    subprocess.run(["taskkill", "/IM", "ra2loader.exe", "/F"], capture_output=True)
    time.sleep(0.5)
    rem_gamemd = B.find_pid("gamemd.exe")
    rem_loader = B.find_pid("ra2loader.exe")
    return {"gamemd_pid": rem_gamemd, "ra2loader_pid": rem_loader, "clean": (rem_gamemd is None and rem_loader is None)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="副屏 + 后台无感真机实测")
    ap.add_argument("--quick-launch", action="store_true", help="仅做副屏启动、坐标验证、截图与清理")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUT_DIR / "report.json"

    prim_mon = WDH.get_target_monitor("primary")
    sec_mon = WDH.get_target_monitor("secondary")
    if not prim_mon or not sec_mon:
        print(json.dumps({"ok": False, "error": "need both primary and secondary monitors", "monitors": _INITIAL_MONITORS}, ensure_ascii=False))
        return 2

    desktop_name = _get_desktop_name()
    prev_fg_hw = int(B.user32.GetForegroundWindow())
    preflight_wins = _list_primary_visible_windows(prim_mon["bounds"])
    preflight = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "desktop": desktop_name,
        "game_dir": str(B.GAME_DIR),
        "monitors": _INITIAL_MONITORS,
        "primary_bounds": prim_mon["bounds"],
        "secondary_bounds": sec_mon["bounds"],
        "prev_fg": {
            "hwnd": prev_fg_hw,
            "title": _get_win_title(prev_fg_hw),
            "rect": _get_win_rect(prev_fg_hw) if prev_fg_hw else None,
        },
        "primary_visible_windows_count": len(preflight_wins),
        "primary_visible_windows_sample": preflight_wins[:8],
        "cursor_initial": list(_get_cursor_pos() or ()),
    }

    report: dict = {
        "mode": "quick_launch" if args.quick_launch else "full",
        "preflight": preflight,
        "phase1_launch": {},
        "phase2_nav": {},
        "phase3_background": {},
        "phase3b_minimized": {},
        "cleanup": {},
    }
    proc = None
    try:
        if desktop_name.lower() != "default":
            report["phase1_launch"] = {
                "ok": False,
                "error": f"running in non-interactive desktop '{desktop_name}'; must run from interactive WinSta0\\Default session (e.g. via win-main started by start_win_worker.ps1)",
            }
            return 1

        B.kill_game()
        subprocess.run(["taskkill", "/IM", "ra2loader.exe", "/F"], capture_output=True)
        time.sleep(0.5)

        t_launch0 = time.time()
        pid = B.launch()
        WDH.start_mute_watcher(pid, mute=True)
        hwnd = None
        t_hw_end = time.time() + 20.0
        while time.time() < t_hw_end and not hwnd:
            hwnd = B.find_game_hwnd(pid)
            if not hwnd:
                time.sleep(0.4)
        if not hwnd:
            report["phase1_launch"] = {"ok": False, "pid": pid, "error": "hwnd not found within 20s"}
            return 1

        bbox_initial = list(B.window_bbox(hwnd))
        # 若窗口还未在副屏，强制放置（不抢焦点）
        if not _bbox_in_bounds(bbox_initial, sec_mon["bounds"]):
            WDH.place_hwnd_on_secondary(hwnd, no_activate=True)
            time.sleep(0.3)
            bbox_initial = list(B.window_bbox(hwnd))

        # 等待主菜单（先给足启动时间，满 18s 未出现全部 6 枚主菜单钮则补按两次 ESC 跳过片头并待滑出动画完成）
        mainmenu_ok = False
        esc_sent = False
        last_verify = None
        t_mm_start = time.time()
        while time.time() - t_mm_start < 40.0:
            v = _verify_menu_buttons(hwnd, "mainmenu")
            last_verify = v
            if v["ok"]:
                mainmenu_ok = True
                time.sleep(2.0)
                break
            elapsed = time.time() - t_mm_start
            if elapsed >= 18.0 and not esc_sent:
                esc_sent = True
                B.focus_game(hwnd)
                B.press_key(0x1B)
                time.sleep(1.2)
                B.press_key(0x1B)
                time.sleep(3.5)
                _restore_foreground(prev_fg_hw, prim_mon["bounds"], hwnd)
                continue
            time.sleep(2.0)

        # 确认主菜单阶段焦点归还或测量主屏窗口数
        bbox_mainmenu = list(B.window_bbox(hwnd))
        in_secondary = _bbox_in_bounds(bbox_mainmenu, sec_mon["bounds"])
        after_wins = _list_primary_visible_windows(prim_mon["bounds"], exclude_hwnd=hwnd)
        prev_hwnds = {w["hwnd"] for w in preflight_wins}
        after_hwnds = {w["hwnd"] for w in after_wins}
        minimized_from_preflight = [w for w in preflight_wins if w["hwnd"] not in after_hwnds]

        shot1 = B.grab(hwnd, OUT_DIR / "01_mainmenu.png")
        mute_phase1 = WDH.get_pid_mute_state(pid)
        if not mute_phase1.get("muted"):
            WDH.mute_pid_audio(pid, mute=True)
            mute_phase1 = WDH.get_pid_mute_state(pid)
        report["phase1_launch"] = {
            "ok": bool(in_secondary and shot1.get("plausible") and len(minimized_from_preflight) == 0),
            "pid": pid,
            "hwnd": int(hwnd),
            "launch_elapsed_s": round(time.time() - t_launch0, 2),
            "bbox_initial": bbox_initial,
            "bbox_mainmenu": bbox_mainmenu,
            "in_secondary_bounds": in_secondary,
            "mainmenu_verified": mainmenu_ok,
            "esc_sent_to_skip_intro": esc_sent,
            "verify_mainmenu": last_verify,
            "audio_mute_state": mute_phase1,
            "primary_windows_before": len(preflight_wins),
            "primary_windows_after": len(after_wins),
            "primary_windows_lost": minimized_from_preflight,
            "shot_01_mainmenu": shot1,
        }

        if args.quick_launch:
            return 0 if report["phase1_launch"]["ok"] else 1

        # Phase 2: 副屏导航进遭遇战（先聚焦留图 01b_mainmenu_focused.png，确认菜单钮稳定）
        B.focus_game(hwnd)
        time.sleep(1.5)
        shot1b = B.grab(hwnd, OUT_DIR / "01b_mainmenu_focused.png")

        step_sp = _click_with_verify(hwnd, 700, 218, "sp_submenu", retries=3, wait=3.5, shot_prefix="nav_sp")
        shot2 = B.grab(hwnd, OUT_DIR / "02_sp_submenu.png")

        matched_sp = (step_sp.get("verify") or {}).get("matched_want") or []
        skirmish_y = 262 if len(matched_sp) == 3 else 304
        step_skirmish = (
            _click_with_verify(hwnd, 700, skirmish_y, "skirmish_setup", retries=3, wait=8.5, shot_prefix="nav_sk")
            if step_sp["ok"]
            else {"ok": False, "skipped": True}
        )
        shot3 = B.grab(hwnd, OUT_DIR / "03_skirmish_setup.png")

        proc = B.open_proc(pid)
        mon = B.BattleMonitor(proc)
        map_select = {"attempted": False}
        step_start = {"ok": False}
        battle_ready = False
        shot3b = None
        shot3c = None
        if step_skirmish["ok"]:
            sk_buttons = (step_skirmish.get("verify") or {}).get("got_buttons") or [220, 262, 556]
            custom_y = sk_buttons[1] if len(sk_buttons) >= 2 else 262
            B.focus_game(hwnd)
            B.send_click(hwnd, 700, custom_y, lw=800, lh=600)
            time.sleep(2.5)
            shot3b = B.grab(hwnd, OUT_DIR / "03b_map_browser.png")
            mb_check = _verify_menu_buttons(hwnd, "map_browser")
            map_select = {"attempted": True, "custom_btn_y": custom_y, "map_browser_ok": mb_check["ok"], "mb_check": mb_check}
            if mb_check["ok"]:
                B.focus_game(hwnd)
                B.send_click(hwnd, 260, 113, lw=800, lh=600)
                time.sleep(0.8)
                B.send_click(hwnd, 720, 178, lw=800, lh=600)
                time.sleep(2.5)
                shot3c = B.grab(hwnd, OUT_DIR / "03c_skirmish_after_map.png")
                map_select["returned_skirmish"] = _verify_menu_buttons(hwnd, "skirmish_setup")

            cur_btns = [y for y in B.sidebar_red_buttons(hwnd) if y >= 150]
            start_y = cur_btns[0] if cur_btns else 220
            c_before = _get_cursor_pos()
            B.focus_game(hwnd)
            B.set_esc_locked(True)
            B.send_click(hwnd, 700, start_y, lw=800, lh=600)
            c_after = _get_cursor_pos()
            dx = abs(c_after[0] - c_before[0]) if (c_before and c_after) else None
            dy = abs(c_after[1] - c_before[1]) if (c_before and c_after) else None
            step_start = {
                "clicked": True,
                "start_btn_y": start_y,
                "cur_btns_before_start": cur_btns,
                "cursor_delta": [dx, dy] if dx is not None else None,
                "cursor_restored": (dx is not None and dx <= 2 and dy <= 2),
            }
            battle_ready = B.wait_battle_ready(mon, hwnd, timeout=60.0, min_fps=3.0)
            step_start["ok"] = battle_ready

        units_fg = mon.mobile_counts()
        frame_fg = mon.frame()
        shot4 = B.grab(hwnd, OUT_DIR / "04_battle_fg.png")

        report["phase2_nav"] = {
            "ok": bool(step_sp["ok"] and step_skirmish["ok"] and battle_ready),
            "shot_01b_mainmenu_focused": shot1b,
            "step_sp_submenu": step_sp,
            "skirmish_btn_y": skirmish_y,
            "shot_02_sp_submenu": shot2,
            "step_skirmish_setup": step_skirmish,
            "shot_03_skirmish_setup": shot3,
            "map_select": map_select,
            "shot_03b_map_browser": shot3b,
            "shot_03c_skirmish_after_map": shot3c,
            "step_start_game": step_start,
            "battle_ready": battle_ready,
            "frame_after_entry": frame_fg,
            "units_after_entry": units_fg,
            "shot_04_battle_fg": shot4,
        }

        if not battle_ready:
            return 1

        # Phase 3: 真后台（将前台焦点切回主屏，副屏无焦点持续运行）
        fg_restore = _restore_foreground(prev_fg_hw, prim_mon["bounds"], hwnd)
        time.sleep(0.5)
        fg_before_bg = int(B.user32.GetForegroundWindow())
        frame_bg0 = mon.frame()
        units_bg0 = mon.mobile_counts()
        t_bg0 = time.perf_counter()

        sample_ok = True
        sample_error = None
        try:
            sw_res = B.sample_window(pid, proc, seconds=5.0, hz=100.0, require_match=True)
        except Exception as exc:
            sample_ok = False
            sample_error = str(exc)
            sw_res = B.sample_window(pid, proc, seconds=5.0, hz=100.0, require_match=False)

        # 补足至至少 6s 观测窗
        elapsed_bg = time.perf_counter() - t_bg0
        if elapsed_bg < 6.0:
            time.sleep(6.0 - elapsed_bg)
        elapsed_bg = time.perf_counter() - t_bg0
        frame_bg1 = mon.frame()
        units_bg1 = mon.mobile_counts()

        # 不抢焦点直接抓取副屏游戏窗口截图
        shot5 = B.grab(hwnd, OUT_DIR / "05_battle_bg_unfocused.png")
        fg_after_bg = int(B.user32.GetForegroundWindow())
        bbox_bg = list(B.window_bbox(hwnd))
        mute_phase3 = WDH.get_pid_mute_state(pid)

        report["phase3_background"] = {
            "ok": bool(
                fg_before_bg != int(hwnd)
                and fg_after_bg != int(hwnd)
                and sample_ok
                and (frame_bg1 > frame_bg0)
                and (shot5.get("md5") != shot4.get("md5"))
            ),
            "audio_mute_state": mute_phase3,
            "foreground_restore": fg_restore,
            "fg_before_bg": fg_before_bg,
            "fg_after_bg": fg_after_bg,
            "fg_stayed_off_game": (fg_before_bg != int(hwnd) and fg_after_bg != int(hwnd)),
            "bbox_during_bg": bbox_bg,
            "frame_bg0": frame_bg0,
            "frame_bg1": frame_bg1,
            "delta_frames": frame_bg1 - frame_bg0,
            "elapsed_s": round(elapsed_bg, 2),
            "avg_fps_over_bg": round((frame_bg1 - frame_bg0) / max(elapsed_bg, 0.1), 2),
            "units_bg0": units_bg0,
            "units_bg1": units_bg1,
            "sample_require_match_ok": sample_ok,
            "sample_error": sample_error,
            "sample_window": sw_res,
            "shot_05_battle_bg_unfocused": shot5,
            "shot_md5_changed_vs_fg": shot5.get("md5") != shot4.get("md5"),
        }

        # Phase 3b: 最小化隐藏对比（3 秒探针）
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
            "elapsed_s": round(dt_m, 2),
            "minimized_fps": round((f_min1 - f_min0) / max(dt_m, 0.1), 2),
            "keeps_advancing": (f_min1 > f_min0),
        }

        return 0 if report["phase3_background"]["ok"] else 1
    finally:
        if proc:
            try:
                B.kernel32.CloseHandle(proc)
            except Exception:
                pass
        report["cleanup"] = _cleanup_processes()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
