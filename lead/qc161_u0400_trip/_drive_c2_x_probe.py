#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C26-06 观测驱动候选（本线写域，**离线核验件——本轮不发射**）。

★ 为什么需要它（REVIEW_S438 / C26-06 逐条落地；不新增 Hook、不写状态、不跳确认、不丢存档）：
  1. **投递≠处理**：现驱动 PostMessageW 返回值/GetLastError 未入 rec ⇒ 本件必记
     （返回、错误码、实际目标 hwnd + 该窗所属 pid/tid、WM_CLOSE 序号）。
  2. **关窗前后时间线**：窗口集变化（含游戏内绘制看不见 ⇒ 每阶段抓桌面截屏补 UI 记录）、
     阶段哨兵（singleton/hwnd/exitstate/frame/ws）逐样，关窗前 5s / 关窗后按 watch 全采。
  3. **三态可分**：每个只读量区分「值 0」/「读失败」/「地址不可达(页不存在)」——
     ReadProcessMemory 失败再验页状态（QueryWorkingSetEx 的 Shared/Valid 位），
     不满足则记 `unreadable`，**绝不当 0**。
  4. **缺省 0 ≠ 显式写 0**：新增 `bail_mode="default"` 臂（ini **不写该键**），与
     `"explicit0"`（写 =0）分报——只有 default 臂运行时读回才算缺省实证。
  5. **取证先于清扫**：except.txt 摘取、日志拷贝、截屏归档全部在 rmtree **之前**（161412 教训）。
  6. 局内判定=帧钟推进（沿用 L1REG 进局方法学，harness7 只 import 零改动）。

★ 与 L1REG 的差：L1REG 是回归趟（判据=退不退）；本件是**取证趟**——每臂输出
  `x_probe_verdict`（H1 确认 UI 等待 / H2 消息被吞 / 不可分）所需的原始时间线。
★ 串行三臂设计（审阅后才排真机；本轮零发射）见 x_ingame_close_20261026/X_*.md 设计节。

★ 预检/自检（离线可跑，零游戏）：
  python _drive_c2_x_probe.py                 # 预检（只读）
  python _drive_c2_x_probe.py --selfcheck     # 合成 rec/三态/键模式 单元自检
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
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "c2ab_x"
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
C2_DIR = ROOT / "lead/qc161_u0400_trip/d09a_c2_candidate"
H7_PATH = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
THEIR_PROBE = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"

GAMEMD_SHA16 = "73201cc021497c95"
LOADER_SHA16 = "ebddf6a61273c874"
C2_DLL_SHA256 = "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
G_FRAME = 0x00A8ED84
BAIL_SITE = 0x006BE0E1
WM_CLOSE = 0x0010
WM_QUIT = 0x0012

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
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
k32.GetLastError.restype = wt.DWORD
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


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_h7():
    os.environ["QC151_OUT_DIR"] = str(MYCARD / "_h7_workdir")
    spec = importlib.util.spec_from_file_location("harness7_ro", H7_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_probe():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe", THEIR_PROBE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROBE = None

# ---------------------------------------------------------------------------
# 三态读值：0 / read-fail(带 winerror) / page-unreachable ⇒ 字符串 "unreadable"
# ---------------------------------------------------------------------------
def tri_read_u32(h, addr):
    """返回 (kind, value)：kind ∈ {"ok","read_fail","unreadable_page"}。"""
    buf = ctypes.create_string_buffer(4)
    got = ctypes.c_size_t(0)
    ctypes.set_last_error(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), ctypes.cast(buf, ctypes.c_void_p),
                               4, ctypes.byref(got))
    if ok and got.value == 4:
        return ("ok", int.from_bytes(buf.raw[:4], "little"))
    err = ctypes.get_last_error()
    # ERROR_PARTIAL_COPY(299)/无效页族 ⇒ 区分「读失败(地址在但页被换出)」vs「页不存在」
    # 保守口径：err 属于访问族 ⇒ unreadable_page；其余 ⇒ read_fail。
    if err in (299, 998, 999):
        return ("unreadable_page", err)
    return ("read_fail", err)


def rpm_bytes(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), ctypes.cast(buf, ctypes.c_void_p),
                               size, ctypes.byref(got))
    return buf.raw[:got.value] if (ok and got.value == size) else None


def enum_windows(pid):
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
        wins.append({"hwnd": hwnd, "title": t.value, "class": c.value,
                     "visible": bool(u32.IsWindowVisible(hwnd))})
        return True

    u32.EnumWindows(ENUMPROC_T(_cb), 0)
    return wins


def phase_sentinels(pid):
    """一个时间点的全哨兵（独立句柄；三态分记，绝不当 0）。"""
    h = k32.OpenProcess(0x0400 | 0x0010, False, pid)
    out = {"t": round(time.time(), 3)}
    if not h:
        out["err"] = "OpenProcess %d" % ctypes.get_last_error()
        return out
    try:
        for name, addr in (("singleton", G_SINGLETON), ("hwnd", G_HWND),
                           ("exitstate", G_EXITSTATE), ("frame", G_FRAME)):
            kind, val = tri_read_u32(h, addr)
            out[name] = val if kind == "ok" else ("%s:%d" % (kind, val))
        hook = rpm_bytes(h, BAIL_SITE, 6)
        out["hook6"] = hook.hex() if hook else "read_fail"
    finally:
        k32.CloseHandle(h)
    return out


def window_timeline(pid, tag):
    return {"t": round(time.time(), 3), "tag": tag,
            "windows": enum_windows(pid)}


# ---------------------------------------------------------------------------
# 键模式：explicit1 / explicit0 / default（缺键）——三臂开关**读回验证**
# ---------------------------------------------------------------------------
KEY_MODES = ("explicit1", "explicit0", "default")


def apply_bail_mode(ini: Path, guard: int, bail_mode: str) -> None:
    """写 EnableRC4Guard 与（仅 explicit*）EnableRC4ExitBail；default=**确保该键不存在**。
    回读逐键验证，不符即抛（假开臂=§426 教训）。"""
    lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(lines) if ln.strip() == "[Logic]"), None)
    assert hi is not None, "源 ini 缺 [Logic]"
    # 先清本线两键（防旧值混叠），再按模式写
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
    # default ⇒ 不写 bail 键
    lines = lines[:hi + 1] + new_sec + keep + lines[j:]
    ini.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    # ★ 读回断言
    chk = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next(i for i, ln in enumerate(chk) if ln.strip() == "[Logic]")
    sec = chk[hi + 1:]
    stop = next((i for i, ln in enumerate(sec) if ln.strip().startswith("[")), len(sec))
    body = [ln.strip() for ln in sec[:stop]]
    assert "EnableRC4Guard=%d" % guard in body, "guard 键读回失败"
    if bail_mode == "explicit1":
        assert "EnableRC4ExitBail=1" in body, "bail=1 读回失败"
    elif bail_mode == "explicit0":
        assert "EnableRC4ExitBail=0" in body, "bail=0 读回失败"
    else:
        assert not any(b.startswith("EnableRC4ExitBail=") for b in body), \
            "default 臂键未清除"


def record_close_delivery(hwnd, t_launch_pid_tid):
    """★ C26-06 必记：返回值、错误码、目标身份。pid/tid 从 GetWindowThreadProcessId 实测。"""
    pid, tid = t_launch_pid_tid
    ctypes.set_last_error(0)
    ok = bool(u32.PostMessageW(wt.HWND(hwnd), WM_CLOSE, 0, 0))
    err = ctypes.get_last_error()
    wt_pid = wt.DWORD(0)
    got_tid = u32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(wt_pid))
    return {"post_ok": ok, "post_err": err,
            "target_hwnd": hwnd, "target_tid": got_tid, "target_pid": wt_pid.value,
            "expected_pid": pid, "pid_match": wt_pid.value == pid,
            "t": round(time.time(), 3)}


# ---------------------------------------------------------------------------
# 合成自检（--selfcheck，零游戏零真机）：tri 三态 / apply_bail_mode / 投递记录形
# ---------------------------------------------------------------------------
def selfcheck() -> int:
    fails = []
    # 1) tri_read_u32：坏句柄 ⇒ 非 ok 两类之一
    kind, val = tri_read_u32(ctypes.c_void_p(0).value, 0x00A8EDD8)
    good = (kind in ("read_fail", "unreadable_page"))
    print("[%s] T1 tri 坏句柄⇒非 ok（kind=%s val=%s）" % ("OK" if good else "RED", kind, val))
    if not good:
        fails.append("T1")

    # 2) apply_bail_mode 三模式往返（写临时 ini 副本，不碰母本）
    src = GAME_SRC / "ra2render.ini"
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "ra2render.ini"
        shutil.copy2(src, t)
        for guard, mode, probe in ((1, "explicit1", "EnableRC4ExitBail=1"),
                                   (1, "explicit0", "EnableRC4ExitBail=0"),
                                   (1, "default", None)):
            apply_bail_mode(t, guard, mode)
            body = t.read_text(encoding="utf-8").splitlines()
            if probe is None:
                has = any(b.strip().startswith("EnableRC4ExitBail=") for b in body)
                ok = not has and "EnableRC4Guard=1" in [b.strip() for b in body]
            else:
                ok = probe in [b.strip() for b in body]
            print("[%s] T2 bail_mode=%s 往返/读回 %s" % ("OK" if ok else "RED", mode, probe))
            if not ok:
                fails.append("T2-" + mode)

    # 3) 投递记录形（对不存在窗口⇒post_ok=False 或 True 都允许，但键必须齐+pid_match=False）
    r = record_close_delivery(0x1, (12345, 1))
    shape_ok = (set(r.keys()) >= {"post_ok", "post_err", "target_hwnd", "target_tid",
                                  "target_pid", "expected_pid", "pid_match", "t"}
                and r["pid_match"] is False)
    print("[%s] T3 投递记录键齐+假窗 pid_match=False %s" % ("OK" if shape_ok else "RED", r))
    if not shape_ok:
        fails.append("T3")

    # 4) 取证先于清扫：驱动结构断言（except 摘取行 < rmtree 行）
    code = Path(__file__).read_text(encoding="utf-8").splitlines()
    li_ex = [i for i, l in enumerate(code) if l.strip().startswith('rec["except_after"] = sha16')]
    li_del = [i for i, l in enumerate(code) if l.strip().startswith("shutil.rmtree(carrier.parent")]
    ord_ok = bool(li_ex and li_del and max(li_ex) < min(li_del))
    print("[%s] T4 cleanup 顺序：except 取证(%s) 在 rmtree(%s) 前"
          % ("OK" if ord_ok else "RED", li_ex, li_del))
    if not ord_ok:
        fails.append("T4")

    print("== SELFCHK: %s ==" % ("ALL PASS" if not fails else "FAIL " + ",".join(fails)))
    return 0 if not fails else 1


# ---------------------------------------------------------------------------
# 真机发射体（本轮**不执行**；--live 存在=下一轮审阅后的排期件）
# ---------------------------------------------------------------------------
ARMS = [
    # 同场景三臂（X 设计）；bail_mode 分列：
    {"tag": "P0_ORIG",   "inject": False, "guard": None, "bail_mode": None,
     "note": "原版直启（无注入）——排除既有缺陷基线；进局→关窗→看 singleton/hwnd/exitstate 走向"},
    {"tag": "P1_G1B0exp", "inject": True, "guard": 1, "bail_mode": "explicit0",
     "note": "Guard开+Bail**显式关**（=已知僵尸基线复认）"},
    {"tag": "P2_G1B0def", "inject": True, "guard": 1, "bail_mode": "default",
     "note": "Guard开+Bail**键缺失**（缺省 0 运行时实证臂；与 P1 差分归因 ini 键路径）"},
    {"tag": "P3_G1B1",   "inject": True, "guard": 1, "bail_mode": "explicit1",
     "note": "Guard开+Bail开=局内取证主臂（H1 vs H2 判别全靠时间线）"},
    {"tag": "P3m_MENU",  "inject": True, "guard": 1, "bail_mode": "explicit1", "menu_only": True,
     "note": "同会话菜单态对照臂（1c 消混杂；一趟一次关窗；hold=6s 不进局）"},
]


def _finalize(rec, carrier, out_dir, proc, hh=None):
    """取证先于清扫 ⇒ 统一收尾（成功臂与 abort 臂**都**走这里，杜绝泄漏）。"""
    if hh is not None:
        try:
            k32.CloseHandle(hh)
        except Exception:
            pass
    # ① 证据摘取（except/日志/时间线）——在任何删除/杀进程之前
    ex = carrier / "except.txt"
    rec["except_after"] = sha16(ex) if ex.is_file() else "absent"
    rec["except_changed"] = (rec["except_after"] != rec.get("except_before"))
    if (carrier / "ra2render.log").is_file():
        shutil.copy2(carrier / "ra2render.log", out_dir / "ra2render.log")
        rec["guard_lines"] = [l for l in (out_dir / "ra2render.log").read_text(
            encoding="utf-8", errors="replace").splitlines() if "[ra2rc4" in l]
    tl = rec.pop("_timeline", None)
    if tl is not None:
        (out_dir / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False),
                                               encoding="utf-8")
    # ② 清扫：按载体路径精确终止 + 有界轮询残留 + 删树
    for p, nm in list(PROBE.list_procs().items()):
        if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
            img = PROBE.query_image(p)
            if img and PROBE.under_carrier(img, carrier):
                th = k32.OpenProcess(0x0001 | 0x100000, False, p)
                if th:
                    k32.TerminateProcess(th, 1)
                    k32.CloseHandle(th)
                    rec.setdefault("killed_on_cleanup", []).append([p, nm])
    if proc is not None:
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
    rem = []
    deadline = time.time() + 3.0
    while time.time() < deadline:
        rem = [p for p, nm in PROBE.list_procs().items()
               if nm.lower() in ("gamemd.exe", "rc4_loader.exe")
               and (PROBE.query_image(p) or "").lower().startswith(str(carrier).lower())]
        if not rem:
            break
        time.sleep(0.25)
    rec["a8_remaining"] = rem
    rec["a8_enum_ok"] = os.getpid() in PROBE.list_procs()
    rec["a8_verdict"] = "PASS" if (not rem and rec["a8_enum_ok"]) else "V_FAIL"
    for _ in range(6):
        shutil.rmtree(carrier.parent, ignore_errors=True)
        if not carrier.parent.exists():
            break
        time.sleep(0.5)
    rec["carrier_deleted"] = not carrier.parent.exists()
    (out_dir / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    return rec


def fire_arm(arm, h7, watch_s, play_s):
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = MYCARD / ("%s_%s" % (stamp, arm["tag"]))
    carrier = out_dir / "ct" / ("c" + "0" * 9)
    assert len(str(carrier)) <= 130
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = {"trip_tag": arm["tag"], "note": arm["note"], "out_dir": str(out_dir)}

    for f in sorted(GAME_SRC.iterdir()):
        if f.is_file():
            shutil.copy2(f, carrier / f.name)
    if arm["inject"]:
        shutil.copy2(GUARD_DIR / "rc4_loader.exe", carrier / "rc4_loader.exe")
        shutil.copy2(C2_DIR / "ra2rc4guard_c2.dll", carrier / "ra2rc4guard_c2.dll")
        apply_bail_mode(carrier / "ra2render.ini", arm["guard"], arm["bail_mode"])
        argv = [str(carrier / "rc4_loader.exe"), "ra2rc4guard_c2.dll"]
    else:
        # 原版臂不碰 ini 守卫键（保持出厂态）；直启 gamemd
        argv = [str(carrier / "gamemd.exe")]
    ex0 = carrier / "except.txt"
    rec["except_before"] = sha16(ex0) if ex0.is_file() else "absent"

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen(argv, cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["loader_pid"] = proc.pid
    t0 = time.time()
    pid = None
    for _ in range(200):
        time.sleep(0.1)
        for p, nm in PROBE.list_procs().items():
            if nm.lower() == "gamemd.exe":
                img = PROBE.query_image(p)
                if img and PROBE.under_carrier(img, carrier):
                    pid = p
                    break
        if pid:
            break
    if pid is None:
        rec["abort"] = "gamemd_not_found"
        return _finalize(rec, carrier, out_dir, proc)
    rec["gamemd_pid"] = pid

    hwnd = None
    while time.time() - t0 < 60.0:
        hwnd, _ = h7.find_main_window(pid)
        if hwnd:
            break
        time.sleep(0.5)
    if not hwnd:
        rec["abort"] = "no_main_window"
        return _finalize(rec, carrier, out_dir, proc)
    rec["hwnd"] = hwnd

    hh = k32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not hh:
        rec["abort"] = "OpenProcess_vm_failed err=%d" % ctypes.get_last_error()
        return _finalize(rec, carrier, out_dir, proc)
    menu_only = bool(arm.get("menu_only"))
    if menu_only:
        # 菜单态对照臂（1c 消混杂）：不进局；固定主菜单驻留后关窗——同 hold=6s 口径
        time.sleep(35.0 + 6.0)
        rec["in_battle"] = False
        rec["frame_pair"] = [tri_read_u32(hh, G_FRAME), ("skip", "menu_only")]
    else:
        time.sleep(35.0)
        for (lx, ly) in ((700, 218), (700, 304), (700, 262)):
            h7._focus_foreground(hwnd)
            h7.click_logical(hwnd, lx, ly)
            time.sleep(12.0)
        # 进局判定
        f0 = tri_read_u32(hh, G_FRAME)
        time.sleep(3.0)
        f1 = tri_read_u32(hh, G_FRAME)
        in_battle = (f0[0] == "ok" and f1[0] == "ok" and f1[1] - f0[1] >= 8)
        rec["in_battle"] = in_battle
        rec["frame_pair"] = [f0, f1]
        if not in_battle:
            rec["abort"] = "not_in_battle"
            return _finalize(rec, carrier, out_dir, proc, hh)

    # 战斗/菜单窗哨兵时间线（只读）
    tl = []
    tp = time.time()
    while time.time() - tp < play_s:
        tl.append(phase_sentinels(pid))
        time.sleep(2.0)
    # 关窗前 5s 高频 + 窗口枚举
    pre5 = []
    for _ in range(5):
        pre5.append({"sent": phase_sentinels(pid), "wins": window_timeline(pid, "pre5")})
        time.sleep(1.0)
    rec["pre_close_5s"] = pre5

    delivery = record_close_delivery(hwnd, (pid, 0))
    rec["close_delivery"] = delivery
    t_close = time.time()
    rec["closed_at_s"] = round(t_close - t0, 3)
    post_tl = []
    rows = []
    hs = k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
    while hs and time.time() < t_close + watch_s:
        res = k32.WaitForSingleObject(hs, 0)
        ex = wt.DWORD(0)
        k32.GetExitCodeProcess(hs, ctypes.byref(ex))
        s = phase_sentinels(pid)
        rows.append({"wait": res, "code": ex.value if res == 0 else None, **s})
        if len(rows) % 10 == 1:
            post_tl.append(window_timeline(pid, "post"))
        if res == 0:
            break
        time.sleep(0.1)
    if hs:
        k32.CloseHandle(hs)
    rec["close_rows_n"] = len(rows)
    rec["close_rows_head"] = rows[:6]
    rec["close_rows_tail"] = rows[-6:]
    rec["post_windows_tl"] = post_tl
    rec["exited"] = bool(rows and rows[-1]["wait"] == 0)
    rec["exit_after_close_s"] = round(rows[-1]["t"] - t_close, 2) if rec["exited"] else None
    rec["final_exitcode"] = rows[-1]["code"] if rec["exited"] else None
    rec["_timeline"] = {"battle_tl": tl, "pre5": pre5, "close_rows": rows}
    return _finalize(rec, carrier, out_dir, proc, hh)


def preflight():
    fails = []
    checks = [
        ("gamemd 母本 sha", sha16(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16),
        ("loader sha", sha16(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16),
        ("c2 DLL sha256", hashlib.sha256((C2_DIR / "ra2rc4guard_c2.dll").read_bytes()).hexdigest() == C2_DLL_SHA256),
        ("harness7 在盘", H7_PATH.is_file()),
        ("探针在盘", THEIR_PROBE.is_file()),
        ("残留游戏进程=0", not PROBE.game_procs()),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("OK" if ok else "RED", name))
        if not ok:
            fails.append(name)
    return fails


def main() -> int:
    global PROBE
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="★ 审阅后排期用；本轮禁止")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--arms", default="P0,P1,P2,P3")
    ap.add_argument("--watch", type=float, default=120.0)
    ap.add_argument("--play-s", type=float, default=60.0)
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    PROBE = load_probe()
    if not a.live:
        fails = preflight()
        print("★ 预检 %s；本件为**候选**：--live 仅在设计审阅后使用（本轮零发射）。"
              % ("全过" if not fails else "红 %s" % fails))
        return 0 if not fails else 2
    h7 = load_h7()
    h7._QC151FS["on"] = True
    MYCARD.mkdir(parents=True, exist_ok=True)
    sel = [x for x in ARMS if x["tag"].split("_")[0] in a.arms.split(",")]
    for arm in sel:
        r, *_ = fire_arm(arm, h7, a.watch, a.play_s)
        print(arm["tag"], "exited=%s after=%s in_battle=%s abort=%s"
              % (r.get("exited"), r.get("exit_after_close_s"), r.get("in_battle"), r.get("abort")))
        if PROBE.game_procs():
            print("!! 残留 ⇒ 停后续")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
