#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182i_c20_v2_fix.py —— 修 C20 v2 的一处实测缺陷（S-182h1）。

事故形态：v2 的 _c20_ast_ledger 写了 `if len(vals) >= 3:`，而 os.path.join(TIER, VDIR, FILE)
的 Constant 实参只有 **2** 个（TIER 是 Name 节点，不是 Constant）⇒ 判据返回 None ⇒
生产 check_disc 立刻 exit 1 并报 cannot resolve LEDGER。**这是可失败断言当场抓出的**
（上生产后第一次实跑就红），没有进入任何结论。

正确判据：Constant 实参 >= 2，取最后两个（目录段 + 文件名段）。
"""
import hashlib, io, os, shutil, sys, tempfile
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
OLD_SHA = 'a3fa11e2fc04eec5c60dfdb5049f729b415f0e32f0670fc4da99a5fa6a20e119'
OLD_BYTES = 75065

fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c
def sha(b): return hashlib.sha256(b).hexdigest()

raw = open(GATE, 'rb').read()
ck('A0 旧 sha 命中（v2 首版）', sha(raw) == OLD_SHA, sha(raw)[:16])
ck('A1 旧字节命中', len(raw) == OLD_BYTES, len(raw))
if fails: sys.exit(1)
src = raw.decode('utf-8')

O = "            if len(vals) >= 3:\n                return vals[-2], vals[-1]"
N = ("            # S-182h1：os.path.join(TIER, VDIR, FILE) 的 Constant 实参只有 2 个\n"
     "            # （TIER 是 ast.Name 不是 Constant）。首版写 >= 3 ⇒ 恒返回 None ⇒ 生产假红。\n"
     "            if len(vals) >= 2:\n                return vals[-2], vals[-1]")
ck('B1 锚点唯一', src.count(O) == 1, src.count(O))
new = src.replace(O, N, 1)
nb = new.encode('utf-8')
ck('B2 CR 0', nb.count(b'\r') == 0)

# 沙箱先验证解析器本身能取到生产文件
tmpd = tempfile.mkdtemp(prefix='r182i_')
try:
    import ast, re
    blk = new[new.index('def _c20_ast_ledger'):new.index('def _c20_vdir_literals')]
    ns = {'ast': ast, 're': re}
    exec(blk, ns)
    got = ns['_c20_ast_ledger'](io.open(os.path.join(ROOT, '_r161', 'gate_runner.py'),
                                        encoding='utf-8').read())
    ck('C1 修正后解析器能取到 (dir, file)', got == ('R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv'), got)
    # 反控：import 形态必须返回 None（交给 import 分支）
    imp = "from facts_floors import EXPECT_CUR as LEDGER\n"
    ck('C2 反控：import 形态返回 None（由 import 分支处理）',
       ns['_c20_ast_ledger'](imp) is None)
    # 反控：函数内夹具不计（只看顶层）
    fix = ("LEDGER = 1\n"
           "def f():\n    LEDGER = os.path.join(TIER, 'R17_R131_FACTINDEX_V562', 'FACT_INDEX.tsv')\n")
    ck('C3 反控：函数内夹具不计入顶层解析', ns['_c20_ast_ledger'](fix) is None)
finally:
    shutil.rmtree(tmpd, ignore_errors=True)

bak = os.path.join(BL, 'check_disc.py.before_r182_C20v2fix_%s.bak' % sha(raw)[:12])
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('D1 独占备份', os.path.exists(bak), os.path.basename(bak))
with open(GATE, 'wb') as f:
    f.write(nb)
back = open(GATE, 'rb').read()
ck('D2 回读一致', sha(back) == sha(nb))
print('NEW_SHA=%s' % sha(back))
print('NEW_BYTES=%d' % len(back))
if fails:
    print('FAILED %r' % (fails,)); sys.exit(1)
print('[exit 0]')
