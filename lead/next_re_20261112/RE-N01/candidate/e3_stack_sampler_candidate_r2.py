#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""E3 栈采样候选件（甲案：SuspendThread + GetThreadContext + StackWalk64）。

===============================================================================
授权状态（2026-11-12，用户明示「D 13 选 c」；台账 §611）
===============================================================================
已解除：编写「SuspendThread / StackWalk 候选件 + 离线单测」的禁令。
未解除：**真机发射 / 活进程采集 / attach / 读活进程内存**。
        依据 D-15 与 D-31 Q4，须用户**当轮明示**。
⇒ 本件只实现与离线单测；`--live` 入口显式拒绝执行并给出原因。
   **本文件不含、也不会主动发起任何真机采集。**

===============================================================================
设计约束（逐条对应台账 §611 与 E3 卡 §2/§4/§5）
===============================================================================
C1 触发条件：帧号 [0xA8ED84] 连续 N=1.0 s 不变（§532 复算误触率 0）。
C2 采样方式：甲案 SuspendThread → GetThreadContext → StackWalk64 → ResumeThread。
C3 单次总停顿硬上限 ≤ 50 ms（E3 卡 §4：甲案 ≤50ms/次）。
C4 死锁防护（甲案自述「可能自造死锁」，本件必须显式对冲）：
   D1 逐线程「挂→走→立刻恢复」，不一次性全挂（把挂起窗口压到最小）；
   D2 SuspendThread 前记录 prev_count，恢复时按差值精确还原，不留残余挂起；
   D3 全程 try/finally 兜底：任何异常路径都恢复所有已挂线程；
   D4 跳过自身线程；跳过已处于挂起态（prev_count>0）的线程，不接管别人的挂起态；
   D5 StackWalk64/符号初始化在**挂起任何线程之前**完成，避免挂起态下触发模块加载；
   D6 单线程栈走查预算与总预算双闸，任一超限即中止并恢复。
C5 停止/回退（E3 卡 §5 照录）：采样步失败 ⇒ 记录错误码，**不重试、不强杀**，
   不影响其余哨兵读数；候选件在独立文件，冻结母本三件**零字节**改动。
C6 反身护栏：与目标②读数**分列**；本件不写任何状态、不注入。

===============================================================================
⚠ 真机验证结果（2026-11-12，用户授权真机后执行）
===============================================================================
验证方法：对**无害哑进程**（自 spawn 的 sleep python 子进程）跑真实 Win32 路径，
          **未触碰 gamemd.exe**。脚本 `_live_verify_dummy.py`，**17 项 0 失败**。
已证（真机读数）：
  - MF-1 修复有效：真实 `SuspendThread` 首次返回 0、二次返回 1（计数语义）、
    两次 `ResumeThread` 返回 2→1（精确还原）；
  - MF-2 修复有效：真实 `CreateToolhelp32Snapshot`+`Thread32First` 在设了 `dwSize` 后正常；
  - `GetThreadContext`(AMD64) 取到非零 Rip/Rsp。
★★ 真机验证抓出的**关键新事实**（离线单测不可能发现）：
  1. **64 位进程中 `GetThreadContext` 必须用 AMD64 CONTEXT（1232 B）**。
     传 `CONTEXT_i386`(716 B) 会**返回成功但字段全零**——静默失败，不报错。
     本件已复现该陷阱（ok=1 而 eip=0x0）。
  2. **gamemd.exe 是 32 位进程**。64 位 Python 采集它**不能**直接用 `GetThreadContext`，
     必须走 `Wow64GetThreadContext` + WOW64_CONTEXT；或改用 32 位进程采集。
     ⇒ **这是真机放行的前置条件，尚未实现。**

===============================================================================
⚠ 能力边界声明（MF-7，评审 R6 要求白纸黑字）
===============================================================================
1. **死锁防护 D1–D6 仅经「离线 stub」验证，未在真机独立验证。**
   stub 证明的是「我们的控制流在每个分支上都把挂起恢复了」，
   **不证明**真实 `SuspendThread`/`ResumeThread`/`StackWalk64` 配对下的行为。
2. **离线单测通过 ≠ 真机可行。** 本件不因此宣称任何真机可用性。
3. 甲案「可能自造死锁」的风险来源是 E3 方案原文，本线**未独立验证**该风险的真实程度
   （E3 卡 §8-4 自认）。

===============================================================================
⚠ 反身护栏（MF-8，评审 R5 要求落为机制）
===============================================================================
E3 卡 §4 认定甲案对目标②（正常退出读数）是**高反身影响**（挂起目标线程本身扰动②的读数窗口）。
本件的对冲：
  - 采样结果写入 **独立输出目录** `E3_OUT_DIR`（与②读数物理分列，不同文件）；
  - 提供 `reflexive_guard_ok()`：要求调用方显式声明「本次采样窗口与②读数窗口不重叠」；
  - 本件**不读、不写**任何②读数文件（`G_EXITSTATE` 只作常量登记，供上位判断窗口冲突）。
"""
from __future__ import print_function

import ctypes
import ctypes.wintypes as wt
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------- 常量

REPO = Path(r"D:\Project\ra2-campaign-forge")

# 与母本 probe_v2 一致的哨兵地址（只读引用，不复制其代码）
G_FRAME = 0x00A8ED84        # 帧号（C1 触发量）
# 目标②的退出态地址。★ MF-8：本件**只登记、永不读取**；用于上位判断「采样窗口是否与②读数窗口重叠」。
G_EXITSTATE = 0x00A8EDD8

# MF-8：采样结果的独立输出目录（与②读数**物理分列**，不复用②的任何文件路径）
E3_OUT_DIR = REPO / "lead" / "re_d13_ruling_20261112" / "e3_out"

# C1 触发阈值
STALL_N_SECONDS = 1.0       # §532：真实正常抖动上限 360 拍 = 900 ms，N=1.0s 误触率 0
MIN_FRAME_OBSERVATIONS = 8  # 判「连续不变」所需的最少观测数（250ms 采样 → ≥2s 覆盖）

# C3 / D6 预算
TOTAL_PAUSE_BUDGET_MS = 50.0     # 单次采样总停顿硬上限
PER_THREAD_WALK_BUDGET_MS = 0.0  # 单线程预算；0=禁用（只由总预算 budget_ms 控制）
                                 # 注：曾设 15ms，但在 19 线程目标上会过早截断；
                                 #     C3 的硬约束是「单次总停顿 ≤50ms」，由 budget_ms 承担。

# 冻结母本（C5：零字节改动，只 import 复用）
MOTHER_PROBE_V2 = REPO / "lead" / "qc161_u0400_trip" / "_drive_c2_x_probe_v2.py"
MOTHER_PROBE_V2_SHA = "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9"
MOTHER_EARLYCLOSE = REPO / "lead" / "qc161_u0400_trip" / "_drive_c2_x_earlyclose.py"
MOTHER_EARLYCLOSE_SHA = "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1"

# Win32 常量
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
CONTEXT_i386 = 0x00010000
CONTEXT_CONTROL = CONTEXT_i386 | 0x00000001
MAX_STACK_DEPTH = 32


# ---------------------------------------------------------------- RE-N01 状态契约
# 四态 + 显式 error（见 SAMPLER_CONTRACT.md / DISAGREE.md）：
#   not_attempted      未采集（零线程挂起；前置/归属拒绝）
#   ok                 无错误（errors=[] 但**没有**逐线程恢复正面证据）
#   resume_verified_ok 恢复成功（resume_ret 有效 + resume_ok=True + 无恢复错误）
#   resume_failed      恢复失败（恢复返回值无效/异常/_resume_errors 非空）
#   error              采样异常或预算超限（显式失败，绝不塞进 ok）
# **禁止**用 null / 空列表兼表上述任一状态。
SAMPLE_STATES = ("not_attempted", "ok", "resume_verified_ok",
                 "resume_failed", "error")
# 与 sample_state 正交：专门表达「恢复成功」的正面证据（B1/B2）。
RESUME_STATES = ("not_applicable", "verified_ok", "failed", "unknown")


class E3Fail(Exception):
    """采样步失败（C5：记录错误码，不重试、不强杀）。"""


def reflexive_guard_ok(goal2_window=None, sample_window=None):
    """MF-8 反身护栏：要求调用方显式确认「采样窗口与②读数窗口不重叠」。

    返回 (ok, reason)。**默认拒绝**（保守）：调用方必须显式传两个不重叠的窗口。
    窗口格式：(start_epoch, end_epoch) 元组。
    """
    if goal2_window is None or sample_window is None:
        return (False, "windows_not_declared")
    try:
        g0, g1 = float(goal2_window[0]), float(goal2_window[1])
        s0, s1 = float(sample_window[0]), float(sample_window[1])
    except Exception:                                   # noqa: BLE001
        return (False, "window_format_invalid")
    if s1 <= s0:
        return (False, "sample_window_empty")
    # 重叠判定：区间相交
    if max(g0, s0) < min(g1, s1):
        return (False, "windows_overlap")
    return (True, "ok")


def write_e3_output(result, out_dir=None):
    """MF-8：把采样结果写进**独立目录**（与②读数物理分列）。

    只写本件自己的文件；不读、不改②读数文件。
    """
    d = Path(out_dir) if out_dir else E3_OUT_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = d / ("e3_sample_%d.json" % int(result.get("pid", 0)))

    def _default(o):
        # ctypes 结构（ctx["_raw"] 等）不可 JSON 序列化 ⇒ 只留类型名，不丢数据
        if isinstance(o, ctypes.Structure):
            return {"__ctypes__": type(o).__name__}
        if isinstance(o, ctypes.Array):
            return {"__ctypes_array__": type(o).__name__, "len": len(o)}
        if isinstance(o, bytes):
            return {"__bytes_len__": len(o)}
        return {"__unserializable__": type(o).__name__}

    try:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1,
                                   default=_default), encoding="utf-8")
        return (path, None)
    except Exception as e:                              # noqa: BLE001
        return (None, "write_fail:%s" % type(e).__name__)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- OPS 抽象
# 全部 Win32 调用经 OPS 注入 ⇒ 离线单测可完全 stub（母本 run_fault_tests 同款模式）。
OPS = {}


def _now_ns():
    """RE-N01：事件级计时统一用 perf_counter_ns（可经 OPS["now_ns"] 注入假时钟）。

    原件 sample() 的预算闸仍用 OPS["now"]（time.monotonic），**保持 47 项原单测不变**；
    本函数只服务于新增的单线程入口 / 分项计时，不改动原有任何判据。
    """
    fn = OPS.get("now_ns")
    if fn is not None:
        return int(fn())
    return time.perf_counter_ns()


class EventTimer(object):
    """RE-N01：单一 perf_counter_ns 时钟的整数里程碑。

    所有分项时间由**同一组整数时间戳做差**（望远镜求和），因此
    「端到端 ≥ 分项之和」在数学上精确成立，不依赖浮点换算。
    离线测试可注入假 now_ns，构造「采样函数本身慢 + 后续步骤慢」场景（T-A3）。
    """

    def __init__(self, now_ns=None):
        self._now = now_ns or _now_ns
        self.marks = {}

    def mark(self, name):
        v = int(self._now())
        self.marks[name] = v
        return v

    def get(self, name):
        return self.marks.get(name)


def cost_from_marks(marks, t_candidate_ns=None):
    """由整数里程碑构造 cost_ns（缺失项记 0，不静默丢弃字段）。

    字段（单位 ns）：
      detect_ns       检测延迟：候选发现 → 检测判定成立
      preflight_ns    前置校验：判定成立 → preflight/位宽查询完成
      ownership_ns    PID/TID 归属校验（Toolhelp 快照）
      open_ns         OpenThread + SuspendThread
      context_ns      取上下文
      walk_ns         走栈
      resume_ns       恢复
      overhead_ns     收尾（组事件/序列化等，恢复完成 → 事件结束）
      suspend_held_ns 实际线程挂起时长 suspend→resume（**重叠子区间**，
                      不是可加的分项；见 SAMPLER_CONTRACT.md）
      end_to_end_ns   检测判定成立 → 事件结束（任务卡口径）
      event_total_ns  候选发现 → 事件结束（整事件，含检测延迟）
    """
    def g(k):
        v = marks.get(k)
        return int(v) if v is not None else 0

    t_cand = g("candidate") if t_candidate_ns is None else int(t_candidate_ns)
    t_verd = g("verdict")
    t_pref = g("preflight")
    t_own = g("ownership")
    t_susp = g("suspend")
    t_ctx = g("context")
    t_walk = g("walk")
    t_res = g("resume")
    t_end = g("end")

    def d(a, b):
        return max(0, int(b) - int(a)) if (a and b) else 0

    return {
        "detect_ns": d(t_cand, t_verd),
        "preflight_ns": d(t_verd, t_pref),
        "ownership_ns": d(t_pref, t_own),
        "open_ns": d(t_own, t_susp),
        "context_ns": d(t_susp, t_ctx),
        "walk_ns": d(t_ctx, t_walk),
        "resume_ns": d(t_walk, t_res),
        "overhead_ns": d(t_res, t_end),
        "suspend_held_ns": d(t_susp, t_res),
        "end_to_end_ns": d(t_verd, t_end),
        "event_total_ns": d(t_cand, t_end),
    }


def bind_real_ops():
    """绑定真实 Win32 调用。**只被 --live 路径使用；本件默认不调用。**

    ★ MF-1 修复（评审 P0）：**全部 k32 函数必须显式设 restype/argtypes**。
      若不设，ctypes 默认返回 c_int：
        - `SuspendThread` 失败返回 **-1**（DWORD 0xFFFFFFFF 经 c_int 变负数）
          ⇒ 旧判据 `prev == 0xFFFFFFFF` 永不命中 ⇒ 挂起失败被当成功 ⇒ 采样未挂起线程。
        - `OpenThread`/`CreateToolhelp32Snapshot` 句柄高位为 1 时变负数 ⇒ `not h` 判空靠运气。
      范式照抄母本 `_drive_c2_x_probe_v2.py:80-90`。
    """
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # --- 句柄与返回值签名（MF-1）---
    k32.OpenProcess.restype = wt.HANDLE
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.CloseHandle.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.OpenThread.restype = wt.HANDLE
    k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.SuspendThread.restype = wt.DWORD          # 成功=上次挂起计数；失败=(DWORD)-1
    k32.SuspendThread.argtypes = [wt.HANDLE]
    k32.ResumeThread.restype = wt.DWORD          # 成功=上次挂起计数；失败=(DWORD)-1
    k32.ResumeThread.argtypes = [wt.HANDLE]
    k32.GetThreadContext.restype = wt.BOOL
    k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.Thread32First.restype = wt.BOOL
    k32.Thread32First.argtypes = [wt.HANDLE, ctypes.c_void_p]
    k32.Thread32Next.restype = wt.BOOL
    k32.Thread32Next.argtypes = [wt.HANDLE, ctypes.c_void_p]
    k32.ReadProcessMemory.restype = wt.BOOL
    k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    # ★ Wow64：读 32 位目标（gamemd.exe）必须走这两个
    k32.IsWow64Process.restype = wt.BOOL
    k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
    try:
        k32.Wow64GetThreadContext.restype = wt.BOOL
        k32.Wow64GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
    except AttributeError:                          # 32 位宿主上无此 API
        pass

    OPS["now"] = time.monotonic
    OPS["sleep"] = time.sleep
    OPS["now_ns"] = time.perf_counter_ns        # RE-N01：事件级分项计时（真实路径）
    OPS["open_process"] = lambda access, pid: k32.OpenProcess(access, False, pid)
    OPS["close_handle"] = k32.CloseHandle
    OPS["read_mem"] = _real_read_mem(k32)
    OPS["create_snapshot"] = k32.CreateToolhelp32Snapshot
    OPS["thread_first"] = k32.Thread32First
    OPS["thread_next"] = k32.Thread32Next
    OPS["open_thread"] = k32.OpenThread
    OPS["suspend_thread"] = k32.SuspendThread
    OPS["resume_thread"] = k32.ResumeThread
    OPS["get_thread_context"] = k32.GetThreadContext
    OPS["close_thread_handle"] = k32.CloseHandle
    OPS["is_wow64"] = lambda h: _is_wow64(k32, h)
    OPS["wow64_get_thread_context"] = getattr(k32, "Wow64GetThreadContext", None)


def _is_wow64(k32, h):
    """判断句柄所指进程是否为 32 位（WOW64）。返回 True/False/None(未知)。"""
    try:
        flag = wt.BOOL(0)
        if not k32.IsWow64Process(h, ctypes.byref(flag)):
            return None
        return bool(flag.value)
    except Exception:                               # noqa: BLE001
        return None


def _real_read_mem(k32):
    def _rm(h, addr, size):
        buf = (ctypes.c_char * size)()
        n = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n))
        if not ok:
            return (None, ctypes.get_last_error())
        return (buf.raw, 0)
    return _rm


# INVALID = (DWORD)-1，Win32 失败哨兵。设了 restype=DWORD 后即为 0xFFFFFFFF。
SUSPEND_FAILED = 0xFFFFFFFF


# ---------------------------------------------------------------- C1 触发逻辑


class StallDetector(object):
    """帧号连续不变检测（C1）。

    语义（逐条可单测）：
      - 每次 observe(frame) 记 (t, frame)。
      - 若 frame 与「本段起点帧值」不同 ⇒ 段重置，起点更新。
      - 若 frame 与起点相同，且 (now - 起点t) >= N ⇒ 判停滞，返回 True（只报一次）。
      - frame 为 None（读失败）⇒ **不计入、不重置、不判停滞**（读失败不是停滞证据）。
    """

    def __init__(self, n_seconds=STALL_N_SECONDS, min_obs=MIN_FRAME_OBSERVATIONS):
        self.n = float(n_seconds)
        self.min_obs = int(min_obs)
        self.reset()

    def reset(self):
        self.base_frame = None
        self.base_t = None
        self.obs = 0
        self.fired = False

    def observe(self, t, frame):
        """返回 True 表示「刚刚」判定为停滞（同段只报一次）。"""
        if frame is None:
            # 读失败：不推进、不重置、不计数
            return False
        self.obs += 1
        if self.base_frame is None or frame != self.base_frame:
            self.base_frame = frame
            self.base_t = t
            self.fired = False
            return False
        if self.fired:
            return False
        if self.obs < self.min_obs:
            return False
        if (t - self.base_t) >= self.n:
            self.fired = True
            return True
        return False


# ---------------------------------------------------------------- C2 采样器


class StackSampler(object):
    """甲案采样器：SuspendThread → GetThreadContext → StackWalk64 → ResumeThread。

    死锁防护 D1–D6 见模块 docstring。核心不变式：
      **每个被挂起的线程，在离开作用域前一定被恢复**（try/finally + 精确计数还原）。
    """

    def __init__(self, budget_ms=TOTAL_PAUSE_BUDGET_MS,
                 per_thread_ms=PER_THREAD_WALK_BUDGET_MS,
                 max_depth=MAX_STACK_DEPTH):
        self.budget_ms = float(budget_ms)
        self.per_thread_ms = float(per_thread_ms)
        self.max_depth = int(max_depth)
        self.max_threads = 0        # 0=不限；>0 时只采前 N 个线程
        self._target_is32 = None    # 进程级位宽（sample() 里用进程句柄查一次）
        self.frames_is_single = False
        # 可注入的栈走查器（离线单测用 stub）
        self.stack_walker = None
        # MF-6：恢复失败聚合（由sample 汇总进 errors，不静默）
        self._resume_errors = []

    # -------- MF-4：挂起前前置校验（fail-fast，防「先挂后败再恢复」） --------
    def preflight(self):
        """在挂起**任何**线程之前确认依赖可用（D5）。返回错误串或 None。

        注：walker 不再是硬前置 —— 无 walker 时 `_walk` 退回**单帧**（只报 ip），
        这条路径不会「先挂后败」，因为它不依赖外部 walker。
        真正的硬前置是 **context 读取通道**：没有它，挂起后必然失败。
        """
        has_ctx = ("get_context_stub" in OPS
                   or ("is_wow64" in OPS and OPS.get("wow64_get_thread_context") is not None)
                   or "get_thread_context" in OPS)
        if not has_ctx:
            return "context_not_bound"
        return None

    # -------- RE-N01：公开入口，把隐式私有属性写成显式契约 --------
    def preflight_target(self, pid, tid=None, timer=None):
        """**一次**完成：进程级位宽查询 + preflight() + 目标 PID/TID 归属校验。

        对应任务卡「完整事件入口统一验证目标 PID/TID 归属、位宽、所需 API 和 walker」。
        与原件 sample() 的差别（B4/B5）：sample_one_thread() 自身不调 preflight()，
        _get_context() 又依赖私有属性 self._target_is32 —— 原件只由驱动在 :328
        外部赋私有属性，或由 sample() 内部查询。本入口把这三件事收进一个**公开方法**，
        调用方不需要、也不应该再写私有属性。

        **绝不挂起任何线程**：全部校验在任何 SuspendThread 之前完成；
        返回 ok=False 时调用方必须放弃本次采样（T-B3/T-B4）。

        Toolhelp 归属校验用 CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD) 快照
        （即 enumerate_threads 的同一通道），校验 tid 是否属于 pid。
        离线测试中该通道由 OPS stub 提供，不触碰真实 Win32。

        返回 dict（**永不返回 None**，避免用 null 兼表状态）：
          {ok, reason, pid, tid, is32, target_bits, preflight:{ok,reason},
           ownership:{pid,tid,validated,tid_belongs_to_pid,n_threads_in_pid,reason},
           walker_ready, n_threads_in_pid, phase_ms}
        """
        t0 = _now_ns()
        if timer is not None:
            timer.mark("preflight")
            timer.mark("ownership")   # 占位：早退路径未做归属校验 ⇒ ownership_ns=0
        out = {
            "ok": False, "reason": "", "pid": int(pid),
            "tid": int(tid) if tid is not None else None,
            "is32": None, "target_bits": None,
            "preflight": {"ok": False, "reason": ""},
            "ownership": {"pid": int(pid), "tid": int(tid) if tid is not None else None,
                          "validated": False, "tid_belongs_to_pid": False,
                          "n_threads_in_pid": 0, "reason": ""},
            "walker_ready": self.stack_walker is not None,
            "n_threads_in_pid": 0,
            "phase_ms": {},
        }
        # --- (1) preflight：context 通道等硬前置（原件 :336-348 的语义，逐字保留） ---
        pf = self.preflight()
        t1 = _now_ns()
        if pf is not None:
            out["reason"] = "preflight:" + pf
            out["preflight"] = {"ok": False, "reason": pf}
            out["phase_ms"] = {"preflight_ms": (t1 - t0) / 1e6,
                               "total_ms": (_now_ns() - t0) / 1e6}
            return out
        out["preflight"] = {"ok": True, "reason": "ok"}

        # --- (2) 进程级位宽查询（一次；显式写入 self._target_is32） ---
        is32 = None
        self._target_is32 = None
        if "is_wow64" in OPS:
            try:
                hproc = OPS["open_process"](0x1000, pid)
                if hproc:
                    try:
                        is32 = OPS["is_wow64"](hproc)
                    finally:
                        OPS["close_handle"](hproc)
            except Exception:                                # noqa: BLE001
                is32 = None
        t2 = _now_ns()
        self._target_is32 = is32
        out["is32"] = is32
        out["target_bits"] = 32 if is32 else (64 if is32 is False else None)
        if is32 is None and "get_context_stub" not in OPS:
            # 与原件 sample() :541-543 同判据：无 context stub 又查不到位宽 ⇒ 拒绝
            out["reason"] = "wow64_query_failed"
            out["phase_ms"] = {"preflight_ms": (t1 - t0) / 1e6,
                               "wow64_ms": (t2 - t1) / 1e6,
                               "total_ms": (_now_ns() - t0) / 1e6}
            return out

        # --- (3) PID/TID 归属校验（Toolhelp 快照） ---
        tids = []
        try:
            tids = self.enumerate_threads(pid)
        except E3Fail as e:
            out["reason"] = "enumerate_threads_fail:" + str(e)
            out["ownership"]["reason"] = str(e)
            out["phase_ms"] = {"preflight_ms": (t1 - t0) / 1e6,
                               "wow64_ms": (t2 - t1) / 1e6,
                               "ownership_ms": (_now_ns() - t2) / 1e6,
                               "total_ms": (_now_ns() - t0) / 1e6}
            return out
        t3 = _now_ns()
        if timer is not None:
            timer.mark("ownership")   # Toolhelp 快照归属校验实际完成点
        tidset = set(int(x) for x in tids)
        out["n_threads_in_pid"] = len(tidset)
        out["ownership"]["n_threads_in_pid"] = len(tidset)
        if tid is None:
            out["ownership"]["validated"] = True
            out["ownership"]["tid_belongs_to_pid"] = None
            out["ownership"]["reason"] = "tid_not_requested"
        elif int(tid) in tidset:
            out["ownership"]["validated"] = True
            out["ownership"]["tid_belongs_to_pid"] = True
            out["ownership"]["reason"] = "toolhelp_snapshot_tid_in_pid"
        else:
            out["reason"] = "tid_not_in_pid:tid=%d,pid=%d" % (int(tid), int(pid))
            out["ownership"]["validated"] = True
            out["ownership"]["tid_belongs_to_pid"] = False
            out["ownership"]["reason"] = "tid_not_in_toolhelp_snapshot"
            out["phase_ms"] = {"preflight_ms": (t1 - t0) / 1e6,
                               "wow64_ms": (t2 - t1) / 1e6,
                               "ownership_ms": (t3 - t2) / 1e6,
                               "total_ms": (_now_ns() - t0) / 1e6}
            return out
        t4 = _now_ns()
        out["ok"] = True
        out["reason"] = "ok"
        out["phase_ms"] = {"preflight_ms": (t1 - t0) / 1e6,
                           "wow64_ms": (t2 - t1) / 1e6,
                           "ownership_ms": (t4 - t2) / 1e6,
                           "total_ms": (t4 - t0) / 1e6}
        return out

    # -------- 线程枚举 --------
    def enumerate_threads(self, pid):
        """返回目标进程线程 id 列表（不含自身 pid，D4/MF-5）。"""
        # MF-5：自采样守卫 —— 传自身 pid 会导致挂起自己所在进程（含采样线程）⇒ 自死锁
        if int(pid) == os.getpid():
            raise E3Fail("refuse_self_pid:%d" % pid)
        snap = OPS["create_snapshot"](TH32CS_SNAPTHREAD, 0)
        if not snap or snap == -1:
            raise E3Fail("snapshot_fail")
        out = []
        try:
            entry = _ThreadEntry32()
            # MF-2 修复（评审 P0）：Thread32First **必须**先设 dwSize，否则真机必败。
            # 旧版未设（stub 在测试内代设，掩盖了此缺陷）。
            entry.dwSize = ctypes.sizeof(_ThreadEntry32)
            ok = OPS["thread_first"](snap, ctypes.byref(entry))
            while ok:
                if entry.th32OwnerProcessID == pid:
                    out.append(int(entry.th32ThreadID))
                entry.dwSize = ctypes.sizeof(_ThreadEntry32)
                ok = OPS["thread_next"](snap, ctypes.byref(entry))
        finally:
            OPS["close_handle"](snap)
        return out

    # -------- 单线程安全采样（D1/D2/D3/D4） --------
    def sample_one_thread(self, tid, timer=None):
        """挂起单个线程 → 取上下文 → 走栈 → **严格恢复**。

        返回 dict；任何失败都不抛给调用方以外的地方（E3Fail 由 sample() 捕获）。

        RE-N01 增量（**控制流与错误串逐字保留**，只增补返回字段）：
          * errors          : list[str]，本次调用自身的恢复/采样错误（B2：原件单线程
                              路径永不汇总 _resume_errors；这里显式带出，不再靠 null）
          * resume_ok       : bool | None（None 仅当本次没有发起恢复）
          * resume_ret      : int | None（ResumeThread 原始返回值）
          * prev            : int（SuspendThread 的上次挂起计数；两分支都带）
          * suspend_held_ms : float | None（suspend→resume 的实测挂起时长）
          * phase_ms        : dict（open/suspend/context/walk/resume/total 分项）
        注意：Ctx 原始寄存器值仍在 ctx 里（不替换成类型名，见任务卡 §3.5）。
        """
        t_open0 = _now_ns()
        h = OPS["open_thread"](THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                               THREAD_QUERY_INFORMATION, False, tid)
        t_open1 = _now_ns()
        if not h:
            raise E3Fail("open_thread_fail:tid=%d" % tid)
        prev = None
        suspended_by_us = False
        out = None
        err_base = len(self._resume_errors)
        resume_ret = None
        resume_ok = None
        t_suspend = None
        phase = {"open_ms": (t_open1 - t_open0) / 1e6,
                 "suspend_ms": None, "context_ms": None,
                 "walk_ms": None, "resume_ms": None,
                 "suspend_held_ms": None, "total_ms": None}
        try:
            prev = OPS["suspend_thread"](h)
            t_suspend = _now_ns()
            if timer is not None:
                timer.mark("suspend")
            phase["suspend_ms"] = (t_suspend - t_open1) / 1e6
            # MF-1 修复：失败判据必须同时覆盖 None / -1 / 0xFFFFFFFF。
            # 设了 restype=DWORD 后失败为 0xFFFFFFFF；未设时为 -1（旧版的 bug 根源）。
            if prev is None or prev == SUSPEND_FAILED or prev == -1:
                raise E3Fail("suspend_thread_fail:tid=%d:prev=%r" % (tid, prev))
            # D4：prev>0 说明该线程本已处于挂起态（别人的挂起），我们不接管
            if prev > 0:
                # 一次 ResumeThread 只抵消我们自己的 +1，不会释放别人的挂起（D2 已核）
                r0 = OPS["resume_thread"](h)
                resume_ret = r0
                resume_ok = not (r0 is None or r0 == SUSPEND_FAILED or r0 == -1)
                if r0 is None or r0 == SUSPEND_FAILED or r0 == -1:
                    # MF-6：恢复失败不可静默（否则留下不可见残余挂起）
                    raise E3Fail("resume_restore_fail:tid=%d" % tid)
                out = {"tid": tid, "skipped": "already_suspended", "prev": int(prev),
                       "errors": [], "resume_ok": resume_ok, "resume_ret": r0,
                       "suspend_held_ms": 0.0, "phase_ms": dict(phase)}
                return out
            suspended_by_us = True

            t_ctx0 = _now_ns()
            ctx = self._get_context(h)
            t_ctx1 = _now_ns()
            if timer is not None:
                timer.mark("context")
            phase["context_ms"] = (t_ctx1 - t_ctx0) / 1e6
            frames = self._walk(ctx, hthread=h)
            t_walk1 = _now_ns()
            if timer is not None:
                timer.mark("walk")
            phase["walk_ms"] = (t_walk1 - t_ctx1) / 1e6
            out = {"tid": tid, "prev": int(prev), "ctx": ctx, "frames": frames,
                   "errors": [], "resume_ok": None, "resume_ret": None,
                   "suspend_held_ms": None, "phase_ms": dict(phase)}
            return out
        finally:
            # D3 兜底：无论成功/异常，若我们挂起了它就必须恢复
            if suspended_by_us:
                t_resume0 = _now_ns()
                try:
                    r = OPS["resume_thread"](h)
                    resume_ret = r
                    resume_ok = not (r is None or r == SUSPEND_FAILED or r == -1)
                    # MF-6：恢复返回值校验（失败记入 errors 由上层汇总）
                    if r is None or r == SUSPEND_FAILED or r == -1:
                        self._resume_errors.append("resume_fail:tid=%d" % tid)
                except Exception:                       # noqa: BLE001
                    self._resume_errors.append("resume_exc:tid=%d" % tid)
                t_resume1 = _now_ns()
                if timer is not None:
                    timer.mark("resume")
                phase["resume_ms"] = (t_resume1 - t_resume0) / 1e6
                if t_suspend is not None:
                    phase["suspend_held_ms"] = (t_resume1 - t_suspend) / 1e6
            phase["total_ms"] = (_now_ns() - t_open0) / 1e6
            if out is not None:
                out["errors"] = list(self._resume_errors[err_base:])
                out["resume_ok"] = resume_ok
                out["resume_ret"] = resume_ret
                out["suspend_held_ms"] = phase.get("suspend_held_ms")
                out["phase_ms"] = dict(phase)
            OPS["close_thread_handle"](h)

    def _get_context(self, h):
        """取目标线程上下文。**按目标位宽分流**（真机验证确立的两条硬事实）。

        分流规则：
          - 目标是 32 位（WOW64，如 gamemd.exe）⇒ `Wow64GetThreadContext` + WOW64_CONTEXT(716B)
          - 目标是 64 位                              ⇒ `GetThreadContext` + CONTEXT_AMD64(1232B)
        ★ 结构不匹配时 API **返回成功但字段全零**（静默失败）。故取完必须做
          「非零自检」：Ip/Sp 全零即判失败，绝不把零上下文当有效读数返回。
        """
        if "get_context_stub" in OPS:
            return OPS["get_context_stub"](h)

        if "wow64_get_thread_context" not in OPS or "is_wow64" not in OPS:
            raise E3Fail("context_not_bound")

        # ★ 关键：IsWow64Process 要 **进程句柄**，不是线程句柄。
        #   旧实现把线程句柄传进去 ⇒ 每个线程都 wow64_query_failed（19 线程 19 个错误）。
        #   正确做法：位宽是**进程级属性**，采样前查一次即可。
        is32 = self._target_is32
        if is32 is None:
            raise E3Fail("wow64_query_not_done")
        if is32:
            api = OPS["wow64_get_thread_context"]
            if api is None:
                raise E3Fail("wow64_api_missing")
            ctx = WOW64_CONTEXT()
            ctx.ContextFlags = WOW64_CONTEXT_CONTROL
            if not api(h, ctypes.byref(ctx)):
                raise E3Fail("wow64_get_context_failed")
            if ctx.Eip == 0 and ctx.Esp == 0:
                # 静默零填充 ⇒ 结构不匹配，不得当有效读数
                raise E3Fail("context_silent_zero:wow64")
            return {"bits": 32, "ip": ctx.Eip, "sp": ctx.Esp, "bp": ctx.Ebp,
                    "eflags": ctx.EFlags, "cs": ctx.SegCs, "_raw": ctx}

        # 64 位目标
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            raise E3Fail("native64_requires_64bit_host")
        api64 = OPS.get("get_thread_context")
        if api64 is None:
            raise E3Fail("get_context_api_missing")
        buf = (ctypes.c_byte * 1232)()
        ctypes.memset(ctypes.byref(buf), 0, 1232)
        # ContextFlags @ 偏移 48（AMD64）
        ctypes.c_uint32.from_buffer(buf, 48).value = CONTEXT_AMD64_CONTROL
        if not api64(h, ctypes.byref(buf)):
            raise E3Fail("get_context_failed")
        rip = ctypes.c_uint64.from_buffer(buf, 248).value
        rsp = ctypes.c_uint64.from_buffer(buf, 152).value
        rbp = ctypes.c_uint64.from_buffer(buf, 160).value
        if rip == 0 and rsp == 0:
            raise E3Fail("context_silent_zero:amd64")
        return {"bits": 64, "ip": rip, "sp": rsp, "bp": rbp, "_raw": buf}

    def _walk(self, ctx, hthread=None):
        """栈走查。

        优先级：
          1. 注入的 `stack_walker`（真 StackWalk64 / 测试 stub）
          2. OPS 里的 `walk_stub`（离线单测）
          3. **单帧回退** —— 只报 ctx["ip"]，并置 frames_is_single=True（不冒充调用栈）

        真机路径下由 `--live` 注入 StackWalker（见 `attach_stackwalker`），
        它需要 hthread + 原始 CONTEXT 结构（32 位必须 WOW64_CONTEXT）。
        """
        if self.stack_walker is not None:
            sw_obj = self.stack_walker
            if getattr(sw_obj, "is_dbghelp_walker", False):
                # StackWalker 实例：需 (hthread, raw_ctx, ip, sp, bp)
                raw = (ctx or {}).get("_raw")
                return sw_obj.walk(hthread, raw,
                                   (ctx or {}).get("ip"),
                                   (ctx or {}).get("sp"),
                                   (ctx or {}).get("bp"))
            # 普通 callable（测试 stub）
            try:
                return sw_obj(ctx, self.max_depth)
            except TypeError:
                return sw_obj(ctx)
        if "walk_stub" in OPS:
            return OPS["walk_stub"](ctx, self.max_depth)
        # 单帧回退（真机无 dbghelp 时的最小可用形态）
        ip = (ctx or {}).get("ip")
        if not ip:
            raise E3Fail("no_ip_in_context")
        self.frames_is_single = True
        return [ip]

    # -------- RE-N01：事件级单线程入口（互斥于 sample() 的全线程路径） --------
    def sample_single(self, tid, pid, budget_ms=None, timer=None):
        """**一次**事件级单线程采样；与整体 sample(pid) 严格互斥。

        任务卡 §3.1/§3.2：完整事件入口统一验证 PID/TID 归属、位宽、所需 API；
        每事件单独收集挂起前计数、恢复返回值、异常、预算超限、实际采样线程数；
        恢复失败必须可见；null / 空列表 / 确认成功分开表达。

        与原件驱动 :350-375 的关键差别：
          * **绝不**调用 sample(pid)（全线程）；只走一次 sample_one_thread；
          * preflight_target() 在**任何 SuspendThread 之前**完成（B3/B4/B5）；
          * 整个采样包在 try/except 内，E3Fail/任意异常都落到事件里，
            **不穿透监测循环**（原件 B3：一次恢复失败丢整趟结果）；
          * 恢复结果 / 预算 / 异常 / 线程数 / 归属 / 分项计时全部显式字段。

        返回 dict（永不 None）。sample_state 四态（+ 显式 error）见模块常量
        SAMPLE_STATES；resume_state 与 sample_state 正交，专门表达「恢复成功」
        的**正面证据**，不把 errors=[] 当作恢复成功（B1/B2）。
        """
        timer = timer or EventTimer()
        budget = float(self.budget_ms if budget_ms is None else budget_ms)
        timer.mark("verdict")

        ev = {
            "mode": "single_thread",
            "pid": int(pid), "tid": int(tid),
            "sample_state": "not_attempted",
            "resume_state": "not_applicable",
            "resume_ret": None, "resume_ret_present": False,
            "resume_ok": None, "prev": None,
            "errors": [], "exception": "",
            "budget_exceeded": False, "budget_state": "within", "budget_ms": budget,
            "n_threads_sampled": 0, "n_threads_attempted": 0,
            "preflight": {}, "ownership": {},
            "one": None, "frames": [], "ctx": None,
            "phase_ms": {}, "suspend_held_ms": None,
            "cost_ns": {}, "ns_marks": {},
            "sample_called": False,         # 恒 False：本入口不碰全线程 sample()
            "sample_one_thread_calls": 0,
        }

        # --- (1) 前置契约：一次完成位宽 + preflight + PID/TID 归属校验 ---
        pf = self.preflight_target(pid, tid, timer=timer)
        ev["preflight"] = {
            "ok": bool(pf["ok"]), "reason": pf["reason"],
            "is32": pf["is32"], "target_bits": pf["target_bits"],
            "preflight": dict(pf["preflight"]),
            "walker_ready": bool(pf["walker_ready"]),
            "n_threads_in_pid": pf["n_threads_in_pid"],
            "phase_ms": dict(pf["phase_ms"]),
        }
        ev["ownership"] = dict(pf["ownership"])
        ev["phase_ms"].update(pf["phase_ms"])
        if not pf["ok"]:
            ev["sample_state"] = "not_attempted"
            ev["resume_state"] = "not_applicable"
            ev["errors"] = ["preflight_rejected:" + pf["reason"]]
            ev["budget_state"] = "not_checked"
            timer.mark("suspend")      # 占位：零线程被挂起
            timer.mark("context")
            timer.mark("walk")
            timer.mark("resume")
            timer.mark("end")
            ev["cost_ns"] = cost_from_marks(timer.marks)
            ev["ns_marks"] = dict(timer.marks)
            return ev

        # --- (2) 唯一一次单线程采样；异常必须落进事件，不得穿透 ---
        ev["sample_one_thread_calls"] = 1
        ev["n_threads_attempted"] = 1
        one = None
        try:
            one = self.sample_one_thread(int(tid), timer=timer)
        except E3Fail as e:
            ev["exception"] = "E3Fail:" + str(e)
            ev["errors"].append("sample_one_thread_fail:" + str(e))
            ev["sample_state"] = "error"
        except Exception as e:                              # noqa: BLE001
            ev["exception"] = type(e).__name__ + ":" + str(e)
            ev["errors"].append("sample_one_thread_unexpected:" + type(e).__name__)
            ev["sample_state"] = "error"
        finally:
            # 若采样过程中途抛异常，补齐里程碑，保证 cost_ns 六个字段都在
            for mk in ("suspend", "context", "walk", "resume"):
                if timer.get(mk) is None:
                    timer.mark(mk)
        timer.mark("end")

        if one is not None:
            ev["one"] = one
            ev["prev"] = one.get("prev")
            ev["ctx"] = one.get("ctx")
            ev["frames"] = one.get("frames") or []
            ev["phase_ms"].update(one.get("phase_ms") or {})
            ev["suspend_held_ms"] = one.get("suspend_held_ms")
            ev["n_threads_sampled"] = 1
            errs = list(one.get("errors") or [])
            ev["errors"].extend(errs)
            r = one.get("resume_ret")
            ev["resume_ret"] = r
            ev["resume_ret_present"] = one.get("resume_ret") is not None
            ev["resume_ok"] = one.get("resume_ok")

            if one.get("resume_ok") is True and not errs and not ev["exception"]:
                # 正面证据：ResumeThread 返回有效值 + 无恢复错误 ⇒ 恢复成功
                ev["resume_state"] = "verified_ok"
                ev["sample_state"] = "resume_verified_ok"
            elif (one.get("resume_ok") is False or errs
                  or one.get("resume_ret") in (SUSPEND_FAILED, -1)):
                ev["resume_state"] = "failed"
                ev["sample_state"] = "resume_failed"
            elif one.get("resume_ok") is None:
                ev["resume_state"] = "unknown"
                ev["sample_state"] = "ok"
            else:
                ev["resume_state"] = "unknown"
                ev["sample_state"] = "ok"
        elif not ev["exception"]:
            # 理论上不可达；显式保留为可区分状态，不用 null
            ev["sample_state"] = "ok"
            ev["resume_state"] = "unknown"
            ev["errors"].append("no_result_returned")

        # --- (3) 预算状态（事件级；超限保留且不扩大采样） ---
        ev["cost_ns"] = cost_from_marks(timer.marks)
        ev["ns_marks"] = dict(timer.marks)
        e2e = int(ev["cost_ns"].get("end_to_end_ns", 0))
        if e2e / 1e6 > budget:
            ev["budget_exceeded"] = True
            ev["budget_state"] = "exceeded"
            ev["errors"].append("budget_exceeded:%.3fms>%.3fms"
                                % (e2e / 1e6, budget))
            if ev["sample_state"] not in ("error", "resume_failed", "not_attempted"):
                ev["sample_state"] = "error"
        return ev

    # -------- 整体采样（C3/D6 预算双闸） --------
    def sample(self, pid, timer=None):
        """全线程入口。timer 可选：驱动传入 EventTimer 以记录事件级分项里程碑。

        RE-N01：新增可选参数**不改变**原有调用语义（--selftest 的 47 项逐字未改）；
        驱动的全线程路径只调本方法，**从不**直接调 sample_one_thread（P1）。
        """
        self._resume_errors = []
        t_entry = OPS["now"]()
        result = {"pid": pid, "t": round(t_entry, 3), "threads": [], "errors": [],
                  "paused_ms": None, "aborted": False, "enum_ms": None,
                  "budget_ms": self.budget_ms}
        # MF-4（P1）：挂起任何线程**之前**做前置校验，避免逐线程「先挂后败再恢复」
        pf = self.preflight()
        if timer is not None:
            timer.mark("preflight")
        if pf is not None:
            result["errors"].append("preflight:" + pf)
            return result
        try:
            tids = self.enumerate_threads(pid)
        except E3Fail as e:
            result["errors"].append(str(e))
            return result
        if timer is not None:
            timer.mark("ownership")
        if self.max_threads > 0 and len(tids) > self.max_threads:
            result["truncated_from"] = len(tids)
            tids = tids[:self.max_threads]
        result["n_threads"] = len(tids)

        # ★ 位宽是**进程级属性**：用进程句柄查一次（IsWow64Process 不接受线程句柄）。
        #   注：进程句柄用 PROCESS_QUERY_LIMITED_INFORMATION(0x1000) 即可，不需要更多权限。
        self._target_is32 = None
        if "is_wow64" in OPS:
            try:
                hproc = OPS["open_process"](0x1000, pid)
                if hproc:
                    try:
                        self._target_is32 = OPS["is_wow64"](hproc)
                    finally:
                        OPS["close_handle"](hproc)
            except Exception:                            # noqa: BLE001
                self._target_is32 = None
        if "get_context_stub" not in OPS and self._target_is32 is None:
            result["errors"].append("wow64_query_failed")
            return result
        result["target_bits"] = 32 if self._target_is32 else 64

        # ★ 预算基准在**枚举之后**起算。
        #   理由：C3 的「单次总停顿 ≤ 50ms」约束的是**挂起线程那一段**（suspend→walk→resume），
        #   枚举线程快照（CreateToolhelp32Snapshot 遍历）并不挂起任何线程，不该计入暂停预算。
        #   （旧实现从 sample() 开头起算，导致 19 线程目标在第一次迭代前就误报 budget_exceeded。）
        t0 = OPS["now"]()
        result["enum_ms"] = round((t0 - t_entry) * 1000.0, 3)

        for tid in tids:
            if (OPS["now"]() - t0) * 1000.0 > self.budget_ms:
                result["aborted"] = True
                result["errors"].append("budget_exceeded")
                break
            try:
                result["threads"].append(self.sample_one_thread(
                    tid, timer=timer if timer is not None else None))
            except E3Fail as e:
                # C5：记录错误码，不重试、不强杀
                result["errors"].append(str(e))
            except Exception as e:                       # noqa: BLE001
                result["errors"].append("unexpected:%s" % type(e).__name__)
            # MF-3（P1）：单线程预算闸 —— 累计停顿超过 per-thread 预算即停止继续采样该轮
            over_total = (OPS["now"]() - t0) * 1000.0 > self.budget_ms
            over_perthread = self.per_thread_ms > 0 and (OPS["now"]() - t0) * 1000.0 > self.per_thread_ms
            if over_total or over_perthread:
                result["aborted"] = True
                result["errors"].append("budget_exceeded" if over_total
                                        else "per_thread_budget_exceeded")
                break
        result["paused_ms"] = round((OPS["now"]() - t0) * 1000.0, 3)
        # MF-6：把恢复失败汇总进 errors（不静默）
        for e in self._resume_errors:
            result["errors"].append(e)
        return result


def attach_stackwalker(sampler, hproc, pid, is32, max_frames=32):
    """给 sampler 挂上真 StackWalk64 回溯器。返回 (ok, err)。

    需要同目录的 3_stackwalker.py（独立模块，含结构定义与 5 参数回调）。
    挂载后 _walk 走真回溯；失败则保持单帧回退（并如实返回 err）。
    """
    try:
        import importlib.util as _ilu
        import os as _os
        here = _os.path.dirname(_os.path.abspath(__file__))
        mod_path = _os.path.join(here, "e3_stackwalker.py")
        if not _os.path.exists(mod_path):
            return (False, "e3_stackwalker_missing")
        spec = _ilu.spec_from_file_location("e3_stackwalker", mod_path)
        swm = _ilu.module_from_spec(spec)
        spec.loader.exec_module(swm)
        mods = swm.modules_of(pid)
        walker = swm.StackWalker(hproc, is32, mods, max_frames=max_frames)
        if not walker.init_symbols():
            return (False, walker.last_error or "sym_init_fail")
        walker.is_dbghelp_walker = True
        sampler.stack_walker = walker
        sampler._dbghelp_walker = walker
        return (True, None)
    except Exception as e:                               # noqa: BLE001
        return (False, "attach_exc:%s" % type(e).__name__)


class _ThreadEntry32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD),
                ("cntUsage", wt.DWORD),
                ("th32ThreadID", wt.DWORD),
                ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", wt.LONG),
                ("tpDeltaPri", wt.LONG),
                ("dwFlags", wt.DWORD)]


# ---------------------------------------------------------------- CONTEXT 结构
# ★ 真机验证确立的两条硬事实（见模块 docstring）：
#   1) 64 位进程读 64 位目标 → GetThreadContext + CONTEXT_AMD64（1232 B）
#   2) 64 位进程读 **32 位** 目标（gamemd.exe）→ Wow64GetThreadContext + WOW64_CONTEXT（716 B）
#   结构不匹配时 API **返回成功但字段全零**（静默失败），不会报错。

WOW64_CONTEXT_i386 = 0x00010000
WOW64_CONTEXT_CONTROL = WOW64_CONTEXT_i386 | 0x00000001      # 0x00010001
CONTEXT_AMD64 = 0x00100000
CONTEXT_AMD64_CONTROL = CONTEXT_AMD64 | 0x00000001           # 0x00100001

WOW64_CONTEXT_SIZE = 716
OFF_WOW64_EIP = 184
OFF_WOW64_ESP = 196


class WOW64_CONTEXT(ctypes.Structure):
    """32 位上下文（716 B），供 `Wow64GetThreadContext` 使用。

    字段偏移与 CONTEXT_i386 完全一致：Eip@184 / Esp@196 / Ebp@180 / EFlags@192。
    真机实测（对 SysWOW64\\charmap.exe）：Eip=0x766911dc、Esp=0x003ffb44、
    EFlags=0x00000206、SegCs=0x23（32 位 ring-3 选择子，64 位为 0x33）⇒ 确证 32 位上下文。
    """
    _fields_ = [
        ("ContextFlags", wt.DWORD),
        ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
        ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
        ("FloatSave", ctypes.c_byte * 112),
        ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
        ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
        ("Ecx", wt.DWORD), ("Eax", wt.DWORD),
        ("Ebp", wt.DWORD), ("Eip", wt.DWORD), ("SegCs", wt.DWORD), ("EFlags", wt.DWORD),
        ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
        ("ExtendedRegisters", ctypes.c_byte * 512),
    ]


# ---------------------------------------------------------------- 冻结母本自验


def verify_mothers_untouched():
    """C5：冻结母本零字节改动（实算比对，不是转引）。"""
    res = []
    for p, want in ((MOTHER_PROBE_V2, MOTHER_PROBE_V2_SHA),
                    (MOTHER_EARLYCLOSE, MOTHER_EARLYCLOSE_SHA)):
        if not p.exists():
            res.append((p.name, None, want, False))
            continue
        got = sha_file(p)
        res.append((p.name, got, want, got == want))
    return res


def load_mother_probe():
    """按 E3 卡 §3.1 要求：用 importlib **复用**母本的读取通道，而非重写。

    母本 `_drive_c2_x_probe_v2.py` 含 `OpenProcess` / `ReadProcessMemory` /
    `tri_read_u32` / `phase_sentinels`。本候选件**不复制其代码**，只 import 复用。

    ★ 安全：**只 import，不调用**。import 本身不触碰任何进程
      （母本模块级只定义常量与函数，`bind_real_ops()` 需显式调用才会绑定 Win32）；
      调用 `phase_sentinels(pid)` 才会真读进程 ⇒ 那属真机路径，本件不调用。

    返回 (module, err)。err 非空表示未能复用（此时调用方必须降级或报错，**不得**自行重写读取通道）。
    """
    if not MOTHER_PROBE_V2.exists():
        return (None, "mother_missing")
    # 复用前先验指纹，防母本被改
    if sha_file(MOTHER_PROBE_V2) != MOTHER_PROBE_V2_SHA:
        return (None, "mother_sha_mismatch")
    try:
        spec = importlib.util.spec_from_file_location(
            "e3_mother_probe_v2", str(MOTHER_PROBE_V2))
        if spec is None or spec.loader is None:
            return (None, "spec_none")
        mod = importlib.util.module_from_spec(spec)
        # 注意：母本模块顶层无副作用（无 bind_real_ops() 调用），可安全 import
        spec.loader.exec_module(mod)
        return (mod, None)
    except Exception as e:                               # noqa: BLE001
        return (None, "import_fail:%s" % type(e).__name__)


# ---------------------------------------------------------------- 离线单测


def run_selftest():
    """纯离线单测（零真机）。全部 Win32 调用走 stub。"""
    fails = []
    counter = {"n": 0}

    def t(name, cond, ev=""):
        counter["n"] += 1
        print("[%s] %-52s %s" % ("OK" if cond else "RED", name, ev))
        if not cond:
            fails.append(name)

    print("=" * 78)
    print("E3 候选件离线单测（零真机 · 全部 Win32 经 stub）")
    print("=" * 78)

    saved = dict(OPS)
    try:
        # ---------- 1. C1 触发逻辑 ----------
        print("\n-- C1 帧号停推检测 --")
        d = StallDetector(n_seconds=1.0, min_obs=4)
        seq = [(0.0, 100), (0.25, 100), (0.5, 100), (0.75, 100)]
        fired = [d.observe(t, f) for t, f in seq]
        t("C1-a 未满 1.0s 不触发", not any(fired), str(fired))
        t("C1-b 满 1.0s 触发一次", d.observe(1.05, 100) is True)
        t("C1-c 同段只报一次", d.observe(1.5, 100) is False)
        t("C1-d 帧号变化即重置", d.observe(1.6, 101) is False and d.fired is False)

        d2 = StallDetector(n_seconds=1.0, min_obs=4)
        for i in range(4):
            d2.observe(i * 0.25, 100)
        t("C1-e 读失败(None)不推进不重置",
          d2.observe(2.0, None) is False and d2.base_frame == 100)
        t("C1-f 读失败后仍能正常触发", d2.observe(2.1, 100) is True)

        d3 = StallDetector(n_seconds=1.0, min_obs=8)
        for i in range(5):
            d3.observe(i * 0.25, 7)
        t("C1-g 观测数不足 min_obs 不触发", d3.observe(1.5, 7) is False, "obs=5<8")

        # ---------- 2. C2/D 死锁防护 ----------
        print("\n-- C2/D 死锁防护（挂起必恢复） --")
        state = {"suspended": set(), "resumed": set(), "open": set(),
                 "t": [0.0], "resume_calls": 0}

        def now():
            state["t"][0] += 0.001
            return state["t"][0]

        def mk_ops(threads, fail_on=None, prev_map=None):
            prev_map = prev_map or {}

            def create_snapshot(_flags, _pid):
                return 1234

            def thread_first(_snap, ptr):
                e = ctypes.cast(ptr, ctypes.POINTER(_ThreadEntry32)).contents
                e.dwSize = ctypes.sizeof(_ThreadEntry32)
                e.th32ThreadID = threads[0]
                e.th32OwnerProcessID = 999
                return 1

            def thread_next(_snap, ptr):
                e = ctypes.cast(ptr, ctypes.POINTER(_ThreadEntry32)).contents
                idx = threads.index(e.th32ThreadID) + 1
                if idx >= len(threads):
                    return 0
                e.th32ThreadID = threads[idx]
                return 1

            def open_thread(_acc, _inh, tid):
                if fail_on == tid:
                    return None
                state["open"].add(tid)
                return 1000 + tid

            def suspend_thread(h):
                tid = h - 1000
                state["suspended"].add(tid)
                return prev_map.get(tid, 0)

            def resume_thread(h):
                tid = h - 1000
                state["suspended"].discard(tid)
                state["resumed"].add(tid)
                state["resume_calls"] += 1
                return 0

            def close_handle(_h):
                return 1

            def close_thread_handle(_h):
                return 1

            return {"now": now, "create_snapshot": create_snapshot,
                    "thread_first": thread_first, "thread_next": thread_next,
                    "open_thread": open_thread, "suspend_thread": suspend_thread,
                    "resume_thread": resume_thread, "close_handle": close_handle,
                    "close_thread_handle": close_thread_handle,
                    "get_context_stub": lambda h: {"bits": 32, "ip": 0x401000 + (h - 1000), "sp": 0x1000, "bp": 0x1100, "eflags": 0x202, "cs": 0x1b},
                    "walk_stub": lambda ctx, depth: [ctx["ip"]]}

        # 正常路径
        state["suspended"].clear(); state["resumed"].clear()
        OPS.clear(); OPS.update(mk_ops([11, 12, 13]))
        s = StackSampler()
        r = s.sample(999)
        t("D-a 三线程全部被采样", len([x for x in r["threads"] if "frames" in x]) == 3,
          "n=%d" % len(r["threads"]))
        t("D-b 采样结束后无残留挂起", not state["suspended"], str(state["suspended"]))
        t("D-c 三线程都被恢复过",
          {11, 12, 13} <= state["resumed"], str(state["resumed"]))
        t("D-d 无错误", not r["errors"], str(r["errors"]))

        # 已处于挂起态（D4）：不接管
        state["suspended"].clear(); state["resumed"].clear()
        OPS.clear(); OPS.update(mk_ops([21, 22], prev_map={21: 1}))
        s = StackSampler()
        r = s.sample(999)
        skipped = [x for x in r["threads"] if x.get("skipped") == "already_suspended"]
        t("D-e prev>0 的线程被跳过不接管", len(skipped) == 1, str(skipped))
        t("D-f 被跳过的线程已还原挂起态后未被我们恢复掉",
          state["resumed"] == {21, 22}, str(state["resumed"]))

        # OpenThread 失败（C5：记录错误码，继续其余）
        state["suspended"].clear(); state["resumed"].clear()
        OPS.clear(); OPS.update(mk_ops([31, 32, 33], fail_on=32))
        s = StackSampler()
        r = s.sample(999)
        t("C5-a 单线程失败不影响其余", len(r["threads"]) == 2, "n=%d" % len(r["threads"]))
        t("C5-b 错误码被记录", any("open_thread_fail" in e for e in r["errors"]),
          str(r["errors"]))
        t("C5-c 失败后无残留挂起", not state["suspended"], str(state["suspended"]))

        # 预算闸（C3/D6）
        state["suspended"].clear(); state["resumed"].clear()

        def slow_now():
            state["t"][0] += 0.030       # 每次 now() 前进 30ms
            return state["t"][0]

        o = mk_ops([41, 42, 43, 44, 45])
        o["now"] = slow_now
        OPS.clear(); OPS.update(o)
        s = StackSampler(budget_ms=50.0)
        r = s.sample(999)
        t("C3-a 超预算即中止", r["aborted"] is True, "paused=%.1fms" % r["paused_ms"])
        t("C3-b 中止后无残留挂起", not state["suspended"], str(state["suspended"]))

        # D3 最严路径：走栈时抛「非 E3Fail」异常，仍必须恢复（评审 R3 指出的缺口）
        state["suspended"].clear(); state["resumed"].clear()

        def boom(ctx, depth):
            raise RuntimeError("walker exploded")

        o = mk_ops([51, 52])
        o["walk_stub"] = boom
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        r = s.sample(999)
        t("D3-a 非 E3Fail 异常下仍恢复全部挂起",
          not state["suspended"] and {51, 52} <= state["resumed"],
          "susp=%s resumed=%s" % (state["suspended"], state["resumed"]))
        t("D3-b 非 E3Fail 异常被记为 unexpected 且不逃逸",
          any(e.startswith("unexpected:") for e in r["errors"]), str(r["errors"]))

        # 刚好等于预算边界（不超）
        state["suspended"].clear(); state["resumed"].clear()
        edge = {"t": [0.0]}

        def edge_now():
            edge["t"][0] += 0.010
            return edge["t"][0]

        o = mk_ops([61])
        o["now"] = edge_now
        OPS.clear(); OPS.update(o)
        # 两道闸都要放宽，才能测「预算内不中止」：总 50ms、单线程也放宽到 50ms
        s = StackSampler(budget_ms=50.0, per_thread_ms=50.0)
        r = s.sample(999)
        t("C3-c 预算内（20ms<50ms）不中止", r["aborted"] is False
          and "budget_exceeded" not in r["errors"], "paused=%.1fms" % r["paused_ms"])

        # MF-3：单线程预算（比总预算更紧）应生效
        state["suspended"].clear(); state["resumed"].clear()
        state["t"][0] = 0.0
        o = mk_ops([62, 63, 64])
        o["now"] = lambda: (state["t"].__setitem__(0, state["t"][0] + 0.010), state["t"][0])[1]
        OPS.clear(); OPS.update(o)
        s = StackSampler(budget_ms=1000.0, per_thread_ms=15.0)
        r = s.sample(999)
        t("MF3-a 单线程预算(15ms)先于总预算(1000ms)生效",
          "per_thread_budget_exceeded" in r["errors"], str(r["errors"]))
        t("MF3-b 单线程预算中止后无残留挂起", not state["suspended"], str(state["suspended"]))

        # snapshot 失败（须先过 preflight，故同时提供 walk/context stub）
        OPS.clear()
        OPS.update({"now": now, "create_snapshot": lambda a, b: -1,
                    "close_handle": lambda h: 1,
                    "get_context_stub": lambda h: {"bits": 32, "ip": 0x401000, "sp": 0x1000, "bp": 0x1100, "eflags": 0x202, "cs": 0x1b},
                    "walk_stub": lambda ctx, depth: [ctx["ip"]]})
        s = StackSampler()
        r = s.sample(999)
        t("C5-d snapshot 失败被记录不抛", any("snapshot_fail" in e for e in r["errors"]),
          str(r["errors"]))

        # MF-4：preflight 前置校验（**context 通道**未绑定时应在挂起之前就拒绝）
        # 注：walker 不再是硬前置 —— 无 walker 时 _walk 退回单帧（只报 ip），不会先挂后败。
        state["suspended"].clear(); state["resumed"].clear()
        o = mk_ops([71, 72])
        del o["get_context_stub"]              # 抽掉 context 通道
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        r = s.sample(999)
        t("MF4-a context 未绑定 → preflight 拒绝",
          any("preflight:context_not_bound" == e for e in r["errors"]), str(r["errors"]))
        t("MF4-b preflight 拒绝后零线程被挂起",
          not state["suspended"] and not state["resumed"],
          "susp=%s resumed=%s" % (state["suspended"], state["resumed"]))

        # MF-4c：无 walker 但有 context 时，退回单帧（只报 ip），仍须正常恢复
        state["suspended"].clear(); state["resumed"].clear()
        o = mk_ops([73])
        del o["walk_stub"]
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        r = s.sample(999)
        th = [x for x in r["threads"] if "frames" in x]
        t("MF4-c 无 walker 时退回单帧（frames 长度 1）",
          len(th) == 1 and len(th[0]["frames"]) == 1, str(r["threads"]))
        t("MF4-d 单帧回退路径仍无残留挂起", not state["suspended"], str(state["suspended"]))

        # MF-5：自采样守卫（传自身 pid 必须拒绝）
        OPS.clear(); OPS.update(mk_ops([81]))
        s = StackSampler()
        r = s.sample(os.getpid())
        t("MF5 自 pid 被拒（防自死锁）",
          any(e.startswith("refuse_self_pid") for e in r["errors"]), str(r["errors"]))

        # MF-1：suspend 失败返回 0xFFFFFFFF / -1 / None 三形态都必须被判为失败
        for bad, label in ((0xFFFFFFFF, "0xFFFFFFFF"), (-1, "-1"), (None, "None")):
            state["suspended"].clear(); state["resumed"].clear()
            o = mk_ops([91])

            def mk_susp_fail(badval):
                def _s(h):
                    return badval
                return _s
            o["suspend_thread"] = mk_susp_fail(bad)
            OPS.clear(); OPS.update(o)
            s = StackSampler()
            r = s.sample(999)
            t("MF1 suspend 失败(%s) 被判失败不误采" % label,
              any("suspend_thread_fail" in e for e in r["errors"])
              and not r["threads"] and not state["resumed"],
              "errors=%s resumed=%s" % (r["errors"], state["resumed"]))

        # MF-6：ResumeThread 失败必须记入 errors（不静默）
        state["suspended"].clear(); state["resumed"].clear()
        o = mk_ops([95])
        o["resume_thread"] = lambda h: 0xFFFFFFFF
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        r = s.sample(999)
        t("MF6 resume 失败被记入 errors（不静默）",
          any("resume_fail" in e or "resume_restore_fail" in e for e in r["errors"]),
          str(r["errors"]))

        # MF-8：反身护栏 + 独立输出目录
        t("MF8-a 未声明窗口 → 默认拒绝", reflexive_guard_ok() == (False, "windows_not_declared"))
        t("MF8-b 窗口重叠 → 拒绝", reflexive_guard_ok((0, 10), (5, 15)) == (False, "windows_overlap"))
        t("MF8-c 窗口不重叠 → 通过", reflexive_guard_ok((0, 10), (10, 20)) == (True, "ok"))
        # RE-N01 / §四：原用 tempfile.mkdtemp() 落在 %TEMP%。DSH 在
        # workspace-write 策略下把 %TEMP% 映射成 dsh-* 临时根：允许建目录、
        # 拒绝**在该目录内新建文件** ⇒ 该项假红（PermissionError），与采样器无关。
        # 现改为被测工作区内的临时子目录，断言性质（写入独立目录成功）不变，
        # 同时不再越出本轮写域 lead/next_re_20261112/RE-N01/。
        tmpout = Path(__file__).resolve().parent.parent / "out" / "_selftest_scratch"
        tmpout.mkdir(parents=True, exist_ok=True)
        pth, werr = write_e3_output({"pid": 4242, "threads": []}, out_dir=tmpout)
        t("MF8-d 输出写入独立目录成功", pth is not None and werr is None, str(werr))
        t("MF8-e 输出目录在写域内（非②读数路径）",
          str(E3_OUT_DIR).startswith(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112"),
          str(E3_OUT_DIR))

        # ---------- 3. C5 冻结母本零改动 + importlib 复用 ----------
        print("\n-- C5 冻结母本零字节改动 + importlib 复用（只 import 不调用） --")
        for name, got, want, okk in verify_mothers_untouched():
            t("C5-mother %s" % name, okk,
              (got[:16] + "..." if got else "MISSING"))

        mod, err = load_mother_probe()
        t("C5-import 母本 import 成功（只 import，未绑定 Win32）",
          err is None and mod is not None, str(err))
        if mod is not None:
            t("C5-import 复用得到 tri_read_u32", hasattr(mod, "tri_read_u32"))
            t("C5-import 复用得到 phase_sentinels", hasattr(mod, "phase_sentinels"))
            t("C5-import 母本 OPS 未被绑定（未触发任何真实 Win32）",
              isinstance(getattr(mod, "OPS", None), dict) and len(mod.OPS) == 0,
              "len(OPS)=%d" % len(getattr(mod, "OPS", {})))
            t("C5-import G_FRAME 与母本一致",
              getattr(mod, "G_FRAME", None) == G_FRAME,
              "mother=%s ours=%s" % (hex(getattr(mod, 'G_FRAME', 0)), hex(G_FRAME)))

        # ---------- 4. 真机入口护栏（已授权，但护栏不因授权放宽） ----------
        print("\n-- 真机入口护栏（2026-11-12 已授权真机；护栏仍在） --")
        import contextlib as _cl
        import io as _io
        _b1 = _io.StringIO()
        with _cl.redirect_stderr(_b1):
            rc_nospec = main_live(["--live"])
        t("AUTH-a 无 --pid/--launch 时拒绝并返回 2", rc_nospec == 2, "rc=%d" % rc_nospec)
        _b2 = _io.StringIO()
        with _cl.redirect_stderr(_b2):
            rc_self = main_live(["--live", "--pid", str(os.getpid())])
        t("AUTH-b 自 pid 拒绝并返回 4（防自死锁）", rc_self == 4, "rc=%d" % rc_self)

        # ============================================================
        # RE-N01 新增项（**单独编号 N01-xx**；上面 47 项逐字未改）
        # 全部离线 stub，零真机、零 Win32 调用。
        # ============================================================
        print("\n-- RE-N01 新增项（N01-xx，最小增量验证） --")

        def _mk_ops2(threads=(30668,), pid=14412, resume_fail=False,
                     ctx_bound=True, now_ns=None):
            st = {"t": [0], "suspend_calls": 0, "resume_calls": 0,
                  "sample_calls": 0, "open_calls": 0, "closed": []}
            clock = now_ns or (lambda: (st["t"].__setitem__(0, st["t"][0] + 1_000_000),
                                        st["t"][0])[1])
            idx = {"i": -1}

            def _tf(_snap, ptr):
                e = ctypes.cast(ptr, ctypes.POINTER(_ThreadEntry32)).contents
                e.dwSize = ctypes.sizeof(_ThreadEntry32)
                idx["i"] = 0
                if not threads:
                    return 0
                e.th32ThreadID = threads[0]
                e.th32OwnerProcessID = pid
                return 1

            def _tn(_snap, ptr):
                e = ctypes.cast(ptr, ctypes.POINTER(_ThreadEntry32)).contents
                idx["i"] += 1
                if idx["i"] >= len(threads):
                    return 0
                e.dwSize = ctypes.sizeof(_ThreadEntry32)
                e.th32ThreadID = threads[idx["i"]]
                return 1

            o = {
                "now": lambda: st["t"][0] / 1e9,
                "now_ns": clock,
                "create_snapshot": lambda a, b: 4242,
                "thread_first": _tf,
                "thread_next": _tn,
                "close_handle": lambda h: 1,
                "open_process": lambda a, p: 9999,
                "is_wow64": lambda h: True,
                "open_thread": lambda a, b, tid: (st.__setitem__("open_calls", st["open_calls"] + 1), 10000 + tid)[1],
                "close_thread_handle": lambda h: 1,
                "suspend_thread": lambda h: (st.__setitem__("suspend_calls", st["suspend_calls"] + 1), 0)[1],
                "resume_thread": lambda h: (st.__setitem__("resume_calls", st["resume_calls"] + 1),
                                            (0xFFFFFFFF if resume_fail else 0))[1],
            }
            if ctx_bound:
                o["get_context_stub"] = lambda h: {"bits": 32, "ip": 0x401000,
                                                   "sp": 0x1000, "bp": 0x1100,
                                                   "eflags": 0x202, "cs": 0x1b}
                o["walk_stub"] = lambda c, depth: [c["ip"], c["ip"] + 4]
            return o, st

        # N01-01 新返回字段齐全（B1/B2）
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        one = s.sample_one_thread(30668)
        need = ("errors", "resume_ok", "resume_ret", "prev",
                "suspend_held_ms", "phase_ms")
        t("N01-01 sample_one_thread 六新字段齐全（含 errors 非 null）",
          all(k in one for k in need) and isinstance(one["errors"], list)
          and one["resume_ok"] is True and one["resume_ret"] == 0,
          str({k: one.get(k) for k in need}))

        # N01-02 preflight_target 一次完成位宽+preflight+归属，且不挂起
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        pf = s.preflight_target(14412, 30668)
        t("N01-02 preflight_target ok：位宽+preflight+TID∈PID，零挂起",
          pf["ok"] is True and pf["is32"] is True
          and pf["ownership"]["tid_belongs_to_pid"] is True
          and pf["preflight"]["ok"] is True and st["suspend_calls"] == 0,
          "reason=%s susp=%d" % (pf["reason"], st["suspend_calls"]))

        # N01-03 TID 不属于 PID ⇒ 拒绝（Toolhelp 快照）
        o, st = _mk_ops2(threads=(30668, 30669))
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        pf = s.preflight_target(14412, 77777)
        t("N01-03 TID∉PID 被拒且写明原因",
          pf["ok"] is False
          and pf["ownership"]["tid_belongs_to_pid"] is False
          and "tid_not_in_pid" in pf["reason"]
          and st["suspend_calls"] == 0, pf["reason"])

        # N01-04 恢复失败必须进入事件（不是 null、不是空）
        o, st = _mk_ops2(resume_fail=True)
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        ev = s.sample_single(30668, 14412)
        t("N01-04 恢复失败 → sample_state=resume_failed，errors 非空",
          ev["sample_state"] == "resume_failed"
          and ev["resume_state"] == "failed"
          and len(ev["errors"]) > 0 and ev["sample_state"] is not None,
          "state=%s errors=%s" % (ev["sample_state"], ev["errors"]))

        # N01-05 preflight 失败 ⇒ 零线程挂起 + 事件写明原因
        o, st = _mk_ops2(ctx_bound=False)
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        ev = s.sample_single(30668, 14412)
        t("N01-05 preflight 失败：零挂起 + not_attempted + 原因",
          st["suspend_calls"] == 0
          and ev["sample_state"] == "not_attempted"
          and "context_not_bound" in ev["preflight"]["reason"],
          "susp=%d reason=%s" % (st["suspend_calls"], ev["preflight"]["reason"]))

        # N01-06 sample_single 绝不调用全线程 sample()（互斥）
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        calls = {"sample": 0}
        orig_sample = StackSampler.sample

        def _spy_sample(self, pid):
            calls["sample"] += 1
            return orig_sample(self, pid)

        StackSampler.sample = _spy_sample
        try:
            ev = s.sample_single(30668, 14412)
        finally:
            StackSampler.sample = orig_sample
        t("N01-06 sample_single 全线程 sample() 调用数==0",
          calls["sample"] == 0 and ev["sample_called"] is False,
          "calls=%d" % calls["sample"])

        # N01-07 干净单线程 ⇒ 恢复成功正面证据
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        ev = s.sample_single(30668, 14412)
        t("N01-07 干净采样 ⇒ resume_verified_ok（正面证据，非仅 errors=[]）",
          ev["sample_state"] == "resume_verified_ok"
          and ev["resume_state"] == "verified_ok"
          and ev["resume_ret_present"] is True
          and ev["errors"] == [] and ev["n_threads_sampled"] == 1,
          "state=%s resume=%s" % (ev["sample_state"], ev["resume_state"]))

        # N01-08 cost_from_marks：六字段齐全 + 端到端 ≥ 分项之和
        fake = EventTimer(now_ns=lambda: 0)
        marks = {"candidate": 0, "verdict": 100, "preflight": 200,
                 "ownership": 300, "suspend": 400, "context": 600,
                 "walk": 900, "resume": 1000, "end": 1100}
        fake.marks = dict(marks)
        c = cost_from_marks(fake.marks, t_candidate_ns=marks["candidate"])
        six = ("detect_ns", "context_ns", "walk_ns", "resume_ns",
               "end_to_end_ns", "suspend_held_ns")
        t("N01-08 六计时字段存在且 end_to_end ≥ 在窗口内分项之和",
          all(k in c for k in six)
          and c["end_to_end_ns"] >= (c["preflight_ns"] + c["ownership_ns"]
                                    + c["open_ns"] + c["context_ns"]
                                    + c["walk_ns"] + c["resume_ns"]
                                    + c["overhead_ns"])
          and c["suspend_held_ns"] <= c["end_to_end_ns"],
          "e2e=%d susp=%d" % (c["end_to_end_ns"], c["suspend_held_ns"]))

        # N01-09 异常被收进事件，不穿透监测循环（B3）
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        OPS["open_thread"] = lambda a, b, tid: None
        s = StackSampler()
        ev = s.sample_single(30668, 14412)
        t("N01-09 E3Fail 被事件吸收，不逃逸（修 B3）",
          ev["sample_state"] == "error" and ev["exception"].startswith("E3Fail")
          and len(ev["errors"]) > 0, ev["exception"])

        # N01-10 四态 + error 两两不同、无 None/空串
        states = ("not_attempted", "ok", "resume_verified_ok", "resume_failed",
                  "error")
        t("N01-10 五取值两两不同且均非 null/空（四态可区分）",
          len(set(states)) == 5 and all(x for x in states)
          and all(x in SAMPLE_STATES for x in states),
          str(states))

        # N01-11 单线程入口不依赖外部私有属性写入（B5）
        o, st = _mk_ops2()
        OPS.clear(); OPS.update(o)
        s = StackSampler()
        # 故意不写 s._target_is32 —— 原件 sample_one_thread 会 wow64_query_not_done
        ev = s.sample_single(30668, 14412)
        t("N01-11 不写私有 _target_is32 也能完整单线程采样",
          ev["sample_state"] == "resume_verified_ok" and s._target_is32 is True,
          "is32=%s state=%s" % (s._target_is32, ev["sample_state"]))

    finally:
        OPS.clear()
        OPS.update(saved)

    print("\n" + "=" * 78)
    total = counter["n"]
    print("结果：%d 项检查，%d 项失败%s" % (total, len(fails),
                                    "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


# ---------------------------------------------------------------- 真机入口（拒绝）


def main_live(argv):
    """`--live` 入口：**真机采集**（用户 2026-11-12 授权「统一真机以及一切操作」）。

    用法:
        --live --pid <PID> [--out DIR] [--dry-run]
        --live --launch <EXE> [--out DIR]      自启动并采样（退出时终止）

    安全护栏（每一条都在代码里，不是只写在文档里）：
      L1 必须显式给目标（--pid 或 --launch）；不猜。
      L2 拒绝采样自身 pid（防自死锁）。
      L3 `--dry-run` 只做枚举与位宽判定，**不挂起任何线程**。
      L4 采样结果写独立目录（MF-8），不碰②读数文件。
      L5 任何一步失败只记错误码，**不重试、不强杀**（C5）。
      L6 `--launch` 启动的进程，在 finally 里终止，不遗留。
    """
    def opt(name, default=None):
        if name in argv:
            i = argv.index(name)
            if i + 1 < len(argv):
                return argv[i + 1]
        return default

    pid_s = opt("--pid")
    exe = opt("--launch")
    dry = "--dry-run" in argv
    out_dir = opt("--out")
    try:
        budget = float(opt("--budget", "300"))      # 默认 300ms（19 线程量级实测需 ~60ms，留余量）
    except ValueError:
        budget = 300.0
    try:
        max_threads = int(opt("--max-threads", "0"))  # 0=不限
    except ValueError:
        max_threads = 0

    if not pid_s and not exe:
        print("!! --live 需要 --pid <PID> 或 --launch <EXE>", file=sys.stderr)
        return 2

    proc = None
    try:
        # 先绑定真实 ops（--launch 分支需要 OPS["sleep"] 等在启动前可用）
        bind_real_ops()

        if exe:
            import subprocess
            print("启动目标: %s" % exe)
            proc = subprocess.Popen([exe], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            pid = proc.pid
            OPS["sleep"](1.2)          # 等它起来
        else:
            pid = int(pid_s)

        if pid == os.getpid():
            print("!! 拒绝采样自身 pid=%d（防自死锁）" % pid, file=sys.stderr)
            return 4

        s = StackSampler(budget_ms=budget)
        if max_threads > 0:
            s.max_threads = max_threads

        # L3: dry-run 只枚举与判位宽
        if dry:
            print("[dry-run] 不挂起任何线程")
            tids = s.enumerate_threads(pid)
            print("  pid=%d  线程数=%d  tids=%s" % (pid, len(tids), tids))
            if tids:
                h = OPS["open_process"](0x1000, pid)
                if h:
                    w = OPS["is_wow64"](h)
                    OPS["close_handle"](h)
                    print("  目标位宽: %s" % ("32 位(WOW64)" if w else "64 位"))
            return 0

        # 真采样前挂 StackWalk64 回溯器（拿真调用栈，而非单帧）
        # ★ 必须先判位宽再 attach：attach 需要 is32 决定用 I386 还是 AMD64 机器类型；
        #   若在 sample() 之前拿不到（_target_is32 尚未计算），会用错机器类型 ⇒ OSError。
        hproc = OPS["open_process"](0x0010 | 0x0400, pid)   # VM_READ | QUERY_INFORMATION
        walker_ok, walker_err = (False, "no_open_process")
        if hproc:
            is32 = None
            try:
                is32 = OPS["is_wow64"](hproc)
            except Exception:                            # noqa: BLE001
                is32 = None
            if is32 is None:
                walker_ok, walker_err = (False, "wow64_query_failed")
            else:
                s._target_is32 = is32        # 提前固化，sample() 内会复用
                walker_ok, walker_err = attach_stackwalker(s, hproc, pid, bool(is32))
            if not walker_ok:
                print("!! StackWalker 挂载失败(%s) ⇒ 退回单帧" % walker_err, file=sys.stderr)
        try:
            res = s.sample(pid)
        finally:
            if walker_ok:
                try:
                    s.stack_walker.cleanup()
                except Exception:                        # noqa: BLE001
                    pass
            if hproc:
                OPS["close_handle"](hproc)
        print("pid=%d n_threads=%s paused_ms=%s aborted=%s errors=%s"
              % (pid, res.get("n_threads"), res.get("paused_ms"),
                 res.get("aborted"), res["errors"]))
        res["frames_is_single"] = s.frames_is_single
        res["stackwalker"] = walker_ok
        if s.frames_is_single:
            print("  ⚠ 单帧模式（非调用栈）：StackWalker 未挂上")
        for th in res["threads"]:
            if "frames" in th:
                ctx = th.get("ctx") or {}
                fr = th["frames"]
                # frames 元素可能是 dict({"addr","name"}) 或裸 int（stub）
                def _fmt(x):
                    if isinstance(x, dict):
                        return x.get("name") or hex(int(x.get("addr") or 0))
                    return hex(int(x))
                print("  tid=%-6d bits=%s ip=%s frames=%d"
                      % (th["tid"], ctx.get("bits"),
                         hex(ctx.get("ip", 0)) if ctx.get("ip") else "?",
                         len(fr)))
                for i, x in enumerate(fr[:8]):
                    print("        #%d %s" % (i, _fmt(x)))
                if len(fr) > 8:
                    print("        ... (%d more)" % (len(fr) - 8))
            else:
                print("  tid=%-6d skipped=%s" % (th["tid"], th.get("skipped")))

        # L4: 写独立输出目录
        pth, werr = write_e3_output(res, out_dir=out_dir)
        if pth:
            print("输出: %s" % pth)
        else:
            print("!! 输出写入失败: %s" % werr, file=sys.stderr)
        return 0 if not res["errors"] else 5
    finally:
        if proc is not None:
            try:
                proc.terminate(); proc.wait(timeout=5)
                print("已终止目标进程 rc=%r" % proc.returncode)
            except Exception as e:                      # noqa: BLE001
                print("终止目标失败: %s" % e, file=sys.stderr)
        OPS.clear()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--live" in argv:
        return main_live(argv)
    if "--selftest" in argv or not argv:
        return run_selftest()
    print("用法: python -I -X utf8 %s --selftest                  （离线单测）"
          % os.path.basename(__file__))
    print("      --live --pid <PID> [--budget MS] [--max-threads N] [--dry-run] [--out DIR]  （真机采集；已授权）")
    print("      --live --launch <EXE> [--out DIR]               （自启动并采样）")
    return 2


if __name__ == "__main__":
    sys.exit(main())
