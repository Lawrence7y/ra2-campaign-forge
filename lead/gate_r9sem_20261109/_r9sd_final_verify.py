# -*- coding: utf-8 -*-
r"""_r9sd_final_verify.py — 交付件 GATE_R9_SEMANTIC_ELEMENT.md 的自跑支撑（只读核验）。

零真机、零采样代码；Python = python -I -X utf8 + 绝对路径；指纹用 hashlib。
写域只落 _r9sd_final_out.json / _r9sd_final_stdout.txt。
内容：
 (1) 九件派发指纹自算 + 被核对象绑定行实算
 (2) 5 处独立 R9 复现（自实现 r9_normalize / r9_element_present，与只读 g7 交叉校验）
 (3) 复核回件 7 条近似负样本复跑（V1..V7，逐字照录 _r9sv_verify.py:150-225）
 (4) 撰写人 POS20/NEG24 复跑 + 4 域 + 32 域/302 项不放松（独立重算翻案）
 (5) 调用方计数（纯 Python 扫文件，无 shell）+ 最小改动 diff 行数 + 绑定行严格格式自检
 (6) 越界：写域外无 _r9sd_ 产物；9 件收尾复算
"""
from __future__ import annotations

import ast
import difflib
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(WDIR))
import _r9s_predicates as R9S  # noqa: E402
import _r9s_samples as S  # noqa: E402

OUT: dict = {}
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


def fp9():
    rows = []
    for rel, (h, b) in BASE9.items():
        d = (ROOT / rel).read_bytes()
        got_h, got_b = hashlib.sha256(d).hexdigest(), len(d)
        rows.append({"file": rel, "sha256": got_h, "bytes": got_b, "match": got_h == h and got_b == b})
    return {"rows": rows, "all_match": all(x["match"] for x in rows)}


print("=== (1) 九件派发指纹自算 ===")
f0 = fp9()
for x in f0["rows"]:
    print("  %-5s %-60s %s %d" % ("MATCH" if x["match"] else "DRIFT", x["file"][:60], x["sha256"][:16], x["bytes"]))
print("  all_match =", f0["all_match"])
OUT["fingerprints_start"] = f0
obj = (ROOT / "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md").read_bytes()
print("  binding_object: sha256 = %s bytes = %d" % (hashlib.sha256(obj).hexdigest(), len(obj)))
OUT["binding_object"] = {"sha256": hashlib.sha256(obj).hexdigest(), "bytes": len(obj)}

# --- (2) 独立 R9 实现（依据实读 _g7_predicates.py:31-53） ---
_WRAP_CHARS = "`\u00b4\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f"


def my_norm(text):
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`", text):
        out.append(text[pos:m.start()])
        out.append(m.group(1).replace("\n", "").replace("\r", ""))
        pos = m.end()
    out.append(text[pos:])
    return "".join(" " if ch in _WRAP_CHARS else ch for ch in "".join(out))


def my_r9(text, token):
    if token in text:
        return True, "raw"
    if token in my_norm(text):
        return True, "normalized"
    return False, ""


CASES = [
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md", "需谁批准", 108),
    ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", "实跑输出", 65),
    ("lead/n11_wording_fix_20261108/N11_WORDING_FIX.md", "改前改后", 76),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "脚本存在性", 32),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "可重建", 87),
]
print("\n=== (2) 5 处独立 R9 复现 ===")
case_rows = []
for rel, tok, ln in CASES:
    text = (ROOT / rel).read_text(encoding="utf-8")
    lit = tok in text
    mine = my_r9(text, tok)
    g7 = R9S.R9.r9_element_present(text, tok)
    r9s = R9S.r9s_element_present(text, tok)
    line = text.splitlines()[ln - 1]
    rec = {"rel": rel, "token": tok, "line": ln, "lineText": line,
           "literal_present": lit, "r9_mine": list(mine), "r9_g7": list(g7),
           "r9s_present": r9s[0], "r9s_layer": r9s[1]}
    case_rows.append(rec)
    print("  %-10s literal=%-5s mine=%-18s g7=%-18s r9s=(%s,%s)"
          % (tok, lit, str(mine), str(g7), r9s[0], r9s[1] or "(none)"))
    print("     L%d: %s" % (ln, line[:110]))
allfalse = all(not x["literal_present"] and x["r9_mine"] == [False, ""]
               and x["r9_g7"] == [False, ""] for x in case_rows)
print("  all_false =", allfalse)
OUT["five_cases"] = case_rows
OUT["five_all_false"] = allfalse

# --- (3) 复核回件 7 条近似负样本（逐字照录 _r9sv_verify.py:150-225） ---
NEAR = [
    ("V1", "实跑输出", "## 3 五处缺陷逐处可达性实证\n"
     "### 3.1 W1\n"
     "- **构造输入 → 实跑返回**：classify 直调，pre 八变体 × read_error 两型，16/16 格实跑：\n"
     "```\n"
     "（本轮已实跑并记录，全部 16 格返回值见 _mr_probe1_out.txt:159-174）\n"
     "```\n"
     "- **落哪一行 / 与矩阵声称是否一致**：16/16，out:159-174；已实跑并记录，输出不再重列。\n"),
    ("V2", "需谁批准", "## 5 裁决与可执行改动清单\n"
     "### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n"
     "改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n"),
    ("V3", "改前改后", "## 4 订正草案（改前/改后逐处对照）\n"
     "### 4.1 方案 A（最小改动·推荐）\n"
     "- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。\n"
     "- 【改后】改后句见方案 B 的对应行，本件不重录。\n"
     "- 【要点】只换「一一对应」→「逐项对应」并插入拆分括注。\n"),
    ("V4", "脚本存在性", "## 3 脚本搜索全结果与存在性判定（四路逐路）\n"
     "### 3.1 路线一：文件名搜索【本轮实跑】\n"
     "全树 .py 共 11790 个，逐路结论：未见生成器命名痕迹。\n"
     "### 3.2 路线二：内容搜索\n"
     "命中 32 件，均属事后复核件。\n"
     "### 3.5 存在性判定\n"
     "**判定：生成脚本的存在状况以台账 §604 记载为准，本件不另下结论。**\n"),
    ("V5", "可重建", "## 4 重建可行性与单向压缩候选筛选\n"
     "### 4.1 正确算法：五项口径唯一性\n"
     "| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n"
     "**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** "
     "已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
    ("V6", "可重建", "## 4 重建可行性与单向压缩候选筛选\n"
     "### 4.1 正确算法：五项口径唯一性\n"
     "**判定：正确算法并非【可唯一重建】。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
    ("V7", "脚本存在性", "## 3 脚本搜索全结果与存在性判定（四路逐路）\n"
     "### 3.5 存在性判定\n"
     "**判定：生成脚本存在性以台账 §604 记载为准，本件不另下结论。**\n"),
]
print("\n=== (3) 复核回件 7 条近似负样本复跑（期望全 False） ===")
near_rows = []
for vid, tok, txt in NEAR:
    ok, layer, detail = R9S.r9s_element_present(txt, tok)
    r9ok, r9layer = my_r9(txt, tok)
    ev = detail.get("evidence", [])
    rec = {"id": vid, "token": tok, "expect": False, "r9s_present": ok, "r9s_layer": layer,
           "r9_present": r9ok, "r9_layer": r9layer, "caught": (ok is False),
           "evidence": ev}
    near_rows.append(rec)
    print("  %-3s %-8s r9=(%s,%s) r9s=(%s,%s) caught=%s"
          % (vid, tok, r9ok, r9layer or "(none)", ok, layer or "(none)", rec["caught"]))
    if ok:
        print("     !! 漏抓 evidence =", json.dumps(ev, ensure_ascii=False)[:220])
n5 = sum(1 for x in near_rows[:5] if x["caught"])
a7 = all(x["caught"] for x in near_rows)
print("  V1..V5 caught = %d/5  all_7_caught = %s" % (n5, a7))
OUT["near_miss"] = {"rows": near_rows, "v1_v5_caught": n5, "all_7_caught": a7}

# --- (4) 撰写人样本集 + 4 域 + 32 域独立重算 ---
print("\n=== (4) POS/NEG + 4 域 + 32 域不放松 ===")
sample_rows = []
for s in S.SAMPLES:
    ok, layer, _d = R9S.r9s_element_present(s["text"], s["token"])
    sample_rows.append({"id": s["id"], "expect": s["expect"], "present": ok,
                        "pass": ok == s["expect"]})
pos_n = sum(1 for x in sample_rows if x["expect"])
neg_n = sum(1 for x in sample_rows if not x["expect"])
pos_pass = sum(1 for x in sample_rows if x["expect"] and x["pass"])
neg_pass = sum(1 for x in sample_rows if not x["expect"] and x["pass"])
allpass = pos_pass == pos_n and neg_pass == neg_n
print("  POS %d/%d  NEG %d/%d  all_pass=%s" % (pos_pass, pos_n, neg_pass, neg_n, allpass))
OUT["samples"] = {"positive": pos_n, "negative": neg_n, "positive_pass": pos_pass,
                  "negative_pass": neg_pass, "all_pass": allpass, "rows": sample_rows}

BASE = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}
LOOP_RE = re.compile(r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)")


def gate_src(low):
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    if k < 0 or end < 0:
        return ""
    body = low[k + len("const GATE_CODE = ["):end]
    parts = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else ""


def elements_of(r):
    p = RUNS.get(r["run"])
    elems = []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        if i >= 0:
            low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
            src = gate_src(low.get("lowered", ""))
            for m in LOOP_RE.finditer(src):
                try:
                    elems += ast.literal_eval(m.group(2))
                except Exception:
                    pass
    return [x for x in elems if x]


WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
FOUR = {d for d, _ in WHITELIST}
four_rows = []
for r in ROWS:
    if r["domain"] not in FOUR:
        continue
    mp = ROOT / r["domain"].rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace")
    elems = elements_of(r)
    p9, _ = R9S.R9.r9_check(text, elems)
    p9s, w9s = R9S.r9s_check(text, elems)
    m9 = [x for x in p9 if x.startswith("缺要素")]
    m9s = [x for x in p9s if x.startswith("缺要素")]
    other = [x for x in r["gateProblems"] if not x.startswith("缺要素")]
    remaining = m9s + other
    four_rows.append({"domain": r["domain"], "r9_missing": m9, "r9s_missing": m9s,
                      "remaining": remaining})
    print("  %-46s R9缺=%d R9S缺=%d 剩余=%d %s"
          % (r["domain"], len(m9), len(m9s), len(remaining),
             json.dumps(remaining, ensure_ascii=False)[:90]))
OUT["four_domains"] = four_rows
print("  4 域剩余缺要素 =", sum(len(x["r9s_missing"]) for x in four_rows))

flips, tightens, n_items, n_identical, main_missing = [], [], 0, 0, []
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    if not mp.is_file():
        main_missing.append(dom)
        continue
    text = mp.read_text(encoding="utf-8", errors="replace")
    for k in elements_of(r):
        n_items += 1
        ok0, lay0 = R9S.R9.r9_element_present(text, k)
        ok1, lay1, _ = R9S.r9s_element_present(text, k)
        if ok0 == ok1 and lay0 == lay1:
            n_identical += 1
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST})
        if ok0 and (not ok1):
            tightens.append({"domain": dom, "token": k})
outside = [f for f in flips if not f["whitelisted"]]
norelax = len(outside) == 0 and len(flips) == len(WHITELIST)
print("  n_domains=%d n_items=%d identical=%d changed=%d main_missing=%s"
      % (len(ROWS), n_items, n_identical, n_items - n_identical, json.dumps(main_missing)))
print("  n_flips=%d outside_whitelist=%d n_tightens=%d no_relaxation=%s"
      % (len(flips), len(outside), len(tightens), norelax))
for f in flips:
    print("     FLIP %-46s %-10s whitelisted=%s" % (f["domain"], f["token"], f["whitelisted"]))
OUT["domains32"] = {"n_domains": len(ROWS), "n_items": n_items,
                    "identical": n_identical, "changed": n_items - n_identical,
                    "main_missing": main_missing, "flips": flips, "tightens": tightens,
                    "outside_whitelist": outside, "no_relaxation": norelax}

# --- (5) 调用方计数（纯 Python 扫文件，无 shell）+ diff + 绑定行严格格式 ---
print("\n=== (5) 调用方 / 最小改动 / 绑定行格式 ===")
FP = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
py_files = list((ROOT / "lead").rglob("*.py"))
mjs_files = list((ROOT / "lead").rglob("*.mjs")) + list((ROOT / ".zcode").rglob("*.mjs"))
pin_files = 0
for p in py_files + list((ROOT / ".zcode").rglob("*.py")) + mjs_files:
    try:
        if FP in p.read_text(encoding="utf-8", errors="replace"):
            pin_files += 1
    except OSError:
        pass


def count_lines(needle):
    n = 0
    for p in py_files:
        try:
            n += sum(1 for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
                     if needle in ln)
        except OSError:
            pass
    return n


r9ep = count_lines("r9_element_present")
r9chk = count_lines("r9_check")
cd = count_lines("check_deliverable")
print("  g7_fp_pin_files(py+mjs,lead+.zcode) = %d ; r9_element_present_lines=%d r9_check_lines=%d check_deliverable_lines=%d"
      % (pin_files, r9ep, r9chk, cd))
OUT["caller_counts"] = {"g7_fp_pin_files": pin_files, "r9_element_present_lines": r9ep,
                        "r9_check_lines": r9chk, "check_deliverable_lines": cd}

# 复核口径：排除本写域后，按「函数名 + 可选空白 + (」正则计调用点（_r9sv_verify.py:426-451）
scan_files = [p for p in py_files if WDIR not in p.parents]


def scan_calls(pattern):
    rx = re.compile(pattern)
    hits = []
    for p in scan_files:
        try:
            for i, l in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(l):
                    hits.append((str(p.relative_to(ROOT)).replace("\\", "/"), i))
        except OSError:
            pass
    return hits


n_r9e = len(scan_calls(r"r9_element_present\s*\("))
n_r9c = len(scan_calls(r"r9_check\s*\("))
n_cd = len(scan_calls(r"check_deliverable\s*\("))
print("  (reviewer口径, 排除写域) r9_element_present=%d r9_check=%d check_deliverable=%d"
      % (n_r9e, n_r9c, n_cd))
OUT["caller_counts_reviewer_style"] = {"r9_element_present": n_r9e, "r9_check": n_r9c,
                                       "check_deliverable": n_cd}

# 复核撰写人称 grep -rl 指纹 --include=*.py --include=*.mjs lead .zcode | wc -l = 46 的可复现性
pin46_files = [p for p in py_files + mjs_files + list((ROOT / ".zcode").rglob("*.py"))
               if p.suffix.lower() in (".py", ".mjs")]
pin46 = sum(1 for p in set(pin46_files)
            if FP in p.read_text(encoding="utf-8", errors="replace"))
print("  (pin 46 复现口径, py+mjs, lead+.zcode) count =", pin46)

orig = (ROOT / "lead/gate_r9r12_20261109/_g9_gate.py").read_text(encoding="utf-8").splitlines()
cand = (WDIR / "_r9s_g9_candidate.py").read_text(encoding="utf-8").splitlines()
diff = list(difflib.unified_diff(orig, cand, lineterm=""))
changed_hunks = sum(1 for x in diff if x.startswith("@@"))
print("  minpatch unified_diff lines=%d hunks=%d" % (len(diff), changed_hunks))
OUT["minpatch_diff"] = {"lines": len(diff), "hunks": changed_hunks}

design = (WDIR / "_r9s_DESIGN.md").read_text(encoding="utf-8")
strict = re.compile(r"^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$", re.M)
ms = strict.findall(design)
print("  design strict binding matches =", len(ms), ms)
OUT["design_binding_strict"] = {"n": len(ms), "lines": ms}
OUT["spec_inventory"] = R9S.spec_inventory()

# --- (6) 收尾九件复算 + 越界 ---
f1 = fp9()
stray = [str(p.relative_to(ROOT)) for p in (ROOT / "lead").rglob("_r9sd_*")
         if WDIR not in p.parents]
print("\n=== (6) 收尾 ===")
print("  readonly_9_unchanged =", f1["all_match"])
print("  stray_r9sd_files_outside_wdir =", json.dumps(stray))
OUT["fingerprints_end"] = f1
OUT["stray"] = stray
(WDIR / "_r9sd_final_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1),
                                           encoding="utf-8", newline="\n")
print("wrote _r9sd_final_out.json")
