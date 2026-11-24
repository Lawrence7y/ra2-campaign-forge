import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for s in secs:
 print(s['nm'],hex(s['va']),hex(s['va']+max(s['vsize'],s['rawsize'])), 'raw',hex(s['raw']),hex(s['rawsize']))
for gva in [0xa8ed84,0xabefdc]:
 rva=gva-IB
 s=next((s for s in secs if s['rva']<=rva<s['rva']+max(s['vsize'],s['rawsize'])),None)
 print('FIND',hex(gva),s)
 if s:
  off=s['raw']+(rva-s['rva'])
  print(' off',hex(off),'rawsize',hex(s['rawsize']),'within raw?',off+32<=s['raw']+s['rawsize'])
  if off+32<=len(DATA):
   print(' bytes',DATA[off:off+32].hex())
