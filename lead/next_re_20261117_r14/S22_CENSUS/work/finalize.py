import sys, os, json, collections, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
OUT=Path(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS')
EVD=OUT/'EVIDENCE'
rows=[]
with open(OUT/'CENSUS.tsv',encoding='utf-8') as f:
    hdr=f.readline().rstrip('\n').split('\t')
    for ln in f:
        r=ln.rstrip('\n').split('\t')
        if len(r)==len(hdr): rows.append(dict(zip(hdr,r)))
kinds=collections.Counter(r['anchor_kind'] for r in rows)
n=len(rows); anch=kinds['A1']+kinds['A2']+kinds['A3']; un=kinds['A4']
cc=collections.Counter(r['class_name'] for r in rows if r['anchor_kind']!='A4')
top=cc.most_common(40); top_sum=sum(v for _,v in top)
mig=collections.Counter()
for r in rows:
    sg=r['suggested_subsystem']
    if r['anchor_kind']!='A4' and sg and sg!='S22(保留)' and sg!='-' and not sg.endswith('(hint)'): mig[sg]+=1
manifest=(EVD/'scan_manifest.txt').read_text(encoding='utf-8')
def mval(k):
    mm=re.search(r'^'+re.escape(k)+r'=(\d+)',manifest,re.M); return int(mm.group(1)) if mm else 0
TD=mval('TD_count'); COL=mval('COL_count'); VTS=mval('vtable_count'); SLOTS=mval('vtable_slots')
if (COL,VTS,SLOTS)==(0,0,0):
    mm=re.search(r'TD_count=(\d+) COL_count=(\d+) vtable_count=(\d+) vtable_slots=(\d+)',manifest)
    if mm: TD,COL,VTS,SLOTS=[int(x) for x in mm.groups()]
exe_size=mval('exe_size'); sha=re.search(r'^exe_sha256=(\S+)',manifest,re.M).group(1)
cov_n=sum(1 for _ in open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/coverage.tsv',encoding='utf-8',errors='replace'))-1
atl_n=sum(1 for _ in open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv',encoding='utf-8',errors='replace'))-1
covrows=[ln.rstrip('\n').split('\t') for ln in open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/coverage.tsv',encoding='utf-8',errors='replace').read().splitlines()[1:] if ln.strip()]
s22all=sum(1 for r in covrows if r[1]=='S22')
gmap={r[0].upper():r[4] for r in covrows}
g=collections.Counter(gmap[r['entry']] for r in rows)
special=['SpawnManagerClass','InfantryClass','BuildingClass','UnitClass','VehicleClass','AircraftClass','FootClass','TechnoClass','ObjectClass','AbstractClass','TeamClass','HouseClass','WeaponTypeClass','WarheadTypeClass','BulletClass','CommandClass','TagClass','TriggerClass','SuperClass','ParticleClass','AnimClass','CellClass','MapClass','CampaignClass']
special_rows=[]
for c in special:
    if cc[c]:
        sg=next((r['suggested_subsystem'] for r in rows if r['class_name']==c and r['anchor_kind']!='A4'),'-')
        special_rows.append((c,cc[c],sg))

L=[]
L.append('# S22-CENSUS SUMMARY'); L.append('')
L.append('## 口径与总体')
L.append('- S22_TOTAL = **%d**（coverage.tsv subsystem==S22 ∩ function_atlas.tsv entry，先统一大小写）；盘上复算一致。'%n)
L.append('- coverage.tsv 全表 %d 行；S22 全量 %d 行；atlas %d 行；S22 中 %d 行在 atlas 外（本卡不计）。'%(cov_n,s22all,atl_n,s22all-n))
L.append('- 只读 gamemd.exe：%d B，SHA-256 `%s`；未改 coverage / PANEL / 任何卡目录。'%(exe_size,sha))
L.append(''); L.append('## 类名可定性（D-37 事实基础）')
L.append('- ANCHORED = **%d / %d = %.2f%%**（A1=%d，A2=%d，A3=%d）。'%(anch,n,100*anch/n,kinds['A1'],kinds['A2'],kinds['A3']))
L.append('- UNANCHORED = **%d / %d = %.2f%%**（A4）；这不是语义未证，只表示三条类名通道未命中。'%(un,n,100*un/n))
L.append('- 独立扫描：TD=%d，COL=%d，.rdata 虚表=%d，槽值=%d（不读 vtables_v2.json，不用 atlas 边界反推虚表）。'%(TD,COL,VTS,SLOTS))
L.append('- 类名链固定为 COL+0xC -> TD，名在 TD+8 内联串；COL+8 是 CD 偏移，未用于取名。')
L.append(''); L.append('## 按 TD 类名聚合（Top 40 + 其余）')
L.append('| # | TD 类名 | 行数 | 建议归属(不执行) |'); L.append('|---:|---|---:|---|')
for i,(cls,cnt) in enumerate(top,1):
    sg=next(r['suggested_subsystem'] for r in rows if r['class_name']==cls and r['anchor_kind']!='A4')
    L.append('| %d | `%s` | %d | %s |'%(i,cls,cnt,sg))
L.append('| — | 其余 %d 个类名合计 | %d | — |'%(len(cc)-40,anch-top_sum))
L.append(''); L.append('## 明显业务子系统类（建议，不执行）')
L.append('| 类名 | 行数 | 建议流向 |'); L.append('|---|---:|---|')
for c,cnt,sg in special_rows: L.append('| `%s` | %d | %s |'%(c,cnt,sg))
L.append(''); L.append('## 若 D-37 允许再归属')
L.append('- 可迁移建议行数 = **%d**（仅明确业务类；模板/容器建议留 S22；未定类不可迁移）。'%sum(mig.values()))
L.append('- 流向分布：'+'；'.join('%s %d 行'%(k,v) for k,v in sorted(mig.items()))+'。')
L.append('- 注意：`006B6C90`/`006B6EA0` 两个 SpawnManager 构造器是 S22 行（在 atlas 内），`006B7F10`/`006B8120` 是 S10 行；本卡只判类名，不执行归属。')
L.append(''); L.append('## A4 抽样与防假否定')
L.append('- `EVIDENCE/A4_samples.tsv` 给 40 行抽样；每行说明 A1 查了 %d 个槽值、A2 对 entry+size 体逐指令查 `mov [reg],VT`、A3 查了 %d COL + %d TD 的立即数引用。'%(SLOTS,COL,TD))
L.append('- 另查等价形：寄存器中介 VT 写、内存 disp 指向 COL/TD、体内 raw dword COL/TD；只在 `channel_hits.tsv` 留痕，不提升为 A2/A3。')
L.append('- 边界说明：`006B6EA0` 的 5 参数构造路径在 atlas 入口+size 之外；本卡按用户规定的 entry-body 口径，不越过边界改判。')
L.append(''); L.append('## 交付')
L.append('- `CENSUS.tsv`（%d 行）；`EVIDENCE/`（全量 RTTI/COL/VT/槽/通道/A4 抽样/计数）；`work/census.py`（可复跑）。'%n)
L.append('- 文件均写在 `S22_CENSUS/` 内；统计 grade 只读第 5 列，未用 grade 参与类名判定。')
(OUT/'SUMMARY.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
json.dump(dict(S22_TOTAL=n,ANCHORED=anch,UNANCHORED=un,A1=kinds['A1'],A2=kinds['A2'],A3=kinds['A3'],A4=kinds['A4'],anchored_pct=round(100*anch/n,2),unanchored_pct=round(100*un/n,2),coverage_rows=cov_n,atlas_rows=atl_n,s22_all_rows=s22all,TD=TD,COL=COL,vtable_tables=VTS,vtable_slots=SLOTS,distinct_anchored_classes=len(cc),top40_rows=top_sum,rest_rows=anch-top_sum,migration_suggested=sum(mig.values()),migration_by_subsystem=dict(mig),grade_distribution=dict(g),sha256=sha),open(EVD/'counts.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(EVD/'suggested_subsystem_distribution.tsv','w',encoding='utf-8',newline='') as f:
    f.write('suggested_subsystem\tanchored_rows\n')
    for k,v in sorted(collections.Counter(r['suggested_subsystem'] for r in rows if r['anchor_kind']!='A4').items()): f.write('%s\t%d\n'%(k,v))

P=[]
P.append('# S22-CENSUS PROGRESS'); P.append('')
P.append('- 口径：coverage.tsv subsystem==S22 ∩ function_atlas.tsv entry；entry 统一大小写；atlas size 列按十进制读。')
P.append('- 总体：S22 全量 %d 行；S22∩atlas **%d** 行（盘上复算一致）；coverage 全表 %d 行；atlas %d 行。'%(s22all,n,cov_n,atl_n))
P.append('- 二进制：gamemd.exe %d B，SHA-256 `%s`；ImageBase 0x400000；只读打开。'%(exe_size,sha))
P.append(''); P.append('实际扫过的通道（A4 不是假否定）：')
P.append('1. A1：`.rdata` 对齐 dword 找 COL 前缀，COL=sig0, +0xC->TD, +0x10 CHD；从 vt=pos+4 逐槽走到非 `.text`/下一 COL 边界；得 %d 表 / %d 槽；再用槽值集合查 entry。未用 atlas entry+size 反推虚表。'%(VTS,SLOTS))
P.append('2. A1 防坑：TD 名取 `TD+8` 内联 `.?AV/.?AU ... @@`；从不把 `TD+8` 当指针；`COL+8` 只作 CD 偏移，不用于取名。')
P.append('3. A2：对每条 S22∩atlas 行按 atlas size 取体，capstone skipdata=True 逐指令判 `mov [base/index],imm` 且 imm∈%d 个 vtable 起点。'%VTS)
P.append('4. A3：同一指令流逐操作数查 IMM∈%d COL ∪ %d TD；另查 MEM.disp 与体内 raw dword 作等价形留痕。'%(COL,TD))
P.append('5. 双通道：A1 完全不依赖 atlas entry+size；A2/A3 依赖 entry+size 但由反汇编证据逐条留痕。')
P.append('6. 区间空洞 / 边界：未用 atlas 边界推 A1；A2仅按 entry+size 体判定；006B6EA0 的 vptr 写在 0x6B6F5F（距入口 0x70 < size 241）体内命中，006B6C90 按字面 A1/A2/A3 未命中记 A4。')
P.append('7. 不存在判定：A4 = A1/A2/A3 全不命中，且等价形（寄存器中介 VT 写、disp COL/TD、raw dword）计数写入证据。')
P.append('8. 结果：A1=%d，A2=%d，A3=%d，A4=%d；ANCHORED=%d (%.2f%%)，UNANCHORED=%d (%.2f%%)。'%(kinds['A1'],kinds['A2'],kinds['A3'],kinds['A4'],anch,100*anch/n,un,100*un/n))
P.append('9. 写域：仅 `S22_CENSUS/`；未写 coverage / PANEL / 其它卡目录；未 git commit。')
(OUT/'PROGRESS.md').write_text('\n'.join(P)+'\n',encoding='utf-8')
print('SUMMARY lines',len(L),'PROGRESS lines',len(P))
print('kinds',dict(kinds),'classes',len(cc),'migration',sum(mig.values()),dict(mig))
print('special head',special_rows[:12])
