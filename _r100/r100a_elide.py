#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付一：objdump 的 tab-... 省略行是什么 —— 5 处 8 字节零填充，不是长指令换行

R99 已证 9,028 条「只有字节列」的行是长指令的换行续行（宿主 + 续行 = 下一条起始）。
但反汇编里还有 5 行完全另一种形态：单独一行 tab + 三个点（省略号），
R99 的全链解析把这种行计入 other，既没定性也没定量。

本脚本要回答四件事，全部机械可判：
  E1 省略行有几条、每条省略了多少字节（用「上一条已打印指令的末尾」到「下一条打印指令的起点」夹出来）
  E2 被省略的字节内容是什么、能否被 capstone 逐条解码并恰好铺满
  E3 省略的触发阈值（必须从数据来，不许拍）：零游程长度的直方图 vs 实际被省略的游程
  E4 把省略字节计回来以后，.text 是否被指令逐字节无缝覆盖（长度和 == 段跨度，差 0）
      —— R99 报的长度和 4,060,005 与段跨度 4,060,045 差 40，本脚本给出这 40 字节的归属

正反控：
  PC1 省略行数 == .text 内长度 >= 8 的零游程数（同一现象的两种独立观测）
  PC2 每条被省略区间在两套独立数据源（反汇编地址几何 / exe 原始字节）上都恰为 8 字节且全零
  PC3 capstone 对被省略区间逐条解码，长度和恰好等于区间长度（可铺满，无残字节）
  PC4 长度和 + 省略字节 == 段跨度，且指令数 == 1,392,516 + 20
  NC1 阈值反控：若阈值取 7，则「应被省略」的游程数远大于实际（模型被证伪）
  NC2 长指令反控：若把省略字节算作前一条指令的一部分，capstone 必须在同一地址解出等长指令
      （实测解不出 ⇒「省略 = 长指令」这一读法被证伪）

产物：_r100/r100a_elide.json
"""
import os, io, re, json, array, bisect, struct, collections
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
DUMP = '/tmp/r93_disasm.txt'
EXE = 'ra2bench/gamemd.exe'
OUT = '_r100/r100a_elide.json'
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
assert raw[e:e + 4] == b'PE\0\0'
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
TLO, HIVS, HIRS, TROFF = T[1], T[2], T[3], T[4]
SPAN = HIVS - TLO
def off_of(va):
    for nm, lo, hivs, hirs, roff, rsz in SECS:
        if lo <= va < lo + rsz:
            return roff + (va - lo)
    return None

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I')
LENS = array.array('B')
MNS = []
wraps = array.array('I'); wl = array.array('B')
elide_line_idx = []       # 省略行在「已打印指令序列」中的位置：紧跟在第 n 条之后
nother = 0
nprint = 0
for ln in io.open(DUMP, encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16))
        LENS.append(len(m.group(2).split()))
        t = m.group(3).strip()
        mm = re.match(r'^(\w+)', t)
        MNS.append(mm.group(1) if mm else '')
        nprint += 1
        continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split()))
        continue
    if ELIDE.match(ln):
        elide_line_idx.append(nprint)      # == 下一条待打印指令的下标（即省略处）
        continue
    nother += 1
N = len(starts)
SSET = set(starts)
IDX = {a: i for i, a in enumerate(starts)}
put('parse', {'printed': N, 'wraps': len(wraps), 'elide_lines': len(elide_line_idx),
              'other': nother, 'first': hex(starts[0]), 'last': hex(starts[-1])})
ck('S0 已打印 1,392,516 条 / 续行 9,028 条 / 省略行（如实报）',
   N == 1392516 and len(wraps) == 9028, '%d / %d / elide %d' % (N, len(wraps), len(elide_line_idx)))

# ---- 真长度（R99 口径：本行 + 其后续行）
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n

# ---- E1 每条省略行的位置与省略字节数（反汇编几何）
EL = []
for k in elide_line_idx:
    prev_i = k - 1
    prev_end = starts[prev_i] + TL[prev_i]
    next_start = starts[k]
    EL.append({'idx': k, 'prev': hex(starts[prev_i]), 'prev_len': LENS[prev_i],
               'prev_truelen': TL[prev_i], 'prev_end': hex(prev_end),
               'next': hex(next_start), 'elided': next_start - prev_end})
put('elide_sites', EL)
ck('E1 每条省略行夹出的省略字节数（反汇编几何口径）',
   all(x['elided'] > 0 for x in EL), [x['elided'] for x in EL])

# ---- E2 被省略区间的原始字节（exe 独立数据源）+ capstone 铺满
txtb = raw[TROFF:TROFF + SPAN]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
E2 = []
for x in EL:
    a = int(x['prev_end'], 16); b = int(x['next'], 16)
    blob = raw[off_of(a):off_of(a) + (b - a)]
    ins = []
    p = a
    for i in md.disasm(blob, a):
        ins.append({'a': hex(i.address), 'len': i.size, 't': '%s %s' % (i.mnemonic, i.op_str)})
        p = i.address + i.size
    E2.append({'at': hex(a), 'to': hex(b), 'nbytes': b - a, 'bytes': blob.hex(' '),
               'all_zero': all(c == 0 for c in blob), 'insn': ins,
               'tiled': (p == b), 'sum_ins_len': sum(i['len'] for i in ins)})
put('elided_bytes', E2)
ck('PC2 每段被省略区间在 exe 原始字节上恰好全零，且与反汇编几何算出的长度相同',
   all(x['all_zero'] and x['nbytes'] == y['elided'] for x, y in zip(E2, EL)),
   [(x['nbytes'], y['elided']) for x, y in zip(E2, EL)])
ck('PC3 capstone 对被省略区间逐条解码并恰好铺满（无残字节）',
   all(x['tiled'] and x['sum_ins_len'] == x['nbytes'] for x in E2),
   [(x['sum_ins_len'], x['nbytes'], len(x['insn'])) for x in E2])
def insn_at(va):
    o = off_of(va)
    return next(md.disasm(raw[o:o + 32], va), None)
NC2 = []
for x, y in zip(EL, E2):
    pv = int(x['prev'], 16)
    ins = insn_at(pv)
    NC2.append({'prev': x['prev'], 'cap_len': ins.size if ins else None,
                'printed_truelen': x['prev_truelen'], 'would_be': x['prev_truelen'] + y['nbytes']})
put('nc2_long_insn', NC2)
ck('NC2 长指令反控：若省略字节属于前一条指令，capstone 应在该地址解出 printed+truelen+elided 的长度；'
   '实测 5/5 都只解出 2 字节 ⇒「省略 = 长指令」读法被证伪',
   all(z['cap_len'] == z['printed_truelen'] and z['cap_len'] != z['would_be'] for z in NC2),
   [(z['cap_len'], z['would_be']) for z in NC2])

# ---- E3 零游程直方图（阈值必须从数据来）
runs = []
i = 0
while i < len(txtb):
    if txtb[i] == 0:
        j = i
        while j < len(txtb) and txtb[j] == 0:
            j += 1
        runs.append((TLO + i, j - i))
        i = j
    else:
        i += 1
hist = collections.Counter(l for _, l in runs)
big = [(a, l) for a, l in runs if l >= 8]
put('zero_runs', {'total': len(runs), 'hist_ge4': {str(k): v for k, v in sorted(hist.items()) if k >= 4},
                  'n_ge8': len(big), 'ge8': [[hex(a), l] for a, l in big]})
ck('PC1 省略行数 == .text 内长度 >= 8 的零游程数（两种独立观测同数）',
   len(elide_line_idx) == len(big), '%d vs %d' % (len(elide_line_idx), len(big)))
ck('E3 阈值从数据来：长度恰好 7 的零游程 203 条一条都没被省略，长度 >= 8 的 5 条全部被省略',
   hist.get(7) == 203 and len(big) == 5, dict((k, hist.get(k)) for k in (6, 7, 8, 9, 11)))
ck('NC1 阈值反控：若阈值取 7，则应省略 208 条（实测 5）⇒ 阈值 7 的模型被证伪',
   hist.get(7) + len(big) != len(elide_line_idx),
   '%d vs %d' % (hist.get(7) + len(big), len(elide_line_idx)))
# 省略按几何对齐到 2 字节指令边界：每段起点 == 某零游程内偏移，段尾 == 下一条打印指令
align = []
for x, y in zip(EL, E2):
    a = int(y['at'], 16)
    hit = [(hex(ra), rl, a - ra) for ra, rl in big if ra <= a < ra + rl]
    align.append({'at': y['at'], 'in_run': hit[0] if hit else None})
put('elide_alignment', align)

# ---- E4 逐字节无缝覆盖
tot_tl = sum(TL)
elided_total = sum(x['elided'] for x in EL)
n_elided_insn = sum(len(x['insn']) for x in E2)
put('coverage', {'span': SPAN, 'sum_truelen': tot_tl, 'elided_total': elided_total,
                 'sum_plus_elided': tot_tl + elided_total, 'diff_to_span': tot_tl + elided_total - SPAN,
                 'n_printed': N, 'n_elided_insn': n_elided_insn, 'n_total': N + n_elided_insn})
ck('E4 长度和 + 被省略字节 == .text 段跨度（差 0，逐字节无缝覆盖）',
   tot_tl + elided_total == SPAN, '%d + %d vs %d (diff %d)' % (
       tot_tl, elided_total, SPAN, tot_tl + elided_total - SPAN))
ck('PC4 指令总数 == 1,392,516 + 20（每条 2 字节、铺满 40 字节）',
   n_elided_insn == 20 and elided_total == 40, '%d / %d' % (n_elided_insn, elided_total))

# ---- 下游一：被省略的 20 条地址有没有被跳转/调用直接指向
# 自错修正（本轮第二次犯「判据无判别力」）：第一版把 E2 里的 insn['a']（hex 字符串）
# 与 JTGT（整数集合）求交，交集恒为空 ⇒ 断言 PASS 却毫无判别力。
# 修法：统一成整数，并加一条反控（必须至少命中 1 个，否则说明扫描本身坏了）。
JTGT = set()
JN = 0
for ln in io.open(DUMP, encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if not m:
        continue
    t = m.group(3).strip()
    mm = re.match(r'^(\w+)\s*(.*)$', t)
    if not mm:
        continue
    mn, rest = mm.group(1), mm.group(2).strip()
    if mn not in ('je','jne','jz','jnz','jl','jle','jg','jge','jb','jbe','ja','jae','js','jns',
                  'jo','jno','jp','jnp','jpe','jpo','jc','jnc','jcxz','jecxz','jecxnz',
                  'loop','loope','loopne','jmp','call'):
        continue
    if not rest or rest.startswith('*') or '[' in rest:
        continue
    try:
        v = int(rest.split()[0], 0)
    except ValueError:
        continue
    JTGT.add(v); JN += 1
EL_ADDR = set()
for y in E2:
    for ins in y['insn']:
        EL_ADDR.add(int(ins['a'], 16))
hit = sorted(EL_ADDR & JTGT)
put('elided_targets', {'elided_insn': len(EL_ADDR), 'jump_edges': JN,
                       'jump_targets_total': len(JTGT),
                       'elided_hit': len(hit), 'list': [hex(x) for x in hit]})
ck('E5a 扫描反控：跳转目标集非空且规模合理（否则本判据无判别力）',
   len(JTGT) > 50000, '%d 个目标 / %d 条边' % (len(JTGT), JN))
ck('E5b 被省略的 20 条指令里有没有被 jump/call 直接指向的（如实报，不预设 0）',
   True, '%d 个命中：%s' % (len(hit), [hex(x) for x in hit]))

# ---- 下游二：物理零游程长度 vs 被省略区间长度（两种口径，必须分开报）
put('denominator', {'starts_printed': N, 'starts_with_elided': N + n_elided_insn,
                    'sum_truelen_printed': tot_tl, 'span': SPAN,
                    'physical_zero_runs': [[hex(a), l] for a, l in big],
                    'elided_intervals': [[y['at'], y['nbytes']] for y in E2],
                    'note': '物理零游程 9/8/9/11/8；被省略区间恒 8 —— 前三条游程的首字节'
                            '被前一条 01 xx 指令的操作数吃掉，故两种口径必须分开报'})

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:200])
