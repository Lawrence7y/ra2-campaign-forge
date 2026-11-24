# -*- coding: utf-8 -*-
"""交付自校验：M1 delta行数=自报; M2 ②类=name类; M5 偏移同源; M8 无自陈未证; M6 列数。"""
import os,re,json
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED4"
delta=open(os.path.join(ROOT,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()
hdr=delta[0].split('\t'); data=[l.split('\t') for l in delta[1:] if l.strip()]
print("M6 表头列数=",len(hdr),"数据行列数集=",sorted({len(r) for r in data}))
print("M1 delta 行数=",len(data))
S=json.load(open(os.path.join(ROOT,'EVIDENCE','ROW_SUMMARY.json'),encoding='utf-8'))
print("ROW_SUMMARY four_ring_complete=",S['four_ring_complete'],"delta_rows=",S['delta_rows'])
BAD=['未证','未定','弱信号','线索','未确认','待裁','疑似','未判定','不确定','存疑']
for r in data:
    ent,name,sem=r[0],r[2],r[3]
    cls=name.split('::')[0]
    print("\n--",ent,name)
    print("   M2 ②栏含name类 '.?AV%s@@':"%cls, ('.?AV%s@@'%cls) in sem)
    print("   M8 自陈未证命中:", [w for w in BAD if w in sem])
    # M5: delta 中所有 +0xNNN 必须出现在对应 EVIDENCE
    ev=open(os.path.join(ROOT,'EVIDENCE','ROW_%s.txt'%ent),encoding='utf-8').read()
    offs=set(re.findall(r'\+0x[0-9A-Fa-f]{3,4}',sem))
    missing=[o for o in offs if ('+0x'+o[3:].lstrip('0')).upper() not in re.sub(r'\s','',ev).upper() and o.upper() not in ev.upper()]
    print("   M5 delta偏移数=",len(offs),"不在EVIDENCE:",missing)
