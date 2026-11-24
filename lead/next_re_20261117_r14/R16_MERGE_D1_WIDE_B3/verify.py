# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B3 · 逐项验证 ①–⑩（PASS/FAIL），输出 VERIFY_RESULT.json。
所有数字实测，不引用预测；还原性用 pin + before_col4 自证。
只读 coverage.tsv / PANEL.md / delta / atlas；只写本目录 VERIFY_RESULT.json。
"""
import os, sys, json, hashlib, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B3")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_WIDE_B3", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
EXCLUDE = {"005F4B10"}

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
    if trailing: lines = lines[:-1]
    txt = b.decode("utf-8")
    all_lines = txt.split("\n")
    if trailing: all_lines = all_lines[:-1]
    data = [ln.split("\t") for ln in all_lines[1:]]
    return lines, all_lines, data, trailing

def parse_delta(b):
    dl = b.decode("utf-8-sig").split("\n")
    if dl and dl[-1] == "": dl = dl[:-1]
    return [ln.split("\t") for ln in dl[1:]]

p_lines, p_all, p_rows, p_trail = parse_cov_bytes(pin_cov)
a_lines, a_all, a_rows, a_trail = parse_cov_bytes(after_cov)
drows = parse_delta(delta_b)
merged4 = {ne(d[0]): d[3] for d in drows if ne(d[0]) not in EXCLUDE}
assert len(before_col4)==17 and len(merged4)==17
assert set(before_col4)==set(merged4)

# ---- ① 17 行第 4 列严格前缀（盘上原值为严格前缀） ----
pref_detail = []; pref_ok = 0
for e, info in before_col4.items():
    idx = info["line_number"] - 1
    old4 = info["value"]                 # 盘上原第 4 列（pin）
    new4 = a_lines[idx].split(b"\t")[3].decode("utf-8")
    ok = (new4 == merged4[e]) and new4.startswith(old4) and len(new4) > len(old4)
    pref_ok += int(ok)
    pref_detail.append(dict(entry=e, strict_prefix=ok,
                            new_eq_delta_col4=(new4==merged4[e]),
                            old_len=len(old4), new_len=len(new4)))
one_ok = (pref_ok == 17)
rec("①", one_ok, dict(n=pref_ok, total=17, rows=pref_detail,
    note="17 行取 R16_D1_WIDE_B3/delta.tsv 第4列；005F4B10 已排除"))

# ---- ② 明确核 005F4B10 未被改动（整行 + 第4列逐字节） ----
ex = baseline["excluded"]
ex_idx = ex["line_number"] - 1
ex_p_line = p_lines[ex_idx]
ex_a_line = a_lines[ex_idx]
ex_p_col4 = ex_p_line.split(b"\t")[3]
ex_a_col4 = ex_a_line.split(b"\t")[3]
ex_expected = ex["col4"].encode("utf-8")
ex_unchanged = (
    ex_p_line == ex_a_line and
    ex_a_col4 == ex_expected and
    ex_a_col4 == baseline["excluded"]["col4"].encode("utf-8") and
    ex["entry"] not in {e for e in before_col4} and
    ex["entry"] not in [r["entry"] for r in pref_detail]
)
rec("②", ex_unchanged, dict(entry=ex["entry"], line_number=ex["line_number"],
    pin_col4=ex_p_col4.decode("utf-8"), after_col4=ex_a_col4.decode("utf-8"),
    pin_line_sha=sha(ex_p_line), after_line_sha=sha(ex_a_line),
    full_line_byte_identical=(ex_p_line==ex_a_line),
    col4_byte_identical=(ex_a_col4==ex_expected),
    grade=ex["grade"], note="005F4B10 整行与第4列逐字节未动；未并入 delta 任何变更"))

# ---- ③ 逐字节还原性（pin + before_col4：17 行第4列换回原值后 sha == 改前） ----
rev_lines = list(a_lines)
for e, info in before_col4.items():
    idx = info["line_number"] - 1
    cols = rev_lines[idx].split(b"\t")
    assert cols[3].decode("utf-8") == merged4[e], (e, "after col4 not merged delta")
    cols[3] = info["value"].encode("utf-8")
    rev_lines[idx] = b"\t".join(cols)
rev_cov = b"\n".join(rev_lines) + (b"\n" if a_trail else b"")
rev_ok = (rev_cov == pin_cov) and (sha(rev_cov) == sha(pin_cov))
rec("③", rev_ok, dict(rev_sha=sha(rev_cov), pin_sha=sha(pin_cov),
                      pin_bytes=len(pin_cov), rev_bytes=len(rev_cov),
                      byte_equal=(rev_cov==pin_cov),
                      note="pin + before_col4 自证：17 行第4列换回改前原值后逐字节等于改前"))

# ---- ④ 不变量 18,498 / {8:18498} / [已证] 1,654 / atlas 内 1,648 / 外 6 ----
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
four_ok = (len(a_rows)==18498 and dict(coldist)=={8:18498} and n_yz==1654 and yz_in==1648 and yz_out==6)
rec("④", four_ok, inv)

# ---- ⑤ 只有 17 行第4列变、其余列逐字节同、grade 未变 ----
idx_set = {info["line_number"]-1 for info in before_col4.values()}
line_count_same = len(p_lines)==len(a_lines)
non_target_identical = all(p_lines[i]==a_lines[i] for i in range(len(p_lines)) if i not in idx_set)
target_detail = []; target_ok = True
for e, info in before_col4.items():
    idx = info["line_number"]-1
    pc = p_lines[idx].split(b"\t"); ac = a_lines[idx].split(b"\t")
    other_same = all(pc[j]==ac[j] for j in [0,1,2,4,5,6,7])
    grade_same = pc[4]==ac[4]
    col4_changed = pc[3]!=ac[3]
    target_detail.append(dict(entry=e, other7_byte_equal=other_same,
                              grade_unchanged=grade_same, col4_changed=col4_changed,
                              grade=ac[4].decode("utf-8")))
    target_ok &= other_same and grade_same and col4_changed
five_ok = line_count_same and non_target_identical and target_ok and len(idx_set)==17
rec("⑤", five_ok, dict(line_count_same=line_count_same, p_lines=len(p_lines), a_lines=len(a_lines),
    non_target_lines_byte_identical=non_target_identical,
    excluded_line_unchanged=(p_lines[ex_idx]==a_lines[ex_idx]),
    target_rows=target_detail))

# ---- ⑥ 口径 A/B 实测改前改后（不许推算） ----
def cal_a_b(rows):
    A=B=0
    for r in rows:
        if len(r)>=8 and r[4].strip()=="[已证]":
            if "④" in r[3]: A+=1
            if "④ 活表槽位见证" in r[3]: B+=1
    return A,B
pA,pB = cal_a_b(p_rows); aA,aB = cal_a_b(a_rows)
pre_has4 = sum(1 for info in before_col4.values() if "④" in info["value"])
pre_hasphrase = sum(1 for info in before_col4.values() if "④ 活表槽位见证" in info["value"])
six_ok = (pA==430 and pB==263 and aA-pA==17 and aB-pB==17 and pre_has4==0 and pre_hasphrase==0)
rec("⑥", six_ok, dict(A_before=pA, A_after=aA, net_A=aA-pA,
    B_before=pB, B_after=aB, net_B=aB-pB,
    pre_has4_of_17=pre_has4, pre_hasphrase_of_17=pre_hasphrase,
    pct_A_before="%.2f"%(100.0*pA/1654), pct_A_after="%.2f"%(100.0*aA/1654),
    pct_B_before="%.2f"%(100.0*pB/1654), pct_B_after="%.2f"%(100.0*aB/1654),
    note="全部从 pin/after 盘上字节实测，非推算；改前 A=430/B=263 为实测值"))

# ---- ⑦ §12.6 命中数变化（实测） ----
def sec126(rows):
    lines=occ=0
    for r in rows:
        if len(r)>=8 and "§12.6" in r[3]:
            lines+=1; occ+=r[3].count("§12.6")
    return lines,occ
p126l,p126o = sec126(p_rows); a126l,a126o = sec126(a_rows)
seven_ok = (a126l-p126l==17 and a126o-p126o==17)
rec("⑦", seven_ok, dict(lines_before=p126l, lines_after=a126l, lines_net=a126l-p126l,
    occ_before=p126o, occ_after=a126o, occ_net=a126o-p126o,
    note="17 行各追加 1 处 D-47 披露指向 §12.6；005F4B10 未并不计（实测）"))

# ---- ⑧ PANEL 还原性（插入 1 条 M101，既有内容零删除零改字） ----
ins_at = merge_log["panel"]["inserted_after_line"]   # 313
ins_n  = merge_log["panel"]["inserted_lines"]        # 9
p_plines = pin_panel.split(b"\n")
a_plines = after_panel.split(b"\n")
rev_plines = a_plines[:ins_at] + a_plines[ins_at+ins_n:]
rev_panel = b"\n".join(rev_plines)
panel_rev_ok = (rev_panel == pin_panel) and (sha(rev_panel)==sha(pin_panel))
orig_identical = len(rev_plines)==len(p_plines) and all(p_plines[i]==rev_plines[i] for i in range(len(p_plines)))
m101 = merge_log["panel"]["m101_text"]
m101_present = all(ln.encode("utf-8") in a_plines for ln in m101)
m100_block = p_plines[304:313]  # 1-based L305-L313
m100_intact = all(ln in a_plines for ln in m100_block)
anchors_ok = (b"M100 " in a_plines[304] and
              "M101 ".encode("utf-8") in a_plines[313] and
              b"M77 " in a_plines[313+ins_n])
eight_ok = (panel_rev_ok and orig_identical and m101_present and m100_intact and anchors_ok and
            len(a_plines)==len(p_plines)+ins_n)
rec("⑧", eight_ok, dict(panel_rev_sha=sha(rev_panel), panel_pin_sha=sha(pin_panel),
    panel_rev_ok=panel_rev_ok, original_lines_byte_identical=orig_identical,
    m101_all_lines_present=m101_present, m100_block_intact=m100_intact, anchors_ok=anchors_ok,
    before_lines=len(p_plines), after_lines=len(a_plines), inserted=ins_n,
    inserted_after_line=ins_at))

# ---- ⑨ 达标未翻转（名义 S15,S16,S17 / 严格 S17） ----
b_nom = [r["S"] for r in sp_before["rows"] if r["dod_nominal"]]
af_nom = [r["S"] for r in sp_after["rows"] if r["dod_nominal"]]
b_str = [r["S"] for r in sp_before["rows"] if r["dod_strict"]]
af_str = [r["S"] for r in sp_after["rows"] if r["dod_strict"]]
b_pv = sp_before["total"]["proved_n"]; af_pv = sp_after["total"]["proved_n"]
b_pvs = sp_before["total"]["proved_strict_n"]; af_pvs = sp_after["total"]["proved_strict_n"]
nine_ok = (b_nom==af_nom==["S15","S16","S17"] and b_str==af_str==["S17"] and b_pv==af_pv and b_pvs==af_pvs)
per_sub = []
for br, ar in zip(sp_before["rows"], sp_after["rows"]):
    per_sub.append(dict(S=br["S"], proved_before=br["proved_n"], proved_after=ar["proved_n"],
        strict_before=br["proved_strict_n"], strict_after=ar["proved_strict_n"],
        nominal_before=br["dod_nominal"], nominal_after=ar["dod_nominal"],
        strict_dod_before=br["dod_strict"], strict_dod_after=ar["dod_strict"]))
rec("⑨", nine_ok, dict(nominal_before=b_nom, nominal_after=af_nom,
    strict_before=b_str, strict_after=af_str,
    total_proved_before=b_pv, total_proved_after=af_pv,
    total_proved_strict_before=b_pvs, total_proved_strict_after=af_pvs,
    per_subsystem=per_sub,
    note="strict_panel_local.py 权威口径（输出本目录），[未证] 带方括号字面过滤"))

# ---- ⑩ 行尾不混用 ----
def le(b): return dict(crlf=b.count(b"\r\n"), lf_only=b.count(b"\n")-b.count(b"\r\n"),
                       lone_cr=b.count(b"\r")-b.count(b"\r\n"), bom=b[:3]==b"\xef\xbb\xbf")
cov_le = le(after_cov); pan_le = le(after_panel)
ten_ok = (cov_le["crlf"]==0 and cov_le["lone_cr"]==0 and cov_le["lf_only"]==18498 and
          pan_le["crlf"]==0 and pan_le["lone_cr"]==0 and pan_le["lf_only"]==708 and
          not cov_le["bom"] and not pan_le["bom"])
rec("⑩", ten_ok, dict(coverage=cov_le, panel=pan_le,
    note="coverage LF=18498（无末尾 LF）；PANEL LF=708 = 699+9 插入行"))

# ---- write result ----
all_pass = all(v["status"]=="PASS" for v in results.values())
out = dict(all_pass=all_pass, checks=results,
    coverage=dict(before_sha=sha(pin_cov), after_sha=sha(after_cov)),
    panel=dict(before_sha=sha(pin_panel), after_sha=sha(after_panel)))
with open(os.path.join(OUT, "VERIFY_RESULT.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for k in ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]:
    print(k, results[k]["status"])
print("ALL_PASS", all_pass)
print("COV sha", sha(pin_cov), "->", sha(after_cov))
print("PANEL sha", sha(pin_panel), "->", sha(after_panel))
