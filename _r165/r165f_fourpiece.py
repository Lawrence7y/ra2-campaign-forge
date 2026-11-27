#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-f · 四件套写入（R14_COMMON §2.170 / 台账 §1220 / LEAD_LOCK OV / 看板第 165 轮）

写入纪律（每次修改前必须执行）：
  1) 在 R17_LEAD_BASELINE/ 用 wx 模式独占创建唯一备份
  2) 断言旧 sha256 与 CR 计数（四项不变量）
  3) 一次性写入（追加，不改任何既有字节）
  4) 回读校验：新增字节数、CR 计数不变、前缀逐字节相同
幂等：已是终态则只做终态校验。
"""
import hashlib
import io
import json
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r165/r165f_fourpiece.json')

FILES = {
    'R14_COMMON': (os.path.join(T, 'R14_COMMON.md'), 1081),
    'LEDGER': (os.path.join(R, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337),
    'LEAD_LOCK': (os.path.join(R, 'lead/LEAD_LOCK'), 137),
    'STATUS_BOARD': (os.path.join(T, 'STATUS_BOARD.md'), 0),
}

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r165f_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


def append(path, cr_expected, new_text, tag, marker):
    """追加 new_text（纯后缀），返回是否改动。"""
    raw = rb(path)
    ck('%s 改前 CR == %d' % (tag, cr_expected), raw.count(b'\r') == cr_expected, raw.count(b'\r'))
    old_sha = sha(raw)
    txt = raw.decode('utf-8')
    if marker in txt:
        ck('%s 幂等：本轮段落已存在' % tag, True)
        return False, old_sha, old_sha
    b = bak(path, tag)
    ck('%s 备份 wx 独占' % tag, os.path.isfile(b), os.path.basename(b))
    ck('%s 备份逐字节等于原文' % tag, sha(rb(b)) == old_sha)
    # 确保原文以单个换行结尾后直接拼接（不引入空行、不改既有字节）
    add = new_text if txt.endswith('\n') else '\n' + new_text
    newraw = raw + add.encode('utf-8')
    with open(path, 'wb') as f:
        f.write(newraw)
    back = rb(path)
    ck('%s 回读前缀逐字节不变' % tag, back[:len(raw)] == raw)
    ck('%s 回读 CR 未变（== %d）' % (tag, cr_expected), back.count(b'\r') == cr_expected,
       back.count(b'\r'))
    ck('%s 回读新增字节 == %d' % (tag, len(add.encode())), len(back) - len(raw) == len(add.encode()),
       len(back) - len(raw))
    ck('%s sha256 已变' % tag, sha(back) != old_sha)
    return True, old_sha, sha(back)


# ---------------------------------------------------------------- 0 · 基线
print('== 0 · 四件套基线（不变量）==')
base = {}
for k, (p, cr) in FILES.items():
    raw = rb(p)
    base[k] = {'path': p, 'cr': raw.count(b'\r'), 'lf': raw.count(b'\n'), 'bytes': len(raw),
               'sha': sha(raw)}
    print('   %-14s CR=%4d LF=%5d bytes=%8d sha=%s' % (k, base[k]['cr'], base[k]['lf'],
                                                      base[k]['bytes'], base[k]['sha'][:16]))
    ck('0.%s CR 等于期望值 %d' % (k, cr), base[k]['cr'] == cr, base[k]['cr'])
    if k == 'STATUS_BOARD':
        ck('0.STATUS_BOARD 行数 <= 300（当前 %d）' % base[k]['lf'], base[k]['lf'] <= 300, base[k]['lf'])

# ---------------------------------------------------------------- 1 · R14_COMMON §2.170
print()
print('== 1 · R14_COMMON §2.170 ==')
sec = io.open(os.path.join(R, '_r165/section_2_170.md'), encoding='utf-8').read()
ck('1.0 §2.170 正文无 CR', sec.count('\r') == 0, sec.count('\r'))
ck('1.1 §2.170 以 ## 2.170 开头', sec.startswith('## 2.170'), sec[:20])
# S-520：四段源文件都带结尾换行；append() 的 `if txt.endswith('\n')` 分支负责不重复补。
# 上一版断言写成「源文件不得以换行结尾」⇒ 与 append 的实现相反，属判据自相矛盾。
ck('1.2 §2.170 以恰好一个换行结尾（append 不会再补，且不会留空行）',
   sec.endswith('\n') and not sec.endswith('\n\n'), repr(sec[-3:]))
changed, s0, s1 = append(FILES['R14_COMMON'][0], 1081, sec, 'R14_COMMON', '\n## 2.170 · R165：')

ck('1.3 §2.170 段头在全文恰 1 次（防重复追加）',
   rb(FILES['R14_COMMON'][0]).decode('utf-8').count('\n## 2.170 · R165：') == 1,
   rb(FILES['R14_COMMON'][0]).decode('utf-8').count('\n## 2.170 · R165：'))

# ---------------------------------------------------------------- 2 · 台账 §1220
print()
print('== 2 · 台账 §1220 ==')
led = io.open(os.path.join(R, '_r165/section_1220.md'), encoding='utf-8').read()
ck('2.0 §1220 无 CR', led.count('\r') == 0)
changed2, l0, l1 = append(FILES['LEDGER'][0], 337, led, 'LEDGER', '\n## §1220\n')

ck('2.3 §1220 段头在全文恰 1 次（防重复追加）',
   rb(FILES['LEDGER'][0]).decode('utf-8').count('\n## §1220\n') == 1,
   rb(FILES['LEDGER'][0]).decode('utf-8').count('\n## §1220\n'))

# ---------------------------------------------------------------- 3 · LEAD_LOCK OV
print()
print('== 3 · LEAD_LOCK OV ==')
lock = io.open(os.path.join(R, '_r165/section_OV.md'), encoding='utf-8').read()
ck('3.0 LEAD_LOCK 段无 CR', lock.count('\r') == 0)
changed3, k0, k1 = append(FILES['LEAD_LOCK'][0], 137, lock, 'LEAD_LOCK', '## OV · R17 第 165 轮')

ck('3.3 OV 段头在全文恰 1 次（防重复追加）',
   rb(FILES['LEAD_LOCK'][0]).decode('utf-8').count('\n## OV · R17 第 165 轮') == 1,
   rb(FILES['LEAD_LOCK'][0]).decode('utf-8').count('\n## OV · R17 第 165 轮'))

# ---------------------------------------------------------------- 4 · 看板第 165 轮（最新在前 => 前插）
print()
print('== 4 · 看板第 165 轮（最新在前 ⇒ 前插，不是追加）==')
board = io.open(os.path.join(R, '_r165/section_board_r165.md'), encoding='utf-8').read()
ck('4.0 看板段无 CR', board.count('\r') == 0)
ck('4.0b 看板段自身含段头恰 1 次', board.count('R17 第 165 轮') == 1, board.count('R17 第 165 轮'))
bp = FILES['STATUS_BOARD'][0]
braw = rb(bp)
btxt = braw.decode('utf-8')
if 'R17 第 165 轮' in btxt:
    ck('4.1 幂等：看板第 165 轮段已存在', True)
    b0 = b1 = sha(braw)
else:
    b0 = sha(braw)
    bb = bak(bp, 'STATUS_BOARD')
    ck('4.1 备份 wx 独占', os.path.isfile(bb), os.path.basename(bb))
    ck('4.2 备份逐字节等于原文', sha(rb(bb)) == b0)
    nb = board + '\n' + btxt
    with open(bp, 'wb') as f:
        f.write(nb.encode('utf-8'))
    back = rb(bp)
    b1 = sha(back)
    ck('4.3 回读后缀逐字节不变（前插只动前缀）', back.decode('utf-8').endswith(btxt))
    ck('4.4 回读 CR 仍 0', back.count(b'\r') == 0, back.count(b'\r'))
    ck('4.5 总行数 <= 300', back.count(b'\n') <= 300, back.count(b'\n'))
    ck('4.6 回归：原首行（第 164 轮段头）仍在', 'R17 第 164 轮' in back.decode('utf-8'))
    ck('4.7 sha256 已变', b1 != b0)

# ---------------------------------------------------------------- 5 · 终态
print()
print('== 5 · 四件套终态 ==')
fin = {}
for k, (p, cr) in FILES.items():
    raw = rb(p)
    fin[k] = {'cr': raw.count(b'\r'), 'lf': raw.count(b'\n'), 'bytes': len(raw), 'sha': sha(raw)}
    print('   %-14s CR=%4d LF=%5d bytes=%8d' % (k, fin[k]['cr'], fin[k]['lf'], fin[k]['bytes']))
    ck('5.%s CR 未变（== %d）' % (k, cr), fin[k]['cr'] == cr, fin[k]['cr'])
    ck('5.%sb 字节只增不减' % k, fin[k]['bytes'] >= base[k]['bytes'],
       (base[k]['bytes'], fin[k]['bytes']))
ck('4.8 看板第 165 轮段头在全文恰 1 次（幂等不重复前插）',
   rb(bp).decode('utf-8').count('## \U0001f7e2 R17 第 165 轮') == 1,
   rb(bp).decode('utf-8').count('## \U0001f7e2 R17 第 165 轮'))

res = {'before': base, 'after': fin, 'FAILS': len(FAILS), 'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('FAILS=%d' % len(FAILS))
for f in FAILS:
    print('   -', f)
sys.exit(1 if FAILS else 0)
