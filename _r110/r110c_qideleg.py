#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110c_qideleg.py —— 修正 r110a 的 S7 盲区：QueryInterface 会「先委托基类、再比自己的 IID」。

r110a 的 S7 报「172 个 QI 类里有 1 个（AircraftClass）不认 IUnknown」。
实测该函数体开头是：
    0x414290 push ebx / mov ebx,[esp+8] / ...
    0x4142a2 call 0x410260        ; ← 0x410260 是 AbstractClass 的 QI，体内比对 IUnknown
    0x4142a7 test eax,eax / jge 0x4142e9
    0x4142ab mov ecx,4 ; mov edi,0x7e9b40 ; repe cmpsd   ; ← 基类失败后才比自己的 IID
即「派生类 QI = 委托基类 QI + 追加自己的 IID」。故 IUnknown 是被**经委托**认得的，
不是不认。这是我自己判据的盲区（自错 L-04），本轮把它闭环。

判据：
  D1 对每个 QI 实现函数，看函数体前 40 条指令里是否有 call <另一 QI 实现>；
     若有则记为该实现的「委托基」。
  D2 传递闭包后，统计「最终是否认得 IUnknown」——三种口径并列：
       直接：体内 mov edi,0x7f7c90
       1 跳委托：直接 ∪ {委托目标的直接集}
       全闭包：直接 ∪ 传递闭包
  D3 反控：随机 20000 个指令起点，前 40 条里出现 call <任一 QI 实现> 的比例（基线）。
  D4 自环/互环检测：委托关系必须无环（除基类 QI 自身）。
内存纪律：只解 172 个 QI 实现的头部 240 B。
"""
import array, bisect, json, os, random, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda v: v - IB

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

d110 = json.load(open('_r110/r110a_iidmap.json'))
QIrows = d110['rows']
ck('S1 读回 r110a 的 QI 类数 %d（应 172）' % len(QIrows), len(QIrows) == 172, len(QIrows))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
def head(f, cap=240):
    return list(md.disasm_lite(raw[fo(f):fo(f) + cap], f))

# 每个实现函数的直接 IID 集
impl_direct = {}   # func -> set(iid_ptr)
for r in QIrows:
    f = int(r['slot0'], 16)
    impl_direct.setdefault(f, set()).update(int(x['ptr'], 16) for x in r['iids'])
ck('S2 distinct QI 实现函数 = %d（r110a 报 90）' % len(impl_direct), len(impl_direct) == 90, len(impl_direct))

IMPLS = set(impl_direct)

# D1 委托基
deleg = {}
for f in sorted(IMPLS):
    tgt = []
    for a, sz, m, o in head(f):
        if m == 'call' and o.startswith('0x'):
            t = int(o, 16)
            if t in IMPLS and t != f:
                tgt.append(t)
    deleg[f] = tgt
n_del = sum(1 for v in deleg.values() if v)
ck('D1 有「委托基类 QI」的 QI 实现 = %d/%d；委托边总数 = %d'
   % (n_del, len(IMPLS), sum(len(v) for v in deleg.values())), True,
   {'with_deleg': n_del, 'edges': sum(len(v) for v in deleg.values()),
    'sample': [(hex(a), [hex(x) for x in b]) for a, b in deleg.items() if b][:4]})

# D4 环检测
WHITE, GREY, BLACK = 0, 1, 2
color = {f: WHITE for f in IMPLS}
cyc = []
def dfs(u, stack):
    color[u] = GREY
    for v in deleg.get(u, ()):
        if color.get(v) == GREY:
            cyc.append(stack[stack.index(v):] + [v] if v in stack else [u, v])
        elif color.get(v) == WHITE:
            dfs(v, stack + [v])
    color[u] = BLACK
for f in sorted(IMPLS):
    if color[f] == WHITE:
        dfs(f, [f])
ck('D4 委托关系中的环 = %d 个（基类链应无环；有环即判据取错，如把 tail-call 当委托）'
   % len(cyc), len(cyc) == 0, [[hex(x) for x in c] for c in cyc[:3]])

# D2 传递闭包
def closure(f, seen=None):
    seen = seen or set()
    if f in seen:
        return set()
    seen.add(f)
    s = set(impl_direct.get(f, ()))
    for v in deleg.get(f, ()):
        s |= closure(v, seen)
    return s

IUNK = 0x7f7c90
direct_yes = {f for f in IMPLS if IUNK in impl_direct[f]}
close_yes = {f for f in IMPLS if IUNK in closure(f)}
ck('D2 IUnknown 认得的口径对比：直接 %d/%d；含委托闭包 %d/%d'
   % (len(direct_yes), len(IMPLS), len(close_yes), len(IMPLS)),
   len(close_yes) >= len(direct_yes), {'direct': len(direct_yes), 'closure': len(close_yes)})

cls_by_impl = defaultdict(list)
for r in QIrows:
    cls_by_impl[int(r['slot0'], 16)].append(r['cls'])
cls_direct = set(c for f in direct_yes for c in cls_by_impl[f])
cls_close = set(c for f in close_yes for c in cls_by_impl[f])
ck('D3 按类计：直接认 IUnknown 的类 = %d/172（r110a S7 报 171）；含委托闭包 = %d/172'
   % (len(cls_direct), len(cls_close)), len(cls_close) >= 171,
   {'direct': len(cls_direct), 'closure': len(cls_close),
    'still_missing': sorted(set(r['cls'] for r in QIrows) - cls_close)})

# AircraftClass 的正控：它必须经委托认得
ac = [r for r in QIrows if r['cls'] == 'AircraftClass'][0]
acf = int(ac['slot0'], 16)
ck('D5 正控：AircraftClass 的 QI 0x%x 委托到 %s，且该目标直接比 IUnknown ⇒ 它其实认得 IUnknown'
   % (acf, [hex(x) for x in deleg[acf]]),
   any(t in direct_yes for t in deleg[acf]), {'deleg': [hex(x) for x in deleg[acf]],
                                              'target_direct_iunk': [hex(x) for x in deleg[acf] if x in direct_yes]})

# D3 反控
f2 = open('_r108/branchmap2.bin', 'rb')
D = {}
while True:
    hd = f2.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k2 = f2.read(kl).decode()
    arr = array.array('I'); arr.frombytes(f2.read(n * isz)); D[k2] = arr
f2.close()
starts = D['starts']
rnd = random.Random(110)
N = 20000
hit = 0
for a in rnd.sample(list(starts), N):
    if a + 240 > TE:
        continue
    for g in head(a):
        if g[2] == 'call' and g[3].startswith('0x') and int(g[3], 16) in IMPLS:
            hit += 1
            break
base = 100.0 * hit / N
real = 100.0 * n_del / len(IMPLS)
ck('D6 反控：随机 %d 个指令起点里「头部 240 B 内 call 到某个 QI 实现」的 = %d（%.3f%%）；'
   '真 QI 实现里含委托的 = %.1f%% ⇒ 富集 %.1f 倍'
   % (N, hit, base, real, real / max(base, 1e-9)),
   real >= 5 * max(base, 0.01), {'rand': hit, 'rand_pct': round(base, 3), 'real_pct': round(real, 1),
                                 'enrich': round(real / max(base, 1e-9), 1)})

json.dump({'checks': checks, 'impls': len(IMPLS), 'with_deleg': n_del,
           'deleg': {hex(a): [hex(x) for x in b] for a, b in sorted(deleg.items()) if b},
           'cycles': [[hex(x) for x in c] for c in cyc],
           'iunk_direct': len(cls_direct), 'iunk_closure': len(cls_close),
           'impl_direct_iunk': len(direct_yes), 'impl_closure_iunk': len(close_yes),
           'negctl': [hit, N, round(base, 3)],
           'aircraft': {'func': hex(acf), 'deleg': [hex(x) for x in deleg[acf]]}},
          open('_r110/r110c_qideleg.json', 'w'), ensure_ascii=False, indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (np_, len(checks), len(checks) - np_))
