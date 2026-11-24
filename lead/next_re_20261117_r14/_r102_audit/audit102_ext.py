#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计 · 第二组实验：锚的鉴别力、非 ASCII 打印、delete-detection、cross 分布。"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

TRUE = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(TRUE, 'lead', 'next_re_20261117_r14')
BAK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
RC = os.path.join(R14, 'DISC_RECHECK.tsv')
FZ = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
PRE_C12 = os.path.join(BAK, 'R102.before_check_disc_C12_20261124_042045.bak')
PRE_VER = os.path.join(BAK, 'R102.before_DISC_RECHECK_ver_bump_20261124_042045.bak')
OUT = os.path.join(R14, '_r102_audit')
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def sb(tag, gate=GATE, rc=RC, fz=FZ):
    d = os.path.join(tempfile.gettempdir(), 'aud102b_' + tag)
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
    for src, name in ((gate, 'check_disc.py'), (rc, 'DISC_RECHECK.tsv'), (fz, 'DISC_UNVERIFIABLE.tsv')):
        shutil.copyfile(src, os.path.join(t, name))
    return t


def run(d, *a, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, 'check_disc.py'] + list(a), cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    return p.returncode, p.stdout


def resign(d):
    """把沙箱内 FREEZE_SHA256 改成沙箱冻结档的 sha。"""
    p = os.path.join(d, 'check_disc.py')
    t = io.open(p, encoding='utf-8').read()
    t = re.sub(r"(?m)^FREEZE_SHA256\s*=\s*\S+.*$",
               "FREEZE_SHA256 = '%s'" % sha(os.path.join(d, 'DISC_UNVERIFIABLE.tsv')), t)
    io.open(p, 'w', encoding='utf-8', newline='').write(t)


def edit_fz(d, fn):
    p = os.path.join(d, 'DISC_UNVERIFIABLE.tsv')
    rows = [l.split('\t') for l in io.open(p, encoding='utf-8', newline='').read().split('\n') if l]
    head, body = rows[0], rows[1:]
    fn(body)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        '\n'.join(['\t'.join(r) for r in [head] + body]) + '\n')


# ---------------------------------------------------------------- E1 锚的鉴别力
def e1():
    """对冻结档 12 行的 grep= 锚，统计在各自产物里的命中次数。
    命中次数 >> 1 表示该锚不能区分「这一条纪律」与「任意别的纪律」。"""
    fz = [l.split('\t') for l in io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    rows = []
    for c in fz:
        p = os.path.join(TRUE, c[2].replace('\\', '/'))
        expr = c[3]
        head = expr.split(' ')[0]
        txt = io.open(p, encoding='utf-8', errors='replace').read()
        if head.startswith('grep='):
            pat = expr[len('grep='):].strip()
            n = len(re.findall(pat, txt, re.M))
        else:
            n = None
        rows.append({'id': c[0], 'file': c[2], 'expr': expr, 'hits': n})
        log('### E1 id=%-3s hits=%-5s expr=%s' % (c[0], n, expr))
    # 对照：把同一个锚套到「别的纪律」上是否也能命中（证明非特指）
    return rows


def e1_specificity():
    """把冻结档锚移到另一个产物上，看是否仍然命中——若命中，锚不绑定具体主张。"""
    fz = [l.split('\t') for l in io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    txt_rc = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8').read()
    out = []
    for c in fz:
        expr = c[3]
        if not expr.startswith('grep='):
            continue
        pat = expr[len('grep='):].strip()
        try:
            n = len(re.findall(pat, txt_rc, re.M))
        except re.error:
            n = 'BAD'
        out.append({'id': c[0], 'expr': expr, 'hits_in_R14_COMMON': n})
        log('### E1b id=%-3s 同一锚在 R14_COMMON 命中=%s (expr=%s)' % (c[0], n, expr))
    return out


# ---------------------------------------------------------------- E2 非 ASCII 打印
def e2():
    """C12 的 FAIL 文本会把冻结档校验式原样打进 stdout；docstring 第 20 行声称不使用非 ASCII 打印。"""
    d = sb('e2')
    def f(body):
        for r in body:
            if r[0] == '4':
                r[3] = 'grep=复合条目ZZZ不命中'
    edit_fz(d, f)
    resign(d)
    rc, out = run(d)
    nonascii = [b for b in out if b > 127]
    log('### E2 坏锚(含中文) exit=%d stdout 非ASCII字节数=%d' % (rc, len(nonascii)))
    log(out.decode('utf-8', 'replace'))
    # 模拟 GBK 控制台
    rc2, out2 = run(d, env={'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'})
    log('### E2b PYTHONIOENCODING=gbk 下 exit=%d' % rc2)
    log(out2.decode('utf-8', 'replace')[-1200:])
    return {'utf8_exit': rc, 'nonascii_bytes': len(nonascii),
            'gbk_exit': rc2, 'gbk_tail': out2.decode('utf-8', 'replace')[-800:]}


# ---------------------------------------------------------------- E3 sha 未同步 vs 已同步（改前门禁）
def e3():
    out = {}
    # a: 改前门禁 + 坏锚 + sha 未同步 -> 期望 C11 TAMPERED
    d = sb('e3a', gate=PRE_C12, rc=PRE_VER)
    def f(body):
        for r in body:
            if r[0] == '1':
                r[3] = 'grep=ZZZ_9f3a'
    edit_fz(d, f)
    rc, sout = run(d)
    log('### E3a 改前门禁 + 坏锚 + sha未同步 exit=%d' % rc)
    log(sout.decode('utf-8', 'replace'))
    out['pre_bad_anchor_sha_stale'] = {'exit': rc, 'stdout': sout.decode('utf-8', 'replace')}
    # b: 改前门禁 + 坏锚 + sha已同步 -> 期望 exit 0（C12 之前无鉴别力）
    resign(d)
    rc2, sout2 = run(d)
    log('### E3b 改前门禁 + 坏锚 + sha已同步 exit=%d' % rc2)
    log(sout2.decode('utf-8', 'replace'))
    out['pre_bad_anchor_sha_synced'] = {'exit': rc2, 'stdout': sout2.decode('utf-8', 'replace')}
    return out


# ---------------------------------------------------------------- E4 删/改自身检查是否被抓
def e4():
    out = {}
    src = io.open(GATE, encoding='utf-8').read()
    variants = {}
    # v1 删整段 C12，GATE_VER 不变
    s = src.index('# ---- C12 ')
    e = src.index("notes.append('C12 frozen-anchor live-check:")
    e = src.index('\n', e) + 1
    variants['v1_drop_C12'] = src[:s] + src[e:]
    # v2 删整段 C6 阈值接线
    s = src.index('# ---- C6 阈值')
    e = src.index("notes.append('C6 threshold ok")
    e = src.index('\n', e) + 1
    variants['v2_drop_C6MAX'] = src[:s] + src[e:]
    # v3 C12 里只把 fail 改成 notes（等效于关掉判定）
    variants['v3_neuter_C12'] = src.replace(
        "            if _ok is not True:\n                fails.append('%s frozen anchor does not hold",
        "            if False:\n                fails.append('%s frozen anchor does not hold")
    # v4 C6MAX 判定改成恒真
    variants['v4_neuter_C6MAX'] = src.replace('if cross > C6MAX:', 'if False:')
    for name, text in variants.items():
        assert text != src, name
        d = sb('e4_' + name, gate=GATE)
        io.open(os.path.join(d, 'check_disc.py'), 'w', encoding='utf-8', newline='').write(text)
        resign(d)
        rc, sout = run(d)
        log('### E4 %-16s exit=%d  banner=%s' %
            (name, rc, [l for l in sout.decode('utf-8', 'replace').split('\n') if 'check_disc.py (' in l]))
        out[name] = {'exit': rc}
    return out


# ---------------------------------------------------------------- E5 cross 分布
def e5():
    txt = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8').read()
    lines = txt.split('\n')
    cur, sec, REF = None, [], re.compile(r'纪律\s*(\d+(?:\s*/\s*\d+)*)')
    for l in lines:
        m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
        if m:
            cur = m.group(1)
        sec.append(cur)
    hits = []
    for i, l in enumerate(lines):
        c = sec[i]
        mine = bool(c) and c.startswith('2.') and float(c.split('.')[1]) >= 14 if c else False
        if mine:
            continue
        for m in REF.finditer(l):
            if re.search(r'纪律\s*19\s*条', l):
                continue
            hits.append((c, m.group(1), len(re.split(r'\s*/\s*', m.group(1)))))
    from collections import Counter
    log('### E5 cross 明细（section, 引用, 计几个号）:')
    for h in hits:
        log('        %s' % (h,))
    log('### E5 cross 总计=%d 按 section: %s' % (sum(h[2] for h in hits), dict(Counter(h[0] for h in hits))))
    return {'hits': hits, 'total': sum(h[2] for h in hits),
            'by_section': dict(Counter(h[0] for h in hits))}


# ---------------------------------------------------------------- E6 C12 是否覆盖「冻结档第 8 列」
def e6():
    """C12 不读第 8 列（冻结时是否已声称有）。把它改成 NO/GARBAGE 是否仍 exit 0。"""
    out = {}
    for val in ('NO', 'GARBAGE', ''):
        d = sb('e6_' + (val or 'empty'))
        def f(body):
            for r in body:
                if r[0] == '1':
                    r[7] = val
        edit_fz(d, f)
        resign(d)
        rc, sout = run(d)
        fails = [l for l in sout.decode('utf-8', 'replace').split('\n') if l.startswith('  FAIL')]
        log('### E6 冻结档第8列=%r exit=%d fails=%s' % (val, rc, fails))
        out[repr(val)] = {'exit': rc, 'fails': fails}
    return out


# ---------------------------------------------------------------- E7 冻结档与 DISC_RECHECK 交叉同一性
def e7():
    """冻结档第 2/3/4 列与 DISC_RECHECK 同 id 行的第 2/5/6 列是否必须一致？C12 未要求。"""
    fz = [l.split('\t') for l in io.open(FZ, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    rcrows = [l.split('\t') for l in io.open(RC, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    rcm = {r[0]: r for r in rcrows}
    out = []
    for c in fz:
        r = rcm[c[0]]
        same_sec = c[1] == r[1]
        same_path = c[2].replace('\\', '/') == r[4].replace('\\', '/')
        same_expr = c[3] == r[5]
        out.append({'id': c[0], 'same_section': same_sec, 'same_path': same_path, 'same_expr': same_expr})
        log('### E7 id=%-3s 节相同=%s 产物相同=%s 校验式相同=%s' %
            (c[0], same_sec, same_path, same_expr))
    return out


# ---------------------------------------------------------------- E8 runs
def e8():
    """谁在跑 check_disc.py？有没有人传 --c6max？"""
    p = subprocess.run(['grep', '-rn', '--include=*.py', '--include=*.sh', '-e', 'check_disc.py',
                        '-e', 'c6max', R14, os.path.join(TRUE, 'tools'), os.path.join(TRUE, 'lead')],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    lines = [l for l in p.stdout.decode('utf-8', 'replace').split('\n') if l]
    keep = [l for l in lines if '_r102' not in l and 'R17_LEAD_BASELINE' not in l]
    log('### E8 调用点/提及（去掉 baseline 与 _r102）：共 %d 行' % len(keep))
    for l in keep[:40]:
        log('        ' + l)
    return keep


def main():
    res = {}
    res['E1_anchor_hits'] = e1()
    res['E1b_specificity'] = e1_specificity()
    res['E2_nonascii'] = e2()
    res['E3_pre_gate'] = e3()
    res['E4_selfdelete'] = e4()
    res['E5_cross'] = e5()
    res['E6_col8'] = e6()
    res['E7_freeze_vs_recheck'] = e7()
    res['E8_callers'] = e8()
    io.open(os.path.join(OUT, 'AUDIT102_ext.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, 'audit102_ext.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102_ext.json + audit102_ext.log')


if __name__ == '__main__':
    main()
