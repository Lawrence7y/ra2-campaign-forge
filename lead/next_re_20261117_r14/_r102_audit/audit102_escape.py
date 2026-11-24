#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计 · 第五组：run_expr 空格截断、冻结档当逃生门、C11 账目、删 C12 的组合。"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

TRUE = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(TRUE, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
RC = os.path.join(R14, 'DISC_RECHECK.tsv')
FZ = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
OUT = os.path.join(R14, '_r102_audit')
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def sb(tag):
    d = os.path.join(tempfile.gettempdir(), 'aud102e_' + tag)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, 'lead', 'next_re_20261117_r14'))
    for n in sorted(os.listdir(TRUE)):
        if n == 'lead':
            continue
        os.symlink(os.path.join(TRUE, n), os.path.join(d, n))
    os.symlink(os.path.join(TRUE, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(d, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    t = os.path.join(d, 'lead', 'next_re_20261117_r14')
    for n in sorted(os.listdir(R14)):
        if n in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', '__pycache__'):
            continue
        os.symlink(os.path.join(R14, n), os.path.join(t, n))
    for src, name in ((GATE, 'check_disc.py'), (RC, 'DISC_RECHECK.tsv'), (FZ, 'DISC_UNVERIFIABLE.tsv')):
        shutil.copyfile(src, os.path.join(t, name))
    return t


def run(d, *a, **kw):
    e = dict(os.environ)
    if 'env' in kw:
        e.update(kw['env'])
    p = subprocess.run([sys.executable, 'check_disc.py'] + list(a), cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def resign(d):
    p = os.path.join(d, 'check_disc.py')
    t = io.open(p, encoding='utf-8').read()
    t = re.sub(r"(?m)^FREEZE_SHA256\s*=\s*\S+.*$",
               "FREEZE_SHA256 = '%s'" % sha(os.path.join(d, 'DISC_UNVERIFIABLE.tsv')), t)
    io.open(p, 'w', encoding='utf-8', newline='').write(t)


def edit_fz(d, idwanted, col, val):
    p = os.path.join(d, 'DISC_UNVERIFIABLE.tsv')
    rows = [l.split('\t') for l in io.open(p, encoding='utf-8', newline='').read().split('\n') if l]
    hit = 0
    for r in rows[1:]:
        if r[0] == str(idwanted):
            r[col - 1] = val
            hit += 1
    assert hit == 1
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in rows) + '\n')


# ------------------------------------------------------------ H1 run_expr 空格截断
def h1():
    """head = expr.split(' ')[0] —— 含空格的模式被截断成第一段。
    构造：整条模式在产物里 0 命中，但第一段命中 => 门禁 PASS。"""
    out = {}
    # 冻结档 id 5 的产物是 R17_R64_ADEQUACY2/lead_recheck2.tsv
    prod = os.path.join(TRUE, 'lead', 'next_re_20261117_r14/R17_R64_ADEQUACY2/lead_recheck2.tsv')
    txt = io.open(prod, encoding='utf-8', errors='replace').read()
    full = r'复合条目的锚是并集 ZZZ_NOT_THERE'
    log('### H1 整条模式 %r 在产物中命中=%d' % (full, len(re.findall(full, txt, re.M))))
    log('### H1 截断后 head=%r 命中=%d' % (full.split(' ')[0], len(re.findall(full.split(' ')[0], txt, re.M))))
    d = sb('h1')
    edit_fz(d, 5, 4, 'grep=' + full)
    resign(d)
    rc, sout = run(d)
    fails = [l for l in sout.split('\n') if l.startswith('  FAIL')]
    note = [l for l in sout.split('\n') if 'C12' in l]
    log('### H1 冻结档 id5 校验式=%r -> exit=%d' % ('grep=' + full, rc))
    log('        NOTE %s' % note)
    log('        FAIL %s' % fails)
    out['space_truncation'] = {'exit': rc, 'fails': fails, 'note': note}
    # 同样打法用到 grepcount（含空格）
    full2 = r'ZZZ_A ZZZ_B=1'
    d2 = sb('h1b')
    edit_fz(d2, 5, 4, 'grepcount=' + full2)
    resign(d2)
    rc2, sout2 = run(d2)
    fails2 = [l for l in sout2.split('\n') if l.startswith('  FAIL')]
    log('### H1b 冻结档 id5 校验式=%r -> exit=%d fails=%s' % ('grepcount=' + full2, rc2, fails2))
    out['grepcount_space'] = {'exit': rc2, 'fails': fails2}
    return out


# ------------------------------------------------------------ H2 冻结档 = 逃生门
def h2():
    """把某行弄成 C11 FAIL（删掉它的自描述行），确认非冻结时 FAIL；
    再把它加进冻结档 + 重签 sha + 冻结档校验式保持命中 => C12 不阻止，门禁 exit 0。"""
    out = {}
    # 先算 C11 账目
    rows = [l.split('\t') for l in io.open(RC, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    fzids = set(int(l.split('\t')[0]) for l in io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l)
    you = [int(r[0]) for r in rows if r[6].strip().startswith('有')]
    wu = [int(r[0]) for r in rows if not r[6].strip().startswith('有')]
    log('### H2 claims-有 %d 个: %s' % (len(you), you))
    log('### H2 claims-无 %d 个: %s' % (len(wu), wu))
    log('### H2 冻结 id %d 个: %s ; 有∩冻结=%s ; 有−冻结=%s'
        % (len(fzids), sorted(fzids), sorted(set(you) & fzids), sorted(set(you) - fzids)))
    out['accounting'] = {'you': you, 'wu': wu, 'frozen': sorted(fzids)}
    # 选中 有−冻结 的一行（应当能被 C11 真判），删掉它产物里的自描述行 => C11 FAIL
    target = sorted(set(you) - fzids)[0]
    out['target'] = target
    r = [x for x in rows if int(x[0]) == target][0]
    prod = os.path.join(TRUE, r[4].replace('\\', '/'))
    log('### H2 目标 id=%d 产物=%s' % (target, r[4]))
    # 沙箱里把产物替换成一个不含自描述行的副本；先断掉目录级 symlink
    d = sb('h2a')
    root_a = os.path.dirname(os.path.dirname(d))
    rel = r[4].replace('\\', '/')
    parts = rel.split('/')
    dcur = root_a
    for p_ in parts[:-1]:
        nxt = os.path.join(dcur, p_)
        if os.path.islink(nxt):
            os.unlink(nxt)
            os.makedirs(nxt)
        dcur = nxt
    psand = os.path.join(root_a, rel)
    body = io.open(prod, encoding='utf-8', errors='replace').read()
    keep = '\n'.join(l for l in body.split('\n') if not l.startswith('DISC_RECHECK '))
    io.open(psand, 'w', encoding='utf-8', newline='').write(keep)
    rc, sout = run(d)
    f = [l for l in sout.split('\n') if l.startswith('  FAIL')]
    log('### H2a 非冻结行 %d 失去自描述行 -> exit=%d fails=%s' % (target, rc, f))
    out['nonfrozen_broken'] = {'exit': rc, 'fails': f}
    # H2b: 同一坏产物 + 把该行加进冻结档（产物/校验式沿用 DISC_RECHECK 的）+ 重签
    d2 = sb('h2b')
    root_b = os.path.dirname(os.path.dirname(d2))
    rel2 = r[4].replace('\\', '/')
    parts2 = rel2.split('/')
    dcur2 = root_b
    for p_ in parts2[:-1]:
        nxt = os.path.join(dcur2, p_)
        if os.path.islink(nxt):
            os.unlink(nxt)
            os.makedirs(nxt)
        dcur2 = nxt
    psand2 = os.path.join(root_b, rel2)
    io.open(psand2, 'w', encoding='utf-8', newline='').write(keep)
    p = os.path.join(d2, 'DISC_UNVERIFIABLE.tsv')
    txt = io.open(p, encoding='utf-8', newline='').read()
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt + '\t'.join([str(target), r[1], r[4], r[5], 'structurally_unverifiable',
                         '审计认为不可自产出', '2026-11-24T05:00:00+08:00', 'YES']) + '\n')
    resign(d2)
    rc2, sout2 = run(d2)
    f2 = [l for l in sout2.split('\n') if l.startswith('  FAIL')]
    log('### H2b 同一坏产物 + 加进冻结档 + 重签 -> exit=%d fails=%s' % (rc2, f2))
    out['frozen_escape'] = {'exit': rc2, 'fails': f2}
    note = [l for l in sout2.split('\n') if 'C11 col7' in l or 'C11 frozen' in l]
    log('        %s' % note)
    out['frozen_escape_notes'] = note
    return out


# ------------------------------------------------------------ H3 删 C12 + 删冻结档
def h3():
    out = {}
    src = io.open(GATE, encoding='utf-8').read()
    s = src.index('# ---- C12 ')
    e = src.index("notes.append('C12 frozen-anchor live-check:")
    e = src.index('\n', e) + 1
    chopped = src[:s] + src[e:]
    # a: 只删 C12
    d = sb('h3a')
    io.open(os.path.join(d, 'check_disc.py'), 'w', encoding='utf-8', newline='').write(chopped)
    rc, sout = run(d)
    log('### H3a 只删 C12（其余不动）exit=%d' % rc)
    out['drop_c12'] = rc
    # b: 删 C12 + 删冻结档
    d2 = sb('h3b')
    io.open(os.path.join(d2, 'check_disc.py'), 'w', encoding='utf-8', newline='').write(chopped)
    os.unlink(os.path.join(d2, 'DISC_UNVERIFIABLE.tsv'))
    rc2, sout2 = run(d2)
    f2 = [l for l in sout2.split('\n') if l.startswith('  FAIL')]
    log('### H3b 删 C12 + 删冻结档 exit=%d fails=%s' % (rc2, f2))
    out['drop_c12_and_freeze'] = {'exit': rc2, 'fails': f2}
    # c: 不删 C12，只删冻结档
    d3 = sb('h3c')
    os.unlink(os.path.join(d3, 'DISC_UNVERIFIABLE.tsv'))
    rc3, sout3 = run(d3)
    f3 = [l for l in sout3.split('\n') if l.startswith('  FAIL')]
    log('### H3c 只删冻结档（保留 C12）exit=%d fails=%s' % (rc3, f3))
    out['drop_freeze_only'] = {'exit': rc3, 'fails': f3}
    return out


# ------------------------------------------------------------ H4 docstring 前后对比
def h4():
    pre = io.open(os.path.join(R14, 'R17_LEAD_BASELINE',
                               'R102.before_check_disc_C12_20261124_042045.bak'),
                  encoding='utf-8').read().split('"""')[1]
    cur = io.open(GATE, encoding='utf-8').read().split('"""')[1]
    log('### H4 docstring 与改前完全相同 = %s' % (pre == cur))
    log('### H4 docstring 行数 pre=%d cur=%d' % (len(pre.split('\n')), len(cur.split('\n'))))
    # C10 doc 措辞 vs 代码注释
    for l in cur.split('\n'):
        if '字节数' in l or 'C10' in l:
            log('        DOC| ' + l)
    src = io.open(GATE, encoding='utf-8').read()
    for i, l in enumerate(src.split('\n'), 1):
        if '不用字节数' in l or 'C10 self row' in l or 'C10 no row' in l:
            log('        CODE:%d| %s' % (i, l.strip()))
    return {'doc_unchanged': pre == cur,
            'c10_doc_says_bytes': '字节数' in cur}


def main():
    res = {}
    res['H1_space_truncation'] = h1()
    res['H2_escape_hatch'] = h2()
    res['H3_delete_combos'] = h3()
    res['H4_doc'] = h4()
    io.open(os.path.join(OUT, 'AUDIT102_escape.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, 'audit102_escape.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102_escape.json + audit102_escape.log')


if __name__ == '__main__':
    main()
