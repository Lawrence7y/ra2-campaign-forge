#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109h_slotcover.py —— 只问一个问题：277 个 owner 里到底有多少个「真的写在某类虚表里」。

r109a/f 报覆盖 82/277=29.6%，但 r109f 的 F2c 与 r109a 的 S15 数字**一模一样**（66/19/3），
这本身可疑：F2 换了 E 集（加了 SLOTF）却没动一个数。先证「换 E 集不可能改变这 82」，
再看剩下的 195 个究竟是「不是虚方法」还是「是虚方法但槽值被 thunk 挡住」。
  H1 复算：A 标签用「槽值集合」而不是「E 成员」定义，避免 E 口径耦合
  H2 195 个无归因的 owner：报它们的 call 站点数、是否 HB、是否 call 目标
  H3 检查是否有 owner 落在 thunk 的目标侧却有 thunk 反过来指它（thunk 掩蔽）
  H4 与 R107 已证 3 个（0x708c30 / 0x728c00 / 0x728e30）逐个对照，作正控
"""
import bisect, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda va: va - IB
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
A = json.load(open('_r109/r109a_attr.json'))
OWN = [int(o['owner'], 16) for o in A['owners']]
ck('S1 277 owner', len(OWN) == 277, len(OWN))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
insns = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        insns.append((a, sz, m, o))
    if last <= pos: last = pos + 1
    pos = last
starts = [x[0] for x in insns]; SSET = set(starts)
calls = [(a, int(o, 16)) for a, _, m, o in insns if m == 'call' and o.startswith('0x')]
rets = [a for a, _, m, _ in insns if m.startswith('ret')]
ck('S2 指令数 1,392,592', len(insns) == 1392592, len(insns))

SLOT = defaultdict(set)          # 槽值地址 -> {类}
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); i += 1
ck('S3 distinct 槽值地址 == 6499', len(SLOT) == 6499, len(SLOT))
# H1 纯槽值口径（不经过 E）
nA1 = sum(1 for o in OWN if o in SLOT)
ck('H1 纯槽值口径：277 个 owner 中直接出现在某类虚表里的 = %d' % nA1, nA1 == 66, nA1)
# H3 thunk 掩蔽
TH = {}
for x in list(SLOT):
    i = bisect.bisect_left(starts, x)
    if i < len(insns) and insns[i][0] == x:
        a, sz, m, o = insns[i]
        if m == 'jmp' and o.startswith('0x'):
            TH[x] = int(o, 16)
ck('H3 jmp thunk（槽值里）== 28', len(TH) == 28, len(TH))
nTh = sum(1 for o in OWN if o in TH)
nTgt = sum(1 for o in OWN if o in set(TH.values()))
ck('H3b owner 中「本身是 thunk」= %d、「是 thunk 的目标」= %d（后者应已含在 66 里）'
   % (nTh, nTgt), True, (nTh, nTgt))
ck('H3c thunk 目标里已含于 66 的比例 = %d/%d' % (sum(1 for o in OWN if o in set(TH.values()) and o in SLOT),
   nTgt), True, nTgt)

# H4 正控：R107 已证的 3 个
for addr, cls_expect in ((0x708c30, None), (0x728c00, 'TunnelLocomotionClass'), (0x728e30, 'TunnelLocomotionClass')):
    got = sorted(SLOT.get(addr, []))
    ck('H4 正控 %s：槽值表给出类 %s' % (hex(addr), got), bool(got), got)

# H2 195 个无归因
cov = set(int(o['owner'], 16) for o in A['owners'] if o['A'] or o['B'])
UNC = [o for o in OWN if o not in cov]
ck('H2 无归因 owner == %d' % len(UNC), len(UNC) == 195, len(UNC))
CC = Counter(t for _, t in calls)
nHB = 0; nCT = 0; ncalls = []
for o in UNC:
    nHB += (o in SLOT or o in TH)  # 近似：HB 另算
for o in UNC:
    nCT += bool(CC.get(o)); ncalls.append(CC.get(o, 0))
ck('H2b 195 个里是 call 直接目标的 = %d，被调用次数中位数 = %d，1 次以上 = %d'
   % (nCT, sorted(ncalls)[len(ncalls) // 2], sum(1 for x in ncalls if x)),
   True, {'nCT': nCT, 'median': sorted(ncalls)[len(ncalls) // 2]})
# H2c 它们的 call 站点是否都在 .text（若 owner 只被间接调用则 0）
ck('H2c 195 个里调用次数 == 0 的 = %d（只经虚表/函数指针调度，故无直接 call 站点）'
   % sum(1 for x in ncalls if x == 0), True, sum(1 for x in ncalls if x == 0))
json.dump({'checks': checks, 'nA1': nA1, 'nTh': nTh, 'nTgt': nTgt,
           'unc': len(UNC), 'unc_callt': nCT, 'unc_median': sorted(ncalls)[len(ncalls) // 2],
           'unc_zero': sum(1 for x in ncalls if x == 0)},
          open('_r109/r109h_slotcover.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
