#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182g_recompute_audit.py —— 复算审计员 #435 对 C20 的七条结论（规则 D：不许直接采信）。

逐条复算，全部只读 + 内存字符串（B5 另加 /tmp 沙箱实体副本，绝不软链，见 S-182e1）。
  A. B1 判别矩阵：七种「第二份台账常量」写法，(a)/(d) 各自判定
  B. B3 locals() 不可区分「指针坏」与「没跑」
  C. B4 C20 块内版本字面量：注释 3 处 / 非注释 0 处
  D. B5 空隙：建 V564 目录但不改三处指针 ⇒ 三门是否全绿（审计说全绿）
  E. B6 import 形态（from facts_floors import EXPECT_CUR as LEDGER）是否假 FAIL
  F. B2 C19 FAIL 时 C20 是否仍打印绿 NOTE
  G. B1 第 4 点：(a) 顶格锚 vs (d) 允许缩进 ⇒ 函数内夹具是否假 FAIL
"""
import ast, hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
FF = os.path.join(ROOT, '_r160', 'facts_floors.py')

fails, oks = [], []
def ck(n, c, d=''):
    (oks if c else fails).append(n)
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    return c

def rd(p): return io.open(p, encoding='utf-8', newline='').read()

# ---- 复现 C20 里的两个解析器（逐字复制判定逻辑，不改语义）----
RE_JOIN = ("^LEDGER" + "(\\s*)=\\s*os\\.path\\.join\\(\\s*TIER\\s*,\\s*'([^']+)'\\s*,\\s*'([^']+)'\\s*\\)")
RE_D = r'^\s*LEDGER\s*=\s*os\.path\.join\([^)]*FACTINDEX_V\d+'

def resolve_a(txt):
    return re.search(RE_JOIN, txt, re.M) is not None

def count_d(txt):
    return len(re.findall(RE_D, txt, re.M))

BASE = rd(GR)
print('--- A：B1 判别矩阵（七工况）---')
cases = [
    ('生产现况', BASE, True, 1),
    ('同名再赋值 LEDGER=V562', BASE + "\nLEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n", True, 2),
    ('换名 LEDGER2=V562', BASE + "\nLEDGER2 = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n", True, 1),
    ('换名 LEDGER_ALT=V562', BASE + "\nLEDGER_ALT = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n", True, 1),
    ('裸字面量 X=os.path.join', BASE.replace(
        "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')",
        "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')\nX = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')"),
     True, 1),
    ('拼接写法 V5+\'62\'', BASE.replace(
        "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')",
        "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_' + 'V563', 'FACT_INDEX.tsv')"),
     False, 0),
    ('函数内缩进夹具', BASE + "\ndef _fix():\n    LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n    return LEDGER\n",
     True, 2),
]
rows = []
for name, txt, exp_a, exp_d in cases:
    a, d = resolve_a(txt), count_d(txt)
    rows.append((name, a, d, exp_a, exp_d))
    print('   %-24s (a)=%-5s (d)=%d   [审计预期 a=%s d=%s] %s'
          % (name, a, d, exp_a, exp_d, 'OK' if (a, d) == (exp_a, exp_d) else 'DIFF'))
ck('A1 审计矩阵六工况与我的复算逐格一致',
   all((a, d) == (ea, ed) for _, a, d, ea, ed in rows if _ != '换名 LEDGER2=V562'),
   [r[0] for r in rows if (r[1], r[2]) != (r[3], r[4])])
# S-182g1：审计表里写「LEDGER2=V562 ⇒ (d) 计数 0 ⇒ 报 declares 0」，我复算 (d)=1（它是 1，因为
# 原有那份 LEDGER 行仍被数到）。区别不改变结论（都不报「第二份」），但数字要订正。
r_led2 = [r for r in rows if r[0] == '换名 LEDGER2=V562'][0]
print('   订正：审计表写 (d)=0 实为 %d（报的错是「多了一份但没被抓」，不是「第一份都没了」）' % r_led2[2])
ck('A2 换名形态下 (a) 仍解析成功（故不会报 cannot resolve）⇒ 审计那格需订正',
   r_led2[1] is True, r_led2[1])
ck('A3 换名形态整体判定：C20 对它仍绿（漏抓确认）',
   r_led2[1] is True and r_led2[2] == 1)
ck('A4 函数内缩进夹具 (d) 计数 2 ⇒ 假 FAIL 确认', rows[-1][2] == 2, rows[-1][2])
ck('A5 拼接写法 (a) 解析失败 ⇒ 假 FAIL 确认', rows[5][1] is False)

print('\n--- E：B6 import 形态（本判据最该支持的终局重构）---')
imported = BASE.replace(
    "LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')",
    "from facts_floors import EXPECT_CUR as LEDGER")
ck('E1 import 形态下 (a) 解析失败 ⇒ 报 cannot resolve LEDGER（假 FAIL 确认）',
   resolve_a(imported) is False)
ck('E2 import 形态下 (d) 计数 0', count_d(imported) == 0, count_d(imported))
ck('E3 import 形态在语义上等价（LEDGER 与 EXPECT_CUR 同源）',
   'EXPECT_CUR as LEDGER' in imported)

print('\n--- C：B4 C20 块内版本字面量 ---')
L = rd(GATE).split('\n')
s = next(i for i, l in enumerate(L) if l.startswith('# ---- C20 [R182 新增]'))
e = next(i for i, l in enumerate(L) if l.startswith('# ---- C5 CR 抽查 ----'))
blk = '\n'.join(L[s:e])
raw = len(re.findall(r'R17_R13\d+_FACTINDEX_V\d+', blk))
noncomment = len([l for l in blk.split('\n') if not l.strip().startswith('#')
                  and re.search(r'R17_R13\d+_FACTINDEX_V\d+', l)])
anyV = len(re.findall(r'V\d+', blk))
print('   块 %d 行；FACTINDEX 版本字面量 raw=%d / 非注释行=%d；任意 V<数字> 共 %d 处'
      % (e - s, raw, noncomment, anyV))
ck('C1 非注释行版本字面量 0 处（代码侧无硬编码）', noncomment == 0, noncomment)
# v2 之后这两条**方向反转**：审计指出的「注释里有 1 处可直接粘贴的版本字面量」与
# 「注释里 3 处 V<数字>」应双双归零。这不是判据失效，是判据在追赶修复（S-182g2）。
ck('C2 v2 后注释里可粘贴的版本字面量必须归零（审计 B4 已被采纳）', raw == 0, raw)
ck('C3 v2 后注释里 V<数字> 必须归零', anyV == 0, anyV)

print('\n--- B：B3 locals() 不可区分 ---')
# 模拟：指针字段不可解析时 C19 不绑定 _c19_abs
def sim(pt_text):
    ns = {}
    m1 = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', pt_text)
    m2 = re.search(r'\| 字节数 \| (\d+) \|', pt_text)
    m3 = re.search(r'\| 版本目录 \| (\S+) \|', pt_text)
    m4 = re.search(r'\| 相对路径 \| (\S+) \|', pt_text)
    if m1 and m2 and m3 and m4:
        ns['_c19_abs'] = os.path.join(ROOT, m4.group(1))
    return ns.get('_c19_abs')
pt = rd(os.path.join(TIER, 'FACT_INDEX_CURRENT.md'))
ok_val = sim(pt)
bad_val = sim(pt.replace('| 版本目录 | ', '| 版本目录X | '))
ck('B1 正常指针 ⇒ 取到路径', ok_val is not None)
ck('B2 字段不可解析 ⇒ 取到 None（与「C19 没跑」同值，不可区分）', bad_val is None)
ck('B3 与审计结论一致：两种失败形态在 C20 侧都表现为 None', bad_val is None and ok_val is not None)

print('\n--- D：B5 空隙（建 V564 但不改三处指针 ⇒ 三门全绿？）---')
def mirror(mutate):
    tmpd = tempfile.mkdtemp(prefix='r182g_')
    try:
        sb = os.path.join(tmpd, 'gatesb')
        os.makedirs(sb)
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
        OVR = {'check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv',
               'R14_COMMON.md', 'STATUS_BOARD.md', 'FACT_INDEX_CURRENT.md'}
        for name in os.listdir(TIER):
            if name in OVR:
                continue
            os.symlink(os.path.join(TIER, name), os.path.join(tdir, name))
        for name in OVR:
            shutil.copy2(os.path.join(TIER, name), os.path.join(tdir, name))
        for d, f in (('_r160', 'facts_floors.py'), ('_r161', 'gate_runner.py')):
            dd = os.path.join(sb, d)
            if os.path.islink(dd):
                raise RuntimeError('S-182e1 guard: %s is symlink' % dd)
            os.makedirs(dd, exist_ok=True)
            # facts_floors 的 ROOT 由自身位置反推 ⇒ 放在 sb/_r160 下即指向 sb
            shutil.copy2(os.path.join(ROOT, d, f), os.path.join(dd, f))
        mutate(tmpd, sb, tdir)
        env = dict(os.environ); env['PYTHONDONTWRITEBYTECODE'] = '1'
        gate = subprocess.run([sys.executable, os.path.join(tdir, 'check_disc.py')],
                              capture_output=True, text=True, cwd=tdir, env=env, timeout=600)
        facts = subprocess.run([sys.executable, os.path.join(sb, '_r160', 'facts_floors.py')],
                               capture_output=True, text=True, cwd=sb, env=env, timeout=600)
        return (gate.returncode, gate.stdout + gate.stderr,
                facts.returncode, facts.stdout + facts.stderr)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

def m_v564(t, sb, td):
    """建 V564 目录（内容与 V563 相同），三处指针**一个都不改**。"""
    # V563 在镜像里是软链（只读区）⇒ 用**读**方式取内容，写到实体新目录 V564，
    # 不对软链做任何写/删（S-182e1 事故根因就是「对软链目录做写操作」）。
    src = os.path.join(td, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
    dst = os.path.join(td, 'R17_R131_FACTINDEX_V564')
    if os.path.islink(dst):
        raise RuntimeError('sandbox V564 is symlink; refusing')
    os.makedirs(dst, exist_ok=True)
    raw = open(src, 'rb').read()
    with open(os.path.join(dst, 'FACT_INDEX.tsv'), 'wb') as f:
        f.write(raw)
    assert os.path.islink(dst) is False

grc, gout, frc, fout = mirror(m_v564)
print('   check_disc exit=%d ; facts_floors exit=%d' % (grc, frc))
print('   C19 行: %s' % [l.strip()[:90] for l in gout.split('\n') if 'C19 fact-layer link:' in l])
print('   C20 行: %s' % [l.strip()[:90] for l in gout.split('\n') if 'C20 three-way' in l])
ck('D1 B5 空隙确认：建 V564 但不改指针 ⇒ check_disc exit 0', grc == 0, grc)
ck('D2 facts_floors 也 exit 0', frc == 0, frc)
ck('D3 C19/C20 均报 ok（无任何告警）',
   'C19 fact-layer link: ok(' in gout and 'C20 three-way ledger path: ok(' in gout)

print('\n--- F：B2 C19 FAIL 时 C20 是否仍打印绿 NOTE ---')
def m_ff_drift(t, sb, td):
    """让 facts CUR_SHA256 与现盘脱钩 ⇒ C19 应 FAIL；C20 的三方路径仍相等。"""
    p = os.path.join(sb, '_r160', 'facts_floors.py')
    txt = rd(p)
    if os.path.islink(p):
        raise RuntimeError('facts is symlink')
    io.open(p, 'w', encoding='utf-8', newline='').write(
        re.sub(r"^CUR_SHA256 = '[0-9a-f]{64}'", "CUR_SHA256 = '%s'" % ('0' * 64), txt, count=1, flags=re.M))
grc2, gout2, frc2, fout2 = mirror(m_ff_drift)
c19f = [l.strip()[:80] for l in gout2.split('\n') if 'C19' in l and 'FAIL' in l]
c20ok = 'C20 three-way ledger path: ok(' in gout2
print('   check_disc exit=%d ; C19 FAIL 行 %d 条 ; C20 ok 行 %s' % (grc2, len(c19f), c20ok))
for l in c19f[:3]: print('     ', l)
ck('F1 该工况 check_disc exit 1（门级不假绿）', grc2 == 1, grc2)
# v2 之后方向反转：C19 红时 C20 不得报 ok，且必须给出「cannot certify」FAIL。
c20cert = any('C20 cannot certify the three-way link while C19' in l for l in gout2.split('\n'))
ck('F2 v2 后 C19 红时 C20 不再打印 ok 行（审计 B2 已被采纳）', not c20ok, c20ok)
ck('F2b v2 后 C19 红时 C20 给出 cannot-certify FAIL', c20cert, c20cert)

print('\n--- 汇总 ---')
print('--- 附：v2 逐条采纳状态 ---')
for nm, done in (('B1 (a) 改 AST（双引号/注解/pathlib/拼接/import 全过）', True),
                 ('B1b (d) 改字面量集合大小（换名副本也被抓）', True),
                 ('B3 locals().get → _c19_ptr_state 显式状态', True),
                 ('B2/B5 C19 红时 C20 不再报绿', True),
                 ('B4 注释去掉可粘贴版本字面量', True),
                 ('B5 边界文字改诚实（当前版无人覆盖）', True),
                 ('B5b 新增 C21 版本单调判据 —— 未采纳（与升版顺序冲突，审计也不建议）', False)):
    print('   [%s] %s' % ('已采纳' if done else '未采纳', nm))
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
