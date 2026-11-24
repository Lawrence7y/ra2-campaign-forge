import csv, os
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
COV=os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
OUT=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','work','lookup.txt')
rows={r['entry'].upper():r for r in csv.DictReader(open(COV,encoding='utf-8',errors='replace'),delimiter='\t')}
want=['0043B740','007353C0','00517A50','00413D20','0044FAF8','00449E16','004430C2','0041B1B4',
      '005F3900','006F2B40','004D31E0','004105A0','007014A0','005F4D30','005F4EC0',
      '004A9720','004A9770','0054BFF0','005F8110','005F4D30']
with open(OUT,'w',encoding='utf-8') as o:
    for w in want:
        r=rows.get(w)
        if r: o.write('%s\t%s\t%s\t%s\t%s\n'%(w,r['subsystem'],r['name'],r['grade'],r['one_line_semantics']))
        else: o.write('%s\tNOT-IN-COVERAGE\n'%w)
print('wrote',OUT)
