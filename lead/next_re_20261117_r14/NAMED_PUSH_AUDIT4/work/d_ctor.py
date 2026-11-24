import sys, json, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def body(entry, limit=0x1500):
    seen, work, visited = {}, [entry], set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 5000:
            visited.add(a)
            i = ins_at(a)
            if not i: break
            seen[a] = i
            mn = i.mnemonic
            if mn.startswith('ret') or mn == 'hlt': break
            if mn == 'jmp':
                if i.op_str.startswith('0x'):
                    a = int(i.op_str, 16); continue
                break
            if mn.startswith('j') and i.op_str.startswith('0x'):
                work.append(int(i.op_str, 16))
            a = i.address + i.size
            if a - entry > limit: break
    return [seen[k] for k in sorted(seen)]

def rtti(vt):
    col = img.u32(vt - 4)
    if not col: return None
    td = img.u32(col + 0xC)
    return img.cstr(td + 8) if td else None

for arg in sys.argv[1:]:
    f = int(arg, 16)
    b = body(f)
    print("\n=== ctor %08X (%d) ===" % (f, len(b)))
    for i in b[:14]:
        print("   " + fmt(i))
    for i in b:
        if i.mnemonic == 'mov' and ', 0x' in i.op_str and i.op_str.startswith('dword ptr ['):
            v = int(i.op_str.split(', ')[1], 16)
            if 0x7E1000 <= v < 0x812000:
                nm = rtti(v)
                if nm:
                    print("   VT-STORE " + fmt(i) + "   -> %s" % nm)
    print("   ... tail:")
    for i in b[-8:]:
        print("   " + fmt(i))
