# -*- coding: utf-8 -*-
r"""_wl_step3_struct.py — 白名单机制结构审查：registered token 的域分布 + 复核回件 7 条近似负样本独立复跑。

验证：(1) SPECS 恰 5 键 → 未登记 token 结构性不可能翻案；但「已登记 token 出现在白名单外域」是否可能？
      (2) 复核 V1..V7 逐条复跑（不采信复核结论，自己跑）。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
sys.path.insert(0, str(ROOT / "lead" / "gate_r9sem_20261109"))
import _r9s_predicates as R9S

step1 = json.loads((WDIR / "_wl_step1_out.json").read_text(encoding="utf-8"))
WHITELIST = {tuple(x) for x in step1["domains32"]["whitelist"]}
print("=== (1) 已登记 token 在 302 项中的域分布 ===")
dist = {}
for row in step1["domains32"]["rows"]:
    if row.get("main_missing"): continue
    for e in row["per_element"]:
        if e["token"] in R9S.SPECS:
            dist.setdefault(e["token"], []).append({
                "domain": row["domain"], "r9": e["r9_present"], "r9s": e["r9s_present"],
                "in_whitelist": (row["domain"], e["token"]) in WHITELIST})
for tok, rows in dist.items():
    print(f"  token={tok}  出现 {len(rows)} 次")
    for r in rows:
        print(f"     {r['domain']:<48} r9={r['r9']} r9s={r['r9s']} whitelisted={r['in_whitelist']}")
tot = sum(len(v) for v in dist.values())
outside = [(t, r["domain"]) for t, v in dist.items() for r in v if not r["in_whitelist"]]
print(f"  → 已登记 token 共 {tot} 次；其中白名单外 {len(outside)} 次 = {outside}")
print("  → SPECS 5 键 ⇒ 297 个未登记 token 的项 R9S≡R9（结构性不翻案）；"
      "白名单外 0 主要是设计后果，不是独立实证")

# (2) 复核回件 7 条近似负样本（定义照录 _r9sv_verify.py:150-225，本会话独立复跑）
NEAR = [
 ("V1","实跑输出","## 3 五处缺陷逐处可达性实证\n### 3.1 W1\n- **构造输入 → 实跑返回**：classify 直调，pre 八变体 × read_error 两型，16/16 格实跑：\n```\n（本轮已实跑并记录，全部 16 格返回值见 _mr_probe1_out.txt:159-174）\n```\n- **落哪一行 / 与矩阵声称是否一致**：16/16，out:159-174；已实跑并记录，输出不再重列。\n"),
 ("V2","需谁批准","## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n"),
 ("V3","改前改后","## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A（最小改动·推荐）\n- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n- 【要点】只换「一一对应」→「逐项对应」并插入拆分括注。\n"),
 ("V4","脚本存在性","## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.1 路线一：文件名搜索【本轮实跑】\n全树 .py 共 11790 个，逐路结论：未见生成器命名痕迹。\n### 3.2 路线二：内容搜索\n命中 32 件，均属事后复核件。\n### 3.5 存在性判定\n**判定：生成脚本的存在状况以台账 §604 记载为准，本件不另下结论。**\n"),
 ("V5","可重建","## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
 ("V6","可重建","## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n**判定：正确算法并非【可唯一重建】。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
 ("V7","脚本存在性","## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.5 存在性判定\n**判定：生成脚本存在性以台账 §604 记载为准，本件不另下结论。**\n"),
]
print("\n=== (2) 复核 7 条近似负样本：本会话独立复跑（期望全 False）===")
rows = []
for cid, tok, txt in NEAR:
    ok, layer, detail = R9S.r9s_element_present(txt, tok)
    r9ok, r9lay = R9S.R9.r9_element_present(txt, tok)
    caught = not ok
    rows.append({"id": cid, "token": tok, "r9": r9ok, "r9_layer": r9lay,
                 "r9s": ok, "r9s_layer": layer, "caught": caught,
                 "evidence": detail.get("evidence")})
    print(f"  {cid} {tok:<8} R9={r9ok}/{r9lay or '(none)'}  R9S={ok}/{layer or '(none)'}  caught={caught}")
n_caught5 = sum(1 for r in rows[:5] if r["caught"])
n_caught7 = sum(1 for r in rows if r["caught"])
print(f"  → V1..V5 caught = {n_caught5}/5   all_7_caught = {n_caught7}/7")

OUT = {"registered_token_distribution": dist, "n_registered_occurrences": tot,
       "registered_outside_whitelist": outside,
       "near_miss_rerun": rows, "v1_v5_caught": n_caught5, "all7_caught": n_caught7}
(WDIR / "_wl_step3_struct_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1),
                                                encoding="utf-8", newline="\n")
print("\nWROTE _wl_step3_struct_out.json")
