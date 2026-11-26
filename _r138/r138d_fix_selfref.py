#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r138d_fix_selfref.py —— 修正 v5.33 里的自指版本号错误。

缺陷（R138 自错 S-263）：写 F35 追加段时写「故 F35 是 v5.32 里与 F23 并列的
两条整行证据链失联项之一」，但这一行写入之后已经位于 v5.33 内。版本自指错：
读者会去找 v5.32 的 F35，而 v5.32 的 F35 并没有这句话。

修法：改成不带版本号的表述（「本表里与 F23 并列的…」），并补一句该结论的
统计时点锚（基于 v5.32 全表普查），使时点与版本都可追。

纪律：wx 备份 -> 断言旧 sha -> 一次性写入 -> 回读校验。
"""
import os
import sys
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
F = os.path.join(R14, 'R17_R105_FACTINDEX_V533', 'FACT_INDEX.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
DRY = '--dry' in sys.argv

OLD_SHA = '9cd171c748adcf7336b8d02629a80b50e56653520b11304bb292607c051f8cda'
OLD_BYTES = 66602

OLD = u'故 F35 是 v5.32 里与 F23 并列的**两条整行证据链失联项**之一。'
NEW = (u'故 F35 是本表里与 F23 并列的**两条整行证据链失联项**之一'
       u'（该普查的时点是 v5.32 全表，R138 复查未变）。')

fails, buf = [], []


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def main():
    W('# r138d 修正 F35 自指版本号')
    b = open(F, 'rb').read()
    ck('旧字节数 == %d' % OLD_BYTES, len(b) == OLD_BYTES, len(b))
    ck('旧 sha256 与写入后基线一致', hashlib.sha256(b).hexdigest() == OLD_SHA,
       hashlib.sha256(b).hexdigest())
    ck('旧文件 CR == 0', b.count(b'\r') == 0)
    t = b.decode('utf-8')
    ck('缺陷字符串恰出现 1 次', t.count(OLD) == 1, t.count(OLD))
    nt = t.replace(OLD, NEW)
    ck('修正后缺陷字符串消失', OLD not in nt)
    ck('修正后新表述在场', NEW in nt)
    nb = nt.encode('utf-8')
    ck('新文件 CR == 0', nb.count(b'\r') == 0)
    ck('行数不变 55', nb.count(b'\n') == 55, nb.count(b'\n'))
    # 只改这一行
    ol, nl = t.split('\n'), nt.split('\n')
    ck('只有 F35 那一行变化',
       [i for i in range(len(ol)) if ol[i] != nl[i]] == [35],
       [i for i in range(len(ol)) if ol[i] != nl[i]])

    if DRY:
        W('--dry 不写盘；新 sha = ' + hashlib.sha256(nb).hexdigest())
        return 0 if not fails else 1

    ts = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'FACT_INDEX.tsv.before_R138_v533_fix_%s.bak' % ts)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, b)
    finally:
        os.close(fd)
    ck('备份已 wx 独占创建', os.path.exists(bak))
    ck('备份 sha == 旧 sha',
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == OLD_SHA)

    # 原地重写：先删后写（同目录，O_EXCL 不适用原地替换）
    tmp = F + '.tmp_r138d'
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, nb)
    finally:
        os.close(fd)
    os.replace(tmp, F)
    W('  原地替换完成')

    rt = open(F, 'rb').read()
    ck('回读 sha 一致', hashlib.sha256(rt).hexdigest()
       == hashlib.sha256(nb).hexdigest())
    ck('回读 CR == 0', rt.count(b'\r') == 0)
    ck('回读 55 行', rt.count(b'\n') == 55)
    ck('回读缺陷字符串已消失', OLD.encode('utf-8') not in rt)
    ck('临时文件已清理', not os.path.exists(tmp))

    W()
    W('== 断言 %d PASS / %d FAIL ==' % (len(buf) - len(fails) - 1, len(fails)))
    W('new sha = ' + hashlib.sha256(rt).hexdigest())
    W('new bytes = %d (%+d)' % (len(rt), len(rt) - OLD_BYTES))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
