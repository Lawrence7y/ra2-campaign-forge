import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import audit_lib as A
rows,hdr=A.load_func_atlas()
d={va:rec for va,rec in rows}
targets=[0x46CC90,0x46CCD0,0x46CE10,0x46CFC0,0x46D070,0x46D330,0x46D350,0x46D360,0x470C90,0x471500,0x471520,0x52CB90,0x46FC00,0x410A60,0x6851F0,0x52F260,0x46CB60]
for t in targets:
    print(f"{t:08X}: {'IN ATLAS '+str(d.get(t,{}).get('name','?')) if t in d else 'NOT in atlas'}")
