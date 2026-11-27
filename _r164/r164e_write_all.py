#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r164e_write_all.py —— R164 四件套一次性落盘（含 CR / 节数 / 行数回归断言）

四件套：
  1) lead/next_re_20261117_r14/R14_COMMON.md  新增 ## 2.169   （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md       新增 ## §1219   （CR 必须保持 337）
  3) lead/LEAD_LOCK                            新增 ## OU 段   （CR 必须保持 137）
  4) lead/next_re_20261117_r14/STATUS_BOARD.md 新增第 164 轮    （CR 必须保持 0，行数 <= 300）

写入纪律：wx 独占创建唯一备份 -> 断言旧 sha256 / CR / 节数 -> 一次性写入 -> 回读校验。
任何一步失败即整体放弃（先全部校验，再逐个写）。
支持幂等重跑（判据与时刻无关）。★ 探针纪律：已写过判定必须在读片段之前做。

额外断言（本轮新增）：
  - V543 一字未改（sha256 仍 6b00f955…）、V544 仍是本轮终值（00c4f41f… / 100,616 B）
  - facts_floors.py / gate_runner.py / FACT_INDEX_CURRENT.md 三处 pin 已同步（回归，不改它们）
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
SRC = R + '/_r164'
V543 = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
V544 = T + '/R17_R116_FACTINDEX_V544/FACT_INDEX.tsv'
FLOORS = R + '/_r160/facts_floors.py'
RUNNER = R + '/_r161/gate_runner.py'
CURMD = T + '/FACT_INDEX_CURRENT.md'

V543_SHA = '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f'
V544_SHA = '00c4f41fcba51c25828a3279542c0ab16727d994ddfcf3d2d8eda814fef764c2'
V544_BYTES = 100616

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:240]) if d else ''))
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
    out = os.path.join(BD, os.path.basename(path) + '.before_r164_%s_%s.bak' % (tag, stamp))
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
print('  R14_COMMON         %d B CR=%d' % (len(o_rc), cr(o_rc)))
print('  GOAL_THREE_TARGETS %d B CR=%d' % (len(o_led), cr(o_led)))
print('  LEAD_LOCK          %d B CR=%d' % (len(o_lock), cr(o_lock)))
print('  STATUS_BOARD       %d B CR=%d lines=%d' % (len(o_brd), cr(o_brd), o_brd.count(b'\n')))
print('  BOARD_ARCHIVE      %d B CR=%d' % (len(o_ba), cr(o_ba)))

rc_t, led_t, lock_t, brd_t = (o_rc.decode('utf-8'), o_led.decode('utf-8'),
                              o_lock.decode('utf-8'), o_brd.decode('utf-8'))
sc, sl = sec_rc(rc_t), sec_led(led_t)
# R164 自错 S-507：首版 ALREADY 只看 R14_COMMON 与台账 ⇒ 看板没写也进幂等分支、
# 终态断言假 FAIL。四件必须**同时**判，缺一即视为未写。


ck('0.1 R14_COMMON CR == 1081', cr(o_rc) == 1081, cr(o_rc))
ck('0.2 GOAL_THREE_TARGETS CR == 337', cr(o_led) == 337, cr(o_led))
ck('0.3 LEAD_LOCK CR == 137', cr(o_lock) == 137, cr(o_lock))
ck('0.4 STATUS_BOARD CR == 0', cr(o_brd) == 0, cr(o_brd))
ck('0.5 BOARD_ARCHIVE CR == 2952（本轮不动归档）', cr(o_ba) == 2952, cr(o_ba))
# 逐件幂等（R164 自错 S-508：首版用一个全局 ALREADY，一旦某件已写就误判其余三件）
RC_DONE = '## 2.169' in rc_t.replace('\r\n', '\n')
LED_DONE = '## §1219' in led_t.replace('\r\n', '\n')
LOCK_DONE = '## OU · R17 第 164 轮' in lock_t
BRD_DONE = brd_t.startswith('## 🟢 R17 第 164 轮')
print('  已完成标记: rc=%s led=%s lock=%s board=%s' % (RC_DONE, LED_DONE, LOCK_DONE, BRD_DONE))
ck('0.6a R14_COMMON 末节 ∈ {168,169}', sc[-1] in (168, 169), sc[-1])
ck('0.6b R14_COMMON 节数 = 162 + RC_DONE', len(sc) == 162 + int(RC_DONE), (len(sc), RC_DONE))
ck('0.7a 台账末节 ∈ {1218,1219}', sl[-1] in (1218, 1219), sl[-1])
ck('0.7b 台账节数 = 676 + LED_DONE', len(sl) == 676 + int(LED_DONE), (len(sl), LED_DONE))
ck('0.8 LEAD_LOCK 含 OT 段（历史）且 OU 段状态一致',
   '## OT · R17 第 163 轮' in lock_t and (('## OU · R17 第 164 轮' in lock_t) == LOCK_DONE),
   [l for l in lock_t.split('\n') if l.startswith('## ')][-1][:20])
ck('0.9 STATUS_BOARD 行数 < 260（无需归档）', o_brd.count(b'\n') < 260, o_brd.count(b'\n'))

print('== 0b · 台账与 pin 的回归断言（本轮不改它们）==')
ck('0b.1 V543 一字未改', sha(rb(V543)) == V543_SHA, sha(rb(V543))[:16])
v544 = rb(V544)
ck('0b.2 V544 = 100,616 B / 00c4f41f…', sha(v544) == V544_SHA and len(v544) == V544_BYTES,
   (len(v544), sha(v544)[:16]))
ft, rt, ct = rb(FLOORS).decode(), rb(RUNNER).decode(), rb(CURMD).decode()
ck('0b.3 facts_floors 四点已同步 V544',
   'R17_R116_FACTINDEX_V544' in ft and V544_SHA in ft and ('TOTAL_BYTES = %d' % V544_BYTES) in ft
   and "'F24': (10520, 17631)," in ft)
ck('0b.4 gate_runner LEDGER 指向 V544 且无 V543 残留', 'R17_R116_FACTINDEX_V544' in rt and 'V543' not in rt)
ck('0b.5 指针文件 sha/字节/轮次已同步',
   V544_SHA in ct and ('| 字节数 | %d |' % V544_BYTES) in ct and '| 声明轮次 | R164 |' in ct)

if fails:
    print('\n[abort] 前置断言失败')
    sys.exit(1)

print('== 1 · 读入四段新文本 ==')
new_rc = io.open(SRC + '/section_2_169.md', encoding='utf-8').read()
new_led = io.open(SRC + '/section_1219.md', encoding='utf-8').read()
new_lock = io.open(SRC + '/section_OU.md', encoding='utf-8').read()
new_brd = io.open(SRC + '/section_board_r164.md', encoding='utf-8').read()
for nm, t in (('2.169', new_rc), ('§1219', new_led), ('OU', new_lock), ('board', new_brd)):
    ck('1.1 %s 段非空且全 LF（无 CR）' % nm, len(t) > 500 and '\r' not in t, len(t))
ck('1.2 2.169 以 `## 2.169` 开头', new_rc.startswith('## 2.169'))
ck('1.3 §1219 以 `## §1219` 开头', new_led.startswith('## §1219'))
ck('1.4 OU 以 `## OU · R17 第 164 轮` 开头', new_lock.startswith('## OU · R17 第 164 轮'))
ck('1.5 看板段以 `## 🟢 R17 第 164 轮` 开头', new_brd.startswith('## 🟢 R17 第 164 轮'))
ck('1.6 四段均无未替换占位（{ } 花括号模板残留）',
   all('{0}' not in t and '%s' not in t for t in (new_rc, new_led, new_lock, new_brd)))

print('== 2 · 写入（幂等）==')
plan = []
if RC_DONE and LED_DONE and LOCK_DONE and BRD_DONE:
    print('  [idempotent] 四件套已全部写过，转终态校验')
else:
    # R14_COMMON：CRLF 混合形态，追加时沿用文件末段的分隔习惯
    rc_t_orig = rc_t
    rc_new = rc_t
    sep_rc = '\r\n' if '\r\n' in rc_t[-400:] else '\n'
    body_rc = new_rc.replace('\n', sep_rc) if sep_rc == '\r\n' else new_rc
    if not rc_t.endswith(sep_rc):
        rc_new += sep_rc
    rc_new += sep_rc + body_rc
    if not RC_DONE:
        plan.append((RC, 'R14_COMMON', rc_t, rc_new, sc, 169))
    else:
        print('  [idempotent] R14_COMMON 已写')

    sep_led = '\r\n' if '\r\n' in led_t[-400:] else '\n'
    body_led = new_led.replace('\n', sep_led) if sep_led == '\r\n' else new_led
    led_new = led_t
    if not led_t.endswith(sep_led):
        led_new += sep_led
    led_new += sep_led + body_led
    if not LED_DONE:
        plan.append((LED, 'LEDGER', led_t, led_new, sl, 1219))
    else:
        print('  [idempotent] LEDGER 已写')

    sep_lock = '\r\n' if '\r\n' in lock_t[-400:] else '\n'
    body_lock = new_lock.replace('\n', sep_lock) if sep_lock == '\r\n' else new_lock
    lock_new = lock_t
    if not lock_t.endswith(sep_lock):
        lock_new += sep_lock
    lock_new += sep_lock + body_lock
    if not LOCK_DONE:
        plan.append((LOCK, 'LEAD_LOCK', lock_t, lock_new, None, None))
    else:
        print('  [idempotent] LEAD_LOCK 已写')

    # 看板是**最新在前**（现行板首节是第 163 轮）⇒ 新段必须**前插**，不是追加。
    # R164 自错 S-506：首版照抄其余三件的「追加」写法，两次断言当场抓出（首节不是 164 轮）。
    brd_new = new_brd.rstrip('\n') + '\n\n' + brd_t
    if not BRD_DONE:
        plan.append((BRD, 'STATUS_BOARD', brd_t, brd_new, None, None))
    else:
        print('  [idempotent] STATUS_BOARD 已写')

    for path, label, old_t, new_t, secs, want in plan:
        nb = new_t.encode('utf-8')
        if label == 'R14_COMMON':
            ck('2.%s CR 保持 1081' % label, nb.count(b'\r') == 1081, nb.count(b'\r'))
            got = sec_rc(new_t)
            ck('2.%s 节数 %d → %d，末节 169' % (label, len(secs), len(got)),
               len(got) == len(secs) + 1 and got[-1] == 169, (len(secs), len(got), got[-1]))
        if label == 'LEDGER':
            ck('2.%s CR 保持 337' % label, nb.count(b'\r') == 337, nb.count(b'\r'))
            got = sec_led(new_t)
            ck('2.%s 节数 %d → %d，末节 1219' % (label, len(secs), len(got)),
               len(got) == len(secs) + 1 and got[-1] == 1219, (len(secs), len(got), got[-1]))
        if label == 'LEAD_LOCK':
            ck('2.%s CR 保持 137' % label, nb.count(b'\r') == 137, nb.count(b'\r'))
            ck('2.%s 新增 `## OU · R17 第 164 轮` 且原 OT 段仍在' % label,
               '## OU · R17 第 164 轮' in new_t and '## OT · R17 第 163 轮' in new_t)
        if label == 'STATUS_BOARD':
            ck('2.%s CR 保持 0' % label, nb.count(b'\r') == 0, nb.count(b'\r'))
            ck('2.%s 行数 %d → %d（<=300）' % (label, old_t.count('\n') + 1, new_t.count('\n') + 1),
               new_t.count('\n') + 1 <= 300, new_t.count('\n') + 1)
            ck('2.%s 新段在第 1 节且第 163 轮记录仍保留' % label,
               new_t.startswith('## 🟢 R17 第 164 轮') and '## 🟢 R17 第 163 轮' in new_t)
        if label == 'STATUS_BOARD':
            # 看板：旧文是新文的**后缀**（前插，无原地改写）
            ck('2.%s 旧文是新文的**后缀**（前插，无原地改写）' % label,
               new_t.endswith(old_t))
        else:
            ck('2.%s 旧文是新文的**前缀**（纯追加，无原地改写）' % label,
               new_t.startswith(old_t.rstrip('\r\n')) or new_t.startswith(old_t))

    for path, label, old_t, new_t, secs, want in plan:
        ck('2.9 %s 写前生产 sha 未变' % label, sha(rb(path)) == sha(old_t.encode('utf-8')))
        b = bak(path, label)
        ck('2.9b %s 备份与旧态逐字节相同' % label, rb(b) == old_t.encode('utf-8'), os.path.basename(b))
        with open(path, 'wb') as f:
            f.write(new_t.encode('utf-8'))
        ck('2.9c %s 回读逐字节相同' % label, rb(path) == new_t.encode('utf-8'))
        print('     %-13s %d -> %d B' % (label, len(old_t.encode()), len(new_t.encode())))

print('== 3 · 终态校验 ==')
f_rc, f_led, f_lock, f_brd, f_ba = rb(RC), rb(LED), rb(LOCK), rb(BRD), rb(BA)
ck('3.1 R14_COMMON CR 1081 / 末节 169 / 含 2.169', cr(f_rc) == 1081
   and sec_rc(f_rc.decode('utf-8'))[-1] == 169
   and '## 2.169 · R164' in f_rc.decode('utf-8'))
ck('3.2 台账 CR 337 / 末节 1219 / 含 §1219', cr(f_led) == 337
   and sec_led(f_led.decode('utf-8'))[-1] == 1219
   and '## §1219' in f_led.decode('utf-8'))
ck('3.3 LEAD_LOCK CR 137 / 含 OU 段', cr(f_lock) == 137
   and '## OU · R17 第 164 轮' in f_lock.decode('utf-8'))
ck('3.4 看板 CR 0 / 行数 <= 300 / 首节是 164 轮', cr(f_brd) == 0
   and f_brd.count(b'\n') <= 300
   and f_brd.decode('utf-8').startswith('## 🟢 R17 第 164 轮'))
ck('3.5 BOARD_ARCHIVE 一字未动（CR 2952）', cr(f_ba) == 2952 and sha(f_ba) == sha(o_ba))
ck('3.6 V543 一字未改 / V544 仍是终值', sha(rb(V543)) == V543_SHA
   and sha(rb(V544)) == V544_SHA)

print('\n== 结果 ==')
print('FAIL = %d' % len(fails))
if fails:
    for f in fails:
        print('  FAILED: ' + f)
    sys.exit(1)
print('[exit 0]')
sys.exit(0)
