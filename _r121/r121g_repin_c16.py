#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121g_repin_c16.py -- 按 C16b/C16d 的设计重钉 C16_FLOORS 与 C16_FLOORS_SHA256，并升 GATE_VER。

为什么必须重钉（不是绕过）：
  R121 正常新增 R14_COMMON 的 §2.125 后，门禁报 unpinned 1。
  C16b 的设计就是：表外新节数超过上限时必须由 Lead 显式把新节钉进 C16_FLOORS。
  C16d 的设计是：改任一条 floor 必须同时改 sha 常量，否则 TAMPERED。

本脚本做什么：
  1) 从盘上 R14_COMMON.md 实测 §2.125 的字节数 B。
  2) floor = max(400, B // 2)，与该门禁历史上的「建表时实测字节的一半」口径一致。
     （R119 的 2.123 是 9421 -> 2355，即 9421//4 不是，实测是 2355 = 9421//4 不对，
       2355*4=9420，所以历史口径是 //4。本脚本先实测历史口径再套用，不猜。）
  3) 把 125:floor 插进 C16_FLOORS（保持升序），重算规范化串 sha256，写回常量。
  4) GATE_VER 'R120' -> 'R121'，并同步 DISC_RECHECK.tsv 第 20 行的自述 grep。

反控：
  N1 只改 floor 不改 sha ⇒ 门禁必须报 C16d TAMPERED（实测跑一次）。
  N2 floor 写大 1 ⇒ 实测 C16 必须报 hollowed out（实测跑一次）。
  N3 恢复正确值后门禁必须 exit 0 且 unpinned 0。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
TSV = os.path.join(BASE, 'DISC_RECHECK.tsv')
COMMON = os.path.join(BASE, 'R14_COMMON.md')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def section_bytes(path):
    rc = open(path, encoding='utf-8', errors='replace').read()
    cur, buf, out = None, [], {}
    for l in rc.split('\n'):
        m = re.match(r'^##\s+2\.(\d+)\b', l)
        if m:
            if cur is not None:
                out[cur] = len('\n'.join(buf).encode('utf-8'))
            cur, buf = int(m.group(1)), [l]
        elif cur is not None:
            buf.append(l)
    if cur is not None:
        out[cur] = len('\n'.join(buf).encode('utf-8'))
    return out


def run_gate():
    p = subprocess.run([sys.executable, 'check_disc.py'], cwd=BASE,
                       capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


# ---- 1) 实测历史口径：floor = 建表时字节 // 4（用台账里记录过的两次建表字节验证）----
src = open(GATE, encoding='utf-8').read()
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
floors = {int(k): int(v) for k, v in re.findall(r'(\d+):\s*(\d+)', m.group(1))}
sizes = section_bytes(COMMON)

# 台账里两次重钉记录过的「建表时字节」与「钉值」；口径若真是 //4，两对都必须精确相等。
RECORDED = [(9421, 2355, '2.123 @R119'), (9325, 2331, '2.124 @R120')]
hist = [(b, f, b // 4, b // 4 == f, tag) for b, f, tag in RECORDED]
ck('S1 实测历史 floor 口径（建表字节, 钉值, //4, 是否精确相等, 出处）= %s'
   % json.dumps([[a, b, c, d, e] for a, b, c, d, e in hist], ensure_ascii=False),
   all(h[3] for h in hist), {'hist': [[a, b, c, d, e] for a, b, c, d, e in hist]})
ck('S1b 两次历史重钉都精确等于 字节//4 ⇒ 口径唯一',
   all(h[3] for h in hist) and len({h[2] for h in hist}) == 2, {'n': len(hist)})

B125 = sizes.get(125)
new_floor = B125 // 4 if B125 else None
ck('S3 §2.125 实测字节 = %s，按 字节//4 口径推出的 floor = %s' % (B125, new_floor),
   B125 is not None and new_floor is not None and new_floor > 400,
   {'bytes': B125, 'floor': new_floor})
div = [4]

# ---- 2) 写盘前断言 ----
old_gate = open(GATE, 'rb').read()
old_sha = hashlib.sha256(old_gate).hexdigest()
ck('S4 门禁未被并发修改（GATE_VER 仍为 R120）', "GATE_VER = 'R120'" in src,
   {'sha': old_sha[:16]})

stamp = time.strftime('%Y%m%d_%H%M%S')
bpath = os.path.join(BASE, 'R17_LEAD_BASELINE', 'SUPERSEDED.before_r121g_gate_%s.bak' % stamp)
with open(bpath, 'xb') as f:
    f.write(old_gate)
with open(os.path.join(BASE, 'R17_LEAD_BASELINE', 'SUPERSEDED.before_r121g_tsv_%s.bak' % stamp), 'xb') as f:
    f.write(open(TSV, 'rb').read())
ck('S5 门禁与 TSV 均 wx 排他备份', os.path.isfile(bpath), {'backup': os.path.basename(bpath)})

# ---- 3) 插入 floor 并重算 sha ----
new_floors = dict(floors)
new_floors[125] = new_floor
norm = '\n'.join('%d:%d' % (k, new_floors[k]) for k in sorted(new_floors))
new_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()


def render_floors(d):
    items = ['%d: %d' % (k, d[k]) for k in sorted(d)]
    lines, cur = [], '    '
    for it in items:
        piece = it + ', '
        if len(cur) + len(piece) > 98:
            lines.append(cur.rstrip())
            cur = '    '
        cur += piece
    lines.append(cur.rstrip().rstrip(','))
    return 'C16_FLOORS = {\n' + '\n'.join(lines) + '\n}'


new_src = re.sub(r'C16_FLOORS = \{.*?\n\}', lambda _m: render_floors(new_floors), src, count=1, flags=re.S)
new_src = re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'",
                 "C16_FLOORS_SHA256 = '%s'" % new_sha, new_src, count=1)
new_src = new_src.replace("GATE_VER = 'R120'", "GATE_VER = 'R121'", 1)

open(GATE, 'w', encoding='utf-8', newline='\n').write(new_src)

# TSV 同步
tsv = open(TSV, encoding='utf-8').read()
tsv2 = tsv.replace("grep=(?m)^GATE_VER = 'R120'", "grep=(?m)^GATE_VER = 'R121'")
ck('S7 TSV 自述行 GATE_VER 已同步', tsv2 != tsv, {'changed': tsv2 != tsv})
open(TSV, 'w', encoding='utf-8', newline='\n').write(tsv2)

# ---- 4) 反控 N1/N2 与恢复：用 try/finally 保证崩溃时门禁一定回到正确状态 ----
cur = open(GATE, encoding='utf-8').read()
try:
    broken = cur.replace("125: %d" % new_floor, "125: %d" % (new_floor + 1), 1)
    ck('N0 反控 构造的 broken 确实改了 floor', broken != cur, {'n': new_floor + 1})
    open(GATE, 'w', encoding='utf-8', newline='\n').write(broken)
    rc1, out1 = run_gate()
    ck('N1 反控 改 floor 不改 sha ⇒ 门禁报 C16d TAMPERED 且 exit 非 0',
       rc1 != 0 and 'C16d floor table TAMPERED' in out1, {'rc': rc1})

    # N2 必须把 floor 抬到**实测字节之上**才会触发 hollowed out；
    # 初版写成 floor+1（仍远小于 8073）⇒ 门禁 exit 0，反控自身失效（本轮自错 S-95）。
    over = B125 + 1
    norm2 = '\n'.join('%d:%d' % (k, over if k == 125 else new_floors[k])
                      for k in sorted(new_floors))
    sha2 = hashlib.sha256(norm2.encode('utf-8')).hexdigest()
    broken2 = cur.replace("125: %d" % new_floor, "125: %d" % over, 1)
    broken2 = broken2.replace("C16_FLOORS_SHA256 = '%s'" % new_sha,
                              "C16_FLOORS_SHA256 = '%s'" % sha2, 1)
    ck('N2a 反控 构造的 broken2 确实同时改了 floor 与 sha（floor 抬到实测字节之上）',
       sha2 != new_sha and broken2 != cur and over > B125,
       {'over': over, 'bytes': B125, 'sha2': sha2[:16]})
    open(GATE, 'w', encoding='utf-8', newline='\n').write(broken2)
    rc2, out2 = run_gate()
    ck('N2 反控 floor 抬到实测字节之上且 sha 同步 ⇒ 门禁报 C16 hollowed out 且 exit 非 0',
       rc2 != 0 and 'hollowed out' in out2, {'rc': rc2})
finally:
    open(GATE, 'w', encoding='utf-8', newline='\n').write(cur)
    ck('S7b finally 已把门禁恢复为正确版本',
       open(GATE, encoding='utf-8').read() == cur,
       {'sha': hashlib.sha256(open(GATE, 'rb').read()).hexdigest()[:16]})

# ---- 6) 恢复正确值并终检 ----
open(GATE, 'w', encoding='utf-8', newline='\n').write(cur)
rc3, out3 = run_gate()
ck('S8 恢复正确值后门禁 exit 0', rc3 == 0, {'rc': rc3})
ck('S9 门禁报 unpinned 0', 'unpinned 0' in out3,
   {'line': [l for l in out3.split('\n') if 'per-section floors' in l][:1]})
ck('S10 门禁报 GATE_VER = R121', 'check_disc.py (R121)' in out3, {})
ck('S11 门禁报 pinned 119', 'pinned 119' in out3,
   {'line': [l for l in out3.split('\n') if 'per-section floors' in l][:1]})

final = open(GATE, 'rb').read()
ck('S12 终态 sha 与写入内容一致',
   hashlib.sha256(final).hexdigest() == hashlib.sha256(cur.encode('utf-8')).hexdigest(),
   {'sha': hashlib.sha256(final).hexdigest()[:16]})

outp = '/home/t628/projects/ra2-campaign-forge/_r121/r121g_repin_c16.json'
open(outp, 'w', encoding='utf-8').write(json.dumps(
    dict(checks=checks, b125=B125, new_floor=new_floor, divisor=div[0],
         old_sha=old_sha, new_sha=new_sha, backup=os.path.basename(bpath),
         gate_sha=hashlib.sha256(final).hexdigest()), ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), outp))
sys.exit(0 if npass == len(checks) else 1)
