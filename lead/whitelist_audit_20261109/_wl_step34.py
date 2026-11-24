# -*- coding: utf-8 -*-
r"""_wl_step34.py — 白名单独立审查 / 第三步(d) 反事实推演 + 第四步 5 条「形式像而实质空」样本。

只读加载 R9S 谓词（不改其源码），逐条实跑 r9s_element_present。
第三步(d)：模拟「白名单里有 1 条是错的」——把该条从白名单移除、或把谓词对
该条改回 R9 原判，观察 _r9s_regress.py:204-206 的 no_relaxation 公式报什么。
第四步：5 条构造样本，逐条给 (present, layer, detail)。

产物：_wl_step34_out.json / _wl_step34_stdout.txt。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
sys.path.insert(0, str(ROOT / "lead" / "gate_r9sem_20261109"))
import _r9s_predicates as R9S

# ---------------------------------------------------------------------------
# 第三步(d)：白名单里有 1 条是错的，回归会报什么？
# 复刻 _r9s_regress.py:113-119 的 WHITELIST 与 :204-206 的 no_relaxation 公式
# ---------------------------------------------------------------------------
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
# 本会话第一步实跑得到的 5 条翻案（_wl_step1_out.json）
step1 = json.loads((WDIR / "_wl_step1_out.json").read_text(encoding="utf-8"))
flips = [(f["domain"], f["token"]) for f in step1["domains32"]["flips"]]

def no_relaxation_formula(wl, fs):
    outside = [f for f in fs if f not in wl]
    return (len(outside) == 0 and len(fs) == len(wl) and all(f in wl for f in fs)), outside

print("=== 第三步(d) 反事实：白名单 5 条里有 1 条是错的（其实语义不在场） ===")
d3 = {}
for i, wrong in enumerate(sorted(WHITELIST), 1):
    # 情形 A：第三方裁定把「错的那条」从白名单移除，但谓词仍把它判 PASS（翻案照旧）
    wl_removed = set(WHITELIST) - {wrong}
    nr_a, out_a = no_relaxation_formula(wl_removed, flips)
    # 情形 B：白名单不动（仍含错条），谓词照旧把 5 条全判 PASS —— 这正是现状
    nr_b, out_b = no_relaxation_formula(set(WHITELIST), flips)
    d3[f"case_{i}"] = {
        "wrong_entry": list(wrong),
        "A_whitelist_removed_but_predicate_unchanged": {
            "n_flips": len(flips), "n_whitelist": len(wl_removed),
            "flips_outside_whitelist": [list(x) for x in out_a],
            "no_relaxation": nr_a,
            "note": "按当前公式会报 FAIL（no_relaxation=False），但这只是集合不等，不是语义判定",
        },
        "B_whitelist_unchanged_current_state": {
            "n_flips": len(flips), "n_whitelist": len(WHITELIST),
            "flips_outside_whitelist": [], "no_relaxation": nr_b,
            "note": "★ 错条仍在白名单内 ⇒ 回归照报 PASS：自证循环成立",
        },
    }
    print(f"  case_{i} wrong={wrong}")
    print(f"     A 移除白名单错条(谓词未改): no_relaxation={nr_a} outside={len(out_a)}")
    print(f"     B 白名单不动(现状)      : no_relaxation={nr_b} outside=0  ← 仍 PASS")

# 情形 C：错条其实是「不该翻案」，即谓词本应判 False；但白名单把它列进来
# —— 此时 n_flips=4，公式因 len(flips)!=len(WHITELIST) 会 FAIL，但 FAIL 的理由是「数量」
print("  case_C 若谓词本应不翻案(错条其实语义不在场)，但被强行翻案：flips 仍 5、白名单仍 5 → PASS")
d3["case_C"] = {
    "note": "错条被 R9S 判 True（假阳性），且它恰在白名单内 ⇒ flips=5=whitelist、outside=0、no_relaxation=True、VERDICT=PASS；回归没有任何机制检查该条语义是否真在场",
}
# 情形 D：把白名单扩充 1 条（错的写法：为容纳 1 条假阳性而加白名单项）
wl_plus = set(WHITELIST) | {("lead/fake_domain/", "假要素")}
nr_d, out_d = no_relaxation_formula(wl_plus, flips)
d3["case_D_whitelist_plus_one"] = {"no_relaxation": nr_d, "n_whitelist": len(wl_plus),
                                    "note": "白名单多 1 条、flips 仍 5 ⇒ len(flips)!=len(WHITELIST) ⇒ FAIL（仅数量）"}
print(f"  case_D 白名单多 1 条(flips 不变): no_relaxation={nr_d}")

# ---------------------------------------------------------------------------
# 第四步：5 条「语义不在场但形式上像」的样本
# ---------------------------------------------------------------------------
CF = [
    {"id": "CF1", "token": "需谁批准", "label": "批准人待定",
     "text": "## 5 改动清单\n### 5.2 处方\n批准人待定，需谁批准尚需确认。\n"},
    {"id": "CF2", "token": "实跑输出", "label": "实跑已做但无输出数据",
     "text": "## 3 可达性\n### 3.1 W1\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 落哪一行：与矩阵声称是否一致，详见后续附件。\n"},
    {"id": "CF3", "token": "改前改后", "label": "改前改后并列但无对照",
     "text": "## 4 订正草案（改前/改后逐处对照）\n\n### 4.1 方案 A\n\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n"},
    {"id": "CF4", "token": "脚本存在性", "label": "存在性待查",
     "text": "## 3 脚本搜索全结果与存在性判定\n\n### 3.1 路线一\n\n脚本存在性待查，本件不另下结论。\n"},
    {"id": "CF5", "token": "可重建", "label": "重建待验证",
     "text": "## 4 重建可行性\n\n### 4.1 五项口径唯一性\n\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n"},
]

print("\n=== 第四步 5 条『形式像而实质空』样本逐条实跑 ===")
cf_rows = []
for s in CF:
    ok, layer, detail = R9S.r9s_element_present(s["text"], s["token"])
    ok_r9, lay_r9 = R9S.R9.r9_element_present(s["text"], s["token"])
    rec = {"id": s["id"], "token": s["token"], "label": s["label"], "text": s["text"],
           "r9_present": ok_r9, "r9_layer": lay_r9,
           "r9s_present": ok, "r9s_layer": layer, "detail": detail,
           "misjudged_as_present": bool(ok)}
    cf_rows.append(rec)
    print(f"  {s['id']} [{s['label']}] token={s['token']}  R9={ok_r9}/{lay_r9 or '(none)'}  "
          f"R9S={ok}/{layer or '(none)'}  misjudged={'★YES' if ok else 'no'}")
    if ok:
        ev = detail.get("evidence")
        print(f"     evidence = {json.dumps(ev, ensure_ascii=False)[:300]}")

n_mis = sum(1 for x in cf_rows if x["misjudged_as_present"])
print(f"\n  → 误判在场 = {n_mis}/5   (升级过宽? {'YES' if n_mis else 'NO on these 5'})")

OUT = {"step3_counterfactual": d3, "step4_counterfactual_samples": cf_rows,
       "step4_n_misjudged": n_mis}
(WDIR / "_wl_step34_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1),
                                         encoding="utf-8", newline="\n")
print("\nWROTE _wl_step34_out.json")
