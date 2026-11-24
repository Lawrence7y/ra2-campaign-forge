# -*- coding: utf-8 -*-
# R17-R66 统一口径的递归下降审计：与 verify_r66.py §[5d] 完全同一参数
#   roots = {0x00401000} ∪ 清单 6,728 个调用目标；每函数至多 2,000 条指令
# 输出线性反汇编（bounds）相对真值的：已证真 / 已证假 / 不可证
import json, struct, bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
D = open(EXE, "rb").read()

PENT = struct.unpack_from("<I", D, 0x3C)[0]; COFF = PENT + 4
NS = struct.unpack_from("<H", D, COFF + 2)[0]; OSZ = struct.unpack_from("<H", D, COFF + 16)[0]
OPT = COFF + 20; IB = struct.unpack_from("<I", D, OPT + 0x1C)[0]; SO = OPT + OSZ
SEC = []
for i in range(NS):
    o = SO + 40 * i
    n = D[o:o + 8].rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", D, o + 8)
    SEC.append((n, IB + va, vs, rp, rs))
TN, TSV, TVS, TRP, TRS = [s for s in SEC if s[0] == ".text"][0]
TEND = TSV + TVS

def rd(va, n=16):
    if not (TSV <= va < TEND):
        return None
    d = va - TSV
    return D[TRP + d:TRP + d + n]

sm = json.load(open(ROOT + r"\S21_DIRECT\_audit\EVIDENCE\scan_mine.json", "rb"))
pairs = set(map(tuple, sm["calls"]))
tgts = set(t for s, t in pairs)

# ---- 原始 E8 字节对 ----
raw = {}
for i in range(TRP, TRP + TVS - 4):
    if D[i] == 0xE8:
        site = TSV + (i - TRP)
        raw[site] = (site + 5 + struct.unpack_from("<i", D, i + 1)[0]) & 0xFFFFFFFF
raw_pairs = set((s, t) for s, t in raw.items())

# ---- 递归下降（唯一实现） ----
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
roots = {0x00401000} | tgts
dec = set(); work = sorted(roots); nins = 0
while work:
    fn = work.pop()
    if fn in dec:
        continue
    pc = fn; fs = set()
    for _ in range(2000):
        if pc in fs or pc in dec:
            break
        fs.add(pc); dec.add(pc)
        b = rd(pc)
        if not b:
            break
        g = list(md.disasm(b, pc, count=1))
        if not g:
            break
        ins = g[0]; nins += 1
        o0 = ins.bytes[0]
        if ins.mnemonic == "call" and ins.size == 5 and o0 == 0xE8:
            work.append((ins.address + 5 + struct.unpack("<i", ins.bytes[1:5])[0]) & 0xFFFFFFFF)
        elif ins.mnemonic == "jmp" and ins.size == 5 and o0 == 0xE9:
            work.append((ins.address + 5 + struct.unpack("<i", ins.bytes[1:5])[0]) & 0xFFFFFFFF); break
        elif ins.mnemonic == "jmp" and ins.size == 2 and o0 == 0xEB:
            work.append(ins.address + 2 + struct.unpack("<b", ins.bytes[1:2])[0]); break
        elif ins.mnemonic.startswith("j") and ins.size == 6 and o0 == 0x0F and (ins.bytes[1] & 0xF0) == 0x80:
            work.append(ins.address + 6 + struct.unpack("<i", ins.bytes[2:6])[0])
        elif ins.mnemonic.startswith("j") and ins.size == 2 and 0x70 <= o0 <= 0x7F:
            work.append(ins.address + 2 + struct.unpack("<b", ins.bytes[1:2])[0])
        elif ins.mnemonic.startswith("ret"):
            break
        pc = ins.address + ins.size

# 指令长度表（用于判「严格落在已解码指令内部」）
md.detail = False
lenof = {}
for a in sorted(dec):
    b = rd(a, 16)
    if not b:
        continue
    g = list(md.disasm(b, a, count=1))
    if g:
        lenof[a] = g[0].size
starts = sorted(lenof)

def inside(s):
    k = bisect.bisect_right(starts, s) - 1
    if k < 0:
        return None
    a = starts[k]
    return (a, lenof[a]) if a < s < a + lenof[a] else None

conf = [p for p in pairs if p[0] in dec]
fp = [(s, t, inside(s)) for s, t in pairs if inside(s)]
unproven = [p for p in pairs if p[0] not in dec and not inside(p[0])]

# ---- 3 条「目标在目标集合内却未记录」 ----
tgt_all = set(t for s, t in pairs)
cand = sorted(p for p in raw_pairs if p[1] in tgt_all and p not in pairs)
verdict = {}
for s, t in cand:
    g = list(md.disasm(rd(s, 8), s, count=1))
    verdict["%08X" % s] = dict(target="%08X" % t, rd_start=(s in dec),
                               rd_text=(g[0].mnemonic + " " + g[0].op_str) if g else None,
                               inside=inside(s))

# ---- 越界 target ----
oob = sorted((s, t) for s, t in pairs if not (0x400000 <= t < TEND))
oob_info = []
for s, t in oob:
    g = list(md.disasm(rd(s, 8), s, count=1))[0]
    oob_info.append(dict(site="%08X" % s, target="%08X" % t, bytes=g.bytes.hex(),
                         rd_start=s in dec, rd_text=g.mnemonic + " " + g.op_str))

# ---- 从已确认入口重扫：重扫有、清单无 ----
rescan = {}
for entry in sorted(tgts):
    pc = entry
    for _ in range(2000):
        b = rd(pc)
        if not b:
            break
        g = list(md.disasm(b, pc, count=1))
        if not g:
            break
        ins = g[0]
        if ins.mnemonic == "call" and ins.size == 5 and ins.bytes[0] == 0xE8:
            rescan[(ins.address, (ins.address + 5 + struct.unpack("<i", ins.bytes[1:5])[0]) & 0xFFFFFFFF)] = 1
        if ins.mnemonic.startswith("ret"):
            break
        pc = ins.address + ins.size
only_rescan = sorted(set(rescan) - pairs)

out = dict(
    rd_instructions=nins, rd_starts=len(dec), roots=len(roots),
    documented_pairs=len(pairs),
    confirmed_start=len(conf), proven_false=len(fp), unproven=len(unproven),
    proven_false_detail=[["%08X" % s, "%08X" % t, "%08X" % i[0], i[1]] for s, t, i in fp],
    raw_e8_pairs=len(raw_pairs), boundary_pairs=len(pairs),
    raw_minus_boundary=len(raw_pairs) - len(pairs),
    candidates_not_recorded=verdict,
    out_of_image=oob_info, out_of_image_confirmed=sum(1 for x in oob_info if x["rd_start"]),
    rescan_pairs=len(rescan), rescan_only=[[("%08X" % s), ("%08X" % t)] for s, t in only_rescan],
)
open(ROOT + r"\_r66\rd_audit.json", "w", encoding="utf-8", newline="\n").write(
    json.dumps(out, ensure_ascii=False, indent=1) + "\n")

for k in ("rd_instructions", "rd_starts", "roots", "documented_pairs", "confirmed_start",
          "proven_false", "unproven", "raw_e8_pairs", "boundary_pairs", "raw_minus_boundary",
          "out_of_image_confirmed", "rescan_pairs"):
    print("%-24s %s" % (k, out[k]))
print("out_of_image              %d" % len(oob_info))
print("rescan_only               %s" % out["rescan_only"])
print("proven_false_detail       %s" % out["proven_false_detail"])
for s, v in verdict.items():
    print("cand %s -> %s  rd_start=%s  %s" % (s, v["target"], v["rd_start"], v["rd_text"]))
for x in oob_info:
    print("oob %s -> %s  %-14s rd_start=%s" % (x["site"], x["target"], x["bytes"], x["rd_start"]))
