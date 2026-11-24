import json, os

P = {
 "T42": r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\qc151_fields.json",
 "E4":  r"D\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e4\qc151_fields.json",
}
# fix typo-safe literal for E4
P["E4"] = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_202611023e4\qc151_fields.json" if False else r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e4\qc151_fields.json"

for k in ("T42", "E4"):
    rp = os.path.realpath(P[k])
    if not rp.startswith(r"D:\Project\ra2-campaign-forge"):
        raise SystemExit("bad path")
    with open(P[k], "r", encoding="utf-8") as fh:
        d = json.load(fh)
    print("=====", k, " type:", type(d).__name__)
    if isinstance(d, dict):
        print("top keys:", list(d.keys())[:10], "... total", len(d))
        items = None
        for cand in ("fields", "rows", "records", "entries", "data"):
            if cand in d and isinstance(d[cand], list):
                items = d[cand]; break
        if items is None:
            print("no list field found; showing small keys")
            for kk, vv in d.items():
                if not isinstance(vv, (list, dict)) or len(vv) < 6:
                    print("  ", kk, "=", repr(vv)[:200])
            items = []
        meta = d.get("META") or d.get("meta")
        if meta:
            print("META:", json.dumps(meta, ensure_ascii=False)[:600])
    elif isinstance(d, list):
        items = d
        print("len:", len(d))
        print("first row:", json.dumps(d[0], ensure_ascii=False)[:400])
    if items:
        for row in items:
            if isinstance(row, dict) and "forensics" in json.dumps(row.get("key", "")):
                print("FORENSIC ROW:", json.dumps(row, ensure_ascii=False))
    print()
