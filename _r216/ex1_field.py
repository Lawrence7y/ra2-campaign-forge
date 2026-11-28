#!/usr/bin/env python3
# R216-EX1: AbstractClass +0x10/+0x20 writers & consumers, one-shot forensics.
import sys, os, re, json, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_REG_ECX, X86_REG_ESP, X86_REG_EBP
X86_REG_NONE = 0

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUTD = os.path.join(ROOT, '_r216')
RAW = P.RAW
TB = P.B['.text']
LO, HI = TB['lo'], TB['rawptr'] + TB['rawsize']
IB = LO - TB['rawptr']                      # image base
o2v = lambda o: o + IB
v2o = P.r2o
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False
MDD = Cs(CS_ARCH_X86, CS_MODE_32)
MDD.detail = True
REGS = 'eax|ecx|edx|ebx|esp|ebp|esi|edi'
CACHE = {}

def mem_re(width, disp):
    return re.compile(r'\b' + width + r'\s+ptr\s+\[\s*(' + REGS + r')\s*\+\s*0x' + format(disp, 'x') + r'\s*\]', re.I)

def find_func_start(va, window=256):
    """Boundary rule: nearest >=2-byte 0xCC int3 padding run before va; start = first byte after run.
       If no CC run within 256 bytes, use va itself as start. Fallback candidate: byte after 0xC3."""
    off = v2o(va)
    lo = max(v2o(LO), off - window)
    cc, c3 = [], []
    for i in range(lo + 1, off):
        if RAW[i - 1] == 0xCC and RAW[i] == 0xCC:
            j = i
            while j < off and RAW[j] == 0xCC:
                j += 1
            cc.append(o2v(j))
        if RAW[i - 1] == 0xC3 and RAW[i] != 0xCC:
            c3.append(o2v(i))
    if cc:
        return max(cc), 'nearest >=2x0xCC int3 padding run (start=first byte after run)'
    if c3:
        return max(c3), 'fallback: byte after nearest 0xC3 within 256B'
    return va, 'no CC/C3 boundary within 256B; start=given address'

def decode_func(va, maxbytes=200):
    """Primary decode: linear from the given address, stop at first ret/jmp (<=200B).
       Prefix boundary is computed separately (task 2) via find_func_start()."""
    insns, stop_reason = [], 'maxbytes(200)'
    n = 0
    for i in MDD.disasm(RAW[v2o(va):v2o(va) + maxbytes], va):
        n += i.size
        rec = {'va': hex(i.address), 'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'op_str': i.op_str}
        insns.append(rec)
        if i.mnemonic.startswith('ret'):
            stop_reason = 'ret'
            break
        if i.mnemonic in ('jmp', 'ljmp') and i.address > va:
            stop_reason = 'jmp'
            break
    prefix_start, rule = find_func_start(va)
    # parameter & access analysis on exactly the decoded body
    ret_imm, esp_reads, field, other = None, [], [], []
    for i in MDD.disasm(RAW[v2o(va):v2o(va) + n], va):
        if i.mnemonic == 'ret':
            try:
                ret_imm = int(i.op_str, 16)
            except Exception:
                ret_imm = 0
        for op in i.operands:
            if op.type == X86_OP_MEM:
                b, d = op.mem.base, op.mem.disp
                if b == X86_REG_ECX and d in (0x10, 0x20):
                    field.append({'va': hex(i.address), 'insn': i.mnemonic + ' ' + i.op_str,
                                  'disp': hex(d), 'width_bytes': op.size, 'operand_index': i.operands.index(op),
                                  'mnemonic': i.mnemonic})
                elif b == X86_REG_NONE:
                    other.append({'va': hex(i.address), 'kind': 'absolute', 'insn': i.mnemonic + ' ' + i.op_str})
                elif b in (X86_REG_ESP, X86_REG_EBP):
                    if b == X86_REG_ESP and d > 0:
                        esp_reads.append({'va': hex(i.address), 'disp': d, 'insn': i.mnemonic + ' ' + i.op_str})
                else:
                    other.append({'va': hex(i.address), 'kind': 'field/other reg base', 'insn': i.mnemonic + ' ' + i.op_str})
    writes = [f for f in field if f['operand_index'] == 0 and f['mnemonic'] in
              ('mov', 'movzx', 'xor', 'and', 'or', 'add', 'sub', 'inc', 'dec')]
    return {'va': hex(va), 'prefix_start': hex(prefix_start), 'prefix_rule': rule, 'decode_origin': hex(va),
            'decode_rule': 'linear from given address, stop at first ret/jmp, <=200B', 'stop_reason': stop_reason,
            'bytes_decoded': n, 'instructions': insns, 'ret_imm': ret_imm,
            'arg_count_from_ret_imm': None if ret_imm is None else ret_imm // 4,
            'esp_positive_reads': esp_reads, 'ecx_10_20_field_ops': field,
            'ecx_10_20_writes': writes, 'other_accesses': other}

def cc_boundaries():
    """One pass: addresses of first byte after every >=2-byte 0xCC run in .text."""
    out = []
    i = v2o(LO)
    while i < HI - 1:
        if RAW[i] == 0xCC and RAW[i + 1] == 0xCC:
            j = i
            while j < HI and RAW[j] == 0xCC:
                j += 1
            out.append(o2v(j))
            i = j
        else:
            i += 1
    return out

CCB = cc_boundaries()
import bisect

def approx_start(site_va):
    k = bisect.bisect_right(CCB, site_va) - 1
    return CCB[k] if k >= 0 else None

def scan_calls(target):
    hits = []
    o = v2o(LO)
    end = HI - 4
    while o < end:
        if RAW[o] == 0xE8:
            rel = int.from_bytes(RAW[o + 1:o + 5], 'little', signed=True)
            site = o2v(o)
            if site + 5 + rel == target:
                hits.append({'site': hex(site), 'approx_func_start': None if approx_start(site) is None else hex(approx_start(site))})
        o += 1
    return hits

def field_scan(width, disp, mnos):
    """Segmented disasm_lite: reset at each 0xCC padding boundary (anti-drift), dedup by (addr,mnemonic)."""
    rx = mem_re(width, disp)
    starts = [LO] + CCB + [HI]
    found = {}
    for idx in range(len(starts) - 1):
        s, e = starts[idx], starts[idx + 1]
        for addr, size, mn, ops in MD.disasm_lite(RAW[v2o(s):v2o(e)], s):
            m = mn.lower()
            if m not in mnos:
                continue
            mo = rx.search(ops)
            if not mo:
                continue
            is_mem_first = bool(re.match(r'^\s*' + width + r'\s+ptr', ops, re.I))
            cls = None
            if m in ('movzx', 'test', 'cmp'):
                cls = 'read'
            elif m == 'mov':
                cls = 'write' if is_mem_first else 'read'
            elif m in ('xor', 'and', 'or'):
                cls = 'rmw'
            if cls:
                found[(addr, m)] = {'va': hex(addr), 'mnemonic': m, 'op_str': ops, 'class': cls, 'reg': mo.group(1)}
    vals = sorted(found.values(), key=lambda x: int(x['va'], 16))
    return vals

def top10(vals):
    return vals[:10]

# ---------- 1/2: function bodies ----------
F1 = decode_func(0x4a1d50)
F2 = decode_func(0x4a1ca0)

# ---------- 3: call sites ----------
calls = {hex(t): {'count': len(scan_calls(t)), 'sites': scan_calls(t)} for t in (0x4a1d50, 0x4a1ca0)}

# ---------- 4: field scans ----------
b20 = field_scan('byte', 0x20, {'mov', 'movzx', 'test', 'cmp', 'xor', 'and', 'or'})
d10 = field_scan('dword', 0x10, {'mov', 'xor', 'and', 'or', 'test', 'cmp'})
b20_read = [x for x in b20 if x['class'] == 'read']
b20_write = [x for x in b20 if x['class'] == 'write']
b20_rmw = [x for x in b20 if x['class'] == 'rmw']
d10_read = [x for x in d10 if x['class'] == 'read']
d10_write = [x for x in d10 if x['class'] == 'write']
d10_rmw = [x for x in d10 if x['class'] == 'rmw']

# ---------- 5: controls ----------
neg_b24 = field_scan('byte', 0x24, {'mov', 'movzx', 'test', 'cmp', 'xor', 'and', 'or'})
neg_d14 = field_scan('dword', 0x14, {'mov', 'xor', 'and', 'or', 'test', 'cmp'})
pos1 = any(int(x['va'], 16) == 0x410456 for x in b20_read)
c1 = [x['site'] for x in calls[hex(0x4a1d50)]['sites']]
c2 = [x['site'] for x in calls[hex(0x4a1ca0)]['sites']]
pos2a = '0x41041e' in c1
pos2b = '0x410429' in c2
neg1 = (len(neg_b24) != len(b20)) and (len(neg_d14) != len(d10))
neg2 = len(scan_calls(0x4a1d51)) == 0

result = {
    'meta': {'file': 'ra2bench/gamemd.exe', 'sha256': hashlib.sha256(RAW).hexdigest(),
             'text_lo': hex(LO), 'text_hi_file': hex(HI), 'image_base': hex(IB),
             'cc_boundary_count': len(CCB), 'capstone': '5.0.7',
             'field_scan_rule': 'disasm_lite, reset at every >=2x0xCC padding boundary; dedup by (addr,mnemonic)',
             'call_rule': 'raw E8 rel32 byte scan across .text; target=site+5+rel32; approx func start=nearest preceding CC-run end'},
    'functions': [F1, F2], 'calls': calls,
    'field_counts': {'b20_all': len(b20), 'b20_read': len(b20_read), 'b20_write': len(b20_write), 'b20_rmw': len(b20_rmw),
                     'd10_all': len(d10), 'd10_read': len(d10_read), 'd10_write': len(d10_write), 'd10_rmw': len(d10_rmw)},
    'top10': {'b20_read': top10(b20_read), 'b20_write': top10(b20_write), 'd10_all': top10(d10)},
    'controls': {'pos_mov_dl_410456': pos1, 'pos_diagnostic_410456': top10([x for x in b20 if int(x['va'], 16) in (0x410450, 0x410451, 0x410452, 0x410453, 0x410454, 0x410455, 0x410456, 0x410457)]), 'pos_call_41041e_4a1d50': pos2a, 'pos_call_410429_4a1ca0': pos2b,
                 'neg_disp_0x24_vs_0x20': {'base': len(b20), 'changed': len(neg_b24), 'pass': neg1},
                 'neg_disp_0x14_vs_0x10': {'base': len(d10), 'changed': len(neg_d14), 'pass': neg1},
                 'neg_call_target_4a1d51_count': len(scan_calls(0x4a1d51)), 'neg_call_pass': neg2},
}
with open(os.path.join(OUTD, 'ex1.json'), 'w') as f:
    json.dump(result, f, indent=2)

L = []
A = L.append
A('=== R216-EX1 FIELD OFFSETS ===')
A('sha256=%s text=[%s,%s) image_base=%s cc_boundaries=%d' % (result['meta']['sha256'], hex(LO), hex(HI), hex(IB), len(CCB)))
A('scan rules: %s | %s' % (result['meta']['field_scan_rule'], result['meta']['call_rule']))
for F in (F1, F2):
    A('\n--- function %s ---' % F['va'])
    A('prefix_start=%s prefix_rule=%s | decode_origin=%s decode_rule=%s decoded=%dB stop=%s' %
      (F['prefix_start'], F['prefix_rule'], F['decode_origin'], F['decode_rule'], F['bytes_decoded'], F['stop_reason']))
    for x in F['instructions']:
        A('  %s  %-10s %s' % (x['va'], x['mnemonic'], x['op_str']))
    A('ret_imm=%s arg_count(ret_imm/4)=%s' % (F['ret_imm'], F['arg_count_from_ret_imm']))
    A('esp_positive_reads=%s' % json.dumps(F['esp_positive_reads']))
    A('ecx_10_20_field_ops=%s' % json.dumps(F['ecx_10_20_field_ops']))
    A('ecx_10_20_writes=%s' % json.dumps(F['ecx_10_20_writes']))
    A('other_accesses=%s' % json.dumps(F['other_accesses']))
A('\n=== CALL SITES ===')
for t, v in calls.items():
    A('%s count=%d' % (t, v['count']))
    for s in v['sites']:
        A('   site=%s approx_func_start=%s' % (s['site'], s['approx_func_start']))
A('\n=== FIELD COUNT ===')
A(json.dumps(result['field_counts'], sort_keys=True))
for k, v in result['top10'].items():
    A('TOP10 %s:' % k)
    for x in v:
        A('   %s %s %s' % (x['va'], x['mnemonic'], x['op_str']))
A('\n=== CONTROLS ===')
A(('PASS' if pos1 else 'FAIL') + ' pos: mov dl,byte ptr [ecx+0x20] @0x410456 in b20_read=%s' % pos1)
A(('PASS' if pos2a else 'FAIL') + ' pos: call 0x4a1d50 @0x41041e=%s' % pos2a)
A(('PASS' if pos2b else 'FAIL') + ' pos: call 0x4a1ca0 @0x410429=%s' % pos2b)
A(('PASS' if neg1 else 'FAIL') + ' neg: 0x20 count=%d vs 0x24 count=%d ; 0x10 count=%d vs 0x14 count=%d' % (len(b20), len(neg_b24), len(d10), len(neg_d14)))
A(('PASS' if neg2 else 'FAIL') + ' neg: call target 0x4a1d51 count=%d' % len(scan_calls(0x4a1d51)))
A('\nDONE')
txt = '\n'.join(L) + '\n'
open(os.path.join(OUTD, 'ex1_out.txt'), 'w').write(txt)
sys.stdout.write(txt)
