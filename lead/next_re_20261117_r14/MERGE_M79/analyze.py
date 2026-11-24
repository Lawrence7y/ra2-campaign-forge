# -*- coding: utf-8 -*-
"""M79 PRE-MERGE ANALYSIS (read-only). Recompute all baselines from disk."""
import csv, os, sys, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(ROOT, "R4_FILL_91_R3", "fill_delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# ---------- coverage ----------
raw = open(COV, "rb").read()
text = raw.decode("utf-8")
lines = text.split("\n")
trailing = lines[-1] == ""
data = lines[1:-1] if trailing else lines[1:]
rows = [ln.split("\t") for ln in data]
print("COV sha256        :", hashlib.sha256(raw).hexdigest())
print("COV BOM           :", raw.startswith(b"\xef\xbb\xbf"))
print("COV has CR        :", "\r" in text)
print("COV trailing LF   :", trailing)
print("COV header        :", repr(lines[0]))
print("COV data rows     :", len(rows))
print("COV col counts    :", dict(collections.Counter(len(r) for r in rows)))

# ---------- atlas ----------
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
print("ATLAS unique entry:", len(atlas))

# ---------- counts ----------
full = [r for r in rows if r[4].strip() == "[已证]"]
atl_in = [r for r in full if ne(r[0]) in atlas]
atl_out = [r for r in full if ne(r[0]) not in atlas]
print("[已证] full        :", len(full))
print("[已证] atlas_in    :", len(atl_in))
print("[已证] atlas_out   :", len(atl_out))

# ---------- ④ 已成文 baseline (several criteria) ----------
criteria = {
    "col4 contains ④ (any)": lambda s: "④" in s,
    "col4 contains '④ ' (④+space)": lambda s: "④ " in s,
    "col4 contains '④：'": lambda s: "④：" in s,
    "col4 contains '④ ' or '④：'": lambda s: ("④ " in s or "④：" in s),
    "col4 contains '④升级句'": lambda s: "④升级句" in s,
    "col4 contains '活表槽位见证'": lambda s: "活表槽位见证" in s,
}
for name, fn in criteria.items():
    c = sum(1 for r in full if fn(r[3]))
    print(f"BASE ④[{name:34s}] : {c}")

# ---------- delta ----------
draw = open(DELTA, "rb").read()
dtext = draw.decode("utf-8-sig")
dlines = dtext.split("\n")
dtrailing = dlines[-1] == ""
ddata = dlines[1:-1] if dtrailing else dlines[1:]
drows = [ln.split("\t") for ln in ddata]
print("")
print("DELTA sha256      :", hashlib.sha256(draw).hexdigest())
print("DELTA BOM         :", draw.startswith(b"\xef\xbb\xbf"))
print("DELTA has CR      :", "\r" in dtext)
print("DELTA trailing LF :", dtrailing)
print("DELTA header      :", repr(dlines[0]))
print("DELTA data rows   :", len(drows))
print("DELTA col counts  :", dict(collections.Counter(len(r) for r in drows)))
print("DELTA grades      :", dict(collections.Counter(r[4].strip() for r in drows)))

# ---------- map ----------
cov_by_e = {}
for i, r in enumerate(rows):
    cov_by_e.setdefault(ne(r[0]), []).append((i, r))
dmap = {}
for r in drows:
    dmap.setdefault(ne(r[0]), []).append(r)

print("")
print("DELTA unique entries:", len(dmap))
print("DELTA entries appearing >1 in delta:", [e for e,v in dmap.items() if len(v)>1])
missing = [e for e in dmap if e not in cov_by_e]
print("DELTA entries not in coverage:", missing)
dup = [e for e in dmap if e in cov_by_e and len(cov_by_e[e])>1]
print("DELTA entries duplicated in coverage:", dup)

# compare cols 1/2/3/5 (entry normalized), and see col4/col6 relation
mismatch_sub, mismatch_name, mismatch_grade = [], [], []
col4_prefix_ok = 0
col4_already_has = 0
col6_is_suffix = 0
col6_examples = []
for e, dv in dmap.items():
    d = dv[0]
    i, c = cov_by_e[e][0]
    if c[1].strip() != d[1].strip(): mismatch_sub.append((e, c[1], d[1]))
    if c[2].strip() != d[2].strip(): mismatch_name.append((e, c[2], d[2]))
    if c[4].strip() != d[4].strip(): mismatch_grade.append((e, c[4], d[4]))
    # does coverage col4 appear as prefix of delta col4?
    if d[3].startswith(c[3]): col4_prefix_ok += 1
    # does coverage col4 already contain ④?
    if "④" in c[3]: col4_already_has += 1
    # does delta col6 start with coverage col6? (append relation)
    if d[5].startswith(c[5]): col6_is_suffix += 1
    if len(col6_examples) < 5:
        col6_examples.append((e, c[5], d[5], c[3][:80], d[3][:80]))

print("")
print("mismatch subsystem :", len(mismatch_sub), mismatch_sub[:5])
print("mismatch name      :", len(mismatch_name), mismatch_name[:5])
print("mismatch grade     :", len(mismatch_grade), mismatch_grade[:5])
print("delta col4 startswith cov col4:", col4_prefix_ok, "/", len(dmap))
print("cov col4 already has ④       :", col4_already_has, "/", len(dmap))
print("delta col6 startswith cov col6:", col6_is_suffix, "/", len(dmap))
print("")
print("--- col6 examples (entry | cov6 | delta6 | cov4[:80] | delta4[:80]) ---")
for e,c6,d6,c4,dd4 in col6_examples:
    print(f"  {e}:")
    print(f"    cov6 = {c6}")
    print(f"    del6 = {d6}")
    print(f"    cov4 = {c4}")
    print(f"    del4 = {dd4}")

# one full example
e0 = sorted(dmap)[0]
d = dmap[e0][0]; i,c = cov_by_e[e0][0]
print("")
print("=== FULL EXAMPLE", e0, "===")
print("COV  col4:", repr(c[3]))
print("DEL  col4:", repr(d[3]))
print("COV  col6:", repr(c[5]))
print("DEL  col6:", repr(d[5]))
