# -*- coding: utf-8 -*-
"""把 16 份 FACT_INDEX 标记重指向 v5.11，并为 v5.10 目录新建标记。
只改「指向 v5.10」的那处字符串，其余字节不动（回读逐字断言）。
"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')
OLD, NEW = 'R17_R65_FACTINDEX_V510', 'R17_R66_FACTINDEX_V511'

targets = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' in files:
        p = os.path.join(dirpath, 'SUPERSEDED.md')
        t = io.open(p, encoding='utf-8', newline='').read()
        if OLD in t:
            targets.append((p, t))
assert len(targets) == 16, len(targets)

ts = datetime.datetime.now().strftime('%H%M%S')
ok = 0
for p, old_txt in targets:
    b = os.path.join(BK, 'SUPERSEDED.before_v511_%s_%s' % (os.path.basename(os.path.dirname(p)), ts))
    with open(b, 'xb') as f:
        f.write(io.open(p, 'rb').read())
    sha_before = hashlib.sha256(io.open(p, 'rb').read()).hexdigest()

    new_txt = old_txt.replace(OLD, NEW)
    assert new_txt != old_txt
    assert NEW in new_txt
    # CR 不变量：标记文件的 CRLF 计数不得变化
    assert new_txt.count('\r\n') == old_txt.count('\r\n'), p

    with open(p, 'wb') as f:
        f.write(new_txt.encode('utf-8'))
    back = io.open(p, encoding='utf-8', newline='').read()
    assert back == new_txt, p
    # 除替换串外逐字节相同
    assert back.replace(NEW, OLD) == old_txt, p
    ok += 1

# v5.10 目录：新建标记
v510 = os.path.join(R14, OLD, 'SUPERSEDED.md')
assert not os.path.exists(v510), 'already exists'
mark = """# 本目录已作废 —— 请勿引用

**当前权威版本：(v5.11) `R17_R66_FACTINDEX_V511`**

- 作废原因：v5.11 修正了 `F15` / `F35` 两处 `limitations` 缺陷，并按跨家族审计结论修正 `F24` / `F29` 的 `statement` 正文
  （详见 `R17_R66_FACTINDEX_V511\\CHANGES.md`）。
- 本目录内容**字节未动**，仅作历史留存。
- 引用本目录的任何数字时，须同时说明其为 v5.10 历史快照。
"""
with open(v510, 'x', encoding='utf-8', newline='') as f:
    f.write(mark)
assert os.path.exists(v510)

print('rewrote markers = %d' % ok)
print('created marker  = R17_R65_FACTINDEX_V510\\SUPERSEDED.md')

# 复核：全部标记现应指向 v5.11
allm = []
for dirpath, _, files in os.walk(R14):
    if 'SUPERSEDED.md' in files:
        p = os.path.join(dirpath, 'SUPERSEDED.md')
        t = io.open(p, encoding='utf-8', newline='').read()
        allm.append((os.path.basename(dirpath), NEW in t, OLD in t and NEW not in t, 'FACTINDEX' in t.upper()))
bad = [a for a in allm if a[3] and not a[1]]
print('markers total = %d ; still pointing old = %d' % (len(allm), len(bad)))
assert not bad, bad
print('OK')
