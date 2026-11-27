#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 D：给 F24 的三桶漂移补「测量时刻 + 清单 sha」的可重跑入口（R151 待办 3）。

判据：把此刻的现盘读数与清单 sha、脚本 sha、测量时刻 UTC 一起钉成一个记录，
使任何人可在同一脚本 + 同一清单 sha 下复现 65/64/4,352 三桶。
正控：三桶件数之和 == 4,417；反控：rel 拼仓库根 ⇒ 存在 0 件。
"""
import hashlib, json, os, subprocess, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TF = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
SCRIPT = os.path.join(ROOT, '_r148/r148b_f24_survival.py')
OUT = os.path.join(ROOT, '_r152/r152d_buckets_pin.json')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


# 冻结纪律：本文件一旦存在即视为「已钉时刻」，不再重写 —— 否则每跑一次 measured_at 变一次，
# 引用它的 v5.41 正文就会跟着变（首版就踩了这个坑，见 S-377）。
FROZEN = os.path.exists(OUT)
if FROZEN:
    prev = json.load(open(OUT))
    print('  已存在测量记录 ⇒ 冻结复用（不重写 OUT）')
    print('  冻结 measured_at =', prev['measured_at_utc'])
raw = open(TF, 'rb').read()
tsha = hashlib.sha256(raw).hexdigest()
rows = [l.split('\t') for l in raw.decode('utf-8').split('\n')[1:] if l.strip()]
ck('1.1 清单 4,417 数据行', len(rows) == 4417, len(rows))
ck('1.2 清单 696,579 B / sha 363a1199…',
   len(raw) == 696579 and tsha.startswith('363a1199'), (len(raw), tsha[:16]))
ck('1.3 清单 sum(bytes) == 737,517,286',
   sum(int(r[1]) for r in rows) == 737517286, sum(int(r[1]) for r in rows))

script_sha = hashlib.sha256(open(SCRIPT, 'rb').read()).hexdigest()
measured_at = prev['measured_at_utc'] if FROZEN else time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

# 逐行 stat（与 r148b 同口径，独立重写一遍以免「只是复跑别人的脚本」）
exist, exist_b, same, same_b, diff, miss, miss_b = 0, 0, 0, 0, [], 0, 0
for r in rows:
    p = os.path.join(ROOT, 'lead', r[0])
    want = int(r[1])
    if os.path.exists(p):
        got = os.path.getsize(p)
        exist += 1
        exist_b += got
        if got == want:
            same += 1
            same_b += want
        else:
            diff.append({'rel': r[0], 'list': want, 'disk': got})
    else:
        miss += 1
        miss_b += want
print('  现盘存在 %d 件 / %d B；同字节 %d 件 / %d B；不同 %d 件；不存在 %d 件 / %d B'
      % (exist, exist_b, same, same_b, len(diff), miss, miss_b))
ck('2.1 三桶件数之和 == 4,417（划分完备）', exist + miss == 4417 and same + len(diff) == exist,
   (exist, miss, same, len(diff)))
ck('2.2 三桶字节之和 == 737,517,286（按口径归一后）',
   same_b + sum(d['list'] for d in diff) + miss_b == 737517286,
   same_b + sum(d['list'] for d in diff) + miss_b)
ck('2.3 存在 65 件 / 44,470,975 B', (exist, exist_b) == (65, 44470975), (exist, exist_b))
ck('2.4 同字节 64 件 / 26,846,620 B', (same, same_b) == (64, 26846620), (same, same_b))
ck('2.5 不存在 4,352 件 / 709,757,429 B', (miss, miss_b) == (4352, 709757429), (miss, miss_b))
ck('2.6 差异恰 1 件且为 a2_sites.json（913,237 -> 17,624,355，差 +16,711,118）',
   len(diff) == 1 and diff[0]['rel'].endswith('a2_sites.json')
   and diff[0]['list'] == 913237 and diff[0]['disk'] == 17624355
   and diff[0]['disk'] - diff[0]['list'] == 16711118, diff)
# 反控
miss_root = sum(1 for r in rows if not os.path.exists(os.path.join(ROOT, r[0])))
ck('2.7 反控 rel 拼仓库根 ⇒ 存在 0 件', exist == 0 if False else miss_root == 4417, miss_root)

rec = {'measured_at_utc': measured_at,
       'list': {'path': 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv',
                'bytes': len(raw), 'sha256': tsha, 'rows': len(rows)},
       'script': {'path': '_r148/r148b_f24_survival.py', 'sha256': script_sha},
       'buckets': {'exists': {'files': exist, 'disk_bytes': exist_b},
                   'exists_same_bytes': {'files': same, 'list_bytes': same_b},
                   'exists_diff_bytes': {'files': len(diff), 'detail': diff},
                   'missing': {'files': miss, 'list_bytes': miss_b}},
       'rust_proof': {'same_list_plus_diff_list_plus_missing': same_b + 913237 + miss_b},
       'fails': fails}
if not FROZEN:
    json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)
else:
    ck('冻结记录与本次实测逐项相同（三桶 + 清单 sha + 脚本 sha）',
       json.load(open(OUT))['buckets'] == rec['buckets']
       and json.load(open(OUT))['list'] == rec['list']
       and json.load(open(OUT))['script'] == rec['script'],
       (json.load(open(OUT))['buckets'], json.load(open(OUT))['script']['sha256'][:16]))
print('  测量时刻 UTC =', measured_at)
print('  清单 sha256    =', tsha)
print('  r148b sha256   =', script_sha[:16])
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
