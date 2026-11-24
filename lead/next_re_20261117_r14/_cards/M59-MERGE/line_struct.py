# -*- coding: utf-8 -*-
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md'
d=open(p,'r',encoding='utf-8',newline='').read()
L=d.split('\n')[:-1]
out=[]
for n in (69,70,77,119,120,183,184,503):
    line=L[n-1]
    out.append("=== L%d length=%d lastpipe=%d ===" % (n,len(line),line.rfind('|')))
    out.append("HEAD: "+repr(line[:60]))
    out.append("TAIL: "+repr(line[-60:]))
    out.append("SPLIT(|' | ')=%d parts, first=%r, last=%r" % (len(line.split(' | ')),line.split(' | ')[0],line.split(' | ')[-1]))
open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_cards\M59-MERGE\LINESTRUCT.txt','w',encoding='utf-8').write('\n'.join(out))
print('ok')
