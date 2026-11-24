from __future__ import annotations
import os, sys, struct, json, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_INS_CALL, X86_OP_MEM

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_C3'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
SIZES = {
    '00539760': 303,
    '0053AB50': 18,
    '0053AF40': 289,
    '00595740': 404,
    '00599650': 4124,
}
SITES = {
    '00539760': ['00685506'],
    '0053AB50': ['006851AC'],
    '0053AF40': ['0053A742'],
    '00595740': ['0058B745'],
    '00599650': ['00598A74'],
}
pe = pefile.PE(EXE, fast_load=False)
imagebase = pe.OPTIONAL_HEADER.ImageBase
blob = open(EXE, 'rb').read()
sec = next(s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text')
text_rva = sec.VirtualAddress
text_vs = sec.Misc_VirtualSize
text_raw_size = sec.SizeOfRawData
text_off = pe.get_offset_from_rva(text_rva)
text = blob[text_off:text_off + text_vs]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def cov_names():
    names = {}
    with open(COV, 'r', encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            p = line.rstrip('\r\n').split('\t')
            if len(p) >= 3:
                names[p[0].lower()] = p[2]
    return names

def hex8(x): return f'{x:08X}'

def rva_off(rva):
    return pe.get_offset_from_rva(rva)

def read_va(va, n):
    o = rva_off(va - imagebase)
    return blob[o:o+n]

def disasm_range(va, size):
    return list(md.disasm(read_va(va, size), va))

def rel32_target(insn):
    if len(insn.bytes) < 5 or insn.bytes[0] != 0xE8:
        return None
    rel = int.from_bytes(insn.bytes[1:5], 'little', signed=True)
    return insn.address + 5 + rel

def selftest19():
    mem_ops = 0
    no_index_int0 = 0
    no_index_none = 0
    has_index_attr = 0
    for insn in md.disasm(read_va(0x401000, 0x20000), 0x401000):
        try:
            ops = insn.operands
        except Exception:
            continue
        for op in ops:
            if op.type == X86_OP_MEM:
                mem_ops += 1
                if hasattr(op, 'index'): has_index_attr += 1
                if op.mem.index == 0: no_index_int0 += 1
                if op.mem.index is None: no_index_none += 1
    return {'mem_ops_sample': mem_ops, 'no_index_int0': no_index_int0, 'no_index_none': no_index_none, 'hasattr_index': has_index_attr}

def stats():
    insn_n = 0
    e8_boundary = 0
    e8_call = 0
    for insn in md.disasm(text, imagebase + text_rva):
        insn_n += 1
        if insn.bytes and insn.bytes[0] == 0xE8:
            e8_boundary += 1
            if insn.id == X86_INS_CALL: e8_call += 1
    return {
        'sha256': hashlib.sha256(blob).hexdigest(),
        'text_rva': hex8(text_rva), 'text_virtual_size': text_vs,
        'text_raw_size': text_raw_size,
        'insn_virtualsize': insn_n, 'e8_at_boundary': e8_boundary,
        'e8_id_call': e8_call, 'raw_e8_bytes': text.count(b'\xE8'),
        'coverage_pct_virtualsize': 100.0,
    }

def dump_functions():
    names = cov_names()
    os.makedirs(os.path.join(BASE, 'EVIDENCE'), exist_ok=True)
    summaries = {}
    for ent, size in SIZES.items():
        va = int(ent, 16)
        insns = disasm_range(va, size)
        lines = []
        calls = []
        writes = []
        for insn in insns:
            off = insn.address - va
            ann = ''
            if insn.id == X86_INS_CALL:
                tgt = rel32_target(insn)
                if tgt is None:
                    ann = ' ; call_indirect'
                    calls.append({'off': f'+0x{off:X}', 'site': hex8(insn.address), 'target': '', 'name': '', 'asm': f'{insn.mnemonic} {insn.op_str}'})
                else:
                    nm = names.get(hex8(tgt).lower(), '')
                    ann = f' ; call_target={hex8(tgt)}' + (f' {nm}' if nm and nm != 'sub_' + hex8(tgt).lower() else '')
                    calls.append({'off': f'+0x{off:X}', 'site': hex8(insn.address), 'target': hex8(tgt), 'name': nm, 'asm': f'{insn.mnemonic} {insn.op_str}'})
            if insn.mnemonic in ('mov','movsx','movzx','add','sub','inc','dec','and','or','xor') and insn.op_str.startswith(('dword ptr [', 'word ptr [', 'byte ptr [')):
                writes.append((f'+0x{off:X}', f'{insn.mnemonic} {insn.op_str}'))
            lines.append(f'{hex8(insn.address)} +0x{off:04X}  {insn.bytes.hex():<16} {insn.mnemonic} {insn.op_str}{ann}')
        p = os.path.join(BASE, 'EVIDENCE', f'disasm_{ent}.txt')
        open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        summaries[ent] = {
            'size': size, 'instructions': len(insns), 'calls': calls,
            'first': lines[:8], 'last': lines[-8:],
            'mem_ops_sample': writes[:40], 'disasm_path': p,
        }
    return summaries

def verify_sites():
    out = {}
    for ent, sites in SITES.items():
        rows = []
        target = int(ent, 16)
        for s in sites:
            va = int(s, 16)
            b = read_va(va, 5)
            rel = int.from_bytes(b[1:5], 'little', signed=True)
            comp = va + 5 + rel
            insns = list(md.disasm(read_va(va, 16), va))
            at_boundary = bool(insns and insns[0].address == va and insns[0].id == X86_INS_CALL)
            rows.append({'site': hex8(va), 'bytes': b.hex(), 'rel32': rel, 'computed': hex8(comp), 'target': ent, 'at_boundary': at_boundary, 'self_loop': comp == va})
        out[ent] = rows
    return out

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if cmd in ('stats','all'):
        print('STATS ' + json.dumps(stats(), ensure_ascii=False))
    if cmd in ('selftest','all'):
        print('SELFTEST19 ' + json.dumps(selftest19(), ensure_ascii=False))
    if cmd in ('sites','all'):
        print('SITES ' + json.dumps(verify_sites(), ensure_ascii=False))
    if cmd in ('functions','all'):
        s = dump_functions()
        for ent, d in s.items():
            print('\nFUNCTION ' + ent + ' size=' + str(d['size']) + ' instr=' + str(d['instructions']))
            for ln in d['first']: print('  ' + ln)
            print('  ...')
            for ln in d['last']: print('  ' + ln)
            print('  CALLS:')
            for c in d['calls']: print('    ' + json.dumps(c, ensure_ascii=False))
