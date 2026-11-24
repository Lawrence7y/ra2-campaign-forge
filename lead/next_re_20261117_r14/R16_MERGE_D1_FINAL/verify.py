# -*- coding: utf-8 -*-
"""R16-MERGE-D1-FINAL · 逐项验证 ①–⑧（PASS/FAIL），输出 VERIFY_RESULT.json。
所有数字实测，不引用预测；还原性用 pin + before_col4 自证。
"""
import os, sys, json, hashlib, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_FINAL")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_FINAL", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

pin_cov   = open(os.path.join(OUT, "_pin_coverage.tsv"), "rb").read()
pin_panel = open(os.path.join(OUT, "_pin_PANEL.md"), "rb").read()
after_cov = open(COV, "rb").read()
after_panel = open(PANEL, "rb").read()
delta_b = open(DELTA, "rb").read()
baseline = json.load(open(os.path.join(OUT, "baseline.json"), encoding="utf-8"))
before_col4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
merge_log = json.load(open(os.path.join(OUT, "MERGE_LOG.json"), encoding="utf-8"))
sp_before = json.load(open(os.path.join(OUT, "before_strict_panel.json"), encoding="utf-8"))
sp_after  = json.load(open(os.path.join(OUT, "after_strict_panel.json"), encoding="utf-8"))

results = {}
def rec(k, ok, detail): results[k] = dict(status="PASS" if ok else "FAIL", detail=detail)

# ---- parse helpers ----
def parse_cov_bytes(b):
    lines = b.split(b"\n")
    trailing = b.endswith(b"\n")
    if trailing: lines = lines[:-1]      # drop trailing empty segment
    txt = b.decode("utf-8")
    all_lines = txt.split("\n")
    if trailing: all_lines = all_lines[:-1]
    data = [ln.split("\t") for ln in all_lines[1:]]
    return lines, all_lines, data, trailing

p_lines, p_all, p_rows, p_trail = parse_cov_bytes(pin_cov)
a_lines, a_all, a_rows, a_trail = parse_cov_bytes(after_cov)
dlines = delta_b.decode("utf-8-sig").split("\n")
if dlines and dlines[-1]=="": dlines=dlines[:-1]
drows = [ln.split("\t") for ln in dlines[1:]]

targets = ["0051B1F0","0051DAF0","00522340","0070B570","00748190"]

# ---- ① strict prefix 5/5 ----
pref_ok = 0
pref_detail = []
for d in drows:
    e = d[0].strip().upper()
    info = before_col4[e]
    idx = info["row_index_0based"]       # 0-based data-row index (header excluded)
    old4 = info["value"]
    new4 = a_rows[idx][3]
    ok = (new4 == d[3]) and new4.startswith(old4) and len(new4) > len(old4)
    pref_ok += int(ok)
    pref_detail.append(dict(entry=e, strict_prefix=ok, new_eq_delta=new4==d[3],
                            old_len=len(old4), new_len=len(new4)))
rec("①", pref_ok==5 and len(drows)==5, dict(n=pref_ok, total=5, rows=pref_detail))

# ---- ② byte reversibility (pin + before_col4) ----
rev_lines = list(a_lines)
rev_rows = [r[:] for r in a_rows]
for e, info in before_col4.items():
    idx = info["line_number"]-1
    cols = rev_lines[idx].split(b"\t")
    cols[3] = info["value"].encode("utf-8")
    rev_lines[idx] = b"\t".join(cols)
rev_cov = b"\n".join(rev_lines) + (b"\n" if a_trail else b"")
rev_ok = (sha(rev_cov) == sha(pin_cov))
rec("②", rev_ok, dict(rev_sha=sha(rev_cov), pin_sha=sha(pin_cov),
                      pin_bytes=len(pin_cov), rev_bytes=len(rev_cov)))

# ---- ③ invariants ----
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i==0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))
coldist = collections.Counter(len(r) for r in a_rows)
n_yz = yz_in = yz_out = 0
for r in a_rows:
    if len(r)>=8 and r[4].strip()=="[已证]":
        n_yz += 1
        if ne(r[0]) in atlas: yz_in += 1
        else: yz_out += 1
inv = dict(data_rows=len(a_rows), col_dist=dict(coldist), grade_yizheng=n_yz,
           yizheng_atlas_in=yz_in, yizheng_atlas_out=yz_out)
inv_ok = (len(a_rows)==18498 and dict(coldist)=={8:18498} and n_yz==1654 and yz_in==1648 and yz_out==6)
rec("③", inv_ok, inv)

# ---- ④ only 5 col4 changed, others byte-identical, grade unchanged ----
idx_set = {info["line_number"]-1 for info in before_col4.values()}
line_count_same = len(p_lines)==len(a_lines)
non_target_identical = all(p_lines[i]==a_lines[i] for i in range(len(p_lines)) if i not in idx_set)
target_detail = []
target_ok = True
for e, info in before_col4.items():
    idx = info["line_number"]-1
    pc = p_lines[idx].split(b"\t"); ac = a_lines[idx].split(b"\t")
    other_same = all(pc[j]==ac[j] for j in [0,1,2,4,5,6,7])
    grade_same = pc[4]==ac[4]
    col4_changed = pc[3]!=ac[3]
    target_detail.append(dict(entry=e, other7_byte_equal=other_same, grade_unchanged=grade_same,
                              col4_changed=col4_changed))
    target_ok &= other_same and grade_same and col4_changed
four_ok = line_count_same and non_target_identical and target_ok and len(idx_set)==5
rec("④", four_ok, dict(line_count_same=line_count_same, p_lines=len(p_lines), a_lines=len(a_lines),
    non_target_lines_byte_identical=non_target_identical, target_rows=target_detail))

# ---- ⑤ 口径 A/B measured before/after ----
def cal_a_b(rows):
    A=B=0
    for r in rows:
        if len(r)>=8 and r[4].strip()=="[已证]":
            if "④" in r[3]: A+=1
            if "④ 活表槽位见证" in r[3]: B+=1
    return A,B
pA,pB = cal_a_b(p_rows); aA,aB = cal_a_b(a_rows)
five_ok = (aA-pA==5 and aB-pB==5)
rec("⑤", five_ok, dict(A_before=pA, A_after=aA, net_A=aA-pA, B_before=pB, B_after=aB, net_B=aB-pB,
    expected="A +5; B +5 (5 rows all write '④ 活表槽位见证' substring)",
    note="measured from disk before/after, not extrapolated (R16-5 lesson)"))

# ---- ⑥ PANEL reversibility + insertion correctness ----
inserted = merge_log["panel"]["inserted_lines"]  # 7
ins_line = merge_log["panel"]["inserted_after_line"]  # 289
p_plines = pin_panel.split(b"\n")
a_plines = after_panel.split(b"\n")
# remove inserted lines: segments indices 289..289+inserted-1
rev_plines = a_plines[:289] + a_plines[289+inserted:]
rev_panel = b"\n".join(rev_plines)
panel_rev_ok = (sha(rev_panel)==sha(pin_panel))
# compare pin lines against the *reversed* after-lines (index-aligned)
orig_identical = all(p_plines[i]==rev_plines[i] for i in range(len(p_plines)))
m98_present = all(ln.encode("utf-8") in a_plines for ln in merge_log["panel"]["m98_text"])
anchor_ok = (b"M97 " in a_plines[283] and b"M98 " in a_plines[289] and b"M77 " in a_plines[289+inserted])
six_ok = panel_rev_ok and orig_identical and m98_present and anchor_ok and len(a_plines)==len(p_plines)+inserted
rec("⑥", six_ok, dict(panel_rev_sha=sha(rev_panel), panel_pin_sha=sha(pin_panel),
    panel_rev_ok=panel_rev_ok, original_lines_byte_identical=orig_identical,
    m98_all_lines_present=m98_present, anchor_ok=anchor_ok,
    before_lines=len(p_plines), after_lines=len(a_plines), inserted=inserted,
    inserted_after_line=ins_line))

# ---- ⑦ 达标 not flipped ----
b_rows = sp_before["rows"]; af_rows = sp_after["rows"]
b_nom = [r["S"] for r in b_rows if r["dod_nominal"]]
af_nom = [r["S"] for r in af_rows if r["dod_nominal"]]
b_str = [r["S"] for r in b_rows if r["dod_strict"]]
af_str = [r["S"] for r in af_rows if r["dod_strict"]]
b_pv = sp_before["total"]["proved_n"]; af_pv = sp_after["total"]["proved_n"]
b_pvs = sp_before["total"]["proved_strict_n"]; af_pvs = sp_after["total"]["proved_strict_n"]
seven_ok = (b_nom==af_nom and b_str==af_str and b_pv==af_pv and b_pvs==af_pvs)
per_sub = []
for br, ar in zip(b_rows, af_rows):
    per_sub.append(dict(S=br["S"], proved_before=br["proved_n"], proved_after=ar["proved_n"],
        strict_before=br["proved_strict_n"], strict_after=ar["proved_strict_n"],
        nominal_before=br["dod_nominal"], nominal_after=ar["dod_nominal"],
        strict_dod_before=br["dod_strict"], strict_dod_after=ar["dod_strict"]))
rec("⑦", seven_ok, dict(nominal_before=b_nom, nominal_after=af_nom, strict_before=b_str, strict_after=af_str,
    total_proved_before=b_pv, total_proved_after=af_pv,
    total_proved_strict_before=b_pvs, total_proved_strict_after=af_pvs,
    per_subsystem=per_sub, note="strict_panel_local.py (authoritative caliber, output to own dir)"))

# ---- ⑧ line endings not mixed ----
def le(b): return dict(crlf=b.count(b"\r\n"), lf_only=b.count(b"\n")-b.count(b"\r\n"),
                       lone_cr=b.count(b"\r")-b.count(b"\r\n"), bom=b[:3]==b"\xef\xbb\xbf")
cov_le = le(after_cov); pan_le = le(after_panel)
eight_ok = (cov_le["crlf"]==0 and cov_le["lone_cr"]==0 and cov_le["lf_only"]==18498 and
            pan_le["crlf"]==0 and pan_le["lone_cr"]==0 and pan_le["lf_only"]==682 and
            not cov_le["bom"] and not pan_le["bom"])
rec("⑧", eight_ok, dict(coverage=cov_le, panel=pan_le,
    note="coverage LF=18498 (no trailing LF); PANEL LF=682 = 675+7 inserted lines"))

# ---- write result ----
all_pass = all(v["status"]=="PASS" for v in results.values())
out = dict(all_pass=all_pass, checks=results,
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(after_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(after_panel)))
with open(os.path.join(OUT, "VERIFY_RESULT.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for k in ["①","②","③","④","⑤","⑥","⑦","⑧"]:
    print(k, results[k]["status"])
print("ALL_PASS", all_pass)
print("COV sha", sha(pin_cov), "->", sha(after_cov))
print("PANEL sha", sha(pin_panel), "->", sha(after_panel))
