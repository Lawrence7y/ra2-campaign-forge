# -*- coding: utf-8 -*-
r"""_n13_migration_check.py — 迁移配方粘贴实跑：改前 3 行 → 改后 5 行

验证三件事：
  U1 调用方接口不变：P 仍是 list，问题串仍是 '含越权断言 <token>' 家族，
     ok = not P 的字典输出形状不变。
  U2 朴素字面门禁在真件上 FAIL（2 条），谓词化门禁在真件上 PASS（A/B/C 全放过）。
  U3 降级形态：删掉/找不到谓词模块（ImportError）时退回朴素字面全拦，
     绝不静默 PASS（宁可误拦不可放过）；且真断言仍被抓住。
"""

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
PUB = ROOT / "lead" / "ledger_bound_20261109" / "LEDGER_BOUND_VOLUME.md"
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def gate(t, mode):
    """mode = 'before'（改前 3 行）| 'after'（改后 5 行）| 'degraded'（导入失败）"""
    P = []
    if mode == "before":
        # ---- 改前 3 行（既有朴素字面门禁，_dnv_gate.py:14-15） ----
        for bad in ['已入账', '已追加', '已生效']:
            if bad in t:
                P.append('含越权断言 ' + bad)
    elif mode in ("after", "degraded"):
        # ---- 改后 5 条语句（迁移配方；except 覆盖真删文件的 OSError） ----
        try:
            import importlib.util as _u
            import pathlib as _p
            if mode == "degraded":
                raise ImportError("模拟谓词模块缺失/删文件")
            if not (N13.is_file() and G7.is_file()):
                raise ImportError("谓词模块文件缺失")
            _s = _u.spec_from_file_location('_n13', str(N13)); _m = _u.module_from_spec(_s); _s.loader.exec_module(_m)
            _g = _u.spec_from_file_location('_g7', str(G7)); _g7 = _u.module_from_spec(_g); _g.loader.exec_module(_g7)
            for _p in _m.r13_assertions(t, ['已入账', '已追加', '已生效'], r10_scan=_g7.r10_scan, r12_scan=_g7.r12_scan)[0]:
                P.append(_p)
        except (ImportError, OSError, AttributeError):
            for bad in ['已入账', '已追加', '已生效']:
                if bad in t:
                    P.append('含越权断言 ' + bad)   # 降级：字面全拦，不放过
    return {"ok": not P, "problems": P}


def main():
    text = PUB.read_text(encoding="utf-8")
    checks = []

    r_before = gate(text, "before")
    r_after = gate(text, "after")
    r_degraded = gate(text, "degraded")

    checks.append(("U1 接口形状一致",
                   all(set(r.keys()) == {"ok", "problems"} and isinstance(r["problems"], list)
                       and isinstance(r["ok"], bool)
                       for r in (r_before, r_after, r_degraded)),
                   "三形态均返回 {ok:bool, problems:list}"))
    checks.append(("U2 改前 FAIL", r_before["ok"] is False and len(r_before["problems"]) == 2,
                   json.dumps(r_before, ensure_ascii=False)))
    checks.append(("U2 改后 PASS", r_after["ok"] is True and len(r_after["problems"]) == 0,
                   json.dumps(r_after, ensure_ascii=False)))
    checks.append(("U3 降级形态不静默 PASS",
                   r_degraded["ok"] is False and len(r_degraded["problems"]) == 2,
                   json.dumps(r_degraded, ensure_ascii=False)))

    # 真断言在 after 形态下必须被抓住（不放宽判据）
    t_bad = "未验：本笔已入账\ngrep 结果：此笔已入账\n§2 清单 / 该条已入账 / §3 依赖"
    r_bad = gate(t_bad, "after")
    checks.append(("U4 真断言仍被抓住（含复核 ④ 的三族漏网）",
                   r_bad["ok"] is False and len(r_bad["problems"]) >= 3,
                   json.dumps(r_bad, ensure_ascii=False)))

    # U5：真删文件（非 raise ImportError）也必须干净 FAIL，不能抛未捕获 OSError
    import shutil
    hidden = ROOT / "lead" / "gate_n13_20261109" / "_n13_hidden_for_u5.py"
    moved = False
    try:
        shutil.move(str(N13), str(hidden))
        moved = True
        try:
            r_del = gate(text, "after")
            checks.append(("U5 真删谓词模块后干净 FAIL（不崩溃）",
                           r_del["ok"] is False and len(r_del["problems"]) == 2,
                           json.dumps(r_del, ensure_ascii=False)))
        except Exception as e:
            checks.append(("U5 真删谓词模块后干净 FAIL（不崩溃）", False,
                           "未返回字典，抛出 %s: %s" % (type(e).__name__, e)))
    finally:
        if moved:
            shutil.move(str(hidden), str(N13))

    for cid, ok, detail in checks:
        print(("PASS" if ok else "FAIL"), cid, "|", detail)
    all_pass = all(c[1] for c in checks)
    print("MIGRATION_ALL_PASS =", all_pass)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
