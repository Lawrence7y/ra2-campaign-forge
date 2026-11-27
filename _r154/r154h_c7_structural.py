# -*- coding: utf-8 -*-
"""R154 · C7 死分支：把「字节恒定」换成一条**可机检的结构判据**再测一次。

为什么需要这一步：r154d 测出 A 档为空，但那是因为 27 个产物**没有历史备份**（观测次数=1），
不是「已证会漂」。所以「字节恒不恒定」在这些行上不可判。R14_COMMON §2.49 的结论是
「字节数对**一次生成、不再改**的产物是好选择」，于是换一条结构判据来判「是不是一次生成产物」：

  P1  产物是否落在**轮次专属目录**（形如 R17_R<数字>_* 或 _r<数字>）而不是工作目录
  P2  产物所在目录里是否**没有**任何 .bak（有 .bak = 这个目录的东西被改过）
  P3  产物 mtime 与所在轮次目录内所有文件的最大 mtime 之差（=「同轮产物、之后没再动」的机械代理）

三条都不是语义判断。据此给出「可写 bytes= 的候选行」与「不可写」的两组，供裁定用；
本脚本不改门禁。
"""
import io, os, re, json, sys, time, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = ROOT + '/lead/next_re_20261117_r14/'
DR = P + 'DISC_RECHECK.tsv'
WORKDIRS = {P.rstrip('/'), ROOT, ROOT + '/lead'}

def resolve(p):
    p = p.strip().replace('\\', '/')
    if not p: return None
    for base in (ROOT + '/', ROOT + '/lead/', P):
        if os.path.isfile(base + p): return base + p
    return None

ROUNDDIR = re.compile(r'/(?:R17_R\d+_[^/]+|_r\d+|R\d+_[^/]+)$')

rows = [l.rstrip('\n').split('\t') for l in io.open(DR, encoding='utf-8')]
body = [r for r in rows[1:] if len(r) == 7]

recs = []
for r in body:
    did, prod, expr = r[0], r[4].strip(), r[5].strip()
    ap = resolve(prod)
    d = {'id': did, 'expr': expr, 'product': prod, 'exists': bool(ap)}
    if ap:
        ddir = os.path.dirname(ap)
        d['dir'] = ddir
        d['in_workdir'] = ddir in WORKDIRS
        d['in_rounddir'] = bool(ROUNDDIR.search(ddir))
        d['dir_baks'] = sorted(f for f in os.listdir(ddir) if f.endswith('.bak'))
        mt = os.path.getmtime(ap)
        others = []
        for f in os.listdir(ddir):
            fp = os.path.join(ddir, f)
            if os.path.isfile(fp) and fp != ap:
                others.append(os.path.getmtime(fp))
        d['mtime'] = int(mt)
        d['max_other_mtime'] = int(max(others)) if others else 0
        d['is_mtime_max'] = mt >= (max(others) if others else 0)
        d['bytes'] = os.path.getsize(ap)
        d['p1'] = d['in_rounddir'] and not d['in_workdir']
        d['p2'] = (len(d['dir_baks']) == 0)
        d['p3'] = d['is_mtime_max']
    recs.append(d)

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)
byid = {d['id']: d for d in recs}

chk(len(recs) == 31, 'rows = %d' % len(recs))
chk(all(d['exists'] for d in recs), 'all resolve')

for d in recs:
    d['cand'] = d['p1'] and d['p2'] and d['p3']

print('id  rounddir workdir dirbaks mtime_max  cand  product')
for d in recs:
    print('%-3s %-8s %-7s %-7d %-9s %-5s %s' % (
        d['id'], d['in_rounddir'], d['in_workdir'], len(d['dir_baks']),
        d['is_mtime_max'], d['cand'], d['product'].split('\\')[-1]))

cand = [d for d in recs if d['cand']]
notc = [d for d in recs if not d['cand']]
print()
print('P1&P2&P3 全部满足（可写 bytes= 的候选）= %d  ids=%r' % (len(cand), [d['id'] for d in cand]))
print('不满足的 = %d  ids=%r' % (len(notc), [(d['id'], d['p1'], d['p2'], d['p3']) for d in notc]))

chk(len(cand) + len(notc) == 31, 'candidate split closes: %d+%d=31' % (len(cand), len(notc)))
# 关键：工作目录里的 4 行（含门禁自身）必须全部不在候选里
work = [d['id'] for d in recs if d['in_workdir']]
chk(sorted(work, key=int) == ['1', '2', '9', '20'],
    'workdir rows = %r (expect exactly the 4 drifted ones)' % sorted(work, key=int))
chk(all(not byid[i]['cand'] for i in work), 'all 4 workdir rows are excluded from candidates')
# P1 单独就能把 4 行剔掉
chk(all(not d['p1'] for d in recs if d['in_workdir']), 'P1 alone excludes every workdir row')

# 候选行必须都是轮次目录、目录内 0 bak
chk(all(d['in_rounddir'] for d in cand), 'every candidate lives in a round directory')
chk(all(not d['dir_baks'] for d in cand), 'no candidate directory contains a .bak')

# 反控 1：把「in_workdir」判据去掉，候选数必须变化（说明判据有作用，不是恒真/恒假）
# S-394: 首版反控写「去掉 P1 候选数必须变化」，实测 19 -> 19 —— 不变。
# 复算原因：4 个工作目录行同时 p3=False，所以 P1 在这份数据上**被 P3 完全覆盖**（冗余）。
# 这不是判据错，是「本轮数据里 P1 没有独立贡献」——如实登记，并把结论改用能被反驳的形式：
alt = [d for d in recs if d['p2'] and d['p3']]
chk(len(alt) == len(cand),
    'P1 is REDUNDANT on this data: P2&P3 alone already yields %d = %d candidates (S-394)' % (len(alt), len(cand)))
p1_only = [d['id'] for d in recs if (not d['p1']) and d['p2'] and d['p3']]
chk(not p1_only, 'no row is excluded by P1 alone (would be: %r) -- so P1 carries no独立 power today' % p1_only)
# 反控 2：mtime 判据必须有反例（否则 P3 无鉴别力）
chk(any(not d['is_mtime_max'] for d in recs),
    'P3 has at least one counter-example (%d rows are not the newest in their dir)'
    % sum(1 for d in recs if not d['is_mtime_max']))
# 反控 3：自造路径
chk(resolve('lead/next_re_20261117_r14/R17_R999_NOPE/REPORT.md') is None,
    'NEGCTRL fake round path does not resolve')

out = {'rows': len(recs),
       'candidates': [{'id': d['id'], 'file': d['product'].split('\\')[-1],
                       'dir': os.path.relpath(d['dir'], ROOT), 'bytes': d['bytes']} for d in cand],
       'excluded': [{'id': d['id'], 'file': d['product'].split('\\')[-1],
                     'p1': d['p1'], 'p2': d['p2'], 'p3': d['p3']} for d in notc],
       'workdir_ids': sorted(work, key=int),
       'pass': len(NOTES), 'fail': len(FAILS), 'fails': FAILS, 'notes': NOTES,
       'measured_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
io.open(ROOT + '/_r154/r154h_c7_structural.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
