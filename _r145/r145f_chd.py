#!/usr/bin/env python3
"""R145 F：用 RTTI 类层次描述符（CHD/BCD）独立验证「同一槽连写 3 个虚表 = 基类链」。

r145e 发现 0x4A863C 循环体在同一槽 [eax-8]（对象偏移 0）连写 3 个虚表：
  0x7E192C → 0x7E4F64 → 0x7E6060，last-store-wins = 0x7E6060。
若这是 MSVC 构造函数的「基类 ctor 各自写 vptr」形态，则三张虚表的 TD 应在同一继承链上，
且 COL+0x10 指向的 ClassHierarchyDescriptor 里应列有基类 BaseClassDescriptor。

MSVC 32 位 RTTICompleteObjectLocator（本项目 COL 恰 5 dword，无 pSelf）：
  [0]=signature(0/1)  [4]=offset  [8]=cdOffset  [0xC]=pTypeDescriptor  [0x10]=pClassDescriptor
ClassHierarchyDescriptor: [0]=signature [4]=attributes [8]=numBaseClasses [0xC]=pBaseClassArray
BaseClassDescriptor: [0]=pTypeDescriptor [4]=numContainedBases [8]=PMD(mdisp,pdisp,vdisp) [0x14]=attributes
本脚本读这三层，输出三张虚表的 TD 名、CHD 里的基类链，并判定链序是否与写入顺序一致。
"""
import sys, json, struct, hashlib
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
name_of_td = {}
for td, nm in TDs.items():
    name_of_td[td] = nm.decode('latin-1', 'replace')

def td_name(td):
    return name_of_td.get(td)

def col_of(vt):
    c = B.dw(vt - 4)
    return c if c in COL else None

def chd_of(col):
    p = B.dw(col + 16)
    return p if p and B.sec_of(p) else None

def parse_chd(p):
    sig, attr, n, arr = B.dw(p), B.dw(p + 4), B.dw(p + 8), B.dw(p + 12)
    bcds = []
    if arr and B.sec_of(arr):
        for i in range(min(n or 0, 24)):
            bp = B.dw(arr + 4 * i)
            if not bp or not B.sec_of(bp): continue
            ptd = B.dw(bp)
            mdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0]
            pdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 12)))[0]
            vdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 16)))[0]
            bcds.append({'pTD': hex(ptd), 'name': td_name(ptd),
                         'numContained': B.dw(bp + 4),
                         'mdisp': mdisp, 'pdisp': pdisp, 'vdisp': vdisp})
    return {'sig': sig, 'attr': attr, 'numBase': n, 'pArray': hex(arr) if arr else None, 'bcds': bcds}

chain_vts = [0x7E192C, 0x7E4F64, 0x7E6060]
rows = []
for vt in chain_vts:
    c = col_of(vt)
    row = {'vt': hex(vt), 'col': hex(c) if c else None,
           'col_dwords': [B.dw(c + 4 * k) for k in range(5)] if c else None,
           'td': hex(B.dw(c + 12)) if c else None,
           'td_name': td_name(B.dw(c + 12)) if c else None,
           'offset': B.dw(c + 4) if c else None,
           'cdOffset': B.dw(c + 8) if c else None,
           'chd': None}
    p = chd_of(c) if c else None
    if p: row['chd'] = dict(parse_chd(p), va=hex(p))
    rows.append(row)

names = [r['td_name'] for r in rows]
# 链序判定：0x7E6060 的 CHD 里是否列出另两张，且 mdisp 全 0（vptr 在偏移 0）
last = rows[-1]['chd']
last_bcd_names = [b['name'] for b in (last['bcds'] if last else [])]
listed = [n for n in names if n in last_bcd_names]
mdisps = [b['mdisp'] for b in (last['bcds'] if last else [])]
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(),
 'rows': rows,
 'td_names': names,
 'last_chain_lists': listed,
 'last_mdisps': mdisps,
 'all_mdisp_zero': all(x == 0 for x in mdisps) if mdisps else None,
 'distinct_td': len(set(n for n in names if n)),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：三张虚表都能追到 COL 与 TD 名', all(r['col'] and r['td_name'] for r in rows), names)
chk('三张虚表的 TD 互不相同（不是同一类重复写）', res['distinct_td'] == 3, res['distinct_td'])
chk('三张的 COL.offset 全为 0（vptr 在对象偏移 0，与 B=8 反推一致）', all(r['offset'] == 0 for r in rows), [r['offset'] for r in rows])
chk('三张都有 CHD（pClassDescriptor 非空且落在节内）', all(r['chd'] for r in rows), [bool(r['chd']) for r in rows])
chk('最后装的那张（0x7E6060）的 CHD 基类表里列出了另两张的 TD', set(listed) == set(n for n in names if n), listed)
chk('CHD 基类表里 mdisp 全 0（没有虚拟基类位移）', res['all_mdisp_zero'] is True, mdisps)
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145f_chd.json', 'w'), indent=1)
for r in rows:
    print(r['vt'], r['td_name'], 'offset', r['offset'], 'cdOffset', r['cdOffset'])
    if r['chd']:
        print('   CHD sig', r['chd']['sig'], 'attr', r['chd']['attr'], 'numBase', r['chd']['numBase'])
        for bcd in r['chd']['bcds']:
            print('     base', bcd['name'], 'mdisp', bcd['mdisp'], 'pdisp', bcd['pdisp'], 'vdisp', bcd['vdisp'], 'numContained', bcd['numContained'])
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-56s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
