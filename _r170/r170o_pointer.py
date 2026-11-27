#!/usr/bin/env python3
"""R170 O：FACT_INDEX_CURRENT.md 指针 V549 -> V550（先写新版本目录再改指针，顺序不可反）。"""
import hashlib, json, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
PTR=T+'/FACT_INDEX_CURRENT.md'
V550=T+'/R17_R122_FACTINDEX_V550/FACT_INDEX.tsv'
BAK=T+'/R17_LEAD_BASELINE'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])
raw=open(V550,'rb').read(); sha=hashlib.sha256(raw).hexdigest()
ck('O0 V550 身份', sha.startswith('d85034b0') and len(raw)==120495 and raw.count(b'\r')==0, (sha[:8],len(raw)))
t=open(PTR,encoding='utf-8').read()
ck('O1 指针改前指 V549', 'R17_R121_FACTINDEX_V549' in t and 'f1d3212715a23d9d' in t, 'ok')
b=open(PTR,'rb').read()
bak=os.path.join(BAK,'FACT_INDEX_CURRENT.md.before_r170.bak')
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
t2=t.replace('R17_R121_FACTINDEX_V549','R17_R122_FACTINDEX_V550')
t2=t2.replace('f1d3212715a23d9da5189a6c0630a0955d4a722a7f7ae10ce07791b2f8f4c085', sha)
t2=t2.replace('| 字节数 | 117545 |','| 字节数 | 120495 |')
t2=t2.replace('| 声明轮次 | R169 |','| 声明轮次 | R170 |')
t2=t2.replace('版本号 530..549 连续无缺，V549 同时是','版本号 530..550 连续无缺，V550 同时是')
t2=t2.replace('V530..V549 是 20 个可独立复核的快照','V530..V550 是 21 个可独立复核的快照')
t2=t2.replace('补一个 V547 草稿','补一个 V547 草稿')
open(PTR,'wb').write(t2.encode('utf-8'))
n=open(PTR,encoding='utf-8').read()
ck('O2 新指针指 V550 / d85034b0 / 120495 / R170', ('R17_R122_FACTINDEX_V550' in n) and (sha[:8] in n) and ('120495' in n) and ('R170' in n), 'ok')
ck('O3 旧目录号/旧字节/旧声明轮次全不残留', ('R17_R121_FACTINDEX_V549' not in n) and ('117545' not in n) and ('| 声明轮次 | R169 |' not in n), 'ok')
ck('O4 V549 仍在盘且 sha 未变', hashlib.sha256(open(T+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv','rb').read()).hexdigest().startswith('f1d32127'), 'ok')
ck('O5 指针 CR 0', open(PTR,'rb').read().count(b'\r')==0, 'ok')
ck('O6 反控：举例句里的 V547 保留（说明用，不该删）', '补一个 V547 草稿' in n, 'ok')
ck('O7 版本区间字符串 V530..V550 且在盘 21 份',
   'V530..V550' in n and len([d for d in os.listdir(T) if re.match(r'R17_R1\d\d_FACTINDEX_V5\d\d$',d)])==21,
   len([d for d in os.listdir(T) if re.match(r'R17_R1\d\d_FACTINDEX_V5\d\d$',d)]))
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'sha':sha,'bytes':len(raw)},
          open(ROOT+'/_r170/r170o_pointer.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
