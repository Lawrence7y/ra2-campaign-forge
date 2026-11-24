"""_rsv_blocks2.py — tightened, evidence-anchored marker detection (independent).
Definition: a marker line must START with '#### ' or '<!-- ' or '## ↓↓↓' / '## ↑↑↑'
and contain the literal 草案正文 plus a directional token. No prose lines.
Run: python -I -X utf8 ".../_rsv_blocks2.py"
"""
import os, hashlib
ROOT = r"D:/Project/ra2-campaign-forge"
def L(rel):
    return open(os.path.join(ROOT, rel), "r", encoding="utf-8", newline="").read().split("\n")

def is_start(s):
    s = s.strip()
    if not (s.startswith("<!--") or s.startswith("####") or s.startswith("##")):
        return False
    if "草案正文" not in s:
        return False
    return ("逐字转录开始" in s) or ("↓↓↓" in s) or ("从这里开始整段复制" in s)

def is_end(s):
    s = s.strip()
    if not (s.startswith("<!--") or s.startswith("####") or s.startswith("##")):
        return False
    if "草案正文" not in s:
        return False
    return ("逐字转录结束" in s) or ("↑↑↑" in s) or ("逐字照抄结束" in s)

FILES = [
"lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
"lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
"lead/ledger_appendix_20261108/_lad_tpl.md",
"lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
"lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
"lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
"lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
"lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
]
for rel in FILES:
    lines = L(rel)
    st = [i+1 for i,x in enumerate(lines) if is_start(x)]
    en = [i+1 for i,x in enumerate(lines) if is_end(x)]
    pairs = []
    for s in st:
        nxt = [e for e in en if e > s]
        if nxt: pairs.append((s, min(nxt)))
        else: pairs.append((s, None))
    print(f"{rel}")
    print(f"  start={st}  end={en}  pairs={pairs}")
    for s,e in pairs:
        if e:
            body = lines[s:e-1]
            print(f"    block {s}-{e}: inner {s+1}..{e-1} ({len(body)} lines), body_sha_LFjoin={hashlib.sha256(chr(10).join(body).encode('utf-8')).hexdigest()[:16]}…")
    print()
