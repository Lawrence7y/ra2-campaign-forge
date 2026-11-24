import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for gva in [0x7e9860,0x7e9864,0x7e9868,0x7e986c]:
 v=u32(gva)
 print(hex(gva),'->',hex(v),'VT?' ,v in vt_by_addr, 'COL?',v in cols, 'TD?',v in tds)
 if v in vt_by_addr:
  print('  vt rec',vt_by_addr[v])
