import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for gva in [0x7E9860,0x7E9864,0xB0B884,0xA8ED84]:
 print('GLOBAL',hex(gva))
 rva=gva-IB; ss=next((ss for ss in secs if ss['rva']<=rva<ss['rva']+max(ss['vsize'],ss['rawsize'])),None)
 if not ss: print(' no section'); continue
 print(' section',ss['nm'],'vsize',hex(ss['vsize']),'rawsize',hex(ss['rawsize']))
 off=ss['raw']+(rva-ss['rva'])
 print(' off',hex(off),'in raw?',off+4<=ss['raw']+ss['rawsize'])
 if off+4<=len(DATA):
  v=struct.unpack_from('<I',DATA,off)[0]
  print(' bytes',DATA[off:off+4].hex(),'value',hex(v),'VT?',v in vt_by_addr)
  if v in vt_by_addr: print('  class',vt_by_addr[v]['cls'])
