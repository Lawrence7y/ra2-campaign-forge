"""_rsv_r5.py — step 8: probe the R5 refuting-quote exclusion of _rs_carrier_scan.py.
Import the author's classifier directly (read-only) and feed controlled synthetic
lines: true assertions, true refutations, and adversarial near-misses.
Run: python -I -X utf8 ".../_rsv_r5.py"
"""
import importlib.util, os, sys
P = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
spec = importlib.util.spec_from_file_location("cscan", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)   # read-only; does not execute main()

NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
CANON = "- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。"

# (label, line, expected_role family, note)
CASES = [
 ("A: bare assertion (should be ASSERTION)",
  "- **边界（如实）**：§604 内联生成脚本未落盘，只能判「不可复现」、不能定位当年错误步骤；本节只登记复算事实。", "ASSERTION"),
 ("B: §609 refuting quote inside block (should be REFUTING_QUOTE)",
  "- **关系**：其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）**自本节起不再成立**——错误步骤已定位（dur 字典错位），该句属被本节取代的过时表述。", "REFUTING_QUOTE"),
 ("C: refutation WITHOUT any quote pair (no 「」『』``)",
  "- 不能定位当年错误步骤 这句已过时，不再成立，已定谳，已定位。", "ANALYSIS_MENTION"),
 ("D: quoted assertion with NO negation word (should be QUOTED, not ASSERTION)",
  "- 原文：「只能判「不可复现」、不能定位当年错误步骤」", "QUOTED"),
 ("E: bare assertion + a single innocuous '复核' word (pollutes NEG_LEX)",
  "- 只能判「不可复现」、不能定位当年错误步骤；待复核。", "ANALYSIS_MENTION?"),
 ("F: bare assertion + 'grep' mentioned",
  "- 只能判「不可复现」、不能定位当年错误步骤；见 grep 结果。", "ANALYSIS_MENTION?"),
 ("G: the real LEDGER:123 line (verbatim canonical)",
  CANON, "ASSERTION"),
 ("H: the real LEDGER:215 line (§6.3, inside doc but outside block)",
  "3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。", "ASSERTION"),
 ("I: real §609:22 line (should be REFUTING_QUOTE)",
  open(r"D:/Project/ra2-campaign-forge/lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md","r",encoding="utf-8",newline="").read().splitlines()[21], "REFUTING_QUOTE"),
 ("J: real bound:270 line (should be REFUTING_QUOTE)",
  open(r"D:/Project/ra2-campaign-forge/lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md","r",encoding="utf-8",newline="").read().splitlines()[269], "REFUTING_QUOTE"),
 ("K: real bound:196 line (should be ASSERTION, in block)",
  open(r"D:/Project/ra2-campaign-forge/lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md","r",encoding="utf-8",newline="").read().splitlines()[195], "ASSERTION"),
]
print("=== R5 CLASSIFIER PROBE (direct import of author's classify_line) ===")
print("needles =", NEEDLES)
print()
for label, line, want_family in CASES:
    c = m.classify_line(line, NEEDLES, CANON)
    role = c["role"] if c else "<NO-HIT>"
    print(f"--- {label}")
    print(f"    want_family={want_family}  got_role={role}")
    print(f"    quote_delim={c['quote_delim'] if c else None} neg={c['neg'] if c else None}")
    print(f"    vline={c['verbatim_line_equal'] if c else None} vquote={c['verbatim_quote_equal'] if c else None}")
    print(f"    line[:120]={line[:120]}")
print()
print("=== OBSERVATION: does a bare assertion with one NEG_LEX word become non-ASSERTION? ===")
for extra in ["复核","grep","逐字","命中","验收","未验项","过时","改前","不再成立"]:
    line = "- 只能判「不可复现」、不能定位当年错误步骤；" + extra + "。"
    c=m.classify_line(line,NEEDLES,CANON)
    print(f"  +{extra!r:14} -> role={c['role']:<18} neg={c['neg']}")
