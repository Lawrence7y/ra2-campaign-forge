#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A8 运行级验证 v2：证明**启动后异常逃出主体**时 finally 真的清扫。

★★ v1 的致命缺陷（由异族复核员发现）：
   三个用例无一命中 A8 的原始缺陷场景 —— "启动后、主体内部抛异常"。
   - C1 在 create_carrier 抛，被主体自己的 except 吞掉（走显式 abort 分支）
   - C2/C3 走正常 return
   ⇒ 把 one_trip 改成**完全没有 try/finally**，v1 仍然 8/8 PASS。
   即：v1 对目标缺陷**零敏感度**。

v2 的修正：
  1. **主用例必须是"启动后、主体内部抛异常"**，异常点在
     `rec["guard"] = parse_guard_log(...)` 之前（此时进程已起、调试器已附加）。
  2. **负控**：把 one_trip 的 try/finally 整个去掉，断言必须转红。
     这是判定门禁是否有效的唯一标准。
  3. 每个用例都断言 `_cleanup` 的**调用次数**，不只断言"没崩"。

全程不启动任何真实进程、不碰真机二进制（桩替换）。
"""
import ast
import sys
import types
from pathlib import Path

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))

SRC_TEXT = (CARD / "_rc4_ab_probe.py").read_text(encoding="utf-8")

RESULTS = []


def check(tag, cond, evidence=""):
    RESULTS.append((tag, bool(cond), evidence))
    print("  %-50s %s  %s" % (tag, "PASS" if bool(cond) else "FAIL", evidence))
    return bool(cond)


class FakeProc:
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


def build_stubs(P, raise_at):
    """把真机依赖全换成桩。raise_at 指定异常注入点。"""
    calls = {"cleanup": 0}
    real_cleanup = P._cleanup

    def fake_cleanup(proc, carrier, rec, attached):
        calls["cleanup"] += 1
        rec["_cleaned"] = True
        rec["a8_verdict"] = "PASS"
        rec["a8_enum_ok"] = True
        rec["cleanup_ok"] = True

    P._cleanup = fake_cleanup

    def fake_create_carrier(carrier, extra):
        carrier.mkdir(parents=True, exist_ok=True)
        (carrier / "gamemd.exe").write_bytes(b"stub")
        return {"gamemd.exe": 4}

    P.create_carrier = fake_create_carrier
    P.sha256_file = lambda p: P.GAMEMD_SHA16 + "0" * 48
    P.subprocess = types.SimpleNamespace(
        Popen=FakeProc, DEVNULL=-3, TimeoutExpired=Exception)

    def fake_wait_for_debug_event(byref_de, timeout):
        P.ctypes.get_last_error = lambda: 121
        return False

    P.k32 = types.SimpleNamespace(
        DebugActiveProcess=lambda pid: True,
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
    P.game_procs = lambda: {}
    P.rm_carrier = lambda cdir: (True, None)
    P.a8_sweep = lambda cdir, own: {"verdict": "PASS", "remaining": [],
                                    "enum_probe_before": {"ok": True},
                                    "enum_probe_after": {"ok": True}}

    # ★★ 关键：异常注入点在**主体内部、进程已起之后**。
    #   parse_guard_log 在主体末尾，此时 pid 已设、调试器已附加。
    def fake_parse_guard_log(p):
        if raise_at == "after_launch":
            raise RuntimeError("stub: boom after launch")
        return {"hits_total": 0}

    P.parse_guard_log = fake_parse_guard_log

    clock = {"t": 0.0}

    def fake_time():
        clock["t"] += 0.05
        return clock["t"]

    P.time = types.SimpleNamespace(
        time=fake_time, sleep=lambda s: None,
        strftime=lambda f: "20261023T000000")
    P.CARRIER_PATH_MAX = 4096
    P.CLOSE_WAIT_S = 20.0
    return calls, real_cleanup


def run_case(raise_at, patch_shell=None):
    """跑一趟；patch_shell 用于负控（把 one_trip 换成无 finally 版本）。

    ★★ 必须把 CARD 指向临时目录：主体会 `CARD/ab_*_t1/ct/...` 建载体，
      跑在真实 CARD 上会在仓库里留下 stub gamemd.exe（v1 就这样污染过仓库）。
    """
    import importlib
    import tempfile
    import _rc4_ab_probe as P
    importlib.reload(P)

    orig_one_trip = P.one_trip
    if patch_shell is not None:
        P.one_trip = patch_shell(P)

    calls, real = build_stubs(P, raise_at)
    FakeProc.launched = 0
    tmp = tempfile.mkdtemp(prefix="a8rt_")
    old_card = P.CARD
    P.CARD = Path(tmp)
    try:
        rec = P.one_trip(1, "A", None, 0.1, 0.1, False)
        raised = None
    except BaseException as e:                      # noqa: BLE001
        rec, raised = None, repr(e)
    finally:
        P._cleanup = real
        P.one_trip = orig_one_trip
        P.CARD = old_card
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return {"rec": rec, "raised": raised, "calls": calls,
            "launched": FakeProc.launched}


def no_finally_shell(P):
    """负控：完全去掉 try/finally，异常直接逃出去（v1 对这种实现仍判 PASS）。"""
    def one_trip(idx, arm, dll_name, hold_s, debug_timeout, keep_dump):
        state = {"proc": None, "carrier": None, "rec": None}
        return P._one_trip_body(idx, arm, dll_name, hold_s, debug_timeout,
                                keep_dump, state)
    return one_trip


def main():
    print("=" * 92)
    print("A8 运行级验证 v2（v1 对目标缺陷零敏感度，本版把异常注入到主体内部）")
    print("=" * 92)

    # ---- 正控：主体内部抛异常 ----
    print()
    print("--- 正控：启动后、主体内部抛异常 ---")
    r = run_case("after_launch")
    rec = r["rec"] or {}
    check("P1 进程确实启动了（证明异常在启动之后）",
          r["launched"] == 1, "launched=%d" % r["launched"])
    check("P1 异常未逃出 one_trip（外壳兜住）",
          r["raised"] is None, r["raised"] or "")
    check("P1 abort 记录了 unhandled_exception",
          "unhandled_exception" in (rec.get("abort") or ""),
          (rec.get("abort") or "")[:70])
    check("P1 _cleanup 被调用恰好一次（finally 生效）",
          r["calls"]["cleanup"] == 1, "cleanup=%d" % r["calls"]["cleanup"])

    # ---- 负控：去掉 finally，同一用例必须转红 ----
    print()
    print("--- 负控：把 one_trip 的 try/finally 整个去掉 ---")
    r2 = run_case("after_launch", patch_shell=no_finally_shell)
    rec2 = r2["rec"] or {}
    check("N1 无 finally 时异常逃出 one_trip",
          r2["raised"] is not None, (r2["raised"] or "")[:60])
    check("N1 无 finally 时 _cleanup 未被调用（证明断言有敏感度）",
          r2["calls"]["cleanup"] == 0, "cleanup=%d" % r2["calls"]["cleanup"])

    # ★ 这条是整个门禁的有效性证明：
    #   同一注入点下，"有 finally" 与 "无 finally" 的 cleanup 次数必须不同。
    check("N1 门禁对 finally 有敏感度（1 vs 0）",
          r["calls"]["cleanup"] == 1 and r2["calls"]["cleanup"] == 0,
          "有 finally=%d / 无 finally=%d"
          % (r["calls"]["cleanup"], r2["calls"]["cleanup"]))

    # ---- 正常路径不重复清扫 ----
    print()
    print("--- 正常路径 ---")
    r3 = run_case(None)
    rec3 = r3["rec"] or {}
    check("P2 正常路径 _cleanup 恰好一次",
          r3["calls"]["cleanup"] == 1, "cleanup=%d" % r3["calls"]["cleanup"])
    check("P2 正常路径无 abort", rec3.get("abort") is None,
          rec3.get("abort") or "")

    # ---- 幂等：源码级（用 AST 断言，不用裸子串） ----
    print()
    print("--- 幂等（AST）---")
    tree = ast.parse(SRC_TEXT)
    cu = [n for n in tree.body
          if isinstance(n, ast.FunctionDef) and n.name == "_cleanup"][0]
    body_src = ast.get_source_segment(SRC_TEXT, cu) or ""
    check("P3 _cleanup 有幂等短路（函数体内）",
          'if rec.get("_cleaned"):' in body_src, "")
    check("P3 幂等标记在清扫动作之前",
          body_src.find('rec["_cleaned"] = True') != -1
          and body_src.find('rec["_cleaned"] = True')
          < body_src.find("a8_sweep("),
          "标记位置 < a8_sweep 位置")

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    if npass != len(RESULTS):
        print("失败项：")
        for t, c, e in RESULTS:
            if not c:
                print("  - %s  %s" % (t, e))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
