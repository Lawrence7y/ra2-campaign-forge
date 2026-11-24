"""S11-K2 T5: regenerate TARGETS.tsv from CURRENT coverage.tsv (S11 rows only)."""
import csv
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\TARGETS.tsv'
UPGRADED={'004B4CF0','004B66E0','004D0390','005172B0','0054DF90','005B1B40','006635B0','006A42A0','0071A120','0072A200','0075CBD0','004AF540','004B5AB0'}
rows=[]
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['subsystem']=='S11': rows.append(r)
print('S11 rows =',len(rows))
with open(OUT,'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','现name','现grade','缺什么','取证计划'])
    for r in sorted(rows,key=lambda z:z['entry']):
        e=r['entry'].upper(); g=r['grade']
        if e in UPGRADED:
            miss='本卡已补齐字节硬证'; plan='已交 coverage_delta.tsv（GetSize 双向闭合 / ctor vtable-install+factory-call）'
        elif g=='[已证]':
            miss='已证（本卡复核是否可加固）'; plan='RTTI/GetSize/vtable 再核'
        elif g=='[静态推断]':
            miss='缺字节级硬证（入口/语义仅静态推断）'; plan='查 off4/off0 vtable 槽位+B8/C3 或构造器分配点'
        else:
            miss='缺入口字节证据+语义'; plan='查是否 vtable 槽直指/构造器调用点/字段双支撑'
        w.writerow([r['entry'],r['name'],g,miss,plan])
print('wrote',OUT)
