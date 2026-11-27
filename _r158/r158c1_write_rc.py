#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158c1_write_rc.py — 向 R14_COMMON.md 追加 §2.163。
纪律：备份已在 r158b1 建好 → 断言旧 sha256 / CR → 一次性写入 → 回读逐项校验。
幂等：若 §2.163 已存在则跳过写入，只做终态校验（可反复运行）。
S-429 教训：量**该节自身字节**，不量增量。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
P = R + '/lead/next_re_20261117_r14/R14_COMMON.md'
SEC_F = R + '/_r158/section_2_163.md'
BAK = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE/before_r158_rc_20261127_064311.md'

EXPECT_OLD_SHA8 = '281bc45c29afdf8d3752'
EXPECT_CR = 1081
EXPECT_SEC_MIN = 11000     # 该节自身字节下界（实测 11343；下界不要写高，见 S-437）
PRE_SEC = 161              # 写入前最后一节（--pre 模式下断言）
POST_SEC = 163             # 写入后末节（= 162 + 1）

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

raw = io.open(P, encoding='utf-8', newline='').read()
sec_text = io.open(SEC_F, encoding='utf-8', newline='').read()
ck('0.1 节稿字节数 > 下界（按 bytes 不按 chars，S-390/S-437 同族）',
   len(sec_text.encode('utf-8')) > EXPECT_SEC_MIN, len(sec_text.encode('utf-8')))
ck('0.2 节稿 CR 为 0（全 LF）', sec_text.count('\r') == 0, sec_text.count('\r'))
ck('0.3 节稿无反引号之外的异常（标题逐字）',
   sec_text.startswith('## 2.163 【R158, 2026-11-27】'), sec_text[:40])

already = re.search(r'(?m)^##\s+2\.163\b', raw.replace('\r\n', '\n')) is not None
if already:
    print('  [idempotent] §2.163 已存在，跳过写入，只做终态校验')
new = raw
else_note = None
if not already:
    ck('1.1 备份存在', os.path.exists(BAK), BAK)
    ck('1.2 旧 sha 前缀吻合', hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20] == EXPECT_OLD_SHA8,
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20])
    ck('1.3 旧 CR 计数吻合', raw.count('\r') == EXPECT_CR, raw.count('\r'))
    # 写入前末节必须 <= 162（不含 163）
    secs = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', raw.replace('\r\n', '\n'))]
    ck('1.4 写入前不含 §2.163', 163 not in secs, max(secs))
    body = sec_text if sec_text.endswith('\n') else sec_text + '\n'
    new = raw + '\n' + body
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print('  [written] 追加 %d 字符' % len(body))

# ---------- 终态校验（幂等可重跑）----------
back = io.open(P, encoding='utf-8', newline='').read()
ck('2.1 回读 CR 计数仍为 %d' % EXPECT_CR, back.count('\r') == EXPECT_CR, back.count('\r'))
_n = back.replace('\r\n', '\n')
secs = [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', _n)]
ck('2.2 末节号 == %d' % POST_SEC, max(secs) == POST_SEC, max(secs))
ck('2.3 §2.163 恰出现 1 次', _n.count('\n## 2.163 ') + (1 if _n.startswith('## 2.163 ') else 0) == 1,
   _n.count('\n## 2.163 '))
ck('2.4 节数 == 写入前 +1（=163-6=157）', len(secs) == 157, len(secs))
# 该节自身字节（S-429：量本节，不量增量）
m = re.search(r'(?ms)^##\s+2\.163\b.*?(?=^##\s+2\.\d+\b|\Z)', _n)
ck('2.5 能切出 §2.163 节体', m is not None, m is not None)
if m:
    body_now = m.group(0)
    nbytes = len(body_now.encode('utf-8'))
    ck('2.6 该节字节 >= %d（下界，非增量）' % EXPECT_SEC_MIN, nbytes >= EXPECT_SEC_MIN, nbytes)
    for tok in ('V533→V534', 'F29', 'F35', 'strict_panel.py', '1,392,592',
                '100.000000%', '86.188273%', 'S-431', '未取得'):
        ck('2.7 节体含关键 token %r' % tok, tok in body_now, tok in body_now)
ck('2.8 全文无 CRLF 混入（CR 只来自既有行）',
   back.count('\r\n') == back.count('\r'), (back.count('\r\n'), back.count('\r')))
ck('2.9 文件字节数 > 1,360,000', len(back.encode('utf-8')) > 1360000, len(back.encode('utf-8')))

print('\nFAILS=%d  bytes=%d  cr=%d  secs=%d  last=%d' %
      (len(fails), len(back.encode('utf-8')), back.count('\r'), len(secs), max(secs)))
sys.exit(0 if not fails else 1)
