import csv, os, re, hashlib
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S16S21_B1"
raw = open(os.path.join(D,"delta.tsv"),"rb").read()
print("BOM?", raw[:3]==b"\xef\xbb\xbf")
rows = list(csv.reader(open(os.path.join(D,"delta.tsv"), encoding="utf-8"), delimiter="\t"))
hdr = rows[0]; body = rows[1:]
print("header:", hdr)
print("cols ok:", hdr == ["entry","subsystem","name","one_line_semantics","grade","evidence_path"])
print("n rows:", len(body))
ok = True
for r in body:
    if len(r) != 6: print("  BAD colcount", len(r), r[0]); ok=False; continue
    e = r[0]
    if not re.fullmatch(r"[0-9A-F]{8}", e): print("  BAD entry fmt", e); ok=False
    if e != e.upper(): print("  BAD not upper", e); ok=False
    if r[4] != "[已证]": print("  BAD grade", r[4]); ok=False
    ev = r[5]
    if not os.path.exists(ev): print("  MISSING evidence", ev); ok=False
    print("  %s %s %-28s grade=%s ev_exists=%s" % (e, r[1], r[2], r[4], os.path.exists(ev)))
print("delta all good:", ok)
# 交叉核对 name/subsystem 与 SURVEY 原样
src = {}
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        src[row["entry"]] = (row["subsystem"], row["name"])
for r in body:
    s, n = src[r[0]]
    print("  name/subsystem unchanged %s: %s" % (r[0], (s,n)==(r[1],r[2])))
# base_rate
print("\nbase_rate.tsv:"); print(open(os.path.join(D,"base_rate.tsv"), encoding="utf-8").read().strip())
