# -*- coding: utf-8 -*-
"""R208 p2：C16_FLOORS 重钉纳入 §2.215 + C16_FLOORS_SHA256 更新。
写入纪律：wx 备份 -> 断言旧 sha/CR -> 一次性写 -> 回读校验（含重算 sha 常量自洽）。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
CD=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
bak=BASE+'/check_disc.py.before_r208_pin_20261128.bak'
src=open(CD,'rb').read()
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
os.write(fd,src); os.close(fd)
assert open(bak,'rb').read()==src
s0=hashlib.sha256(src).hexdigest()
print('old sha',s0[:16],'CR',src.count(b'\r\n'))
s=src.decode('utf-8')
# 1) 找 2.215 节正文字节数（与 check_disc 同口径：标题行之后到下一节之前，'\n'.join 后 utf-8 长度）
def sect_bytes(text, sid):
    lines=text.split('\n')
    out=[];cur=None
    for l in lines:
        m=re.match(r'^##\s+(\d+)\.(\d+)',l)
        if m:
            cur=int(m.group(2))
            continue
        if cur==sid: out.append(l)
    return len('\n'.join(out).encode('utf-8')) if out else 0
sz=sect_bytes(s,215)
print('§2.215 measured bytes',sz)
floor=int(sz*0.5)
print('floor (half)',floor)
# 2) 插入 215 到 C16_FLOORS（按 id 升序位置）
m=re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})',s,re.S)
body=m.group(2)
assert '215:' not in body
lines=body.split('\n')
# 找到第一个 id > 215 的行插到它前面，否则末尾
ins=len(lines)
for i,l in enumerate(lines):
    mm=re.match(r'\s*(\d+):',l)
    if mm and int(mm.group(1))>215:
        ins=i;break
lines.insert(ins,'    215: %d,'%floor)
nb='\n'.join(lines)
s2=s[:m.start(2)]+nb+s[m.end(2):]
# 3) 重算 sha 常量
m2=re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})',s2,re.S)
body2=m2.group(2)
pairs=re.findall(r'(\d+):\s*(\d+)',body2)
d={int(k):int(v) for k,v in pairs}
norm='\n'.join('%d:%d'%(k,d[k]) for k in sorted(d))
newsha=hashlib.sha256(norm.encode('utf-8')).hexdigest()
print('floors',len(d),'new sha',newsha[:16])
s3=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%newsha,s2)
assert s3!=s2
open(CD+'.r208tmp','w',encoding='utf-8',newline='').write(s3)
os.replace(CD+'.r208tmp',CD)
chk=open(CD,'rb').read()
print('new file CR',chk.count(b'\r\n'),'== old',src.count(b'\r\n'))
assert chk.count(b'\r\n')==src.count(b'\r\n')
# 回读校验：重算
s4=open(CD,encoding='utf-8').read()
b4=re.search(r'(C16_FLOORS = \{\n)(.*?)(\n\})',s4,re.S).group(2)
d4={int(k):int(v) for k,v in re.findall(r'(\d+):\s*(\d+)',b4)}
n4='\n'.join('%d:%d'%(k,d4[k]) for k in sorted(d4))
h4=hashlib.sha256(n4.encode('utf-8')).hexdigest()
c4=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",s4).group(1)
print('verify: recomputed',h4[:16],'constant',c4[:16],'match',h4==c4,'ids',len(d4),'has215',215 in d4)
assert h4==c4
json.dump(dict(floor215=floor,measured=sz,ids=len(d4),sha=c4,oldsha=s0),open(ROOT+'/_r208/p2_pin_c16.json','w'),ensure_ascii=False,indent=1)
