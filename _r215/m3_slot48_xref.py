# -*- coding: utf-8 -*-
"""R215 m3：【指令级】虚槽 +0x48 的调用点普查（区分 call/jmp、寄存器、以及是否 SIB）。
纯字节扫描（不反汇编全段），命中后 capstone 单条复核。
同时给出『+0x48 是第几热门的 disp8 虚槽』——用于判断 +0x48 是否是特殊槽。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P, capstone
raw=P.RAW; t=P.B['.text']; tb=t['lo']; n=t['rawsize']; o0=t['rawptr']
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dis(a,k=1):
    o=P.r2o(a)
    return [(x.address,x.bytes.hex(),x.mnemonic,x.op_str) for x in md.disasm(raw[o:o+32],a,count=k)]
target=0x48
call_hits=[]
jmp_hits=[]
CH=0x10000
for base in range(o0,o0+n,CH):
    chunk=raw[base:min(base+CH,o0+n)]
    va=tb+(base-o0)
    for ins in md.disasm_lite(chunk,va):
        a,sz,mn,op=ins
        if mn not in ('call','jmp'): continue
        if not op.endswith('+ 0x48]'): continue
        # 只要内存操作数为唯一操作数（间接 call/jmp）
        if ',' in op.split('[')[0]: continue
        (call_hits if mn=='call' else jmp_hits).append((a,op,sz))
print('call [reg+0x48] 命中=%d  jmp [reg+0x48] 命中=%d'%(len(call_hits),len(jmp_hits)))
byreg=collections.Counter()
for a,op,sz in call_hits+jmp_hits:
    reg=op.split('[')[1].split(' ')[0]
    byreg[reg]+=1
print('按基址寄存器:',byreg.most_common())
# 逐条 capstone detail 复核 + 取 disp 确认
ok=0; bad=0
for a,op,sz in call_hits+jmp_hits:
    o=P.r2o(a)
    d=list(md.disasm(raw[o:o+sz],a,count=1))
    if d and d[0].operands and d[0].operands[0].type==capstone.x86.X86_OP_MEM and d[0].operands[0].mem.disp==0x48: ok+=1
    else: bad+=1
print('detail 复核 disp==0x48 成立=%d 不成立=%d'%(ok,bad))
# 全 disp8 虚槽热度：对全部 call/jmp [reg+disp8] 统计 disp 分布
disp_hist=collections.Counter()
allvirt=0
for base in range(o0,o0+n,CH):
    chunk=raw[base:min(base+CH,o0+n)]
    va=tb+(base-o0)
    for ins in md.disasm_lite(chunk,va):
        a,sz,mn,op=ins
        if mn not in ('call','jmp'): continue
        if '[' not in op or ']' not in op: continue
        inner=op.split('[')[1].split(']')[0]
        if '+' not in inner or 'esp' in inner or 'ebp' in inner: continue
        try: dv=int(inner.split('+')[1].strip(),16)
        except Exception: continue
        if dv>0x400: continue
        disp_hist[dv]+=1; allvirt+=1
print('全段间接 call/jmp [reg+disp8<=0x400] 总数=%d distinct disp=%d'%(allvirt,len(disp_hist)))
print('disp 热度 top15:',[(hex(k),v) for k,v in disp_hist.most_common(15)])
print('disp=0x48 热度排名=%d 次数=%d'%(
    [k for k,_ in disp_hist.most_common()].index(0x48)+1, disp_hist.get(0x48,0)))
# 27 个 slot18 目标是否被 call [reg+0x48] 之外的直接 call 引用
print('--- +0x48 命中位点（前 40） ---')
for a,op,sz in (call_hits+jmp_hits)[:40]: print(' %08x %-22s'%(a,op))
json.dump({'call48':len(call_hits),'jmp48':len(jmp_hits),'byreg':byreg.most_common(),
 'detail_ok':ok,'detail_bad':bad,'virt_total':allvirt,
 'disp_top':[(hex(k),v) for k,v in disp_hist.most_common(20)],
 'rank48':[k for k,_ in disp_hist.most_common()].index(0x48)+1,
 'hits':[[hex(a),op] for a,op,sz in call_hits+jmp_hits]},
 open('/home/t628/projects/ra2-campaign-forge/_r215/m3.json','w'),indent=1)
