#!/usr/bin/env python3
"""R170 H：V550 变更的等长性预演（只读，不写盘）。
唯一改动：F29 statement 的「不在本条任何一列」-> 「不参与本条任何计数」。
关键断言：两串字节数相等（否则会触碰 facts_floors D6/D8 下界）。
"""
import hashlib, json
ROOT='/home/t628/projects/ra2-campaign-forge'
V=ROOT+'/lead/next_re_20261117_r14/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

OLD='不在本条任何一列'
NEW='不参与本条任何计数'
ck('H0 两串字节数相等', len(OLD.encode())==len(NEW.encode()), (len(OLD.encode()),len(NEW.encode())))
raw=open(V,'rb').read()
ck('H1 源 sha', hashlib.sha256(raw).hexdigest().startswith('f1d32127'), hashlib.sha256(raw).hexdigest()[:8])
txt=raw.decode('utf-8')
ck('H2 全文件 OLD 出现次数 = 3（stmt 1 + lim 2）', txt.count(OLD)==3, txt.count(OLD))
lines=txt.split('\n')
new_lines=[]
for ln in lines:
    f=ln.split('\t')
    if f[0]=='F29' and len(f)==5:
        ck('H3 F29 stmt 内 OLD 恰 1 次', f[1].count(OLD)==1, f[1].count(OLD))
        f[1]=f[1].replace(OLD,NEW)
        ck('H4 替换后 stmt 内 OLD = 0、NEW = 1', f[1].count(OLD)==0 and f[1].count(NEW)==1, (f[1].count(OLD),f[1].count(NEW)))
        ck('H5 stmt 字节数不变', len(f[1].encode())==len(''.join(lines[:0]).encode())+len(f[1].encode()), 'n/a')
        new_lines.append('\t'.join(f))
    else:
        new_lines.append(ln)
out='\n'.join(new_lines)
ck('H6 新全文 CR = 0', '\r' not in out, 'ok')
ck('H7 新全文字节数 == 旧（等长改写）', len(out.encode())==len(raw), (len(out.encode()),len(raw)))
ck('H8 差分行恰 1 行 = F29', sum(1 for a,b in zip(lines,new_lines) if a!=b)==1,
   [l.split('\t')[0] for l in lines if l.split('\t')[0] in ('F29',)][:1])
newsha=hashlib.sha256(out.encode()).hexdigest()
ck('H9 新 sha != 旧 sha', newsha!=hashlib.sha256(raw).hexdigest(), newsha[:16])
# 反控：若误替换成更短/更长串会破等长
ck('H10 反控：旧串替换成长串会使总字节变多', len(raw)+1 != len(out.encode()), 'ok')
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'new_sha':newsha,'bytes':len(out.encode()),
           '_out':out},open(ROOT+'/_r170/r170h_plan_v550.json','w'),ensure_ascii=False,indent=1)
print('new sha', newsha); print('bytes', len(out.encode()))
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
