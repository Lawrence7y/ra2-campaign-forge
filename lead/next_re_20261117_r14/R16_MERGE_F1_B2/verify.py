# -*- coding: utf-8 -*-
"""R16-MERGE-F1 B2 验证脚本（可复跑，只读盘 + 本目录 before_state.json）。
9 项验证全部按卡面 §4；输出 VERIFY.txt 到本目录。不修改任何 coverage/PANEL 文件。
"""
import os, sys, json, hashlib, csv, re, collections, datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
OUT  = os.path.join(ROOT, "R16_MERGE_F1_B2")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
STRICT_JSON = os.path.join(OUT, "strict_panel.json")

bs=json.load(open(os.path.join(OUT,"before_state.json"),encoding="utf-8"))
as_=json.load(open(os.path.join(OUT,"after_state.json"),encoding="utf-8"))
BEFORE_COV_SHA=bs["coverage"]["sha256"]; BEFORE_PAN_SHA=bs["panel"]["sha256"]
AFTER_COV_SHA=as_["coverage"]["sha256"]; AFTER_PAN_SHA=as_["panel"]["sha256"]
BEFORE_COL4=bs["before_col4"]
M90=bs["panel_insert_block"]
DENTRIES=as_["merged_entries"]

results=[]
def chk(n, label, ok, detail=""):
    results.append((n,label,"PASS" if ok else "FAIL",detail))
    print(("PASS" if ok else "FAIL"), f"[{n}]", label, ("- "+detail) if detail else "")

def sha(b): return hashlib.sha256(b).hexdigest()
def lines_of(p):
    raw=open(p,"rb").read(); return raw, raw.decode("utf-8").split("\n")

cov_raw,cov_lines=lines_of(COV)
pan_raw,pan_lines=lines_of(PANEL)
data=[ln for ln in cov_lines[1:] if ln!=""]
rows=[ln.split("\t") for ln in data]
assert all(len(r)==8 for r in rows)
idx_by={}
for i,r in enumerate(rows): idx_by.setdefault(r[0].strip().upper(),[]).append(i)

# ---------- 1. coverage 逐字节还原性 ----------
orig_by_e={e:rows[idx_by[e][0]][3] for e in DENTRIES}
recon_rows=[list(r) for r in rows]
for e in DENTRIES:
    recon_rows[idx_by[e][0]][3]=BEFORE_COL4[e]
recon_cov_raw=("\n".join([cov_lines[0]]+["\t".join(r) for r in recon_rows])).encode("utf-8")
recon_sha=sha(recon_cov_raw)
chk(1,"coverage.tsv 逐字节还原性（18 行第4列换回改前原值后 sha256 == 改前 sha256）",
    recon_sha==BEFORE_COV_SHA,
    f"recon={recon_sha[:12]} before={BEFORE_COV_SHA[:12]}")

# ---------- 2. 不变量 ----------
proved=sum(1 for r in rows if r[4].strip()=="[已证]")
col_dist=dict(collections.Counter(len(r) for r in rows))
# atlas
atlas=set()
with open(ATLAS,encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0: continue
        p=line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            e=p[0].strip().upper()
            if e.startswith("0X"): e=e[2:]
            try: e="%08X"%int(e,16)
            except ValueError: pass
            atlas.add(e)
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except ValueError: return e
in_atlas=sum(1 for r in rows if r[4].strip()=="[已证]" and ne(r[0]) in atlas)
out_atlas=proved-in_atlas
grade18=[rows[idx_by[e][0]][4].strip() for e in DENTRIES]
inv_ok=(len(data)==18498 and col_dist=={8:18498} and proved==1654
        and in_atlas==1648 and out_atlas==6
        and all(g=="[已证]" for g in grade18) and len(grade18)==18)
chk(2,"不变量 18498/{8:18498}/1654/1648/6 + 18 行 grade 仍 [已证]",inv_ok,
    f"rows={len(data)} coldist={col_dist} proved={proved} atlas_in={in_atlas} atlas_out={out_atlas} grade18_ok={sum(1 for g in grade18 if g=='[已证]')}/18")

# ---------- 3. 只有 18 行第4列变了 ----------
before_rows=[list(r) for r in rows]
for e in DENTRIES:
    before_rows[idx_by[e][0]][3]=BEFORE_COL4[e]
diff_idx=[i for i in range(len(rows)) if rows[i]!=before_rows[i]]
diff_entries=sorted(rows[i][0].strip().upper() for i in diff_idx)
only_col4=all([j for j in range(8) if rows[i][j]!=before_rows[i][j]]==[3] for i in diff_idx)
chk(3,"只有 18 行第4列变了（差异 entry 恰为这 18 个，每行仅第4列不同）",
    diff_entries==sorted(DENTRIES) and only_col4,
    f"diff_rows={len(diff_idx)} entry_match={diff_entries==sorted(DENTRIES)} only_col4={only_col4}")

# ---------- 4. 严格前缀 18/18 ----------
prefix_ok=[]
for e in DENTRIES:
    b=BEFORE_COL4[e]; a=orig_by_e[e]
    prefix_ok.append(a!=b and a.startswith(b))
chk(4,"严格前缀 18/18",all(prefix_ok),f"{sum(prefix_ok)}/18")

# ---------- 5. 六个实测数 ----------
NA_pre=sum(1 for r in recon_rows if r[4].strip()=="[已证]" and "④" in r[3])
NA_post=sum(1 for r in rows if r[4].strip()=="[已证]" and "④" in r[3])
NB_pre=sum(1 for r in recon_rows if r[4].strip()=="[已证]" and "④ 活表槽位见证" in r[3])
NB_post=sum(1 for r in rows if r[4].strip()=="[已证]" and "④ 活表槽位见证" in r[3])
NpreA=sum(1 for e in DENTRIES if "④" in BEFORE_COL4[e])
NpreB=sum(1 for e in DENTRIES if "④ 活表槽位见证" in BEFORE_COL4[e])
six=dict(N_pre_A=NpreA,N_pre_B=NpreB,N_A_pre=NA_pre,N_A_post=NA_post,N_B_pre=NB_pre,N_B_post=NB_post)
six_ok=(NpreA==bs["N_pre_A"]==15 and NpreB==bs["N_pre_B"]==0
        and NA_pre==bs["N_A_pre"]==351 and NA_post==as_["N_A_post"]==354
        and NB_pre==bs["N_B_pre"]==152 and NB_post==as_["N_B_post"]==170
        and NA_post-NA_pre==3 and NB_post-NB_pre==18)
chk(5,"六个实测数",six_ok,json.dumps(six,ensure_ascii=False)+" netA=3 netB=18")

# ---------- 6. §12.6 / §12.4 命中计数（18 行内 + 全表） ----------
seg126_18=seg124_18=0
for e in DENTRIES:
    seg=orig_by_e[e][len(BEFORE_COL4[e]):]
    if "§12.6" in seg: seg126_18+=1
    if "§12.4" in seg: seg124_18+=1
def full126(rws): return sum(1 for r in rws if "§12.6" in r[3])
def full124(rws): return sum(1 for r in rws if "§12.4" in r[3])
t126_post=full126(rows); t124_post=full124(rows)
t126_pre=full126(recon_rows); t124_pre=full124(recon_rows)
chk(6,"§12.6/§12.4 命中计数",
    seg126_18==18 and seg124_18==0 and t124_post==0 and t124_pre==0 and t126_post==t126_pre+18,
    f"18行内 §12.6={seg126_18}/18 §12.4={seg124_18}; 全表 §12.6 {t126_pre}->{t126_post} §12.4 {t124_pre}->{t124_post}")

# ---------- 7. PANEL.md 还原性 ----------
# 找到 M90 块（marker 行到 '本次只补...' 行），整块切掉
m90_start=None
for i,ln in enumerate(pan_lines):
    if ln.startswith("> ✅ **M90 补记"):
        m90_start=i; break
m90_ok=False; m90_detail="M90 marker not found"
if m90_start is not None:
    m90_end=m90_start
    j=m90_start
    while j<len(pan_lines):
        ln=pan_lines[j]
        if ln.startswith("> 📌") or (ln and not ln.startswith("> ")) or ln=="": break
        m90_end=j; j+=1
    block=pan_lines[m90_start:m90_end+1]
    recon_pan_raw="\n".join(pan_lines[:m90_start]+pan_lines[m90_end+1:]).encode("utf-8")
    rps=sha(recon_pan_raw)
    m90_ok=(block==M90 and rps==BEFORE_PAN_SHA)
    m90_detail=f"block_lines={m90_start+1}-{m90_end+1} block_eq={block==M90} recon={rps[:12]} before={BEFORE_PAN_SHA[:12]}"
chk(7,"PANEL.md 还原性（删掉 M90 披露块后 sha256 == 改前 sha256）",m90_ok,m90_detail)

# ---------- 8. 达标未翻转（strict_panel.py 口径复算） ----------
sp_ok=False; sp_detail="strict_panel.json missing"
if os.path.exists(STRICT_JSON):
    sp=json.load(open(STRICT_JSON,encoding="utf-8"))
    nom=sorted(r["S"] for r in sp["rows"] if r["dod_nominal"])
    strict=sorted(r["S"] for r in sp["rows"] if r["dod_strict"])
    sp_ok=(nom==["S15","S16","S17"] and strict==["S17"]
           and sp["total"]["dod_nominal"]==3 and sp["total"]["dod_strict"]==1
           and sp["total"]["proved_n"]==1648 and sp["total"]["proved_strict_n"]==1331)
    sp_detail=f"nominal={','.join(nom)} strict={','.join(strict)} proved={sp['total']['proved_n']} strict_n={sp['total']['proved_strict_n']}"
chk(8,"达标未翻转（strict_panel.py 复算：名义 S15,S16,S17 / 严格 S17）",sp_ok,sp_detail)

# ---------- 9. 行尾 ----------
def le_raw(raw): return dict(crlf=raw.count(b"\r\n"),lf=raw.count(b"\n"),cr=raw.count(b"\r"),ends=raw.endswith(b"\n"))
cov_le_b=bs["coverage"]; cov_le_a=as_["coverage"]
pan_le_b=bs["panel"]; pan_le_a=as_["panel"]
le_ok=(
    cov_le_b["crlf"]==0 and cov_le_b["cr"]==0 and cov_le_a["crlf"]==0 and cov_le_a["cr"]==0
    and pan_le_b["crlf"]==0 and pan_le_b["cr"]==0 and pan_le_a["crlf"]==0 and pan_le_a["cr"]==0
    and cov_le_b["ends_with_newline"]==cov_le_a["ends_with_newline"]
    and pan_le_b["ends_with_newline"]==pan_le_a["ends_with_newline"]
)
chk(9,"行尾（两文件改前改后均 LF-only，无混用）",le_ok,
    f"cov before LF={cov_le_b['lf']} after LF={cov_le_a['lf']} CRLF=0; pan before LF={pan_le_b['lf']} after LF={pan_le_a['lf']} CRLF=0")

# ---------- sha 对照 ----------
chk(0,"改前/改后 sha256 与 state 一致（sanity）",
    sha(cov_raw)==AFTER_COV_SHA and sha(pan_raw)==AFTER_PAN_SHA,
    f"cov disk={sha(cov_raw)[:12]} state={AFTER_COV_SHA[:12]}; pan disk={sha(pan_raw)[:12]} state={AFTER_PAN_SHA[:12]}")

npass=sum(1 for r in results if r[2]=="PASS")
nfall=sum(1 for r in results if r[2]=="FAIL")
lines=["R16-MERGE-F1 B2 · VERIFY（9 项验证）",
       "generated: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
       "="*70]
for n,label,st,detail in results:
    lines.append(f"[{n}] {st}  {label}")
    if detail: lines.append("      "+detail)
lines.append("")
lines.append(f"TOTAL: {npass} PASS / {nfall} FAIL")
lines.append("")
lines.append("coverage.tsv: BEFORE %d %s -> AFTER %d %s" % (
    bs["coverage"]["bytes"],BEFORE_COV_SHA[:8],as_["coverage"]["bytes"],AFTER_COV_SHA[:8]))
lines.append("PANEL.md    : BEFORE %d %s -> AFTER %d %s" % (
    bs["panel"]["bytes"],BEFORE_PAN_SHA[:8],as_["panel"]["bytes"],AFTER_PAN_SHA[:8]))
lines.append("六个实测数: "+json.dumps(six,ensure_ascii=False))
lines.append("达标集合: 名义 S15,S16,S17 / 严格 S17（strict_panel.py 复算）")
open(os.path.join(OUT,"VERIFY.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("="*50)
print(f"VERIFY: {npass} PASS / {nfall} FAIL")
