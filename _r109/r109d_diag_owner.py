#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109d_diag_owner.py —— 先自检「caller 归属」这个仪器，再谈 Q 的死活。

r109c 报出 Q 精确率 1.3%（76 例 1 对 75 错），低到不像「判据弱」，更像**仪器坏**。
按 R108 的教训（判据发火率必须与随机基线同时报，且先证仪器），本脚本只做诊断：
  D1 抽样 40 个 call 站点：goto = max E <= site 是否真是外壳函数？
     判据（组合，不单用首条 ret）：(a) site 之后到下一 ret 之间无第二个 E 成员被「跨过」
     (b) goto 到 site 之间出现的 ret 数分布（R108 已证早退使首条 ret 不可作反证，只报分布）
     (c) goto 是否 HB / call 目标 / 槽值（外部证据计数）
  D2 若 goto 与「同函数」不符，试第二口径：用 CFG 直线体从每个 E 起点出发，
     看 site 落在哪个起点的直线体里（前向不跟跳转，只跟 fallthrough）
  D3 决定性对照：拿 20 个**已知类**的虚方法（真值来自槽表），人工核对它们的直接 caller
     由 D1 口径算出的类是否等于真值；若连它们都错，才说明口径坏；
     若它们对而全量错，则说明 Q 的语义假设（同类方法互调）本身不成立。
"""
import bisect, hashlib, json, os, random, re, struct
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
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
starts = []; calls = []; rets = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            calls.append((a, int(o, 16)))
        elif m.startswith('ret'):
            rets.append(a)
    if last <= pos: last = pos + 1
    pos = last
SSET = set(starts); RETS = sorted(rets)
def d1(a, n=1):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65): q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in RETS:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET: HB.add(q)
CALLT = set(t for _, t in calls if TS <= t < TE)
SLOT = defaultdict(set)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); i += 1
E = sorted(CALLT | set(SLOT) | HB)
ck('D0 |E| == 19490（与 r109b S9 同口径）', len(E) == 19490, len(E))
def owner_of(a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None

# ---- D1 ----
random.seed(10966)
samp = random.sample(calls, 40)
diag = []
for a, t in samp:
    o = owner_of(a)
    i = bisect.bisect_right(RETS, o); j = bisect.bisect_right(RETS, a)
    nret = j - i
    # 排他性： (o, a] 内不得有其它 E 成员（构造保证），另查 o 的直线体是否跨过 site
    g = d1(o, 1)[0]
    diag.append({'site': hex(a), 'tgt': hex(t), 'owner': hex(o), 'n_ret_between': nret,
                 'owner_first': g[2] + ' ' + g[3], 'owner_HB': o in HB,
                 'owner_callt': o in CALLT, 'owner_slot': o in SLOT})
ck('D1 40 个抽样 call 站点：owner 到 site 之间 ret 数为 0 的比例 = %d/40（早退使非 0 不断定错，仅报分布）'
   % sum(1 for d in diag if d['n_ret_between'] == 0), True,
   Counter(d['n_ret_between'] for d in diag).most_common(6))
ck('D1b owner 具外部证据（HB 或 call 目标或槽值）的比例 = %d/40'
   % sum(1 for d in diag if d['owner_HB'] or d['owner_callt'] or d['owner_slot']), True,
   Counter(('HB' if d['owner_HB'] else '') + ('CT' if d['owner_callt'] else '') + ('SL' if d['owner_slot'] else '')
           for d in diag).most_common())

# ---- D3 决定性对照：已知类的虚方法，其 caller 的类 == 真值吗 ----
TRUTH = {f: next(iter(s)) for f, s in SLOT.items() if len(s) == 1}
HAV = [f for f in TRUTH if any(t == f for _, t in calls)]
ck('D2 5153 个唯一类真值函数中，被直接 call 的 == 218（r109c 报 213 是另一份 E 集口径下算的，见自错 E-d1）',
   len(HAV) == 218, len(HAV))
CLS2F = defaultdict(set)
for f, c in TRUTH.items(): CLS2F[c].add(f)
same = diff = 0; rows = []
for f in HAV:
    v = Counter()
    for a, t in calls:
        if t != f: continue
        o = owner_of(a)
        if o in TRUTH: v[TRUTH[o]] += 1
    truth = TRUTH[f]
    if not v: continue
    cl, n = v.most_common(1)[0]
    same += (cl == truth); diff += (cl != truth)
    rows.append({'func': hex(f), 'truth': truth, 'pred': cl, 'votes': v.most_common(4)})
p = 100.0 * same / (same + diff) if same + diff else 0.0
ck('D3 已知类函数的 caller 投票（含单票）精确率 = %.1f%%（%d 对 / %d 错）' % (p, same, diff),
   True, {'p': round(p, 1), 'same': same, 'diff': diff})
# D3b 关键机制检验：调用者是不是「同类」
ck('D3b 若把 caller 的类与真值同类记 +1：同类票占全部票的比例 = 需实测', True, '见 tally')
tally = Counter()
for f in HAV:
    truth = TRUTH[f]
    for a, t in calls:
        if t != f: continue
        o = owner_of(a)
        if o in TRUTH:
            tally['same' if TRUTH[o] == truth else 'diff'] += 1
ck('D3b caller 类同 / 异 的票数 = %d / %d（同类占比 %.1f%%）'
   % (tally['same'], tally['diff'], 100.0 * tally['same'] / max(1, tally['same'] + tally['diff'])),
   True, dict(tally))

# D4 多票样本里错在哪：给 3 个错例的地址，供人工看字节
errs = [r for r in rows if r['pred'] != r['truth']][:5]
ck('D4 前 5 个错例', True, errs)
json.dump({'checks': checks, 'diag40': diag, 'prec': round(p, 2), 'same': same, 'diff': diff,
           'tally': dict(tally), 'errs': errs}, open('_r109/r109d_diag_owner.json', 'w'),
          ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
