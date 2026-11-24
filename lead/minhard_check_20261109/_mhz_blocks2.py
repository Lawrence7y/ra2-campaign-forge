# _mhz_blocks2.py — precise block pairing / identity / stale-fingerprint / §609 checks (this session)
import hashlib
import os
import re
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
def rp(rel): return os.path.join(ROOT, rel.replace("/", os.sep))
def rb(rel):
    with open(rp(rel), "rb") as f: return f.read()
def ls(rel): return rb(rel).decode("utf-8").splitlines()

O = []
def p(s=""): O.append(str(s))

# anchored marker patterns only (not prose)
START_PATTERNS = [
    re.compile(r"^<!--\s*=+\s*草案正文 \d+ 逐字转录开始.*-->$"),
    re.compile(r"^## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓$"),
    re.compile(r"^#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓$"),
]
END_PATTERNS = [
    re.compile(r"^<!--\s*=+\s*草案正文 \d+ 逐字转录结束.*-->$"),
    re.compile(r"^## ↑↑↑ 草案正文结束 ↑↑↑$"),
    re.compile(r"^#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑$"),
]
def blocks(rel):
    L = ls(rel)
    starts = [i+1 for i,x in enumerate(L) if any(q.match(x) for q in START_PATTERNS)]
    ends   = [i+1 for i,x in enumerate(L) if any(q.match(x) for q in END_PATTERNS)]
    assert len(starts) == len(ends), (rel, starts, ends)
    return list(zip(starts, ends)), L

G1 = "- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。"
G2 = "3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。"

p("== A. precise block pairs + IN_BLOCK for the three groups & extra carriers ==")
CASES = [
 ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", [("处8", 123, G1), ("#C1", 215, G2)]),
 ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", [("处9", 25, G1)]),
 ("lead/ledger_appendix_20261108/_lad_tpl.md", [("#C2", 151, G2)]),
 ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md", [("#A3", 171, None)]),
 ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", [("合订本1", 196, G1)]),
 ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", [("合订本2", 129, G1)]),
 ("lead/ledger_bound_20261109/_lb2_TEMPLATE.md", []),
 ("lead/gate_doc_name_fix_20261109/_dnv_sandbox36/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", [("sandbox36", 123, G1)]),
 ("lead/gate_doc_name_fix_20261109/_dnw_sandbox/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", [("dnw", 123, G1)]),
 ("lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md", [("refsync", 102, G1)]),
 ("lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md", [("rs1", 131, G1), ("rs2", 144, G1)]),
]
for rel, probes in CASES:
    bs, L = blocks(rel)
    p(f"  {rel}  blocks={bs}")
    for tag, n, expect in probes:
        inside = any(s < n < e for s,e in bs)
        verbatim = (L[n-1] == expect) if expect else None
        p(f"    {tag} :{n} IN_BLOCK={inside} VERBATIM_G1G2={verbatim}")

# ============ B. G1 repo-wide exact-line hits (this session, all of ROOT) ============
p("")
p("== B. repo-wide exact-line G1 scan (whole repo, this session) ==")
hits=[]; scanned=0
# -- scope: lead/ tree only (whole-repo walk over untracked GLM/Qwen/.tmp trees timed out; see §6 未验)
for base, dirs, files in os.walk(os.path.join(ROOT, "lead")):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
    for fn in files:
        if not fn.lower().endswith((".md",".py",".txt",".json")): continue
        fp = os.path.join(base, fn)
        try: txt = open(fp,"rb").read().decode("utf-8")
        except Exception: continue
        scanned += 1
        for i,ln in enumerate(txt.splitlines(),1):
            if ln == G1: hits.append((os.path.relpath(fp,ROOT).replace(os.sep,"/"), i))
p(f"  scope = {os.path.join(ROOT, 'lead')}  files_scanned={scanned} TOTAL_HITS={len(hits)}")
for rel,i in sorted(hits): p(f"    {rel}:{i}")

# ============ C. §607 body identity (4 copies) ============
p("")
p("== C. §607 正文段 SHA256 identity (:13-26 / :111-124 / :184-197 / :117-130) ==")
def slice_sha(rel, a, b):
    raw = ("\n".join(ls(rel)[a-1:b]) + "\n").encode("utf-8")
    return len(raw), hashlib.sha256(raw).hexdigest()
SEGS = [
 ("_la_draft3 :13-26", "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 13, 26),
 ("LEDGER :111-124", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 111, 124),
 ("BOUND_VOL :184-197", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 184, 197),
 ("_lb :117-130", "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 117, 130),
]
ref=None
for tag, rel, a, b in SEGS:
    n,h = slice_sha(rel,a,b)
    if ref is None: ref=h
    p(f"  {tag} bytes={n} sha256={h} ==_la_draft3? {h==ref}")

# ============ D. stale fingerprint registration surface ============
p("")
p("== D. stale-fingerprint registrations that break if :25 changes (grep d5dc8f97 / e9842d41 / 7703 / 4894) ==")
NEEDLES = ["d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6",
           "e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698"]
for base, dirs, files in os.walk(os.path.join(ROOT,"lead")):
    dirs[:] = [d for d in dirs if d not in (".git","__pycache__")]
    for fn in files:
        if not fn.lower().endswith((".md",".py",".txt",".json")): continue
        fp=os.path.join(base,fn)
        try: L=open(fp,"rb").read().decode("utf-8").splitlines()
        except Exception: continue
        ms=[(i,l) for i,l in enumerate(L,1) if any(n in l for n in NEEDLES)]
        if ms:
            rel=os.path.relpath(fp,ROOT).replace(os.sep,"/")
            p(f"  -- {rel} ({len(ms)} lines) --")
            for i,l in ms: p(f"     :{i}: {l[:160]}")

# ============ E. §609 relation sentence copies ============
p("")
p("== E. §609 正文含『自本节起不再成立』的副本 ==")
KEY="自本节起不再成立"
for rel in ["lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
            "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
            "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
            "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
            "lead/ledger_bound_20261109/_lb2_TEMPLATE.md"]:
    ms=[(i,l) for i,l in enumerate(ls(rel),1) if KEY in l]
    p(f"  {rel} hits={len(ms)}")
    for i,l in ms: p(f"     :{i}: {l[:180]}")

# ============ F. SLOW_WINDOW:127 / _sa:90 / ATTR:136 ============
p("")
p("== F. 13 件内未登记的同类过时句 & 连带项 ==")
for rel,ns in [("lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",[127]),
               ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md",[136]),
               ("lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",[90]),
               ("lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md",[95])]:
    L=ls(rel)
    p(f"  -- {rel} --")
    for n in ns: p(f"     :{n}: {L[n-1] if n<=len(L) else '<OOR>'}")
A=ls("lead/s604_attribution_20261108/S604_ATTRIBUTION.md")[135]
B=ls("lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md")[89]
p(f"  ATTRIBUTION:136 == _sa:90 ? {A==B}")

# ============ G. build script presence ============
p("")
p("== G. _lad_build.py / _lb_build.py presence ==")
for rel in ["lead/ledger_appendix_20261108/_lad_build.py",
            "lead/ledger_bound_20261109/_lb_build.py"]:
    p(f"  {rel} exists={os.path.isfile(rp(rel))}")

# ============ H. file counts in write domain ============
p("")
p("== H. write domain counts ==")
WD=rp("lead/minhard_check_20261109")
for pref in ["_mh_","_mhv_","_mhz_","MINHARD_SET_CHECK.md"]:
    fs=[f for f in os.listdir(WD) if f.startswith(pref)]
    p(f"  prefix {pref!r} count={len(fs)}")

sys.stdout.write("\n".join(O)+"\n")
