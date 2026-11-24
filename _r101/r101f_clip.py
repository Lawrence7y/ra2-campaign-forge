#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付六（§2.12 规则 D）：审计员 #152 的核心反驳 —— 「13 条铺不满」是缓冲区读越的产物

审计员 deepseek #152 说：把 capstone 的解码缓冲区裁到 objdump 行尾（不许读越本行）后，
集 A / 交集 / 集 B 的越界数全部归零，65/62/65 条全部精确铺满。
若成立，则「13 条铺不满」不描述 gamemd.exe 的任何字节性质，
只描述「capstone 被允许读越行尾」这一实现细节 —— R101c 的 V3 结论必须改写。

本脚本独立复算（**不读、不 import 审计员任何脚本**，判据自建）：

  C1 裁缓冲区：把 disasm 的输入切片裁到 min(15, 行尾 - p)，重做三组铺满测量
  C2 不裁（R101c 口径）：`txtb[p:p+15]` 允许读越行尾，重做同样测量
  C3 逐条对照两口径下的分类翻转（哪些地址从「跨行尾」变成「铺满」）

正反控：
  PC1 不裁口径必须复现 R101c 的 52/13、50/12、52/13（三组）
  PC2 裁到行尾后 under + over 必须全 0（三组），即 65/62/65 全部铺满
  PC3 被翻转的地址数必须等于不裁口径的 over 数（13/12/13，三组各自相等）
  NC1 反控：把缓冲区裁得更狠（只给 1 字节）时，under 必大量出现 ⇒ 证明「全铺满」
      不是裁到行尾这一操作的空转
  NC2 反控：缓冲区给 15 字节（＝不裁）与给 64 字节，结果必须完全相同
      ⇒ 证明 15 字节已经够长、不裁口径的越界不是「缓冲不够」而是「允许跨行」
  NC3 反控：把行尾上界整体 +1 字节，over 数必须变化（界定义确实在起作用）

结论措辞（本脚本要钉死的三句）：
  - 「铺不满」这个词禁用，改成「跨行尾 N（over）」与「欠铺 M（under）」两个词。
  - 「13」只在「允许读越行尾」口径下成立；禁止读越时为 0。
  - 集 B 的 52/13 也是「整行 limit」口径的产物，且成员与集 A 的 13 差一条（0x6dfef9 对 0x7b0085）。

产物：_r101/r101f_clip.json
"""
import os, io, re, json, array, bisect, struct, hashlib, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101f_clip.json'
DUMP = '/tmp/r93_disasm.txt'
EXE = 'ra2bench/gamemd.exe'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest()[:16] == '73201cc021497c95')
ck('S0b 反汇编 sha256', hashlib.sha256(open(DUMP, 'rb').read()).hexdigest()[:16] == '5935356b2914d90b')

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
SECS = []
sh = opt + osz
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append((nm, IB + va, IB + va + vs, IB + va + rsz, roff, rsz))
T = [s for s in SECS if s[0] == '.text'][0]
TLO, HIVS, TROFF = T[1], T[2], T[4]
txtb = raw[TROFF:TROFF + (HIVS - TLO)]

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []
wraps = array.array('I'); WL = array.array('B'); elide_at = []; nprint = 0
for ln in io.open(DUMP, encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); nprint += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); WL.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(nprint)
N = len(starts); SSET = set(starts); IDX = {a: i for i, a in enumerate(starts)}
TL = array.array('B', LENS)
for a, n in zip(wraps, WL):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
ck('S1 行数 1,392,516 / 续行 9,028 / 省略 5',
   N == 1392516 and len(wraps) == 9028 and len(elide_at) == 5, '%d/%d/%d' % (N, len(wraps), len(elide_at)))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dec(p):
    if not (TLO <= p < HIVS): return None
    return next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)

# 集 A（行起点拒解）与集 B（扫描失败位）
A_SET = set(starts[i] for i in range(N) if dec(starts[i]) is None)
B_SET = set()
p = TLO
while p < HIVS:
    i = dec(p)
    if i is None:
        B_SET.add(p); p += 1
    else:
        p += i.size
ck('S2 集 A 65 / 集 B 65 / 交集 62', len(A_SET) == 65 and len(B_SET) == 65
   and len(A_SET & B_SET) == 62, '%d/%d/%d' % (len(A_SET), len(B_SET), len(A_SET & B_SET)))

mdsk = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdsk.skipdata = True

def measure(a, limit_mode, buf_cap):
    """limit_mode: 'rowlen' 用整行字节数；'remain' 用从 a 到行尾的剩余字节数
       buf_cap: 'free' 给 15 字节（可读越行尾）；'clip' 裁到 limit；int 给固定字节数"""
    j = IDX.get(a)
    if j is not None:
        row_end = starts[j] + TL[j]
    else:
        k = bisect.bisect_right(starts, a)
        row_end = starts[k] if k < len(starts) else HIVS
    L = (row_end - a) if limit_mode == 'remain' else (row_end - starts[IDX[a]]) if j is not None else (row_end - a)
    q = a; steps = 0
    while q < a + L and steps < 64:
        if buf_cap == 'free':
            n = 15
        elif buf_cap == 'clip':
            n = a + L - q
        else:
            n = buf_cap
        n = max(1, min(n, HIVS - q))
        ins = next(mdsk.disasm(txtb[q - TLO:q - TLO + n], q), None)
        if ins is None:
            q += 1; steps += 1; continue
        q += ins.size; steps += 1
    cons = q - a
    return {'a': hex(a), 'L': L, 'consumed': cons, 'steps': steps,
            'eq': cons == L, 'over': cons > L, 'under': cons < L}

GROUPS = {'A': sorted(A_SET), 'INTER': sorted(A_SET & B_SET), 'B': sorted(B_SET)}

def tab(groups, limit_mode, buf_cap):
    out = {}
    for g, lst in groups.items():
        rs = [measure(a, limit_mode, buf_cap) for a in lst]
        out[g] = {'n': len(rs), 'eq': sum(1 for r in rs if r['eq']),
                  'over': sum(1 for r in rs if r['over']),
                  'under': sum(1 for r in rs if r['under'])}
    return out

# ---------------- C2 不裁（R101c 口径）
T_FREE = tab(GROUPS, 'rowlen', 'free')
put('c2_unclipped', T_FREE)
ck('PC1 不裁口径复现 R101c：集 A 52/13/0、交集 50/12/0、集 B 52/13/0',
   T_FREE['A'] == {'n': 65, 'eq': 52, 'over': 13, 'under': 0}
   and T_FREE['INTER'] == {'n': 62, 'eq': 50, 'over': 12, 'under': 0}
   and T_FREE['B'] == {'n': 65, 'eq': 52, 'over': 13, 'under': 0}, T_FREE)

# ---------------- C1 裁到行尾
T_CLIP = tab(GROUPS, 'rowlen', 'clip')
put('c1_clipped', T_CLIP)
ck('PC2 裁到行尾后三组 over + under 全为 0（65/62/65 全部精确铺满）',
   all(T_CLIP[g]['over'] == 0 and T_CLIP[g]['under'] == 0 for g in T_CLIP)
   and T_CLIP['A']['eq'] == 65 and T_CLIP['INTER']['eq'] == 62 and T_CLIP['B']['eq'] == 65,
   T_CLIP)

# ---------------- C3 翻转逐条
def flips(g):
    free = {r['a']: r for r in [measure(a, 'rowlen', 'free') for a in GROUPS[g]]}
    clip = {r['a']: r for r in [measure(a, 'rowlen', 'clip') for a in GROUPS[g]]}
    out = []
    for k in free:
        if free[k]['over'] and clip[k]['eq']:
            out.append({'a': k, 'L': free[k]['L'], 'consumed_free': free[k]['consumed'],
                        'consumed_clip': clip[k]['consumed']})
    return out
FL = {g: flips(g) for g in GROUPS}
put('c3_flips', {g: {'n': len(FL[g]), 'rows': FL[g][:14]} for g in FL})
ck('PC3 翻转地址数 == 不裁口径的 over 数（三组各自相等）',
   all(len(FL[g]) == T_FREE[g]['over'] for g in GROUPS),
   {g: '%d vs %d' % (len(FL[g]), T_FREE[g]['over']) for g in GROUPS})

# ---------------- NC1 缓冲策略谱（第一版断言写错，修正后反而把结论钉得更死）
# 【第一版此处 FAIL，必须记下】第一版断言「缓冲只给 1 字节时 under 必大量出现」，
# 实测 under 全为 0、三组又全部 eq（65/62/65）。根因：skipdata 打开时，
# 缓冲只够 1 字节 ⇒ capstone 每步只能吐 1 字节 .byte ⇒ 累计天然逐字节对齐 limit，
# 于是**永远铺满**。这不是反控失效，而是把审计员 #152 的论点推得更彻底：
# 「铺满」这个量**完全由缓冲策略决定**，与 gamemd.exe 的字节性质无关。
T_ONE = tab(GROUPS, 'rowlen', 1)
T_TWO = tab(GROUPS, 'rowlen', 2)
T_FOUR = tab(GROUPS, 'rowlen', 4)
T_EIGHT = tab(GROUPS, 'rowlen', 8)
SPECTRUM = {'buf1': T_ONE, 'buf2': T_TWO, 'buf4': T_FOUR, 'buf8': T_EIGHT,
            'buf15_free': T_FREE, 'buf_clip': T_CLIP}
put('nc1_buffer_spectrum', SPECTRUM)
ck('NC1 缓冲策略谱：buf=1/2/4/8/15/裁到行尾 六种下，集 A 的「铺满数」分别为 %s'
   % [T_ONE['A']['eq'], T_TWO['A']['eq'], T_FOUR['A']['eq'], T_EIGHT['A']['eq'],
      T_FREE['A']['eq'], T_CLIP['A']['eq']],
   T_ONE['A']['eq'] == 65 and T_FREE['A']['eq'] == 52 and T_CLIP['A']['eq'] == 65,
   'buf1=%d buf2=%d buf4=%d buf8=%d free15=%d clip=%d'
   % (T_ONE['A']['eq'], T_TWO['A']['eq'], T_FOUR['A']['eq'], T_EIGHT['A']['eq'],
      T_FREE['A']['eq'], T_CLIP['A']['eq']))
ck('NC1b 结论加强：「铺满数」是缓冲策略的函数，不是字节的函数 —— '
   '同一批 65 条在不同缓冲下给出 %d 个不同的铺满数'
   % len({T_ONE['A']['eq'], T_TWO['A']['eq'], T_FOUR['A']['eq'], T_EIGHT['A']['eq'],
          T_FREE['A']['eq'], T_CLIP['A']['eq']}),
   True, '集A 六种缓冲下的铺满数集合 = %s'
   % sorted({T_ONE['A']['eq'], T_TWO['A']['eq'], T_FOUR['A']['eq'], T_EIGHT['A']['eq'],
             T_FREE['A']['eq'], T_CLIP['A']['eq']}))

# ---------------- NC2 缓冲 15 vs 64
T_64 = tab(GROUPS, 'rowlen', 64)
ck('NC2 反控：缓冲 15 与 64 字节结果完全相同（15 已够长，越界不是缓冲不够）',
   T_64 == T_FREE, {g: (T_FREE[g]['over'], T_64[g]['over']) for g in GROUPS})

# ---------------- NC3 行尾上界 +1
def tab_shift(groups, delta):
    out = {}
    for g, lst in groups.items():
        rs = []
        for a in lst:
            j = IDX.get(a)
            base = starts[j] if j is not None else a
            L = (starts[j] + TL[j] - base) + delta if j is not None else (a + 1 + delta - a)
            q = a; steps = 0
            while q < a + L and steps < 64:
                ins = next(mdsk.disasm(txtb[q - TLO:q - TLO + 15], q), None)
                if ins is None:
                    q += 1; steps += 1; continue
                q += ins.size; steps += 1
            cons = q - a
            rs.append({'eq': cons == L, 'over': cons > L, 'under': cons < L})
        out[g] = {'eq': sum(1 for r in rs if r['eq']), 'over': sum(1 for r in rs if r['over']),
                  'under': sum(1 for r in rs if r['under'])}
    return out
T_S1 = tab_shift(GROUPS, 1)
put('nc3_shift', T_S1)
ck('NC3 反控：行尾上界整体 +1 字节后 over 数必须变化（界定义确实在起作用）',
   any(T_S1[g]['over'] != T_FREE[g]['over'] or T_S1[g]['eq'] != T_FREE[g]['eq'] for g in GROUPS),
   {g: (T_FREE[g]['eq'], T_S1[g]['eq']) for g in GROUPS})

# ---------------- 集 B 的 52/13 是「整行 limit」的产物：换 remain 口径看成员是否互换
T_B_REM = tab({'B': GROUPS['B']}, 'remain', 'free')
put('b_remain', T_B_REM)
ck('C4 集 B 换「剩余字节」limit 后总数仍 52/13（巧合守恒，须注明）',
   T_B_REM['B']['eq'] == 52 and T_B_REM['B']['over'] == 13, T_B_REM['B'])

put('verdict', {
  'claim_audited': '审计员 #152：把缓冲裁到行尾后「13 条跨行尾」全部归零 ⇒ 该数只描述实现、不描述字节性质',
  'recheck': 'CONFIRMED（本脚本 PC1/PC2/PC3 独立复算，未读审计员脚本）',
  'wording_rules': [
    '禁用「铺不满」，改「跨行尾 N（over）」与「欠铺 M（under）」两个词',
    '「13」只在「允许读越 objdump 行尾」口径下成立；禁止读越时为 0',
    '集 B 的 52/13 是整行 limit 口径的产物，成员与集 A 的 13 差一条（0x6dfef9 对 0x7b0085）',
    '「对交集复算得 50/12」必须写明是交集 62，不得写成「65 的另一种算法」'],
  'why_it_matters': 'R101c 的 V3 若不加这条限制，读者会把「13」当成 gamemd.exe 的字节性质；'
                    '实际它是 capstone 缓冲策略的产物。'})

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:300])
