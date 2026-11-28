# -*- coding: utf-8 -*-
"""R218 m20：把 931 个 s>=256 消费位点按「槽序号能落在哪张表」归并，并刻画 .data 16 字节记录结构。
正控：s=11 (disp 0x2c) 位点应 1114（m19 同口径）。
"""
import sys,collections,struct
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; lo=t['lo']; raw=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
pos=0;cands=[]
while pos<len(raw):
    got=False
    for a,sz,mn,ops in mdl.disasm_lite(raw[pos:pos+64],lo+pos):
        got=True
        if mn in ('call','jmp'):
            s=ops.strip()
            if s.startswith('dword ptr ['):
                inner=s[s.index('[')+1:s.rindex(']')]
                if '*' not in inner:
                    parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                    if parts and len(parts)<=2 and parts[0] in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'):
                        d=0;ok=True
                        if len(parts)==2:
                            try: d=int(parts[1],0)
                            except: ok=False
                        if ok and parts[0]!='esp': cands.append((a,mn,inner,d))
        pos+=sz; break
    if not got: pos+=1
hi=[c for c in cands if c[3]>=0x400]
print('[正控] s=11 位点 %d（应 1114）'%sum(1 for c in cands if c[3]==0x2c))
print('[s>=256] %d  不同 s=%d'%(len(hi),len(set(c[3]//4 for c in hi))))
cnt=collections.Counter(c[3]//4 for c in hi)
SLOTMAX=[(344,'UnitClass'),(343,'InfantryClass'),(341,'Aircraft/Foot'),(322,'Building'),(309,'Techno'),(161,'Radio')]
def owner(s):
    for n,nm in SLOTMAX:
        if s<n: return nm+'(max%d)'%n
    return '超出最大槽数'
print('[top s 与所属表]')
for s,n in cnt.most_common(14):
    addrs=[hex(a) for a,_,_,d in hi if d//4==s][:5]
    print('   s=%3d disp=%05x n=%3d  %-24s 位点 %s'%(s,s*4,n,owner(s),addrs))
print('[按所属表汇总]')
for k,v in collections.Counter(owner(c[3]//4) for c in hi).most_common(): print('   %-24s %4d'%(k,v))
print('\n[.data 16B 记录刻画]')
for a in (0x876ff0,0x877000,0x877010,0x877020,0x87b170,0x87b17c,0x87b18c,0x87b19c):
    o=P.r2o(a); print('   %08x %s'%(a,P.RAW[o:o+32].hex()))
da=P.B['.data']; draw=P.RAW[da['rawptr']:da['rawptr']+da['rawsize']]
pat=struct.pack('<I',0x800040); offs=[]; s0=0
while True:
    i=draw.find(pat,s0)
    if i<0: break
    offs.append(da['lo']+i); s0=i+1
print('   .data 内 COL 0x800040 出现 %d 处 %s'%(len(offs),[hex(x) for x in offs]))
