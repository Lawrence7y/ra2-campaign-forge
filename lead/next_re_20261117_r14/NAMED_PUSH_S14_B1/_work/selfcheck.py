# -*- coding: utf-8 -*-
"""交付物自校验：delta 格式/去重/路径存在；并逐行复核被引用的关键字节。"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = BASE
ok = True

# --- delta.tsv ---
rows = [l.rstrip("\n").split("\t") for l in io.open(os.path.join(B, "delta.tsv"), encoding="utf-8")]
hdr, body = rows[0], rows[1:]
assert hdr == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], hdr
print("delta header OK; rows =", len(body))
seen = set()
for r in body:
    e = r[0]
    assert re.fullmatch(r"[0-9A-F]{8}", e), "entry not uppercase hex: %r" % e
    assert not e.startswith("0x")
    assert r[1] == "S14" and r[4] == "[已证]"
    p = r[5].replace("/", "\\")
    assert os.path.isfile(p), "missing evidence: %s" % p
    assert os.path.basename(p) == "ROW_%s.txt" % e, p
    assert e not in seen; seen.add(e)
print("delta entries:", sorted(seen))

# --- 每行语义互不相同 ---
sems = [r[3] for r in body]
print("distinct semantics:", len(set(sems)), "/", len(sems))
assert len(set(sems)) == len(sems)

# --- 逐行复核关键字节 ---
CHECK = [  # (addr, expected hex bytes, 说明)
    (0x410389, "b803400080", "0x410380 空参返 E_POINTER"),
    (0x41032B, "b803400080", "0x410320 空参返 E_POINTER"),
    (0x523CE7, "83c8ff", "0x523C90 未命中 or eax,-1"),
    (0x523CEC, "8bc6", "0x523C90 命中 mov eax,esi"),
    (0x41F783, "e808451000", "row3 call 0x523C90"),
    (0x41F788, "83f8ff", "row3 cmp eax,-1"),
    (0x41F78B, "740b", "row3 je ->0x41F798"),
    (0x5031C9, "e8b2d1f0ff", "row7 call 0x410380"),
    (0x5031D0, "0f8c930e0000", "row7 jl ->0x504069"),
    (0x5122D0, "e8abe0efff", "row10 call 0x410380"),
    (0x5122D7, "0f8c90010000", "row10 jl ->0x51246D"),
    (0x512491, "e88ade efff".replace(" ", ""), "row11 call 0x410320"),
    (0x512498, "0f8cbe000000", "row11 jl ->0x51255C"),
    (0x65AC52, "e8c956dbff", "row14 call 0x410320"),
    (0x65AC59, "7c4a", "row14 jl ->0x65ACA5"),
]
for addr, exp, what in CHECK:
    got = R.read_va(addr, len(exp) // 2).hex()
    flag = "OK " if got == exp else "BAD"
    if got != exp: ok = False
    print("%s %08X %-14s got=%s exp=%s  %s" % (flag, addr, "", got, exp, what))

# --- 槽值 == entry（18 行）---
AN = json.load(open(os.path.join(B, "_work", "analysis.json"), encoding="utf-8"))
bad = 0
for rec in AN:
    slot = [s for s in rec["ring2_slots"] if s.get("rtti_name")]
    if not slot:
        print("BAD no rtti slot", rec["entry"]); bad += 1; continue
    v = R.u32(int(slot[0]["slot_va"], 16))
    if v != int(rec["entry"], 16):
        print("BAD slot value", rec["entry"], hex(v)); bad += 1
print("18 行槽值 == entry 复核：bad =", bad)
ok = ok and bad == 0
print("ALL OK" if ok else "FAILURES PRESENT")
