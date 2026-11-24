"""facts2: correct main-vtable identification (store to [reg] with offset 0)."""
import sys, json, struct, bisect, re, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
STARTS = IDX['starts']
OP_NEW = 0x7C8E17

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def num(s):
    s = s.strip()
    if re.fullmatch(r'-?0x[0-9a-f]+', s): return int(s, 16)
    if re.fullmatch(r'-?\d+', s): return int(s, 10)
    return None
def rtti(vt):
    col = img.u32(vt - 4)
    if not col: return None
    td = img.u32(col + 0xC)
    nm = img.cstr(td + 8) if td else None
    return nm if nm and nm.startswith('.?A') else None
def body(entry, limit=0x1500):
    seen, work, visited = {}, [entry], set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 5000:
            visited.add(a)
            ins = ins_at(a)
            if not ins: break
            seen[a] = ins
            mn = ins.mnemonic
            if mn.startswith('ret') or mn == 'hlt': break
            if mn == 'jmp':
                if ins.op_str.startswith('0x'):
                    a = int(ins.op_str, 16); continue
                break
            if mn.startswith('j') and ins.op_str.startswith('0x'):
                work.append(int(ins.op_str, 16))
            a = ins.address + ins.size
            if a - entry > limit: break
    return [seen[k] for k in sorted(seen)]

def stores(b):
    """all mov [dest], imm  where dest is memory and imm points to RTTI'd vt"""
    out = []
    for i in b:
        if i.mnemonic != 'mov' or ', 0x' not in i.op_str: continue
        dst, src = i.op_str.split(', ', 1)
        if not dst.startswith('dword ptr ['): continue
        v = num(src)
        if not v or not (0x7E1000 <= v < 0x812000): continue
        nm = rtti(v)
        if not nm: continue
        m = re.fullmatch(r'dword ptr \[(\w+)([^\]]*)\]', dst)
        reg, disp = (m.group(1), m.group(2).strip()) if m else (None, None)
        out.append(dict(at='%08X' % i.address, vt='%08X' % v, name=nm,
                        reg=reg, disp=disp, off0=(disp in ('', None))))
    return out

entry = int(sys.argv[1], 16)
R = dict(entry='%08X' % entry)
bd = body(entry, 0x500)
# factory vt / rtti
FV = None
for name, base, vsz, praw, rsz in img.sections:
    if name == '.text': continue
    b = img.read(base, max(vsz, rsz))
    for i in range(0, len(b) - 3, 4):
        if struct.unpack_from('<I', b, i)[0] == entry:
            va = base + i
            for k in range(1, 9):
                vt = va - 4 * k
                nm = rtti(vt)
                if nm:
                    R['factory'] = dict(vt='%08X' % vt, slot=k, slot_va='%08X' % va,
                                        name=nm, col='%08X' % (img.u32(vt - 4) or 0),
                                        td='%08X' % (img.u32(img.u32(vt - 4) + 0xC) or 0))
                    FV = vt
                    break
            if FV: break
    if FV: break

inner = re.search(r'TClassFactory@V(\w+)@@', R['factory']['name']).group(1)
R['element'] = inner
exp = '.?AV' + inner + '@@'
R['expected_obj_rtti'] = exp

R['codes'] = [('%08X' % i.address, i.op_str) for i in bd
              if i.mnemonic == 'mov' and i.op_str.startswith('eax, 0x8')]
R['rets'] = ['%08X %s' % (i.address, i.bytes.hex(' ')) for i in bd if i.mnemonic.startswith('ret')]
for i in bd:
    if i.mnemonic == 'call' and i.op_str == 'dword ptr [eax]':
        R['qi_call'] = dict(at='%08X' % i.address, bytes=i.bytes.hex(' '))
    if i.mnemonic == 'call' and i.op_str == 'dword ptr [edx + 0x20]':
        R['rel_call'] = dict(at='%08X' % i.address, bytes=i.bytes.hex(' '))

# object ctor: the direct call guarded by 'mov ecx, eax' after operator new
ctor = None
for n, i in enumerate(bd):
    if i.mnemonic == 'call' and i.op_str.startswith('0x') and num(i.op_str) != OP_NEW:
        ctor = num(i.op_str)
        R['obj_ctor'] = '%08X' % ctor
        break
cb = body(ctor, 0x1500)
st = stores(cb)
R['ctor_vt_stores'] = st
main = [s for s in st if s['off0']]
match = [s for s in main if s['name'] == exp]
pick = (match or main or [None])[-1]
R['main_vt'] = pick
if pick:
    vt = int(pick['vt'], 16)
    slot0 = img.u32(vt)
    R['main_slot0'] = '%08X' % (slot0 or 0)
    if slot0:
        qb = body(slot0, 0x600)
        R['qi_callee'] = dict(
            addr='%08X' % slot0,
            n=len(qb),
            codes=['%08X %s' % (x.address, x.op_str) for x in qb
                   if x.mnemonic == 'mov' and ', 0x8' in x.op_str],
            zeros=['%08X %s' % (x.address, x.op_str) for x in qb
                   if x.mnemonic == 'xor' and x.op_str.replace(' ', '') == 'eax,eax'],
            rets=['%08X %s' % (x.address, x.bytes.hex(' ')) for x in qb if x.mnemonic.startswith('ret')])
print(json.dumps(R, indent=1))
