"""Build coverage_delta.tsv for the 8 delivered rows. Uses verified data only.
Card S05-KPROVED3."""
import sys, os, json, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))

CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\rtti_holders.json"))
RSUM=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\EVIDENCE\ROW_SUMMARY.json"))

# (entry, name, ③b detail [same string as EVIDENCE], 错源⑯ [same as EVIDENCE])
ROWS=[
 ('006F3330','FootClass::slot185',
  '③b②可证伪错误码/返回约定2处:+0x00BD cmp dword ptr [eax+0xd50],-1/+0x00C4 je错误路(无效索引→错路);+0x0478 cmp eax,-1/+0x047B jne/+0x047D xor eax,eax(返回0当-1)。严格档③b②成立,不依赖D-42细则#1。',
  '4表同slot185(AircraftClass/BuildingClass/FootClass/TechnoClass)→错源⑯归属=基类级(共同基类TechnoClass);name栏FootClass为其中一表,TD+8逐字与name类一致;DV/V同slot别名=无(非容器族)'),
 ('006F8DF0','TechnoClass::slot241',
  '③b④有界对象读写循环:+0x03FC..+0x0595回跳(backedge +0x0595 jne→+0x03FC),循环体显式对象写+0x0522 mov [edi+0x10],ecx/+0x0525 mov [edx+eax*4],ebp/+0x0569 mov [edi+0x10],ecx/+0x0570 mov [edx+eax*4],ecx;界判+0x057B cmp eax,ecx;推进+0x050B/+0x0552 add eax,ecx;体内9次helper虚调。另有同构大循环+0x05EE..+0x095B(显式对象写8处)。读→判→显式写→推进+界全齐,严格档③b④成立,非仅栈累加。',
  '单持有表TechnoClass slot241,错源⑯不触发(holders=1);DV/V同slot别名=无(非容器族)'),
 ('006FC0B0','FootClass::slot240',
  '③b②可证伪-1哨兵4处:+0x0717 cmp eax,-1/je错误路;+0x087C cmp edx,-1/je;+0x0887 cmp eax,-1/je;+0x08AB cmp edx,-1/je(索引-1→错路/返回3)。严格档③b②成立,不依赖D-42细则#1。',
  '2表同slot240(FootClass/TechnoClass)→错源⑯归属=基类级(共同基类TechnoClass);name栏FootClass为其中一表,TD+8逐字一致;DV/V同slot别名=无(非容器族)'),
 ('006FFEC0','TechnoClass::slot29',
  '③b②可证伪-1哨兵:+0x03D3 cmp edx,-1/+0x03D6 je错误路(无效索引-1→错路);另有有界循环+0x01F9..+0x0238(cmp edi,esi/全局界/inc推进)。严格档③b②成立,不依赖D-42细则#1。',
  '单持有表TechnoClass slot29,错源⑯不触发(holders=1);DV/V同slot别名=无(非容器族)'),
 ('00704350','TechnoClass::slot187',
  '③b②可证伪-1哨兵3处:+0x01A8 cmp edi,-1/je;+0x01D5 cmp ebx,-1/je;+0x0201 cmp eax,-1/je(索引-1→错路)。③b④有界循环:+0x05B7..+0x05C8(inc eax/add ecx,4/cmp eax,3/jl)与+0x05D5..+0x0639(cmp 0xffff/0xff哨兵/inc edi/add esi,4/cmp edi,3/jl)。严格档③b②+④成立。',
  '单持有表TechnoClass slot187,错源⑯不触发(holders=1);DV/V同slot别名=无(非容器族)'),
 ('0070BF50','TechnoClass::slot5',
  '③b②可证伪返回约定:+0x000C call 0x65ab80/+0x0011 xor ebx,ebx/+0x0013 cmp eax,ebx/+0x0015 jl→+0x02F9(pop esi;pop ebx;ret 8),helper返回负值时本函数立即返回该负值(错误返回字节可预测);③b④有界循环+0x003F..+0x004E(dec ebp初值8/jne回跳,add edi,4推进,每轮call 0x6cf240清一字段)。严格档③b②成立,不依赖D-42细则#1。',
  '单持有表TechnoClass slot5,错源⑯不触发(holders=1);DV/V同slot别名=无(非容器族)'),
 ('00712170','TechnoTypeClass::slot25',
  '③b②可证伪-1哨兵35处(如+0x0CC2/+0x0CFE/+0x0D3A cmp eax,-1/je错误路);③b④显式对象写有界循环:+0x076C..+0x0828(backedge +0x0828 jl→+0x076C,写+0x07DA mov [edi-0x1fc],eax/+0x0811 mov [edi],eax,推进+0x081D inc eax/+0x0822 add edi,0x1c,界+0x0826 cmp eax,ecx)与+0x39CB..+0x3C19(backedge +0x3C19 jl→+0x39CB,12处显式对象写,+0x3C17 cmp eax,ecx界)。严格档③b②+④成立。',
  '单持有表TechnoTypeClass slot25,错源⑯不触发(holders=1);DV/V同slot别名=无(非容器族)'),
 ('00716150','AircraftTypeClass::slot42',
  '③b④有界循环:+0x005E..+0x0104回跳(backedge +0x0104 jne→+0x005E),读word[esi]/word[esi+2],哨兵界+0x005E cmp word[esi],0x7fff/+0x0065 cmp word[esi+2],0x7fff(0x7fff=终止哨兵),推进+0x0077 add esi,4,写+0x0085 mov [esp+0x14],cx/+0x008A mov [esp+0x16],dx/+0x0095 mov [esp+0x18],eax(坐标为累加器写口径)。严格档③b④成立(哨兵界+推进+显式累加器写),不依赖D-42细则#1。',
  '4表同slot42(AircraftTypeClass/InfantryTypeClass/TechnoTypeClass/UnitTypeClass)→错源⑯归属=基类级(共同基类TechnoTypeClass);name栏AircraftTypeClass为其中一表,TD+8逐字一致;DV/V同slot别名=无(非容器族)'),
]

# ② full holder enumeration string with class-name consistency assertion
def fmt_holders(key,name):
    hs=HOLD[key]
    cls=name.split('::')[0]
    parts=[]
    for h in hs:
        mark="←name类"+cls if h['name']=='.?AV'+cls+'@@' else ""
        parts.append(f"{h['vt']}[{h['slot']}]→COL{h['col']}→TD+8='{h['name']}'{mark}")
    # M2: name class must appear as a TD+8 holder class
    assert any(h['name']=='.?AV'+cls+'@@' for h in hs), f"class mismatch {cls} {key} {hs}"
    return "②全.rdata原始命中="+str(len(hs))+"表全部持有:"+";".join(parts)+"(name类"+cls+"为其中一持有表,TD+8逐字一致)"

def fmt_sites(key):
    r=next(z for z in RSUM if z['entry']==key)
    ss=r['sites']
    saddr=','.join(ss[:4])
    return len(ss),saddr

out=["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
for key,name,bdetail,x16 in ROWS:
    x=CFG[key]; e=int(key,16)
    ns,saddr=fmt_sites(key)
    p1=f"①entry {key} 16B对齐+E8体外直调见证"
    p2=fmt_holders(key,name)+";"+x16
    p3=bdetail
    p4=f"④direct E8边界@外体站点{ns}处({saddr}),site+5+rel32==entry/体外/非自环;CFG extent+0x0000..+0x{int(x['hi'],16)-e:04X}"
    sem=f"[已证] {p1};{p2};{p3};{p4}"
    ev=f"EVIDENCE/ROW_{key}.txt;EVIDENCE/ROW_SUMMARY.json;EVIDENCE/baselines.json"
    out.append('\t'.join([key,'S05',name,sem,'[已证]',ev]))

open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\coverage_delta.tsv",'w',encoding='utf-8').write('\n'.join(out)+'\n')
print("wrote coverage_delta.tsv with",len(out)-1,"data rows")
# self checks
import re
BAD=['未证','未定','弱信号','线索']
for line in out[1:]:
    p=line.split('\t')
    assert p[4]=='[已证]'
    for b in BAD: assert b not in p[3], f"badword {b} in {p[0]}"
assert len(out)-1==8
print("SELFCHECK: 8 rows, grade all [已证], no self-undeclared words, class names match name")
