# -*- coding: utf-8 -*-
"""gate_r3_semantic_20261107.py — B 链 R3 语义复审确定性门禁。

总控会话撰写，工作流以 world.run 调用，子代理不可修改、不可放宽。

用法：
    python -I -X utf8 <abs path> pre    只核上游五件指纹（含新绑定）
    python -I -X utf8 <abs path> post   核上游 + 复审交付件全量判定

退出码：0 = 全 PASS；1 = 有 FAIL。

本脚本只读，唯一输出是 stdout。不执行被审候选（只做 ast.parse 静态解析）。
"""

import ast
import hashlib
import os
import re
import sys

NL = chr(10)
CR = bytes([13])
BOM = bytes([239, 187, 191])

MODE = sys.argv[1] if len(sys.argv) > 1 else 'post'
ROOT = 'D:/Project/ra2-campaign-forge'

MOTHER = ROOT + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'
CAND = ROOT + '/lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'
DIFF = ROOT + '/lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff'
DESIGN = ROOT + '/lead/b2b_design_20261106/B2B_DESIGN.md'
PREAUD = ROOT + '/lead/b2b_preaudit_20261106/B2B_PREAUDIT.md'
BIND = ROOT + '/lead/b2b_n1_binding_20261107/N1_BINDING.md'

R3DIR = ROOT + '/lead/b2b_candidate_review3_20261107'
R3DOC = R3DIR + '/CANDIDATE_SEMANTIC_REVIEW_R3.md'
R3AUDIT = R3DIR + '/review/SEMANTIC_REVIEW_AUDIT_R3.md'
R3PROBE = R3DIR + '/_review_probe_r3.py'
R3PROBEOUT = R3DIR + '/_review_probe_r3_out.txt'
R3TESTOUT = R3DIR + '/_test_rerun_out.txt'
R3GATEOUT = R3DIR + '/_gate_rerun_out.txt'

M_SHA = '517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636'
C_SHA = 'ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2'
D_SHA = '565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf'
P_SHA = '3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f'
B_SHA = '00ea6fe87ee5508b84332447b23951d4db86a1682ee36aaa48a3bd9cf774d310'

M_B, C_B, D_B, P_B, B_B = 399508, 412759, 66735, 20615, 8493
DIFF_SHA = '72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9'
DIFF_B = 18454

F7 = ['freshnessState', 'freshnessConfidence', 'freshnessNote',
      'capturedAtIso', 'priorMtimeIso', 'priorSha256', 'evidenceExistsAfter']
F_ALT = ['FRESHNESS_STATE', 'FRESHNESS_CONFIDENCE', 'FRESHNESS_NOTE',
         'CAPTURED_AT_ISO', 'PRIOR_MTIME_ISO', 'PRIOR_SHA256', 'EVIDENCE_EXISTS_AFTER']

fails = []


def ck(ok, label, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + label + (('  |  ' + detail) if detail else ''))
    if not ok:
        fails.append(label)


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ 上游五件
cb = rd(CAND) if os.path.exists(CAND) else b''
mb = rd(MOTHER)
db = rd(DESIGN)
pb = rd(PREAUD)
bb = rd(BIND) if os.path.exists(BIND) else b''
dbf = rd(DIFF) if os.path.exists(DIFF) else b''

ck(os.path.exists(CAND) and sha(cb) == C_SHA and len(cb) == C_B,
   'U1 被审候选（新，LF 版）零漂移',
   (('%d B %s' % (len(cb), sha(cb)[:16])) if cb else 'MISSING'))
ck(sha(mb) == M_SHA and len(mb) == M_B, 'U2 母本零漂移',
   '%d B %s' % (len(mb), sha(mb)[:16]))
ck(sha(db) == D_SHA and len(db) == D_B, 'U3 批准设计零漂移',
   '%d B %s' % (len(db), sha(db)[:16]))
ck(sha(pb) == P_SHA and len(pb) == P_B, 'U4 设计预审零漂移',
   '%d B %s' % (len(pb), sha(pb)[:16]))
ck(bb and sha(bb) == B_SHA and len(bb) == B_B, 'U5 N-1 绑定记录零漂移',
   (('%d B %s' % (len(bb), sha(bb)[:16])) if bb else 'MISSING'))
ck(dbf and sha(dbf) == DIFF_SHA and len(dbf) == DIFF_B, 'U6 CANDIDATE_LF.diff 零漂移',
   (('%d B %s' % (len(dbf), sha(dbf)[:16])) if dbf else 'MISSING'))

# 候选与母本的行尾必须一致（N-1 关闭的实质）
if cb:
    ck(cb.count(CR) == 0, 'U7 被审候选零 CR 字节', 'CR=%d' % cb.count(CR))
    ck(not cb.startswith(BOM), 'U8 被审候选无 BOM')

# ------------------------------------------------------------------ 候选基础事实
cand_text = cb.decode('utf-8') if cb else ''
ast_ok = False
if cand_text:
    try:
        tree = ast.parse(cand_text)
        ast_ok = True
    except SyntaxError as exc:
        print('INFO  ast.parse 失败: %s' % exc)
ck(ast_ok, 'U9 被审候选 ast.parse 成功')

if MODE == 'pre':
    print('SUMMARY_PRE fails=%d' % len(fails))
    raise SystemExit(0 if not fails else 1)

# ------------------------------------------------------------------ 静态：调用点
def find_calls(tree, fname):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            nm = None
            if isinstance(f, ast.Name):
                nm = f.id
            elif isinstance(f, ast.Attribute):
                nm = f.attr
            if nm == fname:
                out.append(node)
    return out


if ast_ok:
    cpe_calls = find_calls(tree, 'copy_post_except_evidence')
    ck(len(cpe_calls) >= 1, 'S1 copy_post_except_evidence 调用点存在',
       'count=%d' % len(cpe_calls))
    missing = []
    for c in cpe_calls:
        kw = [k.arg for k in c.keywords if k.arg]
        if 'pre_freshness_snapshot' not in kw:
            missing.append(getattr(c, 'lineno', -1))
    ck(not missing, 'S2 每个 copy_post_except_evidence 调用点都传 pre_freshness_snapshot',
       ('缺失行 ' + str(missing)) if missing else '%d/%d' % (len(cpe_calls), len(cpe_calls)))

    ft_calls = find_calls(tree, 'finalize_trip')
    ck(len(ft_calls) >= 1, 'S3 finalize_trip 调用点存在', 'count=%d' % len(ft_calls))

    # freshness 7 字段：设计 :83 定义「_emit_f 每次固定写 7 个 FRESHNESS group 字段」，
    # 其中 4 键由 FRESHNESS_KEY_PREFIX 拼出、3 键为字面量 —— 故按 AST 数 _emit_f 内的 rec.add，
    # 不按扁平字面量搜（那样必然搜不全）。
    emit = [n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == '_emit_f']
    if emit:
        fn = emit[0]
        adds = [x for x in ast.walk(fn) if isinstance(x, ast.Call)
                and isinstance(x.func, ast.Attribute) and x.func.attr == 'add']
        on_group = [x for x in adds
                    if x.args and isinstance(x.args[0], ast.Name)
                    and x.args[0].id == 'FRESHNESS_GROUP']
        ck(len(adds) == 7, 'S4 _emit_f 内 rec.add 恰为 7 处', 'found=%d' % len(adds))
        ck(len(on_group) == 7, 'S4b 7 处 rec.add 全部写入 FRESHNESS_GROUP',
           '%d/%d' % (len(on_group), len(adds)))
    else:
        ck(False, 'S4 _emit_f 函数存在', '未找到 def _emit_f')

    # unknown 不得给 high
    bad = re.findall(r'unknown[^\n]{0,80}["\']high["\']', cand_text, re.IGNORECASE)
    ck(not bad, 'S5 unknown 未与 high 置信同现', ('样例 ' + str(bad[:2])) if bad else '')

    # freshness_* 不被退出码判据读取（粗判：退出码判据区间不得出现 freshness）
    ecHits = re.findall(r'^\s*(?:ec|exit_code|exitcode|rc)\s*=\s*[^\n]*freshness', cand_text,
                        re.MULTILINE | re.IGNORECASE)
    ck(not ecHits, 'S6 退出码判据未读 freshness_*', ('命中 ' + str(ecHits[:2])) if ecHits else '')

# ------------------------------------------------------------------ 反扫描
SCAN = ['OpenProcess', 'ReadProcessMemory', 'SuspendThread', 'StackWalk',
        'MiniDump', 'SetWindowsHookEx', 'CreateRemoteThread',
        'WriteProcessMemory', 'VirtualAllocEx', 'ctypes']
if cand_text:
    mtext = mb.decode('utf-8')
    for kw in SCAN:
        ck(cand_text.count(kw) == mtext.count(kw),
           'S7 反扫描 %s 计数与母本相同' % kw,
           '%d vs %d' % (cand_text.count(kw), mtext.count(kw)))

# ------------------------------------------------------------------ 复审交付件
ck(os.path.exists(R3DIR), 'R0 R3 写域目录存在', R3DIR)
for p, label in ((R3DOC, 'R1 主判定书'), (R3AUDIT, 'R2 独立复核件'),
                 (R3PROBE, 'R3 探针脚本'), (R3PROBEOUT, 'R4 探针输出'),
                 (R3TESTOUT, 'R5 测试重跑输出'), (R3GATEOUT, 'R6 门禁重跑输出')):
    ok = os.path.exists(p) and os.path.getsize(p) > 0
    ck(ok, label + '存在且非空', ('%d B' % os.path.getsize(p)) if os.path.exists(p) else 'MISSING')

if os.path.exists(R3DOC):
    doc = rd(R3DOC).decode('utf-8', 'replace')

    ck(doc.count('\r') == 0, 'R7 主判定书零 CR 字节')

    # 四个不同 64-hex + 四组字节数。★ 判据按「去千分位逗号后匹配」，且只要求
    # 候选/母本/设计三件（设计预审件非 R3 的必列对象 —— R3 以 N1 绑定记录代之）。
    norm = doc.replace(',', '')
    hexes = set(re.findall(r'\b[0-9a-f]{64}\b', doc))
    ck(len(hexes) >= 4, 'R8 主判定书含 >=4 个不同 64-hex 指纹', 'found=%d' % len(hexes))
    for h in (C_SHA, M_SHA, D_SHA):
        ck(h in doc, 'R9 主判定书载明 %s…' % h[:12])
    ck(P_SHA in doc or B_SHA in doc,
       'R9b 主判定书载明设计预审或 N-1 绑定之一', 'either acceptable')
    for nb in (C_B, M_B, D_B):
        ck(str(nb) in norm, 'R10 主判定书载明字节数 %d' % nb)

    # verdict 行
    vm = re.search(r'^verdict:\s*(PASS|BLOCKED)\s*$', doc, re.MULTILINE)
    ck(vm is not None, 'R11 主判定书含独占一行的 verdict: PASS|BLOCKED',
       vm.group(0) if vm else 'missing')
    verdict = vm.group(1) if vm else None

    # 五小节
    for sec in ('状态矩阵对照', '调用传参核对', '输出字段核对', 'F/E 分离核对', '范围限制核对'):
        ck(sec in doc, 'R12 主判定书含小节「%s」' % sec)

    for sec in ('## 阻断项', '## 未验', '## 证据等级说明'):
        ck(sec in doc, 'R13 主判定书含小节「%s」' % sec)

    # 「未验」非空
    i = doc.find('## 未验')
    j = doc.find(NL + '## ', i + 5)
    body = doc[i:j if j > 0 else len(doc)]
    nonempty = len(body.replace('## 未验', '').strip()) > 40
    ck(nonempty, 'R14 「未验」小节非空', '%d chars' % len(body))

    # 一致性：PASS 则阻断项必须为空/写「无」
    i2 = doc.find('## 阻断项')
    j2 = doc.find(NL + '## ', i2 + 5)
    blk = doc[i2:j2 if j2 > 0 else len(doc)]
    blk_body = blk.replace('## 阻断项', '').strip()
    no_block = (len(blk_body) < 60) or ('无' in blk_body and 'BLOCKED' not in blk_body)
    if verdict == 'PASS':
        ck(no_block, 'R15 verdict=PASS 时阻断项为空或写「无」', blk_body[:70])
    else:
        ck(True, 'R15 verdict 非 PASS，跳过阻断项一致性', str(verdict))

    # 证据等级三档必须分列
    for kw in ('机械门禁', '报告字段', '语义'):
        ck(kw in doc, 'R16 主判定书区分证据等级关键词「%s」' % kw)

    # 越界扫描：只在**肯定语境**下算越界。判定书里正当的边界声明形如
    # 「不构成『候选可应用到母本』」「不等于：…、集成已演练」——这些是否定句，必须放过。
    NEG = r'不构成|不等于|不代表|并不|不能|无权|不签|未做|未验|尚未|零真机|非'
    OVER = ['已应用到母本', '目标②已修复', '真机验证通过', '候选可用', '集成已演练', '可应用到母本']
    hits = []
    for w in OVER:
        for m in re.finditer(r'[^\n。；]*' + re.escape(w) + r'[^\n。；]*', doc):
            seg = m.group(0)
            if not re.search(NEG, seg):
                hits.append(w + '（肯定语境）: ' + seg.strip()[:60])
    ck(not hits, 'R17 主判定书无越界断言', ('命中 ' + str(hits[:3])) if hits else '')

if os.path.exists(R3AUDIT):
    aud = rd(R3AUDIT).decode('utf-8', 'replace')
    for key in ('subjectSha256', 'subjectBytes', 'checkedEveryRow',
                'noOverreach', 'blockedCount'):
        ck(key in aud, 'A1 复核件含字段 %s' % key)
    ck(C_SHA in aud, 'A2 复核件绑定被审对象 SHA256')
    ck(': true' in aud or 'true' in aud, 'A3 复核件布尔字段为 true 形态')

if os.path.exists(R3TESTOUT):
    to = rd(R3TESTOUT).decode('utf-8', 'replace')
    ck('PASS=' in to and 'FAIL=' in to, 'A4 测试重跑输出含 PASS= 与 FAIL=')
    m = re.search(r'FAIL=(\d+)', to)
    ck(m is not None and int(m.group(1)) == 0, 'A5 重跑测试 FAIL=0',
       m.group(0) if m else 'no FAIL=')

if os.path.exists(R3GATEOUT):
    go = rd(R3GATEOUT).decode('utf-8', 'replace')
    ck('ALL 9 GATES PASSED' in go or 'EXIT=0' in go or 'exit=0' in go.lower(),
       'A6 候选门禁重跑通过', go.strip().split(NL)[-1][:70] if go.strip() else '')

print('SUMMARY_POST fails=%d verdict=%s' % (len(fails), 'see R11'))
raise SystemExit(0 if not fails else 1)
