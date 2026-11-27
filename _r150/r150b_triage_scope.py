#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 B：外部调研产物 _ext/f_partial_triage/ 的口径复算 ——
(1) 它用的 FACT_INDEX 是 v5.32 还是 v5.40（scope drift 的机械证据）；
(2) 它的 32 条与 v5.40 现盘「部分失联」集合的差集；
(3) 它每条 alive_paths 里点名的在盘件是否真在盘（对其结论做机械复核，不重做定性）。
只读。
"""
import hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead','next_re_20261117_r14')
TRI=os.path.join(ROOT,'_ext','f_partial_triage','TRIAGE.tsv')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

# --- 1. triage 的输入版本 ---
src=open(os.path.join(ROOT,'_ext','f_partial_triage','triage.py'),encoding='utf-8').read()
m=re.search(r"FIX = os\.path\.join\(ROOT,\s*'([^']+)'\)",src)
inp=m.group(1); print('  triage 输入:',inp)
ck('1.1 triage 输入是 v5.32 而非 v5.40', inp.endswith('R17_R104_FACTINDEX_V532/FACT_INDEX.tsv'), inp)
ck('1.2 该输入文件在盘', os.path.exists(os.path.join(ROOT,inp)))
sha532=hashlib.sha256(open(os.path.join(ROOT,inp),'rb').read()).hexdigest()
sha540=hashlib.sha256(open(os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv'),'rb').read()).hexdigest()
ck('1.3 两版 sha 不同（不是同一文件）', sha532!=sha540, (sha532[:8],sha540[:8]))

def row_of(path,fid):
    for ln in open(path,encoding='utf-8').read().split('\n')[1:]:
        if not ln.strip(): continue
        p=ln.split('\t')
        if p[0]==fid: return p
    return None
def nitems(col):
    n=0
    for seg in col.split(';'):
        if seg.strip(): n+=1
    return n
r532=row_of(os.path.join(ROOT,inp),'F35'); r540=row_of(os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv'),'F35')
n532,n540=nitems(r532[3]),nitems(r540[3])
print('  F35 evidence 项数 v5.32=%d  v5.40=%d'%(n532,n540))
ck('1.4 v5.32 的 F35 只有 1 个证据项（整行全失）', n532==1, n532)
ck('1.5 v5.40 的 F35 有 5 个证据项（R148 拆过后变部分失联）', n540==5, n540)

# --- 2. 33 vs 32 差集 ---
cen=json.load(open(os.path.join(ROOT,'_r150','r150a_evidcensus.json')))
partial_now=sorted(f for f,v in cen['census'].items() if v['live']>0 and v['dead']>0)
tri=[]
for ln in open(TRI,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    tri.append(ln.split('\t')[0])
tri=sorted(tri)
print('  现盘部分失联 %d 条 / triage 覆盖 %d 条'%(len(partial_now),len(tri)))
ck('2.1 现盘部分失联 33 条', len(partial_now)==33, len(partial_now))
ck('2.2 triage 覆盖 32 条', len(tri)==32, len(tri))
ck('2.3 差集恰 {F35}', sorted(set(partial_now)-set(tri))==['F35'], sorted(set(partial_now)-set(tri)))
ck('2.4 triage 没有多出任何 fid', set(tri)-set(partial_now)==set(), sorted(set(tri)-set(partial_now)))
ck('2.5 triage 明确排除 F23（整行全失）', 'F23' not in tri)

# --- 3. 逐条复核 alive_paths 是否真在盘 ---
bad=[]; tot=0; per={}
for ln in open(TRI,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    p=ln.split('\t'); fid=p[0]; alive=p[3]
    paths=[]
    for seg in alive.split(';'):
        s=seg.strip()
        if not s: continue
        # 锚点里可能含嵌套括号（如 (§2.10 / 一 / (a′))），故不能用「剥最后一对括号」：
        # 改为按 FACT_INDEX 同口径在第一个左括号处切路径；若切出的路径不存在，
        # 再退回整串（覆盖「文件名本身含括号」的情形）。S-353 记此自错。
        cand0 = s.split('(')[0].strip()
        paths.append(('cut', cand0, s))
    ok=0; miss=[]
    for _kind, cut, full in paths:
        tot+=1
        hit=False
        for s in ([cut, full] if cut!=full else [cut]):
            q=s.replace('\\','/')
            cands=[os.path.join(ROOT,q), os.path.join(ROOT,'lead',q)]
            if any(os.path.exists(c) for c in cands): hit=True; break
        if hit: ok+=1
        else: miss.append(full)
    per[fid]={'cited':len(paths),'alive':ok,'missing':miss}
    if miss: bad.append((fid,miss))
print('  triage 点名的在盘件共 %d 项，其中不存在 %d 项'%(tot,sum(len(x[1]) for x in bad)))
for fid,miss in bad: print('    %s 点的 alive 里不存在: %s'%(fid,miss))
ck('3.1 triage 点名的在盘件全部真在盘（0 项失配）', not bad, (len(bad), tot))

# 正控/负控
ck('4.1 正控 R14_COMMON.md 判活', os.path.exists(os.path.join(D14,'R14_COMMON.md')))
ck('4.2 负控 自造件判死', not os.path.exists(os.path.join(D14,'ZZZ_QQQ_NEVER.md')))
ck('4.3 负控 COVERAGE/PANEL.md 判死', not os.path.exists(os.path.join(D14,'COVERAGE','PANEL.md')))

# 三档统计自洽
import collections
cnt=collections.Counter(ln.split('\t')[4] for ln in open(TRI,encoding='utf-8').read().split('\n')[1:] if ln.strip())
print('  triage 三档:',dict(cnt))
ck('5.1 5+18+9=32', cnt['仍可核验']==5 and cnt['需重建']==18 and cnt['不可核验']==9 and sum(cnt.values())==32, dict(cnt))
rep=open(os.path.join(ROOT,'_ext','f_partial_triage','REPORT.md'),encoding='utf-8').read()
ck('5.2 REPORT 正文的 32/5/18/9 与 TSV 一致',
   '合计 **32** 条（5+18+9=32）' in rep)

out={'triage_input':inp,'triage_input_sha256':sha532,'v540_sha256':sha540,
     'f35_items':{'v532':n532,'v540':n540},
     'partial_now':partial_now,'triage_fids':tri,
     'diff':sorted(set(partial_now)-set(tri)),
     'alive_check':per,'alive_mismatch':bad,'alive_cited_total':tot,'tiers':dict(cnt)}
json.dump(out,open(os.path.join(ROOT,'_r150','r150b_triage_scope.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
