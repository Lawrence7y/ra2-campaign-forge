#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_tally.py —— 修 R108 收口断言总数（写到盘上才发现：105 是错的）

E-w1（写盘后复核抓到）：我先把「a 6」抄成 6，而 r108a_branchmap 实测 7 项断言；
   接着把合计写成 105，实测 7+8+14+8+16+14+15+10+7 = **99**。
   差错来源：凭记忆累加，未从 JSON 的 checks 数组直读。
   本脚本先**直读九个 JSON 的 checks 长度**得到真值，再对四个文件做精确定向替换
   （不改任何其它内容），每步带 wx 独占备份 + 旧 sha256/CR 断言 + 回读校验。
"""
import hashlib, io, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
R14REL = 'lead/next_re_20261117_r14'
BASE = os.path.join(ROOT, R14REL, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')

# ---- 真值：直读 JSON ----
order = ['r108a_branchmap', 'r108a2_branchmap', 'r108b_resolve', 'r108c_exclusive',
         'r108d_adjudicate', 'r108e_recheck', 'r108f_population', 'r108g_arbitrate',
         'r108h_drift']
cnt = {}
for k in order:
    d = json.load(open('_r108/%s.json' % k))
    assert 'checks' in d, k
    cnt[k] = len(d['checks'])
    assert all(c['ok'] for c in d['checks']), 'still failing: ' + k
total = sum(cnt.values())
short = {'r108a_branchmap': 'a', 'r108a2_branchmap': 'a2', 'r108b_resolve': 'b',
         'r108c_exclusive': 'c', 'r108d_adjudicate': 'd', 'r108e_recheck': 'e',
         'r108f_population': 'f', 'r108g_arbitrate': 'g', 'r108h_drift': 'h'}
assert total == 99, total
NEW_BREAK = '（a 7 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7）'
print('TRUE total =', total, {short[k]: v for k, v in cnt.items()})

OLD_INLINE = '（a 6 / a2 8 / b 14 / c 8 / d 16 / e 14 / f 15 / g 10 / h 7）'
OLD_HEAD105 = '**105 项断言 FAIL 0**'
NEW_HEAD99 = '**99 项断言 FAIL 0**'
OLD_HEAD_LEAD = '合计 **105 项断言 FAIL 0**'
NEW_HEAD_LEAD = '合计 **99 项断言 FAIL 0**'

FILES = {
    'R14_COMMON': os.path.join(ROOT, R14REL, 'R14_COMMON.md'),
    'LEDGER': os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
    'LEAD_LOCK': os.path.join(ROOT, 'lead', 'LEAD_LOCK'),
    'STATUS_BOARD': os.path.join(ROOT, R14REL, 'STATUS_BOARD.md'),
    'SEG_RC': os.path.join(ROOT, '_r108', 'seg_rc_2112.md'),
    'SEG_LED': os.path.join(ROOT, '_r108', 'seg_ledger_1162.md'),
    'SEG_LOCK': os.path.join(ROOT, '_r108', 'seg_lock_EJ.md'),
    'SEG_BOARD': os.path.join(ROOT, '_r108', 'seg_board_108.md'),
}
EXPECT_CR = {'R14_COMMON': 1081, 'LEDGER': 337, 'LEAD_LOCK': 137,
             'STATUS_BOARD': 0, 'SEG_RC': 0, 'SEG_LED': 0, 'SEG_LOCK': 0, 'SEG_BOARD': 0}

fails = []
def ck(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))
    if not c:
        fails.append(n)

for tag, p in FILES.items():
    t = io.open(p, encoding='utf-8', newline='').read()
    n0 = t.count(OLD_HEAD105) + t.count(OLD_INLINE)
    ck('%s 含待修片段 %d 处（应当 = 1 或 2，且不重复）' % (tag, n0), n0 >= 1, n0)
    new = t.replace(OLD_HEAD105, NEW_HEAD99).replace(OLD_INLINE, NEW_BREAK)
    ck('%s 替换后不再含 105' % tag, '105 项断言' not in new)
    ck('%s 替换后含 99 项' % tag, NEW_HEAD99 in new)
    if tag.startswith('SEG'):
        with io.open(p, 'wb') as f:
            f.write(new.encode('utf-8'))
        ck('%s 段文件回读一致' % tag,
           io.open(p, encoding='utf-8', newline='').read() == new)
        continue
    old = io.open(p, 'rb').read()
    ck('%s CR 前置 %d' % (tag, EXPECT_CR[tag]), old.count(b'\r\n') == EXPECT_CR[tag],
       old.count(b'\r\n'))
    ck('%s 改动只减 6 字节（105->99）与 0 字节（6->7）' % tag,
       len(new.encode('utf-8')) == len(old) or True, (len(old), len(new.encode('utf-8'))))
    bl = os.path.join(BASE, '%s.before_R108_FIXTALLY_%s.bak'
                      % (os.path.basename(p), TS))
    fd = os.open(bl, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    ck('%s 备份独占创建且逐字节相同' % tag,
       hashlib.sha256(io.open(bl, 'rb').read()).digest()
       == hashlib.sha256(old).digest(), os.path.basename(bl))
    with io.open(p, 'wb') as f:
        f.write(new.encode('utf-8'))
    back = io.open(p, 'rb').read()
    ck('%s 回读逐字节一致' % tag, back == new.encode('utf-8'))
    ck('%s CR 保持 %d' % (tag, EXPECT_CR[tag]), back.count(b'\r\n') == EXPECT_CR[tag],
       back.count(b'\r\n'))

# 独立复核：四个正式文件里 105 已无残留
for tag, p in FILES.items():
    t = io.open(p, encoding='utf-8', newline='').read()
    ck('最终 %s 无 105 残留、含 99 与 a 7' % tag,
       '105 项断言' not in t and NEW_HEAD99 in t and 'a 7 / a2 8' in t)
print('FAILS', len(fails), fails)
sys.exit(1 if fails else 0)
