"""Step 2: build class hierarchy from CHD; scan ③b features for all 83 candidates;
produce per-candidate disassembly with entry-relative offsets and a feature summary.
"""
import json, struct
from pathlib import Path
from s09lib import (u32, cstr, is_ro, sec_of, cfg_extent, decode_range, tables_holding,
                    DATA, TEXT_LO, TEXT_HI)

OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4")
WORK = OUT/'work'
EV = OUT/'EVIDENCE'

tables = json.load(open(WORK/'attrib_raw.json'))

# ---- build class parent chain from CHD ----
# COL layout: +0 sig, +4 off, +8 cdOffset, +0xC TD, +0x10 CHD
# CHD: +0 sig, +4 attr, +8 numBases, +0xC pBaseArray
# BaseArray[i] = ptr to BCD; BCD+0 = pTD ; name = cstr(TD+8)
def class_parent(td):
    """Find COL for this TD, return (class_name, direct_base_name)."""
    # scan for COL whose +0xC == td
    for t in _all_tables_meta:
        if t['td'] == td:
            col = t['col']
            chd = u32(col + 0x10)
            if not chd or not is_ro(chd):
                return None
            nb = u32(chd + 8)
            pba = u32(chd + 0xC)
            if not pba or not is_ro(pba) or nb is None or nb < 2:
                return None
            bcd1 = u32(pba + 4)   # base class array[1] = direct primary base
            if not bcd1:
                return None
            btd = u32(bcd1)
            bn = cstr(btd + 8) if btd else None
            return (cstr(td + 8), bn)
    return None

# We need COL list with td/col; recompute from VTABLES_ALL
cols = []
with (EV/'VTABLES_ALL.tsv').open(encoding='utf-8') as f:
    next(f)
    for ln in f:
        p = ln.rstrip('\n').split('\t')
        cols.append(dict(vt=int(p[0],16), col=int(p[1],16), td=int(p[2],16), name=p[3]))
_all_tables_meta = cols

parent_map = {}
for c in cols:
    if c['td'] in parent_map: continue
    col = c['col']; chd = u32(col+0x10)
    if not chd or not is_ro(chd): continue
    nb = u32(chd+8); pba = u32(chd+0xC)
    if not pba or not is_ro(pba) or nb is None or nb < 1: continue
    bcd1 = u32(pba+0)   # BaseClassArray[0] = primary direct base (MSVC CHD)
    if not bcd1: continue
    btd = u32(bcd1)
    bn = cstr(btd+8) if btd else None
    parent_map[c['td']] = (c['name'], bn)

def base_chain(name):
    """Return [name, parent, grandparent...] via td lookup by name."""
    td_by_name = {}
    for c in cols:
        td_by_name.setdefault(c['name'], c['td'])
    out=[name]; cur=name; seen={name}
    for _ in range(12):
        td=td_by_name.get(cur)
        if not td: break
        pr=parent_map.get(td)
        if not pr or not pr[1] or pr[1] in seen: break
        cur=pr[1]; out.append(cur); seen.add(cur)
    return out

def common_base(names):
    """Given list of .?AV/.?AU names, find deepest common ancestor (last in chain that all share)."""
    chains=[base_chain(n) for n in names]
    if not chains: return None
    # chains are most-derived -> base; common suffix by set intersection preserving order of first
    common=set(chains[0])
    for ch in chains[1:]: common &= set(ch)
    # pick the element that is deepest (appears latest) in the first chain among common
    best=None; besti=-1
    for i,n in enumerate(chains[0]):
        if n in common: best=n; besti=i
    return best

# ---- ③b feature scan per candidate ----
def analyze_entry(entry_hex, atlas_sz):
    entry=int(entry_hex,16)
    lo,hi,insns,byda = cfg_extent(entry)
    # bound dump/feature window by atlas size (CFG used separately for site channel)
    win_hi = min(hi, entry + atlas_sz) if atlas_sz else hi
    disp = [i for i in insns if i.address < win_hi]
    dis_lines=[]
    f=dict(n=0,calls=0,jcc=0,jmp=0,backedges=0,jump_tables=0,mem_writes=0,cmp_imm=0,
           ret=[],call_targets=[],guards=[],lo=lo,hi=hi,win_hi=win_hi)
    for ins in disp:
        off=ins.address-entry
        dis_lines.append('%08X  +0x%04X  %-8s %s' % (ins.address,off,ins.mnemonic,ins.op_str))
        f['n']+=1
        m=ins.mnemonic
        if m=='call':
            f['calls']+=1
            for op in ins.operands:
                if op.type==__import__('capstone').x86.X86_OP_IMM:
                    f['call_targets'].append('%08X'%op.imm)
        if m.startswith('j') and m!='jmp':
            f['jcc']+=1
            for op in ins.operands:
                if op.type==__import__('capstone').x86.X86_OP_IMM and op.imm<ins.address:
                    f['backedges']+=1
        if m=='jmp': f['jmp']+=1
        if m.startswith('ret'): f['ret'].append('+0x%04X'%off)
        if 'cmp' in m and any(op.type==__import__('capstone').x86.X86_OP_IMM for op in ins.operands):
            f['cmp_imm']+=1
        # jump table: jmp with mem operand having index reg
        if m in ('jmp','call'):
            for op in ins.operands:
                if op.type==__import__('capstone').x86.X86_OP_MEM and op.mem.index!=0:
                    if m=='jmp': f['jump_tables']+=1
        for op in ins.operands:
            if op.type==__import__('capstone').x86.X86_OP_MEM and op.access==__import__('capstone').CS_AC_WRITE:
                f['mem_writes']+=1
    return f,dis_lines

rem_rows = json.load(open(WORK/'s09_A_remaining.json'))
sz_by = {r['entry']: r['size'] for r in rem_rows}
res={}
for r in rem_rows:
    e=int(r['entry'],16)
    eh='%08X'%e
    f,dl=analyze_entry(eh, sz_by.get(eh,0))
    # ② attribution
    ht=[]  # from attrib_raw
    ar=json.load(open(WORK/'attrib_raw.json'))[eh]
    names=[h['name'] for h in ar['hits']]
    cb=common_base(names)
    f['entry']=eh; f['nhits']=ar['n_hits']; f['slots']=sorted(set(h['slot'] for h in ar['hits']))
    f['names']=names; f['common_base']=cb
    f['chains']={n:base_chain(n) for n in sorted(set(names))}
    res[eh]=f
    Path(EV/('DISASM_%s.txt'%eh)).write_text('\n'.join(dl),encoding='utf-8')

json.dump(res,open(WORK/'features.json','w'),ensure_ascii=False,indent=1)

# print compact summary
print('%-8s %4s %5s %3s %4s %3s %4s %4s %3s  %-30s %s'%(
    'entry','sz','nins','call','jcc','jmp','back','jtbl','wr','common_base','slots'))
for eh,f in sorted(res.items()):
    lo,hi=f['lo'],f['hi']
    print('%-8s %4d %5d %3d %4d %3d %4d %4d %3d  %-30s %s'%(
        eh,hi-lo,f['n'],f['calls'],f['jcc'],f['jmp'],f['backedges'],f['jump_tables'],
        f['mem_writes'],str(f['common_base'])[:30],f['slots']))
