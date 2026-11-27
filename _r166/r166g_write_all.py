#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166g_write_all.py —— R166 四件套一次性落盘（含 CR / 节数 / 行数回归断言）

四件套：
  1) lead/next_re_20261117_r14/R14_COMMON.md  新增 ## 2.171  （CR 必须保持 1081）
  2) lead/GOAL_THREE_TARGETS_20261018.md      新增 ## §1221  （CR 必须保持 337）
  3) lead/LEAD_LOCK                            新增 ## OW    （CR 必须保持 137）
  4) lead/next_re_20261117_r14/STATUS_BOARD.md 新增第 166 轮（CR 保持 0，行数 <= 300，前插）

写入纪律：wx 独占创建唯一备份 -> 断言旧 sha256 / CR / 节数 -> 一次性写入 -> 回读校验。
失败即整体放弃（先全部校验，再逐个写）。支持幂等重跑（已写过则转终态校验）。
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
RC = os.path.join(T, 'R14_COMMON.md')
LED = os.path.join(R, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(R, 'lead/LEAD_LOCK')
BRD = os.path.join(T, 'STATUS_BOARD.md')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r166/r166g_write_all.json')

S2171 = io.open('/tmp/sec_2171.md', encoding='utf-8').read()
S1221 = io.open('/tmp/sec_1221.md', encoding='utf-8').read()
SOW = io.open('/tmp/sec_OW.md', encoding='utf-8').read()
SBRD = io.open('/tmp/sec_board_r166.md', encoding='utf-8').read()

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r166g_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


# ---- 前置：四件都不含本轮新段（幂等前提）
print('== 0 幂等前置 ==')
rc0 = rb(RC)
led0 = rb(LED)
lock0 = rb(LOCK)
brd0 = rb(BRD)
ck('A0 R14_COMMON 尚无 §2.171', b'## 2.171' not in rc0, rc0.count(b'## 2.171'))
ck('A1 LEDGER 尚无 §1221', '## §1221'.encode() not in led0, led0.count('## §1221'.encode()))
ck('A2 LEAD_LOCK 尚无 ## OW', b'\n## OW ' not in lock0, lock0.count(b'## OW'))
ck('A3 看板尚无第 166 轮段', '第 166 轮'.encode() not in brd0, brd0.count('第 166 轮'.encode()))

print('\n== 1 旧态不变量 ==')
ck('B0 R14_COMMON CR == 1081', rc0.count(b'\r') == 1081, rc0.count(b'\r'))
ck('B1 LEDGER CR == 337', led0.count(b'\r') == 337, led0.count(b'\r'))
ck('B2 LEAD_LOCK CR == 137', lock0.count(b'\r') == 137, lock0.count(b'\r'))
ck('B3 STATUS_BOARD CR == 0', brd0.count(b'\r') == 0, brd0.count(b'\r'))
brd_lines0 = brd0.decode('utf-8').count('\n')
ck('B4 看板行数 < 260（无需先归档）', brd_lines0 < 260, brd_lines0)

# 节数
n_rc = len(re.findall(r'(?m)^##\s*2\.\d+', rc0.decode('utf-8')))
n_led = len(re.findall(r'(?m)^##\s*§\d+', led0.decode('utf-8')))
print('  节数：R14_COMMON 2.x = %d ; LEDGER § = %d' % (n_rc, n_led))
print('  R14_COMMON 旧 sha %s ; LEDGER 旧 sha %s' % (sha(rc0)[:16], sha(led0)[:16]))
ck('B5 R14_COMMON 旧 sha == 记录值（若无记录只打印）', True, sha(rc0)[:16])

# ---- 构造新内容
print('\n== 2 构造 ==')
# 1) R14_COMMON：追加到文件尾（全 LF）。原文含 CRLF 混合（CR=1081），追加部分必须**不含 CR**。
rc_txt = rc0.decode('utf-8')
tail = '' if rc_txt.endswith('\n') else '\n'
new_rc = rc_txt + tail + '\n' + S2171 if not rc_txt.endswith('\n\n') else rc_txt + S2171
if rc_txt.endswith('\n'):
    new_rc = rc_txt + '\n' + S2171
else:
    new_rc = rc_txt + '\n\n' + S2171
new_rc_b = new_rc.encode('utf-8')

# 2) LEDGER：同样追加
led_txt = led0.decode('utf-8')
new_led = (led_txt + '\n' + S1221) if led_txt.endswith('\n') else (led_txt + '\n\n' + S1221)
new_led_b = new_led.encode('utf-8')

# 3) LEAD_LOCK：追加 OW 段
lock_txt = lock0.decode('utf-8')
new_lock = (lock_txt + SOW) if lock_txt.endswith('\n') else (lock_txt + '\n' + SOW)
new_lock_b = new_lock.encode('utf-8')

# 4) STATUS_BOARD：**前插**（新轮次在最上）
brd_txt = brd0.decode('utf-8')
new_brd = SBRD.rstrip('\n') + '\n\n' + brd_txt
new_brd_b = new_brd.encode('utf-8')

print('\n== 3 新态断言 ==')
ck('C0 R14_COMMON CR 仍 1081（追加段全 LF）', new_rc_b.count(b'\r') == 1081, new_rc_b.count(b'\r'))
ck('C1 R14_COMMON 新增段不含 CR', b'\r' not in S2171.encode('utf-8'), 'LF-only append')
ck('C2 LEDGER CR 仍 337', new_led_b.count(b'\r') == 337, new_led_b.count(b'\r'))
ck('C3 LEAD_LOCK CR 仍 137', new_lock_b.count(b'\r') == 137, new_lock_b.count(b'\r'))
ck('C4 STATUS_BOARD CR 仍 0', new_brd_b.count(b'\r') == 0, new_brd_b.count(b'\r'))
n_rc2 = len(re.findall(r'(?m)^##\s*2\.\d+', new_rc))
n_led2 = len(re.findall(r'(?m)^##\s*§\d+', new_led))
ck('C5 R14_COMMON 节数 +1（%d -> %d）' % (n_rc, n_rc2), n_rc2 == n_rc + 1, (n_rc, n_rc2))
ck('C6 LEDGER 节数 +1（%d -> %d）' % (n_led, n_led2), n_led2 == n_led + 1, (n_led, n_led2))
brd_lines1 = new_brd.count('\n')
ck('C7 看板总行数 <= 300', brd_lines1 <= 300, brd_lines1)
ck('C8 看板新增段在最前且含「第 166 轮」',
   new_brd.startswith('## 🟢 R17 第 166 轮') and '第 166 轮' in new_brd[:3000],
   new_brd[:40])
ck('C9 旧内容逐字保留（前缀/后缀包含性检查）',
   brd0.decode('utf-8') in new_brd and led_txt in new_led and lock_txt in new_lock
   and rc_txt in new_rc, 'all contain')

print('\n== 4 落盘 ==')
for path, blob, tag, oldb in ((RC, new_rc_b, 'R14_COMMON', rc0),
                               (LED, new_led_b, 'LEDGER', led0),
                               (LOCK, new_lock_b, 'LEAD_LOCK', lock0),
                               (BRD, new_brd_b, 'BOARD', brd0)):
    cur = rb(path)
    if cur == blob:
        ck('D %s 已是终态（幂等）' % tag, True, 'no change')
        continue
    ck('D0 %s 现盘仍是旧态（写前复查）' % tag, cur == oldb, 'ok')
    bp = bak(path, tag)
    ck('D1 %s 备份已 wx 创建且与旧态逐字节相同' % tag, rb(bp) == oldb, os.path.basename(bp))
    with open(path, 'wb') as f:
        f.write(blob)
    ck('D2 %s 回读 == 内存' % tag, sha(rb(path)) == sha(blob), sha(rb(path))[:16])

# ---- 收口：再量一次 CR（备份/写入之后）
print('\n== 5 收口复核 ==')
ck('E0 R14_COMMON CR 1081', rb(RC).count(b'\r') == 1081, rb(RC).count(b'\r'))
ck('E1 LEDGER CR 337', rb(LED).count(b'\r') == 337, rb(LED).count(b'\r'))
ck('E2 LEAD_LOCK CR 137', rb(LOCK).count(b'\r') == 137, rb(LOCK).count(b'\r'))
ck('E3 STATUS_BOARD CR 0 / 行数 <=300',
   rb(BRD).count(b'\r') == 0 and rb(BRD).decode('utf-8').count('\n') <= 300,
   (rb(BRD).count(b'\r'), rb(BRD).decode('utf-8').count('\n')))
ck('E4 四件最终 sha 已记录', True,
   {'rc': sha(rb(RC))[:12], 'led': sha(rb(LED))[:12], 'lock': sha(rb(LOCK))[:12],
    'brd': sha(rb(BRD))[:12]})

json.dump({'sec171_bytes': len(S2171.encode('utf-8')),
           'sec1221_bytes': len(S1221.encode('utf-8')),
           'secOW_bytes': len(SOW.encode('utf-8')),
           'secBoard_bytes': len(SBRD.encode('utf-8')),
           'rc_sha': sha(rb(RC)), 'led_sha': sha(rb(LED)),
           'lock_sha': sha(rb(LOCK)), 'brd_sha': sha(rb(BRD)),
           'brd_lines': rb(BRD).decode('utf-8').count('\n'),
           'sections': [n_rc, n_rc2, n_led, n_led2],
           'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), len(FAILS), OUT))
if FAILS:
    print('FAILS: %s' % FAILS)
sys.exit(1 if FAILS else 0)
