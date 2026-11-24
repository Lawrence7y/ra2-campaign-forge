# -*- coding: utf-8 -*-
"""_ecv_compare.py — 复核员比对 harness：
同一文件分别跑 [设计员判据 _ec_criterion] 与 [复核员独立判据 _ecv_judge]，逐件比 class/verdict/E。
另含 --full263 模式：两判据对 263 件 NO_EXIT_AT_ALL 全量跑 + 复核员独立出口检测 vs 普查。
只读被检脚本；输出写本写域 _ecv_compare_results.json。
"""
import collections
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

spec = importlib.util.spec_from_file_location("_ec_criterion", os.path.join(HERE, "_ec_criterion.py"))
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)

spec2 = importlib.util.spec_from_file_location("_ecv_judge", os.path.join(HERE, "_ecv_judge.py"))
MJ = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(MJ)

SAMPLES9 = [
    "lead/re_line_20261105/D21_RULING/_d21_burden5.py",
    "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py",
    "lead/re_line_20261105/_leader/_a7_acf_probe.py",
    "lead/re_line_20261105/_leader/_intra_frame_census.py",
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
]

MINE12 = [
    "lead/dtrigger_compare_20261107/_check_dtrigger.py",
    "lead/w2_samecause_20261109/_w2w_fp9.py",
    "lead/c97_scope_recheck_20261108/_c97_check.py",
    "lead/d13b_design_20261106/_test_state_machine.py",
    "lead/cert_realcheck_20261109/_cr_real_verify.py",
    "lead/bexec_n4_20261108/_n4_ast_scan.py",
    "lead/r33e_merge_20261109/_re_struct_diff.py",
    "lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py",
    "lead/chain_vs_single_20261109/_cs_attrib.py",
    "lead/stale_pass_20261109/_sp_gen_word.py",
    "lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py",
    "lead/counterpart_fix_20261109/_cf_enum_counterpart.py",
]

CTLS = sorted(x for x in os.listdir(HERE) if x.startswith("_ecv_ctl_") and x.endswith(".py"))


def run_both(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    theirs = EC.analyze_file(p, rel)
    mine = MJ.analyze_file(p, rel)
    return theirs, mine


def efmt(e):
    if not e:
        return "-"
    return "/".join(str(e.get(k, "-"))[0] for k in ("E1", "E2", "E3", "E4"))


def main():
    rows = []
    ndiff = 0
    print("%-58s | %-23s | %-23s" % ("rel", "designer cls/verdict/E", "reviewer cls/verdict/E"))
    print("-" * 118)
    for rel in SAMPLES9 + MINE12 + ["lead/exit_criterion_20261110/" + x for x in CTLS]:
        theirs, mine = run_both(rel)
        t, m = efmt(theirs.get("e")), efmt(mine.get("e"))
        same = (theirs["class"] == mine["class"] and theirs["verdict"] == mine["verdict"] and t == m)
        if not same:
            ndiff += 1
        rows.append({"rel": rel,
                     "designer": {"class": theirs["class"], "verdict": theirs["verdict"], "e": theirs.get("e"),
                                  "facts": theirs.get("facts")},
                     "reviewer": {"class": mine["class"], "verdict": mine["verdict"], "e": mine.get("e"),
                                  "facts": mine.get("facts")},
                     "identical": same})
        print("%-58s | %-9s %-10s %-4s | %-9s %-10s %-4s %s"
              % (rel.split("/")[-1] + ("  [" + rel.split("/")[-2] + "]" if "/" in rel else ""),
                 theirs["class"], theirs["verdict"], t,
                 mine["class"], mine["verdict"], m, "" if same else "  <<< DIFF"))

    print("\n比对件数=%d  完全一致=%d  有分歧=%d" % (len(rows), len(rows) - ndiff, ndiff))

    if "--full263" in sys.argv:
        with open(os.path.join(ROOT, "lead", "const_exit_20261109", "_ce_final_out.json"),
                  encoding="utf-8") as f:
            census = json.load(f)
        no_exit = [r["rel"] for r in census["rows"] if r["cls"] == "NO_EXIT_AT_ALL"]
        cnt_t = collections.Counter()
        cnt_m = collections.Counter()
        cls_mismatch = []
        exit_mismatch = []
        for rel in no_exit:
            p = os.path.join(ROOT, rel.replace("/", os.sep))
            th = EC.analyze_file(p, rel)
            mi = MJ.analyze_file(p, rel)
            cnt_t[(th["class"], th["verdict"])] += 1
            cnt_m[(mi["class"], mi["verdict"])] += 1
            if th["class"] != mi["class"]:
                cls_mismatch.append({"rel": rel, "designer": th["class"], "reviewer": mi["class"]})
            if mi["facts"].get("n_exit", 0) > 0:
                exit_mismatch.append({"rel": rel, "reviewer_exit_lines": mi["facts"].get("exit_lines")})
        print("\n== full263 == n=%d" % len(no_exit))
        print("designer(cls,verdict):", dict(cnt_t))
        print("reviewer(cls,verdict):", dict(cnt_m))
        print("class 不一致件数 =", len(cls_mismatch))
        for x in cls_mismatch[:20]:
            print("   ", x)
        print("reviewer 检出出口件数（应=0，与普查 NO_EXIT 分歧） =", len(exit_mismatch))
        for x in exit_mismatch[:10]:
            print("   ", x)
        json.dump({"pair_rows": rows,
                   "full263": {"n": len(no_exit),
                               "designer_counts": {("%s|%s" % k): v for k, v in cnt_t.items()},
                               "reviewer_counts": {("%s|%s" % k): v for k, v in cnt_m.items()},
                               "class_mismatch": cls_mismatch,
                               "reviewer_exit_found": exit_mismatch}},
                  open(os.path.join(HERE, "_ecv_compare_results.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    else:
        json.dump({"pair_rows": rows},
                  open(os.path.join(HERE, "_ecv_compare_results.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print("结果已写 _ecv_compare_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
