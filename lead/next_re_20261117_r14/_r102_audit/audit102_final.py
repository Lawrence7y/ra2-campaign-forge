#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R102 审计 · 第六组：C6MAX 能否单独 FAIL、缺冻结档时 C12 崩溃、C12 是否被 C7 完全支配。"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

TRUE = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(TRUE, 'lead', 'next_re_20261117_r14')
BAK = os.path.join(R14, 'R17_LEAD_BASELINE')
GATE = os.path.join(R14, 'check_disc.py')
PRE_C12 = os.path.join(BAK, 'R102.before_check_disc_C12_20261124_042045.bak')
PRE_VER = os.path.join(BAK, 'R102.before_DISC_RECHECK_ver_bump_20261124_042045.bak')
RC = os.path.join(R14, 'DISC_RECHECK.tsv')
FZ = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
NSMAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
OUT = os.path.join(R14, '_r102_audit')
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def sb(tag, gate=GATE, rc=RC, fz=FZ, nsmap=NSMAP):
    d = os.path.join(tempfile.gettempdir(), 'aud102f_' + tag)
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
        if n in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv',
                 'DISC_NS_MAP.tsv', '__pycache__'):
            continue
        os.symlink(os.path.join(R14, n), os.path.join(t, n))
    for src, name in ((gate, 'check_disc.py'), (rc, 'DISC_RECHECK.tsv'),
                      (fz, 'DISC_UNVERIFIABLE.tsv'), (nsmap, 'DISC_NS_MAP.tsv')):
        if src is not None:
            shutil.copyfile(src, os.path.join(t, name))
    return t


def run(d, *a):
    p = subprocess.run([sys.executable, 'check_disc.py'] + list(a), cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


# ---------------------------------------------------------------- K1 缺冻结档的两种行为
def k1():
    out = {}
    for tag, gate in (('now', GATE), ('pre', PRE_C12)):
        d = sb('k1_' + tag, gate=gate, rc=(RC if tag == 'now' else PRE_VER))
        os.unlink(os.path.join(d, 'DISC_UNVERIFIABLE.tsv'))
        rc, sout = run(d)
        tail = [l for l in sout.split('\n') if l.strip()][-6:]
        crash = 'Traceback' in sout
        log('### K1 冻结档缺失，门禁=%s: exit=%d crash=%s' % (tag, rc, crash))
        for l in tail:
            log('        ' + l)
        out[tag] = {'exit': rc, 'crash': crash, 'tail': tail}
    return out


# ---------------------------------------------------------------- K2 C6MAX 能否单独 FAIL
def k2():
    """cross +N 且 NS_MAP +N INCLUDE 行（地图同步维护）=> 只有 C6MAX 能挡。"""
    out = {}
    # 逐段尝试：加多少条才让 cross 增长到 121
    txt = io.open(NSMAP, encoding='utf-8', newline='').read()
    rows = [l.split('\t') for l in txt.split('\n') if l]
    log('### K2 DISC_NS_MAP 表头 %d 列: %s' % (len(rows[0]), rows[0]))
    log('### K2 首行数据: %s' % rows[1])
    inc = [r for r in rows[1:] if len(r) > 5 and r[5].strip() == 'INCLUDE']
    log('### K2 现有 INCLUDE 行数=%d' % len(inc))
    # 造 N 条：向 R14_COMMON 加跨命名空间引用，同时向 NS_MAP 加 INCLUDE 行
    N = 112
    d = sb('k2')
    rcp = os.path.join(d, 'R14_COMMON.md')
    # 找到第一个 ## 1 之前的区域？简单：在文件尾（当前节 = 最后一节的号）追加
    # 需要保证落在外层（非 2.14+）。用 §8 区域更稳：直接追加到文件末尾会继承最后一节的 cur
    # 先查最后一节
    body = io.open(rcp, encoding='utf-8').read()
    cur = None
    for l in body.split('\n'):
        m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
        if m:
            cur = m.group(1)
    log('### K2 R14_COMMON 最后出现的节号=%s（决定追加行归属）' % cur)
    # 追加在文件头之前不行（cur=None 也算外层）；在最前面插一个 ## 8.99 段
    add = ['## 8.99', ''] + ['- 审计注入 纪律 %d 引用测试' % (900 + i) for i in range(N)] + ['']
    newbody = '\n'.join(add) + body
    io.open(rcp, 'w', encoding='utf-8', newline='').write(newbody)
    # NS_MAP 加 N 行 INCLUDE
    ns = [l.split('\t') for l in io.open(NSMAP, encoding='utf-8', newline='').read().split('\n') if l]
    tpl = list(inc[0]) if inc else ['x'] * len(ns[0])
    for i in range(N):
        row = list(tpl)
        row[0] = '审计注入 %d' % (900 + i)
        row[5] = 'INCLUDE'
        ns.append(row)
    io.open(os.path.join(d, 'DISC_NS_MAP.tsv'), 'w',
            encoding='utf-8', newline='').write(
        '\n'.join('\t'.join(r) for r in ns) + '\n')
    rc, sout = run(d)
    lines = [l for l in sout.split('\n') if 'C6' in l or l.startswith('  FAIL') or 'exit' in l]
    log('### K2 注入 %d 条跨命名空间引用 + %d 条 INCLUDE 行：exit=%d' % (N, N, rc))
    for l in lines:
        log('        ' + l)
    out['plus_112_synced'] = {'exit': rc, 'lines': lines}
    # 同沙箱加 --c6max=100000 应当回绿
    rc2, sout2 = run(d, '--c6max=100000')
    log('### K2b 同沙箱 --c6max=100000 -> exit=%d' % rc2)
    out['plus_112_c6max_raised'] = rc2
    # 少一条（N-1），cross=120，应当刚好过
    d2 = sb('k2b')
    rcp2 = os.path.join(d2, 'R14_COMMON.md')
    body2 = io.open(rcp2, encoding='utf-8').read()
    add2 = ['## 8.99', ''] + ['- 审计注入 纪律 %d 引用测试' % (900 + i) for i in range(N - 1)] + ['']
    io.open(rcp2, 'w', encoding='utf-8', newline='').write('\n'.join(add2) + body2)
    ns2 = [l.split('\t') for l in io.open(NSMAP, encoding='utf-8', newline='').read().split('\n') if l]
    for i in range(N - 1):
        row = list(tpl)
        row[0] = '审计注入 %d' % (900 + i)
        row[5] = 'INCLUDE'
        ns2.append(row)
    io.open(os.path.join(d2, 'DISC_NS_MAP.tsv'), 'w',
            encoding='utf-8', newline='').write('\n'.join('\t'.join(r) for r in ns2) + '\n')
    rc3, sout3 = run(d2)
    lines3 = [l for l in sout3.split('\n') if 'C6' in l or l.startswith('  FAIL')]
    log('### K2c 注入 %d 条（cross=120）exit=%d' % (N - 1, rc3))
    for l in lines3:
        log('        ' + l)
    out['plus_111_synced'] = {'exit': rc3, 'lines': lines3}
    return out


# ---------------------------------------------------------------- K3 C12 被 C7 支配（活体演示）
def k3():
    """改产物使 C7 的锚不命中而 C12 的锚仍命中 => C12 在该行永不单独报警。"""
    out = {}
    d = sb('k3')
    rcp = os.path.join(d, 'R14_COMMON.md')
    body = io.open(rcp, encoding='utf-8').read()
    # 把 "**纪律 1 ·" 改成 "**纪律 1：" —— C7 锚（含 " 1 ·"）失配，C12 锚（"**纪律"）仍命中
    before = body.count('**纪律 1 ·')
    new = re.sub(r'\*\*纪律 1 ·', '**纪律 1 :', body)
    n = len(re.findall(r'\*\*纪律 1 ·', body))
    io.open(rcp, 'w', encoding='utf-8', newline='').write(new)
    rc, sout = run(d)
    fails = [l for l in sout.split('\n') if l.startswith('  FAIL')]
    c12 = [l for l in sout.split('\n') if 'C12' in l]
    log('### K3 把 "**纪律 1 ·" 改成 "**纪律 1 :"（%d 处）: exit=%d' % (n, rc))
    log('        %s' % c12)
    for f in fails:
        log('        ' + f)
    out['c1_anchor_broken'] = {'exit': rc, 'fails': fails, 'c12': c12}
    # 反向：让 C12 能单独报而 C7 不报 —— 结构上不可能（C12 锚是 C7 锚的泛化）。
    # 用平凡锚验证：把冻结档 id1 的锚换成 "grep=(?m)" （恒命中）——若 C12 是"真核验"，它必须仍 pass；
    # 这正是"泛化"方向，说明 C12 的通过不携带信息。
    out['note'] = 'C12 锚⊇C7 锚，故 C12 通过 ⇒ 无信息；C12 失败 ⇒ C7 必先失败（见 F1）'
    return out


# ---------------------------------------------------------------- K4 A2 复跑（最短命令）
def k4():
    """把 A2 的复跑压成可粘贴的最小步骤，写进产物。"""
    return {
        'step1': 'python3 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py',
        'script': '_r102_audit/audit102_run.py 的 a2() / audit102_escape.py 的 h3()',
    }


def main():
    res = {}
    res['K1_missing_freeze'] = k1()
    res['K2_c6max_alone'] = k2()
    res['K3_c12_dominated'] = k3()
    res['K4_repro'] = k4()
    io.open(os.path.join(OUT, 'AUDIT102_final.json'), 'w', encoding='utf-8').write(
        json.dumps(res, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, 'audit102_final.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('\n[written] AUDIT102_final.json + audit102_final.log')


if __name__ == '__main__':
    main()
