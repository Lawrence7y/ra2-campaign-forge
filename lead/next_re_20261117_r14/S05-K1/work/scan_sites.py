"""Scan .text for vtable-write sites (C7 05 absolute and C7 /0 register-based),
build the batch class-name-recovery channel, and run a baseline specificity test.
Read-only on gamemd.exe.
"""
import pefile, struct, os, json, random

ROOT = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge')
PE_PATH = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
OUT_DIR = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'S05-K1', 'EVIDENCE')

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True; MD.detail = True

pe = pefile.PE(PE_PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode('ascii', 'replace')
    SECS.append({'name': nm, 'va': s.VirtualAddress + IB, 'vs': s.Misc_VirtualSize,
                 'raw': s.PointerToRawData, 'rs': s.SizeOfRawData})
DATA = open(PE_PATH, 'rb').read()
SECMAP = {s['name']: s for s in SECS}
TEXT = SECMAP['.text']; RDATA = SECMAP['.rdata']

def off(va):
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vs'], s['rs']):
            d = va - s['va']
            if d < s['rs']:
                return s['raw'] + d
    return None

def sec_of(va):
    for s in SECS:
        if s['va'] <= va < s['va'] + max(s['vs'], s['rs']):
            return s['name']
    return None

def rd(va):
    o = off(va)
    if o is None or o + 4 > len(DATA): return None
    return struct.unpack_from('<I', DATA, o)[0]

def rdstr(va, n=140):
    o = off(va)
    if o is None: return None
    return DATA[o:o+n].split(b'\0')[0].decode('ascii', 'replace')

def demangle(nm):
    if not nm: return None
    if nm.startswith('.?AV') or nm.startswith('.?AU'):
        x = nm[4:]
        return x[:-2] if x.endswith('@@') else x
    return nm

def col_to_name(col):
    if not col or sec_of(col) not in ('.rdata','.data'): return None
    td = rd(col + 0xC)
    if not td or sec_of(td) not in ('.rdata','.data'): return None
    nm = rdstr(td + 8)
    if nm and (nm.startswith('.?AV') or nm.startswith('.?AU')): return demangle(nm)
    return None

# ---- atlas function intervals ----
funcs = []  # (entry, size)
with open(ATLAS) as f:
    hdr = f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 2: continue
        try:
            e = int(p[0], 16); sz = int(p[1], 10)
            funcs.append((e, sz))
        except ValueError:
            continue
funcs.sort()
starts = [e for e,_ in funcs]
import bisect
def enclosing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0:
        e, sz = funcs[i]
        if e <= va < e + max(sz,1):
            return e, sz
    return None, None

# ---- find raw byte occurrences of a 4-byte LE value in .text ----
def find_le4(va):
    pat = struct.pack('<I', va)
    lo, hi = TEXT['raw'], TEXT['raw'] + TEXT['rs']
    idx = DATA.find(pat, lo, hi)
    hits = []
    while idx != -1:
        site_va = TEXT['va'] + (idx - TEXT['raw'])
        hits.append((site_va, idx))
        idx = DATA.find(pat, idx + 1, hi)
    return hits

# ---- decode instruction containing an immediate equal to `va` ending near hit ----
def insn_writing_imm(hit_va, imm_val, window=12):
    """Try decoding from candidate starts before hit; find insn with mem dest + imm operand == imm_val."""
    base_off = off(hit_va)
    cands = []
    for k in range(1, window):
        s_va = hit_va - k
        so = off(s_va)
        if so is None: continue
        for insn in MD.disasm(DATA[so:so+24], s_va):
            if insn.address > hit_va + 4: break
            try:
                ops = insn.operands
            except Exception:
                continue  # skipdata pseudo-instruction
            # immediate operand matching
            imm_match = any(op.type == X86_OP_IMM and op.imm == imm_val for op in ops)
            mem_dest = bool(ops) and ops[0].type == X86_OP_MEM
            if imm_match and mem_dest:
                cands.append({'va': '%08X' % insn.address, 'bytes': insn.bytes.hex(),
                              'text': insn.mnemonic + ' ' + insn.op_str,
                              'len': insn.size})
                break
    # unique
    uniq = {}
    for c in cands: uniq[c['va']] = c
    return list(uniq.values())

VTABLES = {
    'AbstractClass':0x7E1F50,'ObjectClass':0x7EF060,'TechnoClass':0x7F4960,
    'FootClass':0x7E8C94,'BuildingClass':0x7E3EBC,'UnitClass':0x7F5C70,
    'InfantryClass':0x7EB058,'AircraftClass':0x7E22A4,
}

out = {'atlas_functions': len(funcs), 'vtable_sites': {}, 'abs_init_points': [], 'baseline': {}}

# per-vtable write sites
for nm, vt in VTABLES.items():
    sites = []
    for site_va, idx in find_le4(vt):
        insns = insn_writing_imm(site_va, vt)
        for ins in insns:
            fe, fsz = enclosing(ins['va'] and int(ins['va'],16))
            sites.append({'insn_va': ins['va'], 'bytes': ins['bytes'], 'text': ins['text'],
                          'bytes_site': '%08X' % site_va,
                          'encl_func': ('%08X'%fe) if fe else None,
                          'encl_size': fsz})
    out['vtable_sites'][nm] = sites
    print('%-14s writes=%d' % (nm, len(sites)))
    for s in sites:
        print('    %s %-38s func=%s' % (s['insn_va'], s['text'][:38], s['encl_func']))

# ---- batch channel: all C7 05 <dest><val> absolute writes where val in .rdata ----
all_vt_values = {}
hit = DATA.find(b'\xC7\x05', TEXT['raw'], TEXT['raw']+TEXT['rs'])
n_c705 = 0
while hit != -1:
    va = TEXT['va'] + (hit - TEXT['raw'])
    if hit + 10 <= len(DATA):
        dest = struct.unpack_from('<I', DATA, hit+2)[0]
        val = struct.unpack_from('<I', DATA, hit+6)[0]
        if sec_of(val) == '.rdata':
            n_c705 += 1
            fe, fsz = enclosing(va)
            nm = col_to_name(rd(val - 4))  # treat val as vtable, val[-1] as COL
            all_vt_values.setdefault(val, {'write_sites': [], 'name': nm})
            all_vt_values[val]['write_sites'].append({'va': '%08X'%va, 'dest':'%08X'%dest,
                                                      'func': ('%08X'%fe) if fe else None})
    hit = DATA.find(b'\xC7\x05', hit+1, TEXT['raw']+TEXT['rs'])

out['abs_init_points'] = [{'vt':'%08X'%v, 'name': d['name'], 'sites': d['write_sites']}
                          for v,d in sorted(all_vt_values.items())]
named = sum(1 for v,d in all_vt_values.items() if d['name'])
out['baseline']['c705_total_in_rdata'] = n_c705
out['baseline']['distinct_vals'] = len(all_vt_values)
out['baseline']['named_vals'] = named
print('\n=== C7 05 absolute-init channel ===')
print('C7 05 writes with val in .rdata: %d, distinct vals: %d, resolved to RTTI name: %d' % (
    n_c705, len(all_vt_values), named))
for v,d in sorted(all_vt_values.items()):
    print('  val=%08X name=%-24s nsites=%d' % (v, d['name'] or '?', len(d['write_sites'])))

# ---- baseline test: random 4-aligned .rdata addresses (not known vtables) ----
# criterion: addr[-1] dword is COL in .rdata/.data AND COL+0xC->TD name valid
rng = random.Random(20261117)
lo = RDATA['va'] + 4; hi = RDATA['va'] + RDATA['vs'] - 8
known_vt = set(VTABLES.values()) | set(all_vt_values.keys())
# build set of real vtable VAs from symbols.json
sp = os.path.join(ROOT,'re_atlas','evidence','rtti','symbols.json')
try:
    sj = json.load(open(sp, encoding='utf-8', errors='replace'))
    for c in sj.get('classes',{}).values():
        if c.get('vtable_va'): known_vt.add(int(c['vtable_va'],16))
except Exception as e:
    print('symbols load warn', e)
pos=[]; tries=0
while len(pos)<200 and tries<20000:
    a = rng.randrange(lo, hi) & ~3
    tries+=1
    if a in known_vt: continue
    if a-4 in known_vt: continue
    pos.append(a)
fp=0
for a in pos:
    if col_to_name(rd(a-4)):
        fp+=1
out['baseline']['random_rdata_n'] = len(pos)
out['baseline']['random_rdata_named'] = fp
out['baseline']['random_rdata_fp_pct'] = 100.0*fp/len(pos) if pos else None
print('\n=== baseline: %d random 4-aligned .rdata non-vtable addrs: %d named (%.2f%%) ===' % (
    len(pos), fp, 100.0*fp/len(pos) if pos else 0))

outp = os.path.join(OUT_DIR, 'vtable_write_sites.json')
with open(outp,'w',encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print('WROTE', outp)
