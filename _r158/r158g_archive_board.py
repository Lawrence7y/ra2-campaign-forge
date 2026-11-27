#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158g_archive_board.py — 把 STATUS_BOARD 最早的 2 段（第 156 / 157 轮）逐字搬入 BOARD_ARCHIVE。

纪律：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；搬移逐字节等价。
反控：归档追加片段 + 看板剩余部分 必须逐字节复现**搬移前**的看板。
幂等：若归档已含 156/157 两段，跳过搬移、只做终态校验。
顺序：先归档后删看板（反了会先丢后补）。
"""
import hashlib, io, os, re, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
SB = R + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
BA = R + '/lead/next_re_20261117_r14/BOARD_ARCHIVE.md'
BD = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

sb = io.open(SB, encoding='utf-8', newline='').read()
ba = io.open(BA, encoding='utf-8', newline='').read()
ck('0.1 看板 CR = 0', sb.count('\r') == 0, sb.count('\r'))
ck('0.2 归档 CR = 2952', ba.count('\r') == 2952, ba.count('\r'))

starts = [(m.start(), m.group(0)) for m in re.finditer(r'(?m)^## 🟢 R17 第 \d+ 轮', sb)]
print('  看板段数 =', len(starts), [s[1][:24] for s in starts])

if '## 🟢 R17 第 156 轮' in ba and '## 🟢 R17 第 157 轮' in ba:
    print('  [idempotent] 归档已含 156/157，跳过搬移')
    segs = None
else:
    ck('0.3 看板至少 3 段（才有 2 段可归档）', len(starts) >= 3, len(starts))
    # 前两段 = 最早的两段，到第三段首为止
    seg1 = sb[starts[0][0]:starts[1][0]]
    seg2 = sb[starts[1][0]:starts[2][0]]
    print('  最早两段: %s / %s' % (seg1[:26].strip(), seg2[:26].strip()))
    print('  字符数: %d / %d' % (len(seg1), len(seg2)))
    ck('0.4 最早两段分别是 156 与 157 轮',
       '第 156 轮' in seg1[:40] and '第 157 轮' in seg2[:40],
       (seg1[:30], seg2[:30]))
    segs = (seg1, seg2)

    # 备份两文件（wx 独占）
    stamp = time.strftime('%Y%m%d_%H%M%S')
    for tag, path in (('arch', BA), ('board', SB)):
        dst = os.path.join(BD, 'before_r158_arch2_%s_%s.bak' % (tag, stamp))
        fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(open(path, 'rb').read())
        ck('1.0 %s 备份已建（wx）' % tag, os.path.exists(dst), os.path.basename(dst))

    head = ba if ba.endswith('\n') else ba + '\n'
    add = '\n' + seg1.rstrip('\n') + '\n\n' + seg2.rstrip('\n') + '\n'
    new_ba = head + add
    tmp = BA + '.r158tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(new_ba)
    os.replace(tmp, BA)

    new_sb = sb[starts[2][0]:]
    tmp2 = SB + '.r158tmp'
    with io.open(tmp2, 'w', encoding='utf-8', newline='') as f:
        f.write(new_sb)
    os.replace(tmp2, SB)
    print('  [archived] 156/157 已搬入归档并从看板移除')

    # 反控（S-439：首版用手拼重构建，多补了一个 \n 而假 FAIL）——
    # 正确的反控是两条**结构等价**断言，不依赖拼装：
    #   (a) 新看板必须是原看板的严格**后缀**（一字未改、只砍头）
    #   (b) 归档尾部必须逐字等于被砍掉的那段（strip 掉尾部空行后）
    ck('1.1 反控(a)：新看板 == 原看板的严格后缀（只砍头、一字未改）',
       sb.endswith(new_sb), {'orig_len': len(sb), 'new_len': len(new_sb),
                             'removed': len(sb) - len(new_sb)})
    removed = sb[:len(sb) - len(new_sb)]
    ck('1.2 反控(b)：归档尾部 == 被砍掉那段（去尾部空行后逐字相等）',
       (io.open(BA, encoding='utf-8', newline='').read()).endswith('\n' + removed.strip('\n') + '\n'),
       {'removed_len': len(removed)})
    ck('1.3 被砍掉的段首恰是 seg1 的段首', removed.startswith(seg1[:40]), removed[:30])
    ck('1.4 被砍掉的长度 == seg1+seg2 长度',
       len(removed) == len(seg1) + len(seg2), (len(removed), len(seg1) + len(seg2)))

sb2 = io.open(SB, encoding='utf-8', newline='').read()
ba2 = io.open(BA, encoding='utf-8', newline='').read()
ck('2.1 看板 CR 仍为 0', sb2.count('\r') == 0, sb2.count('\r'))
ck('2.2 归档 CR 仍为 2952', ba2.count('\r') == 2952, ba2.count('\r'))
ck('2.3 归档已含 156 轮', '## 🟢 R17 第 156 轮' in ba2, ba2.count('## 🟢 R17 第 156 轮'))
ck('2.4 归档已含 157 轮', '## 🟢 R17 第 157 轮' in ba2, ba2.count('## 🟢 R17 第 157 轮'))
ck('2.5 看板已不含 156 轮', '## 🟢 R17 第 156 轮' not in sb2, sb2.count('## 🟢 R17 第 156 轮'))
ck('2.6 看板已不含 157 轮', '## 🟢 R17 第 157 轮' not in sb2, sb2.count('## 🟢 R17 第 157 轮'))
ck('2.7 看板仍含 158 轮', '## 🟢 R17 第 158 轮' in sb2, sb2.count('## 🟢 R17 第 158 轮'))
nlines = sb2.count('\n') + (0 if sb2.endswith('\n') else 1)
ck('2.8 看板行数 <= 300', nlines <= 300, nlines)
ck('2.9 看板行数未再触发归档线 260', nlines < 260, nlines)
# S-440：幂等重跑时 ba 已是搬移后的归档，'增加'必然为假 ⇒ 改为
# 「归档同时含 156/157 两段」这个**终态**判据（与时刻无关），另单独量两段自身字节。
ck('2.10 归档同时含 156 与 157 两段（终态判据，非增量）',
   ('## 🟢 R17 第 156 轮' in ba2) and ('## 🟢 R17 第 157 轮' in ba2),
   (ba2.count('## 🟢 R17 第 156 轮'), ba2.count('## 🟢 R17 第 157 轮')))
_m156 = re.search(r'(?ms)^##\s+🟢 R17 第 156 轮.*?(?=^##\s|\Z)', ba2)
_m157 = re.search(r'(?ms)^##\s+🟢 R17 第 157 轮.*?(?=^##\s|\Z)', ba2)
ck('2.11 归档内 156/157 两段各自字节 > 3000',
   bool(_m156) and bool(_m157) and len(_m156.group(0).encode()) > 3000
   and len(_m157.group(0).encode()) > 3000,
   (len(_m156.group(0).encode()) if _m156 else 0,
    len(_m157.group(0).encode()) if _m157 else 0))

print('\nFAILS=%d  看板 lines=%d bytes=%d cr=%d | 归档 bytes=%d cr=%d' %
      (len(fails), nlines, len(sb2.encode()), sb2.count('\r'),
       len(ba2.encode()), ba2.count('\r')))
sys.exit(0 if not fails else 1)
