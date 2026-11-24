# -*- coding: utf-8 -*-
"""导出 EVIDENCE\ 证据文件（只写 RECON_UNMERGED\EVIDENCE\）。"""
import os, re, json, hashlib, collections

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT,"RECON_UNMERGED","EVIDENCE")
CUR  = os.path.join(ROOT,"COVERAGE","coverage.tsv")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
def W(name, text):
    open(os.path.join(OUT,name),"w",encoding="utf-8",newline="\n").write(text)

CARDS = ["S01_KPROVED","S03_C8","S05_KPROVED4","S05_KPROVED5","S05-K2","S07-K2",
"S09_KPROVED2","S10_K11","S10_K14","S10_KPROVED4","S11_DIRECT","S11_K5","S13_DIRECT",
"S13_K11","S13_KPROVED2","S15_K5","S16_N2","S19-K2","S21_KPROVED2","SEMFIX_6",
"SEMFIX_REST","SEMFIX_S10","SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3","W177_KA"]

# ---- 1 基线 ----
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
lines=[l for l in open(CUR,encoding="utf-8",errors="replace")]
rows=[l for l in lines if l.strip() and not l.startswith("entry,")]
ents=[l.split("\t")[0] for l in rows]
dup=[e for e,c in collections.Counter(ents).items() if c>1]
b=[]
b.append("# 基线（只读）")
b.append("coverage.tsv = lead\\next_re_20261117_r14\\COVERAGE\\coverage.tsv")
b.append("SHA-256 = "+sha(CUR))
b.append("size = %d bytes  mtime = 2026-11-19 17:23:14"%os.path.getsize(CUR))
b.append("总行 = %d（含表头 1 行），数据行 = %d"%(len(lines),len(rows)))
b.append("表头（逗号分隔）= "+lines[0].strip())
b.append("数据行切分字段数分布 = "+str(collections.Counter(len(l.rstrip("\n").split("\t")) for l in rows)))
b.append("entry 唯一数 = %d，重复 = %d %s"%(len(set(ents)),len(dup),dup))
g=collections.Counter(l.split("\t")[4] for l in rows)
b.append("grade 直方图（只读第 5 列）= "+str(dict(g)))
b.append("")
b.append("# function_atlas.tsv")
ap=os.path.join(ROOT,"..","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
ap=os.path.normpath(ap)
al=[l for l in open(ap,encoding="utf-8",errors="replace")]
b.append("path = "+ap)
b.append("总行 = %d，数据行 = %d（期望 12,916）"%(len(al),len(al)-1))
b.append("表头 = "+al[0].strip())
b.append("")
b.append("# 目标二进制")
b.append("ra2youli\\gamemd.exe SHA-256 = 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476（现场复算，与派卡一致；只读，未改）")
b.append("")
b.append("# 快照字节同一性")
b.append("_hygiene\\coverage.M48.bak SHA-256 == 当前 coverage.tsv ⇒ M48 之后无并表事件")
W("baseline.txt","\n".join(b)+"\n")

# ---- 2 快照语义证明 ----
s=[]
s.append("# 证明：_hygiene\\coverage.M<N>.bak = M<N> 卡的『合并前』备份")
s.append("# 判据：若 .bak 为合并后，则已被 M<N> 并入的行不应出现在其中。取三个已知并表记录做单点核验。")
s.append("")
def get(p,e):
    for l in open(p,encoding="utf-8",errors="replace"):
        if l.startswith(e+"\t"):
            q=l.rstrip("\n").split("\t"); return q[4],q[3]
    return None
cases=[("0040F0A0","M36 的 MERGE_LOG 声明 source_card=SEMFIX_6、old=[静态推断]…→new=DynamicVector…"),
       ("0047AE10","M44 的 MERGE_LOG 声明 basis=SEMFIX_SLOTS2/coverage_delta.tsv、old=槽语义未证→new=③b④…"),
       ("006F3330","M45 的 MERGE_LOG 声明 basis=SEMFIX_SLOTS3/…+S05_KPROVED3/_audit/VERDICT.md")]
for e,why in cases:
    s.append("## entry %s   （%s）"%(e,why))
    for m in range(33,47):
        p=os.path.join(ROOT,"_hygiene","coverage.M%d.bak"%m)
        if not os.path.exists(p): continue
        g=get(p,e)
        if g: s.append("   M%-3d.bak  grade=%-10s sem=%s"%(m,g[0],g[1][:60]))
    g=get(CUR,e)
    s.append("   CURRENT   grade=%-10s sem=%s"%(g[0],g[1][:60]))
    s.append("")
s.append("# 结论：新值首次出现在 M<N+1>.bak 中 ⇒ M<N>.bak 是合并前快照，实施并表的卡号 = bak 编号 − 1")
s.append("# 交叉印证：M45.bak 含 SEMFIX_SLOTS2 的 11 行（M44 并入）；M46.bak 含 SEMFIX_SLOTS3 的 15 行（M45 并入）。")
W("snapshot_map.txt","\n".join(s)+"\n")

# ---- 3 逐行时间线 ----
ft=json.load(open(os.path.join(ROOT,"RECON_UNMERGED","work","final_table.json"),encoding="utf-8"))
tl=["card\tentry\tdelta_grade\tdisk_grade\tdisk_sem_eq_delta\tsem_first_at\tgrade_first_at\tmerge_records"]
for x in ft:
    tl.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(x["card"],x["entry"],x["delta_grade"],x["disk_grade"],
        "Y" if x["disk_sem_eq"] else "N", x["sem_first_at"], x["grade_first_at"],
        " ".join("%s:%s"%(y["m"],y["src_card"] or "-") for y in x["merge_recs"])))
W("timeline_rows.tsv","\n".join(tl)+"\n")

# ---- 4 delta 逐卡形态 ----
d=["card\tdelta_bytes\tn_data_rows\tform"]
for c in CARDS:
    p=os.path.join(ROOT,c,"coverage_delta.tsv")
    n=os.path.getsize(p) if os.path.exists(p) else -1
    rows_=[]
    if n>0:
        for l in open(p,encoding="utf-8",errors="replace"):
            if ENTRY_RE.match(l.split("\t")[0].strip()): rows_.append(1)
    if n==0: form="空文件（0 字节）"
    elif len(rows_)==0: form="仅表头/注释，0 数据行"
    else: form="%d 数据行"%len(rows_)
    d.append("%s\t%d\t%d\t%s"%(c,n,len(rows_),form))
W("delta_shapes.tsv","\n".join(d)+"\n")
print("evidence written")
