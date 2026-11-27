#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 N：把 S-383..S-385 三条补记进已落盘的四件套（幂等）。

为什么要单独一步：§2.158 / §1208 / OK9 / 看板第八节写的是 S-379..S-382 四条；
门禁回归阶段又出了三条新的（S-383..S-385），若不补记，下一轮会读到「本轮自错共四条」
与实际不符。写入纪律同前：wx 备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。
"""
import hashlib
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(D, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(D, 'STATUS_BOARD.md')
BAKDIR = os.path.join(D, 'R17_LEAD_BASELINE')

fail = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fail.append(n)
    return ok


def patch_append(p, cr_want, anchor_str, add):
    raw = open(p, 'rb').read()
    ck('%s CR == %d' % (os.path.basename(p), cr_want), raw.count(b'\r') == cr_want,
       raw.count(b'\r'))
    t = raw.decode('utf-8')
    ck('%s 幂等：新条目尚未存在' % os.path.basename(p), add[:32] not in t)
    ck('%s 锚点存在' % os.path.basename(p), anchor_str in t)
    bak = os.path.join(BAKDIR, os.path.basename(p) + '.before_r153n_%s.bak'
                       % time.strftime('%Y%m%d_%H%M%S'))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('备份 wx %s' % os.path.basename(bak), os.path.exists(bak))
    t2 = t.replace(anchor_str, anchor_str + add, 1)
    ck('%s 内容确实变化' % os.path.basename(p), t2 != t)
    open(p, 'wb').write(t2.encode('utf-8'))
    back = open(p, 'rb').read()
    ck('%s 回读一致' % os.path.basename(p), back == t2.encode('utf-8'))
    ck('%s CR 未变' % os.path.basename(p), back.count(b'\r') == cr_want, back.count(b'\r'))


A_RC = ('- **S-382**：`r153h` 里把 `extra = set()` 当字典用，直接 `TypeError`；改 `dict` 后通过。\n'
        '  与前族同：断言里写进了本该被查询的量。\n'
        '\n'
        '### 六之二 · 门禁回归阶段新增 S-383..S-385（三条，全是假 FAIL，无一条数据错）\n'
        '- **S-383**：`r153l` 断言 `s.count("GATE_VER = \'R152\'") == 1` 时**把注释行也算进去了** ——\n'
        '  `check_disc.py` 第 532 行的说明文字含同一子串，故实测计数 **2**、断言假 FAIL。\n'
        '  但那次 `str.replace` 是**全量替换**，两处都被改成 R153，**结果反而是对的**。\n'
        '  正确判据是行首锚定 `(?m)^GATE_VER = \'R153\'`（`r153m` 已按此复核，恰 1 处）。\n'
        '- **S-384**：孤儿进程判据写成 `grep -E \'_r153/|check_disc\'`，**命中本会话自己的 claude 命令行**\n'
        '  （其 prompt 正文含 `check_disc` 字样），实测得 **4** 而非 0。改为只认 `python3` 解释器形态。\n'
        '- **S-385**：改窄后仍得 **1** —— 那 1 个就是**本脚本自己**（`python3 _r153/r153m_final.py`）。\n'
        '  必须 `-v me=<自身 PID>` 排除自身。⇒ 连续两条同族：**判据没排除「被测对象就是测量者」**。\n'
        '**七条（S-379..S-385）全是判据/口径缺陷，无一条数据错。**\n')

A_LED = ('\n\n### 六之二 · 门禁回归阶段新增 S-383..S-385（三条假 FAIL）\n'
         'S-383：`r153l` 对 `GATE_VER` 的断言把注释行算进计数（实测 2 而非 1），但 `str.replace` 是全量替换、\n'
         '结果正确 ⇒ 断言写窄了；正确判据是行首锚定。S-384：孤儿进程判据命中本会话自己的 claude 命令行\n'
         '（prompt 正文含 `check_disc`），实测 4。S-385：改窄后仍得 1，那 1 个是脚本自身 PID。\n'
         '⇒ 连续两条同族：**判据没排除「被测对象就是测量者」**。七条全是判据/缺陷，无一条数据错。\n')

A_LOCK = ('OK10. 🔴 **补记 S-383..S-385（门禁回归阶段，三条全是假 FAIL）.** '
          '**S-383**：`r153l` 对 `GATE_VER` 的断言用朴素子串计数，把 `check_disc.py` L532 注释里的同一子串也算进去，'
          '实测 2 而非 1 ⇒ 假 FAIL；但 `str.replace` 是全量替换，两处都已改对，**结果反而正确**，'
          '正确判据是行首锚定 `(?m)^GATE_VER = \'R153\'`（`r153m` 复核恰 1 处）。'
          '**S-384**：孤儿进程判据 `grep -E \'_r153/|check_disc\'` **命中本会话自己的 claude 命令行**（prompt 正文含该字样），实测 4。'
          '**S-385**：改窄后仍得 1 —— 那 1 个是**本脚本自身 PID**，须 `-v me=<pid>` 排除。'
          '⇒ S-384/S-385 连续同族：**判据没排除「被测对象就是测量者」**。'
          '**本轮自错共七条（S-379..S-385），全是判据/口径缺陷，无一条数据错。**\n')

A_BRD = ('\n**补记 S-383..S-385（门禁回归阶段，三条全是假 FAIL，无一条数据错）**：'
         '**S-383** `r153l` 对 `GATE_VER` 的断言用朴素子串计数，把 `check_disc.py` L532 注释里的同一子串算进去，'
         '实测 2 而非 1 ⇒ 假 FAIL；但 `str.replace` 是全量替换，两处都已改对，**结果反而正确**，'
         '正确判据是行首锚定（`r153m` 复核恰 1 处）。'
         '**S-384** 孤儿进程判据命中**本会话自己的 claude 命令行**（prompt 正文含 `check_disc`），实测 4。'
         '**S-385** 改窄后仍得 1 —— 那 1 个是**本脚本自身 PID**。'
         '⇒ S-384/S-385 连续同族：判据没排除「被测对象就是测量者」。**本轮共七条（S-379..S-385），无一条数据错。**\n')

print('[R14_COMMON §2.158 六之二]')
patch_append(RC, 1081,
             '- **S-382**：`r153h` 里把 `extra = set()` 当字典用，直接 `TypeError`；改 `dict` 后通过。\n'
             '  与前族同：断言里写进了本该被查询的量。\n', A_RC)
print('\n[台账 §1208 六之二]')
patch_append(LED, 337,
             '**四条全是判据/口径缺陷，无一条数据错。**', A_LED)
print('\n[LEAD_LOCK OK10]')
patch_append(LOCK, 137,
             '病根与前族同：**断言里写进本该被查询的量**。\n', A_LOCK)
print('\n[看板第八节补记]')
patch_append(BRD, 0,
             '真区分不在「有没有缺」，在缺的内容落在哪。**S-382** `r153h` 把 `set()` 当 dict 用致 `TypeError`。\n',
             A_BRD)

print('\n[终态]')
for k, (p, cr) in {'R14_COMMON': (RC, 1081), 'LEDGER': (LED, 337),
                   'LEAD_LOCK': (LOCK, 137), 'BOARD': (BRD, 0)}.items():
    b = open(p, 'rb').read()
    ck('%s CR == %d' % (k, cr), b.count(b'\r') == cr, b.count(b'\r'))
    print('  %-12s %9d B sha=%s' % (k, len(b), hashlib.sha256(b).hexdigest()[:16]))
bl = [l for l in open(BRD, encoding='utf-8', newline='').read().split('\n') if l]
print('看板非空行 = %d' % (len(bl) - 1))

print('\nFAIL %d：%s' % (len(fail), fail))
sys.exit(1 if fail else 0)
