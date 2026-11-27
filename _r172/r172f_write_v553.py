# -*- coding: utf-8 -*-
"""R172 F：FACT_INDEX V552 -> V553，只改 F24.statement 一处（给溯源链终值补「快照值」后置限定）。

动机（R172 实测，r172a/r172b）：分句级判据下 F24 的 4,417 共 10 次，
BODY 型（后跟「件/文件」的语料体量）4 次，其中 ST@959 是唯一不在场的一次；
R171 判为「该改」的 ST@449 其实在括注内已带限定（分句级在场） ⇒ R171 的指认方向反了。

写入纪律：独占建目录 -> 断言源 sha/字节/CR -> 一次性写 -> 回读逐字节校验。
"""
import difflib, hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIER = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14'))
SRC = os.path.join(TIER, 'R17_R124_FACTINDEX_V552', 'FACT_INDEX.tsv')
DST_DIR = os.path.join(TIER, 'R17_R125_FACTINDEX_V553')
DST = os.path.join(DST_DIR, 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src_raw = io.open(SRC, 'rb').read()
SHA552 = '28155d363b75de4832d81ce7cf2e6a5bf432e7845aaf0815ccf32529c8361d42'
ck('P0 V552 现盘 sha == 28155d36…', hashlib.sha256(src_raw).hexdigest() == SHA552, hashlib.sha256(src_raw).hexdigest()[:16])
ck('P0b V552 120,962 B / 55 行 / CR 0',
   len(src_raw) == 120962 and src_raw.count(b'\n') == 55 and b'\r' not in src_raw, len(src_raw))

text = src_raw.decode('utf-8')
lines = text.split('\n')
trailing = lines[-1] == ''
if trailing: lines = lines[:-1]
hdr = lines[0].split('\t')
idx = next(i for i, l in enumerate(lines) if l.split('\t')[0] == 'F24')
cols = lines[idx].split('\t')
ck('P0c F24 5 列 / statement 10565 B', len(cols) == 5 and len(cols[1].encode()) == 10565,
   (len(cols), len(cols[1].encode())))

OLD = '→ 4,416 件 / 736,151,921 B → **4,417 件 / 737,517,286 B**）：构成 ='
NEW = '→ 4,416 件 / 736,151,921 B → **4,417 件 / 737,517,286 B**（**2026-11-22 快照值，非现盘体量**））：构成 ='
ck('P1 锚串在原 statement 恰 1 次', cols[1].count(OLD) == 1, cols[1].count(OLD))
cols[1] = cols[1].replace(OLD, NEW, 1)
lines[idx] = '\t'.join(cols)
out_text = '\n'.join(lines) + ('\n' if trailing else '')
out_raw = out_text.encode('utf-8')

if os.path.exists(DST_DIR):
    FAIL.append('P2 DST 存在'); N[0] += 1; print('FAIL P2')
else:
    os.makedirs(DST_DIR); ck('P2 DST 独占新建', True)
io.open(DST, 'w', encoding='utf-8', newline='').write(out_text)
back = io.open(DST, 'rb').read()
ck('P3 回读逐字节相同 / CR 0 / 55 行', back == out_raw and b'\r' not in back and back.count(b'\n') == 55)
ck('P3b V552 一字未改', hashlib.sha256(io.open(SRC, 'rb').read()).hexdigest() == SHA552)

o = [l for l in text.split('\n') if l]
n2 = [l for l in back.decode('utf-8').split('\n') if l]
diffs = [i for i in range(len(o)) if o[i] != n2[i]]
ck('P4 差分行恰 1 行且 fact_id == F24', len(diffs) == 1 and n2[diffs[0]].split('\t')[0] == 'F24', diffs)
cell = [hdr[k] for k in range(5) if o[diffs[0]].split('\t')[k] != n2[diffs[0]].split('\t')[k]]
ck('P4b 变化单元恰 1 个且是 statement', cell == ['statement'], cell)
ck('P4c 其余 53 行 × 5 列逐字节相同',
   all(o[i].split('\t')[k] == n2[i].split('\t')[k] for i in range(len(o)) if i not in diffs for k in range(5)))
sm = difflib.SequenceMatcher(None, o[diffs[0]].split('\t')[1], n2[diffs[0]].split('\t')[1])
ops = [t for t in sm.get_opcodes() if t[0] != 'equal']
ck('P4d 旧->新 statement 只含 1 个 insert', len(ops) == 1 and ops[0][0] == 'insert', ops)

delta = len(back) - len(src_raw)
print('\n  V553 = %d B / %d 行 / CR %d / sha256 %s' % (len(back), back.count(b'\n'), back.count(b'\r'), hashlib.sha256(back).hexdigest()))
print('  增量 %d B' % delta)
ck('P5 增量 == 实测差 %d（逐字重算，不写预算值）' % delta,
   delta == len(NEW.encode()) - len(OLD.encode()), (delta, len(NEW.encode()) - len(OLD.encode())))
rec = {'v553_bytes': len(back), 'v553_sha256': hashlib.sha256(back).hexdigest(), 'delta_bytes': delta,
       'f24_st_bytes': len(cols[1].encode()), 'v552_sha256': SHA552}
io.open(os.path.join(HERE, 'r172f_v553.json'), 'w', encoding='utf-8').write(json.dumps(rec, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
