# -*- coding: utf-8 -*-
"""_cmpw_scenarios.py — 交付前独立复跑复核员指出的「partial」缺陷。
只读复核员留下的玩具输入/旧真实输入，调用被核 _cmp_assert.py，
输出一律写 _cmpw_ 前缀新文件（不覆盖任何 _cmp_ / _cmpv_ 既有件）。
用法：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_scenarios.py
"""
import json
import pathlib
import subprocess
import sys

WD = pathlib.Path("D:/Project/ra2-campaign-forge/lead/comparability_20261109")
ASSERT = str(WD / "_cmp_assert.py")
ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")

# (标签, A, B, manifest, 复核员期望说明)
S = [
    ("1_only_I", "_cmpv_s_1_only_I_A.json", "_cmpv_s_1_only_I_B.json", "_cmpv_s_1_only_I_man.json",
     "只改算法 I → 按报告判据应 COMPARABLE（唯一判对的单轴场景）"),
    ("2_only_G", "_cmpv_s_2_only_G_A.json", "_cmpv_s_2_only_G_B.json", "_cmpv_s_2_only_G_man.json",
     "只改真值 G → 报告 §2(b) 要求 G 变=不可比(硬)，应 NOT 判 COMPARABLE"),
    ("3_only_E", "_cmpv_s_3_only_E_A.json", "_cmpv_s_3_only_E_B.json", "_cmpv_s_3_only_E_man.json",
     "只改评测脚本 E → 报告要求 E 变=不可比(硬)，应 NOT 判 COMPARABLE"),
    ("4_only_S", "_cmpv_s_4_only_S_A.json", "_cmpv_s_4_only_S_B.json", "_cmpv_s_4_only_S_man.json",
     "只改样本 S → 报告要求 S 变=不可比(硬)，断言给 PARTIALLY_COMPARABLE 偏松"),
    ("5_only_note", "_cmpv_s_5_only_note_A.json", "_cmpv_s_5_only_note_B.json", "_cmpv_s_5_only_note_man.json",
     "只改 note 判读本体（第五样）→ 看五轴是否漏检"),
    ("6_only_M", "_cmpv_x_6_only_M_A.json", "_cmpv_x_6_only_M_B.json", "_cmpv_x_6_only_M_m.json",
     "只改度量 M → 报告要求 M 变=不可比(硬)，断言给 PARTIALLY_COMPARABLE 偏松"),
    ("7_crossed_G_E", "_cmpv_x_7_crossed_G_E_A.json", "_cmpv_x_7_crossed_G_E_B.json", "_cmpv_x_7_crossed_G_E_m.json",
     "G+E 两硬轴 + manifest 自列 4 个字符串 → 断言 fail-open 判 COMPARABLE_CROSSED"),
    ("8_crossed_S_G", "_cmpv_x_8_crossed_S_G_A.json", "_cmpv_x_8_crossed_S_G_B.json", "_cmpv_x_8_crossed_S_G_m.json",
     "S+G 两轴 + 4 个字符串 → 断言 fail-open 判 COMPARABLE_CROSSED"),
]
# 真实两版 + 反事实（补齐假指纹声明 0 格交叉）
REAL = [
    ("REAL_72_74", "_gp_regression_v1_union_out.json", "_gp_regression_out.json",
     WD / "_cmp_manifest.json", "真实两版：期望 INDETERMINATE"),
    ("HYPO_counterfactual", "_gp_regression_v1_union_out.json", "_gp_regression_out.json",
     WD / "_cmp_toy_manifest_hypo.json", "反事实补齐假 I/E 指纹并声明 0 格交叉：期望 NOT_COMPARABLE"),
]


def run(tag, pa, pb, pm):
    po = WD / ("_cmpw_scen_%s.json" % tag)
    r = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", ASSERT, str(pa), str(pb),
         "--manifest", str(pm), "--label-a", "A", "--label-b", "B", "--out", str(po)],
        capture_output=True, text=True)
    d = json.loads(po.read_text(encoding="utf-8"))
    print("[%s] EXIT=%d verdict=%s differing_axes=%s unknown_axes=%s" %
          (tag, r.returncode, d["verdict"], d["differing_axes"], d["unknown_axes"]))
    print("    axes=%s" % {k: v["state"] for k, v in d["axes"].items()})
    print("    n_expect_changes=%d n_note_changes=%d strict_n=%d" %
          (d["n_expect_changes"], d["n_note_changes"], d["strict_subset"]["n"]))
    print("    reason=%s" % d["reason"])
    return d


def main():
    print("=== 复核员玩具场景（8 个）独立复跑 ===")
    for tag, a, b, m, note in S:
        print("  · 场景 %s：%s" % (tag, note))
        run(tag, WD / a, WD / b, WD / m)
    print("\n=== 真实两版 + 反事实 ===")
    gp = ROOT / "lead" / "gate_pipeline_20261109"
    for tag, a, b, m, note in REAL:
        print("  · %s：%s" % (tag, note))
        run(tag, gp / a, gp / b, m)
    print("\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
