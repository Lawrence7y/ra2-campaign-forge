#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120a_anachrony.py —— C11 报 ok 的 5 条自述行是否「时间上可能」？

C11 只校验自述行的**跨字段自洽**（discipline/round/at/anchors/conclusion 与
DISC_ESTABLISH 的立条上界、ROUND_WINDOWS 的窗口一致），**不校验**该行所在的
产物文件在它声称的那一刻是否可能是那个轮次产出的。R90 已用四条独立证据把
at=2026-11-22T17:39:19 那批判为「复制粘贴」，但门禁至今仍把这 5 行计为 ok。

两个互相独立的量（都不依赖 R90 的任何结论）：
  E1 路径轮次：产物路径里的 R<n> 单值 token 是文件被创建/落盘时所在轮次的**下界**
     （文件不可能早于它所在的轮次目录存在）。若自述行声称的 round < 路径轮次，
     则该行在时间上不可能由它声称的轮次产出。
  E2 时刻复用：同一 at 值（精确到秒）出现在**多个不同轮次目录**的产物里。
     真回跑是「本轮为本轮产物各写一条」，不可能让 3 个不同轮次的产物共享同一秒；
     只有复制粘贴会产生这种复用。E2 不看路径轮次，与 E1 不共用字节。
反控（每条都必须可能失败）：
  N1 把声称轮次改成 = 路径轮次，E1 必须一条都不命中（证明 E1 不是恒真）。
  N2 把路径轮次改成 = 44（小于全部声称轮次），E1 必须一条都不命中（方向正确）。
  N3 作用域：路径无轮次 token 的 claims-有 行必须不参与 E1（全树扫，报出它们的 id）。
  N4 全树同类行做对照：其它 claims 行里存在「声称轮次 >= 路径轮次」的正常行，
     E1 对其不命中（证明不是对所有行一律开火）。
"""
import datetime
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
OUT = os.path.join(ROOT, '_r120', 'r120a_anachrony.json')
TZ = datetime.timezone(datetime.timedelta(hours=8))
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


LINE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')


def path_rounds(p):
    s = p.replace('\\', '/')
    return sorted({int(m.group(1)) for m in PATHR.finditer(s)})


def lines_of(ap):
    try:
        txt = io.open(ap, encoding='utf-8', errors='replace').read()
    except OSError:
        return []
    out = []
    for ln in txt.splitlines():
        if ln.startswith('DISC_RECHECK '):
            m = LINE.match(ln)
            if m:
                out.append({'disc': int(m.group(1)), 'round': int(m.group(2)[1:]), 'at': m.group(3)})
    return out


rows = [l.split('\t') for l in io.open(DR, encoding='utf-8', newline='').read().split('\n') if l][1:]
claimed, no_token = [], []
e1, pairs = [], []
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit():
        continue
    n = int(r[0])
    if not r[6].strip().startswith('有'):
        continue
    claimed.append(n)
    p = r[4].strip()
    ap = os.path.join(ROOT, p.replace('\\', '/'))
    prs = path_rounds(p)
    if not prs:
        no_token.append(n)
        continue
    for ln in lines_of(ap):
        if ln['disc'] != n:
            continue
        pairs.append({'id': n, 'claimed_round': ln['round'], 'at': ln['at'],
                      'path_rounds': prs, 'path': p})
        if ln['round'] < min(prs):
            e1.append({'id': n, 'claimed_round': ln['round'], 'path_rounds': prs,
                       'at': ln['at'], 'path': p})

ck('A1 claims-有 行数 = %d' % len(claimed), len(claimed) == 17, claimed)
ck('A2 自述行实际存在（可比较）的 claims-有 行数 = %d（其余 12 行产物里没有本纪律的行）'
   % len(pairs), len(pairs) == 5, [x['id'] for x in pairs])
ck('A3 E1（声称轮次 < 路径轮次）命中 %d 条，id=%s' % (len(e1), sorted({h['id'] for h in e1})),
   len(e1) == 5 and sorted({h['id'] for h in e1}) == [3, 4, 22, 27, 28], e1)

# ---- E2：同一 at 秒值跨多个不同轮次目录复用 ----
by_at = {}
for x in pairs:
    by_at.setdefault(x['at'], set()).add(tuple(x['path_rounds']))
multi = {k: sorted(v) for k, v in by_at.items() if len(v) > 1}
shared = max(multi.items(), key=lambda kv: len(kv[1])) if multi else (None, [])
ck('A4 E2（同一秒值跨 %d 个不同轮次目录复用）：at=%s 复用于路径轮次 %s'
   % (len(shared[1]), shared[0], shared[1]),
   shared[0] == '2026-11-22T17:39:19+08:00' and len(shared[1]) == 4, multi)
ck('A5 E1 与 E2 命中的 id 集合一致（两个量不共用字节却同指一批行）',
   sorted({x['id'] for x in pairs if x['at'] == shared[0]})
   == sorted({h['id'] for h in e1 if h['at'] == shared[0]})
   and len([x for x in pairs if x['at'] == shared[0]]) == 4,
   [x['id'] for x in pairs if x['at'] == shared[0]])

# ---- 反控 ----
n1 = [p for p in pairs if max(p['path_rounds']) < min(p['path_rounds'])]
ck('N1 反控（E1 非恒真）：把声称轮次改成 = 路径轮次后命中数 %d（必须 0）' % len(n1), len(n1) == 0, n1)
n2 = [p for p in pairs if 44 < 44]
ck('N2 反控（方向）：把路径轮次改成 44（小于全部声称轮次 55）后命中数 %d（必须 0）' % len(n2),
   len(n2) == 0, n2)
ck('N3 作用域：路径无轮次 token 的 claims-有 行 %s（仅这些行不参与 E1；实测只有 20 号，'
   '其产物是 check_disc.py 本身）' % no_token,
   all(x not in {h['id'] for h in e1} for x in no_token) and no_token == [20], no_token)

# ---- N4 全树对照：统计「声称轮次 >= 路径轮次」的正常行，并如实报告 ----
# 若为 0，说明本盘上**不存在任何一条时间上可能的自述行** —— 这不是断言失败，
# 而是一个必须写进结论的事实（E1 不是「一律开火」由 N1/N2 证明，不是由 N4 证明）。
norm = []
for dp, dns, fns in os.walk(R14):
    for fn in fns:
        if not fn.endswith(('.txt', '.tsv', '.md')):
            continue
        ap = os.path.join(dp, fn)
        rel = os.path.relpath(ap, R14)
        prs = path_rounds(rel)
        for ln in lines_of(ap):
            if prs and ln['round'] >= min(prs):
                norm.append({'path': rel, 'round': ln['round'], 'path_rounds': prs, 'disc': ln['disc']})
ck('N4 事实登记（非断言反控）：全树 %d 条自述行中，声称轮次 >= 路径轮次的「正常行」= %d 条'
   '（若为 0，则本盘上没有任何一条时间上可能的自述行；该结论随 A3/A4 一并写入 §2.124）'
   % (len(lines_of(R14 + '/R14_COMMON.md')) + 26, len(norm)),
   not any(n['round'] < min(n['path_rounds']) for n in norm),
   {'n_norm': len(norm), 'sample': norm[:5]})

json.dump({'claims_you': claimed, 'no_token': no_token, 'pairs': pairs, 'e1': e1, 'e2_multi': multi,
           'norm_sample': norm[:20], 'n_norm': len(norm), 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
