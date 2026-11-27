#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-h · 把「十二 · 门禁 R164 → R165」增量补进已落盘的四件套，并同步 C16 下界

背景（S-526）：四件套已在 r165f 落盘，之后我又做了门禁升级（r165g），
按纪律「落盘后再改门禁必须补写该节」——R164 就是这么做的（它的「十二节」是后写的）。
本脚本只做三件事：
  1) 把四段源文件里新增的尾部（从「**十二 · 门禁 R164 → R165」起）追加到盘上对应段落末尾
  2) 同步把断言数 201 -> 246 / 六脚本 -> 七脚本 的措辞改正
  3) 按 §2.170 的**新**字节重钉 C16 下界 170 与 C16_FLOORS_SHA256（下界 = 字节一半）
每一步都带「改前/改后」双断言与幂等。
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
GATE = os.path.join(T, 'check_disc.py')
COMMON = os.path.join(T, 'R14_COMMON.md')
LEDGER = os.path.join(R, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(R, 'lead/LEAD_LOCK')
BOARD = os.path.join(T, 'STATUS_BOARD.md')
OUT = os.path.join(R, '_r165/r165h_append_gate_section.json')

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
    out = os.path.join(BD, os.path.basename(path) + '.before_r165h_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


MARK = '**十二 · 门禁 R164 → R165'
SRC = {
    'R14_COMMON': (COMMON, os.path.join(R, '_r165/section_2_170.md'), 1081),
    'LEDGER': (LEDGER, os.path.join(R, '_r165/section_1220.md'), 337),
    'LEAD_LOCK': (LOCK, os.path.join(R, '_r165/section_OV.md'), 137),
    'STATUS_BOARD': (BOARD, os.path.join(R, '_r165/section_board_r165.md'), 0),
}

print('== 1 · 从源文件取「十二节」增量（源文件是唯一权威）==')
delta = {}
for k, (dst, src, cr) in SRC.items():
    s = io.open(src, encoding='utf-8').read()
    ck('%s 源文件含十二节段头' % k, MARK in s, s.count(MARK))
    tail = s[s.index(MARK):]
    ck('%s 增量段无 CR' % k, tail.count('\r') == 0)
    delta[k] = tail
    print('   %-14s 增量 %d B' % (k, len(tail.encode())))

print()
print('== 2 · 盘上四件套：补断言数措辞 + 追加十二节 ==')
for k, (dst, src, cr) in SRC.items():
    raw = rb(dst)
    txt = raw.decode('utf-8')
    old_sha = sha(raw)
    ck('%s CR 未变基线 %d' % (k, cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    if MARK in txt:
        ck('%s 幂等：十二节已在盘上' % k, True)
        continue
    # 2a 先在**该段的范围内**改正断言数措辞（不动别的段）
    anchor = {'R14_COMMON': '\n## 2.170 · R165：', 'LEDGER': '\n## §1220\n',
              'LEAD_LOCK': '\n## OV · R17 第 165 轮', 'STATUS_BOARD': '## \U0001f7e2 R17 第 165 轮'}[k]
    i = txt.index(anchor)
    head, seg = txt[:i], txt[i:]
    # 段内措辞升到 246 / 七脚本（与源文件一致），这是**本轮同一段的措辞更新**，不是历史改写
    seg = (seg.replace('**合计 201 断言 0 FAIL**', '**合计 246 断言 0 FAIL**')
              .replace('六脚本 **201 断言 0 FAIL**', '七脚本 **246 断言 0 FAIL**')
              .replace('`r165f`（**31**，四件套写入 + 幂等两次）',
                       '`r165f`（**31**，四件套写入 + 幂等两次）/ `r165g`（**45**，门禁 R164→R165 + 沙箱双负控）')
              .replace('`r165f`(31)，**合计 201 断言',
                       '`r165f`(31)/`r165g`(45)，**合计 246 断言'))
    # S-528：段内断言数措辞可能是 201（首跑）或 246（源文件已更新），两态都算前置合格
    ck('%s 段内已含断言数措辞（201 或 246 两态）' % k,
       ('201 断言' in seg) or ('246 断言' in seg),
       (seg.count('201 断言'), seg.count('246 断言')))
    newtxt = head + seg.rstrip('\n') + '\n' + delta[k]
    b = bak(dst, k)
    ck('%s 备份 wx 独占' % k, os.path.isfile(b), os.path.basename(b))
    ck('%s 备份逐字节等于原文' % k, sha(rb(b)) == old_sha)
    with open(dst, 'wb') as f:
        f.write(newtxt.encode('utf-8'))
    back = rb(dst)
    ck('%s 回读 CR 未变（== %d）' % (k, cr), back.count(b'\r') == cr, back.count(b'\r'))
    ck('%s 回读含十二节恰 1 次' % k, back.decode('utf-8').count(MARK) == 1,
       back.decode('utf-8').count(MARK))
    # S-527：正确的前缀口径是「段之前的字节逐字节不变」，段内允许改措辞（201->246），段尾只允许追加
    ck('%s 回读：段之前的前缀逐字节不变' % k, back[:i] == raw[:i])
    ck('%s 回读：文件以新增量结尾（只追加不覆盖）' % k,
       back.decode('utf-8').rstrip('\n').endswith(delta[k].rstrip('\n')))

print()
print('== 3 · §2.170 新字节 + C16 下界同步 ==')
cm = io.open(COMMON, encoding='utf-8').read()
i = cm.index('\n## 2.170 · R165：')
SEC = len(cm[i + 1:].encode())
FLOOR = SEC // 2
print('   §2.170 现字节 %d，下界应为 %d' % (SEC, FLOOR))
gt = io.open(GATE, encoding='utf-8').read()
bi = gt.index('C16_FLOORS = {')
bj = gt.index('\n}', bi)
blk = gt[bi:bj + 2]
floors = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', blk, re.M)]
ck('3.1 表 164 节且 170 在表内', len(floors) == 164 and 170 in dict(floors), len(floors))
cur = dict(floors)[170]
ck('3.2 当前下界 %d 与「现字节一半 %d」的关系（脱钩则需重钉）' % (cur, FLOOR), True, (cur, FLOOR))
if cur != FLOOR:
    nb = re.sub(r'^    170: \d+,$', '    170: %d,' % FLOOR, blk, flags=re.M)
    nf = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', nb, re.M)]
    ck('3.3 重钉后仍 164 节、前 163 条不变', len(nf) == 164 and nf[:163] == floors[:163], len(nf))
    nsha = sha('\n'.join('%d:%d' % (k2, v) for k2, v in sorted(nf)).encode())
    g2 = gt[:bi] + nb + gt[bj + 2:]
    g2 = re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'", "C16_FLOORS_SHA256 = '%s'" % nsha,
                g2, count=1, flags=re.M)
    ck('3.4 只替换表块与 C16 指纹两处', g2.count("C16_FLOORS_SHA256 = '%s'" % nsha) == 1)
    g2 = re.sub(r'^    170: \d+,$', '    170: %d,' % FLOOR, g2, count=0, flags=re.M) \
        if g2.count('    170: %d,' % FLOOR) == 0 else g2
    ck('3.5 终态里 170 恰出现 1 次（防 S-524 双写）', g2.count('    170: ') == 1, g2.count('    170: '))
    if sha(rb(GATE)) != sha(g2.encode()):
        b = bak(GATE, 'c16')
        ck('3.6 备份 wx 独占', os.path.isfile(b), os.path.basename(b))
        with open(GATE, 'wb') as f:
            f.write(g2.encode())
        ck('3.7 已写盘', sha(rb(GATE)) == sha(g2.encode()), sha(rb(GATE))[:16])
    else:
        ck('3.7 幂等', True)
else:
    ck('3.3 下界已等于现字节一半，无需重钉', True)

print()
print('== 4 · 终态校验 ==')
gt = io.open(GATE, encoding='utf-8').read()
bi = gt.index('C16_FLOORS = {')
bj = gt.index('\n}', bi)
fl = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', gt[bi:bj + 2], re.M)]
nsha = sha('\n'.join('%d:%d' % (k2, v) for k2, v in sorted(fl)).encode())
ck('4.1 表 164 节', len(fl) == 164, len(fl))
ck('4.2 170 下界 == §2.170 现字节一半', dict(fl)[170] == SEC // 2, (dict(fl)[170], SEC // 2))
ck('4.3 注册的 C16 指纹 == 重算', re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt, re.M).group(1) == nsha,
   nsha[:16])
for k, (dst, src, cr) in SRC.items():
    raw = rb(dst)
    ck('4.4 %s CR == %d' % (k, cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    ck('4.5 %s 十二节恰 1 次' % k, raw.decode('utf-8').count(MARK) == 1)

res = {'sec_170_bytes': SEC, 'floor_170': SEC // 2, 'c16_sha': nsha,
       'FAILS': len(FAILS), 'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('SEC_170_BYTES=%d FLOOR=%d C16_SHA=%s' % (SEC, SEC // 2, nsha))
print('FAILS=%d' % len(FAILS))
for f_ in FAILS:
    print('   -', f_)
sys.exit(1 if FAILS else 0)
