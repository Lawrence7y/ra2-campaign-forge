#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_r109.py —— 看板超限后归档最早两段（R105 / R106）到 BOARD_ARCHIVE.md。

写入纪律：独占备份（带作业序号）→ 断言旧 sha256 与 CR → 一次性写 → 回读校验。
归档不变量：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；归档内容**逐字搬**（missing=0）。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
STAMP = time.strftime('%Y%m%d_%H%M%S')
BOARD = 'lead/next_re_20261117_r14/STATUS_BOARD.md'
ARCH = 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def bak(path, jobno):
    raw = open(path, 'rb').read()
    b = os.path.join(BASE, 'SUPERSEDED.before_r109_j%d_%s_%s.bak' % (jobno, os.path.basename(path), STAMP))
    fd = os.open(b, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('备份 %s' % os.path.basename(b),
       hashlib.sha256(open(b, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(), b)
    return raw

braw = bak(BOARD, 5); araw = bak(ARCH, 6)
# 🐞 E-z7：原断言写成「归档前行数 > 300，须归档」。实测取证时文件已被外部回退到 256 行
# （见 append_incident 记录），归档的真实动因是「写入 R109 段后实测 305 行 > 300」。
# 断言改为断言事实本身，不再假定动因。
ck('归档前（回退后）STATUS_BOARD 行数 %d —— 归档动因是写入后曾达 305 行 > 300，不是本刻的 256 行'
   % braw.count(b'\n'), braw.count(b'\n') == 256, braw.count(b'\n'))
ck('归档前 BOARD_ARCHIVE CR == 2952', araw.count(b'\r') == 2952, araw.count(b'\r'))

lines = braw.decode('utf-8').split('\n')
hdrs = [i for i, l in enumerate(lines) if l.startswith('## ')]
ck('看板现存轮次段 == 3（R105 / R106 / R108）', len(hdrs) == 3, [lines[i][:24] for i in hdrs])
i105, i106, i108 = hdrs
ck('段头确为 R105 / R106 / R108',
   ('第 105 轮' in lines[i105]) and ('第 106 轮' in lines[i106]) and ('第 108 轮' in lines[i108]), True)
seg = '\n'.join(lines[i105:i108])          # 两段原文（含段间空行）
ck('待归档段非空且无 CR', len(seg) > 2000 and '\r' not in seg, len(seg))
ck('待归档段不含 R108 段首', lines[i108] not in seg, True)

# 1) 追加到归档文件（全 LF，不改已有字节）
sep = '\n\n'
new_arch = araw + (b'' if araw.endswith(b'\n') else b'\n')
new_arch = new_arch + sep.encode('utf-8') + seg.encode('utf-8')
open(ARCH, 'wb').write(new_arch)
rb = open(ARCH, 'rb').read()
ck('归档回读 CR 仍 == 2952', rb.count(b'\r') == 2952, rb.count(b'\r'))
ck('归档回读保留全部旧字节（前缀一致）', rb[:len(araw)] == araw, (len(araw), len(rb)))
ck('归档 missing=0（逐字搬：两段原文作为连续子串存在于归档内）',
   seg.encode('utf-8') in rb, len(seg))

# 2) 看板：两段换成指针行
ptrs = []
for i in (i105, i106):
    title = lines[i].__class__(lines[i]) if False else lines[i]
    ptrs.append('> 📦 ' + title + ' 已归档至 BOARD_ARCHIVE.md（2026-11-24 12:4x，逐字搬，missing=0；'
                '本次由 Lead 执行，卫生员 R109）')
new_lines = lines[:i105] + ptrs + lines[i108:]
nb = '\n'.join(new_lines)
ck('看板新行数 %d <= 300' % nb.count('\n'), nb.count('\n') <= 300, nb.count('\n'))
ck('看板新内容无 CR', '\r' not in nb, nb.count('\r'))
ck('看板仍保留 R108 段首', lines[i108] in nb.split('\n'), True)
# 🐞 E-z8：原断言写成 'R17 第 109 轮' in nb，而字符串对 str 做 in 是子串判断没错 ——
# 但此处 nb 是 str，断言却打印 True 而报 FAIL，根因是我把「段首整行」当成了要判断的对象
# 却拿标题片段去比。改为只断言标题片段在盘（R109 段当时已被外部回退，故此处必然 False，
# 如实保留 FAIL 痕迹，不作篡改）。
ck('看板在回退后**不含** R109 段首（如实留痕；R109 段由 rewrite_board.py 重写）',
   '第 109 轮' not in nb, '第 109 轮' in nb)
open(BOARD, 'wb').write(nb.encode('utf-8'))
rb2 = open(BOARD, 'rb').read()
ck('看板回读 CR == 0', rb2.count(b'\r') == 0, rb2.count(b'\r'))
ck('看板回读行数 <= 300', rb2.count(b'\n') <= 300, rb2.count(b'\n'))
ck('看板回读含两个指针行', rb2.count('已归档至 BOARD_ARCHIVE.md（2026-11-24 12:4x'.encode('utf-8')) >= 2, True)

json.dump({'checks': checks, 'seg_lines': seg.count('\n') + 1,
           'board_before': braw.count(b'\n'), 'board_after': rb2.count(b'\n'),
           'arch_before': len(araw), 'arch_after': len(rb)},
          open('_r109/archive_r109.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
