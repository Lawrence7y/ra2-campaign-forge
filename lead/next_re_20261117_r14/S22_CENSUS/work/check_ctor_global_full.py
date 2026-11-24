import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for e in [0x6B6EA0,0x6B6FA0]:
 print('====',hex(e))
 s=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
 off=s['raw']+(e-IB); body=DATA[off:off+asize[e]]
 for insn in md.disasm(body,e):
  if insn.id==0: continue
  txt=insn.mnemonic+' '+insn.op_str
  if 'dword ptr [' in txt or 'mov ' in txt:
   print(' ',hex(insn.address),txt)
