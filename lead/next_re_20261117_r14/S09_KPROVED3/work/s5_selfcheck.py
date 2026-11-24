"""S09-KPROVED3 step 5: consistency self-check against own evidence files."""
from __future__ import annotations

import csv
import re

import k3lib as k

EV = k.OUT / "EVIDENCE"


def rows(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


delta = rows(k.OUT / "coverage_delta.tsv")
holders = rows(EV / "VTABLES_ALL8.tsv")
attrib = {r["entry"]: r for r in rows(EV / "CLASS_ATTRIB.tsv")}
sites = rows(EV / "DIRECT_SITES_8.tsv")
contract = rows(EV / "CONTRACT_3B.tsv")

ok = True
log = []
for d in delta:
    e = d["entry"]
    sem = d["one_line_semantics"]
    checks = []

    checks.append(("name_base_match", d["name"] == attrib[e]["delta_name"]))

    hrows = [h for h in holders if h["entry"] == e]
    vts = {h["vt"][-6:].upper() for h in hrows}
    named = {h["td_plus8_name"] for h in hrows}
    sem_vts = {v[-6:].upper() for v in re.findall(r"vt([0-9A-F]{6,8})", sem)}
    checks.append(("all_holder_vts_listed", sem_vts == vts))
    sem_names = set(re.findall(r"\.\?A[UV][A-Za-z0-9_@]+", sem))
    checks.append(("holder_names_subset", sem_names <= named))
    checks.append(("holder_count", len(hrows) == int(attrib[e]["n_holders"])))

    sites_in = set()
    for chunk in re.findall(r"E8@([0-9A-F/]+)", sem):
        sites_in.update(p for p in chunk.split("/") if len(p) == 8)
    good_sites = {s["site"] for s in sites if s["entry"] == e and s["ok_external"] == "1"}
    checks.append(("direct_sites_exact", sites_in == good_sites))

    dis = (EV / f"DISASM_{e}.txt").read_text(encoding="utf-8")
    offs = {f"{int(x, 16):04X}" for x in re.findall(r"(?<!\w)\+0x([0-9A-Fa-f]+)", sem)}
    dis_offs = set(re.findall(r"\+0x([0-9A-F]{4})", dis))
    missing = sorted(offs - dis_offs)
    checks.append(("offsets_in_disasm", not missing))

    c = next(x for x in contract if x["entry"] == e)
    checks.append(("contract_admits", "进 delta" in c["verdict"]))
    if "细则#1" in sem:
        checks.append(("L4_labeled", "细则#1级" in sem))

    for label, val in checks:
        if not val:
            ok = False
        log.append(f"{e}\t{label}\t{'PASS' if val else 'FAIL'}")

delta_entries = {d["entry"] for d in delta}
admitted = {c["entry"] for c in contract if "进 delta" in c["verdict"] and "不进 delta" not in c["verdict"]}
check = ("delta_entry_set", delta_entries == admitted)
if not check[1]:
    ok = False
log.append(f"ALL\t{check[0]}\t{'PASS' if check[1] else 'FAIL'}")

(EV / "SELFCHECK.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
print("\n".join(log))
print("OVERALL", "PASS" if ok else "FAIL")
