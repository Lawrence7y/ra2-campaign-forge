# -*- coding: utf-8 -*-
"""r134b_controls.py -- R134 门禁修法（C7c 结构判据 + C7d 第5/6列指纹钉）的正反控。

沙箱：symlink 真树，仅 check_disc.py 与 DISC_RECHECK.tsv 为可写副本
      （R133 S-227 教训：不得 copytree 811MB 树）。
复原一律从内存基线写回（R130 S-203 教训）。

正控（P）：修法不得误伤
  P1 未改副本 exit 0
  P2 C7c 打印 27 行被测、0 可空
  P3 C7d 打印指纹 ok
负控（N）：每一处改动都必须被抓住，且必须报出对应的检查名
  N1 HOLE A：col5 换到另一个同样满足该式的产物 -> exit 1 且报 C7d
  N2 HOLE B：col6 追加永真分支 -> exit 1 且报 C7d
  N3 HOLE B 的独立一侧：只把 col6 换成可空正则（不追加，直接写成 .* 之类）
     -> exit 1 且**同时**报 C7d（被钉住）与 C7c（结构判据本身也拒收）
  N4 N3 的强化：连 C7d 常量与行指纹一起重钉（模拟「伪造者同改表与常量」）
     -> C7d 放行，但 C7c 仍 exit 1。这一条证明 C7c 与 C7d 是两个独立条件，
        不是把同一个判断写两遍；也是 C7c 相对 sha 钉的独立价值所在。
  N5 col5 指向不满足该式的产物 -> exit 1 且报 C7（原有判据仍有效，未被本次改动削弱）
"""
import io, os, re, shutil, subprocess, sys, hashlib, json, copy

ROOT = '/home/t628/projects/ra2-campaign-forge'
REAL = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SB = os.path.join(ROOT, '_r134', 'sb2')
ROWS_TSV = 'DISC_RECHECK.tsv'
GATE = 'check_disc.py'
res = []
OUT = {}


def _safe_rmtree(path):
    """R134 事故防护（S-233）：沙箱用 symlink 指向真树，shutil.rmtree 在遇到目录软链时
    的行为依赖实现细节，实测在 _r134/sb 上把真树 lead/.../R17_R84_T1_NARRATIVE 的内容
    删空并把目录换成了自环软链。故移除前先逐个解链，只删普通文件与空目录。"""
    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.islink(fp):
                os.unlink(fp)
            else:
                os.remove(fp)
        for d in dirs:
            dp = os.path.join(root, d)
            if os.path.islink(dp):
                os.unlink(dp)
            else:
                try:
                    os.rmdir(dp)
                except OSError:
                    pass
    try:
        os.rmdir(path)
    except OSError:
        pass


def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
    return p.returncode, p.stdout, p.stderr


def build():
    if os.path.isdir(SB):
        _safe_rmtree(SB)
    r14 = os.path.join(SB, 'lead', 'next_re_20261117_r14')
    os.makedirs(r14)
    for name in os.listdir(REAL):
        if name == GATE:
            continue
        try:
            os.symlink(os.path.join(REAL, name), os.path.join(r14, name))
        except OSError:
            pass
    os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(SB, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    os.symlink(os.path.join(ROOT, '_r94'), os.path.join(SB, '_r94'))
    for n in (GATE, ROWS_TSV):
        src = os.path.join(REAL, n)
        dst = os.path.join(r14, n)
        if os.path.lexists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
    return r14


def gate(r14):
    rc, out, _ = sh([sys.executable, os.path.join(r14, GATE)])
    fails = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
    return rc, fails, out


def rd(r14):
    t = io.open(os.path.join(r14, ROWS_TSV), encoding='utf-8', newline='').read()
    assert '\r' not in t
    ls = [l for l in t.split('\n') if l]
    return ls[0], [l.split('\t') for l in ls[1:]]


def wr(r14, hdr, rows):
    io.open(os.path.join(r14, ROWS_TSV), 'w', encoding='utf-8', newline='').write(
        hdr + '\n' + '\n'.join('\t'.join(r) for r in rows) + '\n')


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-56s %s' % ('PASS' if cond else 'FAIL', name, detail))


r14 = build()
_, rows0 = rd(r14)
BASE = copy.deepcopy(rows0)
HDR = rd(r14)[0]


def restore():
    wr(r14, HDR, copy.deepcopy(BASE))


# ---------- 正控 ----------
rc1, f1, o1 = gate(r14)
chk('P1 unmodified copy exit 0 (no self-inflicted FAIL)', rc1 == 0, 'exit=%d fails=%d' % (rc1, len(f1)))
chk('P2 C7c reports 27 rows tested, 0 nullable',
    bool(re.search(r'C7c vacuity pre-filter: 27 regex rows tested against empty string, 0 nullable', o1)),
    'C7c note present')
chk('P3 C7d reports fingerprint ok',
    bool(re.search(r'C7d product/expression fingerprint ok: 31 rows, sha256=[0-9a-f]{16}', o1)),
    'C7d note present')

# ---------- N1 HOLE A ----------
hdr, rows = rd(r14)
prods = sorted(set(r[4].strip().replace('\\', '/') for r in rows))


def ev_ok(path, expr):
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False
    e = expr.strip(); head = e.split(' ')[0]
    if head.startswith('grep='):
        t = io.open(ap, encoding='utf-8', errors='replace').read()
        return len(re.findall(e[len('grep='):].strip(), t, re.M)) >= 1
    m = re.fullmatch(r'grepcount=(.*)=(\d+)$', e, re.S)
    if m:
        t = io.open(ap, encoding='utf-8', errors='replace').read()
        return len(re.findall(m.group(1), t, re.M)) == int(m.group(2))
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = h = 0
        for ln in io.open(ap, encoding='utf-8', errors='replace'):
            s = ln.strip()
            if s.startswith('DISC_RECHECK '):
                continue
            if h == 0:
                h = 1; continue
            n += 1
        return n == int(m3.group(1))
    return None


sw = None
for r in rows:
    e = r[5].strip(); cur = r[4].strip().replace('\\', '/')
    alts = [q for q in prods if q != cur and ev_ok(q, e) is True]
    if alts:
        sw = (r[0], cur, alts[0]); r[4] = alts[0].replace('/', '\\'); break
wr(r14, hdr, rows)
rc2, f2, _ = gate(r14)
chk('N1 HOLE A (col5 swapped, same expr still true) -> exit 1 reporting C7d',
    rc2 == 1 and any('C7d' in x for x in f2),
    'id=%s %s->%s exit=%d C7d=%s' % (sw[0], sw[1].split('/')[-1], sw[2].split('/')[-1], rc2,
                                     any('C7d' in x for x in f2)))
OUT['N1'] = {'id': sw[0], 'exit': rc2}
restore()

# ---------- N2 HOLE B ----------
hdr, rows = rd(r14)
t2 = None
for r in rows:
    if r[5].strip().startswith('grep='):
        r[5] = r[5].rstrip() + '|(?m:^)'; t2 = r[0]; break
wr(r14, hdr, rows)
rc3, f3, _ = gate(r14)
chk('N2 HOLE B (col6 appended vacuous branch) -> exit 1 reporting C7d',
    rc3 == 1 and any('C7d' in x for x in f3),
    'id=%s exit=%d C7d=%s' % (t2, rc3, any('C7d' in x for x in f3)))
OUT['N2'] = {'id': t2, 'exit': rc3}
restore()

# ---------- N3 col6 直接写成可空正则 ----------
hdr, rows = rd(r14)
t3 = None
for r in rows:
    if r[5].strip().startswith('grep='):
        r[5] = 'grep=.*'; t3 = r[0]; break
wr(r14, hdr, rows)
rc4, f4, _ = gate(r14)
hit_c7c = any('C7c' in x for x in f4)
hit_c7d = any('C7d' in x for x in f4)
chk('N3 vacuous regex in col6 -> exit 1 reporting BOTH C7c and C7d',
    rc4 == 1 and hit_c7c and hit_c7d,
    'id=%s exit=%d C7c=%s C7d=%s' % (t3, rc4, hit_c7c, hit_c7d))
OUT['N3'] = {'id': t3, 'exit': rc4, 'c7c': hit_c7c, 'c7d': hit_c7d}

# ---------- N4 同改表与常量：C7d 放行，C7c 仍抓 ----------
hdr, rows = rd(r14)
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
newsha = hashlib.sha256(blob.encode('utf-8')).hexdigest()
rowsha = dict((r[0], hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                                    .encode('utf-8')).hexdigest()) for r in rows if len(r) == 7)
gp = os.path.join(r14, GATE)
gsrc = io.open(gp, encoding='utf-8').read()
gsrc2 = re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{64}'", "C7_TEXT_SHA256 = '%s'" % newsha, gsrc)
assert gsrc2 != gsrc, 'C7_TEXT_SHA256 constant not found for N4'
gsrc3 = re.sub(r"C7_ROW_SHA = \{[^}]*\}",
               'C7_ROW_SHA = {' + ', '.join("'%s': '%s'" % (k, v) for k, v in rowsha.items()) + '}',
               gsrc2, count=1)
assert gsrc3 != gsrc2, 'C7_ROW_SHA dict not found for N4'
io.open(gp, 'w', encoding='utf-8').write(gsrc3)
rc5, f5, _ = gate(r14)
c7d_pass = not any('C7d' in x for x in f5)
c7c_fail = any('C7c' in x for x in f5)
chk('N4 re-pin C7d constants too -> C7d passes but C7c still exit 1 (independent)',
    rc5 == 1 and c7d_pass and c7c_fail,
    'exit=%d C7d_pass=%s C7c_fail=%s' % (rc5, c7d_pass, c7c_fail))
OUT['N4'] = {'exit': rc5, 'c7d_pass': c7d_pass, 'c7c_fail': c7c_fail}

# 复原门禁与表
shutil.copy2(os.path.join(REAL, GATE), gp)
restore()

# ---------- N5 col5 指向不满足的产物：原有 C7 仍生效 ----------
hdr, rows = rd(r14)
t5 = None
for r in rows:
    e = r[5].strip(); cur = r[4].strip().replace('\\', '/')
    bad = [q for q in prods if q != cur and ev_ok(q, e) is False]
    if bad:
        r[4] = bad[0].replace('/', '\\'); t5 = (r[0], bad[0].split('/')[-1]); break
wr(r14, hdr, rows)
rc6, f6, _ = gate(r14)
hit_c7 = any(re.search(r'\bC7\b', x) and 'C7c' not in x and 'C7d' not in x for x in f6)
chk('N5 col5 points at a non-satisfying product -> exit 1 via original C7',
    rc6 == 1 and hit_c7, 'id=%s->%s exit=%d C7=%s' % (t5[0], t5[1], rc6, hit_c7))
OUT['N5'] = {'id': t5[0], 'exit': rc6}
restore()

# ---------- 收口 ----------
rc7, f7, _ = gate(r14)
real_rc, _, _ = sh([sys.executable, os.path.join(REAL, GATE)])
real_sha = hashlib.sha256(io.open(os.path.join(REAL, ROWS_TSV), 'rb').read()).hexdigest()
OUT['real_rows_sha'] = real_sha
chk('Z1 restore -> sandbox exit 0 and real tree exit 0',
    rc7 == 0 and real_rc == 0, 'sb=%d real=%d real_sha=%s' % (rc7, real_rc, real_sha[:16]))

n = sum(1 for _, ok, _ in res if ok)
print('\n%d/%d PASS' % (n, len(res)))
OUT['summary'] = {'pass': n, 'total': len(res),
                  'results': [{'name': a, 'ok': b, 'detail': c} for a, b, c in res]}
io.open(os.path.join(ROOT, '_r134', 'r134b_controls.json'), 'w', encoding='utf-8').write(
    json.dumps(OUT, ensure_ascii=False, indent=1))
sys.exit(0 if n == len(res) else 1)
