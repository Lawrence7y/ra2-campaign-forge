"""Per-row full fact extraction -> facts.json entry. usage: python facts.py 006BF810"""
import sys, json, struct, bisect, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt

img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
CALLS = [(a, t) for a, t in IDX['calls']]
IATC = [(a, t) for a, t in IDX['iat']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
STARTS = IDX['starts']
IAT_CRC, IAT_CCI, OP_NEW = 0x7E15D8, 0x7E15FC, 0x7C8E17

def fstart(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return STARTS[i] if i >= 0 else None
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def num(s):
    s = s.strip()
    if re.fullmatch(r'-?0x[0-9a-f]+', s): return int(s, 16)
    if re.fullmatch(r'-?\d+', s): return int(s, 10)
    return None
def scan_dword(val, lo, hi):
    out = []
    b = img.read(lo, hi - lo)
    if not b: return out
    for i in range(0, len(b) - 3, 4):
        if struct.unpack_from('<I', b, i)[0] == val:
            out.append(lo + i)
    return out
def body(entry, limit=0x500):
    seen, work, visited = {}, [entry], set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 3000:
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

def rtti(vt):
    col = img.u32(vt - 4)
    if not col: return None
    td = img.u32(col + 0xC)
    return dict(col=col, sig=img.u32(col), offset=img.u32(col + 4), td=td,
                name=img.cstr(td + 8) if td else None)

def find_vt(entry):
    """data dword == entry, walk back to a table whose COL (vt-4) resolves to a
    type descriptor: return (vt, slot_index)."""
    out = []
    for name, base, vsz, praw, rsz in img.sections:
        if name == '.text': continue
        for va in scan_dword(entry, base, base + max(vsz, rsz)):
            for k in range(1, 9):
                vt = va - 4 * k
                col = img.u32(vt - 4)
                if not col: continue
                sig = img.u32(col)
                td = img.u32(col + 0xC)
                if sig in (0, 1) and td and img.cstr(td + 8, 8) and img.cstr(td + 8, 4).startswith('.?A'):
                    out.append((vt, k, va, img.cstr(td + 8)))
                    break
    return out

entry = int(sys.argv[1], 16)
R = dict(entry='%08X' % entry)

# ②
R['vt'] = []
for vt, k, va, name in find_vt(entry):
    r = rtti(vt)
    slots = [img.u32(vt + 4 * i) for i in range(6)]
    R['vt'].append(dict(vt='%08X' % vt, slot=k, slot_va='%08X' % va,
                        col='%08X' % r['col'], td='%08X' % r['td'], name=name,
                        slots=['%08X' % (s or 0) for s in slots]))

# ③b
bd = body(entry)
R['body'] = [fmt(i) for i in bd]
R['codes'] = [('%08X' % i.address, i.op_str) for i in bd
              if i.mnemonic == 'mov' and i.op_str.startswith('eax, 0x8')]
R['rets'] = [('%08X' % i.address, i.bytes.hex(' ')) for i in bd if i.mnemonic.startswith('ret')]
R['qi'] = [('%08X' % i.address, i.bytes.hex(' '), i.op_str) for i in bd
           if i.mnemonic == 'call' and i.op_str == 'dword ptr [eax]']
# test/jge after QI
R['qi_after'] = []
if R['qi']:
    qa = int(R['qi'][0][0], 16)
    for i in bd:
        if qa <= i.address <= qa + 0x18:
            R['qi_after'].append('%08X %s %s' % (i.address, i.bytes.hex(' '), fmt(i)[24:]))
R['direct_calls'] = [('%08X' % i.address, i.op_str) for i in bd
                     if i.mnemonic == 'call' and i.op_str.startswith('0x')]
for i in bd:
    if i.mnemonic == 'call' and i.op_str == 'dword ptr [edx + 0x20]':
        R['release'] = ('%08X' % i.address, i.bytes.hex(' '))
# delete-flag push before release
R['release_ctx'] = []
if 'release' in R:
    ra = int(R['release'][0], 16)
    for i in bd:
        if ra - 12 <= i.address <= ra:
            R['release_ctx'].append('%08X %s %s' % (i.address, i.bytes.hex(' '), fmt(i)[24:]))

# QI callee: follow the object ctor -> its vt -> slot0
R['obj_ctor'] = None
for i in bd:
    if i.mnemonic == 'call' and i.op_str.startswith('0x') and num(i.op_str) != OP_NEW:
        R['obj_ctor'] = '%08X' % num(i.op_str)
        break
def vts_of_ctor(ctor):
    outs = []
    b = body(ctor, limit=0x1200)
    for i in b:
        if i.mnemonic == 'mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            v = num(i.op_str.split(', ')[1])
            if v and 0x7E1000 <= v < 0x812000:
                r = rtti(v)
                if r and r['name'] and r['name'].startswith('.?A'):
                    outs.append((i.address, v, r['name']))
    return outs
R['obj_vts'] = []
if R['obj_ctor']:
    for a, v, nm in vts_of_ctor(int(R['obj_ctor'], 16)):
        slot0 = img.u32(v)
        R['obj_vts'].append(dict(at='%08X' % a, vt='%08X' % v, name=nm,
                                 slot0='%08X' % (slot0 or 0)))
        if slot0 and img.is_text(slot0):
            qi_body = body(slot0, limit=0x600)
            R['qi_callee'] = dict(addr='%08X' % slot0,
                                  codes=['%08X %s' % (x.address, x.op_str) for x in qi_body
                                         if x.mnemonic == 'mov' and ', 0x8' in x.op_str],
                                  zero=['%08X %s' % (x.address, x.op_str) for x in qi_body
                                        if x.mnemonic in ('xor', 'mov') and x.op_str.replace(' ', '') in ('eax,eax', 'eax,0x0')],
                                  rets=['%08X %s' % (x.address, x.bytes.hex(' ')) for x in qi_body
                                        if x.mnemonic.startswith('ret')],
                                  size=len(qi_body))
            break

print(json.dumps(R, indent=1, ensure_ascii=False))
