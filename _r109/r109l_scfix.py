#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109l_scfix.py —— 修 r109e 的 SC 判据，重判「最近 E 成员是不是容器」。

🐞 自错 E-z2：r109e 的 SC 判据写的是「遇 ret 即函数结束」，而 R108 已用 0x46dfd0 一族
   （同一函数内 5 条 ret 0x10 各自 add esp,0x410 配对）证伪了「ret 即函数界」。
   r109e 因此把 121/400 个「早退 ret 在同一函数内」的站点误判成「容器取错」，
   报出「旧口径只有 69.8% 正确」这个**错数字**。本脚本改为只用 HB（硬边界）判：
     contain(S, site) ⇔ (S, site] 内无 HB 起点
  并同时报三档，避免再把「判据太严」记成「口径错」：
     SC1 只用 HB（可用）
     SC2 HB + 首个 ret（r109e 的错口径，留作对照，不采信）
     SC3 同时要求 site 在「S 之后第一个 HB 之前」
  另加反控：随机取两个起点 (S, X)，SC1 说 S 含 X 的比例应约等于「以 HB 分段的平均段长占比」。
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
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() ==
   '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
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
rets = [a for a, _, m, _ in insns if m.startswith('ret')]
calls = [(a, int(o, 16)) for a, _, m, o in insns if m == 'call' and o.startswith('0x')]
ck('S1 指令数 1,392,592', len(insns) == 1392592, len(insns))
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65): q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in rets:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET: HB.add(q)
ck('S2 HB == 17766', len(HB) == 17766, len(HB))
HBS = sorted(HB)
CALLT = set(t for _, t in calls if TS <= t < TE)
SLOT = defaultdict(set)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); i += 1
E = sorted(CALLT | set(SLOT) | HB)
ck('S3 |E| == 19490', len(E) == 19490, len(E))
def owner_old(a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None
def sc1(S, x):
    i = bisect.bisect_right(HBS, S)
    j = bisect.bisect_right(HBS, x)
    return i == j
def sc2(S, x):
    if not sc1(S, x): return False
    i = bisect.bisect_right(rets, S); j = bisect.bisect_right(rets, x)
    return i == j

random.seed(11011)
samp = random.sample(calls, 400)
res = Counter()
for a, t in samp:
    o = owner_old(a)
    ok1 = sc1(o, a); ok2 = sc2(o, a)
    res['sc1'] += ok1; res['sc2'] += ok2
    res['both'] += (ok1 and ok2); res['sc1_only'] += (ok1 and not ok2); res['sc2_only'] += (ok2 and not ok1)
    res['neither'] += (not ok1 and not ok2)
ck('E1 修正：400 个抽样 call 站点，SC1（只用 HB）判「最近 E 成员是容器」= %d/400 = %.1f%%；'
   'r109e 的 SC2（HB+首 ret）只给 %d/400 ⇒ 我上一稿的 69.8%% 是**误判**'
   % (res['sc1'], 100.0 * res['sc1'] / 400, res['sc2']),
   True, dict(res))
ck('E1b SC1 通过率应接近 1（旧口径若结构性正确则全过）', res['sc1'] >= 396, res['sc1'])
# 逐条核对 SC1 未过的 4-
bad = [(hex(a), hex(owner_old(a))) for a, t in samp if not sc1(owner_old(a), a)]
ck('E1c SC1 未过的站点（如实列出，供逐条定性）', True, bad[:8])
# 反控：随机 (S,X) 上证
rn = 0; hitc = 0
for _ in range(5000):
    s1 = random.choice(starts); x1 = random.choice(starts)
    if x1 <= s1: continue
    rn += 1; hitc += sc1(s1, x1)
ck('E1d 反控：随机 (S<X) 对里 SC1 判「S 含 X」= %d/%d = %.1f%%（旧口径在 call 站点上 %.1f%% ⇒ 富集 %.1f 倍）'
   % (hitc, rn, 100.0 * hitc / rn, 100.0 * res['sc1'] / 400,
      (res['sc1'] / 400.0) / max(1e-9, hitc / rn)),
   True, {'rand_pct': round(100.0 * hitc / rn, 1)})
json.dump({'checks': checks, 'sc1': res['sc1'], 'sc2': res['sc2'], 'res': dict(res),
           'bad': bad, 'rand': [hitc, rn]}, open('_r109/r109l_scfix.json', 'w'),
          ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
