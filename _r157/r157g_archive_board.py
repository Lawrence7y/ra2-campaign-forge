#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R157 归档：把 STATUS_BOARD 最早的 2 段（R154/R155）逐字搬入 BOARD_ARCHIVE。

纪律：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；搬移必须逐字节等价。
反控：把「归档追加 + 看板删除 + 剩余部分」拼回去，必须逐字节复现原看板。
幂等：若归档里已有 R154/R155 段，则跳过搬移、只做终态校验。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
SB = R + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
BA = R + '/lead/next_re_20261117_r14/BOARD_ARCHIVE.md'
BAK = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

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

# 定位看板里的段
starts = [(m.start(), m.group(0)) for m in re.finditer(r'(?m)^## 🟢 R17 第 \d+ 轮', sb)]
print('  看板段数 =', len(starts), [s[1][:20] for s in starts])
ck('0.3 看板恰 3 段（R154/R155/R156）', len(starts) == 3, len(starts))

# 取前两段（含分隔空行的边界处理：段文本 = 从段首到下一段首）
seg1 = sb[starts[0][0]:starts[1][0]]
seg2 = sb[starts[1][0]:starts[2][0]]
print('  R154 段 %d 字符 / R155 段 %d 字符' % (len(seg1), len(seg2)))
ck('0.4 R154 段首含「第 154 轮」', '第 154 轮' in seg1[:40], seg1[:30])
ck('0.5 R155 段首含「第 155 轮」', '第 155 轮' in seg2[:40], seg2[:30])

if '## 🟢 R17 第 154 轮' in ba and '## 🟢 R17 第 155 轮' in ba:
    print('归档已含 R154/R155，跳过搬移')
else:
    # 先归档（追加到归档末尾），再删看板 —— 顺序不能反（反了会先丢后补）
    bak_ba = os.path.join(BAK, 'BOARD_ARCHIVE.md.before_r157_arch_%s.bak'
                          % __import__('time').strftime('%Y%m%d_%H%M%S'))
    fd = os.open(bak_ba, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(BA, 'rb').read())
    ck('1.0 归档备份已建（wx）', os.path.exists(bak_ba))

    new_ba = (ba if ba.endswith('\n') else ba + '\n') + '\n' + seg1.rstrip('\n') + '\n\n' + seg2.rstrip('\n') + '\n'
    tmp = BA + '.r157tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(new_ba)
    os.replace(tmp, BA)

    new_sb = sb[starts[2][0]:]
    tmp2 = SB + '.r157tmp'
    with io.open(tmp2, 'w', encoding='utf-8', newline='') as f:
        f.write(new_sb)
    os.replace(tmp2, SB)
    print('已归档 R154/R155 并从看板移除')

# ---------- 终态校验 ----------
sb2 = io.open(SB, encoding='utf-8', newline='').read()
ba2 = io.open(BA, encoding='utf-8', newline='').read()
ck('2.1 看板 CR 仍为 0', sb2.count('\r') == 0, sb2.count('\r'))
ck('2.2 归档 CR 仍为 2952', ba2.count('\r') == 2952, ba2.count('\r'))
ck('2.3 归档已含 R154 段', '## 🟢 R17 第 154 轮' in ba2, ba2.count('## 🟢 R17 第 154 轮'))
ck('2.4 归档已含 R155 段', '## 🟢 R17 第 155 轮' in ba2, ba2.count('## 🟢 R17 第 155 轮'))
ck('2.5 看板已不含 R154 段', '## 🟢 R17 第 154 轮' not in sb2, '')
ck('2.6 看板已不含 R155 段', '## 🟢 R17 第 155 轮' not in sb2, '')
ck('2.7 看板仍含 R156 段', '## 🟢 R17 第 156 轮' in sb2, '')
print('    看板 %d 行 / %d B   归档 %d 行 / %d B'
      % (sb2.count('\n'), len(sb2.encode()), ba2.count('\n'), len(ba2.encode())))

# 反控：拼回去必须逐字节复现原看板
# 归档末尾追加的正是 seg1 + seg2，故 original == seg1 + seg2 + sb_new
rebuilt = seg1 + seg2 + sb2
ck('2.8 反控：seg1 + seg2 + 新看板 逐字节复现原看板', rebuilt == sb,
   (len(rebuilt), len(sb)))

print('    归档 sha256 =', hashlib.sha256(ba2.encode()).hexdigest()[:8])
print('    看板 sha256 =', hashlib.sha256(sb2.encode()).hexdigest()[:8])

print()
print('== 收口 ==')
if fails:
    print('FAIL 共 %d 条：' % len(fails))
    for f in fails:
        print('   -', f)
else:
    print('全部 PASS（无 FAIL）')
sys.exit(1 if fails else 0)
