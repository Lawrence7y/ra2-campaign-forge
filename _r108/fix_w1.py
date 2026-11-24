#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w1.py —— 把 E-w1（写盘后复核抓到的第 9 处自错）补进四件套正文

E-w1 事实记录（不粉饰）：
  ① 收口断言总数首稿写 **105**，从九个 JSON 的 checks 数组直读的真值是 **99**
     （a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7）；差错是凭记忆累加。
  ② 同时把 a 抄成 6（实测 7）。
  ③ 修数脚本 fix_tally.py 首版还对 R14_COMMON 段断言「应当含 99 项」——
     而 R14_COMMON 的节体例本来就不带收口行（R107 §2.111 也没有），
     该断言是我的脚本预期写错，不是文件缺失；已如实登记。
本脚本只追加一行 E-w1 到「自错」段末，并把「自错 8 处」改成「自错 9 处」。
每步：wx 独占备份 -> 断言 CR -> 一次性写 -> 回读校验。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14REL = 'lead/next_re_20261117_r14'
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

W1_LOCK = ('E-w1 收口断言总数首稿写 **105**，直读九个 JSON 的 checks 数组真值是 **99**'
           '（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7），'
           '且 a 被抄成 6（实测 7）—— 差错是凭记忆累加、未直读产物；'
           '修数脚本首版还对 R14_COMMON 断言「应当含 99 项」，而该节体例本就不带收口行（R107 §2.111 同样没有），'
           '是我的脚本预期写错而非文件缺失。\n')
W1_SHORT = ('  E-w1 收口总数首稿写 105，直读九个 JSON 真值 **99**（a 7 而非 6）—— 凭记忆累加；'
            '修数脚本还对 R14_COMMON 误断言「应含 99 项」（该节体例不带收口行）。\n')

JOBS = [
    # (path, anchor_line_prefix, insert_text, expect_cr, replace_pairs)
    ('lead/LEAD_LOCK', 'E-z2 遇 `and esp,-8` 即返回，把 0x4ffdd0 的帧记成对齐修饰而**漏掉其 `sub esp,0x70`**。',
     W1_LOCK, 137, [('**自错 8 处，全部由断言当场抓住**', '**自错 9 处，全部由断言当场抓住**')]),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md',
     '  E-z1「call 目标全在指令起点」实测差 27；E-z2 遇 `and esp,-8` 即返回 ⇒ 漏掉 0x4ffdd0 的 `sub esp,0x70`。',
     W1_SHORT, 0, [('- 🐞 **自错 8 处（全部由断言抓住）**', '- 🐞 **自错 9 处（全部由断言抓住）**')]),
    ('lead/GOAL_THREE_TARGETS_20261018.md',
     '把 0x4ffdd0 的帧记成对齐修饰而漏掉其 `sub esp,0x70`。',
     W1_LOCK, 337, [('**H. 自错 7 处（全部由断言当场抓住）**', '**H. 自错 9 处（全部由断言当场抓住）**')]),
    ('_r108/seg_lock_EJ.md',
     'E-z2 遇 `and esp,-8` 即返回，把 0x4ffdd0 的帧记成对齐修饰而**漏掉其 `sub esp,0x70`**。',
     W1_LOCK, 0, [('**自错 8 处，全部由断言当场抓住**', '**自错 9 处，全部由断言当场抓住**')]),
    ('_r108/seg_board_108.md',
     '  E-z1「call 目标全在指令起点」实测差 27；E-z2 遇 `and esp,-8` 即返回 ⇒ 漏掉 0x4ffdd0 的 `sub esp,0x70`。',
     W1_SHORT, 0, [('**自错 8 处（全部由断言抓住）**', '**自错 9 处（全部由断言抓住）**')]),
    ('_r108/seg_ledger_1162.md',
     '把 0x4ffdd0 的帧记成对齐修饰而漏掉其 `sub esp,0x70`。',
     W1_LOCK, 0, [('**H. 自错 7 处（全部由断言当场抓住）**', '**H. 自错 9 处（全部由断言当场抓住）**')]),
]
fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

for path, anchor, ins, ecr, reps in JOBS:
    t = io.open(path, encoding='utf-8', newline='').read()
    ck('%s 锚点唯一（%d 次）' % (path, t.count(anchor)), t.count(anchor) == 1, t.count(anchor))
    ck('%s 尚未写过 E-w1' % path, 'E-w1 ' not in t)
    old_b = io.open(path, 'rb').read()
    ck('%s CR 前置 %d' % (path, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    new = t.replace(anchor, anchor + '\n' + ins, 1)
    for a, b in reps:
        if a in new:
            new = new.replace(a, b, 1)
    ck('%s 替换后含 E-w1' % path, 'E-w1 ' in new)
    if not path.startswith('_r108'):
        bl = os.path.join(BASE, '%s.before_R108_EW1_%s.bak'
                          % (os.path.basename(path), TS))
        fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份独占且逐字节同' % path,
           hashlib.sha256(io.open(bl, 'rb').read()).digest()
           == hashlib.sha256(old_b).digest(), os.path.basename(bl))
    with io.open(path, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(path, 'rb').read()
    ck('%s 回读逐字节一致' % path, back == new.encode('utf-8'))
    ck('%s CR 保持 %d' % (path, ecr), back.count(b'\r\n') == ecr, back.count(b'\r\n'))

print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
