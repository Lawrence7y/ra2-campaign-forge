#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r138g_repin.py —— R138 门禁两常量显式重钉（C7d 全表摘要 + C11 FREEZE 摘要）。

为什么必须重钉而不是改判据：R138 同步了 DISC_RECHECK 第 21 行的 grep 式子
（R137 -> R138），这是一次**正常的登记式同步**；C7d 把 (id,col5,col6) 整表钉住、
C11 把冻结档整表钉住，故任何同步都必须显式重钉常量。这正是它们的设计意图：
把「悄悄改一行」变成「必须显式改常量」。

重钉前先自证有分辨力：门禁刚报 drifted ids=['20']，即**只有第 20 行漂移**，
其余 30 行不动 —— 若不是这样，说明我改错了地方。

纪律：wx 备份 -> 断言旧 sha -> 一次性写入 -> 回读校验 -> 重跑门禁 exit 0。
"""
import os
import io
import re
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
DU = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')

DRY = '--dry' in sys.argv
TS = time.strftime('%Y%m%d_%H%M%S')
fails, buf = [], []


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def main():
    W('# R138 门禁两常量重钉%s' % ('  [DRY]' if DRY else ''))
    gt = io.open(GATE, encoding='utf-8', newline='').read()

    # ---------- ① C7d：逐行复算，证「只有 id 20 漂移」 ----------
    W('= 1 · C7d 全表摘要 =')
    rows = [l.split('\t') for l in
            io.open(DR, encoding='utf-8', newline='').read().split('\n') if l.strip()]
    ck('DISC_RECHECK 31 行数据 + 表头', len(rows) == 32, len(rows))
    body = rows[1:]
    ck('全部行 7 列', all(len(r) == 7 for r in body))
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in body)
    new_c7 = hashlib.sha256(blob.encode('utf-8')).hexdigest()

    old_pin = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", gt).group(1)
    ck('旧 C7_TEXT_SHA256 为 b49da749…', old_pin.startswith('b49da749'), old_pin[:16])
    # 逐行对比旧 C7_ROW_SHA，找漂移行
    mrow = re.search(r"C7_ROW_SHA = \{(.*?)\}", gt, re.S).group(1)
    old_rows = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", mrow))
    ck('旧 C7_ROW_SHA 有 31 条', len(old_rows) == 31, len(old_rows))
    drift = []
    for r in body:
        h = hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                           .encode('utf-8')).hexdigest()
        if old_rows.get(r[0]) != h:
            drift.append(r[0])
    ck('只有 id 20 漂移（与门禁报的 drifted ids 一致）', drift == ['20'], drift)
    W('  新 C7_TEXT_SHA256 = %s' % new_c7[:16])

    # 生成新的 C7_ROW_SHA 字面量（保持原顺序与原格式）
    new_rows = {}
    for r in body:
        new_rows[r[0]] = hashlib.sha256(
            ('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
            .encode('utf-8')).hexdigest()
    # 用旧表顺序重排，确保只改漂移那条
    order = re.findall(r"'(\d+)': '[0-9a-f]{64}'", mrow)
    ck('旧表键序可复现 31 条', len(order) == 31, len(order))
    new_lit = ', '.join("'%s': '%s'" % (k, new_rows[k]) for k in order)
    changed_keys = [k for k in order if old_rows[k] != new_rows[k]]
    ck('字面量中只有 1 个键变化', changed_keys == ['20'], changed_keys)

    gt2 = gt.replace("C7_TEXT_SHA256 = '%s'" % old_pin,
                     "C7_TEXT_SHA256 = '%s'" % new_c7)
    ck('C7_TEXT_SHA256 已替换', new_c7 in gt2)
    old_lit_m = re.search(r"C7_ROW_SHA = \{(.*?)\}", gt, re.S)
    old_lit = old_lit_m.group(1)
    gt2 = gt2.replace('C7_ROW_SHA = {' + old_lit + '}',
                      'C7_ROW_SHA = {' + new_lit + '}')
    ck('C7_ROW_SHA 已替换', C7_row_ok(gt2, new_rows))

    # ---------- ② C11：FREEZE 摘要 ----------
    W('= 2 · C11 FREEZE 摘要 =')
    du_b = open(DU, 'rb').read()
    new_freeze = hashlib.sha256(du_b).hexdigest()
    old_freeze = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", gt2).group(1)
    ck('旧 FREEZE_SHA256 为 d72a199b…', old_freeze.startswith('d72a199b'),
       old_freeze[:16])
    W('  新 FREEZE_SHA256 = %s' % new_freeze[:16])
    # 自证：DISC_UNVERIFIABLE 内容确实只改了一处锚
    ck('DISC_UNVERIFIABLE 恰含 1 处 R138 锚',
       du_b.decode('utf-8').count("grep=(?m)^GATE_VER = 'R138'") == 1)
    ck('DISC_UNVERIFIABLE 已无 R137 锚',
       "grep=(?m)^GATE_VER = 'R137'" not in du_b.decode('utf-8'))
    gt3 = gt2.replace("FREEZE_SHA256 = '%s'" % old_freeze,
                      "FREEZE_SHA256 = '%s'" % new_freeze)
    ck('FREEZE_SHA256 已替换', new_freeze in gt3)

    # ---------- ③ 只改这两个常量 ----------
    W('= 3 · 只改这两个常量 =')
    ol, nl = gt.split('\n'), gt3.split('\n')
    diff = [i for i in range(len(ol)) if ol[i] != nl[i]]
    ck('改动行数 == 3（C7_TEXT_SHA256 / C7_ROW_SHA / FREEZE_SHA256）',
       len(diff) == 3, len(diff))
    for i in diff:
        W('    L%d: %s' % (i + 1, nl[i][:70]))
    ck('GATE_VER 未被本次改动',
       [i for i in diff if 'GATE_VER' in ol[i]] == [])

    if DRY:
        W()
        W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
        for f in fails:
            W('  FAIL: ' + f)
        return 0 if not fails else 1

    # ---------- 写 ----------
    p = os.path.join(BASE, 'check_disc.py.before_R138_repin_%s.bak' % TS)
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, gt.encode('utf-8'))
    finally:
        os.close(fd)
    ck('门禁备份 wx 独占创建',
       hashlib.sha256(open(p, 'rb').read()).hexdigest()
       == hashlib.sha256(gt.encode('utf-8')).hexdigest())

    nb = gt3.encode('utf-8')
    tmp = GATE + '.tmp_r138g'
    if os.path.exists(tmp):
        os.remove(tmp)
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, nb)
    finally:
        os.close(fd)
    os.replace(tmp, GATE)
    rt = open(GATE, 'rb').read()
    ck('回读 sha 一致', hashlib.sha256(rt).hexdigest() == hashlib.sha256(nb).hexdigest())

    W()
    W('== %d PASS / %d FAIL ==' % (len(buf) - len(fails), len(fails)))
    W('C7_TEXT_SHA256  = %s' % new_c7)
    W('FREEZE_SHA256   = %s' % new_freeze)
    for f in fails:
        W('  FAIL: ' + f)
    return 0 if not fails else 1


def C7_row_ok(gate_text, expect):
    m = re.search(r"C7_ROW_SHA = \{(.*?)\}", gate_text, re.S)
    got = dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", m.group(1)))
    return got == expect


if __name__ == '__main__':
    sys.exit(main())
