import csv

SRC = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"

rows = []
with open(SRC, encoding="utf-8") as fh:
    for row in csv.DictReader(fh, delimiter="\t"):
        if row["subsystem"] == "S04":
            rows.append(row)

rows.sort(key=lambda x: int(x["entry"], 16))
b2 = rows[18:36]  # 第 19–36 行（1-based 含两端）= 0-based [18,36)

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2\work\b2_entries.tsv", "w", encoding="utf-8") as fh:
    fh.write("entry\tsubsystem\tname\tgrade\tsize\tn_insn\tn_call\tn_site\tn_valid\n")
    for r in b2:
        fh.write("\t".join([r["entry"], r["subsystem"], r["name"], r["grade"],
                            r["size"], r["n_insn"], r["n_call"], r["n_site"], r["n_valid"]]) + "\n")

print("S04 total=%d, B2 slice=%d" % (len(rows), len(b2)))
for r in b2:
    print(r["entry"], r["name"], r["size"])
