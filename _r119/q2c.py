import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
TI = 0x7f9594
out = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json"))
VERD = {}
for va_s in ("0x817bb0", "0x817bc0", "0x819088"):
    va = int(va_s, 16); o = PE_.va2off(va)
    d = [u32(o+4*i) for i in range(4)]
    op = PE_.va2off(va+0x10)
    d16, d20 = u32(op), u32(op+4)
    nm = BUF[op+8:op+8+2]
    VERD[va_s] = {
      "addr": va_s,
      "bytes_at_addr": BUF[o:o+16].hex(" "),
      "dwords": [hex(x) for x in d],
      "q1_is_com_shape_TRUE_defn(d1==0,d2==0x000000C0,d3==0x46000000)":
          (d[1] == 0 and d[2] == 0x000000C0 and d[3] == 0x46000000),
      "q1_is_com_shape_CARD_WORDING(d1==0,(d2&0xFFFF)==0xC000,d3==0x46000000)":
          (d[1] == 0 and (d[2] & 0xFFFF) == 0xC000 and d[3] == 0x46000000),
      "byte_evidence_for_q1": "dword[1]@%s=0x%08x ; dword[2]@%s=0x%08x ; dword[3]@%s=0x%08x" % (
          hex(va+4), d[1], hex(va+8), d[2], hex(va+12), d[3]),
      "q2_plus0x10_is_type_info": {"addr": hex(va+0x10), "dword": hex(d16),
          "answer": "yes" if d16 == TI else "no",
          "why": "dword @%s = 0x%08x, not 0x%08x" % (hex(va+0x10), d16, TI)},
      "q3_plus0x10_is_decorated_name": {
          "addr": hex(va+0x18), "bytes": BUF[op+8:op+8+24].hex(" "),
          "ascii": "".join(chr(c) if 32 <= c < 127 else "." for c in BUF[op+8:op+8+24]),
          "answer": "yes" if nm == b".?" else "no",
          "why": "first 2 bytes @%s = %s ; reserved dword @%s = 0x%08x" % (
              hex(va+0x18), BUF[op+8:op+10].hex(" "), hex(va+0x14), d20)},
    }
out["q2"]["explicit_verdicts"] = VERD
json.dump(out, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q2.json","w"), indent=1)
for k, v in VERD.items():
    print("====", k, v["bytes_at_addr"], v["dwords"])
    print("   Q1 COM(card wording):", v["q1_is_com_shape_CARD_WORDING(d1==0,(d2&0xFFFF)==0xC000,d3==0x46000000)"], " COM(true shape):", v["q1_is_com_shape_TRUE_defn(d1==0,d2==0x000000C0,d3==0x46000000)"], "|", v["byte_evidence_for_q1"])
    print("   Q2 +0x10 type_info:", v["q2_plus0x10_is_type_info"]["answer"], v["q2_plus0x10_is_type_info"]["why"])
    print("   Q3 +0x10 decorated name:", v["q3_plus0x10_is_decorated_name"]["answer"], v["q3_plus0x10_is_decorated_name"]["why"], v["q3_plus0x10_is_decorated_name"]["ascii"])
