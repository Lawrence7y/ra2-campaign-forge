#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 G：规则 D —— 复算审计员 #339（deepseek, audit）的 7 条关键主张。
每条都给行号与逐字引文；不合则 FAIL 并打印实测量。
"""
import hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead'); D14=os.path.join(LEAD,'next_re_20261117_r14')
LOCK=os.path.join(LEAD,'LEAD_LOCK'); R14=os.path.join(D14,'R14_COMMON.md')
LED=os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md')
G=os.path.join(D14,'check_disc.py')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def L(p): return open(p,encoding='utf-8',errors='replace').read().split('\n')

lock=L(LOCK); r14=L(R14); led=L(LED); gate=open(G,encoding='utf-8').read()

def show(tag, lines, idxs, n=150):
    for i in idxs:
        if 0 < i <= len(lines):
            print('   %s L%d: %s'%(tag,i,lines[i-1][:n]))

# ---------- 主张 1：LEAD_LOCK 2688/2696、R14_COMMON 6147 已登记 F23 零可核验证据且处置「未降级」 ----------
show('LOCK',lock,[2688,2696]); show('R14',r14,[6147])
c1a = 'F23' in lock[2687] and ('零' in lock[2687] or '0' in lock[2687])
ck('1a LEAD_LOCK:2688 讲 F23 零证据', c1a, lock[2687][:120])
c1b = '未降级' in ''.join(lock[max(0,2680):2700])
ck('1b LEAD_LOCK 2680..2700 内有「未降级」', c1b)
c1c = '未降级' in ''.join(r14[6130:6160])
ck('1c R14_COMMON 6130..6160 内有「未降级」', c1c)
# S-357：这里原写死「>=5 次」，实测 LEAD_LOCK 全文只有 1 次 —— 又是把本该被查询的量写进断言。
# 改为：打印实测，只断言「至少 1 次」（即审计员引的这句确实在盘，不是它编的）。
n_weijiang = len(re.findall('未降级', '\n'.join(lock)))
n_r14_wj = len(re.findall('未降级', '\n'.join(r14)))
print('   LEAD_LOCK「未降级」%d 次 / R14_COMMON %d 次'%(n_weijiang,n_r14_wj))
ck('1d 「未降级」至少在 LEAD_LOCK 或 R14_COMMON 出现 1 次', n_weijiang+n_r14_wj>=1, (n_weijiang,n_r14_wj))

# ---------- 主张 2：LEAD_LOCK:3439(DО8)/R14:7723/台账 44626,44630；理由=证据全失但数字可算；「不降级也不升格」 ----------
show('LOCK',lock,[3439,3441,3443]); show('R14',r14,[7723]); show('LED',led,[44626,44630])
c2a = 'F23' in lock[3438] or 'F23' in lock[3437]
ck('2a LEAD_LOCK:3439 附近讲 F23 档位', c2a, lock[3438][:120])
c2b = ('降级' in ''.join(lock[3430:3450])) and ('升格' in ''.join(lock[3430:3450]))
ck('2b LEAD_LOCK 3430..3450 同现「降级」「升格」', c2b)
c2c = ('全失' in ''.join(lock[3430:3450])) or ('失联' in ''.join(lock[3430:3450]))
ck('2c 同段自述证据全失', c2c)
c2d = ('不降级' in ''.join(led[44620:44635])) or ('不升格' in ''.join(led[44620:44635]))
ck('2d 台账 44620..44635 有「不降级/不升格」', c2d)

# ---------- 主张 3：R14_COMMON 12645（R149）二选一前置条件 ----------
show('R14',r14,[12645],200)
c3 = ('降级' in r14[12644]) and ('R90' in r14[12644] or '档 2' in r14[12644])
ck('3 R14_COMMON:12645 讲「降级须先撤 R90 档 2」', c3, r14[12644][:160])

# ---------- 主张 4：LEAD_LOCK:3441 F35 单点+原件全失 ⇒ 不可核验成立；F35 grade 全程 [流程] ----------
c4 = 'F35' in lock[3440]
ck('4a LEAD_LOCK:3441 讲 F35', c4, lock[3440][:140])
import csv
fix=os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv')
f35=[l.split('\t') for l in open(fix,encoding='utf-8').read().split('\n') if l.startswith('F35\t')][0]
ck('4b F35 grade 现为 [流程]', f35[2]=='[流程]', f35[2])
# 回溯：查所有历史 FACT_INDEX 版本里 F35 的 grade
import glob
hist=[]
for p in sorted(glob.glob(os.path.join(D14,'R17_R1*_FACTINDEX_*','FACT_INDEX.tsv'))):
    for l in open(p,encoding='utf-8').read().split('\n'):
        if l.startswith('F35\t'):
            hist.append((os.path.basename(os.path.dirname(p)), l.split('\t')[2]))
print('   F35 grade 历史:', sorted(set(x[1] for x in hist)), '版本数', len(hist))
ck('4c F35 在所有版本里都是 [流程]（从未被降）', set(x[1] for x in hist)=={'[流程]'}, set(x[1] for x in hist))

# ---------- 主张 5：台账 39601 自标「照录，不重算」；47079/47083 七式是定义式 ----------
c5a = ('照录' in led[39600]) and ('不重算' in led[39600] or '未重算' in led[39600] or '不自行' in led[39600])
ck('5a 台账:39601 自标照录不重算', c5a, led[39600][:160])
c5b = ('定义式' in led[47078]) or ('定义式' in led[47082])
ck('5b 台账 47079/47083 提到「定义式」', c5b, (led[47078][:100], led[47082][:100]))
c5c = ('1196' in led[47078] or '1,196' in led[47078]) and 'N' in led[47078]
ck('5c 同行给出 1196=N−A 形态', c5c, led[47078][:160])

# ---------- 主张 6：门禁三项模式全 0；且无目录遍历能力 ----------
for pat in ('FACT_INDEX','FACTINDEX','R17_R1'):
    print('   门禁命中 %-12s : %d'%(pat, len(re.findall(pat,gate))))
ck('6a 门禁对 FACT_INDEX / FACTINDEX / R17_R1 全 0',
   all(len(re.findall(p,gate))==0 for p in ('FACT_INDEX','FACTINDEX','R17_R1')))
walk=[(k,len(re.findall(k,gate))) for k in ('os.walk','listdir','glob','scandir')]
print('   遍历原语:',walk)
ck('6b 门禁无任何目录遍历原语（结构性够不着）', all(n==0 for _,n in walk), walk)
# 正控/负控
pos=[(k,len(re.findall(k,gate))) for k in ('R14_COMMON','STATUS_BOARD')]
print('   正控:',pos)
ck('6c 正控 门禁确实引用 R14_COMMON 与 STATUS_BOARD', all(n>0 for _,n in pos), pos)
ck('6d 负控 自造串 0 命中', len(re.findall('ZZZ_GATE_QQQ',gate))==0)

# ---------- 主张 7：sha 前缀 fabd1e57 被 10 个文件引用 ----------
pref='fabd1e57'
hits=[]
for dp,dn,fn in os.walk(LEAD):
    if 'R17_LEAD_BASELINE' in dp: continue
    for f in fn:
        p=os.path.join(dp,f)
        try:
            if os.path.getsize(p)>8_000_000: continue
            t=open(p,encoding='utf-8',errors='replace').read()
        except Exception: continue
        if pref in t: hits.append(os.path.relpath(p,ROOT))
print('   含 fabd1e57 的文件 (%d):'%len(hits))
for h in sorted(hits): print('     ',h)
ck('7a fabd1e57 被 >=5 个真实文件引用（不是单点）', len(hits)>=5, len(hits))
# 审计员报「10 个文件」，但其中 next_re_20261117_r14_real/* 是指向真实件的 symlink、
# 另 2 个是本轮我自己的调度卡 ⇒ 真实独立载体要打折。S-358 记此。
real_hits=[]
for h in sorted(hits):
    fp=os.path.join(ROOT,h)
    if os.path.islink(fp): continue
    if '/_cards/' in h: continue
    real_hits.append(h)
print('   去掉 symlink 与本轮调度卡后的真实载体 (%d):'%len(real_hits))
for h in real_hits: print('     ',h)
sym=[h for h in sorted(hits) if os.path.islink(os.path.join(ROOT,h))]
print('   其中 symlink:',sym)
ck('7b 真实独立载体 5 个（审计员报的 10 含 symlink 与本轮自造卡，须打折）', len(real_hits)==5, len(real_hits))

out={'lock_2688':lock[2687][:200],'lock_2696':lock[2695][:200],'r14_6147':r14[6146][:200],
     'lock_3439':lock[3438][:200],'lock_3441':lock[3440][:200],'r14_7723':r14[7722][:200],
     'r14_12645':r14[12644][:250],'led_39601':led[39600][:200],
     'led_47079':led[47078][:200],'led_47083':led[47082][:200],
     'f35_grade_history':sorted(set(x[1] for x in hist)),
     'gate_FACT_INDEX_hits':len(re.findall('FACT_INDEX',gate)),
     'gate_walk_primitives':dict(walk),
     'fabd1e57_files':sorted(hits),'fabd1e57_real_carriers':real_hits}
json.dump(out,open(os.path.join(ROOT,'_r150','r150g_audit_recheck.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
