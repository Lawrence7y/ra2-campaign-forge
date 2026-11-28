#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B probe5: classify secondary VT constants near fallback call sites."""
import sys,struct,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
for v in (0x7eff04,0x7eff24,0x7efe44,0x7efe64,0x7f4108,0x7f4134,0x7f4154,0x7f79bc,0x7f7a3c,0x7ee184,0x7ee424,0x7ee50c,0x7ee5f4,0x7ee6fc,0x7ee814):
 print('%s md=%d %s'%(hex(v),COL[VT[v]]['mdisp'],COL[VT[v]]['name']) if v in VT else '%s NOT-VT'%hex(v))
