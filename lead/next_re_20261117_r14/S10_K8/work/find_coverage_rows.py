import io
p=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
keys=['004DF320','004DF3A0','004DFA70','00521760','006F4960','004DFB70','004DFCB0','004DFE00','006B6EA0','006B6FA0','006B6C90','006B7F10','004E0E80','006B7010']
for line in io.open(p,'r',encoding='utf-8',errors='replace'):
 f=line.rstrip('\n').split('\t')
 if f and f[0].upper() in keys: print(f[0],'S=',f[1],'grade=',f[4],'name=',f[2])
