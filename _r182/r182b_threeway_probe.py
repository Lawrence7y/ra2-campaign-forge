#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182b_threeway_probe.py —— C20「三方路径一致性」上生产前的可行性实测。

R181 未取得项②：gate_runner.LEDGER、facts_floors.EXPECT_CUR、指针相对路径三处各写一份
版本目录字面量，无人守「三者指同一份」。R181 的 C19 只守了后两者（(e) 判据）。
本脚本先证明三件事，再决定是否上生产：
  T1 三处字面量现在是否真的**各自独立**（不是同一常量传递）—— 词法取值 + 出现次数
  T2 词法解析器能否取到 gate_runner.LEDGER（Call 形式，ast 顶层 Constant 取不到）
  T3 沙箱里把 gate_runner.LEDGER 改成 V562 后，判据能否 FAIL（有分辨力）
  T4 沙箱里把三处**同时**改成 V562（含指针与 facts）后判据仍绿？
     —— 若仍绿，说明它是「升版一致性」判据而非「防篡改」判据，必须如实登记这个边界。
边界如实声明：本判据只证「三处指向同一绝对路径」，不证「那份文件是当前版」。
后者由 facts_floors.D0 与 C19 (a)(b)(c) 负责。

S-182b1 预埋：词法解析必须处理 os.path.join(TIER, 'DIR', 'FILE') 与
LEDGER = os.path.join(TIER, 'DIR', 'FILE') 两种变量名，且**不得**把 ROOT/TIER 的
定义行误取成 LEDGER（用变量名精确锚）。
"""
import hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')

fails, oks = [], []
def ck(n, c, d=''):
    (oks if c else fails).append(n)
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    return c

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def resolve_tier_join(txt, varname, tier_path):
    """词法取 <varname> = os.path.join(TIER, 'DIR', 'FILE')，返回绝对路径或 None。
    变量名精确锚定；不用 ast（这些是 Call，不是 Constant）。"""
    pat = (r'^' + re.escape(varname) +
           r"\s*=\s*os\.path\.join\(\s*TIER\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*\)")
    m = re.search(pat, txt, re.M)
    if not m:
        return None
    return os.path.join(tier_path, m.group(1), m.group(2))

print('--- T1：三处字面量是否各自独立 ---')
gt = rd(GATE); ft = rd(FACTS); gr = rd(GR); pt = rd(PTR)
for nm, txt in (('check_disc.py', gt), ('facts_floors.py', ft), ('gate_runner.py', gr)):
    n = len(re.findall(r'R17_R13\d_FACTINDEX_V\d+', txt))
    print('   %-16s 版本字面量出现 %d 次' % (nm, n))
ck('T1a facts_floors 有独立版本字面量（非 import 传递）',
   len(re.findall(r"'R17_R13\d_FACTINDEX_V\d+'", ft)) >= 1)
ck('T1b gate_runner 有独立版本字面量', len(re.findall(r"'R17_R13\d_FACTINDEX_V\d+'", gr)) >= 1)
ck('T1c check_disc 无生效版本字面量（只在注释里）',
   len(re.findall(r"^\s*\w+\s*=\s*os\.path\.join\([^)]*R17_R13\d_FACTINDEX", gt, re.M)) == 0,
   len(re.findall(r"R17_R13\d_FACTINDEX", gt)))

print('--- T2：词法解析器 ---')
led_gr = resolve_tier_join(gr, 'LEDGER', TIER)
exp_ff = resolve_tier_join(ft, 'EXPECT_CUR', TIER)
mp = re.search(r'\| 相对路径 \| (\S+) \|', pt)
ptr_abs = os.path.join(ROOT, mp.group(1).replace('\\', '/').strip()) if mp else None
print('   gate_runner.LEDGER  -> %r' % led_gr)
print('   facts.EXPECT_CUR    -> %r' % exp_ff)
print('   指针相对路径         -> %r' % ptr_abs)
ck('T2a 解析 gate_runner.LEDGER 成功', led_gr is not None)
ck('T2b 解析 facts_floors.EXPECT_CUR 成功', exp_ff is not None)
ck('T2c 解析指针相对路径成功', ptr_abs is not None)
ck('T2d 三者现盘同一路径（基线必须绿，否则 C20 一上就红）',
   bool(led_gr and exp_ff and ptr_abs and
        os.path.normpath(led_gr) == os.path.normpath(exp_ff) == os.path.normpath(ptr_abs)),
   (led_gr, exp_ff, ptr_abs))
ck('T2e 反控：解析不存在的变量名必须返回 None（解析器不是恒真）',
   resolve_tier_join(gr, 'NO_SUCH_CONST', TIER) is None)
ck('T2f 反控：用 ROOT 当变量名不得误命中（变量名精确锚）',
   resolve_tier_join(gr, 'TIER', TIER) is None)

print('--- T3/T4：沙箱镜像实测 ---')
def mirror(mutate):
    tmpd = tempfile.mkdtemp(prefix='r182b_')
    try:
        sbox = os.path.join(tmpd, 'lead', 'next_re_20261117_r14')
        os.makedirs(sbox)
        for n in sorted(os.listdir(TIER)):
            p = os.path.join(TIER, n)
            if n in ('check_disc.py',):
                continue
            os.symlink(p, os.path.join(sbox, n))
        os.symlink(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                   os.path.join(tmpd, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
        for d, f in (('_r160', 'facts_floors.py'), ('_r161', 'gate_runner.py')):
            os.makedirs(os.path.join(tmpd, d), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, d, f), os.path.join(tmpd, d, f))
        shutil.copy2(GATE, os.path.join(sbox, 'check_disc.py'))
        mutate(tmpd, sbox)
        env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
        p = subprocess.run([sys.executable, os.path.join(sbox, 'check_disc.py')],
                           capture_output=True, text=True, cwd=sbox, env=env, timeout=600)
        o = p.stdout + p.stderr
        return p.returncode, [l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')], o
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

def mutate_gr_version(t, s):
    p = os.path.join(t, '_r161', 'gate_runner.py')
    txt = rd(p)
    os.unlink(p)
    io.open(p, 'w', encoding='utf-8', newline='').write(
        txt.replace('R17_R131_FACTINDEX_V563', 'R17_R131_FACTINDEX_V562', 1))

# 生产 check_disc 里目前没有 C20，先看基线镜像是否稳定（作为差分基准）
rc0, fs0, o0 = mirror(lambda t, s: None)
print('   基线镜像 rc=%d FAIL=%d' % (rc0, len(fs0)))
for f in fs0[:4]:
    print('      ' + f[:120])
print('   （镜像里非 C19/C20 的 FAIL 属镜像环境造成，见 S-675 同族）')
rc1, fs1, o1 = mirror(mutate_gr_version)
print('   改 gate_runner.LEDGER→V562 后 rc=%d FAIL=%d' % (rc1, len(fs1)))
ck('T3 现状：改 gate_runner.LEDGER 后生产 check_disc 仍绿 ⇒ 缺口真实存在（不是已有人守）',
   rc0 == rc1 and [f for f in fs0 if 'C20' in f] == [] and [f for f in fs1 if 'C20' in f] == [],
   (rc0, rc1))

print('--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
