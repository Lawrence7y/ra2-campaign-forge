#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 K：收口自检 + 给看板补一条「14 B 的逐字节归属」（纯追加）。

补这条的理由：r175a 的 E2c/E2d/E2e 已把 14 B 拆成可逐字节指认的三段，但 V557 的 statement
里那句用的是「键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4」这种粗分组（数字自洽、标签偏笼统）；
本段把精确形式写进看板，供下一轮引用时不必再推。
"""
import hashlib, io, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
F4 = os.path.join(TIER, 'STATUS_BOARD.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
P = os.path.join(TIER, 'D41_SUBST/_audit/EVIDENCE/a2_sites.json')
OUT = os.path.join(ROOT, '_r175/r175k_closeout.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = io.open(P, 'rb').read()
seg = raw[913237:913250]
ck('A1 raw[913237:913250] 逐字节 == b"}, \\"bounds\\": "（13 B）', seg == b'}, "bounds": ', len(seg))
ck('A2 该 13 B 去掉首字节 } 后 == b", \\"bounds\\": "（12 B）', seg[1:] == b', "bounds": ', len(seg[1:]))
ck('A3 文档末字节是 }', raw[-1:] == b'}', raw[-1:])
ck('A4 值末字节偏移 17,624,354 是 ]', raw[17624354:17624355] == b']', raw[17624354:17624355])
ck('A5 14 = 12 + 1(]) + 1(})', 12 + 1 + 1 == 14, 12 + 1 + 1)
ck('A6 14 = (913,250 − 913,237) + 1', (913250 - 913237) + 1 == 14, (913250 - 913237) + 1)

bd = io.open(F4, 'rb').read()
ck('B1 看板 CR == 0', bd.count(b'\r') == 0, bd.count(b'\r'))
t = bd.decode('utf-8')
ADD = '**14 B 的逐字节归属（本轮补，供下轮直接引用）**：14 = b", \\"bounds\\": " 的 **12 B**（`raw[913238:913250]` 逐字节等于）+ 值末 `]` **1 B**（偏移 17,624,354）+ 文档末 `}` **1 B**（偏移 17,624,355）；等价写法 14 = (913,250 − 913,237) + 1。V557 的 statement 里那句「键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4」与上式**同值但标签粗**：8 = `\\"bounds\\"` 含引号、1 + 1 = 冒号与冒号后空格、4 = 逗号 + 逗号后空格 + `]` + `}` —— 数字自洽，引用时以本式为准。\n'
ck('B2 追加前该锚串 0 次', t.count('14 B 的逐字节归属') == 0, t.count('14 B 的逐字节归属'))
new = t + ADD
ck('B3 新 CR == 0', new.encode('utf-8').count(b'\r') == 0, new.encode('utf-8').count(b'\r'))
ck('B4 新行数 < 260', new.count('\n') < 260, new.count('\n'))
ck('B5 以母本为前缀', new.startswith(t), True)
if fails:
    print('★ fail-closed：%d 条未过' % len(fails)); sys.exit(1)
osha = hashlib.sha256(bd).hexdigest()
bak = os.path.join(BASE, 'STATUS_BOARD.md.before_r175k_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(bd)
ck('C1 备份 sha 命中旧 sha', hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == osha, os.path.basename(bak))
io.open(F4, 'w', encoding='utf-8', newline='').write(new)
back = io.open(F4, 'rb').read()
ck('C2 回读一致', back == new.encode('utf-8'), len(back))
ck('C3 回读 CR == 0', back.count(b'\r') == 0, back.count(b'\r'))
print('\n== %d 断言, %d FAIL ==  看板 %d -> %d B / %d 行' % (n, len(fails), len(bd), len(back), back.count(b'\n')))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'assertions': n,
    'board': [len(bd), len(back), back.count(b'\n')]}, ensure_ascii=False, indent=1))
sys.exit(1 if fails else 0)
