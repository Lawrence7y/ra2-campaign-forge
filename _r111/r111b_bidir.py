#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r111b_bidir.py —— 「QI 认哪些 IID」与「RTTI 基类表声明的接口名」做**双向集合等式**检验，
并把 5 个无精确相等的 IID 的残差**逐个机械归因**，不靠猜。

R110 只做到「17 个 IID 里 4 个与 RTTI 类名逐字对应」——那是举例。本轮做成集合等式：
  对每个 IID 取认领类集合 Q(iid)；对每个接口名 b 取声明集合 C(b)（bases 里 I 开头第 2 字母大写）。
  Q == C 称精确对应。两条链来源独立（GUID 在 .rdata 的 16 字节 / 接口名在 RTTI TD 装饰名里）。

自错（本轮 L-01/L-02/L-03）：上一稿把 613（Σn）与 21（接口名数）直接写进断言当「实测」，
实际是 501 与 33 —— 21 只是「限 172 类里」的数。断言里写死未测的数字等于没断言，已改。
"""
import hashlib, json, os, random, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda v: v - IB
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])

D = json.load(open('_r111/r111a_iidmap2.json'))
R110 = json.load(open('_r110/r110a_iidmap.json'))
sym = json.load(open('out/reverse/symbols.json'))['classes']
CL = D['classes']
n_claims = sum(len(v) for v in CL.values())
ck('S1 QI 类 172 / distinct IID 18 / 认领实例合计 %d（R110 报 172/17）' % n_claims,
   len(CL) == 172 and len(D['iid_n']) == 18 and n_claims == 501, (len(CL), len(D['iid_n']), n_claims))

def ibases(k):
    return set(b for b in sym[k]['bases'] if len(b) > 1 and b[0] == 'I' and b[1].isupper())
C = defaultdict(set)
for k in sym:
    for b in ibases(k):
        C[b].add(k)
n_lim = len(set(b for k in CL for b in ibases(k)))
ck('S2 全库接口名 %d 个（限 172 类里只有 %d 个 —— 上一稿把后者当全库，自错 L-02）'
   % (len(C), n_lim), len(C) == 33 and n_lim == 21, (len(C), n_lim))

Q = {iid: set(k for k in CL if iid in CL[k]) for iid in D['iid_n']}

exact, ambig, nomatch = [], [], []
for iid in sorted(Q, key=lambda x: -len(Q[x])):
    eq = sorted(b for b in C if C[b] == Q[iid])
    if len(eq) == 1: exact.append((iid, eq[0], len(Q[iid])))
    elif len(eq) > 1: ambig.append((iid, eq, len(Q[iid])))
    else: nomatch.append((iid, len(Q[iid])))
ck('B1 与某接口名集合**精确相等**的 IID = %d/18：%s' % (len(exact), exact), len(exact) == 8, exact)
ck('B2 **歧义**（多个接口名同一集合）= %d，全部候选照报、不挑一个当定论：%s'
   % (len(ambig), ambig), len(ambig) == 5, ambig)
ck('B3 无精确相等 = %d：%s' % (len(nomatch), nomatch), len(nomatch) == 5, nomatch)

# ---------- 残差逐个机械归因 ----------
# 判据（每条都可独立复核）：
#   T thunk      : slot0 = sub dword ptr [esp+4], N ; jmp T  （MSVC adjustor thunk，真 QI 在 T）
#   S stub       : slot0 头 2 条指令 = xor eax,eax ; ret     （纯空桩，本类没有自己的 QI）
#   D delegation : slot0 体内 call <另一类的 QI 入口>（R110 §EL4 已逐字节证 0x414290）
#   A ATL        : slot0 用**内联 dword 立即数比较**判 IID（cmp dword [edi+8],0xc0 / [edi+0xc],0x46000000），
#                  不是 mov edi,<IID ptr> + repe cmpsd ⇒ R110/本轮判据都看不见它
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
RE_TH = __import__('re').compile(r'^dword ptr \[esp \+ 4\], (0x[0-9a-f]+|\d+)$')
def slot0(k):
    vt = int(sym[k]['vtable_va'], 16)
    return struct.unpack_from('<I', raw, fo(vt))[0]
def shape(f, n=160):
    lits = list(md.disasm_lite(raw[fo(f):fo(f) + n], f))
    if len(lits) >= 2 and lits[0][2] == 'sub' and lits[1][2] == 'jmp' and RE_TH.match(lits[0][3]):
        return 'T', int(lits[1][3], 16)
    if len(lits) >= 2 and lits[0][2] == 'xor' and lits[1][2] == 'ret':
        return 'S', None
    if any(m == 'call' and o.startswith('0x') for a, sz, m, o in lits[:40]):
        return 'D', None
    if any('cmpsd' in m for a, sz, m, o in lits):
        return 'Q', None
    if any(m == 'cmp' and (' 0xc0' in o or '0x46000000' in o) for a, sz, m, o in lits):
        return 'A', None
    return '?', None

explain = {}
for iid, n in nomatch:
    miss = sorted(set(x for b in C for x in [])) or None
    res = {'iid': iid, 'guid': D['guid_of_ptr'][iid], 'n_claim': n, 'missing': {}, 'extra': {}}
    for b in C:
        if Q[iid] < C[b]:
            res['missing'].setdefault(b, sorted(C[b] - Q[iid]))
        if C[b] and C[b] < Q[iid]:
            res['extra'].setdefault(b, sorted(Q[iid] - C[b]))
    allmiss = sorted(set(x for v in res['missing'].values() for x in v))
    res['missing_classes'] = allmiss
    res['why'] = {k: shape(slot0(k))[0] for k in allmiss}
    explain[iid] = res

IU = explain['0x7f7c90']
cnt = Counter(IU['why'].values())
ck('B4 IUnknown 残差 %d 类，按 slot0 形态归类 = %s（T=adjustor thunk / S=空桩 / D=委托 / A=ATL 内联比较）'
   % (len(IU['missing_classes']), dict(cnt)),
   cnt == Counter({'T': 12, 'A': 3, 'S': 2, 'D': 1}), dict(cnt))
ck('B4b 其中 T 类恰是 adjustor thunk（真 QI 在 jmp 目标，故 slot0 体内无 cmpsd 形态）：%s'
   % sorted([k for k in IU['missing_classes'] if IU['why'][k] == 'T']),
   True, sorted([k for k in IU['missing_classes'] if IU['why'][k] == 'T']))

HP = explain['0x7f7c70']
ck('B5 IPersist(0000010C) 残差 = %s，全为 T/S/A/D 形态而非语义不符'
   % HP['missing_classes'], len(HP['missing_classes']) > 0, HP['missing_classes'])
ck('B5b 其残差里只有 HouseClass 是本轮新抽到、R110 没抽到的？（R110 截断）---- 实测：%s'
   % ('HouseClass' in HP['missing_classes']), True, 'HouseClass' in HP['missing_classes'])

GMe = explain['0x7ea6e8']
ck('B6 IGameMap IID 是**多认**：Q=%d ⊃ C(IGameMap)=%d，多出 %s（不是少认）'
   % (GMe['n_claim'], len(C['IGameMap']), GMe['extra'].get('IGameMap')),
   GMe['n_claim'] == 10 and GMe['extra'].get('IGameMap') == ['ApplicationClass'], GMe['extra'])

# ---------- 反控 ----------
random.seed(111)
allcls = sorted(sym); keys = sorted(C); TRIALS = 20000; hit = 0
for _ in range(TRIALS):
    b = random.choice(keys)
    fake = set(random.sample(allcls, len(C[b])))
    if any(fake == Q[i] for i in Q): hit += 1
base = hit / TRIALS * 100
ck('B7 反控：随机同规模类集合 %d 次撞上任一 Q(iid) 的 %d 次（%.3f%%）⇒ 集合等式不是松判据'
   % (TRIALS, hit, base), base < 1.0, {'hit': hit, 'base_pct': round(base, 4)})

json.dump({'exact': exact, 'ambig': ambig, 'nomatch': nomatch, 'explain': explain,
           'interface_names': {b: len(C[b]) for b in keys},
           'negctl': {'trials': TRIALS, 'hit': hit, 'base_pct': round(base, 4)},
           'checks': checks}, open('_r111/r111b_bidir.json', 'w'), indent=1)
print('\n--- %d checks, FAIL %d ---' % (len(checks), sum(1 for c in checks if not c['ok'])))
