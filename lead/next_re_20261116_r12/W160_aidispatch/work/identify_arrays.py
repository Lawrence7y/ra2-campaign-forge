import csv, json, os, re
R=r"D:\Project\ra2-campaign-forge"
arrp=os.path.join(R,"lead","next_re_20261112_r10","W132_arrays","instance_arrays.tsv")
rows=list(csv.DictReader(open(arrp,encoding='utf-8'),delimiter='\t'))
targets=['0x0087F778','0x0087F77C','0x0087F780','0x0087F784','0x0087F788','0x0087F78C','0x008A020C','0x008A0218','0x00B04BD4','0x00B04BE0','0x00A83E04','0x00A83E10','0x00A83E34','0x00A83E40','0x00A8022C','0x00A80238','0x00887324','0x008B40F8','0x008B40CC','0x008B40D8','0x00A8B230']
for t in targets:
    hits=[r for r in rows if t.lower() in (r['base'].lower(),r['items'].lower(),r['count'].lower(),r['vftable'].lower())]
    print(f"\n{t}: {len(hits)}")
    for h in hits: print('  ',h)
# also show all rows with 'Team' 'DiskLaser' 'RadSite' 'Logic' in element
for kw in ['Team','DiskLaser','Rad','Logic','ObjectClass','Abstract','Tag','Trigger','Factory','House']:
    hs=[(r['element'],r['base'],r['items'],r['count'],r['vftable'],r['col']) for r in rows if kw.lower() in r['element'].lower()]
    print(f"\n[{kw}] {len(hs)}:")
    for h in hs[:15]: print('  ',h)
