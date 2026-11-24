import sys,os,re,struct,random
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
CARD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cstr(va):
 if va is None:return None
 for name,vb,vs,pr,rs,ch in pu.sections():
  if vb<=va<vb+min(vs,rs):
   b=pu.read(va,160)
   if not b:return None
   s=b.split(b'\0')[0].strip()
   if len(s)>=3 and sum(32<=c<127 for c in s)>=0.9*len(s): return s.decode('ascii','replace')
 return None
refs=pu.scan_rel32_calls(0x4068E0)
# total direct calls baseline
allcalls=[]
for name,vb,vs,pr,rs,ch in pu.sections():
 if not (ch & 0x20000000): continue
 d=pu.read(vb,rs)
 for i in range(len(d)-4):
  if d[i]==0xE8:
   dest=vb+i+5+struct.unpack_from('<i',d,i+1)[0]
   allcalls.append((vb+i,dest,d))
prefix_pushimm=0; prefix_push8=0; prefix_pushreg=0; strcnt=0; strings=[]
for a,_ in refs:
 b=pu.read(a-5,5)
 if b and len(b)==5 and b[0]==0x68:
  prefix_pushimm+=1
  va=struct.unpack('<I',b[1:5])[0]
  s=cstr(va)
  if s:
   strcnt+=1
   if len(strings)<40: strings.append((a,va,s))
 b2=pu.read(a-2,2)
 if b2 and b2[0]==0x6A: prefix_push8+=1
 b1=pu.read(a-1,1)
 if b1 and 0x50<=b1[0]<=0x57: prefix_pushreg+=1
base=0
for a,dest,d in allcalls:
 off=a-vb if False else None
 # locate section data by address
 for name,vb2,vs2,pr2,rs2,ch2 in pu.sections():
  if vb2<=a<vb2+rs2:
   i=a-vb2
   if i>=5 and d[i-5]==0x68: base+=1
   break
lines=[]
lines.append('S17-K5 0x4068E0 call-site pattern')
lines.append('direct E8 callers='+str(len(refs)))
lines.append('immediately preceded by push imm32 (68)=%d (%.2f%%)'%(prefix_pushimm,100*prefix_pushimm/len(refs)))
lines.append('immediately preceded by push imm8 (6A)=%d'%prefix_push8)
lines.append('immediately preceded by push reg (50-57)=%d'%prefix_pushreg)
lines.append('push imm32 resolving to printable C string=%d'%strcnt)
lines.append('baseline all direct E8 call sites='+str(len(allcalls))+' preceded by push imm32='+str(base)+' (%.2f%%)'%(100*base/len(allcalls)))
lines.append('first 40 string-push call sites:')
for a,va,s in strings: lines.append(f'  0x{a:X}: push 0x{va:X} -> {s!r}')
lines.append('body bytes at 0x4068E0 = '+repr(pu.read(0x4068E0,1))+' (single instruction ret; entry==exit)')
txt='\n'.join(lines)+'\n'
open(CARD+r'\EVIDENCE\4068e0_callsite_pattern.txt','w',encoding='utf-8').write(txt)
print(txt)
