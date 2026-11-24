
p=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S10_K8F/coverage_delta.tsv'
b=open(p,'rb').read()
for line in b.splitlines():
 f=line.split(b'\t')
 if f and f[0] in (b'004DFCB0',b'004DFE00'):
  print('ADDR',f[0].decode())
  print(' name bytes',f[2])
  print(' grade bytes',f[4])
  print(' grade utf8',f[4].decode('utf-8'))
  print(' nfields',len(f))
