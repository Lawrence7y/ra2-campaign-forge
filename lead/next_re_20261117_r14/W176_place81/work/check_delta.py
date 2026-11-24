p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\coverage_delta.tsv"
for i, line in enumerate(open(p, encoding="utf-8"), 1):
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 6:
        print("BAD", i, len(parts), repr(line))
    elif i > 1:
        try:
            int(parts[0], 16)
        except ValueError:
            print("BADHEX", i, parts[0])
        if len(parts[0]) != 8:
            print("LEN", i, len(parts[0]), parts[0])
print("checked")
