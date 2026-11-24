# -*- coding: utf-8 -*-
r"""_wl_selfproof.py — 白名单自证循环的可执行反例。

不改任何盘上文件：只在内存中把 5 个真实域的主件文本换成「语义空但形式像」的片段，
按 _r9s_regress.py:162-206 / :223-229 的公式重算 flips / no_relaxation / VERDICT。
若 5 条全翻案且全在白名单内 → 回归仍报 PASS，自证循环得证。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
sys.path.insert(0, str(ROOT / "lead" / "gate_r9sem_20261109"))
import _r9s_predicates as R9S
import _r9s_samples as S

step1 = json.loads((WDIR / "_wl_step1_out.json").read_text(encoding="utf-8"))
WHITELIST = {tuple(x) for x in step1["domains32"]["whitelist"]}
# 5 个语义空片段（每条都保留真实段落的表层结构，只把关键值换成指针/未决/占位）
EMPTY = {
 ("lead/matrix_ab_ruling_20261109/", "需谁批准"):
   "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n",
 ("lead/matrix_reach_20261109/", "实跑输出"):
   "## 3 五处缺陷逐处可达性实证\n### 3.1 W1\n- **构造输入 → 实跑返回**：classify 直调，16/16 格实跑：\n```\n  verdict='详见台账' conf='none'\n```\n- 落哪一行 / 与矩阵声称是否一致：16/16，out:159-174。\n",
 ("lead/n11_wording_fix_20261108/", "改前改后"):
   "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n",
 ("lead/s604_script_gap_20261109/", "脚本存在性"):
   "## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.5 存在性判定\n**结论：生成脚本【不存在且从未落盘】（以台账记载为准，本件不另下结论）。**\n",
 ("lead/s604_script_gap_20261109/", "可重建"):
   "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n",
}

print("=== 内存中把 5 个白名单项换成语义空片段，逐条跑 R9 / R9S ===")
flips, tightens, n_items = [], [], 0
for row in step1["domains32"]["rows"]:
    if row.get("main_missing"): continue
    dom = row["domain"]
    # 该域若属白名单域，则用「语义空」文本替换；其余域的 text 仍取真实主件
    empty_texts = {k: v for (d, k), v in EMPTY.items() if d == dom}
    if empty_texts:
        # 只替换该域白名单 token 的判定（其他 token 仍按真实主件，不影响 flips 统计）
        real_text = (ROOT / dom.rstrip("/") / row["main"]).read_text(encoding="utf-8", errors="replace")
        text_for = {k: t for k, t in empty_texts.items()}
    else:
        real_text = (ROOT / dom.rstrip("/") / row["main"]).read_text(encoding="utf-8", errors="replace")
        text_for = {}
    for e in row["per_element"]:
        k = e["token"]
        n_items += 1
        txt = text_for.get(k, real_text)
        ok0, lay0 = R9S.R9.r9_element_present(txt, k)
        ok1, lay1, _ = R9S.r9s_element_present(txt, k)
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST,
                          "semantically_empty": (dom, k) in EMPTY})
        if ok0 and (not ok1): tightens.append({"domain": dom, "token": k})

outside = [f for f in flips if not f["whitelisted"]]
no_relaxation = (len(outside) == 0 and len(flips) == len(WHITELIST)
                 and all(f["whitelisted"] for f in flips))
samples_ok = all(
    (R9S.r9s_element_present(s["text"], s["token"])[0] == s["expect"])
    for s in S.SAMPLES)
# VERDICT 公式 (_r9s_regress.py:223-229)：samples.all_pass ∧ no_relaxation ∧ 4 域剩余缺要素=0
verdict = "PASS" if (samples_ok and no_relaxation) else "FAIL"
print(f"  n_items={n_items}  n_flips={len(flips)}  outside_whitelist={len(outside)}  n_tightens={len(tightens)}")
for f in flips:
    print(f"     FLIP {f['domain']:<46} {f['token']:<10} whitelisted={f['whitelisted']}  ★语义空={f['semantically_empty']}")
print(f"  no_relaxation = {no_relaxation}   samples_all_pass = {samples_ok}")
print(f"  ★ VERDICT = {verdict}   ← 5 条全都语义不在场，回归仍报 PASS")
print("  结论：白名单由派发方预置且 no_relaxation 只做集合包含检查 ⇒ 回归无法检出『白名单内假阳性』")

OUT = {"flips": flips, "n_flips": len(flips), "outside_whitelist": len(outside),
       "n_tightens": len(tightens), "no_relaxation": no_relaxation,
       "samples_all_pass": samples_ok, "verdict_simulation": verdict,
       "all_5_semantically_empty": all(f["semantically_empty"] for f in flips)}
(WDIR / "_wl_selfproof_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1),
                                             encoding="utf-8", newline="\n")
print("\nWROTE _wl_selfproof_out.json")
