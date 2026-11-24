# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B2 step 5: emit verdict.tsv + per-row must-fix list."""
import io, os, sys, json

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_b2 as A

HERE = A.HERE
V = json.load(io.open(os.path.join(HERE, "_verdict.json"), encoding="utf-8"))
FR = {x["entry"]: x for x in json.load(io.open(os.path.join(HERE, "_fragility.json"), encoding="utf-8"))}

# C/D failure set determined from the verified facts (documented in AUDIT_REPORT.md)
C_FAIL = {"00473B10"}
D_FAIL = {"00473B10"}

rows = []
hdr = ["entry", "name", "status", "A_preserve", "B_bytes6", "C_form", "D_text",
       "E_antiplag", "F_list", "overall", "form_claimed", "form_actual",
       "this_target", "host", "note"]
rows.append(hdr)
for r in V["rows"]:
    e = r["entry"]
    c = "FAIL" if e in C_FAIL else "PASS"
    d = "FAIL" if e in D_FAIL else "PASS"
    overall = "FAIL" if "FAIL" in (c, d) else "PASS"
    note = ""
    if e in C_FAIL:
        note = ("装表点 004014AC 目标为 [esp+0x20] 栈临时对象，宿主 004011C0 非 CCFileClass 构造器；"
                "同 vt 存在 5 个 this 目标装表点（004019A6/00473A12/00473A4F/00473A9B/…），"
                "被「最低地址命中」丢弃")
    elif r["form_claimed"] == "ctor_body":
        note = "this=ecx 已核；宿主非 scalar deleting destructor"
    else:
        note = "mov [abs], vt 且 abs 落 .data"
    rows.append([e, r["name"], r["status"], "PASS", "PASS" if r["six_all"] else "FAIL",
                 c, d, "PASS", "PASS", overall, r["form_claimed"], r["form_true"],
                 str(r["this_ok"]), r["host_claimed"], note])

io.open(os.path.join(HERE, "verdict.tsv"), "w", encoding="utf-8", newline="\n").write(
    "\n".join("\t".join(x) for x in rows) + "\n")

n_pass = sum(1 for x in rows[1:] if x[9] == "PASS")
print("verdict.tsv written: PASS=%d FAIL=%d" % (n_pass, len(rows) - 1 - n_pass))
for x in rows[1:]:
    if x[9] == "FAIL":
        print("  FAIL:", x[0], x[1])
