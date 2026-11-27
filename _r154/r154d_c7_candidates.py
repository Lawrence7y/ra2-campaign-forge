# -*- coding: utf-8 -*-
"""R154 · C7 三个死分支（exists / bytes= / none）有没有「自然真实行」的机械筛查。

档位定义（只看机械量，不看语义）：
  A = 该产物有 >=2 次历史观测（同目录副本或 *.bak）且字节恒定  -> 有资格写 bytes=N
  B = 只有 1 次观测（就是现在这一份）                          -> 无漂移证据，写 bytes= 属未验证的钉
  C = >=2 次观测且字节不恒定                                    -> 写 bytes= 必是忙碌功陷阱

第二组测量（本脚本的关键正控）：C 档那几行**现在用的是 grep=**，所以必须验证
「在字节漂移的每一个历史版本里，该行的 grep 式仍然命中」——若命中，则 grep= 的选择
不是随意、而是被 109/51 个历史版本实测支持；若不命中，则该行本身就不可靠。
对 id 20（check_disc.py，门禁自身）额外做反控：老版本里不含当前 GATE_VER token，
这正是纪律 20 必须靠 C10 做「登记值 == 脚本值」而不是钉字节的原因。
"""
import io, os, re, json, sys, collections, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = ROOT + '/lead/next_re_20261117_r14/'
DR = P + 'DISC_RECHECK.tsv'

def resolve(p):
    p = p.strip().replace('\\', '/')
    if not p: return None
    for base in (ROOT + '/', ROOT + '/lead/', P):
        if os.path.isfile(base + p): return base + p
    return None

rows = [l.rstrip('\n').split('\t') for l in io.open(DR, encoding='utf-8')]
body = [r for r in rows[1:] if len(r) == 7]

all_baks, dirfiles, nfiles = [], collections.defaultdict(list), 0
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d != '.git']
    for fn in fns:
        nfiles += 1
        dirfiles[dp].append(fn)
        if fn.endswith('.bak'): all_baks.append(os.path.join(dp, fn))
    if nfiles > 400000: raise SystemExit('walk guard')

recs = []
for r in body:
    did, prod, expr = r[0], r[4].strip(), r[5].strip()
    ap = resolve(prod)
    d = {'id': did, 'product': prod.split('\\')[-1], 'expr': expr, 'exists': bool(ap)}
    if ap:
        base, ddir = os.path.basename(ap), os.path.dirname(ap)
        same = [os.path.join(ddir, f) for f in dirfiles[ddir]
                if f == base or (f.startswith(base + '.') and re.match(r'^.*\.(?:bak|before_.*)$', f))]
        hist = [b for b in all_baks if base in os.path.basename(b)]
        obs = sorted(set(same + hist))
        sizes = []
        for f in obs:
            try: sizes.append((f, os.path.getsize(f)))
            except OSError: pass
        cur = os.path.getsize(ap)
        d.update(obs=len(obs), paths=obs, sizes=sorted(set(s for _, s in sizes) | {cur}), cur=cur)
        d['tier'] = ('A' if len(obs) >= 2 and len(d['sizes']) == 1 else
                     'C' if len(obs) >= 2 else 'B')
    recs.append(d)

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)
byid = {d['id']: d for d in recs}

chk(len(recs) == 31, 'rows = %d' % len(recs))
chk(all(d['exists'] for d in recs), 'all 31 products resolve')
A = [d for d in recs if d['tier'] == 'A']
B = [d for d in recs if d['tier'] == 'B']
C = [d for d in recs if d['tier'] == 'C']
chk(len(A) + len(B) + len(C) == 31, 'A+B+C = %d+%d+%d = 31' % (len(A), len(B), len(C)))

print('id  tier obs distinct_sizes  cur       product')
for d in recs:
    print('%-3s %-4s %-3d %-15s %-9s %s' % (d['id'], d['tier'], d['obs'], len(d['sizes']), d['cur'], d['product']))
print()
print('A 档（>=2 观测 且 字节恒定）= %d  -> %r' % (len(A), [d['id'] for d in A]))
print('B 档（仅 1 次观测）        = %d' % len(B))
print('C 档（观测到字节漂移）      = %d' % len(C))
for d in C: print('   ', d['id'], d['product'], 'obs=%d' % d['obs'],
                  'distinct=%d' % len(d['sizes']), 'min=%d max=%d' % (d['sizes'][0], d['sizes'][-1]))

# ---- 关键测量二：C 档那几行的 grep= 在历史版本上还命中吗 ----
def head(expr):
    return expr.strip().split(' ')[0]
def pattern(expr):
    h = head(expr)
    if h.startswith('grep='): return expr[len('grep='):].strip()
    if h.startswith('grepcount='):
        m = re.match(r'^(.*)=(\d+)$', expr[len('grepcount='):].strip(), re.S)
        return m.group(1) if m else None
    return None

hist_ok = {}
for d in C:
    pat = pattern(d['expr'])
    if pat is None:  # rows= 形态的 C 档不会出现，留空防护
        hist_ok[d['id']] = None; continue
    hit = tot = 0
    for f in d['paths']:
        try: txt = io.open(f, encoding='utf-8', errors='replace').read()
        except OSError: continue
        tot += 1
        try:
            if re.search(pat, txt, re.M): hit += 1
        except re.error: pass
    hist_ok[d['id']] = (hit, tot)
    print('   hist-grep id %-3s hit/tot = %d/%d  pat=%r' % (d['id'], hit, tot, pat[:48]))

ids1 = [i for i in ('1', '2', '9') if i in hist_ok and hist_ok[i]]
chk(len(ids1) == 3, 'C-tier includes the three R14_COMMON rows (ids %r)' % ids1)
for i in ids1:
    hit, tot = hist_ok[i]
    chk(hit == tot, 'id %s grep= matches in ALL %d historical versions (so grep= is drift-proof here)' % (i, tot))

h20, t20 = hist_ok.get('20', (0, 0))
chk(h20 < t20, 'id 20 (check_disc.py) current GATE_VER token matches only %d/%d historical versions '
               '-> a bytes= pin would be a busywork trap; the token+C10 trick is required' % (h20, t20))
chk(h20 >= 1, 'id 20 matches in the CURRENT version too (%d >= 1)' % h20)

chk(not A, 'A-tier is EMPTY: no product has >=2 observations with constant size, '
           'so NO natural bytes=N row exists today')

# ---------- 反控 ----------
chk(bool(C), 'POSCTRL C-tier non-empty (%d) so the drift measure has power' % len(C))
chk(len(C) < len(recs), 'NEGCTRL not everything drifted (%d < %d)' % (len(C), len(recs)))
# S-390: 首版断言「当前字节 = 历史最大值（文件只增）」，被 r153o 的去重版反驳 ——
# 1323075 (before_r153o) -> 1322910 (current)，差值 165 B 恰是删掉的两行 S-382 重复条目。
# 结论修正：这类文档**不是只增**，去重会让它变小，故「历史最大」不能当字节上限用。
d0 = byid['1']
chk(d0['sizes'][0] <= d0['cur'] <= d0['sizes'][-1],
    'id 1 current %d sits inside observed range [%d,%d] (it is NOT the max -> R14_COMMON can shrink by dedup)'
    % (d0['cur'], d0['sizes'][0], d0['sizes'][-1]))
chk(d0['cur'] < d0['sizes'][-1],
    'id 1 is strictly below the observed max by %d B -> "only grows" is FALSE (S-390)'
    % (d0['sizes'][-1] - d0['cur']))
# 自造反控：把一个不存在的 basename 拿去匹配 bak，必须 0 命中
chk(not [b for b in all_baks if 'ZZZ_R154_NO_SUCH_PRODUCT.bin' in os.path.basename(b)],
    'NEGCTRL self-made basename matches 0 backups')
# 正控：R14_COMMON.md 的 bak 必须真被匹配到（否则 C 档计数不可信）
chk(len([b for b in all_baks if 'R14_COMMON.md' in os.path.basename(b)]) >= 100,
    'POSCTRL R14_COMMON.md backups found = %d (>=100)'
    % len([b for b in all_baks if 'R14_COMMON.md' in os.path.basename(b)]))

out = {'rows': len(recs), 'walked_files': nfiles, 'total_baks': len(all_baks),
       'A': [{'id': d['id'], 'file': d['product'], 'obs': d['obs'], 'bytes': d['cur']} for d in A],
       'B': [{'id': d['id'], 'file': d['product'], 'obs': d['obs'], 'bytes': d['cur']} for d in B],
       'C': [{'id': d['id'], 'file': d['product'], 'obs': d['obs'], 'distinct_sizes': len(d['sizes']),
              'min': d['sizes'][0], 'max': d['sizes'][-1]} for d in C],
       'hist_grep': {k: list(v) for k, v in hist_ok.items() if v},
       'pass': len(NOTES), 'fail': len(FAILS), 'fails': FAILS, 'notes': NOTES,
       'measured_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
io.open(ROOT + '/_r154/r154d_c7_candidates.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
