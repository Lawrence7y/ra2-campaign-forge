#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 C：F23「grade 该不该降」这条待办的前提检查 ——
(1) grade 轴的定义在盘有几处、措辞是否指「建立时的证据强度」而不是「原件现在还在」；
(2) 全库是否存在「证据原件失联 ⇒ grade 降级」这条规则（正控：必须能找到「降级」这个词的其它用法）；
(3) FACT_INDEX.tsv 本身是否被门禁 check_disc.py 覆盖（0 引用则说明它有零约束）。
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
def rd(p): return open(p,encoding='utf-8',errors='replace').read()

led=rd(LED); r14=rd(os.path.join(D14,'R14_COMMON.md')); lock=rd(os.path.join(LEAD,'LEAD_LOCK'))

# ---- 1. grade 轴的定义 ----
defs=[m for m in re.finditer(r'分级口径[：:](.{0,220})', led, re.S)]
print('  台账「分级口径」出现 %d 处'%len(defs))
# S-354：这里原写死「>=20 处」，实测 16 处 —— 断言里出现了本应被查询的量。
# 改为只断言「存在且不止一处」（这条是前提检查，不是计数命题），具体数一律打印后引用。
ck('1.1 台账分级口径定义存在且不止一处', len(defs)>=2, len(defs))
# 定义里是否出现「签发件已核 / 实测 / 独立重算」这类「建立时的证据形态」措辞
motive=sum(1 for m in defs if re.search(r'实测|独立重算|直接|签发件|字节', m.group(1)))
print('  其中提到实测/独立复算/字节等「证据形态」的: %d'%motive)
ck('1.2 定义措辞以「证据形态」为主（>=70%%）', motive>=0.7*len(defs), '%d/%d'%(motive,len(defs)))
# 定义里是否出现「文件是否还在盘」
ondisk=sum(1 for m in defs if re.search(r'在盘|现存|失联|存在性', m.group(1)))
print('  其中提到「在盘/现存/失联」的: %d'%ondisk)
ck('1.3 没有任何一处把 grade 定义成「原件是否仍在盘」', ondisk==0, ondisk)
sample=re.search(r'分级口径[：:](.{0,160})', led).group(1).replace('\n',' ')
print('  样本定义:', sample[:150])

# ---- 2. 有没有「原件失联 ⇒ 降级」这条规则 ----
hits=[]
for name,txt in (('台账',led),('R14_COMMON',r14),('LEAD_LOCK',lock)):
    for m in re.finditer(r'(失联|不在盘|原件.{0,6}失|已失)[^\n。；]{0,80}降级', txt):
        hits.append((name,m.group(0)[:120]))
    for m in re.finditer(r'降级[^\n。；]{0,80}(失联|不在盘|原件.{0,6}失|已失)', txt):
        hits.append((name,m.group(0)[:120]))
print('  「失联⇔降级」同句命中 %d 条'%len(hits))
for h in hits[:8]: print('   ',h)
ck('2.1 三份权威件里没有「原件失联 ⇒ grade 降级」这条规则', not hits, hits[:3])
# 正控：「降级」这个词本身必须能找到（不是判据把词弄丢了）
n_dg=len(re.findall('降级', led))
print('  台账「降级」出现 %d 次'%n_dg)
ck('2.2 正控：「降级」在台账里大量出现（>=200）', n_dg>=200, n_dg)
# 正控：确实存在「因证据不足而降级」的先例
prec=re.findall(r'[^\n]{0,60}(?:应降级|降为|降级为)[^\n]{0,60}', led)
print('  降级先例句 %d 条，样本:'%len(prec))
for p in prec[:3]: print('    ', p[:110])
ck('2.3 正控：存在「因证据不足/虚高而降级」的先例', len(prec)>=3, len(prec))

# ---- 3. FACT_INDEX 是否被门禁覆盖 ----
gate=rd(os.path.join(D14,'check_disc.py'))
n_fi=len(re.findall(r'FACT_INDEX', gate))
n_factindex_dir=len(re.findall(r'R17_R1\d\d_FACTINDEX', gate))
print('  check_disc.py 里 FACT_INDEX 命中 %d 次、FACTINDEX 目录名命中 %d 次'%(n_fi,n_factindex_dir))
ck('3.1 门禁对 FACT_INDEX 零引用（它有零约束）', n_fi==0 and n_factindex_dir==0, (n_fi,n_factindex_dir))
# 正控：门禁确实提到了别的台账/看板件（证明「没提到」不是解析失败）
# S-355：原把 LEAD_LOCK 也塞进「必有引用」清单，实测门禁对它 0 引用 —— 又是写死进断言的量。
# 改为：先逐个打印，再只用「实测确非零的那三个」做正控，并把 LEAD_LOCK=0 当作一条独立观察登记。
_pat={'R14_COMMON':0,'BOARD':0,'DISC_RECHECK':0,'LEAD_LOCK':0}
for kw in _pat: _pat[kw]=len(re.findall(kw,gate))
for kw,n in _pat.items(): print('   门禁提到 %-14s : %d 次'%(kw,n))
ck('3.2 正控：门禁对 R14_COMMON / 看板 / DISC_RECHECK 确有引用（解析没失效）',
   _pat['R14_COMMON']>0 and _pat['BOARD']>0 and _pat['DISC_RECHECK']>0, _pat)
ck('3.2b 观察登记（非断言）：门禁对 LEAD_LOCK 引用次数', True, _pat['LEAD_LOCK'])
# 负控：搜一个绝不该出现的串
ck('3.3 负控：自造串 ZZZ_GATE_NEVER_QQQ 在门禁里 0 命中',
   len(re.findall('ZZZ_GATE_NEVER_QQQ', gate))==0)

out={'grade_defs':len(defs),'defs_evidence_phrasing':motive,'defs_ondisk_phrasing':ondisk,
     'downgrade_on_missing_rule':hits,'downgrade_word_count':n_dg,'downgrade_precedents':len(prec),
     '_pat':_pat,'gate_FACT_INDEX_refs':n_fi,'gate_FACTINDEX_dir_refs':n_factindex_dir,
     'sample_definition':sample}
json.dump(out,open(os.path.join(ROOT,'_r150','r150c_grade_axis.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
