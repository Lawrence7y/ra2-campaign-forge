import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for e in [0x6B6C90,0x6B6EA0]:
 print('==== %08X size %d ===='%(e,asize[e]))
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+asize[e]]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  txt=insn.mnemonic+' '+insn.op_str
  hit=[]
  for op in insn.operands:
   if op.type==X86_OP_IMM:
    v=op.imm&0xffffffff
    if v in vt_by_addr: hit.append('VT')
    if v in cols: hit.append('COL')
    if v in tds: hit.append('TD')
  if ('0x7f36' in txt.lower()) or hit or insn.id==X86_INS_MOV and len(insn.operands)>=2 and insn.operands[0].type==X86_OP_MEM:
   print(' ',hex(insn.address),txt,hit)
