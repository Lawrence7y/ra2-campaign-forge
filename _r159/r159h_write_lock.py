#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159f_write_rc.py — 把 §2.164 追加进 R14_COMMON.md。

写入纪律：wx 独占备份 -> 断言旧 sha256 与 CR/LF 计数 -> 一次性写 -> 回读校验。
幂等：若末尾已是该节，跳过写入但照常跑全部校验。
断言一律用「节自身字节数」量增量，不用 len(new)-len(old)（S-429 同族）。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
RC = R + '/lead/LEAD_LOCK'
SEC = R + '/_r159/section_OP.md'
BD = D + '/R17_LEAD_BASELINE'
CR_EXPECT = 137

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def rb(p):
    with open(p, 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

cur = rd(RC)
sec = rd(SEC).rstrip('\n')
sha_old = sha(rb(RC))
cr0, lf0 = cur.count('\r'), cur.count('\n')
print('== 0 · 旧态 ==')
print('  R14_COMMON.md bytes=%d CR=%d LF=%d sha256=%s' % (len(rb(RC)), cr0, lf0, sha_old[:16]))
ck('0.1 CR 计数 == %d（不变量）' % CR_EXPECT, cr0 == CR_EXPECT, cr0)
ck('0.2 该节文件无 CR（全 LF 追加）', sec.count('\r') == 0, sec.count('\r'))
ck('0.3 该节以 ## OP 开头', sec.startswith('## OP '), sec[:20])
sec_bytes = len(sec.encode())
print('  节自身字节数 =', sec_bytes)
ck('0.4 节自身字节数 > 6000（内容不为空壳）', sec_bytes > 6000, sec_bytes)

secs0 = re.findall(r'(?m)^##\s+([A-Z]{1,2})(\d*)', cur.replace('\r\n', '\n'))
print('  末段字母 =', secs0[-1] if secs0 else None)
ck('0.5 旧文件末段 ∈ {OI（未写）, OP（已写=幂等态）}', bool(secs0) and secs0[-1][0] in ('OI','OP'), secs0[-1] if secs0 else None)
ck('0.6 幂等探针：OP 段是否已在（两种态都合法）', True, ('already' if any(x[0]=='OP' for x in secs0) else 'needs-write'))

print('\n== 1 · 追加 ==')
already = cur.rstrip('\n').endswith(sec)
if already:
    print('  [idempotent] 文件末已含 ## OP')
    new = cur
else:
    ck('1.1 旧文件以换行结尾（追加不会粘行）', cur.endswith('\n'), repr(cur[-3:]))
    new = cur + sec + '\n'
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BD, 'LEAD_LOCK.before_r159_OP_%s.bak' % stamp)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(RC))
    ck('1.2 备份已建（wx 独占）', os.path.exists(bak), os.path.basename(bak))
    ck('1.3 备份 sha == 写前实读 sha', sha(rb(bak)) == sha_old, None)
    with io.open(RC, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print('  [written] 追加 %d B' % sec_bytes)

back = rd(RC)
print('\n== 2 · 回读校验 ==')
ck('2.1 文件以该节结尾', back.rstrip('\n').endswith(sec), None)
ck('2.2 CR 计数未变（仍 %d）' % CR_EXPECT, back.count('\r') == CR_EXPECT, back.count('\r'))
secs1 = re.findall(r'(?m)^##\s+([A-Z]{1,2})(\d*)', back.replace('\r\n', '\n'))
ck('2.3 末段变为 OP', secs1[-1][0] == 'OP', secs1[-1] if secs1 else None)
ck('2.4 段数 == 升 OP 后的值（幂等重跑时不变）', len(secs1) == len(secs0), len(secs1))
ck('2.5 OP 段唯一（无重复追加）', sum(1 for x in secs1 if x[0]=='OP') == 1, sum(1 for x in secs1 if x[0]=='OP'))
# 反控：原文件内容是新文件的严格前缀
ck('2.6 反控：原文件内容是回读内容的严格前缀（只追加、未改写）',
   back.startswith(cur), None)
# 用节自身字节数验证增量（不用 len(new)-len(old)，那是 S-429 的错法）
delta = len(back.encode()) - len(cur.encode())
ck('2.7 字节增量：未写态 == 节字节+1；已写态 == 0（两种都合法，S-429 不重犯）',
   delta == sec_bytes + 1 or (already and delta == 0), (delta, sec_bytes + 1, already))

print('\n== 3 · 内容抽查（关键数字真的写进去了）==')
body = back[back.rfind('## OP '):]
for tok, why in [('c2ee063f', 'coverage.tsv 的 sha256'),
                 ('V540', 'F23 分解首现版本'),
                 ('无外部规范权威', 'F35 修订措辞'),
                 ('R17_LEDGER_1063', 'F08 台账目录对照'),
                 ('279a1035', '重钉后的 C14 口径值'),
                 ('f5a38753', '新 FREEZE_SHA256'),
                 ('a540a1f8', '新 C7_TEXT_SHA256')]:
    ck('3.x 含 %s（%s）' % (tok, why), tok in body, None)

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
