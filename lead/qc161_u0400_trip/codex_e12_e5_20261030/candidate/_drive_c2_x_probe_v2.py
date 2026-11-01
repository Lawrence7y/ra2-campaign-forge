#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C26-08 修订候选 v2（替代 _drive_c2_x_probe.py；原件留作快照，本版逐条关闭 9 项实现阻断）。

★ REVIEW_S439_X_LAUNCH_GATE.md 映射（G-1..G-9，全部经 --faulttest 替身覆盖，零真启动）：
  G-1 载体目录先建后拷，建后断言空
  G-2 fire_arm 恒返回单个 dict；main 直接收 dict（FT1 协议测试）
  G-3 --live 与离线**都**先跑 preflight；发射前每臂再复验 sha；harness7/探针钉批准指纹
  G-4 桌面截屏**实现**（GDI 屏 DC BitBlt，h7 同纪律）；tick[0xA8ED80]/ws 进 sentinels；
      UI 记录=截图+窗口枚举双通道（不再拿枚举代替游戏内绘制 UI）
  G-5 收尾两阶段：证据尽力 + 清扫保证（finally）；阶段异常→verdict=FAIL，不被 PASS 覆盖
  G-6 终态两时点：close_last + after_kill（强杀/等待后再读日志/except），迟到终态不丢
  G-7 删除边界：carrier_identity_ok（resolve 无重解析 ∧ 在批准根 ∧ 无存活进程）；
      rmtree **不** ignore_errors；残留>0 或身份不符 ⇒ 保留载体报 delete_reason（不无条件删）
  G-8 菜单臂独立时序：P3m 不跑战斗窗，走「菜单就绪闸」（frame==0∧singleton≠0∧hwnd≠0 连续3样本）
      +可核对时长 menu_ready_s；与旧 d09b hold=6s 臂差异如实记
  G-9 硬停：投递失败/OpenProcess/Wait 失败/窗口身份不符/零 close 样本 ⇒ verdict=FAIL+停后续；
      ctypes 一律 set_last_error(0)+get_last_error；三态=ok / read_fail(err,mbi) / page_absent，
      299 经 VirtualQueryEx 补证后才区分「页不存在」vs「读失败」（FT6）

★ 纪律（承 C26-06）：不新增 Hook、不写退出状态、不点确认、不丢存档、不碰冻结 harness；
  线程挂起/EIP 快照**不在本版**（若需=侵入性单列再裁，REVIEW C26-06 末条）。
★ 静态链口径（C26-07）：本件只取证，**不预设**「宿主未进入 / c″ 必未达 / 全局归零即可二分」；
  post-close 全量落 timeline.json（杜绝「只存末 6 行」再犯）。

用法：
  python _drive_c2_x_probe_v2.py               # 预检（只读，不发射）
  python _drive_c2_x_probe_v2.py --faulttest   # ★ 故障注入离线测试（替身 OS，禁真启动游戏）
  python _drive_c2_x_probe_v2.py --live ...    # 仍被硬闸拦：需 APPROVED_THIS_ROUND=True（本轮永假）
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import itertools
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "c2ab_x"
APPROVED_CT_ROOT = MYCARD
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
C2_DIR = ROOT / "lead/qc161_u0400_trip/d09a_c2_candidate"
H7_PATH = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
THEIR_PROBE = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"

GAMEMD_SHA16 = "73201cc021497c95"
LOADER_SHA16 = "ebddf6a61273c874"
C2_DLL_SHA256 = "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"
H7_SHA16 = "d019e8beecfb5fd8"
PROBE_SHA16 = "b063052cd02df28c"
SRC_FILE_COUNT = 88
CARRIER_PATH_MAX = 130          # §445 软洞补闸：载体目录长度闸（口径=目录非文件路径，承 _drive_c2_ab.py:62/387）

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
G_FRAME = 0x00A8ED84
G_TICK = 0x00A8ED80
BAIL_SITE = 0x006BE0E1
WM_CLOSE = 0x0010
WAIT_TIMEOUT, WAIT_OBJECT_0 = 258, 0
MEM_COMMIT, MEM_FREE, MEM_RESERVE = 0x1000, 0x10000, 0x2000
REPARSE_MASK = 0x400

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
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
u32.PostMessageW.restype = wt.BOOL
u32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.IsWindowVisible.restype = wt.BOOL
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextW.restype = ctypes.c_int
u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
ENUMPROC_T = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC_T, wt.LPARAM]


class TripFail(Exception):
    pass


_CALL_SEQ = itertools.count(1)   # 每次 fire_arm 唯一后缀，防同秒/替身时钟撞名


def real_sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# OPS seam：所有 OS/进程/文件/时间动作。production 用真实现；--faulttest 整体替换替身。
# 返回契约在此钉死（review 第 26/35 条「以实际接口测试」）：
#   read_mem(h,addr,size) -> (bytes|None, err:int)
#   vquery(h,addr)        -> ((state:int, base:int, size:int) | None, err:int)
#   post_close(hwnd)      -> (ok:bool, err:int)
#   get_exit_code(h)      -> (ok:bool, code:int)
#   list_procs()          -> {pid:name}
#   under_carrier(img, cdir:Path) -> bool
# ---------------------------------------------------------------------------
class MemBasicInfo(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]


k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p,
                              ctypes.POINTER(MemBasicInfo), ctypes.c_size_t]


def _r_read_mem(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ctypes.set_last_error(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), ctypes.cast(buf, ctypes.c_void_p),
                               size, ctypes.byref(got))
    if ok and got.value == size:
        return buf.raw[:size], 0
    return None, ctypes.get_last_error()


def _r_vquery(h, addr):
    mbi = MemBasicInfo()
    ctypes.set_last_error(0)
    n = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if n == 0:
        return None, ctypes.get_last_error()
    base = mbi.BaseAddress if mbi.BaseAddress else 0
    return (int(mbi.State), int(base), int(mbi.RegionSize)), 0


def _r_post_close(hwnd):
    ctypes.set_last_error(0)
    ok = bool(u32.PostMessageW(wt.HWND(hwnd), WM_CLOSE, 0, 0))
    return ok, ctypes.get_last_error()


def _r_get_exit_code(h):
    e = wt.DWORD(0)
    ok = k32.GetExitCodeProcess(h, ctypes.byref(e))
    return bool(ok), int(e.value)


def _r_window_pid(hwnd):
    w = wt.DWORD(0)
    tid = u32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(w))
    return int(w.value), int(tid)


def _r_enum_windows(pid):
    wins = []

    def _cb(hwnd, _):
        w = wt.DWORD(0)
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
        if w.value != pid:
            return True
        t = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, t, 256)
        c = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, c, 256)
        wins.append({"hwnd": int(hwnd or 0), "title": t.value, "class": c.value,
                     "visible": bool(u32.IsWindowVisible(hwnd))})
        return True

    u32.EnumWindows(ENUMPROC_T(_cb), 0)
    return wins


def _r_popen(argv, cwd, env):
    return subprocess.Popen(list(argv), cwd=str(cwd), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class PMEMCT(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def _r_working_set_kb(h):
    psapi = ctypes.WinDLL("psapi")
    m = PMEMCT()
    m.cb = ctypes.sizeof(m)
    if not psapi.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb):
        return None
    return int(m.WorkingSetSize) // 1024


def _r_carrier_identity_ok(carrier: Path):
    try:
        real = carrier.resolve()
        base = APPROVED_CT_ROOT.resolve()
    except Exception as e:
        return False, "resolve:%r" % e
    try:
        real.relative_to(base)
    except ValueError:
        return False, "outside_approved_root:%s" % real
    if carrier.exists():
        try:
            st = os.stat(carrier)
            if getattr(st, "st_file_attributes", 0) & REPARSE_MASK:
                return False, "reparse_point"
        except OSError:
            pass
    return True, "ok"


# default = production seam；PROBE/H7 由 bind_real_ops 填充后处理项
OPS = {}
PROBE = None
H7 = None
CURRENT_CARRIER = [None]


def _o_under_carrier(proc_pid):
    img = OPS["query_image"](proc_pid)
    c = CURRENT_CARRIER[0]
    return bool(img) and OPS["under_carrier"](img, c)


def bind_real_ops():
    global PROBE, H7
    PROBE = load_probe()
    H7 = load_h7()
    H7._QC151FS["on"] = True

    def _capture(out_png: Path):
        """★ A2-b 修（异族审计 BS-1）：改用 h7 自家捕获口径——24bpp DIB + pad4 行距，
        直接把 buf.raw 与 stride 交 write_png_no_filter（其 D-115 一次 B/R 交换即得文件色=屏幕色）。
        旧实现取 32bpp、自行交换后又按 w*3 切 stride=w*4 的缓冲 ⇒ 每行剪切+二次交换，出废帧。"""
        import ctypes as _c
        u = _c.windll.user32
        w, hh = u.GetSystemMetrics(78), u.GetSystemMetrics(79)
        hdc = u.GetDC(None)
        try:
            memdc = gdi32.CreateCompatibleDC(hdc)
            bmp = gdi32.CreateCompatibleBitmap(hdc, w, hh)
            gdi32.SelectObject(memdc, bmp)

            class BIH(_c.Structure):
                _fields_ = [("biSize", _c.c_uint), ("biWidth", _c.c_int),
                            ("biHeight", _c.c_int), ("biPlanes", _c.c_ushort),
                            ("biBitCount", _c.c_ushort), ("biCompression", _c.c_uint),
                            ("biSizeImage", _c.c_uint), ("biXPelsPerMeter", _c.c_int),
                            ("biYPelsPerMeter", _c.c_int), ("biClrUsed", _c.c_uint),
                            ("biClrImportant", _c.c_uint)]
            bih = BIH(40, w, -hh, 1, 24, 0, 0, 0, 0, 0, 0)   # ★ 24bpp，同 h7:2489
            stride = ((w * 3 + 3) // 4) * 4                   # ★ pad4 行距，同 h7:2491
            buf = _c.create_string_buffer(stride * hh)
            gdi32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT,
                                        _c.c_void_p, _c.c_void_p, wt.UINT]
            gdi32.GetDIBits.restype = _c.c_int
            ctypes.set_last_error(0)
            if not gdi32.BitBlt(memdc, 0, 0, w, hh, hdc, 0, 0, 0x00CC0020):
                raise TripFail("BitBlt err=%d" % ctypes.get_last_error())
            if gdi32.GetDIBits(memdc, bmp, 0, hh, buf, _c.byref(bih), 0) == 0:
                raise TripFail("GetDIBits failed err=%d" % ctypes.get_last_error())
            # 写侧交 h7 唯一口径：stride≠w*3 时按 stride 切行、丢 padding、做一次 B/R 交换
            H7.write_png_no_filter(Path(out_png), w, hh, buf.raw, stride)
        finally:
            u.ReleaseDC(None, hdc)
        return Path(out_png)

    OPS.update(
        now=time.time, sleep=time.sleep, popen=_r_popen,
        open_process=lambda a, pid: k32.OpenProcess(a, False, pid),
        close_handle=lambda h: k32.CloseHandle(h),
        wait0=lambda h: k32.WaitForSingleObject(h, 0), get_exit_code=_r_get_exit_code,
        terminate=lambda h: k32.TerminateProcess(h, 1),
        read_mem=_r_read_mem, vquery=_r_vquery, post_close=_r_post_close,
        enum_windows=_r_enum_windows, window_pid=_r_window_pid,
        list_procs=lambda: dict(PROBE.list_procs()),
        query_image=lambda pid: PROBE.query_image(pid) or "",
        under_carrier=lambda img, c: PROBE.under_carrier(img, c),
        find_main_window=lambda pid: H7.find_main_window(pid)[0],
        copy_file=lambda s, d: shutil.copy2(s, d),
        mkdir=lambda d: Path(d).mkdir(parents=True, exist_ok=False),
        rmtree=lambda d: shutil.rmtree(d),
        exists=lambda p: Path(p).exists(), isfile=lambda p: Path(p).is_file(),
        read_bytes=lambda p: Path(p).read_bytes(),
        carrier_identity_ok=_r_carrier_identity_ok,
        working_set_kb=_r_working_set_kb,
        capture_screen=_capture,
        sha16=real_sha16,
        sha256_file=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(),
        nav_focus=lambda hwnd: H7._focus_foreground(hwnd),
        nav_click=lambda hwnd, lx, ly: H7.click_logical(hwnd, lx, ly),
    )


def load_h7():
    os.environ["QC151_OUT_DIR"] = str(MYCARD / "_h7_workdir")
    spec = importlib.util.spec_from_file_location("harness7_ro_v2", H7_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_probe():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe_v2", THEIR_PROBE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tri_read_u32(h, addr):
    """G-9 三态；299 经 vquery 补证才分 page_absent/read_fail。"""
    raw, err = OPS["read_mem"](h, addr, 4)
    if raw is not None:
        return ("ok", int.from_bytes(raw, "little"))
    mbi, verr = OPS["vquery"](h, addr)
    detail = {"rpm_err": err, "vquery_err": verr, "mbi_state": mbi[0] if mbi else None}
    if mbi is not None and mbi[0] != MEM_COMMIT:
        return ("page_absent", detail)
    return ("read_fail", detail)


def _sentinel_get(row, name):
    v = row.get(name)
    return v if isinstance(v, int) else None


def phase_sentinels(pid):
    h = OPS["open_process"](0x0400 | 0x0010, pid)
    if not h:
        raise TripFail("OpenProcess(sentinel) pid=%d err=%d" % (pid, ctypes.get_last_error()))
    out = {"t": round(OPS["now"](), 3)}
    try:
        for name, addr in (("singleton", G_SINGLETON), ("hwnd", G_HWND),
                           ("exitstate", G_EXITSTATE), ("frame", G_FRAME), ("tick", G_TICK)):
            kind, val = tri_read_u32(h, addr)
            out[name] = val if kind == "ok" else {"state": kind, "detail": val}
        raw, _ = OPS["read_mem"](h, BAIL_SITE, 6)
        out["hook6"] = raw.hex() if raw is not None else {"state": "read_fail"}
        out["ws_kb"] = OPS["working_set_kb"](h)
        out["visible_windows"] = [{"title": w["title"], "class": w["class"]}
                                  for w in OPS["enum_windows"](pid) if w["visible"]]
    finally:
        OPS["close_handle"](h)
    return out


def apply_bail_mode(ini: Path, guard: int, bail_mode: str) -> None:
    lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(lines) if ln.strip() == "[Logic]"), None)
    if hi is None:
        raise TripFail("源 ini 缺 [Logic]")
    keep = []
    j = hi + 1
    while j < len(lines) and not lines[j].strip().startswith("["):
        s = lines[j].strip()
        if not (s.startswith("EnableRC4Guard=") or s.startswith("EnableRC4ExitBail=")
                or s.startswith("RC4GuardDryRun=")):
            keep.append(lines[j])
        j += 1
    new_sec = ["EnableRC4Guard=%d" % guard]
    if bail_mode == "explicit1":
        new_sec.append("EnableRC4ExitBail=1")
    elif bail_mode == "explicit0":
        new_sec.append("EnableRC4ExitBail=0")
    elif bail_mode != "default":
        raise TripFail("bad bail_mode %r" % bail_mode)
    lines = lines[:hi + 1] + new_sec + keep + lines[j:]
    ini.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    body = [ln.strip() for ln in ini.read_text(
        encoding="utf-8", errors="replace").splitlines()]
    hi2 = next((i for i, ln in enumerate(body) if ln == "[Logic]"), None)
    sec, stop = body[hi2 + 1:], len(body)
    for i in range(hi2 + 1, len(body)):
        if body[i].startswith("[") and i > hi2:
            stop = i; break
    sub = sec[:stop - hi2 - 1]
    if "EnableRC4Guard=%d" % guard not in sub:
        raise TripFail("guard 键读回失败")
    if bail_mode == "explicit1" and "EnableRC4ExitBail=1" not in sub:
        raise TripFail("bail=1 读回失败")
    if bail_mode == "explicit0" and "EnableRC4ExitBail=0" not in sub:
        raise TripFail("bail=0 读回失败")
    if bail_mode == "default" and any(b.startswith("EnableRC4ExitBail=") for b in sub):
        raise TripFail("default 臂键未清除")


ARMS = [
    {"key": "P0", "tag": "P0_ORIG", "inject": False, "guard": None, "bail_mode": None,
     "mode": "battle", "note": "原版直启（无注入）；局内关窗基线（H3）"},
    {"key": "P0N", "tag": "P0N_INJ_OFF", "inject": True, "guard": 0, "bail_mode": "default",
     "mode": "battle", "note": "注入中性臂：loader+候选DLL 但守卫双关=出厂 .text（隔离 P0↔P1 的注入变量）"},
    {"key": "P1", "tag": "P1_G1B0exp", "inject": True, "guard": 1, "bail_mode": "explicit0",
     "mode": "battle", "note": "Guard开+Bail显式关（§429 菜单僵尸的局内延伸对照）"},
    {"key": "P2", "tag": "P2_G1B0def", "inject": True, "guard": 1, "bail_mode": "default",
     "mode": "battle", "note": "Guard开+Bail键缺失：缺省 0 **运行时日志读回**验证臂（配置合同）"},
    {"key": "P3", "tag": "P3_G1B1", "inject": True, "guard": 1, "bail_mode": "explicit1",
     "mode": "battle", "note": "Guard开+Bail开=局内取证主臂：全量时间线+截图+投递记录"},
    {"key": "P3m", "tag": "P3m_MENU", "inject": True, "guard": 1, "bail_mode": "explicit1",
     "mode": "menu", "note": "同会话菜单态对照：菜单就绪闸×3，不跑战斗窗；与旧 hold=6s 臂差异如实记"},
]


def screenshot_best_effort(out_dir, tag, rec):
    try:
        p = out_dir / "shots" / ("%s.png" % tag)
        p.parent.mkdir(parents=True, exist_ok=True)
        OPS["capture_screen"](p)
        rec.setdefault("shots", []).append({"tag": tag, "path": str(p),
                                            "t": round(OPS["now"](), 3)})
    except Exception as e:
        rec.setdefault("evidence_errors", []).append("shot:%s:%r" % (tag, e))


def finalize(rec, carrier, out_dir, proc):
    """G-5/G-6/G-7 两阶段收尾，本函数绝不抛出。① 证据尽力 ② 清扫保证。"""
    def _ev(phase_name):
        try:
            ex = carrier / "except.txt"
            if OPS["isfile"](ex):
                rec.setdefault("except_at", {})[phase_name] = OPS["sha16"](ex)
            else:
                rec.setdefault("except_at", {})[phase_name] = "absent"
            if OPS["isfile"](carrier / "ra2render.log"):
                dst = out_dir / ("ra2render_%s.log" % phase_name)
                OPS["copy_file"](carrier / "ra2render.log", dst)
                rec.setdefault("guard_log_at", {})[phase_name] = str(dst)
        except Exception as e:
            rec.setdefault("evidence_errors", []).append("ev:%s:%r" % (phase_name, e))

    _ev("close_last")   # ① 观察末时点（清扫前）

    survivors = []
    try:
        for p, nm in list(OPS["list_procs"]().items()):
            if nm.lower() in ("gamemd.exe", "rc4_loader.exe") and _o_under_carrier(p):
                survivors.append([p, nm])
    except Exception as e:
        rec.setdefault("cleanup_errors", []).append("list:%r" % e)

    if survivors:
        rec["killed_on_cleanup"] = survivors
        for p, nm in survivors:
            try:
                th = OPS["open_process"](0x0001 | 0x100000, p)
                if th:
                    OPS["terminate"](th)
                    OPS["close_handle"](th)
            except Exception as e:
                rec.setdefault("cleanup_errors", []).append("term:%d:%r" % (p, e))
    if proc is not None:
        try:
            proc.wait(timeout=5)
        except Exception as e:
            rec.setdefault("cleanup_errors", []).append("wait:%r" % e)

    _ev("after_kill")   # ② 强杀/等待后再采（迟到的终态日志/except 不丢）

    rem = []
    deadline = OPS["now"]() + 3.0
    while OPS["now"]() < deadline:
        try:
            rem = [p for p, nm in list(OPS["list_procs"]().items())
                   if nm.lower() in ("gamemd.exe", "rc4_loader.exe") and _o_under_carrier(p)]
        except Exception as e:
            rec.setdefault("cleanup_errors", []).append("rescan:%r" % e)
            rem = ["rescan_failed"]
            break
        if not rem:
            break
        OPS["sleep"](0.25)
    rec["a8_remaining"] = rem
    try:
        rec["a8_enum_ok"] = os.getpid() in OPS["list_procs"]()
    except Exception as e:
        rec["a8_enum_ok"] = False
        rec.setdefault("cleanup_errors", []).append("enumctl:%r" % e)
    rec["a8_verdict"] = "PASS" if (not rem and rec["a8_enum_ok"]) else "V_FAIL"

    if rem:
        rec.update(carrier_retained=True, carrier_deleted=False,
                   delete_reason="survivors_under_carrier")
    else:
        ok_id, det = OPS["carrier_identity_ok"](carrier.parent)
        if not ok_id:
            rec.update(carrier_retained=True, carrier_deleted=False,
                       delete_reason="identity:%s" % det)
        else:
            try:
                OPS["rmtree"](carrier.parent)
                rec["carrier_deleted"] = not OPS["exists"](carrier.parent)
                rec["carrier_retained"] = not rec["carrier_deleted"]
            except Exception as e:
                rec.update(carrier_deleted=False, carrier_retained=True,
                           delete_reason="rmtree_error:%r" % e)
                rec.setdefault("cleanup_errors", []).append("rmtree:%r" % e)

    ea = rec.get("except_at", {})
    if "after_kill" in ea:
        rec["except_changed"] = (ea["after_kill"] != rec.get("except_before"))
    if rec["verdict"] == "OK" and (rec.get("evidence_errors") or rec.get("cleanup_errors")):
        rec["verdict"] = "PARTIAL"     # 失败不被 PASS 覆盖（G-5/G-9）
    try:
        (out_dir / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    except Exception as e:
        rec.setdefault("evidence_errors", []).append("recwrite:%r" % e)
    return rec


def _precheck_shas():
    sha = OPS["sha16"]
    for name, pth, want in (("gamemd", GAME_SRC / "gamemd.exe", GAMEMD_SHA16),
                            ("loader", GUARD_DIR / "rc4_loader.exe", LOADER_SHA16),
                            ("h7", H7_PATH, H7_SHA16), ("probe", THEIR_PROBE, PROBE_SHA16)):
        if sha(pth) != want:
            raise TripFail("precheck_sha:%s=%s≠%s" % (name, sha(pth), want))
    if OPS["sha256_file"](C2_DIR / "ra2rc4guard_c2.dll") != C2_DLL_SHA256:
        raise TripFail("precheck_c2_sha256")


def fire_arm(arm, watch_s, play_s) -> dict:
    """G-1/G-2/G-5/G-6/G-7/G-8/G-9 全关闭；**恒返回单个 dict**；异常→phase 标注→finalize。"""
    stamp = "%s_%04d" % (time.strftime("%Y%m%dT%H%M%S"), next(_CALL_SEQ))
    out_dir = MYCARD / ("%s_%s" % (stamp, arm["tag"]))
    carrier = out_dir / "ct" / ("c" + "0" * 9)
    CURRENT_CARRIER[0] = carrier
    rec = {"trip_tag": arm["tag"], "mode": arm["mode"], "note": arm["note"],
           "out_dir": str(out_dir), "verdict": "OK", "phase": "init",
           "watch_s": watch_s, "play_s": play_s if arm["mode"] == "battle" else 0}
    proc = None
    made_carrier = False
    try:
        rec["phase"] = "precheck"
        if any(nm.lower() in ("gamemd.exe", "rc4_loader.exe")
               for nm in OPS["list_procs"]().values()):
            raise TripFail("precheck_residual_procs")
        _precheck_shas()
        ok_id, det = OPS["carrier_identity_ok"](carrier)
        if not ok_id:
            raise TripFail("carrier_identity:%s" % det)

        rec["phase"] = "mkdir"
        # §445 补闸：载体目录过长⇒在建树前即拦（made_carrier 仍 False，无清扫/无泄漏）
        if len(str(carrier)) > CARRIER_PATH_MAX:
            raise TripFail("carrier_pathlen:%d>%d" % (len(str(carrier)), CARRIER_PATH_MAX))
        out_dir.mkdir(parents=True, exist_ok=True)
        OPS["mkdir"](carrier)
        made_carrier = True
        if any(carrier.iterdir()):
            raise TripFail("carrier_not_empty_after_mkdir")

        rec["phase"] = "copy"
        for f in sorted(GAME_SRC.iterdir()):
            if f.is_file():
                OPS["copy_file"](f, carrier / f.name)
        ex0 = carrier / "except.txt"
        rec["except_before"] = OPS["sha16"](ex0) if OPS["isfile"](ex0) else "absent"
        argv = [str(carrier / "gamemd.exe")]
        if arm["inject"]:
            rec["phase"] = "inject_setup"
            OPS["copy_file"](GUARD_DIR / "rc4_loader.exe", carrier / "rc4_loader.exe")
            OPS["copy_file"](C2_DIR / "ra2rc4guard_c2.dll", carrier / "ra2rc4guard_c2.dll")
            apply_bail_mode(carrier / "ra2render.ini", arm["guard"], arm["bail_mode"])
            argv = [str(carrier / "rc4_loader.exe"), "ra2rc4guard_c2.dll"]

        rec["phase"] = "popen"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = OPS["popen"](argv, str(carrier), env)
        rec["loader_pid"] = proc.pid
        t0 = OPS["now"]()

        rec["phase"] = "find_pid"
        pid = None
        for _ in range(200):
            OPS["sleep"](0.1)
            for p, nm in list(OPS["list_procs"]().items()):
                if nm.lower() == "gamemd.exe" and _o_under_carrier(p):
                    pid = p
                    break
            if pid:
                break
        if pid is None:
            raise TripFail("gamemd_not_found")
        rec["gamemd_pid"] = pid

        rec["phase"] = "find_window"
        hwnd = None
        while OPS["now"]() - t0 < 60.0:
            hwnd = OPS["find_main_window"](pid)
            if hwnd:
                break
            OPS["sleep"](0.5)
        if not hwnd:
            raise TripFail("no_main_window_60s")
        wpid, wtid = OPS["window_pid"](hwnd)
        if wpid != pid:
            raise TripFail("window_pid_mismatch win=%d pid=%d" % (wpid, pid))
        rec["hwnd"], rec["window_tid"] = hwnd, wtid

        tl = []
        if arm["mode"] == "battle":
            rec["phase"] = "nav"
            OPS["sleep"](35.0)
            for (lx, ly) in ((700, 218), (700, 304), (700, 262)):
                OPS["nav_focus"](hwnd)
                OPS["nav_click"](hwnd, lx, ly)
                OPS["sleep"](12.0)
            rec["phase"] = "in_battle_gate"
            s0 = phase_sentinels(pid)
            OPS["sleep"](3.0)
            s1 = phase_sentinels(pid)
            f0, f1 = _sentinel_get(s0, "frame"), _sentinel_get(s1, "frame")
            rec["in_battle"] = bool(f0 is not None and f1 is not None and f1 - f0 >= 8)
            rec["battle_gate_pair"] = [s0, s1]
            if not rec["in_battle"]:
                raise TripFail("not_in_battle")
            rec["phase"] = "battle_window"
            tp = OPS["now"]()
            while OPS["now"]() - tp < play_s:
                tl.append(phase_sentinels(pid))
                OPS["sleep"](2.0)
            rec["battle_tl_n"] = len(tl)
            screenshot_best_effort(out_dir, "battle_end", rec)
        else:
            rec["phase"] = "menu_ready_gate"
            OPS["sleep"](35.0)
            ready, tm = 0, OPS["now"]()
            while OPS["now"]() - tm < 90.0 and ready < 3:
                s = phase_sentinels(pid)
                tl.append(s)
                ok = (s.get("frame") == 0 and isinstance(s.get("singleton"), int)
                      and s["singleton"] != 0 and isinstance(s.get("hwnd"), int) and s["hwnd"] != 0)
                ready = ready + 1 if ok else 0
                OPS["sleep"](1.0)
            rec["menu_ready"] = ready >= 3
            rec["menu_ready_s"] = round(OPS["now"]() - tm, 1)
            rec["battle_tl_n"] = len(tl)
            if not rec["menu_ready"]:
                raise TripFail("menu_not_ready_90s")
            screenshot_best_effort(out_dir, "menu_ready", rec)

        rec["phase"] = "pre5"
        pre5 = []
        for _ in range(5):
            s = phase_sentinels(pid)
            pre5.append({"t": s["t"], "sent": s})
            OPS["sleep"](1.0)
        rec["pre_close_5s_n"] = len(pre5)
        last = pre5[-1]["sent"]
        if arm["mode"] == "battle" and _sentinel_get(last, "frame") is None:
            raise TripFail("scene_recheck_unreadable")
        rec["scene_before_close"] = last
        screenshot_best_effort(out_dir, "pre_close", rec)

        rec["phase"] = "deliver"
        ok_post, err_post = OPS["post_close"](hwnd)
        rec["close_delivery"] = {"post_ok": ok_post, "post_err": err_post,
                                 "target_hwnd": hwnd, "win_pid": wpid, "win_tid": wtid,
                                 "t": round(OPS["now"](), 3)}
        if not ok_post:
            raise TripFail("PostMessageW_failed err=%d" % err_post)
        t_close = OPS["now"]()
        rec["closed_at_s"] = round(t_close - t0, 3)

        rec["phase"] = "watch"
        rows = []
        hs = OPS["open_process"](0x0400 | 0x0010 | 0x100000, pid)
        if not hs:
            raise TripFail("OpenProcess_watch err=%d" % ctypes.get_last_error())
        try:
            while OPS["now"]() < t_close + watch_s:
                res = OPS["wait0"](hs)
                cok, excode = OPS["get_exit_code"](hs)
                row = {"t": round(OPS["now"](), 3), "wait": res,
                       "code": excode if cok and res == WAIT_OBJECT_0 else None,
                       "code_read_ok": cok}
                for nm2, addr2 in (("exitstate", G_EXITSTATE), ("frame", G_FRAME),
                                   ("hwnd", G_HWND), ("singleton", G_SINGLETON), ("tick", G_TICK)):
                    kind, val = tri_read_u32(hs, addr2)
                    row[nm2] = val if kind == "ok" else {"state": kind}
                rows.append(row)
                if len(rows) % 20 == 1:
                    try:
                        rec.setdefault("post_windows", []).append(
                            {"t": row["t"], "visible": [w for w in OPS["enum_windows"](pid) if w["visible"]]})
                    except Exception as e:
                        rec.setdefault("evidence_errors", []).append("wins:%r" % e)
                if res == WAIT_OBJECT_0:
                    break
                OPS["sleep"](0.1)
        finally:
            OPS["close_handle"](hs)
        rec["close_rows_n"] = len(rows)
        if len(rows) == 0:
            raise TripFail("zero_close_samples")
        (out_dir / "timeline.json").write_text(
            json.dumps({"battle_tl": tl, "pre5": pre5, "close_rows": rows},
                       ensure_ascii=False), encoding="utf-8")
        screenshot_best_effort(out_dir, "post_close_end", rec)
        exited = rows[-1]["wait"] == WAIT_OBJECT_0
        rec["exited"] = exited
        rec["exit_kind"] = ("natural" if exited else
                            "still_running_at_watch_end" if rows[-1]["wait"] == WAIT_TIMEOUT
                            else "wait_error:%d" % rows[-1]["wait"])
        rec["exit_after_close_s"] = round(rows[-1]["t"] - t_close, 2) if exited else None
        rec["final_exitcode"] = rows[-1]["code"] if exited else None
    except TripFail as e:
        rec["verdict"] = "FAIL"
        rec["fail"] = str(e)[:300]
    except Exception as e:
        rec["verdict"] = "FAIL"
        rec["fail"] = "unexpected@%s:%r" % (rec.get("phase"), e)
    finally:
        if not made_carrier:
            # 载体没建成：仍尽力存 rec（无清扫对象）
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                                   encoding="utf-8")
            except Exception:
                pass
        else:
            try:
                finalize(rec, carrier, out_dir, proc)
            except Exception as e:
                rec["finalize_leaked_error"] = repr(e)
    return rec


APPROVED_THIS_ROUND = False   # 审阅权在 Codex；本轮永假


def preflight() -> list:
    sha = OPS.get("sha16", real_sha16)
    fails = []
    checks = [
        ("gamemd 母本 sha", sha(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16),
        ("loader sha", sha(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16),
        ("c2 DLL sha256", hashlib.sha256((C2_DIR / "ra2rc4guard_c2.dll").read_bytes()).hexdigest() == C2_DLL_SHA256),
        ("harness7 批准指纹", sha(H7_PATH) == H7_SHA16),
        ("探针批准指纹", sha(THEIR_PROBE) == PROBE_SHA16),
        ("游戏源 88 件", GAME_SRC.is_dir() and len([f for f in GAME_SRC.iterdir() if f.is_file()]) == SRC_FILE_COUNT),
        ("残留游戏进程=0", not PROBE.game_procs()),
    ]
    for name, ok in checks:
        print("  [%s] %-30s" % ("OK" if ok else "RED", name))
        if not ok:
            fails.append(name)
    return fails


# ---------------------------------------------------------------------------
# 故障注入离线测试（替身 OS，禁真启动游戏；每条对应 REVIEW 一条阻断）
# ---------------------------------------------------------------------------
def _stub_read(addr_val_map, default=(b"\x00\x00\x00\x00", 0)):
    def _rm(h, addr, size):
        if addr in addr_val_map:
            v = addr_val_map[addr]
            return (v, 0) if isinstance(v, bytes) else v     # (bytes,0) 或 (None,err)
        return default
    return _rm


def run_fault_tests() -> int:
    global MYCARD, APPROVED_CT_ROOT, GAME_SRC, PROBE, H7
    fails = []

    def t(name, cond, ev=""):
        print("[%s] %-48s %s" % ("OK" if cond else "RED", name, ev))
        if not cond:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="xprobe_ft_"))
    saved = (MYCARD, APPROVED_CT_ROOT, GAME_SRC, PROBE, H7, dict(OPS))
    try:
        MYCARD = tmp / "c2ab_x"; MYCARD.mkdir(parents=True)
        APPROVED_CT_ROOT = MYCARD
        GAME_SRC = tmp / "src"; GAME_SRC.mkdir()
        for i in range(SRC_FILE_COUNT):
            (GAME_SRC / ("f%03d" % i)).write_bytes(b"Z")
        (GAME_SRC / "gamemd.exe").write_bytes(b"Z")
        (GAME_SRC / "ra2render.ini").write_text("[Logic]\n", encoding="utf-8")

        class StubProc:
            def __init__(self): self.pid = 4242
            def wait(self, timeout=5): return 0

        def base_ops(survivors="clean", post_ok=True, rmtree_fail=False, popen_fail=False,
                     mkdir_fail=False, frame_mode="battle", read_fail_addr=None):
            """survivors: clean=杀后消失 / stuck=杀不掉 / none=从不出现
               frame_mode: battle=两次读递增 / menu=恒0(菜单就绪) / stuck0=恒0(战斗判负)"""
            st = {"t": [1000.0], "launched": [False], "killed": [False],
                  "frame_calls": [0], "gone": set()}

            def now():
                st["t"][0] += 0.5
                return st["t"][0]

            def list_procs():
                if survivors == "none" or not st["launched"][0]:
                    return {}
                if st["killed"][0] and survivors == "clean":
                    return {}
                return {4242: "gamemd.exe", 4243: "rc4_loader.exe"}

            def _mkdir(d):
                if mkdir_fail:
                    raise OSError("mkdir_fail")
                Path(d).mkdir(parents=True, exist_ok=True)

            def _read(h, addr, size):
                if read_fail_addr is not None and addr == read_fail_addr:
                    return None, 299
                if addr == G_FRAME:
                    if frame_mode in ("menu", "stuck0"):
                        return struct.pack("<I", 0), 0
                    st["frame_calls"][0] += 1
                    return struct.pack("<I", 100 * st["frame_calls"][0]), 0
                if addr == G_SINGLETON:
                    return struct.pack("<I", 12345), 0
                if addr == G_HWND:
                    return struct.pack("<I", 999), 0
                return struct.pack("<I", 1), 0

            return {
                "now": now, "sleep": lambda s: None,
                "popen": (lambda *a, **k: (_ for _ in ()).throw(TripFail("popen_fail")))
                         if popen_fail else (lambda argv, cwd, env: (st.__setitem__("launched", [True]), StubProc())[1]),
                "open_process": lambda a, pid: 1, "close_handle": lambda h: None,
                "wait0": lambda h: WAIT_TIMEOUT, "get_exit_code": lambda h: (True, 259),
                "terminate": lambda h: st.__setitem__("killed", [True]),
                "read_mem": _read,
                "vquery": lambda h, addr: ((MEM_FREE, addr, 0), 0) if (read_fail_addr == addr)
                    else ((MEM_COMMIT, addr, 0x1000), 0),
                "post_close": lambda hwnd: (post_ok, 0 if post_ok else 1400),
                "enum_windows": lambda pid: [], "window_pid": lambda hwnd: (4242, 99),
                "list_procs": list_procs,
                "query_image": lambda pid: str(CURRENT_CARRIER[0] / "gamemd.exe"),
                "under_carrier": lambda img, c: os.path.normcase(str(img)).startswith(
                    os.path.normcase(str(c)) + os.sep),
                "find_main_window": lambda pid: 0x1234,
                "copy_file": lambda s, d: shutil.copy2(s, d), "mkdir": _mkdir,
                "rmtree": (lambda d: (_ for _ in ()).throw(OSError("locked"))) if rmtree_fail
                          else (lambda d: (shutil.rmtree(d, ignore_errors=True), st["gone"].add(str(d)))),
                "exists": lambda p: str(p) not in st["gone"] and Path(p).exists(),
                "isfile": lambda p: Path(p).is_file(),
                "read_bytes": lambda p: Path(p).read_bytes(),
                "carrier_identity_ok": lambda c: (True, "ok"),
                "working_set_kb": lambda h: 66000,
                "capture_screen": lambda p: Path(p).write_bytes(b"PNG"),
                "sha16": lambda p: (GAMEMD_SHA16 if "gamemd" in str(p) else
                                    LOADER_SHA16 if "loader" in str(p) else
                                    H7_SHA16 if "harness7" in str(p) else
                                    PROBE_SHA16 if "probe" in str(p) else real_sha16(p)),
                "sha256_file": lambda p: (C2_DLL_SHA256 if "rc4guard_c2" in str(p)
                                          else hashlib.sha256(Path(p).read_bytes()).hexdigest()),
                "nav_focus": lambda hwnd: None, "nav_click": lambda h, x, y: None,
            }

        def install(ops):
            for k in list(OPS): OPS.pop(k, None)
            OPS.update(ops)

        PROBE = type("P", (), {"game_procs": staticmethod(lambda: [])})()

        # FT1 返回协议=单个 dict + menu 臂全程 OK（G-2/G-8）；先验类型再取值（防崩）
        install(base_ops(frame_mode="menu")); r0 = fire_arm(dict(ARMS[5]), 1.0, 0)
        is_dict = isinstance(r0, dict)
        r = r0 if is_dict else {"verdict": "NOT_DICT", "fail": repr(type(r0))[:40]}
        t("FT1 fire_arm 返回单个 dict+verdict", is_dict and r.get("verdict") in ("OK", "PARTIAL"),
          "%s %s" % (r.get("verdict"), r.get("fail", ""))[:40])

        # FT2 投递失败⇒FAIL + 清扫仍跑（G-9/G-5）
        install(base_ops(frame_mode="menu", post_ok=False)); r = fire_arm(dict(ARMS[5]), 1.0, 0)
        t("FT2 投递失败⇒FAIL", r["verdict"] == "FAIL" and "PostMessageW" in r.get("fail", ""), r.get("fail", "")[:50])
        t("FT2 投递失败仍清扫", r.get("carrier_deleted") is True)

        # FT3 杀不掉的残留⇒保留载体报原因（G-7）
        install(base_ops(frame_mode="menu", survivors="stuck")); r = fire_arm(dict(ARMS[5]), 1.0, 0)
        t("FT3 残留⇒carrier_retained+delete_reason",
          r.get("carrier_retained") is True and r.get("carrier_deleted") is False
          and r.get("delete_reason") == "survivors_under_carrier", str(r.get("delete_reason")))

        # FT3b 身份不符⇒保留载体（G-7）
        ops = base_ops(frame_mode="menu"); ops["carrier_identity_ok"] = lambda c: (False, "reparse_point")
        install(ops); r = fire_arm(dict(ARMS[5]), 1.0, 0)
        if r["verdict"] == "FAIL":   # fire_arm 前置身份检查也会拦——两条路都算保留
            t("FT3b 身份不符被前置拦", "identity" in r.get("fail", ""), r.get("fail", "")[:40])
        else:
            t("FT3b 身份不符⇒保留+delete_reason",
              r.get("delete_reason", "").startswith("identity:"), str(r.get("delete_reason", ""))[:40])

        # FT4 rmtree 异常⇒留痕不吞（G-7）
        install(base_ops(frame_mode="menu", rmtree_fail=True))
        r = fire_arm(dict(ARMS[5]), 1.0, 0)
        t("FT4 rmtree_error 可见", "rmtree_error" in str(r.get("delete_reason", "")) and bool(r.get("cleanup_errors")),
          str(r.get("delete_reason", ""))[:40])

        # FT5 popen 异常⇒安全收尾+证据尽力（G-5）
        install(base_ops(frame_mode="menu", popen_fail=True))
        r = fire_arm(dict(ARMS[5]), 1.0, 0)
        t("FT5 popen 异常安全（无泄漏、有 _rec）",
          r["verdict"] == "FAIL" and "finalize_leaked_error" not in r
          and OPS["isfile"](Path(r["out_dir"]) / "_rec.json"), r.get("fail", "")[:40])

        # FT6 tri 分型（G-9：299 不自动=页不存在）
        ops = base_ops(frame_mode="menu"); install(ops)
        OPS["read_mem"] = lambda h, a, s: (None, 299)
        OPS["vquery"] = lambda h, a: ((MEM_FREE, a, 0), 0)
        kind, val = tri_read_u32(1, G_FRAME)
        t("FT6a 299+FREE⇒page_absent", kind == "page_absent", kind)
        OPS["vquery"] = lambda h, a: ((MEM_COMMIT, a, 0x1000), 0)
        kind, val = tri_read_u32(1, G_FRAME)
        t("FT6b 299+COMMIT⇒read_fail(不冒充页缺失)", kind == "read_fail", kind)

        # FT7 menu 臂时序独立：play_s 记 0、有 menu_ready_s 与旧臂差异（G-8）
        install(base_ops(frame_mode="menu")); r = fire_arm(dict(ARMS[5]), 1.0, 60.0)
        t("FT7 menu 臂 play_s=0+menu_ready_s 在录",
          r.get("play_s") == 0 and isinstance(r.get("menu_ready_s"), float) and r.get("menu_ready") is True,
          "play_s=%s ready=%s t=%s" % (r.get("play_s"), r.get("menu_ready"), r.get("menu_ready_s")))

        # FT8 载体创建失败⇒FAIL@mkdir，不误删（G-1）
        install(base_ops(frame_mode="menu", mkdir_fail=True))
        r = fire_arm(dict(ARMS[5]), 1.0, 0)
        t("FT8 创建失败⇒FAIL phase=mkdir", r["verdict"] == "FAIL" and r.get("phase") == "mkdir",
          "phase=%s" % r.get("phase"))

        # FT9 live 硬闸
        t("FT9 live 闸关死", APPROVED_THIS_ROUND is False)

        # FT10 零 close 样本⇒FAIL（G-9）
        install(base_ops(frame_mode="menu")); r = fire_arm(dict(ARMS[5]), -1.0, 0)
        t("FT10 零样本⇒FAIL", r["verdict"] == "FAIL" and "zero_close_samples" in r.get("fail", ""),
          r.get("fail", "")[:40])

        # FT11 证据阶段异常⇒OK 降 PARTIAL（G-5；finalize 直测；载体=一次性 temp，绝不误删他树）
        install(base_ops(frame_mode="menu"))
        OPS["isfile"] = lambda p: (_ for _ in ()).throw(OSError("ev fail"))
        rec11 = {"verdict": "OK", "phase": "watch"}
        t11 = Path(tempfile.mkdtemp(prefix="xprobe_ft11_"))
        finalize(rec11, t11 / "ct" / "carrierX", t11 / "out", None)
        t("FT11 证据异常⇒PARTIAL 非 OK+errors 留痕",
          rec11["verdict"] == "PARTIAL" and rec11.get("evidence_errors"), str(rec11.get("verdict")))
        shutil.rmtree(t11, ignore_errors=True)

        # FT12 battle 臂全链路：timeline 全量（close_rows 数==close_rows_n，且 >6 行
        #      ⇒ 「只存末 6」型回归可被检出；d09b 教训的**可杀**版本）（G-6）
        install(base_ops(frame_mode="battle"))
        r = fire_arm(dict(ARMS[4]), 40.0, 2.0)     # P3 battle：stub 时钟 0.5s/步 ⇒ ~10+ 行
        if r["verdict"] != "FAIL":
            tlj = json.loads((Path(r["out_dir"]) / "timeline.json").read_text(encoding="utf-8"))
            t("FT12 battle 臂 in_battle+timeline 全量(>6行)",
              r.get("in_battle") is True and len(tlj["close_rows"]) == r.get("close_rows_n", -1)
              and len(tlj["close_rows"]) > 6
              and r.get("exit_kind") == "still_running_at_watch_end",
              "rows=%s tl=%s exit=%s" % (r.get("close_rows_n"), len(tlj["close_rows"]), r.get("exit_kind")))
            shots = Path(r["out_dir"]) / "shots"
            t("FT12 截图通道在录", bool(r.get("shots")) and shots.is_dir() and any(shots.iterdir()),
              "%d shots" % len(r.get("shots", [])))
        else:
            t("FT12 battle 臂全链路", False, "FAIL:" + r.get("fail", "")[:60])

        # FT13 载体路径过长⇒建树前拦（§445 补闸；phase=mkdir 前，made_carrier=False 无泄漏）
        install(base_ops(frame_mode="menu"))
        _mc_saved = MYCARD
        try:
            globals()["MYCARD"] = tmp / ("d" * 60) / ("e" * 60) / "c2ab_x"
            r13 = fire_arm(dict(ARMS[5]), 1.0, 0)
        finally:
            globals()["MYCARD"] = _mc_saved
        t("FT13 pathlen 越界⇒FAIL carrier_pathlen",
          r13["verdict"] == "FAIL" and "carrier_pathlen" in r13.get("fail", "")
          and r13.get("carrier_deleted") is not True,
          "%s out_len=%d" % (r13.get("fail", "")[:34], len(str(r13.get("out_dir", "")))))

        print("== FAULTTEST: %s ==" % ("ALL PASS" if not fails else "FAIL " + ",".join(fails)))
        return 0 if not fails else 1
    finally:
        MYCARD, APPROVED_CT_ROOT, GAME_SRC, PROBE, H7, ops_saved = saved
        for k in list(OPS): OPS.pop(k, None)
        OPS.update(ops_saved)
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--approved", action="store_true")
    ap.add_argument("--faulttest", action="store_true")
    ap.add_argument("--arms", default="P0,P1,P2,P3")
    ap.add_argument("--watch", type=float, default=40.0)
    ap.add_argument("--play-s", type=float, default=60.0)
    a = ap.parse_args()
    if a.faulttest:
        return run_fault_tests()
    bind_real_ops()
    fails = preflight()          # G-3：live/离线都先跑
    if not a.live:
        print("★ 预检 %s；候选件不发射。" % ("全过" if not fails else "红 %s" % fails))
        return 0 if not fails else 2
    if fails:
        print("!! live 被预检拦（G-3）"); return 2
    if not (a.approved and APPROVED_THIS_ROUND):
        print("!! live 硬闸：APPROVED_THIS_ROUND=%s（Codex 审定版本前永假）" % APPROVED_THIS_ROUND)
        return 3
    sel = [x for x in ARMS if x["key"] in [s.strip() for s in a.arms.split(",")]]
    for arm in sel:
        r = fire_arm(arm, a.watch, a.play_s)
        print(r["trip_tag"], "verdict=%s exited=%s after=%s in_battle=%s menu=%s fail=%s"
              % (r["verdict"], r.get("exited"), r.get("exit_after_close_s"),
                 r.get("in_battle"), r.get("menu_ready"), r.get("fail")))
        if r["verdict"] not in ("OK",):     # G-9 硬停（PARTIAL 也停）
            print("!! 臂非 OK ⇒ 停后续"); break
    return 0


if __name__ == "__main__":
    sys.exit(main())
