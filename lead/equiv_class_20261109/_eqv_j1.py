# _eqv_j1.py — J1 反例哈希独立实算 + Q4 文档弃权复跑 + 否定句×溯源词共现面查（全部只读）。
import hashlib
import os
import re
import sys

ROOT = "D:/Project/ra2-campaign-forge"
SL_PY = ROOT + "/lead/samedoc_link_20261109/_sl_link.py"
_b = open(SL_PY, "rb").read()
assert hashlib.sha256(_b).hexdigest() == "a4ae4dc1d87d1ed052c4480883b206ef17ed3cd7a5" if False else hashlib.sha256(_b).hexdigest() == "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5"
assert len(_b) == 12475
sys.dont_write_bytecode = True
sys.path.insert(0, ROOT + "/lead/samedoc_link_20261109")
import _sl_link as SL  # noqa: E402

DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")
Q4HEX = "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251"

DUMPS = [
    "lead/qc161_u0400_trip/l1b_20261021/except_post_20261021T184518530551.txt",
    "lead/qc161_u0400_trip/l1c_20261021/except_post_20261021T190509073827.txt",
    "lead/qc161_u0400_trip/l1d_20261021/except_post_20261021T192647245700.txt",
    "lead/qc161_u0400_trip/l1e_20261021/except_post_20261021T204059731043.txt",
    "lead/qc161_u0400_trip/l3_20261021/except_post_20261021T211447471728.txt",
    "out/re_work/work_chain/CONTINUE_20261003/lead/q161/except_post_20261017T230724883941.txt",
    "lead/qc161_u0400_trip/l1_u0800_20261020/evidence_r2/except_carrier_6694b75e.txt",
]
for rel in DUMPS:
    p = ROOT + "/" + rel
    if not os.path.isfile(p):
        print("MISSING " + rel)
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    tag = "MATCH6694" if h == Q4HEX else "DIFF"
    print("dump %-96s %s %s" % (rel, h[:12], tag))

q4p = ROOT + "/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/Q4_RELATION.md"
text = open(q4p, encoding="utf-8").read()
res = SL.link(text, os.path.dirname(q4p), Q4HEX, 26405, root=ROOT)
decl_all = []
for i, ln in enumerate(text.splitlines(), 1):
    if DECL_RE.search(ln):
        decl_all.append(i)
print("Q4_RELATION raw=%s anchors=%d DECL_RE命中行=%s" % (
    res["verdict"], len(res.get("anchors", [])), decl_all or "[]"))

FIXT = [
    "lead/gate_validate_20261108/_gv_fixtures/caseB/qc151_trip.derived_same.py",
    "lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.same.py",
]
for rel in FIXT:
    p = ROOT + "/" + rel
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    tag = "CA23-CLASS" if h == "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2" else "DIFF"
    print("fixture %-96s %s %s" % (rel, h[:12], tag))

print()
print("negation x provenance co-occurrence in lead/ *.md (read-only walk):")
NEG_RE = re.compile(r"(?:不得|禁止|勿|不要).{0,40}(?:复制自|复制为)")
hits = []
for dirpath, dirnames, filenames in os.walk(ROOT + "/lead"):
    for fn in filenames:
        if fn.lower().endswith(".md"):
            fp = os.path.join(dirpath, fn)
            try:
                t = open(fp, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for i, ln in enumerate(t.splitlines(), 1):
                if NEG_RE.search(ln):
                    hits.append(fp + ":" + str(i) + " " + ln.strip()[:110])
print("hits =", len(hits))
for h in hits[:12]:
    print("  " + h)
