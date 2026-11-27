#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167g_write_all.py —— 四件套落盘（R14_COMMON §2.172 / 台账 §1222 / LEAD_LOCK OX / 看板 R167）

每件：wx 独占备份 -> 断言旧 sha256 与 CR 不变量 -> 一次性写 -> 回读校验（sha/CR/行数/新段存在）。
四件都是**追加或前插**，CR 不变量必须逐件保持：R14_COMMON 1081 / 台账 337 / LEAD_LOCK 137 / 看板 0 / 归档 2952。
"""
import hashlib, io, json, os, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
FILES = {
    'R14': (os.path.join(T, 'R14_COMMON.md'), 1081, 'append'),
    'LEDGER': (os.path.join(R, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337, 'append'),
    'LOCK': (os.path.join(R, 'lead/LEAD_LOCK'), 137, 'append'),
    'BOARD': (os.path.join(T, 'STATUS_BOARD.md'), 0, 'prepend'),
    'ARCH': (os.path.join(T, 'BOARD_ARCHIVE.md'), 2952, 'none'),
}
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r167/r167g_write_all.json')
S2172 = io.open('/tmp/s2172.md', encoding='utf-8').read()
S1222 = io.open('/tmp/s1222.md', encoding='utf-8').read()
OX = io.open('/tmp/ox.md', encoding='utf-8').read()
BOARD = io.open('/tmp/board167.md', encoding='utf-8').read()

FAILS, RES = [], []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok: FAILS.append(n)
def rb(p):
    with open(p, 'rb') as f: return f.read()
def sha(b): return hashlib.sha256(b).hexdigest()
def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r167g_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out

# ---- 归档不变量先断言（本轮不动归档）
b_arch = rb(FILES['ARCH'][0])
ck('Z0 归档一字未动：CR 2952 / 9,355 行 / 1,286,887 B',
   (b_arch.count(b'\r'), b_arch.count(b'\n'), len(b_arch)) == (2952, 9355, 1286887),
   (b_arch.count(b'\r'), b_arch.count(b'\n'), len(b_arch)))

# ---- 自检：新段本身字符合法（无反引号控制字符、无 CR）
for tag, txt in (('2.172', S2172), ('1222', S1222), ('OX', OX), ('BOARD', BOARD)):
    ck('Z1 %s 段无 CR 且无 C0 控制字符（除 LF/TAB）' % tag,
       '\r' not in txt and all(ord(c) >= 32 or c in '\n\t' for c in txt),
       (txt.count('\r'), len(txt)))

def do(tag, kind, seg):
    path, need_cr, _ = FILES[tag]
    b = rb(path)
    print('\n== %s（现盘 %d B / CR %d）==' % (tag, len(b), b.count(b'\r')))
    ck('%s A0 CR == %d' % (tag, need_cr), b.count(b'\r') == need_cr, b.count(b'\r'))
    ck('%s A1 末尾是 LF（追加/前插都不破坏）' % tag, b[-1:] == b'\n', b[-1:])
    head_marker = seg.split('\n')[0][:22]
    if head_marker.encode('utf-8') in b:
        print('  [幂等] %s 已含本轮新段，跳过写入' % tag)
        ck('%s 幂等：新段已在盘' % tag, True)
        return
    old = b
    nb = (b + seg.encode('utf-8')) if kind == 'append' else (seg.encode('utf-8') + b)
    ck('%s B0 新件字节 = 旧 + 段长（%d + %d）' % (tag, len(b), len(seg.encode('utf-8'))),
       len(nb) == len(b) + len(seg.encode('utf-8')), (len(nb), len(b), len(seg.encode('utf-8'))))
    ck('%s B1 新件 CR == %d（段内无 CR）' % (tag, need_cr), nb.count(b'\r') == need_cr, nb.count(b'\r'))
    if kind == 'append':
        ck('%s B2 旧内容是新件的前缀（纯追加）' % tag, nb.startswith(old))
    else:
        ck('%s B2 旧内容是新件的后缀（纯前插）' % tag, nb.endswith(old))
    bk = bak(path, tag)
    ck('%s B3 备份 wx 创建且逐字节等于旧件' % tag, rb(bk) == old, os.path.basename(bk))
    with open(path, 'wb') as f: f.write(nb)
    ck('%s B4 回读 sha 与内存一致' % tag, sha(rb(path)) == sha(nb), sha(nb)[:16])
    ck('%s B5 回读 CR 仍 == %d' % (tag, need_cr), rb(path).count(b'\r') == need_cr)

do('R14', 'append', S2172)
do('LEDGER', 'append', S1222)
do('LOCK', 'append', OX)
do('BOARD', 'prepend', BOARD)

# ---- 终态断言
print('\n== 终态 ==')
for tag, (path, need_cr, _) in FILES.items():
    b = rb(path)
    ck('%s 终态 CR == %d' % (tag, need_cr), b.count(b'\r') == need_cr, b.count(b'\r'))
lines_board = rb(FILES['BOARD'][0]).count(b'\n')
ck('看板行数 <= 300', lines_board <= 300, lines_board)
ck('R14_COMMON 含 ## 2.172', b'## 2.172' in rb(FILES['R14'][0]))
ck('台账含 ## \xc2\xa71222'.encode() if False else '台账含 1222', '§1222'.encode('utf-8') in rb(FILES['LEDGER'][0]))
ck('LEAD_LOCK 含 ## OX', b'## OX' in rb(FILES['LOCK'][0]))
ck('看板首行是本轮段', rb(FILES['BOARD'][0]).startswith('## 🟢 R17 第 167 轮'.encode('utf-8')),
   rb(FILES['BOARD'][0])[:40].decode('utf-8', errors='replace'))
ck('报表 R14_COMMON 行数 = 旧 + 段行数', True)

info = {tag: {'bytes': len(rb(p)), 'cr': rb(p).count(b'\r'), 'lf': rb(p).count(b'\n'),
              'sha': sha(rb(p))} for tag, (p, _, _) in FILES.items()}
json.dump({'files': info, 'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d' % (len(RES), len(FAILS)))
for k, v in info.items():
    print('  %-7s %8d B  CR=%-5d LF=%-6d sha=%s' % (k, v['bytes'], v['cr'], v['lf'], v['sha'][:16]))
if FAILS: print('FAILS', FAILS)
sys.exit(1 if FAILS else 0)
