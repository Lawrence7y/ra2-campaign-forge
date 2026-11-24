"""s2: full candidate analysis — enumerate 49 A-set, holding tables, sites, ③b features."""
import sys, os, json, struct, re
sys.path.insert(0, os.path.dirname(__file__))
from core import (Bin, build_rtti, holding_tables, attribute_base, cls_short,
                  sweep_calls, disasm_window, ancestors, X86_OP_MEM, X86_OP_IMM)
from capstone.x86 import X86_OP_REG

HERE = os.path.dirname(__file__)
R14 = os.path.dirname(os.path.dirname(HERE))  # work -> S10_KPROVED4 -> next_re_20261117_r14
b = Bin()
rtti = build_rtti(b)
sw = sweep_calls(b)

# A-set from audit ground truth (49 entries)
A_ENTRIES = [
 "004D55C0","004D55F0","004D5690","004D7170","004D74E0","004D7D50","004D82B0",
 "004D85D0","004D8F40","004D94B0","004D9920","004D9960","004D9C10","004DA2B0",
 "004DB1A0","004DB250","004DB260","004DB3C0","004DB690","004DBAD0","004DBED0",
 "004DC030","004DDDE0","004DDED0","004DE620","004DF040","00517CC0","005F5E80",
 "006F3AD0","006F3D60","006F77B0","006F9DD0","006FB010","006FBC90","006FBDC0",
 "006FC030","006FDA00","00701120","00701140","00702D40","00706640","00707D20",
 "00708C30","00708E00","007099E0","0070E140","0070E1A0","0070EFD0","00710460",
]

# Exclusion set (16 unique)
EXCLUDE = set([
 # S10_KPROVED2 (8)
 "004D74E0","004D7D50","004D7170","004D85D0","004DB3C0","004D9960","004DF040","004DB690",
 # S10_KPROVED3 (8, incl rejected 004DDDE0)
 "004D82B0","004D5690","004DB260","00702D40","00706640","00708C30","004D94B0","004DDDE0",
 # SEMFIX_SLOTS2 S10 rows (7) - all subset of KPROVED3
])

CAND = [e for e in A_ENTRIES if e not in EXCLUDE]
print('A count', len(A_ENTRIES), 'exclude', len(EXCLUDE), 'candidates', len(CAND))

# Load a_rows_remaining for names/sites
rem = json.load(open(os.path.join(R14, 'S10_KPROVED3', 'work', 'a_rows_remaining.json'), encoding='utf-8'))
name_by = {r['entry']: r['name'] for r in rem}
sites_by = {r['entry']: [s for s in r['ring4_direct_sites'].split(';') if s] for r in rem}
rtti_cls_by = {r['entry']: r['rtti_classes'] for r in rem}

def mem_str(op):
    if op.type != X86_OP_MEM:
        return None
    parts = []
    if op.mem.base:
        parts.append(op.reg_name(op.mem.base))
    if op.mem.index:
        parts.append('+' + op.reg_name(op.mem.index))
        if op.mem.scale != 1:
            parts.append('*' + str(op.mem.scale))
    d = op.mem.disp
    if d:
        parts.append(f'{d:+#x}')
    return '[' + ''.join(parts) + ']'


def analyze_3b(entry):
    insns = disasm_window(b, entry, max_bytes=16384)
    res = {'n_ins': len(insns), 'jump_tables': [], 'loops': [], 'error_paths': [],
           'mem_shape': None, 'guards': [], 'raw': []}
    # index instructions
    for i, ins in enumerate(insns):
        res['raw'].append((ins.address, ins.mnemonic, ins.op_str))
    # --- jump tables: jmp with mem operand having index reg ---
    for i, ins in enumerate(insns):
        if ins.mnemonic in ('jmp',) and ins.operands:
            op = ins.operands[0]
            if op.type == X86_OP_MEM and op.mem.index and op.mem.scale in (2,4,8):
                # find bounds check in previous 12 insns
                bound = None
                for j in range(max(0,i-14), i):
                    p = insns[j]
                    if p.mnemonic == 'cmp' and len(p.operands)==2 and p.operands[1].type==X86_OP_IMM:
                        bound = (p.address, p.operands[1].imm, p.mnemonic)
                res['jump_tables'].append({
                    'addr': ins.address, 'off': ins.address-entry,
                    'ins': f'{ins.mnemonic} {ins.op_str}', 'index_reg': ins.reg_name(op.mem.index),
                    'scale': op.mem.scale, 'base': ins.reg_name(op.mem.base) if op.mem.base else None,
                    'disp': op.mem.disp, 'bound': bound})
    # --- backward branches (loops) ---
    for i, ins in enumerate(insns):
        if ins.mnemonic.startswith('j') and ins.operands:
            op = ins.operands[0]
            if op.type == X86_OP_IMM:
                tgt = op.imm
                if tgt < ins.address and tgt >= entry:
                    # loop body = insns with address in [tgt, ins.address]
                    body = [x for x in insns if tgt <= x.address <= ins.address]
                    writes = []
                    for x in body:
                        if x.mnemonic in ('mov','dec','inc','add','sub','and','or','xor','stos','movsb','movsd'):
                            for o in x.operands:
                                if o.type == X86_OP_MEM and x.mnemonic in ('mov','dec','inc','add','sub','and','or','xor'):
                                    # heuristic: dest is first operand for these
                                    if o is x.operands[0]:
                                        writes.append((x.address, x.mnemonic, x.op_str))
                    res['loops'].append({
                        'head': tgt, 'head_off': tgt-entry, 'backedge': ins.address,
                        'backedge_off': ins.address-entry, 'jcc': ins.mnemonic,
                        'n_ins': len(body), 'writes': writes[:12], 'n_writes': len(writes)})
    # --- error-code paths: cmp with 0x8000xxxx / -1 ---
    for i, ins in enumerate(insns):
        if ins.mnemonic in ('cmp','test') and len(ins.operands)>=2:
            for o in ins.operands:
                if o.type == X86_OP_IMM:
                    v = o.imm & 0xffffffff
                    if v >= 0x80000000 or v in (0xffffffff,):
                        nxt = insns[i+1].mnemonic if i+1 < len(insns) else None
                        res['error_paths'].append({'addr': ins.address, 'off': ins.address-entry,
                            'ins': f'{ins.mnemonic} {ins.op_str}', 'imm': f'{v:#x}', 'next': nxt})
    # --- memory shape: count mov [reg+disp],imm writes in first 200 insns ---
    ctor_writes = 0
    vt_writes = 0
    for ins in insns[:260]:
        if ins.mnemonic == 'mov' and len(ins.operands)==2:
            dst, src = ins.operands
            if dst.type == X86_OP_MEM and src.type == X86_OP_IMM:
                ctor_writes += 1
    if ctor_writes >= 10:
        res['mem_shape'] = {'n_field_writes': ctor_writes}
    return res

out = []
for e in A_ENTRIES:
    ea = int(e, 16)
    hs = holding_tables(b, rtti, ea)
    base, note = attribute_base(hs)
    sites = sites_by.get(e, [])
    sres = []
    for s in sites:
        sa = int(s,16)
        sres.append({'site': s, 'boundary': sa in sw['boundaries'],
                     'target': f"{sw['calls'].get(sa,0):08X}", 'ok': sw['calls'].get(sa)==ea})
    feat = analyze_3b(ea)
    out.append({'entry': e, 'name': name_by.get(e,'?'), 'excluded': e in EXCLUDE,
        'n_holds': len(hs), 'attrib': base, 'attrib_note': note,
        'holders': [{'vt':f"{h['vt']:#x}",'slot':h['slot'],'col':f"{h['col']:#x}",
                     'td':f"{h['td']:#x}",'name':h['name']} for h in hs],
        'sites': sres, 'feat': {k:v for k,v in feat.items() if k!='raw'}})

json.dump(out, open(os.path.join(HERE,'..','EVIDENCE','candidate_analysis.json'),'w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote candidate_analysis.json')
# Summary per candidate
for r in out:
    if r['excluded']:
        continue
    f = r['feat']
    jt = len(f['jump_tables']); lp=len(f['loops']); ep=len(f['error_paths']); ms=bool(f['mem_shape'])
    sitok = all(s['ok'] for s in r['sites']) and len(r['sites'])>0
    print(f"{r['entry']} {r['name'][:28]:28s} holds={r['n_holds']}->{r['attrib'] or '?':12s} "
          f"JT={jt} LP={lp} EP={ep} MS={int(ms)} sites={len(r['sites'])}/{sum(s['ok'] for s in r['sites'])} ins={f['n_ins']}")
