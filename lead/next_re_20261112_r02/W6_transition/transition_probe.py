#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W6 —— 过渡态定向复现 S_sleep 签名（真机单实例）。

目标：在四个过渡窗口（进图 / 退出到主菜单 / 对局结束 / 再次进图）里密集采样，
一旦出现「frame 连续 ≥1s 不推进（真实 t_mono_ns 差）且四门控全 0」⇒ 立刻抓
窗口线程栈（Suspend→Walk→Resume，单次 ≤50ms），用 **第 4 帧** 判定归属：

    frame[3] == gamemd+0x207f17   ⇒ S_sleep 复现 [已证]
    frame[3] == gamemd+0x15e332   ⇒ 正常态（前 3 帧通用前缀，不算命中）
    其它                          ⇒ 第三签名

判别陷阱（必须遵守）：正常局内前 3 帧与 S_sleep 完全相同
（ntdll+0x7858c / KERNELBASE+0x16a1f0 / +0x16a18f = 主循环 Sleep(30) 通用前缀）。
前 3 帧命中不算命中，只看第 4 帧。

★ 直接复用（只读 importlib 加载，零字节改动）：
  * W3_stack_contrast/stack_contrast.py —— load_assets / read_sentinels /
    attach_walker / install_raw_capture / do_grab / norm_frame / load_baseline
  * W1_realtime_probe/realtime_gate_probe.py —— 启动/导航/选图/开局/
    RaiseWindow/close_game/restore_configs（经 w3.load_assets() 载入）
  * lead/re_d13_ruling_20261112/_hl_match_14412.json —— 基准 7 帧（只读）

授权：启动 gamemd.exe、只读 RPM、SuspendThread/GetThreadContext(WOW64)/
      StackWalk64/ResumeThread、枚举窗口线程、发送窗口消息/点击控件。
禁止：MiniDump、断点、代码注入、写目标进程内存、改 exe/dll、hook。
只处理自己启动的那个 pid；不杀别的进程。

写域：仅 lead/next_re_20261112_r02/W6_transition/（本文件与其 out/）。
实例锁：lead/next_re_20261112_r02/.game_instance.lock（开工持有、收尾恢复 owner=lead）。

用法：
  python -X utf8 transition_probe.py --map-pattern "Proving Grounds"
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

# ------------------------------------------------------------------ 常量 / 路径
RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W6 = ROOT / "lead" / "next_re_20261112_r02" / "W6_transition"
OUT = W6 / "out"
STACKS = OUT / "stacks"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"
W3_PATH = (ROOT / "lead" / "next_re_20261112_r02" / "W3_stack_contrast"
           / "stack_contrast.py")
LOCK_PATH = ROOT / "lead" / "next_re_20261112_r02" / ".game_instance.lock"
SELF_OWNER = "W6-transition-subagent"
LEAD_OWNER = "lead"

EXPECTED_HASHES = {
    "RA2MD.INI":          "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "ddraw.ini":          "c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52",
    "RA2MD.INI.benchbak": "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "gamemd.exe":         "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll":          "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
}
VERIFY_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak",
                "gamemd.exe", "ddraw.dll")
RESTORE_FILES = ("RA2MD.INI", "ddraw.ini")

GAME_WND_CLASS = "Yuri's Revenge"
STILL_ACTIVE = 259

# 基准第 4 帧（判定锚点）
SLEEP_F3 = "gamemd+0x207f17"
NORMAL_F3 = "gamemd+0x15e332"

PREV_CALLS = {
    "ntdll+0x7858c": "frame[0]=当前 EIP（非返回地址）：ntdll 等待原语内（Sleep 最终落点）",
    "kernelbase+0x16a1f0": "返回地址：KERNELBASE Sleep 实现内",
    "kernelbase+0x16a18f": "返回地址：KERNELBASE Sleep 包装内",
    "gamemd+0x207f17": "返回地址：前一条调用 = push 0x1E + call [0x7E11F0] = Sleep(30)（Lead 已证）",
    "user32+0x74775": "返回地址：USER32 内（EnumChildWindows/模态消息循环）",
    "user32+0x3505d": "返回地址：USER32 内模态泵",
    "gamemd+0x20833f": "返回地址：前一条调用 = call ebx = EnumChildWindows(hWnd,0x606800,1)（Lead 已证）",
    "gamemd+0x15e332": "返回地址：正常局内主循环 Sleep(30) 的调用点（W3 三趟已定性为正常态第 4 帧）",
}

LOG_LINES = []
PHASE_EVENTS = []


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


def phase_log(phase, msg):
    line = log("[%s] %s" % (phase, msg))
    PHASE_EVENTS.append({"t_utc_iso": utc_iso(), "t_mono_ns": time.perf_counter_ns(),
                         "phase": phase, "msg": msg})
    return line


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True, default=str)


def write_json(name, obj):
    p = OUT / name
    p.write_text(jdump(obj) + "\n", encoding="utf-8")
    return p


def load_module(mod_name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("importlib spec None: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_txt(t):
    """控件文字规范化：去 gui: 前缀、去加速键、小写。"""
    n = (t or "").strip().lower()
    if n.startswith("gui:") or n.startswith("gui_"):
        n = n[4:]
    n = n.replace("&", "").strip()
    import re as _re
    n = _re.sub(r"\s*\([a-z]\)\s*$", "", n).strip()
    n = _re.sub(r"\s*&[a-z]\s*$", "", n).strip()
    return n


def check_lock():
    """实例锁守卫：owner 必须是 lead（允许接管）或自己（已持有）。
    其它代理标识 ⇒ 停手报告。"""
    try:
        txt = LOCK_PATH.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError("实例锁不可读 %s: %r" % (LOCK_PATH, e))
    owner = None
    for line in txt.splitlines():
        if line.startswith("owner="):
            owner = line.split("=", 1)[1].strip()
    if owner == LEAD_OWNER:
        return "lead_free"
    if owner == SELF_OWNER:
        return "self_held"
    raise RuntimeError("实例锁 owner=%r 不是 lead 也不是本代理 ⇒ 可能有并发实例，停手"
                       % owner)


def write_lock(owner, purpose):
    LOCK_PATH.write_text(
        "run_id=%s\nowner=%s\ntime=%s\npurpose=%s\n"
        % (RUN_ID, owner, datetime.datetime.now().astimezone().isoformat(), purpose),
        encoding="utf-8")


# ------------------------------------------------------------------ UI 快照
class _RECT(ctypes.Structure):
    _fields_ = [("left", wt.LONG), ("top", wt.LONG),
                ("right", wt.LONG), ("bottom", wt.LONG)]


class UISnap(object):
    __slots__ = ("t_mono_ns", "t_utc_iso", "n_tops", "n_children", "game_tid",
                 "tops", "buttons", "statics", "button_texts")

    def as_dict(self):
        return {"t_mono_ns": self.t_mono_ns, "t_utc_iso": self.t_utc_iso,
                "n_tops": self.n_tops, "n_children": self.n_children,
                "game_tid": self.game_tid,
                "tops": self.tops, "buttons": self.buttons,
                "statics": self.statics}


def ui_snapshot(w1, pid, full=True):
    """枚举本 pid 窗口树。full=True 时含子控件（否则只统计顶层 + 游戏窗口 tid）。"""
    u = w1.u
    snap = UISnap()
    snap.t_mono_ns = time.perf_counter_ns()
    snap.t_utc_iso = utc_iso()
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(int(h))
        return True

    u.EnumWindows(w1.ENUM(cb), 0)
    snap.n_tops = len(tops)
    snap.game_tid = None
    game_hwnd = 0
    for h in tops:
        if w1.wcls(h) == GAME_WND_CLASS:
            q = wt.DWORD(0)
            u.GetWindowThreadProcessId(h, ctypes.byref(q))
            snap.game_tid = int(q.value) or None
            game_hwnd = h
            break
    snap.tops = [{"hwnd": h, "cls": w1.wcls(h), "text": w1.wtxt(h),
                  "visible": bool(u.IsWindowVisible(h))} for h in tops[:12]]
    snap.n_children = None
    snap.buttons = []
    snap.statics = []
    if full:
        ctrls = w1.controls(pid)          # (hwnd, cls, text, visible) 全后代
        snap.n_children = len(ctrls)
        seen_btn = set()
        for h, c, t, v in ctrls:
            if not t:
                continue
            item = {"hwnd": int(h), "cls": c, "text": t, "visible": bool(v)}
            if c == "Button" and h not in seen_btn:
                seen_btn.add(h)
                snap.buttons.append(item)
            elif c == "Static":
                snap.statics.append(item)
        # 只保留可见 + 常用字段，避免快照过大
        snap.buttons = [b for b in snap.buttons if b["visible"]][:40]
        snap.statics = [s for s in snap.statics if s["visible"]][:40]
    return snap


def state_flags(snap):
    """纯 UI 状态分类（不依赖内存读数，避免循环论证）。"""
    btn_n = [norm_txt(b["text"]) for b in (snap.buttons or []) if b.get("visible")]
    st_n = [norm_txt(s["text"]) for s in (snap.statics or []) if s.get("visible")]
    f = {
        "main_menu": any("singleplayer" in t for t in btn_n),
        "dialog_askabort": any(t == "askabortmission" for t in (btn_n + st_n)),
        "skirmish_screen": any(t in ("skirmish", "choosemap", "usemap", "startgame")
                               for t in btn_n),
    }
    score_words = ("playagain", "again", "continue", "restart", "score", "stats",
                   "重新", "继续", "再玩", "结算")
    f["score_like"] = (any(w in t for t in btn_n for w in score_words)
                       and not f["main_menu"] and not f["dialog_askabort"])
    return f


# ------------------------------------------------------------------ 采样器
class TransitionSampler(object):
    """单线程密集采样 + 停推检测 + 定向抓栈。

    每拍：读哨兵（frame/g1..g4/mode/A8E9A0/ABCD58/exitstate）+ 顶层窗口数 +
    游戏窗口 tid；每 ui_interval_s 一次完整 UI 快照（子窗口数 + 按钮文字）。
    frame 连续 ≥1s 不推进且四门控全 0 ⇒ 抓窗口线程栈（限次/冷却）。
    """

    def __init__(self, w1, w3, hproc, pid, c0_tid, sampler, walker, raw_state,
                 mods_all, base_frames, sink, a):
        self.w1 = w1
        self.w3 = w3
        self.hproc = hproc
        self.pid = pid
        self.c0_tid = int(c0_tid)
        self.r2_sampler = sampler
        self.walker = walker
        self.raw_state = raw_state
        self.mods_all = mods_all
        self.base_frames = base_frames
        self.sink = sink
        self.a = a
        self.seq = 0
        self.samples = []
        self.grabs = []
        self.grab_seq = 0
        self.last_frame_value = None
        self.last_frame_change_ns = time.perf_counter_ns()
        self.last_grab_ns = 0
        self.grab_counts = {}
        self.hold_abort = False
        self.stopped = False

    # ---- 读数 ----
    def read_state(self):
        s = self.w3.read_sentinels(self.w1, self.hproc)
        ec = wt.DWORD(0)
        ok = self.w1.k32.GetExitCodeProcess(self.hproc, ctypes.byref(ec))
        alive = bool(ok and ec.value == STILL_ACTIVE)
        return s, alive

    def alive(self):
        ec = wt.DWORD(0)
        ok = self.w1.k32.GetExitCodeProcess(self.hproc, ctypes.byref(ec))
        return bool(ok and ec.value == STILL_ACTIVE)

    def tick(self, phase, full_ui=False):
        s, alive = self.read_state()
        t_ns = time.perf_counter_ns()
        self.seq += 1
        rec = {
            "seq": self.seq, "phase": phase, "kind": "sample",
            "t_mono_ns": int(s.get("t_perf_ns") or t_ns),
            "t_utc_iso": s.get("t_utc_iso"),
            "frame": s.get("frame"),
            "g1": s.get("g1"), "g2": s.get("g2"),
            "g3": s.get("g3"), "g4": s.get("g4"),
            "mode_A8B238": s.get("mode_A8B238"),
            "ingame_A8E9A0": s.get("ingame_A8E9A0"),
            "latch_ABCD58": s.get("latch_ABCD58"),
            "exitstate": s.get("exitstate"),
            "all_gates_zero": s.get("all_gates_zero"),
            "alive": alive,
        }
        n_tops, game_tid = cheap_tops(self.w1, self.pid)
        rec["n_tops"] = n_tops
        rec["game_tid"] = game_tid
        if full_ui:
            snap = ui_snapshot(self.w1, self.pid, full=True)
            rec["ui"] = snap.as_dict()
            self.last_snap = snap
        else:
            snap = ui_snapshot(self.w1, self.pid, full=False)
            self.last_snap = snap
        # 停推检测（真实 t_mono_ns 差）
        f = rec["frame"]
        if f is not None:
            if self.last_frame_value is not None and f != self.last_frame_value:
                self.last_frame_change_ns = t_ns
            elif self.last_frame_value is None:
                self.last_frame_change_ns = t_ns
            self.last_frame_value = f
        rec["frame_stall_s"] = (t_ns - self.last_frame_change_ns) / 1e9
        self.samples.append(rec)
        try:
            self.sink.write(rec)
        except Exception as e:                                    # noqa: BLE001
            log("!! ndjson 写行失败 %r" % e)
        return rec, snap

    # ---- 抓栈 ----
    def maybe_grab(self, phase, snap, reason):
        """停推触发抓栈。返回抓栈记录或 None。"""
        if self.hold_abort:
            return None
        now = time.perf_counter_ns()
        if (now - self.last_grab_ns) < int(self.a.grab_cooldown_s * 1e9):
            return None
        cap = self.a.grab_cap_per_phase
        if self.grab_counts.get(phase, 0) >= cap:
            return None
        if len(self.grabs) >= self.a.grab_cap_total:
            return None
        rec = self.grab_now(phase, reason, snap)
        self.last_grab_ns = time.perf_counter_ns()
        return rec

    def grab_now(self, phase, reason, snap=None):
        """定向抓栈（挂→走→立刻恢复，≤50ms）。"""
        self.grab_seq += 1
        label = "G%02d" % self.grab_seq
        # 目标线程：优先当前游戏窗口线程（过渡期窗口可能重建），回退 c0_tid
        n_tops, tid = cheap_tops(self.w1, self.pid)
        if not tid:
            tid = self.c0_tid
        self.grab_counts[phase] = self.grab_counts.get(phase, 0) + 1
        s_before, _ = self.read_state()
        phase_log(phase, "抓栈 %s 开始 tid=%s 原因=%s frame=%s" %
                  (label, tid, reason, s_before.get("frame")))
        t0 = time.perf_counter_ns()
        try:
            rec = self.w3.do_grab(label, phase, self.r2_sampler, self.r2_sampler_stackobj,
                                  self.walker, self.w1, self.hproc, self.pid,
                                  int(tid), self.a.budget_ms,
                                  self.a.r2_event_budget_ms, s_before,
                                  self.raw_state, self.mods_all, self.base_frames)
        except Exception as e:                                    # noqa: BLE001
            log("!! 抓栈 %s 异常 %r" % (label, e))
            rec = {"label": label, "phase": phase, "error": "%s: %s"
                   % (type(e).__name__, e), "usable": False, "frames": [],
                   "n_frames": 0}
        wall_ms = (time.perf_counter_ns() - t0) / 1e6
        v = grab_verdict(rec, self.base_frames)
        rec["grab_reason"] = reason
        rec["grab_wall_ms"] = round(wall_ms, 3)
        rec["grab_verdict"] = v
        rec["ui_at_grab"] = snap.as_dict() if snap is not None else None
        self.grabs.append(rec)
        log("    抓栈 %s 判定=%s wall=%.1fms frames=%s" %
            (label, v["verdict"], wall_ms,
             " → ".join(f["norm"] or "?" for f in rec.get("frames", []))))
        if rec.get("hold_exceeded_50ms") or rec.get("budget_exceeded_r2"):
            self.hold_abort = True
            log("!! %s 挂起超预算，之后不再抓栈" % label)
        return rec

    # ---- 相位循环 ----
    def run_phase(self, phase, timeout, stop_fn=None, ui_interval=0.5,
                  tail_s=0.0, grab_reason=None):
        """密集采样直到 stop_fn/超时/进程退出；tail_s 为满足停止条件后继续采样时长。

        stop_fn(state) 的 state = {"snap": 最近全量快照, "sample": 最近样本,
        "advance_stable_s": 连续推进秒数或 0}
        返回相位摘要 dict。
        """
        phase_log(phase, "开始（timeout=%.0fs ui=%.2fs）" % (timeout, ui_interval))
        t0 = time.perf_counter_ns()
        last_ui = 0.0
        stop_hit = None
        stable_since_ns = None
        adv_hist = []            # (t_ns, frame) 供 1s 推进窗
        n_ui_full = 0
        while True:
            now = time.perf_counter_ns()
            elapsed = (now - t0) / 1e9
            do_full = (time.perf_counter() - last_ui) >= ui_interval
            rec, snap = self.tick(phase, full_ui=do_full)
            if do_full:
                last_ui = time.perf_counter()
                n_ui_full += 1
            if not rec["alive"]:
                phase_log(phase, "进程已退出，提前结束相位")
                stop_hit = "process_exited"
                break
            # 连续推进秒数（真实 t_mono_ns）：最近 1s 窗内 frame 增量>0
            f = rec["frame"]
            if f is not None:
                adv_hist.append((rec["t_mono_ns"], f))
                # 只保留最近 ~1.1s 的样本；最老样本即「~1s 前」的帧值
                while len(adv_hist) > 1 and \
                        adv_hist[0][0] < rec["t_mono_ns"] - int(1.1e9):
                    adv_hist.pop(0)
                adv_1s = None
                if len(adv_hist) >= 2 and \
                        adv_hist[0][0] <= rec["t_mono_ns"] - int(1.0e9):
                    adv_1s = f - adv_hist[0][1]
                if adv_1s is not None and adv_1s > 0:
                    if stable_since_ns is None:
                        stable_since_ns = now
                else:
                    stable_since_ns = None
            state = {"snap": getattr(self, "last_snap", snap),
                     "sample": rec,
                     "advance_stable_s": ((now - stable_since_ns) / 1e9
                                          if stable_since_ns is not None else 0.0),
                     "elapsed_s": elapsed}
            # 停推触发抓栈（门控全 0 + frame 有效 + ≥1s）
            if (grab_reason is not None and rec["frame"] is not None
                    and rec["all_gates_zero"] is True
                    and rec["frame_stall_s"] >= self.a.stall_threshold_s):
                self.maybe_grab(phase, snap, grab_reason)
            if stop_fn is not None:
                try:
                    hit = stop_fn(state)
                except Exception as e:                            # noqa: BLE001
                    log("!! stop_fn 异常 %r（按未命中继续）" % e)
                    hit = None
                if hit:
                    stop_hit = hit
                    break
            if elapsed >= timeout:
                stop_hit = "timeout"
                break
            # sleep 到下一拍
            spent = time.perf_counter_ns() - now
            delay = self.a.interval_s - spent / 1e9
            if delay > 0:
                time.sleep(delay)
        if tail_s > 0 and stop_hit not in (None, "process_exited"):
            t_tail = time.perf_counter()
            while time.perf_counter() - t_tail < tail_s:
                now = time.perf_counter_ns()
                rec, snap = self.tick(phase, full_ui=False)
                if (grab_reason is not None and rec["frame"] is not None
                        and rec["all_gates_zero"] is True
                        and rec["frame_stall_s"] >= self.a.stall_threshold_s):
                    self.maybe_grab(phase, snap, grab_reason)
                if not rec["alive"]:
                    phase_log(phase, "tail 期间进程退出")
                    stop_hit = "process_exited"
                    break
                spent = time.perf_counter_ns() - now
                delay = self.a.interval_s - spent / 1e9
                if delay > 0:
                    time.sleep(delay)
        dur = (time.perf_counter_ns() - t0) / 1e9
        mine = [s for s in self.samples if s["phase"] == phase]
        fv = [s["frame"] for s in mine if s["frame"] is not None]
        summ = {
            "phase": phase, "stop_reason": stop_hit, "duration_s": round(dur, 3),
            "n_samples": len(mine), "n_ui_full": n_ui_full,
            "frame_first": fv[0] if fv else None,
            "frame_last": fv[-1] if fv else None,
            "frame_net_delta": (fv[-1] - fv[0]) if len(fv) >= 2 else None,
            "grabs": [g["label"] for g in self.grabs if g.get("phase") == phase],
        }
        phase_log(phase, "结束 stop=%s dur=%.1fs n=%d frame %s→%s grabs=%s" %
                  (stop_hit, dur, len(mine), summ["frame_first"],
                   summ["frame_last"], summ["grabs"]))
        return summ

    def wait_ui(self, phase, pred, timeout, ui_interval=0.25, grab_reason=None):
        """只做 UI 等待（每拍照常采样）。pred(snap) → truthy 即停。"""
        def stop(state):
            try:
                return pred(state["snap"]) or None
            except Exception:
                return None
        return self.run_phase(phase, timeout, stop_fn=stop,
                              ui_interval=ui_interval, grab_reason=grab_reason)


def cheap_tops(w1, pid):
    """每拍的轻量窗口读数：顶层窗口数 + 游戏窗口线程 tid。"""
    u = w1.u
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(int(h))
        return True

    u.EnumWindows(w1.ENUM(cb), 0)
    tid = None
    for h in tops:
        if w1.wcls(h) == GAME_WND_CLASS:
            q = wt.DWORD(0)
            # ★ GetWindowThreadProcessId 的 tid 是**返回值**；第二参数写回的是 pid。
            ret = u.GetWindowThreadProcessId(h, ctypes.byref(q))
            tid = int(ret) or None
            break
    return len(tops), tid


# ------------------------------------------------------------------ 判定
def grab_verdict(rec, base_frames):
    """第 4 帧判定（红线：前 3 帧命中不算命中）。"""
    norms = [f.get("norm") for f in rec.get("frames", [])]
    n = len(norms)
    f3 = norms[3] if n >= 4 else None
    raw = rec.get("raw_stack_crosscheck") or {}
    kp = raw.get("key_points_found") or {}
    ebp = [e.get("norm") for e in (raw.get("ebp_chain") or [])]
    v = {
        "n_frames": n, "norms": norms, "frame3": f3,
        "raw_207f17_on_raw_stack": bool(kp.get(SLEEP_F3)),
        "raw_20833f_on_raw_stack": bool(kp.get("gamemd+0x20833f")),
        "ebp_chain_norms": ebp,
    }
    if f3 == SLEEP_F3:
        v["verdict"] = "S_sleep_hit"
    elif f3 == NORMAL_F3:
        v["verdict"] = "normal_ingame_f3"
    elif f3 is None:
        v["verdict"] = "insufficient_depth_%d" % n
    else:
        v["verdict"] = "third_signature:" + str(f3)
    return v


def stall_segments(samples, stall_s=1.0):
    """frame 停推段（真实 t_mono_ns 差）。段内所有样本须四门控全 0 才算「且门控全 0」。"""
    segs = []
    cur = None
    for s in samples:
        f, t = s.get("frame"), s.get("t_mono_ns")
        gates0 = (s.get("all_gates_zero") is True)
        if f is None:
            if cur:
                segs.append(cur)
            cur = None
            continue
        if cur is not None and cur["frame"] == f:
            cur["t_end"] = t
            cur["n"] += 1
            cur["phases"].add(s.get("phase"))
            if not gates0:
                cur["gates_all_zero"] = False
        else:
            if cur:
                segs.append(cur)
            cur = {"frame": f, "t_start": t, "t_end": t, "n": 1,
                   "phases": {s.get("phase")}, "gates_all_zero": gates0}
    if cur:
        segs.append(cur)
    out = []
    for g in segs:
        dur = ((g["t_end"] - g["t_start"]) / 1e9) if g["t_end"] and g["t_start"] else 0.0
        out.append({"frame": g["frame"], "duration_s": round(dur, 3),
                    "n_samples": g["n"],
                    "phases": sorted(x for x in g["phases"] if x),
                    "gates_all_zero": bool(g["gates_all_zero"]),
                    "qualifies": bool(dur >= stall_s and g["gates_all_zero"])})
    return out


def phase_curve(samples, phase):
    mine = [s for s in samples if s["phase"] == phase]
    fv = [s["frame"] for s in mine if s["frame"] is not None]
    ts = [s["t_mono_ns"] for s in mine]
    dur = ((ts[-1] - ts[0]) / 1e9) if len(ts) >= 2 else 0.0
    # 1s 窗推进率
    adv = 0
    tot = 0
    for i in range(len(mine)):
        t = mine[i]["t_mono_ns"]
        j = i
        while j > 0 and t - mine[j - 1]["t_mono_ns"] < int(1.0e9):
            j -= 1
        if mine[i]["frame"] is not None and mine[j]["frame"] is not None \
                and t - mine[j]["t_mono_ns"] >= int(0.9e9):
            tot += 1
            if mine[i]["frame"] - mine[j]["frame"] > 0:
                adv += 1
    ints = [(ts[i] - ts[i - 1]) / 1e9 for i in range(1, len(ts))]
    return {
        "phase": phase, "n_samples": len(mine), "duration_s": round(dur, 3),
        "frame_first": fv[0] if fv else None,
        "frame_last": fv[-1] if fv else None,
        "frame_net_delta": (fv[-1] - fv[0]) if len(fv) >= 2 else None,
        "advancing_1s_windows": adv, "total_1s_windows": tot,
        "advancing_ratio": (round(adv / tot, 3) if tot else None),
        "mean_interval_ms": (round(1000.0 * sum(ints) / len(ints), 2) if ints else None),
        "max_interval_ms": (round(1000.0 * max(ints), 2) if ints else None),
    }


# ------------------------------------------------------------------ 报告渲染
def render_repro(meta, phases, segs_by_phase, segs_all, grabs, samples, a):
    t = []
    A = t.append
    A("# REPRO.md —— 过渡态定向复现 S_sleep（第 4 帧判定）")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("- 判别红线：正常局内前 3 帧与 S_sleep 相同（`ntdll+0x7858c / "
      "KERNELBASE+0x16a1f0 / +0x16a18f` 主循环 Sleep(30) 通用前缀）；"
      "**只看第 4 帧**：`gamemd+0x207f17` = S_sleep；`gamemd+0x15e332` = 正常态；"
      "其它 = 第三签名。")
    A("- 触发条件：`frame 连续 ≥%.1fs 不推进（真实 t_mono_ns 差）且四门控全 0` ⇒ 抓窗口线程栈。" %
      a.stall_threshold_s)
    A("- 采样间隔：%.0f ms；UI 全量快照 %.2f s 一次（子窗口数 + 按钮/Static 文字）。" %
      (a.interval_s * 1000, a.ui_interval_s))
    A("")
    hits = [g for g in grabs if g.get("grab_verdict", {}).get("verdict") == "S_sleep_hit"]
    thirds = [g for g in grabs if str(g.get("grab_verdict", {}).get("verdict", "")).startswith("third_signature")]
    A("## 1. 总判定")
    A("")
    if hits:
        A("**[已证] S_sleep 复现成功** —— 共 %d 次抓栈第 4 帧 = `gamemd+0x207f17`。" % len(hits))
    else:
        A("**本趟未复现 S_sleep**（无任何抓栈第 4 帧 = `gamemd+0x207f17`）。"
          "按红线「没观测到 ≠ 不存在」，如实记录覆盖窗口与停推段。")
    A("")
    A("## 2. 过渡窗口清单与帧推进曲线摘要")
    A("")
    A("| 窗口(phase) | stop | 时长(s) | 样本数 | frame 首→末 | 净增量 | 1s窗推进率 | 停推≥%.0fs段(全0) | 最长停推(s) | 抓栈 |" %
      a.stall_threshold_s)
    A("|---|---|---|---|---|---|---|---|---|---|")
    for ph, summ in phases.items():
        cur = phase_curve(samples, ph)
        qs = [s for s in segs_by_phase.get(ph, []) if s["qualifies"]]
        mx = max([s["duration_s"] for s in qs], default=0.0)
        A("| %s | %s | %s | %d | %s→%s | %s | %s | %d | %.2f | %s |" %
          (ph, summ.get("stop_reason"), cur["duration_s"], cur["n_samples"],
           cur["frame_first"], cur["frame_last"], cur["frame_net_delta"],
           ("%s/%s" % (cur["advancing_1s_windows"], cur["total_1s_windows"])
            if cur["total_1s_windows"] else "—"),
           len(qs), mx, "、".join(summ.get("grabs") or []) or "（无）"))
    A("")
    A("> 1s窗推进率 = 「最近 1.0s 内 frame 增量>0」的窗口占比（≈帧推进健康度）。"
      "停推段按真实 `t_mono_ns` 差计算，段内所有样本四门控全 0 才计入「且门控全 0」。"
      "**注意**：跨 phase 的停推段（同一冻结 frame 值跨越相位边界）会在每个跨越相位重复计数，"
      "「最长停推」是该段的全长；段的唯一明细以 §3 为准（每段一行，phases 列出全部跨越相位）。")
    A("")
    A("## 3. 「停推 ≥%.0fs 且门控全 0」段明细（全部）" % a.stall_threshold_s)
    A("")
    q_all = [s for s in segs_all if s["qualifies"]]
    if not q_all:
        A("本趟**未出现**任何满足「frame 停推 ≥%.0fs 且四门控全 0」的段。" % a.stall_threshold_s)
    else:
        A("| # | frame(停推值) | 时长(s) | 样本数 | 门控全0 | 跨越 phase |")
        A("|---|---|---|---|---|---|")
        for i, s in enumerate(q_all, 1):
            A("| %d | %s | %.2f | %d | %s | `%s` |" %
              (i, s["frame"], s["duration_s"], s["n_samples"],
               s["gates_all_zero"], "`,`".join(s["phases"])))
    A("")
    A("## 4. 抓栈判定（第 4 帧逐条）")
    A("")
    if not grabs:
        A("本趟无任何抓栈。")
    else:
        A("| label | phase | 触发原因 | frames | 第4帧 | 判定 | 0x207f17在原始栈 | 0x20833f在原始栈 | EBP链 | held(ms) |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for g in grabs:
            v = g.get("grab_verdict") or {}
            ti = (g.get("timing_ns") or {})
            A("| %s | %s | %s | %d | `%s` | **%s** | %s | %s | `%s` | %.3f |" %
              (g.get("label"), g.get("phase"),
               str(g.get("grab_reason"))[:60], v.get("n_frames", 0),
               v.get("frame3") or "—", v.get("verdict"),
               v.get("raw_207f17_on_raw_stack"), v.get("raw_20833f_on_raw_stack"),
               "→".join(x or "?" for x in (v.get("ebp_chain_norms") or [])) or "—",
               (ti.get("suspend_held_ns") or 0) / 1e6))
        A("")
        for g in grabs:
            v = g.get("grab_verdict") or {}
            sb = g.get("sentinels_at_grab") or {}
            A("### %s（%s）判定=%s" % (g.get("label"), g.get("phase"),
                                       v.get("verdict")))
            A("")
            A("- 抓栈时刻读数：frame=%s g1=%s g2=%s g3=%s g4=%s mode=%s "
              "A8E9A0=%s ABCD58=%s exitstate=%s" %
              (sb.get("frame"), sb.get("g1"), sb.get("g2"), sb.get("g3"),
               sb.get("g4"), sb.get("mode_A8B238"), sb.get("ingame_A8E9A0"),
               sb.get("latch_ABCD58"), sb.get("exitstate")))
            A("- 逐帧（**返回地址**，非执行点；frame[0]=被挂起瞬间 EIP）：")
            A("")
            for i, f in enumerate(g.get("frames", [])):
                note = PREV_CALLS.get(f.get("norm") or "",
                                      "符号未解析，不作已证事实")
                A("  - #%d `%s` addr=%s —— %s" %
                  (i, f.get("name") or "?", f.get("addr_hex"), note))
            A("")
    A("## 5. 第三签名清单")
    A("")
    if thirds:
        for g in thirds:
            v = g.get("grab_verdict") or {}
            A("- %s（%s）：%s，帧序列 `%s`" %
              (g.get("label"), g.get("phase"), v.get("verdict"),
               " → ".join(x or "?" for x in (v.get("norms") or []))))
    else:
        A("无（没有出现既非 `gamemd+0x207f17` 也非 `gamemd+0x15e332` 的第 4 帧）。")
    A("")
    A("## 6. 结论边界")
    A("")
    A("- 判定只对本趟该 pid / 该地图 / 该时刻成立，不外推。")
    A("- 「没观测到」≠「不存在」：本趟未复现时，只说明四个过渡窗口在本趟条件下"
      "未出现 S_sleep 特征栈，不排除其它过渡路径或更长等待下的出现。")
    A("- 栈帧是返回地址；`stackwalk_false:0` 是正常走完不是失败；"
      "原始栈/EBP 链仅作外层帧交叉核验，栈残留 ≠ 活跃帧。")
    A("")
    return "\n".join(t) + "\n"


def render_safety(meta, grabs, a):
    t = []
    A = t.append
    A("# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`；单次挂起预算 = **%.1f ms**（suspend_held_ns）。" %
      (RUN_ID, utc_iso(), a.budget_ms))
    A("")
    A("## 1. 逐次抓栈的挂起/恢复核对")
    A("")
    A("| label | tid | prev_count | resume_ret | sample_state | resume_state | held(ms) | errors | 干净还原 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for g in grabs:
        if "error" in g and not g.get("label"):
            continue
        clean = g.get("clean_restore_no_residual_suspend")
        A("| %s | %s | %s | %s | %s | %s | %.3f | %s | %s |" %
          (g.get("label"), g.get("tid"), g.get("prev_count"), g.get("resume_ret"),
           g.get("sample_state"), g.get("resume_state"),
           ((g.get("timing_ns") or {}).get("suspend_held_ns") or 0) / 1e6,
           json.dumps(g.get("errors") or [], ensure_ascii=False), clean))
    ok = [g for g in grabs if g.get("clean_restore_no_residual_suspend")]
    A("")
    A("- 抓栈总数 %d；干净还原（prev=0 → resume_ret=1）=%d ⇒ **零残留挂起 = %s**。" %
      (len(grabs), len(ok), "是" if grabs and len(ok) == len(grabs)
       else ("是（无抓栈）" if not grabs else "否 / 见上表")))
    A("- hold_abort（超预算中止）= %s。" % meta.get("hold_abort"))
    A("")
    A("## 2. 安全约束落地")
    A("")
    A("1. 逐线程「挂→走→立刻恢复」（W3 `do_grab`→r2 `sample_single` 单线程口径）；"
      "`try/finally` 兜底；`prev_count>0` 的线程被跳过。")
    A("2. 跳过自身线程：目标 tid=%s ≠ 采样器自身线程（GetCurrentThreadId=%s）。" %
      (meta.get("c0_tid"), meta.get("self_tid")))
    A("3. 符号初始化在挂起前完成（`attach_walker` 在任何抓栈之前执行）。")
    A("4. 单次挂起 ≤%.0f ms；r2 事件预算 %.0f ms；两者分别记录。" %
      (a.budget_ms, a.r2_event_budget_ms))
    A("5. 全程只读 `ReadProcessMemory`；无写目标内存、无注入、无断点、无 MiniDump、无 hook。")
    A("6. 只处理自己启动的 pid=%s；收尾残留核对见 CONFIG_RESTORE.md。" % meta.get("pid"))
    A("")
    return "\n".join(t) + "\n"


def render_config_restore(prelaunch, residual_before, residual_after, rows,
                          inv_counts, diff, restore_verify, close_steps):
    t = []
    A = t.append
    A("# CONFIG_RESTORE.md —— 配置逐字节还原与残留进程核对")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    A("## 1. 启动前守卫（实算 SHA-256）")
    A("")
    A("| 文件 | bytes | 实算 SHA-256 | 期望 | 一致 |")
    A("|---|---|---|---|---|")
    for name in VERIFY_FILES:
        r = prelaunch.get(name, {})
        A("| %s | %s | `%s` | `%s` | %s |" %
          (name, r.get("bytes"), r.get("sha256"), r.get("expected"), r.get("match")))
    A("")
    A("## 2. 残留进程核对")
    A("")
    A("- 启动前 gamemd 残留：**%d** 个 `%s`" % (len(residual_before), residual_before))
    A("- 收尾后 gamemd 残留：**%d** 个 `%s`" % (len(residual_after), residual_after))
    A("- 关闭步骤：")
    for s in close_steps:
        A("  - %s" % s)
    A("")
    A("## 3. 配置逐字节还原")
    A("")
    A("| 文件 | 还原前 SHA | 基线副本 SHA | 还原后 SHA | 字节一致 | 哈希一致 |")
    A("|---|---|---|---|---|---|")
    for r in rows:
        if r.get("verify_only"):
            A("| %s | (仅校验) | `%s` | `%s` | — | 未改动=%s |" %
              (r["file"], r.get("baseline_tsv_sha256"), r.get("post_sha256"),
               r.get("unchanged")))
        elif "error" in r:
            A("| %s | - | - | - | - | %s |" % (r["file"], r["error"]))
        else:
            A("| %s | `%s` | `%s` | `%s` | %s | %s |" %
              (r["file"], r.get("pre_restore_sha256"), r.get("baseline_tsv_sha256"),
               r.get("post_restore_sha256"), r.get("byte_identical_to_baseline"),
               r.get("sha_match")))
    A("")
    A("本卡独立逐字节复核：")
    A("")
    A("| 文件 | 基线 SHA | 目标 SHA | 字节相同 | 与守卫一致 |")
    A("|---|---|---|---|---|")
    for r in restore_verify:
        if "error" in r:
            A("| %s | - | - | - | %s |" % (r["file"], r["error"]))
        else:
            A("| %s | `%s` | `%s` | %s | %s |" %
              (r["file"], r.get("baseline_sha256"), r.get("target_sha256"),
               r.get("byte_identical"), r.get("matches_expected")))
    A("")
    A("## 4. 游戏写回文件清单（还原前比对）")
    A("")
    A("- 启动前 %d 项 / 收尾 %d 项；新增 %d / 删除 %d / 变化 %d" %
      (inv_counts[0], inv_counts[1], len(diff.get("added") or []),
       len(diff.get("removed") or []), len(diff.get("changed") or [])))
    for k in ("added", "removed", "changed"):
        A("- %s (%d): %s" % (k, len(diff.get(k) or []),
                             "、".join("`%s`" % x for x in (diff.get(k) or [])[:60])
                             or "（无）"))
    A("")
    return "\n".join(t) + "\n"


def render_runlog(meta, phases, phase_events, exit_code, started, ended, cmdline):
    t = []
    A = t.append
    A("# RUNLOG.md —— 过渡态 S_sleep 复现执行日志")
    A("")
    A("- run_id: `%s`" % RUN_ID)
    A("- 开始(UTC): `%s`；结束(UTC): `%s`；本地: `%s`" % (started, ended, local_iso()))
    A("- 退出码: **%d**" % exit_code)
    A("- 命令: `%s`" % cmdline)
    A("- Python: `%s` / `%s`" % (sys.executable, sys.version.split()[0]))
    A("- pid=%s tid(c0)=%s self_tid=%s is32=%s walker_ok=%s" %
      (meta.get("pid"), meta.get("c0_tid"), meta.get("self_tid"),
       meta.get("is32"), meta.get("walker_ok")))
    A("- 实例锁：开工 owner=%s → 收尾恢复 owner=lead。" % SELF_OWNER)
    A("")
    A("## 1. 参数")
    A("")
    A("```json")
    A(jdump({k: meta.get("args_raw", {}).get(k) for k in
             ("map_pattern", "interval_ms", "ui_interval_ms", "stall_threshold_s",
              "budget_ms", "r2_event_budget_ms", "grab_cap_per_phase",
              "grab_cap_total", "grab_cooldown_s")}))
    A("```")
    A("")
    A("## 2. 相位摘要")
    A("")
    A("| phase | stop | 时长(s) | 样本 | frame 首→末 | 抓栈 |")
    A("|---|---|---|---|---|---|")
    for ph, summ in phases.items():
        A("| %s | %s | %s | %s | %s→%s | %s |" %
          (ph, summ.get("stop_reason"), summ.get("duration_s"),
           summ.get("n_samples"), summ.get("frame_first"), summ.get("frame_last"),
           "、".join(summ.get("grabs") or []) or "（无）"))
    A("")
    A("## 3. 相位事件时间线（节选）")
    A("")
    for e in phase_events:
        A("- `%s` [%s] %s" % (e["t_utc_iso"], e["phase"], e["msg"]))
    A("")
    A("## 4. stdout（首 80 行 + 尾 80 行，完整见 out/stdout.txt）")
    A("")
    A("```text")
    for line in LOG_LINES[:80]:
        A(line)
    if len(LOG_LINES) > 160:
        A("... (省略 %d 行) ..." % (len(LOG_LINES) - 160))
    for line in LOG_LINES[-80:]:
        A(line)
    A("```")
    A("")
    A("## 5. 收尾")
    A("")
    for s in (meta.get("close_steps") or []):
        A("- %s" % s)
    A("- 收尾后 gamemd 残留: %d `%s`" %
      (len(meta.get("residual_after") or []), meta.get("residual_after")))
    A("")
    return "\n".join(t) + "\n"


def render_uncovered(meta, phases, segs_all, grabs, w_b, w_c, w_d):
    t = []
    A = t.append
    A("# UNCOVERED.md —— 未覆盖与不确定项")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    items = []
    if w_c and not w_c.get("attempted"):
        items.append("**对局结束过渡（W_C）未覆盖**：%s。" %
                     (w_c.get("reason") or "自然结束不可达且未发现结算入口"))
    elif w_c and w_c.get("attempted"):
        items.append("**对局结束过渡（W_C）覆盖方式**：%s；stop=%s。" %
                     (w_c.get("how"), w_c.get("stop")))
    if w_b and not w_b.get("exited"):
        items.append("**退出到主菜单过渡（W_B）未完成退出**：%s；W_D 因此未执行。" %
                     (w_b.get("reason") or "确认路径未成功"))
    if w_d and not w_d.get("attempted"):
        items.append("**再次进图（W_D）未执行**：%s。" % (w_d.get("reason") or "未回到主菜单"))
    if not grabs:
        items.append("**零抓栈**：整趟未触发停推条件或抓栈均失败；"
                     "不得用「无帧」冒充结论。")
    if not [s for s in segs_all if s["qualifies"]]:
        items.append("**零停推段**：整趟未出现「frame 停推 ≥1s 且门控全 0」段；"
                     "按红线如实记录，未用更短阈值凑事件。")
    items += [
        "**符号解析未做**：USER32/KERNELBASE/ntdll 偏移只按 模块+偏移 比对；"
        "帧的「前一条调用」描述仅对 Lead 已证的 `gamemd+0x207f17(Sleep 30)` 与 "
        "`gamemd+0x20833f(EnumChildWindows)` 成立。",
        "**单线程采样**：只抓游戏窗口线程；其它线程（音频/网络/渲染）状态本卡未采。",
        "**抓栈扰动**：每次抓栈短暂冻结窗口线程（≤50ms）；已量化记录但不宣称零扰动。",
        "**StackWalk64 深度局限**：32 位无 PDB 下走查常在第 4 帧正常终止"
        "（`stackwalk_false:0`）；更外层帧依赖挂起窗口内只读原始栈 + EBP 链交叉核验，"
        "栈残留 ≠ 活跃帧。",
        "**单图单趟**：仅 `%s` / 一局内连续覆盖；未覆盖其它地图、不同负载、"
        "联机/录像、长时间运行后的自然停推。" % meta.get("map", ""),
    ]
    for i, s in enumerate(items, 1):
        A("%d. %s" % (i, s))
        A("")
    return "\n".join(t) + "\n"


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
    ap.add_argument("--interval-ms", type=float, default=30.0)
    ap.add_argument("--ui-interval-ms", type=float, default=500.0)
    ap.add_argument("--stall-threshold-s", type=float, default=1.0)
    ap.add_argument("--budget-ms", type=float, default=50.0)
    ap.add_argument("--r2-event-budget-ms", type=float, default=300.0)
    ap.add_argument("--grab-cap-per-phase", type=int, default=3)
    ap.add_argument("--grab-cap-total", type=int, default=22)
    ap.add_argument("--grab-cooldown-s", type=float, default=2.5)
    ap.add_argument("--menu-timeout", type=float, default=120.0)
    ap.add_argument("--stable-seconds", type=float, default=10.0)
    ap.add_argument("--menu-tail-seconds", type=float, default=15.0)
    ap.add_argument("--w-b-timeout", type=float, default=150.0)
    ap.add_argument("--w-c-timeout", type=float, default=90.0)
    ap.add_argument("--load-timeout", type=float, default=180.0)
    ap.add_argument("--max-frames", type=int, default=20)
    ap.add_argument("--raw-stack-bytes", type=int, default=65536)
    a = ap.parse_args()
    a.interval_s = a.interval_ms / 1000.0
    a.ui_interval_s = a.ui_interval_ms / 1000.0
    args_raw = {k: getattr(a, k) for k in (
        "map_pattern", "interval_ms", "ui_interval_ms", "stall_threshold_s",
        "budget_ms", "r2_event_budget_ms", "grab_cap_per_phase", "grab_cap_total",
        "grab_cooldown_s", "menu_timeout", "stable_seconds", "menu_tail_seconds",
        "w_b_timeout", "w_c_timeout", "load_timeout")}

    OUT.mkdir(parents=True, exist_ok=True)
    STACKS.mkdir(parents=True, exist_ok=True)
    started_utc = utc_iso()
    cmdline = "%s -X utf8 %s %s" % (
        sys.executable, str(W6 / "transition_probe.py"),
        " ".join("%s" % x for x in sys.argv[1:]))

    meta = {"run_id": RUN_ID, "pid": None, "c0_tid": None, "self_tid": None,
            "is32": None, "walker_ok": None, "map": None, "hold_abort": False,
            "residual_before": [], "residual_after": [], "close_steps": [],
            "error": None, "args_raw": args_raw}
    exit_code = 0
    prelaunch = {}
    rows = []
    restore_verify = []
    diff = {"added": [], "removed": [], "changed": []}
    inv_before, inv_after = {}, {}
    close_steps = []
    lock_restored = False
    w_b_info = {"exited": False, "reason": None, "clicks": []}
    w_c_info = {"attempted": False, "how": None, "stop": None}
    w_d_info = {"attempted": False, "reason": None}

    w3 = None
    w1 = None
    r2 = None
    sw = None
    sampler = None
    walker = None
    hproc = None
    sink = None
    pid = 0
    game_hwnd = 0

    try:
        # ---------------- S0 守卫 ----------------
        log("[S0] 实例锁 + 残留进程 + 哈希守卫")
        lock_state = check_lock()
        log("    实例锁 owner 状态 = %s（接管）" % lock_state)
        write_lock(SELF_OWNER, "W6 过渡态定向复现 S_sleep（真机单实例）")
        w3 = load_module("w6_w3_stack_contrast", W3_PATH)
        w1, r2, sw = w3.load_assets()
        w3.OUT = STACKS                     # do_grab/write_json → out/stacks/
        w3.log = log
        w3.SENTINELS = dict(w3.SENTINELS)
        w3.SENTINELS["exitstate"] = (0x00A8EDD8, 4)
        log("    只读资产加载完成（W1 导航 / r2 采样器 / e3_stackwalker）")

        residual_before = w1.list_gamemd()
        meta["residual_before"] = residual_before
        if residual_before:
            raise GuardStop("启动前已存在 gamemd 残留，停手不杀：%r" % residual_before)
        for name in VERIFY_FILES:
            p = GAME_DIR / name
            if not p.exists():
                raise GuardStop("缺少文件 %s" % p)
            h = sha256_file(p)
            prelaunch[name] = {"bytes": p.stat().st_size, "sha256": h,
                               "expected": EXPECTED_HASHES[name],
                               "match": h == EXPECTED_HASHES[name]}
            log("    %-20s %8d %s match=%s" %
                (name, prelaunch[name]["bytes"], h, prelaunch[name]["match"]))
        if not all(v["match"] for v in prelaunch.values()):
            bad = [n for n, v in prelaunch.items() if not v["match"]]
            raise GuardStop("启动前哈希不一致，按卡停止：%s" % bad)
        inv_before = w1.inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inv_before))
        base = w3.load_baseline()
        w3.write_json("baseline_14412.json", base)
        base_norms = [f["norm"] for f in base["frames"]]
        log("    基准 7 帧：%s" % " → ".join(base_norms))
        if base_norms[3] != SLEEP_F3:
            raise GuardStop("基准第 4 帧 = %s ≠ %s，判锚失效" % (base_norms[3], SLEEP_F3))
        write_json("prelaunch.json", {"residual_before": residual_before,
                                      "hashes": prelaunch,
                                      "baseline_norms": base_norms})

        # ---------------- S1 启动 ----------------
        log("[S1] WMI 分离启动 gamemd.exe")
        launcher_pid = w1.launch_game()
        pid, own = w1.wait_for_pid(launcher_pid, a.menu_timeout)
        meta["pid"] = pid
        log("    pid=%d 归属=%s launcher_pid=%d" % (pid, own, launcher_pid))
        hproc = w1.k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess 失败")
        flag = wt.BOOL(0)
        w1.k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        sig = w1.rpm(hproc, w3.CODE_SIG_ADDR, len(w3.CODE_SIG_EXPECT))
        sig_ok = (sig == w3.CODE_SIG_EXPECT)
        log("    is32=%s 代码签名@0x55DE4F ok=%s" % (is32, sig_ok))
        if not sig_ok:
            raise GuardStop("代码签名不匹配，地址基线失效，停手")

        # ---------------- S2 回溯器挂载（挂起前） ----------------
        log("[S2] 挂起任何线程之前完成 StackWalk64/符号初始化")
        r2.bind_real_ops()
        sampler = r2.StackSampler(budget_ms=a.r2_event_budget_ms)
        att = w3.attach_walker(r2, sw, sampler, hproc, pid, is32,
                               max_frames=a.max_frames)
        meta["walker_ok"] = att["ok"]
        if not att["ok"]:
            raise GuardStop("回溯器挂载失败(%s)，不抓栈" % att["err"])
        walker = att["walker"]
        mods_all = att["mods_all"]
        raw_state = w3.install_raw_capture(walker, w1, hproc, a.raw_stack_bytes)
        log("    walker ok n_modules=%d max_frames=%d raw_bytes=%d" %
            (att["n_modules"], a.max_frames, a.raw_stack_bytes))
        wtid, hwnds = w3.game_window_tid(w1, pid)
        meta["c0_tid"] = int(wtid) if wtid else None
        log("    游戏窗口 hwnd=%s tid=%s" % (hwnds[:1], wtid))
        if not wtid:
            raise GuardStop("未找到游戏窗口线程，不抓栈")
        k32s = ctypes.WinDLL("kernel32", use_last_error=True)
        k32s.GetCurrentThreadId.restype = wt.DWORD
        cur_tid = int(k32s.GetCurrentThreadId())
        meta["self_tid"] = cur_tid
        if int(wtid) == cur_tid:
            raise GuardStop("目标 tid == 采样器自身线程，拒绝")
        c0_tid = int(wtid)

        sink = w1.NDJSONSink(OUT / "samples.ndjson")
        ts = TransitionSampler(w1, w3, hproc, pid, c0_tid, r2, walker, raw_state,
                               mods_all, base["frames"], sink, a)
        ts.r2_sampler_stackobj = sampler
        game_hwnd = int(hwnds[0]) if hwnds else 0

        # ---------------- P0 主菜单等待（intro 不抓栈；menu_idle 抓栈） ----------------
        ts.wait_ui("P0_intro", lambda s: state_flags(s)["main_menu"],
                   timeout=a.menu_timeout, ui_interval=0.3, grab_reason=None)
        ph = ts.wait_ui("P0_menu_idle", lambda s: False,
                        timeout=12.0, ui_interval=0.5,
                        grab_reason="menu_idle_stall")

        # ---------------- W_A 进图窗口 ----------------
        log("[W_A] 导航 SinglePlayer → Skirmish → 选图 → StartGame")
        if not w1.click(pid, "GUI:SinglePlayer", 3.0):
            raise GuardStop("GUI:SinglePlayer 点击失败")
        if not w1.click(pid, "GUI:Skirmish", 3.5):
            raise GuardStop("GUI:Skirmish 点击失败")
        map_info = w1.select_map_by_name(hproc, pid, a.map_pattern)
        meta["map"] = map_info
        log("    地图：index=%s name=%r" % (map_info.get("index"),
                                           map_info.get("display_name")))
        hwnds2 = w1.game_top_windows(pid)
        if hwnds2:
            game_hwnd = int(hwnds2[0])
        if not w1.click(pid, "GUI:StartGame", 0.05):
            raise GuardStop("GUI:StartGame 点击失败")
        phase_log("W_A_load", "已点击 GUI:StartGame，从点击瞬间开始密集采样")

        def w_a_stop(state):
            return ("stable_%.1fs" % a.stable_seconds
                    if state["advance_stable_s"] >= a.stable_seconds else None)

        ph = ts.run_phase("W_A_load", timeout=a.load_timeout, stop_fn=w_a_stop,
                          ui_interval=a.ui_interval_s,
                          grab_reason="load_transition_stall")
        if ph["stop_reason"] == "process_exited":
            raise GuardStop("W_A 期间进程退出")
        # 局内平静态对照抓栈（协议强制 N0；非停推触发）
        ts.wait_ui("W_A_ingame", lambda s: False, timeout=5.0, ui_interval=0.5)
        ts.grab_now("W_A_ingame", "N0_normal_ingame_contrast")
        ts.wait_ui("W_A_ingame", lambda s: False, timeout=8.0, ui_interval=0.5)

        # ---------------- W_B 退出到主菜单过渡 ----------------
        log("[W_B] Esc → GUI:AbortMission → 确认（Yes 路径）")
        w_b_t0 = time.perf_counter()
        tried_positions = set()
        reopened = 0
        landed = None
        while time.perf_counter() - w_b_t0 < a.w_b_timeout and reopened <= 4:
            snap = ui_snapshot(w1, pid, full=True)
            sf = state_flags(snap)
            if sf["main_menu"]:
                landed = "main_menu_no_dialog"
                break
            # 1) 打开 Esc 局内菜单（若未开）
            menu_open = any((b.get("text") or "").lower().startswith("gui:")
                            for b in (snap.buttons or []))
            if not menu_open and not sf["dialog_askabort"]:
                w1.force_foreground(game_hwnd)
                w1.send_esc()
                ts.wait_ui("W_B_esc_menu",
                           lambda s: (any((b.get("text") or "").lower()
                                          .startswith("gui:")
                                          for b in (s.buttons or []))
                                      or state_flags(s)["dialog_askabort"]),
                           timeout=6.0, ui_interval=0.2)
            snap = ui_snapshot(w1, pid, full=True)
            sf = state_flags(snap)
            if sf["main_menu"]:
                landed = "main_menu_no_dialog"
                break
            # 2) 确认框未开时先点 GUI:AbortMission
            if not sf["dialog_askabort"]:
                ab = next((b for b in snap.buttons
                           if "abortmission" in norm_txt(b["text"])), None)
                if ab is None:
                    phase_log("W_B_esc_menu", "菜单无 AbortMission（按钮=%s）" %
                              [b["text"] for b in snap.buttons][:12])
                    reopened += 1
                    time.sleep(0.8)
                    continue
                okc = bool(w1.u.PostMessageW(ab["hwnd"], 0x00F5, 0, 0))
                phase_log("W_B_esc_menu", "点击 %r hwnd=%d -> %s" %
                          (ab["text"], ab["hwnd"], okc))
                ts.wait_ui("W_B_esc_menu", lambda s: state_flags(s)["dialog_askabort"],
                           timeout=6.0, ui_interval=0.2)
                snap = ui_snapshot(w1, pid, full=True)
                sf = state_flags(snap)
            if not sf["dialog_askabort"]:
                phase_log("W_B_esc_menu", "确认框未出现（按钮=%s）" %
                          [b["text"] for b in snap.buttons][:12])
                reopened += 1
                continue
            # 3) 确认对话框候选：yes 词汇优先，其次 GUI:Blank（位图按钮）
            cands = []
            for b in snap.buttons:
                n = norm_txt(b["text"])
                if not b["visible"]:
                    continue
                if any(w in n for w in ("yes", "ok", "confirm", "sure", "确定",
                                        "是")):
                    cands.append((0, b["hwnd"], b["text"]))
                elif n == "blank" or n == "":
                    cands.append((1, b["hwnd"], b["text"]))
            cands.sort()
            pos_seq = list(cands)
            clicked_any = False
            for pos, (prio, h, txt) in enumerate(pos_seq):
                if pos in tried_positions:
                    continue
                tried_positions.add(pos)
                okc = bool(w1.u.PostMessageW(h, 0x00F5, 0, 0))
                w_b_info["clicks"].append({"pos": pos, "prio": prio, "hwnd": h,
                                           "text": txt, "clicked": okc,
                                           "t_utc_iso": utc_iso()})
                phase_log("W_B_confirm_click",
                          "点击候选 pos=%d prio=%d text=%r hwnd=%d -> %s" %
                          (pos, prio, txt, h, okc))
                clicked_any = True
                # 阶段1：对话框是否关闭（3s 内仍开 ⇒ 该候选无效，立刻换下一个）
                ph = ts.run_phase("W_B_confirm_click", timeout=3.0,
                                  stop_fn=lambda st: (
                                      "dialog_gone"
                                      if not state_flags(st["snap"])["dialog_askabort"]
                                      else None),
                                  ui_interval=0.2,
                                  grab_reason="confirm_click_stall")
                if ph["stop_reason"] != "dialog_gone":
                    s_now, alive = ts.read_state()
                    if not alive:
                        landed = "process_exited"
                        break
                    phase_log("W_B_confirm_click",
                              "候选 pos=%d 点击后确认框仍在，试下一个" % pos)
                    continue
                # 阶段2：落点判别（最长 25s）：主菜单 / 遭遇战设置屏 / 结算屏 /
                # 帧恢复推进；期间「帧停推+门控全0」自动抓栈（exit 过渡高价值窗口）
                def _land_stop(st):
                    sf3 = state_flags(st["snap"])
                    if sf3["main_menu"]:
                        return "main_menu"
                    if sf3["skirmish_screen"]:
                        return "skirmish_screen"
                    if sf3["score_like"]:
                        return "score_screen"
                    if st["advance_stable_s"] >= 2.0:
                        return "back_ingame"
                    return None
                ph = ts.run_phase("W_B_confirm_click", timeout=25.0,
                                  stop_fn=_land_stop, ui_interval=0.3,
                                  grab_reason="confirm_click_stall")
                landed_now = ph["stop_reason"]
                snap2 = ui_snapshot(w1, pid, full=True)
                sf2 = state_flags(snap2)
                s_now, alive = ts.read_state()
                if not alive:
                    landed = "process_exited"
                    break
                if landed_now == "main_menu" or sf2["main_menu"]:
                    landed = "main_menu"
                    break
                if landed_now == "skirmish_screen" or sf2["skirmish_screen"]:
                    landed = "skirmish_screen"
                    break
                if landed_now == "score_screen" or sf2["score_like"]:
                    landed = "score_screen"
                    break
                if landed_now == "back_ingame":
                    phase_log("W_B_confirm_click",
                              "候选 pos=%d 关闭对话框回局内（当作 No）；重开菜单换下一个" % pos)
                    break
                if sf2["dialog_askabort"]:
                    continue                      # 该候选无效，试下一个
                # 25s 内既非主菜单也非结算也非回局内 ⇒ 如实记 unknown（不过度等待）
                phase_log("W_B_confirm_click",
                          "候选 pos=%d 后落点未知（stop=%s 按钮=%s）" %
                          (pos, landed_now,
                           [b["text"] for b in snap2.buttons][:12]))
                landed = "unknown_after_click"
                break
            if landed in ("main_menu", "skirmish_screen", "score_screen",
                          "process_exited", "main_menu_no_dialog",
                          "unknown_after_click"):
                break
            reopened += 1
            if reopened > 3:
                break
        w_b_dur = time.perf_counter() - w_b_t0
        w_b_info["exited"] = landed in ("main_menu", "main_menu_no_dialog",
                                        "skirmish_screen")
        w_b_info["landed"] = landed
        w_b_info["duration_s"] = round(w_b_dur, 2)
        if not w_b_info["exited"]:
            w_b_info["reason"] = "确认路径未到达主菜单/遭遇战设置屏（landed=%s）" % landed
            log("!! W_B 未退出：landed=%s" % landed)

        if w_b_info["exited"]:
            # 退出完成后的菜单闲置尾段（主菜单或遭遇战设置屏）：
            # 帧冻结+门控全0 ⇒ 抓栈（S_sleep 高嫌疑位；run3 在此已两次命中）
            ts.wait_ui("idle_after_exit", lambda s: False,
                       timeout=a.menu_tail_seconds, ui_interval=0.5,
                       grab_reason="menu_idle_stall")

        # ---------------- W_C 对局结束过渡 ----------------
        snap = ui_snapshot(w1, pid, full=True)
        sf = state_flags(snap)
        if sf["score_like"]:
            w_c_info["attempted"] = True
            w_c_info["how"] = "结算屏按钮（ texts=%s）" % [b["text"] for b in snap.buttons][:12]
            log("[W_C] 检测到疑似结算屏，尝试点击 restart/continue 类按钮")
            cands = [b for b in snap.buttons
                     if any(w in norm_txt(b["text"]) for w in
                            ("restart", "again", "continue", "重新", "继续", "再玩"))]
            for b in cands[:3]:
                okc = bool(w1.u.PostMessageW(b["hwnd"], 0x00F5, 0, 0))
                phase_log("W_C_settlement", "点击 %r hwnd=%d -> %s" %
                          (b["text"], b["hwnd"], okc))
                ph = ts.run_phase("W_C_settlement", timeout=a.w_c_timeout,
                                  stop_fn=lambda st: (
                                      "main_menu" if state_flags(st["snap"])["main_menu"]
                                      else ("advancing" if st["advance_stable_s"] >= 8.0
                                            else None)),
                                  ui_interval=a.ui_interval_s,
                                  grab_reason="settlement_stall")
                w_c_info["stop"] = ph["stop_reason"]
                if state_flags(getattr(ts, "last_snap")).get("main_menu"):
                    ts.wait_ui("menu_idle_after_w_c", lambda s: False,
                               timeout=8.0, ui_interval=0.5,
                               grab_reason="menu_idle_stall")
                    break
        else:
            w_c_info["attempted"] = False
            w_c_info["reason"] = ("对局结束过渡不可达：中止路径落点=%s（未出现结算屏），"
                                  "自然结束不可脚本化" % landed)

        # ---------------- W_D 再次进图 ----------------
        # run3 实测：确认放弃后落点是**遭遇战设置屏**（GUI:Back/StartGame/ChooseMap…），
        # 不是主菜单 ⇒ 两个起点都支持：设置屏直接 StartGame；主菜单走完整导航。
        snap = ui_snapshot(w1, pid, full=True)
        sf_d = state_flags(snap)
        from_skirmish = bool(sf_d["skirmish_screen"])
        from_main_menu = bool(sf_d["main_menu"])
        if from_skirmish or from_main_menu:
            w_d_info["attempted"] = True
            w_d_info["start_from"] = ("skirmish_screen" if from_skirmish
                                      else "main_menu")
            log("[W_D] 再次开局（起点=%s，覆盖 加载→局内 边界）" %
                w_d_info["start_from"])
            map_info2 = None
            if from_main_menu:
                if w1.click(pid, "GUI:SinglePlayer", 3.0) and \
                        w1.click(pid, "GUI:Skirmish", 3.5):
                    try:
                        map_info2 = w1.select_map_by_name(hproc, pid, a.map_pattern)
                        meta["map2"] = map_info2
                    except Exception as e:                        # noqa: BLE001
                        log("!! W_D 选图失败 %r" % e)
                        w_d_info["reason"] = "选图失败"
                        map_info2 = None
                else:
                    w_d_info["reason"] = "主菜单导航按钮未命中"
            if not w_d_info.get("reason"):
                if not w1.click(pid, "GUI:StartGame", 0.05):
                    log("!! W_D StartGame 点击失败")
                    w_d_info["reason"] = "StartGame 点击失败"
                else:
                    phase_log("W_D_load", "第二次 StartGame，开始密集采样")

                    def w_d_stop(state):
                        return ("stable_%.1fs" % a.stable_seconds
                                if state["advance_stable_s"] >= a.stable_seconds
                                else None)

                    ts.run_phase("W_D_load", timeout=a.load_timeout,
                                 stop_fn=w_d_stop, ui_interval=a.ui_interval_s,
                                 grab_reason="load_transition_stall2")
                    ts.wait_ui("W_D_ingame", lambda s: False, timeout=5.0,
                               ui_interval=0.5)
                    ts.grab_now("W_D_ingame", "N1_normal_ingame_contrast")
                    ts.wait_ui("W_D_ingame", lambda s: False, timeout=6.0,
                               ui_interval=0.5)
        else:
            w_d_info["reason"] = "落点既非遭遇战设置屏也非主菜单（按钮=%s）" % \
                [b["text"] for b in snap.buttons][:10]

    except GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
    except Exception as e:                                        # noqa: BLE001
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())

    # ---------------- 收尾 ----------------
    finally:
        ended_utc = utc_iso()
        log("[P1] 收尾：walker cleanup → 关游戏 → 残留核对 → 配置还原 → 锁恢复")
        ts_obj = locals().get("ts")
        grabs = ts_obj.grabs if ts_obj is not None else []
        samples = ts_obj.samples if ts_obj is not None else []
        try:
            if walker is not None:
                walker.cleanup()
                log("    SymCleanup 完成")
        except Exception as e:                                    # noqa: BLE001
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
        except Exception as e:                                    # noqa: BLE001
            log("    CloseHandle 异常 %r" % e)
        try:
            close_steps = (w1.close_game(pid, game_hwnd) if (w1 is not None and pid)
                           else ["no_pid_no_launch: 未启动实例，无需关闭"])
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:                                    # noqa: BLE001
            close_steps = ["close_game 异常: %r" % e]
        try:
            residual_after = w1.list_gamemd() if w1 is not None else []
        except Exception:
            residual_after = []
        meta["residual_after"] = residual_after
        log("    收尾后 gamemd 残留 = %d %s" % (len(residual_after), residual_after))
        try:
            inv_after = w1.inventory(GAME_DIR) if w1 is not None else {}
            diff = (w1.diff_inventory(inv_before, inv_after)
                    if w1 is not None else diff)
        except Exception as e:                                    # noqa: BLE001
            log("    inventory_after 异常 %r" % e)
        try:
            rows = w1.restore_configs() if w1 is not None else []
        except Exception as e:                                    # noqa: BLE001
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
        for name in RESTORE_FILES:
            try:
                sb = (BASELINE_DIR / name).read_bytes()
                db = (GAME_DIR / name).read_bytes()
                restore_verify.append({
                    "file": name,
                    "baseline_sha256": hashlib.sha256(sb).hexdigest(),
                    "target_sha256": hashlib.sha256(db).hexdigest(),
                    "byte_identical": sb == db,
                    "matches_expected": (hashlib.sha256(db).hexdigest()
                                         == EXPECTED_HASHES[name])})
            except Exception as e:                                # noqa: BLE001
                restore_verify.append({"file": name, "error": repr(e)})
        # 实例锁恢复 owner=lead
        try:
            write_lock(LEAD_OWNER, "W6 收尾恢复：真机实例互斥归还 Lead")
            lock_restored = True
            log("    实例锁已恢复 owner=lead")
        except Exception as e:                                    # noqa: BLE001
            log("    实例锁恢复异常 %r" % e)
        meta["lock_restored"] = lock_restored

        # ---------------- 分析与交付 ----------------
        try:
            if ts_obj is not None:
                segs_all = stall_segments(samples, a.stall_threshold_s)
                phases_seq = []
                for s in samples:
                    if s["phase"] not in phases_seq:
                        phases_seq.append(s["phase"])
                segs_by_phase = {}
                for ph in phases_seq:
                    segs_by_phase[ph] = [s for s in segs_all if ph in s["phases"]]
                phases = {}
                for ph in phases_seq:
                    mine = [x for x in samples if x["phase"] == ph]
                    fv = [x["frame"] for x in mine if x["frame"] is not None]
                    # stop 原因从相位事件回填（该相位最后一次「结束 stop=…」）
                    stop_reason = None
                    for e in PHASE_EVENTS:
                        if e.get("phase") == ph and str(e.get("msg", "")).startswith("结束 stop="):
                            stop_reason = str(e["msg"]).split("结束 stop=", 1)[1].split()[0]
                    phases[ph] = {
                        "phase": ph, "stop_reason": stop_reason,
                        "duration_s": round(
                            ((mine[-1]["t_mono_ns"] - mine[0]["t_mono_ns"]) / 1e9)
                            if len(mine) >= 2 else 0.0, 3),
                        "n_samples": len(mine),
                        "frame_first": fv[0] if fv else None,
                        "frame_last": fv[-1] if fv else None,
                        "grabs": [g.get("label") for g in grabs
                                  if g.get("phase") == ph],
                        "stop_reason": None,
                    }
                write_json("grabs_index.json",
                           [{k: g.get(k) for k in ("label", "phase", "grab_reason",
                                                   "grab_verdict", "grab_wall_ms",
                                                   "n_frames", "usable",
                                                   "stackwalk_end_reason",
                                                   "prev_count", "resume_ret",
                                                   "clean_restore_no_residual_suspend")}
                            for g in grabs])
                write_json("phase_summary.json", phases)
                write_json("stall_segments.json", segs_all)
                write_json("w_b_c_d_info.json",
                           {"W_B": w_b_info, "W_C": w_c_info, "W_D": w_d_info})
                (W6 / "REPRO.md").write_text(
                    render_repro(meta, phases, segs_by_phase, segs_all, grabs,
                                 samples, a), encoding="utf-8")
                (W6 / "SAFETY.md").write_text(
                    render_safety(meta, grabs, a), encoding="utf-8")
                (W6 / "CONFIG_RESTORE.md").write_text(
                    render_config_restore(prelaunch, residual_before,
                                          residual_after, rows,
                                          (len(inv_before), len(inv_after)),
                                          diff, restore_verify, close_steps),
                    encoding="utf-8")
                (W6 / "RUNLOG.md").write_text(
                    render_runlog(meta, phases, PHASE_EVENTS, exit_code,
                                  started_utc, ended_utc, cmdline), encoding="utf-8")
                (W6 / "UNCOVERED.md").write_text(
                    render_uncovered(meta, phases, segs_all, grabs,
                                     w_b_info, w_c_info, w_d_info),
                    encoding="utf-8")
                (OUT / "stdout.txt").write_text("\n".join(LOG_LINES) + "\n",
                                                encoding="utf-8")
                meta["ended_utc"] = ended_utc
                meta["grabs_n"] = len(grabs)
                write_json("run_meta.json", meta)
                log("[P1] 交付完成（exit_code=%d, samples=%d, grabs=%d）" %
                    (exit_code, len(samples), len(grabs)))
        except Exception as e:                                    # noqa: BLE001
            log("!! 文档生成异常 %r" % e)
            log(traceback.format_exc())
        try:
            if sink is not None:
                sink.close()
        except Exception:
            pass

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
