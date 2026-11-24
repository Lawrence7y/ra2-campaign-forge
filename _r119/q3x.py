import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]
insns = []; o = 0; N = len(TB)
while o < N:
    got = 0
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+65536], TVA + o):
        insns.append((a, sz, mn, op)); got = 1; o = a - TVA + sz
    if not got or o < N: o += 1
starts = {a: (sz, mn, op) for (a, sz, mn, op) in insns}
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))
lin = {h["va"] if isinstance(h["va"],int) else int(h["va"],16) for h in res["q3"]["a"]["all_hits"]}
import json as _j; res["q3"]["a"]["all_hits"]=[dict(h, va=hex(h["va"]) if isinstance(h["va"],int) else h["va"]) for h in res["q3"]["a"]["all_hits"]]
raw = set()
for i in range(N-8):
    b = TB[i]
    if b == 0xC1 and ((TB[i+1]>>3)&7)==4 and TB[i+2]==4: raw.add(TVA+i)
    elif b == 0xC0 and ((TB[i+1]>>3)&7)==4 and TB[i+2]==4: raw.add(TVA+i)
    elif b == 0x66 and TB[i+1]==0xC1 and ((TB[i+2]>>3)&7)==4 and TB[i+3]==4: raw.add(TVA+i)
only_raw = sorted(raw - lin)
explain = []
for a in only_raw:
    if a in starts:
        sz, mn, op = starts[a]
        explain.append({"addr": hex(a), "in_linear_decode_but_form_missed": True, "mnem": mn, "ops": op,
                        "bytes": TB[a-TVA:a-TVA+sz].hex(" ")})
    else:
        # is it the C1 byte of a 66-prefixed instruction starting 1 byte earlier?
        if a-1 in starts and TB[a-1-TVA] == 0x66:
            sz, mn, op = starts[a-1]
            explain.append({"addr": hex(a), "kind": "66-prefix offset artifact: real instruction starts at %s" % hex(a-1),
                            "mnem": mn, "ops": op, "bytes": TB[a-1-TVA:a-1-TVA+sz].hex(" ")}) 
        else:
            explain.append({"addr": hex(a), "kind": "not an instruction start in the linear decode (inside a non-code/data blob)"})
res["q3"]["a"]["raw_byte_scan_cross_check"] = {
  "linear_sweep_n": len(lin), "raw_scan_n": len(raw),
  "only_in_raw_n": len(only_raw), "only_in_linear_n": len(lin - raw),
  "only_in_linear": [hex(x) for x in sorted(lin - raw)],
  "only_in_raw_explained": explain}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
for e in explain: print(e)
print("only_in_linear:", [hex(x) for x in sorted(lin-raw)])
