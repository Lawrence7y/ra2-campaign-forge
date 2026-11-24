import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for r in cr:
 e=int(r[0],16)
 if (0x6B6C00<=e<=0x6B8300) or (0x40BE00<=e<=0x40C500):
  print('\t'.join(r))
