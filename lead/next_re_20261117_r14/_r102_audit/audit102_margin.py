#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计 · 第三组：C12 边际鉴别力、非 ASCII 打印、未覆盖列、跨表蕴含。"""
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
    d = os.path.join(tempfile.gettempdir(), 'aud102c_' + tag)
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
    io.open(p, 'w', encoding='utf-8', newline='').write(
        '\n'.join('\t'.join(r) for r in rows) + '\n')


# ---------------------------------------------------------------- F1 跨表蕴含
def f1():
    """对每个冻结 id：冻结档校验式的命中行集合 是否 ⊇ DISC_RECHECK 同 id 校验式的命中行集合？
    若是，则「C7 该行通过」⇒「C12 该行通过」，C12 对该行零边际鉴别力。"""
    fz = {r[0]: r for r in (l.split('\t') for l in
                            io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l)}
    rc = {r[0]: r for r in (l.split('\t') for l in
                            io.open(RC, encoding='utf-8', newline='').read().split('\n')[1:] if l)}
    out = []

    def hitset(expr, txt):
        if not expr.startswith('grep='):
            return None
        pat = expr[len('grep='):].strip()
        return set(m.start() for m in re.finditer(pat, txt, re.M))

    for i in sorted(fz, key=int):
        f, r = fz[i], rc[i]
        p = os.path.join(TRUE, f[2].replace('\\', '/'))
        if not os.path.isfile(p):
            out.append({'id': i, 'status': 'PRODUCT_MISSING'})
            log('### F1 id=%-3s 产物缺失 %s' % (i, f[2]))
            continue
        txt = io.open(p, encoding='utf-8', errors='replace').read()
        fs = hitset(f[3], txt)
        rs = hitset(r[5], txt)
        if fs is None or rs is None:
            out.append({'id': i, 'status': 'NON_GREP', 'freeze': f[3], 'recheck': r[5]})
            log('### F1 id=%-3s 非 grep 分支，无法比蕴含' % i)
            continue
        sup = rs <= fs
        out.append({'id': i, 'freeze': f[3], 'recheck': r[5],
                    'freeze_hits': len(fs), 'recheck_hits': len(rs),
                    'recheck_implied_by_freeze': sup,
                    'freeze_weaker_or_equal': sup})
        log('### F1 id=%-3s 冻结锚命中=%-4d recheck锚命中=%-4d C7过⇒C12过=%s' %
            (i, len(fs), len(rs), sup))
        log('        冻结: %s' % f[3])
        log('        recheck: %s' % r[5])
    return out


# ---------------------------------------------------------------- F2 非 ASCII 打印 + GBK
def f2():
    out = {}
    # C12 的 FAIL 文本带中文（冻结档校验式原文）
    d = sb('f2c12')
    edit_fz(d, 5, 4, 'grep=复合条目的锚是并集ZZZ_NOMATCH')
    resign(d)
    rc, sout = run(d)
    fails = [l for l in sout.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
    log('### F2a C12 FAIL 文本 exit=%d' % rc)
    for l in fails:
        log('        ' + l)
    na = [b for b in sout if b > 127]
    log('### F2a stdout 非 ASCII 字节数=%d' % len(na))
    rc2, sout2 = run(d, env={'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'})
    log('### F2b 同场景 PYTHONIOENCODING=gbk exit=%d' % rc2)
    log(sout2.decode('utf-8', 'replace')[-1400:])
    out['c12_utf8'] = {'exit': rc, 'fails': fails, 'nonascii_bytes': len(na)}
    out['c12_gbk'] = {'exit': rc2, 'tail': sout2.decode('utf-8', 'replace')[-1200:]}
    # C7 同样（改前就有的行为，用来对照「新引入」还是「既有」）
    d2 = sb('f2c7')
    p = os.path.join(d2, 'DISC_RECHECK.tsv')
    rows = [l.split('\t') for l in io.open(p, encoding='utf-8', newline='').read().split('\n') if l]
    for r in rows[1:]:
        if r[0] == '5':
            r[5] = 'grep=复合条目的锚是并集ZZZ_NOMATCH'
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in rows) + '\n')
    rc3, sout3 = run(d2)
    fails3 = [l for l in sout3.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
    log('### F2c C7 FAIL 文本 exit=%d fails=%s' % (rc3, fails3))
    out['c7_utf8'] = {'exit': rc3, 'fails': fails3}
    # 全文件哪些 print 会带出数据里的中文
    src = io.open(GATE, encoding='utf-8').read()
    out['print_lines_with_nonascii_literal'] = [
        (i, l.strip()) for i, l in enumerate(src.split('\n'), 1)
        if re.search(r'print\(', l) and re.search(r'[^\x00-\x7f]', l)]
    log('### F2d print 行里含非 ASCII 的行: %s' % out['print_lines_with_nonascii_literal'])
    return out


# ---------------------------------------------------------------- F3 C12 未覆盖的列
def f3():
    out = {}
    cases = [(2, '§9.99', '节号改成不存在的节'),
             (3, r'lead\next_re_20261117_r14\NO_SUCH_FILE.md', '产物路径改成不存在文件'),
             (5, 'BOGUS_CATEGORY', '类别列改成非法值'),
             (8, 'MAYBE', '第8列改成非法值')]
    for col, val, desc in cases:
        d = sb('f3_%d' % col)
        edit_fz(d, 1, col, val)
        resign(d)
        rc, sout = run(d)
        fails = [l for l in sout.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
        log('### F3 冻结档 id1 第%d列=%r（%s）exit=%d fails=%s' % (col, val, desc, rc, fails))
        out['col%d' % col] = {'value': val, 'desc': desc, 'exit': rc, 'fails': fails}
    # 12 行冻结时刻全部同一秒 —— 是否合理？只报告事实
    ts = [l.split('\t')[6] for l in io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    log('### F3 冻结档 12 行时刻：去重后 %s' % sorted(set(ts)))
    out['timestamps'] = sorted(set(ts))
    return out


# ---------------------------------------------------------------- F4 C6MAX 是否可被 CLI 关掉
def f4():
    out = {}
    for a in ('--c6max=100000', '--c6max=9', '--c6max=8'):
        rc, sout = run(R14, a)
        log('### F4 check_disc.py %s -> exit=%d' % (a, rc))
        out[a] = rc
    # 是否存在把 --c6max 写死的调用点
    p = subprocess.run(['grep', '-rn', 'c6max', R14, '--include=*.py', '--include=*.sh',
                        '--include=*.md', '--include=*.json'],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    lines = [l for l in p.stdout.decode('utf-8', 'replace').split('\n')
             if l and 'R17_LEAD_BASELINE' not in l and '_r102_audit' not in l
             and '_r94/_audit' not in l and 'live_pin' not in l]
    log('### F4 c6max 提及（去备份/自审目录）%d 行:' % len(lines))
    for l in lines[:30]:
        log('        ' + l)
    out['mentions'] = lines
    return out


# ---------------------------------------------------------------- F5 谁真正执行门禁
def f5():
    pats = [r'subprocess\.\w+\([^\n]*check_disc', r'os\.system\([^\n]*check_disc',
            r'check_output\([^\n]*check_disc', r'Popen\([^\n]*check_disc',
            r'"check_disc\.py"', r"'check_disc\.py'"]
    out = []
    for root, dirs, files in os.walk(os.path.join(TRUE, 'lead')):
        dirs[:] = [d for d in dirs if d not in ('R17_LEAD_BASELINE', '__pycache__')]
        for fn in files:
            if not fn.endswith(('.py', '.sh', '.md', '.json', '.service')):
                continue
            p = os.path.join(root, fn)
            if os.path.getsize(p) > 3_000_000:
                continue
            try:
                txt = io.open(p, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            for pat in pats[:5]:
                for m in re.finditer(pat, txt):
                    ln = txt[:m.start()].count('\n') + 1
                    out.append('%s:%d: %s' % (os.path.relpath(p, TRUE), ln,
                                              txt.split('\n')[ln - 1].strip()[:120]))
    uniq = sorted(set(out))
    log('### F5 check_disc.py 的执行调用点（去重）%d 个:' % len(uniq))
    for l in uniq:
        log('        ' + l)
    return uniq


def main():
    res = {}
    res['F1_implication'] = f1()
    res['F2_nonascii'] = f2()
    res['F3_uncovered_cols'] = f3()
    res['F4_c6max'] = f4()
    res['F5_callers'] = f5()
    io.open(os.path.join(OUT, 'AUDIT102_margin.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, 'audit102_margin.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102_margin.json + audit102_margin.log')


if __name__ == '__main__':
    main()
