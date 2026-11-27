#!/usr/bin/env python3
"""R170 J2：V550 回读复核（订正 r170j 的两条**我自己的断言缺陷** S-568/S-569）。
S-568：J11 把「字符 +3」写死，实际替换是 8 字→9 字（字符 +1、UTF-8 字节 +3）。
S-569：J12 期望 limitations 旧串 2 次，忘了本段追加文本自身引用该串 1 次 ⇒ 真值 3。
判据改为：statement 字符差 == +1 且字节差 == +3；limitations 旧串 == 3 且其中 2 处是历史段。
"""
import hashlib, io, json, csv, re
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
V549=T+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
V550=T+'/R17_R122_FACTINDEX_V550/FACT_INDEX.tsv'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

def load(p):
    return list(csv.reader(io.StringIO(open(p,encoding='utf-8',newline='').read()),delimiter='\t'))
r5=load(V549); r6=load(V550)
raw5=open(V549,'rb').read(); raw6=open(V550,'rb').read()
ck('K0 V550 55 行 × 5 列 / CR 0', len(r6)==55 and all(len(x)==5 for x in r6) and raw6.count(b'\r')==0, (len(r6),raw6.count(b'\r')))
ck('K1 V550 字节 120,495 / sha d85034b0', len(raw6)==120495 and hashlib.sha256(raw6).hexdigest().startswith('d85034b0'), (len(raw6),hashlib.sha256(raw6).hexdigest()[:8]))
i23=[k for k,x in enumerate(r6) if x[0]=='F23'][0]; i29=[k for k,x in enumerate(r6) if x[0]=='F29'][0]
ck('K2 F29 statement 字符 +1 / 字节 +3',
   len(r6[i29][1])-len(r5[i29][1])==1 and len(r6[i29][1].encode())-len(r5[i29][1].encode())==3,
   (len(r5[i29][1]),len(r6[i29][1]),len(r5[i29][1].encode()),len(r6[i29][1].encode())))
ck('K3 F29 statement 新串恰 1、旧串 0', r6[i29][1].count('不参与本条任何计数')==1 and r6[i29][1].count('不在本条任何一列')==0,
   (r6[i29][1].count('不参与本条任何计数'),r6[i29][1].count('不在本条任何一列')))
ck('K4 F29 limitations 旧串 3 次（历史 2 + 本轮引用 1）', r6[i29][4].count('不在本条任何一列')==3, r6[i29][4].count('不在本条任何一列'))
ck('K5 反控：追加段之前的前缀逐字节等于 V549 的 F29 limitations',
   r6[i29][4].startswith(r5[i29][4]), r5[i29][4][-40:])
ck('K6 F23 grade = 未取得 且 V549 是 [已证]', r6[i23][2]=='未取得' and r5[i23][2]=='[已证]', (r5[i23][2],r6[i23][2]))
ck('K7 F23 limitations 是纯前缀扩展', r6[i23][4].startswith(r5[i23][4]), 'ok')
ck('K8 F23 statement 一字未改', r6[i23][1]==r5[i23][1], 'ok')
diff=[r6[k][0] for k in range(55) if r6[k]!=r5[k]]
ck('K9 差分行恰 {F23,F29}', set(diff)=={'F23','F29'}, diff)
# grade 分布
from collections import Counter
c5=Counter(x[2] for x in r5[1:]); c6=Counter(x[2] for x in r6[1:])
print('grade V549',dict(c5)); print('grade V550',dict(c6))
ck('K10 grade 分布变化恰 [已证] −1 / 未取得 +1', c5['[已证]']-c6['[已证]']==1 and c6['未取得']-c5['未取得']==1, (dict(c5),dict(c6)))
ck('K11 反控：其余三档计数不变', c5['[静态推断]']==c6['[静态推断]'] and c5['[流程]']==c6['[流程]'], 'ok')
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'grade_v549':dict(c5),'grade_v550':dict(c6)},
          open(ROOT+'/_r170/r170j2_verify.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
