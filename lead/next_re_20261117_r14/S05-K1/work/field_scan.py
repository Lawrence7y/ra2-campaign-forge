"""T3 field semantic double-support scanner.
Scans .text once (capstone skipdata=True), indexes all [reg+disp] accesses by offset,
attributes enclosing function to class via symbols.json vfuncs + ctor vtable-write sites.
Outputs per-field write census + read samples.
"""
import pefile, struct, os, json, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'ra2youli','gamemd.exe')
ATLAS=os.path.join(ROOT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
SJ=os.path.join(ROOT,'re_atlas','evidence','rtti','symbols.json')
OUTDIR=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','EVIDENCE')

pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b'\0').decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))
DATA=open(P,'rb').read()
SM={s[0]:s for s in SECS}; TEXT=SM['.text']
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True

funcs=[]
with open(ATLAS) as f:
    f.readline()
    for line in f:
        p=line.rstrip('\n').split('\t')
        try: funcs.append((int(p[0],16),int(p[1])))
        except: pass
funcs.sort(); starts=[e for e,_ in funcs]
def enclosing(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0:
        e,sz=funcs[i]
        if e<=va<e+max(sz,1): return e
    return None

sj=json.load(open(SJ,encoding='utf-8',errors='replace'))
func_class=collections.defaultdict(set)
for nm,c in sj.get('classes',{}).items():
    short=nm
    if short.startswith('?'): continue
    for vf in c.get('vfuncs',[]):
        try: func_class[int(vf,16)].add(short)
        except: pass
ctor_map={
 0x410170:{'AbstractClass'},0x4101C0:{'AbstractClass'},0x4101F0:{'AbstractClass'},0x4105A0:{'AbstractClass'},
 0x5F3900:{'ObjectClass'},0x5F3B50:{'ObjectClass'},0x5F3B80:{'ObjectClass'},
 0x6F2B40:{'TechnoClass'},0x6F4300:{'TechnoClass'},0x6F4500:{'TechnoClass'},
 0x4D31E0:{'FootClass'},0x4D3540:{'FootClass'},0x4D3590:{'FootClass'},
 0x43B680:{'BuildingClass'},0x43B740:{'BuildingClass'},0x43BCF0:{'BuildingClass'},
 0x7353C0:{'UnitClass'},0x735780:{'UnitClass'},0x744470:{'UnitClass'},
 0x517A50:{'InfantryClass'},0x517D90:{'InfantryClass'},0x521960:{'InfantryClass'},
 0x413D20:{'AircraftClass'},0x414080:{'AircraftClass'},0x41B430:{'AircraftClass'},
}
for f,cs in ctor_map.items(): func_class[f]|=cs

off_access=collections.defaultdict(list)
n_insn=0
base=DATA[TEXT[3]:TEXT[3]+TEXT[4]]
for ins in MD.disasm(base, TEXT[1]):
    n_insn+=1
    try: ops=ins.operands
    except: continue
    if not ops: continue
    write_mn={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb','neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
    for oi,op in enumerate(ops):
        if op.type!=X86_OP_MEM: continue
        disp=op.mem.disp
        has_index = op.mem.index!=0
        rec={'va':ins.address,'mn':ins.mnemonic,'op':ins.op_str,
             'bytes':ins.bytes.hex(),'oi':oi,'base':ins.reg_name(op.mem.base) if op.mem.base else None,
             'index':ins.reg_name(op.mem.index) if op.mem.index else None,
             'disp':disp,'has_index':has_index,
             'func':enclosing(ins.address)}
        rec['classes']=sorted(func_class.get(rec['func'],set())) if rec['func'] else []
        rec['is_write']=(oi==0 and ins.mnemonic in write_mn)
        off_access[disp].append(rec)

print('scanned insns',n_insn,'distinct disps',len(off_access))

TARGET_FIELDS=[
 (0x10,'AbstractClass','UniqueID (serialized by AbstractClass::Save)'),
 (0x20,'AbstractClass','Dirty bool (IsDirty returns !Dirty)'),
 (0x74,'ObjectClass','in-world / on-map flag (render filter 0x48288C)'),
 (0x80,'ObjectClass','NeedsRedraw/sprite dirty flag (consumed at draw)'),
 (0x81,'ObjectClass','Limbo flag'),
 (0x94,'ObjectClass','Layer index (-1 = no layer)'),
 (0x21C,'TechnoClass','owner HouseClass* (SetOwner 0x7014A0)'),
 (0x1AC,'TechnoClass','can-place predicate'),
]

result={'scanned_insns':n_insn,'distinct_disps':len(off_access),'fields':{}}
for disp,focus,note in TARGET_FIELDS:
    recs=off_access.get(disp,[])
    writes=[r for r in recs if r['is_write'] and not r['has_index']]
    reads=[r for r in recs if not r['is_write'] and not r['has_index']]
    focus_w=[r for r in writes if r['classes'] and any((c==focus) for c in r['classes'])]
    focus_r=[r for r in reads if r['classes'] and any((c==focus) for c in r['classes'])]
    result['fields']['0x%X'%disp]={
        'focus':focus,'note':note,
        'total_writes':len(writes),'total_reads':len(reads),
        'attributed_writes':len(focus_w),'attributed_reads':len(focus_r),
        'write_funcs':collections.Counter(r['func'] for r in writes if r['func']).most_common(12),
        'class_write_hist':collections.Counter(c for r in writes for c in r['classes']).most_common(),
        'class_read_hist':collections.Counter(c for r in reads for c in r['classes']).most_common(),
        'focus_write_samples':focus_w[:12],'focus_read_samples':focus_r[:12],
        'all_write_samples':writes[:40],'all_read_samples':reads[:40],
    }
    print('field +0x%-4X %-14s writes=%d reads=%d | focus(%s) w=%d r=%d | classes_w=%s'%(
        disp,focus,len(writes),len(reads),focus,len(focus_w),len(focus_r),
        dict(collections.Counter(c for r in writes for c in r['classes']))))
    print('    write funcs top:',[(('%08X'%f) if f else None,c) for f,c in collections.Counter(r['func'] for r in writes if r['func']).most_common(8)])

outp=os.path.join(OUTDIR,'field_access_scan.json')
with open(outp,'w',encoding='utf-8') as f:
    json.dump(result,f,indent=1,ensure_ascii=False)
print('WROTE',outp)
