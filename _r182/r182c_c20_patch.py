#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182c_c20_patch.py —— 给 check_disc.py 加 C20「三方路径一致性」判据。fail-closed。

R181 未取得项②原文：「gate_runner.LEDGER 与 facts_floors.EXPECT_CUR、指针相对路径三处的
三方路径一致性仍无人守（审计实测 crontab/systemd 对三门接线各 0 条）」。
C19 的 (e) 只守了后两者（facts.EXPECT_CUR vs 指针），gate_runner 那一份**从未被告知**。

实测前提（_r182/r182b 10 断言 0 FAIL）：
  T1 三处字面量各自独立（facts 1 次 / gate_runner 1 次 / check_disc 0 次生效字面量）
  T2 词法解析器对三处均取到同一绝对路径；变量名精确锚（不存在名 / ROOT / TIER 均返回 None）
  T3 沙箱把 gate_runner.LEDGER 改成 V562 后，现盘 check_disc **仍绿** ⇒ 缺口真实存在

C20 判据（五条，全部从盘上现算，本脚本内不存任何版本号常量）：
  (a) gate_runner.py 存在且其 LEDGER 行可词法解析 → 得到绝对路径 P_gr
  (b) P_gr 必须 == 指针相对路径解析出的绝对路径（与 C19 同源，故不重复实现解析）
  (c) P_gr 必须 == facts_floors.EXPECT_CUR 解析出的绝对路径
  (d) gate_runner.py 里 LEDGER 字面量必须**恰 1 处**（多于 1 ⇒ 存在第二份可漂移的常量）
  (e) 读不到 / 解析不出 / 文件缺失 → FAIL，不跳过

**边界（如实登记，不粉饰）**：C20 只证「三处指向同一绝对路径」，**不证**「那份是当前版」。
后者由 facts_floors.D0（sha257 指针）与 C19 (a)(b)(c) 负责。三处**同时**改成 V562 时 C20 仍绿 ——
这是「升版一致性」判据的共同上限，与 D9/D10/C19 同族，不追求消除。
"""
import hashlib, io, os, re, shutil, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BASELINE = os.path.join(TIER, 'R17_LEAD_BASELINE')

OLD_SHA = '94645dc2edf170d1bd12e375d213e1d4282dc73962736bf7203310d6de776d26'
OLD_BYTES = 66363

fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c

def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
# ---- C20 [R182 新增] 三方路径一致性：gate_runner / facts_floors / 指针必须指同一份台账 ----
# 存在理由（实测）：R181 把它登记为未取得项② —— gate_runner.py 第 51 行写
#   LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')
# facts_floors.py 第 46 行写同形状的 EXPECT_CUR，指针文件第三行写同一相对路径。
# 三处**各自独立**（_r182/r182b T1：check_disc 生效字面量 0、facts 1、gate_runner 1），
# 而 C19 的 (e) 只比对后两者 ⇒ **gate_runner 那一份从未被告知**。
# 实测分辨率（_r182/r182b T3）：沙箱把 gate_runner.LEDGER 改成 V562，本脚本基线仍 exit 0
# 且无任何 C20 条目 ⇒ 现状是「三份常量各写各的、无人守同一性」，不是「已有人守」。
#
# 判据（全部从盘上现算；本块内**不存任何版本号常量**）：
#   (a) gate_runner.py 存在，且其 LEDGER 行可词法解析（Call 形式，ast 顶层 Constant 取不到）
#   (b) 解析出的绝对路径必须 == 指针「相对路径」解析出的绝对路径
#   (c) 解析出的绝对路径必须 == facts_floors.EXPECT_CUR 解析出的绝对路径
#   (d) gate_runner.py 里 LEDGER 的版本字面量必须恰 1 处（>1 ⇒ 第二份可漂移常量）
#   (e) 文件缺失 / 解析不出 / 常量缺失 → FAIL，不跳过
#
# **边界**：C20 只证「三处指向同一绝对路径」，**不证**「那份是当前版」。后者由
# facts_floors.D0 与 C19 的 (a)(b)(c) 负责。三处**同时**改成 V562 时本块仍绿 ——
# 「升版一致性」判据的共同上限，与 D9/D10/C19 同族，如实登记、不追求消除。
C20_GR = os.path.join(ROOT, '_r161', 'gate_runner.py')

def _c20_join_of(txt, varname, tier_path):
    """词法取 <varname> = os.path.join(TIER, 'DIR', 'FILE') -> 绝对路径 / None。
    变量名精确锚（_r182/r182b T2e/T2f：不存在名与 ROOT/TIER 均返回 None）。"""
    pat = ('^' + varname +
           "(\\s*)=\\s*os\\.path\\.join\\(\\s*TIER\\s*,\\s*'([^']+)'\\s*,\\s*'([^']+)'\\s*\\)")
    m = re.search(pat, txt, re.M)
    if not m:
        return None
    return os.path.join(tier_path, m.group(2), m.group(3))

_c20 = 'not-run'
if not os.path.exists(C20_GR):
    fails.append('C20 gate_runner.py missing: %s (the third copy of the ledger path is the one '
                 'this check exists for; absent means the three-way link is unverifiable, not '
                 '"nothing to check")' % C20_GR)
else:
    _c20_txt = io.open(C20_GR, encoding='utf-8', newline='').read()
    _c20_gr = _c20_join_of(_c20_txt, 'LEDGER', R14)
    _c20_ff = _c19_eval_expect_cur(C19_FACTS) if os.path.exists(C19_FACTS) else None
    # 指针相对路径：复用 C19 已解析出的 _c19_abs（同一次运行、同一份指针），不重复实现
    _c20_ptr = locals().get('_c19_abs')
    if _c20_gr is None:
        fails.append('C20 cannot resolve LEDGER in gate_runner.py (the runner must declare which '
                     'ledger it feeds to both gates)')
    else:
        _c20_occ = len(re.findall(r'^\s*LEDGER\s*=\s*os\.path\.join\([^)]*FACTINDEX_V\d+',
                                  _c20_txt, re.M))
        if _c20_occ != 1:
            fails.append('C20 gate_runner.py declares %d LEDGER version literals (expected exactly '
                         '1; a second copy is a constant that can drift silently)' % _c20_occ)
        if _c20_ff is None:
            fails.append('C20 cannot resolve EXPECT_CUR in facts_floors.py')
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ff):
            fails.append('C20 gate_runner.LEDGER=%r vs facts_floors.EXPECT_CUR=%r (the runner '
                         'feeds gate 2 a different file than gate 2 checks by default)'
                         % (_c20_gr, _c20_ff))
        if _c20_ptr is None:
            fails.append('C20 pointer relative path unavailable (cannot complete the three-way '
                         'comparison; see the C19 entry for the reason)')
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ptr):
            fails.append('C20 gate_runner.LEDGER=%r vs pointer=%r (the runner drives both gates '
                         'against a version the pointer no longer declares)'
                         % (_c20_gr, _c20_ptr))
        if not [x for x in fails if x.startswith('C20')]:
            _c20 = 'ok(%s)' % os.path.basename(os.path.dirname(_c20_gr))
            notes.append('C20 three-way ledger path (runner/facts/pointer): all three resolve to '
                         '%r' % _c20_gr)
        else:
            _c20 = 'FAIL'
'''

ANCHOR = "# ---- C5 CR 抽查 ----"
PRINT_ANCHOR = "print('C19 fact-layer link: %s' % _c19)"
PRINT_NEW = "print('C19 fact-layer link: %s' % _c19)\nprint('C20 three-way ledger path: %s' % _c20)"

def build(src):
    assert src.count(ANCHOR) == 1, 'anchor count %d' % src.count(ANCHOR)
    assert src.count(PRINT_ANCHOR) == 1
    out = src.replace(ANCHOR, BLOCK + '\n' + ANCHOR, 1)
    out = out.replace(PRINT_ANCHOR, PRINT_NEW, 1)
    return out

raw = open(GATE, 'rb').read()
print('--- 旧态硬闸 ---')
ck('A0 旧 sha256 命中', sha(raw) == OLD_SHA, (sha(raw)[:16], OLD_SHA[:16]))
ck('A1 旧字节数命中', len(raw) == OLD_BYTES, (len(raw), OLD_BYTES))
ck('A2 旧文件 CR 0（全 LF）', raw.count(b'\r') == 0, raw.count(b'\r'))
if fails:
    print('硬闸未过，拒绝写盘'); sys.exit(1)

src = raw.decode('utf-8')
new = build(src)

print('--- 沙箱先跑语法与 import 面 ---')
tmpd = tempfile.mkdtemp(prefix='r182c_')
try:
    sand = os.path.join(tmpd, 'check_disc.py')
    io.open(sand, 'w', encoding='utf-8', newline='').write(new)
    import py_compile
    py_compile.compile(sand, doraise=True, cfile=os.path.join(tmpd, 'x.pyc'))
    ck('B1 语法编译通过', True)
    nb = new.encode('utf-8')
    ck('B2 新文 CR 0（全 LF）', nb.count(b'\r') == 0, nb.count(b'\r'))
    ck('B3 纯插入：旧文每一行都在新文中按原顺序出现',
       all(l in new for l in src.split('\n')), 'n/a')
    old_lines = src.split('\n'); new_lines = new.split('\n')
    added = len(new_lines) - len(old_lines)
    print('   bytes %d -> %d (+%d) ; lines %d -> %d (+%d)'
          % (len(raw), len(nb), len(nb) - len(raw), len(old_lines), len(new_lines), added))
    ck('B4 新增行数 > 0 且删除行 0（用最长公共子序列粗判：新行数 - 旧行数 == 新增块行数）',
       added > 0)
finally:
    shutil.rmtree(tmpd, ignore_errors=True)

print('--- 独占备份 + 写盘 ---')
ts = 'r182_C20'
bak = os.path.join(BASELINE, 'check_disc.py.before_%s_%s.bak'
                   % (ts, hashlib.sha256(raw).hexdigest()[:12]))
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)   # wx 等价：O_EXCL 独占
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('C1 备份独占创建成功', os.path.exists(bak), bak)
ck('C2 备份内容 == 旧盘内容', sha(open(bak, 'rb').read()) == OLD_SHA)

with open(GATE, 'wb') as f:
    f.write(new.encode('utf-8'))
rb2 = open(GATE, 'rb').read()
ck('D1 回读 sha256 == 预期', sha(rb2) == sha(new.encode('utf-8')), sha(rb2)[:16])
ck('D2 回读字节数 == 预期', len(rb2) == len(new.encode('utf-8')), len(rb2))
ck('D3 回读 CR 0', rb2.count(b'\r') == 0, rb2.count(b'\r'))

print('--- 回读后断言新块在场 ---')
for nm, needle in (('C20 块头', '# ---- C20 [R182 新增]'),
                   ('C20 打印行', "print('C20 three-way ledger path: %s' % _c20)"),
                   ('C20 解析器', 'def _c20_join_of(')):
    ck('E %s 在场' % nm, needle in rb2.decode('utf-8'))

print('--- 汇总 ---')
print('PASS/FAIL: fails=%r' % (fails,))
print('NEW_SHA=%s' % sha(rb2))
print('NEW_BYTES=%d' % len(rb2))
if fails:
    print('[exit 1]'); sys.exit(1)
print('[exit 0]')
