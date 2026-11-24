import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for e in [0x6B7F10,0x6B8120,0x49B94A,0x533FD0,0x710AF0,0x6E6540,0x724CD0,0x6263D0]:
 print('==== %08X ===='%e)
 if e in slot_to_members:
  for m in slot_to_members[e]: print(' A1',m)
 else: print(' A1 none')
 if e not in asize: print(' not in atlas'); continue
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); sz=asize[e]; body=DATA[off:off+sz]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  txt=insn.mnemonic+' '+insn.op_str
  hit=[]
  for op in insn.operands:
   if op.type==X86_OP_IMM:
    v=op.imm&0xffffffff
    if v in coltd: hit.append(('imm',v,'COL' if v in cols else 'TD'))
   elif op.type==X86_OP_MEM and op.mem.disp:
    v=op.mem.disp&0xffffffff
    if v in coltd: hit.append(('disp',v,'COL' if v in cols else 'TD'))
  if insn.id==X86_INS_MOV and len(insn.operands)>=2:
   op0,op1=insn.operands[0],insn.operands[1]
   if op0.type==X86_OP_MEM and op1.type==X86_OP_IMM and (op1.imm&0xffffffff) in vt_by_addr:
    hit.append(('movVT',op1.imm&0xffffffff,'VT'))
  if hit: print(' ',hex(insn.address),txt,hit)
