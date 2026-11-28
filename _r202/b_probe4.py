#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B probe4: identify host class for the 3 fallback none sites."""
import sys, struct, bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def s32(v):return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
 s=P.B[sn];n=s['rawsize']//4;return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def it(x):return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
 base,w,n=wv(sn)
 for i in range(n-4):
  if w[i] not in (0,1,2) or w[i+2]!=0:continue
  if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata':continue
  nm=P.cstr(w[i+3]+8,400)
  if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
 base,w,n=wv(sn)
 for i in range(n):
  if it(w[i]) and P.dw(base+4*i-4) in COL:VT[base+4*i]=P.dw(base+4*i-4)
CLS={v:COL[VT[v]]['name'] for v in VT}
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)];INS=[];p=0
while p<len(BUF):
 got=False
 for off,sz,mn,op in md.disasm_lite(BUF[p:p+65536],LO+p):
  got=True;INS.append((off,sz,mn,op));p+=sz
 if not got:p+=1
INS.sort();ADDRS=[a for a,_,_,_ in INS]
def dis_range(a,b):
 i0=bisect.bisect_left(ADDRS,a);i1=bisect.bisect_left(ADDRS,b)
 for x in INS[i0:i1]:print('   %s %s %s'%(hex(x[0]),x[2],x[3]))
import re
def classify_imm(op):
 for tok in re.findall(r'0x[0-9a-fA-F]+',op):
  v=int(tok,16)
  if v in VT:return (hex(v),CLS[v])
 return None
print('=== wider call contexts ===')
for a,b,label in ((0x637f40,0x637fa6,'637fa2'),(0x6382e0,0x63834a,'638346'),(0x6f3e60,0x6f3f88,'6f3f83'),(0x636120,0x636260,'636120'),(0x6370b0,0x637120,'637114-pre')):
 print('\n--- %s %s..%s'%(label,hex(a),hex(b)));dis_range(a,b)
print('\n=== backward VT-immediate scan (up to 400 bytes before each call site) ===')
for c in (0x637fa2,0x638346,0x6f3f83):
 i=bisect.bisect_right(ADDRS,c)-1
 print('\n-- call %s'%hex(c))
 for a,sz,mn,op in INS[max(0,i-140):i]:
  k=classify_imm(op)
  if k:print('   %s %s %s -> %s %s'%(hex(a),mn,op,k[0],k[1]))
print('\n=== forward VT writes on same base reg after call ===')
for c in (0x637fa2,0x638346,0x6f3f83):
 i=bisect.bisect_right(ADDRS,c)-1
 print('\n-- call %s'%hex(c))
 for a,sz,mn,op in INS[i:i+80]:
  k=classify_imm(op)
  if k or ('mov' in mn and ('[' in op)):print('   %s %s %s%s'%(hex(a),mn,op,(' -> '+k[0]+' '+k[1]) if k else ''))
