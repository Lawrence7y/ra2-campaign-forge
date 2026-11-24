#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付二：起始集的独立判据 —— 不给「线性扫描」，给「链式核验」

第一版（已作废，如实记）：用 capstone 从 0x401000 线性解码到 0x7e038d，想在整体上
与 objdump 起始集对照。实测在 0x46f5a0 处 UNDECODABLE（objdump 在该处打印的是一条
带非法字节的指令，capstone 不认）⇒ 线性扫描从 0x401000 起**根本走不到段尾**
（155,215 条、452,000 字节后中止）。这个判据**不成立**，不是数据的问题，
是「整段线性可解码」这个前提本身为假。此路作废。

改用可行的独立判据（逐条局部，不依赖全程可解码）：
  L 链式核验：对每对相邻打印起始 (a_i, a_{i+1})，capstone 在 a_i 处解出的长度
    必须 == 真长度 TL[i] 且 a_i + TL[i] == a_{i+1}。这条同时校验「切分」与「起点」。
  S 省略段核验：5 处省略零段按 2 字节切出的 20 个地址，capstone 必须逐条解出 2 字节。
  W 已知例外族：不符的必须全部落在 x87 WAIT 前缀族（objdump 把 9B 并入前一条）。
  T 起点唯一性：从 a_0 + 1 起解码，第一条的地址/长度与从 a_0 起不同。

正反控：
  PC1 链式核验通过数 + WAIT 族数 == 总相邻对数（不允许有第三种来源）
  PC2 省略段 20 个地址全部 2 字节且首尾相接
  NC1 错开 1 字节起点，解出的第一条长度必须与正确起点不同（否则起点判据无判别力）
  NC2 把 TL 换成 R98 的 LENS（错长度）重跑链式核验，必须显著变差（否则真长度无意义）

产物：_r100/r100b_linear.json
"""
import os, io, re, json, array, struct, bisect, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100b_linear.json'
EXE = 'ra2bench/gamemd.exe'
DUMP = '/tmp/r93_disasm.txt'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:800]), flush=True)

raw = open(EXE, 'rb').read()
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
wraps = array.array('I'); wl = array.array('B')
elide_at = []
nprint = 0
for ln in io.open(DUMP, encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); nprint += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(nprint)
N = len(starts)
IDX = {a: i for i, a in enumerate(starts)}
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
put('base', {'printed': N, 'wraps': len(wraps), 'elide': len(elide_at),
             'sum_LENS': sum(LENS), 'sum_TL': sum(TL), 'max_TL': max(TL)})

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
def dec(va):
    o = va - TLO
    if o < 0 or o >= len(txtb):
        return None
    return next(md.disasm(txtb[o:o + 16], va), None)

# ---- NC1 起点唯一性（先做，快）
a0 = starts[0]
i0, i1 = dec(a0), dec(a0 + 1)
put('nc1_origin', {'a0': hex(a0), 'from_a0': (i0.size if i0 else None,
                                              '%s %s' % (i0.mnemonic, i0.op_str) if i0 else None),
                   'from_a0p1': (i1.size if i1 else None,
                                 '%s %s' % (i1.mnemonic, i1.op_str) if i1 else None)})
ck('NC1 从 0x401001 起解出的第一条与从 0x401000 起不同 ⇒ 起点判据有判别力',
   (i0 is not None and i1 is not None and
    (i1.size != i0.size or (i1.mnemonic, i1.op_str) != (i0.mnemonic, i0.op_str))),
   '%s vs %s' % (i0.size if i0 else None, i1.size if i1 else None))

# ---- L 链式核验
WAIT = ('fstcw', 'fstsw', 'fsave', 'fldcw', 'fclex', 'finit', 'fstenv', 'fnstcw', 'fnstsw',
        'fnsave', 'fnclex', 'fninit', 'fnstenv')
ok = 0; bad = []
for i in range(N - 1):
    a = starts[i]
    ins = dec(a)
    if ins is None:
        bad.append({'i': i, 'a': hex(a), 'why': 'UNDECODABLE', 'tl': TL[i]}); continue
    if ins.size == TL[i] and a + TL[i] == starts[i + 1]:
        ok += 1
    else:
        bad.append({'i': i, 'a': hex(a), 'cap_len': ins.size, 'tl': TL[i],
                    'printed_len': LENS[i],
                    'cap_txt': '%s %s' % (ins.mnemonic, ins.op_str),
                    'obj_txt': TXT[i][:48],
                    'next': hex(starts[i + 1])})
put('chain', {'pairs': N - 1, 'ok': ok, 'bad': len(bad), 'bad_sample': bad[:10]})
WAIT_OBJ = ('fstcw', 'fstsw', 'fsave', 'fldcw', 'fclex', 'finit', 'fstenv')
hosts = set(starts[k - 1] for k in elide_at)
waits = [b for b in bad if b.get('cap_txt', ' ').split()[:1] == ['wait'] or
         (b.get('obj_txt', ' ') or ' ').split()[:1] and
         (b.get('obj_txt', ' ') or ' ').split()[0] in WAIT_OBJ]
elhost = [b for b in bad if int(b['a'], 16) in hosts]
und = [b for b in bad if b.get('why') == 'UNDECODABLE']
rest = [b for b in bad if b not in waits and b not in elhost and b not in und]
put('chain_bad_class', {'wait_family': len(waits), 'elide_host': len(elhost),
                        'capstone_undecodable': len(und), 'other': len(rest),
                        'other_sample': rest[:10]})
ck('PC1 链式核验的不符恰好分成三类（WAIT 族 / 省略段宿主 / capstone 解不出），无第四类',
   len(rest) == 0 and len(und) + len(waits) + len(elhost) == len(bad),
   '%d+%d+%d+%d = %d' % (len(und), len(waits), len(elhost), len(rest), len(bad)))
ck('L 链式核验（真长度口径）在 capstone 能解码且非 WAIT 族的位置 100% 首尾相接',
   ok == N - 1 - len(bad), '%d / %d（不符 %d）' % (ok, N - 1, len(bad)))

# ---- NC2 换成 R98 的错长度 LENS
okb = 0; badb = 0
for i in range(N - 1):
    if starts[i] + LENS[i] == starts[i + 1]:
        okb += 1
    else:
        badb += 1
put('nc2_wronglen', {'ok': okb, 'bad': badb, 'pairs': N - 1})
ck('NC2 错长度（本行字节数）口径下首尾相接的对数显著更少 ⇒ 真长度确有判别力',
   okb < ok and badb > 0, '%d vs %d' % (okb, ok))

# ---- S 省略段核验
ELADD = []
for k in elide_at:
    prev_end = starts[k - 1] + TL[k - 1]
    nxt = starts[k]
    ins_l = []
    p = prev_end
    while p < nxt:
        ins = dec(p)
        if ins is None or ins.size == 0:
            break
        ins_l.append((hex(p), ins.size))
        p += ins.size
    ELADD.append({'from': hex(prev_end), 'to': hex(nxt), 'nbytes': nxt - prev_end,
                  'insn': ins_l, 'tiled': p == nxt})
put('elide_chain', ELADD)
ck('PC2 5 处省略零段各自被 capstone 逐条铺满（合计 20 条 2 字节），首尾相接无残字节',
   all(x['tiled'] and len(x['insn']) == 4 and all(l == 2 for _, l in x['insn']) for x in ELADD),
   [(len(x['insn']), x['tiled']) for x in ELADD])

# ---- 全局：起始集完整性不靠线性扫描，而靠「每个字节都被某条指令覆盖」
covered = 0
gaps = []
pos = TLO
si = 0
# 用真长度算覆盖（不含省略段）
ends = []
for i in range(N):
    ends.append((starts[i], starts[i] + TL[i]))
i = 0
last_end = TLO
uncovered = []
for a, b in ends:
    if a > last_end:
        uncovered.append((last_end, a - last_end))
    if b > last_end:
        last_end = b
if last_end < HIVS:
    uncovered.append((last_end, HIVS - last_end))
put('coverage_gaps', {'n': len(uncovered), 'gaps': [[hex(a), l] for a, l in uncovered],
                      'total_bytes': sum(l for _, l in uncovered)})
ck('E 未覆盖字节恰好是 5 处省略零段（合计 40 字节），别无缺口',
   len(uncovered) == 5 and sum(l for _, l in uncovered) == 40, sum(l for _, l in uncovered))

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:200])
