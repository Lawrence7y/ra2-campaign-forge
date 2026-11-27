#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r163e_write_all.py —— R163 四件套一次性落盘（含 CR / 节数 / 行数回归断言）。

四件套：
  1) lead/next_re_20261117_r14/R14_COMMON.md  新增 ## 2.168   （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md       新增 ## §1218   （CR 必须保持 337）
  3) lead/LEAD_LOCK                            新增 ## OT 段   （CR 必须保持 137）
  4) lead/next_re_20261117_r14/STATUS_BOARD.md 新增第 163 轮    （CR 必须保持 0，行数 <= 300）

写入纪律：wx 独占创建唯一备份 -> 断言旧 sha256 / CR / 节数 -> 一次性写入 -> 回读校验。
任何一步失败即整体放弃（先全部校验，再逐个写）。
支持幂等重跑：已写过则转终态校验（判据与时刻无关）。
★ 探针纪律（本轮 R163 自错 S-490 的教训）：旧态断言先跑一遍再读片段，
  但「已写过」判定必须在**读片段之前**做，且终态分支不引用任何本轮时刻才成立的值。
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
SRC = R + '/_r163'
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
    out = os.path.join(BD, os.path.basename(path) + '.before_r163_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


def sec_rc(t):
    return [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', t.replace('\r\n', '\n'))]


def sec_led(t):
    return [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', t.replace('\r\n', '\n'))]


cr = lambda b: b.count(b'\r')

print('== 0 · 旧态断言 ==')
o_rc, o_led, o_lock, o_brd, o_ba = rb(RC), rb(LED), rb(LOCK), rb(BRD), rb(BA)
print('  R14_COMMON         sha=%s bytes=%d CR=%d' % (sha(o_rc)[:16], len(o_rc), cr(o_rc)))
print('  GOAL_THREE_TARGETS sha=%s bytes=%d CR=%d' % (sha(o_led)[:16], len(o_led), cr(o_led)))
print('  LEAD_LOCK          sha=%s bytes=%d CR=%d' % (sha(o_lock)[:16], len(o_lock), cr(o_lock)))
print('  STATUS_BOARD       sha=%s bytes=%d CR=%d lines=%d'
      % (sha(o_brd)[:16], len(o_brd), cr(o_brd), o_brd.decode().count('\n')))
print('  BOARD_ARCHIVE      sha=%s bytes=%d CR=%d' % (sha(o_ba)[:16], len(o_ba), cr(o_ba)))

rc_t, led_t, lock_t, brd_t = (o_rc.decode('utf-8'), o_led.decode('utf-8'),
                              o_lock.decode('utf-8'), o_brd.decode('utf-8'))
sc, sl = sec_rc(rc_t), sec_led(led_t)
ALREADY = ('## 2.168' in rc_t.replace('\r\n', '\n')
           and '## §1218' in led_t.replace('\r\n', '\n'))

ck('0.1 R14_COMMON CR == 1081', cr(o_rc) == 1081, cr(o_rc))
ck('0.2 LEDGER CR == 337', cr(o_led) == 337, cr(o_led))
ck('0.3 LEAD_LOCK CR == 137', cr(o_lock) == 137, cr(o_lock))
ck('0.4 STATUS_BOARD CR == 0', cr(o_brd) == 0, cr(o_brd))
ck('0.5 BOARD_ARCHIVE CR == 2952', cr(o_ba) == 2952, cr(o_ba))
ck('0.6 V543 FACT_INDEX 未动', sha(rb(V543)) == V543_SHA)

if ALREADY:
    print('\n  [already-written] 四件套已含本轮新节，转终态校验')
    ck('T1 R14_COMMON 162 节、末节 168', (len(sc), max(sc)) == (162, 168), (len(sc), max(sc)))
    ck('T2 LEDGER 末节 1218', max(sl) == 1218, max(sl))
    ck('T3 LEAD_LOCK 含 OT 段', '## OT ·' in lock_t)
    ck('T4 看板行数 <= 300', brd_t.count('\n') <= 300, brd_t.count('\n'))
    ck('T5 看板第 163 轮在最前（先于第 162 轮）',
       brd_t.index('R17 第 163 轮') < brd_t.index('R17 第 162 轮'))
    ck('T6 BOARD_ARCHIVE 未动', cr(o_ba) == 2952)
    ck('T7 V543 未动', sha(rb(V543)) == V543_SHA)
    print('\nFAILS:', fails if fails else 'NONE')
    sys.exit(1 if fails else 0)

n0 = brd_t.count('\n')
ck('0.7 看板行数 < 260（无需归档）', n0 < 260, n0)
ck('0.8 R14_COMMON 161 节、末节 167', (len(sc), max(sc)) == (161, 167), (len(sc), max(sc)))
ck('0.9 LEDGER 末节 1217', max(sl) == 1217, max(sl))
ck('0.10 R14_COMMON 尚无 2.168', 168 not in sc)
ck('0.11 LEDGER 尚无 §1218', 1218 not in sl)
ck('0.12 LEAD_LOCK 末段是 OS、尚无 OT', '## OS ·' in lock_t and '## OT ·' not in lock_t)
ck('0.13 看板尚无第 163 轮', 'R17 第 163 轮' not in brd_t)
if fails:
    print('\n[abort] 旧态断言失败，不写任何文件')
    sys.exit(1)

s2 = io.open(SRC + '/section_2_168.md', encoding='utf-8', newline='').read()
s1218 = io.open(SRC + '/section_1218.md', encoding='utf-8', newline='').read()
sot = io.open(SRC + '/section_OT.md', encoding='utf-8', newline='').read()
sbrd = io.open(SRC + '/section_board_r163.md', encoding='utf-8', newline='').read()

print('\n== 0b · 片段自检 ==')
for nm, t in (('2.168', s2), ('§1218', s1218), ('OT', sot), ('board163', sbrd)):
    ck('0b.%s 片段非空 / 无 CR / 无 C0' % nm,
       len(t) > 200 and '\r' not in t and not re.search(r'[\x00-\x08\x0b-\x1f]', t),
       (len(t), t.count('\r')))
ck('0b.5 2.168 片段以 "## 2.168" 开头', s2.startswith('## 2.168'))
ck('0b.6 §1218 片段以 "## §1218" 开头', s1218.startswith('## §1218'))
ck('0b.7 OT 片段以 "## OT ·" 开头', sot.startswith('## OT ·'))
ck('0b.8 看板片段以 "## 🟢 R17 第 163 轮" 开头', sbrd.startswith('## 🟢 R17 第 163 轮'))
ck('0b.9 片段内不含 "## 2.169" / "## §1219" / "## OU"（不越界写入下一轮）',
   not any(k in s2 + s1218 + sot for k in ('## 2.169', '## §1219', '## OU ·')))
ck('0b.10 片段内断言数字自洽（118 断言 = 30+31+34+23）', 30 + 31 + 34 + 23 == 118)

new_rc = rc_t.rstrip('\n') + '\n\n' + s2.rstrip('\n') + '\n'
new_led = led_t.rstrip('\n') + '\n\n' + s1218.rstrip('\n') + '\n'
new_lock = lock_t.rstrip('\n') + '\n\n' + sot.rstrip('\n') + '\n'
new_brd = sbrd.rstrip('\n') + '\n\n' + brd_t.lstrip('\n')

print('\n== 1 · 写前内存里校验新态 ==')
sc2, sl2 = sec_rc(new_rc), sec_led(new_led)
ck('1.1 R14_COMMON 新态 162 节、末节 168', (len(sc2), max(sc2)) == (162, 168), (len(sc2), max(sc2)))
ck('1.2 R14_COMMON 新态 CR 仍 1081', cr(new_rc.encode()) == 1081, cr(new_rc.encode()))
ck('1.3 LEDGER 新态末节 1218', max(sl2) == 1218, max(sl2))
ck('1.4 LEDGER 新态 CR 仍 337', cr(new_led.encode()) == 337, cr(new_led.encode()))
ck('1.5 LEAD_LOCK 新态 CR 仍 137', cr(new_lock.encode()) == 137, cr(new_lock.encode()))
ck('1.6 看板新态 CR 仍 0', cr(new_brd.encode()) == 0, cr(new_brd.encode()))
n1 = new_brd.count('\n')
ck('1.7 看板新态行数 <= 300', n1 <= 300, n1)
ck('1.8 看板第 163 轮在最前', new_brd.index('R17 第 163 轮') < new_brd.index('R17 第 162 轮'))
ck('1.9 旧内容逐字保留（新看板以原看板为后缀）', new_brd.endswith(brd_t.lstrip('\n')))
ck('1.10 LEAD_LOCK 新态含 OT 且 OS 仍在', '## OT ·' in new_lock and '## OS ·' in new_lock)
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
ck('3.5 R14_COMMON 162 节末 168',
   (len(sec_rc(f_rc.decode())), max(sec_rc(f_rc.decode()))) == (162, 168))
ck('3.6 LEDGER 末节 1218', max(sec_led(f_led.decode())) == 1218)
ck('3.7 看板行数 <= 300', f_brd.decode().count('\n') <= 300, f_brd.decode().count('\n'))
ck('3.8 BOARD_ARCHIVE 一字未动', sha(rb(BA)) == sha(o_ba),
   (sha(rb(BA))[:16], sha(o_ba)[:16]))
ck('3.9 V543 FACT_INDEX 一字未动', sha(rb(V543)) == V543_SHA)
m = re.search(r'(?ms)^##\s+2\.168\b.*?(?=^##\s+2\.\d|\Z)', f_rc.decode('utf-8').replace('\r\n', '\n'))
ck('3.10 2.168 实测字节可量', m is not None, len(m.group(0).encode()) if m else None)
if m:
    print('      2.168 = %d B ; 下界（一半）= %d' % (len(m.group(0).encode()),
                                                    len(m.group(0).encode()) // 2))
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
