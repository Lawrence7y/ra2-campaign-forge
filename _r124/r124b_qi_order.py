# -*- coding: utf-8 -*-
"""R124b: RTTI base-array order vs QueryInterface comparison order (pure bytes).

For each of the 172 classes whose slot 0 is a QI implementation (r110 census),
decode its CompleteObjectLocator -> BaseClassArray (names + mdisp, straight
from the type-name strings the binary itself carries), then walk the QI body
(function-bounded: stop at the first ret after the first repe cmpsd) and
record the GUID immediates loaded into edi in the order compared.
"""
import io, json, os, struct, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pe = pefile.PE(os.path.join(ROOT, 'ra2bench', 'gamemd.exe')); IB = pe.OPTIONAL_HEADER.ImageBase
def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4); return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va): 
    b = rd(va, 4); return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n); e = b.find(b'\x00'); return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')

sym = json.load(io.open(os.path.join(ROOT,'out','reverse','symbols.json'), encoding='utf-8'))['classes']
qi  = json.load(io.open(os.path.join(ROOT,'_r110','r110a_iidmap.json'), encoding='utf-8'))['rows']
md  = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def basearray(vt):
    col = u32(vt - 4)
    chd = u32(col + 16)
    n   = u32(chd + 8); arr = u32(chd + 12)
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        td  = u32(bcd)
        out.append({'td': td, 'name': cstr(td + 8, 192),
                    'mdisp': i32(bcd + 4), 'pdisp': i32(bcd + 8),
                    'vdisp': i32(bcd + 12), 'ncont': u32(bcd + 16),
                    'flags': u32(bcd + 20)})
    return col, out

def qi_body(fn):
    """Instructions of the QI function: stop at the first ret that follows the
    first repe cmpsd (the early-out ret 0xc comes before any cmpsd)."""
    ins = list(md.disasm(rd(fn, 0x600), fn))
    out, seen_cmp = [], False
    for x in ins:
        out.append(x)
        if x.mnemonic.startswith('repe'): seen_cmp = True
        if x.mnemonic.startswith('ret') and seen_cmp: break
    return out

def iid_seq(body):
    seq = []
    for i, x in enumerate(body):
        if x.mnemonic == 'mov' and x.op_str.startswith('edi, 0x'):
            v = int(x.op_str.split(', ')[1], 16)
            w = body[max(0, i-8):i+5]
            if any(y.mnemonic == 'mov' and y.op_str == 'ecx, 4' for y in w) and \
               any(y.mnemonic.startswith('repe') for y in w):
                seq.append(v)
    return seq

rows = []
for r in qi:
    name = r['cls']; rec = sym[name]; vt = int(rec['vtable_va'], 16)
    col, bases = basearray(vt)
    body = qi_body(int(r['slot0'], 16))
    rows.append({'cls': name, 'vt': vt, 'slot0': int(r['slot0'], 16),
                 'n_body_ins': len(body),
                 'bases': bases, 'seq': iid_seq(body),
                 'seq_hex': ['0x%x' % v for v in iid_seq(body)],
                 'accept': [i['ptr'] for i in r['iids']]})
json.dump({'rows': rows}, io.open(os.path.join(ROOT,'_r124','r124b_qi_order.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)

print('classes', len(rows), 'distinct slot0', len(set(x['slot0'] for x in rows)))
print('body insn len distribution', sorted(collections.Counter(x['n_body_ins'] for x in rows).items())[:12])
c = collections.Counter(tuple(x['seq_hex']) for x in rows)
print('seq patterns:')
for k, v in c.most_common(12): print('  ', v, k)
# order statistics for the 7c70 / 7c80 pair
fwd = [x['cls'] for x in rows if 0x7f7c80 in x['seq'] and 0x7f7c70 in x['seq']
       and x['seq'].index(0x7f7c80) < x['seq'].index(0x7f7c70)]
rev = [x['cls'] for x in rows if 0x7f7c80 in x['seq'] and 0x7f7c70 in x['seq']
       and x['seq'].index(0x7f7c70) < x['seq'].index(0x7f7c80)]
print('7c80-before-7c70:', len(fwd), ' reversed:', len(rev), rev[:5])
for nm in rev[:2]:
    x = [y for y in rows if y['cls'] == nm][0]
    print(nm, 'bases', [(b['name'], b['mdisp']) for b in x['bases']])
    print('   seq', x['seq_hex'])
