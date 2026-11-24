import sys, os, struct, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
# recompute edge examples with full instruction context
sem=[]; immhits=[]; rawhits=[]
for row in targets:
 e=int(row[0],16); sz=asize[e]
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+sz]
 ins=list(md.disasm(body,e))
 regvt=collections.defaultdict(set)
 for j,insn in enumerate(ins):
  if insn.id==0: continue
  if insn.id==X86_INS_MOV and len(insn.operands)>=2:
   dst,src=insn.operands[0],insn.operands[1]
   if dst.type==X86_OP_MEM and src.type==X86_OP_REG:
    vals=regvt.get(src.reg,set())
    for v in sorted(vals): sem.append((e,j,insn.address,insn.mnemonic+' '+insn.op_str,v,[x.mnemonic+' '+x.op_str for x in ins[max(0,j-4):j+2] if x.id!=0]))
  if insn.id==X86_INS_MOV and len(insn.operands)>=2:
   dst,src=insn.operands[0],insn.operands[1]
   if dst.type==X86_OP_REG:
    if src.type==X86_OP_IMM and (src.imm&0xffffffff) in vt_by_addr: regvt[dst.reg]={(src.imm&0xffffffff)}
    elif src.type==X86_OP_MEM and (src.mem.disp&0xffffffff) in vt_by_addr: regvt[dst.reg]={(src.mem.disp&0xffffffff)}
    elif src.type==X86_OP_REG: regvt[dst.reg]=set(regvt.get(src.reg,set()))
    else: regvt.pop(dst.reg,None)
  writes=set(insn.regs_write)
  for reg in writes:
   if insn.id==X86_INS_MOV and len(insn.operands)>=2 and insn.operands[0].type==X86_OP_REG and insn.operands[0].reg==reg: continue
   regvt.pop(reg,None)
  for op in insn.operands:
   if op.type==X86_OP_IMM and (op.imm&0xffffffff) in coltd:
    immhits.append((e,insn.address,insn.mnemonic+' '+insn.op_str,op.imm&0xffffffff,'COL' if (op.imm&0xffffffff) in cols else 'TD'))
 for i in range(0,max(0,len(body)-3),4):
  v=struct.unpack_from('<I',body,i)[0]
  if v in coltd: rawhits.append((e,e+i,v,'COL' if v in cols else 'TD'))
print('SEMANTIC A2 HITS',len(sem))
for x in sem[:60]: print(f'{x[0]:08X} j={x[1]} @{x[2]:08X} {x[3]:<42} vt={x[4]:08X} | ' + ' ; '.join(x[5]))
print('\nA3 IMMEDIATE HITS',len(immhits))
for x in immhits: print(f'{x[0]:08X} @{x[1]:08X} {x[2]:<42} {x[3]:08X} {x[4]}')
print('\nA3 RAW HITS',len(rawhits))
for x in rawhits: print(f'{x[0]:08X} @{x[1]:08X} {x[2]:08X} {x[3]}')
