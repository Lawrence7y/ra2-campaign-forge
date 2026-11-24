# -*- coding: utf-8 -*-
# _gv_build_fixtures.py —— 真违规样本构建器（★测试数据，仅静态 AST 分析用，禁止执行）
# 样本素材尽量取自仓内既有字节（母本 qc151 / 既有门禁码），不新写任何可运行采样实现。
import hashlib, pathlib, re, json

R = pathlib.Path('D:/Project/ra2-campaign-forge')
FX = R / 'lead/gate_validate_20261108/_gv_fixtures'

mother_path = R / 'lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'
mother = mother_path.read_text(encoding='utf-8')
mlines = mother.splitlines()

# 从母本既有字节提取素材（不手工新写 API 名）
OPENPROC_LINE = None
for ln in mlines:
    if 'OpenProcess(' in ln and '=' in ln:
        OPENPROC_LINE = ln
        break
API_NAME = re.search(r'(\w+)\(', OPENPROC_LINE).group(1).split('.')[-1]  # OpenProcess
assert API_NAME == 'OpenProcess', API_NAME
# 三个会话级字面从既有门禁码字节中提取（_gv_gates/1552e9fe.py 的启动正则）
gate_src = (R / 'lead/gate_validate_20261108/_gv_gates/1552e9fe.py').read_text(encoding='utf-8')
gm, rl, yu = re.search(r'\((gamemd)\|', gate_src).group(1), re.search(r'\|(ra2loader)\|', gate_src).group(1), re.search(r'\|(YURI)\)', gate_src).group(1)

DOC6 = ''.join('## %d 节%d\n\n内容占位。\n\n' % (i, i) for i in range(1, 7))

def w(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')
    return p

made = []

# ---------- caseA: 新建脚本 subprocess 启动游戏进程（真违规） ----------
caseA = FX / 'caseA'
w(caseA / 'SPEC.md', '# caseA 交付说明\n\n' + DOC6 + '验收：本域仅含一个启动游戏的违规样本脚本，用于门禁回归。\n')
evil = '''# -*- coding: utf-8 -*-
# 【真违规样本 A】门禁回归测试数据 —— 模拟「新建脚本以 subprocess 启动游戏进程」。
# ★ 禁止执行本件：它只应被静态检查器（AST）读取。launch/launch_never 均为死代码定义。
import subprocess


def launch():
    subprocess.Popen(['%s.exe', '-win'])
    subprocess.run(['%s.exe'])


def launch_never():
    if False:
        subprocess.check_output(['%s.exe'])
''' % (gm, rl, yu)
w(caseA / '_evil_launcher.py', evil)

# ---------- caseB: 派生副本（对照=逐字节相同）与 派生+1新增调用边（真违规） ----------
caseB = FX / 'caseB'
w(caseB / 'SPEC.md', '# caseB 交付说明\n\n' + DOC6 + '验收：derived_same 应判派生放行；derived_plus1 含新增调用边应判 FAIL。\n')
# 注意：用字节模式写副本，避免文本模式 LF→CRLF 转换改变哈希（实测会把副本变成
# b2b_candidate_20261106/qc151_trip.candidate.py（CRLF 版）的孪生而非预期母本）
mb_bytes_raw = mother_path.read_bytes()
(caseB / 'qc151_trip.derived_same.py').write_bytes(mb_bytes_raw)
tail = b'\n' if not mb_bytes_raw.endswith(b'\n') else b''
plus1_bytes = mb_bytes_raw + tail + ('\n\nif False:  # 【真违规样本 B】静态测试用死分支：复制母本既有语句一次，制造 1 条新增调用边\n'
                                    + OPENPROC_LINE + '\n').encode('utf-8')
(caseB / 'qc151_trip.derived_plus1.py').write_bytes(plus1_bytes)
mother = None  # 防误用：后续一律字节模式

# ---------- caseC: 双件并存且均无关系声明（真违规） ----------
caseC = FX / 'caseC'
w(caseC / 'Alpha_Report.md', '# Alpha 交付件\n\n' + DOC6 + '（本件无绑定行、无关系声明——违规样本 C）\n')
w(caseC / 'Beta_Report.md', '# Beta 交付件\n\n' + DOC6 + '（本件无绑定行、无关系声明——违规样本 C）\n')

# ---------- caseD: 伪造/失配/缺失的指纹锚（真违规 ×3）+ 正确锚对照 ----------
caseD = FX / 'caseD'
mb = (R / 'lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md').read_bytes()
mb_hash, mb_bytes = hashlib.sha256(mb).hexdigest(), len(mb)
w(caseD / 'd0_correct' / 'SPEC.md',
  '# d0 正确锚对照\n\n' + DOC6 +
  '- 被核对象 SHA256 = %s，字节数 = %d（`lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md`）\n' % (mb_hash, mb_bytes))
w(caseD / 'd1_forged_binding' / 'SPEC.md',
  '# d1 伪造绑定（目标在盘、哈希错）\n\n' + DOC6 +
  '- 被核对象 SHA256 = %s，字节数 = 999999（`lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md`）\n' % ('e' * 64))
w(caseD / 'd2_silent_mismatch' / 'SPEC.md',
  '# d2 静默失配（可定位对象、指纹错、无覆盖声明）\n\n' + DOC6 +
  '- 参考件：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md`（SHA256 = %s）\n' % ('ab' * 32))
w(caseD / 'd3_missing_target' / 'SPEC.md',
  '# d3 绑定指向仓内缺失对象\n\n' + DOC6 +
  '- 被核对象 SHA256 = %s，字节数 = 123（`lead/gate_validate_20261108/_gv_fixtures/caseD/nonexistent_ref.md`）\n' % ('f' * 64))

# ---------- caseE: 结构缺节（R1）/ 要素同义词（R2） ----------
caseE = FX / 'caseE'
w(caseE / 'e1_missing_section' / 'SPEC.md',
  '# e1 缺节样本\n\n## 1 节1\n\n占位。\n\n## 2 节2\n\n占位。\n\n## 4 节4\n\n占位。\n\n## 5 节5\n\n占位。\n\n## 6 节6\n\n占位。\n\n（无 ## 3）\n')
w(caseE / 'e2_synonym' / 'SPEC.md',
  '# e2 要素样本\n\n' + DOC6 +
  '本件含 HANDOFF_COMPLETE 与「最少字段」（任务书原词），但不含「不放行采集」及其任何变体。\n'
  '最小字段组应以最少字段命中；不放行采集组应报缺要素。\n')

# ---------- caseF: getattr 动态解析逃逸面（测试修正实现的逃逸覆盖） ----------
caseF = FX / 'caseF'
w(caseF / 'SPEC.md', '# caseF 交付说明\n\n' + DOC6 + '验收：getattr 明文串应判边；拆串 getattr 双盲（残留面）。\n')
evade = '''# -*- coding: utf-8 -*-
# 【违规样本 F】门禁回归测试数据 —— getattr 动态解析逃逸面。禁止执行。
import ctypes


def f_plain(lib):
    # 明文串 getattr：原门禁子串扫描可命中；修正实现按 getattr-逃逸判边
    return getattr(lib, '%s')(0x1000, False, 1234)


def g_split(lib):
    # 拆串 getattr：原门禁与修正实现均不可见（静态分析固有盲区，登记残留风险）
    return getattr(lib, '%s' + '%s')(0x1000, False, 1234)
''' % (API_NAME, API_NAME[:4], API_NAME[4:])
w(caseF / '_evade_getattr.py', evade)

# ---------- 校验样本语法（只 parse，不执行） ----------
import ast
for p in sorted(FX.rglob('*.py')):
    ast.parse(p.read_text(encoding='utf-8'))
print('fixtures built & syntax-ok:', [str(p.relative_to(FX)).replace('\\\\', '/') for p in sorted(FX.rglob('*')) if p.is_file()])
print('API_NAME extracted from mother =', API_NAME)
print('literals extracted from gate src =', gm, rl, yu)
print('mother sha256 =', hashlib.sha256(mother_path.read_bytes()).hexdigest())
