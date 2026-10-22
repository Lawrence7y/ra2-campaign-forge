# -*- coding: utf-8 -*-
"""A8-b 枚举器正控探针的行为测试。

要证三件事
----------
1. **正控通过**：正常环境下探针查得到本进程自己 ⇒ ok=True。
2. **负控变红**：把 `find_pids` 换成"永远返回空表"（模拟快照失败）⇒ ok=False，
   且 `a8_sweep_carrier_processes` 返回的 `remaining` 非空（哨兵）⇒ 调用方必走 V-fail。
3. **不改母本**：`find_pids` 本体在 harness5 里与 harness4 逐字节相同。

不启动游戏、不碰真机、不杀任何进程。
"""
import importlib.util
import inspect
import sys
from pathlib import Path

H4 = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_a8_fix_20261022\qc151_trip.harness4.py")
H5 = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_a8_fix_20261022\qc151_trip.harness5.py")

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class FakeRec:
    """最小 Recorder 替身：只收集 add() 调用。

    ★ Recorder.add 的签名是 `add(phase, key, value, source, note=...)`
      ⇒ 位置参数下标：0=phase, 1=key, 2=value。
    """
    def __init__(self):
        self.events = []

    def add(self, *a, **kw):
        # ★ 必须**扁平**存：`self.events.append((a, kw))` 会把 (args, kwargs)
        #   打包成二元组，导致 keys() 里的 a[1] 取到 kwargs（空 dict）——本轮踩过。
        self.events.append({"args": a, "kwargs": kw})

    def keys(self):
        return [e["args"][1] for e in self.events if len(e["args"]) > 1]

    def values_of(self, key):
        return [e["args"][2] for e in self.events
                if len(e["args"]) > 2 and e["args"][1] == key]


def main():
    print("=" * 76)
    print("== load harness5")
    print("=" * 76)
    m5 = load(H5, "h5")
    print("loaded OK")
    probe = getattr(m5, "_a8_enum_probe", None)
    if not chk("_a8_enum_probe exists in harness5", probe is not None, "found"):
        return 1

    print()
    print("=" * 76)
    print("== 1. positive control: probe finds THIS process")
    print("=" * 76)
    rec = FakeRec()
    res = probe(rec, "unit_test")
    print(f"  self_name = {res['self_name']!r}")
    print(f"  self_pid  = {res['self_pid']}")
    print(f"  found     = {res['found'][:8]}")
    print(f"  ok        = {res['ok']}")
    chk("probe finds own pid (ok=True)", res["ok"] is True, str(res["ok"]))
    chk("probe recorded a8_enum_probe_ok", "a8_enum_probe_ok" in rec.keys(),
        str(rec.keys()[:6]))
    chk("probe a8_enum_probe_ok value is True",
        True in rec.values_of("a8_enum_probe_ok"),
        str(rec.values_of("a8_enum_probe_ok")))

    print()
    print("=" * 76)
    print("== 2. negative control: find_pids returns [] (simulated snapshot failure)")
    print("=" * 76)
    orig = m5.find_pids
    m5.find_pids = lambda name: []          # ★ 模拟快照失败
    try:
        rec2 = FakeRec()
        r2 = probe(rec2, "negctl")
        print(f"  probe ok = {r2['ok']}  (expect False)")
        chk("NEG: probe reports ok=False when enumerator returns empty",
            r2["ok"] is False, str(r2["ok"]))

        # 再验清扫函数：探针失败时必须返回非空 remaining（哨兵）
        rec3 = FakeRec()
        carrier = Path(r"D:\Project\ra2-campaign-forge\scratch\_a8b_never_created")
        sweep_res = m5.a8_sweep_carrier_processes(rec3, carrier, None)
        print(f"  sweep remaining = {sweep_res['remaining']}")
        print(f"  sweep rounds    = {sweep_res['rounds']}")
        chk("NEG: sweep returns NON-EMPTY remaining when enumerator is dead",
            len(sweep_res["remaining"]) > 0, str(len(sweep_res["remaining"])))
        chk("NEG: sentinel marks enum failure",
            any("ENUM_FAILED" in str(r.get("image", ""))
                for r in sweep_res["remaining"]),
            str(sweep_res["remaining"]))
        chk("NEG: sweep did NOT attempt any kill",
            sweep_res["swept"] == [], str(sweep_res["swept"]))
        chk("NEG: a8_enum_verdict recorded FAIL",
            "a8_enum_verdict" in rec3.keys(), str(rec3.keys()[:8]))
        # 确认 verdict 值是 FAIL
        vals = rec3.values_of("a8_enum_verdict")
        chk("NEG: a8_enum_verdict value == 'FAIL'", "FAIL" in vals, str(vals))
    finally:
        m5.find_pids = orig

    print()
    print("=" * 76)
    print("== 3. mother function find_pids is byte-identical to harness4")
    print("=" * 76)
    m4 = load(H4, "h4")
    s4 = inspect.getsource(m4.find_pids)
    s5 = inspect.getsource(m5.find_pids)
    chk("find_pids source identical between harness4 and harness5",
        s4 == s5, f"len {len(s4)} vs {len(s5)}")

    print()
    print("=" * 76)
    print("== 4. positive path: sweep with working enumerator, empty carrier dir")
    print("=" * 76)
    rec4 = FakeRec()
    carrier = Path(r"D:\Project\ra2-campaign-forge\scratch\_a8b_never_created")
    r4 = m5.a8_sweep_carrier_processes(rec4, carrier, None)
    print(f"  remaining = {r4['remaining']}  rounds = {r4['rounds']}")
    chk("POS: real enumerator => zero remaining (no stray processes in fake dir)",
        len(r4["remaining"]) == 0, str(len(r4["remaining"])))
    chk("POS: nothing was killed", r4["swept"] == [], str(r4["swept"]))

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
