# -*- coding: utf-8 -*-
"""_r9sv_extra.py — 补充独立核验：撰写人负样本复跑、准入机制、调用方、绑定行惯例。"""
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(WDIR))
import _r9s_predicates as r9s
import _r9s_samples as S

OUT = {}

# --- (A) 撰写人 20 正 / 24 负样本：我自己逐条跑当前谓词 ---
print("=== (A) 撰写人样本集独立复跑 ===")
rows = []
for s in S.SAMPLES:
    ok, layer, _ = r9s.r9s_element_present(s["text"], s["token"])
    rows.append({"id": s["id"], "token": s["token"], "expect": s["expect"],
                 "present": ok, "layer": layer, "pass": ok == s["expect"]})
pos = [x for x in rows if x["expect"]]
neg = [x for x in rows if not x["expect"]]
OUT["their_samples"] = {
    "n_pos": len(pos), "pos_pass": sum(1 for x in pos if x["pass"]),
    "n_neg": len(neg), "neg_pass": sum(1 for x in neg if x["pass"]),
    "all_pass": all(x["pass"] for x in rows),
    "failed_ids": [x["id"] for x in rows if not x["pass"]],
}
print("  POS %d/%d  NEG %d/%d all_pass=%s failed=%s"
      % (OUT["their_samples"]["pos_pass"], len(pos),
         OUT["their_samples"]["neg_pass"], len(neg),
         OUT["their_samples"]["all_pass"], OUT["their_samples"]["failed_ids"]))

# 负样本与守卫词表的共设计程度：NEG 文本里出现守卫词的条数
guard_words = ["待指定", "尚未", "无需批准", "待验", "输出未采集", "PROBE_DONE", "详见",
               "索引", "TBD", "待定", "略。", "不可重建", "待补", "未验", "无输出",
               "待确认", "见附件", "需进一步"]
n_with_guard = 0
for s in S.NEG:
    if any(w in s["text"] for w in guard_words):
        n_with_guard += 1
OUT["their_samples"]["neg_with_guard_vocabulary"] = n_with_guard
OUT["their_samples"]["neg_without_guard_vocabulary"] = len(neg) - n_with_guard
print("  NEG 中含现成守卫词/占位词 = %d/%d；不含 = %d"
      % (n_with_guard, len(neg), len(neg) - n_with_guard))
for s in S.NEG:
    if not any(w in s["text"] for w in guard_words):
        print("     不含守卫词的 NEG: %s %s —— %s" % (s["id"], s["token"], s["text"][:100].replace("\n", " | ")))

# --- (B) 未登记 token：R9S ≡ R9 ---
print("\n=== (B) 未登记 token 等价性 ===")
probe = "## 1 声明\n本撰写会话未修改任何既有文件，门禁代码零改动。\n"
for tok in ["未改 _c7_selfcheck.py", "APPROVE_SCOPE", "「被核对象」", "任意新词"]:
    a = r9s.R9.r9_element_present(probe, tok)
    b = r9s.r9s_element_present(probe, tok)
    same = (a[0] == b[0] and a[1] == b[1])
    print("  %-24s R9=%s R9S=(%s,%r) identical=%s" % (tok, a, b[0], b[1], same))
OUT["unregistered_equivalent"] = True

# --- (C) 准入标准：有无强制执行代码 ---
print("\n=== (C) 准入 7 条有无执行器 ===")
src = (WDIR / "_r9s_predicates.py").read_text("utf-8")
design = (WDIR / "_r9s_DESIGN.md").read_text("utf-8")
# 精确查「实际 import / 调用」而非注释里的字样
imports = re.findall(r"^\s*(?:import|from)\s+([\w\.]+)", src, re.M)
calls = re.findall(r"\b(difflib|SequenceMatcher|editdistance|fuzzywuzzy|rapidfuzz|embedding)\s*\(", src)
OUT["admission"] = {
    "imports": imports,
    "fuzzy_library_calls": calls,
    "has_admission_validator": bool(re.search(r"def\s+\w*(?:admit|admission|validate_spec|check_spec|register_spec)\w*\s*\(", src, re.I)),
    "exact_dict_lookup_lines": [i + 1 for i, l in enumerate(src.splitlines()) if "SPECS.get(token)" in l],
    "specs_keys": list(r9s.SPECS.keys()),
    "rules_in_design": [i for i in range(1, 8) if re.search(r"^%d\.\s" % i, design, re.M)],
}
print("  imports =", imports)
print("  fuzzy_library_calls =", calls)
print("  has_admission_validator =", OUT["admission"]["has_admission_validator"])
print("  exact_dict_lookup_lines =", OUT["admission"]["exact_dict_lookup_lines"])
print("  specs_keys =", OUT["admission"]["specs_keys"])
print("  rules_in_design (numbered lines found) =", OUT["admission"]["rules_in_design"])

# --- (D) 4 域升级后 gateProblems 剩余（自己算，不采信 (B) 段） ---
print("\n=== (D) 4 域剩余问题独立计算 ===")
B = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_text("utf-8"))
FOUR = ("lead/matrix_ab_ruling_20261109/", "lead/matrix_reach_20261109/",
        "lead/n11_wording_fix_20261108/", "lead/s604_script_gap_20261109/")
reg = json.loads((WDIR / "_r9s_regress_out.json").read_text("utf-8"))
elems_by = {x["domain"]: x["elements"] for x in reg["four_domains"]}
four = []
for r in B["rows"]:
    if r["domain"] not in FOUR:
        continue
    p = ROOT / r["domain"].rstrip("/") / r["main"]
    t = p.read_text("utf-8", errors="replace")
    els = elems_by[r["domain"]]
    probs, _ = r9s.r9s_check(t, els)
    missing = [x for x in probs if x.startswith("缺要素")]
    other = [x for x in r["gateProblems"] if not x.startswith("缺要素")]
    rec = {"domain": r["domain"], "baseline": r["gateProblems"],
           "r9s_missing": missing, "non_element_baseline": other,
           "remaining": missing + other}
    four.append(rec)
    print("  %-46s baseline=%d r9s_missing=%d remaining=%d %s"
          % (r["domain"], len(r["gateProblems"]), len(missing),
             len(rec["remaining"]), json.dumps(rec["remaining"], ensure_ascii=False)[:200]))
OUT["four_domains"] = four
OUT["four_domains_total_remaining"] = sum(len(x["remaining"]) for x in four)
print("  total remaining =", OUT["four_domains_total_remaining"])

# --- (E) 调用方清单（含一个被 harness 隐去名字的文件） ---
print("\n=== (E) gate_fp7 目录文件 & r9_element_present 调用方 ===")
for p in sorted((ROOT / "lead/gate_fp7_20261108").glob("*.py")):
    print("   ", p.name)
OUT["caller_files"] = [p.name for p in sorted((ROOT / "lead/gate_fp7_20261108").glob("*.py"))]

# --- (F) 复核回件绑定行惯例：查历史复核回件绑的是什么 ---
print("\n=== (F) 历史复核回件绑定行惯例抽样 ===")
pat = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
found = []
for p in (ROOT / "lead").rglob("*.md"):
    try:
        t = p.read_text("utf-8", errors="replace")
    except Exception:
        continue
    if "复核" not in t[:1500]:
        continue
    for m in pat.finditer(t):
        # 找该行前后 200 字，看有没有描述对象
        seg = t[max(0, m.start() - 300):m.end() + 200]
        found.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "hex": m.group(1), "bytes": int(m.group(2)),
                      "context": seg[:260].replace("\n", " | ")})
        break
    if len(found) >= 8:
        break
for f in found:
    print("  %-58s %s/%d" % (f["file"][:58], f["hex"][:12], f["bytes"]))
    print("      ctx:", f["context"][:230])
OUT["binding_line_precedents"] = found

(WDIR / "_r9sv_extra_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nwrote _r9sv_extra_out.json")
