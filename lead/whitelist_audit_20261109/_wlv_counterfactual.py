# -*- coding: utf-8 -*-
r"""_wlv_counterfactual.py — 白名单复核员：自证循环 + 对抗样本 独立推演。

不 import 撰写人的 _wl_step34.py / _wl_selfproof.py；自己构造语义空片段、
自己重跑 32 域 302 项（复用本复核员自己的 _wlv_regress_out.json 的 per_element
与 elements，不复用撰写人的 _wl_step1_out.json），自己套 _r9s_regress.py:204-206 /
:223-229 的公式（公式本身是被核对象的定义，必须照抄才能测它）。

三组：
  (D1) 1 条白名单项语义不在场（内存替换该域该 token 的判定文本），其余不动 → 观察 VERDICT
  (D2) 5 条全语义不在场 → 观察 VERDICT
  (D3) 5 条 CF 对抗样本逐条 R9/R9S 判定
  (D4) 移除白名单 1 项 / 多加 1 项 的集合敏感性
"""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
RDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(RDIR))
import _r9s_predicates as R9S  # noqa: E402
import _r9s_samples as S      # noqa: E402

MY = json.loads((WDIR / "_wlv_regress_out.json").read_text(encoding="utf-8"))
ROWS = MY["all_rows"]
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}

# ---- 我自己构造的 5 条「形式像而语义空」片段（与撰写人 _wl_step34/_wl_selfproof 措辞不同，
#      但语义性质相同：指针 / 未决 / 占位 / 不另下结论；保留各 spec 的表层结构） ----
EMPTY = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"):
        "## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **参见另件登记**，pf2:200；改后立即做登记 7/8）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n",
    ("lead/matrix_reach_20261109/", "实跑输出"):
        "## 3 五处缺陷逐处可达性实证\n### 3.1 W1\n- **构造输入 → 实跑返回**：classify 直调，16/16 格实跑：\n```\n  verdict='以台账为准' conf='none'\n```\n- 落哪一行 / 与矩阵声称是否一致：16/16，out:159-174。\n",
    ("lead/n11_wording_fix_20261108/", "改前改后"):
        "## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n",
    ("lead/s604_script_gap_20261109/", "脚本存在性"):
        "## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.5 存在性判定\n**判定：生成脚本【不存在且从未落盘】（以台账记载为准，本件不另下结论）。**\n",
    ("lead/s604_script_gap_20261109/", "可重建"):
        "## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n",
}


def run_regression(replace_keys, whitelist=WHITELIST, verbose=False):
    """按 _r9s_regress.py:162-206 / :223-229 公式重跑；replace_keys = 要换成语义空文本的 (域,token) 集合。"""
    flips, tightens, n_items = [], [], 0
    for row in ROWS:
        if row.get("main_missing"):
            continue
        dom = row["domain"]
        real_text = (ROOT / dom.rstrip("/") / row["main"]).read_text(encoding="utf-8", errors="replace") \
            if "main" in row else ""
        # 用本复核员 _wlv_regress_out.json 里保存的 main 名（若缺则从 ref 补）
        for e in row["per_element"]:
            k = e["token"]
            n_items += 1
            key = (dom, k)
            txt = EMPTY[key] if key in replace_keys and key in EMPTY else real_text
            ok0, lay0 = R9S.R9.r9_element_present(txt, k)
            ok1, lay1, _d = R9S.r9s_element_present(txt, k)
            if (not ok0) and ok1:
                flips.append({"domain": dom, "token": k})
            if ok0 and (not ok1):
                tightens.append({"domain": dom, "token": k})
    outside = [f for f in flips if (f["domain"], f["token"]) not in whitelist]
    no_relax = (len(outside) == 0 and len(flips) == len(whitelist)
                and all((f["domain"], f["token"]) in whitelist for f in flips))
    samples_ok = all(R9S.r9s_element_present(s["text"], s["token"])[0] == s["expect"]
                     for s in S.SAMPLES)
    verdict = "PASS" if (samples_ok and no_relax) else "FAIL"
    return {"n_items": n_items, "n_flips": len(flips), "outside": len(outside),
            "n_tightens": len(tightens), "no_relaxation": no_relax,
            "samples_all_pass": samples_ok, "VERDICT": verdict,
            "flips": flips}


# 补 main 名：从编排方 JSON 的 rows 取（只取名字，不取判定）
REF = json.loads((RDIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
main_by_dom = {r["domain"]: r.get("main") for r in REF["domains32"]["rows"]}
for row in ROWS:
    if "main" not in row:
        row["main"] = main_by_dom.get(row["domain"], "")

print("=== 基线（无替换）===")
b = run_regression(set())
print(f"  n_items={b['n_items']} n_flips={b['n_flips']} outside={b['outside']} "
      f"no_relaxation={b['no_relaxation']} samples_all_pass={b['samples_all_pass']} VERDICT={b['VERDICT']}")

print("\n=== (D1) 第三步(d)：白名单 5 条中『有 1 条是错的』（该域该 token 换成语义空文本，白名单不动）===")
for wrong in sorted(WHITELIST):
    r = run_regression({wrong})
    print(f"  wrong={wrong[0]:<46} {wrong[1]:<8} → n_flips={r['n_flips']} outside={r['outside']} "
          f"no_relaxation={r['no_relaxation']} VERDICT={r['VERDICT']}")

print("\n=== (D2) 5 条全换成语义空片段 ===")
a = run_regression(set(EMPTY.keys()))
print(f"  n_items={a['n_items']} n_flips={a['n_flips']} outside={a['outside']} "
      f"no_relaxation={a['no_relaxation']} samples_all_pass={a['samples_all_pass']} VERDICT={a['VERDICT']}")
for f in a["flips"]:
    print(f"     FLIP {f['domain']:<46} {f['token']:<8} 语义空={(f['domain'],f['token']) in EMPTY}")
print("  ★ 5 条全错仍 PASS ?", a["VERDICT"] == "PASS" and a["n_flips"] == 5)

print("\n=== (D4) 集合敏感性：白名单移除 1 项 / 多加 1 项（文本不动）===")
for wrong in sorted(WHITELIST):
    r = run_regression(set(), whitelist=WHITELIST - {wrong})
    print(f"  移除 {wrong[1]:<8} → no_relaxation={r['no_relaxation']} outside={r['outside']} VERDICT={r['VERDICT']}")
plus = set(WHITELIST) | {("lead/fake_domain/", "假要素")}
r = run_regression(set(), whitelist=plus)
print(f"  多加 1 项        → no_relaxation={r['no_relaxation']} outside={r['outside']} VERDICT={r['VERDICT']}")

# ---- (D3) 第四步：我自己构造 5 条 CF 样本（措辞与撰写人不同，形态同任务书点名）----
CF = [
    {"id": "WCF1", "token": "需谁批准", "label": "批准人待定",
     "text": "## 5 改动清单\n### 5.2 处方\n批准人待定，需谁批准尚需确认。\n"},
    {"id": "WCF2", "token": "实跑输出", "label": "实跑已做但无输出数据",
     "text": "## 3 可达性\n### 3.1 W1\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 落哪一行：与矩阵声称是否一致，详见后续附件。\n"},
    {"id": "WCF3", "token": "改前改后", "label": "改前改后并列但无对照（改后为指针）",
     "text": "## 4 订正草案（改前/改后逐处对照）\n\n### 4.1 方案 A\n\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n"},
    {"id": "WCF4", "token": "脚本存在性", "label": "存在性待查",
     "text": "## 3 脚本搜索全结果与存在性判定\n\n### 3.1 路线一\n\n脚本存在性待查，本件不另下结论。\n"},
    {"id": "WCF5", "token": "可重建", "label": "重建待验证（未决问句）",
     "text": "## 4 重建可行性\n\n### 4.1 五项口径唯一性\n\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n"},
]
print("\n=== (D3) 第四步：5 条『形式像而实质空』对抗样本逐条独立实跑 ===")
cf_rows = []
for s in CF:
    ok, layer, detail = R9S.r9s_element_present(s["text"], s["token"])
    ok0, lay0 = R9S.R9.r9_element_present(s["text"], s["token"])
    mis = bool(ok)
    cf_rows.append({"id": s["id"], "token": s["token"], "r9": ok0, "r9_layer": lay0,
                    "r9s": ok, "r9s_layer": layer, "misjudged": mis,
                    "evidence": detail.get("evidence")})
    print(f"  {s['id']} {s['token']:<8} R9={ok0}/{lay0 or '(none)':<10} "
          f"R9S={ok}/{layer or '(none)':<10} misjudged={'★YES' if mis else 'no'}")
    if mis:
        print(f"     evidence = {json.dumps(detail.get('evidence'), ensure_ascii=False)[:320]}")
n_mis = sum(1 for x in cf_rows if x["misjudged"])
print(f"\n  → 误判在场 = {n_mis}/5   misjudged_ids={[x['id'] for x in cf_rows if x['misjudged']]}")

OUT = {"baseline": b, "d1_one_wrong": {f"{w[0]}|{w[1]}": run_regression({w}) for w in sorted(WHITELIST)},
       "d2_all_five_empty": a, "d4_remove": {}, "cf": cf_rows, "cf_n_misjudged": n_mis}
(WDIR / "_wlv_counterfactual_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wlv_counterfactual_out.json")
