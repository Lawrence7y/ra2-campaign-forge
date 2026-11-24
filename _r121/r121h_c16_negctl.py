#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121h_c16_negctl.py -- 补验 C16 的 N2 反控（floor 抬到实测字节之上 ⇒ 必须 hollowed out）。

为什么单独一个脚本：
  r121g 的 N2 初版把 floor 写成 new_floor+1（=2019），仍远小于实测 8073，
  所以门禁当然 exit 0 —— 反控本身失效（自错 S-95）。而 r121g 已经不可重跑
  （GATE_VER 已是 R121，重跑会在 S4 处按设计失败）。故把这条反控独立出来。

做法：备份 -> 在临时副本上改 floor 与 sha -> 跑门禁 -> 断言 hollowed out -> 恢复 -> 复跑断言 exit 0。
全程 try/finally，保证崩溃时门禁一定回到原样。
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
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def run_gate():
    p = subprocess.run([sys.executable, 'check_disc.py'], cwd=BASE,
                       capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


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


src = open(GATE, encoding='utf-8').read()
raw = src.encode('utf-8')
old_sha = hashlib.sha256(raw).hexdigest()

ck('P0 前置：GATE_VER 已是 R121，且 125 已钉进表',
   "GATE_VER = 'R121'" in src and re.search(r'\b125:\s*\d+', src) is not None,
   {'sha': old_sha[:16]})

m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
floors = {int(k): int(v) for k, v in re.findall(r'(\d+):\s*(\d+)', m.group(1))}
sizes = section_bytes(os.path.join(BASE, 'R14_COMMON.md'))
B125, F125 = sizes[125], floors[125]
ck('P1 实测 §2.125 = %d 字节，钉值 %d（= 字节//4），两者都 > 400' % (B125, F125),
   B125 > 400 and F125 == B125 // 4, {'bytes': B125, 'floor': F125})

stamp = time.strftime('%Y%m%d_%H%M%S')
bpath = os.path.join(BASE, 'R17_LEAD_BASELINE', 'SUPERSEDED.before_r121h_negctl_%s.bak' % stamp)
with open(bpath, 'xb') as f:
    f.write(raw)
ck('P2 门禁已 wx 排他备份', os.path.isfile(bpath), {'backup': os.path.basename(bpath)})

over = B125 + 1
norm = '\n'.join('%d:%d' % (k, over if k == 125 else floors[k]) for k in sorted(floors))
sha2 = hashlib.sha256(norm.encode('utf-8')).hexdigest()

try:
    broken = src.replace('125: %d' % F125, '125: %d' % over, 1)
    broken = broken.replace("C16_FLOORS_SHA256 = '%s'"
                            % re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src).group(1),
                            "C16_FLOORS_SHA256 = '%s'" % sha2, 1)
    ck('N2a 构造体确实同时改了 floor（抬到 %d > 实测 %d）与 sha' % (over, B125),
       broken != src and ('125: %d' % over) in broken, {'over': over, 'sha2': sha2[:16]})
    open(GATE, 'w', encoding='utf-8', newline='\n').write(broken)
    rc2, out2 = run_gate()
    ck('N2 反控 floor 抬到实测字节之上且 sha 同步 ⇒ 门禁报 C16 hollowed out 且 exit 非 0',
       rc2 != 0 and 'hollowed out' in out2, {'rc': rc2})
finally:
    open(GATE, 'w', encoding='utf-8', newline='\n').write(src)

back = open(GATE, 'rb').read()
ck('R1 finally 恢复后 sha 与原始一致', hashlib.sha256(back).hexdigest() == old_sha,
   {'sha': hashlib.sha256(back).hexdigest()[:16]})
rc3, out3 = run_gate()
ck('R2 恢复后门禁 exit 0', rc3 == 0, {'rc': rc3})
ck('R3 恢复后 unpinned 0 且 GATE_VER = R121',
   'unpinned 0' in out3 and 'check_disc.py (R121)' in out3,
   {'line': [l for l in out3.split('\n') if 'per-section floors' in l][:1]})

outp = '/home/t628/projects/ra2-campaign-forge/_r121/r121h_c16_negctl.json'
open(outp, 'w', encoding='utf-8').write(json.dumps(
    dict(checks=checks, bytes125=B125, floor125=F125, over=over,
         gate_sha=hashlib.sha256(back).hexdigest()), ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), outp))
sys.exit(0 if npass == len(checks) else 1)
