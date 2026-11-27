#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 K：登记第 6 条自错 S-377（产物自指：r152d 每次刷新 measured_at，r152e 重生成 v5.41 ⇒
正文钉值漂移）。同时把台账/LEAD_LOCK/看板的「五条」改成「六条」。"""
import hashlib, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def rw(p, cr, pairs):
    raw = open(p, 'rb').read()
    ck('%s pre CR %d' % (os.path.basename(p), cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    bak = os.path.join(BAKDIR, os.path.basename(p) + '.before_r152k_%s.bak'
                       % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    t = raw.decode('utf-8')
    for a, b in pairs:
        ck('%s 锚点唯一（%d 次）：%s' % (os.path.basename(p), t.count(a), a[:40]), t.count(a) == 1, t.count(a))
        t = t.replace(a, b)
    open(p, 'wb').write(t.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致 / CR %d' % (os.path.basename(p), cr),
       back == t.encode('utf-8') and back.count(b'\r') == cr, back.count(b'\r'))


# ---- 台账：§1207 第八节 ----
LED_OLD = 'S-372（方向错：把「残留句」判成「无作用域假断言」，已按审计员修正）／S-373（把「事实成立」写成「字面只存在于四版」，实测 V534 起仍残留）／S-374（反控写成重言，已换成句级可失败判据）／S-375（落盘写「11 断言」，实测 10 —— 断言里写进本该查询的量，已从源文件重生成而非改输出）／S-376（`[-6:]` 取版本尾码得 `EX_V530`，改 `endswith`）。**无一条是数据错。**'
LED_NEW = LED_OLD[:-len('**无一条是数据错。**')] + \
    '／S-377（**产物自指**：`r152d` 每次运行都刷新 `measured_at`，而 `r152e` 用它生成 v5.41 ⇒ 我在终态校验改脚本后重跑，v5.41 的 sha 与正文钉值同时漂移 `b56f8c28…`/`20:51:21Z` -> `f31c8fdc…`/`20:54:16Z`；修法是把 `r152d` 改成「记录已存在即冻结」，并在冻结分支断言本次实测与冻结记录逐项相同）。**六条无一条是数据错。**'
rw(LED, 337, [('### 八 · 自错五条', '### 八 · 自错六条'), (LED_OLD, LED_NEW)])

# ---- LEAD_LOCK：OJ9 ----
LK_OLD_HDR = 'OJ9. 🔴 **自错 S-372..S-376（五条，两条方向错，无一条数据错）.**'
LK_NEW_HDR = 'OJ9. 🔴 **自错 S-372..S-377（六条，两条方向错，无一条数据错）.**'
LK_OLD_TAIL = '**五条全是判据/口径缺陷，无一条数据错。**'
LK_NEW_TAIL = ('**S-377（产物自指）**：`r152d` 首版每次运行刷新 `measured_at`，`r152e` 用它生成 v5.41 ⇒ '
               '我在终态校验改脚本后重跑，v5.41 的 sha 与正文钉值**同时漂移**（`b56f8c28…`/`20:51:21Z` -> '
               '`f31c8fdc…`/`20:54:16Z`）。修法：`r152d` 改成「记录已存在即冻结复用」，并在冻结分支断言'
               '「本次实测与冻结记录逐项相同」。**它会变的不是查询值，而是我自己产物的生成时刻。**'
               '**六条全是判据/口径缺陷，无一条数据错。**')
rw(LOCK, 137, [(LK_OLD_HDR, LK_NEW_HDR), (LK_OLD_TAIL, LK_NEW_TAIL)])

# ---- 看板：第十节 ----
BR_OLD_HDR = '### 十 · 自错 S-372..S-376（五条，两条方向错，无一条数据错）'
BR_NEW_HDR = '### 十 · 自错 S-372..S-377（六条，两条方向错，无一条数据错）'
BR_OLD_TAIL = '**S-376** `basename[-6:]` 取版本尾码得 `EX_V530` 致两条假 FAIL，改 `endswith`。'
BR_NEW_TAIL = BR_OLD_TAIL + \
    ' **S-377（产物自指）** `r152d` 首版每次运行刷新 `measured_at`，`r152e` 用它生成 v5.41 ⇒ 改脚本后重跑，v5.41 的 sha 与正文钉值同时漂移（`b56f8c28…`/`20:51:21Z` -> `f31c8fdc…`/`20:54:16Z`）；修法：`r152d` 改成「记录已存在即冻结」+ 冻结分支断言本次实测与记录逐项相同。'
rw(BRD, 0, [(BR_OLD_HDR, BR_NEW_HDR), (BR_OLD_TAIL, BR_NEW_TAIL)])

print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
