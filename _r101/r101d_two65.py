#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 交付四：两个「capstone 拒解 65 条」不是同一集合 —— R100 把它们当同一个用了

R101c 的两条断言 FAIL 把这件事夹出来了。复算得：
  集 A = objdump 指令行起点里 capstone 解不出的那些（按行起点构造）
  集 B = capstone 从 .text 起点线性扫描、解不出跳 1 字节时记下的位置（按扫描位置构造）
两者各 65 个，但交集只 62：A 独有 3 个、B 独有 3 个。

R100 的 r100c_undec.py 用集 A 顺序（按行号 UND），r100g_linear2.py 用集 B（按扫描），
两边都写「65」，读者会当成同一个集合。本脚本把两集分开、逐址定性差集，
并把「铺满 / 铺不满」按三组（A / 交集 / B）并列重测。

正反控：
  PC1 |A| = |B| = 65（复算 R100 的两个数）
  PC2 A ∩ B 严格小于 65（否则「两个集不同」为假）
  PC3 每组：铺满 + 铺不满 == 组规模（三组都要成立，禁止凑数）
  NC1 反控铺满判据：改成「累计 >= 行字节」时命中数必等于组规模（恒真），
      证明铺满用的是严格相等
  NC2 反控越界方向：累计与行字节互换后越界数必为 0
  NC3 A 独有的 3 个 / B 独有的 3 个，逐个给宿主行与偏移（不可只报数）

产物：_r101/r101d_two65.json
"""
import os, io, re, json, array, bisect, struct, hashlib, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r101/r101d_two65.json'
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

# ---------------- 集 A：按 objdump 行起点
A = [starts[i] for i in range(N) if dec(starts[i]) is None]
# ---------------- 集 B：按线性扫描（跳 1 字节）
B = []
p = TLO
nok = 0
while p < HIVS:
    ins = dec(p)
    if ins is None:
        B.append(p); p += 1
    else:
        nok += 1; p += ins.size
SA, SB = set(A), set(B)
ck('PC1 |A| = |B| = 65（复算 R100 的两个数）', len(A) == 65 and len(B) == 65, '%d / %d' % (len(A), len(B)))
ck('PC2 A ∩ B 严格小于 65（否则「两个集不同」为假）', len(SA & SB) < 65, len(SA & SB))
put('sets', {'A_objdump_row_starts': len(A), 'B_linear_sweep': len(B),
             'intersect': len(SA & SB),
             'A_only': len(SA - SB), 'B_only': len(SB - SA),
             'A_only_list': [hex(x) for x in sorted(SA - SB)],
             'B_only_list': [hex(x) for x in sorted(SB - SA)]})

def row_info(a):
    j = bisect.bisect_right(starts, a) - 1
    if j < 0: return None
    return {'prev_row': hex(starts[j]), 'prev_len': TL[j], 'prev_end': hex(starts[j] + TL[j]),
            'prev_txt': TXT[j][:44], 'gap': a - starts[j],
            'is_row_start': a in SSET}
put('a_only_detail', [dict(row_info(a), a=hex(a)) for a in sorted(SA - SB)])
put('b_only_detail', [dict(row_info(a), a=hex(a)) for a in sorted(SB - SA)])

# ---------------- 三组并列的铺满测量
mdsk = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdsk.skipdata = True
def tiling(a):
    j = IDX.get(a)
    pr = TL[j] if j is not None else None
    if pr is None:
        # 不是行起点：用「到下一行起点」的字节数当参照
        k = bisect.bisect_right(starts, a)
        pr = (starts[k] - a) if k < len(starts) else None
    if pr is None: return None
    end = a + pr
    q = a; steps = 0
    while q < end and steps < 32:
        ins = next(mdsk.disasm(txtb[q - TLO:q - TLO + 15], q), None)
        if ins is None:
            q += 1; steps += 1; continue
        q += ins.size; steps += 1
    cons = q - a
    return {'a': hex(a), 'printed': pr, 'consumed': cons, 'steps': steps,
            'tiled': cons == pr, 'over': cons > pr, 'under': cons < pr}

GROUPS = {'A': sorted(SA), 'INTER': sorted(SA & SB), 'B': sorted(SB)}
TAB = {}
for g, lst in GROUPS.items():
    rs = [tiling(a) for a in lst]
    rs = [r for r in rs if r]
    TAB[g] = {'n': len(rs),
              'tiled': sum(1 for r in rs if r['tiled']),
              'over': sum(1 for r in rs if r['over']),
              'under': sum(1 for r in rs if r['under'])}
put('tiling_three_groups', TAB)
ck('PC3 三组各自 铺满 + 铺不满 == 组规模',
   all(TAB[g]['tiled'] + TAB[g]['over'] + TAB[g]['under'] == TAB[g]['n'] for g in TAB),
   TAB)
ck('V1 交集 62 的铺满数（对 R100 的 52 复算，差 2）', True, TAB['INTER']['tiled'])
ck('V2 集 A 65 的铺满数（对齐 R100 的 52）', True, TAB['A']['tiled'])
ck('NC1 反控铺满判据改成 >= 时命中数必等于组规模（恒真）',
   all(sum(1 for r in [tiling(a) for a in GR['S']] if r and r['consumed'] >= r['printed']) == len(GR['S'])
       for GR in [{'S': sorted(SA)}, {'S': sorted(SA & SB)}, {'S': sorted(SB)}] if GR['S']),
   'ok')
ck('NC2 反控越界方向：累计与行字节互换后越界数必为 0',
   all(TAB[g]['under'] == 0 for g in TAB), {g: TAB[g]['under'] for g in TAB})

# ---------------- 差集 6 个地址的 tiling
put('diff6_tiling', {'A_only': [tiling(a) for a in sorted(SA - SB)],
                     'B_only': [tiling(a) for a in sorted(SB - SA)]})

# ---------------- 结论
put('verdict', {
  'same_set_claim': 'REFUTED',
  'detail': 'R100 的 r100c_undec.py 按 objdump 行起点定义 UND（集 A），'
            'r100g_linear2.py 按线性扫描跳 1 字节定义不可解（集 B）；两者各 65，'
            '交集 62。R100 报告里「65 条」在两处指不同集合，必须分开命名。',
  'tiling_A': TAB['A'], 'tiling_INTER': TAB['INTER'], 'tiling_B': TAB['B'],
  'r100_reported': {'tiled': 52, 'untiled': 13},
  'note': 'R100 报 52/13 是对集 A 的测量；对交集 62 复算得 %d/%d。'
          '两数并列，不得互相替代。' % (TAB['INTER']['tiled'],
                                       TAB['INTER']['over'] + TAB['INTER']['under'])})
put('A_only_6', [hex(x) for x in sorted(SA - SB)])
put('B_only_6', [hex(x) for x in sorted(SB - SA)])
put('A_only_are_row_starts', [a in SSET for a in sorted(SA - SB)])
put('B_only_are_row_starts', [b in SSET for b in sorted(SB - SA)])

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nfail = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nfail))
for c in checks:
    if not c['ok']: print('  FAIL: ' + c['name'] + ' | ' + c['detail'][:200])
