# -*- coding: utf-8 -*-
# _gv_fixed_rules.py —— GATE_TEMPLATE_FIXED.py.txt (r2) 的第一个可执行实现（回归用）
# 按 R0-R8 文本逐条落地；输出 R7 契约 JSON。
# 用法: python -I -X utf8 _gv_fixed_rules.py --root <域> --doc <交付件名> --config <json文件>
# config: {"sections": 6, "elements": [..], "min_bindings": 1, "json_records": {...}|null,
#          "tpl": "文件名"|null, "extra_fields": [..]}
import ast, hashlib, json, pathlib, re, sys, argparse

REPO = pathlib.Path('D:/Project/ra2-campaign-forge')

BANNED = ['OpenProcess', 'ReadProcessMemory', 'WriteProcessMemory', 'VirtualAllocEx',
          'CreateRemoteThread', 'SetWindowsHookEx', 'SuspendThread', 'TerminateProcess']
BANNED_RE = re.compile(r'^(?:%s|StackWalk\w*|MiniDump\w*)$' % '|'.join(BANNED))
SUBSTR_RE = re.compile(r'OpenProcess|ReadProcessMemory|WriteProcessMemory|SuspendThread|'
                       r'StackWalk|MiniDump|CreateRemoteThread|SetWindowsHookEx|'
                       r'VirtualAllocEx|TerminateProcess|ctypes\.windll')
GAME_RE = re.compile(r'gamemd|ra2loader|YURI')
LITERAL3 = ['gamemd.exe', 'ra2loader', 'taskkill']
CTYPES_ROOTS = ('windll', 'oledll', 'CDLL', 'pythonapi', 'WinDLL')

# R2 同义词组（依据模板 §R2.2 复核实测频次登记；seed= 语料零命中种子词，标 *）
SYNONYMS = {
    '最小字段': ['最少字段', '最小字段', '最小观测字段*', '最少观测字段*', '观测字段与口径*'],
    '最少字段': ['最少字段', '最小字段', '最小观测字段*', '最少观测字段*', '观测字段与口径*'],
    '采集时机': ['采集时机', '观测时机*'],
    '同图控制': ['同图控制', '量级／同图控制', '量级与同图控制', '量级与对照*'],
    '所需帧数': ['所需帧数', '所需帧数论证', '帧数论证', '所需帧数的论证', '趟数论证*', '样本量论证*'],
    '代价上限': ['代价上限', '代价估算*'],
    '能排除的假设': ['能排除的假设', '可排除假设', '可排除的假设', '排除项', '判死方向*'],
    '读数时机': ['读数时机', '字段清单', '观测时机*'],
}

_R2_FOOTNOTE = '（组依据=GATE_TEMPLATE_FIXED §R2.2 频次登记；*=种子词）'

DECL_RE = re.compile(r'就地覆盖|无.{0,4}副本|历史锚|版本锚|覆写前|已存档|留存|中间稿|作废|草稿|供对照|正本')

def sha256(b):
    return hashlib.sha256(b).hexdigest()

# ---------------------------------------------------------------- R1
def r1_sections(text, n_required):
    problems, warnings, nums = [], [], set()
    for m in re.finditer(r'(?m)^##\s+(\d+)(?![.\d])', text):
        nums.add(int(m.group(1)))
    cn = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    for m in re.finditer(r'(?m)^##\s+([一二三四五六七八九十]+)、', text):
        nums.add(cn.get(m.group(1), -1))
    missing = [i for i in range(1, n_required + 1) if i not in nums]
    for i in missing:
        problems.append({'rule_id': 'R1', 'where': 'doc',
                         'what': '缺小节 %d（顶层节号集合 {%s} 中无 %d）' % (i, ','.join(map(str, sorted(nums))), i),
                         'basis': 'R1: ^##\\s+(\\d+)(?![.\\d]) 顶层节号集合匹配'})
    if nums - set(range(1, n_required + 1)):
        warnings.append({'rule_id': 'R1', 'what': '存在必填节号之外的顶层节: %s' % sorted(nums - set(range(1, n_required + 1)))})
    return problems, warnings, sorted(nums)

# ---------------------------------------------------------------- R2
def r2_elements(text, elements):
    problems, warnings = [], []
    for e in elements:
        members = SYNONYMS.get(e, [e])
        main = [m for m in members if not m.endswith('*')]
        seeds = [m[:-1] for m in members if m.endswith('*')]
        if any(m in text for m in main):
            continue
        if any(s in text for s in seeds):
            warnings.append({'rule_id': 'R2', 'what': '要素「%s」仅种子词命中（%s）' % (e, seeds)})
            continue
        problems.append({'rule_id': 'R2', 'where': 'doc',
                         'what': '缺要素 %s（同义词组 %s 均未命中）' % (e, [m.replace('*', '') for m in members]),
                         'basis': 'R2: 同义词组任一命中即通过，任务书原文词优先%s' % _R2_FOOTNOTE})
    return problems, warnings

# ---------------------------------------------------------------- R3
PATH_RE = re.compile(r'([A-Za-z0-9_\-\./\\]+\.[A-Za-z]{2,7})')
# 语义限定指纹（非整件锚）：hex 前窗口出现这些词 ⇒ 该哈希是 rest/聚合/拼接/去头等派生构造，
# 不可按整件现盘重算，降级为人工锚定（不判 fail）
QUALIFIER_RE = re.compile(r'去|rest|REST|聚合|拼接|拼合|截|段|平均|合并|diff of|增量')
# 引证语境（hex 与路径之间的文本含这些词 ⇒ 路径是哈希的「出处引证」而非锚目标）
CITE_CTXT_RE = re.compile(r'实算|命中|派发|同值|与 .*一致|来源|出处|§|复算|自记|记载')
BIND_RE = re.compile(r'被核对象\s*SHA256\s*=\s*`?([0-9a-fA-F]{64})`?\s*[，,]?\s*字节数\s*=\s*([\d,]+)')
SELF_RE = re.compile(r'本件(?:扣行)?\s*SHA256\s*=\s*`?([0-9a-fA-F]{64})`?\s*[，,]?\s*(?:本件)?字节数\s*=\s*([\d,]+)')
HEX_RE = re.compile(r'\b([0-9a-fA-F]{64})\b')
NUM_RE = re.compile(r'(\d[\d,]*)\s*[B字节]{1,2}|字节数\s*=\s*([\d,]+)')

_NAME_IDX = None
def name_index():
    """lead/ 全树文件名索引（裸文件名解析用；构建一次并缓存）。"""
    global _NAME_IDX
    if _NAME_IDX is None:
        idx = {}
        for p in (REPO / 'lead').rglob('*'):
            if p.is_file():
                idx.setdefault(p.name, []).append(p)
        _NAME_IDX = idx
    return _NAME_IDX

def classify_path(cand, doc_root=None):
    """路径分级（解析序：文档同目录 → lead/ → 仓根；裸名走 lead/ 唯一匹配）：
      repo-file / repo-missing / external（仓外或截断）/ ambiguous（同名多命中）/ nopath
    返回 (kind, path, note)。"""
    if not cand:
        return ('nopath', None, '')
    c = cand.replace('\\', '/')
    if '…' in c:
        return ('external', None, '截断路径')
    p = pathlib.PurePath(c)
    is_abs = p.is_absolute() or re.match(r'^[A-Za-z]:[\\/]', c) or c.startswith('/')
    if is_abs:
        fp = pathlib.Path(c)
        try:
            fp.resolve().relative_to(REPO)
        except (ValueError, OSError):
            return ('external', None, '仓外绝对路径')
        return (('repo-file' if fp.is_file() else 'repo-missing'), fp, '')
    bases = []
    if doc_root is not None:
        bases.append(doc_root)
    bases += [REPO / 'lead', REPO]
    notes = []
    for bi, b in enumerate(bases):
        fp = b / c
        try:
            if fp.is_file():
                tag = {0: 'doc域', 1: 'lead/', 2: 'repo'}[bi] if doc_root is not None else {0: 'lead/', 1: 'repo'}[bi]
                return ('repo-file', fp, 'base=' + tag)
        except OSError:
            pass
    notes.append('三基准均未命中')
    if '/' not in c:
        hits = name_index().get(c, [])
        if len(hits) == 1:
            return ('repo-file', hits[0], 'lead/唯一名匹配')
        if len(hits) > 1:
            return ('ambiguous', None, 'lead/ 同名 %d 处' % len(hits))
    return ('repo-missing', None, ';'.join(notes))

def pair_hex_paths(line):
    """行内 64hex 与路径两阶段配对：
      ① 紧邻强配：hex 与路径间隔 ≤3 字符（`X`=hash / hash（`X`） 等）直接一对一；
      ② 其余按位置最近邻一一配对（路径后紧跟 :数字 的行号引证不参与）。
    返回 [(hex, path_or_None, hex_start, path_start), ...]。"""
    toks = []
    for m in HEX_RE.finditer(line):
        toks.append((m.start(), 'hex', m.group(1), 64))
    for m in PATH_RE.finditer(line):
        rest = line[m.end():m.end() + 6]
        if re.match(r':\d', rest):  # 行号引证（file.py:138）→ 非锚目标
            continue
        toks.append((m.start(), 'path', m.group(1), m.end() - m.start()))
    toks.sort(key=lambda t: t[0])
    hexes = [t for t in toks if t[1] == 'hex']
    paths = [t for t in toks if t[1] == 'path']
    pairs = []
    used_hex, used_path = set(), set()
    # ① 紧邻强配
    for hi, h in enumerate(hexes):
        for pi, pt in enumerate(paths):
            if pi in used_path or hi in used_hex:
                continue
            hs, ps = h[0], pt[0]
            if hs > ps:
                gap = hs - (ps + pt[3])
            else:
                gap = ps - (hs + 64)
            if 0 <= gap <= 3:
                pairs.append((h[2], pt[2], hs, ps))
                used_hex.add(hi); used_path.add(pi)
                break
    # ② 最近邻
    for hi, h in enumerate(hexes):
        if hi in used_hex:
            continue
        best, bestd = None, None
        for pi, pt in enumerate(paths):
            if pi in used_path:
                continue
            d = abs(pt[0] - h[0])
            if bestd is None or d < bestd:
                best, bestd = pi, d
        if best is not None:
            used_hex.add(hi); used_path.add(best)
            pairs.append((h[2], paths[best][2], h[0], paths[best][0]))
        else:
            pairs.append((h[2], None, h[0], None))
    pairs.sort(key=lambda t: t[2])
    return pairs

def resolve_path(line):
    """（旧接口，供兼容）行内首个可解析路径。"""
    for m in PATH_RE.finditer(line):
        kind, fp = classify_path(m.group(1))
        if kind == 'repo-file':
            return m.group(1), fp
    return (None, None)

def r3_anchors(text, doc_path, root):
    problems, warnings, bindings = [], [], []
    lines = text.splitlines()
    handled = set()
    decl_in_doc = bool(DECL_RE.search(text))

    def verify_ref(i, hx, pcand, nbytes, is_binding, line_text='', hx_start=0, pstart=None):
        """按 R3-3/R3-2 判定一个 hex+路径对。
        fail 仅限两类：可定位现盘整件锚但重算失配且无覆盖声明；绑定行指仓内缺失对象且无覆盖声明。
        不可机检（仓外/截断/歧义/无路径/语义限定/引证语境）一律 warning（人工锚定）。"""
        # 语义限定指纹（rest/聚合/去头等）⇒ 非整件锚，不参与整件重算
        w0 = line_text[max(0, hx_start - 24):hx_start]
        if QUALIFIER_RE.search(w0):
            bindings.append({'line': i, 'target': '语义限定指纹:' + (pcand or '') , 'declared': hx,
                             'recomputed': '非整件锚(限定语:%s)' % w0.strip()[-18:], 'match': None,
                             'rule_id': 'R3-3' if is_binding else 'R3-2'})
            warnings.append({'rule_id': 'R3-3b' if is_binding else 'R3-2',
                             'what': 'doc:%d 指纹带限定语（%s…）为派生构造哈希，不可整件重算 → 需人工锚定' % (i, w0.strip()[-16:])})
            return
        # 聚合锚回验：绑定行声明「聚合+拼接/串联」构造时，按行内可解析路径重算拼接哈希
        if is_binding and line_text and re.search(r'聚合', line_text) and re.search(r'拼接|串联|concat|连', line_text):
            cands = []
            for m2 in PATH_RE.finditer(line_text):
                rest2 = line_text[m2.end():m2.end() + 6]
                if re.match(r':\d', rest2):
                    continue
                k2, f2, n2 = classify_path(m2.group(1), doc_root=root)
                if k2 == 'repo-file' and f2 != doc_path and f2 not in cands:
                    cands.append(f2)
            if len(cands) >= 2:
                results = []
                for keyf, tag in ((lambda f: f.name, '文件名升序'), (lambda f: str(f), '全路径升序')):
                    fs = sorted(cands, key=keyf)
                    blob = b''.join(f.read_bytes() for f in fs)
                    results.append((sha256(blob), sum(f.stat().st_size for f in fs), tag))
                for agg, tot, tag in results:
                    if agg == hx and (nbytes is None or tot == nbytes):
                        bindings.append({'line': i, 'target': '聚合锚(%s:%d件)' % (tag, len(cands)),
                                         'declared': hx + (('/' + str(nbytes)) if nbytes else ''),
                                         'recomputed': agg + '/' + str(tot), 'match': True, 'rule_id': 'R3-3'})
                        return
                agg, tot, tag = results[0]
                bindings.append({'line': i, 'target': '聚合锚(%s:%d件)' % (tag, len(cands)),
                                 'declared': hx + (('/' + str(nbytes)) if nbytes else ''),
                                 'recomputed': agg + '/' + str(tot), 'match': False, 'rule_id': 'R3-3'})
                problems.append({'rule_id': 'R3-3', 'where': 'doc:%d' % i,
                                 'what': '聚合锚回验失败: %d 件 %s拼接 现盘=%s…/%d 行内=%s…/%s'
                                         % (len(cands), tag, agg[:12], tot, hx[:12], nbytes),
                                 'basis': 'R3-3a: 聚合锚按声明构造现盘重算（伪造指纹防线）'})
                return
            # 可解析件不足 → 人工锚定
            bindings.append({'line': i, 'target': '聚合锚(可解析件不足)', 'declared': hx,
                             'recomputed': 'N/A', 'match': None, 'rule_id': 'R3-3'})
            warnings.append({'rule_id': 'R3-3b', 'what': 'doc:%d 聚合锚可解析件不足（%d 件）→ 需人工锚定' % (i, len(cands))})
            return
        # 引证语境：hex 与路径之间文本是「出处引证」⇒ 路径非锚目标
        if pcand and pstart is not None:
            between = line_text[min(hx_start, pstart):max(hx_start, pstart)]
            if len(between) < 120 and CITE_CTXT_RE.search(between):
                bindings.append({'line': i, 'target': '引证语境:' + (pcand or ''), 'declared': hx,
                                 'recomputed': 'N/A', 'match': None,
                                 'rule_id': 'R3-3' if is_binding else 'R3-2'})
                warnings.append({'rule_id': 'R3-3b' if is_binding else 'R3-2',
                                 'what': 'doc:%d 绑定行缺显式路径（路径处于引证语境「%s…」）→ 需人工锚定' % (i, between.strip()[:24])})
                return
        kind, fp, note = classify_path(pcand, doc_root=root)
        rid = 'R3-3' if is_binding else 'R3-2'
        if kind in ('external', 'ambiguous', 'nopath'):
            bindings.append({'line': i, 'target': '不可机检:' + (pcand or '') + '（' + note + '）', 'declared': hx,
                             'recomputed': 'N/A', 'match': None, 'rule_id': rid})
            warnings.append({'rule_id': 'R3-3b' if is_binding else 'R3-2',
                             'what': 'doc:%d 指纹引用不可机检（%s：%s）→ 需人工锚定，不判 fail' % (i, note, pcand or '缺路径')})
            return
        if kind == 'repo-missing':
            bindings.append({'line': i, 'target': '不在盘:' + (pcand or ''), 'declared': hx,
                             'recomputed': 'N/A', 'match': None, 'rule_id': rid})
            if is_binding and not decl_in_doc:
                problems.append({'rule_id': 'R3-3c', 'where': 'doc:%d' % i,
                                 'what': '绑定行指向仓内缺失对象 %s 且无覆盖/留存声明（静默失配）' % pcand,
                                 'basis': 'R3-3c→R3-2'})
            else:
                warnings.append({'rule_id': 'R3-3c' if is_binding else 'R3-2a',
                                 'what': 'doc:%d 指纹指向不在盘对象 %s%s' % (i, pcand, '，场内有覆盖/留存声明 → 历史锚豁免' if decl_in_doc else '')})
            return
        tb = fp.read_bytes()
        cur = sha256(tb)
        match = (cur == hx) and (nbytes is None or len(tb) == nbytes)
        bindings.append({'line': i, 'target': ('引用锚:' if is_binding else '指纹引用:') + pcand + ('（' + note + '）' if note else ''),
                         'declared': hx + (('/' + str(nbytes)) if nbytes else ''),
                         'recomputed': cur + '/' + str(len(tb)), 'match': match, 'rule_id': rid})
        if not match:
            if decl_in_doc:
                warnings.append({'rule_id': 'R3-2a', 'what': 'doc:%d 指纹与现盘 %s（%s…/%d，%s）失配，场内有覆盖/留存声明 → 按历史锚处理'
                                 % (i, pcand, cur[:12], len(tb), note)})
            else:
                problems.append({'rule_id': rid, 'where': 'doc:%d' % i,
                                 'what': '%s失配: %s（%s）现盘=%s…/%d 行内=%s…%s，且无任何覆盖关系声明（静默失配）'
                                         % ('引用锚' if is_binding else '指纹', pcand, note, cur[:12], len(tb), hx[:12],
                                            ('/' + str(nbytes)) if nbytes else ''),
                                 'basis': 'R3-3a/R3-2: 现盘重算比对；fail 唯一合法情形=静默失配'})

    for i, ln in enumerate(lines, 1):
        # R3-1 自锚（本件扣行两阶段）
        for m in SELF_RE.finditer(ln):
            claimed, nbytes = m.group(1), int(m.group(2).replace(',', ''))
            b = doc_path.read_bytes()
            newtext2 = text.replace(claimed, '0' * 64, 1)
            recomputed = sha256(newtext2.encode('utf-8'))
            ok_hash = recomputed == claimed
            ok_bytes = len(b) == nbytes
            handled.add(claimed)
            bindings.append({'line': i, 'target': '现盘自身(R3-1扣行)', 'declared': claimed + '/' + str(nbytes),
                             'recomputed': recomputed + '/' + str(len(b)), 'match': ok_hash and ok_bytes, 'rule_id': 'R3-1'})
            if not (ok_hash and ok_bytes):
                problems.append({'rule_id': 'R3-1', 'where': 'doc:%d' % i,
                                 'what': '自锚校验失败 hash_ok=%s bytes_ok=%s' % (ok_hash, ok_bytes),
                                 'basis': 'R3-1b: 哈希字段置64个0后重算全件 应等于行内值'})
        # R3-3 绑定行（被核对象 …，字节数 = n）：与行内最近路径配对
        for m in BIND_RE.finditer(ln):
            claimed, nbytes = m.group(1), int(m.group(2).replace(',', ''))
            handled.add(claimed)
            pcand, pstart = None, None
            for hx, pth, hs, ps in pair_hex_paths(ln):
                if hx == claimed:
                    pcand, pstart = pth, ps
                    break
            verify_ref(i, claimed, pcand, nbytes, is_binding=True, line_text=ln, hx_start=m.start(1), pstart=pstart)
        # 其余 64hex 引用 → R3-2（同邻近配对）
        for hx, pth, hs, ps in pair_hex_paths(ln):
            if hx in handled:
                continue
            handled.add(hx)
            verify_ref(i, hx, pth, None, is_binding=False, line_text=ln, hx_start=hs, pstart=ps)
    return problems, warnings, bindings

# ---------------------------------------------------------------- R4
def attr_chain(node):
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

def collect_edges(src):
    tree = ast.parse(src)
    edges, mocks, bare_imports, str_hits = [], [], [], 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == 'getattr' and len(node.args) >= 2:
                base = attr_chain(node.args[0])
                a2 = node.args[1]
                if isinstance(a2, ast.Constant) and isinstance(a2.value, str) and BANNED_RE.match(a2.value):
                    edges.append((node.lineno, 'getattr-逃逸:%s(%s)' % (a2.value, '.'.join(base) if base else '?')))
            fname = None
            if isinstance(fn, ast.Name):
                fname = fn.id
            elif isinstance(fn, ast.Attribute):
                fname = fn.attr
            if fname and BANNED_RE.match(fname):
                edges.append((node.lineno, 'call:' + fname))
            if fname in ('Popen', 'run', 'call', 'check_output', 'system'):
                hit = False
                for a in node.args:
                    for c in ast.walk(a):
                        if isinstance(c, ast.Constant) and isinstance(c.value, str) and GAME_RE.search(c.value):
                            hit = True
                        elif isinstance(c, ast.Attribute) and GAME_RE.search(c.attr):
                            hit = True
                if hit:
                    edges.append((node.lineno, 'launch-game:%s' % fname))
            if fname in ('patch', 'object') and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and SUBSTR_RE.search(a0.value):
                    mocks.append((node.lineno, a0.value[:60]))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and SUBSTR_RE.search(node.value):
            str_hits += 1
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name == 'ctypes' or a.name.startswith('ctypes.'):
                    bare_imports.append((node.lineno, 'import ' + a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == 'ctypes' or node.module.startswith('ctypes')):
                bare_imports.append((node.lineno, 'from ' + node.module + ' import ' + ','.join(a.name for a in node.names)))
    return edges, mocks, bare_imports, str_hits

_UP_HASH = None
def upstream_hash_index():
    global _UP_HASH
    if _UP_HASH is None:
        _UP_HASH = {}
        for p in (REPO / 'lead').rglob('*.py'):
            try:
                _UP_HASH.setdefault(sha256(p.read_bytes()), []).append(p)
            except OSError:
                pass
    return _UP_HASH

def r4_py_scan(root):
    problems, warnings = [], []
    derived, edge_hits = [], []
    idx = upstream_hash_index()
    for py in sorted(root.glob('*.py')):
        src = py.read_text(encoding='utf-8', errors='replace')
        edges, mocks, bare, strhits = collect_edges(src)
        for e in edges:
            edge_hits.append({'file': py.name, 'edge': e[1], 'where': 'ast行%s' % e[0]})
        for b in bare:
            warnings.append({'rule_id': 'R4-1', 'what': '%s:%d 裸 import %s（不判罪，仅警告）' % (py.name, b[0], b[1])})
        if strhits:
            warnings.append({'rule_id': 'R4-3', 'what': '%s 含禁名字符串常量 %d 处（AST 不采字符串，天然豁免）' % (py.name, strhits)})
        for m in mocks:
            warnings.append({'rule_id': 'R4-3b', 'what': '%s:%d mock.patch 拦截串（拦截性非调用性）' % (py.name, m[0])})
        if edges:
            h = sha256(py.read_bytes())
            ups = [u for u in idx.get(h, []) if u != py]
            if ups:
                derived.append({'file': py.name, 'source': str(ups[0].relative_to(REPO)).replace('\\', '/'),
                                'new_edges': 0, 'basis': '逐字节相同（sha256 相等）'})
                warnings.append({'rule_id': 'R4-2', 'what': '%s 为派生副本（逐字节同 %s），继承边 %d 条，新增边=0 → 放行'
                                 % (py.name, derived[-1]['source'], len(edges))})
            else:
                for e in edges:
                    problems.append({'rule_id': 'R4', 'where': '%s:ast行%s' % (py.name, e[0]),
                                     'what': '新增禁 API 调用边/启动边: %s（未找到逐字节相同上游，无法证明继承）' % e[1],
                                     'basis': 'R4-1/R4-2: AST 真实调用边且非派生继承'})
        else:
            h = sha256(py.read_bytes())
            ups = [u for u in idx.get(h, []) if u != py]
            if ups:
                derived.append({'file': py.name, 'source': str(ups[0].relative_to(REPO)).replace('\\', '/'), 'new_edges': 0,
                                'basis': '逐字节相同（sha256 相等）'})
    # R4-5 兜底正则（AST 不可用时）——对全域 .py 文本再扫一次启动
    for py in sorted(root.glob('*.py')):
        src = py.read_text(encoding='utf-8', errors='replace')
        if re.search(r'subprocess\.(Popen|run|call|check_output)\s*\([^)]*(gamemd|ra2loader|YURI)', src):
            if not any(e['file'] == py.name and e['edge'].startswith('launch-game') for e in edge_hits):
                problems.append({'rule_id': 'R4-5', 'where': py.name,
                                 'what': '正则兜底命中启动游戏进程', 'basis': 'R4-5'})
    return problems, warnings, derived, edge_hits

# ---------------------------------------------------------------- R5
def r5_doc_literals(text, docname):
    warnings = []
    for b in LITERAL3:
        n = text.count(b)
        if n:
            warnings.append({'rule_id': 'R5', 'what': '%s 含字面「%s」×%d —— 报告/回件/台账类文档不设字面 fail，只记警告'
                             % (docname, b, n)})
    return warnings

# ---------------------------------------------------------------- R6
WORK_PREFIX = ('_verify', '_gv', '_gt', '_w2', '_fg', '_cal', '_occ', '_probe', '_tmp', '_append')

def r6_dual(root, doc_name, main_text):
    problems, warnings, dual = [], [], []
    shadows = []
    for md in sorted(root.glob('*.md')):
        if md.name == doc_name:
            continue
        if md.name.startswith(WORK_PREFIX):
            continue
        shadows.append(md)
    if not shadows:
        return problems, warnings, dual
    declared = bool(BIND_RE.search(main_text) or SELF_RE.search(main_text) or DECL_RE.search(main_text))
    for md in shadows:
        try:
            t = md.read_text(encoding='utf-8', errors='replace')
            mb = sha256(md.read_bytes())
            sz = md.stat().st_size
        except OSError:
            t, mb, sz = '', 'N/A', 0
        declared = declared or bool(BIND_RE.search(t) or SELF_RE.search(t) or DECL_RE.search(t))
        dual.append({'main': doc_name, 'shadow': md.name, 'shadow_sha256': mb, 'shadow_bytes': sz})
    if declared:
        warnings.append({'rule_id': 'R6', 'what': '双件并存但场内存在关系声明/绑定行（正本=%s）→ 不 fail' % doc_name})
    else:
        for d in dual:
            problems.append({'rule_id': 'R6', 'where': d['shadow'],
                             'what': '双件并存且均无关系声明（正本未判定、中间稿状态不明）',
                             'basis': 'R6-2: fail 条件=二者均无关系声明'})
    return problems, warnings, dual

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--doc', required=True)
    ap.add_argument('--config', required=True)
    a = ap.parse_args()
    cfg = json.loads(pathlib.Path(a.config).read_text(encoding='utf-8'))
    root = pathlib.Path(a.root)
    doc = root / a.doc
    problems, warnings = [], []
    out = {'root': str(root), 'doc': a.doc}
    if not doc.is_file():
        problems.append({'rule_id': 'R0', 'where': a.doc, 'what': '交付件缺失', 'basis': '结构事实: 文件不在盘'})
        out['ok'] = False; out['problems'] = problems; out['warnings'] = warnings
        out['bindings'] = []; out['derived_copies'] = []; out['edge_hits'] = []; out['dual_files'] = []
        print(json.dumps(out, ensure_ascii=False)); return
    b = doc.read_bytes()
    t = b.decode('utf-8', errors='replace')
    out['self_anchor'] = {'sha256': sha256(b), 'bytes': len(b)}
    nsec = cfg.get('sections', 6)
    p, w, nums = r1_sections(t, nsec); problems += p; warnings += w
    out['sections_found'] = nums
    p, w = r2_elements(t, cfg.get('elements', [])); problems += p; warnings += w
    for k in cfg.get('plain_fields', []):
        if k not in t:
            problems.append({'rule_id': 'R0', 'where': a.doc, 'what': '缺结构字段/标签 %s' % k,
                             'basis': 'R0: 结构事实（标识 token，非措辞变体）'})
    p, w, bindings = r3_anchors(t, doc, root); problems += p; warnings += w
    minb = cfg.get('min_bindings', 1)
    nb = len([x for x in bindings if x.get('rule_id') in ('R3-3', 'R3-1')])
    if nb < minb:
        problems.append({'rule_id': 'R3', 'where': a.doc, 'what': 'SHA256 绑定行不足: %d < %d' % (nb, minb),
                         'basis': 'R3/R6-4: 绑定行计数下限（沿用原门禁要求）'})
    out['bindings'] = bindings
    p, w, derived, edge_hits = r4_py_scan(root); problems += p; warnings += w
    out['derived_copies'] = derived; out['edge_hits'] = edge_hits
    warnings += r5_doc_literals(t, a.doc)
    p, w, dual = r6_dual(root, a.doc, t); problems += p; warnings += w
    out['dual_files'] = dual
    # 结构性附加检查（R0）：JSON 记录字段
    jr = cfg.get('json_records')
    if jr:
        js = root / jr['file']
        if not js.is_file():
            problems.append({'rule_id': 'R0', 'where': jr['file'], 'what': '验收 JSON 缺失', 'basis': '结构事实'})
        else:
            try:
                d = json.loads(js.read_text(encoding='utf-8'))
                rows = d if isinstance(d, list) else (d.get('records') if isinstance(d, dict) else [])
                if not isinstance(rows, list) or not rows:
                    problems.append({'rule_id': 'R0', 'where': jr['file'], 'what': '验收记录为空', 'basis': '结构事实'})
                for i, r in enumerate(rows if isinstance(rows, list) else []):
                    miss = [k for k in jr['required'] if k not in r]
                    if miss:
                        problems.append({'rule_id': 'R0', 'where': '%s#%d' % (jr['file'], i),
                                         'what': '记录%d缺字段 %s' % (i, ','.join(miss)), 'basis': '结构事实'})
            except Exception as e:
                problems.append({'rule_id': 'R0', 'where': jr['file'], 'what': '验收 JSON 不可解析: %s' % str(e)[:80], 'basis': '结构事实'})
    if cfg.get('tpl'):
        if not (root / cfg['tpl']).is_file():
            problems.append({'rule_id': 'R0', 'where': cfg['tpl'], 'what': '指定期件缺失', 'basis': '结构事实'})
    out['ok'] = len(problems) == 0
    out['problems'] = problems
    out['warnings'] = warnings
    print(json.dumps(out, ensure_ascii=False))

if __name__ == '__main__':
    main()
