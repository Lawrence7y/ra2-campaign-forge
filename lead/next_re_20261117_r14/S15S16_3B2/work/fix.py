p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15S16_3B2\work\generate_outputs.py"
with open(p, encoding="utf-8") as f:
    lines = f.read().split("\n")
print("before:", repr(lines[229]))
lines[229] = 'n16 = sum(1 for r,s,sl in delta_rows if r["subsystem"]=="S16" and r["in_atlas"])'
print("after :", repr(lines[229]))
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
