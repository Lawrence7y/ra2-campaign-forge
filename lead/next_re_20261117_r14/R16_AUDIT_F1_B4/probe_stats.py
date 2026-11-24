# -*- coding: utf-8 -*-
"""核验 VERDICT.md 里引用的统计数字。"""
import io, os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

d = json.load(io.open(os.path.join(V.HERE, 'verify_out.json'), encoding='utf-8'))
rows = d['rows']

print('appended_len: min=%d max=%d' % (min(r['A']['appended_len'] for r in rows),
                                       max(r['A']['appended_len'] for r in rows)))
print('distinct vt    =', len({r['decl']['vt'] for r in rows}))
print('distinct slot  =', len({r['decl']['slot'] for r in rows}),
      sorted({r['decl']['slot'] for r in rows}))
print('distinct class =', len({r['row_class'] for r in rows}))
print('distinct site  =', len({r['decl']['site'] for r in rows}))
print('distinct func  =', len({r['site_func'] for r in rows}))
print('distinct mangled=', len({r['decl']['mangled'] for r in rows}))
nw = [r['C2']['n_writes'] for r in rows]
print('n_writes per table: min=%d max=%d  values=%s' % (min(nw), max(nw), sorted(set(nw))))
und = [r['entry'] for r in rows if any(w['verdict'] == 'unknown_func' for w in r['C2']['writes'])]
print('rows with unknown_func write points = %d %s' % (len(und), und))
print('total unknown_func write points = %d'
      % sum(1 for r in rows for w in r['C2']['writes'] if w['verdict'] == 'unknown_func'))
print('D checks keys =', len(rows[0]['D']['checks']), list(rows[0]['D']['checks']))
print('E need tokens count = 15 (as written in VERDICT)')
# 逐项 B 计数
for k in ('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8_strict'):
    print('  %s = %d/18' % (k, sum(1 for r in rows if r['B'][k])))
