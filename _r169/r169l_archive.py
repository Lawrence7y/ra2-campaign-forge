#!/usr/bin/env python3
"""R169 L：看板归档（写入第 169 轮后行数 263 >= 260 ⇒ 触发归档，把最早 2 段搬进 BOARD_ARCHIVE）。

纪律：
  · BOARD_ARCHIVE.md CR 必须保持 2952；STATUS_BOARD.md CR 必须保持 0；
  · 归档只搬整段（以行首 '## ' 分段），原文不改一字；
  · 搬走的字节必须原样出现在 ARCHIVE 里（逐字节包含断言）；
  · 归档后 STATUS_BOARD 行数 <= 300（且回到 260 以下，下一轮无需再归档）。
"""
import hashlib, json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
BRD = T + '/STATUS_BOARD.md'
ARC = T + '/BOARD_ARCHIVE.md'
BAKDIR = T + '/R17_LEAD_BASELINE'

def sha(b): return hashlib.sha256(b).hexdigest()

def backup(path, tag):
    b = open(path, 'rb').read()
    dst = os.path.join(BAKDIR, os.path.basename(path) + '.before_r169_' + tag + '.bak')
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(b)
    assert sha(open(dst, 'rb').read()) == sha(b)
    return dst

brd_raw = open(BRD, 'rb').read()
arc_raw = open(ARC, 'rb').read()
assert brd_raw.count(b'\r') == 0 and arc_raw.count(b'\r') == 2952
brd_lines = brd_raw.decode('utf-8').split('\n')
n_before = len(brd_lines) - 1 if brd_lines[-1] == '' else len(brd_lines)
print('board lines before =', n_before, ' archive CR =', arc_raw.count(b'\r'))

# 按行首 '## ' 切段
idx = [i for i, ln in enumerate(brd_lines) if ln.startswith('## ')]
print('sections:', len(idx), 'first 4 at lines', idx[:4])
assert len(idx) >= 3, idx
# 看板最新段在最上（前插），故「最早」两段在末尾：搬走 idx[-2] 起的全部
cut = idx[-2]
moved = '\n'.join(brd_lines[cut:])
rest = '\n'.join(brd_lines[:cut])
assert moved and rest
# 原文不改：搬走的串必须逐字出现在原看板里
assert moved in brd_raw.decode('utf-8')

brd_new_txt = rest if rest.endswith('\n') else rest + '\n'
arc_new_txt = arc_raw.decode('utf-8').rstrip('\n') + '\n\n' + moved + '\n'
brd_new = brd_new_txt.encode('utf-8')
arc_new = arc_new_txt.encode('utf-8')

backup(BRD, 'ARCHIVE_BRD')
backup(ARC, 'ARCHIVE_ARC')
open(BRD, 'wb').write(brd_new)
open(ARC, 'wb').write(arc_new)

rb = open(BRD, 'rb').read(); ra = open(ARC, 'rb').read()
n_after = rb.count(b'\n')

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('L1 STATUS_BOARD 仍 LF-only（CR == 0）', rb.count(b'\r') == 0, rb.count(b'\r'))
chk('L2 BOARD_ARCHIVE CR 仍 == 2952', ra.count(b'\r') == 2952, ra.count(b'\r'))
chk('L3 搬走的两段逐字出现在 ARCHIVE 里', moved.encode('utf-8') in ra, {'moved_bytes': len(moved.encode())})
chk('L4 归档后看板行数 <= 260（下一轮无需再归档）', n_after <= 260, {'after': n_after, 'before': n_before})
chk('L5 看板第 1 行仍是第 169 轮（前插段未被动）', rb.decode('utf-8').split('\n')[0].startswith('## 🟢 R17 第 169 轮'),
    rb.decode('utf-8').split('\n')[0][:50])
chk('L6 看板剩余段数 = 原段数 - 2', len([1 for ln in rb.decode('utf-8').split('\n') if ln.startswith('## ')]) == len(idx) - 2,
    {'before': len(idx), 'after': len([1 for ln in rb.decode('utf-8').split('\n') if ln.startswith('## ')])})
chk('L7 不丢字：ARCHIVE 增加字节 == 搬走字节 + 分隔符',
    len(arc_new) - len(arc_raw) >= len(moved.encode()), {'delta': len(arc_new) - len(arc_raw)})

out = {'board_lines_before': n_before, 'board_lines_after': n_after,
       'moved_bytes': len(moved.encode()), 'sections_before': len(idx),
       'sections_after': len([1 for ln in rb.decode('utf-8').split('\n') if ln.startswith('## ')]),
       'brd_sha': sha(rb), 'arc_sha': sha(ra),
       'arc_cr': ra.count(b'\r'), 'brd_cr': rb.count(b'\r'),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169l_archive.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
print('board', n_before, '->', n_after, 'sections', len(idx), '->', out['sections_after'])
