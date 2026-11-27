#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r163f_archive_board.py —— R163 归档：把看板上最早的 2 段（第 161 / 160 轮）逐字搬入 BOARD_ARCHIVE。

触发条件（任务书硬要求）：STATUS_BOARD.md 行数 >= 260 时必须先归档最早 2 段。
本轮实测起始 **298 行** ⇒ 触发。看板现有三段：162（offset 0）/ 161（4060）/ 160（10040），
按轮次号取最早两段 = 161 与 160。

纪律：BOARD_ARCHIVE CR 保持 **2952**；STATUS_BOARD CR 保持 **0**；搬移逐字节等价。
顺序：先归档后删看板（反了会先丢后补）。
反控两条（不靠字符串拼装重构建）：
  (a) 新看板必须是原看板的严格**前缀**（只砍尾、一字未改）
      ★ S-490：首版抄了「后缀」——但看板是**最新在前**（162 在 offset 0、160 在最后），
        归档最早两段砍的是**尾部**，故正确判据是**前缀**。抄方向会把正常终态误报为 FAIL。
  (b) 归档尾部必须逐字等于被砍掉那段（去尾部空行后）
幂等：若归档已同时含 161/160 两段，跳过搬移、只做终态校验。
"""
import hashlib
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
    if not ok:
        fails.append(n)
    return ok


def rb(p):
    with io.open(p, 'rb') as f:
        return f.read()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r163_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


sb = io.open(SB, encoding='utf-8', newline='').read()
ba = io.open(BA, encoding='utf-8', newline='').read()
ck('0.1 看板 CR == 0', sb.count('\r') == 0, sb.count('\r'))
ck('0.2 归档 CR == 2952', ba.count('\r') == 2952, ba.count('\r'))

pat = re.compile(r'(?m)^## .*?R17 第 (\d+) 轮')
starts = [(m.start(), int(m.group(1))) for m in pat.finditer(sb)]
print('  看板段 = %s（%d 行）' % (starts, sb.count('\n')))
nums = [n for _o, n in starts]

# ★ S-496：首版用「归档是否已含 161/160」当幂等判据 —— 但归档在 R162 之前就已含
#   「R17 第 161/160 轮」之外的历史段时这条会误判（且我回滚过一次导致归档与实际重复）。
#   正确判据只看**看板**：看板还含 161/160 ⇒ 尚未搬移；不含 ⇒ 已搬移（终态）。
IDEMP = (161 not in [n for _o, n in [(m.start(), int(m.group(1)))
                                    for m in re.finditer(r'(?m)^## .*?R17 第 (\d+) 轮', sb)]]
         and 160 not in [n for _o, n in [(m.start(), int(m.group(1)))
                                         for m in re.finditer(r'(?m)^## .*?R17 第 (\d+) 轮', sb)]])
# S-467 谱系：触发条件是「某时刻成立」，幂等重跑时不成立 ⇒ 只在尚未归档时断言，
# 已归档时改断言终态（看板 < 260 且不含 161/160）。
if IDEMP:
    print('  [already-archived] 归档已含 161/160：跳过触发条件断言，只做终态校验')
    ck('0.4b 终态：看板不含 161/160', (161 not in nums) and (160 not in nums), nums)
    ck('0.4c 终态：看板行数 < 260', sb.count('\n') < 260, sb.count('\n'))
else:
    ck('0.3 看板起始行数 >= 260（触发归档）', sb.count('\n') >= 260, sb.count('\n'))
    ck('0.4 看板恰含三段且最早两段是 161/160',
       nums == [162, 161, 160], nums)

if IDEMP:
    print('  [idempotent] 跳过搬移')
else:
    # 按轮次号排序取最早两段
    order = sorted(starts, key=lambda x: x[1])       # 号小者最早
    first_two = order[:2]
    ck('1.0 最早两段 = 161/160', [n for _o, n in first_two] == [160, 161],
       [n for _o, n in first_two])
    cut = min(o for o, _n in first_two)              # 最早一段的起点 = 砍头位置
    head = sb[:cut].rstrip('\n')                     # 保留段（第 162 轮）
    tail = sb[cut:]                                  # 被砍段（161 + 160）
    ck('1.1 被砍段以 "## 🟢 R17 第 161 轮" 开头', tail.startswith('## 🟢 R17 第 161 轮'),
       tail[:26])
    ck('1.2 被砍段含 161 与 160 两段',
       'R17 第 161 轮' in tail and 'R17 第 160 轮' in tail)
    ck('1.3 保留段只含第 162 轮',
       'R17 第 162 轮' in head and 'R17 第 161 轮' not in head)
    new_sb = head + '\n' if head else ''
    new_ba = ba.rstrip('\n') + '\n\n' + tail.rstrip('\n') + '\n'
    ck('2.1 新看板 CR == 0', new_sb.count('\r') == 0)
    ck('2.2 新归档 CR == 2952', new_ba.count('\r') == 2952, new_ba.count('\r'))
    ck('2.3 新看板行数 < 260', new_sb.count('\n') < 260, new_sb.count('\n'))
    ck('2.4 反控(a)：新看板是原看板的严格**前缀**（只砍尾、一字未改）',
       sb.startswith(new_sb) and len(new_sb) < len(sb), 'prefix_ok')
    ck('2.4b 反控：新看板**不是**原看板的后缀（首版 S-490 那个方向）',
       not sb.endswith(new_sb))
    ck('2.5 反控(b)：归档尾部逐字等于被砍段',
       new_ba.rstrip('\n').endswith(tail.rstrip('\n')))
    ck('2.6 归档只增不减：旧归档是新归档的前缀', new_ba.startswith(ba.rstrip('\n')))
    ck('2.7 字符账闭合：len(head_raw) + len(tail) == len(sb)（砍点前后互补）',
       len(sb[:cut]) + len(tail) == len(sb), (len(sb[:cut]), len(tail), len(sb)))
    ck('2.7b 新看板 == 原看板砍点前的内容去掉尾部空行后加一个换行',
       new_sb == sb[:cut].rstrip('\n') + '\n', (len(new_sb), cut))
    if fails:
        print('\n[abort] 校验失败，不写任何文件')
        sys.exit(1)
    b1 = bak(BA, 'archive')
    ck('3.1 备份归档 %s' % os.path.basename(b1), rb(b1) == ba.encode('utf-8'))
    io.open(BA, 'w', encoding='utf-8', newline='').write(new_ba)
    ck('3.2 归档回读一致', io.open(BA, encoding='utf-8', newline='').read() == new_ba)
    b2 = bak(SB, 'board')
    ck('3.3 备份看板 %s' % os.path.basename(b2), rb(b2) == sb.encode('utf-8'))
    io.open(SB, 'w', encoding='utf-8', newline='').write(new_sb)
    ck('3.4 看板回读一致', io.open(SB, encoding='utf-8', newline='').read() == new_sb)
    print('     归档 %d -> %d B (+%d)' % (len(ba.encode()), len(new_ba.encode()),
                                        len(new_ba.encode()) - len(ba.encode())))
    print('     看板 %d -> %d B (行 %d -> %d)' % (
        len(sb.encode()), len(new_sb.encode()), sb.count('\n'), new_sb.count('\n')))

print('\n== 终态复验 ==')
f_sb = io.open(SB, encoding='utf-8', newline='').read()
f_ba = io.open(BA, encoding='utf-8', newline='').read()
ck('4.1 看板 CR == 0', f_sb.count('\r') == 0)
ck('4.2 归档 CR == 2952', f_ba.count('\r') == 2952, f_ba.count('\r'))
ck('4.3 看板行数 < 260', f_sb.count('\n') < 260, f_sb.count('\n'))
ck('4.4 看板不含 161/160', 'R17 第 161 轮' not in f_sb and 'R17 第 160 轮' not in f_sb)
ck('4.5 归档含 161/160', 'R17 第 161 轮' in f_ba and 'R17 第 160 轮' in f_ba)
ck('4.6 看板仍含第 162 轮', 'R17 第 162 轮' in f_sb)
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
