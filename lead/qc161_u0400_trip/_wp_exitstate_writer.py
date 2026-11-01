#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-09-A 设计输入：exitstate[0xA8EDD8] 写入者 —— 硬件写断点趟（v2，纠三错）。

★ v1 的 S1 自证全灭被推翻，原因是**装置错两处**（[[gate-assert-values-not-existence]]
  同族的"装置坏了当被测物坏了"）：
    (a) S1 孩子=64 位 python，却喂 32 位 CONTEXT 结构 ⇒ SetThreadContext 必废；
    (b) x86 DR7 写掩码候选表是凭记忆（0x10C01/…/0x1）——**真值=0x90001**：
        L0=bit0 | 写条件 bits16-17=01(=0x10000) | 长度 bits18-19=10(4B, =0x80000)。
    (c) 32 位被调试进程在 64 位调试器下必须走 **Wow64Get/SetThreadContext**
        （WOW64_CONTEXT=本件结构，总 0x2CC=716B）；这正是游戏（WOW64）的处境。
★ v2 设计：**游戏本身即自证台**——两级阳性对照，同一条代码路径：
    P1 = [0x00B73550]（hwnd 全局）写断点。ab24 双证 WM_CLOSE 后它被写 0
        （hwnd_before_close 非 0 → hwnd_at_hit=0）⇒ **P1 不中 = 装置死**，
        P2 的 0 命中不作数；
    P2 = [0x00A8EDD8]（exitstate）。P1 命中后当场换装 P2 等它的写。
    S0 = 附加后 Wow64GetThreadContext 能读到游戏主线程 Eip（合理 VA 区间）——
        结构/大小/API 错会在这一步炸，不会拖到发射后。
★ 时序：附加 → 泵事件（CREATE_PROCESS/DLL/初始 bp 全 DBG_CONTINUE）→
    窗口出现(S0+装 P1) → +6 s 投 WM_CLOSE → P1 命中(记录) → 拆 P1 装 P2 →
    P2 命中(记录，收) 或 90 s 无命中(诚实登记) → 拆点 → detach → 定向击杀 → 删载体。
★ 异常继续码：单步(0x80000004)一律 **DBG_CONTINUE**（NOT_HANDLED 会把我的断点
    异常喂给游戏 __except，污染观察——ab24 对真 AV 用 NOT_HANDLED 是有意的，
    这里必须不同）。
★ 复用他线件只读：DEBUG_EVENT/k32/u32/list_procs/query_image/under_carrier。
"""
from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "d09b"
PROBE_PATH = ROOT / "lead" / "qc161_u0400_trip" / "_probe_d09b_hang.py"
THEIR = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"

_spec = importlib.util.spec_from_file_location("pd09b", str(PROBE_PATH))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
_spec2 = importlib.util.spec_from_file_location("rc4ab", str(THEIR))
AB = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(AB)
P.MOD = AB

k32, u32 = AB.k32, AB.u32
DEBUG_EVENT = AB.DEBUG_EVENT

EXCEPTION_DEBUG_EVENT = 1
EXC_SINGLE_STEP = 0x80000004
# ★★ WOW64 下硬件断点命中以 STATUS_WX86_SINGLE_STEP(0x4000001E) 投递，
#   不是 0x80000004（v2 趟的 t=14.23 @0x777814「神秘异常」就是 P1 命中本体，
#   因只匹配 0x80000004 被漏计 ⇒ 假 APPARATUS_DEAD。本行是该误读的定谳）。
WX86_SINGLE_STEP = 0x4000001E
EXC_BREAKPOINT = 0x80000003
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

# WOW64/x86 CONTEXT：CONTEXT_DEBUG_REGISTERS=0x10010；整结构 0x2CC
CTX_DR = 0x00010010
# DR7：L0(bit0)=1，条件 bits16-17=01(写)，长度 bits18-19=10(4 字节)
DR7_WRITE4 = 0x1 | (0b01 << 16) | (0b10 << 18)     # == 0x90001
THREAD_ALL = 0x1F03FF

ADDR_HWND = 0x00B73550
ADDR_EXIT = 0x00A8EDD8
WM_CLOSE = 0x0010


class ctxX86(ctypes.Structure):
    _fields_ = [
        ("ContextFlags", wt.DWORD),
        ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
        ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
        ("FloatSave", ctypes.c_byte * 112),
        ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
        ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
        ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
        ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
        ("ExtendedRegisters", ctypes.c_byte * 512),
    ]

assert ctypes.sizeof(ctxX86) == 0x2CC, ctypes.sizeof(ctxX86)

wow64_get = getattr(k32, "Wow64GetThreadContext", None)
wow64_set = getattr(k32, "Wow64SetThreadContext", None)
if wow64_get is None or wow64_set is None:
    raise SystemExit("Wow64*ThreadContext 不可用 ⇒ 装置前提不成立")
wow64_get.restype = wt.BOOL
wow64_get.argtypes = [wt.HANDLE, ctypes.POINTER(ctxX86)]
wow64_set.restype = wt.BOOL
wow64_set.argtypes = [wt.HANDLE, ctypes.POINTER(ctxX86)]
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.SuspendThread.restype = wt.DWORD
k32.SuspendThread.argtypes = [wt.HANDLE]
k32.ResumeThread.restype = wt.DWORD
k32.ResumeThread.argtypes = [wt.HANDLE]


class TEntry(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", ctypes.c_long), ("tpDeltaPri", ctypes.c_long),
                ("dwFlags", wt.DWORD)]

k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Thread32First.restype = wt.BOOL
k32.Thread32First.argtypes = [wt.HANDLE, ctypes.POINTER(TEntry)]
k32.Thread32Next.restype = wt.BOOL
k32.Thread32Next.argtypes = [wt.HANDLE, ctypes.POINTER(TEntry)]


def thread_ids(pid):
    snap = k32.CreateToolhelp32Snapshot(0x4, 0)
    ids = []
    t = TEntry(); t.dwSize = ctypes.sizeof(t)
    if k32.Thread32First(snap, ctypes.byref(t)):
        while True:
            if t.th32OwnerProcessID == pid:
                ids.append(t.th32ThreadID)
            if not k32.Thread32Next(snap, ctypes.byref(t)):
                break
    k32.CloseHandle(snap)
    return ids


def arm_all(pid, addr, clear=False):
    ok, errs = 0, []
    for tid in thread_ids(pid):
        ht = k32.OpenThread(THREAD_ALL, False, tid)
        if not ht:
            errs.append("open t%d=%d" % (tid, ctypes.get_last_error())); continue
        k32.SuspendThread(ht)
        c = ctxX86(); c.ContextFlags = CTX_DR
        if not wow64_get(ht, ctypes.byref(c)):
            errs.append("get t%d=%d" % (tid, ctypes.get_last_error()))
        else:
            c.Dr7 = 0 if clear else DR7_WRITE4
            c.Dr0 = 0 if clear else addr
            c.Dr6 = 0
            if wow64_set(ht, ctypes.byref(c)):
                ok += 1
            else:
                errs.append("set t%d=%d" % (tid, ctypes.get_last_error()))
        k32.ResumeThread(ht)
        k32.CloseHandle(ht)
    return {"armed": ok, "errors": errs[:6]}


def read_mem(hp, addr, n):
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(hp, ctypes.c_void_p(addr),
                                 ctypes.cast(buf, ctypes.c_void_p), n,
                                 ctypes.byref(got)):
        return None
    return buf.raw[:got.value]


def rpm32(hp, addr):
    b = read_mem(hp, addr, 4)
    return int.from_bytes(b, "little") if b and len(b) == 4 else None


def main() -> int:
    live = "--live" in sys.argv
    out = MYCARD / ("wp2_%s" % time.strftime("%Y%m%dT%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    if not live:
        print("dry-run：DR7_WRITE4=%05X sizeof(ctx)=%X；预检不发射"
              % (DR7_WRITE4, ctypes.sizeof(ctxX86)))
        assert not AB.game_procs()
        assert P.sha16(P.GAME_SRC / "gamemd.exe") == P.GAMEMD_SHA16
        print("预检 OK（残留=0、母本 sha）；加 --live")
        return 0

    assert not AB.game_procs(), AB.game_procs()
    assert P.sha16(P.GAME_SRC / "gamemd.exe") == P.GAMEMD_SHA16
    carrier = out / "ct" / ("c" + "0" * 10)
    assert len(str(carrier)) <= P.CARRIER_PATH_MAX
    P.build_carrier(carrier, [P.GUARD_DIR / "rc4_loader.exe",
                              P.GUARD_DIR / "ra2rc4guard.dll"], 1)
    env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), "ra2rc4guard.dll"],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec = {"out_dir": str(out)}
    pid = None
    for _ in range(150):
        time.sleep(0.1)
        for p, nm in AB.list_procs().items():
            if nm.lower() == "gamemd.exe":
                img = AB.query_image(p)
                if img and AB.under_carrier(img, carrier):
                    pid = p
                    break
        if pid:
            break
    assert pid, "gamemd not found under carrier"
    rec["gamemd_pid"] = pid
    assert k32.DebugActiveProcess(pid), "attach failed"
    hp = k32.OpenProcess(0x0400 | 0x0010, False, pid)

    t0 = time.time()
    st = {"phase": "boot", "close_at": None, "window_at": None, "hwnd": None}
    hits = []
    events = []
    polls = []
    got_ctx_once = False

    def snap_globals(tag):
        row = {"t": round(time.time() - t0, 2), "tag": tag,
               "hwnd": rpm32(hp, ADDR_HWND), "exitstate": rpm32(hp, ADDR_EXIT),
               "singleton": rpm32(hp, 0x00887368)}
        if polls and all(row[k] == polls[-1][k] for k in ("hwnd", "exitstate", "singleton")):
            return
        polls.append(row)

    try:
        while time.time() - t0 < 170.0:
            de = DEBUG_EVENT()
            if not k32.WaitForDebugEvent(ctypes.byref(de), 200):
                if ctypes.get_last_error() == 121:
                    el = time.time() - t0
                    snap_globals(st["phase"])
                    if st["phase"] == "boot" and el > 8.0:
                        gw = [w for w in P.enum_windows_for(pid)
                              if w["class"] == "Yuri's Revenge"]
                        if gw:
                            st["window_at"] = round(el, 2)
                            st["hwnd"] = gw[0]["hwnd"]
                            # S0：主线程 ctx 可读 + Eip 合理
                            ids = thread_ids(pid)
                            if ids:
                                ht = k32.OpenThread(THREAD_ALL, False, ids[0])
                                c = ctxX86(); c.ContextFlags = CTX_DR | 0x00010007
                                if ht and wow64_get(ht, ctypes.byref(c)):
                                    # ★ S0 只证明「WOW64 上下文读得动且是 32 位平坦地址」。
                                    #   启动早期线程合法地停在 ntdll（实测 0x77A1A15C），
                                    #   旧谓词只认游戏镜像区间 0x400000..0xC00000 ⇒ 误杀装置。
                                    got_ctx_once = (0x1000 <= c.Eip < 0x7FFFFFFF)
                                    st["S0_eip"] = hex(c.Eip)
                                if ht:
                                    k32.CloseHandle(ht)
                            if got_ctx_once:
                                st["armP1"] = arm_all(pid, ADDR_HWND)
                                st["phase"] = "armed_P1"
                            else:
                                st["phase"] = "S0_FAILED"
                                break
                    elif st["phase"] == "armed_P1" and el - st["window_at"] >= 6.0:
                        u32.PostMessageW(wt.HWND(st["hwnd"]), WM_CLOSE, 0, 0)
                        st["close_at"] = round(el, 3)
                        st["phase"] = "wait_P1"
                    elif st["phase"] in ("armed_P2", "wait_P2") and \
                            el - (st["close_at"] or 0) > 90.0:
                        st["phase_timeout"] = True
                        break
                continue
            code = de.dwDebugEventCode
            if code == EXCEPTION_DEBUG_EVENT:
                er = de.u.Exception.ExceptionRecord
                ec = int(er.ExceptionCode)
                tid = de.dwThreadId
                if ec in (EXC_SINGLE_STEP, WX86_SINGLE_STEP) and st["phase"] in ("armed_P1", "wait_P1"):
                    ht = k32.OpenThread(THREAD_ALL, False, tid)
                    c = ctxX86(); c.ContextFlags = CTX_DR | 0x00010007
                    okc = bool(ht and wow64_get(ht, ctypes.byref(c)))
                    h = {"phase": "P1_hwnd", "t": round(time.time() - t0, 2),
                         "thread": tid,
                         "dr6": hex(c.Dr6) if okc else None,
                         "eip_next": hex(c.Eip) if okc else None,
                         "eax": hex(c.Eax) if okc else None,
                         "exitstate_now": rpm32(hp, ADDR_EXIT),
                         "hwnd_now": rpm32(hp, ADDR_HWND)}
                    if okc and c.Eip:
                        nb = read_mem(hp, max(0, c.Eip - 24), 32)
                        h["bytes_at_eip"] = nb.hex() if nb else None
                        wb = read_mem(hp, max(0, c.Eip - 16), 16)
                        h["bytes_before"] = wb.hex() if wb else None
                    hits.append(h)
                    if ht:
                        k32.CloseHandle(ht)
                    arm_all(pid, 0, clear=True)
                    st["armP2"] = arm_all(pid, ADDR_EXIT)
                    st["phase"] = "armed_P2"
                    k32.ContinueDebugEvent(de.dwProcessId, tid, DBG_CONTINUE)
                    continue
                if ec in (EXC_SINGLE_STEP, WX86_SINGLE_STEP) and st["phase"] in ("armed_P2", "wait_P2"):
                    ht = k32.OpenThread(THREAD_ALL, False, tid)
                    c = ctxX86(); c.ContextFlags = CTX_DR | 0x00010007
                    okc = bool(ht and wow64_get(ht, ctypes.byref(c)))
                    h = {"phase": "P2_exit", "t": round(time.time() - t0, 2),
                         "thread": tid,
                         "dr6": hex(c.Dr6) if okc else None,
                         "eip_next": hex(c.Eip) if okc else None,
                         "regs": {"eax": hex(c.Eax) if okc else None,
                                  "ecx": hex(c.Ecx) if okc else None,
                                  "edx": hex(c.Edx) if okc else None,
                                  "esi": hex(c.Esi) if okc else None,
                                  "edi": hex(c.Edi) if okc else None,
                                  "esp": hex(c.Esp) if okc else None,
                                  "ebp": hex(c.Ebp) if okc else None},
                         "exitstate_now": rpm32(hp, ADDR_EXIT)}
                    if okc and c.Eip:
                        nb = read_mem(hp, max(0, c.Eip - 24), 32)
                        h["bytes_at_eip"] = nb.hex() if nb else None
                    hits.append(h)
                    if ht:
                        k32.CloseHandle(ht)
                    arm_all(pid, 0, clear=True)
                    st["phase"] = "done_P2"
                    k32.ContinueDebugEvent(de.dwProcessId, tid, DBG_CONTINUE)
                    break
                # ★ v3：任何非 AV 异常在 armed 阶段都全量取证（含 Dr6 与 EIP 字节）。
                #   上一趟在 close 当刻（t=14.224→14.23）出现 0x4000001E @ 0x777814，
                #   而那是被写全局所在块——本趟要判定它是不是 #DB 的另一种投递形态。
                if ec != 0xC0000005 and st["phase"] in ("armed_P1", "wait_P1",
                                                        "armed_P2", "wait_P2"):
                    ht = k32.OpenThread(THREAD_ALL, False, tid)
                    c = ctxX86(); c.ContextFlags = CTX_DR | 0x00010007
                    okc = bool(ht and wow64_get(ht, ctypes.byref(c)))
                    e = {"t": round(time.time() - t0, 2), "code": hex(ec),
                         "addr": int(er.ExceptionAddress or 0), "thread": tid,
                         "phase": st["phase"],
                         "dr6": hex(c.Dr6) if okc else None,
                         "eip": hex(c.Eip) if okc else None,
                         "info": [int(er.ExceptionInformation[i] or 0)
                                  for i in range(int(er.NumberParameters))]}
                    if okc and c.Eip:
                        nb = read_mem(hp, max(0, c.Eip - 24), 32)
                        e["bytes_at_eip"] = nb.hex() if nb else None
                    if ht:
                        k32.CloseHandle(ht)
                    events.append(e)
                else:
                    events.append({"t": round(time.time() - t0, 2), "code": hex(ec),
                                   "addr": int(er.ExceptionAddress or 0),
                                   "thread": tid,
                                   "first": int(de.u.Exception.dwFirstChance)})
                k32.ContinueDebugEvent(de.dwProcessId, tid,
                                        DBG_EXCEPTION_NOT_HANDLED
                                        if ec == 0xC0000005 else DBG_CONTINUE)
            else:
                k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)
    finally:
        rec["state"] = st
        rec["hits"] = hits
        rec["events_tail"] = events[-10:]
        arm_all(pid, 0, clear=True)
        try:
            k32.DebugActiveProcessStop(pid)
        except Exception as e:
            rec["detach_err"] = repr(e)
        k32.CloseHandle(hp)
        for p, nm in list(AB.list_procs().items()):
            if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
                img = AB.query_image(p)
                if img and AB.under_carrier(img, carrier):
                    hh = k32.OpenProcess(0x0001 | 0x100000, False, p)
                    if hh:
                        k32.TerminateProcess(hh, 1)
                        k32.CloseHandle(hh)
        try:
            proc.wait(timeout=6)
        except Exception:
            pass
        deadline = time.time() + 3
        while time.time() < deadline and AB.game_procs():
            time.sleep(0.3)
        rem = [p for p, nm in AB.list_procs().items()
               if nm.lower() in ("gamemd.exe", "rc4_loader.exe")
               and (AB.query_image(p) or "").lower().startswith(str(carrier).lower())]
        rec["a8"] = {"rem": rem, "enum_ok": os.getpid() in AB.list_procs()}
        rec["a8"]["verdict"] = "PASS" if (not rem and rec["a8"]["enum_ok"]) else "V_FAIL"
        for _att in range(6):
            shutil.rmtree(carrier.parent, ignore_errors=True)
            if not carrier.parent.exists():
                break
            time.sleep(0.5)
        rec["leftover"] = AB.game_procs()
        p1 = any(h["phase"] == "P1_hwnd" for h in hits)
        p2 = any(h["phase"] == "P2_exit" for h in hits)
        rec["verdict"] = ("WRITER_HIT" if p2 else
                          ("APPARATUS_OK_WRITER_ABSENT" if p1 else "APPARATUS_DEAD"))
        (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "state": st, "hits": hits,
                      "events_tail": events[-4:], "a8": rec["a8"],
                      "leftover": rec["leftover"]},
                     ensure_ascii=False, indent=1)[:2600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
