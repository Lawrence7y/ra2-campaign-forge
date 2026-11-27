#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 E：F23 四计数在权威件的「严格 token 承载」复核（修正 R150D 的子串污染）。
D 版用 substring 匹配，实测 458 在台账里出现 104 次（大量是 0x458 与时间戳），
故这里改用「非十六进制、非数字邻接」的严格 token 判据，并给出逐条落点。
只读。
"""
import json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead'); D14=os.path.join(LEAD,'next_re_20261117_r14')
SRC=[('台账',os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md')),
     ('R14_COMMON',os.path.join(D14,'R14_COMMON.md')),
     ('LEAD_LOCK',os.path.join(LEAD,'LEAD_LOCK')),
     ('看板',os.path.join(D14,'STATUS_BOARD.md')),
     ('看板归档',os.path.join(D14,'BOARD_ARCHIVE.md'))]
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

# 严格 token：左右都不是 [0-9A-Fa-f] 与 0x 前缀，也不是逗号后接 3 位（1,196 用另一式）
def tok(pat):
    return re.compile(r'(?<![0-9A-Fa-fx])'+pat+r'(?![0-9A-Fa-f])')
PATS={'458': tok('458'), '291': tok('291'), '293': tok('293'), '1196': tok(r'1,196')}
res={}
for name,p in SRC:
    t=open(p,encoding='utf-8',errors='replace').read()
    L=t.split('\n')
    d={}
    for k,rx in PATS.items():
        hits=[(i,ln) for i,ln in enumerate(L,1) if rx.search(ln)]
        withring=[(i) for i,ln in hits if '④' in ln]
        d[k]={'any':len(hits),'with_ring4':len(withring),'lines':withring[:6]}
    res[name]=d
    print('  %-10s 严格token: %s'%(name,{k:(v['any'],v['with_ring4']) for k,v in d.items()}))

ck('1.1 台账 458 严格 token 数远小于子串数（证 D 版确有污染）',
   res['台账']['458']['any'] < 104, res['台账']['458']['any'])
ck('1.2 台账四个数各至少 1 处严格 token', all(res['台账'][k]['any']>=1 for k in PATS),
   {k:res['台账'][k]['any'] for k in PATS})

# 关键：找同行给全四元组的行（严格 token 口径）
t=open(SRC[0][1],encoding='utf-8',errors='replace').read()
quad=[]
for i,ln in enumerate(t.split('\n'),1):
    if all(rx.search(ln) for rx in PATS.values()): quad.append(i)
print('  台账同行含全四元组（严格 token）的行:',quad)
ck('2.1 存在同行给全四元组的严格承载', len(quad)>=1, quad)
excerpts=[]
L=t.split('\n')
for i in quad[:4]:
    excerpts.append({'line':i,'text':L[i-1][:300]})
    print('   L%d: %s'%(i,L[i-1][:200]))

# 这些承载行是否有独立复算的记载（关键词）
indep=[]
for i in quad:
    ln=L[i-1]
    if re.search(r'独立复算|自行复算|两套独立实现|三角验证|实跑', ln): indep.append(i)
print('  其中带「独立复算/两套实现」字样的行:',indep)
ck('2.2 至少一处承载行自述独立复算', len(indep)>=1, indep)
ck('2.3 但该独立复算的实现目录不在盘（R41_RECOMPUTE 不存在）',
   not os.path.exists(os.path.join(D14,'R17_R41_RECOMPUTE')))

# 负控
ck('3.1 负控：1,196 的「无逗号」写法 1196 与「有逗号」1,196 是两个 token（不该都算）',
   PATS['1196'].search('1,196') is not None and PATS['1196'].search('11196') is None)
ck('3.2 负控：0x458 / 1458 / 4589 都不是 458 的严格 token',
   PATS['458'].search('0x458') is None and PATS['458'].search('1458') is None
   and PATS['458'].search('4589') is None)
ck('3.3 正控：句中出现 A 458 / 应为 458 时命中',
   PATS['458'].search('口径 A 458 / B 291') is not None)

out={'strict':{k:{kk:{'any':vv['any'],'with_ring4':vv['with_ring4'],'lines':vv['lines']}
                   for kk,vv in v.items()} for k,v in res.items()},
     'quad_lines':quad,'quad_excerpts':excerpts,'independent_lines':indep,
     'D_substring_458_in_ledger':104}
json.dump(out,open(os.path.join(ROOT,'_r150','r150e_f23_token.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
