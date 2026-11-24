# -*- coding: utf-8 -*-
"""M68 apply: 4 rows x 3 cols in coverage.tsv (S12 NAMED_PUSH_AUDIT8 PASS)."""
import csv, os, sys, hashlib, datetime, json
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S12_B1", "delta.tsv")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
MDIR = os.path.join(ROOT, "MERGE_M68")
BAK = os.path.join(MDIR, "coverage.tsv.bak")
EVID = "NAMED_PUSH_AUDIT8/VERDICT.md"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def sha256b(b):
    return hashlib.sha256(b).hexdigest().upper()

def utc_iso(p):
    ts = os.path.getmtime(p)
    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def read_tsv_rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

# delta semantics map (col 4, index 3)
dmap = {}
for r in read_tsv_rows(DELTA)[1:]:
    if len(r) >= 6 and r[0].strip():
        dmap[ne(r[0])] = r[3]

TARGETS = [ne(x) for x in ['00442230', '00447210', '00447F10', '0044E8F0']]
assert len(TARGETS) == 4 and len(set(TARGETS)) == 4
for e in TARGETS:
    assert e in dmap, "delta missing %s" % e

raw = open(COV, "rb").read()
before = dict(bytes=len(raw), mtime_utc=utc_iso(COV), sha256=sha256b(raw))
print("BEFORE sha=", before["sha256"], "bytes=", before["bytes"], "mtime=", before["mtime_utc"])
# backup
open(BAK, "wb").write(raw)
assert sha256b(open(BAK, "rb").read()) == before["sha256"]

text = raw.decode("utf-8")
lines = text.split("\n")
assert len(lines) == 18499, len(lines)
assert lines[-1] != "" and "\t" in lines[-1], repr(lines[-1][:50])

# index target rows
hits = {e: [] for e in TARGETS}
for i in range(1, len(lines)):
    parts = lines[i].split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in hits:
        hits[e].append(i)

for e in TARGETS:
    assert len(hits[e]) == 1, (e, len(hits[e]))

change_log = []
for e in TARGETS:
    i = hits[e][0]
    parts = lines[i].split("\t")
    assert len(parts) == 8
    assert parts[4].strip() == "[静态推断]", (e, parts[4])  # precondition
    old = list(parts)
    # immutable cols
    old1, old2, old3, old7, old8 = parts[0], parts[1], parts[2], parts[6], parts[7]
    parts[3] = dmap[e]           # col4 = delta col4 verbatim
    parts[4] = "[已证]"           # col5
    parts[5] = EVID               # col6
    assert parts[0]==old1 and parts[1]==old2 and parts[2]==old3 and parts[6]==old7 and parts[7]==old8
    assert parts[3] == dmap[e] and "[未证]" not in parts[3]
    lines[i] = "\t".join(parts)
    change_log.append(dict(entry=e, line=i+1, old_grade=old[4], old_evid=old[5],
                           new_grade=parts[4], new_evid=parts[5], sem_len=len(parts[3])))

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
open(COV, "wb").write(new_raw)
after = dict(bytes=len(new_raw), mtime_utc=utc_iso(COV), sha256=sha256b(new_raw))
print("AFTER  sha=", after["sha256"], "bytes=", after["bytes"], "mtime=", after["mtime_utc"])
print("changed rows=", len(TARGETS))
for c in change_log:
    print("  ", c["entry"], "L%d"%c["line"], "grade", c["old_grade"], "->", c["new_grade"],
          "| evid", c["old_evid"], "->", c["new_evid"], "| sem_len", c["sem_len"])

with open(os.path.join(MDIR, "_state.json"), "w", encoding="utf-8") as f:
    json.dump(dict(coverage=dict(before=before, after=after), change_log=change_log),
              f, ensure_ascii=False, indent=1)
