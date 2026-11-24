#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""win_display_helper.py — Windows 多屏定位与副屏/后台无感真机辅助工具。

功能：
  1. 枚举所有显示器，区分主屏 (MONITORINFOF_PRIMARY) 与副屏（如 \\.\\DISPLAY1）。
  2. 将 ra2bench/ddraw.ini 配置为无边框窗口模式，posX/posY 落在副屏内，devmode=true。
  3. 用 SetWindowPos 将运行中的 gamemd.exe 窗口移动到副屏（可选不抢主屏焦点）。

CLI 用法：
  python tools/win_display_helper.py --status
  python tools/win_display_helper.py --configure-ddraw [--game-dir ra2bench]
  python tools/win_display_helper.py --move-running
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MONITORINFOF_PRIMARY = 1
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


class _RECT(ctypes.Structure):
    _fields_ = [("left", wt.LONG), ("top", wt.LONG), ("right", wt.LONG), ("bottom", wt.LONG)]


class _MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wt.DWORD),
        ("rcMonitor", _RECT),
        ("rcWork", _RECT),
        ("dwFlags", wt.DWORD),
        ("szDevice", wt.WCHAR * 32),
    ]


def list_monitors() -> list[dict]:
    """枚举当前所有显示器（仅 Windows 有效，非 Windows 返回空列表）。"""
    if sys.platform != "win32":
        return []
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass

    monitors: list[dict] = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ctypes.POINTER(_RECT), wt.LPARAM)
    def _cb(hmon, _hdc, _lprc, _lparam):
        mi = _MONITORINFOEXW()
        mi.cbSize = ctypes.sizeof(_MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            r = mi.rcMonitor
            w = mi.rcWork
            monitors.append(
                {
                    "device": mi.szDevice,
                    "primary": bool(mi.dwFlags & MONITORINFOF_PRIMARY),
                    "bounds": [r.left, r.top, r.right, r.bottom],
                    "work": [w.left, w.top, w.right, w.bottom],
                    "width": r.right - r.left,
                    "height": r.bottom - r.top,
                }
            )
        return True

    user32.EnumDisplayMonitors(None, None, _cb, 0)
    return monitors


def get_target_monitor(prefer: str = "secondary") -> dict | None:
    """获取目标显示器；prefer='secondary' 时优先返回非主屏，否则回退主屏。"""
    mons = list_monitors()
    if not mons:
        return None
    if prefer == "secondary":
        sec = [m for m in mons if not m["primary"]]
        if sec:
            return sec[0]
    prim = [m for m in mons if m["primary"]]
    return prim[0] if prim else mons[0]


def _set_ddraw_section_kvs(lines: list[str], kvs: list[tuple[str, str]]) -> list[str]:
    """Only update keys inside the [ddraw] section, leaving all game-specific sections intact."""
    out: list[str] = []
    in_ddraw = False
    saw_ddraw = False
    pending = dict(kvs)
    key_pats = {k.lower(): re.compile(rf"^\s*{re.escape(k)}\s*=", re.IGNORECASE) for k, _ in kvs}

    def flush_pending():
        for k, v in kvs:
            if k in pending:
                out.append(f"{k}={pending.pop(k)}")

    for ln in lines:
        sec_m = re.match(r"^\s*\[([^\]]+)\]\s*$", ln)
        if sec_m:
            if in_ddraw:
                flush_pending()
            sec_name = sec_m.group(1).strip().lower()
            in_ddraw = (sec_name == "ddraw")
            if in_ddraw:
                saw_ddraw = True
            out.append(ln)
            continue

        if in_ddraw:
            matched_key = None
            for k, _ in kvs:
                if key_pats[k.lower()].match(ln):
                    matched_key = k
                    break
            if matched_key is not None:
                if matched_key in pending:
                    out.append(f"{matched_key}={pending.pop(matched_key)}")
                continue
        out.append(ln)

    if in_ddraw:
        flush_pending()
    elif not saw_ddraw:
        out.append("[ddraw]")
        flush_pending()
    return out


def configure_ddraw_for_screen(game_dir: Path | str, mode: str = "secondary") -> dict:
    """配置 ddraw.ini 在副屏无边框窗口运行且不锁死鼠标（修改前自动留 .bak_display 备份）。"""
    gd = Path(game_dir)
    ini_path = gd / "ddraw.ini"
    mon = get_target_monitor("secondary" if mode in ("secondary", "background") else "primary")
    if mon is None:
        return {"ok": False, "error": "no monitor detected"}
    wx0, wy0, wx1, wy1 = mon["work"]
    # 留出少量内边距，避免窗口贴边被裁剪
    pos_x = wx0 + 60
    pos_y = wy0 + 60

    if ini_path.exists():
        bak = gd / "ddraw.ini.bak_display"
        if not bak.exists():
            shutil.copy2(ini_path, bak)
        raw = ini_path.read_text(encoding="utf-8", errors="replace")
    else:
        raw = "[ddraw]\n"

    lines = _set_ddraw_section_kvs(
        raw.splitlines(),
        [
            ("windowed", "true"),
            ("fullscreen", "false"),
            ("border", "false"),
            ("devmode", "true"),
            ("savesettings", "0"),
            ("posX", str(pos_x)),
            ("posY", str(pos_y)),
        ],
    )
    ini_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "monitor": mon, "posX": pos_x, "posY": pos_y, "ini": str(ini_path)}


def place_hwnd_on_secondary(hwnd: int, width: int = 800, height: int = 600, no_activate: bool = False) -> dict:
    """将指定 hwnd 移到副屏工作区。"""
    if sys.platform != "win32":
        return {"ok": False, "error": "not win32"}
    mon = get_target_monitor("secondary")
    if not mon:
        return {"ok": False, "error": "no monitor"}
    wx0, wy0, wx1, wy1 = mon["work"]
    x = wx0 + 60
    y = wy0 + 60
    flags = SWP_NOZORDER | SWP_NOSIZE
    if no_activate:
        flags |= SWP_NOACTIVATE
    ok = bool(ctypes.windll.user32.SetWindowPos(wt.HWND(hwnd), None, x, y, width, height, flags))
    return {"ok": ok, "x": x, "y": y, "device": mon["device"], "primary": mon["primary"]}


def find_gamemd_hwnds() -> list[int]:
    if sys.platform != "win32":
        return []
    user32 = ctypes.windll.user32
    res: list[int] = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def _cb(hwnd, _lp):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        if "Yuri" in buf.value or "Red Alert" in buf.value:
            res.append(hwnd)
        return True

    user32.EnumWindows(_cb, 0)
    return res


def _is_pid_alive(pid: int) -> bool:
    if sys.platform != "win32" or pid <= 0:
        return False
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return False
    try:
        code = wt.DWORD(0)
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
            return False
        return int(code.value) == STILL_ACTIVE
    finally:
        k32.CloseHandle(h)


def _with_wasapi_sessions(fn):
    """枚举默认播放设备 (eRender, eMultimedia) 上的全部 WASAPI 音频会话并执行回调。"""
    if sys.platform != "win32":
        return {"ok": False, "error": "not win32"}
    try:
        from ctypes import POINTER, byref, c_float, c_int, c_ulong, c_void_p, HRESULT
        import comtypes
        from comtypes import COMMETHOD, GUID, IUnknown
    except Exception as exc:
        return {"ok": False, "error": f"comtypes unavailable: {exc}"}

    CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
    IID_IMMDeviceEnumerator = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
    IID_IAudioSessionManager2 = GUID("{77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F}")
    IID_IAudioSessionControl2 = GUID("{bfb7ff88-7239-4fc9-8fa2-07c950be9c6d}")
    IID_ISimpleAudioVolume = GUID("{87CE5498-68D6-44E5-9215-6DA47EF883D8}")

    class ISimpleAudioVolume(IUnknown):
        _iid_ = IID_ISimpleAudioVolume
        _methods_ = [
            COMMETHOD([], HRESULT, "SetMasterVolume", (["in"], c_float, "fLevel"), (["in"], POINTER(GUID), "EventContext")),
            COMMETHOD([], HRESULT, "GetMasterVolume", (["out"], POINTER(c_float), "pfLevel")),
            COMMETHOD([], HRESULT, "SetMute", (["in"], c_int, "bMute"), (["in"], POINTER(GUID), "EventContext")),
            COMMETHOD([], HRESULT, "GetMute", (["out"], POINTER(c_int), "pbMute")),
        ]

    class IAudioSessionControl(IUnknown):
        _iid_ = GUID("{F4B1A599-7266-4319-A8CA-E70ACB11E8CD}")
        _methods_ = [
            COMMETHOD([], HRESULT, "GetState", (["out"], POINTER(c_int), "pRetVal")),
            COMMETHOD([], HRESULT, "GetDisplayName", (["out"], POINTER(ctypes.c_wchar_p), "pRetVal")),
            COMMETHOD([], HRESULT, "SetDisplayName", (["in"], ctypes.c_wchar_p, "Value"), (["in"], POINTER(GUID), "EventContext")),
            COMMETHOD([], HRESULT, "GetIconPath", (["out"], POINTER(ctypes.c_wchar_p), "pRetVal")),
            COMMETHOD([], HRESULT, "SetIconPath", (["in"], ctypes.c_wchar_p, "Value"), (["in"], POINTER(GUID), "EventContext")),
            COMMETHOD([], HRESULT, "GetGroupingParam", (["out"], POINTER(GUID), "pRetVal")),
            COMMETHOD([], HRESULT, "SetGroupingParam", (["in"], POINTER(GUID), "Override"), (["in"], POINTER(GUID), "EventContext")),
            COMMETHOD([], HRESULT, "RegisterAudioSessionNotification", (["in"], c_void_p, "NewNotifications")),
            COMMETHOD([], HRESULT, "UnregisterAudioSessionNotification", (["in"], c_void_p, "NewNotifications")),
        ]

    class IAudioSessionControl2(IAudioSessionControl):
        _iid_ = IID_IAudioSessionControl2
        _methods_ = [
            COMMETHOD([], HRESULT, "GetSessionIdentifier", (["out"], POINTER(ctypes.c_wchar_p), "pRetVal")),
            COMMETHOD([], HRESULT, "GetSessionInstanceIdentifier", (["out"], POINTER(ctypes.c_wchar_p), "pRetVal")),
            COMMETHOD([], HRESULT, "GetProcessId", (["out"], POINTER(c_ulong), "pRetVal")),
            COMMETHOD([], HRESULT, "IsSystemSoundsSession"),
            COMMETHOD([], HRESULT, "SetDuckingPreference", (["in"], c_int, "optOut")),
        ]

    class IAudioSessionEnumerator(IUnknown):
        _iid_ = GUID("{E2F5BB11-0570-40CA-ACDD-3AA01277DEE8}")
        _methods_ = [
            COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(c_int), "SessionCount")),
            COMMETHOD([], HRESULT, "GetSession", (["in"], c_int, "SessionCount"), (["out"], POINTER(POINTER(IAudioSessionControl)), "Session")),
        ]

    class IAudioSessionManager2(IUnknown):
        _iid_ = IID_IAudioSessionManager2
        _methods_ = [
            COMMETHOD([], HRESULT, "GetAudioSessionControl", (["in"], POINTER(GUID), "AudioSessionGuid"), (["in"], c_ulong, "StreamFlags"), (["out"], POINTER(c_void_p), "SessionControl")),
            COMMETHOD([], HRESULT, "GetSimpleAudioVolume", (["in"], POINTER(GUID), "AudioSessionGuid"), (["in"], c_ulong, "StreamFlags"), (["out"], POINTER(c_void_p), "AudioVolume")),
            COMMETHOD([], HRESULT, "GetSessionEnumerator", (["out"], POINTER(POINTER(IAudioSessionEnumerator)), "SessionEnum")),
        ]

    class IMMDevice(IUnknown):
        _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
        _methods_ = [
            COMMETHOD([], HRESULT, "Activate", (["in"], POINTER(GUID), "iid"), (["in"], c_ulong, "dwClsCtx"), (["in"], c_void_p, "pActivationParams"), (["out"], POINTER(c_void_p), "ppInterface")),
        ]

    class IMMDeviceEnumerator(IUnknown):
        _iid_ = IID_IMMDeviceEnumerator
        _methods_ = [
            COMMETHOD([], HRESULT, "EnumAudioEndpoints", (["in"], c_int, "dataFlow"), (["in"], c_ulong, "dwStateMask"), (["out"], POINTER(c_void_p), "ppDevices")),
            COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint", (["in"], c_int, "dataFlow"), (["in"], c_int, "role"), (["out"], POINTER(POINTER(IMMDevice)), "ppEndpoint")),
        ]

    comtypes.CoInitialize()
    try:
        enum = comtypes.CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator)
        dev = enum.GetDefaultAudioEndpoint(0, 1)
        p = dev.Activate(byref(IID_IAudioSessionManager2), comtypes.CLSCTX_ALL, None)
        mgr = ctypes.cast(p, POINTER(IAudioSessionManager2))
        se = mgr.GetSessionEnumerator()
        cnt = int(se.GetCount())
        items = []
        for i in range(cnt):
            ctrl = se.GetSession(i)
            c2 = ctrl.QueryInterface(IAudioSessionControl2)
            vol = ctrl.QueryInterface(ISimpleAudioVolume)
            items.append((int(c2.GetProcessId()), vol))
        return fn(items, cnt)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        comtypes.CoUninitialize()


def mute_pid_audio(pid: int, mute: bool = True) -> dict:
    """按进程 PID 通过 WASAPI 仅静音指定进程的音频会话（不改主屏系统音量与游戏 INI）。"""
    target_pid = int(pid)

    def _op(items, cnt):
        matched = 0
        for spid, vol in items:
            if spid == target_pid:
                vol.SetMute(1 if mute else 0, None)
                matched += 1
        return {"ok": True, "pid": target_pid, "matched": matched, "muted": bool(mute), "session_count": cnt}

    return _with_wasapi_sessions(_op)


def get_pid_mute_state(pid: int) -> dict:
    """查询指定 PID 当前在 WASAPI 默认播放设备上的音频静音状态。"""
    target_pid = int(pid)

    def _op(items, cnt):
        states = [bool(vol.GetMute()) for spid, vol in items if spid == target_pid]
        return {
            "found": len(states) > 0,
            "muted": bool(states) and all(states),
            "matched": len(states),
            "session_count": cnt,
        }

    res = _with_wasapi_sessions(_op)
    if "found" not in res:
        return {"found": False, "muted": False, "matched": 0, "session_count": 0, "error": res.get("error")}
    return res


def start_mute_watcher(pid: int, mute: bool = True, duration_s: float = 45.0, interval_s: float = 0.25) -> threading.Thread:
    """后台守护线程：在目标进程注册 WASAPI 会话后立即静音并维持静音（进程退出即停止）。"""
    target_pid = int(pid)

    def _run():
        deadline = time.time() + max(1.0, float(duration_s))
        while time.time() < deadline:
            if not _is_pid_alive(target_pid):
                break
            res = mute_pid_audio(target_pid, mute=mute)
            sleep_s = 1.0 if (res.get("ok") and res.get("matched", 0) > 0) else interval_s
            time.sleep(sleep_s)

    th = threading.Thread(target=_run, name=f"ra2-mute-{target_pid}", daemon=True)
    th.start()
    return th


def _find_gamemd_pids() -> list[int]:
    if sys.platform != "win32":
        return []
    pids: set[int] = set()
    try:
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq gamemd.exe", "/FO", "CSV", "/NH"], text=True, errors="replace")
        for ln in out.splitlines():
            parts = [p.strip('" ') for p in ln.split(",")]
            if len(parts) >= 2 and parts[0].lower() == "gamemd.exe" and parts[1].isdigit():
                pids.add(int(parts[1]))
    except Exception:
        pass
    return sorted(pids)


def main():
    p = argparse.ArgumentParser(description="Windows display & secondary-screen helper for RA2")
    p.add_argument("--status", action="store_true", help="打印显示器枚举结果")
    p.add_argument("--configure-ddraw", action="store_true", help="将 ddraw.ini 配置到副屏")
    p.add_argument("--game-dir", default="", help="游戏目录，默认 <repo>/ra2bench")
    p.add_argument("--mode", default="secondary", choices=["secondary", "background", "primary"])
    p.add_argument("--move-running", action="store_true", help="移动运行中的 gamemd 窗口到副屏")
    p.add_argument("--mute-running", action="store_true", help="通过 WASAPI 静音运行中的 gamemd.exe（可配合 --pid）")
    p.add_argument("--unmute-running", action="store_true", help="取消静音运行中的 gamemd.exe（可配合 --pid）")
    p.add_argument("--pid", type=int, default=0, help="指定目标 PID（默认自动查找运行中的 gamemd.exe）")
    args = p.parse_args()

    out: dict = {}
    if args.status or (not args.configure_ddraw and not args.move_running and not args.mute_running and not args.unmute_running):
        mons = list_monitors()
        sec = get_target_monitor("secondary")
        out["monitors"] = mons
        out["target_secondary"] = sec

    if args.configure_ddraw:
        root = Path(__file__).resolve().parent.parent
        gdir = Path(args.game_dir) if args.game_dir else (root / "ra2bench")
        out["ddraw"] = configure_ddraw_for_screen(gdir, mode=args.mode)

    if args.move_running:
        hwnds = find_gamemd_hwnds()
        out["moved"] = [place_hwnd_on_secondary(h, no_activate=True) for h in hwnds]

    if args.mute_running or args.unmute_running:
        want_mute = bool(args.mute_running and not args.unmute_running)
        pids = [args.pid] if args.pid > 0 else _find_gamemd_pids()
        out["audio"] = [mute_pid_audio(pid, mute=want_mute) for pid in pids]

    import json
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
