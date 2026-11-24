# -*- coding: utf-8 -*-
"""FACT_INDEX v5.15：F24 的规模段重写（吸收 T4 三项必改 + T2 成立部分 + 我自己的复算）。
纪律：读 v5.14 → 只改 F24 statement/limitations → 断言其余 53 行逐字节不变 → 禁零宽字符。
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R71_FACTINDEX_V514')
DST  = os.path.join(R14, 'R17_R73_FACTINDEX_V515')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54

rows = [l.split('\t') for l in data]
byid = {r[0]: r for r in rows}
f24 = byid['F24']
old_stmt, old_lim = f24[1], f24[4]

# 旧的规模段（从「675 行已做」到「不是「指针没连上」。」）
import re
m = re.search(r'675 行已做有界内容级搜索.*?不是「指针没连上」。', old_stmt, re.S)
assert m, old_stmt

NEW_SCALE = ('675 行已做有界内容级搜索（primary 口径 = 6 类扩展名 .tsv/.txt/.json/.md/.csv/.log）。'
             '**规模数只能当「某次测量的快照」引用，不能当常量**：'
             '① 2026-11-21 记录值 23,791 文件 / 1,383,739,755 B（当日「无产物」，未被度量自身产物污染）；'
             '② 2026-11-22 复测 24,693 文件 / 1,586,613,509 B，该数**含**度量自身产物 '
             '`_hits_primary.tsv` 1 文件 / 80,580,525 B ——`mev675.py` 的 `stage_scale` 只排除 `.git` 与 `--out` 目录，不排除自身产物；'
             '③ 仅剔除上述那**一个**文件后得 24,692 文件 / 1,506,032,984 B（= 1.506033 GB = 1.402603 GiB）——'
             '注意此数**仍含** 16 文件 / 1,618,342 B 的其它自身产物（`contamination_check.log` 的三分拆：`_hits_primary` 1 + 其它 R16 16 + rest 24,676），'
             '故**不是「不含任何自身产物」的干净值**；且该快照**没有逐文件清单**，无法逐字节复核。'
             '④ 口径注意：扩展名限制缩小的是**体积比**（约 58 倍），**文件数比仅 2.86 倍**（68,038→23,791）。')

new_stmt = old_stmt.replace(m.group(0), NEW_SCALE + '真实四环回指 = 0'
                            '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
                            '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
assert new_stmt != old_stmt

NEW_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘；'
           '规模数一律须标「测量时刻 + 脚本 + 排除项」：23,791 与 24,693 分属 11-21 与 11-22 两次不同测量、'
           '互不同口径（后者含自身产物）；24,692 只剔了 `_hits_primary.tsv` 一个文件、仍含 16 个其它自身产物、且该快照无逐文件清单；'
           '「1.29 GiB」是 `mev675.py:281` 用 /1024³ 却标 GB 的产物，勿写作 GB；'
           '「58 倍」只对体积成立，文件数比 2.86 倍。')

f24[1] = new_stmt
f24[4] = NEW_LIM
changed = 2

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible char U+%04X' % ord(ch)
# 括号/引号配平粗检（防拼接破句）
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55 and back.count('\t') == 55 * 4
brows = [l.split('\t') for l in back.split('\n')[1:] if l.strip()]
assert len(brows) == 54
for a, b in zip(rows, brows):
    assert a[0] == b[0]
    if a[0] != 'F24':
        assert a == b, 'unexpected change ' + a[0]
dist = {}
for b in brows:
    dist[b[2]] = dist.get(b[2], 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst, os.path.getsize(dst), 'bytes')
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist)
print()
print('NEW F24 statement:'); print(new_stmt)
