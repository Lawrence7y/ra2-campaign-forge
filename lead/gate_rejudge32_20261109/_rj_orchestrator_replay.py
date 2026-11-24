# -*- coding: utf-8 -*-
r"""_rj_orchestrator_replay.py — 逐字复刻当前任务 payload 的 REJUDGE_CODE（只读）。
来源：.zcode/workflow-runs/dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs
      const REJUDGE_CODE = [...].join('\n')（payload.lowered 内）。
用途：核对编排方自己那份双轨输出里「几域 gateProblems 非空 / 几域 bindings=0」。
"""
import json
import pathlib
import re
import sys

root = pathlib.Path('D:/Project/ra2-campaign-forge')
sys.path.insert(0, str(root / 'lead/gate_fp7_20261108'))
o = {'rows': [], 'loadedPredicates': False, 'err': ''}
try:
    import _g7_predicates as g7
    o['loadedPredicates'] = True
except Exception as e:
    o['err'] = str(e)
src = root / 'lead/gate_doc_name_fix_20261109/_dn_regate_out.json'
d = json.loads(src.read_text(encoding='utf-8'))
for r in d['rows']:
    rec = {'domain': r['domain'], 'main': r['main'], 'mainBytes': r['mainBytes'],
           'gateProblems': r.get('gateProblems', []), 'bindings': r.get('bindings'),
           'banned': r.get('params', {}).get('banned', [])}
    p = root / r['domain'].rstrip('/') / r['main']
    if not p.is_file():
        rec['state'] = 'MAIN_MISSING'
        o['rows'].append(rec)
        continue
    t = p.read_text(encoding='utf-8', errors='replace')
    rec['state'] = 'OK'
    rec['sha256'] = __import__('hashlib').sha256(p.read_bytes()).hexdigest()
    if o['loadedPredicates'] and rec['banned']:
        prob10, warn10, hits10 = g7.r10_scan(t, rec['banned'])
        prob12, hits12 = g7.r12_scan(t, rec['banned'])
        naive = []
        for tok in rec['banned']:
            if tok in t:
                naive.append(tok)
        rec['naiveHits'] = naive
        rec['r10Problems'] = prob10
        rec['r10Warnings'] = len(warn10)
        rec['r10Kinds'] = {}
        for h in hits10:
            rec['r10Kinds'][h['kind']] = rec['r10Kinds'].get(h['kind'], 0) + 1
        rec['r12Problems'] = prob12
    else:
        rec['naiveHits'] = [tok for tok in rec['banned'] if tok in t]
        rec['r10Problems'] = ['SKIP: predicates not loaded or empty banned list']
    rec['bindingLines'] = len(re.findall(
        r'被核对象 SHA256\s*=\s*`?[0-9a-fA-F]{64}`?', t))
    o['rows'].append(rec)
print(json.dumps(o, ensure_ascii=False))
