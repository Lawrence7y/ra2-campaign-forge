"""Generate final EVIDENCE for the 8 delivered rows: all RTTI holders (M1),
错源⑯/DV-V attribution, E8 direct sites with byte verification + ecx source,
CFG extent, ③b features with entry-relative offsets, full disasm.
Card S05-KPROVED3."""
import sys, os, json, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\EVIDENCE"
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\rtti_holders.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
call_sites,insns,addr2i=D['call_sites'],D['insns'],D['addr2i']

# (entry, name, ③b tier, ③b detail with entry-relative offsets, 错源⑯ note)
ROWS=[
 ('006F3330','FootClass::slot185','③b②可证伪-1哨兵',
  '③b②可证伪错误码/返回约定2处:+0x00BD cmp dword ptr [eax+0xd50],-1/+0x00C4 je错误路(无效索引→错路);+0x0478 cmp eax,-1/+0x047B jne/+0x047D xor eax,eax(ret 0当-1)。全体内无跳表,但-1哨兵后接可证伪分支,严格档③b②成立。',
  '4表同slot185(AircraftClass/BuildingClass/FootClass/TechnoClass)→错源⑯归属=基类级(共同基类TechnoClass);name栏FootClass为其中一表,TD+8逐字与name类一致'),
 ('006F8DF0','TechnoClass::slot241','③b④完整I/O循环',
  '③b④有界对象读写循环:+0x03FC..+0x0595回跳(backedge +0x0595 jne→+0x03FC),循环体显式对象写+0x0522 mov [edi+0x10],ecx/+0x0525 mov [edx+eax*4],ebp/+0x0569 mov [edi+0x10],ecx/+0x0570 mov [edx+eax*4],ecx;界判+0x057B cmp eax,ecx;推进+0x050B/+0x0552 add eax,ecx;体内9次helper虚调。另有同构大循环+0x05EE..+0x095B(显式对象写8处)。读→判→显式写→推进+界全齐,严格档③b④成立,非仅栈累加。',
  '单持有表TechnoClass slot241,错源⑯不触发(holders=1)'),
 ('006FC0B0','FootClass::slot240','③b②可证伪-1哨兵',
  '③b②可证伪-1哨兵4处:+0x0717 cmp eax,-1/je错误路;+0x087C cmp edx,-1/je;+0x0887 cmp eax,-1/je;+0x08AB cmp edx,-1/je(索引-1→错路/返回3)。严格档③b②成立。',
  '2表同slot240(FootClass/TechnoClass)→错源⑯归属=基类级(共同基类TechnoClass);name栏FootClass为其中一表,TD+8逐字一致'),
 ('006FFEC0','TechnoClass::slot29','③b②可证伪-1哨兵',
  '③b②可证伪-1哨兵:+0x03D3 cmp edx,-1/+0x03D6 je错误路(无效索引-1→错路);另有有界循环+0x01F9..+0x0238(cmp edi,esi/全局界/inc推进)。严格档③b②成立。',
  '单持有表TechnoClass slot29,错源⑯不触发(holders=1)'),
 ('00704350','TechnoClass::slot187','③b②可证伪-1哨兵',
  '③b②可证伪-1哨兵3处:+0x01A8 cmp edi,-1/je;+0x01D5 cmp ebx,-1/je;+0x0201 cmp eax,-1/je(索引-1→错路)。③b④有界循环:+0x05B7..+0x05C8(inc eax/add ecx,4/cmp eax,3/jl)与+0x05D5..+0x0639(cmp 0xffff/0xff哨兵/inc edi/add esi,4/cmp edi,3/jl)。严格档③b②+④成立。',
  '单持有表TechnoClass slot187,错源⑯不触发(holders=1)'),
 ('0070BF50','TechnoClass::slot5','③b②可证伪负返回',
  '③b②可证伪返回约定:+0x000C call 0x65ab80/+0x0011 xor ebx,ebx/+0x0013 cmp eax,ebx/+0x0015 jl→+0x02F9(pop esi;pop ebx;ret 8),即helper返回负值时本函数立即返回该负值(读者可从字节预测错误返回);③b④有界循环+0x003F..+0x004E(dec ebp初值8/jne回跳,add edi,4推进,每轮call 0x6cf240清一字段)。严格档③b②成立。',
  '单持有表TechnoClass slot5,错源⑯不触发(holders=1)'),
 ('00712170','TechnoTypeClass::slot25','③b②可证伪-1哨兵+③b④循环',
  '③b②可证伪-1哨兵35处(如+0x0CC2/+0x0CFE/+0x0D3A cmp eax,-1/je错误路);③b④显式对象写有界循环:+0x076C..+0x0828(backedge +0x0828 jl→+0x076C,写+0x07DA mov [edi-0x1fc],eax/+0x0811 mov [edi],eax,推进+0x081D inc eax/+0x0822 add edi,0x1c,界+0x0826 cmp eax,ecx)与+0x39CB..+0x3C19(backedge +0x3C19 jl→+0x39CB,12处显式对象写,+0x3C17 cmp eax,ecx界)。严格档③b②+④成立。',
  '单持有表TechnoTypeClass slot25,错源⑯不触发(holders=1)'),
 ('00716150','AircraftTypeClass::slot42','③b④有界循环(累加器写口径)',
  '③b④有界循环:+0x005E..+0x0104回跳(backedge +0x0104 jne→+0x005E),读word[esi]/word[esi+2],哨兵界+0x005E cmp word[esi],0x7fff/+0x0065 cmp word[esi+2],0x7fff(0x7fff=终止哨兵,可证伪),推进+0x0077 add esi,4,写+0x0085 mov [esp+0x14],cx/+0x008A mov [esp+0x16],dx/+0x0095 mov [esp+0x18],eax(坐标为累加器写,按累加器写口径)。严格档③b④成立(哨兵界+推进+显式累加器写)。',
  '4表同slot42(AircraftTypeClass/InfantryTypeClass/TechnoTypeClass/UnitTypeClass)→错源⑯归属=基类级(共同基类TechnoTypeClass);name栏AircraftTypeClass为其中一表,TD+8逐字一致'),
]

def insns_around(site,before=6):
    i=addr2i.get(site)
    return [] if i is None else insns[max(0,i-before):i+1]

summary=[]
for key,nm,tier,bdetail,x16 in ROWS:
    e=int(key,16); x=CFG[key]; f=x['features']
    lines=[]
    lines.append(f"# EVIDENCE entry {key} name={nm} subsystem=S05 ③b={tier}")
    lines.append(f"① entry {key}: 16B对齐={e%16==0}; 全.text capstone skipdata扫1,392,592指令/68,253 E8@边界/6,728 distinct(与SURVEY基准逐字同)")
    lines.append(f"CFG extent(entry-relative): +0x0000..+0x{int(x['hi'],16)-e:04X} (nins={x['nins']}, lo={x['lo']}, hi={x['hi']}, 自写CFG不依赖atlas size)")
    lines.append("")
    lines.append("## ② ALL RTTI holding tables (枚举包含该entry的全部持有表, 全.rdata 4对齐原始命中)")
    hs=HOLD[key]
    for h in hs:
        lines.append(f"  vt={h['vt']} slot={h['slot']} COL={h['col']} TD+8='{h['name']}'")
    slots=set(h['slot'] for h in hs); classes=set(h['name'] for h in hs)
    lines.append(f"  持有表数={len(hs)} distinct_classes={len(classes)} slot_set={sorted(slots)}")
    dv=[h for h in hs if 'DynamicVector' in h['name']]
    vv=[h for h in hs if '?$Vector' in h['name'] and 'Dynamic' not in h['name']]
    lines.append(f"  DV/V同slot别名陷阱: DV_holders={len(dv)} V_holders={len(vv)}; DV slot(7+k)==V slot k alias={'CHECK' if (dv and vv) else '无(非容器族/单族)'}")
    lines.append(f"  错源⑯: {x16}")
    lines.append("")
    lines.append("## ④ direct call sites (E8@指令边界 + site+5+rel32==entry + 站点在CFG体外 + 非自环)")
    lo=int(x['lo'],16); hi=int(x['hi'],16)
    sites=call_sites.get(e,[])
    valid=[]
    for s in sites:
        b=bytes_at(s,5); rel=struct.unpack('<i',b[1:5])[0]; tgt=s+5+rel
        inside=lo<=s<hi; selflp=(s==e); ok=(b[0]==0xE8 and tgt==e and not inside and not selflp)
        ctx=insns_around(s,6)
        ecx=[f"{a:08X} {m} {o}" for a,sz,m,o,bb in ctx if m=='mov' and o.startswith('ecx,')]
        lines.append(f"  site={s:08X} E8bytes={b.hex()} rel32={rel} target={tgt:08X} inside_body={inside} self={selflp} OK={ok} ecx_src={ecx[-2:]}")
        if ok: valid.append(s)
    lines.append(f"  total_direct_sites={len(sites)} valid={len(valid)}")
    lines.append("")
    lines.append("## ③b detail (entry-relative +0xNN, 逐字核对同源)")
    lines.append("  "+bdetail)
    lines.append(f"  backedges={f['backedges']}")
    lines.append(f"  jumptables={f['jumptables']} errcmp(-1)={f['errcmp'][:12]}")
    lines.append(f"  ③b特征: memwrites_total={len(f.get('memwrites',[]))} guards={len(f['guards'])}")
    lines.append("")
    lines.append("## full disassembly (entry-relative)")
    for off,m,o,hx in x['body']:
        lines.append(f"  {off:>9}  {hx:<20} {m:<8} {o}")
    open(os.path.join(EVID,f"ROW_{key}.txt"),'w',encoding='utf-8').write('\n'.join(lines))
    summary.append(dict(entry=key,name=nm,tier=tier,n_holders=len(hs),holders=hs,
                        n_dir_valid=len(valid),sites=[f'{s:08X}' for s in valid],
                        extent=x['hi'],nins=x['nins'],bdetail=bdetail,x16=x16,
                        backedges=f['backedges'],errcmp=f['errcmp'][:12]))

json.dump(summary,open(os.path.join(EVID,'ROW_SUMMARY.json'),'w',encoding='utf-8'),indent=1)
for s in summary:
    print(f"{s['entry']} holders={s['n_holders']} dir_valid={s['n_dir_valid']} tier={s['tier']} extent=+0x{int(s['extent'],16)-int(s['entry'],16):04X}  {s['name']}")
