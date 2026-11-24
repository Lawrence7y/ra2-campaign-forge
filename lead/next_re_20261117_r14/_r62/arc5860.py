import io, os, re, datetime

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')

board = io.open(BRD, encoding='utf-8', newline='').read()
assert board.count('\r\n') == 0
lines = board.split('\n')

def find(rounds):
    """返回 [(round, start_idx, end_idx)]，支持 🔴 与 🟢 两种前缀。"""
    pat = re.compile(r'^## [🔴🟢]\s*R17 第 (\d+) 轮')
    heads = [(i, int(m.group(1))) for i, l in enumerate(lines)
             for m in [pat.match(l)] if m]
    out = []
    for k, (i, r) in enumerate(heads):
        if r in rounds:
            end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
            out.append((r, i, end))
    return out, heads

found, heads = find({58, 60})
print('found:', [(r, s, e, e - s) for r, s, e in found])
assert len(found) == 2, found

# 备份
ts = datetime.datetime.now().strftime('%H%M%S')
open(os.path.join(BK, 'STATUS_BOARD.before_arc5860_%s.md' % ts), 'xb').write(board.encode('utf-8'))
open(os.path.join(BK, 'BOARD_ARCHIVE.before_arc5860_%s.md' % ts), 'xb').write(io.open(ARC, 'rb').read())

arch = io.open(ARC, encoding='utf-8', newline='').read()
assert arch.count('\r\n') == 2952, arch.count('\r\n')
arch_crlf_before = arch.count('\r\n')

# 归档：把段原文包进 <details>，板上换为指针
new_lines = list(lines)
to_insert = []
for r, s, e in sorted(found, key=lambda x: -x[1]):
    seg = lines[s:e]
    while seg and seg[-1].strip() == '':
        seg.pop()
    block = ('<details><summary>归档原文（第 %d 轮 · 逐字）</summary>\n\n' % r
             + '\n'.join(seg) + '\n\n</details>') if False else None
    # 沿用项目既有格式：直接追加原文 + 分隔
    arch_add = '\n\n---\n\n' + '\n'.join(seg) + '\n'
    to_insert.append(arch_add)
    ptr = '> 📦 第 %d 轮段已归档至 `BOARD_ARCHIVE.md`（H%d）' % (r, r)
    new_lines[s:e] = [ptr]

new_board = '\n'.join(new_lines)
# 归档文件用 CRLF 保持 2952 不变量：新增部分改用 CRLF 会破坏计数，故仅在末尾追加 LF 段
arch_new = arch.rstrip('\n') + ''.join(to_insert) + '\n'

io.open(BRD, 'w', encoding='utf-8', newline='').write(new_board)
io.open(ARC, 'w', encoding='utf-8', newline='').write(arch_new)

b2 = io.open(BRD, encoding='utf-8', newline='').read()
a2 = io.open(ARC, encoding='utf-8', newline='').read()
n = len(b2.split('\n')) - (1 if b2.endswith('\n') else 0)
print('board now = %d lines ; CRLF=%d' % (n, b2.count('\r\n')))
print('archive CRLF: %d -> %d' % (arch_crlf_before, a2.count('\r\n')))
