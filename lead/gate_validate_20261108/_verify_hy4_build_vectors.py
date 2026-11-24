# -*- coding: utf-8 -*-
# _verify_hy4_build_vectors.py —— 独立复核员·hy4 自建真违规样本（静态测试数据，禁止执行）
# 素材取自仓内既有字节；仅被 AST 解析；全部落在唯一写域 _verify_vectors/。
import pathlib, hashlib

R = pathlib.Path('D:/Project/ra2-campaign-forge')
V = R / 'lead' / 'gate_validate_20261108' / '_verify_vectors'
V.mkdir(parents=True, exist_ok=True)
DOC6 = ''.join('## %d 节%d\n\n内容占位。\n\n' % (i, i) for i in range(1, 7))

def w(rel, s):
    p = V / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')
    return p

mother = R / 'lead' / 'b2b_candidate_lf_20261107' / 'qc151_trip.candidate_lf.py'
mb = mother.read_bytes()

# V1: 新建脚本 subprocess 启动游戏进程（任务点名必做真违规）
w('v1_launch/SPEC.md', '# v1 启动游戏进程\n\n' + DOC6 + '说明：独立构造真违规样本。\n')
w('v1_launch/_launch.py', '''# -*- coding: utf-8 -*-
# 独立复核样本 V1：静态测试数据，禁止执行。仅被 AST 解析。
import subprocess

def go():
    subprocess.Popen(['gamemd.exe', '-win'])
    subprocess.run(['ra2loader.exe'])
    if False:
        subprocess.check_output(['YURI.exe'])
''')

# V2: 派生副本(逐字节孪生, 应放行) + 追加母本完全没有的禁止 API 调用边(应 FAIL)
w('v2_newedge/SPEC.md', '# v2 新增调用边\n\n' + DOC6 + '说明：独立构造真违规样本。\n')
(V / 'v2_newedge' / 'qc151_trip.same.py').write_bytes(mb)
plus = mb + (b'' if mb.endswith(b'\n') else b'\n') + b'\n\nif False:\n    k32.TerminateProcess(h, 0)\n'
(V / 'v2_newedge' / 'qc151_trip.plus1.py').write_bytes(plus)

# V3: 双件并存且均无关系声明
w('v3_dual/Alpha.md', '# Alpha\n\n' + DOC6 + '（无任何绑定行/关系声明）\n')
w('v3_dual/Beta.md', '# Beta\n\n' + DOC6 + '（无任何绑定行/关系声明）\n')

# V4: 正确锚 / 伪造绑定 / 指向仓内缺失对象
target = R / 'lead' / 'matrix_binding_20261108' / 'MATRIX_BINDING_FACTS.md'
th = hashlib.sha256(target.read_bytes()).hexdigest()
tb = len(target.read_bytes())
w('v4_anchor/d0_correct/SPEC.md',
  '# d0\n\n' + DOC6 + '- 被核对象 SHA256 = ' + th + '，字节数 = ' + str(tb) +
  '（`lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md`）\n')
w('v4_anchor/d1_forged/SPEC.md',
  '# d1\n\n' + DOC6 + '- 被核对象 SHA256 = ' + ('e' * 64) + '，字节数 = ' + str(tb) +
  '（`lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md`）\n')
w('v4_anchor/d2_missing/SPEC.md',
  '# d2\n\n' + DOC6 + '- 被核对象 SHA256 = ' + ('f' * 64) + '，字节数 = 1' +
  '（`lead/gate_validate_20261108/_verify_vectors/v4_anchor/nope.md`）\n')

# V5: 缺节 / 要素真缺席（特意不把要素词写进文档任何位置）
w('v5_struct/e1_missing_section/SPEC.md',
  '# e1\n\n## 1 节1\n\n占位。\n\n## 2 节2\n\n占位。\n\n## 4 节4\n\n占位。\n\n## 5 节5\n\n占位。\n\n## 6 节6\n\n占位。\n\n（缺第3节）\n')
w('v5_struct/e2_missing_element/SPEC.md',
  '# e2\n\n' + DOC6 + '本件只写与要素无关的内容：AAA BBB CCC。\n')

# V6: getattr 明文串动态解析
w('v6_getattr/SPEC.md', '# v6\n\n' + DOC6 + '说明：独立构造。\n')
w('v6_getattr/_evade.py', '''# -*- coding: utf-8 -*-
# 独立复核样本 V6：静态测试数据，禁止执行。
def f(lib):
    return getattr(lib, 'OpenProcess')(0x1000, False, 1234)
''')

print('mother TerminateProcess present:', b'TerminateProcess' in mb)
print('plus1 TerminateProcess present:', b'TerminateProcess' in plus)
print('built:', sorted(str(p.relative_to(V)).replace('\\', '/') for p in V.rglob('*') if p.is_file()))
