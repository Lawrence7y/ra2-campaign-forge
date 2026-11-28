# -*- coding: utf-8 -*-
"""R216 m3：①slot0 QI 的 4 个 IID（0x7f7c90/80/70, 0x7e9ae0）字节与引用者；
②mdisp=4/8/12 三张视图共 8 个槽目标函数体；③0x410210/20/30 是否为 adjustor thunk。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
def o(va): return P.r2o(va)
def g32(va): return P.dw(va)
def dump(va,maxb=160):
    print('--- 0x%08x ---'%va)
    nb=0
    for i in mdl.disasm(P.RAW[o(va):o(va)+maxb],va):
        print('  %08x  %-8s %s'%(i.address,i.mnemonic,i.op_str)); nb+=i.size
        if i.mnemonic.startswith('ret') or (i.mnemonic=='jmp'): break
    print('  raw=%s'%P.RAW[o(va):o(va)+nb].hex())
print('=== IID 字节（4 dword 小端）===')
G={}
for a in (0x7f7c90,0x7f7c80,0x7f7c70,0x7e9ae0):
    b=P.RAW[o(a):o(a)+16]
    G[a]=b
    print('  0x%08x = %s'%(a,b.hex()))
    print('     dwords=%s'%' '.join('0x%08x'%g32(a+4*k) for k in range(4)))
    print('     hex=%08X-%04X-%04X-%s-%s'%(*struct.unpack('<IHH',b[:8]),b[8:10].hex().upper(),b[10:16].hex().upper()))
print('=== 8 个次级视图槽目标 ===')
for va in (0x4105e0,0x4105f0,0x410600,0x410210,0x410220,0x410230,0x410580,0x410590):
    dump(va)
# ---- 全 .text 引用了这 4 个 IID 地址的站点（push imm32 = 68 xx xx xx xx）----
t=P.B['.text']; tb=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]; base=t['lo']
print('=== 4 个 IID 地址在 .text 中被 push/lea 引用 ===')
hits=collections.defaultdict(list)
for k in range(len(tb)-5):
    if tb[k]==0x68:
        v=struct.unpack_from('<I',tb,k+1)[0]
        if v in G: hits[v].append((base+k,0x68))
    elif tb[k]==0xb8 and k+5<=len(tb):
        v=struct.unpack_from('<I',tb,k+1)[0]
        if v in G: hits[v].append((base+k,0xb8))
    elif tb[k]==0x8d and k+6<=len(tb) and (tb[k+1]&0xc7)==0x05:
        v=struct.unpack_from('<I',tb,k+2)[0]
        if v in G: hits[v].append((base+k,0x8d))
for a in G:
    print('  0x%08x 引用 %d 处: %s'%(a,len(hits[a]),' '.join('0x%08x(%02x)'%(x,m) for x,m in hits[a][:20])))
json.dump({'iids':{'0x%08x'%a:G[a].hex() for a in G},
  'iid_refs':{'0x%08x'%a:['0x%08x'%x for x,m in hits[a]] for a in G}},
  open('/home/t628/projects/ra2-campaign-forge/_r216/m3.json','w'),indent=1)
