"""T1：生成全量类表（RTTI 名/TD/COL/vtable/槽数/父类 CHD），并按 UI 关键字圈定 S09 候选。"""
import re
import struct
import re_lib as R

b = R.Bin()
rtti = R.RTTI(b)
text = b.sec(".text")
t_lo, t_hi = text["va"], text["va"] + text["rawsize"]

# 从 v2 读槽数
slots_map = {}
with open("rdata_vtables_walk.tsv", encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4:
            slots_map[int(p[0], 16)] = int(p[3])

# 只保留主 vtable（每个 COL 一个；secondary vtable 的 COL 单独一行，用 offset 区分）
rows = []
for col, rec in rtti.cols.items():
    vt = rec["vtable"]
    if vt is None:
        continue
    parent, nbase, bases = rtti.parent_of(col)
    name = rtti.demangle(rec["name"])
    n = slots_map.get(vt, None)
    rows.append(dict(name=name, mangled=rec["name"], td=rec["td"], col=col,
                     vt=vt, slots=n, offset=rec["offset"], parent=parent,
                     nbase=nbase))

rows.sort(key=lambda r: r["name"].lower())
with open("all_classes.tsv", "w", encoding="utf-8") as f:
    f.write("name\tmangled\ttd\tcol\tvtable\tslots\tcol.offset\tparent\tnbase\n")
    for r in rows:
        f.write("%s\t%s\t%08X\t%08X\t%08X\t%s\t%d\t%s\t%s\n" % (
            r["name"], r["mangled"], r["td"], r["col"], r["vt"],
            r["slots"] if r["slots"] is not None else "NA",
            r["offset"], r["parent"] or "", r["nbase"]))

print("classes with vtable:", len(rows))
from collections import Counter
print("slot None:", sum(1 for r in rows if r["slots"] is None))

# UI 关键字
KW = re.compile(r"sidebar|toolbar|menu|dialog|button|gadget|select|command|"
                r"input|wnd|window|mouse|list|scroll|tab|strip|cameo|tooltip|"
                r"checkbox|check|combo|edit|slider|progress|label|frame|"
                r"viewport|tactical|display|radar|power|net|ui", re.I)
print("\n=== UI-related classes (RTTI name match) ===")
ui = [r for r in rows if KW.search(r["name"])]
print("count:", len(ui))
for r in ui:
    print("%-46s vt=%08X col=%08X slots=%-4s parent=%-32s off=%d" % (
        r["name"], r["vt"], r["col"], r["slots"], r["parent"] or "-", r["offset"]))
