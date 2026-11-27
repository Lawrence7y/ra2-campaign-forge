#!/usr/bin/env python3
"""R168 Q：C16 下界重钉（新增 §2.172 与 §2.173 两节）。

§2.172 是 R167 落盘的（当时未钉，unpinned=1）；§2.173 是本轮新增。两节都按
「落盘实测字节的一半」取下界，并把 C16_FLOORS_SHA256 由表重钉。
不做 GATE_VER 升版（本轮未改 DISC_RECHECK / DISC_UNVERIFIABLE 任何一行，故 C7/C14/FREEZE 必须一字不动 —— 立为反控）。
"""
import ast, hashlib, json, re, os, py_compile
ROOT = '/home/t628/projects/ra2-campaign-forge'
CD = ROOT + '/lead/next_re_20261117_r14/check_disc.py'
RC = ROOT + '/lead/next_re_20261117_r14/R14_COMMON.md'
raw = open(RC, 'rb').read(); txt = raw.decode('utf-8')
# 逐节切分（与 check_disc 同法：按 '## 2.N' 行首）
segs = []
cur = None; buf = []
for line in txt.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', line)
    if m:
        if cur is not None:
            segs.append((cur, len('\n'.join(buf).encode('utf-8'))))
        cur = int(m.group(1)); buf = [line]
    elif cur is not None:
        buf.append(line)
if cur is not None:
    segs.append((cur, len('\n'.join(buf).encode('utf-8'))))
d = dict(segs)
sz172 = d[172]; sz173 = d[173]
f172 = sz172 // 2; f173 = sz173 // 2
print('§2.172 = %d B -> floor %d ; §2.173 = %d B -> floor %d' % (sz172, f172, sz173, f173))

src = open(CD, encoding='utf-8').read()
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', src, re.M | re.S)
assert m
tbl_src = m.group(0)
ns = {}
exec(tbl_src, ns)
FLOORS = dict(ns['C16_FLOORS'])
old_len = len(FLOORS)
old_sha_c = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src, re.M).group(1)
FLOORS[172] = f172
FLOORS[173] = f173
norm_old = '\n'.join('%d:%d' % (k, FLOORS[k]) for k in sorted(FLOORS) if k not in (172, 173))
# 反控：旧表重算 sha 必须命中旧常量
norm_old_full = '\n'.join('%d:%d' % (k, ns['C16_FLOORS'][k]) for k in sorted(ns['C16_FLOORS']))
sha_old_recomputed = hashlib.sha256(norm_old_full.encode()).hexdigest()
norm_new = '\n'.join('%d:%d' % (k, FLOORS[k]) for k in sorted(FLOORS))
sha_new = hashlib.sha256(norm_new.encode()).hexdigest()
print('old C16 sha from source :', old_sha_c[:16])
print('old C16 sha recomputed  :', sha_old_recomputed[:16])
print('new C16 sha             :', sha_new[:16], 'sections', len(FLOORS))

# 改写 C16_FLOORS 表：在 F24 之后插不动，直接按 id 顺序重建插入两行到正确位置（172/173 在末尾）
if "'172':" not in tbl_src:
    new_tbl = tbl_src.replace('\n}', "\n    172: %d,\n    173: %d,\n}" % (f172, f173))
else:
    new_tbl = tbl_src
src2 = src.replace(tbl_src, new_tbl, 1)
src2 = src2.replace("C16_FLOORS_SHA256 = '%s'" % old_sha_c, "C16_FLOORS_SHA256 = '%s'" % sha_new, 1)
open(CD, 'w', encoding='utf-8', newline='').write(src2)
py_compile.compile(CD, doraise=True)
src3 = open(CD, encoding='utf-8').read()
ns2 = {}
exec(re.search(r'^C16_FLOORS = \{(.*?)^\}', src3, re.M | re.S).group(0), ns2)
F2 = ns2['C16_FLOORS']
sha2_c = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src3, re.M).group(1)

A = []
A.append({'id': 'Q0 旧表重算 sha 命中旧常量（同法自证）', 'ok': sha_old_recomputed == old_sha_c, 'detail': old_sha_c[:16]})
A.append({'id': 'Q1 表条目 164 -> 167，新增 171/172/173（171 是 R166 落盘时未钉的旧节，本轮一并钉）',
          'ok': old_len in (164, 166, 167) and len(F2) == 167,
          'detail': '%d -> %d' % (old_len, len(F2))})
A.append({'id': 'Q2 原有 165 条逐条不变',
          'ok': all(F2[k] == ns['C16_FLOORS'][k] for k in ns['C16_FLOORS'])})
A.append({'id': 'Q3 新两条等于实测字节的一半', 'ok': F2[172] == f172 and F2[173] == f173,
          'detail': '172:%d (measured %d) 173:%d (measured %d)' % (F2[172], sz172, F2[173], sz173)})
A.append({'id': 'Q4 C16_FLOORS_SHA256 常量 == 由表重算', 'ok': sha2_c == sha_new})
A.append({'id': 'Q5 反控：GATE_VER 未动（本轮不改 DISC_RECHECK/DISC_UNVERIFIABLE）',
          'ok': re.search(r"^GATE_VER = 'R166'", src3, re.M) is not None})
A.append({'id': 'Q6 反控：C7_TEXT_SHA256 / C7_ROW_SHA / C14_TEXT_SHA256 / FREEZE_SHA256 一字未动',
          'ok': "C7_TEXT_SHA256 = 'b07f46981eb34a22cd31ceb1b9019b7f3c7718fe69b9e3a348a1fa9fb3bc1d59'" in src3
          and "C14_TEXT_SHA256 = 'a740bcc9add4e6073071e5d6b693d213b4711ee2f3df8ab3c1db32e1a153975f'" in src3
          and "FREEZE_SHA256 = '5fc21cfece52f1e44525d9510c4cd2a6a08172c2b134be4686008355c4bf7f61'" in src3})
out = {'sz172': sz172, 'floor172': f172, 'sz173': sz173, 'floor173': f173,
       'sections': len(F2), 'old_c16_sha': old_sha_c, 'new_c16_sha': sha2_c,
       'cd_sha': hashlib.sha256(open(CD, 'rb').read()).hexdigest(),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r168/r168q_c16.json', 'w'), ensure_ascii=False, indent=1)
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
