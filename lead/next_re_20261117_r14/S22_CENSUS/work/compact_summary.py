import sys, json, collections
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
cnt=json.load(open(EVD/'counts.json',encoding='utf-8'))
kinds=collections.Counter(r['anchor_kind'] for r in rows)
cc=collections.Counter(r['class_name'] for r in rows if r['anchor_kind']!='A4')
class_sg={}
for r in rows:
    if r['anchor_kind']!='A4' and r['class_name'] not in class_sg: class_sg[r['class_name']]=r['suggested_subsystem']
def is_business(cls):
    sg=class_sg.get(cls,'-')
    return sg not in ('S22(保留)','-','') and not sg.endswith('(hint)')
def mark(cls): return ' ★' if is_business(cls) else ''
top=cc.most_common(40)
special=['SpawnManagerClass','InfantryClass','BuildingClass','UnitClass','VehicleClass','AircraftClass','FootClass','TechnoClass','ObjectClass','AbstractClass','TeamClass','HouseClass','WeaponTypeClass','WarheadTypeClass','BulletClass','CommandClass','TagClass','TriggerClass','SuperClass','ParticleClass','AnimClass','CellClass','MapClass','CampaignClass']
not_top=[]
for c in special:
    if cc[c] and c not in dict(top):
        not_top.append('%s(%d→%s)'%(c,cc[c],class_sg.get(c,'-')))
zero=[c for c in ('InfantryClass','BuildingClass') if not cc[c]]
L=[]
L.append('# S22-CENSUS SUMMARY')
L.append('- 口径/总体：S22_TOTAL=**%d**（coverage subsystem==S22 ∩ atlas entry，统一大小写）；coverage=%d行，S22全量=%d，atlas=%d，S22在atlas外=%d；SHA-256=`%s`；未改共享表。'%(cnt['S22_TOTAL'],cnt['coverage_rows'],cnt['s22_all_rows'],cnt['atlas_rows'],cnt['s22_all_rows']-cnt['S22_TOTAL'],cnt['sha256']))
L.append('- 类名可定性：ANCHORED=**%d/%d=%.2f%%**（A1=%d,A2=%d,A3=%d）；UNANCHORED=**%d/%d=%.2f%%**（A4）；不判grade。'%(cnt['ANCHORED'],cnt['S22_TOTAL'],cnt['anchored_pct'],cnt['A1'],cnt['A2'],cnt['A3'],cnt['UNANCHORED'],cnt['S22_TOTAL'],cnt['unanchored_pct']))
L.append('- 独立扫描：TD=%d，COL=%d，.rdata虚表=%d，槽值=%d；不读vtables_v2、不用atlas边界；类名链=COL+0xC→TD，TD+8内联串（COL+8仅CD偏移）；★=明确业务类建议；Top40外明显业务类=%s；直接RTTI类行数=0=%s。'%(cnt['TD'],cnt['COL'],cnt['vtable_tables'],cnt['vtable_slots'],'; '.join(not_top) if not_top else '无','/'.join(zero) if zero else '无'))
L.append('## TD类名Top40（按行数；★=建议迁出S22）')
L.append('| # | TD类名 | 行数 | 建议 |')
L.append('|---:|---|---:|---|')
for i,(cls,n) in enumerate(top,1): L.append('| %d | `%s`%s | %d | %s |'%(i,cls,mark(cls),n,class_sg.get(cls,'-')))
L.append('| — | 其余%d个类名合计 | %d | — |'%(len(cc)-40,cnt['ANCHORED']-sum(n for _,n in top)))
dist='；'.join('%s %d行'%(k,v) for k,v in sorted(cnt['migration_by_subsystem'].items()))
L.append('若D-37允许再归属：可迁移建议=**%d行**（%s）；模板/容器建议留S22，未定类不可迁移。SpawnManager构造器：S22=006B6C90/006B6EA0，S10=006B7F10/006B8120。'%(cnt['migration_suggested'],dist))
L.append('A4抽样40行逐条说明A1/A2/A3为何未命中（EVIDENCE/A4_samples.tsv）；另查等价形（寄存器中介VT写、MEM.disp、raw dword），只在channel_hits.tsv留痕；006B6EA0在atlas body内A2锚到SpawnManagerClass TD=00840120，006B6C90为A4。交付：CENSUS.tsv+EVIDENCE+work/census.py。')
OUT.joinpath('SUMMARY.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
print('lines',len(L),'top',len(top),'not_top',not_top,'zero',zero)
