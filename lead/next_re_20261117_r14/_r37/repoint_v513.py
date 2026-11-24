# -*- coding: utf-8 -*-
"""标记重指向 v5.13：18 份现指 v5.12 的重写 + 为 v5.12 目录新建标记。"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')
OLD, NEW = 'R17_R67_FACTINDEX_V512', 'R17_R69_FACTINDEX_V513'

targets = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' not in files:
        continue
    p = os.path.join(dirpath, 'SUPERSEDED.md')
    t = io.open(p, encoding='utf-8', newline='').read()
    if NEW in t:
        continue
    if OLD in t:
        targets.append((p, t))
print('to rewrite =', len(targets))
assert len(targets) == 18, len(targets)

ts = datetime.datetime.now().strftime('%H%M%S')
for p, old_txt in targets:
    nm = 'SUPERSEDED.before_v513_%s_%s' % (os.path.basename(os.path.dirname(p)), ts)
    with open(os.path.join(BK, nm), 'xb') as f:
        f.write(io.open(p, 'rb').read())
    new_txt = old_txt.replace(OLD, NEW)
    assert new_txt != old_txt
    assert new_txt.count('\r\n') == old_txt.count('\r\n')
    with open(p, 'wb') as f:
        f.write(new_txt.encode('utf-8'))
    back = io.open(p, encoding='utf-8', newline='').read()
    assert back == new_txt
    assert back.replace(NEW, OLD) == old_txt
print('rewrote =', len(targets))

v512 = os.path.join(R14, OLD, 'SUPERSEDED.md')
if not os.path.exists(v512):
    mark = """# 本目录已作废 —— 请勿引用

**当前权威版本：(v5.13) `R17_R69_FACTINDEX_V513`**

- 作废原因：v5.13 修了 `F24` 的单位错（1.29 实为 GiB、58 倍只是体积比、规模是快照）、
  把 `F29` 的「InterlockedIncrement」由推断升级为导入表证实、并给 `F14` 加了三个数据锚。
- 本目录内容**字节未动**，仅作历史留存。
- 引用本目录任何数字时，须说明其为 v5.12 历史快照。
"""
    with open(v512, 'x', encoding='utf-8', newline='') as f:
        f.write(mark)
    print('created marker for v5.12')

# 复核
tot = pointing = 0
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' not in files:
        continue
    tot += 1
    t = io.open(os.path.join(dirpath, 'SUPERSEDED.md'), encoding='utf-8', newline='').read()
    if NEW in t:
        pointing += 1
print('markers total = %d ; pointing v5.13 = %d ; other(台账卡) = %d' % (tot, pointing, tot - pointing))
