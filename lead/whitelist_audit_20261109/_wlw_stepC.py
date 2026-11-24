# -*- coding: utf-8 -*-
r"""_wlw_stepC.py — 撰写会话（actor#3）独立复跑，全部产物只落唯一写域，前缀 _wlw_。

不 import _r9s_regress.py（它在只读域覆写 _r9s_regress_out.json）。
只 import 被测谓词 _r9s_predicates.py / _r9s_samples.py / _rj_delivery_baseline.json（只读）。
自行实现 32 域 302 项复算、292 数字、CF 对抗样本、逐行 == 比对、样本构成比例。
"""
from __future__ import annotations
import ast, hashlib, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RDIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
BASE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"
MJS = ROOT / ".zcode" / "workflow-runs"
sys.path.insert(0, str(RDIR))
import _r9s_predicates as R9S
import _r9s_samples as SM

R9 = R9S.R9
OUT = {}

# ---------- (1) 正负样本 44 条逐条独立实跑 ----------
rows = []
for s in SM.SAMPLES:
    ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
    rows.append({"id": s["id"], "token": s["token"], "expect": s["expect"],
                 "actual": bool(ok), "layer": layer or "(none)",
                 "pass": bool(ok) == bool(s["expect"])})
pos = [r for r in rows if r["expect"]]
neg = [r for r in rows if not r["expect"]]
OUT["samples"] = {
    "rows": rows,
    "pos_pass": sum(1 for r in pos if r["pass"]), "pos_n": len(pos),
    "neg_pass": sum(1 for r in neg if r["pass"]), "neg_n": len(neg),
    "all_pass": all(r["pass"] for r in rows),
}
print("=== (1) samples ===")
print("  POS %d/%d  NEG %d/%d  all_pass=%s" % (
    OUT["samples"]["pos_pass"], len(pos), OUT["samples"]["neg_pass"], len(neg), OUT["samples"]["all_pass"]))

# ---------- (2) 32 域 / 302 项 / 翻案 5 / 白名单外 0 独立复算 ----------
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
base = json.loads(BASE.read_text(encoding="utf-8"))
ROWS = base["rows"]
mjs_by_name = {p.name: p for p in MJS.glob("*.mjs")}

def gate_src_of(mjs_path):
    t = mjs_path.read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    if i < 0:
        return ""
    low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    s = low.get("lowered", "")
    k = s.find("const GATE_CODE = [")
    if k < 0:
        return ""
    m = re.search(r"\]\s*\.join", s[k:])
    if not m:
        return ""
    body = s[k + len("const GATE_CODE = ["): k + m.start()]
    parts = []
    for sm2 in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + sm2.group(1) + '"'))
        except Exception:
            parts.append(sm2.group(1))
    return "\n".join(parts)

LOOP_RE = re.compile(
    r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)"
)

def elems_of(row):
    elems = []
    run = row.get("run", "")
    p = mjs_by_name.get(run)
    if p is None:
        cand = [q for q in MJS.glob("*.mjs") if run and run in q.name]
        p = cand[0] if cand else None
    if p is None:
        return []
    src = gate_src_of(p)
    for m2 in LOOP_RE.finditer(src):
        try:
            elems += ast.literal_eval(m2.group(2))
        except Exception:
            pass
    return [x for x in elems if x]

all_rows, flips, tightens = [], [], []
n_items = 0
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace") if mp.is_file() else ""
    es = elems_of(r)
    n_items += len(es)
    ch = []
    for k in es:
        r9ok, r9layer = R9.r9_element_present(text, k)
        r9sok, r9slayer, _ = R9S.r9s_element_present(text, k)
        rec = {"domain": dom, "token": k, "r9": bool(r9ok), "r9_layer": r9layer,
               "r9s": bool(r9sok), "r9s_layer": r9slayer}
        all_rows.append(rec)
        if r9ok != r9sok:
            if r9sok and not r9ok:
                rec["whitelisted"] = (dom, k) in WHITELIST
                flips.append(rec)
            else:
                tightens.append(rec)
outside = [f for f in flips if not f["whitelisted"]]
no_relax = (len(outside) == 0 and len(flips) == len(WHITELIST)
            and all(f["whitelisted"] for f in flips))
OUT["regress"] = {
    "n_domains": len(ROWS), "n_items": n_items, "rows": all_rows,
    "flips": flips, "n_flips": len(flips), "tightens": tightens,
    "outside": outside, "no_relaxation": no_relax,
}
print("\n=== (2) 32-domain regression ===")
print("  n_domains=%d n_items=%d n_flips=%d outside=%d n_tightens=%d no_relaxation=%s" % (
    len(ROWS), n_items, len(flips), len(outside), len(tightens), no_relax))
for f in flips:
    print("     FLIP %-46s %-12s whitelisted=%s" % (f["domain"], f["token"], f["whitelisted"]))

# ---------- (3) 292 vs 297 数字独立实算 ----------
spec_tokens = set(R9S.SPECS.keys())
registered = [x for x in all_rows if x["token"] in spec_tokens]
unregistered = [x for x in all_rows if x["token"] not in spec_tokens]
OUT["numbers"] = {
    "n_items": n_items, "registered_occurrences": len(registered),
    "unregistered_items": len(unregistered),
    "distinct_unregistered_tokens": len({x["token"] for x in unregistered}),
    "n_items_minus_5": n_items - 5, "n_items_minus_10": n_items - 10,
    "outside_whitelist_registered": [x for x in registered if (x["domain"], x["token"]) not in WHITELIST],
}
print("\n=== (3) numbers ===")
print("  n_items=%d registered=%d unregistered=%d distinct_unreg=%d 302-5=%d 302-10=%d" % (
    n_items, len(registered), len(unregistered), OUT["numbers"]["distinct_unregistered_tokens"],
    n_items - 5, n_items - 10))
for x in OUT["numbers"]["outside_whitelist_registered"]:
    print("     outsideWL registered: %-46s %-12s r9=%s r9s=%s" % (
        x["domain"], x["token"], x["r9"], x["r9s"]))

# ---------- (4) 对抗样本 CF1–CF5（撰写人原样）+ 我另措辞 WCF1–WCF5 ----------
CF = [
 ("CF1", "需谁批准", "## 5 改动清单\n批准人待定，需谁批准尚需确认，顺序不可倒。\n"),
 ("CF2", "实跑输出", "## 3 可达性\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 结论详见后续附件。\n"),
 ("CF3", "改前改后", "## 4 订正草案（改前/改后逐处对照）\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n"),
 ("CF4", "脚本存在性", "## 3 搜索\n脚本存在性待查，本件不另下结论。\n"),
 ("CF5", "可重建", "## 4 重建可行性\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n五项口径表见上节。\n"),
]
WCF = [
 ("WCF1", "需谁批准", "## 5 改动清单\n本次改动的批准人尚未确定，由谁批准仍需后续确认。\n"),
 ("WCF2", "实跑输出", "## 3 可达性\n16/16 格已实跑完成，返回值详见附件，正文未列出。\n"),
 ("WCF3", "改前改后", "## 4 订正草案\n【改前】详见台账登记。\n【改后】见台账登记，本件不重录。\n逐处对照表另附。\n"),
 ("WCF4", "脚本存在性", "## 3 判定\n该脚本是否在盘，以台账记载为准，本件不另下结论。\n"),
 ("WCF5", "可重建", "## 4 重建可行性\n是否【可唯一重建】尚需核对，本件暂不作判定。\n五项口径表见上节。\n"),
]
def run_cf(name, tok, text):
    r9ok, r9l = R9.r9_element_present(text, tok)
    r9sok, r9sl, detail = R9S.r9s_element_present(text, tok)
    return {"id": name, "token": tok, "text": text,
            "r9": bool(r9ok), "r9_layer": r9l or "(none)",
            "r9s": bool(r9sok), "r9s_layer": r9sl or "(none)",
            "misjudged": bool(r9sok), "detail": detail}
cf_rows = [run_cf(*c) for c in CF]
wcf_rows = [run_cf(*c) for c in WCF]
OUT["counterfactual"] = {"CF": cf_rows, "WCF": wcf_rows}
print("\n=== (4) counterfactual ===")
for r in cf_rows + wcf_rows:
    print("  %-5s %-12s R9=%s/%-9s R9S=%s/%-9s misjudged=%s" % (
        r["id"], r["token"], r["r9"], r["r9_layer"], r["r9s"], r["r9s_layer"], r["misjudged"]))
print("  CF misjudged = %d/5   ids=%s" % (
    sum(1 for r in cf_rows if r["misjudged"]), [r["id"] for r in cf_rows if r["misjudged"]]))
print("  WCF misjudged = %d/5  ids=%s" % (
    sum(1 for r in wcf_rows if r["misjudged"]), [r["id"] for r in wcf_rows if r["misjudged"]]))

# ---------- (5) 白名单机制：1 条错 & 5 条全换语义空，公式实跑 ----------
def verdict_of(flips_now, wl_now):
    outside_now = [f for f in flips_now if (f["domain"], f["token"]) not in wl_now]
    nr = (len(outside_now) == 0 and len(flips_now) == len(wl_now)
          and all((f["domain"], f["token"]) in wl_now for f in flips_now))
    return nr, "PASS" if (OUT["samples"]["all_pass"] and nr) else "FAIL", len(outside_now)
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
# 用替换后的文本重算 flips（不改盘上文件，仅内存）
flips_empty = []
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace") if mp.is_file() else ""
    for k in elems_of(r):
        txt2 = EMPTY.get((dom, k), text) if k in R9S.SPECS else text
        r9ok, _ = R9.r9_element_present(txt2, k)
        r9sok, _, _ = R9S.r9s_element_present(txt2, k)
        if r9ok != r9sok:
            if r9sok and not r9ok:
                flips_empty.append({"domain": dom, "token": k, "semantic_empty": (dom, k) in EMPTY})
            else:
                pass  # tighten, not part of this counterfactual
nr_e, vd_e, out_e = verdict_of(flips_empty, set(WHITELIST))
OUT["selfproof"] = {"n_flips": len(flips_empty), "flips": flips_empty,
                    "no_relaxation": nr_e, "verdict": vd_e, "outside": out_e}
print("\n=== (5) selfproof (all 5 replaced with semantically-empty text) ===")
for f in flips_empty:
    print("     FLIP %-46s %-12s semantic_empty=%s" % (f["domain"], f["token"], f["semantic_empty"]))
print("  n_flips=%d outside=%d no_relaxation=%s VERDICT=%s" % (
    len(flips_empty), out_e, nr_e, vd_e))

# 1 条错（仍翻案，白名单不动）推演，5/5
one_wrong = []
for f in flips:
    nr, vd, o = verdict_of(flips, set(WHITELIST))
    one_wrong.append({"wrong": [f["domain"], f["token"]], "verdict": vd, "outside": o, "no_relaxation": nr})
OUT["one_wrong"] = one_wrong
print("  one-wrong cases (whitelist unchanged): " + ", ".join("%s=%s" % (x["wrong"][1], x["verdict"]) for x in one_wrong))
# 移除 / 加项
wl_minus = set(WHITELIST) - {("lead/matrix_ab_ruling_20261109/", "需谁批准")}
nr_m, vd_m, o_m = verdict_of(flips, wl_minus)
wl_plus = set(WHITELIST) | {("lead/x/", "dummy")}
nr_p, vd_p, o_p = verdict_of(flips, wl_plus)
OUT["set_sensitivity"] = {"remove_one": {"no_relaxation": nr_m, "verdict": vd_m, "outside": o_m},
                          "add_one": {"no_relaxation": nr_p, "verdict": vd_p, "outside": o_p}}
print("  remove 1 whitelist item -> outside=%s no_relaxation=%s VERDICT=%s" % (o_m, nr_m, vd_m))
print("  add 1 whitelist item    -> outside=%s no_relaxation=%s VERDICT=%s" % (o_p, nr_p, vd_p))

# ---------- (6) 五项主件逐字原文 + 围栏块逐行 == 比对 ----------
CASES = [
 ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md", [108, 138, 223, 235]),
 ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", [65, 68, 69, 70, 71, 74]),
 ("lead/n11_wording_fix_20261108/N11_WORDING_FIX.md", [76, 81, 82, 83, 88, 89, 90, 97]),
 ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", [32, 44, 51, 59, 67, 69, 71, 73, 77, 87, 89, 115, 116]),
]
quotes = {}
for rel, nums in CASES:
    L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    quotes[rel] = {str(n): L[n-1] if 1 <= n <= len(L) else "<OOR>" for n in nums}
OUT["quotes"] = quotes
deliv = (ROOT / "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md").read_text(encoding="utf-8").splitlines()
probe = (ROOT / "lead/matrix_reach_20261109/_mr_probe1_out.txt").read_text(encoding="utf-8", errors="replace").splitlines()
fence = []
for dn, pn in [(69, 159), (70, 169), (71, 173)]:
    fence.append({"delivery_line": dn, "probe_line": pn,
                  "equal": deliv[dn-1] == probe[pn-1],
                  "delivery_text": deliv[dn-1], "probe_text": probe[pn-1]})
OUT["fence"] = {"section_header_157": probe[156] if len(probe) >= 157 else "<OOR>", "rows": fence}
print("\n=== (6) fence-block line equality (delivery vs _mr_probe1_out.txt) ===")
print("  probe:157 = %s" % OUT["fence"]["section_header_157"])
for r in fence:
    print("  delivery:%d == probe:%d ? %s" % (r["delivery_line"], r["probe_line"], r["equal"]))

# ---------- (7) 样本构成：是否硬编码字面量 / 与真实主件整块逐字比对 ----------
src_samples = (RDIR / "_r9s_samples.py").read_text(encoding="utf-8")
real_files = {
 "P01": "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
 "P02": "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
 "P03": "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
 "P04": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "P05": "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
}
comp = {}
for p in [r for r in pos][:5]:
    pid = p["id"]
    s = next(x for x in SM.SAMPLES if x["id"] == pid)
    frag = s["text"]
    literal = frag in src_samples
    main = (ROOT / real_files[pid]).read_text(encoding="utf-8", errors="replace")
    whole = frag in main
    lines = [x for x in frag.splitlines() if x.strip()]
    hits = sum(1 for x in lines if x in main)
    comp[pid] = {"literal_in_samples_py": literal, "whole_block_in_main": whole,
                 "nonempty_lines": len(lines), "line_hits": hits}
OUT["sample_composition"] = {
    "pos_n": len(pos), "neg_n": len(neg),
    "pos_all_literal": all(s["text"] in src_samples for s in SM.POS),
    "neg_all_literal": all(s["text"] in src_samples for s in SM.NEG),
    "P01_P05": comp,
    "neg_approx": 21, "neg_obviously_different": 3,
    "neg_matching_guardword_13of24_ref": "_r9sv_extra_stdout.txt:3",
}
print("\n=== (7) sample composition ===")
print("  POS all hardcoded-literal = %s ; NEG all hardcoded-literal = %s" % (
    OUT["sample_composition"]["pos_all_literal"], OUT["sample_composition"]["neg_all_literal"]))
for pid, c in comp.items():
    print("  %s whole_block_in_main=%s line_hits=%d/%d" % (
        pid, c["whole_block_in_main"], c["line_hits"], c["nonempty_lines"]))

(WDIR / "_wlw_stepC_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wlw_stepC_out.json")
