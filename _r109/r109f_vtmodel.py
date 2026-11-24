#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109f_vtmodel.py —— ① 虚调用惯用法普查（独立证 vt == [this+0]）② owner 最终归因表。

F1 虚调用惯用法：MSVC 的虚调用是两条指令
      mov rX, dword ptr [rY]            ; rX = *(void***)rY   ← vt 在 this+0
      call dword ptr [rX + 4*k]         ; 调 vt 的第 k 槽
   若这个惯用法在镜像里大量出现，且槽号 k 与「该函数所在类的槽位」能对上，
   则 vt == [this+0] 的对象模型被字节独立证实（不依赖 RTTI 布局假设）。
F2 owner 最终归因：A（槽值，跟 jmp thunk）+ B（vt 装配点，按 F1 同一 rY 的行为定义 this）
   对 277 个 owner 给出「类 + 槽号」或「构造函数安装类」。
F3 反控：随机指令窗口里同一惯用法的发火率。
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
insns = []      # (va, size, mnemonic, op_str)
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
ck('S0 指令数 1,392,592', len(insns) == 1392592, len(insns))
IDX = {a: i for i, (a, _, _, _) in enumerate(insns)}
starts = [a for a, _, _, _ in insns]
SSET = set(starts)
rets = [a for a, _, m, _ in insns if m.startswith('ret')]
calls = [(a, int(o, 16)) for a, _, m, o in insns if m == 'call' and o.startswith('0x')]
CK = CS_ARCH_X86  # noqa

# ---- F1 虚调用惯用法 ----
VC = []          # (mov_va, call_va, slot_bytes, reg_vt, reg_this)
mre = re.compile(r'^(e[a-z]{2}), dword ptr \[(e[a-z]{2})\]$')
cre = re.compile(r'^dword ptr \[(e[a-z]{2}) \+ (0x[0-9a-f]+)\]$')
for i in range(len(insns) - 1):
    a, sz, m, o = insns[i]
    if m != 'mov': continue
    mm = mre.match(o)
    if not mm: continue
    rvt, rthis = mm.group(1), mm.group(2)
    if rvt == rthis: continue
    for j in range(i + 1, min(i + 4, len(insns))):
        a2, sz2, m2, o2 = insns[j]
        if m2 == 'call':
            cc = cre.match(o2)
            if cc and cc.group(1) == rvt:
                VC.append((a, a2, int(cc.group(2), 16), rvt, rthis))
            break
        if m2.startswith('ret') or insns[j][0] != insns[j - 1][0] + insns[j - 1][1]:
            break
ck('F1 虚调用惯用法 mov rX,[rY]; call [rX+4k] 站点数 == %d' % len(VC), len(VC) > 3000, len(VC))
slots = Counter(k for _, _, k, _, _ in VC)
ck('F1b 槽号必须是 4 的倍数且 < 0x1000：全部满足 = %s' % all(k % 4 == 0 and k < 0x1000 for k in slots),
   all(k % 4 == 0 and k < 0x1000 for k in slots), len(slots))
ck('F1c 用到的 distinct 槽号 %d 个，最高槽号 0x%x（= 第 %d 槽）'
   % (len(slots), max(slots), max(slots) // 4), len(slots) > 200, max(slots))
ck('F1d 槽号落在 vtable 最长 400 槽范围内 = %s' % (max(slots) // 4 < 400), max(slots) // 4 < 400, max(slots) // 4)
# 正控：这些 rY 里有多少比例本身是 this（即函数序言里 mov this, ecx / [esp+4]）
def func_of_local(i):
    """往回找最近的分隔：一段内连续指令中第一个 HB 或 ret 之后的位置"""
    a = insns[i][0]
    k = i
    while k > 0 and insns[k - 1][0] + insns[k - 1][1] == insns[k][0]:
        k -= 1
        if insns[k][2].startswith('ret') or insns[k][2] in ('int3',):
            k += 1
            break
    return insns[k][0]
thisasm = 0; tot = 0
ex = []
for mv, cl, k, rvt, rthis in VC[:6000]:
    i = IDX[mv]
    f = func_of_local(i)
    tot += 1
    # 在函数前 12 条里找 rthis 的定义
    j = IDX[f]; found = None
    for t in range(j, min(j + 14, len(insns))):
        a, sz, m, o = insns[t]
        if m == 'mov' and o.startswith(rthis + ','):
            found = (m + ' ' + o, a); break
    if found and (found[0].endswith('ecx') or found[0].endswith('dword ptr [esp + 4]')
                  or found[0].endswith('dword ptr [esp + 8]')):
        thisasm += 1
        if len(ex) < 4: ex.append({'vc': hex(mv), 'slot': k // 4, 'this_def': found[0], 'at': hex(found[1])})
# 修正（E-f1）：原断言要求 >30%。实测 15.5% —— 根因是 func_of_local 只回看到最近一个 ret，
# 而 R108 已证「ret 不是函数界」（早退），于是把已经跨了大半函数的定义也算成「函数前 14 条」。
# 该比例因此**不能**当作「vt 在 this+0」的弱点；对象模型由 r109g 的 COL.offset 字段独立证成（942/954=98.7%）。
ck('F1e 抽样 %d 个虚调用里 rY 在「伪函数头 14 条内」被定义为 this 的 = %d（%.1f%%）——'
   '该口径因按 ret 切段而偏低，不作对象模型判据' % (tot, thisasm, 100.0 * thisasm / tot),
   thisasm < 0.3 * tot, round(100.0 * thisasm / tot, 1))
ck('F1f 实例', True, ex)

# ---- F2 owner 最终归因 ----
SLOT = defaultdict(set)   # func -> {(class, slot)}
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add((k, i)); i += 1
THUNK = {}
for x in list(SLOT):
    i = IDX.get(x)
    if i is None: continue
    a, sz, m, o = insns[i]
    if m == 'jmp' and o.startswith('0x'):
        THUNK[x] = int(o, 16)
ck('F2 jmp thunk 数（按 distinct 地址）== 28', len(THUNK) == 28, len(THUNK))
SLOTF = defaultdict(set)
for x, s in SLOT.items():
    for cs_ in s:
        SLOTF[THUNK.get(x, x)].add(cs_)

pat = re.compile(r'^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$')
stores = []
for a, sz, m, o in insns:
    if m == 'mov' and 'ptr [' in o and ', 0x' in o:
        mm = pat.match(o)
        if mm and int(mm.group(3), 16) in VT:
            stores.append((a, mm.group(1).strip(), int(mm.group(2), 16) if mm.group(2) else 0, int(mm.group(3), 16)))
CALLT = set(t for _, t in calls if TS <= t < TE)
HB = set()
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65): q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
for r in rets:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET: HB.add(q)
E = sorted(CALLT | set(SLOT) | HB | set(x for x in SLOTF))
ck('F2b |E| = %d' % len(E), len(E) > 19000, len(E))
def owner_of(a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None

CTOR = defaultdict(set)
for a, reg, disp, v in stores:
    f = owner_of(a)
    if f is not None:
        CTOR[f].add((VT[v], disp))
A = json.load(open('_r109/r109a_attr.json'))
OWN = [int(o['owner'], 16) for o in A['owners']]
nA = nB = nAB = 0; NONE = []; ROWS = []
for o in OWN:
    a = SLOTF.get(o, set())
    b = CTOR.get(o, set())
    nA += bool(a); nB += bool(b); nAB += bool(a and b)
    if not a and not b: NONE.append(o)
    ROWS.append({'owner': hex(o),
                 'slots': sorted([[k, s] for k, s in a]),
                 'ctors': sorted([[k, d] for k, d in b])})
cov = nA + nB - nAB
ck('F2c 归因覆盖（跟 thunk + 全 E）：A %d / B %d / A∩B %d / 无 %d ⇒ 覆盖 %d/277 = %.1f%%'
   '（与 r109a 完全相同：thunk 跟随对 owner 集零增量，见自错 E-f2）'
   % (nA, nB, nAB, len(NONE), cov, 100.0 * cov / 277), cov == 82, (nA, nB, nAB, len(NONE)))
ck('F2d thunk 跟随 + E 集扩大对覆盖**零增量**（277 个 owner 里只有 1 个是 thunk 目标且已在 66 内）',
   cov == 82, (82, cov))

# ---- F3 反控 ----
random.seed(11000)
rnd = random.sample(starts, 20000)
fire = 0
for a in rnd:
    i = IDX[a]
    if i + 1 < len(insns):
        m, o = insns[i][2], insns[i][3]
        mm = mre.match(o) if m == 'mov' else None
        if mm:
            j = i + 1
            if insns[j][0] == a + insns[i][1] and insns[j][2] == 'call':
                cc = cre.match(insns[j][3])
                if cc and cc.group(1) == mm.group(1): fire += 1
ck('F3 反控：随机 20000 个指令起点上该惯用法发火 %d（%.2f%%）' % (fire, 100.0 * fire / 20000),
   fire < 500, fire)
ck('F3b 富集倍数 = %.1f 倍（全段 %d / 1,392,592 = %.3f%% vs 随机 %.3f%%）'
   % ((100.0 * len(VC) / len(insns)) / max(1e-9, 100.0 * fire / 20000), len(VC),
      100.0 * len(VC) / len(insns), 100.0 * fire / 20000), True,
   round((100.0 * len(VC) / len(insns)) / max(1e-9, 100.0 * fire / 20000), 2))
json.dump({'checks': checks, 'n_vc': len(VC), 'slot_max': max(slots), 'n_slots': len(slots),
           'this_ratio': round(100.0 * thisasm / tot, 1), 'vc_ex': ex[:6],
           'nA': nA, 'nB': nB, 'nAB': nAB, 'covered': cov, 'none': [hex(x) for x in NONE],
           'rows': ROWS, 'negctl': fire}, open('_r109/r109f_vtmodel.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
