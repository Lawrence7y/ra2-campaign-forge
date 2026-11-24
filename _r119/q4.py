import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]

def scan(imm, label):
    pat = imm.to_bytes(4, "little")
    addrs, i = [], 0
    while True:
        i = TB.find(pat, i)
        if i < 0: break
        addrs.append(TVA + i); i += 1
    return {"label": label, "imm": hex(imm), "pattern": pat.hex(" "),
            "unaligned_count": len(addrs),
            "unaligned_addrs": [hex(x) for x in addrs],
            "aligned_4_count": len([a for a in addrs if a % 4 == 0]),
            "aligned_4_addrs": [hex(a) for a in addrs if a % 4 == 0]}

q = {}
q["0x818858"] = scan(0x818858, "target A")
q["0x820270"] = scan(0x820270, "target B")

# positive controls: .data immediates that ARE referenced (verified by nonzero hit)
ctrl = {}
for c in (0x7f9594, 0x818668, 0x819420, 0x817964, 0x817950, 0x82ba48):
    ctrl[hex(c)] = scan(c, "positive control")

# extra: also scan the whole file (beyond .text) so we can say where they live if not in .text
def scan_all(imm):
    pat = imm.to_bytes(4, "little"); out = []
    i = 0
    while True:
        i = BUF.find(pat, i)
        if i < 0: break
        out.append({"off": hex(i), "va": (hex(PE_.off2va(i)) if PE_.off2va(i) else None),
                    "sec": PE_.secname_of_off(i)})
        i += 1
    return out
allA = scan_all(0x818858); allB = scan_all(0x820270)

out = {"q4": {"text_va": hex(TVA), "text_raw": hex(T["raw"]), "text_size": hex(T["rawsize"]),
              "search": "raw 4-byte little-endian pattern, unaligned, entire .text file image",
              "targets": q,
              "positive_controls": ctrl,
              "positive_control_verdict": all(v["unaligned_count"] >= 1 for k, v in ctrl.items() if k != "0x7f9594"),
              "whole_file_occurrences": {"0x818858": allA, "0x820270": allB}}}
json.dump(out, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q4.json","w"), indent=1)
for k, v in q.items(): print(k, "unaligned:", v["unaligned_count"], "aligned:", v["aligned_4_count"], v["unaligned_addrs"][:20])
for k, v in ctrl.items(): print("ctrl", k, v["unaligned_count"], v["unaligned_addrs"][:6])
print("all-file A:", allA)
print("all-file B:", allB)
