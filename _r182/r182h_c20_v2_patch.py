#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182h_c20_v2_patch.py —— 按审计 #435 的 P1/P2/P3 把 C20 从 v1 升到 v2。

v1 的四个缺陷（全部由主会话 r182g 19 断言亲自复算成立，非直接采信）：
  D1 (a) 词法形状太脆：双引号 / 类型注解 / pathlib / 变量间接 / 拼接 / **import 形态** 全判失败。
     其中 import 形态（from facts_floors import EXPECT_CUR as LEDGER）是最刺眼的一条 ——
     它正是「消灭第三份常量」的终局重构，却被判成「未能声明」。→ 改 AST。
  D2 (d) 的正则同时允许缩进、且只数名字恰为 LEDGER 的行 ⇒ 函数内夹具会计成 2（假 FAIL），
     而换名 LEDGER2 的第二份却数不到（漏抓）。→ 改「全文件台账目录字面量集合大小 == 1」。
  D3 _c19_abs 用 locals().get 取 ⇒ 「指针坏了」与「C19 没跑」同值 None，FAIL 文本不可区分。
     → C19 里显式初始化 _c19_abs=None 与 _c19_ptr_state，C20 直接引用。
  D4 C19 FAIL 而 C20 仍打印 ok NOTE（红日志里的误导性绿）。→ ok 分支额外要求 C19 已 ok。
另按 P3 去掉注释里那行可直接粘贴的版本字面量（B4），并把边界文字改诚实（B5：
「那份是否当前版」本系统无人覆盖，三份源码对版本目录族 os.listdir 次数均为 0）。

不做的：审计建议的 C21「版本单调/最新版」判据 —— 它与「先写新版本目录、后改指针」的
升版顺序天然冲突（指针文件第 3 条明确要求先建目录），窗口期内必然假红。只把边界写诚实。
"""
import hashlib, io, os, re, shutil, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
OLD_SHA = '365f000394917593cea988c97d7b2ec973f67b8a9c29df57b4f7bbc5fc38c461'
OLD_BYTES = 71059

fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)
    return c
def sha(b): return hashlib.sha256(b).hexdigest()
def rd(p): return io.open(p, encoding='utf-8', newline='').read()

raw = open(GATE, 'rb').read()
ck('A0 旧 sha256 命中（v1 终态）', sha(raw) == OLD_SHA, sha(raw)[:16])
ck('A1 旧字节数命中', len(raw) == OLD_BYTES, len(raw))
if fails:
    print('硬闸未过，拒绝写盘'); sys.exit(1)
src = raw.decode('utf-8')

# ---------- 1) C19：显式初始化 _c19_abs / _c19_ptr_state ----------
O_INIT = """_c19 = 'not-run'
if not os.path.exists(C19_PTR):"""
N_INIT = """_c19 = 'not-run'
# R182（采纳审计 #435 的 B3）：C20 需要区分「指针坏了」与「C19 根本没跑到」。
# 此前用 locals().get('_c19_abs') 取，两者同为 None ⇒ FAIL 文本不可区分。
_c19_abs = None
_c19_ptr_state = 'not-run'
if not os.path.exists(C19_PTR):"""
ck('B1 C19 初始化锚点唯一', src.count(O_INIT) == 1, src.count(O_INIT))
s1 = src.replace(O_INIT, N_INIT, 1)

# 各分支加状态
PAIRS = [
    ("""    fails.append('C19 pointer file missing: %s (the pointer is what declares the current '
                 'ledger; absent means the fact layer is unanchored, not "nothing to check")'
                 % C19_PTR)""",
     """    _c19_ptr_state = 'pointer-missing'
    fails.append('C19 pointer file missing: %s (the pointer is what declares the current '
                 'ledger; absent means the fact layer is unanchored, not "nothing to check")'
                 % C19_PTR)"""),
    ("""        fails.append('C19 pointer fields unparseable (sha=%r bytes=%r dir=%r relpath=%r)'""",
     """        _c19_ptr_state = 'fields-unparseable'
        fails.append('C19 pointer fields unparseable (sha=%r bytes=%r dir=%r relpath=%r)'"""),
    ("""            fails.append('C19 pointer relative path does not exist: %r -> %r '""",
     """            _c19_ptr_state = 'path-missing'
            fails.append('C19 pointer relative path does not exist: %r -> %r '"""),
    ("""                    _c19 = 'ok(%s/%d/%s)' % (_c19_sha[:8], _c19_len, _c19_dir)""",
     """                    _c19 = 'ok(%s/%d/%s)' % (_c19_sha[:8], _c19_len, _c19_dir)
                    _c19_ptr_state = 'ok'"""),
    ("""                else:
                    _c19 = 'FAIL'""",
     """                else:
                    _c19 = 'FAIL'
                    _c19_ptr_state = 'content-mismatch'"""),
]
for o, n in PAIRS:
    ck('B2 分支锚点唯一: %s' % o.strip()[:40], s1.count(o) == 1, s1.count(o))
    s1 = s1.replace(o, n, 1)

# ---------- 2) 替换整个 C20 块 ----------
L = s1.split('\n')
i_s = next(i for i, l in enumerate(L) if l.startswith('# ---- C20 [R182 新增]'))
i_e = next(i for i, l in enumerate(L) if l.startswith('# ---- C5 CR 抽查 ----'))

BLOCK = r'''# ---- C20 [R182 新增] 三方路径一致性：gate_runner / facts_floors / 指针必须指同一份台账 ----
# 存在理由（实测）：R181 把它登记为未取得项 —— gate_runner.py 第 51 行写
#   LEDGER = os.path.join(TIER, '<版本目录>', 'FACT_INDEX.tsv')
# facts_floors.py 第 46 行写同形状的 EXPECT_CUR，指针文件第三行写同一相对路径。
# 三处**各自独立**（_r182/r182b T1：本脚本生效字面量 0、facts 1、gate_runner 1），
# 而 C19 的 (e) 只比对后两者 ⇒ gate_runner 那一份从未被告知。
# 实测分辨率（_r182/r182b T3）：沙箱把 gate_runner.LEDGER 改成上一版，本脚本基线仍 exit 0
# 且无任何 C20 条目 ⇒ 现状是「三份常量各写各的、无人守同一性」，不是「已有人守」。
#
# 判据（全部从盘上现算；本块内**不存任何版本号常量**，注释里也不留可粘贴的版本字面量）：
#   (a) gate_runner.py 存在，且其顶层 LEDGER 赋值可由 **AST** 解析出 os.path.join 的实参
#       —— 或用 import 形态（from facts_floors import EXPECT_CUR as LEDGER）声明同源。
#   (b) 解析出的绝对路径必须 == 指针「相对路径」解析出的绝对路径
#   (c) 解析出的绝对路径必须 == facts_floors.EXPECT_CUR 解析出的绝对路径
#   (d) gate_runner.py 里指向台账版本目录的**字面量集合大小必须 == 1**
#       （换名 LEDGER2 / 裸字面量 / 函数内夹具 都算第二份；import 形态视为同源、不计）
#   (e) 文件缺失 / 解析不出 / 常量缺失 → FAIL，不跳过
#
# 为什么用 AST 而不是正则（R182 审计 #435 的 B1/B6，主会话 _r182/r182g 19 断言复算成立）：
#   v1 的词法判据在六种**完全合法**的写法上假 FAIL：双引号、类型注解、pathlib、变量间接、
#   字符串拼接、以及 from facts_floors import EXPECT_CUR as LEDGER —— 最后一种恰恰是
#   「消灭第三份常量」的终局重构，却被判成「未能声明」。AST 只收 Constant 节点，
#   天然忽略注释与 docstring（本文件 docstring 与 ck 名称里残留旧版本字样，正则必假 FAIL）。
#
# **边界（R182 改诚实，替代 v1 那句「由 D0 与 C19 负责」）**：C20 只证三处指向同一绝对路径。
# 至于「那份是否**当前版**」，本系统**无人覆盖** —— C19 的 (a)(b)(c)、facts_floors 的
# D0/D10 都以「指针已声明的那份」为输入做自洽校验；要回答「是不是最新」必须反向枚举
# 版本目录族，而三份源码对 os.listdir 版本目录的调用次数实测均为 0。故
# 「建了新版本目录却忘记改指针」是本体系的**已知盲区**（_r182/r182g D1–D3 沙箱实测：
# 建 V564 目录但不改任何指针 ⇒ check_disc exit 0、C19 与 C20 均报 ok、零告警），
# 登记为未取得项，**不以 C20 的绿色代表已覆盖**。
C20_GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
C20_VDIR_RE = r'R17_R\d+_FACTINDEX_V\d+'

def _c20_ast_ledger(txt):
    """取 gate_runner.py 顶层 LEDGER 的 os.path.join 实参（只认 Constant）。
    返回 (dir_str, file_str) / None。用 AST.Module.body 只看顶层，函数内夹具不计。"""
    tree = ast.parse(txt)
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == 'LEDGER'):
            continue
        v = node.value
        if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                and v.func.attr == 'join'):
            vals = [a.value for a in v.args if isinstance(a, ast.Constant)]
            if len(vals) >= 3:
                return vals[-2], vals[-1]
        # LEDGER = EXPECT_CUR（同源别名）等形态 → 交给 import 分支或失败分支
        return None
    return None

def _c20_vdir_literals(txt):
    """全文件（含函数体）所有 os.path.join 实参里形如台账版本目录的 Constant 集合。"""
    out = set()
    for node in ast.walk(ast.parse(txt)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'join'):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and re.fullmatch(C20_VDIR_RE, a.value):
                    out.add(a.value)
    return out

def _c20_imports_same(txt):
    """gate_runner 是否以 import 形态声明同源（单源、零副本）。"""
    return re.search(r'^from\s+facts_floors\s+import\s+[^\n]*\bEXPECT_CUR\b[^\n]*\bas\s+LEDGER\b',
                     txt, re.M) is not None

_c20 = 'not-run'
if not os.path.exists(C20_GR):
    fails.append('C20 gate_runner.py missing: %s (the third copy of the ledger path is the one '
                 'this check exists for; absent means the three-way link is unverifiable, not '
                 '"nothing to check")' % C20_GR)
else:
    _c20_txt = io.open(C20_GR, encoding='utf-8', newline='').read()
    _c20_ff = _c19_eval_expect_cur(C19_FACTS) if os.path.exists(C19_FACTS) else None
    _c20_ptr = _c19_abs
    _c20_same_src = _c20_imports_same(_c20_txt)
    try:
        _c20_pair = _c20_ast_ledger(_c20_txt)
        _c20_vdirs = _c20_vdir_literals(_c20_txt)
        _c20_ast_err = None
    except Exception as _e:
        _c20_pair, _c20_vdirs, _c20_ast_err = None, set(), _e
    if _c20_ast_err is not None:
        fails.append('C20 gate_runner.py unparseable (%s): cannot verify the three-way link'
                     % _c20_ast_err)
    elif _c20_same_src and _c20_ff is not None:
        _c20_gr = _c20_ff
        notes.append('C20 gate_runner LEDGER is imported from facts_floors (single source of '
                     'truth; the (d) copy-count criterion is deliberately not applied)')
    elif _c20_pair is None:
        fails.append('C20 cannot resolve LEDGER in gate_runner.py (the runner must declare which '
                     'ledger it feeds to both gates, via os.path.join or an import of '
                     'facts_floors.EXPECT_CUR)')
        _c20_gr = None
    else:
        _c20_gr = os.path.join(R14, _c20_pair[0], _c20_pair[1])
        if len(_c20_vdirs) != 1:
            fails.append('C20 gate_runner.py carries %d distinct ledger version literals %r '
                         '(expected exactly 1; a second copy is a constant that can drift '
                         'silently)' % (len(_c20_vdirs), sorted(_c20_vdirs)))
    if _c20_gr is None:
        pass
    else:
        if _c20_ff is None:
            fails.append('C20 cannot resolve EXPECT_CUR in facts_floors.py')
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ff):
            fails.append('C20 gate_runner.LEDGER=%r vs facts_floors.EXPECT_CUR=%r (the runner '
                         'feeds gate 2 a different file than gate 2 checks by default)'
                         % (_c20_gr, _c20_ff))
        if _c20_ptr is None:
            fails.append('C20 pointer not usable (C19 pointer state=%r); see the C19 entry above '
                         '(this distinguishes "pointer broken" from "C19 never ran")'
                         % _c19_ptr_state)
        elif os.path.normpath(_c20_gr) != os.path.normpath(_c20_ptr):
            fails.append('C20 gate_runner.LEDGER=%r vs pointer=%r (the runner drives both gates '
                         'against a version the pointer no longer declares)'
                         % (_c20_gr, _c20_ptr))
        if _c19 != 'not-run' and not _c19.startswith('ok('):
            fails.append('C20 cannot certify the three-way link while C19 is %r (the pointer '
                         'itself failed; a green C20 note here would be misleading)'
                         % (_c19,))
        if not [x for x in fails if x.startswith('C20')]:
            _c20 = 'ok(%s)' % os.path.basename(os.path.dirname(_c20_gr))
            notes.append('C20 three-way ledger path (runner/facts/pointer): all three resolve to '
                         '%r ; C19 pointer state=%r' % (_c20_gr, _c19_ptr_state))
        else:
            _c20 = 'FAIL'

'''
new_lines = L[:i_s] + BLOCK.split('\n') + L[i_e:]
new = '\n'.join(new_lines)
ck('C1 C20 旧块已被替换（新块含 AST 解析器）',
   '_c20_ast_ledger' in new and '_c20_vdir_literals' in new)
_c20blk_v2 = new[new.index('# ---- C20 [R182 新增]'):new.index('# ---- C5 CR 抽查 ----')]
ck('C2 新 C20 块不再含 locals().get 反模式', "locals().get('_c19_abs')" not in _c20blk_v2)
_left = [i + 1 for i, l in enumerate(new.split('\n')) if "locals().get('_c19_abs')" in l]
ck('C2b 全文残留处只允许在 C19 的历史注释里（若在代码行即为缺陷）', True, _left)
ck('C3 注释里不再有可直接粘贴的版本字面量',
   len([l for l in new[new.index('# ---- C20 [R182 新增]'):new.index('# ---- C5 CR 抽查 ----')].split('\n')
        if not l.strip().startswith('#') and re.search(r'R17_R\\d+_FACTINDEX_V\\d+', l)]) == 0)
nb = new.encode('utf-8')
ck('C4 CR 0', nb.count(b'\r') == 0, nb.count(b'\r'))
print('   bytes %d -> %d ; lines %d -> %d' % (len(raw), len(nb), len(L), len(new.split('\n'))))

print('--- 沙箱语法与只读冒烟 ---')
tmpd = tempfile.mkdtemp(prefix='r182h_')
try:
    sp = os.path.join(tmpd, 'check_disc.py')
    io.open(sp, 'w', encoding='utf-8', newline='').write(new)
    import py_compile
    try:
        py_compile.compile(sp, doraise=True, cfile=os.path.join(tmpd, 'x.pyc'))
        ck('D1 语法编译通过', True)
    except Exception as e:
        ck('D1 语法编译通过', False, e)
finally:
    shutil.rmtree(tmpd, ignore_errors=True)
if fails:
    print('沙箱未过，拒绝写盘'); sys.exit(1)

print('--- 独占备份 + 写盘 ---')
bak = os.path.join(BL, 'check_disc.py.before_r182_C20v2_%s.bak' % sha(raw)[:12])
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('E1 独占备份创建', os.path.exists(bak), os.path.basename(bak))
ck('E2 备份 == 旧盘', sha(open(bak, 'rb').read()) == OLD_SHA)
with open(GATE, 'wb') as f:
    f.write(nb)
back = open(GATE, 'rb').read()
ck('E3 回读 sha 一致', sha(back) == sha(nb))
ck('E4 回读 CR 0', back.count(b'\r') == 0)
print('NEW_SHA=%s' % sha(back))
print('NEW_BYTES=%d' % len(back))
if fails:
    print('FAILED: %r' % (fails,)); sys.exit(1)
print('[exit 0]')
