# -*- coding: utf-8 -*-
"""R129h：C17 钉住的五条「时间上不可能」自述行，逐条复核并给出裁定所需的三个量。

C17 现在只做「钉住集合不变」，不裁这五行该改、该撤还是该降级。裁定要三个量：
  量一 路径轮次下界：产物路径里的 R<n> token 最大值（= 该产物最早可能的轮次）。
  量二 声称轮次：自述行里的 round=Rnn。
  量三 外部时钟：该轮次的窗口（由 R17_LEAD_BASELINE 快照推导），以及声称轮次是否在窗口内。
本脚本不裁，只把三个量摆齐，并核 C17 的钉住集合与实测集合是否一致。
"""
import sys, os, json, re, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import ROOT
import io

R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
sys.path.insert(0, R14)
import recheck_verify as v

OUT = os.path.join(ROOT, '_r129', 'r129h_five_rows.json')
rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n') if l][1:]
LINERE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

REC = []
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit(): continue
    if not r[6].strip().startswith('有'): continue
    p = r[4].strip()
    prs = sorted(set(int(m.group(1)) for m in PATHR.finditer(p.replace('\\', '/'))))
    if not prs: continue
    ap = os.path.join(ROOT, p.replace('\\', '/'))
    if not os.path.isfile(ap): continue
    for l in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
        m = LINERE.match(l)
        if not m or int(m.group(1)) != int(r[0]): continue
        rn = int(m.group(2)[1:])
        REC.append({'id': int(r[0]), 'claimed_round': rn, 'at': m.group(3),
                    'path_min_round': min(prs), 'path_rounds': prs, 'path': p})
add('H0 参与复核的自述行数', True, len(REC))
IMP = sorted((x for x in REC if x['claimed_round'] < x['path_min_round']),
             key=lambda x: x['id'])
add('H1 时间上不可能的行 = 声称轮次早于产物路径轮次下界，共 %d 条' % len(IMP),
    len(IMP) == 5, [x['id'] for x in IMP])
PIN = {3: (55, '2026-11-22T17:39:19+08:00'), 4: (55, '2026-11-22T17:40:02+08:00'),
       22: (55, '2026-11-22T17:39:19+08:00'), 27: (55, '2026-11-22T17:39:19+08:00'),
       28: (55, '2026-11-22T17:39:19+08:00')}
add('H2 与 C17_PIN 逐条一致（id / 声称轮次 / at）',
    {(x['id'], x['claimed_round'], x['at']) for x in IMP} ==
    {(k, a, b) for k, (a, b) in PIN.items()},
    [(x['id'], x['claimed_round'], x['at']) for x in IMP])

# 量三：窗口
for x in IMP:
    w = v.ROUND_WINDOWS.get(x['claimed_round'])
    x['claimed_window'] = (w[0].isoformat(), w[1].isoformat()) if w else None
    x['claimed_in_window'] = bool(w and w[0] <= v._hhmmss(x['at'][11:13] + x['at'][14:16] + x['at'][17:19]) < w[1])
add('H3 五条声称轮次 R55 的窗口存在（R54/R55 快照都在盘上）',
    all(x['claimed_window'] for x in IMP), [x['claimed_window'] for x in IMP])
add('H4 五条的 at 都落在 R55 窗口内 —— 即「跨字段自洽」这一层 C11 无法分辨真假',
    all(x['claimed_in_window'] for x in IMP), [(x['id'], x['claimed_in_window']) for x in IMP])
add('H5 五条的产物路径轮次分别是 61/81/84/88，均 > 55，故「R55 产出」在这些路径上不可能',
    all(x['path_min_round'] > x['claimed_round'] for x in IMP),
    {x['id']: x['path_min_round'] for x in IMP})

# 复用秒值
atmap = {}
for x in REC:
    atmap.setdefault(x['at'], set()).add(tuple(x['path_rounds']))
reuse = {k: len(s) for k, s in atmap.items() if len(s) > 1}
add('H6 同一 at 秒值出现在多个不同轮次目录的样品（复制粘贴特征）',
    reuse == {'2026-11-22T17:39:19+08:00': 4}, reuse)
add('H7 那 4 条复用行正好也是五条不可能行里的四条（3/22/27/28），第 4 条（id=4）的 at 不同',
    sorted(x['id'] for x in IMP if x['at'] == '2026-11-22T17:39:19+08:00') == [3, 22, 27, 28],
    [x['id'] for x in IMP if x['at'] == '2026-11-22T17:39:19+08:00'])

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck), 'impossible': IMP, 'reuse': reuse},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
for x in IMP:
    print('  id=%-3d claimed R%-3d path>=R%-3d at=%s' % (x['id'], x['claimed_round'], x['path_min_round'], x['at']))
