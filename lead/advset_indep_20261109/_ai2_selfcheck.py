# -*- coding: utf-8 -*-
"""_ai2_selfcheck.py — 本会话独立重跑六条绕过构造 + 结构性不可达静态枚举。
只 re + 源码 compile/exec 内存加载，不 import 保护件（不产生 __pycache__），
不写保护树，不启动真机，不写采样代码。唯一写域 lead/advset_indep_20261109/。"""
import os

B = r'D:/Project/ra2-campaign-forge'

# memory-load protected source only (compile/exec, no import, no writes)
core = open(B + '/lead/dneg_generative_20261109/_dg_core.py', encoding='utf-8').read()
ns = {'__name__': '_dg_mem'}
exec(compile(core, '_dg_core.py', 'exec'), ns)
DG = ns['DG_DROPIN_RE']
ddn = ns['dg_double_neg']
BR = ns['DG_BREAK_RE']
SEC = ns['DG_SECOND_SUBJ_RE']
CO = ns['DG_COORD_RE']
NEG1, MID, NEG2 = ns['NEG1'], ns['MID'], ns['NEG2']
SECOND = ns['_SECOND']


def pure(s):
    return 'CATCH' if ddn(s)['hit'] else 'PASS'


def raw(s):
    return 'CATCH' if bool(DG.search(s)) else 'PASS'


print('=== ① 未登记边界词（应 PASS 却被 CATCH = fp）===')
w = ['究其根本', '说穿了', '细究起来', '退一步讲', '殊不知', '不宁唯是', '偏偏', '诚然']
r = [(x, bool(BR.search(x)), pure('前稿不敢不承认' + x + '本件不宣告已生效')) for x in w]
print(' ', r)
print('  ① n=%d 未登记且 fp = %d/%d' % (len(r), sum(1 for x, b, p in r if not b and p == 'CATCH'), len(r)))

print('=== ② 未登记引号 ===')
qp = [('〔', '〕'), ('[', ']'), ('<<', '>>'), ('⟪', '⟫'), ('‹', '›')]
r2 = [(a + b, pure(a + '并非不宣告已生效' + b + '只是引文，本件不采信该说法')) for a, b in qp]
print(' ', r2)
print('  ② fp = %d/%d' % (sum(1 for q, p in r2 if p == 'CATCH'), len(r2)))

print('=== ③ COMP 0..6（动词=写成，字符=甲）===')
r3 = [(n, pure('非写成' + '甲' * n + '不可才算本件已生效')) for n in range(0, 7)]
print(' ', r3)
print('  ③ <=4 全 CATCH =', all(p == 'CATCH' for n, p in r3 if n <= 4),
      '; >=5 全 PASS =', all(p == 'PASS' for n, p in r3 if n >= 5))

print('=== ④ 结构性不可达：T12 全笛卡尔积静态枚举 ===')
prod = set(a + b + c for a in set(NEG1) for b in set(MID) for c in set(NEG2))
sec_hit = [s for s in prod if SEC.search(s)]
coord_hit = [s for s in prod if CO.search(s)]
cart = len(set(NEG1)) * len(set(MID)) * len(set(NEG2))
print('  T12 笛卡尔积 = %d 去重 hit_text = %d ; 含 _SECOND = %d ; 含并列标记 = %d'
      % (cart, len(prod), len(sec_hit), len(coord_hit)))
tables = {k: ns[k] for k in ('NEG1', 'MID', 'NEG2', 'GAP', 'SCOPE_VERB', 'SPLIT_TAIL', 'PSEUDO_DN')}
in_tables = [(k, w) for k, ws in tables.items() for w in set(ws) if SEC.search(w)]
print('  7 张表全部条目中含 _SECOND 的条目 =', in_tables)
secwords = [w for w in SECOND.split('|') if '\\' not in w]
r4 = [(w, pure('非登记' + w + '不可才算本件已生效')) for w in secwords]
print('  T3 comp 塞入 %d 个 _SECOND 词 -> DG_pure 全 PASS = %s'
      % (len(r4), all(p == 'PASS' for w, p in r4)))
print('  ④ 结构性不可达 =', len(sec_hit) == 0 and len(in_tables) == 0 and all(p == 'PASS' for w, p in r4))

print('=== ⑤ 并列 veto 双向（fp + fn）===')
r5 = [('本件不承认抑或并不否认已生效', pure('本件不承认抑或并不否认已生效')),
      ('非写成甲或乙不可才算本件已生效', pure('非写成甲或乙不可才算本件已生效'))]
print(' ', r5, ' 双向成立 =', r5[0][1] == 'CATCH' and r5[1][1] == 'PASS')

print('=== ⑥ PSEUDO_DN 位置局部性 ===')
r6 = [(s, raw(s)) for s in ('无非不是不承认本件已生效',
                            '莫非并不是不承认本件已生效',
                            '莫不是不承认本件已生效')]
print(' ', r6, ' 全 CATCH =', all(p == 'CATCH' for s, p in r6))

print('=== 交付形态 guard co_names ===')
try:
    g = open(B + '/lead/gate_fp7_20261108/_g7_predicates.py', encoding='utf-8').read()
    gn = {'__name__': '_g7_mem'}
    exec(compile(g, '_g7_predicates.py', 'exec'), gn)
    for fn in ('r10_context', 'r12_scan'):
        cn = set(gn[fn].__code__.co_names)
        print(' ', fn, {k: (k in cn) for k in
                        ('_mask_quotes', '_scope', 'dg_double_neg', 'DG_SECOND_SUBJ_RE', 'DG_COORD_RE')})
except Exception as e:
    print('  g7 内存加载失败：', type(e).__name__, e)

print('SELF_RUN_DONE')
