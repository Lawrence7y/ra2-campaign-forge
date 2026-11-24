"""Dump a function body and all vt-store sites (mov [reg], imm32 -> data w/ RTTI)."""
import sys, json, bisect, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
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
def body(entry, limit=0x1200):
    seen, work, visited = {}, [entry], set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 4000:
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

for arg in sys.argv[1:]:
    f = int(arg, 16)
    b = body(f)
    print("\n=== %08X (%d insns) ===" % (f, len(b)))
    for i in b:
        mark = ''
        if i.mnemonic == 'mov' and ', 0x' in i.op_str:
            v = num(i.op_str.split(', ')[1])
            if v and 0x7E1000 <= v < 0x812000:
                nm = rtti(v)
                if nm:
                    mark = '   <== VT %s %s' % ('%08X' % v, nm)
        print("  " + fmt(i) + mark)
