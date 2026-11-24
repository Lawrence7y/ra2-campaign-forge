# -*- coding: utf-8 -*-
"""MEASURE-F3A step 2b: split the 274 rows into
  TEMPLATE  = pure "name + class-belonging" boilerplate, zero behaviour text  -> (乙) candidate
  ANCHORED  = text carries at least one byte-checkable ③b anchor             -> (甲) candidate, manual review
Prints every ANCHORED row in full so the judgement is made on real text.
"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A\work")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

def load_cov():
    out = []
    with open(COV, encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("\t")
            if i == 0:
                continue
            out.append(dict(zip(COLS, p)))
    return out

rows = [r for r in load_cov()
        if r["grade"] == "[已证]" and "[未证]" in r["one_line_semantics"]
        and r["subsystem"] != "S22"]

# ---- the boilerplate template, exactly as it appears on disk
TPL = re.compile(
    r"^(?P<body>.*?)：YRpp/kb 地址名；归属 (?P<cls>[^（(]+)"
    r"（名字已证，语义(?:一行)?据名(?:推断)?）\[未证\]$")

# anchor vocabulary = things a reader could re-check against bytes
ANCHOR_PAT = [
    (r"0x[0-9A-Fa-f]{3,}", "hexconst"),
    (r"\+0x[0-9A-Fa-f]+", "off"),
    (r"\bcall\b", "call"),
    (r"\bjmp\b|\bJMP", "jmp"),
    (r"跳表|switch|多路", "jumptable"),
    (r"循环|遍历|迭代", "loop"),
    (r"错误码|返回\s*-1|GetLastError|cmp\s|setne|setz", "errcode"),
    (r"vt\[|vtable|虚表槽|slot\d|槽位", "vt"),
    (r"内存形状|对象大小|字节单例|ctor|构造器", "memshape"),
    (r"边界检查|ja\b|jb\b|jl\b|jg\b", "bounds"),
    (r"入口相对偏移|相对偏移|锚", "anchor"),
]

def anchors(sem):
    body = TPL.match(sem).group("body") if TPL.match(sem) else sem
    # strip the name itself (up to the first ：) so a name like Foo::0x.. cannot fake an anchor
    core = body.split("：", 1)[1] if "：" in body else body
    hits = []
    for pat, tag in ANCHOR_PAT:
        if re.search(pat, core):
            hits.append(tag)
    return hits

buckets = collections.defaultdict(list)
for r in rows:
    sem = r["one_line_semantics"]
    if TPL.match(sem) and not anchors(sem):
        buckets["TEMPLATE"].append(r)
    else:
        buckets["ANCHORED"].append(r)

print("domain:", len(rows))
for k in ("TEMPLATE", "ANCHORED"):
    print("%-9s %3d" % (k, len(buckets[k])))

print("\n===== ANCHORED rows (full text) =====")
for r in sorted(buckets["ANCHORED"], key=lambda r: (r["subsystem"], r["entry"])):
    print("%s\t%s\t%s" % (r["entry"], r["subsystem"], r["name"]))
    print("    anchors=%s" % anchors(r["one_line_semantics"]))
    print("    sem=%s" % r["one_line_semantics"])
    print("    ev =%s" % r["evidence_path"])

# non-template but anchor-free (e.g. free prose) - must be reviewed too
nt = [r for r in rows if not TPL.match(r["one_line_semantics"])]
print("\nnon-template rows:", len(nt))
print("of which anchor-free:", sum(1 for r in nt if not anchors(r["one_line_semantics"])))

print("\n===== distinct TEMPLATE 'cls' values =====")
cc = collections.Counter(TPL.match(r["one_line_semantics"]).group("cls")
                         for r in buckets["TEMPLATE"])
for k, v in cc.most_common():
    print("%3d | %s" % (v, k))
