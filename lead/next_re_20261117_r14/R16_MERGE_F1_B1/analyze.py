# -*- coding: utf-8 -*-
"""R16-MERGE-F1 / B1 — read-only analysis of current disk state.
Computes before-state, baseline invariants, six measured numbers, strict-prefix
and column-equality checks, and §12.6/§12.4 counters. Writes analysis.json.
"""
import os, sys, json, hashlib, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_F1_B1", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
MY   = os.path.join(ROOT, "R16_MERGE_F1_B1")
os.makedirs(MY, exist_ok=True)

def fstat(path):
    b = open(path, "rb").read()
    return dict(mtime=os.path.getmtime(path), size=len(b),
                sha256=hashlib.sha256(b).hexdigest(), lines=b.count(b"\n"))

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# ---------- before state ----------
before = {"coverage.tsv": fstat(COV), "PANEL.md": fstat(PANEL)}

# ---------- load coverage as raw byte lines ----------
raw = open(COV, "rb").read()
assert raw.count(b"\r") == 0, "coverage has CR bytes"
lines = raw.split(b"\n")
# trailing newline => last element empty
trailing_nl = lines[-1] == b""
if trailing_nl:
    lines = lines[:-1]
header = lines[0]
data_lines = lines[1:]
colcount = collections.Counter()
for ln in data_lines:
    colcount[len(ln.split(b"\t"))] += 1

def parse(line):
    return line.split(b"\t")

# ---------- atlas set ----------
atlas = set()
for i, line in enumerate(open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    p = line.rstrip("\r\n").split("\t")
    if p and p[0].strip():
        atlas.add(ne(p[0]))

# ---------- baseline invariants ----------
# redo in str space for grade checks (decode fields)
proved = proved_in = proved_out = 0
for ln in data_lines:
    f = parse(ln)
    if len(f) < 8:
        continue
    grade = f[4].decode("utf-8").strip()
    if grade == "[已证]":
        proved += 1
        if ne(f[0].decode("utf-8")) in atlas:
            proved_in += 1
        else:
            proved_out += 1

baseline = dict(
    data_rows=len(data_lines),
    col_distribution={str(k): v for k, v in sorted(colcount.items())},
    proved=proved, proved_in_atlas=proved_in, proved_out_atlas=proved_out,
    trailing_newline=trailing_nl, crlf_count=raw.count(b"\r"),
)

# ---------- six measured numbers ----------
# 口径 A (MERGE_M79/verify.py:159): grade=="[已证]" and "④" in col4
# 口径 B: grade=="[已证]" and "④ 活表槽位见证" in col4
FOUR = "④"
FOUR_SOLOT = "④ 活表槽位见证"

def four_a_count(line):
    f = parse(line)
    if len(f) < 8:
        return 0
    return 1 if (f[4].decode("utf-8").strip() == "[已证]" and FOUR in f[3].decode("utf-8")) else 0

def four_b_count(line):
    f = parse(line)
    if len(f) < 8:
        return 0
    return 1 if (f[4].decode("utf-8").strip() == "[已证]" and FOUR_SOLOT in f[3].decode("utf-8")) else 0

N_A_pre = sum(four_a_count(ln) for ln in data_lines)
N_B_pre = sum(four_b_count(ln) for ln in data_lines)

# ---------- delta ----------
dlines = open(DELTA, encoding="utf-8").read().split("\n")
if dlines and dlines[-1] == "":
    dlines = dlines[:-1]
assert len(dlines) == 19, f"delta lines {len(dlines)}"
# delta header tab-separated
dhdr = dlines[0].split("\t")
assert dhdr == ["entry","subsystem","name","one_line_semantics","grade","evidence_path","n_sources","conflict"], dhdr
delta_rows = []
for ln in dlines[1:]:
    f = ln.split("\t")
    assert len(f) == 8, len(f)
    delta_rows.append(f)

# map coverage entry -> line index (byte)
cov_by_entry = {}
idx_by_entry = {}
for i, ln in enumerate(data_lines):
    e = parse(ln)[0].decode("utf-8")
    cov_by_entry.setdefault(e, []).append(i)
    idx_by_entry.setdefault(e, []).append(i)

entries = [r[0] for r in delta_rows]
assert len(set(entries)) == 18, "delta entries not unique"

# N_pre_A / N_pre_B on the 18 disk-original col4
N_pre_A = 0
N_pre_B = 0
strict_prefix = []
col_equal = []
missing = []
for r in delta_rows:
    e = r[0]
    if e not in cov_by_entry or len(cov_by_entry[e]) != 1:
        missing.append((e, len(cov_by_entry.get(e, []))))
        continue
    i = cov_by_entry[e][0]
    f = parse(data_lines[i])
    disk_col4 = f[3].decode("utf-8")
    delta_col4 = r[3]
    if FOUR in disk_col4:
        N_pre_A += 1
    if FOUR_SOLOT in disk_col4:
        N_pre_B += 1
    strict_prefix.append((e, delta_col4.startswith(disk_col4), len(disk_col4), len(delta_col4)))
    # cols 1,2,3,5,6,7,8 (0-based 0,1,2,4,5,6,7)
    eq = all(f[k].decode("utf-8") == r[k] for k in [0,1,2,4,5,6,7])
    col_equal.append((e, eq))

assert not missing, f"missing/ambiguous entries: {missing}"

# ---------- simulate merge (in memory) to get post counts ----------
post_lines = list(data_lines)
for r in delta_rows:
    e = r[0]
    i = cov_by_entry[e][0]
    f = parse(data_lines[i])
    f[3] = r[3].encode("utf-8")
    post_lines[i] = b"\t".join(f)

N_A_post = sum(four_a_count(ln) for ln in post_lines)
N_B_post = sum(four_b_count(ln) for ln in post_lines)

# ---------- §12.6 / §12.4 ----------
append_seg = []
for r in delta_rows:
    e = r[0]
    i = cov_by_entry[e][0]
    disk_col4 = parse(data_lines[i])[3].decode("utf-8")
    seg = r[3][len(disk_col4):]
    append_seg.append((e, seg))
seg_126 = sum(seg.count("§12.6") for _, seg in append_seg)
seg_124 = sum(seg.count("§12.4") for _, seg in append_seg)
full_pre_126 = raw.decode("utf-8").count("§12.6")
full_pre_124 = raw.decode("utf-8").count("§12.4")
joined_post = b"\n".join([header] + post_lines)
post_text = joined_post.decode("utf-8")
full_post_126 = post_text.count("§12.6")
full_post_124 = post_text.count("§12.4")

# ---------- fields.tsv: 个位数 entry 体内也装同一张表 (B⑦ outside-body) ----------
# Card §3.2: B1 batch count from fields.tsv self-computed.
# fields.tsv columns inspect later; here just record raw header/rows count.
fldpath = os.path.join(ROOT, "R16_F1_B1", "fields.tsv")
fldlines = open(fldpath, encoding="utf-8").read().split("\n")
if fldlines and fldlines[-1] == "":
    fldlines = fldlines[:-1]

result = dict(
    before=before,
    baseline=baseline,
    six_numbers=dict(
        N_pre_A=N_pre_A, N_pre_B=N_pre_B,
        N_A_pre=N_A_pre, N_A_post=N_A_post,
        N_B_pre=N_B_pre, N_B_post=N_B_post,
        netA=N_A_post - N_A_pre, netB=N_B_post - N_B_pre,
    ),
    strict_prefix=strict_prefix,
    col_equal=col_equal,
    append_seg_counts=dict(seg_126=seg_126, seg_124=seg_124,
                           full_pre_126=full_pre_126, full_pre_124=full_pre_124,
                           full_post_126=full_post_126, full_post_124=full_post_124),
    delta_entries=entries,
    fields_header=fldlines[0],
    fields_row_count=len(fldlines) - 1,
)

with open(os.path.join(MY, "analysis.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("=== BEFORE ===")
for k, v in before.items():
    print(f"  {k}: size={v['size']} sha={v['sha256'][:16]} lines={v['lines']} mtime={v['mtime']}")
print("=== BASELINE ===", json.dumps(baseline, ensure_ascii=False))
print("=== SIX NUMBERS ===", json.dumps(result["six_numbers"], ensure_ascii=False))
print("=== strict prefix all True? ===", all(x[1] for x in strict_prefix), "count", len(strict_prefix))
print("=== col equal all True? ===", all(x[1] for x in col_equal), "count", len(col_equal))
print("=== append seg §12.6/§12.4 ===", seg_126, seg_124, "full pre", full_pre_126, full_pre_124, "full post", full_post_126, full_post_124)
print("=== fields header ===", result["fields_header"], "rows", result["fields_row_count"])
print("WROTE", os.path.join(MY, "analysis.json"))
