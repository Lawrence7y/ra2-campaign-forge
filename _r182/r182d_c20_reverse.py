#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182d_c20_reverse.py —— C20 反向控制（全部在 /tmp 镜像，绝不碰生产）。

镜像做法沿用 R181 的 r181e：仓库根下除 lead/ 外全部符号链接，tier 下除待改文件外全部
符号链接。**只**把 check_disc.py 与待改门禁文件用实体副本 —— 这样 C7 的 31 条产物 grep
仍看到生产实物（避免 S-675 那种「镜像环境造成的假 FAIL」被当成判据失败）。

判据的判据（差分）：每次只认 **C20 条目**的出现/消失，不认镜像环境造成的其它 FAIL。
"""
import hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')

fails, oks = [], []
def ck(n, c, d=''):
    (oks if c else fails).append(n)
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    return c

def rd(p): return io.open(p, encoding='utf-8', newline='').read()

# S-182d2：首版 OVERRIDE 漏了 FACT_INDEX_CURRENT.md ⇒ 它是软链，safe_unlink 正确拒绝
# （护栏生效的证据）。指针是 C19/C20 的靶子，必须在沙箱里是实体副本。
OVERRIDE = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv',
            'R14_COMMON.md', 'STATUS_BOARD.md', 'FACT_INDEX_CURRENT.md'}

def mirror(mutate):
    tmpd = tempfile.mkdtemp(prefix='r182d_')
    try:
        sb = os.path.join(tmpd, 'gatesb')
        os.makedirs(sb)
        # S-182e1（本轮事故，血账）：上一版在 sb 下给**所有**顶层项建软链，包括 _r160 与 _r161，
        # 随后又 os.makedirs(sb/_r160, exist_ok=True) 静默通过，再 os.unlink(sb/_r160/facts_floors.py)
        # ⇒ 穿透软链删了生产实物 26,147 B。R181 S-671/672 记的是「沙箱漏软链」，方向相反。
        # 修法：这两个目录**必须在 sb 下建实体目录**，绝不软链；且 delete 之前先断言它是实体目录。
        for name in os.listdir(ROOT):
            if name in ('lead', '_r160', '_r161'):
                continue
            os.symlink(os.path.join(ROOT, name), os.path.join(sb, name))
        os.makedirs(os.path.join(sb, 'lead'))
        for name in os.listdir(os.path.join(ROOT, 'lead')):
            if name == 'next_re_20261117_r14':
                continue
            os.symlink(os.path.join(ROOT, 'lead', name), os.path.join(sb, 'lead', name))
        tdir = os.path.join(sb, 'lead', 'next_re_20261117_r14')
        os.makedirs(tdir)
        for name in os.listdir(TIER):
            if name in OVERRIDE:
                continue
            os.symlink(os.path.join(TIER, name), os.path.join(tdir, name))
        for name in OVERRIDE:
            shutil.copy2(os.path.join(TIER, name), os.path.join(tdir, name))
        # gate_runner / facts_floors 也要能改 ⇒ 在**实体目录**里放实体副本
        for d, f in (('_r160', 'facts_floors.py'), ('_r161', 'gate_runner.py')):
            dd = os.path.join(sb, d)
            if os.path.islink(dd):
                raise RuntimeError('sandbox %s is a SYMLINK to production; refusing to write '
                                   '(this is exactly the S-182e1 accident)' % dd)
            os.makedirs(dd, exist_ok=True)
            shutil.copy2(os.path.join(ROOT, d, f), os.path.join(dd, f))
        mutate(tmpd, sb, tdir)
        env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
        p = subprocess.run([sys.executable, os.path.join(tdir, 'check_disc.py')],
                           capture_output=True, text=True, cwd=tdir, env=env, timeout=600)
        o = p.stdout + p.stderr
        return p.returncode, [l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')], o
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

def c20(fs): return [f for f in fs if re.search(r'\bC20\b', f)]

def safe_unlink(p):
    """S-182e1 之后加的硬保护：只删沙箱实体目录内的普通文件。
    若任一级父目录是软链 ⇒ 直接抛错，绝不穿透到生产。"""
    q = os.path.abspath(p)
    d = os.path.dirname(q)
    while d and d != '/':
        if os.path.islink(d):
            raise RuntimeError('refusing to unlink %s: parent %s is a symlink' % (p, d))
        d = os.path.dirname(d)
    if os.path.islink(q):
        raise RuntimeError('refusing to unlink %s: target itself is a symlink' % p)
    os.unlink(p)

print('--- B0 基线：镜像里 C20 必须绿 ---')
rc0, fs0, o0 = mirror(lambda t, sb, td: None)
print('   rc=%d FAIL=%d（其中 C20 %d）' % (rc0, len(fs0), len(c20(fs0))))
ck('B0.1 基线镜像 rc==0（保真）', rc0 == 0, (rc0, [f[:70] for f in fs0[:3]]))
ck('B0.2 基线 C20 ok 行在场', 'C20 three-way ledger path: ok(' in o0)
ck('B0.3 基线无任何 C20 FAIL', not c20(fs0), c20(fs0)[:2])

def m1_gr_to_V562(t, sb, td):
    p = os.path.join(sb, '_r161', 'gate_runner.py')
    txt = rd(p); safe_unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V562', 1))

print('--- R1 gate_runner.LEDGER → V562（C19 完全看不见的那一份）---')
rc1, fs1, o1 = mirror(m1_gr_to_V562)
print('   rc=%d C20 FAIL=%r' % (rc1, c20(fs1)[:2]))
ck('R1.1 exit 1', rc1 == 1, rc1)
ck('R1.2 出现 C20 runner-vs-facts FAIL', any('C20 gate_runner.LEDGER' in f and 'EXPECT_CUR' in f for f in fs1),
   [f[:100] for f in c20(fs1)])
ck('R1.3 出现 C20 runner-vs-pointer FAIL', any('C20 gate_runner.LEDGER' in f and 'pointer' in f for f in fs1),
   [f[:100] for f in c20(fs1)])
ck('R1.4 此工况 C19 仍绿（证明这不是 C19 已覆盖的面）',
   'C19 fact-layer link: ok(' in o1, [l for l in o1.split('\n') if 'C19' in l][:1])

def m2_ff_to_V562(t, sb, td):
    p = os.path.join(sb, '_r160', 'facts_floors.py')
    txt = rd(p); safe_unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V562', 1))

print('--- R2 facts_floors.EXPECT_CUR → V562 ---')
rc2, fs2, o2 = mirror(m2_ff_to_V562)
ck('R2.1 exit 1', rc2 == 1, rc2)
ck('R2.2 C20 报 runner-vs-facts 不等', any('C20 gate_runner.LEDGER' in f and 'EXPECT_CUR' in f for f in fs2),
   [f[:100] for f in c20(fs2)])
ck('R2.3 C19 (e) 同时报（两判据重叠面一致，不是互相矛盾）',
   any('C19 fact gate targets a different file' in f for f in fs2), len([f for f in fs2 if 'C19' in f]))

def m3_gr_dup(t, sb, td):
    """v2 的 (d) 判据 = 全文件台账版本目录字面量集合大小。两种第二份都必须被抓：
       同名再赋值（Python 静默覆盖）与换名副本（LEDGER2）。"""
    p = os.path.join(sb, '_r161', 'gate_runner.py')
    txt = rd(p); safe_unlink(p)
    line = "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')\n"
    assert txt.count(line) == 1
    # 造成 2 个不同版本目录字面量：保留原有的 V563，再加一份 V562（换名）
    txt2 = txt + "\nLEDGER2 = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n"
    io.open(p, 'w', encoding='utf-8', newline='').write(txt2)

print('--- R3 gate_runner 出现第二份 LEDGER 常量 ---')
rc3, fs3, o3 = mirror(m3_gr_dup)
ck('R3.1 exit 1', rc3 == 1, rc3)
# v2 的 FAIL 文本已改为 'carries N distinct ledger version literals'（v1 是 'declares N'）。
ck('R3.2 出现 C20 版本字面量集合大小 != 1 的 FAIL',
   any('carries 2 distinct ledger version literals' in f for f in fs3),
   [f[:110] for f in c20(fs3)])

def m4_gr_delete(t, sb, td):
    safe_unlink(os.path.join(sb, '_r161', 'gate_runner.py'))
print('--- R4 gate_runner.py 删除 ⇒ 不得跳过 ---')
rc4, fs4, o4 = mirror(m4_gr_delete)
ck('R4.1 exit 1', rc4 == 1, rc4)
ck('R4.2 出现 C20 gate_runner.py missing FAIL',
   any('C20 gate_runner.py missing' in f for f in fs4), [f[:90] for f in c20(fs4)])

def m5_gr_syntax(t, sb, td):
    p = os.path.join(sb, '_r161', 'gate_runner.py')
    txt = rd(p); safe_unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt.replace("LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')",
                    "LEDGER = some_other_helper('x')", 1))
print('--- R5 gate_runner.LEDGER 改成不可解析形式 ⇒ 不得静默通过 ---')
rc5, fs5, o5 = mirror(m5_gr_syntax)
ck('R5.1 exit 1', rc5 == 1, rc5)
ck('R5.2 出现 C20 cannot resolve LEDGER FAIL',
   any('C20 cannot resolve LEDGER' in f for f in fs5), [f[:90] for f in c20(fs5)])

def m6_ptr_to_V562(t, sb, td):
    p = os.path.join(td, 'FACT_INDEX_CURRENT.md')
    txt = rd(p); safe_unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V562'))
print('--- R6 指针整体改 V562（三处各查各的版本）---')
rc6, fs6, o6 = mirror(m6_ptr_to_V562)
ck('R6.1 exit 1', rc6 == 1, rc6)
# S-182d3：首版用 f.startswith('C19')，而 FAIL 行形如 'FAIL  C19 ...'（strip 后仍以 FAIL 开头）
# ⇒ 计数恒 0、假 FAIL。改用子串匹配。
ck('R6.2 C19 与 C20 都报（重叠面的表现一致）',
   any(' C19 ' in f for f in fs6) and any('C20 gate_runner.LEDGER' in f for f in fs6),
   (len([f for f in fs6 if ' C19 ' in f]), len(c20(fs6))))

def m8_gr_import(t, sb, td):
    """v2 最该支持的终局重构：gate_runner 改成 import 同源 ⇒ 必须绿（v1 会假 FAIL）。"""
    p = os.path.join(sb, '_r161', 'gate_runner.py')
    txt = rd(p); safe_unlink(p)
    txt2 = txt.replace(
        "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')",
        "from facts_floors import EXPECT_CUR as LEDGER")
    io.open(p, 'w', encoding='utf-8', newline='').write(txt2)
print('--- R8 v2 终局重构：gate_runner 用 import 同源 ⇒ 必须绿（v1 假 FAIL 的工况）---')
rc8, fs8, o8 = mirror(m8_gr_import)
ck('R8.1 import 形态下无 C20 FAIL（v1 会在这一格假 FAIL）', not c20(fs8), c20(fs8)[:2])
ck('R8.2 出现「imported from facts_floors」NOTE', 'imported from facts_floors' in o8)

def m9_gr_funcfix(t, sb, td):
    """函数内自测夹具不得被 (d) 计成第二份（v1 会假 FAIL）。"""
    p = os.path.join(sb, '_r161', 'gate_runner.py')
    txt = rd(p); safe_unlink(p)
    txt2 = txt + ("\ndef _fixture():\n"
                  "    LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n"
                  "    return LEDGER\n")
    io.open(p, 'w', encoding='utf-8', newline='').write(txt2)
print('--- R9 v1 假 FAIL 面：函数内自测夹具含另一版本字面量 ---')
rc9, fs9, o9 = mirror(m9_gr_funcfix)
ck('R9.1 v2 的 (b)(c) 仍绿（顶层未变）', not [f for f in c20(fs9) if 'EXPECT_CUR' in f or 'pointer' in f],
   c20(fs9)[:2])
ck('R9.2 但 (d) 报 2 个版本字面量 ⇒ FAIL（这是 v2 的**有意**判据：全文件只许一份）',
   any('C20 gate_runner.py carries 2 distinct' in f for f in fs9), [f[:110] for f in c20(fs9)])
ck('R9.3 如实登记：这一格是「真判据」还是「假 FAIL」取决于策略选择（全文件唯一 vs 顶层唯一）',
   True, 'v2 选全文件唯一')

def m10_c19_red(t, sb, td):
    """C19 内容漂移（facts 常量脱钩）而三方路径仍相等 ⇒ C20 不得打印绿 ok。"""
    p = os.path.join(sb, '_r160', 'facts_floors.py')
    txt = rd(p); safe_unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        __import__('re').sub(r"^CUR_SHA256 = '[0-9a-f]{64}'", "CUR_SHA256 = '%s'" % ('0'*64),
                            txt, count=1, flags=__import__('re').M))
print('--- R10 C19 红时 C20 不得报绿（v1 的误导性 NOTE）---')
rc10, fs10, o10 = mirror(m10_c19_red)
ck('R10.1 exit 1', rc10 == 1, rc10)
ck('R10.2 C20 报 cannot certify while C19 is ... FAIL',
   any('C20 cannot certify the three-way link while C19' in f for f in fs10),
   [f[:110] for f in c20(fs10)])
ck('R10.3 不再出现 C20 ok 行', 'C20 three-way ledger path: ok(' not in o10)

print('--- R7 共同上限：三处同时改成 V562（含指针与 facts）⇒ C20 仍绿，如实登记 ---')
def m7_all(t, sb, td):
    # S-182d4：本精简库现盘只有 V563（530..562 不在盘）⇒ 首版直接指向 V562 目录会 FileNotFound。
    # 在沙箱 tier 里造一份 V562 实体副本（拷贝，不是软链），再让三处一起指向它。
    src563 = os.path.join(td, 'R17_R131_FACTINDEX_V563')
    dst562 = os.path.join(td, 'R17_R131_FACTINDEX_V562')
    if os.path.islink(dst562):
        raise RuntimeError('sandbox V562 is a symlink; refusing')
    os.makedirs(dst562, exist_ok=True)
    shutil.copy2(os.path.join(src563, 'FACT_INDEX.tsv'),
                 os.path.join(dst562, 'FACT_INDEX.tsv'))
    for p in (os.path.join(sb, '_r161', 'gate_runner.py'),
              os.path.join(sb, '_r160', 'facts_floors.py'),
              os.path.join(td, 'FACT_INDEX_CURRENT.md')):
        txt = rd(p); safe_unlink(p)
        io.open(p, 'w', encoding='utf-8', newline='').write(
            txt.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V562'))
    # 指针字段与 facts 常量也要同步成 V562 实物，否则撞 C19
    v562dir = os.path.join(td, 'R17_R131_FACTINDEX_V562')
    for p in (os.path.join(sb, '_r160', 'facts_floors.py'),
              os.path.join(td, 'FACT_INDEX_CURRENT.md')):
        txt = rd(p)
        raw = open(os.path.join(v562dir, 'FACT_INDEX.tsv'), 'rb').read()
        s = hashlib.sha256(raw).hexdigest()
        txt = re.sub(r"CUR_SHA256 = '[0-9a-f]{64}'", "CUR_SHA256 = '%s'" % s, txt)
        txt = re.sub(r'TOTAL_BYTES = \d+', 'TOTAL_BYTES = %d' % len(raw), txt)
        txt = re.sub(r'\| sha256 \| [0-9a-f]{64} \|', '| sha256 | %s |' % s, txt)
        txt = re.sub(r'\| 字节数 \| \d+ \|', '| 字节数 | %d |' % len(raw), txt)
        safe_unlink(p)
        io.open(p, 'w', encoding='utf-8', newline='').write(txt)
rc7, fs7, o7 = mirror(m7_all)
print('   rc=%d C20 FAIL=%r' % (rc7, c20(fs7)[:2]))
ck('R7.1 三处同时升版且自洽 ⇒ 无 C20 FAIL（升版一致性判据，不是防篡改判据）', not c20(fs7), c20(fs7)[:2])
ck('R7.2 如实登记：本工况 rc 仍可能因其它指纹常量未同步而 != 0（那属 D9/C19 面）', True, rc7)

print('--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
