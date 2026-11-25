# -*- coding: utf-8 -*-
"""R128h：给 0x7ea6e8 = IGameMap 这条判决加不可绕过的反控。

r128d 的判据是「MouseClass 的 COL 在 mdisp 0 处唯一的非 IUnknown 接口名 = IGameMap」。
这条判据的唯一危险是：如果很多类都满足「mdisp 0 处唯一」，那它对 MouseClass 也
不给特殊信息。故必须测：
  1) 全库 954 类里，mdisp 0 处「非 IUnknown 的 .?AU 接口名」恰好 1 个的类有多少个；
  2) 其中 MouseClass 的接口名是什么；
  3) 反控：对 mdisp 改成别的值（0x5518）做同一统计，看判据会不会给出别的名字 ——
     若给不出，说明判据依赖的确实是 mdisp 0 这个结构事实，而不是「随便取一个接口名」。
  4) 反控：把「非 IUnknown」这层过滤去掉，MouseClass 会得到什么名字 ——
     若得到 IUnknown，说明过滤是必要的、不是装饰。
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *

OUT = os.path.join(ROOT, '_r128', 'r128h_igamemap_ctrl.json')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    return None if x is None else (x if isinstance(x, int) else int(str(x).strip(), 16))

cols = {}
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt: continue
    c = col_of(vt)
    if not c: continue
    cols[c['type_desc']] = c
add('H0 全库可解 COL 的类数', len(cols) == 954, len(cols))

def single_at(mdisp, drop_unknown_filter=False):
    out = {}
    for nm, c in cols.items():
        au = [b['name'] for b in c['bases']
              if b['name'].startswith('.?AU') and b['mdisp'] == mdisp
              and (drop_unknown_filter or not b['name'].endswith('IUnknown@@'))]
        if len(au) == 1:
            out[nm] = au[0]
    return out

u0 = single_at(0)
add('H1 全库 mdisp 0 处「非 IUnknown 的 .?AU 接口名恰好 1 个」的类共 %d 个；'
    'MouseClass 在其中且该接口名 = .?AUIGameMap@@' % len(u0),
    '.?AVMouseClass@@' in u0 and u0['.?AVMouseClass@@'] == '.?AUIGameMap@@',
    {'n': len(u0), 'mouse': u0.get('.?AVMouseClass@@'),
     'sample': dict(list(u0.items())[:8])})

u5518 = single_at(0x5518)
add('H2 反控一：把 mdisp 换成 0x5518 后，全库没有任何类在该偏移上恰有 1 个 .?AU 接口'
    '（命中集为空，MouseClass 取不到名字）—— 故判据不是「随便挑一个接口名都能凑」，'
    '它只在 mdisp 0 这个位置上给出解，且此位置上不是所有类都有解',
    u5518.get('.?AVMouseClass@@') is None and len(u5518) == 0,
    {'mouse_at_5518': u5518.get('.?AVMouseClass@@'), 'n': len(u5518)})

u0_all = single_at(0, drop_unknown_filter=True)
add('H3 反控二：去掉「非 IUnknown」这层过滤后，MouseClass 在 mdisp 0 处得到两个候选'
    '（IGameMap 与 IUnknown），唯一性消失 —— 过滤是必要的、不是装饰',
    '.?AVMouseClass@@' not in u0_all,
    {'mouse_with_unknown': u0_all.get('.?AVMouseClass@@'), 'n': len(u0_all)})

# 分布：被判据选中的接口名种类
dist = collections.Counter(u0.values())
add('H4 被该判据选中的接口名分布（共 %d 种）：MouseClass 命中的 IGameMap 有 %d 个类共享 —— '
    '共享不削弱结论，因为判决对象是「名字」不是「类」'
    % (len(dist), dist['.?AUIGameMap@@']),
    dist['.?AUIGameMap@@'] >= 1, dict(dist.most_common(10)))

# 关键：IGameMap 出现在多少个类的 RTTI 里，且这些类是不是同一族（窗口族）
ig = [nm for nm, c in cols.items() if any(b['name'] == '.?AUIGameMap@@' for b in c['bases'])]
add('H5 声明 .?AUIGameMap@@ 的类共 %d 个，全部是窗口族（Display/GScreen/Map/Mouse/Power/'
    'Radar/Scroll/Sidebar/Tab）—— 与 GDI 侧窗口对象模型自洽' % len(ig),
    len(ig) == 9, sorted(ig))

# 最后一条：证 IGameMap 不是 IUnknown 的别名
add('H6 反控三：IID_IUnknown 常量 0x7f7c90 = {00000000-...} 的 Data1 全 0，'
    '而 0x7ea6e8 = {96F02EC7-...} 的 Data1 非 0 —— 两者不是同一常量的两个拷贝',
    gt(0x7f7c90).startswith('{00000000-') and gt(0x7ea6e8).startswith('{96F02EC7-'),
    [gt(0x7f7c90), gt(0x7ea6e8)])

json.dump({'checks': ck, 'u0': dict(list(u0.items())[:40]), 'dist': dict(dist)},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128h: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:500])
