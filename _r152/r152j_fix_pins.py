#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 J：把四件里对 v5.41 的钉值改成**最终实测值**，并登记 S-377（重跑测量脚本导致时刻/ sha 漂移）。

起因：r152d 首版每跑一次就刷新 measured_at，r152e 又重生成 v5.41 ⇒ 正文里的 b56f8c28… / 20:51:21Z 与
最终产物（f31c8fdc… / 20:54:16Z）不符。本条把 r152d 改成「已存在即冻结」，并把正文钉值一次改齐。
写入纪律：wx 独占备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。
"""
import hashlib, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
RC = os.path.join(D, 'R14_COMMON.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


# 最终实测钉值
b541 = open(os.path.join(D, 'R17_R113_FACTINDEX_V541/FACT_INDEX.tsv'), 'rb').read()
SHA = hashlib.sha256(b541).hexdigest()
TS = '2026-11-26T20:54:16Z'
ck('v5.41 90,976 B / sha f31c8fdc…', len(b541) == 90976 and SHA.startswith('f31c8fdc'),
   (len(b541), SHA[:16]))
ck('v5.41 内含冻结时刻', TS in b541.decode('utf-8'), '')

CRS = {'R14_COMMON': (RC, 1081), 'LEDGER': (LED, 337), 'LEAD_LOCK': (LOCK, 137), 'BOARD': (BRD, 0)}
REPL = [
    ('b56f8c28…', SHA[:8] + '…'),
    ('b56f8c28332b3e5e', SHA[:16]),
    ('20:51:21Z', TS),
]


def patch(p, name):
    raw = open(p, 'rb').read()
    ck('%s pre CR' % name, raw.count(b'\r') == CRS[name][1], raw.count(b'\r'))
    bak = os.path.join(BAKDIR, os.path.basename(p) + '.before_r152j_%s.bak'
                       % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    t = raw.decode('utf-8')
    n0 = t
    for a, b in REPL:
        t = t.replace(a, b)
    ck('%s 内容变化' % name, t != n0)
    open(p, 'wb').write(t.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致 / CR 未变' % name,
       back == t.encode('utf-8') and back.count(b'\r') == CRS[name][1], back.count(b'\r'))
    ck('%s 无残留旧值' % name,
       'b56f8c28' not in back.decode('utf-8') and '20:51:21Z' not in back.decode('utf-8'), '')


for name, (p, _) in CRS.items():
    patch(p, name)

# ---------- 登记 S-377（改「五条」-> 「六条」并追加一条） ----------
S377_RC = ('- **S-377（本轮第五条第 6 项，产物自指）**：`r152d` 首版把 `measured_at` 设为「每次运行取当前时刻」，'
           '而 `r152e` 又用该 JSON 生成 v5.41 ⇒ 我在终态校验里改脚本后重跑了一次，'
           'v5.41 的 sha 与正文钉值同时漂移（`b56f8c28…`/`20:51:21Z` 变成 `f31c8fdc…`/`20:54:16Z`）。'
           '修法：`r152d` 改成「记录文件已存在即冻结复用」，并在冻结分支加断言「本次实测与冻结记录逐项相同」。'
           '⇒ 病根仍是「断言/产物里写进了一个会变的量」；这次它会变的不是查询值，而是**我自己产物的生成时刻**。')


def add_s377(p, anchor_list, header_old, header_new):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8')
    ck('%s 标题待改点唯一' % os.path.basename(p), t.count(header_old) == 1, t.count(header_old))
    t = t.replace(header_old, header_new)
    ck('%s S-377 锚点唯一' % os.path.basename(p), t.count(anchor_list) == 1, t.count(anchor_list))
    t = t.replace(anchor_list, anchor_list + S377_RC)
    open(p, 'wb').write(t.encode('utf-8'))
    ck('%s 回读一致' % os.path.basename(p), open(p, 'rb').read() == t.encode('utf-8'))


add_s377(RC, '**五条全是判据/口径缺陷，无一条数据错。**',
         '### 九 · 自错 S-372..S-376（五条，两条方向错）',
         '### 九 · 自错 S-372..S-377（六条，两条方向错）')

print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
