#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_w34.py —— 补齐 E-w2 / E-w3 / E-w4 三条，并把自错条数改成真值 13

逐码清点本轮自错（不按行、按条）：
  E-x1 r108c 严格 '>' 判 S ⇒ 13 张 OWNER 误记「拿不到 owner」
  E-x2 排他性判据随机窗口发火率 100% ⇒ 无鉴别力
  E-x3 ret 前缀 0x67 未处理 ⇒ set 排序 TypeError 崩在负控
  E-x4 IMMPTR 把内存 displacement 当立即数 ⇒ 0x71f328 错改判 0x71ef01
  E-y1 帧常量探测深度不足 ⇒ 0x58bda4 两侧同为 None 误判「相同」
  E-y2 「首条 ret 早于 H」口径作废（0x417fe0 反例）
  E-y3 「jmp/jcc BFS 不可达」口径作废（不跟跳转表边）
  E-z1 「call 目标全在指令起点」断言实测差 27
  E-z2 遇 and esp,-8 即返回 ⇒ 漏 0x4ffdd0 的 sub esp,0x70
  E-w1 收口总数首稿 105（真值 99）、a 抄成 6（真值 7）
  E-w2 修数脚本用非唯一锚点，改错了 R107 的 EI6 而不是 R108 的 EJ8
  E-w3 自错条数本身数错（先写 8、后写 9，按行数少算；真值按条 13）
  E-w4 备份文件名只含 basename+时间戳 ⇒ 同文件第二处改动 EEXIST 崩
共 13 条。本脚本只做：把「11 处」改成「13 处」，并在 E-w1 行后追加 E-w2/E-w3/E-w4 三行。
"""
import hashlib, io, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14REL = 'lead/next_re_20261117_r14'
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')
fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

W2 = ('E-w2 修数脚本用「**自错 8 处…**」作替换锚点，而该串在 LEAD_LOCK 里**先出现在 R107 的 EI6**、'
      '后出现在 R108 的 EJ8，`replace(...,1)` 只替换第一处 ⇒ **改错了 R107 的段**，R108 的反倒没动；'
      '已用带段号的全串锚点改回（R107 EI6 还原 8 处、R108 EJ8 改为真值）。\n')
W3 = ('E-w3 「自错几处」本身数错了两次（先写 8、后写 9），根因是按**行**数而不是按**条**数 '
      '（台账体例把 E-y2/E-y3 并成一行）⇒ 逐码清点后真值是 **13 条**。\n')
W4 = ('E-w4 备份文件名只含 basename + 时间戳，同一文件的两处改动落在同一秒 ⇒ '
      '`O_EXCL` 第二次直接 EEXIST 崩掉半个作业；备份名必须带作业序号。\n')

JOBS = [
    ('lead/LEAD_LOCK', 137,
     'E-w1 收口断言总数首稿写 **105**，直读九个 JSON 的 checks 数组真值是 **99**（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7），且 a 被抄成 6（实测 7）—— 差错是凭记忆累加、未直读产物；修数脚本首版还对 R14_COMMON 断言「应当含 99 项」，而该节体例本就不带收口行（R107 §2.111 同样没有），是我的脚本预期写错而非文件缺失。',
     W2, 'EJ8. 🐞 **自错 11 处，全部由断言当场抓住**', 'EJ8. 🐞 **自错 13 处，全部由断言当场抓住**'),
    ('_r108/seg_lock_EJ.md', 0,
     'E-w1 收口断言总数首稿写 **105**，直读九个 JSON 的 checks 数组真值是 **99**（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7），且 a 被抄成 6（实测 7）—— 差错是凭记忆累加、未直读产物；修数脚本首版还对 R14_COMMON 断言「应当含 99 项」，而该节体例本就不带收口行（R107 §2.111 同样没有），是我的脚本预期写错而非文件缺失。',
     W2, 'EJ8. 🐞 **自错 11 处，全部由断言当场抓住**', 'EJ8. 🐞 **自错 13 处，全部由断言当场抓住**'),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0,
     '  E-w1 收口总数首稿写 105，直读九个 JSON 真值 **99**（a 7 而非 6）—— 凭记忆累加；修数脚本还对 R14_COMMON 误断言「应含 99 项」（该节体例不带收口行）。',
     '  ' + W2.replace('\n', '').join(['', '\n']) + '  ' + W3.replace('\n', '').join(['', '\n']) + '  ' + W4,
     '- 🐞 **自错 11 处（全部由断言抓住）**', '- 🐞 **自错 13 处（全部由断言抓住）**'),
    ('_r108/seg_board_108.md', 0,
     '  E-w1 收口总数首稿写 105，直读九个 JSON 真值 **99**（a 7 而非 6）—— 凭记忆累加；修数脚本还对 R14_COMMON 误断言「应含 99 项」（该节体例不带收口行）。',
     '  ' + W2.replace('\n', '').join(['', '\n']) + '  ' + W3.replace('\n', '').join(['', '\n']) + '  ' + W4,
     '- 🐞 **自错 11 处（全部由断言抓住）**', '- 🐞 **自错 13 处（全部由断言抓住）**'),
    ('lead/GOAL_THREE_TARGETS_20261018.md', 337,
     'E-w1 收口断言总数首稿写 **105**，直读九个 JSON 的 checks 数组真值是 **99**（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7），且 a 被抄成 6（实测 7）—— 差错是凭记忆累加、未直读产物；修数脚本首版还对 R14_COMMON 断言「应当含 99 项」，而该节体例本就不带收口行（R107 §2.111 同样没有），是我的脚本预期写错而非文件缺失。',
     W2, '**H. 自错 11 处（全部由断言当场抓住）**', '**H. 自错 13 处（全部由断言当场抓住）**'),
    ('_r108/seg_ledger_1162.md', 0,
     'E-w1 收口断言总数首稿写 **105**，直读九个 JSON 的 checks 数组真值是 **99**（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7），且 a 被抄成 6（实测 7）—— 差错是凭记忆累加、未直读产物；修数脚本首版还对 R14_COMMON 断言「应当含 99 项」，而该节体例本就不带收口行（R107 §2.111 同样没有），是我的脚本预期写错而非文件缺失。',
     W2, '**H. 自错 11 处（全部由断言当场抓住）**', '**H. 自错 13 处（全部由断言当场抓住）**'),
]
for ji, (path, ecr, anchor, ins, oldhead, newhead) in enumerate(JOBS):
    t = io.open(path, encoding='utf-8', newline='').read()
    ck('%s 锚点唯一' % path, t.count(anchor) == 1, t.count(anchor))
    ck('%s 标题锚点唯一' % path, t.count(oldhead) == 1, t.count(oldhead))
    ck('%s 尚未含 E-w2' % path, 'E-w2 ' not in t)
    old_b = io.open(path, 'rb').read()
    ck('%s CR 前置 %d' % (path, ecr), old_b.count(b'\r\n') == ecr, old_b.count(b'\r\n'))
    new = t.replace(anchor, anchor + '\n' + ins, 1).replace(oldhead, newhead, 1)
    ck('%s 含 E-w2/W3/W4 且标题为 13' % path,
       'E-w2 ' in new and 'E-w3 ' in new and 'E-w4 ' in new and newhead in new)
    if not path.startswith('_r108'):
        bl = os.path.join(BASE, '%s.before_R108_EW34_j%d_%s.bak'
                          % (os.path.basename(path), ji, TS))
        fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, old_b)
        finally:
            os.close(fd)
        ck('%s 备份独占同哈希' % path,
           hashlib.sha256(io.open(bl, 'rb').read()).digest()
           == hashlib.sha256(old_b).digest(), os.path.basename(bl))
    with io.open(path, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(path, 'rb').read()
    ck('%s 回读一致 CR %d' % (path, ecr),
       back == new.encode('utf-8') and back.count(b'\r\n') == ecr,
       back.count(b'\r\n'))
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
