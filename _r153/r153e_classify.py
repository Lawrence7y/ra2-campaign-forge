#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 E：把「事项级未命中」分成三种性质，并核 F23 语料依赖件的「曾在册」数值。

分类（这是本轮的关键区分，不做区分会把「statement 跨事项」误当成「锚点写错」）：
  P1 该 token 在**被点名事项块**内      -> 命中
  P2 该 token 在同节**其它事项块**内     -> statement 跨事项（锚点指向的块只是承载之一）
  P3 该 token 在同节**任何位置都没有**   -> 锚点确实指错块（本项才是「锚点粒度错」）
  P4 token 是全表通用的结构词（如节号 1062、数字 107）-> 无鉴别力，单独剔除后再判

F23：台账/看板写的「R41_RECOMPUTE 三目录均不存在」是事实，但漏了「曾存在」。
     11-22 快照清单里三件的字节数与 mtime 可机械读出，本轮把它们钉成可比对的值。
"""
import hashlib
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
SNAP = os.path.join(D, 'R17_R72_T1_CLEANSCALE', 'files_tier_A_snap2.tsv')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


lines = open(LED, encoding='utf-8', newline='').read().split('\n')
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(lines)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
    SEC[num] = (i, end)


def blocks(sec):
    i, e = SEC[sec]
    body = lines[i:e]
    st = []
    for j, l in enumerate(body):
        m = re.match(r'^###\s*(?:事项\s*)?(\d+)', l)
        if m:
            st.append((j, int(m.group(1))))
    out = {}
    for idx, (j, k) in enumerate(st):
        end = st[idx + 1][0] if idx + 1 < len(st) else len(body)
        out[k] = '\n'.join(body[j:end])
    return out


rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
data = rows[1:]
BYID = {r[0]: r for r in data}

LEDREF = re.compile(r'R17_LEDGER_(\d+)')


def split_item(it):
    it = it.strip()
    i = it.find('(')
    if i < 0 or not it.endswith(')'):
        return it, None
    return it[:i], it[i + 1:-1]


TOK = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})'
                 r'|(?<![0-9A-Za-z_.])(\d{1,3}(?:,\d{3}){1,}|\d{3,})(?![0-9A-Za-z_])')


def toks(s):
    out, seen = [], set()
    for m in TOK.finditer(s):
        t = next(g for g in m.groups() if g is not None)
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


print('=== 事项级未命中的三分类 ===')
rowsum = []
for r in data:
    fid, stmt, ev = r[0], r[1], r[3]
    for it in ev.split(';'):
        it = it.strip()
        if 'R17_LEDGER_10' not in it:
            continue
        path, anchor = split_item(it)
        if 'R17_LEDGER_10' not in path:
            continue
        m = LEDREF.search(path)
        sec = '1063' if m.group(1) == '1063R' else m.group(1)
        nums = [int(x) for x in re.findall(r'事项\s*(\d+)', anchor or '')]
        if not nums:
            continue
        B = blocks(sec)
        full = '\n'.join(lines[SEC[sec][0]:SEC[sec][1]])
        T = toks(stmt)
        named = '\n'.join(B.get(n, '') for n in nums)
        p1 = [t for t in T if t in named]
        p2, p3 = [], []
        for t in T:
            if t in named:
                continue
            other = '\n'.join(v for k, v in B.items() if k not in nums)
            if t in other:
                p2.append(t)
            elif t in full:
                p3.append(('HDR', t))       # 在节内但在所有 ### 块之外（节标题/前言）
            else:
                p3.append(('ABSENT', t))
        rowsum.append({'fid': fid, 'sec': sec, 'nums': nums, 'n': len(T),
                       'p1': len(p1), 'p2': p2, 'p3': p3})

print('  %-4s %-6s %-8s %-4s %-5s %-16s %s'
      % ('fid', '节', '事项', 'tok', 'P1', 'P2 跨事项', 'P3 节内无'))
for x in rowsum:
    print('  %-4s §%-5s %-8s %-4d %-5d %-16s %s'
          % (x['fid'], x['sec'], '/'.join(map(str, x['nums'])), x['n'], x['p1'],
             ','.join(x['p2'])[:16], ','.join(k + ':' + t for k, t in x['p3'])[:44]))

cross = [x for x in rowsum if x['p2'] and not x['p3']]
wrongblk = [x for x in rowsum if x['p3']]
print('\n  纯「statement 跨事项」（P3 空）= %d  %s'
      % (len(cross), [(x['fid'], '§' + x['sec']) for x in cross]))
print('  含「节内根本没有的 token」（P3 非空）= %d  %s'
      % (len(wrongblk), [(x['fid'], '§' + x['sec'], x['p3']) for x in wrongblk]))

# 只看 P3 里 ABSENT 的（真正「锚点指错块」）
absent_only = [x for x in rowsum if any(k == 'ABSENT' for k, t in x['p3'])]
print('\n  P3 = ABSENT 的条目（锚点指向的节内根本没有该内容）：')
for x in absent_only:
    ab = [t for k, t in x['p3'] if k == 'ABSENT']
    print('    %-4s §%-5s 事项%-6s 缺 %d 个：%s'
          % (x['fid'], x['sec'], '/'.join(map(str, x['nums'])), len(ab), ab))

# 修正 S-379：初版写「F08 是唯一」，实测 6 个条目都有 ABSENT token。
# 真正的区分不是「有没有 ABSENT」，而是「缺的那块内容落在哪」。
fids_absent = sorted(set(x['fid'] for x in absent_only))
print('\n  有 ABSENT token 的 fid = %d  %s' % (len(fids_absent), fids_absent))
where = {}
for x in absent_only:
    for k, t in x['p3']:
        if k != 'ABSENT':
            continue
        secs_hit = [n for n, (i, e) in SEC.items() if t in '\n'.join(lines[i:e])]
        where.setdefault(t, secs_hit)
print('  这些 token 在台账其它节的位置（前 3 节）：')
for t, ss in list(where.items())[:20]:
    print('    %-14s -> %s%s' % (t, ss[:3], ' (+%d)' % (len(ss) - 3) if len(ss) > 3 else ''))
ck('F08 缺的三串在台账别的节里都有（不是台账没有，是锚点指错了节）',
   all(len(where.get(t, [])) >= 1 for t in ('0x47C3D0', '0x6F322F', '0x6F2B40')),
   [(t, len(where.get(t, []))) for t in ('0x47C3D0', '0x6F322F', '0x6F2B40')])
ck('有 ABSENT 的 fid 不止 F08（初版「唯一」判断已撤回）', len(fids_absent) > 1, fids_absent)
ck('F06 属于「跨事项」而非「锚点写错」',
   any(x['fid'] == 'F06' and x['p2'] and not x['p3'] for x in rowsum))

print()
print('=== F23 语料依赖件：11-22 快照在册值 ===')
raw = open(SNAP, 'rb').read()
_parts = raw.decode('utf-8').split('\n')
_nz = [l for l in _parts if l]
snap_lines = _nz[1:]                     # 丢表头
print('  快照 %d B / split 段数 %d / 非空行 %d / 数据行 %d'
      % (len(raw), len(_parts), len(_nz), len(snap_lines)))
ck('快照行数两口径：非空 24,724（含表头）/ 数据 24,723',
   len(_nz) == 24724 and len(snap_lines) == 24723, (len(_nz), len(snap_lines)))
hits = [l for l in snap_lines if 'R17_R41_RECOMPUTE' in l]
ck('R41_RECOMPUTE 在快照里 3 件', len(hits) == 3, len(hits))
import datetime
tot = 0
for h in hits:
    f = h.split('\t')
    tot += int(f[2])
    ts = datetime.datetime.utcfromtimestamp(int(f[3]) / 1e9).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('    %-52s %8s B  mtime=%s' % (f[0], f[2], ts))
print('  三件合计 %d B' % tot)
cv = [l for l in snap_lines if l.split('\t')[0] == 'next_re_20261117_r14/COVERAGE/coverage.tsv']
ck('coverage.tsv 主份（rel 精确）在快照 1 条', len(cv) == 1, len(cv))
_all_cv = [l for l in snap_lines if l.split('\t')[0].endswith('/COVERAGE/coverage.tsv')]
print('  路径含 /COVERAGE/coverage.tsv 的条数 = %d（主份 1 + _hygiene 备份 %d）'
      % (len(_all_cv), len(_all_cv) - 1))
ck('coverage.tsv 记录数两口径：rel 精确 1 / 路径含 4（与 F23 statement ③ 一致）',
   len(_all_cv) == 4, len(_all_cv))
f = cv[0].split('\t')
ts = datetime.datetime.utcfromtimestamp(int(f[3]) / 1e9).strftime('%Y-%m-%dT%H:%M:%SZ')
print('    %-52s %8s B  mtime=%s' % (f[0], f[2], ts))
ck('coverage.tsv 主份 = 4,147,334 B', int(f[2]) == 4147334, f[2])
ck('三件 + coverage 全部现盘不存在',
   not os.path.exists(os.path.join(D, 'R17_R41_RECOMPUTE')) and
   not os.path.exists(os.path.join(D, 'COVERAGE', 'coverage.tsv')))
# 反控：同尺寸唯一性
same = [l for l in snap_lines if int(l.split('\t')[2]) == 11824 and l.split('\t')[0] != hits[0].split('\t')[0]]
ck('反控：11,824 B 在快照内唯一（排除改名存活）', len(same) == 0, len(same))

print()
print('=== F23 正文现状（供写入用）===')
f23 = BYID['F23']
for name, idx in (('statement', 1), ('limitations', 4)):
    t = f23[idx]
    print('  %-11s %d 字符' % (name, len(t)))
    for kw in ('R41_RECOMPUTE', '曾在册', '内容不可读', '承载', '12 行', '13 行'):
        print('    %-14s %d' % (kw, t.count(kw)))
ck('F23 两列均未写「曾在册」/「内容不可读」（本轮要补的缺口）',
   '曾在册' not in f23[1] + f23[4] and '内容不可读' not in f23[1] + f23[4])

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
