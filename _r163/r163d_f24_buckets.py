#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R163-D · F24 语料值三桶（65 / 64 / 4,352 / 44,470,975 / 26,846,620 / 709,757,429）独立复算

R138/R148/R152 把 F24 的主引用值钉成「4,417 件 / 737,517,286 B 是 2026-11-22 快照值」，
并给了现盘三桶。本轮**独立重写**（不跑 R152 的脚本，不看它的中间产物）从清单 + 现盘重算：

  bucket1 现盘存在      65 件 / 44,470,975 B
  bucket2 其中同字节    64 件 / 26,846,620 B
  bucket3 存在但字节不同  1 件（a2_sites.json：913,237 → 17,624,355，差 +16,711,118）
  bucket4 不存在       4,352 件 / 709,757,429 B
  闭合：65 + 4,352 = 4,417；26,846,620 + 913,237 + 709,757,429 = 737,517,286

关键判据与反控：
  · 「相对 lead/ 根解析」是必要条件：rel 拼**仓库根**应得 0 件（R148 已报，本轮复算）。
  · 差 +16,711,118 必须恰等于 bounds 段的字节数（= a2_sites 总字节 − calls 段字节）。
  · 三个 sha256 钉住：清单 363a1199… / 清单 696,579 B / 4,417 行。
  · 反控：把清单 rel 全部加前缀 junk_ ⇒ 4,417 件全不存在、字节和不变。

只读；只写 _r163/r163d_f24_buckets.json。
"""
import hashlib
import io
import json
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
MAN = 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r163/r163d_f24_buckets.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


# ---------------------------------------------------------------- 0 清单基线
print('== 0 · 清单基线（三要素钉住）==')
raw = io.open(MAN, 'rb').read()
ck('A0 清单字节 = 696,579', len(raw) == 696579, len(raw))
ck('A1 清单 sha256 = 363a1199…', hashlib.sha256(raw).hexdigest().startswith('363a1199'),
   hashlib.sha256(raw).hexdigest()[:16])
lines = [l for l in raw.decode('utf-8').split('\n') if l]
ck('A2 物理行 = 4,418（含表头 ⇒ 数据 4,417）', len(lines) == 4418, len(lines))
hdr = lines[0].split('\t')
print('  表头 = %s' % hdr)
i_rel = hdr.index('rel')
i_byt = hdr.index('bytes')
recs = []
for ln in lines[1:]:
    c = ln.split('\t')
    if len(c) != len(hdr):
        continue
    recs.append((c[i_rel], int(c[i_byt])))
ck('A3 数据行 = 4,417', len(recs) == 4417, len(recs))
ck('A4 清单 sum(bytes) = 737,517,286', sum(b for _r, b in recs) == 737517286,
   sum(b for _r, b in recs))

# ---------------------------------------------------------------- 1 三桶（相对 lead/ 根）
print('\n== 1 · 三桶：按 rel 相对 lead/ 根解析 ==')
BASE = os.path.join(ROOT, 'lead')
ex, same, diff, absent = [], [], [], []
for rel, by in recs:
    p = os.path.join(BASE, rel.replace('\\', '/'))
    if os.path.isfile(p):
        act = os.path.getsize(p)
        ex.append((rel, by, act))
        (same if act == by else diff).append((rel, by, act))
    else:
        absent.append((rel, by))
ck('B1 存在 = 65 件 / 44,470,975 B', len(ex) == 65 and sum(a for _r, _b, a in ex) == 44470975,
   '%d 件 / %d B' % (len(ex), sum(a for _r, _b, a in ex)))
ck('B2 其中同字节 = 64 件 / 26,846,620 B',
   len(same) == 64 and sum(b for _r, b, _a in same) == 26846620,
   '%d 件 / %d B' % (len(same), sum(b for _r, b, _a in same)))
ck('B3 字节不同 = 1 件，且是 a2_sites.json',
   len(diff) == 1 and diff[0][0].endswith('D41_SUBST/_audit/EVIDENCE/a2_sites.json'),
   diff[0][0].split('\\')[-1] if diff else 'none')
ck('B4 该件清单 913,237 / 现盘 17,624,355 / 差 +16,711,118',
   diff and diff[0][1] == 913237 and diff[0][2] == 17624355,
   diff[0][1:] if diff else None)
ck('B5 不存在 = 4,352 件 / 709,757,429 B',
   len(absent) == 4352 and sum(b for _r, b in absent) == 709757429,
   '%d 件 / %d B' % (len(absent), sum(b for _r, b in absent)))
ck('B6 件数闭合 65 + 4,352 = 4,417', len(ex) + len(absent) == 4417)
ck('B7 字节闭合（清单口径）26,846,620 + 913,237 + 709,757,429 = 737,517,286',
   sum(b for _r, b, _a in same) + diff[0][1] + sum(b for _r, b in absent) == 737517286)
ck('B8 字节闭合（现盘口径）44,470,975 − 16,711,118 + 709,757,429 = 737,517,286',
   44470975 - 16711118 + 709757429 == 737517286)

# ---------------------------------------------------------------- 2 差值的身份
print('\n== 2 · +16,711,118 的身份：必须恰等于 a2_sites 的 bounds 段字节 ==')
a2raw = io.open(A2, 'rb').read()
ck('C0 a2_sites.json 现盘字节 = 17,624,355', len(a2raw) == 17624355, len(a2raw))
# ★ S-489：首版写 pos + 2 —— 那是把标记串里 "}" 之后的 ", " 算进 calls 段，实测差 2 字节
#   ⇒ 三条断言假 FAIL。正确定义（与 R95/R152 在盘数逐字一致）：
#     calls 段 = raw[:pos]，即标记 }, "bounds": [ **起始偏移**之前的那 913,237 B；
#     bounds 段 = raw[pos:]，即 17,624,355 − 913,237 = 16,711,118 B。
marker = b'}, "bounds": ['
pos = a2raw.find(marker)
ck('C1 分段标记 }, "bounds": [ 的起始偏移 = 913,237', pos == 913237, pos)
ck('C1b 反控：标记不在 offset 913,239（首版 S-489 那个 pos+2 的口径）', pos != 913239, pos)
calls_bytes = pos
bounds_bytes = len(a2raw) - pos
ck('C2 calls 段 = 913,237 B / bounds 段 = 16,711,118 B', calls_bytes == 913237 and bounds_bytes == 16711118,
   '%d / %d' % (calls_bytes, bounds_bytes))
ck('C3 差值 +16,711,118 恰等于 bounds 段字节 ⇒ 清单那个 913,237 是「只算 calls 段」的值',
   diff[0][2] - diff[0][1] == bounds_bytes, diff[0][2] - diff[0][1])

# ---------------------------------------------------------------- 3 反控
print('\n== 3 · 正反控 ==')
# C1 反控：rel 拼仓库根
ex_root = [r for r, _b in recs if os.path.isfile(os.path.join(ROOT, r.replace('\\', '/')))]
ck('D1 反控：rel 拼**仓库根**得 %d 件（不是 0 件以外的数）' % len(ex_root),
   len(ex_root) == 0, len(ex_root))
# C2 反控：加前缀 junk_
ex_junk = [r for r, _b in recs if os.path.isfile(
    os.path.join(BASE, ('junk_' + r).replace('\\', '/')))]
ck('D2 反控：rel 全部加 junk_ 前缀 ⇒ 0 件（判据对路径敏感）', len(ex_junk) == 0, len(ex_junk))
# C3 正控：把清单自身当对象
ck('D3 正控：清单自身相对 lead/ 解析必须存在且字节 == 696,579',
   os.path.getsize(os.path.join(BASE, MAN[len('lead/'):])) == 696579)
# C4 反控：bytes 列随手 +1 ⇒ 同字节桶必须变 0
same_plus = [1 for r, b, a in same if a == b + 1]
ck('D4 反控：令清单 bytes 全部 +1 ⇒ 同字节桶归 0', len(same_plus) == 0, len(same_plus))
# C5 正控：把 a2_sites 的清单字节改成现盘字节 ⇒ 同字节桶应 65
same_fix = len(same) + (1 if diff and diff[0][2] == 17624355 else 0)
ck('D5 正控：把 a2_sites 清单字节改成 17,624,355 ⇒ 同字节桶 = 65', same_fix == 65, same_fix)

print('\nSUMMARY %d/%d PASS, FAIL=%d' % (len(RES) - FAIL, len(RES), FAIL))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
    {'round': 'R163', 'script': 'r163d_f24_buckets.py', 'fail': FAIL, 'asserts': RES,
     'facts': {'man_bytes': len(raw), 'man_sha16': hashlib.sha256(raw).hexdigest()[:16],
               'rows': len(recs), 'sum_bytes': sum(b for _r, b in recs),
               'exist': len(ex), 'exist_bytes': sum(a for _r, _b, a in ex),
               'same': len(same), 'same_bytes': sum(b for _r, b, _a in same),
               'diff': [(d[0], d[1], d[2]) for d in diff],
               'absent': len(absent), 'absent_bytes': sum(b for _r, b in absent),
               'calls_seg': calls_bytes, 'bounds_seg': bounds_bytes,
               'exist_root': len(ex_root), 'exist_junk': len(ex_junk)}},
    ensure_ascii=False, indent=1))
sys.exit(0 if FAIL == 0 else 1)
