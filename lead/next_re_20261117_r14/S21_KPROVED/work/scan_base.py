import json, os, re, hashlib
import pefile, capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT=os.path.join(BASE,'S21_KPROVED','work')
pe=pefile.PE(EXE)
ib=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
code=text.get_data()[:text.Misc_VirtualSize]
base=ib+text.VirtualAddress
md5=hashlib.sha256(open(EXE,'rb').read()).hexdigest()
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
cs.detail=True
cs.skipdata=True
insns=[]; e8=0
for i in cs.disasm(code,base):
    insns.append((i.address,i.size,i.mnemonic,i.op_str,bytes(i.bytes).hex()))
    if i.mnemonic=='call' and i.size==5 and i.bytes[0]==0xE8:
        e8+=1
print('instructions',len(insns),'E8',e8,'sha256',md5)
# index by address and direct call targets
by_addr={a:(a,s,m,o,b) for a,s,m,o,b in insns}
calls={}
for a,s,m,o,b in insns:
    if m=='call' and s==5 and b.startswith('e8'):
        rel=int.from_bytes(bytes.fromhex(b[2:]),'little',signed=True)
        tgt=a+5+rel
        calls.setdefault(tgt,[]).append(a)
# coverage rows
cov=[]
with open(os.path.join(BASE,'COVERAGE','coverage.tsv'),encoding='utf-8') as f:
    hdr=f.readline().rstrip('\n').split(',')
    for line in f:
        if not line.strip(): continue
        c=line.rstrip('\n').split('\t')
        cov.append(dict(zip(hdr,c)))
s21=[r for r in cov if r['subsystem']=='S21']
print('coverage rows',len(cov),'S21',len(s21))
from collections import Counter
print('grades',Counter(r['grade'] for r in s21))
# per-row 40-instruction head from exact entry, linear sequential, stop at first ret
head={}
for r in s21:
    e=int(r['entry'],16)
    arr=[]
    a=e
    for _ in range(80):
        v=by_addr.get(a)
        if not v: break
        arr.append(v)
        if v[2].startswith('ret'): break
        a+=v[1]
    head[r['entry']]=arr
summary={'instructions':len(insns),'e8_boundary':e8,'sha256':md5,'text_va':hex(base),'text_vsize':hex(text.Misc_VirtualSize),'coverage_rows':len(cov),'s21_rows':len(s21)}
with open(os.path.join(OUT,'scan_base.json'),'w',encoding='utf-8') as f: json.dump(summary,f,indent=2)
with open(os.path.join(OUT,'direct_calls.json'),'w',encoding='utf-8') as f: json.dump({hex(k):v for k,v in calls.items()},f)
with open(os.path.join(OUT,'s21_head_disasm.txt'),'w',encoding='utf-8') as f:
    for r in s21:
        f.write('\n### '+r['entry']+' '+r['name']+' '+r['grade']+'\n')
        for a,s,m,o,b in head[r['entry']]:
            f.write(f'{a:08X} +{a-int(r["entry"],16):04X} {b:<24} {m} {o}\n')
print('wrote scan_base.json direct_calls.json s21_head_disasm.txt')
