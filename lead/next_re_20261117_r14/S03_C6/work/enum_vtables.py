"""Ring (a): enumerate ALL vtables holding each candidate entry.
For every 4-byte VA occurrence of entry in the image, hypothesize vt=X-slot*4,
validate COL=[vt-4] -> TD=[COL+0xC] -> inline name at TD+8 starting with .?A,
and require slot < table_len(vt) (consecutive .text pointers) to kill the
'next table COL as self slot' pseudo-pair (P3 constraint).
Outputs ALL (vt,slot,name,len) pairs; reports pair count and classes.
Read-only on exe. Self-written; no import from other cards.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CAND = ["00431F70","00432050","004322A0","004325C0","00473C00","00473CE0","00473FC0","0047AAB0",
        "0047AE10","00631D30","0065CCA0","0065CDD0","0065D0D0","0065D190","0065D1F0","0065D240"]
pe = C.get_pe(); data = C._data
TV = C.IMAGE_BASE + C.text_section().VirtualAddress
TE = TV + C.text_section().Misc_VirtualSize

def off2va(i):
    for s in pe.sections:
        if s.PointerToRawData <= i < s.PointerToRawData + s.SizeOfRawData:
            return C.IMAGE_BASE + s.VirtualAddress + (i - s.PointerToRawData)
    return None

def occurrences(va):
    pat = struct.pack("<I", va); out = []; start = 0
    while True:
        i = data.find(pat, start)
        if i < 0: break
        v = off2va(i)
        if v is not None: out.append(v)
        start = i + 1
    return out

def valid_col(vt):
    col = C.u32(vt - 4)
    if col is None: return None
    td = C.u32(col + 0xC)
    if td is None: return None
    name = C.cstr(td + 8)
    if name and name.startswith(".?A"):
        return (col, td, name)
    return None

def table_len(vt, maxn=600):
    n = 0
    for k in range(maxn):
        v = C.u32(vt + 4*k)
        if v is None or not (TV <= v < TE): break
        n += 1
    return n

out = {}
for e in CAND:
    entry = int(e, 16)
    occ = occurrences(entry)
    pairs = []
    pseudo = 0
    for X in occ:
        for slot in range(0, 400):
            vt = X - 4*slot
            if vt < 0x400000: break
            vc = valid_col(vt)
            if not vc: continue
            pseudo += 1
            tl = table_len(vt)
            if slot < tl:
                pairs.append({"vt":"0x%x"%vt, "slot":slot, "col":"0x%x"%vc[0],
                              "td":"0x%x"%vc[1], "name":vc[2], "table_len":tl})
    seen = set(); uniq = []
    for p in pairs:
        k = (p["vt"], p["slot"])
        if k not in seen:
            seen.add(k); uniq.append(p)
    uniq.sort(key=lambda p:(p["vt"], p["slot"]))
    classes = sorted(set(p["name"] for p in uniq))
    slots = sorted(set(p["slot"] for p in uniq))
    same_slot_multi = len(uniq) >= 2 and len(slots) == 1
    out[e] = {"entry":e, "n_occ":len(occ), "n_pseudo":pseudo,
              "pairs":uniq, "classes":classes, "slots":slots,
              "multi_table_same_slot":same_slot_multi}
    print("%s occ=%d pseudo=%d pairs=%d classes=%s slots=%s same_slot_multi=%s" % (
        e, len(occ), pseudo, len(uniq), classes, slots, same_slot_multi))
    for p in uniq:
        print("    vt=%s slot=%d name=%s len=%d col=%s td=%s" % (
            p["vt"], p["slot"], p["name"], p["table_len"], p["col"], p["td"]))

with open(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "rtti_all_tables.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("wrote EVIDENCE/rtti_all_tables.json")
