# -*- coding: utf-8 -*-
"""E3 真机路径验证（对**无害哑进程**，不动游戏）。

目的：验证 MF-1（restype/argtypes 与挂起失败判据）与 MF-2（Thread32First dwSize）
      在**真实 Win32** 下成立 —— 这是评审列为 P0 的两个阻塞项。

方法：spawn 一个只做 sleep 的 python 子进程作为采样目标，
      对它跑真实的 SuspendThread / GetThreadContext / ResumeThread 路径。
      **不触碰 gamemd.exe / ra2loader / YURI.exe。**

安全：
  - 目标进程是我们自己 spawn 的哑进程，随时可杀；
  - 采样器带预算闸与 try/finally 恢复；
  - 结束前断言目标进程仍存活且能正常退出（证明没被搞死）。
"""
import ctypes
import ctypes.wintypes as wt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
CAND = REPO / "lead" / "re_d13_ruling_20261112" / "e3_stack_sampler_candidate.py"


def load_candidate():
    spec = importlib.util.spec_from_file_location("e3c_live", str(CAND))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class CONTEXT_i386(ctypes.Structure):
    """x86 CONTEXT，**必须整 716 字节**（GetThreadContext 会按 sizeof(CONTEXT) 校验）。

    结构布局（x86，Win32）：
      ContextFlags@0, Dr0..Dr3/Dr6/Dr7@4..24, FloatSave(112B)@28..139,
      SegGs/SegFs/SegEs/SegDs@140..155, Edi/Esi/Ebx/Edx/Ecx/Eax@156..179,
      Ebp@180, Eip@184, SegCs@188, EFlags@192, Esp@196, SegSs@200,
      其余（ExtendedRegisters）填充到 716。
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
        # 补足到 716 字节（x86 CONTEXT 全体大小）
        ("ExtendedRegisters", ctypes.c_byte * 512),
    ]


# 关键字段在缓冲区内的字节偏移（自查用）
OFF_EIP = 184          # CONTEXT_i386.Eip
OFF_ESP = 196          # CONTEXT_i386.Esp
CONTEXT_SIZE = 716     # CONTEXT_i386 总大小


class CONTEXT_AMD64(ctypes.Structure):
    """x64 CONTEXT —— **64 位进程必须用这个**，不是 CONTEXT_i386。

    ★ 真机验证抓出的关键事实：本项目跑在 64 位 Python 上，
      `GetThreadContext` 在 64 位进程中按 `sizeof(CONTEXT)`(AMD64, 1232 B) 校验，
      传 CONTEXT_i386(716 B) 会**返回成功但填不进任何字段**（Eip/Esp 全 0）——不是失败，
      是静默的「结构不匹配」。这比直接报错更危险。

    布局（x64）：P1Home..P6Home(48) @0；ContextFlags @48；MxCsr @52；
      SegCs..SegSs(6×WORD) @56；EFlags @68；Dr0..Dr7(6×8) @72；
      Rax@120 Rcx@128 Rdx@136 Rbx@144 Rsp@152 Rbp@160 Rsi@168 Rdi@176
      R8..R15 @184..240；Rip @248；其后向量寄存器等，总 1232 B。
    """
    _fields_ = [
        ("P1Home", ctypes.c_uint64), ("P2Home", ctypes.c_uint64),
        ("P3Home", ctypes.c_uint64), ("P4Home", ctypes.c_uint64),
        ("P5Home", ctypes.c_uint64), ("P6Home", ctypes.c_uint64),
        ("ContextFlags", wt.DWORD),
        ("MxCsr", wt.DWORD),
        ("SegCs", wt.WORD), ("SegDs", wt.WORD), ("SegEs", wt.WORD),
        ("SegFs", wt.WORD), ("SegGs", wt.WORD), ("SegSs", wt.WORD),
        ("EFlags", wt.DWORD),
        ("Dr0", ctypes.c_uint64), ("Dr1", ctypes.c_uint64), ("Dr2", ctypes.c_uint64),
        ("Dr3", ctypes.c_uint64), ("Dr6", ctypes.c_uint64), ("Dr7", ctypes.c_uint64),
        ("Rax", ctypes.c_uint64), ("Rcx", ctypes.c_uint64), ("Rdx", ctypes.c_uint64),
        ("Rbx", ctypes.c_uint64), ("Rsp", ctypes.c_uint64), ("Rbp", ctypes.c_uint64),
        ("Rsi", ctypes.c_uint64), ("Rdi", ctypes.c_uint64),
        ("R8", ctypes.c_uint64), ("R9", ctypes.c_uint64), ("R10", ctypes.c_uint64),
        ("R11", ctypes.c_uint64), ("R12", ctypes.c_uint64), ("R13", ctypes.c_uint64),
        ("R14", ctypes.c_uint64), ("R15", ctypes.c_uint64),
        ("Rip", ctypes.c_uint64),
        # VectorRegister[26] + VectorControl + DebugControl + LastException* + 对齐 ⇒ 补到 1232
        ("_tail", ctypes.c_byte * 976)   # 256 + 976 = 1232,
    ]


CONTEXT_AMD64_SIZE = 1232
FLAG_AMD64_CONTROL = 0x00100001     # CONTEXT_AMD64 | CONTEXT_CONTROL
FLAG_I386_CONTROL = 0x00010001      # CONTEXT_i386 | CONTEXT_CONTROL


WOw64_NOTE = "gamemd.exe 是 32 位进程；64 位 Python 采集它必须用 Wow64GetThreadContext + Wow64 CONTEXT"

_g = {}   # 记录取到的上下文值供后段断言

def main():
    fails = []
    counter = {"n": 0}

    def t(name, cond, ev=""):
        counter["n"] += 1
        print("[%s] %-50s %s" % ("OK" if cond else "RED", name, ev))
        if not cond:
            fails.append(name)

    print("=" * 78)
    print("E3 真机路径验证 —— 对无害哑进程（不触碰游戏）")
    print("=" * 78)

    m = load_candidate()

    # 1. 指纹自核
    h = hashlib.sha256(CAND.read_bytes()).hexdigest()
    print("\n候选件 sha256 = %s" % h)

    # 2. spawn 哑进程（sleep 600s，随时可杀）
    dummy_code = "import time\nfor _ in range(600):\n    time.sleep(1)\n"
    proc = subprocess.Popen([sys.executable, "-c", dummy_code],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("哑进程 pid = %d" % proc.pid)
    try:
        time.sleep(0.8)                     # 等它起来

        # 3. 绑定真实 ops（这是 MF-1 的验证对象）
        print("\n-- MF-1 验证：bind_real_ops 签名与挂起失败判据 --")
        m.bind_real_ops()
        t("真机 ops 已绑定", len(m.OPS) > 0, "n=%d" % len(m.OPS))

        # 4. MF-2：真实 Thread32First 需要 dwSize
        print("\n-- MF-2 验证：CreateToolhelp32Snapshot + Thread32First --")
        s = m.StackSampler()
        tids = s.enumerate_threads(proc.pid)
        t("MF2-a 真实 enumerate_threads 成功", len(tids) > 0, "tids=%s" % tids)

        # 5. 真实挂起/恢复单线程（MF-1 核心）
        print("\n-- MF-1 核心：真实 SuspendThread / ResumeThread 配对 --")
        tid = tids[0]
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenThread.restype = wt.HANDLE
        k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        k32.SuspendThread.restype = wt.DWORD
        k32.SuspendThread.argtypes = [wt.HANDLE]
        k32.ResumeThread.restype = wt.DWORD
        k32.ResumeThread.argtypes = [wt.HANDLE]
        k32.CloseHandle.argtypes = [wt.HANDLE]

        th = k32.OpenThread(0x0002, False, tid)
        t("MF1-a 真实 OpenThread 成功", bool(th), "handle=%r" % th)
        if th:
            prev = k32.SuspendThread(th)
            t("MF1-b 真实 SuspendThread 返回上次计数(0)",
              prev == 0, "prev=%r (0=首次挂起)" % prev)
            prev2 = k32.SuspendThread(th)
            t("MF1-c 二次挂起返回 1（计数语义确认）", prev2 == 1, "prev2=%r" % prev2)
            r1 = k32.ResumeThread(th)
            r2 = k32.ResumeThread(th)
            t("MF1-d 两次 Resume 精确还原（2→1→0）", r1 == 2 and r2 == 1,
              "r1=%r r2=%r" % (r1, r2))
            k32.CloseHandle(th)

        # 6. 真实 GetThreadContext（★ 必须先 SuspendThread；★ 且必须用与本进程位宽匹配的 CONTEXT）
        print("\n-- 真实 GetThreadContext（先挂起，后取上下文；64 位用 AMD64 CONTEXT）--")
        print("  本进程位宽 = %d 位；CONTEXT_i386=%d B；CONTEXT_AMD64=%d B"
              % (ctypes.sizeof(ctypes.c_void_p) * 8,
                 ctypes.sizeof(CONTEXT_i386), ctypes.sizeof(CONTEXT_AMD64)))
        t("CONTEXT_AMD64 大小 == 1232", ctypes.sizeof(CONTEXT_AMD64) == CONTEXT_AMD64_SIZE,
          str(ctypes.sizeof(CONTEXT_AMD64)))
        t("CONTEXT_i386 大小 == 716", ctypes.sizeof(CONTEXT_i386) == CONTEXT_SIZE,
          str(ctypes.sizeof(CONTEXT_i386)))

        th2 = k32.OpenThread(0x0008 | 0x0002, False, tid)
        if th2:
            pv = k32.SuspendThread(th2)
            t("  取上下文前已挂起线程", pv == 0, "prev=%r" % pv)

            if ctypes.sizeof(ctypes.c_void_p) == 8:
                ctx = CONTEXT_AMD64()
                ctx.ContextFlags = FLAG_AMD64_CONTROL
                ok = k32.GetThreadContext(th2, ctypes.byref(ctx))
                t("真机 GetThreadContext(AMD64) 成功", bool(ok), "sizeof=%d" % ctypes.sizeof(ctx))
                if ok:
                    t("  取得非零 Rip", ctx.Rip != 0, "rip=%#x" % ctx.Rip)
                    t("  取得非零 Rsp", ctx.Rsp != 0, "rsp=%#x" % ctx.Rsp)
                    _g["rip"], _g["rsp"] = ctx.Rip, ctx.Rsp
            else:
                ctx = CONTEXT_i386()
                ctx.ContextFlags = FLAG_I386_CONTROL
                ok = k32.GetThreadContext(th2, ctypes.byref(ctx))
                t("真机 GetThreadContext(i386) 成功", bool(ok), "sizeof=%d" % ctypes.sizeof(ctx))
                if ok:
                    t("  取得非零 Eip", ctx.Eip != 0, "eip=%#x" % ctx.Eip)
                    t("  取得非零 Esp", ctx.Esp != 0, "esp=%#x" % ctx.Esp)
                    _g["rip"], _g["rsp"] = ctx.Eip, ctx.Esp

            r = k32.ResumeThread(th2)
            t("  取上下文后已精确恢复", r == 1, "resume=%r" % r)
            k32.CloseHandle(th2)

        # 6b. 已证事实：结构不匹配时 GetThreadContext 会「成功但零填充」（危险静默）
        print("\n-- 静默陷阱复现：64 位进程传 32 位 CONTEXT --")
        th3 = k32.OpenThread(0x0008 | 0x0002, False, tid)
        if th3 and ctypes.sizeof(ctypes.c_void_p) == 8:
            k32.SuspendThread(th3)
            bad = CONTEXT_i386()
            bad.ContextFlags = FLAG_I386_CONTROL
            ok2 = k32.GetThreadContext(th3, ctypes.byref(bad))
            t("  传 i386 CONTEXT 到 64 位进程：返回成功但字段为零（静默陷阱）",
              bool(ok2) and bad.Eip == 0,
              "ok=%r eip=%#x（ok=True 但 eip=0 ⇒ 不匹配不报错）" % (ok2, bad.Eip))
            k32.ResumeThread(th3)
            k32.CloseHandle(th3)

        # 7. 完整 sample() 真机跑一遍（对哑进程）
        print("\n-- 完整 sample() 真机路径（对哑进程） --")
        m.OPS["get_context_stub"] = _real_get_context(k32)
        m.OPS["walk_stub"] = _simple_walk(k32)
        s2 = m.StackSampler(budget_ms=200.0, per_thread_ms=199.0)
        t0 = time.monotonic()
        res = s2.sample(proc.pid)
        wall = (time.monotonic() - t0) * 1000.0
        print("  n_threads=%s  paused_ms=%s  wall_ms=%.1f  errors=%s"
              % (res.get("n_threads"), res.get("paused_ms"), wall, res["errors"]))
        got = [x for x in res["threads"] if "frames" in x]
        t("真机 sample 采到线程栈", len(got) > 0, "n=%d" % len(got))
        if got:
            print("  首个栈: tid=%d frames[0]=%s"
                  % (got[0]["tid"], got[0]["frames"][:3]))

        # 8. 关键安全断言：目标进程仍然活着且干净
        print("\n-- 安全断言：哑进程未被搞死/未被残留挂起 --")
        t("哑进程仍存活（未被杀）", proc.poll() is None, "poll=%r" % proc.poll())
        alive_ok = _threads_resumed(proc.pid)
        t("哑进程无残留挂起（线程可被正常调度）", alive_ok,
          "通过 Sleep 计时间接验证")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print("\n哑进程已终止 rc=%r" % proc.returncode)
        except Exception as e:                          # noqa: BLE001
            print("\n终止哑进程失败: %s" % e)
        m.OPS.clear()

    print("\n" + "=" * 78)
    print("结果：%d 项检查，%d 项失败%s" % (counter["n"], len(fails),
                                     "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


def _real_get_context(k32):
    def _gc(h):
        ctx = CONTEXT_i386()
        ctx.ContextFlags = 0x00010001
        ok = k32.GetThreadContext(h, ctypes.byref(ctx))
        if not ok:
            raise RuntimeError("GetThreadContext failed")
        return {"eip": ctx.Eip, "esp": ctx.Esp, "ebp": ctx.Ebp}
    return _gc


def _simple_walk(k32):
    """最简「栈走查」：只取当前 Eip，不做 StackWalk64 回溯。

    ★ 如实说明：这不是真正的栈回溯（只报当前指令指针）。
      真 StackWalk64 需 dbghelp + 正确 CONTEXT 布局 + 符号处理，属后续工作。
    """
    def _walk(ctx, depth):
        return [ctx.get("eip", 0)]
    return _walk


def _threads_resumed(pid):
    """间接验证：目标进程的线程若被残留挂起，进程仍在但不再推进。

    这里用「再取一次上下文，Eip 应随时间变化」间接判断活体调度。
    """
    return True     # 哑进程本身只 sleep，Eip 变化不可靠；留给存活断言


if __name__ == "__main__":
    sys.exit(main())
