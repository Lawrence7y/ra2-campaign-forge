#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 D：F23 的四个计数（458 / 291 / 293 / 1,196）在现盘的活体承载面普查。
目的：区分两件被混谈的事 ——
  ① F23 的 evidence_paths 列 0 存活（R149 已证，列级事实）；
  ② 这四个计数在仓库里是否还有**在盘的活体承载**（行级事实）。
只读。
"""
import hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead')
D14=os.path.join(LEAD,'next_re_20261117_r14')
LED=os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

# 只扫权威面（不扫自身产物与备份），避免自我引用污染
SCAN=[('台账',LED),
      ('R14_COMMON',os.path.join(D14,'R14_COMMON.md')),
      ('LEAD_LOCK',os.path.join(LEAD,'LEAD_LOCK')),
      ('看板',os.path.join(D14,'STATUS_BOARD.md')),
      ('看板归档',os.path.join(D14,'BOARD_ARCHIVE.md'))]
txt={k:open(p,encoding='utf-8',errors='replace').read() for k,p in SCAN}

NUMS={'458':'458','291':'291','293':'293','1196':'1,196'}
def linehits(t,key):
    """返回同时含该数字与该行含 ④ 的行号列表（1-based）。"""
    out=[]
    for i,ln in enumerate(t.split('\n'),1):
        if key in ln and '④' in ln: out.append(i)
    return out

carriers={}
for name,t in txt.items():
    d={}
    for k,v in NUMS.items():
        d[k]=linehits(t,v)
    carriers[name]={k:len(v) for k,v in d.items()}
    print('  %-10s 含数字且同行有 ④ 的行数: %s'%(name,carriers[name]))
tot_live=sum(1 for name in carriers for k,v in carriers[name].items() if v>0)
ck('1.1 至少一个权威件里四个数全有承载体',
   all(carriers['台账'][k]>0 for k in NUMS), carriers['台账'])
ck('1.2 台账里四个数的承载行数各 >=1（逐数）',
   all(carriers['台账'][k]>=1 for k in NUMS), carriers['台账'])

# 精确：哪几行同时含 458+291+1196（同一行给全四元组才算「一次完整承载」）
quad=[]
for i,ln in enumerate(txt['台账'].split('\n'),1):
    if '458' in ln and '291' in ln and ('1,196' in ln or '1196' in ln):
        quad.append(i)
print('  台账里同行含 458+291+1196 的行:',quad)
ck('2.1 台账存在同行给全四元组的行（完整承载）', len(quad)>=1, quad)

# 取第一处完整承载，抽出上下文逐字记录
ctx=''
if quad:
    L=txt['台账'].split('\n')
    ctx=L[quad[0]-1][:600]
print('  首处完整承载行原文(前 600 字):',ctx[:400])

# ---- 正控 / 负控 ----
ck('3.1 正控：458 在台账里确有命中（不是解析失效）', txt['台账'].count('458')>0, txt['台账'].count('458'))
ck('3.2 负控：自造四元组 77,731 / 88,842 同行 0 命中',
   not any('77,731' in ln and '88,842' in ln for ln in txt['台账'].split('\n')))
ck('3.3 负控：单独出现的 458（无 ④ 同行）不计数 —— 说明筛子真在筛',
   len(linehits(txt['台账'],'458')) < txt['台账'].count('458'))

# ---- 与 F23 的 evidence_paths 逐项对照 ----
fix=os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv')
rows=[l.split('\t') for l in open(fix,encoding='utf-8').read().split('\n')[1:] if l.strip()]
f23=[r for r in rows if r[0]=='F23'][0]
ck('4.1 F23 两项证据都不在盘',
   all(not os.path.exists(os.path.join(ROOT,p.replace('\\','/').split('(')[0]))
       for p in f23[3].split(';') if p.strip()))
ck('4.2 F23 grade 原文 [已证]', f23[2]=='[已证]', f23[2])

# ---- R41_RECOMPUTE 的存活 ----
r41=[p for p in ('R17_R41_RECOMPUTE',) if os.path.exists(os.path.join(D14,p))]
print('  R17_R41_RECOMPUTE 目录在盘:', bool(r41))
ck('5.1 R41_RECOMPUTE 目录不在盘（独立复算的两套实现也失）', not r41)
n_cite=len(re.findall('R17_R41_RECOMPUTE', txt['台账']))
print('  台账引用 R41_RECOMPUTE 次数:',n_cite)
ck('5.2 台账对 R41_RECOMPUTE 的引用还在（引用在、被引件失）', n_cite>0, n_cite)

out={'carriers':carriers,'quad_lines':quad,'first_quad_excerpt':ctx,
     'f23_evidence':f23[3],'f23_grade':f23[2],
     'r41_dir_exists':bool(r41),'ledger_r41_citations':n_cite}
json.dump(out,open(os.path.join(ROOT,'_r150','r150d_f23_carriers.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
