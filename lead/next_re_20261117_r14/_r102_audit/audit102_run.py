#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计：证伪主会话的「纯加严」声明。
只读真树（symlink），所有变更落在 /tmp。产物：AUDIT102.json / audit102.log
"""
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TRUE = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(TRUE, 'lead', 'next_re_20261117_r14')
BAK = os.path.join(R14, 'R17_LEAD_BASELINE')

GATE_NOW = os.path.join(R14, 'check_disc.py')
RC_NOW = os.path.join(R14, 'DISC_RECHECK.tsv')
FZ_NOW = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
GATE_PRE_C12 = os.path.join(BAK, 'R102.before_check_disc_C12_20261124_042045.bak')
RC_PRE_VERBUMP = os.path.join(BAK, 'R102.before_DISC_RECHECK_ver_bump_20261124_042045.bak')

LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def build_sandbox(tag, gate_src=GATE_NOW, rc_src=RC_NOW, fz_src=FZ_NOW):
    d = os.path.join(tempfile.gettempdir(), 'aud102_' + tag)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, 'lead', 'next_re_20261117_r14'))
    # 根级条目 symlink
    for name in sorted(os.listdir(TRUE)):
        src = os.path.join(TRUE, name)
        if name == 'lead':
            continue
        os.symlink(src, os.path.join(d, name))
    os.symlink(os.path.join(TRUE, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
               os.path.join(d, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    tgt = os.path.join(d, 'lead', 'next_re_20261117_r14')
    for name in sorted(os.listdir(R14)):
        if name in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', '__pycache__'):
            continue
        os.symlink(os.path.join(R14, name), os.path.join(tgt, name))
    shutil.copyfile(gate_src, os.path.join(tgt, 'check_disc.py'))
    shutil.copyfile(rc_src, os.path.join(tgt, 'DISC_RECHECK.tsv'))
    shutil.copyfile(fz_src, os.path.join(tgt, 'DISC_UNVERIFIABLE.tsv'))
    return tgt


def run_gate(d, *args):
    p = subprocess.run([sys.executable, 'check_disc.py'] + list(args), cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def set_const(path, const, newval):
    txt = io.open(path, encoding='utf-8').read()
    txt2, n = re.subn(r'(%s\s*=\s*)%s' % (re.escape(const), re.escape(repr(newval))),
                      lambda m: m.group(1) + repr(newval), txt)
    if n != 1:
        # 常量值未知，按名字替换整行
        txt2, n = re.subn(r'(?m)^(%s\s*=\s*)\S.*$' % re.escape(const),
                          lambda m: m.group(1) + repr(newval), txt)
    assert n == 1, (const, n)
    io.open(path, 'w', encoding='utf-8', newline='').write(txt2)


def rewrite_freeze_row(fz_path, gate_path, idwanted, col4=None, col2=None, col6=None,
                       col7=None, drop=False, add_raw=None):
    """改冻结档某行指定列，并把 FREEZE_SHA256 常量同步成新 sha（模拟「改锚+同改常量」）。
    col 编号：1=id 2=节 3=产物 4=校验式 5=类别 6=理由 7=冻结时刻 8=声称"""
    lines = io.open(fz_path, encoding='utf-8', newline='').read().split('\n')
    head, body = lines[0], [l for l in lines[1:] if l]
    out = []
    hit = 0
    for l in body:
        c = l.split('\t')
        if c and c[0].strip() == str(idwanted):
            hit += 1
            if drop:
                continue
            if col2 is not None:
                c[2] = col2
            if col4 is not None:
                c[3] = col4
            if col6 is not None:
                c[5] = col6
            if col7 is not None:
                c[6] = col7
            l = '\t'.join(c)
        out.append(l)
    assert hit == 1, ('freeze row hit', hit)
    if add_raw:
        out.append(add_raw)
    io.open(fz_path, 'w', encoding='utf-8', newline='').write('\n'.join([head] + out) + '\n')
    set_const(gate_path, 'FREEZE_SHA256', sha(fz_path))
    return sha(fz_path)


# ------------------------------------------------------------------ A1
def a1():
    rc, out = run_gate(R14)
    log('### A1 真门禁 exit=%d' % rc)
    log(out)
    lines = {k: [l for l in out.split('\n') if k in l] for k in
             ('C12', 'C6 threshold', 'check_disc.py (', 'C10')}
    return {'exit': rc, 'stdout': out, 'picked': lines}


# ------------------------------------------------------------------ A2
def a2():
    res = {}
    # 正控：坏冻结档 + 同步 FREEZE_SHA256，跑「改后」门禁
    d = build_sandbox('a2_new')
    newsha = rewrite_freeze_row(os.path.join(d, 'DISC_UNVERIFIABLE.tsv'),
                                os.path.join(d, 'check_disc.py'), 1,
                                col4=r'grep=ZZZ_NOT_PRESENT_9f3a')
    rc, out = run_gate(d)
    log('### A2 正控(改后门禁 + 坏锚 + 同步sha) exit=%d sha=%s' % (rc, newsha[:16]))
    log(out)
    res['new_gate_bad_anchor'] = {'exit': rc, 'stdout': out}
    # 反控：同一坏冻结档 + 同步 sha，跑「改前」门禁（GATE_VER=R87 + 版本号未抬的 recheck）
    d2 = build_sandbox('a2_pre', gate_src=GATE_PRE_C12, rc_src=RC_PRE_VERBUMP)
    rewrite_freeze_row(os.path.join(d2, 'DISC_UNVERIFIABLE.tsv'),
                       os.path.join(d2, 'check_disc.py'), 1,
                       col4=r'grep=ZZZ_NOT_PRESENT_9f3a')
    # 改前门禁无 C12，故意不再回写 sha：先测「sha 未同步」是否会被 C11 抓
    rc0, out0 = run_gate(d2)
    log('### A2 反控a(改前门禁 + 坏锚 + sha未同步) exit=%d' % rc0)
    log(out0)
    res['pre_gate_bad_anchor_sha_stale'] = {'exit': rc0, 'stdout': out0}
    # 反控 b：再把 sha 同步（改前门禁常量也叫 FREEZE_SHA256）
    set_const(os.path.join(d2, 'check_disc.py'), 'FREEZE_SHA256',
              sha(os.path.join(d2, 'DISC_UNVERIFIABLE.tsv')))
    rc1, out1 = run_gate(d2)
    log('### A2 反控b(改前门禁 + 坏锚 + 同步sha) exit=%d' % rc1)
    log(out1)
    res['pre_gate_bad_anchor_sha_synced'] = {'exit': rc1, 'stdout': out1}
    return res


# ------------------------------------------------------------------ A3
def a3():
    """run_expr 四分支对着冻结档 12 行 / DISC_RECHECK 31 行过一遍。"""
    src = io.open(GATE_NOW, encoding='utf-8').read()
    tree = ast.parse(src)
    fz = [l.split('\t') for l in io.open(FZ_NOW, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    rc_rows = [l.split('\t') for l in io.open(RC_NOW, encoding='utf-8', newline='').read().split('\n')[1:] if l]

    def branch(expr):
        head = expr.split(' ')[0]
        if head.startswith('grep='):
            return 'grep='
        if head.startswith('grepcount='):
            return 'grepcount='
        if head == 'exists':
            return 'exists'
        if re.fullmatch(r'bytes=(\d+)', head):
            return 'bytes=N'
        if re.fullmatch(r'rows=(\d+)', head):
            return 'rows=N'
        if head == 'none':
            return 'none'
        return 'BAD_EXPR'

    fzb = [(r[0], branch(r[3])) for r in fz]
    rcb = [(r[0], branch(r[5])) for r in rc_rows]
    from collections import Counter
    log('### A3 冻结档 12 行分支分布:', dict(Counter(b for _, b in fzb)))
    log('### A3 DISC_RECHECK 31 行分支分布:', dict(Counter(b for _, b in rcb)))
    log('### A3 冻结档逐行:', fzb)
    # exists 分支若不带字节注解的行为：直接调 run_expr 语义复刻？不——改为在沙箱真跑
    res = {'freeze_branches': fzb, 'recheck_branches': rcb,
           'freeze_hist': dict(Counter(b for _, b in fzb)),
           'recheck_hist': dict(Counter(b for _, b in rcb))}
    return res


def a3_live():
    """把冻结档 id 1 的校验式分别换成 exists / bytes=N / rows=N / grepcount=，看 C12 是否 fail-closed。"""
    cases = [
        ('exists-无字节注解', 'exists'),
        ('bytes=错误值', 'bytes=9999999'),
        ('rows=错误值', 'rows=1'),
        ('grepcount=不存在', 'grepcount=ZZZ_9f3a=1'),
        ('grep=必不命中', 'grep=ZZZ_NOT_PRESENT_9f3a'),
        ('grep=. 平凡锚', 'grep=.'),
    ]
    out = {}
    for name, expr in cases:
        d = build_sandbox('a3_' + re.sub(r'[^A-Za-z0-9]+', '_', name))
        rewrite_freeze_row(os.path.join(d, 'DISC_UNVERIFIABLE.tsv'),
                           os.path.join(d, 'check_disc.py'), 1, col4=expr)
        rc, sout = run_gate(d)
        c12 = [l for l in sout.split('\n') if 'C12' in l]
        fails = [l for l in sout.split('\n') if l.startswith('  FAIL')]
        log('### A3 冻结 id1 校验式=%r -> exit=%d %s' % (expr, rc, c12))
        for f in fails:
            log('        ' + f)
        out[name] = {'expr': expr, 'exit': rc, 'c12_lines': c12, 'fails': fails}
    return out


# ------------------------------------------------------------------ A4
def a4():
    out = {}
    for args in ([], ['--c6max=9'], ['--c6max=8'], ['--c6max=0'], ['--c6max=-1'],
                 ['--c6max=abc'], ['--c6max'], ['--c6max=120 '], ['--unknown=1']):
        rc, sout = run_gate(R14, *args)
        tail = [l for l in sout.split('\n') if ('C6 threshold' in l or l.startswith('  FAIL')
                                                or 'ValueError' in l or 'exit' in l or 'C6 cross' in l)]
        log('### A4 args=%r exit=%d -> %s' % (args, rc, tail))
        out[repr(args)] = {'exit': rc, 'tail': tail}
    return out


# ------------------------------------------------------------------ A5
def a5():
    src = io.open(GATE_NOW, encoding='utf-8').read()
    tree = ast.parse(src)
    assigned = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned[t.id] = node.lineno
        elif isinstance(node, (ast.For, ast.If, ast.Try)):
            pass
    loads, stores = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                loads[node.id] = loads.get(node.id, 0) + 1
            else:
                stores[node.id] = stores.get(node.id, 0) + 1
    dead = sorted((v, k) for k, v in assigned.items() if loads.get(k, 0) == 0)
    log('### A5 模块级赋值但 Load=0:', dead)
    log('### A5 C6MAX Load=%d  C11_LANDABLE Load=%d  C11B_PIN_GAP Load=%d  GATE_VER Load=%d'
        % (loads.get('C6MAX', 0), loads.get('C11_LANDABLE', 0),
           loads.get('C11B_PIN_GAP', 0), loads.get('GATE_VER', 0)))
    # 同时找「从未被读的按需开关」：形如 _ENABLE/_FLAG/_ON 之类
    knobs = {k: loads.get(k, 0) for k in assigned if re.search(r'(MAX|MIN|ENABLE|DISABLE|FLAG|OPT|LIMIT|THRESH|ON|PIN|TOL)$', k)}
    log('### A5 阈值/开关型模块常量 Load:', knobs)
    return {'assigned_never_loaded': [{'line': l, 'name': n} for l, n in dead],
            'knob_loads': knobs,
            'gate_ver_load': loads.get('GATE_VER', 0)}


# ------------------------------------------------------------------ A6
def a6():
    doc = io.open(GATE_NOW, encoding='utf-8').read().split('"""')[1]
    doc_lines = doc.split('\n')
    # 抽出 doc 中声明的检查项编号
    doc_ids = re.findall(r'^\s{2}(C\d+b?)\s', doc, re.M)
    code_ids = re.findall(r'---- (C\d+b?)', io.open(GATE_NOW, encoding='utf-8').read())
    checks = {}
    checks['doc_ids'] = doc_ids
    checks['code_section_ids'] = code_ids
    checks['doc_only'] = [x for x in doc_ids if x not in code_ids]
    checks['code_only'] = [x for x in code_ids if x not in doc_ids]
    # 硬编码数字对账
    checks['doc_says_28'] = [l for l in doc_lines if '28' in l]
    src = io.open(GATE_NOW, encoding='utf-8').read()
    checks['code_says_28'] = [l for l in src.split('\n') if '28' in l]
    checks['c10_doc_says_bytes'] = [l for l in doc_lines if '字节数' in l]
    checks['c10_code_comment'] = [l.strip() for l in src.split('\n') if '不用字节数' in l]
    checks['c5_doc_expected'] = re.findall(r'R14_COMMON=(\d+) / 看板=(\d+) / 台账=(\d+)', doc)
    checks['c5_code_expected'] = re.search(r"\('R14_COMMON', RC, (\d+)\), \('STATUS_BOARD', BRD, (\d+)\), \('LEDGER', LED, (\d+)\)", src).groups()
    # 非 ASCII 打印字符
    nonascii = []
    for i, l in enumerate(src.split('\n'), 1):
        if re.search(r'[\u0080-￿]', l):
            nonascii.append(i)
    checks['nonascii_line_count'] = len(nonascii)
    log('### A6 doc 声明检查项:', doc_ids)
    log('### A6 代码段头:', code_ids)
    log('### A6 doc 有代码无:', checks['doc_only'], ' 代码有 doc 无:', checks['code_only'])
    log('### A6 doc 里的 28:', checks['doc_says_28'])
    log('### A6 代码里的 28:', checks['code_says_28'])
    log('### A6 C5 doc 期望 vs 代码期望:', checks['c5_doc_expected'], checks['c5_code_expected'])
    log('### A6 非 ASCII 行数（docstring 声称不使用）:', len(nonascii))
    return checks


# ------------------------------------------------------------------ 额外：C12 能否被自删
def x_selfprotect():
    out = {}
    src = io.open(GATE_NOW, encoding='utf-8').read()
    start = src.index('# ---- C12 ')
    end = src.index("notes.append('C12 frozen-anchor")
    end = src.index('\n', end) + 1
    chopped = src[:start] + src[end:]
    d = build_sandbox('x_noc12')
    io.open(os.path.join(d, 'check_disc.py'), 'w', encoding='utf-8', newline='').write(chopped)
    rc, sout = run_gate(d)
    log('### X1 删掉整段 C12（GATE_VER 不动）exit=%d' % rc)
    log(sout)
    out['c12_removed_exit'] = rc
    out['c12_removed_stdout'] = sout
    # 同时把冻结档改成坏锚（证明「删 C12 + 坏锚」完全无声）
    rewrite_freeze_row(os.path.join(d, 'DISC_UNVERIFIABLE.tsv'),
                       os.path.join(d, 'check_disc.py'), 1, col4='grep=ZZZ_9f3a')
    rc2, sout2 = run_gate(d)
    log('### X2 删掉 C12 + 坏锚 + 同步 sha exit=%d' % rc2)
    out['c12_removed_bad_anchor_exit'] = rc2
    out['c12_removed_bad_anchor_stdout'] = sout2
    return out


def x_c12_semantic():
    """C12 通过后，锚与主张是否有语义绑定？测三种：平凡锚、冻结 id 20 的 GATE_VER 锚、时间戳非法日历。"""
    out = {}
    # 平凡锚已含在 a3_live；这里测「时间戳 2026-13-45T99:99:99+08:00」是否被判严格 ISO8601
    d = build_sandbox('x_ts')
    rewrite_freeze_row(os.path.join(d, 'DISC_UNVERIFIABLE.tsv'),
                       os.path.join(d, 'check_disc.py'), 1,
                       col7='2026-13-45T99:99:99+08:00')
    rc, sout = run_gate(d)
    fails = [l for l in sout.split('\n') if l.startswith('  FAIL')]
    log('### X3 冻结时刻=2026-13-45T99:99:99+08:00 -> exit=%d fails=%s' % (rc, fails))
    out['impossible_timestamp'] = {'exit': rc, 'fails': fails}
    # 冻结 id 20 的锚 grep=(?m)^GATE_VER 与「纪律 20 不可见字符」是否有语义关系（只做静态对照）
    fz = [l.split('\t') for l in io.open(FZ_NOW, encoding='utf-8', newline='').read().split('\n')[1:] if l]
    r20 = [r for r in fz if r[0] == '20'][0]
    log('### X4 冻结 id20 产物=%r 校验式=%r （纪律 20 讲 U+200B 传染/禁用断言）' % (r20[2], r20[3]))
    out['freeze_id20'] = {'product': r20[2], 'expr': r20[3]}
    # 冻结档新增一个 id（加严是否覆盖）
    d2 = build_sandbox('x_add')
    rewrite_freeze_row(os.path.join(d2, 'DISC_UNVERIFIABLE.tsv'),
                       os.path.join(d2, 'check_disc.py'), 1,
                       add_raw='\t'.join(['31', '§2.98', r'lead\next_re_20261117_r14\_r94\falsify_r94.py',
                                          'grep=G2', 'structurally_unverifiable', 'x',
                                          '2026-11-22T17:50:21+08:00', 'NO']))
    rc2, sout2 = run_gate(d2)
    fails2 = [l for l in sout2.split('\n') if l.startswith('  FAIL')]
    log('### X5 冻结档新增 id31（claims=无）+ 同步 sha -> exit=%d fails=%s' % (rc2, fails2))
    out['freeze_add_id'] = {'exit': rc2, 'fails': fails2}
    # 冻结档删除 id 1（claims=有）
    d3 = build_sandbox('x_drop')
    rewrite_freeze_row(os.path.join(d3, 'DISC_UNVERIFIABLE.tsv'),
                       os.path.join(d3, 'check_disc.py'), 1, drop=True)
    rc3, sout3 = run_gate(d3)
    fails3 = [l for l in sout3.split('\n') if l.startswith('  FAIL')]
    log('### X6 冻结档删除 id1（claims=有）+ 同步 sha -> exit=%d fails=%s' % (rc3, fails3))
    out['freeze_drop_id'] = {'exit': rc3, 'fails': fails3}
    return out


def x_c11b():
    """C11b 在卡面之外新增（04:22:58），测它是否真的能 FAIL、是否是「把缺口钉死」的假旋钮。"""
    out = {}
    d = build_sandbox('x_c11b')
    # 把 C11B_PIN_GAP 改一个值，看是否 FAIL（证明它活着）
    set_const(os.path.join(d, 'check_disc.py'), 'C11B_PIN_GAP', [11, 12])
    rc, sout = run_gate(d)
    fails = [l for l in sout.split('\n') if l.startswith('  FAIL')]
    log('### X7 C11B_PIN_GAP 改为 [11,12] -> exit=%d fails=%s' % (rc, fails))
    out['pin_changed'] = {'exit': rc, 'fails': fails}
    # 把 recheck 里 id 11 的第 7 列从「无」改「有」会触发别的检查？只做推断，不真改（会连锁 C11）
    return out


def main():
    res = {}
    res['meta'] = {
        'gate_sha256': sha(GATE_NOW),
        'gate_bytes': os.path.getsize(GATE_NOW),
        'gate_mtime': os.path.getmtime(GATE_NOW),
        'freeze_sha256': sha(FZ_NOW),
        'recheck_sha256': sha(RC_NOW),
        'bak_c12_sha256': sha(GATE_PRE_C12),
        'snapshot': 'snapshot_check_disc_042258.py',
    }
    res['A1'] = a1()
    res['A2'] = a2()
    res['A3'] = a3()
    res['A3_live'] = a3_live()
    res['A4'] = a4()
    res['A5'] = a5()
    res['A6'] = a6()
    res['X_selfprotect'] = x_selfprotect()
    res['X_semantic'] = x_c12_semantic()
    res['X_c11b'] = x_c11b()
    outdir = os.path.join(R14, '_r102_audit')
    io.open(os.path.join(outdir, 'AUDIT102.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(outdir, 'audit102.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102.json + audit102.log')


if __name__ == '__main__':
    main()
