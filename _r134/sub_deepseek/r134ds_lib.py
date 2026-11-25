# -*- coding: utf-8 -*-
"""r134ds_lib.py -- executor helpers for R134 C7/C7b verification.

Sandbox = symlink farm.  NOT copytree (R133 lost a control run: 811 MB into tmpfs).
Only check_disc.py and DISC_RECHECK.tsv are real copies; everything else is a symlink
into the real tree.  ROOT inside the sandbox is derived by the gate itself from
dirname(dirname(dirname(__file__))), so the layout must be <sb>/lead/next_re_20261117_r14/.
"""
import io, os, re, shutil, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
REAL = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
HERE = os.path.join(ROOT, '_r134', 'sub_deepseek')
SNAP = os.path.join(HERE, 'snap')
TSV = 'DISC_RECHECK.tsv'
GATE_TIMEOUT = 600


def build_sandbox(tag, gate_src, tsv_src=None):
    """tag: sandbox dir name.  gate_src/tsv_src: absolute paths of REAL files to copy in."""
    sb = os.path.join(HERE, 'sb_' + tag)
    if os.path.isdir(sb) or os.path.islink(sb):
        shutil.rmtree(sb) if not os.path.islink(sb) else os.remove(sb)
    r14 = os.path.join(sb, 'lead', 'next_re_20261117_r14')
    os.makedirs(r14)
    n_link = 0
    for name in os.listdir(REAL):
        if name in ('check_disc.py', TSV):
            continue
        try:
            os.symlink(os.path.join(REAL, name), os.path.join(r14, name))
            n_link += 1
        except OSError:
            pass
    os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(sb, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    os.symlink(os.path.join(ROOT, '_r94'), os.path.join(sb, '_r94'))
    shutil.copy2(gate_src, os.path.join(r14, 'check_disc.py'))
    shutil.copy2(tsv_src or os.path.join(REAL, TSV), os.path.join(r14, TSV))
    return r14


def gate(r14, timeout=GATE_TIMEOUT):
    """Run the sandbox gate.  Returns (rc, fails, notes, stdout).  rc is MEASURED."""
    try:
        p = subprocess.run([sys.executable, os.path.join(r14, 'check_disc.py')],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ('TIMEOUT', [], [], 'timeout after %ds' % timeout)
    out = p.stdout + p.stderr
    fails = [l.strip() for l in out.split('\n') if l.strip().startswith('FAIL')]
    notes = [l.strip() for l in out.split('\n') if l.strip().startswith('NOTE')]
    return p.returncode, fails, notes, out


def read_rows(r14):
    txt = io.open(os.path.join(r14, TSV), encoding='utf-8', newline='').read()
    assert '\r' not in txt, 'CR in TSV'
    lines = [l for l in txt.split('\n') if l]
    return lines[0], [l.split('\t') for l in lines[1:]]


def write_rows(r14, hdr, rows):
    txt = hdr + '\n' + '\n'.join('\t'.join(r) for r in rows) + '\n'
    io.open(os.path.join(r14, TSV), 'w', encoding='utf-8', newline='').write(txt)


def all_paths(rows):
    return sorted(set(r[4].strip().replace('\\', '/') for r in rows if len(r) == 7))


# ---- faithful mirror of gate run_expr (same file, same decode, same re.M) ----
def run_expr(path, expr):
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False, 'FILE_MISSING'
    head = expr.split(' ')[0]
    cache = {}

    def get_txt():
        if 't' not in cache:
            cache['t'] = io.open(ap, encoding='utf-8', errors='replace').read()
        return cache['t']

    if head.startswith('grep='):
        pat = expr[len('grep='):].strip()
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n >= 1), 'grep hits=%d' % n
    if head.startswith('grepcount='):
        rest = expr[len('grepcount='):].strip()
        m0 = re.match(r'^(.*)=(\d+)$', rest, re.S)
        if not m0:
            return False, 'BAD_GREPCOUNT'
        pat, want = m0.group(1), int(m0.group(2))
        try:
            n = len(re.findall(pat, get_txt(), re.M))
        except re.error as e:
            return False, 'BAD_REGEX:%s' % e
        return (n == want), 'grepcount %d vs %d' % (n, want)
    m = re.search(r'[\(（](\d+)\s*B[\)）]', expr)
    if head == 'exists':
        if m:
            return (os.path.getsize(ap) == int(m.group(1))), 'exists'
        return False, 'exists-without-size-annotation'
    m2 = re.fullmatch(r'bytes=(\d+)', head)
    if m2:
        return (os.path.getsize(ap) == int(m2.group(1))), 'bytes'
    m3 = re.fullmatch(r'rows=(\d+)', head)
    if m3:
        n = 0
        hdr_seen = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for ln in f:
                s = ln.strip()
                if s.startswith('DISC_RECHECK '):
                    continue
                if hdr_seen == 0:
                    hdr_seen = 1
                    continue
                n += 1
        return (n == int(m3.group(1))), 'rows=%d' % n
    if head == 'none':
        return None, 'none'
    return False, 'BAD_EXPR:' + head


def hit_count(path, expr):
    """number of regex hits (grep= / grepcount=), else None"""
    ap = os.path.join(ROOT, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return None
    e = expr.strip()
    if e.startswith('grep='):
        pat = e[len('grep='):].strip()
    elif e.startswith('grepcount='):
        m = re.fullmatch(r'grepcount=(.*)=(\d+)$', e, re.S)
        pat = m.group(1) if m else None
    else:
        return None
    if pat is None:
        return None
    t = io.open(ap, encoding='utf-8', errors='replace').read()
    try:
        return len(re.findall(pat, t, re.M))
    except re.error:
        return None
