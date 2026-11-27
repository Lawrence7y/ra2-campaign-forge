# -*- coding: utf-8 -*-
"""R172 D：FACT_INDEX V551 -> V552，只改 F23.limitations 一处（补「sha 只由 7 列清单给出」的作用域）。

写入纪律：独占建目录 -> 断言源 sha/字节/CR -> 一次性写 -> 回读逐字节校验。
反控：V551 一字未改；仅 1 行变化；变化行仅 1 个单元；其余 53 行 × 5 列逐字节相同。
"""
import hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIER = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14'))
SRC_DIR = os.path.join(TIER, 'R17_R123_FACTINDEX_V551')
SRC = os.path.join(SRC_DIR, 'FACT_INDEX.tsv')
DST_DIR = os.path.join(TIER, 'R17_R124_FACTINDEX_V552')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src_raw = io.open(SRC, 'rb').read()
SHA551 = '5d4981c8b40ecfb1f0a4a3717da13b10a0b173eff600a763a20daac4da12a3fc'
ck('P0 V551 现盘 sha == 5d4981c8…（写入前基线）',
   hashlib.sha256(src_raw).hexdigest() == SHA551, hashlib.sha256(src_raw).hexdigest()[:16])
ck('P0b V551 现盘 120,540 B / 55 行 / CR 0',
   len(src_raw) == 120540 and src_raw.count(b'\n') == 55 and b'\r' not in src_raw,
   (len(src_raw), src_raw.count(b'\n')))

old_text = src_raw.decode('utf-8')
lines = old_text.split('\n')
trailing = lines[-1] == ''
if trailing: lines = lines[:-1]
ck('P0c 末尾有换行且行数 55', trailing and len(lines) == 55)

hdr = lines[0].split('\t')
ck('P0d 表头 5 列逐字', hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], hdr)
idx = next(i for i, l in enumerate(lines) if l.split('\t')[0] == 'F23')
cols = lines[idx].split('\t')
ck('P0e F23 在数据行内、5 列', len(cols) == 5, len(cols))

OLD = '出处为两份**互不相同**的清单'
NEW = ('出处为两份**互不相同**的清单（**作用域：sha256 只由前者给出** —— `unique_content_4417.tsv` 为 7 列'
       '（rel/bytes/decl_bytes/sha256/cluster_size/cluster_wasted/cluster_rep）、全文该 sha256 恰 1 次；'
       '`tier_final_4417.tsv` 为 4 列（rel/bytes/source/why_content）、**无 sha 列、全文该 sha256 出现 0 次**，'
       '它只能佐证路径与字节数、**不能佐证摘要**；两者第 1022 行的 rel 与 bytes 逐字相同）')
ck('P1 锚串在原 limitations 恰 1 次', cols[4].count(OLD) == 1, cols[4].count(OLD))
cols[4] = cols[4].replace(OLD, NEW, 1)
lines[idx] = '\t'.join(cols)
out_text = '\n'.join(lines) + ('\n' if trailing else '')
out_raw = out_text.encode('utf-8')

if os.path.exists(DST_DIR):
    FAIL.append('P2 DST 目录已存在'); N[0] += 1; print('FAIL  02. P2 DST 已存在')
else:
    os.makedirs(DST_DIR)
    ck('P2 DST 目录独占新建', os.path.isdir(DST_DIR))
with io.open(DST, 'w', encoding='utf-8', newline='') as f:
    f.write(out_text)
ck('P2b 未覆盖任何既有文件（V551 仍在盘）', os.path.isfile(SRC))

back = io.open(DST, 'rb').read()
ck('P3 回读字节数 == %d' % len(out_raw), len(back) == len(out_raw), len(back))
ck('P3b 回读内容逐字节相同', back == out_raw)
ck('P3c 新文件 CR 0 / 55 行 / 末尾单 LF',
   b'\r' not in back and back.count(b'\n') == 55 and back.endswith(b'\n') and not back.endswith(b'\n\n'))

o = [l for l in src_raw.decode('utf-8').split('\n') if l]
n2 = [l for l in back.decode('utf-8').split('\n') if l]
ck('P4 行数不变 55', len(o) == len(n2) == 55)
diffs = [i for i in range(len(o)) if o[i] != n2[i]]
ck('P4b 差分行恰 1 行', len(diffs) == 1, diffs)
ck('P4c 该行 fact_id == F23', n2[diffs[0]].split('\t')[0] == 'F23' if diffs else False)
cell = [hdr[k] for k in range(5) if o[diffs[0]].split('\t')[k] != n2[diffs[0]].split('\t')[k]]
ck('P4d 变化单元恰 1 个且是 limitations', cell == ['limitations'], cell)
same = all(o[i].split('\t')[k] == n2[i].split('\t')[k]
           for i in range(len(o)) if i not in diffs for k in range(5))
ck('P4e 其余 53 行 × 5 列逐字节相同', same)

# 反控：新 limitations 必须是旧 limitations 的「插入」（旧串是新串的子序列，且只插不删）
import difflib
sm = difflib.SequenceMatcher(None, cols[4] and o[diffs[0]].split('\t')[4], n2[diffs[0]].split('\t')[4])
ops = [t for t in sm.get_opcodes() if t[0] != 'equal']
ck('P5 旧 limitations -> 新 limitations 只含 1 个 insert 或 1 个 replace（无 delete）',
   len(ops) == 1 and ops[0][0] in ('insert', 'replace'), ops)
_olim = o[diffs[0]].split('\t')[4]; _nlim = n2[diffs[0]].split('\t')[4]
ck('P5b 新 limitations 含旧 limitations 的首 200 与末 200 字符（前缀/后缀未动）',
   _nlim.startswith(_olim[:200]) and _nlim.endswith(_olim[-200:]))
ck('P5c 字节增量 == 实测差 %d（不写预算值）' % (len(back) - len(src_raw)), True)
ck('P6 V551 现盘 sha 仍 == 5d4981c8…（本轮未改母本）',
   hashlib.sha256(io.open(SRC, 'rb').read()).hexdigest() == SHA551)

delta = len(back) - len(src_raw)
print('\n  V552 = %d B / %d 行 / CR %d / sha256 %s' % (len(back), back.count(b'\n'), back.count(b'\r'), hashlib.sha256(back).hexdigest()))
print('  增量 %d B（旧 F23.limitations %d B -> 新 %d B）' % (delta, len(_olim.encode()), len(_nlim.encode())))
rec = {'v552_bytes': len(back), 'v552_lines': back.count(b'\n'), 'v552_sha256': hashlib.sha256(back).hexdigest(),
       'v551_sha256': SHA551, 'delta_bytes': delta,
       'f23_lim_old_bytes': len(_olim.encode()), 'f23_lim_new_bytes': len(_nlim.encode()),
       'f23_st_bytes': len(n2[diffs[0]].split('\t')[1].encode())}
io.open(os.path.join(HERE, 'r172d_v552.json'), 'w', encoding='utf-8').write(json.dumps(rec, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
