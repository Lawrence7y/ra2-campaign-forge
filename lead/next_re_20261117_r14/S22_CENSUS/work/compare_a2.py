import sys, struct, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
a2set=set()
for row in targets:
 e=int(row[0],16)
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+asize[e]]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  if insn.id==X86_INS_MOV and len(insn.operands)>=2:
   o0,o1=insn.operands[0],insn.operands[1]
   if o0.type==X86_OP_MEM and (o0.mem.base!=X86_REG_INVALID or o0.mem.index!=X86_REG_INVALID) and o1.type==X86_OP_IMM:
    if (o1.imm&0xffffffff) in vt_by_addr: a2set.add(row[0].upper())
final=set()
p=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/EVIDENCE/channel_hits.tsv'
lines=open(p,encoding='utf-8').read().splitlines(); hdr=lines[0].split('\t'); i=hdr.index('all_a2')
for l in lines[1:]:
 f=l.split('\t')
 if f[i]: final.add(f[0])
print('explore A2',len(a2set),'final A2',len(final),'explore-only',len(a2set-final),'final-only',len(final-a2set))
print('explore-only sample',sorted(a2set-final)[:20])
print('final-only sample',sorted(final-a2set)[:20])
