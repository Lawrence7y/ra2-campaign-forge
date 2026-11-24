import csv
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03-K2\TARGETS.tsv'
rows={r['entry']:r for r in csv.DictReader(open(p,encoding='utf-8'),delimiter='\t')}
for a in ['004A1DE0','005B4430','00473D10','004A1FB0','00432610','00431B20','00431B80',
          '0065D3A0','0065CA00','00401950','005B4630','004739F0','005B3C20','0047AE10','0065CBF0',
          '0047C620','0052CB90','005B3D00']:
    r=rows.get(a)
    if r:
        sem=r['one_line_semantics'].encode('ascii','replace').decode()
        print(f"{a} grade={r['grade']} name={r['name']} | {sem[:55]}")
    else:
        print(f"{a} NOT-IN-S03-ATLAS")
