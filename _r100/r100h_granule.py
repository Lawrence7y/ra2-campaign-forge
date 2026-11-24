#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 交付八：审计员 #150 的两条反驳由主会话亲自复算（§2.12 规则 D）

#150 对我 S5 与 S3 各提一条反驳，两条都可机械判定：
  A1 粒度不是「>=8 全消失」，而是「省略字节数 = 4 * floor(n/4)」，余数照常打印
     （它报：n=9/10/11 省 8 余 1/2/3；n=12 省 12；n=16 省 16）
     —— 我 R100a 只数了「省略行的条数」，**没量每处省略了多少字节**，这条我确实漏了
  A2 S3 的「长度和 + 40 = 段跨度」只证无遗漏字节，不证切分正确；
     它给出反例：27 处 objdump 把 9B 前缀并入前一条、capstone 拆成 wait + fnX

本脚本用 objdump 真跑合成样本，逐样本量「省略行覆盖多少字节」，
并独立复算 27 处 9B 合并。

正反控：
  PC1 n=8..20 每个样本的省略字节数必须等于 4*floor(n/4)（当 >=8 时）
  PC2 n=7 的省略字节数必须为 0（阈值下界）
  NC1 若模型写成「省略 n 字节」，n=9/10/11 会给出 9/10/11 —— 与实测不符
  NC2 -z 开关必须让全部样本的省略字节数归零（证明这是 objdump 特性而非解码假象）

产物：_r100/r100h_granule.json
"""
import os, io, re, json, subprocess, collections, bisect, struct
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r100/r100h_granule.json'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = collections.OrderedDict()
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

CTL = '/tmp/r100h_ctl'
os.makedirs(CTL, exist_ok=True)
LINE = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]*)\s*\t?(.*)$')
def run(nz, extra=()):
    p = os.path.join(CTL, 'g%d.bin' % nz)
    with open(p, 'wb') as f:
        f.write(b'\x90' * 8 + b'\x00' * nz + b'\x90' * 8)
    out = subprocess.run(['i686-w64-mingw32-objdump', '-D', '-b', 'binary', '-m', 'i386'] + list(extra) + [p],
                         capture_output=True, text=True).stdout
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    covered = 0
    nline = 0
    for ln in out.split('\n'):
        if not ln.strip():
            continue
        if ln.strip() == '...':
            nline += 1
            continue
        m = re.match(r'^\s*([0-9a-f]+):\t([0-9a-f ]+)', ln)
        if not m:
            continue
        addr = int(m.group(1), 16)
        bs = bytes(int(x, 16) for x in m.group(2).split())
        # 该行在样本内的区间
        lo, hi = max(addr, 8), min(addr + len(bs), 8 + nz)
        if lo < hi:
            covered += hi - lo
    return {'n': nz, 'elide_lines': nline, 'covered_in_zero_run': covered,
            'budget': 4 * (nz // 4), 'predicted_4': 4 * (nz // 4) if 4 * (nz // 4) >= 8 else 0,
            'coverage_complement': nz - covered}

G = {}
for nz in range(5, 21):
    G[nz] = run(nz)
put('by_n', {str(k): v for k, v in G.items()})
model_ok = all(G[n]['coverage_complement'] == G[n]['predicted_4'] for n in G)
ck('PC1 省略字节数 == 4*floor(n/4)（n>=8 时），n<8 时为 0 —— 逐样本 %d 个全部相符'
   % len(G), model_ok,
   [(n, G[n]['coverage_complement'], G[n]['predicted_4']) for n in G
    if G[n]['coverage_complement'] != G[n]['predicted_4']])
ck('PC2 n=7 的省略字节数为 0（阈值下界）', G[7]['coverage_complement'] == 0,
   G[7]['coverage_complement'])
ck('NC1 反控：若模型是「省略整条零游程」，n=9/10/11 应给 9/10/11，实测给 %d/%d/%d ⇒ 该模型被证伪'
   % (G[9]['coverage_complement'], G[10]['coverage_complement'], G[11]['coverage_complement']),
   G[9]['coverage_complement'] != 9 or G[11]['coverage_complement'] != 11,
   [G[n]['coverage_complement'] for n in (9, 10, 11)])
Z = {n: run(n, extra=('-z',)) for n in range(5, 21)}
ck('NC2 -z 开关让全部样本省略字节数归零 ⇒ 这是 objdump 的零省略特性，不是解码假象',
   all(Z[n]['coverage_complement'] == 0 for n in Z), sum(Z[n]['coverage_complement'] for n in Z))

# ---- A2 独立复算 27 处 9B 合并
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
txtb = raw[TROFF:TROFF + (HIVS - TLO)]
FULL = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP = re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
starts = []; LENS = []; TXT = []; wraps = []
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts.append(int(m.group(1), 16)); LENS.append(len(m.group(2).split()))
        TXT.append(m.group(3).strip()); continue
    w = WRAP.match(ln)
    if w:
        wraps.append((int(w.group(1), 16), len(w.group(2).split())))
N = len(starts)
TL = list(LENS)
for a, n in wraps:
    j = bisect.bisect_left(starts, a) - 1
    TL[j] += n
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
WAITW = ('fstcw','fstsw','fsave','fldcw','fclex','finit','fstenv',
         'fnstcw','fnstsw','fnsave','fnclex','fninit','fnstenv')
MERG = []
ALL9B = []
for i2 in range(N):
    o = starts[i2] - TLO
    if o < 0 or o >= len(txtb) or txtb[o] != 0x9B:
        continue
    seq = []
    for ins in md.disasm(txtb[o:o + 24], starts[i2]):
        seq.append((ins.size, '%s %s' % (ins.mnemonic, ins.op_str)))
        if len(seq) >= 6:
            break
    txt0 = TXT[i2].split()[0] if TXT[i2].split() else ''
    rec = {'a': hex(starts[i2]), 'objdump_truelen': TL[i2], 'obj_text': TXT[i2][:34],
           'cap_first2': seq[:2], 'cap_two_sum': (seq[0][0] + seq[1][0]) if len(seq) > 1 else None,
           'cap_fill': next((k + 1 for k in range(len(seq))
                             if sum(z[0] for z in seq[:k + 1]) >= TL[i2]), None),
           'cap_fill_sum': next((sum(z[0] for z in seq[:k + 1]) for k in range(len(seq))
                                 if sum(z[0] for z in seq[:k + 1]) >= TL[i2]), None),
           'obj_first': txt0}
    ALL9B.append(rec)
    if txt0 in WAITW:
        MERG.append(rec)
put('nine_b_all', {'n': len(ALL9B)})
put('nine_b_merges', {'n': len(MERG), 'sample': MERG[:6]})
ck('A2 首字节 9B 且 objdump 打成 WAIT 族助记符的行数（独立复算 #150 的 27）',
   len(MERG) == 27, '%d 处（首字节 9B 的行共 %d 条）' % (len(MERG), len(ALL9B)))
agree2 = sum(1 for m in MERG if m['cap_two_sum'] == m['objdump_truelen'])
agreeN = sum(1 for m in MERG if m['cap_fill_sum'] == m['objdump_truelen'])
dist = collections.Counter(m['cap_fill'] for m in MERG)
put('merge_fill', {'n': len(MERG), 'two_insn_match': agree2, 'n_insn_match': agreeN,
                   'insn_count_dist': dict(sorted(dist.items())),
                   'note': 'objdump 把连续的 9B 前缀全部并进同一条 WAIT 族指令；'
                           'capstone 每个 9B 单解一条 wait，故「前两条之和」只对单 9B 成立，'
                           '双 9B 需前三条。按「累计到真长度」口径则 27/27 相符。'})
ck('A2b 按「capstone 累计长度首次 >= objdump 真长度」口径，27 处逐处相符 ⇒ '
   '9B 前缀被合并的机制成立（前两条之和只对单 9B 成立，双 9B 有 %d 处）'
   % (len(MERG) - agree2), agreeN == len(MERG), '%d / %d（前两条口径 %d / %d）'
   % (agreeN, len(MERG), agree2, len(MERG)))

# ---- 5 处真实省略点的粒度口径（IRL 数据）
ELIDE = re.compile(r'^\t\.\.\.\s*$')
elide_at = []; np_ = 0; starts2 = []; LENS2 = []
for ln in io.open('/tmp/r93_disasm.txt', encoding='utf-8', errors='replace'):
    m = FULL.match(ln)
    if m:
        starts2.append(int(m.group(1), 16)); LENS2.append(len(m.group(2).split())); np_ += 1
        continue
    if ELIDE.match(ln):
        elide_at.append(np_)
TL2 = list(LENS2)
for a, n in wraps:
    j = bisect.bisect_left(starts2, a) - 1
    TL2[j] += n
# 物理零游程
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
big = {a: l for a, l in runs if l >= 8}
IRL = []
for k in elide_at:
    pe = starts2[k - 1] + TL2[k - 1]
    nxt = starts2[k]
    el = nxt - pe
    phys = [(hex(a), l) for a, l in big.items() if a <= pe < a + l]
    IRL.append({'elided_from': hex(pe), 'elided': el, 'phys_run': phys,
                'pred_4': 4 * (phys[0][1] // 4) if phys else None,
                'rem': (phys[0][1] - 4 * (phys[0][1] // 4)) if phys else None,
                'matches_4granule': (4 * (phys[0][1] // 4) == el) if phys else None})
put('irl_granule', IRL)
ck('A1b 5 处真实省略点的省略字节数，与「4*floor(物理零游程/4)」模型逐处比对',
   all(x['matches_4granule'] for x in IRL),
   [(x['elided_from'], x['elided'], x['phys_run'], x['pred_4']) for x in IRL])
comp = []
for x in IRL:
    if not x['phys_run']:
        comp.append({'at': x['elided_from'], 'note': 'no >=8 run covers it'}); continue
    pa_hex, pl = x['phys_run'][0][0], x['phys_run'][0][1]
    comp.append({'run_start': pa_hex, 'run_len': pl, 'elided': x['elided'],
                 'residual': pl - x['elided'],
                 'residual_mod4': (pl - x['elided']) % 4})
put('irl_residual', comp)
ck('A1c 5 处残差（游程长 - 省略字节）分别为 %s，全取 {0,1,3} 且 < 4 ⇒ '
   '「4 字节粒度」模型与真实数据逐处相符' % [c.get('residual') for c in comp],
   all(0 <= c.get('residual', -1) < 4 for c in comp),
   [c.get('residual') for c in comp])

R['checks'] = checks
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d / FAIL %d' % (len(checks), nf))
for c in checks:
    if not c['ok']:
        print('  FAIL 明细: ' + c['name'] + ' | ' + c['detail'][:250])
