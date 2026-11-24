# throwaway probe — verify RTTI/CHD layout, C7 05 scan, init-table pattern, demangle
import struct, re
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE = 0x400000
pe = pefile.PE(EXE)
img = pe.get_memory_mapped_image()
size = len(img)
print("SizeOfImage=0x%X mapped=0x%X" % (pe.OPTIONAL_HEADER.SizeOfImage, size))
for s in pe.sections:
    print("  sec %-8s va=0x%08X vsz=0x%06X rsz=0x%06X chars=0x%08X" % (
        s.Name.rstrip(b"\x00").decode(), BASE + s.VirtualAddress,
        s.Misc_VirtualSize, s.SizeOfRawData, s.Characteristics))

def u32(va):
    off = va - BASE
    if off < 0 or off + 4 > size:
        return None
    return struct.unpack_from("<I", img, off)[0]

def cstr(va, maxlen=512):
    off = va - BASE
    if off < 0 or off >= size:
        return None
    end = img.find(b"\x00", off, off + maxlen)
    if end < 0:
        return None
    raw = img[off:end]
    if not raw or any(c < 0x20 or c > 0x7E for c in raw):
        return None
    return raw.decode("ascii")

# --- 1. RTTI chain for known W132 vftable 0x7E182C (CommandClass row) ---
vft = 0x7E182C
col = u32(vft - 4)
ptd = u32(col + 0x0C)
name = cstr(ptd + 8)
print("\n[RTTI] vft=0x%X col=0x%X sig=%d off1=%d cdoff=%d ptd=0x%X name=%r" % (
    vft, col, u32(col), u32(col + 4), u32(col + 8), ptd, name))
chd = u32(col + 0x10)
n = u32(chd + 8)
arr = u32(chd + 0x0C)
print("[CHD] chd=0x%X sig=%d attr=%d numbases=%d arr=0x%X" % (chd, u32(chd), u32(chd + 4), n, arr))
for k in range(n):
    bcd = u32(arr + 4 * k)
    dws = " ".join("%08X" % (u32(bcd + 4 * i) or 0) for i in range(6))
    print("  entry%d bcd=0x%X dwords=[%s]" % (k, bcd, dws))
    for off in (0, 4, 8):
        p = u32(bcd + off)
        nm = cstr(p + 8) if p else None
        print("     +0x%X -> 0x%08X name=%r" % (off, p or 0, nm))

# --- 2. raw C7 05 scan over .text ---
tx = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
lo = BASE + tx.VirtualAddress
hi = lo + tx.SizeOfRawData
blob = img[lo - BASE:hi - BASE]
hits = []
idx = blob.find(b"\xc7\x05")
while idx >= 0:
    if idx + 10 <= len(blob):
        dst, val = struct.unpack_from("<II", blob, idx + 2)
        hits.append((lo + idx, dst, val))
    idx = blob.find(b"\xc7\x05", idx + 1)
print("\n[C7 05] total hits in .text:", len(hits))
print("  stores to 0x87F658:", [(hex(a), hex(v)) for a, d2, v in hits if d2 == 0x87F658])

data_lo, data_hi = 0x812000, 0xB79BE4
def rtti_name(v):
    c2 = u32(v - 4)
    if not c2 or u32(c2) != 0:
        return None
    p = u32(c2 + 0x0C)
    nm = cstr(p + 8) if p else None
    return nm

resolved = {}
unresolved_vft_names = {}
for a, d2, v in hits:
    if data_lo <= d2 < data_hi:
        nm = rtti_name(v)
        if nm and nm.startswith(".?A"):
            if "VectorClass" in nm and "?$" in nm:
                resolved.setdefault(d2, []).append((a, v, nm))
            else:
                unresolved_vft_names.setdefault(nm, 0)
                unresolved_vft_names[nm] += 1
print("  resolved VectorClass-family globals from raw scan:", len(resolved))
other = sorted(set(n for n in unresolved_vft_names if n.startswith(".?A")))
print("  distinct .?A* names stored into .data that are NOT VectorClass-family:", len(other))
for nm in other[:25]:
    print("    ", nm)

# --- 3. init table pattern: push z; push a; call ---
pat = re.compile(rb"\x68(....)\x68(....)\xe8", re.S)
print("\n[init table]")
found = 0
for m in pat.finditer(blob):
    z = struct.unpack("<I", m.group(1))[0]
    a = struct.unpack("<I", m.group(2))[0]
    if a and z and a < z and (z - a) < 0x4000 and 0x7E1000 <= a < 0x812000 and 0x7E1000 <= z < 0x812000:
        ok = bad = 0
        for va in range(a, z, 4):
            p = u32(va)
            if p and lo <= p < BASE + tx.VirtualAddress + tx.Misc_VirtualSize:
                ok += 1
            else:
                bad += 1
        if bad == 0 and ok >= 2:
            found += 1
            print("  candidate @code 0x%08X: xc_a=0x%08X xc_z=0x%08X entries=%d all-text=%s" % (
                lo + m.start(), a, z, ok, bad == 0))
print("  found:", found)

# --- 4. demangle smoke test ---
class Dem:
    def __init__(self, s):
        self.s = s; self.i = 0
    def fail(self): raise ValueError("fail@%d:%r" % (self.i, self.s[self.i:self.i+8]))
    def peek(self, k=0):
        j = self.i + k
        return self.s[j] if j < len(self.s) else ""
    def ident(self):
        j = self.s.find("@", self.i)
        if j < 0: self.fail()
        nm = self.s[self.i:j]; self.i = j + 1
        return nm
    def qualified(self, env):
        parts = []
        while True:
            c = self.peek()
            if c == "@" or c == "":
                if c == "@": self.i += 1
                break
            if c == "?" and self.peek(1) == "$":
                self.i += 2
                parts.append(self.template(env))
            else:
                nm = self.ident()
                if nm[:1].isdigit():
                    d = int(nm[0])
                    parts.append(env[d-1] if env and 1 <= d <= len(env) else "<bk%d>" % d)
                else:
                    parts.append(nm)
            c = self.peek()
            if c == "@":
                self.i += 1
                break
            elif c == "" or not (c.isalnum() or c in "_?"):
                break
        return "::".join(reversed(parts))
    def template(self, env):
        tname = self.ident()
        targs = []
        while True:
            c = self.peek()
            if c == "@":
                self.i += 1
                break
            if c == "": self.fail()
            targs.append(self.type(targs + env))
        env2 = list(targs) + env
        # scope parts after template args (namespaces / backrefs)
        parts = [tname + "<" + ",".join(targs) + ">"]
        while True:
            c = self.peek()
            if c == "@":
                self.i += 1
                break
            elif c == "":
                break
            elif c.isalnum() or c in "_?":
                nm = self.ident() if not (c == "?" and self.peek(1) == "$") else None
                if nm is None:
                    self.i += 2
                    parts.append(self.template(env2))
                elif nm[:1].isdigit():
                    d = int(nm[0])
                    parts.append(env2[d-1] if 1 <= d <= len(env2) else "<bk%d>" % d)
                else:
                    parts.append(nm)
            else:
                break
        return "::".join(reversed(parts))
    def type(self, env):
        c = self.peek()
        if c in "PQRS":
            self.i += 1
            cv = self.peek()
            const = volatile = False
            if cv in "ABCD":
                self.i += 1
                const = cv in "BD"; volatile = cv in "CD"
            inner = self.type(env)
            if volatile: inner += " volatile"
            if const: inner = "const " + inner
            return inner + ("*" if c in "PR" else "^^")
        if c in "VUT":
            self.i += 1
            return self.qualified(env)
        if c == "?" and self.peek(1) == "$":
            self.i += 2
            return self.template(env)
        if c in "AB":
            self.i += 1
            return self.type(env) + "&"
        BASIC = {"D":"char","C":"signed char","E":"unsigned char","F":"short","G":"unsigned short",
                 "H":"int","I":"unsigned int","J":"long","K":"unsigned long","M":"float","N":"double",
                 "O":"long double"}
        if c == "_" and self.peek(1) == "N":
            self.i += 2; return "bool"
        if c in BASIC:
            self.i += 1; return BASIC[c]
        self.fail()

def demangle(nm):
    d = Dem(nm)
    if nm.startswith(".?A"): d.i = 3
    else: return None
    try:
        return d.type([])
    except ValueError:
        return None

tests = [
    ".?AV?$DynamicVectorClass@PAVUnitClass@@@@",
    ".?AV?$DynamicVectorClass@PBVCommandClass@@@@",
    ".?AV?$VectorClass@PAVUnitClass@@@@",
    ".?AV?$DynamicVectorClass@PAV?$List@PAVFooClass@@@@@@",
    ".?AV?$DynamicVectorClass@H@@",
]
print("\n[demangle]")
for t in tests:
    print("  %r -> %r" % (t, demangle(t)))
# demangle the actual resolved names found
print("\n[demangle of real resolved names (first 10)]")
cnt = 0
for d2, lst in sorted(resolved.items()):
    for a, v, nm in lst:
        if cnt < 10:
            print("  base=0x%08X vft=0x%08X %r -> %r" % (d2, v, nm, demangle(nm)))
            cnt += 1
    if cnt >= 10:
        break
