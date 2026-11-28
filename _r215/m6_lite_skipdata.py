# -*- coding: utf-8 -*-
"""R215 m6：解释 m3(765) 与 m4(928) 差额的真实原因。
假设：md.disasm_lite 未开 skipdata，遇到不可解码字节即停，导致每个 64KB 块只解出前缀。
检验：①统计各块被解出的字节覆盖比例；②开 skipdata=True 重跑；③补 SIB 形式的 byte 扫描。
"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
raw=P.RAW; t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']
CH=0x10000
def lite(skip):
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    if skip: md.skipdata=True
    hits=[]; cover=[]
    for base in range(o0,o0+n,CH):
        chunk=raw[base:min(base+CH,o0+n)]
        va=tb+(base-o0); last=0; cnt=0
        for ins in md.disasm_lite(chunk,va):
            a,sz,mn,op=ins; cnt+=1; last=(a-va)+sz
            if mn in ('call','jmp') and op.endswith('+ 0x48]') and ',' not in op.split('[')[0]:
                hits.append((a,op))
        cover.append((va,len(chunk),last,cnt))
    return hits,cover
h0,c0=lite(False); h1,c1=lite(True)
trunc=[x for x in c0 if x[2]<x[1]]
print('no-skipdata: hits=%d 块数=%d 被截断块=%d 覆盖率=%.1f%%'%(
    len(h0),len(c0),len(trunc),100.0*sum(x[2] for x in c0)/sum(x[1] for x in c0)))
print('skipdata  : hits=%d 覆盖率=%.1f%%'%(len(h1),100.0*sum(x[2] for x in c1)/sum(x[1] for x in c1)))
print('截断块样例:',[(hex(a),'got%d/%d'%(l,ln)) for a,ln,l,_ in trunc[:5]])
# SIB 形式 byte 扫描：FF <modrm reg=2/4 mod=01 rm=4> <SIB> <disp8=0x48>
sib=[]
i=o0; end=o0+n-4
while i<end:
    if raw[i]==0xff:
        m=raw[i+1]; mod=m>>6; reg=(m>>3)&7; rm=m&7
        if mod==1 and rm==4 and raw[i+3]==0x48 and reg in (2,4):
            sib.append((tb+(i-o0),'call' if reg==2 else 'jmp',raw[i+2]))
    i+=1
print('SIB 形式 (FF /2|/4, mod=01, rm=100, disp8=0x48) 命中=%d'%len(sib))
print('SIB 的 sib 字节分布:',collections.Counter(hex(s) for _,_,s in sib).most_common())
names={0x24:'[esp+0x48] (栈)',0x44:'[esp+eax*2..]'}
print('SIB 实例:',[(hex(a),k,hex(s)) for a,k,s in sib[:10]])
s1=set(a for a,_ in h1)
m4=json.load(open('/home/t628/projects/ra2-campaign-forge/_r215/m4.json'))
s4=set(int(x,16) for x in m4['call_addrs'])|set(int(x,16) for x in m4['jmp_addrs'])
print('skipdata ∩ byte(non-SIB) = %d ; skipdata-only=%d ; byte-only=%d'%(
    len(s1&s4),len(s1-s4),len(s4-s1)))
print('skipdata-only:',[hex(x) for x in sorted(s1-s4)][:10])
print('byte-only:',[hex(x) for x in sorted(s4-s1)][:10])
json.dump({'noskip_hits':len(h0),'skip_hits':len(h1),
  'trunc_blocks':len(trunc),'cover_noskip':sum(x[2] for x in c0)/sum(x[1] for x in c0),
  'cover_skip':sum(x[2] for x in c1)/sum(x[1] for x in c1),
  'sib':[[hex(a),k,hex(s)] for a,k,s in sib],
  'inter_skip_byte':len(s1&s4),'skip_only':[hex(x) for x in sorted(s1-s4)],
  'byte_only':[hex(x) for x in sorted(s4-s1)],
  'skip_addrs':[hex(a) for a,_ in h1]},
  open('/home/t628/projects/ra2-campaign-forge/_r215/m6.json','w'),indent=1)
