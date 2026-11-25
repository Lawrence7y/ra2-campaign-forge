# -*- coding: utf-8 -*-
"""r136d_gate_controls.py -- 验证 R136 对门禁的四处改动是否各有分辨率（成对反控）

沙箱要点（R73 起 check_disc.py 按 __file__ 反推三层为 ROOT）：
  必须造 /tmp/xxx/lead/next_re_20261117_r14/ 三层结构，否则 ROOT 落到 /tmp、路径全错。
  live 树里只读（门禁不写盘），故制品目录用 symlink 挂进去是安全的；
  但被改的文件必须拷实件，不能用软链（R135 S-238：改软链会写穿真树）。
"""
import os
import shutil
import subprocess
import sys
import tempfile

R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
LEAD = '/home/t628/projects/ra2-campaign-forge/lead'

# 需要拷贝实件的（会被改动）
COPY_FILES = ['check_disc.py', 'recheck_verify.py', 'place_r87.py', 'clock3_r87.py', 'R14_COMMON.md', 'DISC_RECHECK.tsv',
              'DISC_UNVERIFIABLE.tsv', 'DISC_ESTABLISH.tsv', 'DISC_NS_MAP.tsv',
              'STATUS_BOARD.md', 'BOARD_ARCHIVE.md']

res = []


def chk(n, c, d):
    res.append((n, bool(c), d))
    print('%s %-64s %s' % ('PASS' if c else 'FAIL', n, d))


def make_sandbox():
    root = tempfile.mkdtemp(prefix='r136d_', dir='/tmp')
    r14d = os.path.join(root, 'lead', 'next_re_20261117_r14')
    os.makedirs(r14d)
    for f in COPY_FILES:
        s = os.path.join(R14, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(r14d, f))
    # lead 下的另两份被门禁读的文件，拷实件
    for f in ('GOAL_THREE_TARGETS_20261018.md', 'LEAD_LOCK'):
        s = os.path.join(LEAD, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(root, 'lead', f))
    # 制品目录只读挂软链（C7 要按路径查存在性与字节数）。
    # 注意 C7 的产物路径可能落在 lead/ 下任意位置（如 lead/next_re_20261201_xxx/...），
    # 故整个 lead/ 除已拷实件外全部挂软链。
    for base in (R14, LEAD):
        for f in os.listdir(base):
            s = os.path.join(base, f)
            rel = os.path.relpath(s, LEAD)
            t = os.path.join(root, 'lead', rel)
            if os.path.exists(t) or os.path.islink(t):
                continue
            if os.path.isdir(s) and f not in ('sbx',):
                os.symlink(s, t)
    # 部分纪律的产物路径相对 ROOT（如 _r94/falsify_r94.py、_r38/...），
    # 故把工程根下所有 _rNN 与 ra2bench 也挂软链。
    ROOTP = '/home/t628/projects/ra2-campaign-forge'
    for f in os.listdir(ROOTP):
        s = os.path.join(ROOTP, f)
        t = os.path.join(root, f)
        if os.path.exists(t) or os.path.islink(t):
            continue
        if os.path.isdir(s) and f not in ('lead', 'sbx'):
            os.symlink(s, t)
        elif os.path.isfile(s) and f.endswith(('.md',)):
            os.symlink(s, t)
    return root, r14d


def gate(root):
    p = subprocess.run([sys.executable, 'check_disc.py'],
                       cwd=os.path.join(root, 'lead', 'next_re_20261117_r14'),
                       capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


root, r14d = make_sandbox()
try:
    rc, out = gate(root)
    chk('P0 沙箱基线 exit 0（三段式 ROOT 反推正确）', rc == 0,
        'rc=%d ; %s' % (rc, [l for l in out.splitlines() if 'FAIL' in l][:2]))

    COMMON = os.path.join(r14d, 'R14_COMMON.md')
    orig = open(COMMON, 'rb').read()

    # N1: 删 2.140 整节 -> C16b（unpinned/missing）或 C15 必须报
    i = orig.find('## 2.140'.encode())
    open(COMMON, 'wb').write(orig[:i])
    rc, out = gate(root)
    chk('N1 删掉整节 2.140 -> exit 1', rc == 1, 'rc=%d' % rc)
    open(COMMON, 'wb').write(orig)

    # N2: 2.140 只留标题、正文清空 -> C16 单节下界必报
    t = orig.decode('utf-8')
    i = t.find('## 2.140')
    head = t[i:].split('\n')[0]
    open(COMMON, 'w', encoding='utf-8', newline='').write(t[:i] + head + '\n')
    rc, out = gate(root)
    chk('N2 2.140 只留标题（正文清空）-> exit 1 且点名 140',
        rc == 1 and '140' in out, 'rc=%d' % rc)
    open(COMMON, 'wb').write(orig)

    # N3: GATE_VER 回退 R136->R135 而不同步第 20 行 -> C10 / C7d / C12 必报
    GD = os.path.join(r14d, 'check_disc.py')
    c0 = open(GD, 'rb').read()
    open(GD, 'wb').write(c0.replace(b"GATE_VER = 'R136'", b"GATE_VER = 'R135'", 1))
    rc, out = gate(root)
    chk('N3 只回退 GATE_VER 不同步第20行 -> exit 1', rc == 1, 'rc=%d' % rc)
    open(GD, 'wb').write(c0)

    # N4: 改冻结档第 20 行而不重钉 FREEZE_SHA256 -> C11 TAMPERED
    FU = os.path.join(r14d, 'DISC_UNVERIFIABLE.tsv')
    f0 = open(FU, 'rb').read()
    open(FU, 'wb').write(f0.replace(b"GATE_VER = 'R136'", b"GATE_VER = 'R136x'", 1))
    rc, out = gate(root)
    chk('N4 改冻结档不重钉常量 -> exit 1 且报 TAMPERED',
        rc == 1 and 'TAMPERED' in out, 'rc=%d' % rc)
    open(FU, 'wb').write(f0)

    # N5: 冻结档单侧放宽（live 不动）-> C12b 必报
    open(FU, 'wb').write(f0.replace(b"grep=(?m)^GATE_VER = 'R136'",
                                    b"grep=(?m)^GATE_VER", 1))
    rc, out = gate(root)
    chk('N5 冻结档单侧放宽 -> exit 1 且报 C12b', rc == 1 and 'C12b' in out,
        'rc=%d' % rc)
    open(FU, 'wb').write(f0)

    # P1: 全部复原后必须 exit 0
    rc, out = gate(root)
    chk('P1 全部复原 -> exit 0', rc == 0, 'rc=%d' % rc)
finally:
    shutil.rmtree(root, ignore_errors=True)

n = sum(1 for _a, c, _d in res if c)
print('SUMMARY %d/%d PASS' % (n, len(res)))
sys.exit(0 if n == len(res) else 1)
