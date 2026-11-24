# -*- coding: utf-8 -*-
"""_ec_s3_controls.py — 第三步：9 件已知样本正反控 + 9 件编排方未列过的新样本（过拟合检验）。
判据模块经 importlib 以绝对路径加载（兼容 python -I）。只读被检脚本。
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # 仓库根（写域在 lead/ 下一层）

spec = importlib.util.spec_from_file_location(
    "_ec_criterion", os.path.join(HERE, "_ec_criterion.py"))
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)

CONTROLS = [
    # —— 正控（应 GATE+OK）：四件 d2x 门禁
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    # —— 反控
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",            # CONSTANT_EXIT → GATE+E1 FAIL
    "lead/re_line_20261105/D21_RULING/_d21_burden5.py",   # 零出口 stdout-only → PROBE
    "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py",
    "lead/re_line_20261105/_leader/_a7_acf_probe.py",     # 零出口+真写盘 → ARTIFACT
    "lead/re_line_20261105/_leader/_intra_frame_census.py",
]

FRESH = [
    # CONDITIONAL_EXIT + reads_conjunction（预期 GATE）
    "lead/dtrigger_compare_20261107/_check_dtrigger.py",
    "lead/w2_samecause_20261109/_w2w_fp9.py",
    # CONSTANT_EXIT [0]（预期 GATE + E1 FAIL）
    "lead/bexec_n4_20261108/_n4_ast_scan.py",
    "lead/check_masking_20261109/_cm_inject.py",
    # NO_EXIT：产物形态待判（ARTIFACT/PROBE/GATE 均有可能）
    "lead/advset_indep_20261109/_ai2_selfcheck2.py",
    "lead/a_dim_reduced_20261108/_verify_hy4_recompute.py",
    "lead/chain_vs_single_20261109/_cs_attrib.py",
    "lead/cert_realcheck_20261109/_cr_real_verify.py",
    "lead/check_family_20261109/_cf_compose_lineage.py",
]


def run(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    r = EC.analyze_file(p, rel)
    print("=" * 90)
    print("[%s] %s" % (r["verdict"], rel))
    print("   class=%s  facts=%s" % (r["class"], json.dumps(r["facts"], ensure_ascii=False)))
    for code, loc, detail in r["reasons"]:
        print("   %-7s %-58s %s" % (code, loc, detail[:170]))
    return r


def main():
    results = []
    print("########## 已知 9 件（正反控） ##########")
    for rel in CONTROLS:
        results.append(run(rel))
    print()
    print("########## 新样本 9 件（编排方未列，过拟合检验） ##########")
    for rel in FRESH:
        results.append(run(rel))
    print("=" * 90)
    print("%-4s %-10s %-14s %s" % ("verdict", "class", "E1/E2/E3/E4", "rel"))
    for r in results:
        e = r["e"]
        efmt = "/".join(str(e.get(k, "-"))[0] for k in ("E1", "E2", "E3", "E4")) if e else "-"
        print("%-10s %-10s %-14s %s" % (r["verdict"], r["class"], efmt, r["rel"]))
    out = os.path.join(HERE, "_ec_s3_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("\n结果已写 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
