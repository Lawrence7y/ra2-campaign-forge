import sys, json, string
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *

TI = 0x7f9594
PRINT = set(string.printable[:-6].encode())
out = {"q2": {}}

def guid_variants(b):
    d = [int.from_bytes(b[4*i:4*i+4], "little") for i in range(4)]
    v = {
      "dwords": [hex(x) for x in d],
      "card_literal_d2_low16_eq_0xC000": (d[1]==0 and (d[2] & 0xFFFF)==0xC000 and d[3]==0x46000000),
      "win_iuploaded_layout_d2_eq_0x000000C0": (d[1]==0 and d[2]==0x000000C0 and d[3]==0x46000000),
      "d2_high16_eq_0xC000": (d[1]==0 and (d[2]>>16)==0xC000 and d[3]==0x46000000),
    }
    return v

def strs_in(va_from, va_to, ctxb):
    """find NUL-terminated printable ASCII strings fully inside [va_from,va_to) that are
       maximal within ctxb. returns list"""
    res = []
    o0 = PE_.va2off(va_from); o1 = PE_.va2off(va_to)
    p = o0
    while p < o1:
        if BUF[p] in PRINT and (p == 0 or BUF[p-1] not in PRINT):
            e = BUF.find(b"\0", p, o1+1)
            if e > 0 and all(c in PRINT for c in BUF[p:e]) and (e - p) >= 3:
                res.append({"va": hex(PE_.off2va(p)), "len": e-p,
                            "text": BUF[p:e].decode("latin1")})
                p = e + 1; continue
        p += 1
    return res

for va in (0x817bb0, 0x817bc0, 0x819088):
    lo, hi = va-0x40, va+0x40
    rec = {"address": hex(va), "section": PE_.secname_of_off(PE_.va2off(va)),
           "window": f"{hex(lo)}..{hex(hi)} (128 bytes)",
           "hex16": [], "dwords": []}
    o = PE_.va2off(lo)
    for i in range(0, 128, 16):
        rec["hex16"].append({"va": hex(lo+i), "hex": BUF[o+i:o+i+16].hex(" "),
                              "ascii": "".join(chr(c) if 32 <= c < 127 else "." for c in BUF[o+i:o+i+16])})
    for i in range(0, 128, 4):
        v = u32(o+i)
        rec["dwords"].append({"va": hex(lo+i), "hex": hex(v), "dec": v,
                              "u32_ascii": "".join(chr((v>>(8*k))&0xff) if 32 <= ((v>>(8*k))&0xff) < 127 else "." for k in range(4))})
    b16 = BUF[PE_.va2off(va):PE_.va2off(va)+16]
    rec["bytes_at_addr_hex"] = b16.hex(" ")
    g = guid_variants(b16)
    rec["q1_guid_shape"] = g
    # +0x10
    op = PE_.va2off(va+0x10)
    d16 = u32(op)
    nm = cstr(op+8, 300) if BUF[op+8:op+9] in (b".",) else None
    rec["q2_plus0x10_dword_at_ptr"] = hex(d16)
    rec["q2_plus0x10_is_type_info_0x7f9594"] = (d16 == TI)
    rec["q3_plus0x10_ptr_then_reserved_then_name"] = (
        "dword@+0x10=%s, dword@+0x14=%s, bytes@+0x18=%r" % (
            hex(d16), hex(u32(op+4)), BUF[op+8:op+40].split(b"\0")[0]))
    rec["q3_plus0x10_name_starts_dot_qA"] = BUF[op+8:op+10] == b".?"
    # strings in +-0x20
    rec["strings_before_0x20"] = strs_in(va-0x20, va, None)
    rec["strings_after_0x20"] = strs_in(va+0x10, va+0x30, None)
    out["q2"][hex(va)] = rec

json.dump(out, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json","w"), indent=1)
for k,v in out["q2"].items():
    print("=== ", k, v["section"], v["bytes_at_addr_hex"])
    print("   guid variants:", {kk:vv for kk,vv in v["q1_guid_shape"].items() if kk!="dwords"}, v["q1_guid_shape"]["dwords"])
    print("   +0x10 dword:", v["q2_plus0x10_dword_at_ptr"], "isTI", v["q2_plus0x10_is_type_info_0x7f9594"], "name?", v["q3_plus0x10_name_starts_dot_qA"], v["q3_plus0x10_ptr_then_reserved_then_name"])
    print("   strs before:", v["strings_before_0x20"])
    print("   strs after :", v["strings_after_0x20"])
