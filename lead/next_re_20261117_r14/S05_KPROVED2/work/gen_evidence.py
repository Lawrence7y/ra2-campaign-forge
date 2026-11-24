"""Generate final evidence for the 8 delivered rows: RTTI holders, direct sites with
E8 byte verification, CFG extent, ③b features (strict/loose detector verdict), full disasm."""
import sys, os, json, csv, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *
from capstone import *
from capstone.x86 import *

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\EVIDENCE"
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\rtti_holders.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'rb'))
call_sites, insns, addr2i=D['call_sites'],D['insns'],D['addr2i']

ROWS=[
 ('00413F80','AircraftClass::vslot9','③b②可证伪哨兵-1回退 + ③b④有界查表循环'),
 ('006F4AB0','TechnoClass::slot101','③b①物理跳表(0x1c界,字节表+4元表)'),
 ('006F6AC0','TechnoClass::slot53','③b④链表遍历循环(读→虚调→推进→空/标志界)'),
 ('0070C270','TechnoClass::slot13','③b②可证伪哨兵-1界(+4处) + ③b④有界循环'),
 ('007077C0','TechnoClass::slot10','③b②可证伪哨兵-1界(+4处) + ③b④有界循环'),
 ('00716DC0','TechnoTypeClass::slot6','③b④有界数组读写循环(9段)'),
 ('007162F0','TechnoTypeClass::slot5','③b④有界数组读写循环(29次回跳)'),
 ('00700600','TechnoClass::slot28','③b②可证伪哨兵-1错误码(+3处) + ③b④有界循环'),
]

# strict/loose Detector verdict (照 S03_C5 baselines.py)
def insns_ext(entry):
    lo=int(CFG[entry]['lo'],16); hi=int(CFG[entry]['hi'],16)
    return [ (int(off.replace('+0x',''),16)+int(entry,16),m,o) for off,m,o,hx in CFG[entry]['body'] ]

def detector(entry):
    body=insns_ext(entry)
    jt=any(m=='jmp' and 'dword ptr' in o and '*' in o for a,m,o in body)
    err=any(m=='cmp' and o.strip().endswith('-1') for a,m,o in body)
    back=any(m.startswith('j') and m!='jmp' and o.startswith('0x') and int(o,16)<=a for a,m,o in body)
    io=any(m.startswith('call') for a,m,o in body)
    ioloop=back and io and len(body)>=20
    vtw=sum(1 for a,m,o in body if m=='mov' and 'dword ptr' in o and ('0x7e' in o or '0x7f' in o))
    memshape=vtw>=2
    # guard chain loose
    guards=[int(o,16) for a,m,o in body if m.startswith('j') and m!='jmp' and o.startswith('0x')]
    gc=len(guards)>=3 and len(set(guards))>=3
    strict=jt or err or ioloop or memshape
    loose=strict or gc
    return dict(jt=jt,err=err,back=back,ioloop=ioloop,memshape=memshape,guardchain=gc,strict=strict,loose=loose)

summary=[]
for key,nm,tier in ROWS:
    e=int(key,16); x=CFG[key]; f=x['features']
    lines=[]
    lines.append(f"# EVIDENCE entry {key}  name={nm}  ③b={tier}")
    lines.append(f"CFG extent: +0x0000 .. +0x{int(x['hi'],16)-e:04X} (nins={x['nins']}, lo={x['lo']}, hi={x['hi']})")
    lines.append("")
    lines.append("## ② RTTI holding tables (ALL raw .rdata occurrences = valid RTTI holders)")
    hs=HOLD[key]
    for h in hs:
        lines.append(f"  vt={h['vt']} slot={h['slot']} COL={h['col']} TD+8='{h['name']}'")
    # 错源16 conclusion
    slots=set(h['slot'] for h in hs); classes=set(h['name'] for h in hs)
    lines.append(f"  错源⑯: holders={len(hs)} distinct_classes={len(classes)} slot_set={sorted(slots)}")
    # DV/V trap check
    dv=[h for h in hs if 'DynamicVectorClass' in h['name']]
    vv=[h for h in hs if '?$VectorClass' in h['name'] and 'DynamicVectorClass' not in h['name']]
    lines.append(f"  DV/V trap: DV_holders={len(dv)} V_holders={len(vv)}; DV_slot(7+k)==V_slot(k) alias present={'YES-CHECK' if (dv and vv) else 'NO (single table / non-container)'} ")
    lines.append("")
    lines.append("## ④ direct call sites (E8 boundary + site+5+rel32==entry + outside CFG extent + non-self)")
    lo=int(x['lo'],16); hi=int(x['hi'],16)
    sites=call_sites.get(e,[])
    ext=[]
    for s in sites:
        b=bytes_at(s,5); rel=struct.unpack('<i',b[1:5])[0]; tgt=s+5+rel
        inside=lo<=s<hi; selflp=(s==e)
        ok=(tgt==e and not inside and not selflp and b[0]==0xE8)
        ext.append((s,b.hex(),rel,tgt,inside,selflp,ok))
        lines.append(f"  site={s:08X} E8bytes={b.hex()} rel32={rel} target={tgt:08X} inside_body={inside} self={selflp} OK={ok}")
    lines.append(f"  total direct sites={len(sites)} valid={sum(1 for z in ext if z[6])}")
    lines.append("")
    lines.append("## ③b features (entry-relative offsets, +0xNN)")
    lines.append(f"  backedges: {f['backedges']}")
    lines.append(f"  jumptables: {f['jumptables']}")
    lines.append(f"  errcmp(-1): {f['errcmp']}")
    lines.append(f"  guards: {f['guards'][:20]}")
    det=detector(key)
    lines.append(f"  detector: jumptable={det['jt']} errcode={det['err']} ioloop={det['ioloop']} memshape={det['memshape']} guardchain={det['guardchain']} => strict={det['strict']} loose={det['loose']}")
    lines.append("")
    lines.append("## full disassembly (entry-relative)")
    for off,m,o,hx in x['body']:
        lines.append(f"  {off:8} {hx:<20} {m:<8} {o}")
    open(os.path.join(EVID,f"ROW_{key}.txt"),'w',encoding='utf-8').write('\n'.join(lines))
    summary.append(dict(entry=key,name=nm,tier=tier,n_holders=len(hs),n_dv=len(dv),n_v=len(vv),
                        n_dir_valid=sum(1 for z in ext if z[6]),extent=x['hi'],nins=x['nins'],detector=det,
                        backedges=f['backedges'],jumptables=f['jumptables'],errcmp=f['errcmp']))

json.dump(summary,open(os.path.join(EVID,'ROW_SUMMARY.json'),'w',encoding='utf-8'),indent=1)
for s in summary:
    print(f"{s['entry']} holders={s['n_holders']} dir_valid={s['n_dir_valid']} strict={s['detector']['strict']} loose={s['detector']['loose']} extent={s['extent']}  {s['name']}")
