# -*- coding: utf-8 -*-
"""M71 simulate post-merge coverage in memory -> exact panel numbers + DoD flip check."""
import csv, os, sys, re, collections, math
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV   = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S22_B4", "delta.tsv")

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, l in enumerate(f):
        if i == 0: continue
        p = l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

delta = {}
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    for r in list(csv.reader(f, delimiter="\t"))[1:]:
        if len(r) >= 4: delta[ne(r[0])] = r

with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))
data = [r for r in cov[1:] if len(r) >= 8]

def compute(rows, label):
    d = collections.defaultdict(collections.Counter)
    all_proved = 0
    for r in rows:
        e = ne(r[0]); s = r[1].strip(); name = r[2].strip(); sem = r[3]; grade = r[4].strip()
        if grade == "[已证]": all_proved += 1
        if e not in atlas: continue
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name): d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem: d[s]["proved_strict_n"] += 1
    tot = collections.Counter()
    for s in d:
        for k in ("atlas_n","named_L","named_S14","named_strict","proved_n","proved_strict_n"):
            tot[k] += d[s][k]
    nom = []; st = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        c = d[s]; a = c["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if c["named_S14"] >= tn and c["proved_n"] >= tp: nom.append(s)
        if c["named_S14"] >= tn and c["proved_strict_n"] >= tp: st.append(s)
    atlas_proved = sum(d[s]["proved_n"] for s in d)
    out_proved = all_proved - atlas_proved
    print(f"\n===== {label} =====")
    print("data rows:", len(rows))
    print(f"all [已证]: {all_proved}  atlas内: {atlas_proved}  atlas外: {out_proved}")
    c = d["S22"]; a = c["atlas_n"]
    print(f"S22 atlas_n={a} proved={c['proved_n']} ({round(100.0*c['proved_n']/a,2)}%) "
          f"strict={c['proved_strict_n']} ({round(100.0*c['proved_strict_n']/a,2)}%)")
    print(f"TOTAL atlas_n={tot['atlas_n']} proved={tot['proved_n']} ({round(100.0*tot['proved_n']/tot['atlas_n'],2)}%) "
          f"strict={tot['proved_strict_n']} ({round(100.0*tot['proved_strict_n']/tot['atlas_n'],2)}%)")
    print("nominal 达标:", nom, " strict 达标:", st)
    return dict(all_proved=all_proved, atlas_proved=atlas_proved, out_proved=out_proved,
                s22_proved=c['proved_n'], s22_strict=c['proved_strict_n'],
                tot_proved=tot['proved_n'], tot_strict=tot['proved_strict_n'],
                nom=nom, st=st)

before = compute(data, "BEFORE (盘上现值)")
# simulate merge
post = []
changed = 0
for r in data:
    e = ne(r[0])
    if e in delta:
        nr = list(r)
        nr[3] = delta[e][3]                # col4 semantics
        nr[4] = "[已证]"                    # col5 grade
        nr[5] = "NAMED_PUSH_AUDIT12/VERDICT.md"  # col6 evidence
        post.append(nr); changed += 1
    else:
        post.append(r)
print("\nchanged rows:", changed)
after = compute(post, "AFTER (模拟并表)")

print("\n===== DELTAS =====")
for k in ("all_proved","atlas_proved","out_proved","s22_proved","s22_strict","tot_proved","tot_strict"):
    print(f"{k}: {before[k]} -> {after[k]} (+{after[k]-before[k]})")
print("DoD FLIP:", "NO" if (before['nom']==after['nom'] and before['st']==after['st']) else "YES")
print("EXPECTED after: all=1602 atlas=1596 out=6 s22_proved=109 s22_strict=66 tot_proved=1596 tot_strict=1279")
