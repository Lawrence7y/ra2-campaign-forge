#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r172a: F24 的 4,417 六次出现的「分句级在场」判据（R171 待办①：给出客观判据）。

判据（全部机械、可失败）。称某次出现「逐次在场」当且仅当：
  (a) 同一分句内（先以 。；： 切段，再以 ，切分句）；且
  (b) 限定词与值「同层」：
       - 同括号深度，或
       - 限定词所在括号组紧贴值之后开括号（open ∈ [value_end, value_end+2]），即同位语括注。

限定词表 LIM 取 R170/R171 六词 + 非现盘（R171 已实测：W2={11-22,快照}、W3=+现盘；此处取并集作最宽口径，
宽口径下仍不在场者按任何子集口径都不在场）。

自测（正反控，11 条）：
  C1 正控：「4,417（2026-11-22 快照值）」同位语括注 ⇒ 在场
  C2 反控：「4,417，见 2026-11-22 快照值」跨逗号 ⇒ 不在场
  C3 反控：「（4,417）到 2026-11-22 快照值」跨括号 ⇒ 不在场
  C4 反控：限定词在另一段（句号后）⇒ 不在场
"""
import re, sys

LIM = ['11-22', '快照', '失效', '不是现盘', '非现盘', '现盘', '相对']
V = '4,417'
ADJ = 2   # 同位语括注允许的开括号距离

def groups(s):
    """返回 (depth 数组, 括号组列表[(open_idx, close_idx, depth)])"""
    d = [0]*len(s); stack = []; gl = []
    for i, ch in enumerate(s):
        if ch in '(（':
            stack.append(i); d[i] = len(stack)
        elif ch in ')）':
            d[i] = len(stack)
            if stack:
                o = stack.pop(); gl.append((o, i, len(stack)+1))
        else:
            d[i] = len(stack)
    return d, gl

def clauses(s, seps='。；：'):
    out = []; st = 0
    for i, ch in enumerate(s):
        if ch in seps:
            out.append((st, i+1)); st = i+1
    out.append((st, len(s)))
    return out

def is_clause_comma(s, i):
    """全角逗号恒为分句界；半角逗号仅当不在数字千分位内（左右皆非数字）才算分句界。"""
    if s[i] == '，':
        return True
    if s[i] != ',':
        return False
    l = s[i-1] if i > 0 else ''
    r = s[i+1] if i+1 < len(s) else ''
    return not (l.isdigit() and r.isdigit())

def clause_of(s, pos, seps):
    """分句 = 同括号深度内、被 。；： 或分句级逗号隔开的最大区间。

    分隔符只有在与 pos **同括号深度**时才切分；括注内部的 。；： 与逗号都不切
    （R172 前两版的真实缺陷：第一版把千分位逗号当界，第二版把括注内的逗号与分号当界）。
    """
    d, _ = groups(s)
    dp = d[pos]
    issep = lambda i: d[i] == dp and (s[i] in seps or is_clause_comma(s, i))
    lo = pos
    while lo > 0 and not issep(lo - 1):
        lo -= 1
    hi = pos
    while hi < len(s) and not issep(hi):
        hi += 1
    return (lo, hi)

def present(s, pos, seps='。；：'):
    a, b = clause_of(s, pos, seps)
    d, gl = groups(s)
    dp = d[pos]; vend = pos + len(V)
    hits = []
    for kw in LIM:
        for m in re.finditer(re.escape(kw), s):
            q = m.start()
            if not (a <= q < b): continue
            same_depth = (d[q] == dp)
            # 嵌套括注：限定词在值之后的某个括号组内，且该组整段落在同一分句里 ⇒ 视为值的后置限定
            nested = False
            if d[q] > dp:
                for (o, c, dep) in gl:
                    if o <= q <= c and o > vend and o >= a and c <= b:
                        nested = True; break
            adj_group = False
            if d[q] > dp:
                for (o, c, dep) in gl:
                    if o <= q <= c and vend <= o <= vend + ADJ:
                        adj_group = True; break
            if same_depth or adj_group or nested:
                hits.append((kw, q))
    return hits, (a, b)

def selftest():
    T = []
    s1 = '值 4,417（2026-11-22 快照值）在此。'
    h, _ = present(s1, s1.index(V)); T.append(('C1 正控 同位语括注应命中', len(h) >= 2))
    s2 = '值 4,417，见 2026-11-22 快照值。'
    h, _ = present(s2, s2.index(V)); T.append(('C2 反控 跨逗号不应命中', len(h) == 0))
    s3 = '（4,417）到 2026-11-22 快照值。'
    h, _ = present(s3, s3.index(V)); T.append(('C3 反控 跨括号不应命中', len(h) == 0))
    # C8：括注内部的逗号不作分句界（本脚本第二版的真实缺陷）
    # C9：值之后的嵌套括注（不同括号深度、开括号远在值后）应算后置限定
    s9 = '本项唯一语料值 = 4,417 文件 / 737,517,286 B（2026-11-22 快照值，非现盘体量）；'
    h9, _ = present(s9, s9.index(V)); T.append(('C9 正控 值后嵌套括注应命中', len(h9) >= 2))
    # C10 反控：限定词在值「之前」的括注里，不算后置限定
    s10 = '（2026-11-22 快照值）之后 4,417 件 在此；'
    h10, _ = present(s10, s10.index(V)); T.append(('C10 反控 前置括注不算后置限定', len(h10) == 0))
    # C11：括注内部的「；」也不得切分句（第二版的真实缺陷，位置 ST@449）
    s11 = '值 = 4,417 文件（快照 2026-11-22 快照值，非现盘体量；逐文件清单在此）；后话。'
    h11, cl11 = present(s11, s11.index(V))
    T.append(('C11 正控 括注内分号不切分句', len(h11) >= 2))
    s8 = '集合（tier，唯一可引） 4,417 件 是 2026-11-22 快照值。'
    h8, cl8 = present(s8, s8.index(V))
    T.append(('C8 正控 括注内逗号不作界（旧版会把值与该限定切到两分句）', len(h8) >= 2 and cl8[0] == 0))
    s4 = '值 4,417。快照 2026-11-22。'
    h, _ = present(s4, s4.index(V)); T.append(('C4 反控 句号后限定不应命中', len(h) == 0))
    # C5：值内的千分位逗号不得被当作分句界（这是本脚本第一版的真实缺陷）
    T.append(('C5 正控 千分位逗号不作分句界', is_clause_comma('4,417', 1) is False))
    T.append(('C6 正控 全角逗号作分句界', is_clause_comma('甲，乙', 1) is True))
    T.append(('C7 反控 半角逗号两侧非数字作分句界', is_clause_comma('甲,乙', 1) is True))
    return T

def main(path):
    rows = {}
    for line in open(path, encoding='utf-8'):
        c = line.rstrip('\n').split('\t'); rows[c[0]] = c
    f = rows['F24']
    res = []
    for col, name in ((1, 'ST'), (4, 'LIM')):
        s = f[col]
        for m in re.finditer(V, s):
            h, cl = present(s, m.start())
            res.append((name, m.start(), sorted(set(k for k, _ in h)), cl))
    n_in = 0
    print('== 分句级判据（，切分句 + 同层/同位语括注）==')
    for name, pos, hits, cl in res:
        if hits: n_in += 1
        print(('IN ' if hits else 'OUT') + f' {name}@{pos} 限定={hits} 分句={cl}')
    print(f'合计 {len(res)} 次，逐次在场 {n_in}/{len(res)}')
    return res, n_in

if __name__ == '__main__':
    T = selftest(); bad = [n for n, o in T if not o]
    for n, o in T: print(('PASS ' if o else 'FAIL ') + n)
    if bad: print('SELFTEST FAIL:', bad); sys.exit(2)
    print(f'SELFTEST {len(T)}/{len(T)} PASS')
    main(sys.argv[1] if len(sys.argv) > 1 else 'lead/next_re_20261117_r14/R17_R123_FACTINDEX_V551/FACT_INDEX.tsv')
