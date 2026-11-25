# -*- coding: utf-8 -*-
"""R128l：试图给 R127 台账 GY ④ 那条单一来源结论补第二条独立证据链 —— 方法失败，如实记。

R127 GY ④：010C 站点的 ppv 槽值经 setl/dec/and 合成后解引用，简单寄存器跟踪追不到，
「槽只到 +0xc」只由 r127a 的符号执行承担。

本轮尝试：绕开槽值，直接用「IID 引用点附近出现的虚调用偏移」当判据。
  预期 010C(IPersist, 1 个方法) 只能看到 +0xc；0109(IPersistStream, 4 个方法) 应看到更宽。
  反控设计：若两侧数字相同则判据无效。

实测结论：**这个方法不成立**，原因就是 R127 S-170 记的那条 —— 固定窗口必然跨函数边界。
  ±0x200 窗口下两侧最大偏移都是 456(0x1c8)，完全相同，判据没有分辨力。
  收到 +0x80 更窄，但 010C 侧给出 {16,36}、0109 侧给出 {16}，仍是噪声（窗口内的
  虚调用属于相邻函数，与该 IID 句柄无关）。

如实记为「方法失败」，不据此修改任何既有结论，也不把噪声当证据。
这与 R127 的 S-170（三次自算函数边界全失败、最后放弃自算）是同一类教训：
  不自己求函数边界，就不该按「窗口」下任何关于调用偏移的结论。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128l_slot_recheck.json')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

IID = {0x7f7c70: '010C.r', 0x818858: '010C.d', 0x7f7c80: '0109.r', 0x820270: '0109.d'}
iid_at = {k: [] for k in IID}
vcalls = []
for a, sz, m, o in md.disasm_lite(raw, TXT_LO):
    ol = o.lower()
    for k in IID:
        if '0x%x' % k in ol:
            iid_at[k].append(a)
    if m == 'call' and o.startswith('dword ptr [') and ' + 0x' in o:
        try:
            k = int(o.rsplit(' + ', 1)[1].rstrip(']'), 16)
        except ValueError:
            continue
        if k >= 0xc:
            vcalls.append((a, k))
add('L0 流式扫描的四个站点数与偏移 >=0xc 的虚调用总数（数字本身是对的，用于说明窗口里有什么）',
    sum(len(v) for v in iid_at.values()) == 92,
    {'sites': {IID[k]: len(v) for k, v in iid_at.items()}, 'vcalls_ge_0xc': len(vcalls)})

def band(va, lo, hi):
    return sorted({k for a, k in vcalls if va - lo <= a <= va + hi})

res = {}
for k, lab in IID.items():
    s = set()
    for a in iid_at[k]:
        s |= set(band(a, 0x200, 0x200))
    res[lab] = {'n_sites': len(iid_at[k]), 'offs': sorted(s), 'max': max(s) if s else None}
add('L1 失败证据一：±0x200 宽窗口下，010C 侧与 0109 侧的最大虚调用偏移完全相同（都是 0x1c8）'
    '—— 判据无分辨力，因为窗口跨进了相邻函数',
    res['010C.r']['max'] == res['0109.r']['max'] == 0x1c8, res)

near = {k: band_range for k in ()} if False else {}
for k, lab in IID.items():
    s = set()
    for a in iid_at[k]:
        s |= set(band(a, 0, 0x80))
    near[lab] = sorted(s)
add('L2 失败证据二：收到 IID 引用点之后 0x80 字节，010C 侧给出 {16,36}、0109 侧给出 {16}。'
    '若这些真属于该 IID 句柄，010C(IPersist 1 方法) 不可能出现 +0x24 —— 只能是噪声，'
    '说明窗口内的虚调用属于紧邻的其它对象',
    True, near)

add('L3 结论：本方法在两档窗口下都失败，故**不产出第二条独立证据**。'
    'R127 GY ④ 的「槽只到 +0xc 仍只由 r127a 符号执行承担」这一条保持原样，不被本轮改变',
    True, None)

add('L4 这与 R127 S-170 是同一教训：不自己求函数边界，就不能按窗口对调用偏移下结论。'
    '本轮不再尝试第三次（避免把时间花在已经两次失败的路子上），如实留缺',
    True, None)

json.dump({'checks': ck, 'res': res, 'near': near, 'VERDICT': 'METHOD_FAILED'},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128l: %d/%d PASS（本脚本的断言判的是「事实成立」，其中 L1/L2 断言的是「失败」）'
      % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:420])
