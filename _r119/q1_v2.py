import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
TI = 0x7f9594
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json"))
hits = [(int(h["va"],16), int(h["off"],16), h["sec"]) for h in res["q1"]["a"]["addresses"]]

def dws(va, n=4):
    o = PE_.va2off(va)
    if o is None or o+4*n > len(BUF): return None, None
    return o, [u32(o+4*i) for i in range(n)]

def name_at(va, delta=8):
    o = PE_.va2off(va+delta)
    if o is None: return None
    s = cstr(o, 512)
    return None if s is None else s.decode("latin1","replace")

def is_com(d, variant):
    if variant == "card_literal":   # d2 low16 == 0xC000  (as written in the card)
        return d[1] == 0 and (d[2] & 0xFFFF) == 0xC000 and d[3] == 0x46000000
    if variant == "com_true":       # {d1-0000-0000-C000-000000000046}: d2 == 0x000000C0
        return d[1] == 0 and d[2] == 0x000000C0 and d[3] == 0x46000000
    if variant == "ctrl_46000001":
        return d[1] == 0 and d[2] == 0x000000C0 and d[3] == 0x46000001
    if variant == "pos_only_d1_zero":
        return d[1] == 0
    if variant == "pos_only_d3":
        return d[3] == 0x46000000
    raise KeyError(variant)

def run(variant):
    out = []
    for va, off, sec in hits:
        o, d = dws(va-0x10)
        if d is None: continue
        if is_com(d, variant):
            out.append({"type_info_va": hex(va), "type_info_name": name_at(va, 8),
                        "guid_va": hex(va-0x10), "guid_hex": BUF[o:o+16].hex(" "),
                        "guid_dwords": [hex(x) for x in d],
                        "guid_section": PE_.secname_of_off(o)})
    return out

card = run("card_literal")
true_ = run("com_true")
neg = run("ctrl_46000001")
pos1 = run("pos_only_d1_zero")
pos2 = run("pos_only_d3")

res["q1"]["c"] = {
  "card_literal_criterion": {"defn": "d[1]==0 and (d[2]&0xFFFF)==0xC000 and d[3]==0x46000000", "count": len(card), "hits": card},
  "corrected_criterion": {"defn": "d[1]==0 and d[2]==0x000000C0 and d[3]==0x46000000  (i.e. GUID {d1-0000-0000-C000-000000000046}, IID_IUnknown-style COM layout)",
                          "count": len(true_), "hits": true_},
  "note": "card's '3rd dword low16 == 0xC000' does not match the actual COM layout in this image; the C000 byte pair occupies d[2] low 8 bits (d[2]==0x000000C0). Both numbers reported."
}
res["q1"]["d"] = {
  "neg_control_d3_0x46000001_on_corrected_criterion": {"count": len(neg), "hits": neg},
  "pos_control_only_d1_zero": {"count": len(pos1), "defn": "d[1]==0 alone",
                               "must_be_gt_c": len(pos1) > len(true_), "hits": [x["type_info_va"] for x in pos1]},
  "aux_pos_control_only_d3_0x46000000": {"count": len(pos2), "hits": [x["type_info_va"] for x in pos2]},
}

ds = PE_.sec_by_name(".data")
com = []
o = ds["raw"]; end = ds["raw"] + ds["rawsize"]
while o + 16 <= end:
    if u32(o+4) == 0 and u32(o+8) == 0x000000C0 and u32(o+12) == 0x46000000:
        com.append(ds["va"] + (o - ds["raw"]))
    o += 4
det = []
for va in com:
    o = PE_.va2off(va); op = PE_.va2off(va+0x10)
    d = u32(op) if op is not None else None
    nm = name_at(va+0x10, 8)
    det.append({"guid_va": hex(va), "guid_hex": BUF[o:o+16].hex(" "),
                "plus0x10_dword": (hex(d) if d is not None else None),
                "plus0x10_is_0x7f9594": d == TI,
                "plus0x10_name": nm,
                "plus0x10_name_is_?A": bool(nm and nm.startswith(".?A"))})
res["q1"]["e"] = {"defn": "4-byte aligned 16-byte window in .data with d[1]==0,d[2]==0x000000C0,d[3]==0x46000000",
                  "total": len(com), "addresses": [hex(v) for v in com],
                  "n_plus0x10_eq_0x7f9594": sum(1 for x in det if x["plus0x10_is_0x7f9594"]),
                  "n_plus0x10_name_?A": sum(1 for x in det if x["plus0x10_name_is_?A"]),
                  "detail": det}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json","w"), indent=1)
print("c card_literal:", len(card), " corrected:", len(true_))
print("neg(0x46000001):", len(neg), " pos(d1==0 only):", len(pos1), ">", len(true_), len(pos1)>len(true_), " aux(d3 only):", len(pos2))
print("e total:", len(com), " +0x10==TI:", res["q1"]["e"]["n_plus0x10_eq_0x7f9594"], " +0x10 ?A:", res["q1"]["e"]["n_plus0x10_name_?A"])
for x in true_[:20]: print("C:", x["type_info_va"], x["type_info_name"], "|", x["guid_va"], x["guid_hex"], x["guid_section"])
