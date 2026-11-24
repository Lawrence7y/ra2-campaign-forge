"""
S17-F1: template md5, swizzle restore pass, load order, dual-channel boundaries.
"""
import pe_util as P
import hashlib, csv, struct

OUT = []

def emit(s=""):
    print(s); OUT.append(s)

def f(ins):
    return f"0x{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}"

# ===== 1. 35 template bodies md5 (127B code) + 128B =====
emit("="*100); emit("1. Template block bodies md5 (channel: raw bytes)")
emit("="*100)
bodies127 = {}
for i in range(35):
    va = 0x67FDF0 + 0x80*i
    b127 = P.read(va, 127)
    b128 = P.read(va, 128)
    m127 = hashlib.md5(b127).hexdigest() if b127 else None
    m128 = hashlib.md5(b128).hexdigest() if b128 else None
    bodies127.setdefault(m127, []).append(i)
    emit(f"  #{i+1:2d} 0x{va:08X} 127B md5={m127} 128B md5={m128} last_code={b127[-1]:02X}" if b127 else f"#{i+1} NOREAD")
emit(f"  distinct 127B md5 = {len(bodies127)}: " + ", ".join(f"{k[:12]}x{len(v)}" for k,v in bodies127.items()))
# Save_Sides
bs = P.read(0x6805F0, 127)
emit(f"  Save_Sides 0x6805F0 127B md5={hashlib.md5(bs).hexdigest()}")

# ===== 2. Reset 0x6CF350 + slot5 0x6CF490 (restore pass candidates) =====
emit("\n"+"="*100); emit("2. Swizzle Reset 0x6CF350 (slot3 target) + slot5 0x6CF490 + 0x6CF410")
emit("="*100)
for va, nbytes, label in [(0x6CF350, 0x6CF430-0x6CF350, 'Reset 0x6CF350'),
                          (0x6CF490, 0x6CF4B0-0x6CF490, 'slot5 0x6CF490'),
                          (0x6CF410, 0x6CF430-0x6CF410, 'slot9 0x6CF410')]:
    emit(f"\n--- {label} ---")
    for ins in P.disasm(va, nbytes):
        emit("   " + f(ins))

# ===== 3. Find code that reads SwizzleMgr+0x4 / +0x1C vectors (restore pass) =====
emit("\n"+"="*100); emit("3. Who reads [+0x1C] vector of SwizzleMgr (Swizzles_New) — restore pass")
emit("="*100)
# Search Here_I_Am callers and look near them; also scan for lea reg,[reg+0x1c] near 0xB0C110 usage
# Instead: find all functions in range 0x6CF000..0x6CF900 disassembled, list those touching +0x1c/+0x4 of instance
for ins in P.disasm(0x6CF000, 0x6CF900-0x6CF000):
    if '0x1c]' in ins.op_str or '[eax + 4]' in ins.op_str or '0xB0C110' in ins.op_str or '0xb0c110' in ins.op_str:
        emit("   " + f(ins))

# ===== 4. Load_Core: enumerate call [reg+0xC] with preceding push of global (class load order) =====
emit("\n"+"="*100); emit("4. Load_Core 0x67E440 IStream::Read sites with context (6 insns before)")
emit("="*100)
lins = P.disasm(0x67E440, 0x67EB00-0x67E440)
for idx, ins in enumerate(lins):
    if ins.mnemonic == 'call' and '[ecx + 0xc]' in ins.op_str or (ins.mnemonic=='call' and '[eax + 0xc]' in ins.op_str) or (ins.mnemonic=='call' and '[edx + 0xc]' in ins.op_str):
        emit(f"\n  >>> call [reg+0xC] at 0x{ins.address:08X}")
        for j in range(max(0,idx-7), idx+1):
            emit("      " + f(lins[j]))

# ===== 5. Dual-channel function boundary: capstone-derived end vs atlas =====
emit("\n"+"="*100); emit("5. Dual-channel function size (capstone linear ret-end vs atlas.tsv)")
emit("="*100)
atlas = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas_map = {}
try:
    with open(atlas, 'r', encoding='utf-8', errors='ignore') as fh:
        rd = csv.reader(fh, delimiter='\t')
        for row in rd:
            if not row or row[0].strip().startswith('#'): continue
            try:
                a = int(row[0], 16)
                # find a size-like column
                atlas_map[a] = row
            except: pass
except Exception as e:
    emit(f"  atlas read error: {e}")

def capstone_end(entry, maxb=0x2000):
    """walk instructions until first ret at depth 0 (approx) - just report last ret in range before next known boundary"""
    insns = P.disasm(entry, maxb)
    # find the first 'ret' whose address is > entry+0x20
    for ins in insns:
        if ins.mnemonic in ('ret','retf') and ins.address > entry+0x20:
            return ins.address + ins.size, len(insns)
    return None, len(insns)

for entry, label in [(0x67D300,'Save_Core'),(0x67CEF0,'outer'),(0x67E440,'Load_Core'),
                     (0x67FDF0,'tmpl#1'),(0x6CF240,'HereIAm'),(0x6CF350,'Reset')]:
    end, n = capstone_end(entry)
    row = atlas_map.get(entry)
    emit(f"  {label} 0x{entry:X}: capstone first-ret-end=0x{end:X} (size=0x{end-entry:X}={end-entry}) insns_scanned={n}")
    if row:
        emit(f"      atlas row = {row[:6]}")

with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\EVIDENCE\analysis_deep2.txt",'w',encoding='utf-8') as fh:
    fh.write("\n".join(OUT))
