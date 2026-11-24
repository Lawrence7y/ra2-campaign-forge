# -*- coding: utf-8 -*-
# _gt_edge_audit.py — AST 级「动态调用边」审计：区分
#   call_edge   = 真实的动态解析/采样调用（import ctypes、windll 属性链、被禁 API 的真实调用点）
#   string_lit  = 仅作为字符串字面量出现（反禁词列表、注释、文档）
# 并对比「写域内副本 vs 母本」是否新增调用边。
# 只读分析；输出 JSON。python -I -X utf8 运行。
import ast
import hashlib
import json
import pathlib

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')

API_NAMES = ['OpenProcess', 'ReadProcessMemory', 'WriteProcessMemory',
             'VirtualAllocEx', 'CreateRemoteThread', 'SetWindowsHookEx',
             'SuspendThread', 'StackWalk', 'MiniDump', 'TerminateProcess']
GAME_NAMES = ['gamemd', 'ra2loader', 'YURI']


def classify(path):
    """返回 {call_edges:[...], string_lits:n, imports:[...], subprocess:[...]}"""
    src = pathlib.Path(path).read_text(encoding='utf-8')
    tree = ast.parse(src)
    edges, sconsts, subs = [], 0, []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.append('import ' + a.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append('from ' + (node.module or '') + ' import ' + ','.join(a.name for a in node.names))
        elif isinstance(node, ast.Attribute):
            chain = []
            n = node
            while isinstance(n, ast.Attribute):
                chain.append(n.attr)
                n = n.value
            if isinstance(n, ast.Name):
                chain.append(n.id)
            full = '.'.join(reversed(chain))
            base = chain[-1] if chain else ''
            if base == 'ctypes' or 'windll' in chain or 'oledll' in chain:
                edges.append('attr:' + full)
            elif chain and chain[-1] in API_NAMES:
                edges.append('api-attr:' + full)
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in API_NAMES:
                edges.append('call:' + f.id)
            elif isinstance(f, ast.Attribute) and f.attr in API_NAMES:
                edges.append('call:.' + f.attr)
            elif isinstance(f, ast.Attribute) and f.attr in ('Popen', 'run', 'call', 'check_output') \
                    and isinstance(f.value, ast.Name) and f.value.id == 'subprocess':
                argtxt = ast.unparse(node.args[0]) if node.args else ''
                subs.append('subprocess.' + f.attr + '(' + argtxt[:80] + ')')
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for api in API_NAMES + ['ctypes', 'windll']:
                if api in node.value:
                    sconsts += 1
                    break
            for g in GAME_NAMES:
                if g.lower() in node.value.lower():
                    subs.append('strlit:' + node.value[:60])
                    break
    return {'call_edges': sorted(set(edges)), 'string_lits': sconsts,
            'imports': sorted(set(imports)), 'subprocess_or_gamelit': sorted(set(subs))}


out = {}
# 1) B 链写域被标记的三个 .py + 母本对比
pairs = [
    ('lead/b2b_isolated_20261107/qc151_trip.isolated.py',
     'lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'),
]
for iso, mother in pairs:
    b1 = (ROOT / iso).read_bytes()
    b2 = (ROOT / mother).read_bytes()
    out['isolated_vs_mother'] = {
        'identical': b1 == b2,
        'iso_sha256': hashlib.sha256(b1).hexdigest(),
        'mother_sha256': hashlib.sha256(b2).hexdigest(),
        'iso_edges': classify(ROOT / iso)['call_edges'],
        'new_edges_vs_mother': 'N/A（逐字节相同 ⇒ 新增调用边 = 0）',
    }
# 2) 判据第二轮的三个 verify 脚本：是否只有 string_lit、没有 call_edge
for rel in ['lead/dtrigger_round2_20261107/_verify_A_recompute.py',
            'lead/dtrigger_round2_20261107/_verify_C_ast.py',
            'lead/dtrigger_round2_20261107/_verify_D_recompute.py',
            'lead/b2b_isolated_20261107/_integ_probe_isolated.py',
            'lead/b2b_isolated_20261107/_integ_test_isolated.py',
            'lead/b2b_isolated_20261107/_integ_check_isolated.py']:
    out[pathlib.Path(rel).name] = classify(ROOT / rel)
print(json.dumps(out, ensure_ascii=False, indent=1))
