#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计 · 第四组：run_expr 平凡锚漏洞、GBK 崩溃、120 阈值的来历、NOTE 计数。"""
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
    d = os.path.join(tempfile.gettempdir(), 'aud102d_' + tag)
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
    return p.returncode, p.stdout


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


# ------------------------------------------------------------------ G1 平凡锚
def g1():
    out = {}
    cases = [
        ('空 grep=', 'grep='),
        ('grep= 只有空格', 'grep= '),
        ('grep=.*', 'grep=.*'),
        ('grep=(?m)', 'grep=(?m)'),
        ('grep=^', 'grep=^'),
        ('grep=$', 'grep=$'),
        ('grep=a*', 'grep=a*'),
        ('grepcount=空模式=99999999 之外', 'grepcount=a*=1'),
        ('大小写不敏感空串锚', 'grep=(?i)'),
    ]
    for name, expr in cases:
        d = sb('g1_' + re.sub(r'[^A-Za-z0-9]+', '_', name))
        edit_fz(d, 1, 4, expr)
        resign(d)
        rc, sout = run(d)
        fails = [l for l in sout.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
        log('### G1 %-26s expr=%-24r exit=%d fails=%s' % (name, expr, rc, fails))
        out[name] = {'expr': expr, 'exit': rc, 'fails': fails}
    return out


# ------------------------------------------------------------------ G2 GBK 崩溃
def g2():
    out = {}
    # 用 GBK 不可编码字符 U+200B（正是纪律 20 讲的字符）
    for name, ch in (('U+200B', '​'), ('U+1F000', '\U0001F000'), ('U+FFFD', '�')):
        d = sb('g2_' + re.sub(r'[^A-Za-z0-9]+', '_', name))
        edit_fz(d, 1, 4, 'grep=ZZZ%sNOMATCH' % ch)
        resign(d)
        rc, sout = run(d)
        rc2, sout2 = run(d, env={'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'})
        t2 = sout2.decode('utf-8', 'replace')
        crash = 'UnicodeEncodeError' in t2 or 'Traceback' in t2
        tail = [l for l in t2.split('\n') if l.strip()][-4:]
        log('### G2 %-8s UTF-8 exit=%d ; GBK exit=%d crash=%s' % (name, rc, rc2, crash))
        for l in tail:
            log('        ' + l)
        out[name] = {'utf8_exit': rc, 'gbk_exit': rc2, 'gbk_crash': crash, 'gbk_tail': tail}
    # 对照：改前门禁（无 C12）+ 同样 U+200B 夹在 DISC_RECHECK 里（C7 路径）
    d = sb('g2_pre')
    p = os.path.join(d, 'DISC_RECHECK.tsv')
    rows = [l.split('\t') for l in io.open(p, encoding='utf-8', newline='').read().split('\n') if l]
    for r in rows[1:]:
        if r[0] == '5':
            r[5] = 'grep=ZZZ​NOMATCH'
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in rows) + '\n')
    rc3, sout3 = run(d, env={'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'})
    t3 = sout3.decode('utf-8', 'replace')
    log('### G2 对照 C7 路径(改前门禁不含 C12) + U+200B: GBK exit=%d crash=%s'
        % (rc3, ('UnicodeEncodeError' in t3 or 'Traceback' in t3)))
    for l in [l for l in t3.split('\n') if l.strip()][-4:]:
        log('        ' + l)
    out['control_c7_path'] = {'gbk_exit': rc3,
                              'gbk_crash': ('UnicodeEncodeError' in t3 or 'Traceback' in t3)}
    return out


# ------------------------------------------------------------------ G3 120 的来历
def g3():
    txt = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8').read()
    CANON = re.compile(r'(?:⇒\s*)?\*{0,2}纪律\s*(\d+)\s*·')
    LOOSE = re.compile(r'纪律\s*(\d+)')
    canon = len(CANON.findall(txt))
    loose = len(LOOSE.findall(txt))
    log('### G3 R14_COMMON 全库 CANON(纪律 N ·)=%d  LOOSE(纪律 N)=%d  LOOSE-CANON=%d'
        % (canon, loose, loose - canon))
    log('### G3 代码里 cross(compound-aware, 2.14+ 之外)=9')
    # 代码里 CANON/LOOSE 还剩谁在用
    src = io.open(GATE, encoding='utf-8').read()
    log('### G3 代码中 CANON 使用次数=%d LOOSE 使用次数=%d'
        % (len(re.findall(r'\bCANON\b', src)) - 1, len(re.findall(r'\bLOOSE\b', src)) - 1))
    return {'canon': canon, 'loose': loose, 'loose_minus_canon': loose - canon, 'cross_now': 9}


# ------------------------------------------------------------------ G4 C12 NOTE 计数口径
def g4():
    """C12 的 '12 frozen rows' 用的是 _frows[1:] 的长度，含非数据行；加一行注释看 NOTE 是否虚增。"""
    out = {}
    d = sb('g4')
    p = os.path.join(d, 'DISC_UNVERIFIABLE.tsv')
    txt = io.open(p, encoding='utf-8', newline='').read()
    io.open(p, 'w', encoding='utf-8', newline='').write(txt + '# 这是一行注释\n')
    resign(d)
    rc, sout = run(d)
    notes = [l for l in sout.decode('utf-8', 'replace').split('\n') if 'C12' in l]
    log('### G4 冻结档尾部加一行注释 -> exit=%d %s' % (rc, notes))
    out['comment_row'] = {'exit': rc, 'notes': notes}
    # 加一行「非数字 id」的数据行
    d2 = sb('g4b')
    p2 = os.path.join(d2, 'DISC_UNVERIFIABLE.tsv')
    txt2 = io.open(p2, encoding='utf-8', newline='').read()
    io.open(p2, 'w', encoding='utf-8', newline='').write(
        txt2 + 'X\t§2.14\tlead\\a.md\tgrep=ZZZ\tcat\tr\t2026-01-01T00:00:00+08:00\tNO\n')
    resign(d2)
    rc2, sout2 = run(d2)
    notes2 = [l for l in sout2.decode('utf-8', 'replace').split('\n') if 'C12' in l]
    log('### G4b 冻结档加一行 id=X（非法）-> exit=%d %s' % (rc2, notes2))
    out['nonnumeric_row'] = {'exit': rc2, 'notes': notes2}
    return out


# ------------------------------------------------------------------ G5 C7/C12 的 exists-无注解分支
def g5():
    """DISC_RECHECK 里 exists 分支：改成 exists 会不会 fail（证明存在但无注解 = FAIL，即该分支无「通过」路径）。"""
    out = {}
    d = sb('g5')
    p = os.path.join(d, 'DISC_RECHECK.tsv')
    rows = [l.split('\t') for l in io.open(p, encoding='utf-8', newline='').read().split('\n') if l]
    for r in rows[1:]:
        if r[0] == '5':
            r[5] = 'exists'
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in rows) + '\n')
    rc, sout = run(d)
    fails = [l for l in sout.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
    log('### G5 DISC_RECHECK id5 校验式=exists -> exit=%d fails=%s' % (rc, fails))
    out['exists_bare'] = {'exit': rc, 'fails': fails}
    # exists (N B) 形式
    d2 = sb('g5b')
    p2 = os.path.join(d2, 'DISC_RECHECK.tsv')
    rows2 = [l.split('\t') for l in io.open(p2, encoding='utf-8', newline='').read().split('\n') if l]
    for r in rows2[1:]:
        if r[0] == '5':
            r[5] = 'exists (123 B)'
    io.open(p2, 'w', encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in rows2) + '\n')
    rc2, sout2 = run(d2)
    fails2 = [l for l in sout2.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
    log('### G5b DISC_RECHECK id5 校验式=exists (123 B) -> exit=%d fails=%s' % (rc2, fails2))
    out['exists_with_size'] = {'exit': rc2, 'fails': fails2}
    return out


def main():
    res = {}
    res['G1_tautology'] = g1()
    res['G2_gbk'] = g2()
    res['G3_threshold_origin'] = g3()
    res['G4_note_count'] = g4()
    res['G5_exists_branch'] = g5()
    io.open(os.path.join(OUT, 'AUDIT102_probe.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, 'audit102_probe.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102_probe.json + audit102_probe.log')


if __name__ == '__main__':
    main()
