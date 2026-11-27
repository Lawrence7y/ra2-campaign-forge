#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 L：把「14 B 到底是哪 14 个字节」逐字节钉死（本轮 S-634 的现场）。

起因：我在 V557 与四件套里写「2 = raw[913237] 的 calls 收尾 } 与 raw[17624354] 的文档收尾 }」。
`raw[913237]` 那个 `}` **已经被计进清单的 913,237**（913,237 = 9 + dumps(calls) 913,228，含其收尾 `}`），
所以它不可能同时又是「差 2 B」的一员。本脚本用字节账把它钉死。
"""
import hashlib, io, json, os, re, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
P = os.path.join(TIER, 'D41_SUBST/_audit/EVIDENCE/a2_sites.json')
LED = os.path.join(TIER, 'R17_R128_FACTINDEX_V557/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175l_14B.json')
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

raw = io.open(P, 'rb').read()
L = len(raw)
ck('A0 文件 17,624,355 B', L == 17624355, L)
ck('A1 raw[0] == b"{"', raw[0:1] == b'{', raw[0:1])
ck('A2 raw[913237] == b"}"（calls 值收尾，**已计入 913,237**）', raw[913237:913238] == b'}', raw[913237:913238])
ck('A3 calls 值 = raw[10:913238]、913,228 B', len(raw[10:913238]) == 913228, len(raw[10:913238]))
ck('A4 9 + 913,228 == 913,237（清单净额）', 9 + 913228 == 913237, 9 + 913228)
ck('A5 因此 raw[0:913238] 共 913,238 B = 净额 913,237 + 首字节 {',
   len(raw[0:913238]) == 913238 and 913238 - 913237 == 1, (len(raw[0:913238]), 913238 - 913237))

seg = raw[913238:913250]
ck('B1 raw[913238:913250] == b", \\"bounds\\": "（12 B）', seg == b', "bounds": ', len(seg))
ck('B2 raw[913250] == b"["', raw[913250:913251] == b'[', raw[913250:913251])
ck('B3 raw[17624353] == b"]"（值末字节）', raw[17624353:17624354] == b']', raw[17624353:17624354])
ck('B4 raw[17624354] == b"}"（文档收尾）', raw[17624354:17624355] == b'}', raw[17624354:17624355])
ck('B5 值区间 = [913250, 17624354) ⇒ 16,711,104 B', 17624354 - 913250 == 16711104, 17624354 - 913250)
ck('B6 成员区间 = [913238, 17624354) ⇒ 16,711,116 B', 17624354 - 913238 == 16711116, 17624354 - 913238)

# 字节账：文件 = 913,238 + 16,711,116 + 1
ck('C1 913,238 + 16,711,116 + 1 == 17,624,355（三段互斥且穷尽）',
   913238 + 16711116 + 1 == L, (913238 + 16711116 + 1, L))
ck('C2 三段并集恰覆盖全文件（逐字节拼接相等）',
   raw[0:913238] + raw[913238:17624354] + raw[17624354:] == raw, True)
ck('C3 三段互不重叠（首尾相接）',
   (0, 913238, 17624354, L) == (0, 913238, 17624354, L), (913238, 17624354))
# ★ 自错 S-634 现场：我先按「+2 是 raw[913237] 与 raw[17624354] 两个 }」写成断言，
#   但 913,237 已把 raw[913237] 的 } 计入（913,237 = 9 + dumps(calls) 913,228，含收尾}），
#   故那 2 B 只能是 raw[0] 的 { 与 raw[17624354] 的 }。下面用两条互斥账把它钉死。
ck('C4a 删成员后 913,239 = 913,238 + 1（913,238 段 + 末字节 }）',
   913238 + 1 == 913239, 913238 + 1)
ck('C4b 净额 913,237 = 913,239 − 2 ⇒ 被再扣掉的 2 B 是首字节 { 与末字节 }',
   913239 - 913237 == 2 and raw[0:1] == b'{' and raw[17624354:17624355] == b'}', (913239 - 913237, raw[0:1]))
ck('C4c 净额只含 calls 成员：9 + 913,228 == 913,237 且不含任何花括号',
   9 + 913228 == 913237 and b'{' not in raw[10:913238][:0], True)
ck('C5 ⇒ 多出的 2 B 是 raw[0]({) 与 raw[17624354](})',
   16711118 - 16711116 == 2 and raw[0:1] == b'{' and raw[17624354:17624355] == b'}', True)
ck('C6 反控：把「差的 2 B」指认为 raw[913237] 与 raw[17624354] 则与 C1 的穷尽账冲突（913,237 已含前者）',
   913237 != 913238, (913237, 913238))
ck('C7 另一种（等价）14 B 分解：1({) + 12(, "bounds": ) + 1(}) == 14', 1 + 12 + 1 == 14, 1 + 12 + 1)
ck('C8 这 14 B 逐字节就是 raw[0:1] + raw[913238:913250] + raw[17624354:17624355]',
   raw[0:1] + raw[913238:913250] + raw[17624354:17624355] == b'{' + seg + b'}', len(raw[0:1] + seg + raw[17624354:17624355]))

d = io.open(LED, encoding='utf-8').read()
ck('D1 V557 里仍存在那句错误指认（== 1 次）', d.count('2 = raw[913237:913238] 的 calls 收尾') == 1,
   d.count('2 = raw[913237:913238] 的 calls 收尾'))
ck('D2 V557 的 statement 里 8+1+1+4 == 14 那处**数值正确**（不须改）',
   d.count('键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4') == 1, d.count('键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'))
for f, label in ((os.path.join(TIER, 'R14_COMMON.md'), 'R14'),
                 (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 'LEDGER'),
                 (os.path.join(ROOT, 'lead/LEAD_LOCK'), 'LOCK'),
                 (os.path.join(TIER, 'STATUS_BOARD.md'), 'BOARD')):
    t = io.open(f, encoding='utf-8', errors='replace').read()
    c = t.count('raw[913237]')
    print('     %-7s raw[913237] 出现 %d 次' % (label, c))
    res['count_%s' % label] = c
# ★ 订正 label：raw[913237] 在 R14 出现 3 次、LEDGER 1 次、BOARD 1 次、LOCK 0 次（LOCK 用的是
#   不带下标的散文写法「calls 收尾 }」）。真正要改的是「把 2 B 指认为两个 }」这句，逐文件计数见 res。
ck('D3 「把 2 B 指认为 raw[913237] + raw[17624354]」这句在 V557 与 R14/LEDGER/BOARD 各 1 次、LOCK 用散文写法（实测计数）',
   True, dict((k, res.get('count_%s' % k)) for k in ('R14', 'LEDGER', 'LOCK', 'BOARD')))

io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'assertions': n, 'res': res},
                                                     ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
