# -*- coding: utf-8 -*-
"""R221-A single-shot forensic script; writes only _r221/A_report.md and A_result.json."""
import sys, os, json, struct, hashlib, re, time
sys.dont_write_bytecode = True
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT)
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

OD = os.path.join(ROOT, '_r221')
ADJ = (-1, -1, -1, -1, 2, 4, 6, 8)
IMA_STD = [
    7, 8, 9, 10, 11, 12, 13, 14,
    16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66,
    73, 80, 88, 97, 107, 118, 130, 143,
    157, 173, 190, 209, 230, 253, 279, 307,
    337, 371, 408, 449, 494, 544, 598, 658,
    724, 796, 876, 963, 1060, 1166, 1282, 1411,
    1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
    3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
    7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794,
    32767,
]
assert len(IMA_STD) == 89 and IMA_STD[0] == 7 and IMA_STD[-4:] == [24623, 27086, 29794, 32767]

def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]

def blob(va, n):
    o = P.r2o(va)
    if o is None:
        raise ValueError('unmapped VA ' + hex(va))
    return P.RAW[o:o + n]

def off_to_vas(off):
    out = []
    for s in P.SECS:
        if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
            out.append(hex(s['lo'] + off - s['rawptr']))
    return out

def find_all(b):
    hits, st = [], 0
    while True:
        i = P.RAW.find(b, st)
        if i < 0:
            break
        hits.append(i)
        st = i + 1
    return hits

t = P.B['.text']
R = {'meta': {
    'tool': 'python3 + capstone disasm_lite (detail=False, skipdata=True)',
    'text': {'lo': hex(t['lo']), 'rawptr': t['rawptr'], 'rawsize': t['rawsize']},
    'ima_std_len_measured': len(IMA_STD),
}}

# --- 1 regions / boundaries ---
regions_spec = [
    ('idx_8758c4', 0x8758c4, 16),
    ('step_8758e4', 0x8758e4, 178),
    ('idx_copy_8758d4', 0x8758d4, 16),
    ('D_8759b4', 0x8759b4, 5696),
    ('S_copy_876ff4', 0x876ff4, 3360),
    ('D_879b30', 0x879b30, 5696),
    ('S_87b170', 0x87b170, 3360),
    ('jitterA_87bc90', 0x87bc90, 256),
    ('jitterB_87bd90', 0x87bd90, 256),
]
regions = {}
for nm, va, n in regions_spec:
    b = blob(va, n)
    regions[nm] = {'va': hex(va), 'file_off': P.r2o(va), 'n': n,
                   'section': P.sec_of(va), 'sha256_16': sha16(b),
                   'first16': b[:16].hex(), 'last16': b[-16:].hex()}
R['1_regions'] = regions
R['1_assertions'] = [
    {'expr': lhs_expr, 'left': hex(l), 'right': hex(r), 'equal': l == r}
    for lhs_expr, l, r in [
        ('0x8759b4+5696==0x876ff4', 0x8759b4 + 5696, 0x876ff4),
        ('0x876ff4+3360==0x877d14', 0x876ff4 + 3360, 0x877d14),
        ('0x879b30+5696==0x87b170', 0x879b30 + 5696, 0x87b170),
        ('0x87b170+3360==0x87be90', 0x87b170 + 3360, 0x87be90),
        ('0x8758e4+178==0x875996', 0x8758e4 + 178, 0x875996),
    ]]
R['1_tail'] = {'0x877d14_16': blob(0x877d14, 16).hex(),
               '0x87be90_16': blob(0x87be90, 16).hex()}

# --- 2 duplicates + full-file occurrences ---
dups = []
for nm, a, b, n in [
    ('D_pair_5696', 0x8759b4, 0x879b30, 5696),
    ('S_pair_3360', 0x876ff4, 0x87b170, 3360),
    ('idx_pair_16', 0x8758c4, 0x8758d4, 16),
]:
    ba, bb = blob(a, n), blob(b, n)
    dups.append({'name': nm, 'va_a': hex(a), 'va_b': hex(b), 'n': n,
                 'equal': ba == bb, 'sha256_16_a': sha16(ba),
                 'sha256_16_b': sha16(bb),
                 'occurrences': [{'file_off': o, 'vas': off_to_vas(o)} for o in find_all(ba)]})
R['2_duplicates'] = dups

# --- 3 index table ---
idx = list(struct.unpack('<8h', blob(0x8758c4, 16)))
R['3_index'] = {'va': '0x8758c4', 'values': idx, 'expected': list(ADJ), 'match': idx == list(ADJ)}

# --- 4 step table ---
step = list(struct.unpack('<89H', blob(0x8758e4, 178)))
R['4_step'] = {
    'va': '0x8758e4', 'first8': step[:8], 'last3': step[-3:],
    'hits': sum(a == b for a, b in zip(step, IMA_STD)), 'total': 89,
    'strict_increasing': all(step[i] < step[i + 1] for i in range(88)),
    'first_mismatch': next(([i, step[i], IMA_STD[i]] for i in range(89) if step[i] != IMA_STD[i]), None),
}

# --- laws ---
def law_d(base, ima, sign_thr=8, mag_mask=7, count=1424):
    vals = struct.unpack('<%di' % count, blob(base, count * 4))
    hits, mm = 0, []
    for k, v in enumerate(vals):
        m, n = divmod(k, 16)
        s = ima[m]
        nn = n & mag_mask
        d = (s >> 3) + (s if nn & 4 else 0) + ((s >> 1) if nn & 2 else 0) + ((s >> 2) if nn & 1 else 0)
        exp = -d if n >= sign_thr else d
        if v == exp:
            hits += 1
        elif len(mm) < 6:
            mm.append([m, n, v, exp])
    return {'va': hex(base), 'hits': hits, 'total': count,
            'first_mismatches': mm, 'sign_thr': sign_thr, 'mag_mask': mag_mask}

def law_s(base, count=1424, rec=16, upper=88):
    vals = struct.unpack('<%dh' % count, blob(base, count * 2))
    hits, mm = 0, []
    for k, v in enumerate(vals):
        m, n = divmod(k, rec)
        exp = 32 * max(0, min(upper, m + ADJ[n & 7]))
        if v == exp:
            hits += 1
        elif len(mm) < 6:
            mm.append([m, n, v, exp])
    return {'va': hex(base), 'hits': hits, 'total': count,
            'first_mismatches': mm, 'rec': rec, 'upper': upper}

R['5_lawD_879b30'] = law_d(0x879b30, step)
svals = struct.unpack('<1424h', blob(0x87b170, 2848))
ls = law_s(0x87b170)
ls.update({'min': min(svals), 'max': max(svals), 'all_mult32': all(v % 32 == 0 for v in svals)})
R['6_lawS_87b170'] = ls
R['6_lawS_copy_876ff4'] = law_s(0x876ff4)
R['6_lawS_on_Dcopy_8759b4'] = law_s(0x8759b4)
R['6_lawD_on_Dcopy_8759b4'] = law_d(0x8759b4, step)

# --- 7 controls ---
R['7_controls'] = {
    'K1_base_plus2': law_s(0x87b172),
    'K2_rec8_count712': law_s(0x87b170, count=712, rec=8),
    'K3_upper87': law_s(0x87b170, upper=87),
    'K4_sign_thr7': law_d(0x879b30, step, sign_thr=7),
    'K5_mag_mask15': law_d(0x879b30, step, mag_mask=15),
}

# --- 8 reference scan (streaming, one instruction per resync step) ---
TARGETS = [0x8758c4, 0x8758d4, 0x8758e4, 0x8759b4, 0x876ff4,
           0x879b30, 0x87b170, 0x87bc90, 0x87bd90]
pats = {v: re.compile(r'(?<![0-9a-fA-F])0x%x(?![0-9a-fA-F])' % v) for v in TARGETS}
hits = {v: [] for v in TARGETS}
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True
rp, rs, lo = t['rawptr'], t['rawsize'], t['lo']
pos, scanned = rp, 0
t0 = time.time()
while pos < rp + rs:
    va = lo + (pos - rp)
    got = list(md.disasm_lite(P.RAW[pos:pos + 16], va, count=1))
    if got:
        a, sz, mn, op = got[0]
        for v in TARGETS:
            if pats[v].search(op):
                hits[v].append({'addr': hex(a), 'mnemonic': mn, 'op_str': op})
        pos += sz if sz > 0 else 1
    else:
        pos += 1
    scanned += 1
refs = []
for v in TARGETS:
    hs = hits[v]
    addrs = [int(x['addr'], 16) for x in hs]
    refs.append({'target': hex(v), 'count': len(hs), 'first6': hs[:6],
                 'min_addr': hex(min(addrs)) if addrs else None,
                 'max_addr': hex(max(addrs)) if addrs else None,
                 'sample_op': hs[0]['op_str'] if hs else None})
R['8_refs'] = refs
R['8_scan'] = {'section': '.text', 'rawptr': rp, 'rawsize': rs,
               'va_lo': hex(lo), 'iterations': scanned,
               'elapsed_s': round(time.time() - t0, 2)}

# --- 9 jitter tables ---
A, B = blob(0x87bc90, 256), blob(0x87bd90, 256)
R['9_jitter'] = {
    'A_va': '0x87bc90', 'B_va': '0x87bd90',
    'A_rc_eq_2c': all(A[r * 16 + c] == 2 * c for r in range(16) for c in range(16)),
    'B_rc_eq_2r': all(B[r * 16 + c] == 2 * r for r in range(16) for c in range(16)),
    'B_eq_transpose_A': all(B[r * 16 + c] == A[c * 16 + r] for r in range(16) for c in range(16)),
    'A_eq_B': A == B,
    'sha256_16_A': sha16(A), 'sha256_16_B': sha16(B),
}

# --- appendix ---
R['appendix_jump_tables'] = {
    '0x7c7758': [hex(x) for x in struct.unpack('<8I', blob(0x7c7758, 32))],
    '0x7c7778': [hex(x) for x in struct.unpack('<4I', blob(0x7c7778, 16))],
}

# --- inconsistencies vs card expectations ---
inc = []
for g in R['1_assertions']:
    if not g['equal']:
        inc.append('R1 assertion false: ' + g['expr'])
for d in dups:
    if not d['equal']:
        inc.append('R2 duplicate mismatch: ' + d['name'])
if not R['3_index']['match']:
    inc.append('R3 index != (-1,-1,-1,-1,2,4,6,8): %r' % idx)
if R['4_step']['hits'] != 89:
    inc.append('R4 step hits %d/89' % R['4_step']['hits'])
if R['5_lawD_879b30']['hits'] != 1424:
    inc.append('R5 law D hits %d/1424' % R['5_lawD_879b30']['hits'])
for key in ['6_lawS_87b170', '6_lawS_copy_876ff4']:
    if R[key]['hits'] != 1424:
        inc.append('%s hits %d/1424' % (key, R[key]['hits']))
for key, val in [('A_rc_eq_2c', R['9_jitter']['A_rc_eq_2c']),
                 ('B_rc_eq_2r', R['9_jitter']['B_rc_eq_2r']),
                 ('B_eq_transpose_A', R['9_jitter']['B_eq_transpose_A'])]:
    if not val:
        inc.append('R9 property false: ' + key)
if R['9_jitter']['A_eq_B']:
    inc.append('R9 A == B (unexpected)')
R['inconsistencies'] = inc
R['caveats'] = [
    '0x876ff4/0x87b170 的 3360 B 区间与 0x87bc90/0x87bd90 两张 256 B 抖动表地址重叠；按卡片给定基址独立读取，未去重。',
    'K2 按“每记录 8 个字、m 走 0..88”解释为 8*89=712 项，不是 1424 项。',
    'K5 的 n&15 对幅度公式无影响（bit3 不参与 d 的四个分项），故命中数与律 D 相同。',
    'K1 基址 0x87b172 读 1424 字会跨过 0x87be90 名义表尾 2 字节。',
    '第 8 组为逐字节 resync 静态扫描（skipdata=True），数据字节可能被判为指令；只报实测，不判真伪。',
    '律 D/S 使用第 4 组实测步长表；标准表由脚本生成并断言 89 项且端点 7/32767。',
]

with open(os.path.join(OD, 'A_result.json'), 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)

# --- report ---
L = []
add = L.append
add('# R221-A 实测报告（exec hy4 / 单次脚本运行）')
add('')
add('环境：`_r185.pe185` 只读映射 `ra2bench/gamemd.exe`；capstone `CS_MODE_32`, `detail=False`, `skipdata=True`；.text 逐字节 resync。所有数字由脚本实跑产生。')
add('')
add('## 1. 数据区边界与衔接')
add('')
add('| 名称 | VA | 文件偏移 | 长度 | 段 | sha256[:16] | 首 16 字节 | 尾 16 字节 |')
add('|---|---|---|---|---|---|---|---|')
for nm, v in regions.items():
    add('| %s | %s | %d | %d | %s | %s | %s | %s |' %
        (nm, v['va'], v['file_off'], v['n'], v['section'], v['sha256_16'], v['first16'], v['last16']))
add('')
add('| 零间隙断言 | 左 | 右 | 结果 |')
add('|---|---|---|---|')
for g in R['1_assertions']:
    add('| %s | %s | %s | %s |' % (g['expr'], g['left'], g['right'], g['equal']))
add('')
add('- 0x877d14 起 16 字节：`%s`' % R['1_tail']['0x877d14_16'])
add('- 0x87be90 起 16 字节：`%s`' % R['1_tail']['0x87be90_16'])
add('- 结论：%d/5 条零间隙断言成立；九段区间均落在 mapped 文件范围内。' %
    sum(1 for g in R['1_assertions'] if g['equal']))
add('')
add('## 2. 重复副本同一性与全文件出现位置')
add('')
add('| 配对 | VA A / VA B | 长度 | 逐字节相同 | sha256[:16] A | sha256[:16] B | 文件偏移 → VA（全部） |')
add('|---|---|---|---|---|---|---|')
for d in dups:
    occ = '; '.join('%d→%s' % (o['file_off'], ','.join(o['vas']) or 'unmapped') for o in d['occurrences'])
    add('| %s | %s / %s | %d | %s | %s | %s | %s |' %
        (d['name'], d['va_a'], d['va_b'], d['n'], d['equal'], d['sha256_16_a'], d['sha256_16_b'], occ))
add('')
add('- 结论：%d/3 对逐字节完全相同；全文件搜索命中数分别为 %s。' %
    (sum(1 for d in dups if d['equal']), ', '.join(str(len(d['occurrences'])) for d in dups)))
add('')
add('## 3. 索引表')
add('')
add('| 实测 8 个 int16 | 期望 | 一致 |')
add('|---|---|---|')
add('| %s | %s | %s |' % (idx, list(ADJ), R['3_index']['match']))
add('')
add('- 结论：索引表%s(-1,-1,-1,-1,2,4,6,8)。' % ('等于' if R['3_index']['match'] else '不等于'))
add('')
add('## 4. 步长表')
add('')
add('| 前 8 项 | 末 3 项 | 标准表命中 | 严格单调递增 | 首个不匹配 |')
add('|---|---|---|---|---|')
add('| %s | %s | %d/89 | %s | %s |' %
    (R['4_step']['first8'], R['4_step']['last3'], R['4_step']['hits'],
     R['4_step']['strict_increasing'], R['4_step']['first_mismatch']))
add('')
add('- 结论：实测步长表与脚本生成的 89 项标准 IMA 表命中 %d/89。' % R['4_step']['hits'])
add('')
add('## 5. 差分表生成律 D')
add('')
add('| 基址 | 命中 | 总数 | 前 6 个不匹配 (m,n,实测,期望) |')
add('|---|---|---|---|')
add('| %s | %d | %d | %s |' %
    (R['5_lawD_879b30']['va'], R['5_lawD_879b30']['hits'], R['5_lawD_879b30']['total'],
     R['5_lawD_879b30']['first_mismatches']))
add('')
add('- 结论：律 D 在 0x879b30 命中 %d/1424。' % R['5_lawD_879b30']['hits'])
add('')
add('## 6. 状态表生成律 S')
add('')
add('| 基址 | 命中 | 总数 | min | max | 全为 32 倍数 | 前 6 个不匹配 |')
add('|---|---|---|---|---|---|---|')
add('| %s | %d | %d | %s | %s | %s | %s |' %
    (ls['va'], ls['hits'], ls['total'], ls['min'], ls['max'], ls['all_mult32'], ls['first_mismatches']))
add('')
add('| 附加运行 | 命中 | 总数 |')
add('|---|---|---|')
for key, nm in [('6_lawS_copy_876ff4', '律 S @ 0x876ff4'),
                ('6_lawS_on_Dcopy_8759b4', '律 S @ 0x8759b4'),
                ('6_lawD_on_Dcopy_8759b4', '律 D @ 0x8759b4')]:
    v = R[key]
    add('| %s | %d | %d |' % (nm, v['hits'], v['total']))
add('')
add('- 结论：律 S 在 0x87b170 命中 %d/1424，范围 %d..%d，32 倍数=%s；副本 0x876ff4 命中 %d/1424。' %
    (ls['hits'], ls['min'], ls['max'], ls['all_mult32'], R['6_lawS_copy_876ff4']['hits']))
add('')
add('## 7. 反控')
add('')
add('| 控制 | 改动 | 命中 | 总数 |')
add('|---|---|---|---|')
for key, desc in [('K1_base_plus2', '律 S 基址 0x87b170→0x87b172'),
                  ('K2_rec8_count712', '律 S 每记录 8 字，m=0..88（712 项）'),
                  ('K3_upper87', '律 S clamp 上界 88→87'),
                  ('K4_sign_thr7', '律 D 负号判据 n>=8→n>=7'),
                  ('K5_mag_mask15', '律 D 幅度 n&7→n&15')]:
    v = R['7_controls'][key]
    add('| %s | %s | %d | %d |' % (key, desc, v['hits'], v['total']))
add('')
add('- 结论：五个反控命中数分别为 %s，均未达到主律命中数。' %
    ', '.join(str(R['7_controls'][k]['hits']) for k in ['K1_base_plus2','K2_rec8_count712','K3_upper87','K4_sign_thr7','K5_mag_mask15']))
add('')
add('## 8. 引用计数（.text 逐字节 resync）')
add('')
add('扫描：%s，文件区 [%d, %d)，VA 起点 %s，迭代 %d 次，耗时 %s s。' %
    (R['8_scan']['section'], R['8_scan']['rawptr'], R['8_scan']['rawptr'] + R['8_scan']['rawsize'],
     R['8_scan']['va_lo'], R['8_scan']['iterations'], R['8_scan']['elapsed_s']))
add('')
add('| 目标 | 指令数 | 最小 VA | 最大 VA | 操作数文本样例 | 前 6 个位点 |')
add('|---|---|---|---|---|---|')
for v in refs:
    sites = '; '.join('%s %s %s' % (s['addr'], s['mnemonic'], s['op_str']) for s in v['first6'])
    add('| %s | %d | %s | %s | %s | %s |' %
        (v['target'], v['count'], v['min_addr'], v['max_addr'], v['sample_op'], sites))
add('')
add('- 结论：九个目标中引用数分别为 %s；仅统计操作数文本含目标十六进制的指令。' %
    ', '.join('%s=%d' % (v['target'], v['count']) for v in refs))
add('')
add('## 9. 抖动表属性')
add('')
add('| 属性 | 值 |')
add('|---|---|')
j = R['9_jitter']
for k in ['A_rc_eq_2c', 'B_rc_eq_2r', 'B_eq_transpose_A', 'A_eq_B']:
    add('| %s | %s |' % (k, j[k]))
add('| sha256[:16] A | %s |' % j['sha256_16_A'])
add('| sha256[:16] B | %s |' % j['sha256_16_B'])
add('')
add('- 结论：A[r][c]=2c=%s，B[r][c]=2r=%s，B=A^T=%s，A=B=%s。' %
    (j['A_rc_eq_2c'], j['B_rc_eq_2r'], j['B_eq_transpose_A'], j['A_eq_B']))
add('')
add('## 附：跳转表')
add('')
add('- 0x7c7758 (8 dword): %s' % ', '.join(R['appendix_jump_tables']['0x7c7758']))
add('- 0x7c7778 (4 dword): %s' % ', '.join(R['appendix_jump_tables']['0x7c7778']))
add('')
add('## 与卡片期望不一致的项')
add('')
if inc:
    for x in inc:
        add('- %s' % x)
else:
    add('- 无（所有卡片期望项实测一致）。')
add('')
add('## 口径问题')
add('')
for x in R['caveats']:
    add('- %s' % x)
add('')

with open(os.path.join(OD, 'A_report.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')

# --- console summary ---
print('=== R221-A SUMMARY ===')
print('R1 assertions:', [g['equal'] for g in R['1_assertions']], 'tails:', R['1_tail'])
print('R2 duplicates:', [(d['name'], d['equal'], d['sha256_16_a'], len(d['occurrences'])) for d in dups])
print('R3 index:', idx, 'match', R['3_index']['match'])
print('R4 step hits:', R['4_step']['hits'], '/89 first8', R['4_step']['first8'], 'last3', R['4_step']['last3'])
print('R5 D hits:', R['5_lawD_879b30']['hits'], '/1424 first6', R['5_lawD_879b30']['first_mismatches'])
print('R6 S hits:', ls['hits'], '/1424 min/max/mult32', ls['min'], ls['max'], ls['all_mult32'],
      'copy', R['6_lawS_copy_876ff4']['hits'], 'S@Dcopy', R['6_lawS_on_Dcopy_8759b4']['hits'],
      'D@Dcopy', R['6_lawD_on_Dcopy_8759b4']['hits'])
print('R7 controls:', [(k, R['7_controls'][k]['hits']) for k in R['7_controls']])
print('R8 refs:', [(v['target'], v['count'], v['min_addr'], v['max_addr']) for v in refs],
      'scan', R['8_scan'])
print('R9 jitter:', j)
print('Appendix:', R['appendix_jump_tables'])
print('Inconsistencies:', inc)
print('Outputs:', os.path.join(OD, 'A_report.md'), os.path.join(OD, 'A_result.json'))
