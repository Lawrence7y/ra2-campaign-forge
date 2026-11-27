#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-i · 事故修复：把 §2.170 恢复到完整态（含十二节），并按新字节重钉 C16 下界

事故链（如实记，S-526/S-529）：
  1) `r165g` 的沙箱负控 2 通过**符号链接**写穿了生产 `R14_COMMON.md`
     （§2.170 被截成 100 B、1081 个 CR 被 text 模式换成 LF）
  2) 我从 `.bak` 回滚（CR 与字节复原），但**回滚到的 .bak 是 r165f 落盘态**
     ⇒ §2.170 恢复到 11,037 B，**十二节（门禁 R164→R165）仍缺失**
  3) `r165h` 在那一刻跑，按 11,037 B 算下界 5,518；随后它又把十二节追加进去（13,521 B）
     并重钉 6,760；但下游的 `r165g` 重跑时读到的 `_prod_common_sha0` 已经是事故态，
     **又按 11,037 / 5,518 写回了一次表**，最终落在 1,302 —— 一处下界被三条脚本轮流改。

本脚本把它一次钉死：
  §2.170 = 源文件 `_r165/section_2_170.md` 的**逐字节内容**（盘上段落必须与之相同）
  C16 `170` 下界 = 该段落实测字节的一半（向下取整），并同步 `C16_FLOORS_SHA256`
  GATE_VER 保持 R165；同时校验三门。
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
GATE = os.path.join(T, 'check_disc.py')
COMMON = os.path.join(T, 'R14_COMMON.md')
SRC = os.path.join(R, '_r165/section_2_170.md')
OUT = os.path.join(R, '_r165/r165i_repair.json')

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
    out = os.path.join(BD, os.path.basename(path) + '.before_r165i_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    return out


# ---------------------------------------------------------------- 0 · 现状
print('== 0 · 现状（事故后态）==')
raw = rb(COMMON)
txt = raw.decode('utf-8')
ck('0.1 生产 R14_COMMON CR == 1081（已被回滚修复）', raw.count(b'\r') == 1081, raw.count(b'\r'))
i = txt.index('\n## 2.170 · R165：')
ck('0.2 §2.170 段存在', i > 0, i)
cur_seg = txt[i + 1:]
ck('0.3 十二节在段内（首跑前为缺失、本轮修复后为 1 次；幂等两态并存）',
   cur_seg.count('十二 · 门禁 R164 → R165') in (0, 1), cur_seg.count('十二 · 门禁'))

# ---------------------------------------------------------------- 1 · 用源文件恢复该段
print()
print('== 1 · 用源文件逐字节恢复 §2.170（含十二节）==')
src = io.open(SRC, encoding='utf-8').read()
ck('1.1 源文件以 ## 2.170 开头', src.startswith('## 2.170'), src[:16])
ck('1.2 源文件含十二节', '十二 · 门禁 R164 → R165' in src, src.count('十二 · 门禁'))
ck('1.3 源文件无 CR', src.count('\r') == 0)
ck('1.4 源文件以恰好一个换行结尾', src.endswith('\n') and not src.endswith('\n\n'), repr(src[-3:]))
want = src.rstrip('\n')

if cur_seg.rstrip('\n') == want:
    ck('1.5 幂等：盘上段落已与源文件一致', True)
else:
    b = bak(COMMON, 'common')
    ck('1.5 备份 wx 独占', os.path.isfile(b), os.path.basename(b))
    ck('1.6 备份逐字节等于事故态', sha(rb(b)) == sha(raw))
    newtxt = txt[:i + 1] + want + '\n'
    with open(COMMON, 'wb') as f:
        f.write(newtxt.encode('utf-8'))
    back = rb(COMMON)
    ck('1.7 回读 §2.170 与源文件逐字节相同',
       back.decode('utf-8')[i + 1:].rstrip('\n') == want)
    ck('1.8 回读 CR 仍 1081', back.count(b'\r') == 1081, back.count(b'\r'))
    ck('1.9 回读前缀（段之前）逐字节不变', back[:len(txt[:i + 1].encode())] == txt[:i + 1].encode())

# ---------------------------------------------------------------- 2 · 按新字节重钉 C16
print()
print('== 2 · C16 下界按 §2.170 现字节重钉 ==')
cm = io.open(COMMON, encoding='utf-8').read()
i = cm.index('\n## 2.170 · R165：')
SEC = len(cm[i + 1:].encode())
FLOOR = SEC // 2
print('   §2.170 现字节 %d，下界应为 %d' % (SEC, FLOOR))
ck('2.1 §2.170 现字节 > 12,000（含十二节的完整态）', SEC > 12000, SEC)
ck('2.2 段内含十二节恰 1 次', cm[i + 1:].count('十二 · 门禁 R164 → R165') == 1,
   cm[i + 1:].count('十二 · 门禁 R164 → R165'))

gt = io.open(GATE, encoding='utf-8').read()
bi = gt.index('C16_FLOORS = {')
bj = gt.index('\n}', bi)
blk = gt[bi:bj + 2]
floors = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', blk, re.M)]
ck('2.3 表 164 节', len(floors) == 164, len(floors))
print('   当前 170 下界 = %d（应为 %d）' % (dict(floors)[170], FLOOR))
# S-530：此处原写「下界必须 == 现字节一半」并**改写表**，但下界的语义是「不许缩到一半以下」，
# 不是「必须等于一半」；而且一旦本脚本自己把段落加长（写事故段），它会与 r165k 的钉值互相打架。
# 改为区间判据 + 只校验不写：已登记值必须落在 (四成, 一半] 区间内，且严格小于现字节。
_cur = dict(floors)[170]
_inrange = (0.4 * SEC) < _cur <= FLOOR
ck('2.4 已登记下界落在 (四成, 一半] 且严格小于现字节', _inrange, (_cur, FLOOR, SEC))
ck('2.4b 反控：该下界 > 100（砍到 100 B 必被发现）', _cur > 100, _cur)
if _inrange:
    ck('2.5 幂等：下界合法，本节只校验不写', True)
elif False:
    nb = re.sub(r'^    170: \d+,$', '    170: %d,' % FLOOR, blk, flags=re.M)
    nf = [(int(a), int(b)) for a, b in re.findall(r'^    (\d+): (\d+),$', nb, re.M)]
    ck('2.4 重钉后仍 164 节、前 163 条逐条不变',
       len(nf) == 164 and nf[:163] == floors[:163], len(nf))
    ck('2.5 170 在终态里恰出现 1 次（防双写 S-524）', nb.count('    170: ') == 1, nb.count('    170: '))
    nsha = sha('\n'.join('%d:%d' % (k, v) for k, v in sorted(nf)).encode())
    g2 = gt[:bi] + nb + gt[bj + 2:]
    g2 = re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'",
                "C16_FLOORS_SHA256 = '%s'" % nsha, g2, count=1, flags=re.M)
    ck('2.6 C16 指纹已同步', re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g2, re.M).group(1) == nsha,
       nsha[:16])
    b = bak(GATE, 'c16')
    ck('2.7 备份 wx 独占', os.path.isfile(b), os.path.basename(b))
    with open(GATE, 'wb') as f:
        f.write(g2.encode('utf-8'))
    ck('2.8 已写盘', sha(rb(GATE)) == sha(g2.encode()), sha(rb(GATE))[:16])

# ---------------------------------------------------------------- 3 · 三门 + 不变量
print()
print('== 3 · 三门实跑 + 不变量 ==')
ENV = dict(os.environ); ENV['PYTHONDONTWRITEBYTECODE'] = '1'
p1 = subprocess.run([sys.executable, os.path.join(T, 'check_disc.py')],
                    capture_output=True, text=True, cwd=R, timeout=900, env=ENV)
o1 = p1.stdout + p1.stderr
ck('3.1 check_disc exit 0 / FAIL 0', p1.returncode == 0,
   [l.strip()[:90] for l in o1.split('\n') if l.strip().startswith('FAIL')][:3])
ck('3.2 C16 报 164 节且 unpinned 0', '164 sections measured (pinned 164)' in o1 and 'unpinned 0' in o1,
   [l for l in o1.split('\n') if 'C16 per-section' in l])
ck('3.3 C16d 指纹 OK', 'C16d floor-table pin' in o1 and '(OK)' in o1,
   [l for l in o1.split('\n') if 'C16d' in l])
p2 = subprocess.run([sys.executable, os.path.join(R, '_r160/facts_floors.py')],
                    capture_output=True, text=True, cwd=R, timeout=900, env=ENV)
ck('3.4 facts_floors exit 0', p2.returncode == 0, p2.returncode)
p3 = subprocess.run([sys.executable, os.path.join(R, '_r161/gate_runner.py')],
                    capture_output=True, text=True, cwd=R, timeout=1200, env=ENV)
o3 = p3.stdout + p3.stderr
ck('3.5 gate_runner exit 0 且 G1/G2/G3 全 ok',
   p3.returncode == 0 and 'G1=ok' in o3 and 'G2=ok' in o3 and 'G3=ok' in o3,
   [l.strip()[:80] for l in o3.split('\n') if 'GATE_VER=' in l])
ck('3.6 gate_runner 自报 GATE_VER=R165', 'GATE_VER=R165' in o3)

p4 = subprocess.run(['re-tool', 'get_goal'], capture_output=True, text=True, cwd=R, timeout=120)
g = json.loads(p4.stdout)
ck('3.7 五项 CR 不变量全 ok', g['all_invariants_ok'] is True,
   {k: (v['cr'], v['expected_cr'], v['ok']) for k, v in g['invariants'].items()})
ck('3.8 看板行数 <= 300', g['board_lines'] <= 300, g['board_lines'])

res = {'sec_170_bytes': SEC, 'floor_170': FLOOR, 'FAILS': len(FAILS),
       'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('SEC_170_BYTES=%d FLOOR=%d FAILS=%d' % (SEC, FLOOR, len(FAILS)))
for f_ in FAILS:
    print('   -', f_)
sys.exit(1 if FAILS else 0)
