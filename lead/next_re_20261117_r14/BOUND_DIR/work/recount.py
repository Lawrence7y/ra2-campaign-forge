# -*- coding: utf-8 -*-
"""BOUND-DIR 只读重算：盘上现值 + 反例行核验 + S17 标记扫描。

只读 coverage.tsv / function_atlas.tsv；写仅限 BOUND_DIR\\work\\。
口径与 RULING_R15_20261119/work/strict_panel.py 逐条一致（"[未证]" 子串过滤）。
"""
import csv, os, re, collections, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ  = r"D:\Project\ra2-campaign-forge"
ROOT  = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV   = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUTD  = os.path.join(ROOT, "BOUND_DIR", "work")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))

with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))[1:]
cov = [r for r in cov if len(r) >= 8]

d = collections.defaultdict(collections.Counter)
s17_strict_rows, s22_w_rows, nonS22_w_nontpl, empty_sem, w_rows_all = [], [], [], [], []
for r in cov:
    e, sub, name, sem, grade = ne(r[0]), r[1].strip(), r[2].strip(), r[3], r[4].strip()
    if e not in atlas:
        continue
    d[sub]["atlas_n"] += 1
    if grade == "[已证]":
        d[sub]["proved_n"] += 1
        if "[未证]" in sem:
            d[sub]["w_sub"] += 1
            w_rows_all.append(r)
            if sub == "S22":
                s22_w_rows.append(r)
            elif "据名" not in sem:
                nonS22_w_nontpl.append(r)
        else:
            d[sub]["strict_sub"] += 1
            if not sem.strip():
                empty_sem.append(r)
            if sub == "S17":
                s17_strict_rows.append(r)

print("== 盘上现值（strict_panel.py 同口径）==")
tot = collections.Counter()
for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
    c = d[s]
    for k in c:
        tot[k] += c[k]
    print("%-4s atlas_n=%5d proved=%4d strict_sub=%4d w_sub=%3d thr=%d %s" % (
        s, c["atlas_n"], c["proved_n"], c["strict_sub"], c["w_sub"],
        -(-c["atlas_n"] // 2), "STRICT-OK" if c["strict_sub"] >= -(-c["atlas_n"] // 2) else ""))
print("TOTAL atlas_n=%d proved=%d strict_sub=%d w_sub=%d" % (
    tot["atlas_n"], tot["proved_n"], tot["strict_sub"], tot["w_sub"]))

print("\n== 反例行核验 ==")
for tgt in ("004AB9B0", "00522340"):
    hit = [r for r in cov if ne(r[0]) == tgt]
    if hit:
        r = hit[0]
        print("%s sub=%s grade=%s atlas=%s w_sub=%s sem[:110]=%s" % (
            tgt, r[1].strip(), r[4].strip(), ne(r[0]) in atlas, "[未证]" in r[3], r[3][:110]))

print("\n== 非 S22 且语义含[未证]的非模板行（应为 2 行：00522340 甲 / 004C93D0 乙）==")
for r in nonS22_w_nontpl:
    print("%s %s %s sem[:150]=%s" % (ne(r[0]), r[1].strip(), r[4].strip(), r[3][:150]))

print("\n== S22 语义含[未证] %d 行（前 90 字符抽查措辞）==" % len(s22_w_rows))
for r in s22_w_rows:
    print("%s %s %s" % (ne(r[0]), r[4].strip(), r[3][:90]))

print("\n== [已证]∧atlas∧无[未证]∧语义串为空 行数 = %d ==" % len(empty_sem))
for r in empty_sem[:10]:
    print("%s %s" % (ne(r[0]), r[1].strip()))

print("\n== S17 严格计入 %d 行 · 机械标记扫描（非审计，仅定位第二类候选）==" % len(s17_strict_rows))
DOC = re.compile(r"from\s+R\d|\.md\b|kb\b|docs[/\\]re|ledger|R8_ui|R\d_\w+\.md", re.I)
THR = -(-d["S17"]["atlas_n"] // 2)
doc_rows = []
for r in s17_strict_rows:
    sem = r[3]
    is_doc = bool(DOC.search(sem))
    has_off = bool(re.search(r"\+0x[0-9A-Fa-f]{1,6}|0x[0-9A-Fa-f]{6,}", sem))
    if is_doc:
        doc_rows.append((r, has_off))
print("门槛(50%%)=%d；计入=%d；余量=%d" % (THR, len(s17_strict_rows), len(s17_strict_rows) - THR))
print("语义含文档/台账引注标记（from R*/ .md / kb / docs\\re / ledger / R*_*.md）的行数 = %d；其中同时含 +0x/地址锚 = %d" % (
    len(doc_rows), sum(1 for _, h in doc_rows if h)))
with open(os.path.join(OUTD, "s17_doc_marker.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\thas_offset_anchor\tsem\n")
    for r, h in doc_rows:
        f.write("%s\t%s\t%s\t%s\t%s\n" % (ne(r[0]), r[1].strip(), r[2].strip(), h, r[3]))
print("明细已写 BOUND_DIR\\work\\s17_doc_marker.tsv")
for r, h in doc_rows:
    print("%s off_anchor=%s sem[:130]=%s" % (ne(r[0]), h, r[3][:130]))
