"""s2b: ③b feature detection bounded by correct function extents."""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(__file__))
from core import (Bin, build_rtti, sweep_calls, FuncMap, disasm_range,
                  holding_tables, attribute_base, cls_short, ancestors)
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE = os.path.dirname(__file__)
R14 = os.path.dirname(os.path.dirname(HERE))
b = Bin()
rtti = build_rtti(b)
sw = sweep_calls(b)
fm = FuncMap(b, rtti, sw)

rem = json.load(open(os.path.join(R14, 'S10_KPROVED3', 'work', 'a_rows_remaining.json'), encoding='utf-8'))
name_by = {r['entry']: r['name'] for r in rem}
sites_by = {r['entry']: [s for s in r['ring4_direct_sites'].split(';') if s] for r in rem}
EXCLUDE = set("""004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690
004D82B0 004D5690 004DB260 00702D40 00706640 00708C30 004D94B0 004DDDE0""".split())
CAND = [r['entry'] for r in rem if r['entry'] not in EXCLUDE]

def analyze(ea):
    st, en = fm.extent(ea)
    insns = disasm_range(b, st, en)
    res = {'size': en-st, 'n_ins': len(insns), 'jt': [], 'loops': [], 'ep': [], 'writes': []}
    idx = {}
    for i, x in enumerate(insns):
        idx[x.address] = i
    # jump tables: indirect jmp/call via [reg*scale + disp]
    for i, x in enumerate(insns):
        if x.mnemonic in ('jmp','call') and x.operands:
            op = x.operands[0]
            if op.type == X86_OP_MEM and op.mem.index and op.mem.scale in (2,4,8):
                bound = None
                for j in range(max(0,i-16), i):
                    p = insns[j]
                    if p.mnemonic == 'cmp' and len(p.operands)==2 and p.operands[1].type==X86_OP_IMM:
                        bound = (p.address-ea, p.operands[1].imm)
                res['jt'].append({'off': x.address-ea, 'ins': f'{x.mnemonic} {x.op_str}',
                                  'bound': bound})
    # backward branches (loops)
    for i, x in enumerate(insns):
        if x.mnemonic.startswith('j') and x.operands:
            op = x.operands[0]
            if op.type == X86_OP_IMM:
                tgt = op.imm
                if st <= tgt < x.address:
                    body = [y for y in insns if tgt <= y.address <= x.address]
                    w = []
                    for y in body:
                        if y.mnemonic in ('mov','inc','dec','add','sub','and','or','xor') and len(y.operands)>=1:
                            d = y.operands[0]
                            if d.type == X86_OP_MEM:
                                w.append((y.address-ea, y.mnemonic, y.op_str))
                    res['loops'].append({'head': tgt-ea, 'back': x.address-ea,
                                         'jcc': x.mnemonic, 'n': len(body), 'nw': len(w),
                                         'writes': w[:8]})
    # error paths: cmp imm 0x8000xxxx / -1 with following jcc
    for i, x in enumerate(insns):
        if x.mnemonic in ('cmp','test') and len(x.operands)>=2:
            for o in x.operands:
                if o.type == X86_OP_IMM:
                    v = o.imm & 0xffffffff
                    if v >= 0x80000000 or v == 0xffffffff:
                        nxt = insns[i+1].mnemonic if i+1 < len(insns) else None
                        res['ep'].append({'off': x.address-ea, 'ins': f'{x.mnemonic} {x.op_str}',
                                          'imm': f'{v:#x}', 'next': nxt})
    # all explicit mem writes (for loop support / memory shape)
    for x in insns:
        if x.mnemonic in ('mov','inc','dec','add','sub','and','or','xor') and x.operands:
            d = x.operands[0]
            if d.type == X86_OP_MEM:
                res['writes'].append((x.address-ea, x.mnemonic, x.op_str))
    return res

out = {}
for e in CAND:
    ea = int(e,16)
    hs = holding_tables(b, rtti, ea)
    base, note = attribute_base(hs)
    sitok = []
    for s in sites_by.get(e,[]):
        sa = int(s,16)
        sitok.append({'site': s, 'boundary': sa in sw['boundaries'],
                      'target': f"{sw['calls'].get(sa,0):08X}", 'ok': sw['calls'].get(sa)==ea})
    f = analyze(ea)
    out[e] = {'name': name_by.get(e,'?'), 'n_holds': len(hs), 'attrib': base, 'attrib_note': note,
              'holders': [{'vt':f"{h['vt']:#x}",'slot':h['slot'],'name':h['name'],
                           'col':f"{h['col']:#x}",'td':f"{h['td']:#x}"} for h in hs],
              'sites': sitok, 'feat': f}
    print(f"{e} {name_by.get(e,'?')[:26]:26s} holds={len(hs)}->{str(base):12s} "
          f"JT={len(f['jt'])} LP={len(f['loops'])} EP={len(f['ep'])} "
          f"sites={sum(s['ok'] for s in sitok)}/{len(sitok)} size={f['size']} ins={f['n_ins']}")

json.dump(out, open(os.path.join(HERE,'..','EVIDENCE','candidate_analysis_v2.json'),'w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote candidate_analysis_v2.json')
