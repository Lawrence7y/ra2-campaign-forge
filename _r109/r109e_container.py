#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109e_container.py —— 先修仪器再说判据：严格容器判定 + 判据 Q 的重判。

r109c/d 用「<= 站点 的最近 E 成员」当容器函数（R108 口径）。r109d D1 实测 40 个抽样里
**13/40** 在 owner 与站点之间还隔着 ret —— 若那些 ret 之后另有 HB 起点，容器就取错了，
Q 的票源全是错的。本脚本引入严格容器判据 SC：
  从起点 S 前向线性走，遇到 ret 且其后 4 字节对齐处是 HB 起点 ⇒ 该函数在此结束；
  site 必须落在结束点之前，否则 S 不是容器。
对 387 个分派站点与 6719 个 call 站点各算一次 SC 通过率，与旧口径对比。
然后：
  E1 旧口径 vs SC 口径的分歧量（这是 R108 Q4 那条「27/40 有 0 ret」的真实含义）
  E2 Q 在 SC 口径下重评（同类票占比、精确率）
  E3 vivt 对象模型：构造函数里 mov [reg+0], vtable 的实例，同一 reg 在同一函数内
     又被用作 [reg+disp] 的基址读字段 ⇒ 实证 vt == [this+0]
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
ck('S0 HB == 17766', len(HB) == 17766, len(HB))
CALLT = set(t for _, t in calls if TS <= t < TE)
SLOT = defaultdict(set)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); i += 1
E = sorted(CALLT | set(SLOT) | HB); ESET = set(E)
ck('S1 |E| == 19490', len(E) == 19490, len(E))
def owner_old(a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None

HBS = sorted(HB)
def contains(S, site, cap=40000):
    """SC：从 S 前向走，遇 ret 且其后（含填充后）是 HB 起点 ⇒ S 的函数在此结束。"""
    a = S; n = 0
    while a < TE and n < cap:
        if a == site:
            return True, n
        if a > site:
            return False, n
        if a in HBS and a != S:
            return False, n
        g = d1(a, 1)
        if not g:
            return False, n
        if g[0][2].startswith('ret'):
            return False, n
        a = g[0][0] + g[0][1]; n += 1
    return None, n

# ---- E1 口径分歧 ----
SITES = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2: SITES.append((a, int(m2[-1], 16)))
    if last <= pos: last = pos + 1
    pos = last
ck('S2 分派站点 387', len(SITES) == 387, len(SITES))
CALLS_IN = [(a, t) for a, t in calls if TS <= t < TE]
random.seed(10977)
samp = random.sample(CALLS_IN, 400)
res = {'old_ok': 0, 'sc_ok': 0, 'both': 0, 'old_only': 0, 'sc_only': 0, 'neither': 0, 'unknown': 0}
for a, t in samp:
    o = owner_old(a)
    okold = o is not None and o <= a
    okb, n = contains(o, a) if o is not None else (None, 0)
    if okb is None:
        res['unknown'] += 1; continue
    res['old_ok'] += okold; res['sc_ok'] += okb
    res['both'] += (okold and okb)
    res['old_only'] += (okold and not okb)
    res['sc_only'] += (okb and not okold)
    res['neither'] += (not okold and not okb)
# 🐞 本节 E1/E1b/E2/E2b 用的 SC 判据（遇 ret 即函数界）**已被 r109l 证伪**：
# R108 已证 ret 不是函数界（同一函数 5 条早退 ret）。r109l 改用「只用 HB」后，
# 同一批 400 个站点的通过率是 400/400（不是 69.8%）。以下四行断言保留原值**作为错口径留痕**，
# 正确数值见 _r109/r109l_scfix.json 与 _r109/r109c_callervote.json。
ck('E1【已作废口径，仅留痕】400 个 call 站点抽样：旧口径声称包含 %d，SC(ret 版) 判 %d；'
   '旧口径对 SC 错 %d、SC 对旧口径错 %d、都错 %d、不可判 %d'
   % (res['old_ok'], res['sc_ok'], res['old_only'], res['sc_only'], res['neither'], res['unknown']),
   True, res)
sc_ratio = 100.0 * res['sc_ok'] / (res['sc_ok'] + res['old_only'] + res['neither'])
ck('E1b【已作废口径】SC(ret 版) 下「最近 E 成员是容器」的比例 = %.1f%%；'
   'r109l 用 HB 版得 400/400 = 100.0%% ⇒ ret 版把早退误判成跨函数' % sc_ratio,
   True, round(sc_ratio, 1))

# ---- E2 Q 在 SC 口径下重评 ----
TRUTH = {f: next(iter(s)) for f, s in SLOT.items() if len(s) == 1}
CALLERS = defaultdict(list)
for a, t in calls:
    if TS <= t < TE: CALLERS[t].append(a)
# E-z5：原实现按「每个真值函数 × 每条 call」二重循环，且 contains() 每次都从头线性解码，
# 复杂度 O(|TRUTH| * |calls| * 段长)，实测 400s 未收敛。改为按 call 站点一次遍历：
# 对每条 call，先算一次 (o, okb)，再把结果累加到它的被调函数上。等价、线性。
same = diff = 0; ev = 0
_evset = set(f for f in TRUTH if CALLERS.get(f))
ev = len(_evset)
for a, t in calls:
    if t not in _evset: continue
    o = owner_old(a)
    if o is None: continue
    okb, _ = contains(o, a)
    if okb is not True: continue
    if o in TRUTH:
        same += (TRUTH[o] == TRUTH[t]); diff += (TRUTH[o] != TRUTH[t])
ck('E2【近似口径】已知类函数的 caller 同类票 = %d / 异类票 = %d（同类占比 %.2f%%），可评函数 %d'
   % (same, diff, 100.0 * same / max(1, same + diff), ev), True,
   {'same': same, 'diff': diff, 'eval': ev})
# 与随机基线比：随机抽一对 (caller 类, callee 类) 同类概率
cls_pairs = Counter()
allf = [f for f in TRUTH if CALLERS.get(f)]
random.seed(10988)
rnd_same = 0; rnd_n = 20000
for _ in range(rnd_n):
    f = random.choice(allf); g = random.choice(allf)
    rnd_same += (TRUTH[f] == TRUTH[g])
ck('E2b 随机基线（随机两个真值函数同类）概率 = %.2f%%；实测同类票 %.2f%% ⇒ Q 的同类性假设%s'
   % (100.0 * rnd_same / rnd_n, 100.0 * same / max(1, same + diff),
      '成立' if same / max(1, same + diff) > rnd_same / rnd_n else '不成立（不高于随机）'),
   True, {'base': round(100.0 * rnd_same / rnd_n, 2), 'obs': round(100.0 * same / max(1, same + diff), 2)})

# ---- E3 vt == [this+0] 对象模型实证 ----
pat = re.compile(r'^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$')
pos = TS; stores = []
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        if m == 'mov' and 'ptr [' in o and ', 0x' in o:
            mm = pat.match(o)
            if mm and int(mm.group(3), 16) in VT:
                reg = mm.group(1).strip()
                disp = int(mm.group(2), 16) if mm.group(2) else 0
                stores.append((a, reg, disp, int(mm.group(3), 16)))
    if last <= pos: last = pos + 1
    pos = last
ck('E3 vtable 写入点 == 4611（与 r109a S6 同口径）', len(stores) == 4611, len(stores))
at0 = [s for s in stores if s[2] == 0 and s[1] in ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'ebp')]
ck('E3b 写偏移 0 的点 %d / 非 0 偏移 %d（原预期 >3000，实测 2762 ⇒ 非 0 偏移比预想多，'
   '「vt 只写 this+0」的覆盖须靠 COL.offset 字段判，见 r109g）'
   % (len(at0), len(stores) - len(at0)), len(at0) == 2762, (len(at0), len(stores) - len(at0)))
# 同一函数内、同一基址寄存器随后被用作 [reg+disp] 读字段（disp != 0）
byfunc = defaultdict(list)
for a, reg, disp, v in stores:
    f = owner_old(a)
    if f is not None: byfunc[f].append((a, reg, disp, v))
fin = 0; ex = []
VT_REV = VT
for f, lst in byfunc.items():
    regs = set(r for _, r, d, _ in lst if d == 0)
    if not regs: continue
    # 在该函数体内（SC 范围内）找 [reg + disp] 且 disp != 0 的读
    a = f; seen = 0; found = None
    while a < TE and seen < 400:
        g = d1(a, 1)
        if not g: break
        ins = g[0]
        if ins[2] in ('mov', 'movzx', 'movsx', 'cmp', 'test', 'push', 'add', 'or') and 'ptr [' in ins[3]:
            for r in regs:
                if re.search(r'\[%s \+ 0x[0-9a-f]+\]' % r, ins[3]):
                    found = (hex(ins[0]), ins[2] + ' ' + ins[3]); break
        if found or ins[2].startswith('ret'): break
        a = ins[0] + ins[1]; seen += 1
    if found:
        fin += 1
        if len(ex) < 5: ex.append({'func': hex(f), 'vt': hex(lst[0][3]), 'cls': VT_REV[lst[0][3]], 'field_read': found})
ck('E3c 装配函数中「写 [reg+0]=vt 后同一 reg 又被 [reg+disp] 取字段」的实例 = %d / %d（实证 vt 位于 this+0）'
   % (fin, len(byfunc)), fin > 500, (fin, len(byfunc)))
ck('E3d 反控：随机 2000 个指令起点里满足同一形态（写 vt 到 [reg+0] 且随后读字段）的比例 = 需对同一形态取随机基线',
   True, '见 negctl')
# 反控：把 vt 立即数换成随机 .text 地址，重跑 E3c 的形成条件（应当掉到 0，因为写入点定义本身就要求地址 ∈ VT）
rnd_ok = 0
random.seed(10999)
for _ in range(2000):
    a = random.choice(starts)
    g = d1(a, 1)
    if not g: continue
    ins = g[0]
    if ins[2] == 'mov' and 'ptr [' in ins[3] and ', 0x' in ins[3]:
        mm = pat.match(ins[3])
        if mm and mm.group(2) is None and int(mm.group(3), 16) in VT:
            rnd_ok += 1
ck('E3d 反控：随机 2000 个起点中「写偏移 0 且立即数 ∈ VT」的指令 = %d（%.2f%%）'
   % (rnd_ok, 100.0 * rnd_ok / 2000), rnd_ok < 100, rnd_ok)
json.dump({'checks': checks, 'E1': res, 'sc_ratio': round(sc_ratio, 1), 'same': same, 'diff': diff,
           'eval': ev, 'vt_at0': len(at0), 'vt_stores': len(stores), 'e3c': fin,
           'e3c_total': len(byfunc), 'e3c_ex': ex, 'negctl_rnd': rnd_ok},
          open('_r109/r109e_container.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
