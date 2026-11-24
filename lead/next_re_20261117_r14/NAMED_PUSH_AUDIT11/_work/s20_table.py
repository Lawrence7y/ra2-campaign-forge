import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify3.json", encoding="utf-8"))
print("### factory QI accepted IIDs (006C2A50 compares edi = 0x7f7c90 / 0x7f7ca0)")
for va in (0x7F7C90, 0x7F7CA0):
    print(f"  {va:08X}: {hexs(va,16)}")
print()
print("### compact table")
hdr = f"{'entry':<9}{'class':<24}{'objctor':<9}{'mainvt':<9}{'vt0':<9}{'installer':<10}{'CLSID':<10}{'slot8'}"
print(hdr)
for d in rows:
    mv = d["obj_main_vt"]["vt"] if d["obj_main_vt"] else "?"
    s0 = d["obj_main_vt"]["slot0"] if d["obj_main_vt"] else "?"
    print(f"{d['entry']:<9}{d['expected_class']:<24}{d['obj_ctor']:<9}{mv:<9}{s0:<9}"
          f"{d['factory_vt_installers'][0]:<10}{d['clsid']:<10}{d.get('obj_slot8')}")
print()
print("### object main vt RTTI name == expected class ?")
for d in rows:
    m = d["obj_main_vt"]
    ok = m and m["rtti"] == ".?AV" + d["expected_class"] + "@@"
    print(f"  {d['entry']} {d['expected_class']:<24} rtti={m['rtti'] if m else None!r:<40} ok={bool(ok)}")
print()
print("### direct callers (should be empty) + entry ret size")
for d in rows:
    va = int(d["entry"], 16)
    print(f"  {d['entry']} callers={d['direct_callers']} ret_bytes={hexs(va+0x11,3)}")
