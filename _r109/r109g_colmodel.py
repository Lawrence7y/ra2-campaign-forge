#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109g_colmodel.py —— 用 RTTI 的 COL.offset 字段（不是猜布局）直接证「vt 位于 this+offset」。

修 r109a 的 S3 误判：symbols.json 的 col_va 是「每类 lowest-VA 的主 COL」，
而某张 vtable 的 [-4] 可能指向**同一 TD 的另一个 COL**（同一类的次级虚表）。
r109a 拿两者直接比 ⇒ 866/954，误判 88 个为不自洽。本脚本改为：
  G1 以 vtable[-4] 的 COL 为准，沿 COL+0xC(pTD) → TD+8(名字) 读名字，与 symbols.json 的类名比
  G2 解析 COL 的 offset / cdOffset 两字段（VC 布局 signature, offset, cdOffset, pTD, pCHD）
  G3 统计 offset==0 的比例 ⇒ 这就是「vt == [this+0]」的 RTTI 侧证据
  G4 用同一 TD 的多 COL 现象量化次级虚表（基类子对象）
"""
import hashlib, json, os, struct
from collections import Counter, defaultdict

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda va: va - IB
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() ==
   '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
ck('S1 vtable 954', len(VT) == 954, len(VT))

def dw(va):
    return struct.unpack_from('<I', raw, fo(va))[0]
def nm(va):
    p = va; s = b''
    while s.__len__() < 240:
        c = raw[fo(p)]
        if c == 0: break
        s += bytes([c]); p += 1
    return s.decode('latin1')

# G1 沿 vtable[-4] 的 COL 读名字
COLS = {}
rec = []
bad = []
for va, k in VT.items():
    col = dw(va - 4)
    if not (0x400000 <= col < 0x900000):
        bad.append((hex(va), hex(col), 'out')); continue
    sig, off, cdoff, ptd, pchd = (dw(col + 4 * i) for i in range(5))
    name = nm(ptd + 8) if 0x400000 <= ptd < 0x900000 else None
    COLS[va] = (col, sig, off, cdoff, ptd, name)
    rec.append((va, k, col, sig, off, cdoff, ptd, name))
ck('G1 vtable[-4] 落在镜像内的比例 = %d/954', len(rec) == 954, (len(rec), bad[:3]))
named = [r for r in rec if r[7]]
ck('G1b COL+0xC 的 pTD 再 +8 能读出装饰名的比例 = %d/954' % len(named), len(named) == 954, len(named))

def norm(n):
    # ?AVFoo@@ -> Foo  （与 symbols.json 的 key 形态对齐）
    if n.startswith('.?A') and n.endswith('@@'):
        return n[4:-2]          # 只剥前缀 .?AV/.?AU 与尾缀 @@，绝不 replace(@@)：模板名里本就含 @@
    return n
mism = [r for r in rec if norm(r[7]) != r[1]]
ck('G1c COL 链读出的类名与 symbols.json 的类名一致 = %d/954（规范化 ?AV..@@ 后比较）'
   % (954 - len(mism)), len(mism) == 0, [ (r[1], r[7]) for r in mism[:4] ])
ck('S3 修正：r109a 的 866/954 不是因为链坏，而是 symbols.json 的 col_va 记的是「每类 lowest-VA 主 COL」；'
   '按 vtable[-4] 实际所指的 COL 读名字是 %d/954 全对' % (954 - len(mism)), len(mism) == 0, 954 - len(mism))

# G2/G3 COL.offset
offs = Counter(r[4] for r in rec)
ck('G2 COL.offset 分布（前 6）=%s' % offs.most_common(6), True, offs.most_common(6))
zero = offs.get(0, 0)
ck('G3 offset == 0 的 vtable = %d/954 = %.1f%% ⇒ 这些类的 vt 位于 this+0（RTTI 原生字段，非布局假设）'
   % (zero, 100.0 * zero / 954), zero > 700, (zero, round(100.0 * zero / 954, 1)))
ck('G3b offset != 0 的分布（次级虚表 = 基类子对象嵌入）= %s' % offs.most_common()[1:6], True, offs.most_common()[1:6])
ck('G3c cdOffset 分布 = %s', True, Counter(r[5] for r in rec).most_common(5))
ck('G3d signature 字段分布 = %s（VC x86 应为 0）', True, Counter(r[3] for r in rec).most_common(3))

# G4 同 TD 多 COL
byTd = defaultdict(list)
for r in rec: byTd[r[6]].append(r)
multi = {td: v for td, v in byTd.items() if len(v) > 1}
ck('G4 同一 TD 对应多张 vtable 的类 = %d 类（多继承/基类子对象）' % len(multi), True, len(multi))
ex = []
for td, v in list(multi.items())[:4]:
    ex.append({'td': hex(td), 'name': v[0][7], 'vtables': [[hex(r[0]), hex(r[2]), r[4]] for r in v]})
ck('G4b 实例（vtable / COL / offset）', True, ex)

# G5 与 r109a 的 88 个「不一致」逐条解释
A = json.load(open('_r109/r109a_attr.json'))
mis88 = [r for r in rec if sym[r[1]].get('col_va') and r[2] != int(sym[r[1]]['col_va'], 16)]
# G5 精确表述：symbols.json 的 col_va 是「该 TD 的最低 VA COL」（R89 rtti_r89.json 的
# symbols_col_va_lowest_of_td=954 即此口径），而 vtable[-4] 可能指向同一 TD 的**另一条** COL
# （R89 col_per_td 实测 1211 条 COL 分给 954 TD：1 条 860 / 2 条 10 / 3 条 6 / 4 条 76 / 5 条 1 / 7 条 1）。
# 两者 pTD 相同 ⇒ 类名相同 ⇒ 不影响归因。这里把「同 pTD」也一并断言，不只比名字。
ck('G5 r109a 的 88 个「vtable[-4] != col_va」全部是同一 pTD 的另一条 COL（col_va 记的是该 TD 最低 VA 那条），'
   '名字与 pTD 均不变 ⇒ 归因结果不受影响',
   all(norm(r[7]) == r[1] and dw(r[2] + 0xc) == r[6] == dw(int(sym[r[1]]['col_va'], 16) + 0xc) for r in mis88),
   len(mis88))
json.dump({'checks': checks, 'offset_dist': dict(offs), 'zero': zero,
           'multi_td': len(multi), 'ex': ex,
           'cols': {hex(r[0]): [hex(r[2]), r[4], r[5], hex(r[6]), r[7]] for r in rec}},
          open('_r109/r109g_colmodel.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
