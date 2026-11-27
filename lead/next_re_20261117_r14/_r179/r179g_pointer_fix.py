# -*- coding: utf-8 -*-
"""r179g：指针残留订正（r179f 的「不再指向 V561」断言当场抓出四处漏改）。

漏改清单（实测，不是猜）：
  1) 声明依据里的「版本号 530..561 连续无缺」→ 应为 530..563 连续 34 份；
  2) 同一格里残留「V559 是「版本号最大」」这句 R176 时期的旧结论；
  3) 边界段「D0 已钉 V560 的 sha256」→ 现钉 V563；
  4) 边界段「V530..V561 是 32 个」→ 现 34 个。
"""
import hashlib, io, os, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
V = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
SHA = '28423e7928d8414216b6a09f8ea56ef60d484dbd121cf9e5d673ffc3bc45db46'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


raw = open(V, 'rb').read()
ck('A1 V563 sha 与指针一致', hashlib.sha256(raw).hexdigest() == SHA, hashlib.sha256(raw).hexdigest()[:16])
ck('A2 V563 字节 133310', len(raw) == 133310, len(raw))

txt = io.open(PTR, encoding='utf-8', newline='').read()
lines = txt.split('\n')
old = list(lines)
# 逐条精确替换（每处都要断言「旧串存在且仅 1 次」）
reps = [
    ('版本号 530..561 连续无缺', '版本号 530..563 连续无缺'),
    ('；V559 是「版本号最大」。', '。'),
    ('（D0 已钉 V560 的 sha256）', '（D0 已钉 V563 的 sha256）'),
    ('V530..V561 是 32 个可独立复核的快照', 'V530..V563 是 34 个可独立复核的快照'),
]
for a, b in reps:
    n = txt.count(a)
    ck('B 旧串「%s」恰 1 次' % a[:24], n == 1, n)
    txt = txt.replace(a, b)
# S-660：原稿断言「指针不再出现 V559」，实测仍有 1 次 —— 它在 **R176 三次订正**的历史括注里
# （「R128 下现已有 V556/V557/V558/V559 四份」），属**历史记录**，按既定惯例不改。
# 正确判据是「V559 不再被当作当前版结论」，即那半句「V559 是『版本号最大』」必须消失。
ck('C1 当前版结论不再称 V559 为版本号最大', 'V559 是「版本号最大」' not in txt)
ck('C1b 残留的 V559 只出现在 R176 历史括注内',
   txt.count('V559') == 1 and 'R128 下现已有 V556/V557/V558/V559' in txt, txt.count('V559'))
ck('C2 指针不再出现「V560 的 sha256」', 'D0 已钉 V560' not in txt)
ck('C3 指针不再出现 530..561', '530..561' not in txt)
ck('C4 新依据含 530..563 连续 34 份', '530..563 连续 34 份' in txt)
ck('C5 sha / 字节 / 轮次 / 目录四处齐备',
   SHA in txt and '| 字节数 | 133310 |' in txt and '| 声明轮次 | R179 |' in txt
   and 'R17_R131_FACTINDEX_V563' in txt)
ck('C6 行数与改前相同（只改字，不加行）', txt.count('\n') == len(old) - 1, (txt.count('\n'), len(old) - 1))
ck('C7 CR=0', '\r' not in txt)
# 反控：把 530..563 改回 530..561，C4 必须不成立
ck('D1 反控：回改成 530..561 后 C4 判据为假', '530..563 连续 34 份' not in txt.replace('530..563 连续 34 份', '530..561 连续 32 份'))

if FAIL:
    print('ABORT 未写盘'); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry 通过'); sys.exit(0)
open(PTR, 'w', encoding='utf-8', newline='').write(txt)
ck('E1 回读一致', io.open(PTR, encoding='utf-8', newline='').read() == txt)
print('指针 = %d B / sha %s' % (len(txt.encode()), hashlib.sha256(txt.encode()).hexdigest()[:16]))
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
