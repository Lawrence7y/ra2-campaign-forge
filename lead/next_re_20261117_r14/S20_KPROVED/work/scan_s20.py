#!/usr/bin/env python3
# Self-contained S20 evidence scan. No imports from other cards' work/.
import json, os, re, struct, hashlib, random
from collections import defaultdict
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_INS_CALL, X86_INS_MOV, X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX

TARGET = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED'
EV = os.path.join(OUT, 'EVIDENCE')

def u32(data, off):
    return struct.unpack_from('<I', data, off)[0]

def norm_va(x):
    return ('%08X' % (x & 0xffffffff)).upper()

pe = pefile.PE(TARGET, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
text = None
for s in pe.sections:
    if s.Name.rstrip(b'\0').decode('latin1') == '.text':
        text = (s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
        break
assert text is not None

def rva_to_off(rva):
    return pe.get_offset_from_rva(rva)

def va_to_off(va):
    return rva_to_off((va - base) & 0xffffffff)

def off_to_va(off):
    return norm_va((base + pe.get_rva_from_offset(off)) & 0xffffffff)

raw = open(TARGET, 'rb').read()

# Table inputs
cov_rows = []
with open(COV, 'r', encoding='utf-8', newline='') as f:
    hdr_raw = f.readline().rstrip('\r\n')
    for line in f:
        if not line.strip():
            continue
        c = line.rstrip('\r\n').split('\t')
        if len(c) == 8:
            cov_rows.append(c)
atlas = {}
with open(ATLAS, 'r', encoding='utf-8', newline='') as f:
    next(f)
    for line in f:
        if not line.strip():
            continue
        c = line.rstrip('\r\n').split('\t')
        if len(c) >= 9:
            atlas[c[0].upper()] = {'size': int(c[1]), 'n_instr': int(c[2]), 'n_callers': int(c[3]), 'n_callees': int(c[4])}
grade_by_va = {norm_va(int(c[0], 16)): c[4] for c in cov_rows}
name_by_va = {norm_va(int(c[0], 16)): c[2] for c in cov_rows}
sub_by_va = {norm_va(int(c[0], 16)): c[1] for c in cov_rows}
s20_va = [norm_va(int(c[0], 16)) for c in cov_rows if c[1] == 'S20' and c[0].upper() in atlas]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# ⑲ self-check: capstone op.index is 0 (not None) for operands without an index.
selfcheck = []
for label, code in [('direct_call', bytes.fromhex('E800000000')), ('mem_no_index', bytes.fromhex('8B4204'))]:
    ins = next(md.disasm(code, 0x1000))
    op = ins.operands[0]
    selfcheck.append({'label': label, 'mnemonic': ins.mnemonic, 'op_str': ins.op_str,
                      'op_type': op.type, 'index_attr': getattr(op, 'index', 'ABSENT'),
                      'mem_index': getattr(getattr(op, 'mem', None), 'index', 'ABSENT'),
                      'imm': getattr(op, 'imm', None)})
assert selfcheck[0]['op_type'] == X86_OP_IMM and int(selfcheck[0]['imm']) == 0x1005
with open(os.path.join(EV, 'capstone_index_selfcheck.json'), 'w', encoding='utf-8') as f:
    json.dump(selfcheck, f, ensure_ascii=False, indent=2)

# Decode all atlas function bodies once; instruction boundaries are per declared function body.
direct_calls = defaultdict(list)  # target VA -> sites
body_calls = {}                   # caller VA -> list of direct callees
exact_raw = []                    # exact-dispatch-shaped sites
vptr_writes = defaultdict(list)   # global VA -> [(site, vt VA)]
vt_imm_refs = defaultdict(list)   # vt VA -> [(site, kind, detail)]
insn_count = 0
func_count = 0
for entry, meta in atlas.items():
    eva = norm_va(int(entry, 16))
    size = meta['size']
    if size <= 0:
        continue
    try:
        off = va_to_off(int(eva, 16))
        code = raw[off:off + size]
    except Exception:
        continue
    if len(code) != size:
        continue
    func_count += 1
    calls = []
    ecx_global = None
    reg_global = {}
    last = []
    for ins in md.disasm(code, int(eva, 16)):
        if ins.id == 0:
            continue
        insn_count += 1
        site = norm_va(ins.address)
        ops = ins.operands
        # Direct call target, only instruction-boundary IMM operand. Never use op.index.
        if ins.id == X86_INS_CALL and ops and ops[0].type == X86_OP_IMM:
            tgt = norm_va(ops[0].imm)
            rec = {'site': site, 'caller': eva, 'bytes': ins.bytes.hex().upper(), 'insn': f'{ins.mnemonic} {ins.op_str}'}
            direct_calls[tgt].append(rec)
            calls.append({'site': site, 'target': tgt, 'caller': eva, 'insn': rec['insn']})
        # Track mov ecx,<imm global>
        if ins.id == X86_INS_MOV and len(ops) == 2:
            d, s = ops[0], ops[1]
            if d.type == X86_OP_REG and d.reg == X86_REG_ECX and s.type == X86_OP_IMM:
                ecx_global = norm_va(s.imm)
            elif d.type == X86_OP_REG and s.type == X86_OP_MEM:
                if s.mem.base == 0 and s.mem.index == 0 and s.mem.disp:
                    reg_global[d.reg] = norm_va(s.mem.disp)
            elif d.type == X86_OP_MEM and d.reg == 0 and d.mem.base == 0 and d.mem.index == 0 and s.type == X86_OP_IMM:
                g = norm_va(d.mem.disp)
                vt = norm_va(s.imm)
                vptr_writes[g].append({'site': site, 'vt': vt, 'insn': f'{ins.mnemonic} {ins.op_str}', 'caller': eva})
            # Immediate VT references in ordinary mov/push are counted separately.
            if s.type == X86_OP_IMM:
                vt_imm_refs[norm_va(s.imm)].append({'site': site, 'kind': 'mov_imm', 'insn': f'{ins.mnemonic} {ins.op_str}', 'caller': eva})
        # exact dispatch: call [reg+disp], reg loaded from a global, ecx from same/related global.
        if ins.id == X86_INS_CALL and ops and ops[0].type == X86_OP_MEM:
            m = ops[0].mem
            if m.index == 0 and m.disp >= 0 and m.base in reg_global:
                g = reg_global[m.base]
                exact_raw.append({'site': site, 'caller': eva, 'global': g, 'slot': m.disp // 4,
                                  'disp': m.disp, 'base_reg': ins.reg_name(m.base),
                                  'ecx_global': ecx_global, 'insn': f'{ins.mnemonic} {ins.op_str}',
                                  'bytes': ins.bytes.hex().upper()})
        if len(last) >= 4:
            last.pop(0)
        last.append(site)
    body_calls[eva] = calls

# vtable slot hits: scan raw data sections for VA values equal to each S20 entry.
s20_set = set(s20_va)
slot_hits = defaultdict(list)
for s in pe.sections:
    secname = s.Name.rstrip(b'\0').decode('latin1')
    if secname == '.text' or not s.SizeOfRawData:
        continue
    start = s.PointerToRawData
    end = start + s.SizeOfRawData
    for off in range(start, end - 3, 4):
        val = u32(raw, off)
        va = norm_va(val)
        if va in s20_set:
            slot_site = off_to_va(off)
            slot_hits[va].append({'section': secname, 'site': slot_site, 'file_off': off})

def read_va_bytes(va, n):
    try:
        v = int(va, 16) if isinstance(va, str) else int(va)
        off = va_to_off(v)
        return raw[off:off + n]
    except Exception:
        return b''

def rtti_at_vt(vt_va):
    col_b = read_va_bytes((int(vt_va, 16) - 4) & 0xffffffff, 4)
    if len(col_b) != 4:
        return None
    col = u32(col_b, 0)
    td_b = read_va_bytes((col + 0xC) & 0xffffffff, 4)
    if len(td_b) != 4:
        return None
    td = u32(td_b, 0)
    name_b = read_va_bytes((td + 8) & 0xffffffff, 160)
    name = ''
    if name_b:
        z = name_b.find(b'\0')
        name_b = name_b[:z] if z >= 0 else name_b
        name = name_b.decode('ascii', errors='replace')
    return {'vt': vt_va, 'col': norm_va(col), 'td': norm_va(td), 'rtti_name': name}

# Build normalized vtable entries using the slot number embedded in coverage names.
vt_for_entry = {}
slot_pat = re.compile(r'(?:v?slot)(\d+)$', re.I)
for eva in s20_va:
    name = name_by_va.get(eva, '')
    m = slot_pat.search(name)
    if not m:
        continue
    slot = int(m.group(1))
    for hit in slot_hits.get(eva, []):
        vt = norm_va((int(hit['site'], 16) - 4 * slot) & 0xffffffff)
        rtti = rtti_at_vt(vt)
        if not rtti:
            continue
        rec = dict(hit)
        rec.update({'slot': slot, 'vt': vt, **rtti})
        vt_for_entry.setdefault(eva, []).append(rec)

# Exact dispatch resolution: exact site + global vptr write + vt slot contains entry.
vt_index = defaultdict(list)  # (vt, slot) -> [entry]
for eva, recs in vt_for_entry.items():
    for r in recs:
        vt_index[(r['vt'], r['slot'])].append(eva)

exact_by_entry = defaultdict(list)
for site in exact_raw:
    g = site['global']
    writes = vptr_writes.get(g, [])
    for w in writes:
        for eva in vt_index.get((w['vt'], site['slot']), []):
            exact_by_entry[eva].append({**site, 'vt': w['vt'], 'vptr_write_site': w['site'],
                                        'vptr_write_insn': w['insn'], 'target_entry': eva})

# Body callees already proved on disk.
proved_calls = {}
for eva in s20_va:
    proved_calls[eva] = [c for c in body_calls.get(eva, []) if grade_by_va.get(c['target']) == '[已证]' and c['target'] not in s20_set]

# Body field writes (mov [reg+disp], imm) and byte-shape contracts for container slots.
field_writes = {}
body_contract = {}
for eva in s20_va:
    entry = eva
    meta = atlas.get(entry)
    if not meta:
        continue
    try:
        off = va_to_off(int(eva, 16)); code = raw[off:off + meta['size']]
    except Exception:
        continue
    fw = []
    ops = []
    for ins in md.disasm(code, int(eva, 16)):
        if ins.id == 0:
            continue
        o = ins.operands
        if ins.id == X86_INS_MOV and len(o) == 2 and o[0].type == X86_OP_MEM:
            if o[0].mem.base != 0 and o[0].mem.index == 0 and o[1].type == X86_OP_IMM:
                fw.append({'site': norm_va(ins.address), 'base_reg': ins.reg_name(o[0].mem.base),
                           'disp': o[0].mem.disp, 'imm': o[1].imm, 'insn': f'{ins.mnemonic} {ins.op_str}'})
        ops.append(f'{ins.mnemonic} {ins.op_str}')
    field_writes[eva] = fw
    name = name_by_va.get(eva, '')
    m = slot_pat.search(name)
    slot = int(m.group(1)) if m else None
    body_hex = code.hex().upper()
    contract = None
    if slot == 6 and '8B41048B4C24048B0488C20400' in body_hex:
        contract = 'GetItem(int): mov eax,[ecx+4]; mov ecx,[esp+4]; mov eax,[eax+ecx*4]; ret 4'
    elif slot == 3 and ('E8' in body_hex and 'C20400' in body_hex):
        contract = 'FindItemIndex-like: loop/compare/ret4 (byte-shape partial)'
    elif slot == 1 and body_hex.endswith('C20400'):
        contract = 'operator==-like: compare+ret4 (byte-shape partial)'
    body_contract[eva] = {'slot': slot, 'contract': contract, 'n_insn': len(ops),
                          'body_sha256': hashlib.sha256(code).hexdigest().upper()}

# Persist detailed scan.
out = {
    'target_sha256': hashlib.sha256(raw).hexdigest().upper(),
    'text': {'rva': text[0], 'vsize': text[1], 'file_off': text[2], 'raw_size': text[3]},
    'image_base': base, 'atlas_functions_decoded': func_count, 'instructions_decoded': insn_count,
    'direct_call_sites_total': sum(len(v) for v in direct_calls.values()),
    'exact_raw_sites_total': len(exact_raw), 'vptr_write_globals': len(vptr_writes),
    'rows': {}
}
for eva in s20_va:
    out['rows'][eva] = {
        'entry': eva, 'name': name_by_va.get(eva), 'grade': grade_by_va.get(eva),
        'subsystem': sub_by_va.get(eva),
        'atlas': atlas.get(eva),
        'direct_calls_into': direct_calls.get(eva, []),
        'exact_dispatch_into': exact_by_entry.get(eva, []),
        'vtable_slots': vt_for_entry.get(eva, []),
        'vtable_hits_raw': slot_hits.get(eva, []),
        'proved_callees_in_body': proved_calls.get(eva, []),
        'body_field_writes': field_writes.get(eva, []),
        'body_contract': body_contract.get(eva, {}),
    }
with open(os.path.join(EV, 's20_scan.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

def wtsv(name, header, rows):
    with open(os.path.join(EV, name), 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(header) + '\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')

wtsv('direct_call_sites.tsv', ['entry','site','caller','bytes','insn'],
     [[eva, s['site'], s['caller'], s['bytes'], s['insn']] for eva in s20_va for s in direct_calls.get(eva, [])])
wtsv('exact_dispatch_sites.tsv', ['entry','site','caller','global','slot','ecx_global','vt','vptr_write_site','insn','vptr_write_insn'],
     [[eva, s['site'], s['caller'], s['global'], s['slot'], s['ecx_global'], s['vt'], s['vptr_write_site'], s['insn'], s['vptr_write_insn']] for eva in s20_va for s in exact_by_entry.get(eva, [])])
wtsv('vtable_rtti.tsv', ['entry','name','slot','vt','site','section','col','td','rtti_name'],
     [[eva, name_by_va.get(eva,''), r['slot'], r['vt'], r['site'], r['section'], r['col'], r['td'], r['rtti_name']] for eva in s20_va for r in vt_for_entry.get(eva, [])])
wtsv('proved_callees.tsv', ['entry','callee','site','caller','insn'],
     [[eva, c['target'], c['site'], c['caller'], c['insn']] for eva in s20_va for c in proved_calls.get(eva, [])])

wtsv('exact_raw_sites.tsv', ['site','caller','global','slot','ecx_global','base_reg','insn','bytes'],
     [[s['site'], s['caller'], s['global'], s['slot'], s['ecx_global'], s['base_reg'], s['insn'], s['bytes']] for s in exact_raw])
wtsv('vptr_writes.tsv', ['global','site','vt','caller','insn'],
     [[g, w['site'], w['vt'], w['caller'], w['insn']] for g, ws in vptr_writes.items() for w in ws])

# Console summary
static = [e for e in s20_va if grade_by_va[e] == '[静态推断]']
print('SELFCHECK', json.dumps(selfcheck, ensure_ascii=False))
print('TARGET_SHA', out['target_sha256'])
print('FUNCS', func_count, 'INSNS', insn_count, 'DIRECT_CALL_SITES_TOTAL', out['direct_call_sites_total'], 'EXACT_RAW', len(exact_raw))
print('S20', len(s20_va), 'STATIC', len(static))
print('static direct-call entries', sum(1 for e in static if direct_calls.get(e)))
print('static exact entries', sum(1 for e in static if exact_by_entry.get(e)))
print('static vtable+RTTI entries', sum(1 for e in static if vt_for_entry.get(e)))
print('static rows with proved external callee', sum(1 for e in static if proved_calls.get(e)))
print('static union direct|exact', sum(1 for e in static if direct_calls.get(e) or exact_by_entry.get(e)))
print('static direct|exact + vtable+RTTI + proved callee', sum(1 for e in static if (direct_calls.get(e) or exact_by_entry.get(e)) and vt_for_entry.get(e) and proved_calls.get(e)))
