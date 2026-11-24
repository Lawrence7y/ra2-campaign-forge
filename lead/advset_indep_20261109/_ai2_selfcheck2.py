# -*- coding: utf-8 -*-
"""_ai2_selfcheck2.py — 修正 ② 的调用口径后重跑。
★ 如实纠偏：_ai2_selfcheck.py 的 ② 把整句当 pre 传给 dg_double_neg，
   但真实判定器 _dga_adversarial.py:215 走 DG.dg_scan(text, toks)，
   对每个 token 以 text[:m.start()] 为 pre。整句作 pre 会被 _scope 在「只是/，」
   处切断，导致 0/5 假阴性。本脚本按真实口径（dg_scan + token）重跑 ②。
只做 compile/exec 内存加载，不 import 保护件，不写保护树。"""
B = r'D:/Project/ra2-campaign-forge'
core = open(B + '/lead/dneg_generative_20261109/_dg_core.py', encoding='utf-8').read()
ns = {'__name__': '_dg_mem'}
exec(compile(core, '_dg_core.py', 'exec'), ns)
DG = ns['DG_DROPIN_RE']
ddn = ns['dg_double_neg']
Q = ns['DG_QUOTE_RE']

TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]


def detect_dg_pure_hit(text):
    """复刻 _dga_adversarial.py:210-217 的 DG_pure 判定：DG.dg_scan(text, toks)。"""
    import re
    toks = [t for t in TOKS if t in text] or ["已生效"]
    hits = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            r = ddn(text[:m.start()], text[m.end():])
            if r["hit"]:
                hits.append(r["hit_text"])
    return ("CATCH" if hits else "PASS"), (hits[0] if hits else "")


print('=== ② 修正口径后：未登记引号 ===')
MY_QUOTES = [('"', '"'), ("《", "》"), ("(", ")"), ("'", "'"),
             ("【", "】"), ("〈", "〉"), ("｢", "｣"),
             ("〔", "〕"), ("[", "]"), ("<<", ">>"), ("⟪", "⟫"), ("‹", "›")]
rows = []
for op, cl in MY_QUOTES:
    t = op + "并非不宣告已生效" + cl + "只是引文，本件不采信该说法"
    v, h = detect_dg_pure_hit(t)
    rows.append((op + cl, bool(Q.search(op + t[len(op):len(op) + 9] + cl)), v, h))
for q, reg, v, h in rows:
    print('  q=%-6s QUOTE_RE匹配=%-5s DG_pure=%-5s hit=%s' % (q, reg, v, repr(h)))
print('  ② 未登记引号 DG_pure=CATCH（应 PASS 的 fp）= %d/%d'
      % (sum(1 for q, reg, v, h in rows if v == 'CATCH'), len(rows)))
# 对照：已登记「」内置空格应判 PASS
t2 = "「 并非不宣告已生效 」只是引文，本件不采信该说法"
print('  ②b 已登记「」内置空格 expect=PASS DG_pure=%s' % detect_dg_pure_hit(t2)[0])
# 对照 P11 主样本
t3 = '"并非不宣告已生效"只是引文，本件不采信该说法'
print('  ②c P11 主样本 DG_pure=%s hit=%s' % detect_dg_pure_hit(t3))
print('SELF_RUN2_DONE')
