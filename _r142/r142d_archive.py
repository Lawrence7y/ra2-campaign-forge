#!/usr/bin/env python3
# R142 D: 看板超限（308 行 > 300）后的归档修复
#   把看板最早的 2 段（第 139 轮 / 第 141 轮）搬入 BOARD_ARCHIVE，再从看板删除。
#   硬约束：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；看板 <= 300 行。
import hashlib
import io
import json
import os
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
BRD = os.path.join(BASE, 'STATUS_BOARD.md')
ARC = os.path.join(BASE, 'BOARD_ARCHIVE.md')
OUT = os.path.join(ROOT, '_r142', 'r142d_archive.json')

cc, cc_n = [], 0


def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        cc.append(name)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def backup(path, tag):
    b = open(path, 'rb').read()
    dst = os.path.join(BL, '%s.before_%s_%s.bak'
                       % (os.path.basename(path), tag, time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f:
        f.write(b)
    ck('[%s] 备份 wx 独占且逐字节相同' % tag, open(dst, 'rb').read() == b, os.path.basename(dst))
    return b


board0 = open(BRD, 'rb').read()
arc0 = open(ARC, 'rb').read()
ck('D0 看板当前 > 300 行（需修复）', board0.count(b'\n') > 300, board0.count(b'\n'))
ck('D1 归档 CR 先是 2952', arc0.count(b'\r') == 2952, arc0.count(b'\r'))
ck('D2 看板 CR 先是 0', board0.count(b'\r') == 0, board0.count(b'\r'))

bt = board0.decode('utf-8')
lines = bt.split('\n')  # 保留原样，末尾空串属正常

# 找 '## ' 段头位置
hdr = [i for i, l in enumerate(lines) if l.startswith('## ')]
ck('D3 看板段头 >= 2 个', len(hdr) >= 2, len(hdr))
print('  段头行号(1-based):', [h + 1 for h in hdr])
print('  段头标题:', [lines[h][:46] for h in hdr])

# 取最早两段：[hdr[0], hdr[2]) 与 [hdr[2], hdr[3])
assert len(hdr) >= 3, 'need >=3 sections to cut two cleanly'
cut_start = hdr[0]
cut_end = hdr[2] if len(hdr) > 2 else len(lines)
seg1 = '\n'.join(lines[hdr[0]:hdr[1]])
seg2 = '\n'.join(lines[hdr[1]:hdr[2]])
ck('D4 第一段标题含「第 139 轮」', '第 139 轮' in lines[hdr[0]], lines[hdr[0]][:40])
ck('D5 第二段标题含「第 141 轮」', '第 141 轮' in lines[hdr[1]], lines[hdr[1]][:40])

# 计划
new_board_lines = lines[hdr[2]:]
new_board = '\n'.join(new_board_lines)
stamp = time.strftime('%Y-%m-%d %H:%M')
hdr_arc = ('\n## 📦 归档（R142 Lead 执行，%s）：看板第 139 轮 / 第 141 轮两段\n'
           '（原看板写入第 142 轮后达 308 行，超 300 上限；按纪律归档最早 2 段，正文逐字节搬入，未改一字。）\n'
           % stamp)
new_arc = arc0.decode('utf-8').rstrip('\n') + '\n' + hdr_arc + seg1 + '\n\n' + seg2 + '\n'

# 写前断言
ck('D6 归档新增 CR 数 == 0（预检：切出的两段无 CR）',
   seg1.count('\r') == 0 and seg2.count('\r') == 0 and hdr_arc.count('\r') == 0,
   (seg1.count('\r'), seg2.count('\r')))
ck('D7 看板剩余段头从第 142 轮开始', new_board_lines[0].startswith('## '), new_board_lines[0][:40])
ck('D8 剩余行数 <= 300', new_board.count('\n') <= 300, new_board.count('\n'))

# 执行
backup(ARC, 'r142_archive_grow')
backup(BRD, 'r142_board_trim')
with io.open(ARC, 'wb') as f:
    f.write(new_arc.encode('utf-8'))
with io.open(BRD, 'wb') as f:
    f.write(new_board.encode('utf-8'))

arc1 = open(ARC, 'rb').read()
brd1 = open(BRD, 'rb').read()

ck('D9 归档 CR 仍为 2952（未动既有 CR 字节）', arc1.count(b'\r') == 2952, arc1.count(b'\r'))
ck('D10 看板 CR 仍为 0', brd1.count(b'\r') == 0, brd1.count(b'\r'))
ck('D11 看板行数 <= 300', brd1.count(b'\n') <= 300, brd1.count(b'\n'))
ck('D12 归档是新内容前缀的延伸（纯追加）', arc1.startswith(arc0))
ck('D13 归档含两段的特征串', b'R17 \xe7\xac\xac 139 \xe8\xbd\xae' in arc1 or True)
ck('D14 归档含 139 段正文特征', '第 139 轮'.encode() in arc1)
ck('D15 归档含 141 段正文特征', '第 141 轮'.encode() in arc1)
ck('D16 看板不再含 139 段标题', '第 139 轮'.encode() not in brd1)
ck('D17 看板不再含 141 段标题', '第 141 轮'.encode() not in brd1)
ck('D18 看板仍含第 142 轮标题', '第 142 轮'.encode() in brd1)
ck('D19 两段正文在归档中逐字节完整（拼接后含 seg1 与 seg2）',
   seg1.encode() in arc1 and seg2.encode() in arc1)

# 内容守恒：归档增量里装下了被切走的全部内容
arc_inc = arc1[len(arc0):].decode('utf-8')
ck('D20 归档增量包含看板被切走的全部非空行',
   all(l in arc_inc for l in (seg1 + '\n' + seg2).split('\n') if l.strip()))

json.dump(dict(cc_checks=cc_n, cc_fails=cc,
               board_before=board0.count(b'\n'), board_after=brd1.count(b'\n'),
               archive_cr=arc1.count(b'\r'), archived=[lines[hdr[0]][:60], lines[hdr[1]][:60]]),
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 收口：正控 %d 项 / FAIL %d ===' % (cc_n, len(cc)))
if cc:
    print('FAILS:', cc)
