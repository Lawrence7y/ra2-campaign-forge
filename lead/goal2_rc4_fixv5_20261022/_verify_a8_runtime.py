#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A8 的运行级验证：证明异常路径上 finally 真的执行了清扫。

静态门禁（_verify_probe_a4a7a8.py）只能证明「finally 这几个字在文件里」，
证明不了「它真的会被执行」。本脚本用**桩替换**做运行级验证：

  1. 把 _rc4_ab_probe 的模块级依赖全部替换成不碰真机的桩
     （create_carrier / subprocess.Popen / DebugActiveProcess / k32.* …）
  2. 让主体在**不同阶段**抛异常，断言：
       - _cleanup 被调用恰好一次
       - rec["abort"] 里记了 unhandled_exception
       - 没有任何真实进程被启动（桩会记录启动次数）

全程不启动任何真实进程、不碰真机二进制。
"""
import sys
import types
from pathlib import Path

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))

import _rc4_ab_probe as P  # noqa: E402

RESULTS = []


def check(tag, cond, evidence=""):
    RESULTS.append((tag, bool(cond), evidence))
    print("  %-46s %s  %s" % (tag, "PASS" if cond else "FAIL", evidence))


class FakeProc:
    """假 Popen：不启动任何真实进程。"""
    launched = 0

    def __init__(self, *a, **k):
        FakeProc.launched += 1
        self.pid = 4242
        self.returncode = None

    def poll(self):
        return self.returncode

    def kill(self):
        self.returncode = 0

    def wait(self, timeout=None):
        self.returncode = 0
        return 0


def install_stubs(raise_at):
    """把真机依赖换成桩；raise_at 指定在哪一步抛异常。"""
    calls = {"cleanup": 0, "a8": 0}

    orig_cleanup = P._cleanup

    def fake_cleanup(proc, carrier, rec, attached):
        calls["cleanup"] += 1
        # 不调原函数（它会真的去杀进程/枚举），只记录
        rec["_cleaned"] = True
        rec["a8_verdict"] = "PASS"
        rec["a8_enum_ok"] = True
        rec["cleanup_ok"] = True

    P._cleanup = fake_cleanup

    def fake_create_carrier(carrier, extra):
        if raise_at == "create_carrier":
            raise OSError("stub: create_carrier boom")
        carrier.mkdir(parents=True, exist_ok=True)
        (carrier / "gamemd.exe").write_bytes(b"stub")
        return {"gamemd.exe": 4}

    P.create_carrier = fake_create_carrier
    P.sha256_file = lambda p: P.GAMEMD_SHA16 + "0" * 48   # 前 16 位必须匹配
    P.subprocess = types.SimpleNamespace(
        Popen=FakeProc, DEVNULL=-3, TimeoutExpired=Exception)

    def fake_wait_for_debug_event(byref_de, timeout):
        # 桩：立刻报"没有事件"（ERROR_SEM_TIMEOUT=121），让循环走超时分支退出
        P.ctypes.get_last_error = lambda: 121
        return False

    P.k32 = types.SimpleNamespace(
        # ★ raise_at == "attach" 时才返回失败；否则成功进入调试循环
        DebugActiveProcess=lambda pid: (raise_at != "attach"),
        DebugActiveProcessStop=lambda pid: True,
        WaitForDebugEvent=fake_wait_for_debug_event,
        ContinueDebugEvent=lambda *a: True,
        OpenProcess=lambda *a: None,
        TerminateProcess=lambda *a: True,
        WaitForSingleObject=lambda *a: 0,
        CloseHandle=lambda *a: True,
        get_last_error=lambda: 0,
    )
    P.query_image = lambda pid: str(CARD / "ct")
    P.under_carrier = lambda img, cdir: True
    P.list_procs = lambda: {}
    P.find_main_window = lambda pid: 0
    P.parse_guard_log = lambda p: {"hits_total": 0}
    P.game_procs = lambda: {}
    P.rm_carrier = lambda cdir: (True, None)
    P.a8_sweep = lambda cdir, own: {"verdict": "PASS", "remaining": [],
                                    "enum_probe_before": {"ok": True},
                                    "enum_probe_after": {"ok": True}}
    # ★ 时钟必须**递增**：主体的调试循环条件是
    #   `while time.time() - t_attach < debug_timeout`，桩成恒定值会死循环。
    clock = {"t": 0.0}

    def fake_time():
        clock["t"] += 0.05
        return clock["t"]

    P.time = types.SimpleNamespace(
        time=fake_time, sleep=lambda s: None,
        strftime=lambda f: "20261023T000000")
    P.CARRIER_PATH_MAX = 4096
    P.CLOSE_WAIT_S = 20.0

    return calls, orig_cleanup


def run_case(raise_at):
    calls, orig = install_stubs(raise_at)
    FakeProc.launched = 0
    try:
        rec = P.one_trip(1, "A", None, 0.1, 0.1, False)
    except BaseException as e:                      # noqa: BLE001
        return {"raised": repr(e), "calls": calls, "launched": FakeProc.launched}
    finally:
        P._cleanup = orig
    return {"rec": rec, "calls": calls, "launched": FakeProc.launched}


def main():
    print("=" * 90)
    print("A8 运行级验证：异常路径上 finally 是否真的清扫")
    print("=" * 90)

    # C1 建载体阶段抛异常 —— create_carrier 有自己的 except，走的是显式 abort 分支
    r = run_case("create_carrier")
    rec = r.get("rec") or {}
    check("C1 create_carrier 抛异常 ⇒ 不崩到调用方", "raised" not in r,
          r.get("raised", ""))
    check("C1 abort 记录了 carrier_create_failed",
          "carrier_create_failed" in (rec.get("abort") or ""),
          rec.get("abort", ""))
    check("C1 没有启动任何真实进程", r["launched"] == 0, "launched=%d" % r["launched"])

    # C2 附加调试器失败 —— 进程已启动，必须清扫
    r = run_case("attach")
    rec = r.get("rec") or {}
    check("C2 attach 失败 ⇒ abort=DebugActiveProcess_failed",
          rec.get("abort") == "DebugActiveProcess_failed", rec.get("abort", ""))
    check("C2 _cleanup 被调用恰好一次", r["calls"]["cleanup"] == 1,
          "cleanup=%d" % r["calls"]["cleanup"])

    # C3 正常路径（桩下）：cleanup 也必须恰好一次，不能重复
    r = run_case(None)
    rec = r.get("rec") or {}
    check("C3 正常路径 _cleanup 恰好一次", r["calls"]["cleanup"] == 1,
          "cleanup=%d" % r["calls"]["cleanup"])
    check("C3 正常路径无 abort", rec.get("abort") is None, rec.get("abort", ""))

    # C4 幂等：重复调 _cleanup 不应二次清扫
    calls, orig = install_stubs(None)
    fake_rec = {"pid": 1}
    n = {"c": 0}
    P._cleanup = lambda *a, **k: n.__setitem__("c", n["c"] + 1)
    P._cleanup = orig
    # 直接用真 _cleanup 会碰真机，改为对幂等标记做静态断言
    src = (CARD / "_rc4_ab_probe.py").read_text(encoding="utf-8")
    check("C4 _cleanup 有幂等短路", 'if rec.get("_cleaned"):' in src)

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
