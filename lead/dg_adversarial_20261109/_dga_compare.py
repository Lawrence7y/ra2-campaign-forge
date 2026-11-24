# -*- coding: utf-8 -*-
r"""_dga_compare.py — 第四步(b)(d) + 第五步：DG vs H5 vs R12 逐条差异矩阵、
    「不误判」专项口径、交付形态差异、边界与落地前置条件的量化。

读取本写域 _dga_adversarial_out.json / _dga_step1_out.json（均为本会话实跑产出），
只读保护件；输出只落本写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dga_compare.py
"""
import sys, json, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
A = json.loads((WD / "_dga_adversarial_out.json").read_text("utf-8"))
S1 = json.loads((WD / "_dga_step1_out.json").read_text("utf-8"))
rows = A["cases"]
DET = A["detectors"]

print("=== (4b) DG 相对 H5 的逐条增量（严格口径 expect≠AMBIG）===")
pairs = [("DG_pure", "H5_lit"), ("DG_pure", "H5_gov"), ("DG_pure", "R12"),
         ("DG_pure", "DG_dropin"), ("H5_lit", "R12")]
for a, b in pairs:
    awin = bwin = both_same = 0
    aw, bw = [], []
    for x in rows:
        exp = x["expect"]
        if exp == "AMBIG":
            continue
        ga, gb = x["verdicts"][a], x["verdicts"][b]
        oa, ob = (ga == exp), (gb == exp)
        if oa and not ob:
            awin += 1
            aw.append(x["id"])
        elif ob and not oa:
            bwin += 1
            bw.append(x["id"])
        else:
            both_same += 1
    print("  %-10s vs %-10s : %s 独对 %d %s ; %s 独对 %d %s ; 同对/同错 %d" %
          (a, b, a, awin, aw, b, bwin, bw, both_same))

print("\n=== (5a) 「不误判两个独立否定」专项口径（只看 P 组 17 条 PASS）===")
p_rows = [x for x in rows if x["expect"] == "PASS"]
print("  P 组 n =", len(p_rows))
for k in DET:
    fp = [x["id"] for x in p_rows if x["verdicts"][k] == "CATCH"]
    print("  %-10s fp = %d/%d : %s" % (k, len(fp), len(p_rows), fp))
print("  → 作者自造 20 条负样本上 DG fp=0（_dga_step1_out.json:step_a3_fp），"
      "本任务自造 P 组上 DG_pure fp=%d —— 证明 fp=0 是训练集内结论，不是泛化结论" %
      len([x for x in p_rows if x["verdicts"]["DG_pure"] == "CATCH"]))

print("\n=== (5a) 真 DN 专项口径（只看 C 组 CATCH 条）===")
c_rows = [x for x in rows if x["expect"] == "CATCH"]
print("  C 组 n =", len(c_rows))
for k in DET:
    fn = [x["id"] for x in c_rows if x["verdicts"][k] == "PASS"]
    print("  %-10s fn = %d/%d : %s" % (k, len(fn), len(c_rows), fn))

print("\n=== (4b) 19 式覆盖：DG vs H5 是否同分（第一步复核结论）===")
g = S1["step_a1_gaps"]
print("  DG %d/19 ; H5_lit %d/19 ; R12 %d/19（_dga_step1_out.json:step_a1_gaps）" %
      (g["dg"], g["h5"], g["r12"]))
print("  → 19/19 不是 DG 独特价值：H5 的 28 支字面超集同样 19/19。")
extra = [x["id"] for x in rows if x["expect"] == "CATCH"
         and x["verdicts"]["DG_pure"] == "CATCH" and x["verdicts"]["H5_lit"] == "PASS"]
h5only = [x["id"] for x in rows if x["expect"] == "CATCH"
          and x["verdicts"]["DG_pure"] == "PASS" and x["verdicts"]["H5_lit"] == "CATCH"]
print("  DG 独对而 H5_lit 错的 CATCH 条 =", extra, "（19 式之外的生成式泛化）")
print("  H5_lit 独对而 DG 错的 CATCH 条 =", h5only,
      "（H5 通配支 非[^，,。；;]{0,4}不(宣告|…) 过宽反而蒙对）")

print("\n=== (4b) 105,492 串 vs 28 支：口径对齐 ===")
st = S1["stats"]["core"]
print("  DG_STATS =", st)
print("  H5_DN_EXTRA 分支数 =", S1["stats"]["h5_extra_branches"],
      "; H5_R12_TEN 分支数 =", S1["stats"]["h5_ten_branches"],
      "; 合计字面支 =", S1["stats"]["h5_extra_branches"] + S1["stats"]["h5_ten_branches"])
print("  → 任务书「H5 的 28 支字面超集」= H5_DN_EXTRA 的 28 支（其中 27 支纯字面 + "
      "1 支带通配 非[^…]{0,4}不(宣告|…)）；连十式共 38 支。")
print("  → DG 的 105,492 是【笛卡尔积可生成串数】，不是 105,492 个已验证构式；"
      "实读 _dg_core.py:129-136，n_t12=59*23*21=28497、n_t3=59*9*29*5=76995。")

print("\n=== (4c) 维护成本：加 1 个新构式要动几张表 ===")
m = A["maintenance"]
print("  DG 7 张闭合表 + 5 组作用域常量；加 1 项 MID 即新增 %d 个生成串（扰动面）" %
      m["DG_new_entry_delta"]["add_MID_entry_T12_strings"])
print("  H5 加 1 个构式 = H5_DN_EXTRA 加 1 个字面选择支 = 精确 1 个新串；"
      "作用域由 H5_MICRO_BREAK_RE/H5_SELF_SUBJ_RE/H5_CONTRAST_RE 另表维护")
for k, v in m["DG_new_entry_delta"].items():
    print("    %-42s %d" % (k, v))

print("\n=== (5b/3d) 交付形态：guard 在「一行替换」下是否生效（静态 co_names 实查）===")


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


G7 = _load("_dga3_g7", ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE"]
for fn in ("r10_context", "r12_scan"):
    names = getattr(G7, fn).__code__.co_names
    print("  %-12s co_names 含 guard = %s ; 缺失 = %s" %
          (fn, {g: (g in names) for g in guards},
           [g for g in guards if g not in names]))
print("  → 一行替换只改 DOUBLE_NEG_RE，7 条不变式里 ④?（第二主语/并列/引证/切断）"
      "的 4 条 guard 在 r10_context/r12_scan 中一个都不执行；"
      "与 DNEG_GENERATIVE.md:173 的复核结论一致")

print("\n=== (5d) 本工作判不了什么（如实列，均标未验）===")
cannot = [
    "中文双重否定全域真值 / token 级频次：本集 41 条为自造单句，无 BCC/CCL 语料；",
    "真实门禁落地效果：_g7_predicates.py 与所有保护件绝对只读，未改；"
    "DG_dropin 是内存第二模块实例模拟，非真实替换；",
    "繁体/英文/被动/跨行/>24 字距/多语种混合：本集未覆盖，未验；",
    "A 组 5 条 AMBIG 的最终真值：需所有者或语言学裁定，本集只给保守应判敏感性分析；",
    "「不容不 / 未许不 / 非不认可」等是否属规范汉语真 DN：人工裁定，未验；",
    "GP-A2/A3 同义完成词族、证据不独立、分离型 post 整句：不在双重否定方案射程，未改善且未验；",
    "74 条回归的 chain 层间冲突 31→32（作者 Shim）vs 31→31（真实一行替换）："
    "本会话只复现作者 Shim 口径 31→32，未独立重跑真实一行替换口径（标未验）；",
    "H5 补丁其它维度（G1-G4 全域）：本工作只比双重否定一维。",
]
for i, c in enumerate(cannot, 1):
    print("  %d. %s" % (i, c))

out = {
    "novelty_n": A["novelty"]["n_cases"],
    "strict": A["scoring_strict"], "forced": A["scoring_forced"],
    "pairwise": {}, "p_group": {}, "c_group": {},
    "cannot_judge": cannot,
}
for a, b in pairs:
    aw, bw = [], []
    for x in rows:
        if x["expect"] == "AMBIG":
            continue
        ga, gb = x["verdicts"][a], x["verdicts"][b]
        if (ga == x["expect"]) and not (gb == x["expect"]):
            aw.append(x["id"])
        elif (gb == x["expect"]) and not (ga == x["expect"]):
            bw.append(x["id"])
    out["pairwise"][a + "_vs_" + b] = {"a_only_correct": aw, "b_only_correct": bw}
for k in DET:
    out["p_group"][k] = [x["id"] for x in p_rows if x["verdicts"][k] == "CATCH"]
    out["c_group"][k] = [x["id"] for x in c_rows if x["verdicts"][k] == "PASS"]
(WD / "_dga_compare_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dga_compare_out.json")
