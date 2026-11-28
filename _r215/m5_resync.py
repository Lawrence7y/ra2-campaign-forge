# -*- coding: utf-8 -*-
"""R215 m5：m4 byte-only 命中的对齐性判定（局部重同步测试）。
判定规则：对命中地址 A，在 [A-15, A-1] 的每个起点 S 做 capstone 顺序反汇编（最多 16 条、且不越过 A+4），
若存在某个 S 使 A 恰为某条指令的起始地址，则 A 记为 aligned=True（可被某条路径解出），否则 misaligned。
只为区分『字节模式上界』与『线性反汇编可达数』，不作语义推断。
"""
import sys,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
raw=P.RAW
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def aligned(A):
    o=P.r2o(A)
    if o is None: return False
    for back in range(1,16):
        S=A-back; os_=P.r2o(S)
        if os_ is None: continue
        for ins in md.disasm(raw[os_:os_+40],S):
            if ins.address==A: return True
            if ins.address>A: break
            if ins.address+ins.size>S+40: break
    return False
m4=json.load(open('/home/t628/projects/ra2-campaign-forge/_r215/m4.json'))
byte_only=m4['lite_vs_byte']['byte_only_addrs']
lite_only=m4['lite_vs_byte']['lite_only_addrs']
al=[]; mis=[]
for h in byte_only:
    (al if aligned(int(h,16)) else mis).append(h)
print('byte-only %d 中 局部可对齐=%d 判为错位=%d'%(len(byte_only),len(al),len(mis)))
print('判为错位样例:',mis[:12])
for h in lite_only:
    print('lite-only %s 局部可对齐=%s'%(h,aligned(int(h,16))))
# 复核：lite 命中的 765 是否全部局部可对齐（正控）
m3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r215/m3.json'))
bad=0
for a,op in m3['hits']:
    if not aligned(int(a,16)): bad+=1
print('正控：m3 的 %d 条 lite 命中里局部不可对齐=%d'%(len(m3['hits']),bad))
tot=765+len(al)
print('结论：+0x48 间接 call/jmp 的可靠下界=%d 上界=%d'%(765,tot))
json.dump({'byte_only':len(byte_only),'aligned':len(al),'misaligned':len(mis),
  'misaligned_list':mis,'aligned_list':al,'lite_only':lite_only,
  'lower_bound':765,'upper_bound_byte':m4['byte_call']+m4['byte_jmp'],
  'aligned_total':765+len(al),'lite_unaligned':bad},
  open('/home/t628/projects/ra2-campaign-forge/_r215/m5.json','w'),indent=1)
