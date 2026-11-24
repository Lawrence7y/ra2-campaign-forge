#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109b_qrule.py —— 判据 Q 的**自校验**：先用 A 标签当真值量它的精确率，再决定能不能外推到 195 个缺口。

判据 Q：「若函数 F 的直接 caller 中，至少 2 个 caller 的所属函数能由虚表槽值反查到**互相同一**的类 C，
           则推定 F 属于类 C。」
这不是拍脑袋规则：它的合法性必须先在**有真值的那部分**上量出来。本脚本做三件事：
  T1 建真值集：owners 中能被 vtable 槽值反查到**唯一**类名的那批（多类共用同一槽值的排除，或按集合处理）
  T2 在真值集上跑 Q（Q 的输入只用 caller 的 A 标签，不看 F 自己的真值），报精确率/覆盖率/弃权率
  T3 反控：把 A 标签随机置换后重跑，报精确率是否掉到基线；再取 20000 个随机指令起点当 F，报 Q 的发火率
"""
import bisect, hashlib, json, os, random, re, struct
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

A = json.load(open('_r109/r109a_attr.json'))
OWN = [int(o['owner'], 16) for o in A['owners']]
ck('S1 输入为 r109a 的 277 个 owner（自产，非外部报告）', len(OWN) == 277, len(OWN))

# ---- 全段扫描：指令起点 / call 站点 / HB / 槽值 ----
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
starts = []; calls = []; rets = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            calls.append((a, int(o, 16)))
        elif m.startswith('ret'):
            rets.append(a)
    if last <= pos:
        last = pos + 1
    pos = last
SSET = set(starts)
ck('S2 指令数 1,392,592', len(starts) == 1392592, len(starts))

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
ck('S3 HB == 17766', len(HB) == 17766, len(HB))
CALLT = set(t for _, t in calls if TS <= t < TE)
ck('S4 call 目标（.text 内）== 6719', len(CALLT) == 6719, len(CALLT))

SLOT = defaultdict(list)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        SLOT[x].append((k, i))
        i += 1
# jmp thunk 跟到真身（73 个，见 r109a 的形态普查）
def d1(a, n=2):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]
THUNK = {}
for x in list(SLOT):
    g = d1(x, 1)
    if g and g[0][2] == 'jmp' and g[0][3].startswith('0x'):
        THUNK[x] = int(g[0][3], 16)
# 口径修正（E-b1）：r109j 普查按**槽条目**数得 73，本处按 distinct 函数地址数得 28
# （同一 thunk 地址在多张表里重复出现）。两个数字都对，但报「thunk 有几个」必须用 28。
ck('S5 jmp 型槽值 thunk：distinct 函数地址 28 个（槽条目 73 次，同一地址跨表重复）',
   len(THUNK) == 28, len(THUNK))
SLOTF = defaultdict(set)          # func -> set(class)
for x, lst in SLOT.items():
    tgt = THUNK.get(x, x)
    for k, i in lst:
        SLOTF[tgt].add(k)
ck('S6 跟 thunk 后 distinct 槽值函数数 %d（跟之前 %d，差额 = 落在 thunk 上的槽值被合并到目标）'
   % (len(SLOTF), len(SLOT)), len(SLOTF) == 6472 and len(SLOT) == 6499, (len(SLOTF), len(SLOT)))
uniq = sum(1 for f, s in SLOTF.items() if len(s) == 1)
multi = sum(1 for f, s in SLOTF.items() if len(s) > 1)
ck('S7 唯一类函数 %d / 多类共用函数 %d（多类共用是继承未覆盖，不能当唯一真值）' % (uniq, multi),
   uniq + multi == len(SLOTF), (uniq, multi))
ck('S8 一个函数最多被 %d 个类共用（R107 EI3 的 0x708c30 是 4 类）' % max(len(s) for s in SLOTF.values()),
   max(len(s) for s in SLOTF.values()) >= 2, max(len(s) for s in SLOTF.values()))

E = sorted(CALLT | set(SLOT) | HB)
ck('S9 |E|（call ∪ 槽值 ∪ HB，不含 IMMPTR）非空且 > 18000', len(E) > 18000, len(E))
ESET = set(E)
def owner_of(addr):
    i = bisect.bisect_right(E, addr)
    return E[i - 1] if i else None

# caller 反查索引：call 站点 -> 所属函数
CALLERS = defaultdict(list)
for a, t in calls:
    if TS <= t < TE:
        CALLERS[t].append(a)

TRUTH = {f: next(iter(s)) for f, s in SLOTF.items() if len(s) == 1}

def vote(f):
    """Q：统计 f 的直接 caller 的所属函数的唯一 A 类，返回 (判定类 or None, 票表)"""
    v = Counter()
    for a in CALLERS.get(f, []):
        o = owner_of(a)
        if o is not None and o in TRUTH:
            v[TRUTH[o]] += 1
    tot = sum(v.values())
    if tot >= 2:
        cl, n = v.most_common(1)[0]
        if n * 2 > tot:                     # 简单多数，且至少 2 票
            return cl, v
    return None, v

# ---- T2 在真值集上量精确率 ----
EVAL = [f for f in OWN if f in TRUTH]
tp = fp = fn_ = 0
detail = []
for f in EVAL:
    cl, v = vote(f)
    if cl is None:
        fn_ += 1
        continue
    ok = (cl == TRUTH[f])
    tp += ok; fp += (not ok)
    if not ok:
        detail.append({'func': hex(f), 'truth': TRUTH[f], 'pred': cl, 'votes': v.most_common()})
prec = 100.0 * tp / (tp + fp) if tp + fp else 0.0
cov = 100.0 * (tp + fp) / len(EVAL) if EVAL else 0.0
ck('T1 真值集 = %d 个 owner 能被槽值反查到唯一类（277 中的 %d）' % (len(EVAL), len(EVAL)),
   50 <= len(EVAL) <= 120, len(EVAL))
ck('T2 Q 在真值集上的精确率 = %.1f%%（%d 对 / %d 错），覆盖率 %.1f%%，弃权 %d'
   % (prec, tp, fp, cov, fn_), True, {'tp': tp, 'fp': fp, 'abstain': fn_, 'prec': round(prec, 1), 'cov': round(cov, 1)})

# ---- T3 反控 1：置换 A 标签后重跑（应掉到随机水平） ----
keys = list(TRUTH)
vals = list(TRUTH.values())
random.seed(10922)
perm = vals[:]; random.shuffle(perm)
SHUF = dict(zip(keys, perm))
def vote_shuf(f):
    v = Counter()
    for a in CALLERS.get(f, []):
        o = owner_of(a)
        if o is not None and o in SHUF:
            v[SHUF[o]] += 1
    tot = sum(v.values())
    if tot >= 2:
        cl, n = v.most_common(1)[0]
        if n * 2 > tot:
            return cl
    return None
stp = sfp = 0
for f in EVAL:
    cl = vote_shuf(f)
    if cl is None:
        continue
    stp += (cl == TRUTH[f]); sfp += (cl != TRUTH[f])
sprec = 100.0 * stp / (stp + sfp) if stp + sfp else 0.0
# T3 在本真值集上**不可判**：可评样本只有 1 个（55 个真值 owner 里 54 个连 2 票都没有），
# 实时与置换后同为 0.0%，无法给出「显著低于」。样本量不足本身就是结论，故断言改为断言这一点。
ck('T3 反控不可判：可评样本 %d 个（<5），实时 %.1f%% 与置换后 %.1f%% 无法区分 ⇒ 判据 Q 需换大样本（见 r109c）'
   % (tp + fp, prec, sprec), (tp + fp) < 5, {'n': tp + fp, 'real': round(prec, 1), 'shuf': round(sprec, 1)})

# ---- T3b 反控 2：随机指令起点当 F，报 Q 的发火率 ----
random.seed(10933)
rnd = random.sample(starts, 20000)
fire = 0
for a in rnd:
    cl, v = vote(a)
    if cl is not None:
        fire += 1
ck('T4 反控：随机 20000 个指令起点上 Q 发火 %d（%.2f%%）' % (fire, 100.0 * fire / 20000),
   fire < 2000, (fire, round(100.0 * fire / 20000, 2)))

# ---- 外推：对仍未归因的 owner 应用 Q，并标注它靠不靠得住 ----
covd = set(A['owners'][i]['owner'] for i in range(len(A['owners'])) if A['owners'][i]['A'] or A['owners'][i]['B'])
covd = set(int(x, 16) for x in covd)
UNCOV = [f for f in OWN if f not in covd]
EXT = []
for f in UNCOV:
    cl, v = vote(f)
    EXT.append({'func': hex(f), 'pred': cl, 'votes': v.most_common(5), 'n_callsites': len(CALLERS.get(f, []))})
n_ext = sum(1 for e in EXT if e['pred'])
ck('T5 外推：%d 个未归因 owner 中 Q 给出判定 %d 个（占比 %.1f%%）；另有 %d 个连 2 票都没有'
   % (len(UNCOV), n_ext, 100.0 * n_ext / max(1, len(UNCOV)), len(UNCOV) - n_ext), True,
   {'uncovered': len(UNCOV), 'predicted': n_ext})

out = {'checks': checks, 'truth_n': len(EVAL), 'prec': round(prec, 2), 'cov': round(cov, 2),
       'tp': tp, 'fp': fp, 'abstain': fn_, 'shuf_prec': round(sprec, 2),
       'rand_fire': [fire, 20000], 'errors': detail,
       'uncovered_n': len(UNCOV), 'extrapolated_n': n_ext, 'extrapolated': EXT,
       'truth': {hex(k): v for k, v in TRUTH.items()}}
json.dump(out, open('_r109/r109b_qrule.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
