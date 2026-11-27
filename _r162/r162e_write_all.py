#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r162e_write_all.py —— R162 四件套一次性落盘（含 CR / 节数 / 行数回归断言）。

四件套：
  1) lead/next_re_20261117_r14/R14_COMMON.md  新增 ## 2.167   （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md       新增 ## §1217   （CR 必须保持 337）
  3) lead/LEAD_LOCK                            新增 ## OS 段   （CR 必须保持 137）
  4) lead/next_re_20261117_r14/STATUS_BOARD.md 新增第 162 轮    （CR 必须保持 0，行数 <= 300）

写入纪律：wx 独占创建唯一备份 -> 断言旧 sha256 / CR / 节数 -> 一次性写入 -> 回读校验。
任何一步失败即整体放弃（先全部校验，再逐个写）。
支持幂等重跑：若已写过则转终态校验（判据与时刻无关）。
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
BA = T + '/BOARD_ARCHIVE.md'
BD = T + '/R17_LEAD_BASELINE'
SRC = R + '/_r162'
V543 = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
V543_SHA = '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f'

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r162_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


def sec_rc(t):
    return [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', t.replace('\r\n', '\n'))]


def sec_led(t):
    return [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', t.replace('\r\n', '\n'))]


cr = lambda b: b.count(b'\r')

print('== 0 · 旧态断言（任一失败即整体不写）==')
_rb0, _lb0, _kb0, _bb0 = rb(RC), rb(LED), rb(LOCK), rb(BRD)
ALREADY = ('## 2.167' in _rb0.decode('utf-8').replace('\r\n', '\n')
           and '## §1217' in _lb0.decode('utf-8').replace('\r\n', '\n'))
if ALREADY:
    print('  [already-written] 四件套已含本轮新节，转为终态校验')
    ck('T1 R14_COMMON CR 仍 1081', cr(_rb0) == 1081, cr(_rb0))
    ck('T2 LEDGER CR 仍 337', cr(_lb0) == 337, cr(_lb0))
    ck('T3 LEAD_LOCK CR 仍 137', cr(_kb0) == 137, cr(_kb0))
    ck('T4 STATUS_BOARD CR 仍 0', cr(_bb0) == 0, cr(_bb0))
    _sc = sec_rc(_rb0.decode('utf-8'))
    _sl = sec_led(_lb0.decode('utf-8'))
    ck('T5 R14_COMMON 末节 167 且节数 161', (len(_sc), max(_sc)) == (161, 167),
       (len(_sc), max(_sc)))
    ck('T6 LEDGER 末节 1217', max(_sl) == 1217, max(_sl))
    _bt = _bb0.decode()
    ck('T7 看板行数 <= 300', _bt.count('\n') <= 300, _bt.count('\n'))
    ck('T8 看板第 162 轮在最前', _bt.index('R17 第 162 轮') < _bt.index('R17 第 161 轮'))
    ck('T9 V543 一字未动', sha(rb(V543)) == V543_SHA)
    print('\nFAILS:', fails if fails else 'NONE')
    sys.exit(1 if fails else 0)

o_rc, o_led, o_lock, o_brd, o_ba = rb(RC), rb(LED), rb(LOCK), rb(BRD), rb(BA)
print('  R14_COMMON         sha=%s bytes=%d CR=%d' % (sha(o_rc)[:16], len(o_rc), cr(o_rc)))
print('  GOAL_THREE_TARGETS sha=%s bytes=%d CR=%d' % (sha(o_led)[:16], len(o_led), cr(o_led)))
print('  LEAD_LOCK          sha=%s bytes=%d CR=%d' % (sha(o_lock)[:16], len(o_lock), cr(o_lock)))
print('  STATUS_BOARD       sha=%s bytes=%d CR=%d lines=%d'
      % (sha(o_brd)[:16], len(o_brd), cr(o_brd), o_brd.decode().count('\n')))
print('  BOARD_ARCHIVE      sha=%s bytes=%d CR=%d' % (sha(o_ba)[:16], len(o_ba), cr(o_ba)))

ck('0.1 R14_COMMON CR == 1081', cr(o_rc) == 1081, cr(o_rc))
ck('0.2 LEDGER CR == 337', cr(o_led) == 337, cr(o_led))
ck('0.3 LEAD_LOCK CR == 137', cr(o_lock) == 137, cr(o_lock))
ck('0.4 STATUS_BOARD CR == 0', cr(o_brd) == 0, cr(o_brd))
ck('0.5 BOARD_ARCHIVE CR == 2952', cr(o_ba) == 2952, cr(o_ba))
n0 = o_brd.decode().count('\n')
ck('0.6 看板行数 < 260（无需归档）', n0 < 260, n0)

rc_t = o_rc.decode('utf-8')
led_t = o_led.decode('utf-8')
lock_t = o_lock.decode('utf-8')
brd_t = o_brd.decode('utf-8')
sc, sl = sec_rc(rc_t), sec_led(led_t)
ck('0.7 R14_COMMON 160 节、末节 166', (len(sc), max(sc)) == (160, 166), (len(sc), max(sc)))
ck('0.8 LEDGER 末节 1216', max(sl) == 1216, max(sl))
ck('0.9 R14_COMMON 尚无 2.167', 167 not in sc)
ck('0.10 LEDGER 尚无 §1217', 1217 not in sl)
ck('0.11 LEAD_LOCK 末段是 OR', '## OR ·' in lock_t and '## OS ·' not in lock_t)
ck('0.12 看板尚无第 162 轮', 'R17 第 162 轮' not in brd_t)
if fails:
    print('\n[abort] 旧态断言失败，不写任何文件')
    sys.exit(1)

s2 = io.open(SRC + '/section_2_167.md', encoding='utf-8', newline='').read()
s1217 = io.open(SRC + '/section_1217.md', encoding='utf-8', newline='').read()
sos = io.open(SRC + '/section_OS.md', encoding='utf-8', newline='').read()
sbrd = io.open(SRC + '/section_board_r162.md', encoding='utf-8', newline='').read()

print('\n== 0b · 片段自检 ==')
for nm, t in (('2.167', s2), ('§1217', s1217), ('OS', sos), ('board162', sbrd)):
    ck('0b.%s 片段非空 / 无 CR / 无 C0' % nm,
       len(t) > 200 and '\r' not in t and not re.search(r'[\x00-\x08\x0b-\x1f]', t),
       (len(t), t.count('\r')))
ck('0b.5 2.167 片段以 "## 2.167" 开头', s2.startswith('## 2.167'))
ck('0b.6 §1217 片段以 "## §1217" 开头', s1217.startswith('## §1217'))
ck('0b.7 OS 片段以 "## OS ·" 开头', sos.startswith('## OS ·'))
ck('0b.8 看板片段以 "## 🟢 R17 第 162 轮" 开头', sbrd.startswith('## 🟢 R17 第 162 轮'))
# 卡面纪律：_cards 不得出现反引号 —— 四件套不是卡面，允许反引号；此处只检查片段无 CR
ck('0b.9 四片段均无 CR（CR 总数不变的必要条件）',
   all('\r' not in t for t in (s2, s1217, sos, sbrd)))

new_rc = rc_t.rstrip('\n') + '\n\n' + s2.rstrip('\n') + '\n'
new_led = led_t.rstrip('\n') + '\n\n' + s1217.rstrip('\n') + '\n'
new_lock = lock_t.rstrip('\n') + '\n\n' + sos.rstrip('\n') + '\n'
new_brd = sbrd.rstrip('\n') + '\n\n' + brd_t.lstrip('\n')

print('\n== 1 · 写前内存里校验新态 ==')
sc2, sl2 = sec_rc(new_rc), sec_led(new_led)
ck('1.1 R14_COMMON 新态 161 节、末节 167', (len(sc2), max(sc2)) == (161, 167), (len(sc2), max(sc2)))
ck('1.2 R14_COMMON 新态 CR 仍 1081', cr(new_rc.encode()) == 1081, cr(new_rc.encode()))
ck('1.3 LEDGER 新态末节 1217', max(sl2) == 1217, max(sl2))
ck('1.4 LEDGER 新态 CR 仍 337', cr(new_led.encode()) == 337, cr(new_led.encode()))
ck('1.5 LEAD_LOCK 新态 CR 仍 137', cr(new_lock.encode()) == 137, cr(new_lock.encode()))
ck('1.6 看板新态 CR 仍 0', cr(new_brd.encode()) == 0, cr(new_brd.encode()))
n1 = new_brd.count('\n')
ck('1.7 看板新态行数 <= 300', n1 <= 300, n1)
ck('1.8 看板第 162 轮在最前（先出现于第 161 轮）',
   new_brd.index('R17 第 162 轮') < new_brd.index('R17 第 161 轮'))
ck('1.9 旧内容逐字保留（新看板以原看板为后缀）', new_brd.endswith(brd_t.lstrip('\n')))
ck('1.10 LEAD_LOCK 新态含 OS 且 OR 仍在', '## OS ·' in new_lock and '## OR ·' in new_lock)
if fails:
    print('\n[abort] 新态校验失败，不写任何文件')
    sys.exit(1)

print('\n== 2 · 备份 + 一次性写入 + 回读 ==')
for path, old_b, new_t, label in ((RC, o_rc, new_rc, 'common'),
                                  (LED, o_led, new_led, 'ledger'),
                                  (LOCK, o_lock, new_lock, 'lock'),
                                  (BRD, o_brd, new_brd, 'board')):
    b = bak(path, label)
    ck('2.%s 备份 %s' % (label, os.path.basename(b)), os.path.exists(b) and rb(b) == old_b)
    with open(path, 'wb') as f:
        f.write(new_t.encode('utf-8'))
    ck('2.%s 回读逐字一致' % label, rb(path) == new_t.encode('utf-8'))
    print('     %-8s %d -> %d B (+%d)' % (label, len(old_b), len(new_t.encode()),
                                          len(new_t.encode()) - len(old_b)))

print('\n== 3 · 写后全量复验 ==')
f_rc, f_led, f_lock, f_brd = rb(RC), rb(LED), rb(LOCK), rb(BRD)
ck('3.1 R14_COMMON CR == 1081', cr(f_rc) == 1081, cr(f_rc))
ck('3.2 LEDGER CR == 337', cr(f_led) == 337, cr(f_led))
ck('3.3 LEAD_LOCK CR == 137', cr(f_lock) == 137, cr(f_lock))
ck('3.4 STATUS_BOARD CR == 0', cr(f_brd) == 0, cr(f_brd))
ck('3.5 R14_COMMON 161 节末 167',
   (len(sec_rc(f_rc.decode())), max(sec_rc(f_rc.decode()))) == (161, 167))
ck('3.6 LEDGER 末节 1217', max(sec_led(f_led.decode())) == 1217)
ck('3.7 看板行数 <= 300', f_brd.decode().count('\n') <= 300, f_brd.decode().count('\n'))
ck('3.8 BOARD_ARCHIVE 一字未动', sha(rb(BA)) == sha(o_ba),
   (sha(rb(BA))[:16], sha(o_ba)[:16]))
ck('3.9 V543 FACT_INDEX 一字未动', sha(rb(V543)) == V543_SHA)
m = re.search(r'(?ms)^##\s+2\.167\b.*?(?=^##\s+2\.\d|\Z)', f_rc.decode('utf-8').replace('\r\n', '\n'))
ck('3.10 2.167 实测字节可量', m is not None, len(m.group(0).encode()) if m else None)
if m:
    print('      2.167 = %d B ; 下界（一半）= %d' % (len(m.group(0).encode()),
                                                    len(m.group(0).encode()) // 2))
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
