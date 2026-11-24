# -*- coding: utf-8 -*-
r"""_r9sv_verify.py — R9 语义要素设计回件·独立复核（只读核验，产出前缀 _r9sv_）。

独立实现，不采信撰写人的结论：
  (1) 九件指纹自算 + 被核对象/受保护件零漂移；
  (2) 自己实现 r9_normalize / r9_element_present（依据实读 _g7_predicates.py:31-53），
      另以 hashlib 验指纹后 importlib 只读加载 g7 本体做交叉校验，再跑 5 处；
  (3) 自己构造 5 条「近似但缺关键信息」的负样本，跑撰写人的 r9s_element_present；
  (4) 自己独立重跑 32 域 / 逐要素 R9→R9S 比对，与 _r9s_regress_out.json 对账；
  (5) 准入 7 条是否可执行（找有没有准入校验器）、注册表规模、正负样本数；
  (6) 调用方逐个 grep 统计；
  (7) 越界检查：写域外有无 _r9s_/_r9sv_ 产物、9 件是否漂移。

零真机、零采样代码；Python = python -I -X utf8 + 绝对路径；指纹用 hashlib。
"""
from __future__ import annotations

import ast
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
R9S = WDIR / "_r9s_predicates.py"
BASELINE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"

OUT: dict = {}

# ---------------------------------------------------------------------------
# (1) 九件指纹 + 只读件零漂移
# ---------------------------------------------------------------------------
BASE9 = {
    "lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md": ("ed7e326d38a967308acf0e276c262300abf8d68c98aad2d53b8e9f2a3def6528", 51156),
    "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md": ("0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md": ("cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6", 27825),
    "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md": ("4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4", 18966),
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md": ("593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
print("=== (1) 九件指纹自算 ===")
fp_rows = []
for rel, (h, b) in BASE9.items():
    d = (ROOT / rel).read_bytes()
    got_h, got_b = hashlib.sha256(d).hexdigest(), len(d)
    m = (got_h == h and got_b == b)
    fp_rows.append({"file": rel, "sha256": got_h, "bytes": got_b, "match": m})
    print("  %-5s %-60s %s %d" % ("MATCH" if m else "DRIFT", rel[:60], got_h[:16], got_b))
OUT["nine_fingerprints"] = {"rows": fp_rows, "all_match": all(x["match"] for x in fp_rows)}
print("  all_match =", OUT["nine_fingerprints"]["all_match"])

design = WDIR / "_r9s_DESIGN.md"
db = design.read_bytes()
OUT["design_reply"] = {"file": str(design.relative_to(ROOT)),
                       "sha256": hashlib.sha256(db).hexdigest(), "bytes": len(db)}
print("  design_reply =", OUT["design_reply"]["sha256"], OUT["design_reply"]["bytes"])
# 设计回件自己的绑定行（格式自检）
bt = db.decode("utf-8")
m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", bt)
OUT["design_binding_line"] = {"found": bool(m), "hex": m.group(1) if m else None,
                              "bytes": int(m.group(2)) if m else None}
print("  design_binding_line =", OUT["design_binding_line"])

# ---------------------------------------------------------------------------
# (2) 独立实现 R9（依据 _g7_predicates.py:31-53 实读）
# ---------------------------------------------------------------------------
print("\n=== (2) 独立实现 r9_element_present 并跑 5 处 ===")
_WRAP_CHARS = "`\u00b4\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f"


def my_r9_normalize(text: str) -> str:
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`", text):
        out.append(text[pos:m.start()])
        out.append(m.group(1).replace("\n", "").replace("\r", ""))
        pos = m.end()
    out.append(text[pos:])
    n2 = "".join(out)
    return "".join(" " if ch in _WRAP_CHARS else ch for ch in n2)


def my_r9_element_present(text: str, token: str):
    if token in text:
        return True, "raw"
    if token in my_r9_normalize(text):
        return True, "normalized"
    return False, ""


# 交叉校验：hashlib 验指纹后只读加载 g7 本体
spec = importlib.util.spec_from_file_location("_r9sv_g7", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)
assert hashlib.sha256(G7.read_bytes()).hexdigest() == BASE9["lead/gate_fp7_20261108/_g7_predicates.py"][0]

CASES = [
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md", "需谁批准", 108),
    ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", "实跑输出", 65),
    ("lead/n11_wording_fix_20261108/N11_WORDING_FIX.md", "改前改后", 76),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "脚本存在性", 32),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "可重建", 87),
]
case_rows = []
for rel, tok, ln in CASES:
    t = (ROOT / rel).read_text(encoding="utf-8")
    mine = my_r9_element_present(t, tok)
    theirs = g7.r9_element_present(t, tok)
    norm_same = my_r9_normalize(t) == g7.r9_normalize(t)
    rec = {"file": rel, "token": tok, "line": ln,
           "literal_present": tok in t,
           "my_r9_present": mine[0], "my_r9_layer": mine[1],
           "g7_r9_present": theirs[0], "g7_r9_layer": theirs[1],
           "normalize_identical": norm_same,
           "lineText": t.splitlines()[ln - 1]}
    case_rows.append(rec)
    print("  %-14s literal=%-5s mine=(%s,%r) g7=(%s,%r) norm_same=%s"
          % (tok, rec["literal_present"], mine[0], mine[1], theirs[0], theirs[1], norm_same))
    print("     L%d: %s" % (ln, rec["lineText"][:150]))
OUT["five_cases"] = {"rows": case_rows,
                     "all_false": all((not x["my_r9_present"]) and (not x["g7_r9_present"])
                                      for x in case_rows),
                     "any_already_true": any(x["g7_r9_present"] for x in case_rows)}
print("  all_false =", OUT["five_cases"]["all_false"],
      " any_already_true =", OUT["five_cases"]["any_already_true"])

# 加载被核的升级层（其自身先验 g7 指纹）
sys.path.insert(0, str(WDIR))
sp = importlib.util.spec_from_file_location("_r9sv_r9s_under_test", R9S)
r9s = importlib.util.module_from_spec(sp)
sp.loader.exec_module(r9s)
OUT["spec_inventory"] = {"size": len(r9s.spec_inventory()),
                         "ids": [v["id"] for v in r9s.spec_inventory().values()]}
print("  spec_inventory size =", OUT["spec_inventory"]["size"], OUT["spec_inventory"]["ids"])

# ---------------------------------------------------------------------------
# (3) 我自造的 5 条「近似但缺关键信息」负样本
#     每条都刻意模仿真实正例的段落结构，只把关键语义信息抽走/改成指针/否定
# ---------------------------------------------------------------------------
print("\n=== (3) 独立构造 5 条近似负样本（期望 present=False） ===")
NEAR_NEG = [
    {
        "id": "V1", "token": "实跑输出",
        "text": "## 3 五处缺陷逐处可达性实证\n"
                "### 3.1 W1\n"
                "- **构造输入 → 实跑返回**：classify 直调，pre 八变体 × read_error 两型，16/16 格实跑：\n"
                "```\n"
                "（本轮已实跑并记录，全部 16 格返回值见 _mr_probe1_out.txt:159-174）\n"
                "```\n"
                "- **落哪一行 / 与矩阵声称是否一致**：16/16，out:159-174；已实跑并记录，输出不再重列。\n",
        "why": "仿 matrix_reach:65-74 的完整段落：有事件、有围栏块、有 16/16 计数、有 out:159-174 索引，"
               "但全文无任何带具体值的返回数据；「已实跑并记录」+ 指针 ≠ 输出载荷。"
               "任务书点名的近似负样本形态。",
    },
    {
        "id": "V2", "token": "需谁批准",
        "text": "## 5 裁决与可执行改动清单\n"
                "### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n"
                "改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n",
        "why": "仿 RULING_MATRIX_AB.md:108 的赋值句形态（批准人一律 = …），但取值是指针"
               "「见台账登记」而非可指认的施事；wh-变量没被回答。",
    },
    {
        "id": "V3", "token": "改前改后",
        "text": "## 4 订正草案（改前/改后逐处对照）\n"
                "### 4.1 方案 A（最小改动·推荐）\n"
                "- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。\n"
                "- 【改后】改后句见方案 B 的对应行，本件不重录。\n"
                "- 【要点】只换「一一对应」→「逐项对应」并插入拆分括注。\n",
        "why": "仿 N11_WORDING_FIX.md:76-83：标题带「逐处对照」、两个标签齐备，但【改后】只有指针"
               "「见方案 B 的对应行，本件不重录」，没有改后实值文本；Before(t)∧After(t) 的 After 实值缺失。",
    },
    {
        "id": "V4", "token": "脚本存在性",
        "text": "## 3 脚本搜索全结果与存在性判定（四路逐路）\n"
                "### 3.1 路线一：文件名搜索【本轮实跑】\n"
                "全树 .py 共 11790 个，逐路结论：未见生成器命名痕迹。\n"
                "### 3.2 路线二：内容搜索\n"
                "命中 32 件，均属事后复核件。\n"
                "### 3.5 存在性判定\n"
                "**判定：生成脚本的存在状况以台账 §604 记载为准，本件不另下结论。**\n",
        "why": "仿 S604_SCRIPT_GAP.md:32/:44/:51/:69-71 的四路结构（脚本对象、存在性谓词、判定算子全在），"
               "但极性从未决断（「以台账记载为准，不另下结论」），Resolved(d) 不成立。"
               "刻意不写出 token 字面串，避免 L0 裸 in 短路，纯测语义层。",
    },
    {
        "id": "V5", "token": "可重建",
        "text": "## 4 重建可行性与单向压缩候选筛选\n"
                "### 4.1 正确算法：五项口径唯一性\n"
                "| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n"
                "**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** "
                "已有四重独立实现逐位一致，max|Δ|=0.000000。\n",
        "why": "仿 S604_SCRIPT_GAP.md:77-87：五项口径唯一性表、肯定情态串、逐位一致证据全在，"
               "但把「判定」换成「待判…是否…尚需核对」的未决问句，没有交付 ◇Reconstruct 的决断。"
               "与正例只差把「判定」改成「待判」的近似形态。",
    },
]
# 补充探针（不计入要求的 5 条，单列作机制漏点举证）
SUPPLEMENTARY = [
    {
        "id": "V6", "token": "可重建",
        "text": "## 4 重建可行性与单向压缩候选筛选\n"
                "### 4.1 正确算法：五项口径唯一性\n"
                "**判定：正确算法并非【可唯一重建】。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n",
        "why": "与正例 S604_SCRIPT_GAP.md:87 只差插入「并非」两个字，"
               "把肯定情态翻成否定；¬◇Reconstruct 恰与要素相反。测 NEG_CANCEL 词表是否覆盖自然否定式。",
    },
    {
        "id": "V7", "token": "脚本存在性",
        "text": "## 3 脚本搜索全结果与存在性判定（四路逐路）\n"
                "### 3.5 存在性判定\n"
                "**判定：生成脚本存在性以台账 §604 记载为准，本件不另下结论。**\n",
        "why": "token 字面串在「生成脚本存在性」中被裸 in 命中（L0 raw），但全文无任何已决断极性。"
               "测已登记 token 的承诺守卫是否覆盖「字面在场、语义未交付」。",
    },
]
near_rows = []
for s in NEAR_NEG:
    ok, layer, detail = r9s.r9s_element_present(s["text"], s["token"])
    r9ok, r9layer = my_r9_element_present(s["text"], s["token"])
    rec = {"id": s["id"], "token": s["token"], "why": s["why"],
           "expect": False, "r9s_present": ok, "r9s_layer": layer,
           "r9s_spec": detail.get("spec"), "r9s_evidence": detail.get("evidence", []),
           "r9_present": r9ok, "caught": (ok is False)}
    near_rows.append(rec)
    print("  %-3s %-8s r9s_present=%-5s layer=%-9s spec=%-32s caught=%s"
          % (s["id"], s["token"], ok, layer or "(none)", str(rec["r9s_spec"]), rec["caught"]))
    if ok:
        print("     !! 漏抓，证据 =", json.dumps(rec["r9s_evidence"], ensure_ascii=False)[:400])
    print("     why:", s["why"][:170])
OUT["near_miss_negatives"] = {"rows": near_rows,
                              "n": len(near_rows),
                              "n_caught": sum(1 for x in near_rows if x["caught"]),
                              "all_caught": all(x["caught"] for x in near_rows)}
print("  near_miss: %d/%d caught, all_caught=%s"
      % (OUT["near_miss_negatives"]["n_caught"], OUT["near_miss_negatives"]["n"],
         OUT["near_miss_negatives"]["all_caught"]))

print("\n=== (3b) 补充机制探针（不计入 5 条要求样本） ===")
supp_rows = []
for s in SUPPLEMENTARY:
    ok, layer, detail = r9s.r9s_element_present(s["text"], s["token"])
    r9ok, r9layer = my_r9_element_present(s["text"], s["token"])
    rec = {"id": s["id"], "token": s["token"], "why": s["why"],
           "expect": False, "r9s_present": ok, "r9s_layer": layer,
           "r9_present": r9ok, "r9_layer": r9layer,
           "r9s_spec": detail.get("spec"), "r9s_evidence": detail.get("evidence", []),
           "r9s_logic": detail.get("logic"), "caught": (ok is False)}
    supp_rows.append(rec)
    print("  %-3s %-8s r9=(%s,%r) r9s=(%s,%r) caught=%s"
          % (s["id"], s["token"], r9ok, r9layer, ok, layer or "(none)", rec["caught"]))
    if ok:
        print("     !! 漏抓，logic =", rec["r9s_logic"])
        print("     evidence =", json.dumps(rec["r9s_evidence"], ensure_ascii=False)[:300])
OUT["supplementary_probes"] = {"rows": supp_rows,
                               "n_caught": sum(1 for x in supp_rows if x["caught"])}

# ---------------------------------------------------------------------------
# (4) 独立重跑 32 域 / 逐要素（不调用撰写人的 regress 脚本）
# ---------------------------------------------------------------------------
print("\n=== (4) 独立 32 域 / 逐要素不放松重跑 ===")
BASE = json.loads(BASELINE.read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}


def my_gate_src(low: str) -> str:
    k = low.find("const GATE_CODE = [")
    e = low.find("].join", k)
    if k < 0 or e < 0:
        return ""
    body = low[k + len("const GATE_CODE = ["):e]
    parts = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts)


def my_elements(run: str) -> list[str]:
    p = RUNS.get(run)
    if not p:
        return []
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    if i < 0:
        return []
    d, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    src = my_gate_src(d.get("lowered", ""))
    out = []
    for m in re.finditer(
            r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)", src):
        try:
            out += [x for x in ast.literal_eval(m.group(2)) if x]
        except Exception:
            pass
    return out


WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
dom_rows, flips, tightens = [], [], []
n_items = n_identical = n_drift = 0
for r in ROWS:
    dom, main = r["domain"], r["main"]
    mp = ROOT / dom.rstrip("/") / main
    if not mp.is_file():
        dom_rows.append({"domain": dom, "main_missing": True})
        print("  %-48s MAIN MISSING" % dom)
        continue
    raw = mp.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    sha, size = hashlib.sha256(raw).hexdigest(), len(raw)
    main_match = (sha == r["mainSha256"] and size == r["mainBytes"])
    if not main_match:
        n_drift += 1
    elems = my_elements(r["run"])
    per = []
    base_missing = [p.split("缺要素 ", 1)[1] for p in r["gateProblems"] if p.startswith("缺要素")]
    for k in elems:
        ok0, lay0 = my_r9_element_present(text, k)
        ok1, lay1, _ = r9s.r9s_element_present(text, k)
        n_items += 1
        same = (ok0 == ok1 and lay0 == lay1)
        n_identical += int(same)
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST,
                          "in_baseline_missing": k in base_missing})
        if ok0 and (not ok1):
            tightens.append({"domain": dom, "token": k})
        per.append({"token": k, "r9": [ok0, lay0], "r9s": [ok1, lay1], "identical": same})
    changed = [x for x in per if not x["identical"]]
    dom_rows.append({"domain": dom, "main": main, "n_elements": len(elems),
                     "main_match": main_match, "baseline_missing": base_missing,
                     "changed": changed, "per_element": per})
    print("  %-48s elems=%-3d main_match=%-5s base_missing=%-30s changed=%s"
          % (dom, len(elems), main_match, json.dumps(base_missing, ensure_ascii=False)[:30],
             json.dumps([{"t": x["token"], "r9": x["r9"], "r9s": x["r9s"]} for x in changed],
                        ensure_ascii=False)[:160]))

OUT["regression32"] = {
    "n_domains": len(ROWS), "n_domains_with_main": sum(1 for x in dom_rows if not x.get("main_missing")),
    "n_items": n_items, "n_identical": n_identical, "n_changed": n_items - n_identical,
    "n_main_drift": n_drift, "flips": flips, "n_flips": len(flips),
    "n_flips_outside_whitelist": len([f for f in flips if not f["whitelisted"]]),
    "tightens": tightens, "n_tightens": len(tightens),
    "domains": dom_rows,
}
print("  n_domains=%d with_main=%d n_items=%d identical=%d changed=%d main_drift=%d"
      % (len(ROWS), OUT["regression32"]["n_domains_with_main"], n_items, n_identical,
         n_items - n_identical, n_drift))
print("  n_flips=%d outside_whitelist=%d n_tightens=%d"
      % (len(flips), OUT["regression32"]["n_flips_outside_whitelist"], len(tightens)))
for f in flips:
    print("     FLIP %-46s %-12s whitelisted=%s in_baseline_missing=%s"
          % (f["domain"], f["token"], f["whitelisted"], f["in_baseline_missing"]))

# 与撰写人落盘的 regress_out.json 对账
reg = json.loads((WDIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
their_flips = [(x["domain"], x["token"]) for x in reg["domains32"]["flips"]]
my_flips = [(x["domain"], x["token"]) for x in flips]
OUT["regression32"]["cross_check"] = {
    "their_n_domains": len(reg["domains32"]["rows"]),
    "their_n_flips": reg["domains32"]["n_flips"],
    "their_outside_whitelist": len(reg["domains32"]["flips_outside_whitelist"]),
    "their_n_tightens": reg["domains32"]["n_tightens"],
    "their_verdict": reg["verdict"],
    "their_pos": reg["samples"]["positive"], "their_pos_pass": reg["samples"]["positive_pass"],
    "their_neg": reg["samples"]["negative"], "their_neg_pass": reg["samples"]["negative_pass"],
    "flips_match": sorted(their_flips) == sorted(my_flips),
    "their_no_relaxation": reg["no_relaxation"],
}
print("  cross_check:", json.dumps(OUT["regression32"]["cross_check"], ensure_ascii=False))

# ---------------------------------------------------------------------------
# (5) 准入 7 条：有没有可执行的准入校验器？
# ---------------------------------------------------------------------------
print("\n=== (5) 准入标准可执行性 ===")
pred_src = R9S.read_text(encoding="utf-8")
design_src = design.read_text(encoding="utf-8")
admit_names = re.findall(r"def\s+(\w*(?:admit|admission|validate_spec|check_spec|register_spec)\w*)\s*\(",
                         pred_src, re.I)
OUT["admission"] = {
    "predicate_source": str(R9S.relative_to(ROOT)),
    "admission_function_defs_found": admit_names,
    "specs_size": len(r9s.SPECS),
    "has_exact_dict_lookup": "SPECS.get(token)" in pred_src,
    "has_fuzzy": bool(re.search(r"editdistance|difflib|embedding|SequenceMatcher|fuzzy", pred_src, re.I)),
    "design_has_7_rules": all(("%d." % i) in design_src for i in range(1, 8)),
    "design_section": "§2.4 (line 145-159)",
    "code_functions": re.findall(r"^def\s+(\w+)", pred_src, re.M),
}
print("  admission_function_defs_found =", admit_names)
print("  specs_size =", len(r9s.SPECS), " exact_dict_lookup =", OUT["admission"]["has_exact_dict_lookup"],
      " has_fuzzy =", OUT["admission"]["has_fuzzy"])
print("  code_functions =", OUT["admission"]["code_functions"])

# 负样本数 vs 正样本数（自读 samples 源码统计，不跑撰写人 regress）
samples_src = (WDIR / "_r9s_samples.py").read_text(encoding="utf-8")
OUT["admission"]["sample_counts_in_source"] = {
    "POS_ids": len(re.findall(r'\{"id": "P\d\d"', samples_src)),
    "NEG_ids": len(re.findall(r'\{"id": "N\d\d"', samples_src)),
}
print("  sample_counts =", OUT["admission"]["sample_counts_in_source"])

# ---------------------------------------------------------------------------
# (6) 调用方逐个查（排除被核写域自身）
# ---------------------------------------------------------------------------
print("\n=== (6) 调用方逐个查 ===")
py_files = [p for p in (ROOT / "lead").rglob("*.py")
            if "gate_r9sem_20261109" not in str(p)]


def scan(pattern):
    hits = []
    rx = re.compile(pattern)
    for p in py_files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, l in enumerate(lines, 1):
            if rx.search(l):
                hits.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"), "line": i,
                             "text": l.strip()[:160]})
    return hits


r9e = scan(r"r9_element_present\s*\(")
r9c = scan(r"r9_check\s*\(")
cd = scan(r"check_deliverable\s*\(")
OUT["callers"] = {"r9_element_present": r9e, "r9_check": r9c, "check_deliverable": cd,
                  "counts": {"r9_element_present": len(r9e), "r9_check": len(r9c),
                             "check_deliverable": len(cd)}}
print("  counts =", OUT["callers"]["counts"])
print("  -- r9_element_present 直接调用（排除 _g7_predicates.py 内定义/文档串）--")
for h in r9e:
    print("     %s:%d  %s" % (h["file"], h["line"], h["text"][:130]))
print("  -- 指纹 pin 数（py/mjs/md 全 lead+.zcode）--")
pins = 0
for base in (ROOT / "lead", ROOT / ".zcode"):
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".py", ".mjs", ".md", ".txt", ".json"):
            continue
        try:
            if BASE9["lead/gate_fp7_20261108/_g7_predicates.py"][0] in p.read_text("utf-8", errors="replace"):
                pins += 1
        except Exception:
            pass
OUT["callers"]["g7_fingerprint_pins"] = pins
print("  g7_fingerprint_pins =", pins)

# ---------------------------------------------------------------------------
# (7) 越界检查
# ---------------------------------------------------------------------------
print("\n=== (7) 越界检查 ===")
stray = []
for p in (ROOT / "lead").rglob("*"):
    if not p.is_file():
        continue
    if p.name.startswith("_r9s_") or p.name.startswith("_r9sv_"):
        if WDIR not in p.parents:
            stray.append(str(p.relative_to(ROOT)))
OUT["boundary"] = {"stray_r9s_files_outside_wdir": stray,
                   "readonly9_unchanged": OUT["nine_fingerprints"]["all_match"],
                   "g7_unchanged": OUT["nine_fingerprints"]["rows"][5]["match"],
                   "g9_unchanged": OUT["nine_fingerprints"]["rows"][6]["match"],
                   "main32_drift": n_drift}
print("  stray =", stray)
print("  readonly9_unchanged =", OUT["boundary"]["readonly9_unchanged"],
      " g7 =", OUT["boundary"]["g7_unchanged"], " g9 =", OUT["boundary"]["g9_unchanged"],
      " main32_drift =", n_drift)

(WDIR / "_r9sv_verify_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nwrote _r9sv_verify_out.json")
