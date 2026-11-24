# -*- coding: utf-8 -*-
"""W93 只读自检脚本：校验运行中目标进程内的 cnc-ddraw 限帧全局状态。

用途：
    给定目标 PID，进程外只读枚举 ddraw.dll 基址（兼容 ASLR/DYNAMICBASE），
    dump RVA 0x5EE30..0x5EE70 共 16 个 DWORD（对应 DEVMODEA 尾部及紧邻指针），
    并校验限帧相关全局：
      - [base + 0x594E8] maxfps            期望 60（容差 ±0）
      - [base + 0x5F128] interval (ms)     期望 16（容差 ±0；可通过 --interval-tol 放宽至 ±1）
      - [base + 0x5EE48] dmDisplayFrequency 期望等于当前 EnumDisplaySettingsA 刷新率
                                            （本机实测 210 Hz；若 API 失败则兜底 60，容差 ±0）

脚本性质：仅 OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) + ReadProcessMemory，
不启动游戏、不注入、不写目标内存。任何读取或断言失败都会打印原始字节并干净退出，不崩溃。
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys
from typing import Dict, List, Optional, Tuple

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
LIST_MODULES_ALL = 0x03
ENUM_CURRENT_SETTINGS = -1

RVA_MAXFPS = 0x594E8
RVA_INTERVAL = 0x5F128
RVA_LAST_T = 0x5F120
RVA_CUR_T = 0x5F124
RVA_CLAMP_FREQ = 0x5EE48
RVA_DUMP_START = 0x5EE30
DUMP_DWORDS = 16  # 0x5EE30..0x5EE6C (覆盖 0x5EE30..0x5EE70 共 64 字节)

DUMP_FIELD_NAMES: Dict[int, str] = {
    0x5EE30: "DEVMODEA+0x60 (dmPanningWidth/unused)",
    0x5EE34: "DEVMODEA+0x64 (dmPanningHeight/unused)",
    0x5EE38: "DEVMODEA.dmBitsPerPel (+0x68)",
    0x5EE3C: "DEVMODEA.dmPelsWidth (+0x6C)",
    0x5EE40: "DEVMODEA.dmPelsHeight (+0x70)",
    0x5EE44: "DEVMODEA.dmDisplayFlags (+0x74)",
    0x5EE48: "DEVMODEA.dmDisplayFrequency (+0x78) [原误称clamp]",
    0x5EE4C: "DEVMODEA+0x7C (dmICMMethod)",
    0x5EE50: "DEVMODEA+0x80 (dmICMIntent)",
    0x5EE54: "DEVMODEA+0x84 (dmMediaType)",
    0x5EE58: "DEVMODEA+0x88 (dmDitherType)",
    0x5EE5C: "DEVMODEA+0x8C (dmReserved1)",
    0x5EE60: "DEVMODEA+0x90 (dmReserved2)",
    0x5EE64: "DEVMODEA+0x94 (dmPanningWidth)",
    0x5EE68: "DEVMODEA+0x98 (dmPanningHeight)",
    0x5EE6C: "renderer_ctx_ptr (紧随 DEVMODEA 之后)",
}


class _DEVMODEA(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_char * 32),
        ("dmSpecVersion", wt.WORD),
        ("dmDriverVersion", wt.WORD),
        ("dmSize", wt.WORD),
        ("dmDriverExtra", wt.WORD),
        ("dmFields", wt.DWORD),
        ("dmUnused", ctypes.c_byte * 60),
        ("dmBitsPerPel", wt.DWORD),
        ("dmPelsWidth", wt.DWORD),
        ("dmPelsHeight", wt.DWORD),
        ("dmDisplayFlags", wt.DWORD),
        ("dmDisplayFrequency", wt.DWORD),
        ("dmTail", ctypes.c_byte * 32),
    ]


def query_os_display_mode() -> Optional[Tuple[int, int, int, int]]:
    """只读调用 USER32!EnumDisplaySettingsA 获取当前显示器宽/高/色深/刷新率。"""
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.EnumDisplaySettingsA.argtypes = [wt.LPCSTR, wt.DWORD, ctypes.POINTER(_DEVMODEA)]
        user32.EnumDisplaySettingsA.restype = wt.BOOL
        dm = _DEVMODEA()
        dm.dmSize = ctypes.sizeof(_DEVMODEA)
        if not user32.EnumDisplaySettingsA(None, wt.DWORD(ENUM_CURRENT_SETTINGS), ctypes.byref(dm)):
            return None
        return int(dm.dmPelsWidth), int(dm.dmPelsHeight), int(dm.dmBitsPerPel), int(dm.dmDisplayFrequency)
    except Exception:
        return None


def _setup_winapi():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    k32.ReadProcessMemory.argtypes = [
        wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    k32.ReadProcessMemory.restype = wt.BOOL
    psapi.EnumProcessModulesEx.argtypes = [
        wt.HANDLE, ctypes.POINTER(ctypes.c_void_p), wt.DWORD, ctypes.POINTER(wt.DWORD), wt.DWORD
    ]
    psapi.EnumProcessModulesEx.restype = wt.BOOL
    psapi.GetModuleFileNameExW.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.LPWSTR, wt.DWORD]
    psapi.GetModuleFileNameExW.restype = wt.DWORD
    return k32, psapi


def find_module_base(k32, psapi, hproc, module_name: str) -> Optional[int]:
    needle = module_name.lower()
    needed = wt.DWORD(0)
    if not psapi.EnumProcessModulesEx(hproc, None, 0, ctypes.byref(needed), LIST_MODULES_ALL):
        return None
    ptr_size = ctypes.sizeof(ctypes.c_void_p)
    count = max(1, needed.value // ptr_size)
    arr = (ctypes.c_void_p * count)()
    if not psapi.EnumProcessModulesEx(hproc, arr, ctypes.sizeof(arr), ctypes.byref(needed), LIST_MODULES_ALL):
        return None
    count = min(count, needed.value // ptr_size)
    buf = ctypes.create_unicode_buffer(512)
    for i in range(count):
        if arr[i] is None:
            continue
        psapi.GetModuleFileNameExW(hproc, ctypes.c_void_p(arr[i]), buf, 512)
        if os.path.basename(buf.value).lower() == needle:
            return int(arr[i])
    return None


def rpm_bytes(k32, hproc, addr: int, size: int) -> Tuple[Optional[bytes], int]:
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size, ctypes.byref(got))
    err = ctypes.get_last_error()
    if not ok or got.value != size:
        return (buf.raw[: got.value] if got.value > 0 else None), err
    return buf.raw, 0


def format_hex_bytes(b: Optional[bytes]) -> str:
    if b is None:
        return "<READ_FAILED>"
    return " ".join(f"{x:02X}" for x in b)


def check_globals(
    base: int,
    dump_5ee30: Optional[bytes],
    maxfps_b: Optional[bytes],
    interval_b: Optional[bytes],
    last_t_b: Optional[bytes],
    cur_t_b: Optional[bytes],
    expect_maxfps: int,
    expect_interval: int,
    interval_tol: int,
    expect_hz: int,
    hz_tol: int,
    os_mode: Optional[Tuple[int, int, int, int]],
) -> Tuple[bool, List[str]]:
    """纯函数校验与格式化输出（便于离线单元测试与真机共用）。"""
    lines: List[str] = []
    ok = True

    lines.append(f"[BASE] ddraw.dll = 0x{base:08X}")
    if os_mode is not None:
        lines.append(
            f"[OS-DISPLAY] EnumDisplaySettingsA: {os_mode[0]}x{os_mode[1]} @ {os_mode[2]}bpp, {os_mode[3]} Hz"
        )
    else:
        lines.append("[OS-DISPLAY] EnumDisplaySettingsA: <unavailable> (期望值兜底 60 Hz)")

    lines.append("")
    lines.append(f"=== Dump RVA 0x{RVA_DUMP_START:05X}..0x{RVA_DUMP_START + DUMP_DWORDS * 4:05X} ({DUMP_DWORDS} DWORDs) ===")
    if dump_5ee30 is None or len(dump_5ee30) < DUMP_DWORDS * 4:
        lines.append(f"[FAIL] dump 0x{RVA_DUMP_START:05X} 读取失败，已读字节: {format_hex_bytes(dump_5ee30)}")
        ok = False
        freq_val = None
    else:
        for i in range(DUMP_DWORDS):
            rva = RVA_DUMP_START + i * 4
            chunk = dump_5ee30[i * 4 : (i + 1) * 4]
            uval = struct.unpack_from("<I", chunk, 0)[0]
            sval = struct.unpack_from("<i", chunk, 0)[0]
            label = DUMP_FIELD_NAMES.get(rva, "")
            lines.append(
                f"  +0x{rva:05X} (0x{base + rva:08X})  [{format_hex_bytes(chunk)}]  u32={uval:10d} (0x{uval:08X}, i32={sval})  {label}"
            )
        freq_val = struct.unpack_from("<I", dump_5ee30, (RVA_CLAMP_FREQ - RVA_DUMP_START))[0]

    lines.append("")
    lines.append("=== 关键全局断言 ===")

    def _eval_i32(name: str, rva: int, raw: Optional[bytes], expected: int, tol: int) -> None:
        nonlocal ok
        if raw is None or len(raw) < 4:
            lines.append(f"  [FAIL] {name} (+0x{rva:05X}): 读取失败 raw=[{format_hex_bytes(raw)}], 期望 {expected}±{tol}")
            ok = False
            return
        val = struct.unpack_from("<i", raw, 0)[0]
        passed = abs(val - expected) <= tol
        status = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        lines.append(
            f"  [{status}] {name} (+0x{rva:05X}): 实测={val} raw=[{format_hex_bytes(raw)}], 期望={expected} (容差 ±{tol})"
        )

    _eval_i32("maxfps", RVA_MAXFPS, maxfps_b, expect_maxfps, 0)
    _eval_i32("interval_ms", RVA_INTERVAL, interval_b, expect_interval, interval_tol)
    freq_raw = (
        dump_5ee30[RVA_CLAMP_FREQ - RVA_DUMP_START : RVA_CLAMP_FREQ - RVA_DUMP_START + 4]
        if dump_5ee30 is not None and len(dump_5ee30) >= (RVA_CLAMP_FREQ - RVA_DUMP_START + 4)
        else None
    )
    _eval_i32("dmDisplayFrequency", RVA_CLAMP_FREQ, freq_raw, expect_hz, hz_tol)

    for label, rva, raw in (("last_t", RVA_LAST_T, last_t_b), ("cur_t", RVA_CUR_T, cur_t_b)):
        if raw is None or len(raw) < 4:
            lines.append(f"  [INFO] {label} (+0x{rva:05X}): 读取失败 raw=[{format_hex_bytes(raw)}]")
        else:
            uval = struct.unpack_from("<I", raw, 0)[0]
            lines.append(f"  [INFO] {label} (+0x{rva:05X}): u32={uval} raw=[{format_hex_bytes(raw)}]")

    return ok, lines


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="只读自检运行中进程内 cnc-ddraw (ddraw.dll) 的限帧全局与 DEVMODEA 刷新率字段。"
    )
    p.add_argument("pid", type=int, help="目标进程 PID（如运行中的 gamemd.exe）")
    p.add_argument("--module", default="ddraw.dll", help="模块名（默认 ddraw.dll）")
    p.add_argument("--expect-maxfps", type=int, default=60, help="期望 [base+0x594E8] maxfps 值（默认 60，容差 ±0）")
    p.add_argument("--expect-interval", type=int, default=16, help="期望 [base+0x5F128] interval 值 ms（默认 16）")
    p.add_argument("--interval-tol", type=int, default=0, help="interval 容差 ms（默认 0 严格相等；如需兼容 15..17 可设为 1）")
    p.add_argument(
        "--expect-hz",
        type=int,
        default=None,
        help="期望 [base+0x5EE48] dmDisplayFrequency（默认自动读取当前系统 EnumDisplaySettingsA 刷新率，失败时兜底 60）",
    )
    p.add_argument("--hz-tol", type=int, default=0, help="dmDisplayFrequency 容差 Hz（默认 0）")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    os_mode = query_os_display_mode()
    expect_hz = args.expect_hz if args.expect_hz is not None else (os_mode[3] if os_mode is not None else 60)

    k32, psapi = _setup_winapi()
    hproc = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, args.pid)
    if not hproc:
        err = ctypes.get_last_error()
        print(f"[FATAL] OpenProcess(pid={args.pid}) 失败 WinError={err}（请确认 PID 存在且权限足够）", file=sys.stderr)
        return 2

    try:
        base = find_module_base(k32, psapi, hproc, args.module)
        if not base:
            err = ctypes.get_last_error()
            print(f"[FATAL] 进程 pid={args.pid} 未加载模块 {args.module!r} (WinError={err})", file=sys.stderr)
            return 2

        dump_b, err_d = rpm_bytes(k32, hproc, base + RVA_DUMP_START, DUMP_DWORDS * 4)
        maxfps_b, err_m = rpm_bytes(k32, hproc, base + RVA_MAXFPS, 4)
        interval_b, err_i = rpm_bytes(k32, hproc, base + RVA_INTERVAL, 4)
        last_t_b, _ = rpm_bytes(k32, hproc, base + RVA_LAST_T, 4)
        cur_t_b, _ = rpm_bytes(k32, hproc, base + RVA_CUR_T, 4)

        if any(e != 0 for e in (err_d, err_m, err_i)):
            print(f"[WARN] ReadProcessMemory 存在部分读取错误: dump_err={err_d}, maxfps_err={err_m}, interval_err={err_i}")

        ok, lines = check_globals(
            base=base,
            dump_5ee30=dump_b,
            maxfps_b=maxfps_b,
            interval_b=interval_b,
            last_t_b=last_t_b,
            cur_t_b=cur_t_b,
            expect_maxfps=args.expect_maxfps,
            expect_interval=args.expect_interval,
            interval_tol=args.interval_tol,
            expect_hz=expect_hz,
            hz_tol=args.hz_tol,
            os_mode=os_mode,
        )
        for ln in lines:
            print(ln)
        return 0 if ok else 1
    finally:
        k32.CloseHandle(hproc)


if __name__ == "__main__":
    sys.exit(main())
