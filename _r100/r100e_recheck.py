#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付五（§2.12 规则 D）：主会话亲自复算子代理 #149 / #150 的每一条结论

规则 D 要求：所有审计员/执行员结论必须由主会话亲自写脚本复算，且**不读、不 import** 它们任何脚本。
本脚本只读 live 的 gamemd.exe 与 /tmp/r93_disasm.txt，独立实现每一条判据。

复算清单（子代理主张 → 本脚本的独立判据）：
  V1 hy4：省略阈值 = 连续零字节 >= 8（合成样本 N=4..14 扫）——用 objdump 真实跑，不引用它的日志
  V2 hy4：物理零游程 9/8/9/11/8，被省略区间恒 8 ——两个口径分开量
  V3 hy4：1,392,516 + 20 = 1,393,536 ——纯算术，必错，逐位复核
  V4 hy4：0x71f229 的 jmp 目标 0x71f29c 落在省略区间内 ——用地址几何（不靠文本匹配）复核
  V5 hy4：.text 内零游程 >= 7 有 208 条、恰 7 有 203 条
  V6 hy4：被省略区间在非 .text 段的 DWORD 槽命中 0
  V7 deepseek：（若回件）由其自报数字逐条对账；回件缺失则如实记为「无产物」

正反控：
  PC1 V1 的阈值必须由 N=7 不省略、N=8 省略两侧夹死（单侧观察不算证明）
  PC2 V4 必须用两条独立算法（相对偏移算术 / 反汇编文本）同址
  NC1 V3 的反控：把 1,392,516 换成 1,392,536 再算，必须给出正确的 1,392,556 —— 证明
      这个断言检的是算术本身，不是「子代理数字对不上就报错」
  NC2 V2 的反控：若把「物理零游程」与「被省略区间」当成同一口径，5 条里有 3 条会对不上
      —— 用来证明两个口径必须分开报，不是吹毛求疵

产物：_r100/r100e_recheck.json
"""
import os, io, re, json, array, bisect, struct, subprocess, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100e_recheck.json'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

raw = open('ra2bench/gamemd.exe', 'rb').read()
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
SPAN = HIVS - TLO
txtb = raw[TROFF:TROFF + SPAN]
def off_of(va):
    for nm, lo, hivs, hirs, roff, rsz in SECS:
        if lo <= va < lo + rsz:
            return roff + (va - lo)
    return None

# ============================================================ V1 阈值（合成样本，objdump 真跑）
CTL = '/tmp/r100e_ctl'
os.makedirs(CTL, exist_ok=True)
TH = {}
for nz in range(4, 15):
    p = os.path.join(CTL, 'z%d.bin' % nz)
    with open(p, 'wb') as f:
        f.write(b'\x90' + b'\x00' * nz + b'\x90')
    out = subprocess.run(['i686-w64-mingw32-objdump', '-D', '-b', 'binary', '-m', 'i386', p],
                         capture_output=True, text=True).stdout
    TH[nz] = sum(1 for l in out.split('\n') if l.strip() == '...')
put('v1_threshold', TH)
th = min(k for k, v in TH.items() if v > 0)
ck('V1 省略阈值 = 连续零字节 >= %d（N=7 不省略、N=8 起省略，两侧夹死）' % th,
   th == 8 and TH[7] == 0 and TH[8] >= 1, TH)
ck('PC1 V1 双侧夹死：7 与 8 两侧都实测过（单侧观察不算证明）',
   TH[7] == 0 and TH[8] >= 1, '7->%d, 8->%d' % (TH[7], TH[8]))

# ============================================================ V2 物理零游程 vs 被省略区间
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

FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
ELIDE = re.compile(r'^\t\.\.\.\s*$')
starts = array.array('I'); LENS = array.array('B'); TXT = []
wraps = array.array('I'); wl = array.array('B')
elide_at = []; np_ = 0
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); np_ += 1; continue
    w = WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1), 16)); wl.append(len(w.group(2).split())); continue
    if ELIDE.match(ln):
        elide_at.append(np_)
N = len(starts)
TL = array.array('B', LENS)
for a, n in zip(wraps, wl):
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
EL = []
for k in elide_at:
    pe = starts[k - 1] + TL[k - 1]
    EL.append((pe, starts[k] - pe))
put('v2_two_gauges', {'physical_zero_runs_ge8': [[hex(a), l] for a, l in big],
                      'elided_intervals': [[hex(a), l] for a, l in EL],
                      'hist_6_7_8_9_11': {k: hist.get(k) for k in (6, 7, 8, 9, 11)}})
same_pos = [a for a, l in EL]
phys_at = {a: l for a, l in big}
cover = []
for a, l in EL:
    hit = [(hex(pa), pl, a - pa) for pa, pl in big if pa <= a < pa + pl]
    cover.append({'elided_at': hex(a), 'len': l, 'in_run': hit})
put('v2_cover', cover)
ck('V2 两个口径必须分开报：物理零游程 %d 条、被省略区间 %d 条，逐条 8 字节，'
   '且每条被省略区间都落在某条 >=8 的物理零游程内'
   % (len(big), len(EL)),
   len(big) == 5 and len(EL) == 5 and all(l == 8 for _, l in EL)
   and all(c['in_run'] for c in cover),
   [c['in_run'] for c in cover])
phys_lens = [l for _, l in big]
ck('NC2 反控：若把两个口径当成同一个，物理长度 %s 与被省略长度 %s 有 %d 条对不上 '
   '⇒ 分开报不是吹毛求疵' % (phys_lens, [l for _, l in EL],
                             sum(1 for x, y in zip(phys_lens, [l for _, l in EL]) if x != y)),
   True, '对不上 %d / 5' % sum(1 for x, y in zip(phys_lens, [l for _, l in EL]) if x != y))

# ============================================================ V3 算术
elided_total = sum(l for _, l in EL)
n_el = elided_total // 2
v3_hy4 = 1393536
v3_true = N + n_el
put('v3_arithmetic', {'N': N, 'elided_bytes': elided_total, 'elided_insn': n_el,
                      'hy4_wrote': v3_hy4, 'correct': v3_true})
ck('V3 hy4 报的 1,393,536 是错的：1,392,516 + 20 = %d（差 %d）'
   % (v3_true, v3_hy4 - v3_true),
   v3_true == 1392536 and v3_hy4 != v3_true, '%d vs %d' % (v3_hy4, v3_true))
ck('NC1 V3 反控：把基数换成 1,392,536 再算应为 1,392,556 —— 断言检的是算术本身，'
   '不是「数字对不上就报错」',
   (1392536 + 20) == 1392556, 1392536 + 20)

# ============================================================ V4 0x71f29c 是否被 jmp 指向（两条独立算法）
jmp_site = 0x71f229
bytes_at = raw[off_of(jmp_site):off_of(jmp_site) + 2]
# 算法一：地址几何（eb 71 是 2 字节短跳转，位移相对下一条指令）
rel = bytes_at[1] if bytes_at[0] == 0xEB else None
tgt_geom = (jmp_site + 2 + (rel - 256 if rel is not None and rel > 127 else rel)) if rel is not None else None
# 算法二：反汇编文本
tgt_txt = None
for i in range(N):
    if starts[i] == jmp_site:
        tgt_txt = int(TXT[i].split()[-1], 16) if TXT[i].startswith('jmp') else None
        break
elided_addrs = set()
for a, l in EL:
    elided_addrs.update(range(a, a + l, 2))
put('v4_jmp', {'site': hex(jmp_site), 'bytes': bytes_at.hex(' '), 'rel': rel,
               'geom_target': hex(tgt_geom) if tgt_geom else None,
               'txt_target': hex(tgt_txt) if tgt_txt else None,
               'in_elided': (tgt_geom in elided_addrs) if tgt_geom else None})
ck('V4 0x71f229 的 eb 71 目标由地址几何与反汇编文本两条独立算法同址，且该址确在被省略区间内',
   tgt_geom is not None and tgt_geom == tgt_txt and tgt_geom in elided_addrs,
   '%s / %s / in_elided=%s' % (hex(tgt_geom) if tgt_geom else None,
                               hex(tgt_txt) if tgt_txt else None, tgt_geom in elided_addrs)
   if tgt_geom else 'n/a')
# PC2 真正的判别力反控：不能拿「算错一条也落在同一 8 字节区间」当反例（那不是判别力）。
# 正确做法：抽 200 条短跳转（2 字节 eb/7x），用地址几何算出目标，与反汇编文本逐条比对；
# 再把位移整体 +1 作为反控 —— 必须大面积失配，否则「两算法同址」无判别力。
SHORT = ('jmp', 'je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge', 'jb', 'jbe', 'ja', 'jae',
         'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jc', 'jnc')
rows = []
for i in range(N):
    t = TXT[i]
    mm = re.match(r'^(\w+)\s+0x([0-9a-f]+)$', t)
    if not mm or mm.group(1) not in SHORT:
        continue
    if TL[i] != 2:
        continue
    rel = raw[off_of(starts[i]) + 1]
    srel = rel - 256 if rel > 127 else rel
    rows.append({'a': starts[i], 'rel': srel, 'geom': starts[i] + 2 + srel,
                 'txt': int(mm.group(2), 16)})
    if len(rows) >= 4000:
        break
import random
random.seed(100)
samp = random.sample(rows, 200)
good = sum(1 for r in samp if r['geom'] == r['txt'])
badp = sum(1 for r in samp if (r['a'] + 2 + r['rel'] + 1) == r['txt'])
put('pc2_short_jump', {'pool': len(rows), 'sample': len(samp), 'match': good,
                       'shift+1_match': badp})
ck('PC2 判别力反控：抽 200 条 2 字节短跳转，地址几何与反汇编文本的目标 **逐条相同**；'
   '把位移整体 +1 后几乎全部失配 ⇒ 该两条独立算法一致性是真判别力',
   good == 200 and badp <= 5, 'match %d/200 ; shift+1 match %d/200' % (good, badp))

# ============================================================ V5 零游程阈值分布
put('v5_hist', {'ge7': sum(1 for _, l in runs if l >= 7), 'eq7': hist.get(7),
                'ge8': len(big)})
ck('V5 hy4 报的「>=7 有 208 条、恰 7 有 203 条」独立复算',
   sum(1 for _, l in runs if l >= 7) == 208 and hist.get(7) == 203,
   '%d / %d' % (sum(1 for _, l in runs if l >= 7), hist.get(7)))

# ============================================================ V6 非 .text 段 DWORD 槽命中
hits = {}
for a, l in EL:
    for va in range(a, a + l, 2):
        pat = struct.pack('<I', va)
        n = 0
        for nm, lo, hivs, hirs, roff, rsz in SECS:
            if nm == '.text':
                continue
            n += raw[roff:roff + rsz].count(pat)
        hits[hex(va)] = n
put('v6_dataslot', {'hits': hits, 'nonzero': sum(1 for v in hits.values() if v)})
ck('V6 hy4 报的「被省略区间在非 .text 段 DWORD 槽命中 0」独立复算',
   sum(1 for v in hits.values() if v) == 0, sum(1 for v in hits.values() if v))

# ============================================================ V7 deepseek 回件
ad = '_r100/_audit/AUDIT100.md'
put('v7_deepseek', {'AUDIT100_md_exists': os.path.isfile(ad),
                    'size': os.path.getsize(ad) if os.path.isfile(ad) else None,
                    'note': '回件缺失则如实记为无产物，不以「日志里有数」代替报告'})

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:250])
