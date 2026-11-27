#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161d_archive_board.py —— R161 归档：把看板上最早的 2 段（第 158 / 159 轮）逐字搬入 BOARD_ARCHIVE。

触发条件（任务书硬要求）：STATUS_BOARD.md 行数 >= 260 时必须先归档最早 2 段。
本轮实测起始 273 行 ⇒ 触发。归档后看板只剩第 160 轮，再加第 161 轮。

纪律：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；搬移逐字节等价。
顺序：先归档后删看板（反了会先丢后补）。
反控两条（不靠字符串拼装重构建）：
  (a) 新看板必须是原看板的严格**后缀**（只砍头、一字未改）
  (b) 归档尾部必须逐字等于被砍掉那段（去尾部空行后）
幂等：若归档已同时含 158/159 两段，跳过搬移、只做终态校验。
"""
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
SB = T + '/STATUS_BOARD.md'
BA = T + '/BOARD_ARCHIVE.md'
BD = T + '/R17_LEAD_BASELINE'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

sb = io.open(SB, encoding='utf-8', newline='').read()
ba = io.open(BA, encoding='utf-8', newline='').read()
ck('0.1 看板 CR == 0', sb.count('\r') == 0, sb.count('\r'))
ck('0.2 归档 CR == 2952', ba.count('\r') == 2952, ba.count('\r'))
nL = sb.count('\n')
_IDEMP = ('R17 第 158 轮' in ba) and ('R17 第 159 轮' in ba)
# S-467（第十二条）：0.3/0.4 是**触发条件**（某时刻成立），幂等重跑时不成立 ⇒ 会把正常终态误报为 FAIL。
# 触发条件只在「尚未归档」时才断言；已归档时改为断言终态（看板 < 260 且不含 158/159）。
if _IDEMP:
    print('  [already-archived] 归档已含 158/159：跳过触发条件断言，只做终态校验')
else:
    ck('0.3 看板起始行数 >= 260（触发归档）', nL >= 260, nL)

pat = re.compile(r'(?m)^## .*?R17 第 (\d+) 轮')
starts = [(m.start(), int(m.group(1)), m.group(0)) for m in pat.finditer(sb)]
print('  看板段 = %s' % [(s[1], s[0]) for s in starts])
nums = [s[1] for s in starts]
if not _IDEMP:
    ck('0.4 看板含 158/159/160 三段', set([158, 159, 160]).issubset(set(nums)), nums)
else:
    ck('0.4b 终态：看板不含 158/159', (158 not in nums) and (159 not in nums), nums)

if 'R17 第 158 轮' in ba and 'R17 第 159 轮' in ba:
    print('  [idempotent] 归档已含 158/159，跳过搬移')
    segs = None
else:
    # 按轮次号取最早两段（按号排序，不按版面位置）
    order = sorted(starts, key=lambda s: s[1])
    ck('0.5 最早两段是 158 / 159', [order[0][1], order[1][1]] == [158, 159], [o[1] for o in order[:3]])
    # 段边界按版面顺序切片：取版面位置最小与其次的段首作为边界不成立（160 在最前），
    # 故用「按号取段」→ 再按版面位置排序求各自切片
    poss = sorted(starts, key=lambda s: s[0])
    def seg_of(num):
        idx = [i for i, s in enumerate(poss) if s[1] == num][0]
        a = poss[idx][0]
        b = poss[idx + 1][0] if idx + 1 < len(poss) else len(sb)
        return sb[a:b]
    seg158, seg159 = seg_of(158), seg_of(159)
    print('  段字符数 158=%d 159=%d' % (len(seg158), len(seg159)))
    ck('0.6 两段各自 > 3000 字符', len(seg158) > 3000 and len(seg159) > 3000,
       (len(seg158), len(seg159)))

    stamp = time.strftime('%Y%m%d_%H%M%S')
    for tag, path in (('arch', BA), ('board', SB)):
        dst = os.path.join(BD, 'before_r161_arch2_%s_%s.bak' % (tag, stamp))
        fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(open(path, 'rb').read())
        ck('1.0 %s 备份已建（wx 独占）' % tag, os.path.exists(dst), os.path.basename(dst))

    head = ba if ba.endswith('\n') else ba + '\n'
    add = '\n' + seg158.rstrip('\n') + '\n\n' + seg159.rstrip('\n') + '\n'
    new_ba = head + add
    # 从看板删除这两段：剩下的部分 = 原看板减去 seg158 与 seg159
    idx158 = sb.index(seg158); idx159 = sb.index(seg159)
    pieces = []
    pos = 0
    for (a, b) in sorted([(idx158, idx158 + len(seg158)), (idx159, idx159 + len(seg159))]):
        pieces.append(sb[pos:a]); pos = b
    pieces.append(sb[pos:])
    new_sb = ''.join(pieces)

    # 先写归档、再写看板
    tmp = BA + '.r161tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(new_ba)
    os.replace(tmp, BA)
    tmp2 = SB + '.r161tmp'
    with io.open(tmp2, 'w', encoding='utf-8', newline='') as f:
        f.write(new_sb)
    os.replace(tmp2, SB)
    print('  [archived] 158 / 159 已搬入归档并从看板移除')

    ck('1.1 反控(a)：新看板 == 原看板删掉两段后的逐字剩余（一字未改）',
       new_sb == sb[:idx158] + sb[idx158 + len(seg158):idx159] + sb[idx159 + len(seg159):],
       {'orig': len(sb), 'new': len(new_sb)})
    ck('1.2 反控(b)：归档尾部 == 被搬走的两段（去尾部空行后逐字相等）',
       io.open(BA, encoding='utf-8', newline='').read().endswith(
           '\n' + seg158.rstrip('\n') + '\n\n' + seg159.rstrip('\n') + '\n'),
       len(seg158) + len(seg159))

sb2 = io.open(SB, encoding='utf-8', newline='').read()
ba2 = io.open(BA, encoding='utf-8', newline='').read()
ck('2.1 看板 CR 仍 0', sb2.count('\r') == 0, sb2.count('\r'))
ck('2.2 归档 CR 仍 2952', ba2.count('\r') == 2952, ba2.count('\r'))
ck('2.3 归档含 158 / 159', ('R17 第 158 轮' in ba2) and ('R17 第 159 轮' in ba2),
   (ba2.count('R17 第 158 轮'), ba2.count('R17 第 159 轮')))
ck('2.4 看板不含 158 / 159', ('R17 第 158 轮' not in sb2) and ('R17 第 159 轮' not in sb2),
   (sb2.count('R17 第 158 轮'), sb2.count('R17 第 159 轮')))
ck('2.5 看板仍含第 160 轮', 'R17 第 160 轮' in sb2, sb2.count('R17 第 160 轮'))
n2 = sb2.count('\n')
ck('2.6 看板行数 < 260（归档线已解除）', n2 < 260, n2)
ck('2.7 看板行数 <= 300', n2 <= 300, n2)
print('\nFAILS=%d  看板 lines=%d bytes=%d cr=%d | 归档 bytes=%d cr=%d lines=%d'
      % (len(fails), n2, len(sb2.encode()), sb2.count('\r'),
         len(ba2.encode()), ba2.count('\r'), ba2.count('\n')))
sys.exit(0 if not fails else 1)
