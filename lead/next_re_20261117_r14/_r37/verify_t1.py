# -*- coding: utf-8 -*-
"""Lead 独立复算 T1 的结论：0x7E11C8 的导入名是否为 "InterlockedIncrement"。
不复用 T1 的任何代码；自己从 PE 头走一遍。
"""
import io, os, struct

IMG = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
data = open(IMG, 'rb').read()
print('image bytes =', len(data))

import hashlib
print('sha256 =', hashlib.sha256(data).hexdigest().upper())

# --- DOS/NT ---
pe_off = struct.unpack_from('<I', data, 0x3C)[0]
assert data[pe_off:pe_off + 4] == b'PE\0\0', data[pe_off:pe_off + 4]
nsec, = struct.unpack_from('<H', data, pe_off + 6)
opt_size, = struct.unpack_from('<H', data, pe_off + 20)
opt = pe_off + 24
magic, = struct.unpack_from('<H', data, opt)
image_base, = struct.unpack_from('<I', data, opt + 28)
print('PE off=0x%X magic=0x%X image_base=0x%X nsec=%d opt_size=%d' % (pe_off, magic, image_base, nsec, opt_size))
assert magic == 0x10b, 'not PE32'

# DataDirectory[1] = Import
imp_rva, imp_size = struct.unpack_from('<II', data, opt + 96 + 8)
print('Import dir: rva=0x%X size=0x%X' % (imp_rva, imp_size))

# --- 节表 ---
secs = []
st = opt + opt_size
for i in range(nsec):
    o = st + i * 40
    name = data[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o + 8)
    secs.append((name, vaddr, vsize, raddr, rsize))
    print('  sec %-8s VA=0x%08X vsize=0x%-8X raw=0x%-8X rsize=0x%X' % (name, vaddr, vsize, raddr, rsize))

def rva2off(rva):
    for name, vaddr, vsize, raddr, rsize in secs:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            d = rva - vaddr
            if d < rsize:
                return raddr + d
            return None  # 无文件字节
    return None

def off2rva(off):
    for name, vaddr, vsize, raddr, rsize in secs:
        if raddr <= off < raddr + rsize:
            return vaddr + (off - raddr)
    return None

def cstr(off, maxlen=128):
    if off is None or off >= len(data):
        return None
    end = data.find(b'\0', off, min(off + maxlen, len(data)))
    if end < 0:
        return None
    return data[off:end]

# --- 走导入描述符 ---
def walk_imports():
    """返回 {槽VA: (dll, hint, name, thunk_value)}，只按名字导入的项"""
    out = {}
    byname = {}
    p = rva2off(imp_rva)
    assert p is not None
    idx = 0
    while True:
        o = p + idx * 20
        oft, ts, fc, name_rva, ft = struct.unpack_from('<IIIII', data, o)
        if oft == 0 and name_rva == 0 and ft == 0:
            break
        dll_off = rva2off(name_rva)
        dll = cstr(dll_off).decode('ascii', 'replace') if dll_off is not None else '?'
        ilt_rva = oft if oft else ft
        k = 0
        while True:
            t_off = rva2off(ilt_rva + k * 4)
            if t_off is None:
                break
            thunk, = struct.unpack_from('<I', data, t_off)
            if thunk == 0:
                break
            slot_va = image_base + ft + k * 4
            if not (thunk & 0x80000000):
                ib_off = rva2off(thunk)
                if ib_off is not None:
                    hint, = struct.unpack_from('<H', data, ib_off)
                    nm = cstr(ib_off + 2)
                    if nm is not None:
                        byname.setdefault(bytes(nm), []).append((dll, hint, slot_va, thunk, k))
                        out[slot_va] = (dll, hint, nm.decode('ascii', 'replace'), thunk, k)
            k += 1
        idx += 1
    return out, byname

table, byname = walk_imports()
print('total named import slots =', len(table))

TARGET = 0x7E11C8
print()
print('=== 目标槽 0x%X ===' % TARGET)
if TARGET in table:
    dll, hint, name, thunk, k = table[TARGET]
    print('  dll      =', dll)
    print('  hint     =', hint)
    print('  name     = "%s"' % name)
    print('  thunk    = 0x%08X  (idx=%d)' % (thunk, k))
    print('  thunk落在 =', end=' ')
    for nm, vaddr, vsize, raddr, rsize in secs:
        if vaddr <= thunk - image_base < vaddr + max(vsize, rsize):
            print('%s' % nm)
            break
    print('  IBN 原始字节 =', data[rva2off(thunk):rva2off(thunk) + 2 + len(name) + 1].hex(' ').upper())
else:
    print('  NOT FOUND in named imports')

# --- 正控：另取几个槽，看能否解出名字 ---
print()
print('=== 正控 ===')
for va in (0x7E11CC, 0x7E1394, 0x7E1080, 0x7E1000):
    if va in table:
        dll, hint, name, thunk, k = table[va]
        print('  0x%08X -> %-20s hint=%-4d dll=%s idx=%d' % (va, name, hint, dll, k))
    else:
        print('  0x%08X -> 不在命名导入槽内' % va)

# --- 负控：一个不该在 IAT 里的 VA ---
print()
print('=== 负控 ===')
for va in (0x7E2000, 0x6C2AC0):
    print('  0x%08X -> %s' % (va, '在命名导入槽内(意外)' if va in table else '不在命名导入槽内(正确)'))

# --- 核 T1 的两条附带观察 ---
print()
print('=== 附带观察复核 ===')
# 1) 0x6C2AC0 处字节
o = rva2off(0x6C2AC0 - image_base)
if o is not None:
    print('  0x6C2AC0 处 16 字节 =', data[o:o + 16].hex(' ').upper())
# 2) 槽值是否落在 .text
rdata_slots = sum(1 for va, (dll, hint, name, thunk, k) in table.items())
def sec_of(va_abs):
    r = va_abs - image_base
    for nm, vaddr, vsize, raddr, rsize in secs:
        if vaddr <= r < vaddr + max(vsize, rsize):
            return nm
    return '?'
from collections import Counter
cnt = Counter(sec_of(thunk) for (dll, hint, name, thunk, k) in table.values())
print('  全部 %d 个命名导入槽的 thunk 值落在节分布 = %s' % (len(table), dict(cnt)))
