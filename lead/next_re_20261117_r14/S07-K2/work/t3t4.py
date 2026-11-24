"""T3/T4: vtable slot semantics from .rdata + RTTI names + GetSize double-proof.
Slot counting from .rdata section boundary, NOT atlas/JSON.
"""
import sys, os, json, struct, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, md32, load_func_atlas
import capstone, bisect

ROOT = r"D:\Project\ra2-campaign-forge"
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S07-K2\EVIDENCE")
b = Bin()
sections = {s["name"]: s for s in b.sections}
text = sections[".text"]; rdata = sections[".rdata"]
TEXT_LO, TEXT_HI = text["va"], text["va"]+text["rawsize"]
RDATA_LO, RDATA_HI = rdata["va"], rdata["va"]+rdata["rawsize"]
print(".text %08X..%08X  .rdata %08X..%08X" % (TEXT_LO,TEXT_HI,RDATA_LO,RDATA_HI))

def u32(va): return b.u32(va)

def read_cstr(va, maxn=128):
    out = bytearray()
    for i in range(maxn):
        c = b.read(va+i,1)[0]
        if c == 0: break
        out.append(c)
    return out.decode("ascii", errors="replace")

def rtti_name(col):
    # COL + 0xC -> TD ; mangled name is stored INLINE at TD+8 (not a pointer).
    # (per R14 §965: correct chain is COL+0xC -> TD, name at TD+8)
    try:
        td = u32(col+0xC)
        if not (0x400000 <= td < 0x900000):
            return None, td
        # verify TD vftable pointer sanity: [td] should be a .rdata ptr
        return read_cstr(td+8), td
    except Exception as e:
        return None, -1

def count_slots(vt):
    """Count consecutive .text pointers from vt until first non-.text dword.
    Also validate vtable[-1] = COL in .rdata."""
    slots = []
    va = vt
    for i in range(256):
        try: p = u32(va)
        except: break
        if TEXT_LO <= p < TEXT_HI:
            slots.append(p); va += 4
        else:
            break
    col_before = None
    try:
        c = u32(vt-4)
        if RDATA_LO <= c < RDATA_HI: col_before = c
    except: pass
    return slots, col_before

# load canonical list
d = json.load(open(os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"),encoding="utf-8",errors="replace"))["vtables"]
by_vt = {v["vt"]: v for v in d}

# classes of interest
targets = {
    0x7E6060: "LayerClass",
    0x7E5B88: "Blitter",
    0x7E5BA0: "RLEBlitter",
    0x7E2198: "Surface",
    0x7E2070: "BSurface",
    0x7E2104: "XSurface",
    0x7E85D4: "DSurface",
    0x7E192C: "VectorClass",
    0x7E4F64: "DynamicVectorClass",
}

def demangle(n):
    if not n: return n
    s = n.replace(".?AV","").replace("@@","")
    return s

results = []
for vt, label in sorted(targets.items()):
    slots, col_before = count_slots(vt)
    j = by_vt.get(vt, {})
    col = j.get("col", col_before)
    name, td = rtti_name(col) if col else (None,-1)
    json_slots = j.get("slots", "?")
    results.append(dict(vt=vt, label=label, col=col, td=td,
                        rtti=demangle(name), nslots=len(slots), json_slots=json_slots,
                        slots=slots))

with open(os.path.join(OUTDIR,"t3_vtables.json"),"w",encoding="utf-8") as f:
    json.dump(results,f,indent=2)

print("\n%-22s %8s %8s %5s %5s  %s" % ("label","vt","col","slots","json","RTTI"))
for r in results:
    print("%-22s %08X %08X %5d %5s  %s" % (r["label"],r["vt"],r["col"] or 0,r["nslots"],r["json_slots"],r["rtti"]))

# Dump key slots for LayerClass: slot at vtable offset 0x1C (idx7)=Add, 0x10(idx4)=locate
print("\n=== LayerClass vtable slots ===")
lc = [r for r in results if r["label"]=="LayerClass"][0]
for idx,p in enumerate(lc["slots"][:16]):
    off = idx*4
    tag = ""
    if off==0x10: tag=" <-locate/RemoveFromLayer idx4"
    if off==0x1C: tag=" <-Add(0x5519B0) idx7"
    print("  v[%2d] off=0x%02X -> %08X%s" % (idx,off,p,tag))

# T4: B8 imm32 C3 scan over all target vtables (Blitter family)
print("\n=== T4 GetSize B8 imm32 C3 in Blitter-family slots ===")
m = md32(skipdata=False)
blit_results=[]
for v in d:
    cls = v.get("class","") or ""
    if not any(k in cls for k in ["Blit","RLE","Surface"]): continue
    vt=v["vt"]
    slots, _ = count_slots(vt)
    for idx,p in enumerate(slots):
        try: code=b.read(p,6)
        except: continue
        if code[0]==0xB8 and code[5]==0xC3:
            imm=struct.unpack("<I",code[1:5])[0]
            blit_results.append((vt,demangle(cls),idx,imm,p))
print("B8 imm32 C3 hits in Blit/RLE/Surface slots:",len(blit_results))
for vt,cls,idx,imm,p in blit_results[:60]:
    print("  vt=%08X %-55s v[%d] imm=0x%X (%d) at %08X" % (vt,cls[:55],idx,imm,imm,p))
with open(os.path.join(OUTDIR,"t4_getsize_hits.tsv"),"w",encoding="utf-8") as f:
    f.write("vt\tclass\tslot\timm_hex\timm_dec\tfunc\n")
    for vt,cls,idx,imm,p in blit_results:
        f.write("%08X\t%s\t%d\t0x%X\t%d\t%08X\n"%(vt,cls,idx,imm,imm,p))

# ---- BASELINE (discipline 1): whole-image B8 imm32 C3 and B8 imm32 counts ----
data_text = b.pe.__data__[text["raw"]:text["raw"]+text["rawsize"]]
n_c3 = 0; n_imm32 = 0
for i in range(len(data_text)-5):
    if data_text[i] == 0xB8:
        n_imm32 += 1
        if data_text[i+5] == 0xC3:
            n_c3 += 1
print("\n=== BASELINE whole-image .text ===")
print("B8 imm32 (no C3 req) =", n_imm32)
print("B8 imm32 C3          =", n_c3, " (R14 baseline: 837 / 666)")
