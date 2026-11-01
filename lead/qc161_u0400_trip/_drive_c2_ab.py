#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C26-01 真机 A/B：c″ 候选件（RC4Guard=1，ExitBail 0/1）串行双臂 + 运行期布局取证。

★ 裁决依据（lead/codex_handoff_20261026/RULINGS.md C26-01）
  - 候选 DLL 完整 sha256 已核（edb9a0cde129c105…，工件门禁 14/14 已复跑，见 §438 前节）；
  - 串行顺序 CTRL 先（RC4Guard=1、ExitBail=0）→ MAIN 后（RC4Guard=1、ExitBail=1）；
  - 干跑字样不构成布局放行证据 ⇒ 本件用**独立进程旁路读**真实 .text 安装窗：
      站点 0x6BE0E1 的 6B hook 窗必须 == E9 rel32(指向 cave)+90，
      cave 基址处 36B 必须 == 规格字节按**实际 cave 地址**重算的镜像，
      且 0x6BE0E7 的原 je(74 F3) 在 hook 覆盖后**仍可读到**（死代码、不被 patch）——
    三者合起来 =「实际安装布局」证据（C26-01：DryRun 不算）。
  - 判据 v2（§434 三）：
      CTRL：期望僵尸（同窗不退）——CTRL 正常复现挂死=装置阳性，**不作为通过**；
      MAIN：WM_CLOSE 后 **20 s 内自然退出**、句柄可等待/退出码可读、
            无新增 #32770、except.txt 零新增、无 AV、母本指纹不变、残留=0；
      exitstate 允许 0→1 后恒 1 至终；不要求 1→2；强杀≠成功。

★ 纪律
  - 他线件（探针/gamemd 母本/loader/守卫母本 DLL）一字不改，sha 预检失败 ⇒ 不发射；
  - 载体/产物全落本线写域 lead/qc161_u0400_trip/c2ab/；趟内删 ct 树；
  - 母本零污染：gamemd 只 cp 进载体；ra2youli 不动；
  - gamemd stdio 敏感 ⇒ stdout/stderr=DEVNULL，零 PIPE；
  - 无调试器臂不产 dump（设计内：本趟判「退不退」+布局取证，崩溃现场已由 ab24 定谳）；
  - 全部 Win32 句柄声明 argtypes/restypes（x64 截断坑）。

★ 用法
  python _drive_c2_ab.py            # 预检（离线），不发射
  python _drive_c2_ab.py --live     # 真机串行：CTRL → MAIN（watch=150s/臂）
  python _drive_c2_ab.py --live --arms MAIN   # 只跑指定臂（逗号分隔 CTRL,MAIN）
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "c2ab"
THEIR = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
C2_DIR = ROOT / "lead/qc161_u0400_trip/d09a_c2_candidate"
SPEC_JSON = ROOT / "lead/qc161_u0400_trip/d09a_c2_patchspec.json"

GAMEMD_SHA16 = "73201cc021497c95"
LOADER_SHA16 = "ebddf6a61273c874"
THEIR_SHA16 = "b063052cd02df28c"
MOTHER_DLL_SHA16 = "0e2a9995ad71184c"
C2_DLL_SHA256 = "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"
CARRIER_PATH_MAX = 130

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
G_FRAME = 0x00A8ED84
BAIL_SITE = 0x006BE0E1
BAIL_LOOP = 0x006BE0DC
BAIL_EXIT = 0x006BE0E9
WM_CLOSE = 0x0010
WAIT_TIMEOUT, WAIT_OBJECT_0 = 258, 0

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.WaitForSingleObject.restype = wt.DWORD
k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.TerminateProcess.restype = wt.BOOL
k32.TerminateProcess.argtypes = [wt.HANDLE, ctypes.c_uint]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


class PMEMCT(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


psapi.GetProcessMemoryInfo.restype = wt.BOOL
psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMEMCT), wt.DWORD]
u32.PostMessageW.restype = wt.BOOL
u32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.IsWindowVisible.restype = wt.BOOL
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextW.restype = ctypes.c_int
u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetWindowRect.restype = wt.BOOL
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
ENUMPROC_T = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC_T, wt.LPARAM]

MOD = None  # 他线探针模块，main() 初始化（只读复用 list_procs/query_image/under_carrier）


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_their():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe", THEIR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# ini：三键全写（EnableRC4Guard / EnableRC4ExitBail / RC4GuardDryRun），回读验证。
# ★ 沿用 d09b 修复：只认**独占一行**的 [Logic] 节头（注释里的 [Logic] 会骗人）。
# ---------------------------------------------------------------------------
def write_keys(ini: Path, guard: int, bail: int, dry: int) -> None:
    want = {"EnableRC4Guard": guard, "EnableRC4ExitBail": bail, "RC4GuardDryRun": dry}
    lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip() == "[Logic]"), None)
    if idx is None:
        lines += ["", "[Logic]"] + ["%s=%d" % kv for kv in want.items()]
    else:
        end = next((j for j in range(idx + 1, len(lines))
                    if lines[j].strip().startswith("[")), len(lines))
        for k in range(idx + 1, end):
            for key in list(want):
                if lines[k].strip().startswith(key + "="):
                    lines[k] = "%s=%d" % (key, want.pop(key))
                    break
        for key, val in want.items():
            lines.insert(idx + 1, "%s=%d" % (key, val))
    ini.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    # ★ 回读验证：三键必须全部落在独占一行的 [Logic] 之后、下一节头之前
    chk = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(chk) if ln.strip() == "[Logic]"), None)
    if hi is None:
        raise RuntimeError("write_keys 回读失败：无 [Logic] 节头")
    sec = chk[hi + 1:]
    stop = next((i for i, ln in enumerate(sec) if ln.strip().startswith("[")), len(sec))
    body = sec[:stop]
    for key, val in {"EnableRC4Guard": guard, "EnableRC4ExitBail": bail, "RC4GuardDryRun": dry}.items():
        if not any(ln.strip() == "%s=%d" % (key, val) for ln in body):
            raise RuntimeError("write_keys 回读失败：%s=%d 未落在 [Logic] 节内" % (key, val))


def build_carrier(dst: Path, dll_name: str, guard: int, bail: int, dry: int) -> int:
    dst.mkdir(parents=True, exist_ok=False)
    n = 0
    for f in sorted(GAME_SRC.iterdir()):
        if f.is_file():
            shutil.copy2(f, dst / f.name)
            n += 1
    shutil.copy2(GUARD_DIR / "rc4_loader.exe", dst / "rc4_loader.exe")
    shutil.copy2(C2_DIR / "ra2rc4guard_c2.dll", dst / dll_name)
    write_keys(dst / "ra2render.ini", guard, bail, dry)
    return n


# ---------------------------------------------------------------------------
# 独立进程旁路读（布局取证用；与 sample_loop 的 h 句柄独立）
# ---------------------------------------------------------------------------
def rpm(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), ctypes.cast(buf, ctypes.c_void_p),
                               size, ctypes.byref(got))
    return (buf.raw[:got.value] if ok else None)


def rpm_u32(h, addr):
    raw = rpm(h, addr, 4)
    return struct.unpack("<I", raw)[0] if raw is not None else None


def read_cave_hex(h, base):
    raw = rpm(h, base, 36)
    return raw.hex() if raw is not None else None


def bail_hook_expect(cave_base):
    rel = cave_base - (BAIL_SITE + 5)
    if not (-2**31 <= rel <= 2**31 - 1):
        return None
    return (b"\xE9" + struct.pack("<i", rel) + b"\x90").hex()


def mirror_cave(base):
    """BuildExitBailCave 的 Python 镜像（36B；与 _verify_c2_candidate.mirror_cave 同构，
    但这里输入=**实际** cave 基址，输出用于比对运行期读到字节）。"""
    o = bytearray()
    o += b"\xA1\x50\x35\xB7\x00"
    o += b"\x85\xC0"
    o += b"\x0F\x84" + struct.pack("<i", BAIL_EXIT - (base + len(o) + 6))
    o += b"\x83\x3D\xD8\xED\xA8\x00\x01"
    o += b"\x0F\x85" + struct.pack("<i", BAIL_EXIT - (base + len(o) + 6))
    o += b"\xE9" + struct.pack("<i", BAIL_LOOP - (base + len(o) + 5))
    o += b"\xE9" + struct.pack("<i", BAIL_EXIT - (base + len(o) + 5))
    return o.hex()


def working_set_kb(h):
    m = PMEMCT()
    m.cb = ctypes.sizeof(m)
    if not psapi.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb):
        return None
    return m.WorkingSetSize // 1024 if m.WorkingSetSize else None


def enum_windows_for(pid):
    wins = []

    def _cb(hwnd, _):
        w = wt.DWORD(0)
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
        if w.value != pid:
            return True
        buf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls, 256)
        r = wt.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        wins.append({"hwnd": hwnd, "title": buf.value, "class": cls.value,
                     "visible": bool(u32.IsWindowVisible(hwnd)),
                     "rect": [r.left, r.top, r.right, r.bottom]})
        return True

    u32.EnumWindows(ENUMPROC_T(_cb), 0)
    return wins


def find_game_window(pid):
    for w in enum_windows_for(pid):
        if w["class"] == "Yuri's Revenge" and "#32770" not in (w["title"] or ""):
            return w
    return None


def sample_loop(h, pid, t_end, period=0.1):
    rows, seen = [], None
    while time.time() < t_end:
        res = k32.WaitForSingleObject(h, 0)
        alive = (res == WAIT_TIMEOUT)
        ex = wt.DWORD(0)
        k32.GetExitCodeProcess(h, ctypes.byref(ex))
        r = {"t": round(time.time(), 3), "wait_res": res,
             "exitcode": ex.value if res == WAIT_OBJECT_0 else None,
             "singleton": rpm_u32(h, G_SINGLETON),
             "hwnd_glob": rpm_u32(h, G_HWND),
             "exitstate": rpm_u32(h, G_EXITSTATE),
             "frame": rpm_u32(h, G_FRAME),
             "ws_kb": working_set_kb(h) if alive else None}
        if alive:
            wins = enum_windows_for(pid)
            key = tuple(sorted((w["hwnd"], w["title"]) for w in wins))
            if key != seen:
                r["windows"] = wins
                seen = key
        rows.append(r)
        if res == WAIT_OBJECT_0:
            break
        time.sleep(period)
    return rows


# ---------------------------------------------------------------------------
# 布局取证：在**存活进程**里读 bail 站点 hook 窗 + 按日志 cave 基址读 36B 并重算镜像
# ---------------------------------------------------------------------------
def capture_layout(pid, guard_lines, bail_enabled):
    """返回 dict：
      ok=True 当且仅当 (hook 窗 == 期望 E9+90) 且 (cave 36B == 实际基址重算镜像)
      且 (0x6BE0E7 的 74 F3 仍在，未被覆盖)。bail_enabled=False 时要求 hook 窗=原字节。"""
    out = {"requested": bool(bail_enabled)}
    hh = k32.OpenProcess(0x0400 | 0x0010, False, pid)  # QUERY|VM
    if not hh:
        out["ok"] = False
        out["err"] = "OpenProcess_failed err=%d" % ctypes.get_last_error()
        return out
    try:
        hook_raw = rpm(hh, BAIL_SITE, 6)
        dead_raw = rpm(hh, BAIL_SITE + 6, 2)   # 0x6BE0E7 原 je = 74 F3（不被 patch）
        out["hook_win_hex"] = hook_raw.hex() if hook_raw else None
        out["dead_je_hex"] = dead_raw.hex() if dead_raw else None
        # 日志里找 bail cave 基址：[ra2rc4exitbail] 已装 1/1（cave 0xXXXXXXXX；…
        # ★ 十六进制后紧跟**全角**分号 ⇒ 不能 split(" ")，用正则只取 hex 位。
        cave_base = None
        for l in guard_lines or []:
            if "[ra2rc4exitbail]" in l and "已装 1/1" in l:
                m = re.search(r"cave 0x([0-9A-Fa-f]{1,8})", l)
                if m:
                    cave_base = int(m.group(1), 16)
                break
        out["cave_base_from_log"] = hex(cave_base) if cave_base else None
        if bail_enabled:
            if cave_base is None:
                out["ok"] = False
                out["err"] = "no_cave_base_in_log"
                return out
            cave_hex = read_cave_hex(hh, cave_base)
            out["cave_36b_hex"] = cave_hex
            out["cave_expect_hex"] = mirror_cave(cave_base)
            out["hook_expect_hex"] = bail_hook_expect(cave_base)
            ok_hook = (hook_raw is not None and hook_raw.hex() == out["hook_expect_hex"])
            ok_cave = (cave_hex == out["cave_expect_hex"])
            ok_dead = (dead_raw == b"\x74\xF3")
            out["ok"] = bool(ok_hook and ok_cave and ok_dead)
            out["checks"] = {"hook_win": ok_hook, "cave_36b": ok_cave, "dead_je_kept": ok_dead}
        else:
            # CTRL 臂：bail 关 ⇒ 站点必须保持原字节 39 3D D8 ED A8 00，je 74 F3 仍在
            orig6 = bytes.fromhex("393dd8eda800")
            out["ok"] = bool(hook_raw == orig6 and dead_raw == b"\x74\xF3")
            out["checks"] = {"site_untouched": hook_raw == orig6, "orig_je_kept": dead_raw == b"\x74\xF3"}
        return out
    finally:
        k32.CloseHandle(hh)


def _cleanup(proc, carrier, rec):
    try:
        logf = carrier / "ra2render.log"
        if logf.exists():
            out_dir = Path(rec.get("out_dir") or ".")
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logf, out_dir / "ra2render.log")
            rec["guard_lines"] = [l for l in (out_dir / "ra2render.log")
                                  .read_text(encoding="utf-8", errors="replace").splitlines()
                                  if "[ra2rc4" in l]
    except Exception as e:
        rec["guard_log_copy_err"] = repr(e)
    for p, nm in list(MOD.list_procs().items()):
        if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                hh = k32.OpenProcess(0x0001 | 0x100000, False, p)  # Terminate|Synchronize
                if hh:
                    k32.TerminateProcess(hh, 1)
                    k32.CloseHandle(hh)
                    rec.setdefault("killed_on_cleanup", []).append([p, nm])
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    deadline = time.time() + 3.0
    while time.time() < deadline:
        rem = [p for p, nm in MOD.list_procs().items()
               if nm.lower() in ("gamemd.exe", "rc4_loader.exe")
               and (MOD.query_image(p) or "").lower().startswith(str(carrier).lower())]
        if not rem:
            break
        time.sleep(0.25)
    rec["a8_remaining"] = rem
    rec["a8_enum_ok"] = os.getpid() in MOD.list_procs()
    rec["a8_verdict"] = "PASS" if (not rem and rec["a8_enum_ok"]) else "V_FAIL"
    for _att in range(6):
        shutil.rmtree(carrier.parent, ignore_errors=True)
        if not carrier.parent.exists():
            break
        time.sleep(0.5)
    rec["carrier_deleted"] = not carrier.parent.exists()


def run_trip(tag, guard, bail, dry, watch_s=150.0, hold_s=6.0):
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = MYCARD / ("%s_%s" % (stamp, tag))
    carrier = out_dir / "ct" / ("c" + "0" * 10)
    rec = {"tag": tag, "guard_enable": guard, "exitbail_enable": bail, "dry_run": dry,
           "attach_debugger": False, "carrier_len": len(str(carrier)), "out_dir": str(out_dir)}
    if rec["carrier_len"] > CARRIER_PATH_MAX:
        rec["abort"] = "carrier_path_too_long"
        return rec
    out_dir.mkdir(parents=True, exist_ok=True)

    dll_name = "ra2rc4guard_c2.dll"
    rec["carrier_files"] = build_carrier(carrier, dll_name, guard, bail, dry)
    rec["gamemd_sha16"] = sha16(carrier / "gamemd.exe")
    rec["c2_dll_sha256_in_carrier"] = hashlib.sha256((carrier / dll_name).read_bytes()).hexdigest()
    if rec["gamemd_sha16"] != GAMEMD_SHA16:
        rec["abort"] = "gamemd_sha_mismatch"
        _cleanup(None, carrier, rec)
        return rec
    if rec["c2_dll_sha256_in_carrier"] != C2_DLL_SHA256:
        rec["abort"] = "c2_dll_sha_mismatch"
        _cleanup(None, carrier, rec)
        return rec

    ex_path = carrier / "except.txt"
    rec["except_before"] = sha16(ex_path) if ex_path.exists() else None

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), dll_name],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["loader_pid"] = proc.pid
    t_launch = time.time()

    pid = None
    for _ in range(150):
        time.sleep(0.1)
        for p, nm in MOD.list_procs().items():
            if nm.lower() != "gamemd.exe":
                continue
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                pid = p
                break
        if pid:
            break
    if pid is None:
        rec["abort"] = "gamemd_not_found_under_carrier"
        _cleanup(proc, carrier, rec)
        return rec
    rec["gamemd_pid"] = pid

    win = None
    while time.time() - t_launch < 40.0:
        win = find_game_window(pid)
        if win:
            break
        time.sleep(0.5)
    rec["game_window_s"] = round(time.time() - t_launch, 2)
    rec["game_window"] = bool(win)
    if not win:
        rec["abort"] = "no_game_window_40s"
        _cleanup(proc, carrier, rec)
        return rec

    time.sleep(hold_s)

    # ★ 布局取证 #1：关窗前（进程活、守卫应已装）——对 CTRL 臂=站点原样对照
    log_lines = []
    if (carrier / "ra2render.log").exists():
        log_lines = [l for l in (carrier / "ra2render.log").read_text(
            encoding="utf-8", errors="replace").splitlines() if "[ra2rc4" in l]
    rec["layout_pre_close"] = capture_layout(pid, log_lines, bail_enabled=bool(bail))

    pre_wins = {w["hwnd"]: w["title"] for w in enum_windows_for(pid)}
    u32.PostMessageW(wt.HWND(win["hwnd"]), WM_CLOSE, 0, 0)
    t_close = time.time()
    rec["closed_at_s"] = round(t_close - t_launch, 3)

    h = k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)  # QUERY|VM|SYNCHRONIZE
    if not h:
        rec["abort"] = "OpenProcess_failed err=%d" % ctypes.get_last_error()
        _cleanup(proc, carrier, rec)
        return rec
    try:
        rows = sample_loop(h, pid, t_close + watch_s, period=0.1)
    finally:
        k32.CloseHandle(h)
    rec["n_sample"] = len(rows)
    rec["wait_failed_rows"] = sum(1 for r in rows if r["wait_res"] not in (WAIT_TIMEOUT, WAIT_OBJECT_0))
    rec["sample_head"] = rows[:5]
    rec["sample_tail"] = rows[-15:]

    exit_row = next((r for r in rows if r["wait_res"] == WAIT_OBJECT_0), None)
    rec["exited_within_watch"] = exit_row is not None
    rec["exit_after_close_s"] = round(exit_row["t"] - t_close, 2) if exit_row else None
    rec["exited_within_20s"] = (rec["exit_after_close_s"] is not None
                                and rec["exit_after_close_s"] <= 20.0)
    rec["final_exitcode"] = exit_row["exitcode"] if exit_row else None

    def traj(key):
        vs = [(round(r["t"] - t_close, 2), r[key]) for r in rows if r.get(key) is not None]
        return {"first": vs[0] if vs else None, "last": vs[-1] if vs else None,
                "distinct_n": len(set(v for _t, v in vs))}
    for out_key, row_key in (("traj_frame", "frame"), ("traj_exitstate", "exitstate"),
                             ("traj_singleton", "singleton"), ("traj_ws", "ws_kb")):
        rec[out_key] = traj(row_key)

    new_wins = {}
    for r in rows:
        for w in (r.get("windows") or []):
            if w["visible"] and w["hwnd"] != win["hwnd"] and w["hwnd"] not in pre_wins:
                new_wins[w["hwnd"]] = {"title": w["title"], "class": w["class"], "rect": w["rect"]}
    rec["extra_windows_after_close"] = list(new_wins.values())

    if (carrier / "except.txt").exists():
        rec["except_after"] = sha16(carrier / "except.txt")
        rec["except_changed"] = rec["except_after"] != rec["except_before"]

    # ★ 布局取证 #2：关窗后（进程若仍活再读一次，看 hook 窗状态；若已退记 None）
    if exit_row is None:
        hh = k32.OpenProcess(0x0400, False, pid)
        if hh:
            log_lines2 = []
            if (carrier / "ra2render.log").exists():
                log_lines2 = [l for l in (carrier / "ra2render.log").read_text(
                    encoding="utf-8", errors="replace").splitlines() if "[ra2rc4" in l]
            rec["layout_post_close_alive"] = capture_layout(pid, log_lines2, bail_enabled=bool(bail))
            k32.CloseHandle(hh)

    _cleanup(proc, carrier, rec)
    return rec


ARMS = {
    "CTRL": dict(guard=1, bail=0, dry=0, note="RC4Guard=1 / ExitBail=0 ⇒ 预期僵尸=装置阳性"),
    "MAIN": dict(guard=1, bail=1, dry=0, note="RC4Guard=1 / ExitBail=1 ⇒ 预期 20s 内自然退出"),
}


def main() -> int:
    global MOD
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--watch", type=float, default=150.0)
    ap.add_argument("--arms", default="CTRL,MAIN")
    a = ap.parse_args()
    MOD = load_their()

    print("=" * 78)
    print("C26-01 c″ 真机 A/B（CTRL 先 → MAIN 后） live=%s watch=%.0fs" % (a.live, a.watch))
    print("=" * 78)

    fails = []

    def pre(name, ok, detail=""):
        print("  [%s] %-44s %s" % ("OK" if ok else "RED", name, detail))
        if not ok:
            fails.append(name)

    pre("他线探针未改", sha16(THEIR) == THEIR_SHA16, sha16(THEIR))
    pre("gamemd 母本 sha", sha16(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16, sha16(GAME_SRC / "gamemd.exe"))
    pre("守卫母本 DLL sha", sha16(GUARD_DIR / "ra2rc4guard.dll") == MOTHER_DLL_SHA16, sha16(GUARD_DIR / "ra2rc4guard.dll"))
    pre("loader sha", sha16(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16, sha16(GUARD_DIR / "rc4_loader.exe"))
    pre("c″ 候选 DLL sha256（完整）",
        hashlib.sha256((C2_DIR / "ra2rc4guard_c2.dll").read_bytes()).hexdigest() == C2_DLL_SHA256,
        C2_DLL_SHA256[:16] + "…")
    pre("patchspec 在盘", SPEC_JSON.is_file(), str(SPEC_JSON))
    pre("游戏源 88 件", len([f for f in GAME_SRC.iterdir() if f.is_file()]) == 88, "")
    pre("残留游戏进程=0", not MOD.game_procs(), str(MOD.game_procs()))
    if fails:
        print("!! 预检 %d 项红，不发射" % len(fails))
        return 2
    if not a.live:
        print("\n★ 预检全过；加 --live 发射（CTRL→MAIN 串行）。")
        return 0

    MYCARD.mkdir(parents=True, exist_ok=True)
    results = []
    for arm in [x.strip() for x in a.arms.split(",")]:
        cfg = ARMS[arm]
        print("\n" + "-" * 78)
        print("[臂 %s] %s" % (arm, cfg["note"]))
        t0 = time.time()
        r = run_trip(arm + "_c2", cfg["guard"], cfg["bail"], cfg["dry"], watch_s=a.watch)
        r["wall_s"] = round(time.time() - t0, 1)
        results.append(r)
        lp = r.get("layout_pre_close") or {}
        print("   exited=%s within20=%s after=%s code=%s newwins=%s a8=%s layout_ok=%s abort=%s"
              % (r.get("exited_within_watch"), r.get("exited_within_20s"),
                 r.get("exit_after_close_s"), r.get("final_exitcode"),
                 len(r.get("extra_windows_after_close") or []), r.get("a8_verdict"),
                 lp.get("ok"), r.get("abort")))
        try:
            Path(r["out_dir"]).mkdir(parents=True, exist_ok=True)
            (Path(r["out_dir"]) / "_rec.json").write_text(
                json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:
            print("   !! _rec 落盘失败:", repr(e))
        leftover = MOD.game_procs()
        if leftover:
            r["leftover_between"] = leftover
            print("   !! 臂间残留 %s ⇒ 停后续" % leftover)
            break

    (MYCARD / "c2ab_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + "=" * 78)
    for r in results:
        lp = r.get("layout_pre_close") or {}
        print("  %-14s guard=%s bail=%s exited=%-5s w20=%-5s after=%-7s layout=%-5s a8=%s abort=%s"
              % (r.get("tag"), r.get("guard_enable"), r.get("exitbail_enable"),
                 r.get("exited_within_watch"), r.get("exited_within_20s"),
                 r.get("exit_after_close_s"), lp.get("ok"), r.get("a8_verdict"), r.get("abort")))
    print("残留:", MOD.game_procs() or "0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
