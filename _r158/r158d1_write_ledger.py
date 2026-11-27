#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158d1_write_ledger.py — 向 GOAL_THREE_TARGETS 追加 §1213。
纪律同上；幂等（已存在则只做终态校验）。量**该节自身字节**，不量增量（S-429）。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
P = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
SEC_F = R + '/_r158/section_1213.md'
BAK = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE/before_r158_ledger_20261127_064311.md'

EXPECT_OLD_SHA8 = '589367588e6f96fe61e4'
EXPECT_CR = 337
SEC_BYTES_MIN = 7000      # 该节自身字节下界（实测 ~8.9k；下界不写高）
PRE_LAST = 1212
POST_LAST = 1213

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

raw = io.open(P, encoding='utf-8', newline='').read()
sec_text = io.open(SEC_F, encoding='utf-8', newline='').read()
ck('0.1 节稿字节 >= 下界', len(sec_text.encode('utf-8')) >= SEC_BYTES_MIN,
   len(sec_text.encode('utf-8')))
ck('0.2 节稿 CR 为 0', sec_text.count('\r') == 0, sec_text.count('\r'))
ck('0.3 标题逐字', sec_text.startswith('## §1213 【R17 第 158 轮'), sec_text[:40])

_n0 = raw.replace('\r\n', '\n')
already = re.search(r'(?m)^##\s+§1213\b', _n0) is not None
if already:
    print('  [idempotent] §1213 已存在，跳过写入')
else:
    ck('1.1 备份存在', os.path.exists(BAK), BAK)
    ck('1.2 旧 sha 前缀吻合',
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20] == EXPECT_OLD_SHA8,
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20])
    ck('1.3 旧 CR 计数吻合', raw.count('\r') == EXPECT_CR, raw.count('\r'))
    s = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', _n0)]
    ck('1.4 写入前末节 == %d' % PRE_LAST, max(s) == PRE_LAST, max(s))
    ck('1.5 写入前不含 §1213', 1213 not in s, max(s))
    body = sec_text if sec_text.endswith('\n') else sec_text + '\n'
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(raw + '\n' + body)
    print('  [written] 追加 %d 字节' % len(body.encode('utf-8')))

back = io.open(P, encoding='utf-8', newline='').read()
_n = back.replace('\r\n', '\n')
ck('2.1 CR 计数仍为 %d' % EXPECT_CR, back.count('\r') == EXPECT_CR, back.count('\r'))
s = [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', _n)]
ck('2.2 末节 == %d' % POST_LAST, max(s) == POST_LAST, max(s))
ck('2.3 §1213 恰出现 1 次', len(re.findall(r'(?m)^##\s+§1213\b', _n)) == 1,
   len(re.findall(r'(?m)^##\s+§1213\b', _n)))
m = re.search(r'(?ms)^##\s+§1213\b.*?(?=^##\s+§\d+\b|\Z)', _n)
ck('2.4 能切出 §1213 节体', m is not None, m is not None)
if m:
    b = m.group(0)
    nb = len(b.encode('utf-8'))
    ck('2.5 该节字节 >= %d' % SEC_BYTES_MIN, nb >= SEC_BYTES_MIN, nb)
    for tok in ('V533→V534', 'F29', 'F35', '1,392,592', '100.000000%', '86.188273%', 'S-437'):
        ck('2.6 节体含 %r' % tok, tok in b, tok in b)
ck('2.7 CR 只来自既有行（CRLF 数 == CR 数）',
   back.count('\r\n') == back.count('\r'), (back.count('\r\n'), back.count('\r')))
ck('2.8 全文字节 > 5,170,000', len(back.encode('utf-8')) > 5170000, len(back.encode('utf-8')))

print('\nFAILS=%d bytes=%d cr=%d last=%d' %
      (len(fails), len(back.encode('utf-8')), back.count('\r'), max(s)))
sys.exit(0 if not fails else 1)
