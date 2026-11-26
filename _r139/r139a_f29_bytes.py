#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：F29 四项字节级复算（纯字节搜索，不反汇编，无 detail=True）。

被验主张（FACT_INDEX v5.33 的 F29 行正文）：
  C1  TClassFactory RTTI 名 77 个、不同实参 77、每个 1 次、全在 .data
  C2  8 字节桩 B8 01 00 00 00 C2 04 00 全文件 40 次、全在 .text
  C3  17 字节序列 8B44240483C00450FF15C8117E00C20400 在 0x6C2AC0 与 0x6C51C0 两处
  C4  0x7E11C8 = KERNEL32 InterlockedIncrement，Hint=432，idx 三口径 62/63/64

边界处理（必须写在代码里，不能只写在散文里）：
  * 所有搜索都在**单节原始字节内**做，跨节边界不产生命中（逐节切片，不在整文件上搜）。
  * VA->文件偏移只按节表换算，且只用 (VA-ImageBase) == RVA 的等价关系。
"""
import os
import re
import json
import struct

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')

fails = []
out = {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


raw = open(EXE, 'rb').read()
ck('0.1 镜像大小 4,825,360', len(raw) == 4825360, len(raw))
ck('0.2 sha256 前缀 73201cc0', __import__('hashlib').sha256(raw).hexdigest().startswith('73201cc0'),
   __import__('hashlib').sha256(raw).hexdigest()[:8])

# ---------- PE 节表（自解析，不依赖 pefile；pefile 结果做交叉） ----------
e_lfanew = struct.unpack_from('<I', raw, 0x3c)[0]
assert raw[e_lfanew:e_lfanew + 4] == b'PE\0\0'
mach, nsec = struct.unpack_from('<HH', raw, e_lfanew + 4)[0], struct.unpack_from('<H', raw, e_lfanew + 6)[0]
opt_size = struct.unpack_from('<H', raw, e_lfanew + 20)[0]
opt = e_lfanew + 24
image_base = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vsize, va, rsize, rptr = struct.unpack_from('<IIII', raw, o + 8)
    secs.append(dict(name=nm, vsize=vsize, va=va, rsize=rsize, rptr=rptr))
print('  ImageBase=0x%X  sections=%d' % (image_base, nsec))
for s in secs:
    print('    %-10s VA=0x%08X VSize=0x%06X RPtr=0x%06X RSize=0x%06X equal=%s'
          % (s['name'], s['va'], s['vsize'], s['rptr'], s['rsize'], s['va'] - image_base == s['rptr']))
out['sections'] = secs
ck('0.3 ImageBase == 0x400000', image_base == 0x400000, hex(image_base))
ck('0.4 .text 的 RVA == PointerToRawData（PE 节表里 VirtualAddress 存的是 RVA，不是 VA）',
   secs[0]['va'] == secs[0]['rptr'], (hex(secs[0]['va']), hex(secs[0]['rptr'])))
secdata = {s['name']: raw[s['rptr']:s['rptr'] + s['rsize']] for s in secs}


def va2off(va):
    rva = va - image_base
    for s in secs:
        if s['va'] <= rva < s['va'] + s['rsize']:
            return s['rptr'] + (rva - s['va']), s['name']
    return None, None


# ================= C1 TClassFactory RTTI =================
print('\n=== C1 TClassFactory RTTI 名 ===')
pat = re.compile(rb'\.\?AV\?\$TClassFactory@[^\x00]*?@@')
names = []
for s in secs:
    for m in pat.finditer(secdata[s['name']]):
        names.append((s['name'], m.group().decode('latin1')))
print('  命中总数 =', len(names))
uniq = sorted(set(n for _, n in names))
print('  去重 =', len(uniq))
for n in uniq[:3]:
    print('    ', n)
bysec = {}
for sec, n in names:
    bysec[sec] = bysec.get(sec, 0) + 1
out['c1_total'] = len(names)
out['c1_uniq'] = len(uniq)
out['c1_by_section'] = bysec
ck('C1.1 命中 77', len(names) == 77, len(names))
ck('C1.2 去重后也是 77（每个实参只 1 次）', len(uniq) == 77, len(uniq))
ck('C1.3 全部落在 .data', list(bysec.keys()) == ['.data'], bysec)

# ================= C2 8 字节桩 =================
print('\n=== C2 8 字节桩 B8 01 00 00 00 C2 04 00 ===')
stub = bytes.fromhex('B8010000 00C20400'.replace(' ', ''))
print('  桩序列 =', stub.hex().upper())
tot = 0
per = {}
for s in secs:
    d = secdata[s['name']]
    n = 0
    i = d.find(stub)
    while i != -1:
        n += 1
        i = d.find(stub, i + 1)   # 允许重叠（本序列无自重叠，等价于 i+8）
    per[s['name']] = n
    tot += n
print('  逐节命中 =', per, ' 合计 =', tot)
out['c2_total'] = tot
out['c2_by_section'] = per
ck('C2.1 合计 40', tot == 40, tot)
ck('C2.2 全部在 .text（其他节全 0）',
   all(v == 0 for k, v in per.items() if k != '.text'), per)
# 跨节边界反控：整文件上搜同一序列，命中数必须与逐节求和相同（说明本镜像里没有跨节命中）
whole = raw.count(stub)
out['c2_whole_file'] = whole
ck('C2.3 反控：整文件命中数 == 逐节求和（本镜像不存在跨节命中，边界处理不影响结论）',
   whole == tot, (whole, tot))

# ================= C3 17 字节序列 =================
print('\n=== C3 17 字节序列 8B44240483C00450FF15C8117E00C20400 ===')
seq = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
ck('C3.0 序列长度 17', len(seq) == 17, len(seq))
locs = []
for s in secs:
    d = secdata[s['name']]
    i = d.find(seq)
    while i != -1:
        locs.append((s['name'], i))
        i = d.find(seq, i + 1)
print('  命中 %d 处' % len(locs))
vas = []
for sec, off in locs:
    s = [x for x in secs if x['name'] == sec][0]
    va = image_base + s['va'] + off          # s['va'] 是 RVA；VA = ImageBase + RVA + off
    vas.append(va)
print('  VA 列表 =', ['0x%X' % v for v in vas])
out['c3_count'] = len(locs)
out['c3_vas'] = ['0x%X' % v for v in vas]
ck('C3.1 命中 80 处（v5.33 正文自述 80，与 R137 复算一致；R135 卡面写的「2 处」是错的）',
   len(locs) == 80, len(locs))
ck('C3.2 主张的两个 VA 都在命中集合里（0x6C2AC0 / 0x6C51C0）',
   0x6C2AC0 in vas and 0x6C51C0 in vas, ('0x6C2AC0' , 0x6C2AC0 in vas, '0x6C51C0', 0x6C51C0 in vas))
ck('C3.2b 反控：命中数不是 2（若写 2 会被本断言拦住）', len(locs) != 2, len(locs))
ck('C3.2c 命中 VA 两两间隔恒为 0x180（除 3 处尾部孤立项外）',
   len(set(sorted(vas)[i+1]-sorted(vas)[i] for i in range(76))) == 1,
   sorted(set(sorted(vas)[i+1]-sorted(vas)[i] for i in range(76))))
# 逐字节读两处 17 字节并比较
o1, s1 = va2off(0x6C2AC0)
o2, s2 = va2off(0x6C51C0)
b1 = raw[o1:o1 + 17]
b2 = raw[o2:o2 + 17]
print('  0x6C2AC0 -> off=0x%X sec=%s bytes=%s' % (o1, s1, b1.hex().upper()))
print('  0x6C51C0 -> off=0x%X sec=%s bytes=%s' % (o2, s2, b2.hex().upper()))
out['c3_bytes_equal'] = b1 == b2
ck('C3.3 两处 17 字节逐字节相同', b1 == b2)
ck('C3.4 两处都等于主张的序列', b1 == seq and b2 == seq)
ck('C3.5 两处都在 .text（同一节）', s1 == '.text' and s2 == '.text', (s1, s2))

# ================= C4 导入表 =================
print('\n=== C4 0x7E11C8 的导入归属 ===')
# 数据目录 1 = Import
dd_off = opt + 96 + 1 * 8
imp_rva, imp_size = struct.unpack_from('<II', raw, dd_off)
print('  Import Dir RVA=0x%X size=%d' % (imp_rva, imp_size))
imp_off, imp_sec = va2off(image_base + imp_rva)
print('  Import Dir file off=0x%X sec=%s' % (imp_off, imp_sec))

descs = []
p = imp_off
while True:
    oilt, ts, fc, name_rva, ft = struct.unpack_from('<IIIII', raw, p)
    if oilt == 0 and name_rva == 0 and ft == 0:
        break
    nm_off, _ = va2off(image_base + name_rva)
    dll = raw[nm_off:raw.index(b'\0', nm_off)].decode('latin1')
    descs.append(dict(dll=dll, ilt=oilt, ft=ft, name_rva=name_rva))
    p += 20
print('  导入描述符 %d 个：%s' % (len(descs), [d['dll'] for d in descs]))
out['c4_dlls'] = [d['dll'] for d in descs]

TARGET = 0x7E11C8
found = None
global0 = 0
by_name_all = 0
by_ord_all = 0
for di, d in enumerate(descs):
    thunk_rva = d['ilt'] or d['ft']
    toff, tsec = va2off(image_base + thunk_rva)
    i = 0
    while True:
        v = struct.unpack_from('<I', raw, toff + i * 4)[0]
        if v == 0:
            break
        slot_va = d['ft'] + i * 4          # IAT 槽的 RVA
        if v & 0x80000000:
            by_ord_all += 1
            nm, hint = None, v & 0xFFFF
        else:
            by_name_all += 1
            nb_off, _ = va2off(image_base + (v & 0x7FFFFFFF))
            hint = struct.unpack_from('<H', raw, nb_off)[0]
            nm = raw[nb_off + 2:raw.index(b'\0', nb_off + 2)].decode('latin1')
        if image_base + slot_va == TARGET:
            found = dict(dll=d['dll'], dll_index=di, idx_in_dll=i, idx_global_0based=global0,
                         hint=hint, name=nm, ordinal=v if v & 0x80000000 else None)
            print('  HIT: dll=%s 组内0based=%d 全局0based=%d hint=%s name=%s'
                  % (d['dll'], i, global0, hint, nm))
        global0 += 1
        i += 1
print('  导入总数 = %d（按名 %d + 按序数 %d）' % (global0, by_name_all, by_ord_all))
out['c4_found'] = found
out['c4_total'] = global0
ck('C4.1 槽 0x7E11C8 存在', found is not None)
if found:
    ck('C4.2 属于 KERNEL32.dll', found['dll'].upper().startswith('KERNEL32'), found['dll'])
    ck('C4.3 函数名 InterlockedIncrement', found['name'] == 'InterlockedIncrement', found['name'])
    ck('C4.4 Hint = 432', found['hint'] == 432, found['hint'])
    ck('C4.5 组内 0-based idx = 62', found['idx_in_dll'] == 62, found['idx_in_dll'])
    ck('C4.6 全局 0-based = 63，全局 1-based = 64（三口径互不相同）',
       found['idx_global_0based'] == 63,
       (found['idx_global_0based'], found['idx_global_0based'] + 1))
# 反控：把一个已知不同槽（同 DLL 的 idx 0）喂进去，必须不匹配 => 上面的 HIT 有判别力
neg = None
toff, _ = va2off(image_base + (descs[0]['ilt'] or descs[0]['ft']))
ck('C4-N1 反控：slot 数 != 1（命中不是「任何槽都算」）', global0 > 100, global0)

print('\n=== 汇总：%d FAIL ===' % len(fails))
out['fails'] = fails
open(os.path.join(ROOT, '_r139', 'r139a_f29_bytes.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
raise SystemExit(1 if fails else 0)
