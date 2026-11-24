import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]
res = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json"))

def raw_scan(mult):
    """raw byte pattern scan, independent of any disassembler"""
    out = {"shl_rm32_imm8_C1/4_imm": [], "shl_rm8_imm8_C0/4_imm": [], "shl_rm16_imm8_66C1/4_imm": [],
           "imul_r32_rm32_imm8_6B_r_imm": [], "imul_r32_rm32_imm32_69_r_imm": []}
    for i in range(len(TB) - 8):
        b = TB[i]
        # C1 /4 ib  (shl r/m32, imm8)
        if b == 0xC1 and ((TB[i+1] >> 3) & 7) == 4 and TB[i+2] == mult:
            out["shl_rm32_imm8_C1/4_imm"].append(TVA + i)
        if b == 0xC0 and ((TB[i+1] >> 3) & 7) == 4 and TB[i+2] == mult:
            out["shl_rm8_imm8_C0/4_imm"].append(TVA + i)
        if b == 0x66 and TB[i+1] == 0xC1 and ((TB[i+2] >> 3) & 7) == 4 and TB[i+3] == mult:
            out["shl_rm16_imm8_66C1/4_imm"].append(TVA + i)
        if b == 0x6B and TB[i+2] == mult:
            out["imul_r32_rm32_imm8_6B_r_imm"].append(TVA + i)
        if b == 0x69 and TB[i+2:i+6] == bytes([mult, 0, 0, 0]):
            out["imul_r32_rm32_imm32_69_r_imm"].append(TVA + i)
    return out
r16 = raw_scan(4); r8 = raw_scan(8)
res["q3"]["a"]["raw_byte_scan_mul16"] = {k: {"count": len(v), "addrs": [hex(x) for x in v]} for k, v in r16.items()}
res["q3"]["d"]["raw_byte_scan_mul8"] = {k: {"count": len(v), "addrs": [hex(x) for x in v[:40]]} for k, v in r8.items()}
lin = {int(h["va"],16) for h in res["q3"]["a"]["all_hits"]}
rawset = set()
for k, v in r16.items(): rawset |= set(v)
res["q3"]["a"]["cross_check_linear_vs_raw"] = {
  "linear_sweep_total": len(lin), "raw_scan_total": len(rawset),
  "in_linear_not_raw": [hex(x) for x in sorted(lin - rawset)],
  "in_raw_not_linear": [hex(x) for x in sorted(rawset - lin)],
}
json.dump(res, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q3.json","w"), indent=1)
print({k: len(v) for k, v in r16.items()})
print({k: len(v) for k, v in r8.items()})
print("cross:", res["q3"]["a"]["cross_check_linear_vs_raw"]["in_linear_not_raw"],
      res["q3"]["a"]["cross_check_linear_vs_raw"]["in_raw_not_linear"])
