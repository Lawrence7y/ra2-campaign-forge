import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *

TI_VFT = 0x7f9594
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json"))
hits = [(int(h["va"],16), int(h["off"],16), h["sec"]) for h in res["q1"]["a"]["addresses"]]

def dw(va, k):
    o = PE_.va2off(va)
    if o is None: return None
    if o + 4 > len(BUF): return None
    return u32(o + 4*k)

def guid_at(va, d4=0x46000000, check_d2=True):
    """returns (ok, four_dwords)"""
    o = PE_.va2off(va)
    if o is None or o+16 > len(BUF): return (False, None)
    d = [u32(o+4*i) for i in range(4)]
    ok = True
    if check_d2 and d[1] != 0: ok = False
    if (d[2] & 0xFFFF) != 0xC000: ok = False
    if d[3] != d4: ok = False
    return (ok, d)

def name_at(va, delta=8):
    o = PE_.va2off(va+delta)
    if o is None: return None
    s = cstr(o, 512)
    return None if s is None else s.decode("latin1","replace")

# ---- c) GUID at va-0x10 ----
c_hits = []
for va, off, sec in hits:
    gva = va - 0x10
    ok, d = guid_at(gva)
    if ok:
        o = PE_.va2off(gva)
        c_hits.append({"type_info_va": hex(va), "name": name_at(va, 8),
                       "guid_va": hex(gva), "guid_hex": BUF[o:o+16].hex(),
                       "guid_section": PE_.secname_of_off(o),
                       "dwords": [hex(x) for x in d]})
res["q1"]["c"] = {"criterion": "at type_info_va-0x10, 16 bytes with d1&0xFFFF==0xC000, d2==0, d3==0x46000000",
                  "count": len(c_hits), "hits": c_hits}

# ---- d) reverse control: 0x46000001 ----
d_hits = []
for va, off, sec in hits:
    ok, d = guid_at(va-0x10, d4=0x46000001)
    if ok: d_hits.append(hex(va))
res["q1"]["d"] = {"neg_control_d4_0x46000001": {"count": len(d_hits), "hits": d_hits}}

# positive control: only d[1]==0 (2nd dword zero) at va-0x10
p_hits = []
for va, off, sec in hits:
    o = PE_.va2off(va-0x10)
    if o is None: continue
    if u32(o+4) == 0: p_hits.append(hex(va))
res["q1"]["d"]["pos_control_only_d2_zero"] = {"count": len(p_hits), "hits_sample": p_hits[:60],
                                              "must_be_gt_c": len(p_hits) > len(c_hits)}
# extra: only d3==0x46000000
p2 = [hex(va) for va,off,sec in hits if PE_.va2off(va-0x10) is not None and u32(PE_.va2off(va-0x10)+12) == 0x46000000]
res["q1"]["d"]["aux_only_d4_0x46000000"] = {"count": len(p2)}

# ---- e) all COM-shaped 16-byte constants in .data ----
ds = PE_.sec_by_name(".data")
com = []
o = ds["raw"]
end = ds["raw"] + ds["rawsize"]
while o + 16 <= end:
    if (o - ds["raw"]) % 4 == 0:
        if u32(o+4) == 0 and (u32(o+8) & 0xFFFF) == 0xC000 and u32(o+12) == 0x46000000:
            va = ds["va"] + (o - ds["raw"])
            com.append(va)
    o += 4
com_detail = []
for va in com:
    o = PE_.va2off(va)
    plus16 = va + 0x10
    op = PE_.va2off(plus16)
    is_ti = (op is not None and op+4 <= len(BUF) and u32(op) == TI_VFT)
    nm = name_at(plus16, 8)
    com_detail.append({"guid_va": hex(va), "guid_hex": BUF[o:o+16].hex(),
                       "plus0x10_dword": (hex(u32(op)) if op is not None else None),
                       "plus0x10_is_type_info_vft": is_ti,
                       "plus0x10_name": nm,
                       "plus0x10_name_is_?A": nm is not None and nm.startswith(".?A")})
res["q1"]["e"] = {"scan": "4-byte aligned, .data file image 0x812000..0x87e000",
                  "total_com_shaped_in_data": len(com),
                  "addresses": [hex(v) for v in com],
                  "n_plus0x10_is_0x7f9594": sum(1 for x in com_detail if x["plus0x10_is_type_info_vft"]),
                  "n_plus0x10_is_dot_?A_name": sum(1 for x in com_detail if x["plus0x10_name_is_?A"]),
                  "detail": com_detail}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json","w"), indent=1)
print("a total", len(hits))
print("c count", len(c_hits))
print("neg control (0x46000001)", len(d_hits))
print("pos control (d2==0 only)", len(p_hits), ">", len(c_hits), len(p_hits)>len(c_hits))
print("aux d4==0x46000000 only", len(p2))
print("e total COM in .data", len(com))
print("e +0x10 == 0x7f9594:", res["q1"]["e"]["n_plus0x10_is_0x7f9594"], " +0x10 name ?A:", res["q1"]["e"]["n_plus0x10_is_dot_?A_name"])
for x in c_hits: print("C:", x["type_info_va"], x["name"], x["guid_hex"], x["guid_section"])
