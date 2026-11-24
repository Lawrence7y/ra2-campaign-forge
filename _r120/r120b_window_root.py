#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120b_window_root.py —— 门禁 R4 的轮次窗口表为什么只能靠「伪造轮次」通过？

R119 收口时 C11 报 ok=5。本轮 r120a 已用两个独立量证明这 5 条自述行时间上不可能
（声称 R55，产物却在 R61/R81/R84/R88 的目录里，且同一秒值跨 4 个轮次目录复用）。

本脚本回答「为什么」：recheck_verify.ROUND_WINDOWS 的键空间有多大？
若它只覆盖 36..65，则任何**诚实**的、为本轮产物写的自述行都必然 R4 FAIL，
于是「能通过」的唯一办法就是声称一个 <=65 的旧轮次 —— 门禁在结构上奖励伪造。

判据（都可失败）：
  W1 窗口表键空间 = 磁盘推导结果（不是我抄的数）
  W2 窗口表上界 65 与盘上最大轮次（从 R14_COMMON 的 ## 2.N 与 _r*/ 目录推）的差
  W3 5 条 ok 行的声称轮次全部落在窗口表内（= 它们之所以能过，靠的是旧轮次）
  W4 反控：把窗口表人为扩到 R120（不写盘，只在内存里）后，那 5 条行在 R4 上会变成什么
  W5 正控：一个「声称轮次 = 产物路径轮次」的假设行，在当前表下 R4 必 FAIL（证明诚实行不可过）
"""
import datetime
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r120', 'r120b_window_root.json')
sys.path.insert(0, R14)
import recheck_verify as V                                    # noqa: E402

checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


snap_hh, dup = V.load_main_snapshots()
keys = sorted(V.ROUND_WINDOWS)
gaps = [n for n in range(keys[0], keys[-1] + 1) if n not in set(keys)]
ck('W1 ROUND_WINDOWS 的键空间 = %d 个轮次 [%d..%d]，缺号 %s（磁盘快照推导，主快照 %d 份、重复 %d 份）'
   % (len(keys), keys[0], keys[-1], gaps, len(snap_hh), len(dup)),
   keys[0] == 36 and keys[-1] == 65 and gaps == [41, 42], {'n': len(keys), 'gaps': gaps})

# 盘上轮次：R14_COMMON 的 ## 2.N 节 + 全树的 _r<n> 目录
rc = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
secs = sorted(int(x) for x in re.findall(r'(?m)^##\s+2\.(\d+)\b', rc))
rr = sorted({int(m.group(1)) for m in re.finditer(r'(?:^|/)_r(\d+)(?:/|$)', '.')}) if False else []
dirs = sorted({int(m.group(1)) for m in (re.match(r'_r(\d+)$', d) for d in os.listdir(ROOT)) if m})
ck('W2 门禁可验证的最大轮次 = %d；盘上实际推进到的最大轮次 = %d（=_r%d/），'
   'R14_COMMON 最大节号 2.%d'
   % (keys[-1], dirs[-1], dirs[-1], secs[-1]),
   keys[-1] < dirs[-1], {'window_hi': keys[-1], 'disk_hi': dirs[-1], 'n_dirs': len(dirs)})
uncovered = [n for n in dirs if n not in V.ROUND_WINDOWS]
ck('W2b 盘上有目录但门禁无窗口的轮次 %d 个：%s ...（其中 >=66 的全部无窗口）'
   % (len(uncovered), uncovered[:12]),
   len(uncovered) > 30, {'n_uncovered': len(uncovered)})

# W3 5 条 ok 行
LINE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read().split('\n') if l][1:]
ok5 = []
for r in rows:
    if len(r) != 7 or not r[6].strip().startswith('有'):
        continue
    ap = os.path.join(ROOT, r[4].strip().replace('\\', '/'))
    if not os.path.isfile(ap):
        continue
    txt = io.open(ap, encoding='utf-8', errors='replace').read()
    for ln in txt.splitlines():
        m = LINE.match(ln)
        if m and int(m.group(1)) == int(r[0]):
            ok5.append({'id': int(r[0]), 'round': int(m.group(2)[1:]), 'at': m.group(3),
                        'path': r[4].strip()})
ck('W3 这 5 条自述行的声称轮次全部落在窗口表内（%s），故 R4 通过'
   % sorted({x['round'] for x in ok5}),
   len(ok5) == 5 and all(x['round'] in V.ROUND_WINDOWS for x in ok5), ok5)

# W4 反控：试图把窗口表扩到 R66..R120 会发生什么（内存内改，不写盘）
# 端点溯源自检 detect_widening 要求每个窗口端点**恰好**是某份磁盘快照的时刻。
# 故扩表不能只改代码：必须先在 R17_LEAD_BASELINE 里造出对应的快照文件。
saved = dict(V.ROUND_WINDOWS)
t0 = datetime.datetime(2026, 11, 24, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
for n in range(66, 121):
    V.ROUND_WINDOWS[n] = (t0 + datetime.timedelta(hours=(n - 66)), t0 + datetime.timedelta(hours=(n - 65)),
                          'synthetic', 'synthetic')
V._WIDENING_CACHE.clear()
res = {}
for x in ok5:
    row = [y for y in rows if int(y[0]) == x['id']][0]
    okv, det = V.verify_recheck_line(ROOT, row)
    res[x['id']] = {'ok': okv, 'detail': det[:110]}
V.ROUND_WINDOWS.clear()
V.ROUND_WINDOWS.update(saved)
V._WIDENING_CACHE.clear()
all_rejected = all(not v['ok'] and 'W table widened' in v['detail'] for v in res.values())
ck('W4 反控：单独把窗口表扩到 R120（不改磁盘快照）⇒ 5 条行全部被判 %s，原因是端点溯源自检 '
   '「W1 endpoint of R66 not a snapshot instant」⇒ 扩表必须同时伪造 55 份快照文件（成本已抬高）'
   % json.dumps({k: v['ok'] for k, v in res.items()}, ensure_ascii=False),
   all_rejected, {'per_id': {k: v['detail'] for k, v in res.items()}})

# W5 正控：一个「声称轮次 = 产物路径轮次（88）」的诚实行，在当前表下 R4 必 FAIL
row28 = [y for y in rows if y[0].strip() == '28'][0]
ap28 = os.path.join(ROOT, row28[4].strip().replace('\\', '/'))
import hashlib
honest_at = '2026-11-24T19:00:00+08:00'
honest = 'DISC_RECHECK discipline=28 round=R88 at=%s anchors=sha256:%s conclusion=PASS' % (
    honest_at, hashlib.sha256(row28[3].encode('utf-8')).hexdigest())
tmp = os.path.join(ROOT, '_r120', '_w5_product.tmp')
try:
    real = io.open(ap28, encoding='utf-8', errors='replace').read()
    keep = [l for l in real.splitlines() if not l.startswith('DISC_RECHECK discipline=28 ')]
    io.open(tmp, 'w', encoding='utf-8', newline='').write('\n'.join(keep) + '\n' + honest + '\n')
    r2 = list(row28)
    r2[4] = os.path.relpath(tmp, ROOT)
    okv, det = V.verify_recheck_line(ROOT, r2)
finally:
    if os.path.isfile(tmp):
        os.remove(tmp)
ck('W5 正控：为本轮产物写一条诚实行（round=R88，与产物路径轮次一致）⇒ 当前表判定 ok=%s'
   '（detail: %s）—— 若为 False，说明诚实行在结构上不可能通过' % (okv, det[:90]),
   okv is False and 'no round window' in det, {'ok': okv, 'detail': det[:160]})

json.dump({'window_keys': keys, 'n_window': len(keys), 'snap_main': len(snap_hh), 'dup': len(dup),
           'disk_rounds_hi': dirs[-1], 'n_dirs': len(dirs), 'uncovered': uncovered,
           'ok5': ok5, 'w4_after_extend': res, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
