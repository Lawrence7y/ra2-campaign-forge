# -*- coding: utf-8 -*-
"""M59 post-merge verification: recompute everything from disk, write VERIFY.txt."""
import csv, os, collections, re, hashlib

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
D15  = os.path.join(ROOT, "S15S16_3B2", "S15_delta.tsv")
D16  = os.path.join(ROOT, "S15S16_3B2", "S16_delta.tsv")
VERD = os.path.join(ROOT, "S15S16_3B2", "_audit", "verdict.tsv")
OUT  = os.path.join(ROOT, "MERGE_M59", "VERIFY.txt")

PASS = ["006E3DB0","006E4660","006E5730","006E6080","006E6410","00727240","006CE800"]
FAIL = ["006E3E30","006E56E0","006E57A0","007276A0"]
EVID = "S15S16_3B2/_audit/VERDICT.md"

def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X" % int(e,16)
    except ValueError: return e

out=[]
def p(s=""): out.append(str(s))

ok=True
def check(cond, msg):
    global ok
    p(("PASS " if cond else "FAIL ")+msg)
    if not cond: ok=False

# --- atlas ---
atlas=set()
with open(ATLAS,encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0: continue
        q=line.rstrip("\r\n").split("\t")
        if q and q[0].strip(): atlas.add(ne(q[0]))

# --- coverage raw/read ---
raw=open(COV,"r",encoding="utf-8",newline="").read()
p("=== 文件基本形态 ===")
check("\r" not in raw, "coverage.tsv 无 CR（纯 LF）")
check(not raw.endswith("\n"), "coverage.tsv 末尾无换行（与改前一致）")
parts=raw.split("\n")
header=parts[0]
data=parts[1:]
check(header=="entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict",
      "表头逐字未变（逗号分隔 8 字段）")
check(len(data)==18498, "数据行数 = 18,498（实测 %d）"%len(data))
colcount=collections.Counter(len(ln.split("\t")) for ln in data)
check(dict(colcount)=={8:18498}, "所有数据行均 8 列 TAB 分隔（实测 %s）"%dict(colcount))

rows=[ln.split("\t") for ln in data]
byentry={}
for i,r in enumerate(rows): byentry.setdefault(ne(r[0]),[]).append(i)

# --- grade counts ---
gh=collections.Counter(r[4].strip() for r in rows)
full=gh["[已证]"]
ain =sum(1 for r in rows if r[4].strip()=="[已证]" and ne(r[0]) in atlas)
aout=full-ain
p("")
p("=== 全表/atlas 口径已证数 ===")
check(gh["[未证]"]==11024, "[未证] = 11,024（实测 %d）"%gh["[未证]"])
check(gh["[静态推断]"]==5978, "[静态推断] = 5,978（实测 %d）"%gh["[静态推断]"])
check(full==1496, "全表 [已证] = 1,496（实测 %d）"%full)
check(ain==1490, "atlas 内 [已证] = 1,490（实测 %d）"%ain)
check(aout==6, "atlas 外 [已证] = 6（实测 %d）"%aout)
check(sum(gh.values())==18498, "grade 直方图合计 = 18,498")

# --- S15 / S16 proved ---
p("")
p("=== S15 / S16 [已证] 数（atlas 内，按 subsystem） ===")
proved=collections.Counter()
strict=collections.Counter()
for r in rows:
    e=ne(r[0]); s=r[1].strip()
    if e in atlas and r[4].strip()=="[已证]":
        proved[s]+=1
        if "[未证]" not in r[3]: strict[s]+=1
check(proved["S15"]==106, "S15 atlas 内 [已证] (proved) = 106（实测 %d）"%proved["S15"])
check(proved["S16"]==47,  "S16 atlas 内 [已证] (proved) = 47（实测 %d）"%proved["S16"])
check(strict["S15"]==53,  "S15 proved_strict = 53（实测 %d）"%strict["S15"])
check(strict["S16"]==21,  "S16 proved_strict = 21（实测 %d）"%strict["S16"])

# --- delta col4 for comparing ---
delta={}
for df in (D15,D16):
    with open(df,encoding="utf-8-sig",newline="") as f: rr=list(csv.reader(f,delimiter="\t"))
    for r in rr[1:]:
        if len(r)>=6: delta[ne(r[0])]=r[3]

p("")
p("=== 7 行 PASS 新状态（逐列核对） ===")
for e in PASS:
    idxs=byentry.get(e,[])
    if len(idxs)!=1:
        check(False,"%s 在 coverage 出现 %d 次（应 1）"%(e,len(idxs))); continue
    r=rows[idxs[0]]
    checks=[r[4].strip()=="[已证]", r[5]==EVID, r[3]==delta[e]]
    check(all(checks), "%s grade=[已证] / evidence=%s / col4==delta原文（subsys=%s, atlas内=%s）"%(
        e,EVID,r[1], e in atlas))

p("")
p("=== 4 行 FAIL grade 未变（仍 [静态推断]） ===")
for e in FAIL:
    idxs=byentry.get(e,[])
    if len(idxs)!=1:
        check(False,"%s 出现 %d 次"%(e,len(idxs))); continue
    r=rows[idxs[0]]
    check(r[4].strip()=="[静态推断]", "%s grade=[静态推断]（实测 %s）"%(e,r[4].strip()))

# --- verdict cross-check: PASS set exactly 7 / FAIL 4 ---
with open(VERD,encoding="utf-8-sig",newline="") as f: vr=list(csv.reader(f,delimiter="\t"))
vhdr=vr[0]; vdat=vr[1:]
check(vhdr==["entry","subsystem","verdict","check_at","branch_at","consumed_at","reason"],
      "verdict.tsv 7 列表头正确")
check(len(vdat)==11, "verdict.tsv 11 行数据（实测 %d）"%len(vdat))
pass_set=sorted(r[0].strip().upper() for r in vdat if r[2].strip()=="PASS")
fail_set=sorted(r[0].strip().upper() for r in vdat if r[2].strip()=="FAIL")
check(pass_set==sorted(PASS), "verdict PASS 集合恰为 7 行且与卡片一致（实测 %s）"%pass_set)
check(fail_set==sorted(FAIL), "verdict FAIL 集合恰为 4 行且与卡片一致（实测 %s）"%fail_set)

# --- delta counts ---
p("")
p("=== delta 表行数 ===")
with open(D15,encoding="utf-8-sig",newline="") as f: d15=list(csv.reader(f,delimiter="\t"))
with open(D16,encoding="utf-8-sig",newline="") as f: d16=list(csv.reader(f,delimiter="\t"))
check(len(d15)-1==10, "S15_delta 10 行数据（实测 %d）"%(len(d15)-1))
check(len(d16)-1==1,  "S16_delta 1 行数据（实测 %d）"%(len(d16)-1))

# --- atlas membership of 006E6080 ---
check("006E6080" not in atlas, "006E6080 不在 function_atlas（atlas 外，只进全表）")
for e in ("006E3DB0","006E4660","006E5730","006E6410","00727240","006CE800"):
    check(e in atlas, "%s 在 atlas 内"%e)

# --- sha256 current (post) ---
p("")
p("=== 当前文件 SHA-256（改后） ===")
for label,f in (("coverage.tsv",COV),("PANEL.md",PANEL)):
    h=hashlib.sha256(open(f,"rb").read()).hexdigest().upper()
    p("%s = %s"%(label,h))

p("")
p("TOTAL RESULT: "+("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED"))
open(OUT,"w",encoding="utf-8").write("\n".join(out))
print("WROTE",OUT, "OK" if ok else "FAILED")
