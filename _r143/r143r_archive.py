#!/usr/bin/env python3
"""R143 A：看板归档（把最早两段 139/141 搬进 BOARD_ARCHIVE）。

硬约束：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；归档后看板留出的余量
必须够本轮新段（余量 = 300 - 归档后行数）。
"""
import hashlib, io, json, os, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
BRD = os.path.join(BASE, 'STATUS_BOARD.md')
ARC = os.path.join(BASE, 'BOARD_ARCHIVE.md')
OUT = os.path.join(ROOT, '_r143', 'r143r_archive.json')

cc, cc_n = [], 0
def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: cc.append(name)

def backup(path, tag):
    b = open(path, 'rb').read()
    dst = os.path.join(BL, '%s.before_%s_%s.bak' % (os.path.basename(path), tag,
                                                    time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f: f.write(b)
    ck('[%s] 备份 wx 独占且逐字节相同' % tag, open(dst, 'rb').read() == b, os.path.basename(dst))
    return b

board0 = open(BRD, 'rb').read()
arc0 = open(ARC, 'rb').read()
ck('A0 归档 CR 先是 2952', arc0.count(b'\r') == 2952, arc0.count(b'\r'))
ck('A1 看板 CR 先是 0', board0.count(b'\r') == 0, board0.count(b'\r'))
ck('A2 看板行数 299（300 - 本轮余量需先搬段）', board0.count(b'\n') == 299, board0.count(b'\n'))
ck('A3 归档 sha 基线 02049f9f', hashlib.sha256(arc0).hexdigest()[:8] == '02049f9f')
ck('A4 看板 sha 基线 980a27b7', hashlib.sha256(board0).hexdigest()[:8] == '980a27b7')

lines = board0.decode('utf-8').split('\n')
hdr = [i for i, l in enumerate(lines) if l.startswith('## ')]
ck('A5 看板段头恰 3 个', len(hdr) == 3, len(hdr))
ck('A6 第一段是第 139 轮', '第 139 轮' in lines[hdr[0]], lines[hdr[0]][:36])
ck('A7 第二段是第 141 轮', '第 141 轮' in lines[hdr[1]], lines[hdr[1]][:36])
ck('A8 第三段是第 142 轮', '第 142 轮' in lines[hdr[2]], lines[hdr[2]][:36])

seg1 = '\n'.join(lines[hdr[0]:hdr[1]])
seg2 = '\n'.join(lines[hdr[1]:hdr[2]])
rest = lines[hdr[2]:]
ck('A9 切出的两段无 CR', seg1.count('\r') == 0 and seg2.count('\r') == 0)
ck('A10 两段合计行数 = 125 + 101', (hdr[1]-hdr[0]) + (hdr[2]-hdr[1]) == 226,
   (hdr[1]-hdr[0]) + (hdr[2]-hdr[1]))

stamp = time.strftime('%Y-%m-%d %H:%M')
hdr_arc = ('\n## 归档（R143 Lead 执行，%s）：看板第 139 轮 / 第 141 轮两段\n'
           '（原看板 299 行，余量不足以写第 143 轮；按纪律归档最早 2 段，正文逐字节搬入，未改一字。'
           'BOARD_ARCHIVE CR 保持 2952，追加内容全 LF。）\n' % stamp)
new_arc = arc0.decode('utf-8').rstrip('\n') + '\n' + hdr_arc + seg1 + '\n\n' + seg2 + '\n'
new_board = '\n'.join(rest)
ck('A11 归档新增段无 CR', hdr_arc.count('\r') == 0)
ck('A12 归档是纯前缀延伸（旧内容逐字节保留）', new_arc.startswith(arc0.decode('utf-8')))
ck('A13 剩余看板从第 142 轮开始', rest[0].startswith('## ') and '第 142 轮' in rest[0])
ck('A14 归档后看板行数 <= 120（给本轮留足余量）', new_board.count('\n') <= 120, new_board.count('\n'))
ck('A15 归档后看板 CR 仍 0', new_board.count('\r') == 0)

backup(ARC, 'r143_archive_grow')
backup(BRD, 'r143_board_trim')
with io.open(ARC, 'wb') as f: f.write(new_arc.encode('utf-8'))
with io.open(BRD, 'wb') as f: f.write(new_board.encode('utf-8'))

arc1 = open(ARC, 'rb').read(); brd1 = open(BRD, 'rb').read()
ck('A16 归档 CR 仍 2952', arc1.count(b'\r') == 2952, arc1.count(b'\r'))
ck('A17 看板 CR 仍 0', brd1.count(b'\r') == 0, brd1.count(b'\r'))
ck('A18 看板行数 <= 120', brd1.count(b'\n') <= 120, brd1.count(b'\n'))
ck('A19 两段正文在归档中逐字节完整', seg1.encode() in arc1 and seg2.encode() in arc1)
ck('A20 看板不再含 139/141 段头', '第 139 轮'.encode() not in brd1 and '第 141 轮'.encode() not in brd1)
ck('A21 看板仍含第 142 轮', '第 142 轮'.encode() in brd1)
inc = arc1[len(arc0):].decode('utf-8')
ck('A22 归档增量含被切走的全部非空行',
   all(l in inc for l in (seg1 + '\n' + seg2).split('\n') if l.strip()))
ck('A23 归档字节增长 >= 被切走字节', len(arc1) - len(arc0) >= len(seg1.encode()) + len(seg2.encode()),
   len(arc1) - len(arc0))

json.dump(dict(checks=cc_n, fails=cc, board_before=board0.count(b'\n'), board_after=brd1.count(b'\n'),
               arc_bytes_before=len(arc0), arc_bytes_after=len(arc1), arc_cr=arc1.count(b'\r'),
               archived=[lines[hdr[0]][:40], lines[hdr[1]][:40]]),
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 归档：正控 %d 项 / FAIL %d ===' % (cc_n, len(cc)))
if cc: print('FAILS:', cc)
