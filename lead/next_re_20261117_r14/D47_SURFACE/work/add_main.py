# -*- coding: utf-8 -*-
"""Append a runnable __main__ block to surface.py (idempotent)."""
import io

p = 'surface.py'
s = io.open(p, encoding='utf-8').read()
if "__main__" in s:
    print('already has main block')
else:
    block = '''

if __name__ == '__main__':
    # 可复跑入口：分类 + 出表 + 达标算术（产物与 make_outputs.py 相同）
    import make_outputs
    ctx = make_outputs.main()
    print('proved rows            :', ctx['proved'])
    print('F1 / F2 / F3 / F4      :', ctx['cnt']['F1'], '/', ctx['cnt']['F2'],
          '/', ctx['cnt']['F3'], '/', ctx['cnt']['F4'])
    print('bands (B1..B5)         :', dict(ctx['band']))
    print('F1 by subsystem        :', dict(ctx['f1_by_sub']))
    print('nominal (D-43A/12.3)   : %d/22 -> %d/22' % (ctx['before'][0], ctx['after123'][0]))
    print('strict  (D-43A/12.3)   : %d/22 -> %d/22' % (ctx['before'][1], ctx['after123'][1]))
    print('wrote surface.tsv / distribution.tsv / REPORT.md / work/*')
'''
    io.open(p, 'w', encoding='utf-8').write(s.rstrip() + block)
    print('added main block')
