import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
print('targets',len(targets),'vtaddrs',len(vt_by_addr))
cnt=0; samples=[]
for row in targets:
 e=int(row[0],16); s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+asize[e]]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  if insn.id==X86_INS_MOV and len(insn.operands)>=2:
   o0,o1=insn.operands[0],insn.operands[1]
   if o0.type==X86_OP_MEM and (o0.mem.base!=X86_REG_INVALID or o0.mem.index!=X86_REG_INVALID) and o1.type==X86_OP_IMM:
    if (o1.imm&0xffffffff) in vt_by_addr:
     cnt+=1
     if len(samples)<10: samples.append((row[0],hex(insn.address),insn.mnemonic+' '+insn.op_str,hex(o1.imm&0xffffffff)))
print('count occurrences',cnt,'samples',samples)
