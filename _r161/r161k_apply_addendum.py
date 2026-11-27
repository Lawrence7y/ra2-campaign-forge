#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161k_apply_addendum.py —— 把门禁升级那一节追加进四件套的对应段尾（纯后缀追加）。

为什么分两步：门禁升级必须在正文落盘**之后**才能做（2.166 的字节数要先实测出来才能算 C16 下界），
所以 2.166/§1216/OR/看板第 161 轮的正文里，升级那一节只能后补。
本脚本只做三件事：备份 -> 在目标段**末尾**追加 -> 回读 + CR/节数/行数复验。
反控：追加后目标段字节必须恰好增加 addendum 的字节数（不是覆盖、不是插入中间）。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
BD = T + '/R17_LEAD_BASELINE'
SRC = R + '/_r161'
TARGETS = [
    (T + '/R14_COMMON.md', r'(?ms)^##\s+2\.166\b.*?(?=^##\s+2\.\d|\Z)', SRC + '/addendum_2_166.md', '2.166'),
    (R + '/lead/GOAL_THREE_TARGETS_20261018.md', r'(?ms)^##\s+§1216\b.*?(?=^##\s+§\d|\Z)', SRC + '/addendum_1216.md', '§1216'),
    (R + '/lead/LEAD_LOCK', r'(?ms)^##\s+OR ·.*?(?=^##\s+[A-Z]{2} ·|\Z)', SRC + '/addendum_OR.md', 'OR'),
    (T + '/STATUS_BOARD.md', r'(?ms)^##\s+🟢 R17 第 161 轮\b.*?(?=^##\s|\Z)', SRC + '/addendum_board.md', 'board161'),
]

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def rb(p):
    with open(p, 'rb') as f: return f.read()
def sha(b): return hashlib.sha256(b).hexdigest()

def state():
    return {p: rb(p) for p, _, _, _ in TARGETS}

print('== 0 · 旧态不变量 ==')
st0 = state()
for p, pat, add, tag in TARGETS:
    b = st0[p]
    txt = b.decode('utf-8').replace('\r\n', '\n')
    m = re.search(pat, txt)
    ck('0.%s 能定位目标段' % tag, m is not None)
    add_t = io.open(add, encoding='utf-8', newline='').read()
    # 幂等：若该段已含 addendum 的首个特征句，则跳过
    already = add_t.strip().split('\n')[0].strip()[:30] in (m.group(0) if m else '')
    print('     %-8s 段字节=%d 追加片段=%d B 已追加=%s'
          % (tag, len(m.group(0).encode()) if m else 0, len(add_t.encode()), already))
ck('0.5 四份台账 CR 不变量（追加前）',
   st0[T + '/R14_COMMON.md'].count(b'\r') == 1081
   and st0[R + '/lead/GOAL_THREE_TARGETS_20261018.md'].count(b'\r') == 337
   and st0[R + '/lead/LEAD_LOCK'].count(b'\r') == 137
   and st0[T + '/STATUS_BOARD.md'].count(b'\r') == 0,
   (st0[T + '/R14_COMMON.md'].count(b'\r'), st0[R + '/lead/GOAL_THREE_TARGETS_20261018.md'].count(b'\r'),
    st0[R + '/lead/LEAD_LOCK'].count(b'\r'), st0[T + '/STATUS_BOARD.md'].count(b'\r')))

print('\n== 1 · 逐个追加（备份 -> 追加 -> 回读）==')
new_state = {}
for p, pat, add, tag in TARGETS:
    b0 = st0[p]
    txt = b0.decode('utf-8').replace('\r\n', '\n')
    # 注意：不能整体 replace 回 CRLF —— 那会改 CR 总数。改为在**字节层**定位插入点。
    add_t = io.open(add, encoding='utf-8', newline='').read()
    m = re.search(pat, txt)
    if not m:
        ck('1.%s 定位失败' % tag, False); continue
    head = add_t.strip().split('\n')[0].strip()[:30]
    if head in m.group(0):
        print('     %-8s 幂等：段内已含追加片段首句，跳过' % tag)
        new_state[p] = b0
        continue
    # 段在原始字节里的结束位置 = 段文本长度按 utf-8 映射（CRLF 归一化会改变长度 ⇒ 用逐行计数定位）
    seg_txt = m.group(0)
    # 在**原字节**里找到段首的字节偏移
    seg_first_line = seg_txt.split('\n')[0]
    idx = b0.find(seg_first_line.encode('utf-8'))
    ck('1.%s 段首在字节层可定位' % tag, idx >= 0, idx)
    # 段末 = 段首 + 段内容（原字节里段内可能带 CRLF；用「下一段首行」或文件尾来界定）
    nxt = re.search(r'(?m)^##\s', txt[m.end():])
    if nxt:
        nxt_line = txt[m.end():].split('\n')[0]
        b_idx = b0.find(nxt_line.encode('utf-8'), idx + len(seg_first_line.encode('utf-8')))
    else:
        b_idx = len(b0)
    ck('1.%s 段末字节位置找到' % tag, b_idx > idx, (idx, b_idx))
    seg_bytes = b0[idx:b_idx]
    # 追加点：段末（去掉尾部空白行后）+ addendum
    tail = seg_bytes.rstrip(b'\r\n')
    b1 = b0[:idx] + tail + add_t.encode('utf-8') + b0[idx + len(tail):]
    # 反控：新文件 = 旧文件在追加点插入，其余字节不变
    ck('1.%s 追加是纯插入（旧字节全保留）' % tag,
       b1.startswith(b0[:idx] + tail) and b1.endswith(b0[idx + len(tail):]),
       (len(b0), len(b1)))
    ck('1.%s 字节增量 == 追加片段字节数' % tag,
       len(b1) - len(b0) == len(add_t.encode()), (len(b1) - len(b0), len(add_t.encode())))
    ck('1.%s 追加片段不含 CR（CR 总数不变的必要条件）' % tag, b'\r' not in add_t.encode())
    # 备份（wx）
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bp = os.path.join(BD, os.path.basename(p) + '.before_r161_add_%s_%s.bak' % (tag.replace('§', 'S'), stamp))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(b0)
    ck('1.%s 备份与旧态逐字节相同' % tag, rb(bp) == b0, os.path.basename(bp))
    with open(p, 'wb') as f:
        f.write(b1)
    ck('1.%s 回读一致' % tag, rb(p) == b1)
    new_state[p] = b1
    print('     %-8s %d -> %d B (+%d)' % (tag, len(b0), len(b1), len(b1) - len(b0)))

print('\n== 2 · 写后不变量 ==')
n_rc = new_state[T + '/R14_COMMON.md'].count(b'\r')
n_led = new_state[R + '/lead/GOAL_THREE_TARGETS_20261018.md'].count(b'\r')
n_lock = new_state[R + '/lead/LEAD_LOCK'].count(b'\r')
n_brd = new_state[T + '/STATUS_BOARD.md'].count(b'\r')
ck('2.1 R14_COMMON CR 仍 1081', n_rc == 1081, n_rc)
ck('2.2 LEDGER CR 仍 337', n_led == 337, n_led)
ck('2.3 LEAD_LOCK CR 仍 137', n_lock == 137, n_lock)
ck('2.4 STATUS_BOARD CR 仍 0', n_brd == 0, n_brd)
ntxt = new_state[T + '/STATUS_BOARD.md'].decode('utf-8').replace('\r\n', '\n')
ck('2.5 看板行数 <= 300', ntxt.count('\n') <= 300, ntxt.count('\n'))
rc_t = new_state[T + '/R14_COMMON.md'].decode('utf-8').replace('\r\n', '\n')
ck('2.6 R14_COMMON 仍 160 节、末节 166',
   (len(re.findall(r'(?m)^##\s+2\.\d+', rc_t)), max(int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)', rc_t))) == (160, 166))
led_t = new_state[R + '/lead/GOAL_THREE_TARGETS_20261018.md'].decode('utf-8').replace('\r\n', '\n')
ck('2.7 LEDGER 末节仍 1216', max(int(x) for x in re.findall(r'(?m)^##\s+§(\d+)', led_t)) == 1216)
lock_t = new_state[R + '/lead/LEAD_LOCK'].decode('utf-8').replace('\r\n', '\n')
ck('2.8 LEAD_LOCK 段数不变（OR 只有一段）', lock_t.count('\n## OR ·') == 1, lock_t.count('\n## OR ·'))
print('\n  新 2.166 段字节 = %d' % len(re.search(r'(?ms)^##\s+2\.166\b.*?(?=^##\s+2\.\d|\Z)', rc_t).group(0).encode()))
print('  新看板行数 = %d' % ntxt.count('\n'))
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
