"""P0-INITTERM T1: exhaustive _initterm call-site + table boundary enumeration.
Read-only; independent PE parse with pefile; capstone skipdata=True.
Outputs: EVIDENCE/t1_tables.txt, EVIDENCE/t1_tables.json
"""
import sys, os, hashlib, json, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OUT = os.path.join(ROOT, "lead", "next_re_20261117_r14", "P0_INITTERM", "EVIDENCE")
EXPECTED = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

lines = []
def emit(s=""):
    lines.append(str(s))

h = hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()
emit("T1 SHA256: %s %s" % (h, "MATCH" if h == EXPECTED else "MISMATCH"))
assert h == EXPECTED
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
emit("ImageBase: %08X" % IB)
secinfo = {}
for s in pe.sections:
    name = s.Name.decode(errors="replace").rstrip("\x00")
    va = IB + s.VirtualAddress
    vs = s.Misc_VirtualSize
    raw = s.PointerToRawData
    rs = s.SizeOfRawData
    secinfo[name] = dict(va=va, vs=vs, raw=raw, rs=rs)
    emit("SECTION %-8s VA=%08X..%08X VS=%08X RAW=%08X..%08X RS=%08X" % (
        name, va, va+vs, vs, raw, raw+rs, rs))

data = open(EXE, "rb").read()

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError("VA not mapped: %08X" % va)

def read_va(va, n):
    off = va2off(va)
    return data[off:off+n]

def dword_at(va):
    return struct.unpack_from("<I", read_va(va, 4), 0)[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

# --- Decode the _initterm body to confirm semantics ---
emit("\n=== _initterm body @ 0x7CBED3 (dispatcher) ===")
for i in md.disasm(read_va(0x7CBED3, 0x20), 0x7CBED3):
    emit("  %08X  %-16s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

# --- Enumerate ALL direct call/jmp rel32 whose target == 0x7CBED3 ---
INITTERM = 0x7CBED3
text = secinfo[".text"]
text_start = text["va"]; text_end = text["va"] + text["vs"]
text_bytes = read_va(text_start, text["vs"])
direct_sites = []
for pos in range(len(text_bytes)-5):
    op = text_bytes[pos]
    if op == 0xE8 or op == 0xE9:
        rel = struct.unpack_from("<i", text_bytes, pos+1)[0]
        tgt = text_start + pos + 5 + rel
        if tgt == INITTERM:
            direct_sites.append((text_start+pos, "call" if op==0xE8 else "jmp"))
    # EB rel8 cannot reach from far but enumerate anyway
    if op == 0xEB:
        rel = struct.unpack_from("<b", text_bytes, pos+1)[0]
        tgt = text_start + pos + 2 + rel
        if tgt == INITTERM:
            direct_sites.append((text_start+pos, "jmp8"))
emit("\n=== Direct E8/E9/EB target == 0x7CBED3 within .text ===")
for a, k in direct_sites:
    emit("  %08X %s" % (a, k))
emit("  count = %d" % len(direct_sites))

# --- Enumerate indirect references: dword value == 0x7CBED3 in any mapped section ---
dword_refs = []
for name, si in secinfo.items():
    n = si["rs"]  # raw bytes present on disk
    blob = data[si["raw"]:si["raw"]+n]
    for pos in range(0, len(blob)-3):
        v = struct.unpack_from("<I", blob, pos)[0]
        if v == INITTERM:
            dword_refs.append((name, si["va"]+pos))
emit("\n=== dword value == 0x7CBED3 in mapped raw bytes (function-pointer dispatch) ===")
for name, va in dword_refs:
    emit("  %-8s %08X" % (name, va))
emit("  count = %d" % len(dword_refs))

# --- Enumerate exact-body copies of the initterm loop in .text ---
body = b"\x56\x8b\x74\x24\x08\x3b\x74\x24\x0c\x73\x0d\x8b\x06\x85\xc0\x74\x02\xff\xd0\x83\xc6\x04\xeb\xed\x5e\xc3"
copies = []
start = 0
while True:
    p = text_bytes.find(body, start)
    if p < 0: break
    copies.append(text_start + p)
    start = p + 1
emit("\n=== Exact _initterm body byte-pattern copies in .text ===")
for a in copies:
    emit("  %08X" % a)
emit("  count = %d" % len(copies))

# --- For each direct call site, decode backwards to recover pushed boundaries ---
emit("\n=== Recover boundaries at each direct call site ===")
def decode_range(va, n, label):
    emit("  -- %s @ %08X --" % (label, va))
    for i in md.disasm(read_va(va, n), va):
        emit("    %08X  %-16s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

tables = []
for site, kind in direct_sites:
    decode_range(site-0x20, 0x30, "site %08X" % site)
    # collect `push imm32` immediates in the 0x20 bytes before site by scanning raw bytes
    push_vals = []
    for d in range(0, 0x20):
        p = site - d
        b = read_va(p, 5)
        if len(b) == 5 and b[0] == 0x68:
            push_vals.append((p, struct.unpack_from("<I", b, 1)[0]))
    emit("    push imm32 found (addr,val): %s" % [(hex(a), hex(v)) for a,v in push_vals])
    # the two nearest pushes preceding the call are end then begin
    if len(push_vals) >= 2:
        # push order in source: push end (farther), push begin (nearest to call)
        beg_push = push_vals[0]   # nearest push = pfBegin
        end_push = push_vals[1]   # second nearest = pfEnd
        beg, end = beg_push[1], end_push[1]
        nslots = (end - beg)//4 if end>=beg else -1
        emit("    => begin=%08X (push@%08X) end=%08X (push@%08X) slots=%d" % (
            beg, beg_push[0], end, end_push[0], nslots))
        tables.append(dict(site=hex(site), kind=kind, begin=hex(beg), end=hex(end), slots=nslots,
                           push_begin_addr=hex(beg_push[0]), push_end_addr=hex(end_push[0])))

# --- Dump each table's dword values, classify NULL / in-.text ---
emit("\n=== Table contents ===")
for t in tables:
    beg = int(t["begin"], 16); end = int(t["end"], 16)
    emit("  TABLE begin=%08X end=%08X slots=%d site=%s" % (beg, end, t["slots"], t["site"]))
    vals = []
    nnull = 0; nintext = 0; nout = 0
    for i in range(t["slots"]):
        a = beg + 4*i
        v = dword_at(a)
        vals.append(v)
        if v == 0: nnull += 1
        elif text_start <= v < text_end: nintext += 1
        else: nout += 1
    emit("    null=%d in_text=%d out_text=%d" % (nnull, nintext, nout))
    emit("    first 8 slots: %s" % [(hex(beg+4*i), hex(vals[i])) for i in range(min(8,len(vals)))])
    emit("    last  8 slots: %s" % [(hex(beg+4*i), hex(vals[i])) for i in range(max(0,len(vals)-8),len(vals))])
    t["null"]=nnull; t["in_text"]=nintext; t["out_text"]=nout
    t["first8"] = [[hex(beg+4*i), hex(vals[i])] for i in range(min(8,len(vals)))]
    t["last8"] = [[hex(beg+4*i), hex(vals[i])] for i in range(max(0,len(vals)-8),len(vals))]

# --- Focus table: begin 0x812000 end 0x815da4. Slot0 null? then effective 3944 ---
emit("\n=== Main-table count reconciliation ===")
main = [t for t in tables if int(t["begin"],16)==0x812000 and int(t["end"],16)==0x815da4]
if main:
    m = main[0]
    slot0 = dword_at(0x812000)
    emit("  slot[0] @ 0x812000 = %08X" % slot0)
    emit("  (end-begin)/4 = %d" % m["slots"])
    emit("  slots[1..] count = %d" % (m["slots"]-1))
    emit("  audit value 3944 == slots-1 ? %s" % ((m["slots"]-1)==3944))

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT,"t1_tables.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(lines)+"\n")
with open(os.path.join(OUT,"t1_tables.json"),"w",encoding="utf-8") as f:
    json.dump(dict(sha=h, imagebase=hex(IB), sections=secinfo,
                   direct_sites=[[hex(a),k] for a,k in direct_sites],
                   dword_refs=[[n,hex(a)] for n,a in dword_refs],
                   body_copies=[hex(a) for a in copies],
                   tables=tables), f, indent=2)
print("done; lines=%d" % len(lines))
