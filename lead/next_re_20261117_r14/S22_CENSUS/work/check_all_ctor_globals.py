import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
# global dword load addresses in strict-A2 rows: read VA as pointer from file-independent virtual .data if raw unavailable not possible; inspect via bytes at file offset if raw
seen=set(); rows=[]
for row in targets:
 e=int(row[0],16); siz=asize[e]
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+siz]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  if insn.mnemonic=='mov' and len(insn.operands)>=2 and insn.operands[0].type==X86_OP_REG and insn.operands[1].type==X86_OP_MEM:
   g=insn.operands[1].mem.disp & 0xffffffff
   if g and (g,0) not in seen:
    seen.add((g,0))
    rva=g-IB; ss=next((ss for ss in secs if ss['rva']<=rva<ss['rva']+max(ss['vsize'],ss['rawsize'])),None)
    if not ss: continue
    roff=ss['raw']+(rva-ss['rva'])
    if roff+4>ss['raw']+ss['rawsize'] or roff+4>len(DATA): continue
    v=struct.unpack_from('<I',DATA,roff)[0]
    if v in vt_by_addr:
     rows.append((e,insn.address,g,v,vt_by_addr[v]['cls'],vt_by_addr[v]['col'],vt_by_addr[v]['td']))
print('global-to-vt loads',len(rows))
for x in rows[:100]: print('%08X @%08X [%08X]=%08X -> %s col=%08X td=%08X'%x)
