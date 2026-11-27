# -*- coding: utf-8 -*-
"""R154 · C7 三个死分支（exists / bytes= / none）有没有「自然真实行」的机械筛查。

判据：`bytes=N` / `exists ✓(N B)` 只有在「该产物字节数不随正常操作漂移」时才是好校验
（R14_COMMON §2.22 纪律 10 与 §2.49 的「忙碌功陷阱」结论）。故不做主观挑选，只做机械测量：
对 DISC_RECHECK 的 31 行，测它产物在**同目录**下所有同名副本（`.bak` / `.before_*` 等）
的字节数集合 ——
  * 集合大小 > 1  ⇒ 该产物**已被观测到漂移** ⇒ bytes= 是忙碌功陷阱（钉住了会每轮手改）
  * 集合大小 = 1 且副本数 >= 1 ⇒ 候选（当前观测是不漂移）
  * 副本数 = 0 ⇒ 无漂移证据，只能是弱候选（不得据此改门禁）
`none` 分支的自然条件更严格：该行必须**没有产物路径**（文档内锚）。机械判据 = 第 5 列为空或
等于文档内锚占位符。这一条只报计数，不臆造语义。

本脚本只测量，**不改任何门禁文件**。档位判定属裁定，留给正文。
"""
import io, os, re, json, sys, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = ROOT + '/lead/next_re_20261117_r14/'
DR = P + 'DISC_RECHECK.tsv'
DOC_ANCHOR = '\uff08\u6587\u6863\u5185\u951a\uff09'   # （文档内锚）

def resolve(p):
    p = p.strip().replace('\\', '/')
    if not p: return None
    for base in (ROOT + '/', ROOT + '/lead/', P):
        if os.path.isfile(base + p): return base + p
    return None

rows = [l.rstrip('\n').split('\t') for l in io.open(DR, encoding='utf-8')]
hdr, body = rows[0], [r for r in rows[1:] if len(r) == 7]
assert len(body) == 31, len(body)

# ---- 一次 walk（排除 .git），按目录建索引，避免 31 次全盘扫 ----
dirfiles = collections.defaultdict(set)
all_baks = []
nfiles = 0
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d != '.git']
    for fn in fns:
        dirfiles[dp].add(fn); nfiles += 1
        if fn.endswith('.bak'): all_baks.append(os.path.join(dp, fn))
        if nfiles > 400000: raise SystemExit('walk guard tripped: %d files' % nfiles)

def shape(expr):
    h = expr.strip().split(' ')[0]
    if h in ('none', ''): return 'none'
    if h.startswith('bytes='): return 'bytes='
    if h.startswith('rows='): return 'rows='
    if h.startswith('grepcount='): return 'grepcount='
    if h.startswith('grep='): return 'grep='
    if h == 'exists': return 'exists'
    return 'BAD:' + h

_BAK = re.compile(r'^(.*?)\.(?:bak|before_.*)$')
def is_copy_of(fn, target):
    # S-388: 首版用「点号前 stem 相同」，把 falsify_r94.py 与 falsify_r94.json 判成同族副本
    # （同一脚本的 .py/.json 是不同产物，不是同一文件的备份）。改为只认两种真备份形态：
    #   1) <target>.bak           2) <target>.before_*.bak / <target>.before_*
    if fn == target: return True
    return fn.startswith(target + '.') and _BAK.match(fn) is not None

recs = []
for r in body:
    did, prod, expr = r[0], r[4].strip(), r[5].strip()
    sh = shape(expr)
    ap = resolve(prod)
    d = {'id': did, 'shape': sh, 'product': prod, 'exists': bool(ap)}
    if ap:
        dstdir = os.path.dirname(ap)
        st = os.path.basename(ap)
        d['dir'] = dstdir
        d['base'] = st
        copies = sorted(os.path.join(dstdir, f) for f in dirfiles[dstdir] if is_copy_of(f, st))
        # 历史备份：全仓 *.bak 文件名里含该产物 basename（R17_LEAD_BASELINE 用
        # before_<tag>_<target>_<ts>.bak 形态，同目录没有副本）
        hist = sorted(bkp for bkp in all_baks if st in os.path.basename(bkp))
        d['copies'] = copies
        d['hist'] = hist
        sizes, hsizes = [], []
        for f in copies:
            try: sizes.append(os.path.getsize(f))
            except OSError: pass
        for f in hist:
            try: hsizes.append(os.path.getsize(f))
            except OSError: pass
        d['cur_bytes'] = os.path.getsize(ap)
        d['distinct_sizes'] = sorted(set(sizes) | set(hsizes) | {d['cur_bytes']})
    recs.append(d)

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)

chk(len(recs) == 31, 'DISC_RECHECK rows = %d (expect 31)' % len(recs))
chk(all(d['exists'] for d in recs), 'all 31 products resolve on disk ; missing=%r'
    % [d['id'] for d in recs if not d['exists']])

census = collections.Counter(d['shape'] for d in recs)
# S-389: Counter 不含零项，故只与 pin 的非零子集比；零项由下面的 none_nat 断言单独覆盖
_pin_nonzero = {'grep=': 24, 'grepcount=': 3, 'rows=': 4}
chk(census == _pin_nonzero,
    'shape census (non-zero shapes) = %r must equal pin non-zero subset %r ; '
    'exists/bytes=/none pinned 0 and measured 0' % (dict(census), _pin_nonzero))

obs = [d for d in recs if d['exists'] and (d['copies'] or d['hist'])]
drifted = [d for d in obs if len(d['distinct_sizes']) > 1]
stable  = [d for d in obs if len(d['distinct_sizes']) == 1]
nocopy  = [d for d in recs if d['exists'] and not d['copies'] and not d['hist']]

# none 分支的自然条件：无产物路径（文档内锚）
none_nat = [d for d in recs if d['product'] in ('', DOC_ANCHOR) or d['shape'] == 'none']
chk(not none_nat, 'rows whose product cell is empty/doc-anchor (= natural "none" candidates) = %d'
    % len(none_nat))

print('id  shape       copies sizes                      cur        product')
for d in recs:
    print('%-3s %-11s %-4s %-4s %-30s %-10s %s' % (
        d['id'], d['shape'], len(d.get('copies', [])), len(d.get('hist', [])),
        str(d.get('distinct_sizes', []))[:30], d.get('cur_bytes', '-'),
        d['product'].split('\\')[-1]))
print()
print('drifted products (>=2 observed byte sizes, bytes= would be a busywork trap): %d' % len(drifted))
for d in drifted: print('   ', d['id'], d['shape'], d['product'].split('\\')[-1], d['distinct_sizes'])
print('observed single-size (stable so far): %d' % len(stable))
for d in stable: print('   ', d['id'], d['shape'], d['product'].split('\\')[-1], d['distinct_sizes'])
print('no history at all (no .bak, no same-dir copy -> no drift evidence): %d' % len(nocopy))
for d in nocopy: print('   ', d['id'], d['shape'], d['product'].split('\\')[-1], d['cur_bytes'])

# 反控：故意用错 stem 匹配，必须打空
_d0 = os.path.dirname(resolve(body[0][4].replace('\\','/')) or P)
bogus = [f for f in dirfiles[_d0] if is_copy_of(f, 'ZZZ_R154_NO_SUCH_STEM')]
chk(not bogus, 'NEGCTRL bogus stem match -> %d hits (expect 0)' % len(bogus))
# 正控：至少有一行被实测到副本（否则"漂移"这条判据无从谈起）
chk(bool(obs), 'POSCTRL %d products have at least one historical observation (detector has power)' % len(obs))
chk(len(drifted) < len(recs), 'NEGCTRL not everything drifted (%d < %d) so the measure discriminates'
    % (len(drifted), len(recs)))

out = {'rows': len(recs), 'census': dict(census), 'walked_files': nfiles,
       'drifted': [{'id': d['id'], 'shape': d['shape'], 'file': d['product'].split('\\')[-1],
                    'sizes': d['distinct_sizes'], 'copies': len(d['copies'])} for d in drifted],
       'stable_with_copy': [{'id': d['id'], 'shape': d['shape'], 'file': d['product'].split('\\')[-1],
                             'sizes': d['distinct_sizes']} for d in stable],
       'no_copy': [{'id': d['id'], 'shape': d['shape'], 'file': d['product'].split('\\')[-1],
                    'bytes': d['cur_bytes']} for d in nocopy],
       'pass': len(NOTES), 'fail': len(FAILS), 'fails': FAILS, 'notes': NOTES}
io.open(ROOT + '/_r154/r154c_c7_natural.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print()
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
