#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""boot_session_fingerprint.py -- read-only boot-session environment fingerprint.

Purpose
-------
The same machine and the same gamemd.exe produced 31.24 fps in the 2026-10-19
boot session and 8.76-11.64 fps in the 2026-10-21 boot session. The variable
that separates the two groups is the *boot session*, not the GameViewer
private window (see lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md).
This script records the display / GPU / session / DWM / power / system
environment of the current boot session into one JSON document so that a
31-tier session and a 10-tier session can be diffed field by field.

Read-only contract
------------------
* No registry writes, no system setting changes, no process start/stop.
* The only file written is the JSON report in the current working directory.
* Every Win32 call goes through ctypes with explicit argtypes and restype.
* Every field is collected in its own try/except; failures go to "errors".

Requires CPython 3.12 on Windows. Standard library only (ctypes + stdlib).

Exit codes
----------
0  collected (all fields, or some fields failed but the reason is recorded)
1  fatal error inside the script itself
3  not running on Windows
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import locale
import os
import platform
import re
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

SCHEMA = "ra2cf.boot_fingerprint/1"

ENUM_CURRENT_SETTINGS = 0xFFFFFFFF

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_CMONITORS = 80
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
SM_REMOTESESSION = 0x1000

MONITORINFOF_PRIMARY = 0x00000001
MDT_EFFECTIVE_DPI = 0

TH32CS_SNAPPROCESS = 0x00000002

DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004

STATE_FLAG_NAMES = {
    0x00000001: "ATTACHED_TO_DESKTOP",
    0x00000002: "MULTI_DRIVER",
    0x00000004: "PRIMARY_DEVICE",
    0x00000008: "MIRRORING_DRIVER",
    0x00000010: "VGA_COMPATIBLE",
    0x00000020: "REMOVABLE",
    0x00000040: "ACC_DRIVER",
    0x00080000: "UNSAFE_MODES_ON",
    0x00200000: "TS_COMPATIBLE",
    0x01000000: "RDPUDD",
    0x02000000: "DISCONNECT",
    0x04000000: "REMOTE",
    0x08000000: "MODESPRUNED",
}

MAX_ADAPTERS = 32
MAX_MODES_SCANNED = 4096
MAX_MODES_RECORDED = 64

# ---------------------------------------------------------------------------
# ctypes aliases and structures
# ---------------------------------------------------------------------------

HANDLE = ctypes.c_void_p
HMONITOR = HANDLE
HDC = HANDLE
BOOL = ctypes.c_int
DWORD = ctypes.c_ulong
LPCWSTR = ctypes.c_wchar_p
LPARAM = ctypes.c_ssize_t
HRESULT = ctypes.c_long


class POINTL(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


class _DevmodePrinter(ctypes.Structure):
    _fields_ = [
        ("dmOrientation", ctypes.c_short),
        ("dmPaperSize", ctypes.c_short),
        ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short),
        ("dmScale", ctypes.c_short),
        ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short),
        ("dmPrintQuality", ctypes.c_short),
    ]


class _DevmodeDisplay(ctypes.Structure):
    _fields_ = [
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", DWORD),
        ("dmDisplayFixedOutput", DWORD),
    ]


class _DevmodeUnion(ctypes.Union):
    _fields_ = [
        ("printer", _DevmodePrinter),
        ("display", _DevmodeDisplay),
    ]


class DEVMODEW(ctypes.Structure):
    """Win32 DEVMODEW (ANSI-neutral layout, sizeof == 220 on x64/x86)."""

    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", DWORD),
        ("u1", _DevmodeUnion),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", DWORD),
        ("dmPelsWidth", DWORD),
        ("dmPelsHeight", DWORD),
        ("dmDisplayFlags", DWORD),
        ("dmDisplayFrequency", DWORD),
        ("dmICMMethod", DWORD),
        ("dmICMIntent", DWORD),
        ("dmMediaType", DWORD),
        ("dmDitherType", DWORD),
        ("dmReserved1", DWORD),
        ("dmReserved2", DWORD),
        ("dmPanningWidth", DWORD),
        ("dmPanningHeight", DWORD),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("cntUsage", DWORD),
        ("th32ProcessID", DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", DWORD),
        ("cntThreads", DWORD),
        ("th32ParentProcessID", DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


# ---------------------------------------------------------------------------
# Win32 loader: every call declared with argtypes and restype
# ---------------------------------------------------------------------------


class Win32Api(object):
    """Lazily loaded DLLs with fully declared signatures.

    Declaring argtypes/restype is mandatory here: without it ctypes truncates
    HMODULE/HANDLE values to c_int on 64-bit and raises "int too long".
    """

    def __init__(self):
        if not hasattr(ctypes, "WinDLL"):
            raise RuntimeError("ctypes.WinDLL unavailable (not a Windows Python build)")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self.dwmapi = None
        try:
            self.dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        except OSError:
            pass

        self.shcore = None
        try:
            self.shcore = ctypes.WinDLL("shcore", use_last_error=True)
        except OSError:
            pass

        self.MonitorEnumProc = ctypes.WINFUNCTYPE(
            BOOL, HMONITOR, HDC, ctypes.POINTER(RECT), LPARAM
        )
        self.invalid_handle_value = (1 << (8 * ctypes.sizeof(HANDLE))) - 1
        self._declare()

    def _declare(self):
        u = self.user32
        u.EnumDisplayMonitors.argtypes = [
            HMONITOR,
            HDC,
            self.MonitorEnumProc,
            LPARAM,
        ]
        u.EnumDisplayMonitors.restype = BOOL

        u.GetMonitorInfoW.argtypes = [HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
        u.GetMonitorInfoW.restype = BOOL

        u.EnumDisplaySettingsW.argtypes = [
            LPCWSTR,
            DWORD,
            ctypes.POINTER(DEVMODEW),
        ]
        u.EnumDisplaySettingsW.restype = BOOL

        u.EnumDisplayDevicesW.argtypes = [
            LPCWSTR,
            DWORD,
            ctypes.POINTER(DISPLAY_DEVICEW),
            DWORD,
        ]
        u.EnumDisplayDevicesW.restype = BOOL

        u.GetSystemMetrics.argtypes = [ctypes.c_int]
        u.GetSystemMetrics.restype = ctypes.c_int

        if hasattr(u, "GetDpiForSystem"):
            u.GetDpiForSystem.argtypes = []
            u.GetDpiForSystem.restype = ctypes.c_uint

        k = self.kernel32
        if hasattr(k, "GetTickCount64"):
            k.GetTickCount64.argtypes = []
            k.GetTickCount64.restype = ctypes.c_ulonglong

        k.GetTickCount.argtypes = []
        k.GetTickCount.restype = DWORD

        k.GetCurrentProcessId.argtypes = []
        k.GetCurrentProcessId.restype = DWORD

        k.ProcessIdToSessionId.argtypes = [DWORD, ctypes.POINTER(DWORD)]
        k.ProcessIdToSessionId.restype = BOOL

        if hasattr(k, "WTSGetActiveConsoleSessionId"):
            k.WTSGetActiveConsoleSessionId.argtypes = []
            k.WTSGetActiveConsoleSessionId.restype = DWORD

        k.CreateToolhelp32Snapshot.argtypes = [DWORD, DWORD]
        k.CreateToolhelp32Snapshot.restype = HANDLE

        k.Process32FirstW.argtypes = [HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        k.Process32FirstW.restype = BOOL

        k.Process32NextW.argtypes = [HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        k.Process32NextW.restype = BOOL

        k.CloseHandle.argtypes = [HANDLE]
        k.CloseHandle.restype = BOOL

        if self.dwmapi is not None:
            self.dwmapi.DwmIsCompositionEnabled.argtypes = [ctypes.POINTER(BOOL)]
            self.dwmapi.DwmIsCompositionEnabled.restype = HRESULT

        if self.shcore is not None:
            self.shcore.GetDpiForMonitor.argtypes = [
                HMONITOR,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint),
                ctypes.POINTER(ctypes.c_uint),
            ]
            self.shcore.GetDpiForMonitor.restype = HRESULT


_API = None


def api():
    global _API
    if _API is None:
        _API = Win32Api()
    return _API


# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------


def _attempt(errors, key, fn, default=None):
    """Run fn(); on failure record the reason under key and return default."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - per-field isolation is the point
        errors[key] = "%s: %s" % (type(exc).__name__, exc)
        return default


def _run_section(errors, name, fn, fallback):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        errors[name] = "%s: %s" % (type(exc).__name__, exc)
        return fallback


def _win_error(prefix):
    err = ctypes.get_last_error()
    try:
        text = ctypes.FormatError(err).strip()
    except Exception:  # noqa: BLE001
        text = ""
    return "%s (WinError %d: %s)" % (prefix, err, text)


def _decode_output(raw, fallback_encoding=None):
    """Decode subprocess output robustly.

    PowerShell emits UTF-8 (we force [Console]::OutputEncoding); wmic emits the
    OEM code page. BOM / NUL-pattern sniffing covers UTF-16 variants.
    """
    if not raw:
        return ""
    if raw[:4] == b"\xff\xfe\x00\x00":
        return raw.decode("utf-32-le", errors="replace").lstrip("\ufeff")
    if raw[:4] == b"\x00\x00\xfe\xff":
        return raw.decode("utf-32-be", errors="replace").lstrip("\ufeff")
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff")
    if raw[:2] == b"\xfe\xff":
        return raw.decode("utf-16-be", errors="replace").lstrip("\ufeff")
    # UTF-16LE without BOM: every second byte is NUL for ASCII-heavy text.
    sample = raw[:4096]
    if len(sample) >= 8:
        odd = sample[1::2]
        if odd and odd.count(0) > len(odd) * 0.4:
            return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    candidates = []
    if fallback_encoding:
        candidates.append(fallback_encoding)
    try:
        candidates.append("oem")
    except LookupError:
        pass
    candidates.append(locale.getpreferredencoding(False) or "cp1252")
    candidates.append("cp1252")
    for encoding in candidates:
        try:
            return raw.decode(encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("latin-1", errors="replace")


def _run(cmd, timeout=60):
    """Run a read-only external command, never through a shell."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        creationflags=creationflags,
    )


def _canonical(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rect_dict(rect):
    return {
        "left": int(rect.left),
        "top": int(rect.top),
        "right": int(rect.right),
        "bottom": int(rect.bottom),
        "width": int(rect.right - rect.left),
        "height": int(rect.bottom - rect.top),
    }


def _human_ms(ms):
    total = int(ms // 1000)
    days, total = divmod(total, 86400)
    hours, total = divmod(total, 3600)
    minutes, seconds = divmod(total, 60)
    return "%dd %02dh %02dm %02ds" % (days, hours, minutes, seconds)


def _state_flag_names(value):
    return [name for bit, name in STATE_FLAG_NAMES.items() if value & bit]


def _devmode_dict(dm):
    return {
        "device_name": dm.dmDeviceName,
        "width": int(dm.dmPelsWidth),
        "height": int(dm.dmPelsHeight),
        "refresh_hz": int(dm.dmDisplayFrequency),
        "bpp": int(dm.dmBitsPerPel),
        "display_flags": int(dm.dmDisplayFlags),
        "orientation": int(dm.u1.display.dmDisplayOrientation),
        "position": {
            "x": int(dm.u1.display.dmPosition.x),
            "y": int(dm.u1.display.dmPosition.y),
        },
        "fields_mask": "0x%08X" % int(dm.dmFields),
    }


def _current_mode(device_name, sink, tag, strict=True):
    """EnumDisplaySettingsW(device, ENUM_CURRENT_SETTINGS) -> dict or None.

    strict=False is used for adapters that are not attached to the desktop:
    their having no current mode is expected, not a collection error.
    """
    a = api()
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if not a.user32.EnumDisplaySettingsW(
        device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)
    ):
        if strict:
            sink.append("%s: %s" % (tag, _win_error("EnumDisplaySettingsW")))
        return None
    return _devmode_dict(dm)


# ---------------------------------------------------------------------------
# 1. monitors (EnumDisplayMonitors + GetMonitorInfoW + EnumDisplaySettingsW)
# ---------------------------------------------------------------------------


def _monitor_dpi(hmon):
    a = api()
    if a.shcore is None:
        return None
    x = ctypes.c_uint(0)
    y = ctypes.c_uint(0)
    hr = a.shcore.GetDpiForMonitor(
        hmon, MDT_EFFECTIVE_DPI, ctypes.byref(x), ctypes.byref(y)
    )
    if hr != 0:
        return None
    return {"effective": int(x.value), "raw": int(y.value)}


def collect_displays(errors):
    a = api()
    u = a.user32
    monitors = []
    cb_errors = []

    @a.MonitorEnumProc
    def _callback(hmon, hdc, lprc, lparam):  # noqa: ARG001 - Win32 signature
        try:
            mi = MONITORINFOEXW()
            mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if not u.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                raise OSError(_win_error("GetMonitorInfoW"))
            entry = {
                "index": len(monitors),
                "device": mi.szDevice,
                "primary": bool(int(mi.dwFlags) & MONITORINFOF_PRIMARY),
                "flags": int(mi.dwFlags),
                "rect": _rect_dict(mi.rcMonitor),
                "work_rect": _rect_dict(mi.rcWork),
            }
            entry["current_mode"] = _current_mode(
                mi.szDevice, cb_errors, "monitor[%d]" % entry["index"]
            )
            entry["dpi"] = _monitor_dpi(hmon)
            monitors.append(entry)
        except Exception as exc:  # noqa: BLE001 - callback must not raise
            cb_errors.append("%s: %s" % (type(exc).__name__, exc))
        return 1

    # LPARAM is an integer type, so NULL must be passed as LPARAM(0), not None
    # (ctypes only accepts None for pointer-typed parameters).
    if not u.EnumDisplayMonitors(None, None, _callback, LPARAM(0)):
        raise OSError(_win_error("EnumDisplayMonitors"))

    if cb_errors:
        errors["displays.monitor_entries"] = "; ".join(cb_errors)

    system_dpi = None
    if hasattr(u, "GetDpiForSystem"):
        system_dpi = _attempt(
            errors, "displays.system_dpi", lambda: int(u.GetDpiForSystem())
        )

    return {
        "monitors": monitors,
        "monitor_count": len(monitors),
        "system_dpi": system_dpi,
        "system_metrics": {
            "screen_width": _attempt(
                errors, "displays.screen_width", lambda: int(u.GetSystemMetrics(SM_CXSCREEN))
            ),
            "screen_height": _attempt(
                errors, "displays.screen_height", lambda: int(u.GetSystemMetrics(SM_CYSCREEN))
            ),
            "monitor_count_sm": _attempt(
                errors, "displays.monitor_count_sm", lambda: int(u.GetSystemMetrics(SM_CMONITORS))
            ),
            "virtual_screen_width": _attempt(
                errors,
                "displays.virtual_screen_width",
                lambda: int(u.GetSystemMetrics(SM_CXVIRTUALSCREEN)),
            ),
            "virtual_screen_height": _attempt(
                errors,
                "displays.virtual_screen_height",
                lambda: int(u.GetSystemMetrics(SM_CYVIRTUALSCREEN)),
            ),
        },
    }


# ---------------------------------------------------------------------------
# 6. display devices (EnumDisplayDevicesW, adapter + monitor level)
# ---------------------------------------------------------------------------


def _enumerate_modes(device_name, sink, tag, strict=True):
    """Enumerate every mode the adapter reports (registry modes included)."""
    a = api()
    seen = set()
    scanned = 0
    for index in range(MAX_MODES_SCANNED):
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        if not a.user32.EnumDisplaySettingsW(device_name, index, ctypes.byref(dm)):
            break
        scanned += 1
        seen.add(
            (
                int(dm.dmPelsWidth),
                int(dm.dmPelsHeight),
                int(dm.dmDisplayFrequency),
                int(dm.dmBitsPerPel),
            )
        )
    if scanned == 0 and strict:
        sink.append("%s: no modes enumerated" % tag)
    ordered = sorted(seen)
    refresh_rates = sorted({item[2] for item in ordered})
    return {
        "scanned": scanned,
        "distinct_count": len(ordered),
        "refresh_rates_hz": refresh_rates,
        "max_refresh_hz": refresh_rates[-1] if refresh_rates else None,
        "modes_truncated": len(ordered) > MAX_MODES_RECORDED,
        "modes": [
            {"width": w, "height": h, "refresh_hz": hz, "bpp": bpp}
            for (w, h, hz, bpp) in ordered[:MAX_MODES_RECORDED]
        ],
    }


def collect_display_devices(errors):
    a = api()
    u = a.user32
    adapters = []
    for adapter_index in range(MAX_ADAPTERS):
        dd = DISPLAY_DEVICEW()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not u.EnumDisplayDevicesW(None, adapter_index, ctypes.byref(dd), 0):
            break
        flags = int(dd.StateFlags)
        entry = {
            "index": adapter_index,
            "device_name": dd.DeviceName,
            "device_string": dd.DeviceString,
            "device_id": dd.DeviceID,
            "device_key": dd.DeviceKey,
            "state_flags": flags,
            "state_flags_hex": "0x%08X" % flags,
            "state_flag_names": _state_flag_names(flags),
            "attached_to_desktop": bool(flags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP),
            "primary": bool(flags & DISPLAY_DEVICE_PRIMARY_DEVICE),
            "monitors": [],
        }
        mode_errors = []
        # A detached adapter legitimately has no current mode and no modes, so
        # absence is only an error for adapters attached to the desktop.
        attached = entry["attached_to_desktop"]
        try:
            entry["current_mode"] = _current_mode(
                dd.DeviceName, mode_errors, "adapter", strict=attached
            )
        except Exception as exc:  # noqa: BLE001 - isolate one adapter's mode probe
            mode_errors.append("%s: %s" % (type(exc).__name__, exc))
        try:
            entry["modes"] = _enumerate_modes(
                dd.DeviceName, mode_errors, "adapter", strict=attached
            )
        except Exception as exc:  # noqa: BLE001
            mode_errors.append("mode enumeration: %s: %s" % (type(exc).__name__, exc))
        if mode_errors:
            errors["display_devices.%s" % dd.DeviceName] = "; ".join(mode_errors)

        try:
            for monitor_index in range(MAX_ADAPTERS):
                md = DISPLAY_DEVICEW()
                md.cb = ctypes.sizeof(DISPLAY_DEVICEW)
                if not u.EnumDisplayDevicesW(
                    dd.DeviceName, monitor_index, ctypes.byref(md), 0
                ):
                    break
                mflags = int(md.StateFlags)
                entry["monitors"].append(
                    {
                        "index": monitor_index,
                        "device_name": md.DeviceName,
                        "device_string": md.DeviceString,
                        "device_id": md.DeviceID,
                        "device_key": md.DeviceKey,
                        "state_flags": mflags,
                        "state_flags_hex": "0x%08X" % mflags,
                        "state_flag_names": _state_flag_names(mflags),
                        "attached_to_desktop": bool(
                            mflags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
                        ),
                        "primary": bool(mflags & DISPLAY_DEVICE_PRIMARY_DEVICE),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            errors["display_devices.%s.monitors" % dd.DeviceName] = "%s: %s" % (
                type(exc).__name__,
                exc,
            )
        adapters.append(entry)

    attached = [a_["device_name"] for a_ in adapters if a_["attached_to_desktop"]]
    detached = [a_["device_name"] for a_ in adapters if not a_["attached_to_desktop"]]
    primary = [a_["device_name"] for a_ in adapters if a_["primary"]]
    return {
        "adapters": adapters,
        "summary": {
            "adapter_count": len(adapters),
            "attached_count": len(attached),
            "detached_count": len(detached),
            "attached": attached,
            "detached": detached,
            "primary": primary,
        },
    }


# ---------------------------------------------------------------------------
# 2/3/5/7. CIM (Win32_* classes) via PowerShell, wmic fallback
# ---------------------------------------------------------------------------

CIM_SPECS = [
    {
        "key": "video_controllers",
        "class": "Win32_VideoController",
        "props": [
            "Name",
            "DriverVersion",
            "DriverDate",
            "AdapterRAM",
            "CurrentHorizontalResolution",
            "CurrentVerticalResolution",
            "CurrentRefreshRate",
            "VideoModeDescription",
            "VideoProcessor",
            "PNPDeviceID",
            "Status",
            "ConfigManagerErrorCode",
        ],
        "where": None,
    },
    {
        "key": "computer_system",
        "class": "Win32_ComputerSystem",
        "props": [
            "Manufacturer",
            "Model",
            "SystemType",
            "TotalPhysicalMemory",
            "NumberOfLogicalProcessors",
            "HypervisorPresent",
        ],
        "where": None,
    },
    {
        "key": "battery",
        "class": "Win32_Battery",
        "props": [
            "Name",
            "Status",
            "BatteryStatus",
            "EstimatedChargeRemaining",
            "DeviceID",
        ],
        "where": None,
    },
    {
        "key": "operating_system",
        "class": "Win32_OperatingSystem",
        "props": [
            "Caption",
            "Version",
            "BuildNumber",
            "OSArchitecture",
            "LastBootUpTime",
            "InstallDate",
            "TotalVisibleMemorySize",
            "FreePhysicalMemory",
        ],
        "where": None,
    },
    {
        "key": "processor",
        "class": "Win32_Processor",
        "props": [
            "Name",
            "Manufacturer",
            "NumberOfCores",
            "NumberOfLogicalProcessors",
            "MaxClockSpeed",
            "CurrentClockSpeed",
        ],
        "where": None,
    },
    {
        "key": "dwm_process",
        "class": "Win32_Process",
        "props": [
            "Name",
            "ProcessId",
            "ParentProcessId",
            "SessionId",
            "ThreadCount",
            "WorkingSetSize",
            "CreationDate",
        ],
        "where": "Name='dwm.exe'",
    },
]

PS_BATCH = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

function __cf_norm($obj) {
  $h = [ordered]@{}
  foreach ($p in $obj.PSObject.Properties) {
    $v = $p.Value
    if ($v -is [datetime]) { $v = $v.ToString('yyyy-MM-ddTHH:mm:ss') }
    elseif ($v -is [byte[]]) { $v = [Convert]::ToBase64String($v) }
    $h[$p.Name] = $v
  }
  [pscustomobject]$h
}

$out = [ordered]@{}

try {
  $out['video_controllers'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop | Select-Object Name,DriverVersion,DriverDate,AdapterRAM,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,VideoModeDescription,VideoProcessor,PNPDeviceID,Status,ConfigManagerErrorCode | ForEach-Object { __cf_norm $_ }) }
} catch { $out['video_controllers'] = @{ ok = $false; error = $_.Exception.Message } }

try {
  $out['computer_system'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop | Select-Object Manufacturer,Model,SystemType,TotalPhysicalMemory,NumberOfLogicalProcessors,HypervisorPresent | ForEach-Object { __cf_norm $_ }) }
} catch { $out['computer_system'] = @{ ok = $false; error = $_.Exception.Message } }

try {
  $out['battery'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_Battery -ErrorAction Stop | Select-Object Name,Status,BatteryStatus,EstimatedChargeRemaining,DeviceID | ForEach-Object { __cf_norm $_ }) }
} catch { $out['battery'] = @{ ok = $false; error = $_.Exception.Message } }

try {
  $out['operating_system'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop | Select-Object Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime,InstallDate,TotalVisibleMemorySize,FreePhysicalMemory | ForEach-Object { __cf_norm $_ }) }
} catch { $out['operating_system'] = @{ ok = $false; error = $_.Exception.Message } }

try {
  $out['processor'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed | ForEach-Object { __cf_norm $_ }) }
} catch { $out['processor'] = @{ ok = $false; error = $_.Exception.Message } }

try {
  $out['dwm_process'] = @{ ok = $true; data = @(Get-CimInstance -ClassName Win32_Process -Filter "Name='dwm.exe'" -ErrorAction Stop | Select-Object Name,ProcessId,ParentProcessId,SessionId,ThreadCount,WorkingSetSize,CreationDate | ForEach-Object { __cf_norm $_ }) }
} catch { $out['dwm_process'] = @{ ok = $false; error = $_.Exception.Message } }

ConvertTo-Json -InputObject $out -Depth 6 -Compress
"""

PS_BOOT_HISTORY = r"""
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$items = @()
try {
  $events = Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-Kernel-General'; Id = 12, 13 } -MaxEvents 24 -ErrorAction Stop
  foreach ($e in $events) {
    $t = $null
    if ($e.TimeCreated) { $t = $e.TimeCreated.ToString('yyyy-MM-ddTHH:mm:ss') }
    $items += [pscustomobject]@{ TimeCreated = $t; Id = $e.Id }
  }
  @{ ok = $true; data = $items } | ConvertTo-Json -Depth 4 -Compress
} catch {
  @{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json -Depth 4 -Compress
}
"""


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_wmic_list(text):
    rows = []
    current = {}
    for line in text.splitlines():
        line = line.strip("\r")
        if not line.strip():
            if current:
                rows.append(current)
                current = {}
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            current[key.strip()] = value.strip()
    if current:
        rows.append(current)
    return rows


def _is_cjk_locale():
    """True when the console code page is likely a CJK OEM page."""
    try:
        encoding = (locale.getencoding() or "").lower()
    except Exception:  # noqa: BLE001
        return False
    return encoding in ("cp936", "gbk", "gb2312", "cp950", "cp932", "cp949", "cp65001")


def _decode_console(raw):
    """Decode console-tool output (wmic / powercfg): OEM page, not UTF-8."""
    return _decode_output(raw, fallback_encoding="cp936" if _is_cjk_locale() else None)


def _wmic_query(spec, timeout=30):
    wmic = shutil.which("wmic")
    if not wmic:
        raise FileNotFoundError("wmic not found on PATH")
    cmd = [wmic, "path", spec["class"]]
    if spec.get("where"):
        cmd += ["where", spec["where"]]
    cmd += ["get", ",".join(spec["props"]), "/format:list"]
    proc = _run(cmd, timeout=timeout)
    text = _decode_console(proc.stdout)
    rows = _parse_wmic_list(text)
    if proc.returncode != 0 and not rows:
        lowered = text.lower()
        if "no instance" in lowered:
            return []
        detail = _decode_console(proc.stderr).strip() or text.strip()
        raise OSError("wmic exit %d: %s" % (proc.returncode, detail[:300]))
    return rows


def _probe_powershell(timeout=120):
    """Run the batched CIM query. Returns (rows_by_key, per_key_errors, probe)."""
    rows = {}
    failures = {}
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return rows, failures, {"tool": None, "ok": False, "error": "not found on PATH"}
    probe = {"tool": powershell, "ok": False, "error": None}
    try:
        proc = _run(
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                PS_BATCH,
            ],
            timeout=timeout,
        )
        text = _decode_output(proc.stdout).strip()
        if not text:
            raise ValueError(
                "empty output; exit=%d stderr=%r"
                % (proc.returncode, _decode_output(proc.stderr)[:300])
            )
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("unexpected JSON root type: %s" % type(payload).__name__)
        probe["ok"] = True
        probe["exit_code"] = proc.returncode
        for key, entry in payload.items():
            if not isinstance(entry, dict):
                failures[key] = "malformed PowerShell entry"
                continue
            if entry.get("ok"):
                rows[key] = _as_list(entry.get("data"))
            else:
                failures[key] = "powershell: %s" % (entry.get("error") or "unknown error")
    except Exception as exc:  # noqa: BLE001
        probe["error"] = "%s: %s" % (type(exc).__name__, exc)
    return rows, failures, probe


def _probe_wmic():
    """Run every wmic class query. Returns (rows_by_key, per_key_errors, probe)."""
    rows = {}
    failures = {}
    wmic = shutil.which("wmic")
    if not wmic:
        return rows, failures, {"tool": None, "ok": False, "error": "not found on PATH"}
    probe = {"tool": wmic, "ok": False, "error": None, "classes_ok": [], "classes_failed": []}
    for spec in CIM_SPECS:
        key = spec["key"]
        try:
            rows[key] = _wmic_query(spec)
            probe["classes_ok"].append(key)
        except Exception as exc:  # noqa: BLE001
            failures[key] = "wmic: %s" % exc
            probe["classes_failed"].append(key)
    probe["ok"] = bool(probe["classes_ok"])
    if not probe["classes_ok"]:
        probe["error"] = "; ".join(sorted(failures.values()))[:400]
    return rows, failures, probe


def collect_cim(errors, backends):
    """Query every Win32_* class.

    Both PowerShell Get-CimInstance and wmic are always attempted (per the
    task contract) and both probe results are recorded. PowerShell wins when it
    returns data for a class; wmic fills any class PowerShell missed.
    """
    ps_rows, ps_failures, ps_probe = _probe_powershell()
    wmic_rows, wmic_failures, wmic_probe = _probe_wmic()

    result = {}
    for spec in CIM_SPECS:
        key = spec["key"]
        if key in ps_rows:
            result[key] = ps_rows[key]
            backends[key] = "powershell:Get-CimInstance"
        elif key in wmic_rows:
            result[key] = wmic_rows[key]
            backends[key] = "wmic"
        else:
            reason = []
            if key in ps_failures:
                reason.append(ps_failures[key])
            if key in wmic_failures:
                reason.append(wmic_failures[key])
            if not reason:
                reason.append("no backend produced data")
            errors["cim.%s" % key] = " | ".join(reason)

    return result, {"powershell": ps_probe, "wmic": wmic_probe}


def _first(rows):
    if isinstance(rows, list) and rows:
        return rows[0]
    return {}


def collect_gpu(errors, cim):
    controllers = cim.get("video_controllers")
    if controllers is None:
        controllers = []
    normalized = []
    for item in _as_list(controllers):
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "name": item.get("Name"),
                "driver_version": item.get("DriverVersion"),
                "driver_date": item.get("DriverDate"),
                "adapter_ram": item.get("AdapterRAM"),
                "current_width": item.get("CurrentHorizontalResolution"),
                "current_height": item.get("CurrentVerticalResolution"),
                "current_refresh_hz": item.get("CurrentRefreshRate"),
                "video_mode_description": item.get("VideoModeDescription"),
                "video_processor": item.get("VideoProcessor"),
                "pnp_device_id": item.get("PNPDeviceID"),
                "status": item.get("Status"),
                "config_manager_error_code": item.get("ConfigManagerErrorCode"),
            }
        )
    return {"controllers": normalized, "controller_count": len(normalized)}


def collect_session(errors, cim):
    a = api()
    u = a.user32
    k = a.kernel32
    out = {}
    out["env_session_name"] = os.environ.get("SESSIONNAME")
    out["remote_session"] = _attempt(
        errors, "session.remote_session", lambda: int(u.GetSystemMetrics(SM_REMOTESESSION))
    )
    out["monitor_count_sm"] = _attempt(
        errors, "session.monitor_count_sm", lambda: int(u.GetSystemMetrics(SM_CMONITORS))
    )
    out["screen"] = {
        "width": _attempt(
            errors, "session.screen_width", lambda: int(u.GetSystemMetrics(SM_CXSCREEN))
        ),
        "height": _attempt(
            errors, "session.screen_height", lambda: int(u.GetSystemMetrics(SM_CYSCREEN))
        ),
    }

    pid = _attempt(
        errors,
        "session.process_id",
        lambda: int(k.GetCurrentProcessId()),
        os.getpid(),
    )
    out["process_id"] = pid

    def _process_session_id():
        sid = DWORD(0)
        if not k.ProcessIdToSessionId(DWORD(int(pid)), ctypes.byref(sid)):
            raise OSError(_win_error("ProcessIdToSessionId"))
        return int(sid.value)

    def _console_session_id():
        value = int(k.WTSGetActiveConsoleSessionId())
        return value if value != 0xFFFFFFFF else None

    out["process_session_id"] = _attempt(
        errors, "session.process_session_id", _process_session_id
    )
    out["active_console_session_id"] = _attempt(
        errors, "session.active_console_session_id", _console_session_id
    )

    system = _first(cim.get("computer_system"))
    out["computer_system"] = {
        "manufacturer": system.get("Manufacturer"),
        "model": system.get("Model"),
        "system_type": system.get("SystemType"),
        "total_physical_memory": system.get("TotalPhysicalMemory"),
        "hypervisor_present": system.get("HypervisorPresent"),
    }
    blob = " ".join(
        str(system.get(key) or "")
        for key in ("Manufacturer", "Model", "SystemType")
    ).lower()
    vm_markers = (
        "virtual",
        "vmware",
        "vbox",
        "virtualbox",
        "hyper-v",
        "kvm",
        "qemu",
        "xen",
        "hvm domu",
        "parallels",
        "bochs",
        "cloud",
    )
    out["is_vm_guess"] = any(marker in blob for marker in vm_markers)
    return out


def collect_dwm(errors, cim, process_names):
    a = api()
    out = {"composition_enabled": None}
    if a.dwmapi is not None:
        def _composition():
            flag = BOOL(0)
            hr = a.dwmapi.DwmIsCompositionEnabled(ctypes.byref(flag))
            if hr != 0:
                raise OSError("DwmIsCompositionEnabled HRESULT 0x%08X" % (hr & 0xFFFFFFFF))
            return bool(flag.value)

        out["composition_enabled"] = _attempt(
            errors, "dwm.composition_enabled", _composition
        )
    else:
        errors["dwm.composition_enabled"] = "dwmapi.dll not loadable"

    lower_names = [name.lower() for name in process_names]
    out["dwm_exe_in_process_snapshot"] = "dwm.exe" in lower_names
    out["dwm_exe_count_in_snapshot"] = lower_names.count("dwm.exe")

    rows = _as_list(cim.get("dwm_process"))
    out["win32_process_dwm"] = [
        {
            "name": row.get("Name"),
            "process_id": row.get("ProcessId"),
            "parent_process_id": row.get("ParentProcessId"),
            "session_id": row.get("SessionId"),
            "thread_count": row.get("ThreadCount"),
            "working_set_size": row.get("WorkingSetSize"),
            "creation_date": row.get("CreationDate"),
        }
        for row in rows
        if isinstance(row, dict)
    ]
    out["dwm_process_running"] = bool(out["win32_process_dwm"]) or out[
        "dwm_exe_in_process_snapshot"
    ]
    return out


def collect_power(errors, cim):
    out = {}
    try:
        proc = _run(["powercfg", "/getactivescheme"], timeout=30)
        text = _decode_console(proc.stdout).strip()
        if proc.returncode != 0:
            raise OSError(
                "powercfg exit %d: %s"
                % (proc.returncode, _decode_console(proc.stderr).strip()[:300])
            )
        if not text:
            raise ValueError("powercfg produced no output")
        out["active_scheme_raw"] = text
        guid = re.search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            text,
        )
        out["active_scheme_guid"] = guid.group(0).lower() if guid else None
        names = re.findall(r"\(([^()]*)\)", text)
        out["active_scheme_name"] = names[-1].strip() if names else None
    except Exception as exc:  # noqa: BLE001
        errors["power.active_scheme"] = "%s: %s" % (type(exc).__name__, exc)

    battery_rows = _as_list(cim.get("battery"))
    out["battery_present"] = bool(battery_rows) if cim.get("battery") is not None else None
    out["battery"] = [
        {
            "name": row.get("Name"),
            "status": row.get("Status"),
            "battery_status": row.get("BatteryStatus"),
            "estimated_charge_remaining": row.get("EstimatedChargeRemaining"),
            "device_id": row.get("DeviceID"),
        }
        for row in battery_rows
        if isinstance(row, dict)
    ]
    return out


# ---------------------------------------------------------------------------
# 7. processes (toolhelp snapshot, pure ctypes)
# ---------------------------------------------------------------------------


def collect_processes(errors):
    a = api()
    k = a.kernel32
    snapshot = None
    try:
        snapshot = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot is None or snapshot == a.invalid_handle_value:
            raise OSError(_win_error("CreateToolhelp32Snapshot"))
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not k.Process32FirstW(snapshot, ctypes.byref(entry)):
            raise OSError(_win_error("Process32FirstW"))
        names = []
        while True:
            names.append(entry.szExeFile)
            if not k.Process32NextW(snapshot, ctypes.byref(entry)):
                break
        return {
            "count": len(names),
            "dwm_exe_present": "dwm.exe" in [n.lower() for n in names],
            "dwm_exe_count": [n.lower() for n in names].count("dwm.exe"),
            "names": names,
        }
    finally:
        if snapshot is not None and snapshot != a.invalid_handle_value:
            k.CloseHandle(snapshot)


# ---------------------------------------------------------------------------
# 7. system: uptime, OS, CPU, python, script provenance
# ---------------------------------------------------------------------------


def collect_system(errors, cim):
    a = api()
    k = a.kernel32
    out = {}

    def _tick_ms():
        if hasattr(k, "GetTickCount64"):
            return int(k.GetTickCount64())
        return int(k.GetTickCount())

    tick = _attempt(errors, "system.uptime_ms", _tick_ms)
    out["uptime_ms_tick"] = tick
    out["uptime_human"] = _human_ms(tick) if tick is not None else None
    out["uptime_source"] = "GetTickCount64 (does not count suspend time)"
    if tick is not None:
        now_utc = dt.datetime.now(dt.timezone.utc)
        boot = now_utc - dt.timedelta(milliseconds=tick)
        out["boot_time_utc_from_tick"] = boot.strftime("%Y-%m-%dT%H:%M:%SZ")
        out["boot_time_local_from_tick"] = boot.astimezone().strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )

    os_row = _first(cim.get("operating_system"))
    out["os"] = {
        "caption": os_row.get("Caption"),
        "version": os_row.get("Version"),
        "build_number": os_row.get("BuildNumber"),
        "architecture": os_row.get("OSArchitecture"),
        "last_boot_up_time": os_row.get("LastBootUpTime"),
        "install_date": os_row.get("InstallDate"),
        "total_visible_memory_kb": os_row.get("TotalVisibleMemorySize"),
        "free_physical_memory_kb": os_row.get("FreePhysicalMemory"),
        "platform_version_fallback": platform.version(),
    }

    cpu_row = _first(cim.get("processor"))
    out["cpu"] = {
        "name": cpu_row.get("Name"),
        "manufacturer": cpu_row.get("Manufacturer"),
        "cores": cpu_row.get("NumberOfCores"),
        "logical_processors": cpu_row.get("NumberOfLogicalProcessors"),
        "max_clock_mhz": cpu_row.get("MaxClockSpeed"),
        "current_clock_mhz": cpu_row.get("CurrentClockSpeed"),
        "machine": platform.machine(),
        "processor_platform": platform.processor(),
    }

    out["python"] = {
        "version": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "platform": platform.platform(),
    }
    out["timezone"] = {
        "name": time.tzname[0] if time.tzname else None,
        "utc_offset_seconds": -time.timezone,
        "dst_active": bool(time.daylight and time.localtime().tm_isdst > 0),
    }

    script_path = os.path.abspath(__file__) if "__file__" in globals() else None
    script_info = {"path": script_path, "sha256": None}
    if script_path and os.path.isfile(script_path):
        try:
            with open(script_path, "rb") as handle:
                script_info["sha256"] = hashlib.sha256(handle.read()).hexdigest()
        except OSError as exc:
            errors["system.script_sha256"] = "%s: %s" % (type(exc).__name__, exc)
    out["collector"] = script_info
    return out


def collect_boot_history(errors):
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        raise FileNotFoundError("powershell not found on PATH")
    proc = _run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            PS_BOOT_HISTORY,
        ],
        timeout=90,
    )
    text = _decode_output(proc.stdout).strip()
    if not text:
        raise ValueError("empty output; stderr=%r" % _decode_output(proc.stderr)[:300])
    payload = json.loads(text)
    if not isinstance(payload, dict) or not payload.get("ok"):
        raise RuntimeError(
            "event query failed: %s" % ((payload or {}).get("error") or "unknown")
        )
    return {
        "source": "WinEventLog System/Microsoft-Windows-Kernel-General (12=start, 13=stop)",
        "events": _as_list(payload.get("data")),
    }


# ---------------------------------------------------------------------------
# fingerprint + output
# ---------------------------------------------------------------------------


def _env_payload(doc):
    """Stable subset used for env_digest.

    Volatile values (free memory, current clock, process lists, timestamps) are
    deliberately excluded so two runs inside one boot session produce the same
    digest while a different boot session produces a different one.
    """
    system = doc.get("system") or {}
    os_info = system.get("os") or {}
    cpu = system.get("cpu") or {}
    return {
        "displays": {
            "monitors": [
                {
                    "device": item.get("device"),
                    "primary": item.get("primary"),
                    "rect": item.get("rect"),
                    "work_rect": item.get("work_rect"),
                    "current_mode": item.get("current_mode"),
                    "dpi": item.get("dpi"),
                }
                for item in (doc.get("displays") or {}).get("monitors", [])
            ],
            "system_metrics": (doc.get("displays") or {}).get("system_metrics"),
            "system_dpi": (doc.get("displays") or {}).get("system_dpi"),
        },
        "display_devices": {
            "adapters": [
                {
                    "device_name": item.get("device_name"),
                    "device_string": item.get("device_string"),
                    "device_id": item.get("device_id"),
                    "state_flags_hex": item.get("state_flags_hex"),
                    "attached_to_desktop": item.get("attached_to_desktop"),
                    "primary": item.get("primary"),
                    "current_mode": item.get("current_mode"),
                    "modes": item.get("modes"),
                    "monitors": item.get("monitors"),
                }
                for item in (doc.get("display_devices") or {}).get("adapters", [])
            ],
            "summary": (doc.get("display_devices") or {}).get("summary"),
        },
        "gpu": doc.get("gpu"),
        "session": {
            "remote_session": (doc.get("session") or {}).get("remote_session"),
            "monitor_count_sm": (doc.get("session") or {}).get("monitor_count_sm"),
            "process_session_id": (doc.get("session") or {}).get(
                "process_session_id"
            ),
            "active_console_session_id": (doc.get("session") or {}).get(
                "active_console_session_id"
            ),
            "computer_system": (doc.get("session") or {}).get("computer_system"),
            "is_vm_guess": (doc.get("session") or {}).get("is_vm_guess"),
        },
        "dwm": {
            "composition_enabled": (doc.get("dwm") or {}).get("composition_enabled"),
            "dwm_process_running": (doc.get("dwm") or {}).get("dwm_process_running"),
        },
        "power": {
            "active_scheme_guid": (doc.get("power") or {}).get("active_scheme_guid"),
            "active_scheme_name": (doc.get("power") or {}).get("active_scheme_name"),
            "battery_present": (doc.get("power") or {}).get("battery_present"),
        },
        "system": {
            "os": {
                "caption": os_info.get("caption"),
                "version": os_info.get("version"),
                "build_number": os_info.get("build_number"),
                "architecture": os_info.get("architecture"),
                "install_date": os_info.get("install_date"),
            },
            "cpu": {
                "name": cpu.get("name"),
                "manufacturer": cpu.get("manufacturer"),
                "cores": cpu.get("cores"),
                "logical_processors": cpu.get("logical_processors"),
            },
            "boot_key": system.get("boot_key"),
            "timezone": system.get("timezone"),
        },
    }


def _normalize_boot_stamp(value):
    """Turn either WMI datetime format into 'YYYY-MM-DDTHH:MM' (minute precision).

    PowerShell path yields '2026-10-21T09:45:43'; wmic yields
    '20261021094543.500000+480'. Minute precision keeps the key stable across
    runs of one boot session while still separating different sessions.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", text)
    if match:
        return "%s-%s-%sT%s:%s" % match.groups()
    match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", text)
    if match:
        year, month, day, hour, minute = match.groups()[:5]
        return "%s-%s-%sT%s:%s" % (year, month, day, hour, minute)
    return text[:16]


def build_document(errors, backends, sections, probes=None):
    captured_local_dt = dt.datetime.now().astimezone()
    captured_utc_dt = dt.datetime.now(dt.timezone.utc)

    doc = {
        "schema": SCHEMA,
        "fingerprint_id": None,
        "env_digest": None,
        "captured_at_local": captured_local_dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "captured_at_utc": captured_utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": {
            "computer_name": os.environ.get("COMPUTERNAME") or platform.node(),
            "machine": platform.machine(),
        },
        "session": sections["session"],
        "displays": sections["displays"],
        "display_devices": sections["display_devices"],
        "gpu": sections["gpu"],
        "dwm": sections["dwm"],
        "power": sections["power"],
        "system": sections["system"],
        "processes": {
            "count": sections["processes"].get("count"),
            "dwm_exe_present": sections["processes"].get("dwm_exe_present"),
            "dwm_exe_count": sections["processes"].get("dwm_exe_count"),
            "names": sections["processes"].get("names"),
        },
        "boot_history": sections["boot_history"],
        "collection_backends": backends,
        "backend_probe": probes or {},
        "errors": errors,
    }

    # boot_key: minute-resolution boot stamp, stable across runs of one session
    boot_key = None
    os_row = _first(sections["cim"].get("operating_system"))
    last_boot = os_row.get("LastBootUpTime")
    boot_key = _normalize_boot_stamp(last_boot)
    if not boot_key:
        tick_boot = doc["system"].get("boot_time_utc_from_tick")
        boot_key = _normalize_boot_stamp(tick_boot)
    doc["system"]["boot_key"] = boot_key
    doc["system"]["boot_key_source"] = (
        "Win32_OperatingSystem.LastBootUpTime"
        if last_boot
        else "GetTickCount64-derived (suspend time excluded), minute-truncated"
    )

    payload_for_id = dict(doc)
    payload_for_id["_process_id"] = doc["session"].get("process_id")
    payload_for_id["_captured_at_local"] = doc["captured_at_local"]
    payload_for_id.pop("fingerprint_id", None)
    payload_for_id.pop("env_digest", None)
    payload_for_id.pop("errors", None)
    fingerprint_id = _sha256_hex(_canonical(payload_for_id))[:16]
    env_digest = _sha256_hex(_canonical(_env_payload(doc)))[:16]

    doc["fingerprint_id"] = fingerprint_id
    doc["env_digest"] = env_digest
    doc["fingerprint"] = {
        "id": fingerprint_id,
        "id_inputs": "sha256(canonical JSON of all sections + process_id + captured_at_local)[:16]",
        "env_digest": env_digest,
        "env_digest_inputs": "sha256(canonical JSON of stable env subset)[:16]",
        "env_digest_excludes": [
            "captured_at_local/utc",
            "session.process_id",
            "system.uptime_ms_tick",
            "system.uptime_human",
            "system.boot_time_*_from_tick (use system.boot_key)",
            "processes.* (count and names)",
            "dwm.win32_process_dwm[].process_id/creation_date",
            "boot_history (event list)",
            "collection_backends",
            "errors",
        ],
    }
    return doc


def write_report(doc, out_dir):
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    name = "boot_fingerprint_%s_%s.json" % (stamp, doc["fingerprint_id"])
    path = os.path.join(out_dir, name)
    text = json.dumps(doc, ensure_ascii=False, indent=2, default=str)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.write("\n")
    return os.path.abspath(path)


def print_summary(doc, out_path):
    def val(value, suffix=""):
        if value is None:
            return "?"
        return "%s%s" % (value, suffix)

    lines = []
    lines.append("=" * 74)
    lines.append("boot session fingerprint  %s" % doc["fingerprint_id"])
    lines.append("=" * 74)
    lines.append("captured   : %s (%s)" % (doc["captured_at_local"], doc["captured_at_utc"]))
    lines.append("env_digest : %s  (same boot session => same digest)" % doc["env_digest"])

    system = doc.get("system") or {}
    os_info = system.get("os") or {}
    lines.append(
        "os         : %s | %s | build %s | %s"
        % (
            val(os_info.get("caption")),
            val(os_info.get("version")),
            val(os_info.get("build_number")),
            val(os_info.get("architecture")),
        )
    )
    lines.append(
        "boot       : %s (uptime %s, %s)"
        % (
            val(system.get("boot_key")),
            val(system.get("uptime_human")),
            val(system.get("uptime_source")),
        )
    )
    cpu = system.get("cpu") or {}
    lines.append(
        "cpu        : %s | cores=%s logical=%s"
        % (val(cpu.get("name")), val(cpu.get("cores")), val(cpu.get("logical_processors")))
    )

    session = doc.get("session") or {}
    lines.append(
        "session    : remote=%s monitors=%s proc_session=%s console_session=%s env=%s"
        % (
            val(session.get("remote_session")),
            val(session.get("monitor_count_sm")),
            val(session.get("process_session_id")),
            val(session.get("active_console_session_id")),
            val(session.get("env_session_name")),
        )
    )
    computer = session.get("computer_system") or {}
    lines.append(
        "machine    : %s / %s | vm_guess=%s"
        % (
            val(computer.get("manufacturer")),
            val(computer.get("model")),
            val(session.get("is_vm_guess")),
        )
    )

    displays = doc.get("displays") or {}
    monitors = displays.get("monitors") or []
    lines.append("monitors   : %d" % len(monitors))
    for item in monitors:
        mode = item.get("current_mode") or {}
        rect = item.get("rect") or {}
        dpi = item.get("dpi") or {}
        lines.append(
            "  [%d] %-16s %s %sx%s @ %s Hz  rect %sx%s  dpi=%s"
            % (
                item.get("index", 0),
                val(item.get("device")),
                "PRIMARY" if item.get("primary") else "       ",
                val(mode.get("width")),
                val(mode.get("height")),
                val(mode.get("refresh_hz")),
                val(rect.get("width")),
                val(rect.get("height")),
                val(dpi.get("effective")),
            )
        )

    gpu = doc.get("gpu") or {}
    for item in gpu.get("controllers") or []:
        lines.append(
            "gpu        : %s | driver %s (%s) | %sx%s @ %s Hz"
            % (
                val(item.get("name")),
                val(item.get("driver_version")),
                val(item.get("driver_date")),
                val(item.get("current_width")),
                val(item.get("current_height")),
                val(item.get("current_refresh_hz")),
            )
        )
    if not (gpu.get("controllers") or []):
        lines.append("gpu        : ?")

    dwm = doc.get("dwm") or {}
    lines.append(
        "dwm        : composition=%s dwm.exe=%s (snapshot=%s)"
        % (
            val(dwm.get("composition_enabled")),
            val(dwm.get("dwm_process_running")),
            val(dwm.get("dwm_exe_in_process_snapshot")),
        )
    )

    power = doc.get("power") or {}
    lines.append(
        "power      : %s (%s) | battery=%s"
        % (
            val(power.get("active_scheme_guid")),
            val(power.get("active_scheme_name")),
            val(power.get("battery_present")),
        )
    )

    devices = (doc.get("display_devices") or {}).get("summary") or {}
    lines.append(
        "devices    : adapters=%s attached=%s detached=%s primary=%s"
        % (
            val(devices.get("adapter_count")),
            val(devices.get("attached_count")),
            val(devices.get("detached_count")),
            ",".join(devices.get("primary") or []) or "?",
        )
    )
    for item in (doc.get("display_devices") or {}).get("adapters") or []:
        mode = item.get("current_mode") or {}
        modes = item.get("modes") or {}
        lines.append(
            "  %-14s %-52s attached=%-5s %sx%s@%sHz maxHz=%s"
            % (
                val(item.get("device_name")),
                (val(item.get("device_string")) or "")[:52],
                val(item.get("attached_to_desktop")),
                val(mode.get("width")),
                val(mode.get("height")),
                val(mode.get("refresh_hz")),
                val(modes.get("max_refresh_hz")),
            )
        )

    processes = doc.get("processes") or {}
    lines.append("processes  : count=%s" % val(processes.get("count")))

    history = (doc.get("boot_history") or {}).get("events") or []
    if history:
        recent = history[:6]
        lines.append("boot log   : %d event(s), newest first" % len(history))
        for event in recent:
            lines.append(
                "  %s  id=%s %s"
                % (
                    val(event.get("TimeCreated")),
                    val(event.get("Id")),
                    "START" if str(event.get("Id")) == "12" else "STOP",
                )
            )

    errors = doc.get("errors") or {}
    if errors:
        lines.append("errors     : %d field(s) failed" % len(errors))
        for key in sorted(errors):
            lines.append("  - %s: %s" % (key, errors[key]))
    else:
        lines.append("errors     : none")

    lines.append("json       : %s" % out_path)
    lines.append("=" * 74)
    print("\n".join(lines))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Read-only boot-session environment fingerprint (GOAL-3T todo 3)."
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="directory for the JSON report (default: current working directory)",
    )
    parser.add_argument(
        "--no-boot-history",
        action="store_true",
        help="skip the read-only System event-log boot history query",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the human-readable stdout summary",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    if sys.platform != "win32":
        print("error: this collector is Windows-only", file=sys.stderr)
        return 3

    errors = {}
    backends = {}

    cim, probes = _run_section(
        errors, "cim", lambda: collect_cim(errors, backends), ({}, {})
    )

    sections = {
        "cim": cim,
        "displays": _run_section(errors, "displays", lambda: collect_displays(errors), {}),
        "display_devices": _run_section(
            errors, "display_devices", lambda: collect_display_devices(errors), {}
        ),
        "session": _run_section(errors, "session", lambda: collect_session(errors, cim), {}),
        "gpu": _run_section(errors, "gpu", lambda: collect_gpu(errors, cim), {}),
    }

    processes = _run_section(errors, "processes", lambda: collect_processes(errors), {})
    sections["processes"] = processes
    sections["dwm"] = _run_section(
        errors,
        "dwm",
        lambda: collect_dwm(errors, cim, processes.get("names") or []),
        {},
    )
    sections["power"] = _run_section(errors, "power", lambda: collect_power(errors, cim), {})
    sections["system"] = _run_section(errors, "system", lambda: collect_system(errors, cim), {})

    if args.no_boot_history:
        sections["boot_history"] = {"skipped": True, "reason": "--no-boot-history"}
    else:
        sections["boot_history"] = _run_section(
            errors, "boot_history", lambda: collect_boot_history(errors), {}
        )

    doc = build_document(errors, backends, sections, probes)

    out_dir = args.out_dir or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    out_path = write_report(doc, out_dir)

    if not args.quiet:
        print_summary(doc, out_path)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001 - fatal script error -> non-zero
        import traceback

        traceback.print_exc()
        sys.exit(1)
