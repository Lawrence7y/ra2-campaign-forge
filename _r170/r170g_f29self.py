#!/usr/bin/env python3
"""R170 G：F29 自指假句仍在 statement —— R165 只改了 limitations，statement 未回收。
判据：同一行内 statement 断言「不在本条任何一列」，而 limitations 明写正确措辞应为
「该数不参与本条任何计数」、并称该句「自身即反例」。二者在同一行内互斥。
"""
import glob, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
L=ROOT+'/lead/next_re_20261117_r14'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:230])

vers=sorted(glob.glob(L+'/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv'))
row=[]
for p in vers:
    v=os.path.basename(os.path.dirname(p)).split('_')[-1]
    f29=None
    for ln in open(p,encoding='utf-8',newline='').read().split('\n')[1:]:
        if ln.startswith('F29\t'): f29=ln.split('\t'); break
    a=f29[1].count('不在本条任何一列'); b=f29[4].count('不在本条任何一列')
    c=f29[1].count('不参与本条任何计数'); d=f29[4].count('不参与本条任何计数')
    row.append((v,a,b,c,d))
    print('%-5s stmt_old=%d lim_old=%d stmt_new=%d lim_new=%d'%(v,a,b,c,d))
ck('G1 逐版首现「不在本条任何一列」在 statement 的版本', True, next((r[0] for r in row if r[1]), None))
ck('G2 V549 仍在 statement 出现（limitations 已给出正确措辞）', row[-1][1]==1 and row[-1][3]==0 and row[-1][4]>=1, row[-1])
# 精确子串
f29=[r for r in open(L+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv',encoding='utf-8',newline='').read().split('\n') if r.startswith('F29\t')][0].split('\t')
s=f29[1]; lim=f29[4]
i=s.index('不在本条任何一列')
print('STMT ctx :', repr(s[max(0,i-60):i+30]))
j=lim.index('不是**「不在任何一列」') if '不是**「不在任何一列」' in lim else lim.index('不在任何一列')
print('LIM  ctx :', repr(lim[max(0,j-90):j+60]))
ck('G3 limitations 明写正确措辞 = 该数不参与本条任何计数', '该数不参与本条任何计数' in lim, True)
ck('G4 limitations 称该行自身即反例', '自身即反例' in lim, True)
ck('G5 同表另有「不在本条任何一列」的行数（应恰 1 = F29 自身）',
   sum(1 for p in open(L+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv',encoding='utf-8',newline='').read().split('\n')[1:] if p.strip() and '不在本条任何一列' in p)==1, 1)
# 反控：把该句抽掉后，「6 个不同桩体」在本行的出现次数（=2）证明声明句自身是第二处
ck('G6 反控：「6 个不同桩体」在本行出现 2 次（=声明句自指）', (s+'\n'+lim).count('6 个不同桩体')==2, (s.count('6 个不同桩体'), lim.count('6 个不同桩体')))
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'per_version':row},
          open(ROOT+'/_r170/r170g_f29self.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
