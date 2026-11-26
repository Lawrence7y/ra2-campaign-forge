#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r138h_gate_controls.py —— R138 门禁正反控（沙箱，绝不写穿真树）。

沙箱构建沿用 R136/R137 的混合方式：被改的文件拷实件，其余软链挂入。
只用实件+软链，不 copytree（R133 S-227：copytree 811MB 写爆 tmpfs）。

控制项：
  P0  基线：应 exit 0、C16 pinned 136/unpinned 0、C10 ok(R138)
  N1  删 2.142 整节     -> exit 1 且 missing 点名 142
  N2  2.142 只留标题    -> exit 1 且 hollow 点名 142、margin 负
  N3  只回退 GATE_VER 不同步第 21 行 -> exit 1 且报 GATE_VER 不符
  N4  改冻结档不重钉    -> exit 1 且报 TAMPERED
  N5  调小 C16 下界不重钉 -> exit 1 且报 C16d TAMPERED
  P1  复原            -> exit 0
"""
import os
import io
import re
import sys
import shutil
import hashlib
import subprocess
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')

results = []


def run_gate(sandbox):
    p = subprocess.run([sys.executable, os.path.join(sandbox, 'lead', 'next_re_20261117_r14',
                                                     'check_disc.py')],
                       cwd=sandbox, capture_output=True, text=True, timeout=280)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def build_sandbox(tag):
    """被改文件拷实件，其余软链挂入。"""
    sb = tempfile.mkdtemp(prefix='r138_%s_' % tag, dir='/mnt/ssd/tmp')
    os.makedirs(os.path.join(sb, 'lead', 'next_re_20261117_r14'))
    # 顶层 lead/ 下的文件与目录
    for name in os.listdir(os.path.join(ROOT, 'lead')):
        src = os.path.join(ROOT, 'lead', name)
        dst = os.path.join(sb, 'lead', name)
        if os.path.isdir(src) and not os.path.islink(src):
            if name == 'next_re_20261117_r14':
                continue
            os.symlink(src, dst)
        else:
            os.symlink(src, dst)
    # r14 目录内部：只拷实件，其余软链
    REAL = {'check_disc.py', 'R14_COMMON.md', 'STATUS_BOARD.md', 'DISC_RECHECK.tsv',
            'DISC_UNVERIFIABLE.tsv', 'DISC_ESTABLISH.tsv', 'DISC_NS_MAP.tsv'}
    for name in os.listdir(R14):
        src = os.path.join(R14, name)
        dst = os.path.join(sb, 'lead', 'next_re_20261117_r14', name)
        if name in REAL:
            shutil.copy2(src, dst)
        else:
            os.symlink(src, dst)
    # 顶层其它目录软链
    for name in os.listdir(ROOT):
        if name == 'lead' or name in ('.git',):
            continue
        src = os.path.join(ROOT, name)
        dst = os.path.join(sb, name)
        if not os.path.lexists(dst):
            os.symlink(src, dst)
    return sb


def safe_rm(sb):
    """R134 S-233：绝不 shutil.rmtree 在含软链的树上。逐个解链再删目录。"""
    for dp, dns, fns in os.walk(sb, topdown=False, followlinks=False):
        for f in fns:
            p = os.path.join(dp, f)
            if os.path.islink(p):
                os.unlink(p)
            else:
                os.remove(p)
        for d in dns:
            p = os.path.join(dp, d)
            if os.path.islink(p):
                os.unlink(p)
            else:
                try:
                    os.rmdir(p)
                except OSError:
                    pass
    try:
        os.rmdir(sb)
    except OSError:
        pass


def rec(tag, want_rc, got_rc, must, output):
    ok = (got_rc == want_rc) and all(s in output for s in must)
    results.append((tag, ok, want_rc, got_rc, must))
    print(('  PASS ' if ok else '  FAIL ') + tag
          + ' (rc want=%s got=%s; must=%s)' % (want_rc, got_rc, must))
    return ok


def main():
    print('# R138 门禁正反控（沙箱）')
    base_sha = hashlib.sha256(open(GATE, 'rb').read()).hexdigest()

    # ---- P0 基线 ----
    sb = build_sandbox('p0')
    try:
        rc, out = run_gate(sb)
        rec('P0 基线', 0, rc, ['pinned 136', 'unpinned 0', 'ok(R138)'], out)
    finally:
        safe_rm(sb)

    # ---- N1 删 2.142 整节 ----
    sb = build_sandbox('n1')
    try:
        p = os.path.join(sb, 'lead', 'next_re_20261117_r14', 'R14_COMMON.md')
        t = io.open(p, encoding='utf-8', newline='').read()
        i = t.index('## 2.142 ')
        nb = t[:i].rstrip('\n') + '\n'
        io.open(p, 'w', encoding='utf-8', newline='').write(nb)
        rc, out = run_gate(sb)
        rec('N1 删 2.142 整节', 1, rc, ['142'], out)
    finally:
        safe_rm(sb)

    # ---- N2 2.142 只留标题 ----
    sb = build_sandbox('n2')
    try:
        p = os.path.join(sb, 'lead', 'next_re_20261117_r14', 'R14_COMMON.md')
        t = io.open(p, encoding='utf-8', newline='').read()
        i = t.index('## 2.142 ')
        j = t.find('\n## 2.', i + 5)
        head = t[:i]
        title = t[i:t.find('\n', i)]
        rest = t[j:] if j > 0 else '\n'
        nb = head + title + '\n\n' + rest.lstrip('\n')
        io.open(p, 'w', encoding='utf-8', newline='').write(nb)
        rc, out = run_gate(sb)
        rec('N2 2.142 只留标题', 1, rc, ['hollow'], out)
    finally:
        safe_rm(sb)

    # ---- N3 只回退 GATE_VER ----
    sb = build_sandbox('n3')
    try:
        p = os.path.join(sb, 'lead', 'next_re_20261117_r14', 'check_disc.py')
        t = io.open(p, encoding='utf-8', newline='').read()
        t = t.replace("GATE_VER = 'R138'", "GATE_VER = 'R137'")
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
        rc, out = run_gate(sb)
        rec('N3 只回退 GATE_VER', 1, rc, ['GATE_VER'], out)
    finally:
        safe_rm(sb)

    # ---- N4 改冻结档不重钉 ----
    sb = build_sandbox('n4')
    try:
        p = os.path.join(sb, 'lead', 'next_re_20261117_r14', 'DISC_UNVERIFIABLE.tsv')
        b = open(p, 'rb').read()
        open(p, 'wb').write(b + b'\n')
        rc, out = run_gate(sb)
        rec('N4 改冻结档不重钉', 1, rc, ['TAMPERED'], out)
    finally:
        safe_rm(sb)

    # ---- N5 调小 C16 下界不重钉 ----
    sb = build_sandbox('n5')
    try:
        p = os.path.join(sb, 'lead', 'next_re_20261117_r14', 'check_disc.py')
        t = io.open(p, encoding='utf-8', newline='').read()
        t = t.replace('142: 3404,', '142: 1,')
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
        rc, out = run_gate(sb)
        rec('N5 调小 C16 下界不重钉', 1, rc, ['C16d'], out)
    finally:
        safe_rm(sb)

    # ---- P1 复原 ----
    sb = build_sandbox('p1')
    try:
        rc, out = run_gate(sb)
        rec('P1 复原', 0, rc, ['ok(R138)', 'exit 0'], out)
    finally:
        safe_rm(sb)

    # 真树未被改动
    ok = hashlib.sha256(open(GATE, 'rb').read()).hexdigest() == base_sha
    results.append(('真树 gate 未被改动', ok, '-', '-', '-'))
    print(('  PASS ' if ok else '  FAIL ') + '真树 check_disc.py 未被控制脚本改动')

    npass = sum(1 for r in results if r[1])
    print()
    print('== 正反控 %d/%d PASS ==' % (npass, len(results)))
    for tag, ok, w, g, m in results:
        if not ok:
            print('  FAIL: %s (want %s got %s must %s)' % (tag, w, g, m))
    return 0 if npass == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
