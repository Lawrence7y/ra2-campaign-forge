from k14_image import Image
import capstone.x86
img = Image()
pe = img.pe
sections = [(img.base+s.VirtualAddress, img.base+s.VirtualAddress+s.SizeOfRawData, s.Name.rstrip(b"\x00").decode()) for s in pe.sections]
text_lo, text_hi = next((a,b) for a,b,n in sections if n==".text")
rdata_lo, rdata_hi = next((a,b) for a,b,n in sections if n==".rdata")
out = []

def is_text(va):
    return text_lo <= va < text_hi

def type_name(td):
    try:
        b = img.read(td+8, 160)
    except Exception:
        return None
    if not b:
        return None
    s = b.split(b"\x00",1)[0]
    return s.decode("ascii", errors="replace")

def col_name(col):
    try:
        sig = img.u32(col)
        td = img.u32(col+12)
    except Exception:
        return None
    if sig != 0: return None
    n = type_name(td)
    return n if n and (n.startswith(".?AV") or n.startswith(".?AU")) else None
vts = []
for a in range(rdata_lo, rdata_hi-4, 4):
    try:
        col = img.u32(a)
    except Exception:
        continue
    if not (rdata_lo <= col < rdata_hi):
        continue
    n = col_name(col)
    if not n:
        continue
    vt = a + 4
    try:
        ok = is_text(img.u32(vt)) and is_text(img.u32(vt+4)) and is_text(img.u32(vt+8))
    except Exception:
        ok = False
    if ok:
        vts.append((vt, n, a, col))
wanted = [".?AVFootClass@@",".?AVAircraftClass@@",".?AVInfantryClass@@",".?AVUnitClass@@",".?AVBuildingClass@@"]
out.append(f"VTABLES_FOUND={len(vts)}")
out.append("RELEVANT VTABLES (slot 0x2C / 0x184 / 0x18C):")
for vt,n,colptr,col in vts:
    if any(w in n for w in wanted) or vt in (0x7E8C94,0x7E22A4):
        try:
            s2c=img.u32(vt+0x2C); s184=img.u32(vt+0x184); s18c=img.u32(vt+0x18C)
        except Exception:
            continue
        out.append(f"vt={vt:08X} name={n} colptr={colptr:08X} col={col:08X} whatami={s2c:08X} vt184={s184:08X} vt18C={s18c:08X}")
out.append("")
out.append("ALL VTABLES WITH SLOT 0x18C == 004D85D0:")
for vt,n,colptr,col in vts:
    if img.u32(vt+0x18C) == 0x4D85D0:
        out.append(f"vt={vt:08X} name={n} whatami={img.u32(vt+0x2C):08X} vt184={img.u32(vt+0x184):08X}")
out.append("")
out.append("EXACT ADDRESS PROBES:")
for vt in (0x7E8C94,0x7E22A4):
    out.append(f"vt={vt:08X} col_at_minus4={img.u32(vt-4):08X} col_name={col_name(img.u32(vt-4))} whatami={img.u32(vt+0x2C):08X} vt184={img.u32(vt+0x184):08X} vt18C={img.u32(vt+0x18C):08X}")

def find_call(instrs, target):
    return [hex(i.address) for i in instrs if i.mnemonic=="call" and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM and i.operands[0].imm==target]

for va in (0x519630,0x739EC0):
    out.append("")
    out.append(f"=== OVERRIDE {va:08X} ===")
    ins = list(img.md.disasm(img.read(va,0x80),va,count=30))
    for i in ins:
        out.append(f"{i.address:08X}  {i.bytes.hex(' '):<30}  {i.mnemonic:<8}  {i.op_str}")
        if i.mnemonic.startswith("ret"):
            break
    out.append("CALL_4D85D0=" + ",".join(find_call(ins,0x4D85D0)))

res="\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K14\EVIDENCE\VTABLE_RTTI.txt","w",encoding="utf-8").write(res+"\n")
print(res)
