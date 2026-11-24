# -*- coding: utf-8 -*-
# 独立复核：从磁盘镜像原始字节重算跳表 0x6E9F74 的 65 条目及槽位算术
import hashlib, struct, os

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d = open(EXE, 'rb').read()
print('EXE SHA256', hashlib.sha256(d).hexdigest())
print('EXE BYTES', len(d))

# --- PE 头 / 节表 ---
pe = struct.unpack_from('<I', d, 0x3c)[0]
assert d[pe:pe+4] == b'PE\0\0'
nsec = struct.unpack_from('<H', d, pe + 6)[0]
optsz = struct.unpack_from('<H', d, pe + 20)[0]
imagebase = struct.unpack_from('<I', d, pe + 24 + 28)[0]
secs = []
off = pe + 24 + optsz
for i in range(nsec):
    name = d[off:off+8].rstrip(b'\0').decode('ascii', 'replace')
    vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', d, off + 8)
    secs.append((name, vaddr, vsize, rawptr, rawsize))
    off += 40
print('IMAGEBASE', hex(imagebase))
for s in secs:
    print('SEC', s[0], 'VA', hex(s[1]), 'VS', hex(s[2]), 'RAW', hex(s[3]), hex(s[4]))

def va2off(va):
    rva = va - imagebase
    for name, vaddr, vsize, rawptr, rawsize in secs:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

def u32(va):
    o = va2off(va)
    if o is None or o + 4 > len(d):
        return None
    return struct.unpack_from('<I', d, o)[0]

# --- 跳表 0x6E9F74 全 65 条目（.text 内绝对 VA） ---
TBL = 0x6E9F74
table = [u32(TBL + 4 * i) for i in range(65)]
print('\nTABLE@0x6E9F74 count=', len(table))
for target in (0x6E9783, 0x6E961E, 0x6E9DC7, 0x6E9DAE, 0x6E9050):
    idxs = [i for i, v in enumerate(table) if v == target]
    print('  target', hex(target), '-> indices', idxs)
print('  entry[0]=', hex(table[0]), ' entry[16]=', hex(table[16]),
      ' entry[55]=', hex(table[55]), ' entry[56]=', hex(table[56]),
      ' entry[57]=', hex(table[57]))
print('  dword@(TBL+56*4)=0x%X = %s' % (TBL + 56 * 4, hex(table[56])))
print('  dword@(TBL+57*4)=0x%X = %s' % (TBL + 57 * 4, hex(table[57])))

# --- vtable 槽位算术独立重算 ---
print('\n--- vtable dword 与槽位 ---')
bases = {'Aircraft': 0x7E22A4, 'Foot': 0x7E8C94, 'Infantry': 0x7EB058, 'Unit': 0x7F5C70}
checks = [
    (0x7E24CC, 0x414A80, 'Aircraft', 138),
    (0x7E24D0, 0x4166C0, 'Aircraft', 139),
    (0x7E8EF0, 0x4D4280, 'Foot', 151),
    (0x7EB2B4, 0x4D4280, 'Infantry', 151),
    (0x7E8EA4, 0x4D4DC0, 'Foot', 132),
    (0x7F5E80, 0x7447A0, 'Unit', 132),
    (0x7E24FC, 0x4DDF90, 'Aircraft', 150),
    (0x7E8EEC, 0x4DDF90, 'Foot', 150),
    (0x7EB2B0, 0x4DDF90, 'Infantry', 150),
    (0x7F5EC8, 0x4DDF90, 'Unit', 150),
    (0x7EB480, 0x51F330, 'Infantry', 266),
]
for pos, expect_val, cls, expect_slot in checks:
    val = u32(pos)
    slot = (pos - bases[cls]) // 4
    ok = (val == expect_val and slot == expect_slot)
    print(('OK ' if ok else 'BAD'), hex(pos), 'value=', hex(val) if val is not None else 'None',
          'expect=', hex(expect_val), 'slot=', slot, 'expect_slot=', expect_slot, cls)

# --- 0x4166C0 / 0x50D170 序言头字节（条件尾跳 / 5 直调者锚点） ---
print('\n--- 关键序言字节 ---')
for va in (0x4166C0, 0x4166D0, 0x50D170, 0x6ED090, 0x6F0130, 0x7447A0):
    o = va2off(va)
    print(hex(va), 'off', hex(o) if o is not None else None, 'bytes', d[o:o+12].hex(' '))

print('\nDONE')
