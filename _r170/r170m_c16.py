#!/usr/bin/env python3
"""R170 M：C16 下界重钉（新增 §2.175，unpinned 1 -> 0）。
沿 R169 同法：实测本节字节 -> floor = 一半 -> 重钉 C16_FLOORS_SHA256。
反控：GATE_VER 不动、C7_TEXT/FREEZE/C14_TEXT 三者不动（本轮未改 DISC_* 任何行）。
"""
import hashlib, json, os, re, py_compile
ROOT='/home/t628/projects/ra2-campaign-forge'
CD=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
RC=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
BAK=ROOT+'/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])
def sha(b): return hashlib.sha256(b).hexdigest()

b0=open(CD,'rb').read()
bak=os.path.join(BAK,'check_disc.py.before_r170_C16.bak')
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b0)
ck('M0 备份 sha 相同', sha(open(bak,'rb').read())==sha(b0), bak.split('/')[-1])

txt=open(RC,'rb').read().decode('utf-8')
segs=[]; cur=None; buf=[]
for line in txt.split('\n'):
    m=re.match(r'^##\s+2\.(\d+)\b',line)
    if m:
        if cur is not None: segs.append((cur,len('\n'.join(buf).encode())))
        cur=int(m.group(1)); buf=[line]
    elif cur is not None: buf.append(line)
if cur is not None: segs.append((cur,len('\n'.join(buf).encode())))
d=dict(segs)
sz=d[175]; fl=sz//2
ck('M1 §2.175 实测字节', sz>0, (sz, fl))

src=open(CD,encoding='utf-8').read()
m=re.search(r'^C16_FLOORS = \{(.*?)^\}',src,re.M|re.S)
ns={}; exec(m.group(0),ns)
F=dict(ns['C16_FLOORS']); old_len=len(F)
norm_old='\n'.join('%d:%d'%(k,ns['C16_FLOORS'][k]) for k in sorted(ns['C16_FLOORS']))
sha_old=hashlib.sha256(norm_old.encode()).hexdigest()
cur_const=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",src,re.M).group(1)
ck('M2 旧表重算命中旧常量', sha_old==cur_const, (sha_old[:16],cur_const[:16]))

if 175 in F:
    ck('M3 幂等：175 已在表内且等于本次一半', F[175]==fl, (F[175],fl))
else:
    F[175]=fl
norm_new='\n'.join('%d:%d'%(k,F[k]) for k in sorted(F))
sha_new=hashlib.sha256(norm_new.encode()).hexdigest()
src2=re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sha_new,src,count=1,flags=re.M)
src2=re.sub(r'^(\s+)174: 4012,$', r'\1\1#',src2,count=0)  # no-op guard
# 在 174 之后插入 175
src2=re.sub(r'^(\s*)174: 4012,$', lambda mm: mm.group(0)+'\n%s175: %d,'%(mm.group(1),fl), src2, count=1, flags=re.M)
open(CD,'w',encoding='utf-8',newline='').write(src2)
py_compile.compile(CD,doraise=True)

src3=open(CD,encoding='utf-8').read()
m3=re.search(r'^C16_FLOORS = \{(.*?)^\}',src3,re.M|re.S)
ns3={}; exec(m3.group(0),ns3)
ck('M4 读回：175 在表内且值 = 一半', ns3['C16_FLOORS'].get(175)==fl, ns3['C16_FLOORS'].get(175))
ck('M5 读回：其余 %d 条逐条不变'%(old_len-1), all(ns3['C16_FLOORS'][k]==ns['C16_FLOORS'][k] for k in ns['C16_FLOORS']), old_len)
ck('M6 新 sha 常量 == 由新表重算', re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",src3,re.M).group(1)==sha_new, sha_new[:16])
ck('M7 反控：GATE_VER 未变（仍 R166）', re.search(r"^GATE_VER = '([^']+)'",src3,re.M).group(1)=='R166', 'ok')
for name in ('C7_TEXT_SHA256','C14_TEXT_SHA256','FREEZE_SHA256'):
    v0=re.search(r"^%s = '([0-9a-f]{64})'"%name,src,re.M).group(1)
    v1=re.search(r"^%s = '([0-9a-f]{64})'"%name,src3,re.M).group(1)
    ck('M8 反控：%s 一字未动'%name, v0==v1, v0[:16])
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'sz175':sz,'floor175':fl,
           'sha_old':sha_old,'sha_new':sha_new,'n_sections':len(ns3['C16_FLOORS']),
           'cd_sha':sha(open(CD,'rb').read())},
          open(ROOT+'/_r170/r170m_c16.json','w'),ensure_ascii=False,indent=1)
print('§2.175 =',sz,'B -> floor',fl,'| sections',len(ns3['C16_FLOORS']))
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
