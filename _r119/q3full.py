import sys, json, time
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
T = PE_.sec_by_name(".text"); TB = BUF[T["raw"]:T["raw"]+T["rawsize"]]; TVA = T["va"]

t0 = time.time()
insns = []   # (va, size, mnem, op)
o = 0
N = len(TB)
resync = 0
while o < N:
    got = 0
    for (a, sz, mn, op) in md.disasm_lite(TB[o:o+65536], TVA + o):
        insns.append((a, sz, mn, op)); got = 1
        o = a - TVA + sz
    if not got or o < N:
        # stopped on an undecodable byte
        o += 1; resync += 1
        if resync > 3_000_000: break
print("decode", len(insns), "insns, resyncs", resync, "elapsed %.1fs" % (time.time()-t0))

def formof(mn, op, va, sz):
    ops = op.replace(" ", "")
    b = TB[va-TVA:va-TVA+sz]
    if mn in ("shl", "sal"):
        if ops.endswith(",4"):
            if b[0] == 0xC1: return "shl_rm32_imm4_C1/4"
            if b[0] == 0xC0: return "shl_rm8_imm4_C0/4"
            if b[0] == 0x66 and b[1] == 0xC1: return "shl_rm16_imm4_66C1/4"
            if b[0] == 0xD1: return "shl_rm32_1_D1/4"
        if ops.endswith(",cl") or ops.endswith(",CL"):
            return "shl_rm32_cl_D3/4(dyn)"
    if mn == "imul":
        p = op.split(",")
        if len(p) == 3:
            v = p[2].strip()
            if v in ("0x10", "16"):
                if b[0] == 0x6B: return "imul_r32_rm32_imm0x10_6B"
                if b[0] == 0x69: return "imul_r32_rm32_imm0x10_69"
            if v in ("8", "0x8"):
                if b[0] == 0x6B: return "imul_r32_rm32_imm0x8_6B"
                if b[0] == 0x69: return "imul_r32_rm32_imm0x8_69"
    return None

hits16, hits8, dyn, lea8 = [], [], [], []
for (a, sz, mn, op) in insns:
    f = formof(mn, op, a, sz)
    if f:
        rec = {"va": a, "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "mn": mn, "op": op, "form": f}
        if "imm4" in f or "imm0x10" in f: hits16.append(rec)
        elif "imm8" in f and mn == "imul": hits8.append(rec)
        elif "dyn" in f: dyn.append(rec)
    if mn == "lea" and ("*8" in op.replace(" ", "")):
        lea8.append({"va": a, "bytes": TB[a-TVA:a-TVA+sz].hex(" "), "op": op})
print("16x:", len(hits16), " 8x-imul:", len(hits8), " shl,cl:", len(dyn), " lea*8:", len(lea8))
json.dump({"n_insns": len(insns), "resyncs": resync,
           "hits16": hits16, "hits8": hits8, "dyn": dyn, "lea8_n": len(lea8),
           "lea8_sample": lea8[:10]},
          open("/home/t628/projects/ra2-campaign-forge/_r119/_q3_sweep.json","w"), indent=1)
