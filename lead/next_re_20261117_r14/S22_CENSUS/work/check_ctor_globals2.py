import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for gva in [0xa8ed84,0xabefdc,0xabefe8]:
 print('GLOBAL',hex(gva))
 for i in range(8):
  va=gva+4*i
  try:
   v=u32(va)
  except Exception as e:
   print(' ',hex(va),'ERR',e); continue
  print(' ',hex(va),'=',hex(v),'VT',v in vt_by_addr,'COL',v in cols,'TD',v in tds)
  if v in vt_by_addr: print('  ',vt_by_addr[v]['cls'],'col',hex(vt_by_addr[v]['col']),'td',hex(vt_by_addr[v]['td']))
