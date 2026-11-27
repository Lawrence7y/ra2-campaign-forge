# -*- coding: utf-8 -*-
"""R171 E：FACT_INDEX V550 -> V551，只改 F24.statement 一处（增量由逐字重算给出，不写预算值）。

写入纪律：独占建目录 -> 断言源 sha/字节/CR -> 一次性写 -> 回读逐字节校验。
反控：V550 一字未改；仅 1 行变化；变化行仅 1 个单元变化；其余 54 行×5 列逐字节相同。
"""
import hashlib, io, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIER = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14'))
SRC_DIR = os.path.join(TIER, 'R17_R122_FACTINDEX_V550')
SRC = os.path.join(SRC_DIR, 'FACT_INDEX.tsv')
DST_DIR = os.path.join(TIER, 'R17_R123_FACTINDEX_V551')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

# ---- 1. 源断言（旧 sha / 字节 / CR）----
src_raw = io.open(SRC, 'rb').read()
SHA550 = 'd85034b0b2e42fd34e8140e37e1d27be22cefbc2198d455b0295ef662c58a386'
ck('P0 V550 现盘 sha == d85034b0…（写入前基线）',
   hashlib.sha256(src_raw).hexdigest() == SHA550, hashlib.sha256(src_raw).hexdigest()[:16])
ck('P0b V550 现盘 120,495 B / 55 行 / CR 0',
   len(src_raw) == 120495 and src_raw.count(b'\n') == 55 and b'\r' not in src_raw,
   (len(src_raw), src_raw.count(b'\n'), src_raw.count(b'\r')))

old_text = src_raw.decode('utf-8')
lines = old_text.split('\n')
trailing = lines[-1] == ''
if trailing:
    lines = lines[:-1]
ck('P0c 末尾有换行且行数 55', trailing and len(lines) == 55)

hdr = lines[0].split('\t')
idx_f24 = next(i for i, l in enumerate(lines) if l.split('\t')[0] == 'F24')
cols = lines[idx_f24].split('\t')
ck('P0d F24 在数据行内、5 列', len(cols) == 5, len(cols))

OLD = '（逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）'
NEW = '（**2026-11-22 快照值**，非现盘体量；逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）'
ck('P0e 锚串在原 statement 恰 1 次', cols[1].count(OLD) == 1)
cols[1] = cols[1].replace(OLD, NEW, 1)
new_line = '\t'.join(cols)
lines[idx_f24] = new_line

out_text = '\n'.join(lines) + ('\n' if trailing else '')
out_raw = out_text.encode('utf-8')

# ---- 2. 独占写 ----
if os.path.exists(DST_DIR):
    FAIL.append('P1 DST 目录已存在（须为新建）')
    N[0] += 1; print('FAIL  01. P1 DST 已存在')
else:
    os.makedirs(DST_DIR)
    ck('P1 DST 目录独占新建', os.path.isdir(DST_DIR))
with io.open(DST, 'w', encoding='utf-8', newline='') as f:
    f.write(out_text)
ck('P1b 未覆盖任何既有文件（V550 仍在盘）', os.path.isfile(SRC))

# ---- 3. 回读逐字节校验 ----
back = io.open(DST, 'rb').read()
ck('P2 回读字节数 == %d' % len(out_raw), len(back) == len(out_raw), len(back))
ck('P2b 回读内容逐字节相同', back == out_raw)
ck('P2c 新文件 CR 0 / 55 行 / 末尾单 LF',
   b'\r' not in back and back.count(b'\n') == 55 and back.endswith(b'\n') and not back.endswith(b'\n\n'))
_delta_chars = len(NEW) - len(OLD)
_delta_bytes = len(NEW.encode('utf-8')) - len(OLD.encode('utf-8'))
ck('P2d 字节增量 == (NEW-OLD) 的 UTF-8 字节差 %d（逐字重算，不用预算值）' % _delta_bytes,
   len(back) - len(src_raw) == _delta_bytes, (len(back) - len(src_raw), _delta_bytes))
ck('P2e 增量字符数 %d 与增量字节数 %d 不同 ⇒ 中文占多字节（报告时必须分口径）'
   % (_delta_chars, _delta_bytes), _delta_chars != _delta_bytes)

# ---- 4. 差分行/单元分析 ----
o = [l for l in src_raw.decode('utf-8').split('\n') if l]
n = [l for l in back.decode('utf-8').split('\n') if l]
ck('P3 行数不变 55', len(o) == len(n) == 55)
diffs = [i for i in range(len(o)) if o[i] != n[i]]
ck('P3b 差分行恰 1 行', len(diffs) == 1, diffs)
ck('P3c 该行 fact_id == F24', n[diffs[0]].split('\t')[0] == 'F24' if diffs else False)
cell = []
for k in range(5):
    if o[diffs[0]].split('\t')[k] != n[diffs[0]].split('\t')[k]:
        cell.append(hdr[k])
ck('P3d 变化单元恰 1 个且是 statement', cell == ['statement'], cell)
same = all(o[i].split('\t')[k] == n[i].split('\t')[k]
           for i in range(len(o)) if i not in diffs for k in range(5))
ck('P3e 其余 54 行 × 5 列逐字节相同', same)
gen = [i for i in range(len(o)) if i not in diffs and o[i] != n[i]]
ck('P3f 无「整行不变但列序变了」的行', gen == [])

# ---- 5. V550 未被改（反控）----
ck('P4 V550 现盘 sha 仍 == d85034b0…（本轮未改母本）',
   hashlib.sha256(io.open(SRC, 'rb').read()).hexdigest() == SHA550)

print('\n  V551 = %d B / %d 行 / CR %d / sha256 %s'
      % (len(back), back.count(b'\n'), back.count(b'\r'), hashlib.sha256(back).hexdigest()[:16]))
print('  V551 full sha256 = %s' % hashlib.sha256(back).hexdigest())
records = {'V551_bytes': len(back), 'V551_lines': back.count(b'\n'),
           'V551_sha256': hashlib.sha256(back).hexdigest()}
io.open(os.path.join(HERE, 'r171e_v551.json'), 'w', encoding='utf-8').write(
    __import__('json').dumps(records, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
