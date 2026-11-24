from k14_image import Image, COV, ATL
import capstone.x86
img = Image()
out = []

def instrs(va, n=120):
    return list(img.md.disasm(img.read(va, n*16), va, count=n))

for va in (0x005B3040, 0x005B3740):
    out.append(f"=== DISASM {va:08X} ===")
    for i in instrs(va, 60):
        out.append(f"{i.address:08X}  {i.bytes.hex(' '):<32}  {i.mnemonic:<8}  {i.op_str}")
        if i.mnemonic.startswith("ret"):
            break
    out.append("")
text = next(s for s in img.pe.sections if s.Name.rstrip(b"\x00") == b".text")
tstart = img.base + text.VirtualAddress
tbytes = img.data[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
needle = bytes.fromhex("ac6c8100")
raw = []
for off in range(len(tbytes)-len(needle)+1):
    if tbytes[off:off+len(needle)] == needle:
        raw.append(tstart + off)
out.append("TEXT RAW LITERAL 0x816CAC HITS=" + ",".join(hex(x) for x in raw))

atlas = []
with open(ATL, "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 2 and c[0] and all(ch in "0123456789abcdefABCDEF" for ch in c[0]):
            atlas.append((int(c[0],16), int(c[1])))
atlas.sort()
cov = {}
with open(COV, "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 8 and c[0]:
            cov[int(c[0],16)] = c
out.append("RAW HIT CONTEXT (nearest atlas entry):")
for va in raw:
    lo = max((x for x in atlas if x[0] <= va), default=None)
    c = cov.get(lo[0]) if lo else None
    out.append(f"{va:08X}  atlas_lo={lo[0]:08X}+{lo[1]:#x}  cov_name={c[2] if c else '-'}  cov_grade={c[4] if c else '-'}")

res = "\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\MISSION_816CAC.txt","w",encoding="utf-8").write(res+"\n")
print(res)
