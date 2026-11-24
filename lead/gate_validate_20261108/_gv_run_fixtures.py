# -*- coding: utf-8 -*-
# _gv_run_fixtures.py —— 真违规样本回放：修正模板必须仍判 FAIL；对照原门禁口径
import json, pathlib, subprocess, sys, re

R = pathlib.Path('D:/Project/ra2-campaign-forge')
GV = R / 'lead/gate_validate_20261108'
FIX = GV / '_gv_fixtures'
OUT = GV / '_gv_out'
CFG = OUT / 'cfg'
CFG.mkdir(exist_ok=True)

CASES = [
    # (case根, doc, config, 期望 ok, 期望命中的 rule_id 集合)
    ('caseA', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, {'R4'}),
    ('caseB', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, {'R4'}),
    ('caseC', 'Alpha_Report.md', dict(sections=6, elements=[], min_bindings=0), False, {'R6'}),
    ('caseD/d0_correct', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), True, set()),
    ('caseD/d1_forged_binding', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), False, {'R3-3'}),
    ('caseD/d2_silent_mismatch', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, {'R3-2'}),
    ('caseD/d3_missing_target', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), False, {'R3-3c'}),
    ('caseE/e1_missing_section', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, {'R1'}),
    ('caseE/e2_synonym', 'SPEC.md',
     dict(sections=6, elements=['HANDOFF_COMPLETE', '最小字段', '不放行采集'], min_bindings=0), False, {'R2'}),
    ('caseF', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, {'R4'}),
]

lines = []
W = lines.append
results = []
for case, doc, cfg, want_ok, want_rules in CASES:
    cp = CFG / ('cfg_fix_%s.json' % case.replace('/', '_'))
    cp.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(GV / '_gv_fixed_rules.py'),
                        '--root', str(FIX / case), '--doc', doc, '--config', str(cp)],
                       capture_output=True, timeout=600)
    out = json.loads(r.stdout.decode('utf-8', 'replace').strip())
    rules_hit = sorted({p['rule_id'] for p in out.get('problems', [])})
    verdict = 'PASS' if (out['ok'] == want_ok and want_rules <= set(rules_hit)) else 'MISMATCH'
    results.append({'case': case, 'want_ok': want_ok, 'got_ok': out['ok'],
                    'want_rules': sorted(want_rules), 'rules_hit': rules_hit,
                    'problems': out.get('problems'), 'n_warn': len(out.get('warnings', [])),
                    'derived_copies': out.get('derived_copies'), 'edge_hits': out.get('edge_hits'),
                    'dual_files': out.get('dual_files'), 'bindings': out.get('bindings'),
                    'verdict': verdict})
    W('%-26s want_ok=%-5s got_ok=%-5s rules_hit=%-12s %s' % (case, want_ok, out['ok'], rules_hit or [], verdict))
    for p in out.get('problems', []):
        W('    PROBLEM %s' % json.dumps(p, ensure_ascii=False)[:210])

# ---- 原门禁口径对照（caseA/B/F：子串/正则扫描会怎么判） ----
W('')
W('=== 原门禁口径对照（子串/正则扫描） ===')
ORIG_PY_BANNED = ['OpenProcess', 'ReadProcessMemory', 'SuspendThread', 'StackWalk',
                  'MiniDump', 'CreateRemoteThread', 'ctypes.windll']
for case, pats in (('caseA', [r'subprocess\.(Popen|run|call)\s*\([^)]*(gamemd|ra2loader|YURI)']),
                   ('caseB', None), ('caseF', None)):
    root = FIX / case
    for py in sorted(root.glob('*.py')):
        s = py.read_text(encoding='utf-8')
        if pats:
            hit = any(re.search(p, s) for p in pats)
            W('%s/%s 原口径(启动正则)命中=%s' % (case, py.name, hit))
        else:
            hits = [b for b in ORIG_PY_BANNED if b in s]
            W('%s/%s 原口径(禁词子串)命中=%s' % (case, py.name, hits))

(OUT / '_gv_fixtures_out.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(OUT / '_gv_fixtures.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
print('\n'.join(lines))
bad = [r for r in results if r['verdict'] != 'PASS']
print('--- verdict PASS=%d MISMATCH=%d' % (len(results) - len(bad), len(bad)))
