#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sbxlib.py —— R103 共用沙箱：真树只读，可变文件复制到 /tmp，其余 symlink。

复制（可被变异）：
  lead/next_re_20261117_r14/{check_disc.py, DISC_RECHECK.tsv, DISC_UNVERIFIABLE.tsv, R14_COMMON.md}
其余一律 symlink 到真树。R14_COMMON.md 必须复制：冻结档 id 1/2/9 的产物就是它，
要测「给冻结行补一条合法自述行会不会被抓」就必须能往它里面追加而不碰真身。
"""
import hashlib, io, os, shutil, subprocess, sys

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
SBX = '/tmp/r103_sbx'
COPY = ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'R14_COMMON.md')


def _product_rels():
    """DISC_RECHECK.tsv 第 5 列引用的全部产物（去重），相对 real 根。"""
    t = io.open(os.path.join(REAL, R14REL, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read()
    out = set()
    for l in t.split('\n')[1:]:
        c = l.split('\t')
        if len(c) == 7 and c[4].strip():
            out.add(c[4].strip().replace('\\', '/'))
    return sorted(out)


PRODUCTS = _product_rels()


def escape_path(path):
    """返回「路径上第一个是指向真树的 symlink 的那一段」；全实体则返回 None。

    R103 事故的真正机制：产物文件本身不是 symlink，但它的**父目录**是（沙箱只 symlink 了目录）。
    os.path.islink(文件) 因此返回 False —— 只查末端是不足以拦住的，必须逐段查。
    """
    ap = os.path.abspath(path)
    parts = ap.split(os.sep)
    cur = os.sep
    for comp in parts:
        if not comp:
            continue
        cur = os.path.join(cur, comp)
        if os.path.islink(cur):
            return cur
    return None


def guard_write(path):
    """写前守卫：R103 事故教训——沙箱里只要有一段 symlink，写它就等于写真树。
    任何脚本在写之前都必须调本函数；路径上若有 symlink 立刻抛错并中止。"""
    esc = escape_path(path)
    if esc:
        raise RuntimeError('REFUSE: %s resolves through symlink %s into the real tree '
                           '(R103 incident)' % (path, esc))
    return path

def build(sbx=SBX, extra_copy=()):
    if os.path.isdir(sbx):
        shutil.rmtree(sbx)
    os.makedirs(sbx)
    for e in os.listdir(REAL):
        if e == 'lead':
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(sbx, e))
    os.makedirs(os.path.join(sbx, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e == 'next_re_20261117_r14':
            continue
        os.symlink(os.path.join(REAL, 'lead', e), os.path.join(sbx, 'lead', e))
    os.makedirs(os.path.join(sbx, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        s = os.path.join(REAL, R14REL, e)
        d = os.path.join(sbx, R14REL, e)
        if e in COPY or e in extra_copy:
            shutil.copy2(s, d)
        else:
            os.symlink(s, d)
    return sbx

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

UNPATCHED_GATE = None
UNPATCHED_DR = None


def _find_unpatched():
    """R103 落盘前的门禁/表配对（备份在 R17_LEAD_BASELINE）。

    历史事实（「补丁前门禁看不见第 2/3/4 列」）必须用**补丁前**的门禁量，否则脚本会随
    盘上门禁变化而自我失效 —— 本文件第一次跑完就撞上这一点（期望 31/31 全 FAIL）。
    """
    import glob
    base = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
    g = sorted(glob.glob(os.path.join(base, 'R103.before_check_disc_C13C14C15_*.bak')))
    d = sorted(glob.glob(os.path.join(base, 'R103.before_DISC_RECHECK_ver_*.bak')))
    return (io.open(g[-1], encoding='utf-8', newline='').read() if g else None,
            io.open(d[-1], encoding='utf-8', newline='').read() if d else None)


def prepare(extra=(), gate='patched'):
    """建沙箱并实体化产物。gate='unpatched' 时装入 R103 落盘前的门禁/表配对。"""
    build()
    for rel in list(PRODUCTS) + list(extra):
        materialize(rel)
    if gate == 'unpatched':
        global UNPATCHED_GATE, UNPATCHED_DR
        if UNPATCHED_GATE is None:
            UNPATCHED_GATE, UNPATCHED_DR = _find_unpatched()
        assert UNPATCHED_GATE and UNPATCHED_DR, 'unpatched pair missing'
        g = p(SBX, 'check_disc.py')
        d = p(SBX, 'DISC_RECHECK.tsv')
        io.open(g, 'w', encoding='utf-8', newline='').write(UNPATCHED_GATE)
        io.open(d, 'w', encoding='utf-8', newline='').write(UNPATCHED_DR)
    return SBX


def prepare_old():
    """建沙箱 + 把全部产物与额外可变文件实体化。返回沙箱根。"""
    build()
    for rel in list(PRODUCTS) + list(extra):
        materialize(rel)
    return SBX


def run(sbx=SBX, *args):
    g = os.path.join(sbx, R14REL, 'check_disc.py')
    p = subprocess.run([sys.executable, g] + list(args), capture_output=True,
                       text=True, cwd=sbx, env=ENV)
    fails = [l.strip()[6:] for l in p.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    return p.returncode, fails, p.stdout

def p(sbx, rel):
    return os.path.join(sbx, R14REL, rel)

def rows(sbx=SBX, with_header=False):
    """返回 DISC_RECHECK.tsv 的正文行（默认跳过表头）。"""
    t = io.open(p(sbx, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read()
    body = [l.split('\t') for l in t.split('\n') if l]
    return (body if with_header else body[1:]), t

def write_rows(rs, t, sbx=SBX):
    """把正文行写回（自动保留原表头行、LF-only 性质与末尾换行）。"""
    nl = t.endswith('\n')
    hdr = t.split('\n')[0]
    body = hdr + '\n' + '\n'.join('\t'.join(r) for r in rs) + ('\n' if nl else '')
    io.open(p(sbx, 'DISC_RECHECK.tsv'), 'w', encoding='utf-8', newline='').write(body)

def materialize(rel, sbx=SBX):
    """把 sbx 里的 rel 变成**实体文件**：沿途目录从 symlink 展开成实体目录 + 逐项 symlink，
    末端文件复制。这是 R103 事故（写穿透 symlink 改写真树）的结构性修复。"""
    parts = rel.split('/')
    cur_sbx = sbx
    cur_real = REAL
    for comp in parts[:-1]:
        cur_sbx = os.path.join(cur_sbx, comp)
        cur_real = os.path.join(cur_real, comp)
        if os.path.islink(cur_sbx):
            os.unlink(cur_sbx)
            os.makedirs(cur_sbx)
            for e in os.listdir(cur_real):
                if os.path.join(comp, e) in [os.path.dirname(r) for r in PRODUCTS] or True:
                    pass
            for e in os.listdir(cur_real):
                os.symlink(os.path.join(cur_real, e), os.path.join(cur_sbx, e))
        elif not os.path.isdir(cur_sbx):
            os.makedirs(cur_sbx)
    dst = os.path.join(sbx, rel)
    src = os.path.join(REAL, rel)
    if os.path.islink(dst):
        os.unlink(dst)
    if os.path.isfile(src):
        shutil.copy2(src, dst)
    return dst


def real_dr():
    return io.open(p(REAL, 'DISC_RECHECK.tsv'), encoding='utf-8', newline='').read()

def sha(b):
    return hashlib.sha256(b).hexdigest()
