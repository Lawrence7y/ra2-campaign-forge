from pathlib import Path

root = Path(__file__).resolve().parent
c = root / 'candidate'
p = c / '_drive_c2_x_e12.py'
s = p.read_text(encoding='utf-8')
s = s.replace('import json\n', 'import json\nimport math\n')
s = s.replace('EXCEPT_CHECK_EVERY_S = 30.0', 'BOOT_TOLERANCE_MS = 2000\nEXCEPT_CHECK_EVERY_S = 30.0')
s = s.replace('def _r_boot_ms():', '_k32.GetTickCount64.restype = ctypes.c_ulonglong\n_k32.GetTickCount64.argtypes = []\n\n\ndef _r_boot_ms():')
s = s.replace('    V2.OPS["boot_ms"] = _r_boot_ms', '    V2.OPS["boot_ms"] = _r_boot_ms\n    V2.OPS["wallclock_ms"] = lambda: time.time_ns() // 1_000_000')
anchor = '# E2 纯函数（自检套件分臂直测）\n'
helper = '''def capture_boot():
    """Read both clocks at each boundary; keep the batch reference immutable.

    Wall-clock corrections beyond the tolerance conservatively stop the batch.
    This is a session guard, not an authentication-quality boot identifier.
    """
    wall = V2.OPS["wallclock_ms"]()
    uptime = V2.OPS["boot_ms"]()
    if (isinstance(wall, bool) or isinstance(uptime, bool)
            or not isinstance(wall, (int, float)) or not isinstance(uptime, (int, float))
            or not math.isfinite(wall) or not math.isfinite(uptime) or uptime < 0):
        raise V2.TripFail("boot_clock_invalid")
    return {"boot_ms": uptime, "wallclock_ms": wall,
            "boot_wallclock_ms": wall - uptime}


def assert_same_boot(current, reference):
    if (not isinstance(reference, dict) or "boot_wallclock_ms" not in reference
            or not isinstance(reference["boot_wallclock_ms"], (int, float))
            or isinstance(reference["boot_wallclock_ms"], bool)
            or not math.isfinite(reference["boot_wallclock_ms"])):
        raise V2.TripFail("boot_reference_invalid")
    if abs(current["boot_wallclock_ms"] - reference["boot_wallclock_ms"]) > BOOT_TOLERANCE_MS:
        raise V2.TripFail("stop_condition:boot_changed_between_trips(%s!=%s)"
                          % (current["boot_wallclock_ms"], reference["boot_wallclock_ms"]))


'''
s = s.replace(anchor, anchor + helper)
s = s.replace('for seam in ("process_times", "boot_ms"):', 'for seam in ("process_times", "boot_ms", "wallclock_ms"):')
old = '''        rec["boot_ms_at_start"] = V2.OPS["boot_ms"]()
        if boot_ref is not None and rec["boot_ms_at_start"] != boot_ref.get("boot_ms"):
            raise V2.TripFail("stop_condition:boot_changed_between_trips(%s≠%s)"
                              % (rec["boot_ms_at_start"], boot_ref.get("boot_ms")))'''
new = '''        boot_current = capture_boot()
        rec["boot_ms_at_start"] = boot_current["boot_ms"]
        rec["wallclock_ms_at_start"] = boot_current["wallclock_ms"]
        rec["boot_wallclock_ms_at_start"] = boot_current["boot_wallclock_ms"]
        rec["boot_reference"] = dict(boot_ref) if isinstance(boot_ref, dict) else boot_ref
        rec["boot_tolerance_ms"] = BOOT_TOLERANCE_MS
        if boot_ref is not None:
            assert_same_boot(boot_current, boot_ref)'''
assert old in s
s = s.replace(old, new)
s = s.replace('boot_ref = {"boot_ms": V2.OPS["boot_ms"]()}', 'boot_ref = capture_boot()')
s = s.replace('BOOT(GetTickCount64)=%d ms——发射批次须同值复核对（同会话断言）', 'UPTIME(GetTickCount64)=%d ms——批次比较开机墙钟估计，容差2000ms')
p.write_text(s, encoding='utf-8', newline='\n')

p = c / '_drive_c2_x_e12_selftest.py'
s = p.read_text(encoding='utf-8')
s = s.replace('return 5000001 if mode == "boot_change" else 5000000', 'return (5000000 if mode != "boot_change" else 1000) + int(st["t"] * 1000)')
s = s.replace('"process_times": process_times, "boot_ms": boot_ms,', '"process_times": process_times, "boot_ms": boot_ms,\n        "wallclock_ms": lambda: 1700000000000 + int(st["t"] * 1000),')
s = s.replace('boot_ref={"boot_ms": 111111}', 'boot_ref={"boot_ms": 6000000, "boot_wallclock_ms": 1699994997000}')
s = s.replace('boot_ref={"boot_ms": 5000000}', 'boot_ref={"boot_ms": 6000000, "boot_wallclock_ms": 1699995000000}')
s = s.replace('跨趟 BOOT 读数变化 ⇒ 停', '跨趟开机墙钟估计超容差 ⇒ 停')
s = s.replace('boot_change 形态同样被拦（读数≠参考即停，无方向假设）', '重启形态开机墙钟变化同样被拦')
old = '''        ("boot_assert", 'if boot_ref is not None and rec["boot_ms_at_start"] != boot_ref.get("boot_ms"):',
         'if boot_ref is None and rec["boot_ms_at_start"] != boot_ref.get("boot_ms"):', "hang",
         {"__boot_ref": {"boot_ms": 111111}},'''
new = '''        ("boot_assert", 'if abs(current["boot_wallclock_ms"] - reference["boot_wallclock_ms"]) > BOOT_TOLERANCE_MS:',
         'if False:', "hang",
         {"__boot_ref": {"boot_ms": 6000000, "boot_wallclock_ms": 1699994997000}},'''
assert old in s
s=s.replace(old,new)
# A failing setup must retain the underlying failure, not mask it with a KeyError.
s=s.replace('    tl, st = load_tl(r), _st(r, ops)', '    if r.get("verdict") != "OK":\n        print("FIRST_TRIP_FAILURE=" + json.dumps(r, ensure_ascii=False))\n        return 1\n    tl, st = load_tl(r), _st(r, ops)',1)
s=s.replace('    # ---------- G 组 冻结件零写入 ----------', '    _boot_regressions()\n\n    # ---------- G 组 冻结件零写入 ----------')
addition = '''
def _boot_regressions():
    # Run the actual trip twice with one immutable reference and advancing clocks.
    ops = make_ops("hang")
    state = ops["__st"]
    saved = _install(ops, D.V2)
    try:
        ref = D.capture_boot()
        before = dict(ref)
        r1 = D.run_trip(901, ref, watch_s=3.0)
        state["t"] += 137.0
        state["launched"] = False
        state["killed"] = False
        state["t_close"] = None
        r2 = D.run_trip(902, ref, watch_s=3.0)
        check("BOOT-01", "推进时钟同会话双趟实际运行均OK", r1["verdict"] == r2["verdict"] == "OK", (r1.get("fail"),r2.get("fail")))
        check("BOOT-02", "两趟原始uptime递增且批次参考不变", r2["boot_ms_at_start"] > r1["boot_ms_at_start"] and ref == before, ref)
        # New uptime epoch: the second capture must stop before popen.
        state["launched"] = False
        ops["boot_ms"] = lambda: 1000
        D.V2.OPS["boot_ms"] = ops["boot_ms"]
        rr = D.run_trip(903, ref, watch_s=3.0)
        check("BOOT-03", "重启反例实际trip在发射前被拦", rr["verdict"] == "FAIL" and "boot_changed" in rr.get("fail", "") and not state["launched"], rr.get("fail"))
    finally:
        _uninstall(saved)
    for delta in (-2001, -2000, 0, 2000, 2001):
        blocked = _raises(lambda: D.assert_same_boot({"boot_ms": 99, "boot_wallclock_ms": 10000+delta}, {"boot_ms": 1, "boot_wallclock_ms": 10000}), D.V2.TripFail)
        check("BOOT-T%s" % delta, "容差边界双向精确判据", blocked == (abs(delta)>2000), delta)
    for ref in ({}, {"boot_wallclock_ms": float("nan")}, {"boot_wallclock_ms": True}):
        check("BOOT-REF%s" % repr(ref), "无效参考保守拒绝", _raises(lambda: D.assert_same_boot({"boot_wallclock_ms": 0}, ref), D.V2.TripFail))
    # Compile mutations in memory. Exercise the actual comparison, not a duplicate oracle.
    src = DRIVER_PATH.read_text(encoding="utf-8")
    start = src.index("def assert_same_boot(")
    end = src.index("def cpu_delta(", start)
    fn = src[start:end]
    anchor = 'if abs(current["boot_wallclock_ms"] - reference["boot_wallclock_ms"]) > BOOT_TOLERANCE_MS:'
    for name, replacement in (("RAW", 'if current["boot_ms"] != reference["boot_ms"]:'), ("BYPASS", 'if False:')):
        assert fn.count(anchor) == 1
        ns = {"V2": D.V2, "math": __import__("math"), "BOOT_TOLERANCE_MS": D.BOOT_TOLERANCE_MS}
        exec(compile(fn.replace(anchor, replacement), "boot_mut_"+name, "exec"), ns)
        guard = ns["assert_same_boot"]
        same = not _raises(lambda: guard({"boot_ms": 200000, "boot_wallclock_ms": 10000}, {"boot_ms": 1000, "boot_wallclock_ms": 10000}), D.V2.TripFail)
        reboot = _raises(lambda: guard({"boot_ms": 1000, "boot_wallclock_ms": 40000}, {"boot_ms": 1000, "boot_wallclock_ms": 10000}), D.V2.TripFail)
        check("BOOT-MUT-"+name, "旧raw比较或删检查均被正反例抓红", not(same and reboot), (same,reboot))


'''
s=s.replace('run_suite = main_suite', addition+'run_suite = main_suite')
p.write_text(s,encoding='utf-8',newline='\n')
