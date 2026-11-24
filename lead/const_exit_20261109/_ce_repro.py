import sys, os, re, json, ast
sys.dont_write_bytecode = True
os.chdir('D:/Project/ra2-campaign-forge')
idx = {}
for base, lim in (('lead', 99), ('out', 3)):
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in ('__pycache__', '.git')]
        rel = os.path.relpath(dp, base)
        d = 0 if rel == '.' else rel.count(os.sep) + 1
        if d >= lim: dn[:] = []
        for f in fn:
            if f.endswith('.py'):
                idx.setdefault(f, []).append(os.path.join(dp, f).replace(chr(92), '/'))
pat = re.compile(r'([A-Za-z0-9_./\-]+\.py)')
mark = re.compile(r'PASS|exit\s*=\s*0|EXIT=0|SELF_TEST')
cited = {}
for dp, dn, fn in os.walk('lead'):
    dn[:] = [d for d in dn if d not in ('__pycache__', '.git')]
    if dp.count(os.sep) > 5: dn[:] = []
    for f in fn:
        if not f.endswith('.md'): continue
        p = os.path.join(dp, f).replace(chr(92), '/')
        try: t = open(p, encoding='utf-8', errors='replace').read()
        except Exception: continue
        for i, l in enumerate(t.split('\n'), 1):
            if not mark.search(l): continue
            for m in pat.finditer(l):
                b = os.path.basename(m.group(1).replace(chr(92), '/'))
                e = cited.setdefault(b, {'files': set(), 'n': 0})
                e['files'].add(p); e['n'] += 1
def sites(tree):
    funcs = {x.name: x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)}
    out = []
    for n in tree.body:
        for c in ast.walk(n):
            if not isinstance(c, ast.Call): continue
            f = c.func
            if isinstance(f, ast.Attribute) and f.attr == 'exit' and isinstance(f.value, ast.Name) and f.value.id == 'sys':
                arg = c.args[0] if c.args else None
                out.append((n.lineno, 'sys.exit', arg))
            elif isinstance(f, ast.Name) and f.id == 'exit':
                arg = c.args[0] if c.args else None
                out.append((n.lineno, 'exit', arg))
    res = []
    for ln, tag, arg in out:
        if arg is None:
            res.append((ln, tag, 'CONSTANT_EXIT', '无参数 -> 退出码 0'))
        elif isinstance(arg, ast.Constant):
            res.append((ln, tag, 'CONSTANT_EXIT', '字面量 ' + repr(arg.value)))
        elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id in funcs:
            fn = funcs[arg.func.id]
            rs = [x.value for x in ast.walk(fn) if isinstance(x, ast.Return)]
            kinds = set()
            for r in rs:
                if r is None: kinds.add('none')
                elif isinstance(r, ast.Constant): kinds.add('const')
                else: kinds.add('expr')
            if (not rs) or kinds <= {'const', 'none'}:
                res.append((ln, tag, 'CONSTANT_EXIT', tag + '(' + arg.func.id + '()) 的 return 全为字面量或缺省，共 ' + str(len(rs)) + ' 处'))
            else:
                res.append((ln, tag, 'CONDITIONAL_EXIT', tag + '(' + arg.func.id + '()) 至少一处 return 为非字面量，共 ' + str(len(rs)) + ' 处'))
        else:
            res.append((ln, tag, 'CONDITIONAL_EXIT', '参数是非字面量表达式'))
    return res
kd = json.load(open('lead/k1bit_detect_20261109/_kd_detect_out.json', encoding='utf-8'))
census = {os.path.basename(r['rel']) for r in kd['rows']}
rows = []; unread = 0; unparse = []
for b, e in sorted(cited.items()):
    if b not in idx or b in census: continue
    p = idx[b][0]
    try: raw = open(p, 'rb').read()
    except Exception: unread += 1; continue
    try: tree = ast.parse(raw.decode('utf-8-sig', errors='replace'))
    except SyntaxError as ex: unparse.append((b, p, str(ex)[:80])); continue
    ss = sites(tree)
    cls = 'NO_EXIT_AT_ALL' if not ss else ('CONDITIONAL_EXIT' if any(x[2] == 'CONDITIONAL_EXIT' for x in ss) else 'CONSTANT_EXIT')
    rows.append({'rel': p, 'basename': b, 'cls': cls, 'sites': ss, 'cites': e['n'], 'cfiles': len(e['files'])})
from collections import Counter
byc = Counter(r['cls'] for r in rows)
led = {}
for name in ('lead/PENDING_DECISIONS.md', 'lead/GOAL_THREE_TARGETS_20261018.md'):
    t = open(name, encoding='utf-8', errors='replace').read()
    hits = []
    for i, l in enumerate(t.split('\n'), 1):
        if not mark.search(l): continue
        for m in pat.finditer(l):
            b = os.path.basename(m.group(1).replace(chr(92), '/'))
            hits.append((i, b))
    led[name.split('/')[-1]] = hits
cls_of = {r['basename']: r['cls'] for r in rows}
vac = []
for name, hits in led.items():
    for i, b in hits:
        c = cls_of.get(b)
        if c in ('CONSTANT_EXIT', 'NO_EXIT_AT_ALL'):
            vac.append((name, i, b, c))
print(json.dumps({
 'n_cited_basenames': len(cited),
 'n_resolvable_out_of_census': len(rows) + unparse.__len__(),
 'n_scanned': len(rows), 'n_unread': unread, 'n_unparseable': len(unparse),
 'classes': dict(byc),
 'const_or_noexit': [{'rel': r['rel'], 'cls': r['cls'], 'cites': r['cites'], 'cfiles': r['cfiles'], 'sites': r['sites']} for r in rows if r['cls'] in ('CONSTANT_EXIT', 'NO_EXIT_AT_ALL')],
 'conditional': [{'basename': r['basename'], 'rel': r['rel'], 'cites': r['cites']} for r in rows if r['cls'] == 'CONDITIONAL_EXIT'],
 'unparseable': unparse,
 'ledger_hits_total': {k: len(v) for k, v in led.items()},
 'ledger_vacuous': vac,
}, ensure_ascii=False), file=sys.stderr)
print(json.dumps({'ok': True}), file=sys.stdout)