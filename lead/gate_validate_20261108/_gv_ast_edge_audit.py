# -*- coding: utf-8 -*-
# _gv_ast_edge_audit.py —— 独立 AST 调用边审计（不照抄审计方实现）
# 对原门禁扫到的 .py 逐个回答：子串命中 vs AST 真实调用边 vs 字面量/mock 语境
import ast, hashlib, pathlib, re, json, difflib

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead' / 'gate_validate_20261108' / '_gv_out'

BANNED = ['OpenProcess', 'ReadProcessMemory', 'WriteProcessMemory', 'VirtualAllocEx',
          'CreateRemoteThread', 'SetWindowsHookEx', 'SuspendThread', 'TerminateProcess']
BANNED_RE = re.compile(r'^(?:%s|StackWalk\w*|MiniDump\w*)$' % '|'.join(BANNED))
SUBSTR_RE = re.compile(r'OpenProcess|ReadProcessMemory|WriteProcessMemory|SuspendThread|'
                       r'StackWalk|MiniDump|CreateRemoteThread|SetWindowsHookEx|'
                       r'VirtualAllocEx|TerminateProcess|ctypes\.windll')
GAME_RE = re.compile(r'gamemd|ra2loader|YURI')
CTYPES_ROOTS = ('windll', 'oledll', 'CDLL', 'pythonapi', 'WinDLL')

def attr_chain(node):
    """a.b.c -> ['a','b','c']（不含 call/下标），失败返回 None"""
    parts = []
    while node is not None:
        if isinstance(node, ast.Attribute):
            parts.append(node.attr); node = node.value
        elif isinstance(node, ast.Name):
            parts.append(node.id); node = None
        elif isinstance(node, ast.Call):
            return None
        elif isinstance(node, ast.Constant):
            parts.append('<const>'); node = None
        else:
            return None
    return list(reversed(parts))

def collect_edges(tree):
    edges = []      # 真实调用边
    mocks = []      # mock.patch 拦截串
    getattr_ev = [] # getattr 动态解析疑似
    literals = []   # 字符串常量里的禁名（非调用）
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            # getattr(ctypes.windll.kernel32, 'OpenProcess') 逃逸面
            if isinstance(fn, ast.Name) and fn.id == 'getattr' and len(node.args) >= 2:
                base = attr_chain(node.args[0])
                a2 = node.args[1]
                if base and any(p in CTYPES_ROOTS or p == 'ctypes' for p in base):
                    if isinstance(a2, ast.Constant) and isinstance(a2.value, str) and BANNED_RE.match(a2.value):
                        getattr_ev.append((node.lineno, '.'.join(base), a2.value))
            fname = None
            if isinstance(fn, ast.Name):
                fname = fn.id
            elif isinstance(fn, ast.Attribute):
                fname = fn.attr
            # 禁 API 直接调用点
            if fname and BANNED_RE.match(fname):
                edges.append((node.lineno, 'call:' + fname))
            # subprocess / os.system 启动目标检查
            if fname in ('Popen', 'run', 'call', 'check_output', 'system'):
                mod = None
                if isinstance(fn, ast.Attribute):
                    mod = attr_chain(fn)
                game_hit = False
                for a in node.args:
                    for c in ast.walk(a):
                        if isinstance(c, ast.Constant) and isinstance(c.value, str):
                            if GAME_RE.search(c.value):
                                game_hit = True
                        elif isinstance(c, ast.Attribute):
                            if GAME_RE.search(c.attr):
                                game_hit = True
                if game_hit:
                    edges.append((node.lineno, 'launch-game:%s' % ('.'.join(mod) if mod else fname)))
            # mock.patch 拦截语境
            if fname in ('patch', 'object', 'patch_object'):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    if SUBSTR_RE.search(node.args[0].value):
                        mocks.append((node.lineno, node.args[0].value[:60]))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if SUBSTR_RE.search(node.value):
                literals.append((node.lineno, node.value[:60].replace('\n', ' ')))
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name == 'ctypes' or a.name.startswith('ctypes.'):
                    literals.append((node.lineno, 'import ' + a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == 'ctypes' or node.module.startswith('ctypes')):
                names = ','.join(a.name for a in node.names)
                literals.append((node.lineno, 'from %s import %s' % (node.module, names)))
                # from-import 的禁 API 名 + 调用点已在上面 Call 分支覆盖（Name 调用）
    return edges, mocks, getattr_ev, literals

def py_edges(path):
    src = pathlib.Path(path).read_text(encoding='utf-8')
    tree = ast.parse(src)
    return collect_edges(tree), src

targets = [
    # cd57bf1c 域（b2b_isolated）
    'lead/b2b_isolated_20261107/qc151_trip.isolated.py',
    'lead/b2b_isolated_20261107/_integ_test_isolated.py',
    'lead/b2b_isolated_20261107/_integ_probe_isolated.py',
    'lead/b2b_isolated_20261107/_integ_check_isolated.py',
    # 1c93b364 域（dtrigger_round2）
    'lead/dtrigger_round2_20261107/_verify_A_recompute.py',
    'lead/dtrigger_round2_20261107/_verify_C_ast.py',
    'lead/dtrigger_round2_20261107/_verify_D_recompute.py',
]
report = {}
lines = []
W = lines.append
W('=== 独立 AST 边审计 %s' % '===')
for t in targets:
    p = ROOT / t
    if not p.is_file():
        W('MISSING %s' % t); continue
    (edges, mocks, getattr_ev, literals), src = py_edges(p)
    subs = SUBSTR_RE.findall(src)
    key = str(p.relative_to(ROOT))
    report[key] = {
        'substring_hits': len(subs),
        'edges': [list(e) for e in edges],
        'mock_patch': [list(m) for m in mocks],
        'getattr_evasion': [list(g) for g in getattr_ev],
        'string_literals_with_banned': len(literals),
    }
    W('%s' % t)
    W('  子串命中(原门禁口径)=%d | AST调用边=%d | mock.patch拦截=%d | getattr逃逸=%d | 含禁名字符串常量=%d'
      % (len(subs), len(edges), len(mocks), len(getattr_ev), len(literals)))
    for e in edges[:8]:
        W('    EDGE L%s %s' % (e[0], e[1]))
    for m in mocks[:4]:
        W('    MOCK L%s %s' % (m[0], m[1]))
    for g in getattr_ev[:4]:
        W('    GETATTR-EVASION L%s %s -> %s' % (g[0], g[1], g[2]))

# qc151 派生副本 vs 母本
mother = ROOT / 'lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'
copy = ROOT / 'lead/b2b_isolated_20261107/qc151_trip.isolated.py'
mb, cb = mother.read_bytes(), copy.read_bytes()
h = lambda b: hashlib.sha256(b).hexdigest()
ident = mb == cb
(me, mm, mg, ml), msrc = py_edges(mother)
(ce, cm, cg, cl), csrc = py_edges(copy)
new_edges = [e for e in ce if e not in me]
report['qc151_derivation'] = {
    'mother_sha256': h(mb), 'mother_bytes': len(mb),
    'copy_sha256': h(cb), 'copy_bytes': len(cb),
    'byte_identical': ident,
    'mother_edges': len(me), 'copy_edges': len(ce), 'new_edges': len(new_edges),
    'new_edge_list': [list(e) for e in new_edges],
}
W('')
W('=== qc151 派生核对 ===')
W('mother: sha256=%s bytes=%d | copy: sha256=%s bytes=%d' % (h(mb)[:16], len(mb), h(cb)[:16], len(cb)))
W('byte_identical=%s | mother_edges=%d copy_edges=%d new_edges=%d %s'
  % (ident, len(me), len(ce), len(new_edges), new_edges[:5]))

# _integ_test_isolated.py 对上游 diff 行数
up = ROOT / 'lead/b2b_candidate_review3_20261107/_test_candidate_lf.py'
if up.is_file():
    a = up.read_text(encoding='utf-8', errors='replace').splitlines()
    b = (ROOT / 'lead/b2b_isolated_20261107/_integ_test_isolated.py').read_text(encoding='utf-8', errors='replace').splitlines()
    d = list(difflib.unified_diff(a, b, n=0))
    plus = sum(1 for x in d if x.startswith('+') and not x.startswith('+++'))
    minus = sum(1 for x in d if x.startswith('-') and not x.startswith('---'))
    report['integ_test_diff'] = {'upstream': str(up.relative_to(ROOT)), 'plus': plus, 'minus': minus}
    W('')
    W('=== _integ_test_isolated.py diff vs 上游 ===')
    W('upstream=%s  +行=%d  -行=%d  合计=%d' % (up.relative_to(ROOT), plus, minus, plus + minus))
else:
    W('upstream _test_candidate_lf.py 不在盘（未验）')

# 域内其余 .py 全量边扫描（防漏）
W('')
W('=== 两域全部 .py 边扫描 ===')
for dom in ('lead/b2b_isolated_20261107', 'lead/dtrigger_round2_20261107'):
    for p in sorted((ROOT / dom).glob('*.py')):
        (e, m, g, l), _ = py_edges(p)
        subs = len(SUBSTR_RE.findall(p.read_text(encoding='utf-8')))
        W('%s/%s | substr=%d edges=%d mocks=%d getattr=%d' % (dom.split("/")[-1], p.name, subs, len(e), len(m), len(g)))
        for ee in e:
            W('    EDGE L%s %s' % (ee[0], ee[1]))
        for gg in g:
            W('    GETATTR-EVASION L%s %s -> %s' % (gg[0], gg[1], gg[2]))

(OUT / '_gv_ast_edge_audit_out.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(OUT / '_gv_ast_edge_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print('\n'.join(lines))
