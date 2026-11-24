# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:/Project/ra2-campaign-forge/lead"
V = ['只能判「不可复现」','只能判『不可复现』','只能判“不可复现”',
     '只能判不可复现','只能判(不可复现)','只能判 不可复现']
files = {}
for dp, dn, fn in os.walk(ROOT):
    rel = os.path.relpath(dp, ROOT).replace("\\", "/")
    d = 0 if rel == "." else rel.count("/") + 1
    if d > 2:
        dn[:] = []
        continue
    for f in fn:
        if f.endswith(".md"):
            p = os.path.join(dp, f)
            r = os.path.relpath(p, ROOT).replace("\\", "/")
            if r.startswith("needle_norm_20261109/"):
                continue   # 排除本任务写域，冻结到编排方 631 件口径
            files[r] = open(p, encoding="utf-8", errors="replace").read().splitlines()
U  = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if any(v in L for v in V)}
W1 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if '不可复现' in L}
W2 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if '只能判' in L}
W3 = W1 & W2
W4 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1)
      if re.search(r"只能判.{0,3}不可复现", L)}
print("U lines", len(U), "W1", len(W1), "W2", len(W2), "W3", len(W3), "W4", len(W4))
print("U-W3", len(U-W3), "W3-U", len(W3-U), "U-W4", len(U-W4), "W4-U", len(W4-U))
print("W1-U lines", len(W1-U))
print("W1-U 中含 只能判 的行数", sum(1 for r,i in W1-U if '只能判' in files[r][i-1]))
print("W1-U 中含引号的行数", sum(1 for r,i in W1-U if re.search(r'[「『“`]', files[r][i-1])))
nq = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if '只能判不可复现' in L}
print("no_quote lines", len(nq), "all in W3?", nq <= W3)
# 现行 6 负控是否覆盖 6 变体类
print("")
print("=== 负控类目覆盖矩阵（6 变体 vs 6 项负控）===")
controls = {
 'angle_corner': [('ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',123),
                  ('ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',25),
                  ('ledger_bound_20261109/LEDGER_BOUND_VOLUME.md',196),
                  ('ledger_bound_20261109/_lb_BOUND_VOLUME.md',129),
                  ('ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',215)],
 'curly_corner': [('s604_verdict_entry_20261109/_ve_DRAFT_S609.md',22)],
}
for name, nd in [('angle_corner',V[0]),('curly_corner',V[1]),('curly_double',V[2]),
                 ('no_quote',V[3]),('half_paren',V[4]),('no_punct',V[5])]:
    hits = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if nd in L}
    ctl = set(controls.get(name, []))
    print("  %-14s corpus_lines=%2d controls=%d covered=%s" %
          (name, len(hits), len(ctl), "YES" if ctl else "NO(零负控)"))
