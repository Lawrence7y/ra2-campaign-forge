#!/usr/bin/env python3
"""R170 I：§2.12 规则 D —— 复算执行员 #399 与审计员 #400 的每一条不一致。
两条被审对象：F29 statement/limitations 计数、F24 限定词最近距离口径。
"""
import json, re
ROOT='/home/t628/projects/ra2-campaign-forge'
V=ROOT+'/lead/next_re_20261117_r14/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:240])

rows={}
for p in open(V,encoding='utf-8',newline='').read().split('\n')[1:]:
    if not p.strip(): continue
    f=p.split('\t'); rows[f[0]]=f

# ---- 复算 1：#399/#400 一致指出的「6 个不同桩体」在 limitations 是 2 次而非 1 次 ----
s29,l29=rows['F29'][1],rows['F29'][4]
ck('K1 「6 个不同桩体」statement 次数 = 1', s29.count('6 个不同桩体')==1, s29.count('6 个不同桩体'))
ck('K2 「6 个不同桩体」limitations 次数 = 2（卡面原写 1 是错的）', l29.count('6 个不同桩体')==2, l29.count('6 个不同桩体'))
ck('K3 全行合计 = 3', (s29+'\n'+l29).count('6 个不同桩体')==3, (s29+'\n'+l29).count('6 个不同桩体'))
ck('K4 「不在本条任何一列」limitations 次数 = 2', l29.count('不在本条任何一列')==2, l29.count('不在本条任何一列'))
# 两处 limitations 的位置语义（#400 称 1602 为 R138 段「不在本条正文任何一列」、6948 为本段引文）
pos=[m.start() for m in re.finditer(re.escape('不在本条任何一列'),l29)]
ck('K5 两处位置', len(pos)==2, pos)
for p in pos:
    print('   ctx@%d: %s'%(p, l29[max(0,p-60):p+30].replace('\n',' ')))
# 结论仍成立（statement 那句是假句）
ck('K6 limitations 明写正确措辞', '该数不参与本条任何计数' in l29, l29.count('该数不参与本条任何计数'))
ck('K7 limitations 称该行自身即反例', '自身即反例' in l29, 'ok')
ck('K8 statement 仍未采用正确措辞', s29.count('不参与本条任何计数')==0, s29.count('不参与本条任何计数'))

# ---- 复算 2：#400 指出我的最近距离口径漏了「现盘/相对」两词 ----
s24=rows['F24'][1]
occ=[m.start() for m in re.finditer('4,417',s24)]
def nearest(keys):
    ks=[m.start() for k in keys for m in re.finditer(re.escape(k),s24)]
    return [min(abs(o-a) for a in ks) for o in occ]
narrow=nearest(['11-22','快照','失效','不是现盘'])   # 我 r170f 用的（错）
full=nearest(['11-22','快照','失效','不是现盘','现盘','相对'])  # 卡面声明的集合
print('occ',occ); print('narrow',narrow); print('full',full)
ck('L1 6 次出现', len(occ)==6, len(occ))
ck('L2 narrow 口径 = [120,605,31,45,276,651]（我 r170f 的值，可复现）', narrow==[120,605,31,45,276,651], narrow)
ck('L3 full 口径 = [120,605,31,49,189,186]（审计员 #400 指出的真值）', full==[120,605,31,49,189,186], full)
ck('L4 两种口径下窗口覆盖均 = 2/6（结论对口径不敏感）',
   sum(1 for o in occ if any(abs(o-a)<=100 for k in ('11-22','快照','失效','不是现盘','现盘','相对') for a in [m.start() for m in re.finditer(re.escape(k),s24)]))==2, '2/6')
ck('L5 现盘 在 5751 处（使 #5/#6 距离变 189/186）',
   any(m.start()==5751 for m in re.finditer('现盘',s24)), [m.start() for m in re.finditer('现盘',s24)][:6])

# ---- 复算 3：#400 的「V540..V549 F23 statement sha 恒 6552c5b84326」 ----
import glob,os,hashlib
seq=[]
for p in sorted(glob.glob(ROOT+'/lead/next_re_20261117_r14/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv')):
    v=os.path.basename(os.path.dirname(p)).split('_')[-1]
    for ln in open(p,encoding='utf-8',newline='').read().split('\n')[1:]:
        if ln.startswith('F23\t'):
            f=ln.split('\t'); seq.append((v,len(f[1].encode()),hashlib.sha256(f[1].encode()).hexdigest()[:12])); break
print(seq)
ck('M1 V540..V549 F23 statement sha 同一', len({x[2] for x in seq[-10:]})==1, {x[2] for x in seq[-10:]})
ck('M2 该 sha 前缀 = 6552c5b84326', seq[-1][2]=='6552c5b84326', seq[-1][2])
ck('M3 V530..V539 长度 208、V540..V549 长度 1012', {x[1] for x in seq[:10]}=={208} and {x[1] for x in seq[10:]}=={1012}, (seq[0][1],seq[-1][1]))

json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),
           'f29':{'stmt_old':s29.count('不在本条任何一列'),'lim_old':l29.count('不在本条任何一列'),
                  'tile_stmt':s29.count('6 个不同桩体'),'tile_lim':l29.count('6 个不同桩体')},
           'f24':{'occ':occ,'narrow':narrow,'full':full},
           'f23seq':seq},
          open(ROOT+'/_r170/r170i_recompute.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
