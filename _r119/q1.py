import sys, json, struct
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *

TI_VFT = 0x7f9594
target = struct.pack("<I", TI_VFT)

res = {"q1": {}}

# ---------- a) all 4-byte-aligned dwords == 0x7f9594 in file image of all sections ----------
hits = []
for s in PE_.secs:
    base = s["raw"]
    end = s["raw"] + s["rawsize"]
    o = base + ((4 - (base % 4)) % 4)   # 4-byte aligned (file offset alignment == VA alignment since RVA same)
    while True:
        i = BUF.find(target, o, end)
        if i < 0: break
        if i % 4 == 0:
            hits.append((PE_.off2va(i), i, s["name"]))
        o = i + 1
res["q1"]["a"] = {"criterion": "dword == 0x7f9594, 4-byte aligned, within section file image",
                  "total": len(hits),
                  "by_section": {},
                  "addresses": [{"va": hex(v), "off": hex(o), "sec": n} for v, o, n in hits]}
for v, o, n in hits:
    res["q1"]["a"]["by_section"][n] = res["q1"]["a"]["by_section"].get(n, 0) + 1

# ---------- b) what follows pointer+8 ----------
def read_name(va_ptr_hit, delta=8):
    o = PE_.va2off(va_ptr_hit + delta)
    if o is None: return None
    s = cstr(o, 512)
    return None if s is None else s.decode("latin1", "replace")

after8 = []
for v, o, n in hits:
    nm = read_name(v, 8)
    after8.append({"type_info_va": hex(v), "sec": n, "name_at_plus8": nm,
                   "starts_dot_qA": nm is not None and nm.startswith(".?A"),
                   "starts_dot_question": nm is not None and nm.startswith(".?")})
qA = [x for x in after8 if x["starts_dot_qA"]]
dec = [x for x in after8 if x["starts_dot_question"]]
res["q1"]["b"] = {
    "n_total_hits": len(hits),
    "n_plus8_starts_with_?A": len(qA),
    "n_plus8_starts_with_?": len(dec),
    "names_?A": [x["name_at_plus8"] for x in qA],
    "names_?AU": [x["name_at_plus8"] for x in qA if x["name_at_plus8"].startswith(".?AU")],
    "n_names_?AU": len([x for x in qA if x["name_at_plus8"].startswith(".?AU")]),
    "detail": after8,
}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json","w"), indent=1)
print(json.dumps(res["q1"]["a"]["by_section"]), "total", len(hits))
print("plus8 ?A:", len(qA), " ?:", len(dec))
print("?AU count:", res["q1"]["b"]["n_names_?AU"])
print("first 5:", [x["name_at_plus8"] for x in after8[:5]])
