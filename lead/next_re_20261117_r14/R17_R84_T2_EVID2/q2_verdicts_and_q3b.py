#!/usr/bin/env python3
# 记录 Q2 40 件人工判定（只看内容特征：VA/包装/中文/首行 + 对歧义件实读前1500B），不看既有 label
import os, csv
R=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R84_T2_EVID2"
# 顺序对应 q2_sample40_features.txt 的 [01]..[40]
VERD = [
"对象","对象","对象","过程","对象","判不了",   # 1-6
"对象","对象","对象","对象","对象","过程",      # 7-12
"过程","过程","过程","过程","对象","对象",      # 13-18
"对象","对象","对象","对象","过程","对象",      # 19-24
"对象","对象","对象","过程","对象","对象",      # 25-30
"对象","对象","对象","对象","对象","对象",      # 31-36
"过程","对象","过程","对象",                    # 37-40
]
REASON = {
1:"首行 exported .bin size/sha256 + source slice @0x487270：对象导出字节事实",
2:"ra2.mix/0xA8../0xF9.. 245,825B Foundation：mix 条目对象事实",
3:"funcs=12916 insn_map=1030298 text_va=0x401000：对象计数/基址",
4:"poolstats 命名与命中计数(0.68%/94.57%)为测量统计，非对象抄本",
5:"层指针 call[reg+0x1C] 链 + 0x7E6060 地址：对象事实(带中文注)",
6:"自审 '对照 PROGRESS.md 核心数字'：过程自检+对象地址混合，难判",
7:"distinct COL-anchored vtable bases:955：对象虚表事实",
8:"PRIMARY VTABLES recounted：虚表清单对象事实",
9:"factory ctors found in registration fn:67：对象构造点清单",
10:"event name strings at 0x82091C + name[i]@地址：对象字符串表",
11:"all writes to [esi+0] in ctor 0x665650..：对象写点清单",
12:"S0 卫生与就绪基线 + 记录时间 + SHA 表：过程状态记录",
13:"[assert] ... PASS：自检断言，过程输出",
14:"counterexamples_manifest / manipulation / expected：实验清单，过程",
15:"cell_sentinel --perf / 测量对象：扫描逻辑：性能测量，过程",
16:"cpu/frame moving 表：性能测量数据，过程",
17:"# ROW 00417CC0 环①入口与字节：对象行抄本",
18:"# ROW 00524D70 环①入口与字节：对象行抄本",
19:"# ROW 007480B0 环①入口与字节：对象行抄本",
20:"# ROW 004D8560 环①入口与字节：对象行抄本",
21:"# ROW 00519630 环①入口与字节：对象行抄本",
22:"# ROW 0075E2C0 环①入口与字节：对象行抄本",
23:"card 100 rows FUNC 83/100：命中率统计，过程",
24:"# 00431F10 extent/span/n_reachable：对象反汇编事实",
25:"# DISASM entry=0047AAB0 size=13 n_insn=4：对象反汇编",
26:"JSON entry/vt/slot/col/td 结构记录：对象虚表事实表",
27:"JSON strict/loose K,N,p 命中率统计：过程",
28:"====== 004AAE90 ====== 环2基本事实：对象",
29:"JSON entry/vt/col/td/classes 结构记录：对象事实表",
30:"JSON pool_n/K/p/rates 基线统计：过程",
31:"==== 005566A0 name=ControlClass::slot3 size=42：对象细节",
32:"S10 rows/nonproved + 004E0170 name= grade=：对象行事实(含地址)",
33:"==== 004D82B0 FootClass::slot289：对象行抄本",
34:"JSON entry/ok/ndel/vt/cls 审计明细：对象事实表",
35:"# ROW 0075E0C0 环①入口与字节：对象行抄本",
36:"JSON entry/sem/sites/rdata_refs 逐行事实：对象记录表",
37:"W47 builder: wrote ... candidates=114：构建日志，过程",
38:"ROOT ENTRY raw difference (absolute file offset)：对象字节 diff",
39:"W58 FINAL FALSIFICATION + CENSUS：检查/普查记录，过程",
40:"W61 dialog byte diff before/after 664/696 bytes：对象字节 diff",
}
assert len(VERD)==40 and len(REASON)==40
with open(os.path.join(R,"q2_sample40_verdicts.txt"),"w",encoding="utf-8") as f:
    f.write("Q2 40 件人工判定（依据内容，不看任何既有 label）\n")
    from collections import Counter
    for i,v in enumerate(VERD,1):
        f.write(f"[{i:02d}] 我判={v} | {REASON[i]}\n")
    f.write("\n分布: "+str(dict(Counter(VERD)))+"\n")
print("wrote q2_sample40_verdicts.txt", dict(Counter(VERD)))

# ---- Q3 用任务原例的分母口径重算：目录内“全部被检对象(1242)”为分母 ----
import csv
R2=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def load(p): return list(csv.DictReader(open(p,encoding="utf-8",newline=""),delimiter="\t"))
vd=load(os.path.join(R2,"R17_R81_T2_EVID","_verdicts.tsv"))
ud={r["rel"]:int(r["bytes"]) for r in load(os.path.join(R2,"R17_R81_T2_EVID","_undead_evid.tsv"))}
def parent(rel):
    p=os.path.dirname(rel); return p if p else "(root)"
from collections import defaultdict, Counter
dirs=defaultdict(Counter)
for r in vd: dirs[parent(r["rel"])][r["verdict"]]+=1
tie=[r for r in vd if r["verdict"]=="无法判定"]

def rule(min_total, q):
    resolved=[]; unres=[]
    for r in tie:
        c=dirs[parent(r["rel"])]
        tot=sum(c.values())
        o=c["对象抄本"]; p=c["过程输出"]
        if tot<min_total or max(o,p)/tot<q or o==p:
            unres.append(r); continue
        lab="对象抄本" if o>p else "过程输出"
        resolved.append((r,lab,tot,max(o,p)/tot))
    return resolved,unres

lines=[]
for mt,q in [(5,0.75),(6,0.75),(8,0.75),(5,0.8),(3,1.0)]:
    res,unres=rule(mt,q)
    lines.append((mt,q,len(res),sum(ud[r["rel"]] for r,_,_,_ in res),len(unres)))

# 留一法(同目录其他已裁件) 仅对“强多数目录”子集的可靠性
loo_ok=loo_n=0
bydec=defaultdict(list)
for r in vd:
    if r["verdict"] in ("对象抄本","过程输出"): bydec[parent(r["rel"])].append(r["verdict"])
for d,labs in bydec.items():
    tot=sum(dirs[d].values())
    strong = tot>=5 and max(dirs[d]["对象抄本"],dirs[d]["过程输出"])/tot>=0.75
    if not strong: continue
    for i,lab in enumerate(labs):
        others=labs[:i]+labs[i+1:]
        if not others: continue
        pred="对象抄本" if others.count("对象抄本")>=others.count("过程输出") else "过程输出"
        loo_n+=1; loo_ok+=(pred==lab)

with open(os.path.join(R,"q3_summary2.txt"),"w",encoding="utf-8") as f:
    f.write("Q3 规则(分母=目录内1242全部被检件, 例:8件里6件对象=>另2件对象)\n")
    f.write("  min_total=目录被检件下限, q=多数派占比下限\n")
    for mt,q,rc,rb,uc in lines:
        f.write(f"  min_total={mt} q={q}: 可裁 {rc} 件 / {rb} B ; 仍单列 {uc} 件\n")
    f.write(f"\n强多数目录子集的留一法可靠性: {loo_ok}/{loo_n} = {loo_ok/loo_n:.4f}\n")
for mt,q,rc,rb,uc in lines: print("Q3b",mt,q,rc,rb,uc)
print("LOO-strong",loo_ok,"/",loo_n)
