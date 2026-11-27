#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 F：把「事项级 ABSENT」判成真缺陷还是被别的 evidence 项覆盖。

上一版（r153e）只统计「该 token 不在被点名事项块内」，得到 6 个条目。
但 statement 常常是**多主题合并句**，不同 evidence 项分管不同主题 —— 若某个 token
被同一行的**另一项**覆盖，那这一项 ABSENT 就不是缺陷。本脚本补这一步：

  对每个 (fid, item) 的 ABSENT token，检查它是否出现在**同一行其它 evidence 项**的目标段内。
  - 被其它项覆盖  -> OVERLAP（不是缺陷，属多主题合并句的正常分工）
  - 无任何项覆盖  -> DANGLING（该内容在本行所有 evidence 指向的位置里都找不到）

这是本轮唯一能把 F08 与其余 5 条区分开的判据，必须机械跑出来，不靠人看。
"""
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
RC = os.path.join(D, 'R14_COMMON.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
ARC = os.path.join(D, 'BOARD_ARCHIVE.md')
BRD = os.path.join(D, 'STATUS_BOARD.md')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


def load(p):
    return open(p, encoding='utf-8', newline='').read().split('\n')


LEDL = load(LED)
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(LEDL)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(LEDL)
    SEC[num] = (i, end)

RCL = load(RC)
rc_secs = [(i, int(re.match(r'^##\s+2\.(\d+)\b', l).group(1)))
           for i, l in enumerate(RCL) if re.match(r'^##\s+2\.\d+\b', l)]
RCSEC = {}
for k, (i, num) in enumerate(rc_secs):
    end = rc_secs[k + 1][0] if k + 1 < len(rc_secs) else len(RCL)
    RCSEC[num] = (i, end)


def led_block(sec, item):
    i, e = SEC[sec]
    body = LEDL[i:e]
    st = []
    for j, l in enumerate(body):
        m = re.match(r'^###\s*(?:事项\s*)?(\d+)', l)
        if m:
            st.append((j, int(m.group(1))))
    for idx, (j, k) in enumerate(st):
        if k == item:
            end = st[idx + 1][0] if idx + 1 < len(st) else len(body)
            return '\n'.join(body[j:end])
    return ''


def rc_block(num, sub=None):
    i, e = RCSEC[num]
    body = RCL[i:e]
    if sub is None:
        return '\n'.join(body)
    want = {'一': '一', '二': '二', '三': '三', '四': '四', '五': '五', '六': '六'}[sub]
    st = [(j, l) for j, l in enumerate(body) if re.match(r'^###\s*' + want + r'\s', l)]
    if not st:
        return ''
    j = st[0][0]
    later = [x for x in range(j + 1, len(body)) if body[x].startswith('### ')]
    end = later[0] if later else len(body)
    return '\n'.join(body[j:end])


FULL = {}
for name, p in (('LEDGER', LED), ('R14_COMMON', RC), ('LEAD_LOCK', LOCK),
                ('BOARD_ARCHIVE', ARC), ('STATUS_BOARD', BRD)):
    FULL[name] = '\n'.join(load(p))


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


def item_scope(path, anchor):
    """把一条 evidence 项解析成它指向的文本范围；解析不出返回 None（= 在盘但未细分）。"""
    path = path.strip()
    if 'R17_LEDGER_' in path:
        m = re.search(r'R17_LEDGER_(\d+)', path)
        sec = '1063' if m.group(1) == '1063R' else m.group(1)
        nums = [int(x) for x in re.findall(r'事项\s*(\d+)', anchor or '')]
        if nums:
            return '\n'.join(led_block(sec, n) for n in nums), 'LEDGER §%s 事项%s' % (
                sec, '/'.join(map(str, nums)))
        return '\n'.join(LEDL[SEC[sec][0]:SEC[sec][1]]), 'LEDGER §%s 全节' % sec
    if path.endswith('R14_COMMON.md'):
        m = re.search(r'§(\d+(?:\.\d+)*)', anchor or '')
        if m:
            key = m.group(1)
            num = None
            mm = re.match(r'2\.(\d+)$', key)
            if mm:
                num = int(mm.group(1))
            if num is not None and num in RCSEC:
                subs = re.findall(r'([一二三四五六])', anchor or '')
                if subs:
                    return ('\n'.join(rc_block(num, x) for x in subs),
                            'RC §2.%d %s' % (num, '/'.join(subs)))
                return rc_block(num), 'RC §2.%d 全节' % num
            # 非 2.x 节（如 §6 / §13.1）：退到整节文本或全文
            hdrs = [(i, l) for i, l in enumerate(RCL) if re.match(r'^#+\s*' + re.escape(key) + r'\b', l)]
            if hdrs:
                i0 = hdrs[0][0]
                later = [j for j in range(i0 + 1, len(RCL)) if re.match(r'^##\s', RCL[j])]
                i1 = later[0] if later else len(RCL)
                return '\n'.join(RCL[i0:i1]), 'RC §%s' % key
        return FULL['R14_COMMON'], 'RC 全文'
    if path.endswith('LEAD_LOCK'):
        return FULL['LEAD_LOCK'], 'LEAD_LOCK 全文'
    if path.endswith('BOARD_ARCHIVE.md'):
        return FULL['BOARD_ARCHIVE'], 'ARCHIVE 全文'
    if path.endswith('STATUS_BOARD.md'):
        return FULL['STATUS_BOARD'], 'BOARD 全文'
    return None, 'OTHER:' + os.path.basename(path)


rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
data = rows[1:]

print('=== 每个 (fid, 事项锚) 的 ABSENT token 是否被同行其它项覆盖 ===')
summary = []
for r in data:
    fid, stmt, ev = r[0], r[1], r[3]
    items = [x.strip() for x in ev.split(';') if x.strip()]
    parsed = []
    for it in items:
        path, anchor = split_item(it)
        txt, label = item_scope(path, anchor)
        parsed.append({'raw': it, 'label': label, 'txt': txt or ''})
    T = toks(stmt)
    for p in parsed:
        if not p['label'].startswith('LEDGER'):
            continue
        if '事项' not in p['label']:
            continue
        mine_hit = [t for t in T if t in p['txt']]
        absent = [t for t in T if t not in p['txt']]
        if not absent:
            continue
        # 分层覆盖：精准项（有事项/子节锚） vs 全部项（含指向全文的项）
        others_all = '\n'.join(q['txt'] for q in parsed if q is not p)
        others_precise = '\n'.join(q['txt'] for q in parsed if q is not p
                                   and ('事项' in q['label'] or
                                        ('RC §' in q['label'] and '全节' not in q['label']
                                         and '全文' not in q['label'])))
        covered = [t for t in absent if t in others_all]
        dangling = [t for t in absent if t not in others_all]
        cov_precise = [t for t in absent if t in others_precise]
        summary.append({'fid': fid, 'label': p['label'], 'n': len(T),
                        'hit': len(mine_hit), 'absent': absent,
                        'covered': covered, 'dangling': dangling,
                        'cov_precise': cov_precise,
                        'dangle_precise': [t for t in absent if t not in others_precise]})

print('  %-4s %-24s %-4s %-5s %-25s %s'
      % ('fid', '被核项', 'tok', '本项', '被同行其它项覆盖', '无任何项覆盖(DANGLING)'))
for s in summary:
    print('  %-4s %-24s %-4d %-5d %-25s %s'
          % (s['fid'], s['label'], s['n'], s['hit'],
             ','.join(s['covered'])[:25], ','.join(s['dangling'])[:40]))

dang = [s for s in summary if s['dangling']]
print('\n  有 DANGLING 的条目 = %d' % len(dang))
for s in dang:
    print('    %-4s %-24s 悬空 %d 个：%s' % (s['fid'], s['label'], len(s['dangling']), s['dangling']))
ovl = [s for s in summary if s['covered'] and not s['dangling']]
print('  纯 OVERLAP（多主题分工，非缺陷）= %d  %s'
      % (len(ovl), [(s['fid'], s['label']) for s in ovl]))


print('\n=== 分层：只算「精准项」时谁覆盖不了 ===')
print('  %-4s %-24s %-5s %-16s %-16s %s'
      % ('fid', '被核项', '本项', '精准项覆盖', '全部项覆盖', '仅全文项覆盖(粒度问题)'))
for s in summary:
    onlyfull = [t for t in s['absent'] if t not in s['cov_precise'] and t in s['covered']]
    print('  %-4s %-24s %-5d %-16s %-16s %s'
          % (s['fid'], s['label'], s['hit'],
             len(s['cov_precise']), len(s['covered']), ','.join(onlyfull)[:36]))

n_only_full = [s for s in summary if any(t not in s['cov_precise'] and t in s['covered']
                                         for t in s['absent'])]
print('\n  存在「只能被全文项覆盖」的条目 = %d  %s'
      % (len(n_only_full), [(s['fid'], s['label']) for s in n_only_full]))
n_true_dangle = [s for s in summary if s['dangle_precise']]
print('  精准项口径下仍悬空 = %d' % len(n_true_dangle))
for s in n_true_dangle:
    print('    %-4s %-24s %s' % (s['fid'], s['label'], s['dangle_precise']))

ck('F08 的 a–e 三串在「全部项」口径下被覆盖（内容可核）',
   any(s['fid'] == 'F08' and set(s['covered']) >= {'0x47C3D0', '0x6F322F', '0x6F2B40'}
       for s in summary))
ck('F08 的第二项本项只覆盖 a–e 的 0 个（本项对该内容零承载）',
   any(s['fid'] == 'F08' and not (set(s['absent']) & set()) and
       len([t for t in ('0x47C3D0', '0x6F322F', '0x6F2B40') if t not in s['absent']]) == 0
       for s in summary))
ck('F06 的 0x449440 属 OVERLAP（被同行其它项覆盖，不是缺陷）',
   any(s['fid'] == 'F06' and s['covered'] and not s['dangling'] for s in summary))

print('\n=== 正反控 ===')
ck('正控：R14_COMMON §2.9 一 解析非空且含 0x47C3D0', '0x47C3D0' in rc_block(9, '一'))
ck('反控：R14_COMMON §2.9 二 不含 0x47C3D0（子块确实被切开）', '0x47C3D0' not in rc_block(9, '二'))
ck('正控：LEDGER §1064 事项3 解析非空', len(led_block('1064', 3)) > 100)
ck('反控：LEDGER §1064 事项6 不含 0x47C620', '0x47C620' not in led_block('1064', 6))
ck('反控：自造 token 0xFEEDFACE 在所有段内均不出现',
   not any('0xFEEDFACE' in v for v in FULL.values()))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
