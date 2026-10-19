#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_a1a2.py — ZC-GAP-P21 真机 A1/A2 验收（默认档 off / EnableGapProtection=1 on）

用法：
  python tools/gap_p21_a1a2.py --expect off      # A1：默认配置（ini 无键或缺键）
  python tools/gap_p21_a1a2.py --expect on       # A2：EnableGapProtection=1
  python tools/gap_p21_a1a2.py --expect forced-off-mp   # （可选）联机门禁档

流程：杀旧进程 → 记录日志水位 → ra2bench 启动（ra2loader.exe 注入 ra2render.dll）
      → 等 boot → ESC×2 过开场 → 抓 ra2render.log 追加段中的 GapProtection 行
      → ReadProcessMemory 读 @0x568271(2B)/0x568273(6B)/0x568279(2B)/0x56829A(7B)
      → 与磁盘 gamemd.exe 同偏移字节对拍 → 判 PASS/FAIL → 杀进程。
写作用域：仅 out/re_work/zcode_live/gap_p21/**（游戏目录只读，DLL/ini 由调用方装卸）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "tools"))
import bench_replay as B  # noqa: E402

GAME_DIR = PROJECT / "ra2bench"
LOG = GAME_DIR / "ra2render.log"
OUT_DIR = PROJECT / "out" / "re_work" / "zcode_live" / "gap_p21"

IMAGE_BASE = 0x00400000
# 待读窗口（VA）：窗前 cmp / 替换点 / 窗后 jl / 保留的 or
WINDOWS = [
    ("prev",  0x00568271, 2, "3B C3 (cmp eax,ebx)"),
    ("site",  0x00568273, 6, "89 99 34 01 00 00 -> 90 90 90 90 90 90"),
    ("next",  0x00568279, 2, "7C 14 (jl ...)"),
    ("keep",  0x0056829A, 7, "83 89 2C 01 00 00 10 (or [ecx+0x12C],0x10)"),
]


def read_window(proc: int, module_base: int) -> dict:
    out = {}
    for name, va, n, desc in WINDOWS:
        rva = va - IMAGE_BASE
        data = B.rpm(proc, module_base + rva, n)
        out[name] = {
            "va": f"0x{va:08X}", "rva": f"0x{rva:06X}", "expect_desc": desc,
            "mem": data.hex(" ").upper() if data else None,
        }
    return out


def disk_window() -> dict:
    exe = GAME_DIR / "gamemd.exe"
    with open(exe, "rb") as f:
        d = f.read()
    out = {}
    for name, va, n, desc in WINDOWS:
        rva = va - IMAGE_BASE
        out[name] = d[rva:rva + n].hex(" ").upper()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", required=True, choices=["off", "on", "forced-off-mp"])
    ap.add_argument("--boot-wait", type=float, default=24.0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = args.tag or datetime.now().strftime("%H%M%S")

    B.kill_game()
    time.sleep(1.0)
    log_mark = LOG.stat().st_size if LOG.exists() else 0

    # 启动（ra2loader.exe 注入 ra2render.dll；普通 Popen 可跨命令存活）
    exe = (GAME_DIR / "ra2loader.exe").resolve()
    subprocess.Popen([str(exe)], cwd=str(GAME_DIR),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pid, hwnd = None, None
    t_end = time.time() + 30
    while time.time() < t_end and not pid:
        pid = B.find_pid("gamemd.exe")
        time.sleep(0.5)
    if not pid:
        print("[FAIL] 30s 内未启动 gamemd.exe")
        return 2
    time.sleep(2.0)
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)
    print(f"[run] pid={pid} hwnd={hwnd} 等待 boot {args.boot_wait:.0f}s")
    time.sleep(args.boot_wait)

    # 过开场（ESC×2；失败不阻断 —— 补丁在 DLL_PROCESS_ATTACH 即装完）
    try:
        if hwnd:
            B.focus_game(hwnd)
            B.press_key(0x1B); time.sleep(1.2)
            B.press_key(0x1B); time.sleep(2.0)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] intro skip: {e}")

    # ---- 1) 日志判据 ----
    appended = b""
    if LOG.exists():
        with open(LOG, "rb") as f:
            f.seek(log_mark)
            appended = f.read()
    text = appended.decode("utf-8", "replace")
    gap_lines = [l for l in text.splitlines() if "GapProtection" in l or "GapProtect" in l]
    expect_line = {
        "off": "GapProtection=off",
        "on": "GapProtection=on",
        "forced-off-mp": "GapProtection=forced-off-mp",
    }[args.expect]
    log_ok = any(expect_line in l for l in gap_lines)

    # ---- 2) 内存字节判据 ----
    modules = B.list_modules(pid)
    mod = next(((n, b, s) for n, b, s in modules if n.lower() == "gamemd.exe"), None)
    proc = B.open_proc(pid)
    mem = read_window(proc, mod[1]) if mod else {}
    disk = disk_window()
    module_info = {"name": mod[0], "base": f"0x{mod[1]:08X}", "size": mod[2]} if mod else None

    site = mem.get("site", {}).get("mem")
    if args.expect == "on":
        bytes_ok = (site == "90 90 90 90 90 90")
    else:
        bytes_ok = (site == disk.get("site"))
    # 邻接窗无论开关都不得变化（与原盘一致）
    neighbors_ok = all(
        mem.get(k, {}).get("mem") == disk.get(k) for k in ("prev", "next", "keep")
    )

    ok = log_ok and bytes_ok and neighbors_ok
    result = {
        "task": "ZC-GAP-P21", "case": args.expect, "tag": tag,
        "game_dir": str(GAME_DIR), "pid": pid,
        "dll_sha256": subprocess.run(["sha256sum", str(GAME_DIR / "ra2render.dll")],
                                     capture_output=True, text=True).stdout.split()[0],
        "gamemd_sha256": subprocess.run(["sha256sum", str(GAME_DIR / "gamemd.exe")],
                                        capture_output=True, text=True).stdout.split()[0],
        "module": module_info,
        "log_mark": log_mark,
        "gap_log_lines": gap_lines,
        "log_ok": log_ok, "expect_log": expect_line,
        "mem": mem, "disk": disk,
        "bytes_ok": bytes_ok, "neighbors_ok": neighbors_ok,
        "verdict": "PASS" if ok else "FAIL",
    }
    out = OUT_DIR / f"a_{'1' if args.expect == 'off' else '2'}_{args.expect}_{tag}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("case", "log_ok", "bytes_ok", "neighbors_ok", "verdict")},
                     ensure_ascii=False))
    for l in gap_lines:
        print("  LOG:", l)
    for k in ("prev", "site", "next", "keep"):
        print(f"  {k:5s} mem={mem.get(k, {}).get('mem')} disk={disk.get(k)}")

    # 留一个截图存证（主菜单/开场态）
    try:
        if hwnd:
            shot = OUT_DIR / f"a_{'1' if args.expect == 'off' else '2'}_{args.expect}_{tag}.png"
            B.grab(hwnd, shot)
            print(f"[shot] {shot}")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] shot: {e}")

    B.kill_game()
    print(f"[json] {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
