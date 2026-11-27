#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 P：把「指针已补到 V554」这件事实补记到已落盘的四件套（段内追加，不改任何数字）。

为什么必须补：R14 §2.178 与看板第 173 轮段写在指针更新**之前**，当时写的是「仍指 V553」。
现在指针已改成 V554，若不补记，四件套与磁盘就会矛盾 —— 而这正是 R172 那条「指针落后无人发现」
教训的镜像。补记方式：在指定锚点后插入一句，锚点必须唯一（S-593/S-594 纪律）。
"""
import hashlib, io, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n; n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

ADD = (' **【R173 补记·指针同日补齐】** 本轮收口前已把 `FACT_INDEX_CURRENT.md` 从 V553 '
       '补到 **V554**（sha256 `5de4084b…` / **123,851 B** / 声明轮次 R173 / 版本范围 '
       '**V530..V554 共 25 份** / D0 行改为「已钉 V554」）；该文件**不被任何门禁读**，'
       '故它的正确性只能靠这条补记与磁盘自证（与 R172 记的「R171 漏改指针、门禁全绿也没暴露」同一缺口）。')

TARGETS = [
    (os.path.join(TIER, 'R14_COMMON.md'), '## 2.178',
     '`r173h_verify_after_repin.py`（14）、`r173i_r14_section.py`（本段）。', 1081),
    (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), '## §1228',
     '自错 **S-596/S-597/S-598/S-599/S-600/S-601/S-602** 七条全由可失败断言当场抓出、无一条进结论。', 337),
    (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), '\nPD · R17 第 173 轮',
     '**不写「已过跨家族审计」**（与 R166 #388、R172 #403/#405 同类）。', 137),
]
new_contents = {}
for path, anchor, insert_after, want_cr in TARGETS:
    raw = open(path, 'rb').read()
    t = raw.decode('utf-8')
    name = os.path.basename(path)
    ck('A %s CR == %d' % (name, want_cr), raw.count(b'\r') == want_cr, raw.count(b'\r'))
    ck('A %s 锚点唯一（出现恰 1 次）' % name, t.count(insert_after) == 1, t.count(insert_after))
    ck('A %s 尚未补记' % name, t.count('【R173 补记·指针同日补齐】') == 0, t.count('【R173 补记·指针同日补齐】'))
    if t.count(insert_after) != 1:
        continue
    nt = t.replace(insert_after, insert_after + ADD)
    nraw = nt.encode('utf-8')
    ck('B %s CR 不变' % name, nraw.count(b'\r') == want_cr, nraw.count(b'\r'))
    ck('B %s 补记后标记恰 1 次' % name, nt.count('【R173 补记·指针同日补齐】') == 1, 1)
    new_contents[path] = (raw, nt, nraw, name)

if fails:
    print('\n[FAIL-CLOSED] %d 条未过，不写盘。' % len(fails)); sys.exit(1)

for path, (raw, nt, nraw, name) in new_contents.items():
    bak = os.path.join(BASE, '%s.before_r173_ptr_%s.bak' % (name, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('C %s 备份 sha 一致' % name,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
       os.path.basename(bak))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(nt)
    back = open(path, 'rb').read()
    ck('D %s 回读一致' % name, back == nraw, len(back))

# 看板单独处理（要重新判行数）
bd_path = os.path.join(TIER, 'STATUS_BOARD.md')
braw = open(bd_path, 'rb').read(); bt = braw.decode('utf-8')
banchor = ('**未取得**：① `coverage.tsv` / `function_atlas.tsv` 仍不可读（第三次闭世界确认）'
           '⇒ F23 的 458/291/293/1,196/1,654 与 F35 的 `n` 分母仍不可重数；')
ck('E1 看板锚点唯一', bt.count(banchor) == 1, bt.count(banchor))
if bt.count(banchor) == 1:
    bnt = bt.replace(banchor, banchor + ' ⑦ **指针**：`FACT_INDEX_CURRENT.md` 已于同日补到 '
                     '**V554**（`5de4084b…` / 123,851 B / R173 / V530..V554 共 25 份），'
                     '此前它指 V553；该文件不被任何门禁读，故只能靠本条与磁盘自证。')
    bnr = bnt.encode('utf-8')
    ck('E2 看板 CR 仍 0', bnr.count(b'\r') == 0, bnr.count(b'\r'))
    ck('E3 看板行数仍 <= 300', bnr.count(b'\n') <= 300, bnr.count(b'\n'))
    bak = os.path.join(BASE, 'STATUS_BOARD.md.before_r173_ptr_%s.bak' % stamp)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(braw)
    with open(bd_path, 'w', encoding='utf-8', newline='') as f:
        f.write(bnt)
    ck('E4 看板回读一致', open(bd_path, 'rb').read() == bnr, bnr.count(b'\n'))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n), open(os.path.join(ROOT, '_r173', 'r173p_amend.json'), 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
