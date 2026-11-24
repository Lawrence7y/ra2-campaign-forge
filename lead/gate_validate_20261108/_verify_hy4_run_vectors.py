# -*- coding: utf-8 -*-
# _verify_hy4_run_vectors.py —— 独立复核：把自建真违规样本喂给被核方修正检查器 _gv_fixed_rules.py
# 只读调用（参数列表），不改被核方实现；输出写本任务写域 _verify_out/。
import json, pathlib, sys, hashlib

R = pathlib.Path('D:/Project/ra2-campaign-forge')
GV = R / 'lead' / 'gate_validate_20261108'
V = GV / '_verify_vectors'
OUT = GV / '_verify_out'
OUT.mkdir(parents=True, exist_ok=True)
CFG = OUT / 'vcfg'
CFG.mkdir(parents=True, exist_ok=True)
FIXED = GV / '_gv_fixed_rules.py'

CASES = [
    # (case, doc, config, 期望 ok, 说明)
    ('v1_launch', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, 'V1 启动游戏进程'),
    ('v2_newedge', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, 'V2 派生副本+新增调用边'),
    ('v3_dual', 'Alpha.md', dict(sections=6, elements=[], min_bindings=0), False, 'V3 双件无声明'),
    ('v4_anchor/d0_correct', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), True, 'V4 正确锚对照'),
    ('v4_anchor/d1_forged', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), False, 'V4 伪造绑定'),
    ('v4_anchor/d2_missing', 'SPEC.md', dict(sections=6, elements=[], min_bindings=1), False, 'V4 指向缺失对象'),
    ('v5_struct/e1_missing_section', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, 'V5 缺节'),
    ('v5_struct/e2_missing_element', 'SPEC.md', dict(sections=6, elements=['最小字段', '不放行采集'], min_bindings=0), False, 'V5 要素真缺席'),
    ('v6_getattr', 'SPEC.md', dict(sections=6, elements=[], min_bindings=0), False, 'V6 getattr 明文串'),
]

def call(case, doc, cfg):
    cp = CFG / ('c_%s.json' % case.replace('/', '_'))
    cp.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    # 参数列表调用，无 shell 拼接
    import subprocess
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(FIXED),
                        '--root', str(V / case), '--doc', doc, '--config', str(cp)],
                       capture_output=True, timeout=600)
    try:
        return json.loads(r.stdout.decode('utf-8', 'replace').strip()), r.returncode
    except Exception as e:
        return {'parse_error': str(e), 'stderr': r.stderr.decode('utf-8', 'replace')[:300]}, r.returncode

lines = []
W = lines.append
results = []
for case, doc, cfg, want_ok, desc in CASES:
    out, rc = call(case, doc, cfg)
    got = out.get('ok')
    rules = sorted({p.get('rule_id') for p in (out.get('problems') or [])})
    verdict = 'PASS' if got == want_ok else 'FAIL-OF-REVIEW'
    W('%-32s want=%-5s got=%-5s rules=%-18s %s | %s' % (case, want_ok, got, rules or [], verdict, desc))
    for p in (out.get('problems') or [])[:4]:
        W('    P %s %s' % (p.get('rule_id'), str(p.get('what'))[:110]))
    results.append(dict(case=case, desc=desc, want_ok=want_ok, got_ok=got, rc=rc,
                        rules_hit=rules, n_problems=len(out.get('problems') or []),
                        n_warn=len(out.get('warnings') or []),
                        derived_copies=out.get('derived_copies'), edge_hits=out.get('edge_hits'),
                        dual_files=out.get('dual_files'), bindings=out.get('bindings'),
                        verdict=verdict))
W('')
W('=== 汇总：%d 例，符合期望=%d，不符合=%d ===' %
  (len(results), sum(1 for r in results if r['verdict'] == 'PASS'),
   sum(1 for r in results if r['verdict'] != 'PASS')))
(OUT / '_verify_vectors_out.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(OUT / '_verify_vectors.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
print('\n'.join(lines))
