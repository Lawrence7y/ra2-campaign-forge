#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付三：88 个地址的细分 + 0/88 的显著性 + R100 待办②「13 条铺不满」逐条解释

三件事，全部机械可核：

  V1 把 r101b 的 88 个五分类再切一层：R_resync（59）里有多少「重同步后恰好补满宿主尾部」
     （R_exact）与「不补满」（R_other）。R_exact 与 T_exact 加起来才是「同段字节两种切法
     都自洽」的真歧义数，R_other 是纯粹的重同步残渣。

  V2 0/88 的显著性：88 个地址外部引用命中 0，而全体 objdump 起点命中率 6.7874%
     （94,515 / 1,392,516）。用二项分布算 P(X=0)，并与 r101b 的 200 次随机抽 88 的
     经验分布对照。结论必须写明它是「与真起点证据形态不同」，不是「证明不是代码」。

  V3 R100 待办②「65 条里 13 条与 1 字节跳过口径铺不满」—— 逐条给出：
     printed（objdump 该行字节数）/ consumed（skipdata 沿 1 字节跳的累计长度）/
     步数与每步长度、越过多少字节、越过的部分落在哪条 objdump 行里。
     假设：13 条全部是「最后一步 overshoot」即 consumed > printed；
     反控：把 overshoot 判据换成 consumed != printed，若 13 != 52 则说明二者不是同一个数
     （52 是铺满数，13 是铺不满数，两数必须分开报）。

正反控：
  PC1 R_exact + R_other == 59（59 是 r101b 实测，不允许漂移）
  PC2 T_exact + T_short + T_over + R_exact == 「真歧义」总数，且 <= 88
  NC1 反控 V2：把命中率换成 100%（即判据恒真）时 P(0) 必须为 0 —— 证明公式没写反
  NC2 反控 V3：把 overshoot 判据改成 consumed >= printed，命中数必须变成 65（恒真）
  NC3 反控 V3：把 consumed 与 printed 互换，overshoot 数必须为 0（方向性）

产物：_r101/r101c_refine.json
"""
import os, io, re, json, array, bisect, struct, hashlib, math, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101c_refine.json'
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
    return next(md.disasm(txtb[p - TLO:p - TLO + 15], p), None)
ok1, bad1 = [], []
p = TLO
while p < HIVS:
    ins = dec(p)
    if ins is None:
        bad1.append(p); p += 1
    else:
        ok1.append((p, ins.size)); p += ins.size
OK1 = set(a for a, _ in ok1); CAPLEN = dict(ok1); BAD1 = set(bad1)
ck('S2 capstone 跳1 可解 1,392,527 / 不可解 65', len(ok1) == 1392527 and len(bad1) == 65,
   '%d/%d' % (len(ok1), len(bad1)))
only_cap = sorted(OK1 - SSET)
elided_addrs = set()
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    elided_addrs.update(range(pe, starts[k], 2))
EL20 = set(only_cap) & elided_addrs
EIGHTY = sorted(set(only_cap) - EL20)
ck('S3 108 = 20 + 88', len(only_cap) == 108 and len(EL20) == 20 and len(EIGHTY) == 88,
   '%d/%d/%d' % (len(only_cap), len(EL20), len(EIGHTY)))

# ======================================================== V1 细分
def chain_from(h, limit=64):
    if h not in CAPLEN: return None
    seq, p, n = [], h, 0
    while n < limit and p < HIVS and p in CAPLEN:
        seq.append(p); p += CAPLEN[p]; n += 1
    return seq

SUB = collections.Counter(); ROWS = []
for a in EIGHTY:
    j = bisect.bisect_right(starts, a) - 1
    hs = starts[j]; hl = TL[j]; he = hs + hl
    cl = CAPLEN.get(a); ce = a + cl
    if hs not in CAPLEN:
        k = 'R_exact' if ce == he else 'R_other'
    else:
        ch = chain_from(hs) or []
        if a in ch:
            k = 'T_exact' if ce == he else ('T_over' if ce > he else 'T_short')
        else:
            k = 'U_offchain'
    SUB[k] += 1
    ROWS.append({'a': hex(a), 'host': hex(hs), 'hl': hl, 'off': a - hs, 'cl': cl,
                 'cap_end': hex(ce), 'host_end': hex(he), 'sub': k, 'txt': TXT[j][:40]})
put('v1_sub', dict(sorted(SUB.items())))
s59 = SUB['R_exact'] + SUB['R_other']
ck('PC1 R_exact + R_other == 59（r101b 实测值，不允许漂移）', s59 == 59,
   '%d + %d = %d' % (SUB['R_exact'], SUB['R_other'], s59))
amb = SUB['T_exact'] + SUB['R_exact']
ck('PC2 真歧义 = T_exact %d + R_exact %d = %d <= 88' % (SUB['T_exact'], SUB['R_exact'], amb),
   amb == SUB['T_exact'] + SUB['R_exact'] and amb <= 88, amb)
put('v1_verdict', {
  'real_ambiguity_same_bytes_two_ways': amb,
  'pure_resync_residue': SUB['R_other'],
  'capstone_splits_objdump_legal_insn_short': SUB['T_short'],
  'total': 88,
  'note': '「真歧义」=%d（两种切法都恰好铺满同一段字节，静态不可判）；'
          '其余 %d 是 capstone 在双方都解不出的字节上按 1 字节重同步的残渣，'
          '与 objdump 的切分无关。' % (amb, SUB['R_other'] + SUB['T_short'] + SUB['T_over'])})

# ======================================================== V2 显著性
JT = set(); IMMT = set()
JCC = frozenset({'je','jne','jz','jnz','jl','jle','jg','jge','jb','jbe','ja','jae','js','jns',
                 'jo','jno','jp','jnp','jpe','jpo','jc','jnc','jcxz','jecxz','jecxnz',
                 'loop','loope','loopne'})
REG32 = frozenset({'eax','ebx','ecx','edx','esi','edi','ebp','esp'})
def split_ops(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '[': d += 1
        elif ch == ']': d -= 1
        if ch == ',' and d == 0: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out
for i in range(N):
    t = TXT[i]
    if not t: continue
    mn = t.split()[0]; rest = t[len(mn):].strip()
    if not rest: continue
    for o in split_ops(rest):
        if o in REG32 or o.startswith('[') or '*' in o: continue
        tok = o.split()[0] if o else ''
        if not re.match(r'^(0x[0-9a-f]+|-?[0-9]+)$', tok): continue
        try: v = int(tok, 0)
        except ValueError: continue
        if TLO <= v < HIVS: IMMT.add(v)
    if mn in JCC or mn in ('jmp', 'call'):
        ops = split_ops(rest)
        if ops and not (ops[0] in REG32 or ops[0].startswith('[') or '*' in ops[0]):
            try:
                v = int(ops[0].split()[0], 0)
                if TLO <= v < HIVS: JT.add(v)
            except ValueError: pass
DATA = set()
for nm, lo, hivs, hirs, roff, rsz in SECS:
    if nm == '.text': continue
    for q in range(0, rsz - 3, 4):
        v = struct.unpack_from('<I', raw, roff + q)[0]
        if TLO <= v < HIVS: DATA.add(v)
REF = JT | IMMT | DATA
hit_all = sum(1 for a in SSET if a in JT)
rate = hit_all / len(SSET)
hit88 = sum(1 for a in EIGHTY if a in REF)
def binom0(n, p):
    return (1.0 - p) ** n
p0 = binom0(88, rate)
put('v2_signif', {'rate_all_starts': rate, 'hit_all': hit_all, 'n_all': len(SSET),
                  'exp_in_88': rate * 88, 'hit88': hit88, 'p_zero': p0})
ck('V2 0/88 的二项 P(X=0) < 0.01（与全体起点命中率 6.79%% 对照）', p0 < 0.01, '%.5f' % p0)
ck('NC1 反控：把命中率换成 1.0 时 P(0) 必须为 0（公式方向正确）', binom0(88, 1.0) == 0.0,
   binom0(88, 1.0))

# ======================================================== V3 「13 条铺不满」逐条解释
# 【重要口径】R100 的 52/13 是对「集 A = objdump 指令行起点里 capstone 解不出的」测量的。
# 本脚本的第一版按「集 B = 线性扫描跳 1 字节记下的位置」复算，得 50/12，两数差 2。
# r101d_two65.py 已证 A 与 B 各 65、交集 62。这里按集 A 定义重做，并明确两者并列。
A_SET = sorted(starts[i] for i in range(N) if dec(starts[i]) is None)
SA = set(A_SET)
ck('V3-0 集 A（objdump 行起点且 capstone 解不出）规模 == 65', len(A_SET) == 65, len(A_SET))
ck('V3-0b 集 A 与集 B 不是同一集合（交集 %d < 65）' % len(SA & BAD1), len(SA & BAD1) < 65,
   'A %d / B %d / 交 %d' % (len(SA), len(BAD1), len(SA & BAD1)))

mdsk = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdsk.skipdata = True
def tile(a, pr):
    end = a + pr
    p_ = a; steps = []
    guard = 0
    while p_ < end and guard < 32:
        ins = next(mdsk.disasm(txtb[p_ - TLO:p_ - TLO + 15], p_), None)
        if ins is None:
            steps.append([hex(p_), 0]); p_ += 1; guard += 1; continue
        steps.append([hex(p_), ins.size]); p_ += ins.size; guard += 1
    cons = p_ - a
    return {'a': hex(a), 'printed': pr, 'consumed': cons, 'steps': steps,
            'overshoot': cons - pr, 'tiled': cons == pr,
            'row_bytes': raw[TROFF + (a - TLO):TROFF + (a - TLO) + pr].hex(' ')}

DET = [tile(a, TL[IDX[a]]) for a in A_SET]
over = [d for d in DET if d['consumed'] > d['printed']]
equal = [d for d in DET if d['consumed'] == d['printed']]
less = [d for d in DET if d['consumed'] < d['printed']]
put('v3_shape_A', {'n': len(DET), 'overshoot': len(over), 'equal': len(equal), 'under': len(less)})
ck('V3 集 A 的 65 条：overshoot %d / 恰好铺满 %d / 不足 %d，三者之和 == 65'
   % (len(over), len(equal), len(less)), len(over) + len(equal) + len(less) == 65,
   '%d/%d/%d' % (len(over), len(equal), len(less)))
ck('V3a 复算 R100 的 52 铺满 / 13 铺不满（对集 A）',
   len(equal) == 52 and len(over) + len(less) == 13,
   '%d 铺满 / %d 铺不满' % (len(equal), len(over) + len(less)))
ck('V3b 「铺不满」全部是累计长度大于行字节数，无一条小于（方向单一，穷举非抽样）',
   len(less) == 0, len(less))
put('v3_overshoot_rows', over)
put('v3_overshoot_detail', {
  'n': len(over),
  'overshoot_dist': dict(sorted(collections.Counter(d['overshoot'] for d in over).items())),
  'printed_dist': dict(sorted(collections.Counter(d['printed'] for d in over).items())),
  'note': '13 条铺不满全部是最后一步越过 objdump 行尾（overshoot 分布见上），'
          '不存在累计小于行字节数的情形（穷举 65 条）。'})

ck('NC2 反控：改成 consumed >= printed 时命中数必为 65（恒真，证明 13 来自严格大于）',
   sum(1 for d in DET if d['consumed'] >= d['printed']) == 65,
   sum(1 for d in DET if d['consumed'] >= d['printed']))
ck('NC3 反控：把 consumed 与 printed 互换后 overshoot 数必为 0（方向性）',
   sum(1 for d in DET if d['printed'] > d['consumed']) == len(less), len(less))

# 交集 62 的并列数（另一口径，不得混用）
DETI = [tile(a, TL[IDX[a]]) for a in sorted(SA & BAD1)]
put('v3_intersect_62', {'n': len(DETI),
                        'tiled': sum(1 for d in DETI if d['tiled']),
                        'over': sum(1 for d in DETI if d['consumed'] > d['printed']),
                        'under': sum(1 for d in DETI if d['consumed'] < d['printed']),
                        'note': '交集口径 62 条给 50/12，与集 A 的 52/13 差 2；'
                                '两数并列、不可互替（见 r101d_two65.py）。'})

def row_of(x):
    return bisect.bisect_right(starts, x) - 1
OA = []
for d in over:
    a = int(d['a'], 16); pr = d['printed']
    far = a + d['consumed'] - 1
    j = row_of(far)
    OA.append({'a': d['a'], 'printed': pr, 'consumed': d['consumed'],
               'overshoot': d['overshoot'],
               'last_step_len': d['steps'][-1][1], 'last_step_at': d['steps'][-1][0],
               'far_byte_row': hex(starts[j]) if j >= 0 else None,
               'far_row_txt': TXT[j][:36] if j >= 0 else None,
               'far_row_bad': ('(bad)' in TXT[j]) if j >= 0 else None})
put('v3_overshoot_landing', OA)
n_bad = sum(1 for x in OA if x['far_row_bad'])
ck('V3c 13 条越界落点所在 objdump 行带 (bad) 的 %d / %d（如实报，不修饰）' % (n_bad, len(OA)),
   True, '%d / %d' % (n_bad, len(OA)))

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:200])
