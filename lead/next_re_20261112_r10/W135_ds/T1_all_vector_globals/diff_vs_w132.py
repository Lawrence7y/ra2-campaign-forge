# -*- coding: utf-8 -*-
"""Diff my enumeration against the lead's W132 result (49 rows)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
W132 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W132_arrays\instance_arrays.tsv"

def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        rows = []
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            rows.append(dict(zip(head, line.split("\t"))))
    return head, rows

def elem_of(s):
    """Pure element type, with or without the container wrapper (lead writes the wrapper)."""
    s = norm(s)
    if s.startswith("DynamicVectorClass<") and s.endswith(">"):
        s = s[len("DynamicVectorClass<"):-1]
    elif s.startswith("VectorClass<") and s.endswith(">"):
        s = s[len("VectorClass<"):-1]
    return s.strip()

def norm(s):
    s = s.replace("SpotlightClass", "SpotLightClass")
    return s

h132, lead = read_tsv(W132)
hmine, mine = read_tsv(os.path.join(HERE, "vector_globals.tsv"))

mine_by_base = {r["base"].upper(): r for r in mine}
lead_by_base = {r["base"].upper(): r for r in lead}

rep = []
only_lead = []
only_mine = []
diff_elem = []
diff_vft = []

for b in sorted(lead_by_base):
    L = lead_by_base[b]
    M = mine_by_base.get(b)
    if not M:
        only_lead.append(b)
        continue
    same_elem = elem_of(L["element"]) == norm(M["element"])
    same_vft = L["vftable"].upper() == M["vftable"].upper()
    rec = "%s  lead=%-44s mine=%-46s vft(lead %s / mine %s)" % (
        b, L["element"], M["element"], L["vftable"], M["vftable"])
    if not same_elem:
        diff_elem.append(rec)
    elif not same_vft:
        diff_vft.append(rec)
    else:
        rep.append(rec)

for b in sorted(mine_by_base):
    if b not in lead_by_base:
        only_mine.append("%s  %s" % (b, mine_by_base[b]["element"]))

out = []
out.append("W132 rows: %d" % len(lead))
out.append("my rows  : %d" % len(mine))
out.append("")
out.append("== reproduced, same base AND same element (%d) ==" % len(rep))
out.extend("  " + r for r in rep)
out.append("")
out.append("== same base, DIFFERENT element type (%d) ==" % len(diff_elem))
out.extend("  " + r for r in diff_elem)
out.append("")
out.append("== same base+element but different vftable address (%d) ==" % len(diff_vft))
out.extend("  " + r for r in diff_vft)
out.append("")
out.append("== in W132 but not produced by me (%d) ==" % len(only_lead))
out.extend("  " + r for r in only_lead)
out.append("")
out.append("== produced by me, not in W132 (%d) ==" % len(only_mine))
out.extend("  " + r for r in only_mine)
out.append("")
txt = "\n".join(out) + "\n"
with open(os.path.join(HERE, "diff_vs_w132.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write(txt)
print(txt)
