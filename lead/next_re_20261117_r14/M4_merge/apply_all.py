# M4 — apply all 5 fixes. Backups go to M4_merge/_backup/.
import os, collections, bisect, shutil

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COVD = os.path.join(R14, "COVERAGE")
M4D = os.path.join(R14, "M4_merge")
BAK = os.path.join(M4D, "_backup")
os.makedirs(BAK, exist_ok=True)
COV = os.path.join(COVD, "coverage.tsv")
PROBE = os.path.join(COVD, "probe_and_data_entries.tsv")
PEND = os.path.join(COVD, "PENDING_CORRECTIONS.tsv")
UNS = os.path.join(COVD, "UNSOURCED_PROVED.tsv")
PANEL = os.path.join(COVD, "PANEL.md")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
Y="[\u5df2\u8bc1]"; ST="[\u9759\u6001\u63a8\u65ad]"; W="[\u672a\u8bc1]"

def rd(p):
    with open(p,"r",encoding="utf-8",newline="") as f: return f.read()
def wr(p,s):
    with open(p,"w",encoding="utf-8",newline="") as f: f.write(s)
def lines(txt):
    d = txt.split("\n")
    if d and d[-1]=="": d.pop()
    return [l[:-1] if l.endswith("\r") else l for l in d]

for p in (COV,PROBE,PEND,UNS,PANEL):
    shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
print("backups written to", BAK)

# ---------- load ----------
cov_txt = rd(COV); cov_l = lines(cov_txt)
probe_txt = rd(PROBE); probe_l = lines(probe_txt)
pend_txt = rd(PEND); pend_l = lines(pend_txt)
uns_txt = rd(UNS)
panel_txt = rd(PANEL)

# ---------- TASK 1: remove 5 rows from coverage ----------
TARGETS = {"0043F2AE":(302,"0x43f180","S12-K2"),
           "0043F218":(152,"0x43f180","S12-K2"),
           "0043F678":(1272,"0x43f180","S12-K2"),
           "0047C878":(600,"0x47c620","W177-D"),
           "005684B1":(241,"0x5683c0","S12-K2")}
cov_rows = [l.split("\t") for l in cov_l[1:]]
assert len(cov_rows)==18436, len(cov_rows)
removed = {}
kept = [cov_l[0]]
for l in cov_l[1:]:
    f=l.split("\t")
    if f[0].upper() in TARGETS:
        removed[f[0].upper()] = f
    else:
        kept.append(l)
assert len(removed)==5, removed.keys()
assert len(kept)-1==18431, len(kept)-1
new_cov_txt = "\n".join(kept)+"\n"
wr(COV,new_cov_txt)
print("\n[TASK1] coverage rows 18436 ->",len(kept)-1)
for k,v in removed.items(): print("   removed:", v[0],"grade",v[4],"host",TARGETS[k][1],"+",TARGETS[k][0])

# ---------- TASK 1+2: probe rows ----------
probe_rows = [l.split("\t") for l in probe_l[1:]]
# (a) update note on 3 existing internal_label rows already in probe
NOTES = {"0043F218":152,"0043F2AE":302,"0043F678":1272}
out_probe=[probe_l[0]]
seen=set()
for l in probe_l[1:]:
    f=l.split("\t")
    e=f[0].upper()
    if e in NOTES:
        while len(f)<8: f.append("")
        f[7]=f"函数体内标签，宿主 0x43F180 +{NOTES[e]}（M4 从 coverage.tsv 移出；测距复核）"
        seen.add(e)
    out_probe.append("\t".join(f))
assert seen==set(NOTES), seen
# (b) insert 2 new internal_label rows in numeric-entry order
new_rows = [
 ["0047C878","internal_label","S12","CanPlaceBackupBranch",ST,
  "lead/next_re_20261117_r14/W177-D/EVIDENCE/state_bypass_final.jsonl","W177-D",
  "函数体内标签，宿主 0x47C620 +600（M4 从 coverage.tsv 移出；测距复核）"],
 ["005684B1","internal_label","S12","ChainBitReadSite",ST,
  "lead/next_re_20261117_r14/S12-K2/FEED_W177D.md","S12-K2",
  "函数体内标签，宿主 0x5683C0 +241（M4 从 coverage.tsv 移出；测距复核；修正原 evidence 空格笔误）"],
]
def inskey(f):
    try: return int(f[0],16)
    except: return -1
body = out_probe[1:]
for nr in new_rows:
    idx=len(body)
    for i,f in enumerate(body):
        if inskey(f)>int(nr[0],16): idx=i; break
    body.insert(idx,"\t".join(nr))
out_probe = [probe_l[0]]+body
wr(PROBE,"\n".join(out_probe)+"\n")
print("[TASK1+2] probe rows 130 ->",len(out_probe)-1)

# ---------- PENDING rows ----------
new_pend=[]
# task1: 5 reclassification rows
for e in ["0043F2AE","0043F218","0043F678","0047C878","005684B1"]:
    off,host,card = TARGETS[e]
    new_pend.append([card,e,"entry_kind","函数入口(coverage.tsv数据行)",
        f"函数体内标签(internal_label; 宿主 {host.upper()} +{off})",
        "M4 测距复核(a15_contain.py)",
        f"由函数入口改判为函数体内标签: entry−宿主入口={off} < size; 已移出coverage.tsv、移入probe_and_data_entries.tsv"])
# task5: 14 W177-C token mapping rows
WC = os.path.join(R14,"W177-C","coverage_delta.tsv")
mapping={"[已证·复用]":Y,"[已证读数]":Y,"[已证·观测]":Y,"[未证·未调用]":W,"[推断·可观测]":ST}
wc_rows=lines(rd(WC))[1:]
t5count=0
for l in wc_rows:
    f=l.split("\t")
    if len(f)<6: continue
    tok=f[4]
    if tok not in mapping: continue
    ev=f[5].replace("\\","/")
    full=os.path.join(R14,"W177-C",ev)
    exists=os.path.isfile(full)
    mapped=mapping[tok]
    if mapped==Y and not exists: mapped=W
    basis = ("非标token语义归一; evidence_path="+ev+(" 实存, 保留[已证]" if exists else " 不实存, 降[未证]"))
    if mapped==W and tok=="[未证·未调用]": basis="非标token语义归一: 未调用=未证"
    if mapped==ST: basis="非标token语义归一: 推断·可观测=静态推断(未取EIP); evidence_path="+ev+" 实存"
    new_pend.append(["W177-C",f[0],"grade",tok,mapped,"W177-C coverage_delta.tsv",basis])
    t5count+=1
assert t5count==14, t5count
wr(PEND,pend_txt.rstrip("\n")+"\n"+"\n".join("\t".join(r) for r in new_pend)+"\n")
print("[TASK1+5] PENDING rows 86 ->",len(pend_l)-1+len(new_pend),"(task1 5 + task5 14)")

# ---------- TASK 3: UNSOURCED reason phrase (preserve CRLF) ----------
OLD="任何 delta 均未断言 [已证]"
NEW="该行原 [已证] 缺可核来源，已降 [未证]；如需恢复须由卡提供实存 evidence_path"
cnt=uns_txt.count(OLD)
assert cnt==41, cnt
uns_new=uns_txt.replace(OLD,NEW)
assert uns_new.count(OLD)==0
assert uns_new.count("\r\n")==42, uns_new.count("\r\n")
wr(UNS,uns_new)
print("[TASK3] UNSOURCED_PROVED.tsv reason rows replaced:",cnt)

# ---------- TASK 4: PANEL per-S recompute ----------
atlas_e=set(l.split("\t")[0].lower() for l in lines(rd(ATLAS))[1:])
def isL(n): return n!="" and not n.startswith("sub_")
def isS(n): return isL(n) and "::sub_" not in n
cov2=[l.split("\t") for l in new_cov_txt.split("\n")[1:] if l]
per={}
for r in cov2:
    if r[0].lower() not in atlas_e: continue
    d=per.setdefault(r[1],{"n":0,"L":0,"Sc":0,"P":0})
    d["n"]+=1
    if isL(r[2]): d["L"]+=1
    if isS(r[2]): d["Sc"]+=1
    if r[4]==Y: d["P"]+=1
assert sum(d["n"] for d in per.values())==12916

pl=lines(panel_txt)
newpl=[]
changes=[]
for l in pl:
    fs=[x.strip() for x in l.split("|")]
    if len(fs)>=10 and fs[1].startswith("S") and fs[1][1:].isdigit() and fs[1] in per:
        s=fs[1]; d=per[s]
        old=fs[2:10]  # atlas_n,named_n,pctL,pctS,proved_n,pctP,doctype_n,note
        newline=f"| {s} | {d['n']} | {d['L']} | {d['L']/d['n']*100:.2f} | {d['Sc']/d['n']*100:.2f} | {d['P']} | {d['P']/d['n']*100:.2f} | {old[6]} | {old[7]} |"
        if old[0]!=str(d['n']): changes.append((s,"atlas_n",old[0],d['n']))
        newpl.append(newline); continue
    if len(fs)>=10 and fs[1]=="**TOTAL**":
        tot={k:sum(d[k] for d in per.values()) for k in ("n","L","Sc","P")}
        newline=(f"| **TOTAL** | **{tot['n']}** | **{tot['L']}** | **{tot['L']/tot['n']*100:.2f}** | "
                 f"**{tot['Sc']/tot['n']*100:.2f}** | **{tot['P']}** | **{tot['P']/tot['n']*100:.2f}** | {fs[8]} | {fs[9]} |")
        newpl.append(newline); continue
    newpl.append(l)
assert len(changes)==13, changes
# headline count fixes
joined="\n".join(newpl)
joined=joined.replace("全表 **1,281**","全表 **1,278**")
joined=joined.replace("| 当前 `coverage.tsv`（运营文件行数） | **18,436** | M3 并表后 = 14,495 + 3,941；比 C 多 5 = S12-K2 3 + W177-D 2 两个卡新发现的函数行（不在 initterm/residual 口径内） |",
                      "| 当前 `coverage.tsv`（运营文件行数） | **18,431** | M3 并表后 18,436；M4 剥出 5 行函数体内标签后 = C（14,487+3,944=18,431） |")
joined=joined.replace("| 全表 `[已证]` / atlas 内 `[已证]` | **1,281 / 1,274** | atlas 外 7 条 |",
                      "| 全表 `[已证]` / atlas 内 `[已证]` | **1,278 / 1,274** | atlas 外 4 条（M4 剥出 3 行 atlas 外 `[已证]` 体内标签） |")
joined=joined.replace("全表 `[已证]` **1,281**","全表 `[已证]` **1,278**")
# add recompute note after named columns note
note_line = ("\n> **M4 复算注（逐 S 百分比表内可复算）**：`atlas_n` = `coverage.tsv ∩ function_atlas.tsv` 按 coverage 子系统计数（合计 12,916）；"
             "`named_pct_L` = `named_n/atlas_n`、`proved_pct` = `proved_n/atlas_n`；`named_pct_S` = `(named_n−Class::sub_)/atlas_n`，"
             "`Class::sub_` 共 8 条（S05 1 / S06 1 / S19 6），故 `named_pct_S` 略低于 L。本表 13 处 atlas_n 已由 M2 旧值改正（S05/S06/S07/S08/S09/S10/S12/S14/S18/S19/S20/S21/S22）；"
             "atlas_n 未变的 9 个 S 三列百分比同步未变。\n")
marker="旧 `named_pct` 与 `named_pct_L` 同义，已由 L 列取代。\n"
assert marker in joined
joined=joined.replace(marker,marker+note_line,1)
# add M4 bullet to 本次并表 section
mb=("- **M4 合并（本轮）**：剥出 5 行「落在已知函数体内」的非入口行（`0043F2AE`+302/`0043F218`+152/`0043F678`+1272 于 0x43F180；"
    "`0047C878` 于 0x47C620+600；`005684B1` 于 0x5683C0+241），coverage 18,436→18,431、全表 `[已证]` 1,281→1,278、"
    "probe∩coverage 归零；重算逐 S `atlas_n` 13 处与三列百分比；`UNSOURCED_PROVED.tsv` 41 行理由句改写；"
    "W177-C 14 行非标 token 映射登记 PENDING。详见 `M4_merge\\REPORT.md`。\n")
joined=joined.replace("## 本面板已知不完整处",mb+"\n## 本面板已知不完整处",1)
wr(PANEL,joined)
print("[TASK4] PANEL atlas_n changes:",len(changes))
for c in changes: print("   ",c)

# ---------- final verify ----------
print("\n== FINAL VERIFY ==")
cv=[l.split("\t") for l in lines(rd(COV))[1:]]
print("coverage rows:",len(cv),"| grade:",dict(collections.Counter(r[4] for r in cv)))
pv=[l.split("\t") for l in lines(rd(PROBE))[1:]]
pe={r[0].lower() for r in pv}; ce={r[0].lower() for r in cv}
print("probe rows:",len(pv),"| probe ∩ coverage:",sorted(pe&ce))
print("PENDING rows:",len(lines(rd(PEND)))-1)
unsv=rd(UNS); print("UNS CRLF:",unsv.count("\r\n"),"| old phrase left:",unsv.count(OLD),"| new phrase:",unsv.count(NEW))
