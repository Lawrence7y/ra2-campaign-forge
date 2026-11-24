from k14_image import Image
from datetime import datetime, timezone, timedelta
img = Image()
start = 0x004D85D0
size = 2401
code = img.read(start, size)
insns = list(img.md.disasm(code, start))
out = ["S10_K14 TARGET DISASM 004D85D0",
       "TIME=" + datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="microseconds"),
       f"CAP={len(insns)} REAL_INSTRUCTIONS; raw_bytes={size}; image_base={img.base:#x}",
       "addr        bytes                                       mnemonic  operands"]
for i in insns:
    out.append(f"{i.address:08X}  {i.bytes.hex(' '):<48}  {i.mnemonic:<8}  {i.op_str}")
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\TARGET_DISASM.txt","w",encoding="utf-8").write("\n".join(out)+"\n")
print("\n".join(out))
