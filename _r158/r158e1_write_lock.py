#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158e1_write_lock.py — 向 LEAD_LOCK 追加 OI 段。幂等；量本节字节，不量增量。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
P = R + '/lead/LEAD_LOCK'
SEC_F = R + '/_r158/section_OI.md'
BAK = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE/before_r158_lock_20261127_064311.bak'

EXPECT_OLD_SHA8 = '91210621bceb902cc501'
EXPECT_CR = 137
SEC_BYTES_MIN = 7000
PRE_CODE = 'OH'
POST_CODE = 'OI'

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
ck('0.3 标题逐字', sec_text.startswith('## OI · R17 第 158 轮'), sec_text[:36])

_n0 = raw.replace('\r\n', '\n')
already = re.search(r'(?m)^##\s+OI\s+·', _n0) is not None
if already:
    print('  [idempotent] OI 段已存在，跳过写入')
else:
    ck('1.1 备份存在', os.path.exists(BAK), BAK)
    ck('1.2 旧 sha 前缀吻合',
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20] == EXPECT_OLD_SHA8,
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20])
    ck('1.3 旧 CR 计数吻合', raw.count('\r') == EXPECT_CR, raw.count('\r'))
    codes = re.findall(r'(?m)^##\s+([A-Z]{2})\s+·', _n0)
    ck('1.4 写入前末段码 == %s' % PRE_CODE, codes and codes[-1] == PRE_CODE, codes[-1] if codes else None)
    ck('1.5 写入前不含 OI 段', 'OI' not in codes, codes[-3:])
    body = sec_text if sec_text.endswith('\n') else sec_text + '\n'
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(raw + '\n' + body)
    print('  [written] 追加 %d 字节' % len(body.encode('utf-8')))

back = io.open(P, encoding='utf-8', newline='').read()
_n = back.replace('\r\n', '\n')
ck('2.1 CR 计数仍为 %d' % EXPECT_CR, back.count('\r') == EXPECT_CR, back.count('\r'))
codes = re.findall(r'(?m)^##\s+([A-Z]{2})\s+·', _n)
ck('2.2 末段码 == %s' % POST_CODE, codes and codes[-1] == POST_CODE, codes[-1] if codes else None)
ck('2.3 OI 段恰 1 个', codes.count('OI') == 1, codes.count('OI'))
ck('2.4 段数与段码连续性（相邻不重复）', len(codes) == len(set(codes)), len(codes))
m = re.search(r'(?ms)^##\s+OI\s+·.*?(?=^##\s+[A-Z]{2}\s+·|\Z)', _n)
ck('2.5 能切出 OI 段', m is not None, m is not None)
if m:
    b = m.group(0)
    nb = len(b.encode('utf-8'))
    ck('2.6 该段字节 >= %d' % SEC_BYTES_MIN, nb >= SEC_BYTES_MIN, nb)
    ck('2.7 含 OI1..OI11 全部小标', all(('OI%d.' % i) in b for i in range(1, 12)),
       [i for i in range(1, 12) if ('OI%d.' % i) not in b])
    for tok in ('V533→V534', 'F29', 'F35', '1,392,592', '100.000000%', '86.188273%', 'S-437'):
        ck('2.8 段体含 %r' % tok, tok in b, tok in b)
ck('2.9 CR 只来自既有行', back.count('\r\n') == back.count('\r'),
   (back.count('\r\n'), back.count('\r')))
ck('2.10 全文字节 > 1,060,000', len(back.encode('utf-8')) > 1060000, len(back.encode('utf-8')))

print('\nFAILS=%d bytes=%d cr=%d codes=%d last=%s' %
      (len(fails), len(back.encode('utf-8')), back.count('\r'), len(codes), codes[-1]))
sys.exit(0 if not fails else 1)
