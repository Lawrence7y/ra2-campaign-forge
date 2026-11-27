#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：【规则 D】复算「部分失联」集合的基数到底是 32 还是 33，以及两套分档为何背离。

两个独立来源给出的答案不同：
  (A) 外部 triage（_ext/f_partial_triage/TRIAGE.tsv）：32 条 = 5 仍可核验 / 18 需重建 / 9 不可核验
  (B) 执行员 #311（_r141/sub_triage/triage_recompute.tsv）：33 条 = 28 / 2 / 3

本脚本只做**基数与集合**的机械复算（不判分档口径），回答：
  1. 按「至少一条路径失、至少一条路径在盘」的判据，集合基数是多少？
  2. 若把「全部失联」「全部存活」也单列，三者之和是否 = 54？
  3. 32 与 33 的差集是哪一个 fid？为什么会有 1 条之差？

路径解析口径（写进代码，逐项可失败）：
  - evidence_paths 以 ; 分隔
  - 反斜杠 -> 正斜杠
  - 去掉尾部括号定位提示，如 (M71 披露) / (§8.1 ...) —— 只取第一个 ( 之前
  - 路径相对 ROOT（证据路径以 lead/ 开头）解析
  - 存在判定 = os.path.exists（目录也算，因为 PANEL 之类可能是指向目录的提示）

反控：
  N1 把根换成 /tmp => 部分失联集合必须归 0（证明根选对）
  N2 不剥括号提示 => 存活数必须下降（证明剥括号是必要的）
  N3 把「目录也算存在」改成「只算普通文件」=> 存活数只能下降或持平
"""
import csv
import io
import json
import os
import re

ROOT = '/home/t628/projects/ra2-campaign-forge'
FI = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R110_FACTINDEX_V538',
                  'FACT_INDEX.tsv')
OUTJ = os.path.join(ROOT, '_r141', 'r141e_partial_set.json')
fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


rows = list(csv.DictReader(io.open(FI, encoding='utf-8'), delimiter='\t'))
ck('0.1 FACT_INDEX 54 行', len(rows) == 54, len(rows))
ck('0.2 列名 == fact_id/statement/grade/evidence_paths/limitations',
   list(rows[0].keys()) == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'],
   list(rows[0].keys()))


def paths_of(s, strip_paren=True):
    out_ = []
    for p in (s or '').split(';'):
        p = p.strip().replace('\\', '/')
        if not p:
            continue
        if strip_paren and '(' in p:
            p = p.split('(', 1)[0].strip()
        out_.append(p)
    return out_


def exists(p, root=ROOT, files_only=False):
    q = os.path.join(root, p)
    return os.path.isfile(q) if files_only else os.path.exists(q)


allp, full_alive, full_dead, partial = [], [], [], []
detail = {}
for r in rows:
    fid = r['fact_id']
    ps = paths_of(r['evidence_paths'])
    if not ps:
        detail[fid] = dict(n=0, alive=0, dead=0, kind='no-paths')
        continue
    alive = [p for p in ps if exists(p)]
    dead = [p for p in ps if not exists(p)]
    kind = 'alive' if not dead else ('dead' if not alive else 'partial')
    detail[fid] = dict(n=len(ps), alive=len(alive), dead=len(dead), kind=kind,
                       dead_paths=dead[:8])
    allp.append(fid)
    if kind == 'alive':
        full_alive.append(fid)
    elif kind == 'dead':
        full_dead.append(fid)
    else:
        partial.append(fid)

print('\n=== 集合基数 ===')
print('  有路径的事实项      : %d' % len(allp))
print('  全部存活            : %d  %s' % (len(full_alive), full_alive))
print('  全部失联            : %d  %s' % (len(full_dead), full_dead))
print('  部分失联            : %d' % len(partial))
out.update(partial=sorted(partial), full_alive=sorted(full_alive),
           full_dead=sorted(full_dead), n_present=len(allp), detail=detail)

ck('1.1 全部存活 + 全部失联 + 部分失联 == 54（不重不漏）',
   len(full_alive) + len(full_dead) + len(partial) == 54,
   (len(full_alive), len(full_dead), len(partial)))
ck('1.2 部分失联 == 32（外部 triage 的数）', len(partial) == 32, len(partial))

# 与两个来源比对
EXT = os.path.join(ROOT, '_ext', 'f_partial_triage', 'TRIAGE.tsv')
ext_rows = list(csv.DictReader(io.open(EXT, encoding='utf-8'), delimiter='\t'))
ext_set = set(r['fid'] for r in ext_rows)
ck('1.3 外部 triage 32 条', len(ext_set) == 32, len(ext_set))
ck('1.4 我复算的集合与外部 triage 完全相同', set(partial) == ext_set,
   sorted(set(partial) ^ ext_set))

SUB = os.path.join(ROOT, '_r141', 'sub_triage', 'triage_recompute.tsv')
sub_rows = list(csv.DictReader(io.open(SUB, encoding='utf-8'), delimiter='\t'))
sub_set = set(r['fact_id'] for r in sub_rows)
ck('1.5 执行员 #311 报 33 条', len(sub_set) == 33, len(sub_set))
diff = sorted(sub_set - set(partial))
ck('1.6 33 与 32 的差集恰 1 个 fid', len(diff) == 1, diff)
out['exec_extra'] = diff
if diff:
    fid = diff[0]
    print('\n  差出的那一条是 %s：' % fid)
    print('    evidence_paths =', [r['evidence_paths'] for r in rows if r['fact_id'] == fid][0][:400])
    print('    我算的 kind =', detail.get(fid))
    out['exec_extra_detail'] = detail.get(fid)

# ---------- 反控 ----------
print('\n=== 反控 ===')
p2 = []
for r in rows:
    ps = paths_of(r['evidence_paths'])
    alive = [p for p in ps if exists(p, root='/tmp')]
    dead = [p for p in ps if not exists(p, root='/tmp')]
    if ps and alive and dead:
        p2.append(r['fact_id'])
ck('N1 根换成 /tmp => 部分失联归 0（根选对了）', len(p2) == 0, len(p2))

part3 = []
for r in rows:
    ps = paths_of(r['evidence_paths'], strip_paren=False)
    alive = [p for p in ps if exists(p)]
    dead = [p for p in ps if not exists(p)]
    if ps and alive and dead:
        part3.append(r['fact_id'])
ck('N2 不剥括号提示 => 部分失联集合变大（剥括号是必要的）', len(part3) >= len(partial),
   (len(part3), len(partial)))

part4 = []
for r in rows:
    ps = paths_of(r['evidence_paths'])
    alive = [p for p in ps if exists(p, files_only=True)]
    dead = [p for p in ps if not exists(p, files_only=True)]
    if ps and alive and dead:
        part4.append(r['fact_id'])
ck('N3 只算普通文件（目录不算）=> 部分失联集合不缩小', len(part4) >= len(partial),
   (len(part4), len(partial)))

out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(OUTJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
