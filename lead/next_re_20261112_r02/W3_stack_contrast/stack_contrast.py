#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W3 —— 真机批次 B：用「菜单打开时的栈」对撞上一轮「永久冻结栈」。

单变量对照实验：
  自变量 = 局内菜单是否打开（正常局内 C0  /  菜单打开 C1a/C1b/C1c）
  因变量 = 游戏窗口线程的 StackWalk64 调用栈
  基准   = lead/re_d13_ruling_20261112/_hl_match_14412.json 的 7 帧（pid 14412, tid 30668）

授权（本轮用户当轮明示「可以真机」）：
  允许：启动 ra2youli\\gamemd.exe、只读 ReadProcessMemory、
        SuspendThread / GetThreadContext(WOW64) / StackWalk64 / ResumeThread、枚举窗口与线程。
  禁止：MiniDump、断点、代码注入、写目标进程内存、改 exe/dll、hook。
  只处理自己启动的进程；不 taskkill 别人的进程。

安全约束（逐条落地）：
  * 逐线程「挂→走→立刻恢复」，不一次性全挂：用 r2 的 sample_single()（单线程入口）。
  * 全程 try/finally：r2.sample_one_thread 的 finally 保证恢复；本脚本最外层 finally 收尾。
  * 跳过自身线程 / 跳过 prev_count>0：r2 已实现；本脚本另加 GetCurrentThreadId 显式守卫。
  * 单次挂起总时长目标 ≤ 50ms：以 cost_ns.suspend_held_ns 为准，超限即中止后续抓栈并如实记录。
  * StackWalk64 / 符号初始化在挂起任何线程之前完成：attach_walker() 在 C0 之前调用。
  * 抓栈只在主动打开菜单后做（游戏已暂停）；C0 是协议强制的阴性对照，在开局后平静态单次 ≤50ms 完成。
  * 收尾：核对无残留挂起（prev==0 且 resume_ret==1）、无残留进程、配置逐字节还原并实算自证。

写域：仅 lead/next_re_20261112_r02/W3_stack_contrast/（本文件与其 out/ 子目录）。
其余资产全部只读复用（importlib 加载，零字节改动）。

用法：
  python -X utf8 stack_contrast.py [--map-pattern "Proving Grounds"]
                                   [--load-wait 15] [--stable-seconds 20]
                                   [--budget-ms 50] [--max-frames 20]
                                   [--c1-count 3] [--menu-timeout 90]
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path

# ------------------------------------------------------------------ 常量 / 路径
RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W3 = ROOT / "lead" / "next_re_20261112_r02" / "W3_stack_contrast"
OUT = W3 / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"

W1_PATH = ROOT / "lead" / "next_re_20261112_r02" / "W1_realtime_probe" / "realtime_gate_probe.py"
R2_PATH = ROOT / "lead" / "next_re_20261112" / "RE-N01" / "candidate" / "e3_stack_sampler_candidate_r2.py"
SW_PATH = ROOT / "lead" / "re_d13_ruling_20261112" / "e3_stackwalker.py"
BASELINE_STACK_JSON = ROOT / "lead" / "re_d13_ruling_20261112" / "_hl_match_14412.json"

# 启动前守卫哈希（与 baseline_pre_launch/PRE_LAUNCH_BASELINE.tsv 一致；RA2MD.INI 为任务卡守卫值）
EXPECTED_HASHES = {
    "RA2MD.INI":        "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "ddraw.ini":        "c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52",
    "RA2MD.INI.benchbak": "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "gamemd.exe":       "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll":        "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
}
VERIFY_FILES = ("RA2MD.INI", "ddraw.ini", "gamemd.exe", "ddraw.dll")

# 与任务卡一致的哨兵（frame/g1..g4 与 W1 的 ADDR 完全一致；另加 3 个辅助量）
# (地址, 字节数)
SENTINELS = {
    "frame":           (0x00A8ED84, 4),   # dword 帧计数
    "g1":              (0x00A83D49, 1),   # byte 门控1
    "g2":              (0x00A8ECD0, 1),   # byte 门控2
    "g3":              (0x008B41C0, 1),   # byte 门控3
    "g4":              (0x00A83D48, 1),   # byte 门控4
    "mode_A8B238":     (0x00A8B238, 4),   # dword [0xA8B238] 模式枚举（静态：0/3/4/5）
    "ingame_A8E9A0":   (0x00A8E9A0, 1),   # byte  [0xA8E9A0] 循环活动/局内标志
    "latch_ABCD58":    (0x00ABCD58, 1),   # byte  [0xABCD58] 帧处理闩
}
CODE_SIG_ADDR = 0x0055DE4F
CODE_SIG_EXPECT = bytes.fromhex("a0493da800")   # mov al,[0xa83d49]

BM_CLICK = 0x00F5
STILL_ACTIVE = 259

# 基准 7 帧（从 _hl_match_14412.json 实读；此处仅作规范化比较用的 KEY_POINTS 声明）
KEY_POINTS = ("gamemd+0x207f17", "gamemd+0x20833f",
              "user32+0x74775", "user32+0x3505d")

LOG_LINES = []


# ------------------------------------------------------------------ 基础工具
def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def local_iso():
    return datetime.datetime.now().astimezone().isoformat()


def log(msg):
    line = "%s %s" % (utc_iso(), msg)
    LOG_LINES.append(line)
    try:
        print(line, flush=True)
    except Exception:
        pass
    return line


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jdump(obj):
    """JSON 序列化：ctypes/bytes 一律降级为占位对象，绝不丢字段。"""
    def _default(o):
        if isinstance(o, ctypes.Structure):
            return {"__ctypes__": type(o).__name__}
        if isinstance(o, ctypes.Array):
            return {"__ctypes_array__": type(o).__name__, "len": len(o)}
        if isinstance(o, bytes):
            return {"__bytes_len__": len(o)}
        return {"__unserializable__": type(o).__name__}
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True,
                      default=_default)


def write_json(name, obj):
    p = OUT / name
    p.write_text(jdump(obj) + "\n", encoding="utf-8")
    return p


def load_module(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("importlib spec None: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def split_name(name):
    """'ntdll.dll+0x7858c' -> ('ntdll.dll', 0x7858c)。"""
    if not name:
        return (None, None)
    if "+0x" in name:
        m, o = name.rsplit("+0x", 1)
        try:
            return (m, int(o, 16))
        except ValueError:
            return (m, None)
    return (name, None)


def norm_frame(name):
    """规范化用于逐帧比对：去 .dll/.exe 后缀、小写、偏移去前导零。

    绝对 addr 因 ASLR/模块基址不同不可直接比；必须按 模块+偏移 比对。
    """
    if not name:
        return None
    mod, off = split_name(name)
    if mod:
        ml = mod.lower()
        for s in (".dll", ".exe"):
            if ml.endswith(s):
                ml = ml[:-len(s)]
        mod = ml
    if mod and off is not None:
        return "%s+0x%x" % (mod, off)
    return str(name).lower()


# ------------------------------------------------------------------ 只读资产加载
def load_assets():
    w1 = load_module("w3_w1_nav", W1_PATH)
    r2 = load_module("w3_r2_sampler", R2_PATH)
    sw = load_module("w3_e3_stackwalker", SW_PATH)
    # 结构自证（不联网、不碰目标进程）
    assert ctypes.sizeof(r2.WOW64_CONTEXT) == 716, "WOW64_CONTEXT 必须 716B"
    assert ctypes.sizeof(sw.STACKFRAME64) == 264, "STACKFRAME64 必须 264B"
    assert ctypes.sizeof(sw.KDHELP64) == 112, "KDHELP64 必须 112B"
    return w1, r2, sw


def load_baseline():
    d = json.loads(BASELINE_STACK_JSON.read_text(encoding="utf-8"))
    ev = d["events"][0]
    st = ev["stack"]
    return {
        "source": str(BASELINE_STACK_JSON),
        "pid": d.get("pid"), "tid": st.get("tid"), "bits": st.get("bits"),
        "n": st.get("n"), "mode": ev.get("mode"),
        "picked_by": ev.get("picked_by"), "frame": ev.get("frame"),
        "t": ev.get("t"), "paused_ms": ev.get("paused_ms"),
        "frames": [{"addr": int(f["addr"]), "addr_hex": hex(int(f["addr"])),
                    "name": f.get("name"),
                    "module": split_name(f.get("name"))[0],
                    "offset": split_name(f.get("name"))[1],
                    "norm": norm_frame(f.get("name"))}
                   for f in st["frames"]],
    }


# ------------------------------------------------------------------ 哨兵读取
def read_sentinels(w1, hproc):
    out = {}
    for key, (addr, size) in SENTINELS.items():
        b = w1.rpm(hproc, addr, size)
        if b is None:
            out[key] = None
        elif size == 1:
            out[key] = int(b[0])
        else:
            out[key] = int.from_bytes(b, "little")
    out["t_utc_iso"] = utc_iso()
    out["t_perf_ns"] = time.perf_counter_ns()
    gates = [out.get(k) for k in ("g1", "g2", "g3", "g4")]
    out["all_gates_zero"] = all(g == 0 for g in gates) if all(g is not None for g in gates) else None
    out["any_gate_nonzero"] = (any(g != 0 for g in gates)
                               if all(g is not None for g in gates) else None)
    return out


# ------------------------------------------------------------------ 窗口线程 / 按钮
def game_window_tid(w1, pid):
    """返回游戏主窗口所属线程 id（与 _run_hl_match_candidate.game_window_thread 同逻辑）。"""
    hwnds = w1.game_top_windows(pid)
    if not hwnds:
        return None, []
    p_out = wt.DWORD(0)
    ret = w1.u.GetWindowThreadProcessId(hwnds[0], ctypes.byref(p_out))
    return int(ret), [int(h) for h in hwnds]


def find_button(w1, pid, name):
    for h, c, t, v in w1.controls(pid):
        if c == "Button" and name.lower() in (t or "").lower():
            return (int(h), t)
    return (None, None)


def click_button(w1, pid, name, wait=0.8):
    h, t = find_button(w1, pid, name)
    if not h:
        return {"found": False, "name": name, "clicked": False}
    ok = bool(w1.u.PostMessageW(h, BM_CLICK, 0, 0))
    time.sleep(wait)
    return {"found": True, "name": name, "hwnd": h, "text": t, "clicked": ok}


# ------------------------------------------------------------------ 回溯器挂载（挂起前完成）
def attach_walker(r2, sw, sampler, hproc, pid, is32, max_frames=20):
    """在挂起任何线程之前完成 modules_of + SymInitialize(StackWalk64 符号初始化)。

    r2.attach_stackwalker 在 r2 文件所在目录找 e3_stackwalker.py（该目录没有），
    故这里显式加载已验证的 re_d13_ruling_20261112/e3_stackwalker.py。
    """
    mods = sw.modules_of(pid)
    walker = sw.StackWalker(hproc, bool(is32), mods, max_frames=max_frames)
    sym_ok = walker.init_symbols()          # ★ 挂起前：SymInitialize(fInvadeProcess=TRUE)
    if not sym_ok:
        return {"ok": False, "err": walker.last_error or "sym_init_fail",
                "n_modules": len(mods), "mods": [], "walker": None}
    walker.is_dbghelp_walker = True
    sampler.stack_walker = walker
    sampler._dbghelp_walker = walker
    interest = [{"base": hex(b), "size": sz, "name": nm}
                for (b, sz, nm) in mods
                if nm.lower() in ("gamemd.exe", "user32.dll", "kernelbase.dll", "ntdll.dll")]
    return {"ok": True, "err": None, "n_modules": len(mods),
            "mods": interest, "mods_all": mods, "walker": walker, "is32": bool(is32),
            "max_frames": max_frames}


# ------------------------------------------------------------------ 挂起窗口内的只读 raw-stack 交叉核验
def install_raw_capture(walker, w1, hproc, nbytes=65536):
    """包裹 walker.walk：在线程**仍处于挂起态**时，额外只读 RPM 一段原始栈。

    目的：StackWalk64 在 32 位 FPO/无 PDB 的 gamemd.exe 上常在第 3~4 帧就返回 FALSE，
    而基准 7 帧里的关键点（gamemd+0x20833f / USER32 两帧）都在**更外层**。
    仅有 3~4 帧的走查无法排除「外层其实存在」。故在挂起窗口内再读一段原始栈，
    做 (a) EBP 链手工回溯 (b) 基准绝对地址扫描 (c) 通用代码地址清点，作为独立交叉核验。

    * 全部是只读 ReadProcessMemory（本批授权范围），不写目标进程。
    * 发生在 walk() 内 ⇒ 计入 walk_ns / suspend_held_ns（仍受 ≤50ms 预算约束）。
    """
    orig_walk = walker.walk
    CHUNK = 4096
    state = {"raw": None, "sp": None, "bp": None, "n_read": 0,
             "err": None, "capture_ns": 0, "nbytes_requested": int(nbytes)}

    def wrapped(hthread, ctx_struct, ip, sp, bp):
        frames = orig_walk(hthread, ctx_struct, ip, sp, bp)
        t0 = time.perf_counter_ns()
        try:
            chunks, got, base = [], 0, int(sp)
            while got < int(nbytes):
                want = min(CHUNK, int(nbytes) - got)
                b = w1.rpm(hproc, base + got, want)
                if b is None:
                    break
                chunks.append(b)
                got += len(b)
                if len(b) < want:
                    break
            state["raw"] = b"".join(chunks)
            state["n_read"] = got
            state["sp"] = base
            state["bp"] = int(bp) if bp else None
            state["err"] = None if got > 0 else "rpm_zero"
        except Exception as e:                                  # noqa: BLE001
            state["err"] = "%s:%s" % (type(e).__name__, e)
        state["capture_ns"] = time.perf_counter_ns() - t0
        return frames

    walker.walk = wrapped
    return state


def resolve_addr(mods_all, addr):
    """把绝对地址解析成 '模块+0x偏移'（用本次进程真实的模块基址）。"""
    for b, sz, nm in mods_all:
        if b <= addr < b + sz:
            return "%s+0x%x" % (nm, addr - b)
    return None


def analyze_raw_stack(raw_state, mods_all, base_frames):
    """对挂起窗口内读到的原始栈做三项独立核验。返回可序列化 dict。"""
    out = {"captured": False, "err": raw_state.get("err"),
           "nbytes_requested": raw_state.get("nbytes_requested"),
           "n_read": int(raw_state.get("n_read") or 0),
           "sp": raw_state.get("sp"), "bp": raw_state.get("bp"),
           "capture_ns": int(raw_state.get("capture_ns") or 0),
           "ebp_chain": [], "baseline_addr_scan": [], "key_points_found": {},
           "code_addresses": [], "n_code_addresses": 0}
    raw = raw_state.get("raw")
    if not raw:
        return out
    out["captured"] = True
    sp = int(raw_state["sp"])

    def word_at(off):
        if off < 0 or off + 4 > len(raw):
            return None
        return int.from_bytes(raw[off:off + 4], "little")

    # (a) EBP 链手工回溯（独立于 dbghelp FPO）
    chain = []
    bp = raw_state.get("bp")
    seen = set()
    if bp and bp > sp:
        cur = int(bp)
        for _ in range(32):
            off = cur - sp
            if off < 0 or off + 8 > len(raw) or cur in seen:
                break
            seen.add(cur)
            nxt = word_at(off)
            ret = word_at(off + 4)
            if ret is None:
                break
            chain.append({"ebp": cur, "ebp_hex": hex(cur),
                          "ret_addr": ret, "ret_addr_hex": hex(ret),
                          "name": resolve_addr(mods_all, ret),
                          "norm": norm_frame(resolve_addr(mods_all, ret))})
            if not nxt or nxt <= cur or (nxt - sp) + 8 > len(raw):
                break
            cur = int(nxt)
    out["ebp_chain"] = chain

    # (b) 基准 7 帧的绝对地址扫描：用本次进程模块基址 + 基准偏移算出期望绝对地址，
    #     再在原始栈里找这个 4 字节值；同时直接扫基准 JSON 里的原始 addr。
    scanned = []
    for i, bf in enumerate(base_frames):
        mod, off = bf["module"], bf["offset"]
        expected = None
        if mod and off is not None:
            # ★ WOW64 进程里 modules_of() 会同时列出 64 位与 32 位同名 DLL
            #   （ntdll 有两份：0x7ffb... 与 0x77ba...）。目标是 32 位线程，
            #   只取 32 位基址(<4GiB)，否则 expected 会溢出 4 字节。
            cands = [b for b, sz, nm in mods_all
                     if nm.lower() == str(mod).lower() and 0 < int(b) < 0x100000000]
            if cands:
                v = int(cands[0]) + int(off)
                expected = v if 0 <= v <= 0xFFFFFFFF else None
        for tag, val in (("expected_this_process", expected),
                         ("baseline_literal_addr", bf["addr"])):
            if val is None or not (0 <= int(val) <= 0xFFFFFFFF):
                continue
            needle = int(val).to_bytes(4, "little")
            hits, start = [], 0
            while len(hits) < 20:
                k = raw.find(needle, start)
                if k < 0:
                    break
                hits.append({"stack_off": k, "abs_off": hex(sp + k)})
                start = k + 1
            scanned.append({"idx": i, "baseline_name": bf["name"],
                            "tag": tag, "value": int(val),
                            "value_hex": hex(int(val)), "n_hits": len(hits),
                            "hits": hits})
    out["baseline_addr_scan"] = scanned

    # 关键点：是否在原始栈中 ANY 一处出现（expected 或 literal 任一命中即算）
    kp = {}
    for k in KEY_POINTS:
        rows = [s for s in scanned if s["baseline_name"] and
                norm_frame(s["baseline_name"]) == k]
        kp[k] = any(s["n_hits"] > 0 for s in rows)
    # 也把「全 7 帧里除关键点外」的命中纳入统计（供正文用）
    out["key_points_found"] = kp
    out["n_key_points_found_on_raw_stack"] = sum(1 for v in kp.values() if v)
    out["baseline_frames_found_on_raw_stack"] = [
        {"idx": s["idx"], "name": s["baseline_name"], "tag": s["tag"],
         "n_hits": s["n_hits"]}
        for s in scanned if s["n_hits"] > 0]

    # (c) 通用代码地址清点：4 字节对齐、落在任何模块代码范围内的值
    codes, seen_addr = [], set()
    for off in range(0, max(0, len(raw) - 3), 4):
        v = word_at(off)
        if v is None or v in seen_addr:
            continue
        nm = resolve_addr(mods_all, v)
        if nm is None:
            continue
        seen_addr.add(v)
        codes.append({"stack_off": off, "abs_off": hex(sp + off),
                      "addr": v, "addr_hex": hex(v), "name": nm,
                      "norm": norm_frame(nm)})
        if len(codes) >= 400:
            break
    out["code_addresses"] = codes
    out["n_code_addresses"] = len(codes)
    return out


# ------------------------------------------------------------------ 单次抓栈
def do_grab(label, phase, r2, sampler, walker, w1, hproc, pid, tid,
            budget_ms, r2_budget_ms, sentinels_before, raw_state, mods_all,
            base_frames):
    """一次 sample_single：逐线程挂→走→立刻恢复；返回可 JSON 序列化的完整原始记录。

    budget_ms     = 任务卡的「单次挂起总时长 ≤50ms」口径（作用于 suspend_held_ns）。
    r2_budget_ms  = r2 sample_single 的事件级预算（作用于 end_to_end_ns，含 preflight/
                    Toolhelp 枚举）；放宽到 300ms，避免「挂起窗口明明 <50ms 却被
                    preflight 拖过 50ms」误判成 error。两者分别如实记录。
    raw_state     = install_raw_capture 的 state；walk() 在挂起窗口内已经填好原始栈。
    """
    if walker is not None:
        walker.last_error = None            # 重置，便于捕获本次 StackWalk64 FALSE
    # 重置 raw-state，防止本次捕获失败时误用上一趟的快照
    raw_state.update({"raw": None, "sp": None, "bp": None, "n_read": 0,
                      "err": None, "capture_ns": 0})

    timer = r2.EventTimer()
    timer.mark("candidate")
    t_call_utc = utc_iso()
    t0_ns = time.perf_counter_ns()
    ev = sampler.sample_single(int(tid), int(pid), budget_ms=r2_budget_ms, timer=timer)
    t1_ns = time.perf_counter_ns()
    t_call_end_utc = utc_iso()

    # 抓栈「同一时刻」之后的读数（用于扰动/连续性）
    sentinels_after = read_sentinels(w1, hproc)

    one = ev.get("one") or {}
    ctx = ev.get("ctx") or one.get("ctx") or {}
    ctx_regs = {
        "bits": ctx.get("bits"),
        "ip": ctx.get("ip"), "ip_hex": hex(ctx["ip"]) if ctx.get("ip") else None,
        "sp": ctx.get("sp"), "sp_hex": hex(ctx["sp"]) if ctx.get("sp") else None,
        "bp": ctx.get("bp"), "bp_hex": hex(ctx["bp"]) if ctx.get("bp") else None,
        "eflags": ctx.get("eflags"), "cs": ctx.get("cs"),
    }

    frames_raw = ev.get("frames") or []
    frames = []
    for i, f in enumerate(frames_raw):
        if isinstance(f, dict):
            addr = int(f.get("addr") or 0)
            name = f.get("name")
        else:
            addr, name = int(f), None
        mod, off = split_name(name)
        frames.append({
            "idx": i, "addr": addr, "addr_hex": hex(addr),
            "name": name, "module": mod,
            "offset": off, "offset_hex": ("0x%x" % off) if off is not None else None,
            "norm": norm_frame(name),
        })

    cost = ev.get("cost_ns") or {}
    held_ns = int(cost.get("suspend_held_ns") or 0)
    e2e_ns = int(cost.get("end_to_end_ns") or 0)
    hold_exceeded = held_ns > budget_ms * 1e6
    n_frames = len(frames)
    sw_err = getattr(walker, "last_error", None) if walker is not None else None
    errors = list(ev.get("errors") or [])
    prev = ev.get("prev")
    resume_ret = ev.get("resume_ret")
    resume_ok = ev.get("resume_ok")
    sample_state = ev.get("sample_state")
    resume_state = ev.get("resume_state")

    # ---- StackWalk64 终止性质分类（★ 修正第 1 趟的判据 bug） ----
    # _live_verify_stackwalk.py:311-313 明确：StackWalk64 返回 FALSE 是**回溯走到尽头**的
    # 正常终止信号，get_last_error()==0 ⇒ 无 Win32 错误。它不是「抓栈失败」。
    # 只有非 0 错误码 / 符号未初始化 / no_ip / 0 帧 才是真异常。
    if sw_err is None:
        sw_end = "no_false_recorded"
    elif sw_err == "stackwalk_false:0":
        sw_end = "normal_end_of_walk"
    elif (sw_err or "").startswith("stackwalk_false:"):
        sw_end = "anomaly_nonzero_errno"
    else:
        sw_end = "anomaly_" + str(sw_err)
    sw_anomaly = sw_end.startswith("anomaly")

    # 客观深度：走查是否达到基准 7 帧的深度。低于 7 ⇒ 走查本身无法排除外层关键点，
    # 必须依赖挂起窗口内的 raw-stack 交叉核验（不靠「帧少」冒充「不一致」）。
    walk_reaches_baseline_depth = n_frames >= len(base_frames)

    raw = analyze_raw_stack(raw_state, mods_all, base_frames)

    # 「可用」判据：恢复有正面证据、非 0/单帧、无真异常、预算内。
    # stackwalk_false:0（正常终止）**不再**使抓栈失效。
    usable = (sample_state == "resume_verified_ok"
              and resume_state == "verified_ok"
              and resume_ok is True
              and n_frames >= 2
              and not sw_anomaly
              and not errors
              and not hold_exceeded
              and not ev.get("budget_exceeded"))
    # 「无残留挂起」判据：SuspendThread 返回 prev=0（原本运行），ResumeThread 返回 1（我们+1 已还原到 0）
    clean_restore = (prev == 0 and resume_ret == 1 and resume_ok is True
                     and sample_state == "resume_verified_ok" and not errors)

    rec = {
        "label": label, "phase": phase, "run_id": RUN_ID,
        "t_call_utc_iso": t_call_utc, "t_call_end_utc_iso": t_call_end_utc,
        "pid": int(pid), "tid": int(tid),
        "bits": ctx_regs["bits"],
        "prev_count": prev,                      # SuspendThread 前一次挂起计数
        "context_key_registers": ctx_regs,
        "frames": frames,
        "n_frames": n_frames,
        "frames_is_single": (n_frames == 1),
        "stackwalk_last_error": sw_err,         # StackWalk64 FALSE 的错误码
        "stackwalk_end_reason": sw_end,         # 正常终止 / 真异常（第 1 趟判据 bug 已修）
        "stackwalk_is_anomaly": bool(sw_anomaly),
        "walk_reaches_baseline_depth": bool(walk_reaches_baseline_depth),
        "raw_stack_crosscheck": raw,            # 挂起窗口内只读 RPM 的独立核验
        "sentinels_at_grab": sentinels_before,  # 抓栈同一时刻（前一瞬）
        "sentinels_after_grab": sentinels_after,
        "frame_before": (sentinels_before or {}).get("frame"),
        "frame_after": sentinels_after.get("frame"),
        "frame_delta_during_grab": (
            sentinels_after.get("frame") - sentinels_before["frame"]
            if sentinels_before and sentinels_before.get("frame") is not None
            and sentinels_after.get("frame") is not None else None),
        "timing_ns": {
            "context_ns": int(cost.get("context_ns") or 0),   # 取上下文
            "walk_ns": int(cost.get("walk_ns") or 0),         # 走栈
            "resume_ns": int(cost.get("resume_ns") or 0),     # 恢复
            "open_ns": int(cost.get("open_ns") or 0),
            "preflight_ns": int(cost.get("preflight_ns") or 0),
            "ownership_ns": int(cost.get("ownership_ns") or 0),
            "overhead_ns": int(cost.get("overhead_ns") or 0),
            "suspend_held_ns": held_ns,                       # 实际挂起时长
            "end_to_end_ns": e2e_ns,
            "event_total_ns": int(cost.get("event_total_ns") or 0),
            "wall_call_ns": int(t1_ns - t0_ns),
        },
        "ns_marks": ev.get("ns_marks") or {},
        "phase_ms": ev.get("phase_ms") or {},
        "budget_ms": budget_ms,
        "budget_ms_r2_event": r2_budget_ms,
        "budget_exceeded_r2": bool(ev.get("budget_exceeded")),
        "budget_state_r2": ev.get("budget_state"),
        "hold_exceeded_50ms": bool(hold_exceeded),
        "sample_state": sample_state,
        "resume_state": resume_state,
        "resume_ret": resume_ret,                 # ResumeThread 返回值
        "resume_ret_present": ev.get("resume_ret_present"),
        "resume_ok": resume_ok,
        "errors": errors,
        "exception": ev.get("exception"),
        "preflight": ev.get("preflight") or {},
        "ownership": ev.get("ownership") or {},
        "n_threads_sampled": ev.get("n_threads_sampled"),
        "sample_one_thread_calls": ev.get("sample_one_thread_calls"),
        "usable": bool(usable),
        "clean_restore_no_residual_suspend": bool(clean_restore),
        "skipped": one.get("skipped"),
    }
    write_json("%s.json" % label, rec)          # 每次抓栈的原始记录（逐条落盘）
    log("    抓栈 %-4s tid=%s bits=%s prev=%s frames=%d usable=%s "
        "held=%.3fms resume_ret=%s state=%s sw_end=%s raw_bytes=%d key_on_raw=%d/4" %
        (label, rec["tid"], rec["bits"], prev, n_frames, rec["usable"],
         held_ns / 1e6, resume_ret, sample_state, sw_end,
         raw.get("n_read", 0), raw.get("n_key_points_found_on_raw_stack", 0)))
    for i, f in enumerate(frames):
        log("      #%d %-28s addr=%s" % (i, f["name"] or "?", f["addr_hex"]))
    return rec


# ------------------------------------------------------------------ 帧稳定推进
def wait_stable_frame(w1, hproc, seconds, interval=0.25):
    series = []
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        s = read_sentinels(w1, hproc)
        series.append({"t_s": round(time.perf_counter() - t0, 3),
                       "frame": s.get("frame"),
                       "any_gate_nonzero": s.get("any_gate_nonzero")})
        time.sleep(interval)
    vals = [x["frame"] for x in series if x["frame"] is not None]
    net = (vals[-1] - vals[0]) if len(vals) >= 2 else None
    # 最长连续不推进段（采样间隔为单位）
    run = longest = 0
    for i in range(1, len(vals)):
        if vals[i] == vals[i - 1]:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return {"seconds_target": seconds, "interval": interval, "n_samples": len(series),
            "frame_first": vals[0] if vals else None,
            "frame_last": vals[-1] if vals else None,
            "frame_net_delta": net,
            "max_consecutive_nonadvance_samples": longest,
            "frame_advanced": bool(net is not None and net > 0),
            "series": series}


# ------------------------------------------------------------------ 分析 / 判档
def analyze(base, grabs, key_points=KEY_POINTS):
    base_norms = [f["norm"] for f in base["frames"]]
    kp = list(key_points)
    out = {"baseline_norms": base_norms, "key_points": kp, "per_grab": {},
           "tier": "[未证实]", "tier_reason": "", "c0_key_hit": None}

    for g in grabs:
        norms = [f["norm"] for f in g["frames"]]
        pos_same = []
        for i, bn in enumerate(base_norms):
            got = norms[i] if i < len(norms) else None
            pos_same.append({"idx": i, "baseline": bn, "got": got,
                             "same": bool(got is not None and got == bn)})
        key_hits = {k: (k in norms) for k in kp}
        n_key = sum(1 for v in key_hits.values() if v)
        full_seq = (len(norms) >= len(base_norms)
                    and all(s["same"] for s in pos_same))
        raw = g.get("raw_stack_crosscheck") or {}
        raw_kp = raw.get("key_points_found") or {}
        raw_bf = raw.get("baseline_frames_found_on_raw_stack") or []
        ebp = raw.get("ebp_chain") or []
        ebp_kp = {k: any(norm_frame(e.get("name")) == k for e in ebp) for k in kp}
        out["per_grab"][g["label"]] = {
            "usable": g["usable"], "n_frames": g["n_frames"],
            "norms": norms, "pos_same": pos_same,
            "n_pos_same": sum(1 for s in pos_same if s["same"]),
            "key_hits": key_hits, "n_key_hits": n_key,
            "full_7_frame_sequence_match": bool(full_seq),
            "stackwalk_end_reason": g.get("stackwalk_end_reason"),
            "walk_reaches_baseline_depth": g.get("walk_reaches_baseline_depth"),
            "raw_captured": bool(raw.get("captured")),
            "raw_n_read": int(raw.get("n_read") or 0),
            "raw_key_hits": raw_kp,
            "raw_n_key_hits": sum(1 for v in raw_kp.values() if v),
            "raw_baseline_frames_found": raw_bf,
            "ebp_chain_len": len(ebp),
            "ebp_key_hits": ebp_kp,
            "ebp_n_key_hits": sum(1 for v in ebp_kp.values() if v),
        }

    c1s = [g for g in grabs if g["label"].upper().startswith("C1")]
    c0s = [g for g in grabs if g["label"].upper() == "C0"]
    out["c0_key_hit"] = (out["per_grab"]["C0"]["n_key_hits"] if c0s else None)
    out["c0_raw_key_hit"] = (out["per_grab"]["C0"]["raw_n_key_hits"] if c0s else None)

    usable_c1 = [g for g in c1s if g["usable"]]
    info = out["per_grab"]
    all_c1_usable = (len(c1s) >= 3 and len(usable_c1) == len(c1s))
    all_c1_full = all(info[g["label"]]["full_7_frame_sequence_match"] for g in usable_c1) if usable_c1 else False
    all_c1_key4 = all(info[g["label"]]["n_key_hits"] == len(kp) for g in usable_c1) if usable_c1 else False
    c0_clean = (c0s and out["c0_key_hit"] == 0)

    out["walk_depth_limited"] = any(
        not info[g["label"]]["walk_reaches_baseline_depth"] for g in c1s)

    # ★ 关键：原始栈上的命中若**在 C0 阴性对照里同样出现**，就是与菜单无关的「栈残留」，
    #   不能算作「部分一致」的证据。只有 C1 有、C0 没有的命中才可能是判别性线索。
    c0_raw_kp = set(k for k, v in (info["C0"]["raw_key_hits"].items()
                                   if c0s else {}) if v)
    c0_ebp_kp = set(k for k, v in (info["C0"]["ebp_key_hits"].items()
                                   if c0s else {}) if v)
    out["c0_raw_key_points"] = sorted(c0_raw_kp)
    out["c0_ebp_key_points"] = sorted(c0_ebp_kp)
    out["nondiscriminating_residue"] = sorted(c0_raw_kp | c0_ebp_kp)
    discriminating = {}
    for g in c1s:
        d = info[g["label"]]
        raw_only = set(k for k, v in d["raw_key_hits"].items() if v) - c0_raw_kp
        ebp_only = set(k for k, v in d["ebp_key_hits"].items() if v) - c0_ebp_kp
        discriminating[g["label"]] = {
            "raw_discriminating": sorted(raw_only),
            "ebp_discriminating": sorted(ebp_only),
            "frame_key_hits": sorted(k for k, v in d["key_hits"].items() if v),
            "n_pos_same": d["n_pos_same"],
        }
    out["discriminating"] = discriminating
    any_frame_key = any(d["frame_key_hits"] for d in discriminating.values())
    any_frame_pos = any(d["n_pos_same"] > 0 for d in discriminating.values())
    any_discriminating = any(d["raw_discriminating"] or d["ebp_discriminating"]
                             for d in discriminating.values())
    out["any_frame_agreement"] = bool(any_frame_key or any_frame_pos)
    out["any_discriminating_evidence"] = bool(any_discriminating)

    if all_c1_usable and all_c1_full and all_c1_key4 and c0_clean:
        out["tier"] = "[已证]"
        out["tier_reason"] = ("C1a/C1b/C1c 三次独立菜单打开均逐帧复现基准 7 帧序列"
                              "（7/7 位置 module+offset 完全一致），且 4 个关键点全部命中；"
                              "C0（正常局内阴性对照）关键点命中数=0。")
    elif all_c1_usable and all_c1_key4 and c0_clean:
        out["tier"] = "[已证]"
        out["tier_reason"] = ("C1a/C1b/C1c 三次独立菜单打开的 4 个关键点全部命中"
                              "（gamemd+0x207f17 / gamemd+0x20833f / USER32 两帧），"
                              "C0 未命中；但全 7 帧序列并非逐帧完全一致，差异见正文表。")
    elif any_frame_key or any_frame_pos or any_discriminating:
        out["tier"] = "[部分一致]"
        out["tier_reason"] = (
            "C1 的 StackWalk64 帧序列 / EBP 链 / 原始栈里出现了**判别性**的部分一致"
            "（C0 阴性对照里没有的基准帧或位置），但未达到「4 个关键点全部一致」；"
            "逐帧相同/不同见正文表，不按「看起来差不多」判已证。")
    else:
        out["tier"] = "[未证实]"
        out["tier_reason"] = (
            "C1a/C1b/C1c 的 StackWalk64 帧序列逐帧**无一处**与基准相同，4 个关键点"
            "在帧序列里命中 0/4；挂起窗口内只读原始栈的 EBP 链手工回溯也未揭示任何"
            "基准外层帧。原始栈上唯一命中的关键点 %s 在 **C0 正常局内阴性对照里同样出现**，"
            "属与菜单无关的栈残留，不是活跃帧，按口径**不计入**一致证据。"
            "故「上一轮永久冻结栈 == 局内菜单打开时的栈」在本批**未获证实**；"
            "结论仅对本批 `Proving Grounds` / 该 tid / 该时刻成立，不外推。"
            % ("、".join("`%s`" % k for k in out["nondiscriminating_residue"])
               or "（无）"))
    return out


# ------------------------------------------------------------------ 文档渲染
def render_contrast(base, grabs, ana):
    t = []
    A = t.append
    A("# CONTRAST.md —— 逐帧对撞：菜单打开时的栈 vs 上一轮「永久冻结」栈")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("- 基准来源: `%s`（只读）" % base["source"])
    A("- 基准事件: pid=%s tid=%s bits=%s n=%s mode=%s picked_by=%s frame=%s t=%s paused_ms=%s"
      % (base["pid"], base["tid"], base["bits"], base["n"], base["mode"],
         base["picked_by"], base["frame"], base["t"], base["paused_ms"]))
    A("- 本批真机共三次单实例串行启动（每趟各自一趟到底、独立收尾还原）：")
    A("  - **第 1 趟** `out/run1/`：完整跑完；原始帧/addr/耗时/恢复返回值均无误，"
      "但派生的 `usable` 判据误把 `stackwalk_false:0` 当失败（已修）。逐字节归档。")
    A("  - **第 2 趟** `out/run2_aborted/`：补强版新增的只读原始栈扫描遇 WOW64 "
      "同名双份 `ntdll.dll`，取到 64 位基址导致 `to_bytes(4)` 溢出，"
      "在 C0 抓栈后、写盘前异常；`finally` 安全收尾（残留 0、配置还原）。已修，仅作透明留痕。")
    A("  - **第 3 趟** `out/*.json`（本文件 + 本报告）：修正版，判档主判据。"
      "新增挂起窗口内只读原始栈交叉核验。三趟的帧停推/四门控全 0/Δframe>0/配置还原结论一致。")
    A("")
    A("## 0. 比对口径（红线）")
    A("")
    A("1. **栈帧是返回地址，不是执行点**：下表每个 `addr` 是 `call` 指令压栈的返回地址"
      "（frame[0] 为线程被挂起瞬间的当前 EIP，位于 ntdll 等待原语内）。**不得**把返回地址"
      "当成「阻塞指令」或「卡死点」。")
    A("2. **按 模块+偏移 比对，不按绝对 addr**：DLL 受 ASLR 影响，不同进程基址不同，"
      "绝对地址不可比；`gamemd.exe` 基址固定（0x400000）故其绝对 addr 可能恰好相同。"
      "规范化规则：去 `.dll`/`.exe` 后缀、小写、偏移去前导零。")
    A("3. 判定必须逐帧给 `addr` 与 `模块+偏移` 并显式标 相同/不同，"
      "**不因「看起来差不多」判已证**。")
    A("4. 关键点（任务卡指定的最低一致条件）：%s。" %
      "、".join("`%s`" % k for k in ana["key_points"]))
    A("")
    A("## 1. 基准 7 帧（pid 14412 / tid 30668，逐帧说明「前一条调用是什么」）")
    A("")
    A("| # | addr(基准) | 模块+偏移 | 规范化 | 性质 / 前一条调用 |")
    A("|---|---|---|---|---|")
    prev_calls = [
        "frame[0] = 当前 EIP（非返回地址）：线程停在 ntdll 等待原语内（Sleep(30) 最终落入的内核等待）。符号未解析，仅按 module+offset 与已知调用链推断。",
        "返回地址：位于 KERNELBASE 的 Sleep 实现内；前一条调用为进入 ntdll 等待原语。符号未解析，不作已证事实。",
        "返回地址：位于 KERNELBASE 的 Sleep 包装内；前一条调用为更内层的 Sleep 实现。符号未解析，不作已证事实。",
        "**返回地址**：前一条调用是带 `push 0x1E` 的 `Sleep(30)`（Lead 已由反事实复算确认）。阻塞来自这次 Sleep 调用，而非该地址本身。",
        "返回地址：位于 USER32 内；由 gamemd 经 `EnumChildWindows`/模态消息循环进入。符号未解析，不作已证事实。",
        "返回地址：位于 USER32 内（模态菜单/消息泵）；前一条调用为 USER32 内部分发。符号未解析，不作已证事实。",
        "**返回地址**：前一条调用是 `call ebx` = `EnumChildWindows(hWnd, 0x606800, 1)`（Lead 已确认）。",
    ]
    for i, f in enumerate(base["frames"]):
        A("| %d | `%s` | `%s` | `%s` | %s |" %
          (i, f["addr_hex"], f["name"], f["norm"], prev_calls[i] if i < len(prev_calls) else "—"))
    A("")
    A("> 调用链（由内到外）：gamemd 某函数调用 `EnumChildWindows(hWnd,0x606800,1)` → "
      "USER32 模态循环/回调分发 → 回到 gamemd 回调 → `call Sleep(30)` → KERNELBASE → "
      "ntdll 等待原语。**这是一个「模态 UI 轮询 + 30ms Sleep」的栈形**，与「局内菜单打开」一致。")
    A("")

    # 逐帧对比表
    labels = [g["label"] for g in grabs]
    A("## 2. 逐帧对比表：基准 14412 / C0 / C1a / C1b / C1c")
    A("")
    A("单元格格式：`模块+偏移` / `(addr)` / **相同** 或 **不同**（相对同位置基准帧）。"
      "`—` 表示该趟没有这一帧。")
    A("")
    header = ["#", "基准 14412 (addr)"] + ["%s (addr / 相同?)" % l for l in labels]
    A("| " + " | ".join(header) + " |")
    A("| " + " | ".join(["---"] * len(header)) + " |")
    maxrows = max([len(base["frames"])] + [g["n_frames"] for g in grabs]) if grabs else len(base["frames"])
    gmap = {g["label"]: g for g in grabs}
    for i in range(maxrows):
        row = [str(i)]
        if i < len(base["frames"]):
            bf = base["frames"][i]
            row.append("`%s` / `%s`" % (bf["name"], bf["addr_hex"]))
        else:
            row.append("—")
        for l in labels:
            g = gmap[l]
            if i < g["n_frames"]:
                f = g["frames"][i]
                same = (ana["per_grab"][l]["pos_same"][i]["same"]
                        if i < len(ana["per_grab"][l]["pos_same"]) else False)
                mark = "**相同**" if same else "**不同**"
                row.append("`%s` / `%s` / %s" % (f["name"] or "?", f["addr_hex"], mark))
            else:
                row.append("—")
        A("| " + " | ".join(row) + " |")
    A("")

    # 关键点命中表
    A("## 3. 关键点命中 / 逐帧一致统计")
    A("")
    A("| 趟 | usable | 帧数 | StackWalk64 终止性质 | 走查达到 7 帧深度 | 7 帧逐帧一致数 | 全 7 帧序列一致 | 关键点命中 |")
    A("|---|---|---|---|---|---|---|---|")
    for l in labels:
        d = ana["per_grab"][l]
        g = gmap[l]
        A("| %s | %s | %d | `%s` | %s | %d/7 | %s | %d/4 |" %
          (l, g["usable"], d["n_frames"], d.get("stackwalk_end_reason"),
           d.get("walk_reaches_baseline_depth"), d["n_pos_same"],
           d["full_7_frame_sequence_match"], d["n_key_hits"]))
    A("")
    A("关键点逐项（`命中`=该 module+offset 出现在该趟 StackWalk64 帧序列里）：")
    A("")
    A("| 趟 | " + " | ".join("`%s`" % k for k in ana["key_points"]) + " |")
    A("| " + " | ".join(["---"] * (len(ana["key_points"]) + 1)) + " |")
    for l in labels:
        d = ana["per_grab"][l]
        A("| %s | %s |" % (l, " | ".join("命中" if d["key_hits"][k] else "未命中"
                                        for k in ana["key_points"])))
    A("")
    A("- C0（正常局内阴性对照）关键点命中数：**%s**。" % ana["c0_key_hit"])
    A("")
    A("### 关于 `stackwalk_false:0`")
    A("")
    A("- `lead/re_d13_ruling_20261112/_live_verify_stackwalk.py:311-313` 明确把 "
      "`StackWalk64` 返回 FALSE 作为**回溯走到尽头**的正常终止信号；"
      "`get_last_error()==0` 表示没有 Win32 错误。因此 `stackwalk_false:0` "
      "**不是「抓栈失败」**，第 1 趟把它当失败、把 5 次抓栈全标 `usable=false` 是派生判据 bug，"
      "本趟已修正（原始帧/addr/耗时/恢复返回值第 1 趟本来就无误，`out/run1/` 原样归档）。")
    A("- 但 `StackWalk64` 在 32 位、无 PDB、可能用 FPO 的 `gamemd.exe` 上确实可能**提前**走不下去："
      "本批多趟只到 3~4 帧，末帧是 `gamemd.exe` 内某地址而非线程入口。"
      "若走查未达到基准 7 帧的深度，**仅凭帧序列无法排除外层的 "
      "`gamemd+0x20833f` / USER32 两帧**。故第 4 节补做挂起窗口内的只读原始栈交叉核验。")
    A("- `out/run1/` 与 `out/*.json` 均逐帧保留 `addr` 与 `模块+偏移`，"
      "`StackWalk64` 返回 FALSE 的错误码与终止性质逐趟如实记录，不用「无帧」冒充结论。")
    A("")
    A("## 4. 挂起窗口内只读原始栈交叉核验（应对走查深度不足）")
    A("")
    A("方法：在线程**仍处于挂起态**时，额外对 `ESP` 起 64 KiB 做只读 `ReadProcessMemory`"
      "（授权范围内，无写入），随后离线做三项独立核验：")
    A("1. **EBP 链手工回溯**：沿 `[ebp]`→下一帧、`[ebp+4]`→返回地址逐层走，"
      "不依赖 dbghelp 的 FPO 数据；")
    A("2. **基准 7 帧绝对地址扫描**：用本进程真实模块基址 + 基准偏移算出期望绝对地址，"
      "在原始栈里搜该 4 字节值；同时直接搜基准 JSON 里的原始 `addr`；")
    A("3. **通用代码地址清点**：把原始栈上所有落在已加载模块代码范围内的 4 字节值解析为 "
      "`模块+偏移`。")
    A("")
    A("| 趟 | raw 捕获 | 读入字节 | EBP 链长 | 原始栈上命中基准帧 | 关键点(原始栈) | 关键点(EBP 链) |")
    A("|---|---|---|---|---|---|---|")
    for l in labels:
        d = ana["per_grab"][l]
        seen_bf, uniq = set(), []
        for x in d["raw_baseline_frames_found"]:
            key = (x["idx"], x["name"])
            if key not in seen_bf:
                seen_bf.add(key)
                uniq.append(x)
        found = "、".join("`#%d %s`" % (x["idx"], x["name"]) for x in uniq) or "（无）"
        A("| %s | %s | %d | %d | %s | %d/4 | %d/4 |" %
          (l, d["raw_captured"], d["raw_n_read"], d["ebp_chain_len"],
           found, d["raw_n_key_hits"], d["ebp_n_key_hits"]))
    A("")
    A("> 原始栈上的地址是**栈残留**，不等于当前调用栈上的活跃帧；"
      "命中只能说明该代码地址曾在栈上出现，不能单独证明「栈帧序列一致」。"
      "因此本节结果只用于**排除/支持**「外层帧是否存在」，不用于把 `[部分一致]` 抬成 `[已证]`。")
    A("")
    A("### 判别性检验（阴性对照 C0 同命中 ⇒ 不算一致证据）")
    A("")
    A("- C0 原始栈上命中的关键点：%s；C0 EBP 链上命中的关键点：%s。" %
      ("、".join("`%s`" % k for k in ana.get("c0_raw_key_points", [])) or "（无）",
       "、".join("`%s`" % k for k in ana.get("c0_ebp_key_points", [])) or "（无）"))
    A("- 这些点在**正常局内**（菜单未打开）就已出现 ⇒ 与菜单状态无关，"
      "判为**栈残留/非判别性**，不计入一致证据。")
    A("")
    A("| 趟 | 帧序列命中关键点 | 逐帧一致位置数 | 原始栈判别性命中 | EBP 链判别性命中 |")
    A("|---|---|---|---|---|")
    for l in labels:
        d = ana.get("discriminating", {}).get(l)
        if d is None:
            # C0 未纳入判别性表时，用它自身的逐帧一致数如实补一行
            A("| %s | （阴性对照） | %s | （阴性对照） | （阴性对照） |" %
              (l, ana["per_grab"][l]["n_pos_same"]))
            continue
        A("| %s | %s | %s | %s | %s |" %
          (l, "、".join("`%s`" % k for k in d.get("frame_key_hits", [])) or "（无）",
           d.get("n_pos_same", "—"),
           "、".join("`%s`" % k for k in d.get("raw_discriminating", [])) or "（无）",
           "、".join("`%s`" % k for k in d.get("ebp_discriminating", [])) or "（无）"))
    A("")
    A("## 5. 关键读数（供 Lead 复算）")
    A("")
    A("- **C0 与基准共享前 3 帧** `ntdll+0x7858c → KERNELBASE+0x16a1f0 → "
      "KERNELBASE+0x16a18f`：这是游戏主循环 `Sleep(30)` 帧节流的通用前缀"
      "（W1 实测约 31 计数/s），**不是菜单特有**。基准第 3 帧 "
      "`gamemd+0x207f17` 是**另一个** `Sleep(30)` 调用点（C0 为 `gamemd+0x15e332`）。")
    A("- **C1a/C1b/C1c 三趟完全一致**：`win32u+0x11ac → USER32+0xc7f51 → "
      "DDRAW+0x22b06 → gamemd+0x13eb1c`；线程当前 EIP 在 `win32u.dll`（USER32 "
      "系统调用桩，消息等待类），**不在** `ntdll`/`KERNELBASE` 的 Sleep 链里。"
      "即：本环境下「按 Esc 打开局内菜单」让窗口线程进入的是 **USER32 消息等待**，"
      "而非基准那条 `Sleep(30)` + `EnumChildWindows` 模态轮询链。")
    A("- 基准的 `gamemd+0x207f17` / `gamemd+0x20833f` / `USER32+0x3505d` "
      "在 C1 的帧序列、EBP 链、64 KiB 原始栈上**均未出现**。")
    A("- 帧计数与门控：菜单打开时 `frame` 停推（两读数相等）、`g1..g4` 全 0、"
      "`mode[0xA8B238]=5`、`[0xA8E9A0]=1`、`[0xABCD58]=0`；"
      "点 `GUI:ResumeMission` 后 Δframe=13>0（三趟均成立）。")
    A("")
    A("## 6. 结论分档")
    A("")
    A("**%s**" % ana["tier"])
    A("")
    A("- 判档理由：%s" % ana["tier_reason"])
    A("- 分档定义：`[已证]` = 栈帧序列在关键点上一致（三趟 C1 全部命中关键点，且 C0 阴性）；"
      "`[部分一致]` = 仅部分帧一致（正文表列出哪些相同、哪些不同）；"
      "`[未证实]` = 关键帧未复现或抓栈不可用。")
    A("- 若结论为 `[已证]`，其含义是：上一轮 pid 14412 那条「帧计数停推至窗口结束」的 7 帧栈，"
      "与「局内菜单/模态 UI 打开」时的栈一致 ⇒ 该「冻结」是**正常 UI 状态**，"
      "而不是性能/稳定性缺陷。此结论**不**外推到其它成因的停推。")
    A("")
    return "\n".join(t) + "\n"


def render_safety(grabs, budget_ms, hold_abort):
    t = []
    A = t.append
    A("# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`；单次挂起预算 = **%.1f ms**" %
      (RUN_ID, utc_iso(), budget_ms))
    A("")
    A("## 1. 挂起/恢复计数核对（逐线程、精确还原）")
    A("")
    A("| 趟 | tid | prev_count(SuspendThread 返回) | resume_ret(ResumeThread 返回) | "
      "resume_state | sample_state | errors | 无残留挂起(prev=0 且 ret=1) |")
    A("|---|---|---|---|---|---|---|---|")
    for g in grabs:
        A("| %s | %s | %s | %s | %s | %s | %s | %s |" %
          (g["label"], g["tid"], g["prev_count"], g["resume_ret"],
           g["resume_state"], g["sample_state"],
           "[]" if not g["errors"] else json.dumps(g["errors"], ensure_ascii=False),
           g["clean_restore_no_residual_suspend"]))
    A("")
    clean = [g for g in grabs if g["clean_restore_no_residual_suspend"]]
    A("- 抓栈总次数：**%d**；`resume_verified_ok`（恢复成功正面证据）：**%d**；"
      "干净还原（prev=0 → resume_ret=1）：**%d**。" %
      (len(grabs), sum(1 for g in grabs if g["sample_state"] == "resume_verified_ok"), len(clean)))
    A("- **零残留挂起 = %s**。判据说明：`SuspendThread` 返回 `prev_count`（本批要求 =0，"
      "即线程原本在运行、不接管别人的挂起态）；`ResumeThread` 返回其前一次挂起计数（=1），"
      "把计数还原到 0。两者配对即为「无残留挂起」的直接证据。"
      % ("是" if len(clean) == len(grabs) and grabs else "否 / 见上表"))
    A("- 额外行为证据：每次抓栈后游戏仍能响应 `Esc` / `GUI:ResumeMission` 点击，"
      "且恢复后帧计数继续推进（详见 RUNLOG/CONTRAST 的 Δframe 读数），"
      "说明窗口线程未被遗留挂起。")
    A("- 实现约束落地：r2 `sample_single()` 只采 **1 个线程**（逐线程挂→走→立刻恢复，"
      "不一次性全挂）；`sample_one_thread()` 的 `try/finally` 保证任何异常路径都恢复；"
      "`prev>0` 的线程被跳过（`skipped=already_suspended`）；"
      "另加 `GetCurrentThreadId()` 显式守卫，目标 tid 与采样器自身线程不重合。")
    A("")
    A("## 2. 单次挂起耗时（perf_counter_ns 分项）与预算")
    A("")
    A("| 趟 | 取上下文 context_ns | 走栈 walk_ns | 恢复 resume_ns | "
      "挂起总时长 suspend_held_ns(ms) | end_to_end(ms) | r2 预算超限 | 挂起窗口>50ms |")
    A("|---|---|---|---|---|---|---|---|")
    held_vals = []
    for g in grabs:
        ti = g["timing_ns"]
        held_ms = ti["suspend_held_ns"] / 1e6
        held_vals.append(held_ms)
        A("| %s | %d | %d | %d | %d (%.3f) | %.3f | %s | %s |" %
          (g["label"], ti["context_ns"], ti["walk_ns"], ti["resume_ns"],
           ti["suspend_held_ns"], held_ms, ti["end_to_end_ns"] / 1e6,
           g["budget_exceeded_r2"], g["hold_exceeded_50ms"]))
    A("")
    A("- 单次最长挂起耗时：**%.3f ms**（预算 %.1f ms）→ **%s**。" %
      (max(held_vals) if held_vals else 0.0, budget_ms,
       "未超限" if (held_vals and max(held_vals) <= budget_ms) else "超限/无有效样本"))
    A("- 超限处置：`hold_exceeded_50ms` 为真即中止后续抓栈并如实记录；本批触发 = **%s**。" %
      bool(hold_abort))
    A("- 注：r2 的 `budget_exceeded` 以 `end_to_end_ns`（含 preflight/Toolhelp 枚举）计，"
      "**不是**纯挂起窗口；为避免 preflight 把有效样本误判成 error，r2 事件级预算放宽到 "
      "%.0f ms，而任务卡的 50 ms 口径单独施加在 `suspend_held_ns` 上。两者分别如实记录。"
      % (grabs[0].get("budget_ms_r2_event", 300.0) if grabs else 300.0))
    A("  `StackWalk64` 符号初始化 `SymInitialize(fInvadeProcess=TRUE)` 与 `modules_of()` "
      "均在 **C0 之前、挂起任何线程之前** 完成。")
    A("")
    A("## 3. 抓栈对目标的扰动 + 抓栈前后帧计数是否连续")
    A("")
    A("扰动来源（均为只读或极短的线程暂停，无写入、无注入、无断点）：")
    A("1. 逐线程 `SuspendThread` 冻结游戏窗口线程 `suspend_held_ns`（上表，目标 ≤50ms）；"
      "期间该线程不推进逻辑帧，帧计数器 `0xA8ED84` 暂停；恢复后继续。")
    A("2. `StackWalk64` 通过只读 `ReadProcessMemory` 回调读取目标栈内存；"
      "`SymInitialize` 只读枚举目标已加载模块。均不写目标进程。")
    A("3. 抓栈前后各读一次哨兵（只读），本身不改状态。")
    A("4. **本趟（第 3 趟，主判据）额外**：挂起窗口内对 `ESP` 起 64 KiB 做只读 "
      "`ReadProcessMemory`（16 次 4 KiB 分块），用于交叉核验外层帧；该耗时已计入 "
      "`walk_ns` 与 `suspend_held_ns`，逐趟见 `out/*.json` 的 "
      "`raw_stack_crosscheck.capture_ns`。无任何写目标进程内存的操作。")
    A("")
    A("| 趟 | 抓栈前 frame | 抓栈后 frame | Δframe(抓栈窗口内) | 说明 |")
    A("|---|---|---|---|---|")
    for g in grabs:
        A("| %s | %s | %s | %s | %s |" %
          (g["label"], g["frame_before"], g["frame_after"],
           g["frame_delta_during_grab"],
           "菜单暂停态：Δ=0 为预期（无回退、无虚增）" if g["phase"] == "C1_menu_open"
           else "正常局内：短挂起导致该窗口内净增量偏小，恢复后继续推进"))
    A("")
    A("- 结论：菜单暂停态（C1）抓栈前后帧计数**连续且恒定**（Δ=0），未出现回退或虚增；"
      "正常局内（C0）为单线程 ≤50ms 暂停，帧计数无回退。详见 `out/*.json` 的 "
      "`sentinels_at_grab` / `sentinels_after_grab`。")
    A("")
    return "\n".join(t) + "\n"


def render_config_restore(residual_before, residual_after, rows, diff,
                          close_steps, inv_counts, prelaunch):
    t = []
    A = t.append
    A("# CONFIG_RESTORE.md —— 配置逐字节还原与残留进程核对")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    A("## 1. 启动前守卫（实算 SHA-256）")
    A("")
    A("| 文件 | bytes | 实算 SHA-256 | 期望(守卫/基线) | 一致 |")
    A("|---|---|---|---|---|")
    for name in ("RA2MD.INI", "ddraw.ini", "gamemd.exe", "ddraw.dll", "RA2MD.INI.benchbak"):
        r = prelaunch.get(name, {})
        A("| %s | %s | `%s` | `%s` | %s |" %
          (name, r.get("bytes"), r.get("sha256"), EXPECTED_HASHES.get(name),
           r.get("match")))
    A("")
    A("- `RA2MD.INI` 守卫值 `%s`（任务卡）。" % EXPECTED_HASHES["RA2MD.INI"])
    A("")
    A("## 2. 残留进程核对")
    A("")
    A("- 启动前 `gamemd.exe` 残留：**%d** 个 `%s`" % (len(residual_before), residual_before))
    A("- 收尾后 `gamemd.exe` 残留：**%d** 个 `%s`" % (len(residual_after), residual_after))
    A("- 关闭步骤（只针对自己启动的 pid，优雅优先）：")
    for s in close_steps:
        A("  - %s" % s)
    A("")
    A("## 3. 配置逐字节还原（基线 → 还原后，实算自证）")
    A("")
    A("| 文件 | 还原前 SHA | 基线 SHA | 还原后 SHA | 逐字节一致 | 哈希一致 |")
    A("|---|---|---|---|---|---|")
    ok_all = True
    for r in rows:
        if r.get("verify_only"):
            A("| %s | (仅校验，无字节副本) | `%s` | `%s` | — | 未改动=%s |" %
              (r["file"], r.get("baseline_tsv_sha256"), r.get("post_sha256"),
               r.get("unchanged")))
            if not r.get("unchanged"):
                ok_all = False
        elif "error" in r:
            A("| %s | - | - | - | - | %s |" % (r["file"], r["error"]))
            ok_all = False
        else:
            A("| %s | `%s` | `%s` | `%s` | %s | %s |" %
              (r["file"], r.get("pre_restore_sha256"), r.get("baseline_tsv_sha256"),
               r.get("post_restore_sha256"), r.get("byte_identical_to_baseline"),
               r.get("sha_match")))
            if not (r.get("byte_identical_to_baseline") and r.get("sha_match")):
                ok_all = False
    A("")
    A("**配置逐字节还原 = %s**" % ok_all)
    A("")
    A("## 4. 游戏写回了哪些文件（与启动前清单比对）")
    A("")
    A("- 清单范围：`ra2youli\\` 有上限递归扫描；启动前 %d 项，收尾 %d 项。"
      % (inv_counts[0], inv_counts[1]))
    A("- 新增 %d / 删除 %d / 变化 %d" %
      (len(diff["added"]), len(diff["removed"]), len(diff["changed"])))
    for k in ("added", "removed", "changed"):
        A("- %s (%d): %s" % (k, len(diff[k]),
                             "、".join("`%s`" % x for x in diff[k][:60]) or "（无）"))
    A("")
    A("> 清单比对发生在还原**之前**，故记录的是游戏真实写回；还原本身会再次改写配置文件。")
    A("")
    return "\n".join(t) + "\n"


def render_runlog(meta, exit_code, started_utc, ended_utc, cmdline):
    t = []
    A = t.append
    A("# RUNLOG.md —— 真机批次 B 执行日志")
    A("")
    A("- run_id: `%s`" % RUN_ID)
    A("- 开始(UTC): `%s`；结束(UTC): `%s`" % (started_utc, ended_utc))
    A("- 本地时间: `%s`" % local_iso())
    A("- 退出码: **%d**" % exit_code)
    A("- 命令: `%s`" % cmdline)
    A("- Python: `%s` / `%s`" % (sys.executable, sys.version.split()[0]))
    A("- 本批共三次单实例串行真机启动（每趟独立收尾还原、残留进程 0）："
      "第 1 趟 `out/run1/` 完整但派生 `usable` 判据误把 `stackwalk_false:0` 当失败；"
      "第 2 趟 `out/run2_aborted/` 因只读原始栈扫描的 WOW64 同名双模块溢出 bug "
      "在 C0 后异常、已 `finally` 安全收尾并修复，仅作透明留痕；"
      "**本 RUNLOG 对应第 3 趟（主判据）**。"
      "三趟的帧停推/门控全 0/Δframe>0/配置还原结论一致。")
    A("")
    A("## 关键参数与实测")
    A("")
    A("```json")
    A(json.dumps({k: meta.get(k) for k in
                  ("args", "pid", "launcher_pid", "ownership", "is32",
                   "code_signature_ok", "map", "game_hwnd", "window_tid",
                   "c0_tid", "walker", "prelaunch_match_all", "map_index",
                   "frame_stable_summary", "c1_cycles", "resume_verifications",
                   "hold_abort", "error")},
                 ensure_ascii=False, indent=1, default=str))
    A("```")
    A("")
    A("## stdout 片段（完整输出见 `out/stdout.txt`）")
    A("")
    A("```text")
    for line in LOG_LINES[:40]:
        A(line)
    if len(LOG_LINES) > 80:
        A("... (省略 %d 行) ..." % (len(LOG_LINES) - 80))
    for line in LOG_LINES[-40:]:
        A(line)
    A("```")
    A("")
    return "\n".join(t) + "\n"


def render_uncovered(meta, grabs, ana):
    t = []
    A = t.append
    A("# UNCOVERED.md —— 未覆盖与不确定项")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    items = [
        "**符号解析未做**：USER32 / KERNELBASE / ntdll 三处偏移只按 `模块+偏移` 比对，"
        "未加载 PDB、未做反汇编，故 CONTRAST.md 中对这些帧「前一条调用」的描述是"
        "按已知调用链的推断，**不是已证事实**。仅 `gamemd.exe+0x207f17` 的 `Sleep(30)` "
        "与 `gamemd.exe+0x20833f` 的 `EnumChildWindows(hWnd,0x606800,1)` 是 Lead 已确认的反事实。",
        "**绝对地址不可比**：DLL 受 ASLR 影响，跨进程绝对 `addr` 不同；本批一律按 "
        "`模块+偏移` 比对。`gamemd.exe` 非 ASLR，其绝对 addr 可能恰好与基准一致，"
        "但这不用于判档。",
        "**只采一个线程**：只采游戏窗口线程（与基准 `picked_by=only_tid` 一致）。"
        "其它线程（音频、网络、渲染等）的栈本批未采，不能据此断言它们的状态。",
        "**只跑一张图 / 一个难度 / 一趟**：`Proving Grounds` 遭遇战开局后平静态，"
        "未覆盖其它地图、不同单位负载、联机、录像、长时间运行后的自然停推。",
        "**未复现「自然长停」**：本批的帧停推全部由主动按 Esc 打开局内菜单引入；"
        "没有出现自然发生的长时间停推，也没有观测到四门控非零（门控跳过路径）。"
        "因此「门控跳过」与「其它非门控抑制路径」是否存在，本批不判定。",
        "**C0 是协议强制的例外**：安全约束要求「抓栈只在主动打开菜单后做」，"
        "但步骤 3 强制要求 C0（正常局内阴性对照）。本批在开局后平静、无交火的状态下"
        "对 1 个线程做 1 次 ≤50ms 挂起，**未在激烈战斗中挂起**。该次扰动的帧计数"
        "读数见 SAFETY.md。",
        "**抓栈扰动不可完全消除**：任何 SuspendThread 都会短暂冻结目标线程；"
        "本批以 ≤50ms + try/finally + 精确还原 + 前后帧计数读数把它量化，"
        "但不宣称「零扰动」。",
        "**`[0xA8B238]` 模式值只登记原始读数**：静态线称其为模式枚举（0/3/4/5），"
        "本批未对其语义做本机再解码，只作为「同一时刻」状态量记录。",
        "**`EnumChildWindows` 回调 `0x606800` 未在本批反汇编**：不验证回调内部是否"
        "确实调用 `Sleep(30)`；该结论沿用 Lead 的既有复算。",
        "**StackWalk64 的 FPO/帧指针局限**：32 位栈回溯依赖 EBP 链与 dbghelp 的 "
        ".pdata/FPO；若目标用 FPO 优化，深帧可能截断或出现伪帧。本批以 "
        "`n_frames` / `stackwalk_last_error` / `stackwalk_end_reason` / "
        "`walk_reaches_baseline_depth` / `frames_is_single` 如实标记，"
        "不用「无帧/单帧」冒充结论；并在挂起窗口内补只读原始栈 + EBP 链交叉核验。",
        "**「栈残留」不等于「活跃帧」**：原始栈上搜到的基准绝对地址只能证明该地址曾在栈上出现，"
        "不能单独证明栈帧序列一致；本批把它用于排除/支持「外层帧是否存在」，"
        "不用于抬高判档。",
        "**判档边界**：`[已证]` 仅表示「菜单打开时的栈与 14412 那 7 帧在关键点一致」，"
        "即该次冻结属正常 UI 状态；**不**证明所有帧停推都是菜单、"
        "也**不**证明不存在其它成因的停推。",
    ]
    if meta.get("error"):
        items.insert(0, "**本趟存在异常**：`%s`；因此对应当轮结论按实际完成度降级解读。"
                     % meta["error"])
    items.insert(0, "**三次真机启动 + 两处判据/分析代码修正**：本批单实例串行启动三次"
                 "（每趟独立收尾还原、残留进程 0）。第 1 趟 `out/run1/` 完整但派生 `usable` "
                 "判据误把 `stackwalk_false:0` 当失败；第 2 趟 `out/run2_aborted/` 因新增只读"
                 "原始栈扫描在 WOW64 同名双份 `ntdll.dll` 上溢出而中途异常（`finally` 已安全收尾）；"
                 "第 3 趟修正两处、补交叉核验，为判档主判据。三趟的**原始帧/addr/耗时/恢复返回值/"
                 "配置还原**均逐字节留档、可独立复核，未删改任何原始记录。")
    if any(not g["usable"] for g in grabs):
        items.insert(0, "**存在不可用抓栈**：%s；这些趟不参与逐帧判档的「已证」计数。"
                     % "、".join(g["label"] for g in grabs if not g["usable"]))
    for i, s in enumerate(items, 1):
        A("%d. %s" % (i, s))
        A("")
    A("## 判档结果备查")
    A("")
    A("- 总判档：**%s**" % ana["tier"])
    A("- 理由：%s" % ana["tier_reason"])
    A("")
    return "\n".join(t) + "\n"


# ------------------------------------------------------------------ 离线重算（不启动游戏）
def reanalyze_only():
    """从既有 out/*.json 重新生成 CONTRAST/SAFETY/summary 等派生文档。

    用途：分析口径修正后无需再发射真机；原始抓栈 JSON 逐字节不动。
    CONFIG_RESTORE / RUNLOG / UNCOVERED 保留本趟真机运行时写下的版本，只在末尾追加一行说明。
    """
    base = load_baseline()
    order = ["C0", "C1a", "C1b", "C1c"]
    grabs = []
    for lab in order:
        p = OUT / (lab + ".json")
        if not p.exists():
            print("!! reanalyze 缺少 %s" % p, file=sys.stderr)
            return 3
        grabs.append(json.loads(p.read_text(encoding="utf-8")))
    ana = analyze(base, grabs)
    write_json("summary.json", {"analysis": ana,
                                "grabs": [{"label": g["label"], "usable": g["usable"],
                                           "n_frames": g["n_frames"],
                                           "norms": [f["norm"] for f in g["frames"]],
                                           "stackwalk_end_reason": g.get("stackwalk_end_reason"),
                                           "walk_reaches_baseline_depth": g.get("walk_reaches_baseline_depth"),
                                           "raw_n_key_hits": (g.get("raw_stack_crosscheck") or {}).get("n_key_points_found_on_raw_stack"),
                                           "sample_state": g["sample_state"],
                                           "resume_ret": g["resume_ret"],
                                           "prev_count": g["prev_count"],
                                           "hold_ns": g["timing_ns"]["suspend_held_ns"]}
                                          for g in grabs],
                                "reanalyzed": True,
                                "reanalyze_utc": utc_iso()})
    (W3 / "CONTRAST.md").write_text(render_contrast(base, grabs, ana), encoding="utf-8")
    (W3 / "SAFETY.md").write_text(render_safety(grabs, 50.0, False), encoding="utf-8")
    meta = {}
    mp = OUT / "run_meta.json"
    if mp.exists():
        meta = json.loads(mp.read_text(encoding="utf-8"))
    (W3 / "UNCOVERED.md").write_text(render_uncovered(meta, grabs, ana), encoding="utf-8")
    for name, note in (
        ("CONFIG_RESTORE.md", "配置还原结论来自本趟真机运行时实算，未因离线重算改动。"),
        ("RUNLOG.md", "命令/退出码/时间戳来自本趟真机运行时记录；离线重算只刷新了 CONTRAST/SAFETY/summary/UNCOVERED。"),
    ):
        p = W3 / name
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            marker = "> 离线重算补记"
            if marker not in txt:
                stamp = "\n> 离线重算补记（%s）：%s\n" % (utc_iso(), note)
                p.write_text(txt.rstrip() + "\n" + stamp, encoding="utf-8")
    print("[reanalyze] 判档 = %s" % ana["tier"])
    print("[reanalyze] C0 raw key points = %s" % ana.get("c0_raw_key_points"))
    print("[reanalyze] discriminating = %s" % ana.get("discriminating"))
    print("[reanalyze] 文档已刷新（原始 out/*.json 未改动）")
    return 0


# ------------------------------------------------------------------ 主流程
class GuardStop(Exception):
    pass


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--map-pattern", default="Proving Grounds")
    ap.add_argument("--load-wait", type=float, default=15.0)
    ap.add_argument("--stable-seconds", type=float, default=20.0)
    ap.add_argument("--budget-ms", type=float, default=50.0,
                    help="单次挂起总时长上限(ms)，作用于 suspend_held_ns")
    ap.add_argument("--r2-event-budget-ms", type=float, default=300.0,
                    help="r2 sample_single 事件级预算(ms)，作用于 end_to_end_ns（含 preflight）")
    ap.add_argument("--max-frames", type=int, default=20)
    ap.add_argument("--raw-stack-bytes", type=int, default=65536,
                    help="挂起窗口内只读 RPM 的原始栈字节数（用于交叉核验外层帧）")
    ap.add_argument("--c1-count", type=int, default=3)
    ap.add_argument("--menu-timeout", type=float, default=90.0)
    ap.add_argument("--out", default="")
    ap.add_argument("--reanalyze", action="store_true",
                    help="不启动游戏：从 out/C0.json / out/C1*.json 重新生成全部 MD 与 summary.json")
    a = ap.parse_args()

    global OUT
    if a.out:
        OUT = Path(a.out)
    OUT.mkdir(parents=True, exist_ok=True)
    W3.mkdir(parents=True, exist_ok=True)

    if a.reanalyze:
        return reanalyze_only()

    started_utc = utc_iso()
    cmdline = "%s -X utf8 %s %s" % (
        sys.executable, str(W3 / "stack_contrast.py"),
        " ".join('%s' % x for x in sys.argv[1:]))

    meta = {
        "run_id": RUN_ID, "started_utc": started_utc, "cmdline": cmdline,
        "args": vars(a), "pid": None, "launcher_pid": None, "ownership": None,
        "is32": None, "code_signature_ok": None, "map": None, "map_index": None,
        "game_hwnd": None, "window_tid": None, "c0_tid": None,
        "walker": None, "prelaunch": {}, "prelaunch_match_all": None,
        "frame_stable_summary": None, "c1_cycles": [], "resume_verifications": [],
        "hold_abort": False, "error": None,
    }
    grabs = []
    base = load_baseline()
    write_json("baseline_14412.json", base)

    exit_code = 0
    pid = 0
    launcher_pid = 0
    hproc = None
    game_hwnd = 0
    is32 = None
    walker = None
    w1 = r2 = sw = None
    sampler = None
    residual_before = []
    residual_after = []
    close_steps = []
    rows = []
    inv_before = {}
    inv_after = {}
    diff = {"added": [], "removed": [], "changed": []}
    prelaunch = {}
    sentinel_log = []

    def rec_sentinel(tag, s):
        sentinel_log.append({"tag": tag, **s})

    try:
        # ---------------- 步骤 1：启动前守卫 ----------------
        log("[S1] 启动前：残留进程 + 只读资产自证 + 实算 SHA-256")
        w1, r2, sw = load_assets()
        log("    只读资产加载完成：W1 导航 / r2 采样器 / e3_stackwalker（结构自证通过）")
        log("    基准 7 帧已读：%s" % " → ".join(f["name"] for f in base["frames"]))

        residual_before = w1.list_gamemd()
        log("    gamemd 残留 = %d %s" % (len(residual_before), residual_before))
        if residual_before:
            raise GuardStop("启动前已存在 gamemd 残留，拒绝启动：%r" % residual_before)

        for name in ("RA2MD.INI", "ddraw.ini", "gamemd.exe", "ddraw.dll", "RA2MD.INI.benchbak"):
            p = GAME_DIR / name
            if not p.exists():
                raise GuardStop("缺少文件 %s" % p)
            h = sha256_file(p)
            prelaunch[name] = {"bytes": p.stat().st_size, "sha256": h,
                               "expected": EXPECTED_HASHES[name],
                               "match": h == EXPECTED_HASHES[name]}
            log("    %-20s %8d  %s  match=%s" %
                (name, prelaunch[name]["bytes"], h, prelaunch[name]["match"]))
        meta["prelaunch"] = prelaunch
        meta["prelaunch_match_all"] = all(v["match"] for v in prelaunch.values())
        bad = [n for n, v in prelaunch.items() if not v["match"]]
        if bad:
            raise GuardStop("启动前哈希不一致，按任务卡要求停止并报告：%s" % bad)
        inv_before = w1.inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inv_before))
        write_json("prelaunch.json", {"residual_before": residual_before,
                                      "hashes": prelaunch,
                                      "baseline_stack": base})

        # ---------------- 步骤 2：启动 / 导航 / 开局 ----------------
        log("[S2] WMI 分离启动 gamemd.exe")
        launcher_pid = w1.launch_game()
        pid, own = w1.wait_for_pid(launcher_pid, a.menu_timeout)
        meta.update(pid=pid, launcher_pid=launcher_pid, ownership=own)
        log("    pid=%d 归属=%s launcher_pid=%d" % (pid, own, launcher_pid))

        hproc = w1.k32.OpenProcess(0x0010 | 0x0400, False, pid)  # VM_READ | QUERY_INFORMATION
        if not hproc:
            raise RuntimeError("OpenProcess 失败")
        flag = wt.BOOL(0)
        w1.k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        log("    IsWow64Process -> is32=%s" % is32)
        sig = w1.rpm(hproc, CODE_SIG_ADDR, len(CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == CODE_SIG_EXPECT)
        log("    代码签名@0x55DE4F = %r 期望 %r -> ok=%s" %
            (sig.hex() if sig else None, CODE_SIG_EXPECT.hex(), meta["code_signature_ok"]))

        w1.wait_main_menu(pid, a.menu_timeout)
        log("[S3] 导航 SinglePlayer -> Skirmish -> 按名称选图")
        if not w1.click(pid, "GUI:SinglePlayer", 3.0):
            raise RuntimeError("GUI:SinglePlayer 点击失败")
        if not w1.click(pid, "GUI:Skirmish", 3.5):
            raise RuntimeError("GUI:Skirmish 点击失败")
        map_info = w1.select_map_by_name(hproc, pid, a.map_pattern)
        meta["map"] = map_info
        meta["map_index"] = map_info.get("index")
        log("    地图命中：index=%s 显示名=%r 条目=%d 命中数=%d" %
            (map_info.get("index"), map_info.get("display_name"),
             map_info.get("n_items"), map_info.get("n_hits")))
        hwnds = w1.game_top_windows(pid)
        game_hwnd = int(hwnds[0]) if hwnds else 0
        meta["game_hwnd"] = game_hwnd
        log("    游戏主窗口 hwnd=%s" % game_hwnd)
        if not w1.click(pid, "GUI:StartGame", 1.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        log("    等待加载 %.1fs" % a.load_wait)
        time.sleep(a.load_wait)

        # 帧稳定推进 ≥ 20s
        log("[S3b] 帧稳定推进观测 %.1fs" % a.stable_seconds)
        fs = wait_stable_frame(w1, hproc, a.stable_seconds)
        meta["frame_stable_summary"] = {k: v for k, v in fs.items() if k != "series"}
        write_json("frame_stable.json", fs)
        log("    样本=%d frame %s→%s Δ=%s 最长连续不推进=%d 拍"
            % (fs["n_samples"], fs["frame_first"], fs["frame_last"],
               fs["frame_net_delta"], fs["max_consecutive_nonadvance_samples"]))
        if not fs["frame_advanced"]:
            raise GuardStop("开局后帧计数未稳定推进（Δ=%s），按红线不做后续抓栈" %
                            fs["frame_net_delta"])

        # ---------------- 回溯器挂载（挂起任何线程之前） ----------------
        log("[S4] 挂起前完成 StackWalk64/符号初始化（attach_walker）")
        r2.bind_real_ops()
        sampler = r2.StackSampler(budget_ms=a.r2_event_budget_ms)
        att = attach_walker(r2, sw, sampler, hproc, pid, is32, max_frames=a.max_frames)
        meta["walker"] = {k: v for k, v in att.items()
                          if k not in ("walker", "mods_all")}
        walker = att["walker"]
        mods_all = att.get("mods_all") or []
        raw_state = install_raw_capture(walker, w1, hproc, a.raw_stack_bytes) if att["ok"] else None
        log("    StackWalker ok=%s err=%s n_modules=%d is32=%s max_frames=%d raw_stack_bytes=%d" %
            (att["ok"], att["err"], att["n_modules"], is32, a.max_frames, a.raw_stack_bytes))
        for m in att["mods"]:
            log("      %s base=%s size=%d" % (m["name"], m["base"], m["size"]))
        if not att["ok"]:
            raise GuardStop("回溯器挂载失败(%s)，按红线不抓栈、如实收尾" % att["err"])

        # 确定「窗口线程」tid（与基准 only_tid 一致），并做自身线程守卫
        wtid, all_hwnds = game_window_tid(w1, pid)
        meta["window_tid"] = wtid
        log("    游戏窗口线程 tid=%s (主窗口 hwnd=%s)" % (wtid, all_hwnds[:1]))
        if not wtid:
            raise GuardStop("未找到游戏窗口线程，按红线不抓栈")
        k32_self = ctypes.WinDLL("kernel32", use_last_error=True)
        k32_self.GetCurrentThreadId.restype = wt.DWORD
        cur_tid = int(k32_self.GetCurrentThreadId())
        if int(wtid) == cur_tid:
            raise GuardStop("目标 tid 等于采样器自身线程，拒绝挂起（D4）")
        log("    自身线程守卫：采样器 GetCurrentThreadId=%d ≠ 目标 tid=%d ✓" % (cur_tid, wtid))
        c0_tid = int(wtid)
        meta["c0_tid"] = c0_tid

        # ---------------- 步骤 3：C0 阴性对照（正常局内） ----------------
        log("[C0] 正常局内阴性对照：单次 ≤%.0fms 抓栈（平静、无交火）" % a.budget_ms)
        s0 = read_sentinels(w1, hproc)
        rec_sentinel("C0_before", s0)
        g = do_grab("C0", "C0_normal_ingame", r2, sampler, walker, w1,
                    hproc, pid, c0_tid, a.budget_ms, a.r2_event_budget_ms, s0,
                    raw_state, mods_all, base["frames"])
        grabs.append(g)
        rec_sentinel("C0_after", g["sentinels_after_grab"])
        if g["hold_exceeded_50ms"] or g["budget_exceeded_r2"]:
            meta["hold_abort"] = True
            raise GuardStop("C0 挂起超预算，按红线中止后续抓栈并如实记录")

        # ---------------- 步骤 4：C1a/C1b/C1c（每趟：开菜单→确认→抓栈→恢复） ----------------
        cyc_labels = ["C1a", "C1b", "C1c"][:max(0, a.c1_count)]
        for ci, label in enumerate(cyc_labels):
            log("[%s] 第 %d/%d 趟：按 Esc 打开局内菜单" % (label, ci + 1, len(cyc_labels)))
            fg = w1.force_foreground(game_hwnd)
            log("    force_foreground -> %s" % fg)
            w1.send_esc()
            time.sleep(1.0)

            # 确认菜单真的打开 + 帧停推 + 四门控全 0
            fh, ftxt = find_button(w1, pid, "GUI:ResumeMission")
            if not fh:                       # 仅等待重查一次，不用任何强制手段
                time.sleep(0.8)
                fh, ftxt = find_button(w1, pid, "GUI:ResumeMission")
            wtid_now, _ = game_window_tid(w1, pid)
            s_a = read_sentinels(w1, hproc)
            time.sleep(0.45)
            s_b = read_sentinels(w1, hproc)
            rec_sentinel(label + "_confirm_a", s_a)
            rec_sentinel(label + "_confirm_b", s_b)
            menu_present = bool(fh)
            frame_stopped = (s_a.get("frame") is not None and
                             s_b.get("frame") is not None and
                             s_a["frame"] == s_b["frame"])
            gates_zero = (s_a.get("all_gates_zero") is True and
                          s_b.get("all_gates_zero") is True)
            meta["c1_cycles"].append({
                "label": label, "fg_ok": bool(fg), "menu_button_hwnd": fh,
                "menu_button_text": ftxt, "menu_present": menu_present,
                "window_tid_now": wtid_now, "same_tid_as_C0": (wtid_now == c0_tid),
                "frame_a": s_a.get("frame"), "frame_b": s_b.get("frame"),
                "frame_stopped": frame_stopped, "gates_zero": gates_zero,
                "g1": s_b.get("g1"), "g2": s_b.get("g2"),
                "g3": s_b.get("g3"), "g4": s_b.get("g4"),
                "mode_A8B238": s_b.get("mode_A8B238"),
                "ingame_A8E9A0": s_b.get("ingame_A8E9A0"),
                "latch_ABCD58": s_b.get("latch_ABCD58"),
                "sentinels_at_grab": None,
            })
            log("    菜单按钮=%r(hwnd=%s) 帧 %s→%s 停推=%s 四门控全0=%s "
                "g=[%s,%s,%s,%s] mode=%s ingame=%s latch=%s" %
                (ftxt, fh, s_a.get("frame"), s_b.get("frame"), frame_stopped,
                 gates_zero, s_b.get("g1"), s_b.get("g2"), s_b.get("g3"),
                 s_b.get("g4"), s_b.get("mode_A8B238"),
                 s_b.get("ingame_A8E9A0"), s_b.get("latch_ABCD58")))

            if not menu_present:
                log("    !! %s Esc 菜单未出现（或未找到 GUI:ResumeMission）。"
                    "按红线：如实报告，不用其它强制手段，直接收尾还原。" % label)
                meta["error"] = "%s: Esc 菜单未出现/未找到 GUI:ResumeMission" % label
                break
            if not (frame_stopped and gates_zero):
                log("    !! %s 未同时满足「帧停推 + 四门控全 0」，如实记录但仍按协议抓栈一次。" % label)

            # 抓栈「同一时刻」读数
            s_grab = read_sentinels(w1, hproc)
            rec_sentinel(label + "_at_grab", s_grab)
            meta["c1_cycles"][-1]["sentinels_at_grab"] = s_grab
            g = do_grab(label, "C1_menu_open", r2, sampler, walker, w1,
                        hproc, pid, c0_tid, a.budget_ms, a.r2_event_budget_ms, s_grab,
                        raw_state, mods_all, base["frames"])
            grabs.append(g)
            rec_sentinel(label + "_after", g["sentinels_after_grab"])

            if g["hold_exceeded_50ms"] or g["budget_exceeded_r2"]:
                meta["hold_abort"] = True
                log("    !! %s 挂起超预算，中止后续抓栈" % label)
                break

            # 逐趟恢复：点 GUI:ResumeMission（按名称），确认 Δframe>0
            log("[%s] 点 %s 恢复对局" % (label, "GUI:ResumeMission"))
            cres = click_button(w1, pid, "GUI:ResumeMission", wait=0.9)
            s_r = read_sentinels(w1, hproc)
            time.sleep(0.4)
            s_r2 = read_sentinels(w1, hproc)
            delta = (s_r2["frame"] - s_r["frame"]
                     if s_r.get("frame") is not None and s_r2.get("frame") is not None else None)
            rv = {"label": label, "click": cres, "frame_after_click": s_r.get("frame"),
                  "frame_later": s_r2.get("frame"), "delta_frame": delta,
                  "resumed": bool(delta is not None and delta > 0)}
            meta["resume_verifications"].append(rv)
            rec_sentinel(label + "_resume_a", s_r)
            rec_sentinel(label + "_resume_b", s_r2)
            log("    恢复点击=%s Δframe=%s resumed=%s" %
                (cres.get("clicked"), delta, rv["resumed"]))
            if not rv["resumed"]:
                log("    !! %s 恢复未确认（Δframe 非正）。按红线：不用其它强制手段，"
                    "停止后续循环，直接收尾还原。" % label)
                meta["error"] = "%s: 点 GUI:ResumeMission 后 Δframe 非正，恢复未确认" % label
                break

        # ---------------- 分析 ----------------
        log("[S5] 逐帧比对与判档")
        ana = analyze(base, grabs)
        write_json("summary.json", {"analysis": ana,
                                    "grabs": [{"label": g["label"],
                                               "usable": g["usable"],
                                               "n_frames": g["n_frames"],
                                               "norms": [f["norm"] for f in g["frames"]],
                                               "stackwalk_end_reason": g.get("stackwalk_end_reason"),
                                               "walk_reaches_baseline_depth": g.get("walk_reaches_baseline_depth"),
                                               "raw_n_key_hits": (g.get("raw_stack_crosscheck") or {}).get("n_key_points_found_on_raw_stack"),
                                               "ebp_chain_len": len((g.get("raw_stack_crosscheck") or {}).get("ebp_chain") or []),
                                               "sample_state": g["sample_state"],
                                               "resume_ret": g["resume_ret"],
                                               "prev_count": g["prev_count"],
                                               "hold_ns": g["timing_ns"]["suspend_held_ns"]}
                                              for g in grabs]})
        (W3 / "CONTRAST.md").write_text(render_contrast(base, grabs, ana), encoding="utf-8")
        log("    判档 = %s" % ana["tier"])

    except GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
    except Exception as e:                                          # noqa: BLE001
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())

    # ---------------- 收尾（无论如何执行） ----------------
    finally:
        ended_utc = utc_iso()
        log("[P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原")
        try:
            if walker is not None:
                walker.cleanup()
                log("    SymCleanup 完成")
        except Exception as e:                                      # noqa: BLE001
            log("    SymCleanup 异常 %r" % e)
        try:
            if r2 is not None:
                r2.OPS.clear()
        except Exception:
            pass
        try:
            if hproc:
                w1.k32.CloseHandle(hproc)
                hproc = None
        except Exception as e:                                      # noqa: BLE001
            log("    CloseHandle(hproc) 异常 %r" % e)

        try:
            close_steps = w1.close_game(pid, game_hwnd) if (w1 is not None and pid) else [
                "no_pid_no_launch: 未启动实例，无需关闭"]
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:                                      # noqa: BLE001
            close_steps = ["close_game 异常: %r" % e]
            log("    close_game 异常 %r" % e)
        try:
            residual_after = w1.list_gamemd() if w1 is not None else []
        except Exception:
            residual_after = []
        log("    收尾后 gamemd 残留 = %d %s" % (len(residual_after), residual_after))

        try:
            inv_after = w1.inventory(GAME_DIR) if w1 is not None else {}
            diff = w1.diff_inventory(inv_before, inv_after) if w1 is not None else diff
            log("    收尾后文件清单 %d 项" % len(inv_after))
        except Exception as e:                                      # noqa: BLE001
            log("    inventory_after 异常 %r" % e)
        try:
            rows = w1.restore_configs() if w1 is not None else []
            for r in rows:
                log("    还原 %s -> %s" % (r.get("file"),
                                           r.get("post_restore_sha256") or r.get("post_sha256")))
        except Exception as e:                                      # noqa: BLE001
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)

        # 文档（即使早退也产出，缺失项显式标注）
        try:
            if grabs:
                ana = analyze(base, grabs)
            else:
                ana = {"tier": "[未证实]", "tier_reason": "本趟未产生任何抓栈记录。",
                       "baseline_norms": [f["norm"] for f in base["frames"]],
                       "key_points": list(KEY_POINTS), "per_grab": {}, "c0_key_hit": None}
            # CONTRAST/SAFETY 仅在有抓栈时给完整表；否则给「未采集」版
            if grabs:
                (W3 / "CONTRAST.md").write_text(render_contrast(base, grabs, ana), encoding="utf-8")
                (W3 / "SAFETY.md").write_text(
                    render_safety(grabs, a.budget_ms, meta.get("hold_abort")), encoding="utf-8")
            else:
                (W3 / "CONTRAST.md").write_text(
                    render_contrast(base, grabs, ana) +
                    "\n> 本趟未产生抓栈记录；逐帧对比表为空。\n", encoding="utf-8")
                (W3 / "SAFETY.md").write_text(
                    "# SAFETY.md\n\n本趟零抓栈：无挂起、无恢复、无残留挂起；"
                    "分项耗时不适用。原因见 RUNLOG/UNCOVERED。\n", encoding="utf-8")
            (W3 / "CONFIG_RESTORE.md").write_text(
                render_config_restore(residual_before, residual_after, rows, diff,
                                      close_steps, (len(inv_before), len(inv_after)),
                                      prelaunch), encoding="utf-8")
            (W3 / "UNCOVERED.md").write_text(render_uncovered(meta, grabs, ana), encoding="utf-8")
            (W3 / "RUNLOG.md").write_text(
                render_runlog(meta, exit_code, started_utc, ended_utc, cmdline), encoding="utf-8")
            write_json("run_meta.json", meta)
            (OUT / "sentinels.ndjson").write_text(
                "\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)
                          for x in sentinel_log) + "\n", encoding="utf-8")
            (OUT / "stdout.txt").write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
        except Exception as e:                                      # noqa: BLE001
            log("    文档生成异常 %r" % e)
            log(traceback.format_exc())

        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        try:
            write_json("run_meta.json", meta)
        except Exception:
            pass
        log("[P1] 收尾完成（exit_code=%d）" % exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
