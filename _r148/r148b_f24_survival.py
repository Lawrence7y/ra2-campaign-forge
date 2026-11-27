#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 B：F24 语料值失效期三桶复算（清单 vs 现盘逐行 stat）。
三口径：
  ① 现盘存在（不看字节）   件数 + 现盘实际字节
  ② 现盘存在且字节与清单同 件数 + 清单字节
  ③ 存在但字节不同（应恰 1 件 = a2_sites.json，差 +16,711,118 B）
反控：把 rel 拼到仓库根而非 lead/ 根 → 存在数应为 0。
"""
import hashlib, io, json, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
TF = os.path.join(LEAD, 'next_re_20261117_r14', 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


raw = open(TF, 'rb').read()
lines = raw.decode('utf-8').split('\n')
rows = [l.split('\t') for l in lines[1:] if l.strip()]
ck('0.1 清单 4,417 行', len(rows) == 4417, len(rows))
ck('0.2 清单逐行 4 列', all(len(r) == 4 for r in rows), '')
ck('0.3 清单 sum(bytes) == 737,517,286', sum(int(r[1]) for r in rows) == 737517286,
   sum(int(r[1]) for r in rows))


def scan(base):
    exist = []
    same = []
    diff = []
    miss = []
    for r in rows:
        p = os.path.join(base, r['rel'] if isinstance(r, dict) else r[0])
        b = int(r[1] if isinstance(r, list) else r['bytes'])
        if os.path.isfile(p):
            a = os.path.getsize(p)
            exist.append((r[0] if isinstance(r, list) else r['rel'], a, b))
            if a == b:
                same.append(a)
            else:
                diff.append((r[0] if isinstance(r, list) else r['rel'], b, a))
        else:
            miss.append((r[0] if isinstance(r, list) else r['rel'], b))
    return exist, same, diff, miss


ex, sm, df, ms = scan(LEAD)
ck('1 存在+相同+不同+不存在 == 4,417（划分不重不漏）',
   len(ex) + len(ms) == 4417 and len(sm) + len(df) == len(ex),
   (len(ex), len(sm), len(df), len(ms)))
n_exist = len(ex)
b_exist = sum(a for _, a, _ in ex)
n_same = len(sm)
b_same = sum(sm)
ck('2 口径① 65 件 / 44,470,975 B（现盘实际字节）', n_exist == 65 and b_exist == 44470975,
   (n_exist, b_exist))
ck('3 口径② 64 件 / 26,846,620 B（清单字节）', n_same == 64 and b_same == 26846620,
   (n_same, b_same))
ck('4 口径③ 差异恰 1 件', len(df) == 1, df)
if df:
    ck('5 差异件是 a2_sites.json 且清单 913,237 / 现盘 17,624,355 / 差 +16,711,118',
       df[0][0].endswith('D41_SUBST/_audit/EVIDENCE/a2_sites.json')
       and df[0][1] == 913237 and df[0][2] == 17624355 and df[0][2] - df[0][1] == 16711118,
       df[0])
b_miss = sum(b for _, b in ms)
ck('6 不存在 4,352 件 / 709,757,429 B', len(ms) == 4352 and b_miss == 709757429,
   (len(ms), b_miss))
# 精确闭合：清单页值(存在65,取清单字节) + 清单(不存在4352) == 737,517,286
b_list_exist = sum(b for _, _, b in ex)
ck('7 存在65 的清单字节和 == 26,846,620 + 913,237 (= 27,759,857)',
   b_list_exist == 27759857, b_list_exist)
ck('8 清单(存在65) + 清单(不存在4352) == 737,517,286',
   b_list_exist + b_miss == 737517286, b_list_exist + b_miss)
# 现盘字节口径：现盘(存在65) − 差异增量 + 清单(不存在4352) == 737,517,286
ck('9 现盘(65) − 16,711,118 + 清单(4352) == 737,517,286',
   b_exist - 16711118 + b_miss == 737517286, b_exist - 16711118 + b_miss)
ck('9b 反控：不做 −16,711,118 修正则超出清单总值恰 16,711,118（差异项确实必须扣）',
   b_exist + b_miss - 737517286 == 16711118, b_exist + b_miss - 737517286)
# 反控
ex2, sm2, df2, ms2 = scan(ROOT)
ck('10 反控：rel 拼到仓库根 ⇒ 存在 0 件（证明根选对了）', len(ex2) == 0, len(ex2))

print('\n现盘存在 %d 件 / %d B；同字节 %d 件 / %d B；不同 %d 件；不存在 %d 件 / %d B'
      % (n_exist, b_exist, n_same, b_same, len(df), len(ms), b_miss))
json.dump(dict(fails=fails, exist=n_exist, exist_bytes=b_exist, same=n_same, same_bytes=b_same,
               diff=df, missing=len(ms), missing_bytes=b_miss,
               list_sha=hashlib.sha256(raw).hexdigest()[:16]),
          open(os.path.join(ROOT, '_r148', 'r148b_f24_survival.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
