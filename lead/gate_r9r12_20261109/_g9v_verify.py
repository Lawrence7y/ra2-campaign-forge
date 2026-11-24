# -*- coding: utf-8 -*-
# _g9v_verify.py — 复核员事实锚点综合验证（全只读）：
# A) TV3/TV7/CANDIDATE/LEDGER 新旧 problems 计数
# B) b_unclosed_trace 四真绑定行 + 引文锚实算
# C) _integ 声明锚 qc151_trip.candidate_lf.py 实算
# D) REST 3 件 R10 assertion 命中上下文
# E) 第 10 类合成探针（直调 g7.r11_scan）
# F) pycache/保护件 mtime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _g9_gate import check_deliverable, REPO_ROOT, g7  # noqa: E402

REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
TVREQ = ["APPROVE_SCOPE"]

print("== A) 新旧 problems 计数 ==")
for rel, req in [
    ("lead/gate_fp7_20261108/_g7_tv3_double_negation.md", TVREQ),
    ("lead/gate_fp7_20261108/_g7_tv7_split_token.md", TVREQ),
    ("lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md", REQ),
    ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", REQ),
]:
    r = check_deliverable(REPO_ROOT / rel, req, FORB)
    print("--", rel)
    print("   NEW:", [x["msg"][:60] for x in r["problems"]])
    print("   OLD:", [x[:60] for x in r["old_gate"]["problems"]])

print("== B) b_unclosed_trace 四真绑定行 + 引文锚 ==")
doc = REPO_ROOT / "lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md"
text = doc.read_text(encoding="utf-8")
lines = text.split("\n")
print("L60:", lines[59].strip()[:160])
for i in (4, 5, 6, 7):
    m = re.match(r"- 被核对象 SHA256 = ([0-9a-f]{64})，字节数 = ([\d,]+)（`([^`；]+)`", lines[i])
    if not m:
        print("L%d: UNPARSED" % (i + 1), lines[i][:100]); continue
    sha, nbytes, path = m.group(1), int(m.group(2).replace(",", "")), m.group(3)
    p = REPO_ROOT / path
    if p.is_file():
        b = p.read_bytes()
        ok = (hashlib.sha256(b).hexdigest() == sha and len(b) == nbytes)
        print("L%d %s -> %s (%dB) %s" % (i + 1, path, hashlib.sha256(b).hexdigest()[:12], len(b),
                                         "MATCH" if ok else "MISMATCH"))
    else:
        print("L%d %s -> NOT_ON_DISK" % (i + 1, path))
anchor = REPO_ROOT / "lead/dtrigger_round2_20261107/_dB_anchor_recompute_out.txt"
print("anchor _dB_anchor_recompute_out.txt on disk:", anchor.is_file())
cc = REPO_ROOT / "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md"
if cc.is_file():
    b = cc.read_bytes()
    print("CRITERIA_COMPARE.md:", hashlib.sha256(b).hexdigest(), len(b))

print("== C) _integ 声明锚 ==")
qc = REPO_ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
if qc.is_file():
    b = qc.read_bytes()
    print("qc151_trip.candidate_lf.py:", hashlib.sha256(b).hexdigest(), len(b))
else:
    print("NOT_ON_DISK")

print("== D) REST 3 件 R10 assertion 上下文 ==")
for rel in ["lead/goal1_harness7_20261023/HARNESS7_REPORT.md",
            "lead/goal_status_tables_20261019/STATUS_TABLES.md",
            "lead/re_line_20261105/GOAL_RE_CONTINUOUS.md"]:
    t = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
    probs, warns, hits = g7.r10_scan(t, FORB)
    print("--", rel, "assertion hits:", len(probs))
    for h, p_ in zip([h for h in hits if h["kind"] == "assertion"], probs):
        s = max(0, h["pos"] - 30)
        print("   [%s] ...%s..." % (h["token"], t[s:h["pos"] + len(h["token"]) + 30].replace("\n", " ")))

print("== E) 第 10 类合成探针（直调 g7.r11_scan） ==")
hex64 = "ab" * 32
for label, s in [
    ("被核对象**SHA256 = hex**", "被核对象**SHA256 = " + hex64 + "**"),
    ("**被核对象** SHA256 = hex", "**被核对象** SHA256 = " + hex64),
    ("SHA256 = **hex**（仅 hex 加粗）", "被核对象 SHA256 = **" + hex64 + "**"),
]:
    probs, warns, binds = g7.r11_scan(s, HERE)
    print("   %-28s matched=%s" % (label, len(binds) > 0))

print("== F) mtime 核查 ==")
import datetime
def mt(p):
    return datetime.datetime.fromtimestamp(Path(p).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
pyc = REPO_ROOT / "lead/gate_fp7_20261108/__pycache__/_g7_predicates.cpython-312.pyc"
if pyc.is_file():
    print("pycache:", pyc.name, mt(pyc))
for p in ["lead/gate_fp7_20261108/_g7_predicates.py", "lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt",
          "lead/gate_r9r12_20261109/_g9_gate.py", "lead/gate_r9r12_20261109/_g9_regression.md"]:
    print(p, mt(REPO_ROOT / p))
