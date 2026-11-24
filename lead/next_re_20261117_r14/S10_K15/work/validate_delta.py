import os,csv
base=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15"
rows=list(csv.reader(open(os.path.join(base,'coverage_delta.tsv'),'r',encoding='utf-8',newline=''),delimiter='\t'))
assert all(len(r)==9 for r in rows), [len(r) for r in rows]
assert len({r[0] for r in rows})==len(rows),'entry dup'
assert len({r[2] for r in rows})==len(rows),'name dup'
assert all(r[8] in ('symbolic','behavioral','placeholder') for r in rows),'bad kind'
assert all(r[8]!='placeholder' for r in rows),'placeholder'
assert all(r[4] in ('[已证]','[静态推断]','[未证]') for r in rows),'bad grade'
for r in rows:
 p,anchor=r[5].split('#',1); fp=os.path.join(base,p)
 assert os.path.exists(fp),fp
 txt=open(fp,'r',encoding='utf-8').read()
 assert anchor in txt, (fp,anchor)
print('PASS rows',len(rows),'cols',set(len(r) for r in rows),'entries',[r[0] for r in rows],'kinds',[r[8] for r in rows])
