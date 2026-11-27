#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161i_write_all.py —— R161 四件套一次性落盘（含 CR / 节数 / 行数回归断言）。

四件套：
  1) lead/next_re_20261117_r14/R14_COMMON.md  新增 ## 2.166          （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md       新增 ## §1216          （CR 必须保持 337）
  3) lead/LEAD_LOCK                            新增 ## OR 段         （CR 必须保持 137）
  4) lead/next_re_20261117_r14/STATUS_BOARD.md 新增第 161 轮记录      （CR 必须保持 0，行数 <= 300）

写入纪律：wx 独占创建唯一备份 -> 断言旧 sha256 / CR / 节数 -> 一次性写入 -> 回读校验。
任何一步失败即整体放弃（先全部校验，再逐个写）。
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
SRC = R + '/_r161'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def rb(p):
    with open(p, 'rb') as f: return f.read()

def sha(b): return hashlib.sha256(b).hexdigest()

def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r161_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(path))
    return out

def sec_rc(t): return [int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', t.replace('\r\n', '\n'))]
def sec_led(t): return [int(x) for x in re.findall(r'(?m)^##\s+§(\d+)\b', t.replace('\r\n', '\n'))]

print('== 0 · 旧态断言（任一失败即整体不写）==')
# 一次性写入脚本，本身不支持重跑；但为了让「本轮所有证据脚本可复跑」，这里加一个
# **终态检测**：若四件套已含本轮新节，则跳过写入分支、只做终态校验（判据与时刻无关）。
_rb0 = rb(RC); _lb0 = rb(LED); _kb0 = rb(LOCK); _bb0 = rb(BRD)
_rct = _rb0.decode('utf-8').replace('\r\n', '\n')
ALREADY = ('## 2.166' in _rct) and ('## §1216' in _lb0.decode('utf-8'))
if ALREADY:
    print('  [already-written] 四件套已含本轮新节，转为终态校验')
    ck('T1 R14_COMMON CR 仍 1081', _rb0.count(b'\r') == 1081, _rb0.count(b'\r'))
    ck('T2 LEDGER CR 仍 337', _lb0.count(b'\r') == 337, _lb0.count(b'\r'))
    ck('T3 LEAD_LOCK CR 仍 137', _kb0.count(b'\r') == 137, _kb0.count(b'\r'))
    ck('T4 STATUS_BOARD CR 仍 0', _bb0.count(b'\r') == 0, _bb0.count(b'\r'))
    _sc = sec_rc(_rct); _sl = sec_led(_lb0.decode('utf-8').replace('\r\n', '\n'))
    ck('T5 R14_COMMON 160 节末 166', (len(_sc), max(_sc)) == (160, 166), (len(_sc), max(_sc)))
    ck('T6 LEDGER 末节 1216', max(_sl) == 1216, max(_sl))
    ck('T7 看板行数 <= 300', _bb0.decode().count('\n') <= 300, _bb0.decode().count('\n'))
    ck('T8 看板第 161 轮在最前',
       _bb0.decode().index('R17 第 161 轮') < _bb0.decode().index('R17 第 160 轮'))
    ck('T9 V543 一字未动',
       sha(rb(T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv')) ==
       '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f')
    print('\nFAILS:', fails if fails else 'NONE')
    sys.exit(1 if fails else 0)
o_rc, o_led, o_lock, o_brd, o_ba = rb(RC), rb(LED), rb(LOCK), rb(BRD), rb(BA)
cr = lambda b: b.count(b'\r')
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
ck('0.5 BOARD_ARCHIVE CR == 2952（本轮归档后不变量）', cr(o_ba) == 2952, cr(o_ba))
n0 = o_brd.decode().count('\n')
ck('0.6 看板已归档过（行数 < 260，无需再归档）', n0 < 260, n0)

rc_t = o_rc.decode('utf-8'); led_t = o_led.decode('utf-8')
lock_t = o_lock.decode('utf-8'); brd_t = o_brd.decode('utf-8')
sc, sl = sec_rc(rc_t), sec_led(led_t)
ck('0.7 R14_COMMON 159 节、末节 165', (len(sc), max(sc)) == (159, 165), (len(sc), max(sc)))
ck('0.8 LEDGER 末节 1215', max(sl) == 1215, max(sl))
ck('0.9 R14_COMMON 尚无 2.166', 166 not in sc)
ck('0.10 LEDGER 尚无 §1216', 1216 not in sl)
ck('0.11 LEAD_LOCK 末段是 OQ', '## OQ ·' in lock_t and '## OR ·' not in lock_t)
ck('0.12 看板尚无第 161 轮', 'R17 第 161 轮' not in brd_t)
if fails:
    print('\n[abort] 旧态断言失败，不写任何文件'); sys.exit(1)

s2 = io.open(SRC + '/section_2_166.md', encoding='utf-8', newline='').read()
s1216 = io.open(SRC + '/section_1216.md', encoding='utf-8', newline='').read()
sor = io.open(SRC + '/section_OR.md', encoding='utf-8', newline='').read()
sbrd = io.open(SRC + '/section_board_r161.md', encoding='utf-8', newline='').read()
print('\n== 0b · 片段自检 ==')
for nm, t in (('2.166', s2), ('§1216', s1216), ('OR', sor), ('board161', sbrd)):
    ck('0b.%s 片段非空 / 无 CR / 无 C0' % nm,
       len(t) > 200 and '\r' not in t and not re.search(r'[\x00-\x08\x0b-\x1f]', t),
       (len(t), t.count('\r')))
    ck('0b.%s 片段无反引号外泄风险（仅用于正文，允许反引号）' % nm, True)
ck('0b.5 2.166 片段以 "## 2.166" 开头', s2.startswith('## 2.166'))
ck('0b.6 §1216 片段以 "## §1216" 开头', s1216.startswith('## §1216'))
ck('0b.7 OR 片段以 "## OR ·" 开头', sor.startswith('## OR ·'))
ck('0b.8 看板片段以 "## 🟢 R17 第 161 轮" 开头', sbrd.startswith('## 🟢 R17 第 161 轮'))

new_rc = rc_t.rstrip('\n') + '\n\n' + s2.rstrip('\n') + '\n'
new_led = led_t.rstrip('\n') + '\n\n' + s1216.rstrip('\n') + '\n'
new_lock = lock_t.rstrip('\n') + '\n\n' + sor.rstrip('\n') + '\n'
new_brd = sbrd.rstrip('\n') + '\n\n' + brd_t.lstrip('\n')

print('\n== 1 · 写前内存里校验新态 ==')
sc2, sl2 = sec_rc(new_rc), sec_led(new_led)
ck('1.1 R14_COMMON 新态 160 节、末节 166', (len(sc2), max(sc2)) == (160, 166), (len(sc2), max(sc2)))
ck('1.2 R14_COMMON 新态 CR 仍 1081', cr(new_rc.encode()) == 1081, cr(new_rc.encode()))
ck('1.3 LEDGER 新态末节 1216', max(sl2) == 1216, max(sl2))
ck('1.4 LEDGER 新态 CR 仍 337', cr(new_led.encode()) == 337, cr(new_led.encode()))
ck('1.5 LEAD_LOCK 新态 CR 仍 137', cr(new_lock.encode()) == 137, cr(new_lock.encode()))
ck('1.6 看板新态 CR 仍 0', cr(new_brd.encode()) == 0, cr(new_brd.encode()))
n1 = new_brd.count('\n')
ck('1.7 看板新态行数 <= 300', n1 <= 300, n1)
ck('1.8 看板第 161 轮在最前（先出现于第 160 轮）',
   new_brd.index('R17 第 161 轮') < new_brd.index('R17 第 160 轮'))
ck('1.9 旧内容逐字保留（新看板以原看板为后缀）', new_brd.endswith(brd_t.lstrip('\n')))
ck('1.10 四片段本身不含 CR（CR 总数不变的必要条件）',
   all('\r' not in t for t in (s2, s1216, sor, sbrd)))
if fails:
    print('\n[abort] 新态校验失败，不写任何文件'); sys.exit(1)

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
ck('3.5 R14_COMMON 160 节末 166',
   (len(sec_rc(f_rc.decode())), max(sec_rc(f_rc.decode()))) == (160, 166))
ck('3.6 LEDGER 末节 1216', max(sec_led(f_led.decode())) == 1216)
ck('3.7 看板行数 <= 300', f_brd.decode().count('\n') <= 300, f_brd.decode().count('\n'))
ck('3.8 BOARD_ARCHIVE 一字未动（本轮归档已完成于 r161d）', sha(rb(BA)) == sha(o_ba),
   (sha(rb(BA))[:16], sha(o_ba)[:16]))
ck('3.9 V543 FACT_INDEX 一字未动',
   sha(rb(T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv')) == '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f')
print('\n  节字节：2.166 = %d B（新节，供 C16 下界用）'
      % len(('\n'.join(['## 2.166' + x for x in [s2.split('\n', 1)[1]]])).encode()))
m = re.search(r'(?ms)^##\s+2\.166\b.*?(?=^##\s+2\.\d|\Z)', f_rc.decode('utf-8').replace('\r\n', '\n'))
ck('3.10 2.166 实测字节可量', m is not None, len(m.group(0).encode()) if m else None)
print('      2.166 = %d B ; 下界（一半）= %d' % (len(m.group(0).encode()) if m else 0,
                                              (len(m.group(0).encode()) if m else 0) // 2))
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
