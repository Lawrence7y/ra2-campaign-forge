# -*- coding: utf-8 -*-
"""R208 p13：C16_FLOORS 纳入 §2.216 并更新 C16_FLOORS_SHA256。
口径与 check_disc 同法：节正文 = 标题行之后到下一节之前的行，'\n'.join 后 utf-8 长度；下界 = 实测一半。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
CD=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
R14=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
src=open(CD,'rb').read()
bak=BASE+'/check_disc.py.before_r208_pin216_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,src); os.close(fd)
assert open(bak,'rb').read()==src
s=src.decode('utf-8')
def sect_bytes(text, sid):
    out=[];cur=None
    for l in text.split('\n'):
        m=re.match(r'^##\s+(\d+)\.(\d+)',l)
        if m: cur=int(m.group(2)); continue
        if cur==sid: out.append(l)
    return len('\n'.join(out).encode('utf-8')) if out else 0
rt=open(R14,encoding='utf-8',newline='').read()
sz=sect_bytes(rt,216); floor=sz//2
print('§2.216 measured %d floor %d'%(sz,floor))
m=re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})',s,re.S)
body=m.group(2)
assert '216:' not in body
lines=body.split('\n'); ins=len(lines)
for i,l in enumerate(lines):
    mm=re.match(r'\s*(\d+):',l)
    if mm and int(mm.group(1))>216: ins=i;break
lines.insert(ins,'    216: %d,'%floor)
s2=s[:m.start(2)]+'\n'.join(lines)+s[m.end(2):]
body2=re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})',s2,re.S).group(2)
d={int(k):int(v) for k,v in re.findall(r'(\d+):\s*(\d+)',body2)}
norm='\n'.join('%d:%d'%(k,d[k]) for k in sorted(d))
sha=hashlib.sha256(norm.encode()).hexdigest()
print('floors',len(d),'new sha',sha[:16])
s3=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sha,s2)
assert s3!=s2
tmp=CD+'.r208tmp'; open(tmp,'wb').write(s3.encode('utf-8')); os.replace(tmp,CD)
chk=open(CD,'rb').read()
assert chk.count(b'\r\n')==src.count(b'\r\n')
print('check_disc.py %d -> %d B CR %d'%(len(src),len(chk),chk.count(b'\r\n')))
json.dump({'sect216':sz,'floor':floor,'floors':len(d),'sha':sha},open(ROOT+'/_r208/p13_pin216.json','w'))
