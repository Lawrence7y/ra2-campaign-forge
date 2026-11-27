#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 F：规则 D —— 亲自复算执行员 #337（hy4, exec）的七项主结论与审计员 #338/#339。
不复用执行员的脚本，独立写一遍；每项都带一个必须为真与一个必须为假的反例。
"""
import collections, hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead','next_re_20261117_r14')
V540=os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv')
V532=os.path.join(D14,'R17_R104_FACTINDEX_V532','FACT_INDEX.tsv')
TRI=os.path.join(ROOT,'_ext','f_partial_triage','TRIAGE.tsv')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def load(p):
    out=[]
    for ln in open(p,encoding='utf-8').read().split('\n'):
        if not ln.strip(): continue
        out.append(ln.split('\t'))
    return out[0], [r for r in out[1:] if r[0].strip()]

def cut(e):
    e=e.strip()
    i=e.find('(')
    return (e[:i] if i>=0 else e).strip().replace('\\','/')
def alive(rel):
    return os.path.exists(os.path.join(ROOT,rel)) or os.path.exists(os.path.join(ROOT,'lead',rel))

h540,body540=load(V540)
h532,body532=load(V532)
ck('1.1 v5.40 54 数据行', len(body540)==54, len(body540))
ck('1.2 v5.40 sha fabd1e57…', hashlib.sha256(open(V540,'rb').read()).hexdigest().startswith('fabd1e57'))
ck('1.3 v5.32 输入 sha 84863896…（与 v5.40 不同件）',
   hashlib.sha256(open(V532,'rb').read()).hexdigest().startswith('84863896'))
ck('1.4 v5.32 54 数据行', len(body532)==54, len(body532))

def stats(body):
    ent=0; lost=[]; zero=[]; part=[]; grade=collections.Counter()
    for r in body:
        es=[x for x in r[3].split(';') if x.strip()]
        ent+=len(es); grade[r[2]]+=1
        dead=[e for e in es if not alive(cut(e))]
        lost+= [cut(e) for e in dead]
        if es and len(dead)==len(es): zero.append(r[0])
        elif dead: part.append(r[0])
    return ent, lost, zero, part, dict(grade)

ent540,lost540,zero540,part540,g540=stats(body540)
ent532,lost532,zero532,part532,g532=stats(body532)
print('  v5.40: 项 %d / 失 %d / 唯一失 %d / 零存活 %s / 部分失联 %d'
      %(ent540,len(lost540),len(set(lost540)),zero540,len(part540)))
print('  v5.32: 项 %d / 失 %d / 唯一失 %d / 零存活 %s / 部分失联 %d'
      %(ent532,len(lost532),len(set(lost532)),zero532,len(part532)))

ck('2.1 #337 报 178 项 —— 复算一致', ent540==178, ent540)
ck('2.2 #337 报 43 失联项 —— 复算一致', len(lost540)==43, len(lost540))
ck('2.3 #337 报 16 唯一失联路径 —— 复算一致', len(set(lost540))==16, len(set(lost540)))
ck('2.4 #337 报零存活恰 [F23] —— 复算一致', zero540==['F23'], zero540)
ck('2.5 #337 报 grade 27/1/24/2 —— 复算一致',
   g540=={'[已证]':27,'[流程]':24,'未取得':2,'[静态推断]':1}, g540)
ck('2.6 #337 报部分失联 33 条 —— 复算一致', len(part540)==33, len(part540))

# 第二条结论的新事实：v5.32 阶段 F35 也是零存活
ck('3.1 v5.32 阶段零存活是 2 行 [F23, F35]（#337 独有发现）', zero532==['F23','F35'], zero532)
ck('3.2 v5.32 部分失联 32 条（故 triage 的 32 与 v5.32 严格对上）', len(part532)==32, len(part532))
ck('3.3 v5.32 与 v5.40 的失联项数同为 43（失联面没变，变的是 F35 的分母）',
   len(lost532)==len(lost540)==43, (len(lost532),len(lost540)))

# F35 项数
f35_540=[r for r in body540 if r[0]=='F35'][0]
f35_532=[r for r in body532 if r[0]=='F35'][0]
n540=len([x for x in f35_540[3].split(';') if x.strip()])
n532=len([x for x in f35_532[3].split(';') if x.strip()])
ck('4.1 F35 项数 v5.32=1 / v5.40=5', (n532,n540)==(1,5), (n532,n540))

# triage 覆盖
h,tr=load(TRI)
tri=sorted(r[0] for r in tr)
ck('5.1 triage 32 行', len(tr)==32, len(tr))
ck('5.2 triage fid 集 == v5.32 部分失联集（逐项相等）', tri==sorted(part532), (set(tri)^set(part532)))
ck('5.3 与 v5.40 的差集恰 {F35}，反向为空',
   sorted(set(part540)-set(tri))==['F35'] and set(tri)-set(part540)==set(),
   (sorted(set(part540)-set(tri)), sorted(set(tri)-set(part540))))

# 反例：一个必须为真的、一个必须为假的
f23=[r for r in body540 if r[0]=='F23'][0]
ck('6.1 必须为真：F23 两项都不在盘', all(not alive(cut(p)) for p in f23[3].split(';') if p.strip()))
# S-356 记此自错：我原把「必须为假」写成对同一事实再断言一次（not X 与 X 互为否定，
# 同一个 ck 里必然有一个 FAIL），那不是反例，是重复。真正的反例要考**判据本身**：
# 把 alive 换成恒真，同一个零存活算法必须给出不同的答案（0 行），否则说明算法对判据不敏感。
def stats_with(body, alivefn):
    zero=[]
    for r in body:
        es=[x for x in r[3].split(';') if x.strip()]
        dead=[e for e in es if not alivefn(cut(e))]
        if es and len(dead)==len(es): zero.append(r[0])
    return zero
always_true = stats_with(body540, lambda rel: True)
ck('6.2 必须为假的反例：judge 恒真时零存活应为 0 行（≠ 真的 1 行）',
   always_true == [], always_true)
ck('6.3 必须为真的反例：真 judge 下零存活恰 [F23]', stats_with(body540, alive)==['F23'])
ck('6.4 正控 R14_COMMON.md 判活', alive('lead/next_re_20261117_r14/R14_COMMON.md'))
ck('6.5 负控 自造件判死', not alive('lead/next_re_20261117_r14/ZZZ_Q.md'))

out={'v540':{'entries':ent540,'lost':len(lost540),'uniq':len(set(lost540)),
             'zero':zero540,'partial':len(part540),'grade':g540},
     'v532':{'entries':ent532,'lost':len(lost532),'uniq':len(set(lost532)),
             'zero':zero532,'partial':len(part532),'grade':g532},
     'f35_items':{'v532':n532,'v540':n540},
     'triage_rows':len(tr),'diff_v540_minus_tri':sorted(set(part540)-set(tri)),
     'diff_tri_minus_v540':sorted(set(tri)-set(part540))}
json.dump(out,open(os.path.join(ROOT,'_r150','r150f_rule_d.json'),'w'),ensure_ascii=False,indent=1)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
