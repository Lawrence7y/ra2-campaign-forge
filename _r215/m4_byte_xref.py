# -*- coding: utf-8 -*-
"""R215 m4：+0x48 的字节级口径复核（对照 m3 的 lite 线性扫描）——
byte 模式 FF <modrm> 48，modrm=0x50|rm 为 call /2（mod=01），0x60|rm 为 jmp /4。
同时给出对齐性自检：命中位点必须能由 capstone 从该地址解出且 disp==0x48。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
raw=P.RAW; t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
RM={0:'eax',1:'ecx',2:'edx',3:'ebx',5:'ebp',6:'esi',7:'edi'}
res={'call':[], 'jmp':[]}
i=o0; end=o0+n-2
while i<end:
    if raw[i]==0xff:
        m=raw[i+1]
        mod=m>>6; reg=(m>>3)&7; rm=m&7
        if mod==1 and raw[i+2]==0x48 and rm in RM:
            if reg==2: res['call'].append((tb+(i-o0),RM[rm]))
            elif reg==4: res['jmp'].append((tb+(i-o0),RM[rm]))
    i+=1
print('byte 口径: call [reg+0x48]=%d  jmp [reg+0x48]=%d'%(len(res['call']),len(res['jmp'])))
print('call 按寄存器:',collections.Counter(r for _,r in res['call']).most_common())
print('jmp  按寄存器:',collections.Counter(r for _,r in res['jmp']).most_common())
ok=bad=0; badlst=[]
for kind in ('call','jmp'):
    for a,r in res[kind]:
        o=P.r2o(a); d=list(md.disasm(raw[o:o+3],a,count=1))
        if d and d[0].mnemonic==kind and d[0].operands[0].type==capstone.x86.X86_OP_MEM and d[0].operands[0].mem.disp==0x48: ok+=1
        else: bad+=1; badlst.append((hex(a),kind,r))
print('capstone 单条复核 成立=%d 不成立=%d'%(ok,bad))
print('不成立样例:',badlst[:10])
# 与 m3 lite 结果比对
m3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r215/m3.json'))
s3=set(int(a,16) for a,op in m3['hits'])
s4=set(a for a,r in res['call'])|set(a for a,r in res['jmp'])
print('lite∩byte=%d  lite-only=%d  byte-only=%d'%(len(s3&s4),len(s3-s4),len(s4-s3)))
print('byte-only 样例:',[hex(x) for x in sorted(s4-s3)[:10]])
print('lite-only 样例:',[hex(x) for x in sorted(s3-s4)[:10]])
# 每个 +0x48 位点是否在 27 个 slot18 目标的函数体内？—— 用已知简单上界：距目标 <256B 且向后
json.dump({'byte_call':len(res['call']),'byte_jmp':len(res['jmp']),
  'byreg_call':collections.Counter(r for _,r in res['call']).most_common(),
  'byreg_jmp':collections.Counter(r for _,r in res['jmp']).most_common(),
  'capstone_ok':ok,'capstone_bad':bad,
  'call_addrs':[hex(a) for a,_ in res['call']],'jmp_addrs':[hex(a) for a,_ in res['jmp']],
  'lite_vs_byte':{'inter':len(s3&s4),'lite_only':len(s3-s4),'byte_only':len(s4-s3),
                  'byte_only_addrs':[hex(x) for x in sorted(s4-s3)],
                  'lite_only_addrs':[hex(x) for x in sorted(s3-s4)]}},
  open('/home/t628/projects/ra2-campaign-forge/_r215/m4.json','w'),indent=1)
