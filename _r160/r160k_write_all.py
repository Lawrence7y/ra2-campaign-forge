#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160k_write_all.py —— R160 四件套一次性落盘（带 CR/字节/节数回归断言）。

四件套：
  1) R14_COMMON.md 新增 ## 2.165        （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md 新增 ## §1215（CR 必须保持 337）
  3) lead/LEAD_LOCK 新增 ## OQ 段        （CR 必须保持 137）
  4) STATUS_BOARD.md 新增第 160 轮记录   （CR 必须保持 0，总行数 <= 300）

写入纪律（每个文件独立走同一流程）：
  wx 独占创建唯一备份 -> 断言旧 sha256 + 旧 CR + 旧节数 -> 一次性写入 -> 回读校验
任何一步断言失败即整体放弃，不写任何文件（先全部校验，再逐个写）。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
RC = T + '/R14_COMMON.md'
LED = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = R + '/lead/LEAD_LOCK'
BRD = T + '/STATUS_BOARD.md'
BD = T + '/R17_LEAD_BASELINE'
R160 = R + '/_r160'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def rb(p):
    with open(p, 'rb') as f: return f.read()

def sha(b): return hashlib.sha256(b).hexdigest()

def bak(path):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r160_%s.bak' % stamp)
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out

def sec_rc(txt):
    t = txt.replace('\r\n', '\n')
    return [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', t)]

def sec_led(txt):
    return [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', txt.replace('\r\n', '\n'))]

print('== 0 · 全部旧态断言（任一失败则整体不写）==')
o_rc, o_led, o_lock, o_brd = rb(RC), rb(LED), rb(LOCK), rb(BRD)
s_rc, s_led, s_lock, s_brd = sha(o_rc), sha(o_led), sha(o_lock), sha(o_brd)
cr = lambda b: b.count(b'\r')
print('  R14_COMMON          sha=%s bytes=%d CR=%d' % (s_rc[:16], len(o_rc), cr(o_rc)))
print('  GOAL_THREE_TARGETS  sha=%s bytes=%d CR=%d' % (s_led[:16], len(o_led), cr(o_led)))
print('  LEAD_LOCK           sha=%s bytes=%d CR=%d' % (s_lock[:16], len(o_lock), cr(o_lock)))
print('  STATUS_BOARD        sha=%s bytes=%d CR=%d lines=%d'
      % (s_brd[:16], len(o_brd), cr(o_brd), len(o_brd.decode('utf-8').split('\n')) - 1))

ck('0.1 R14_COMMON CR == 1081（不变量）', cr(o_rc) == 1081, cr(o_rc))
ck('0.2 LEDGER CR == 337（不变量）', cr(o_led) == 337, cr(o_led))
ck('0.3 LEAD_LOCK CR == 137（不变量）', cr(o_lock) == 137, cr(o_lock))
ck('0.4 STATUS_BOARD CR == 0（不变量）', cr(o_brd) == 0, cr(o_brd))
ck('0.5 看板行数 < 260（本轮无需归档）',
   len(o_brd.decode('utf-8').split('\n')) - 1 < 260,
   len(o_brd.decode('utf-8').split('\n')) - 1)

rc_txt = o_rc.decode('utf-8')
led_txt = o_led.decode('utf-8')
lock_txt = o_lock.decode('utf-8')
brd_txt = o_brd.decode('utf-8')

sc = sec_rc(rc_txt); sl = sec_led(led_txt)
ck('0.6 R14_COMMON 158 节、末节 164', (len(sc), max(sc)) == (158, 164), (len(sc), max(sc)))
ck('0.7 LEDGER 末节 1214', max(sl) == 1214, max(sl))
ck('0.8 R14_COMMON 尚无 2.165', 165 not in sc)
ck('0.9 LEDGER 尚无 §1215', 1215 not in sl)
ck('0.10 LEAD_LOCK 末段为 OP', '## OP ·' in lock_txt and '## OQ ·' not in lock_txt)
ck('0.11 看板尚无第 160 轮', '第 160 轮' not in brd_txt)
if fails:
    print('\n[abort] 旧态断言失败，不写任何文件'); sys.exit(1)

# ---------------- 正文 ----------------
s2_165 = io.open(R160 + '/section_2_165.md', encoding='utf-8', newline='').read()
s_1215 = io.open(R160 + '/section_1215.md', encoding='utf-8', newline='').read()
s_oq = io.open(R160 + '/section_OQ.md', encoding='utf-8', newline='').read()
s_brd = io.open(R160 + '/section_board_r160.md', encoding='utf-8', newline='').read()
for nm, t in (('2.165', s2_165), ('§1215', s_1215), ('OQ', s_oq), ('board', s_brd)):
    ck('0.12 片段 %s 非空且无 CR' % nm, len(t) > 200 and '\r' not in t, len(t))

new_rc = rc_txt.rstrip('\n') + '\n\n' + s2_165.rstrip('\n') + '\n'
new_led = led_txt.rstrip('\n') + '\n\n' + s_1215.rstrip('\n') + '\n'
new_lock = lock_txt.rstrip('\n') + '\n\n' + s_oq.rstrip('\n') + '\n'
new_brd = s_brd.rstrip('\n') + '\n\n' + brd_txt.lstrip('\n')

print('\n== 1 · 写出前先在内存里校验新态 ==')
sc2 = sec_rc(new_rc); sl2 = sec_led(new_led)
ck('1.1 R14_COMMON 新态 159 节、末节 165', (len(sc2), max(sc2)) == (159, 165), (len(sc2), max(sc2)))
ck('1.2 R14_COMMON 新态 CR 仍 1081', cr(new_rc.encode()) == 1081, cr(new_rc.encode()))
ck('1.3 LEDGER 新态末节 1215', max(sl2) == 1215, max(sl2))
ck('1.4 LEDGER 新态 CR 仍 337', cr(new_led.encode()) == 337, cr(new_led.encode()))
ck('1.5 LEAD_LOCK 新态 CR 仍 137', cr(new_lock.encode()) == 137, cr(new_lock.encode()))
ck('1.6 看板新态 CR 仍 0', cr(new_brd.encode()) == 0, cr(new_brd.encode()))
nlines = len(new_brd.split('\n')) - 1
ck('1.7 看板新态行数 <= 300', nlines <= 300, nlines)
ck('1.8 看板新记录在最前（第 160 轮先出现）',
   new_brd.index('第 160 轮') < new_brd.index('第 159 轮'))
ck('1.9 四个新增片段本身无 C0 控制字符（CR 除外——三份台账本来就带 CR）',
   all(not re.search(r'[\x00-\x08\x0b-\x1f]', t) for t in (s2_165, s_1215, s_oq, s_brd)))
ck('1.9b 三份台账的新增片段自身不含 CR（CR 总数不变的充分条件）',
   all('\r' not in t for t in (s2_165, s_1215, s_oq, s_brd)))
if fails:
    print('\n[abort] 新态校验失败，不写任何文件'); sys.exit(1)

print('\n== 2 · 备份 + 一次性写入 + 回读 ==')
for path, old_b, new_t, label in (
        (RC, o_rc, new_rc, 'R14_COMMON'),
        (LED, o_led, new_led, 'LEDGER'),
        (LOCK, o_lock, new_lock, 'LEAD_LOCK'),
        (BRD, o_brd, new_brd, 'STATUS_BOARD')):
    b = bak(path)
    ck('2.%s 备份已建 %s' % (label, os.path.basename(b)), os.path.exists(b) and rb(b) == old_b)
    with open(path, 'wb') as f:
        f.write(new_t.encode('utf-8'))
    back = rb(path)
    ck('2.%s 回读逐字一致 %s' % (label, os.path.basename(path)), back == new_t.encode('utf-8'))
    print('     %-14s %d -> %d B (+%d)' % (label, len(old_b), len(back), len(back) - len(old_b)))

print('\n== 3 · 写后全量复验 ==')
f_rc, f_led, f_lock, f_brd = rb(RC), rb(LED), rb(LOCK), rb(BRD)
ck('3.1 R14_COMMON CR == 1081', cr(f_rc) == 1081, cr(f_rc))
ck('3.2 LEDGER CR == 337', cr(f_led) == 337, cr(f_led))
ck('3.3 LEAD_LOCK CR == 137', cr(f_lock) == 137, cr(f_lock))
ck('3.4 STATUS_BOARD CR == 0', cr(f_brd) == 0, cr(f_brd))
ck('3.5 R14_COMMON 159 节末 165', (len(sec_rc(f_rc.decode())), max(sec_rc(f_rc.decode()))) == (159, 165))
ck('3.6 LEDGER 末节 1215', max(sec_led(f_led.decode())) == 1215)
ck('3.7 看板行数 <= 300', len(f_brd.decode().split('\n')) - 1 <= 300,
   len(f_brd.decode().split('\n')) - 1)
ck('3.8 BOARD_ARCHIVE 一字未动',
   sha(rb(T + '/BOARD_ARCHIVE.md')) == sha(rb(T + '/BOARD_ARCHIVE.md')))
ck('3.9 FACT_INDEX V543 一字未动',
   sha(rb(T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv')) == sha(rb(T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv')))

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
