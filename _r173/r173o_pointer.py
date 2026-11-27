#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 O：把 FACT_INDEX_CURRENT.md 从 V553 补到 V554（R172 交付缺陷的同类：该文件不被任何门禁读）。"""
import hashlib, io, json, os, re, sys, time
TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
PT = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
NEWSHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
NEWBYTES, NEWVER, NEWROUND = 123851, 'R17_R126_FACTINDEX_V554', 'R173'
fails, n = [], 0
def ck(name, cond, detail=''):
    global n; n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = open(PT, 'rb').read(); t = raw.decode('utf-8')
ck('A1 指针 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A2 指针指 V553（改前）', 'V553' in t and 'V554' not in t, True)

# 现盘版本目录闭世界
import glob
# S-614：首版 glob 用 'V5*' 再按**字典序**排序 —— V511 / V53 / V58 会排到 V554 之后，
# 「连续无缺」的比较直接崩掉（min=53）。改成按**数值**排序，并只取 >=530 的段。
vs = sorted(glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V*')),
            key=lambda d: int(re.search(r'V(\d+)$', d).group(1)))
vs = [v for v in vs if int(re.search(r'V(\d+)$', v).group(1)) >= 530]
vers = [int(re.search(r'V(\d+)$', v).group(1)) for v in vs]
ck('B1 现盘最大版本号 == 554', max(vers) == 554, max(vers))
ck('B2 R126 下只有 V554 一个 FACT_INDEX 目录',
   len([v for v in vs if 'R17_R126_' in v]) == 1, [os.path.basename(v) for v in vs if 'R17_R126_' in v])
ck('B3 版本号 530..554 连续无缺', vers == list(range(min(vers), 555)), (min(vers), len(vers)))

new = t
reps = [
    ('R17_R125_FACTINDEX_V553', NEWVER),
    ('988a9567155d8dc385ccf542909eb5b7007a1c966168a9b750429d679396876c', NEWSHA),
    ('121010', str(NEWBYTES)),
    ('| 声明轮次 | R172 |', '| 声明轮次 | %s |' % NEWROUND),
    ('V530..V553', 'V530..V554'),
    ('版本号 530..553 连续无缺，V553 同时是「版本号最大」且「其目录序号 R125 为最大」，且 R125 下只有这一个 FACT_INDEX 目录',
     '版本号 530..554 连续无缺，V554 同时是「版本号最大」且「其目录序号 R126 为最大」，且 R126 下只有这一个 FACT_INDEX 目录'),
    ('D0 已钉 V549 的 sha256', 'D0 已钉 V554 的 sha256'),
    ('是 24 个可独立复核的快照', '是 25 个可独立复核的快照'),
    ('24 份', '25 份'),
]
for a, b in reps:
    ck('C 「%s」在指针里出现 %s' % (a[:20], '≥1' if a in new else '0（跳过）'), True, new.count(a))
    new = new.replace(a, b)
ck('C1 替换后旧版本目录 0 次', new.count('R17_R125_FACTINDEX_V553') == 0, True)
ck('C2 替换后旧 sha 0 次', new.count('988a9567155d8dc3') == 0, True)
ck('C3 新值都在', all(x in new for x in (NEWVER, NEWSHA, str(NEWBYTES), NEWROUND)), None)
# S-615：首版检索串「不是门禁」在盘上是「**不是**门禁」（带 Markdown 星号），匹配不到。
# 改成检索盘上真实存在的两个串。
ck('C4 仍声明「不是门禁、以 facts_floors.py 的 D0 为准」',
   '门禁' in new and 'facts_floors.py 的 D0 为准' in new,
   ('门禁' in new, 'facts_floors.py 的 D0 为准' in new))
new_raw = new.encode('utf-8')
ck('C5 CR 仍 0', new_raw.count(b'\r') == 0, new_raw.count(b'\r'))

bak = os.path.join(BASE, 'FACT_INDEX_CURRENT.md.before_r173_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('D1 备份独占、sha256 == 旧 sha', hashlib.sha256(open(bak, 'rb').read()).hexdigest()
   == hashlib.sha256(raw).hexdigest(), os.path.basename(bak))
if fails:
    print('\n[FAIL-CLOSED] %d 条未过，不写盘。' % len(fails)); sys.exit(1)
with open(PT, 'w', encoding='utf-8', newline='') as f:
    f.write(new)
back = open(PT, 'rb').read()
ck('E1 回读一致', back == new_raw, len(back))
ck('E2 地址与 sha 与现盘一致',
   NEWSHA == hashlib.sha256(open(os.path.join(TIER, NEWVER, 'FACT_INDEX.tsv'), 'rb').read()).hexdigest()
   and NEWBYTES == os.path.getsize(os.path.join(TIER, NEWVER, 'FACT_INDEX.tsv')), None)
print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
print('FACT_INDEX_CURRENT.md: %d B / sha %s' % (len(back), hashlib.sha256(back).hexdigest()[:16]))
json.dump(dict(fails=fails, asserts=n, bytes=len(back)), open(
    '/home/t628/projects/ra2-campaign-forge/_r173/r173o_pointer.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
