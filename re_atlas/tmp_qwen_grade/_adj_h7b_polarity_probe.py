import ast
import importlib.util
import sys

V = "D:/Project/ra2-campaign-forge/lead/goal1_harness7_20261023/_verify_h7_behavior.py"
spec = importlib.util.spec_from_file_location("vh7", V)
vh7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh7)
src = vh7.H7.read_text(encoding="utf-8")

anchor = 'if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:'
flip = 'if _h7_nav_end is not None and not _H7_STATE["fs_rect_wait_skipped"]:'


def run_suite(mutated_src, tag):
    vh7.results.clear()
    tree = vh7.parse(mutated_src)
    limit = vh7.const_assign(tree, "H7_MEASURE_MAX_NAV_TO_W0_S")
    dl_kind, dl_val = vh7.deadline_assigned_value(tree)
    while_node = vh7.find_while_rect_wait(tree)
    op, op_ok = vh7.late_gate_compare(tree)
    g_nav_end, g_skip = vh7.late_gate_guard(tree)
    checks = []
    checks.append(("E0a", limit is not None))
    checks.append(("E0b", dl_kind == "const"))
    checks.append(("E0c", while_node is not None))
    checks.append(("E0d", op_ok))
    checks.append(("E0e", g_nav_end))
    checks.append(("E0f", g_skip))
    print(f"{tag}: E0 guards = (nav_end={g_nav_end}, skip={g_skip})")
    if not all(v for _, v in checks):
        print(f"{tag}: ABORT at E0 (suite would exit 1)")
        return
    ml = vh7.model_late
    checks.append(("E4a", ml(0.3, limit, op, g_nav_end, g_skip) is False))
    checks.append(("E4b", ml(130.0, limit, op, g_nav_end, g_skip) is True))
    checks.append(("E4c", ml(126.187, limit, op, g_nav_end, guard_skip=False) is False))
    checks.append(("E4d", ml(130.688, limit, op, g_nav_end, guard_skip=False) is False))
    checks.append(("E4e", ml(130.688, limit, op, g_nav_end, guard_skip=True) is True))
    m1 = mutated_src.replace(
        "            _h7_deadline_orig = deadline\n            deadline = 0.0",
        "            _h7_deadline_orig = deadline\n            deadline = deadline")
    if m1 != mutated_src:
        k1, v1 = vh7.deadline_assigned_value(vh7.parse(m1))
        checks.append(("M1", vh7.model_rect_wait(k1, v1, True, (2560, 1440)) > 0))
    else:
        checks.append(("M1-locate", False))
    m2 = mutated_src.replace("H7_MEASURE_MAX_NAV_TO_W0_S = 90.0",
                             "H7_MEASURE_MAX_NAV_TO_W0_S = 1e9")
    if m2 != mutated_src:
        lim2 = vh7.const_assign(vh7.parse(m2), "H7_MEASURE_MAX_NAV_TO_W0_S")
        checks.append(("M2", ml(130.0, lim2, op, g_nav_end, g_skip) is False))
    else:
        checks.append(("M2-locate", False))
    m2b = mutated_src.replace(anchor, "if _h7_nav_end is not None:")
    if m2b != mutated_src:
        gn2, gs2 = vh7.late_gate_guard(vh7.parse(m2b))
        checks.append(("M2b", ml(126.187, limit, op, gn2, guard_skip=False) is True
                       or not gs2))
    else:
        checks.append(("M2b-locate", False))
    m3 = mutated_src.replace("_h7_late = bool(_h7_n2m > H7_MEASURE_MAX_NAV_TO_W0_S)",
                             "_h7_late = bool(_h7_n2m >= H7_MEASURE_MAX_NAV_TO_W0_S)")
    if m3 != mutated_src:
        op3, ok3 = vh7.late_gate_compare(vh7.parse(m3))
        checks.append(("M3", ok3 and ml(limit, limit, op3, g_nav_end, g_skip) is True))
        checks.append(("M3-ctrl", ml(limit, limit, op, g_nav_end, g_skip) is False))
    else:
        checks.append(("M3-locate", False))
    checks.append(("E5a", '_h7_payload["verdict"] = "late_start"' in mutated_src))
    checks.append(("E5b", ('rec.add("MEASURE", "verdict", "late_start", '
                           '"script:_measure_run"') in mutated_src))
    failed = [n for n, v in checks if not v]
    print(f"{tag}: {len(checks) - len(failed)}/{len(checks)} key checks pass; "
          f"FAILED={failed}")


print("anchor count in pristine:", src.count(anchor))
run_suite(src, "PRISTINE")
mC = src.replace(anchor, flip)
assert mC != src, "flip mutation did not hit"
run_suite(mC, "POLARITY-FLIPPED")
