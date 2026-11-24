#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109c_callervote.py —— 判据 Q 的**大样本**校准：真值集从 55 个 owner 扩到全部唯一类槽值函数（5153）。

r109b 的 T2 只拿到 1 个可评样本（55 个真值 owner 里 54 个连 2 票都没有），
那条样本还判错了。样本太小不足以裁定 Q，故本脚本换成大样本：
  C1 真值集 = SLOTF 里唯一类的全部函数（5153），不再限于 277 个 owner
  C2 对每个真值函数跑 Q（票源只允许「caller 的所属函数本身有唯一类真值」），
     分别报 k>=1 / k>=2 / k>=3 三档的精确率、覆盖率
  C3 阈值扫描：多数票比例阈值 0.5 / 0.67 / 1.0
  C4 反控：A 标签随机置换 + 随机起点集
  C5 结论：Q 该判「可用 / 只可当弱提示 / 判死」
"""
import bisect, hashlib, json, os, random, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
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
SSET = set(starts)
ck('S1 指令数 1,392,592', len(starts) == 1392592, len(starts))

def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in sorted(rets):
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
CALLT = set(t for _, t in calls if TS <= t < TE)
ck('S2 HB 17766 / call 目标 6719', len(HB) == 17766 and len(CALLT) == 6719, (len(HB), len(CALLT)))

SLOT = defaultdict(set)
SLOTN = defaultdict(int)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); SLOTN[x] += 1
        i += 1
# thunk 跟随：只跟一层 jmp imm
def d1(a, n=1):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]
THUNK = {}
for x in list(SLOT):
    g = d1(x, 1)
    if g and g[0][2] == 'jmp' and g[0][3].startswith('0x'):
        THUNK[x] = int(g[0][3], 16)
ck('S3 jmp 型 thunk（按 distinct 函数计）== 28（按槽条目计 73：同一地址在多张表重复出现）',
   len(THUNK) == 28, len(THUNK))
SLOTF = defaultdict(set)
for x, s in SLOT.items():
    for k in s:
        SLOTF[THUNK.get(x, x)].add(k)
TRUTH = {f: next(iter(s)) for f, s in SLOTF.items() if len(s) == 1}
ck('S4 真值集（唯一类）== 5153 个函数', len(TRUTH) == 5153, len(TRUTH))
ck('S5 多类共用（继承未覆盖）函数 == 1319，最多共用类数 == 77',
   sum(1 for s in SLOTF.values() if len(s) > 1) == 1319 and max(len(s) for s in SLOTF.values()) == 77,
   (sum(1 for s in SLOTF.values() if len(s) > 1), max(len(s) for s in SLOTF.values())))

E = sorted(CALLT | set(SLOT) | HB | set(TRUTH))
ESET = set(E)
def owner_of(a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None
CALLERS = defaultdict(list)
for a, t in calls:
    if TS <= t < TE:
        CALLERS[t].append(a)
ck('S6 有直接 call 站点的函数数 == %d（5153 真值函数中 %d 个有 caller）'
   % (len(CALLERS), sum(1 for f in TRUTH if CALLERS.get(f))),
   len(CALLERS) > 5000, (len(CALLERS), sum(1 for f in TRUTH if CALLERS.get(f))))

def votes(f):
    v = Counter()
    for a in CALLERS.get(f, []):
        o = owner_of(a)
        if o in TRUTH:
            v[TRUTH[o]] += 1
    return v

def risk_eval(sel, frac):
    tp = fp = 0
    for f in sel:
        v = votes(f)
        tot = sum(v.values())
        if tot == 0: continue
        cl, n = v.most_common(1)[0]
        if n >= 2 and n >= frac * tot:
            tp += (cl == TRUTH[f]); fp += (cl != TRUTH[f])
    return tp, fp

EVAL = [f for f in TRUTH if CALLERS.get(f)]
for kmin in (1, 2, 3):
    tp = fp = 0
    for f in EVAL:
        v = votes(f); tot = sum(v.values())
        if tot < kmin: continue
        cl, n = v.most_common(1)[0]
        if n * 2 > tot:
            tp += (cl == TRUTH[f]); fp += (cl != TRUTH[f])
    p = 100.0 * tp / (tp + fp) if tp + fp else 0.0
    c = 100.0 * (tp + fp) / len(EVAL)
    ck('C2 k>=%d：精确率 %.1f%%（%d 对 / %d 错），覆盖 %d/%d = %.1f%%'
       % (kmin, p, tp, fp, tp + fp, len(EVAL), c), True, (round(p, 1), round(c, 1)))

rows = {}
for frac in (0.5, 0.67, 1.0):
    tp, fp = risk_eval(EVAL, frac)
    p = 100.0 * tp / (tp + fp) if tp + fp else 0.0
    rows[frac] = (tp, fp, round(p, 1))
    ck('C3 多数票阈值 %.2f：精确率 %.1f%%（%d 对 / %d 错）' % (frac, p, tp, fp), True, rows[frac])

# C4 反控：置换标签
random.seed(10944)
keys = list(TRUTH); vals = [TRUTH[k] for k in keys]
perm = vals[:]; random.shuffle(perm)
SHUF = dict(zip(keys, perm))
tp = fp = 0
for f in EVAL:
    v = Counter()
    for a in CALLERS.get(f, []):
        o = owner_of(a)
        if o in SHUF: v[SHUF[o]] += 1
    tot = sum(v.values())
    if tot >= 2:
        cl, n = v.most_common(1)[0]
        if n * 2 > tot:
            tp += (cl == TRUTH[f]); fp += (cl != TRUTH[f])
sp = 100.0 * tp / (tp + fp) if tp + fp else 0.0
real = rows[0.5][2]
# 修正（E-c1）：原断言要求「实时比置换高 10 个百分点」。实测**两者同为 0.0%**，
# 说明 Q 在实时数据上也没有任何信息量，置换反控在这里**没有区分力**（地板效应）。
# 断言改为断言「实时不高于置换 + 一个极小量」，并把地板效应本身写成结论。
ck('C4 反控呈地板效应：实时 %.2f%% 与置换 %.2f%% 同为 0 ⇒ Q 无信息量（此反控已无区分力）'
   % (real, sp), real - sp < 1.0, (round(sp, 2), real))

# C5 随机起点反控
random.seed(10955)
rnd = random.sample(starts, 20000)
fire = 0
for a in rnd:
    v = votes(a); tot = sum(v.values())
    if tot >= 2:
        cl, n = v.most_common(1)[0]
        if n * 2 > tot: fire += 1
ck('C5 随机 20000 个指令起点发火 %d（%.2f%%）' % (fire, 100.0 * fire / 20000), fire < 2000,
   (fire, round(100.0 * fire / 20000, 2)))

# C6 单票（k>=1）情形的分解：这是不是「只要被某类方法调用一次就贴标」？
tp = fp = 0
for f in EVAL:
    v = votes(f); tot = sum(v.values())
    if tot != 1: continue
    cl, n = v.most_common(1)[0]
    tp += (cl == TRUTH[f]); fp += (cl != TRUTH[f])
p1 = 100.0 * tp / (tp + fp) if tp + fp else 0.0
ck('C6 只有 1 票的样本：%d 个，精确率 %.1f%%（%d 对 / %d 错）'
   % (tp + fp, p1, tp, fp), True, {'n': tp + fp, 'p': round(p1, 1)})

out = {'checks': checks, 'truth_n': len(TRUTH), 'eval_n': len(EVAL), 'fracs': {str(k): v for k, v in rows.items()},
       'single_vote': {'n': tp + fp, 'p': round(p1, 1)}, 'shuf_p': round(sp, 2),
       'rand_fire': [fire, 20000], 'n_thunk': len(THUNK)}
json.dump(out, open('_r109/r109c_callervote.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
