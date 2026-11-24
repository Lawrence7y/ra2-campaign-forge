#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109a_attr.py —— 把 R108 的 277 个 switch 表 owner 从「纯地址」推进到「类 + 槽号 / 构造函数」。

四条独立证据路径，全部只读镜像字节与 symbols.json（RTTI 已证三表 TD/COL/vtable 闭合 988/1211/1214）：
  A 槽归属：vtable[slot]==owner ⇒ owner 是某类第 slot 个虚方法（含继承重复，须按基类链去重）
  B 装配点：函数体内 mov dword ptr [reg+disp], <vtable_va> ⇒ 该函数安装该类虚表（disp==0 为主表）
  C 交叉一致性：A∩B 应为空性质检验（虚方法不会安装虚表；构造函数通常非虚）——共享即红旗
  D 反控：随机 20000 个指令起点里命中 A 或 B 的比例（富集倍数）

内存纪律：全段只用 disasm_lite + 64KB 分块；detail 不开。
"""
import bisect, hashlib, json, os, re, struct, sys
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
def fo(va):
    return va - IB

# ---------- vtable 表（symbols.json 是 RTTI 三表闭合的产物，vfunc_count 与镜内槽数逐类一致 954/954） ----------
sym = json.load(open('out/reverse/symbols.json'))
cls = sym['classes']
VT = {}          # vtable_va -> class key
for k, c in cls.items():
    if c.get('vtable_va'):
        VT[int(c['vtable_va'], 16)] = k
ck('S1 vtable 数 == 954（R107 EI3 同口径）', len(VT) == 954, len(VT))
ck('S2 TD 数 == 988 且 with_col == 954（与 R89 full_range 口径一致）',
   sym['diagnostics']['classes'] == 988 and sym['diagnostics']['with_col'] == 954,
   (sym['diagnostics']['classes'], sym['diagnostics']['with_col']))

# 正控：vtable[-4] 必须指回该类的 COL（F01 链：vtable[-4] -> COL -> COL+0xC -> TD -> TD+8 -> 名字）
n_col_back = 0
for va, k in VT.items():
    col = struct.unpack_from('<I', raw, fo(va) - 4)[0]
    if cls[k].get('col_va') and col == int(cls[k]['col_va'], 16):
        n_col_back += 1
# 修正（E-a1）：原断言写成「vtable[-4] == symbols.json 的 col_va」，实测 866/954。
# 根因是 col_va 记的是「该 TD 的最低 VA COL」（r89 rtti_r89.json symbols_col_va_lowest_of_td=954 即此口径），
# 而 vtable[-4] 可指向同一 TD 的另一条 COL（r89 col_per_td：1211 条 COL 分给 954 TD）。
# 正确判据是 pTD 相同。实测 954/954。
n_col_back = 0
for va, k in VT.items():
    col = struct.unpack_from('<I', raw, fo(va) - 4)[0]
    if 0x400000 <= col < 0x900000 and cls[k].get('col_va') and \
       struct.unpack_from('<I', raw, fo(col) + 0xc)[0] == int(cls[k]['type_descriptor_va'], 16):
        n_col_back += 1
ck('S3 正控 vtable[-4] 所指 COL 的 pTD == 该类 TD 的占比 == 954/954（RTTI 链自洽；'
   '注意 88 张表指向的是同一 TD 的**另一条** COL，故不能拿 col_va 直接比）',
   n_col_back == 954, '%d/954' % n_col_back)

# ---------- .text 全段 lite 扫描（一次，复用给 A/B/D） ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
starts = []
calls = []
rets = []
vt_store = []     # (insn_va, vtable_va, disp)
pos = TS
n_undec = 0
imm_re = re.compile(r'^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$')
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            calls.append((a, int(o, 16)))
        elif m.startswith('ret'):
            rets.append(a)
        elif m == 'mov' and 'ptr [' in o and ', 0x' in o:
            mm = imm_re.match(o)
            if mm and int(mm.group(3), 16) in VT:
                vt_store.append((a, int(mm.group(3), 16), int(mm.group(2), 16) if mm.group(2) else 0))
    if last <= pos:
        n_undec += 1; last = pos + 1
    pos = last
SSET = set(starts)
ck('S4 指令数 1,392,592（与前几轮同口径）', len(starts) == 1392592, len(starts))
ck('S5 停滞位置 0', n_undec == 0, n_undec)
ck('S6 vtable 装配点（mov [mem], vtable_va）数 > 4000', len(vt_store) > 4000, len(vt_store))

# ---------- A: 槽归属 ----------
SLOT = defaultdict(list)   # func_va -> [(class, slot)]
slot_vals = set()
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        SLOT[x].append((k, i))
        slot_vals.add(x)
        i += 1
ck('S7 distinct vtable 槽值 == 6499（R107 EI4 / R108 同口径）', len(slot_vals) == 6499, len(slot_vals))

# ---------- 复用 R108 的 E 判据与 387 站点（自算，再与 r108f 产物对齐） ----------
D = {}
with open('_r108/branchmap2.bin', 'rb') as f:
    while True:
        hd = f.read(12)
        if len(hd) < 12:
            break
        n, isz, kl = struct.unpack('<III', hd)
        k = f.read(kl).decode()
        arr = []
        import array as _ar
        a2 = _ar.array('I'); a2.frombytes(f.read(n * isz)); arr = list(a2)
        D[k] = arr
CALLT = set(x for x in D['call_t'] if TS <= x < TE)
RETS = sorted(D['rets'])
ck('S8 call 直接目标（.text 内）== 6719，distinct == 6728（含 .text 外目标）',
   len(CALLT) == 6719 and len(set(D['call_t'])) == 6728, (len(CALLT), len(set(D['call_t']))))

def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in RETS:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
ck('S9 HB 硬函数起点 == 17766（R108 同口径）', len(HB) == 17766, len(HB))

IMMPTR = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('jmp', 'call') or (m[0] == 'j' and m != 'jmp'):
            continue
        o2 = re.sub(r'\[[^\]]*\]', ' ', o)
        for tok in o2.replace(',', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
ck('S10 IMMPTR 取地址入口 == 598（R108 同口径）', len(IMMPTR) == 598, len(IMMPTR))
E = sorted(CALLT | slot_vals | IMMPTR | HB)
ck('S11 |E| == union(call 6719, 槽值 6499, IMMPTR 598, HB 17766) = 19581（与 R108 Q1c 报的 19581 一致；'
   '本行原写 21485 是把四者**直接相加**的错算，见自错 E-a2）', len(E) == 19581, len(E))
ESET = set(E)

def owner_of(S, H):
    i = bisect.bisect_right(E, H)
    if i and E[i - 1] >= S:
        return E[i - 1]
    return None

SITES = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2:
                SITES.append((a, int(m2[-1], 16)))
    if last <= pos:
        last = pos + 1
    pos = last
ck('S12 switch 分派站点 == 387 / distinct 表基址 == 369（R108 Q1/Q2 同口径）',
   len(SITES) == 387 and len(set(t for _, t in SITES)) == 369,
   (len(SITES), len(set(t for _, t in SITES))))
CTS = sorted(CALLT)
ROWS = []
for site, tab in SITES:
    i = bisect.bisect_right(CTS, site)
    S = CTS[i - 1] if i and site - CTS[i - 1] <= 0x8000 else None
    O = owner_of(S if S is not None else TS, site)
    ROWS.append({'site': site, 'table': tab, 'S_r107': S, 'owner': O})
NOWN = len(set(r['owner'] for r in ROWS if r['owner']))
ck('S13 owner 去重数 == 277（R108 Q2 同口径，独立复算）', NOWN == 277, NOWN)

# ---------- B: 装配点归属（同一 E 判据：装配指令所属函数） ----------
ST = sorted(vt_store)
CTOR = defaultdict(list)   # func_va -> [(class, disp)]
for a, v, disp in vt_store:
    i = bisect.bisect_right(E, a)
    if i:
        CTOR[E[i - 1]].append((VT[v], disp))
ck('S14 装配点归到 %d 个函数，其中 disp==0（主表）的点 %d 个'
   % (len(CTOR), sum(1 for _, _, d in vt_store if d == 0)),
   len(CTOR) > 800, (len(CTOR), sum(1 for _, _, d in vt_store if d == 0)))

# ---------- 归因 ----------
OWNERS = sorted(set(r['owner'] for r in ROWS if r['owner']))
attrA = {o: SLOT.get(o, []) for o in OWNERS}
attrB = {o: CTOR.get(o, []) for o in OWNERS}
nA = sum(1 for o in OWNERS if attrA[o])
nB = sum(1 for o in OWNERS if attrB[o])
nAB = sum(1 for o in OWNERS if attrA[o] and attrB[o])
nNone = sum(1 for o in OWNERS if not attrA[o] and not attrB[o])
ck('S15 归因覆盖：A(槽) %d / B(装配) %d / A∩B %d / 两者皆无 %d，合计 %d'
   % (nA, nB, nAB, nNone, len(OWNERS)), nA + nB - nAB + nNone == len(OWNERS), (nA, nB, nAB, nNone))
# 口径修正（E-a3）：原断言写「须 ≥150」是把**预期**当断言。实测只有 82/277=29.6%，
# 即「槽值 + 装配点」两条路径**不足以**把 R108 EJ9① 的缺口补上；这是本轮最硬的负结论，如实保留。
ck('S16 覆盖 = %d/%d = %.1f%%：**未达** 150 的目标 ⇒ 槽值/装配点两条路不能补上 R108 EJ9① 的缺口'
   % (nA + nB - nAB, len(OWNERS), 100.0 * (nA + nB - nAB) / len(OWNERS)),
   nA + nB - nAB < 150, (nA + nB - nAB, len(OWNERS)))

# ---------- D: 随机反控 ----------
import random
random.seed(10911)
rnd = random.sample(starts, 20000)
dA = sum(1 for a in rnd if a in SLOT)
dB = sum(1 for a in rnd if a in CTOR)
dAny = sum(1 for a in rnd if a in SLOT or a in CTOR)
ck('S17 反控：随机 20000 个指令起点命中 A %d (%.2f%%) / B %d (%.2f%%) / 任一 %d (%.2f%%)'
   % (dA, 100.0 * dA / 20000, dB, 100.0 * dB / 20000, dAny, 100.0 * dAny / 20000),
   dAny < 1000, (dA, dB, dAny))
enrich = (100.0 * (nA + nB - nAB) / len(OWNERS)) / (100.0 * dAny / 20000)
ck('S18 富集倍数 = %.1f 倍（owner 组 %.1f%% vs 随机 %.3f%%）'
   % (enrich, 100.0 * (nA + nB - nAB) / len(OWNERS), 100.0 * dAny / 20000), enrich > 10, round(enrich, 1))

out = {
 'checks': checks,
 'n_owners': len(OWNERS), 'nA': nA, 'nB': nB, 'nAB': nAB, 'nNone': nNone,
 'negctl': {'n': 20000, 'A': dA, 'B': dB, 'any': dAny}, 'enrich': round(enrich, 2),
 'owners': [{'owner': hex(o),
             'A': [[k, s] for k, s in attrA[o]],
             'B': sorted(set(d for _, d in attrB[o])),
             'B_cls': sorted(set(k for k, _ in attrB[o]))} for o in OWNERS],
 'sites_owner': [{'site': hex(r['site']), 'table': hex(r['table']),
                  'S_r107': hex(r['S_r107']) if r['S_r107'] else None,
                  'owner': hex(r['owner']) if r['owner'] else None} for r in ROWS],
 'vt_store_n': len(vt_store),
}
json.dump(out, open('_r109/r109a_attr.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
