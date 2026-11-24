"""Independent RE evidence library for R4_FILL_AUDIT (v2).

Reads the PE bytes itself and disassembles with capstone. No code from the
executor's fill.py is imported or reused, and nothing here reads
R4_FILL_91_R2/evidence/*.txt.
"""
import bisect
import struct

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"


class Image:
    def __init__(self, path=EXE):
        self.path = path
        self.pe = pefile.PE(path, fast_load=False)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.buf = self.pe.__data__
        self.sections = []
        for s in self.pe.sections:
            self.sections.append(dict(
                name=s.Name.decode().rstrip('\x00'),
                va=self.base + s.VirtualAddress,
                vsize=s.Misc_VirtualSize,
                raw_off=s.PointerToRawData,
                raw_size=s.SizeOfRawData,
            ))
        self.by_name = {s['name']: s for s in self.sections}
        self.text = self.by_name['.text']
        self.entry = self.base + self.pe.OPTIONAL_HEADER.AddressOfEntryPoint

    def off(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['raw_size']):
                d = va - s['va']
                if d >= s['raw_size']:
                    return None
                o = s['raw_off'] + d
                if 0 <= o < len(self.buf):
                    return o
                return None
        return None

    def raw(self, va, n):
        o = self.off(va)
        return None if o is None else self.buf[o:o + n]

    def u32(self, va):
        b = self.raw(va, 4)
        return struct.unpack('<I', b)[0] if b and len(b) == 4 else None

    def u16(self, va):
        b = self.raw(va, 2)
        return struct.unpack('<H', b)[0] if b and len(b) == 2 else None

    def cstr(self, va, maxn=300):
        b = self.raw(va, maxn)
        if b is None:
            return None
        z = b.find(b'\x00')
        return b[:len(b) if z < 0 else z]

    def in_image(self, va):
        return self.off(va) is not None

    def secname(self, va):
        for s in self.sections:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['raw_size']):
                return s['name']
        return None

    def is_text(self, va):
        s = self.text
        return s['va'] <= va < s['va'] + s['vsize']


class Dis:
    def __init__(self, img):
        self.img = img
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.detail = True
        self._sweep = None

    # ---------- decode ----------
    def at(self, va, n=1):
        out, a = [], va
        for _ in range(n):
            chunk = self.img.raw(a, 16)
            if not chunk:
                break
            got = None
            for ins in self.md.disasm(chunk, a):
                got = ins
                break
            if got is None:
                break
            out.append(got)
            a += got.size
        return out

    def one(self, va):
        got = self.at(va, 1)
        return got[0] if got else None

    # ---------- linear sweep of .text (exact boundaries for prev-insn lookups) ----
    def sweep(self):
        if self._sweep is not None:
            return self._sweep
        tv = self.img.text
        blob = self.img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
        index = {}
        bad = 0
        for ins in self.md.disasm(blob, tv['va']):
            index[ins.address] = ins
        self._sweep = (index, bad)
        return self._sweep

    def index(self):
        return self.sweep()[0]

    def prev(self, va):
        """Instruction immediately preceding va in the linear sweep."""
        s = self.sweep()[0]
        keys = self._keys if hasattr(self, '_keys') else None
        if keys is None:
            self._keys = sorted(s)
            keys = self._keys
        i = bisect.bisect_left(keys, va) - 1
        if i < 0:
            return None, None
        p = keys[i]
        ins = s[p]
        if ins.address + ins.size != va:
            return p, None
        return p, ins

    # ---------- operands ----------
    @staticmethod
    def imm(ins):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                return op.imm
        return None

    @staticmethod
    def mem(ins):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                return op
        return None

    @staticmethod
    def dst_is_mem(ins):
        return bool(ins.operands) and ins.operands[0].type == capstone.x86.X86_OP_MEM

    @staticmethod
    def jtarget(ins):
        if ins.operands and ins.group(capstone.x86.X86_GRP_JUMP):
            op = ins.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                return op.imm
        return None

    @staticmethod
    def calltarget(ins):
        if ins.mnemonic == 'call' and ins.operands:
            op = ins.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                return op.imm
        return None

    # ---------- CFG walk (calls not followed) ----------
    def body(self, start, limit=80000):
        seen, work = {}, [start]
        while work:
            a = work.pop()
            while True:
                if a in seen or len(seen) > limit:
                    break
                ins = self.one(a)
                if ins is None:
                    break
                seen[a] = ins
                m = ins.mnemonic
                if m in ('ret', 'retf', 'int3', 'ud2', 'hlt', 'icebp'):
                    break
                if ins.group(capstone.x86.X86_GRP_JUMP):
                    t = self.jtarget(ins)
                    if t is not None:
                        work.append(t)
                    if m == 'jmp':
                        break
                a = ins.address + ins.size
        return seen


def demangle_class(dec_raw):
    if not dec_raw:
        return None
    s = dec_raw.decode('latin-1')
    if not s.startswith('.?A'):
        return None
    rest = s[3:]
    if not rest or rest[0] not in 'VU':
        return None
    body = rest[1:]
    if not body.endswith('@@'):
        return None
    return body[:-2]


def col_at(img, vt):
    """Read the COL that guard the table starting at vt (u32(vt-4))."""
    col = img.u32(vt - 4)
    if col is None or not img.in_image(col):
        return None
    d = dict(col=col,
             sig=img.u32(col),
             offset=img.u32(col + 4),
             cd=img.u32(col + 8),
             td=img.u32(col + 0xC),
             pchd=img.u32(col + 0x10),
             pself=img.u32(col + 0x14))
    if d['td'] and img.in_image(d['td']):
        d['td_raw'] = img.cstr(d['td'] + 8)
        d['td_name'] = demangle_class(d['td_raw'])
    else:
        d['td_raw'], d['td_name'] = None, None
    return d


def plausible_col(img, col):
    """MSVC6-style COL: signature 0, small offset, pTD -> decorated TD name.
    (pSelf reads 0 in this image, so it is NOT used as a validity test.)"""
    if col is None or not img.in_image(col):
        return False
    if img.u32(col) != 0:
        return False
    off = img.u32(col + 4)
    if off is None or off > 0x1000:
        return False
    td = img.u32(col + 0xC)
    if not td or not img.in_image(td):
        return False
    return demangle_class(img.cstr(td + 8, 96)) is not None


def vtable_start(img, hit, cap=8000):
    """Walk back over table entries until the dword in front is a plausible
    COL whose address is data (not code) — that address is the table start."""
    c = hit
    for _ in range(cap):
        col = img.u32(c - 4)
        if col is not None and not img.is_text(col) and plausible_col(img, col):
            return c
        c -= 4
        if not img.in_image(c):
            break
    return None


def store_sites(img, dis, value):
    """Every .text instruction that stores the immediate `value` to memory.
    Candidate addresses come from a byte search for the imm32, then each is
    validated by decoding an instruction that ends exactly at the immediate."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    pat = struct.pack('<I', value)
    found, loaded = {}, {}
    pos = blob.find(pat)
    while pos >= 0:
        end = pos + 4
        for start in range(max(0, end - 15), end):
            ins = None
            for i in dis.md.disasm(blob[start:end], tv['va'] + start):
                ins = i
                break
            if ins is None or ins.address + ins.size != tv['va'] + end:
                continue
            if not any(op.type == capstone.x86.X86_OP_IMM and op.imm == value
                       for op in ins.operands):
                continue
            if ins.mnemonic.startswith('mov') and dis.dst_is_mem(ins):
                found.setdefault(tv['va'] + start, ins)
            else:
                loaded.setdefault(tv['va'] + start, ins)
        pos = blob.find(pat, pos + 1)
    return found, loaded


def prev_insn(dis, va):
    """Previous instruction boundary of va via the linear sweep (validated)."""
    p, ins = dis.prev(va)
    return ins


def atexit_superset(img, stub, window=48):
    """Conservative *superset* of atexit registrations: every function address
    that appears as a `push imm32` (0x68 + imm32) inside the `window` bytes
    before a `call <stub>`. Over-inclusive on purpose: proving a host is NOT in
    this set is therefore a safe argument."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    out = []
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            if tv['va'] + pos + 5 + rel == stub:
                lo = max(0, pos - window)
                p = blob.find(b'\x68', lo, pos - 4)
                while p >= 0:
                    fn = struct.unpack('<I', blob[p + 1:p + 5])[0]
                    if img.is_text(fn):
                        out.append((tv['va'] + pos, fn, tv['va'] + p))
                    p = blob.find(b'\x68', p + 1, pos - 4)
        pos = blob.find(b'\xe8', pos + 1)
    return out


def call_targets_anywhere(img):
    """Call rel32 destinations that are themselves instruction boundaries in the
    local sense: 0xE8 followed by rel32 landing inside .text."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    out = set()
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            tgt = tv['va'] + pos + 5 + rel
            if img.is_text(tgt):
                out.add(tgt)
        pos = blob.find(b'\xe8', pos + 1)
    return out


def atexit_set(img, dis, stub=None):
    """Kept for compatibility: strict `68 imm32; E8 rel32` form."""
    return atexit_superset(img, stub or ATEXIT_STUB_GUESS, window=0) if False else \
        [(c, f) for c, f, _ in atexit_superset(img, stub or ATEXIT_STUB_GUESS, window=8)]


def atexit_set(img, dis, stub):
    """Strict form `68 imm32; E8 rel32 -> stub` (push immediately before)."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    out = []
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos >= 5 and blob[pos - 5] == 0x68 and pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            if tv['va'] + pos + 5 + rel == stub:
                fn = struct.unpack('<I', blob[pos - 4:pos])[0]
                if img.is_text(fn):
                    out.append((tv['va'] + pos, fn))
        pos = blob.find(b'\xe8', pos + 1)
    return out


def start_candidates(img):
    """Plausible function starts: byte after >=2 bytes of 0xCC/0x90 padding,
    byte after a `ret` / `ret imm16` / `jmp rel`, plus call destinations."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    cands = set()
    i, n = 0, len(blob)
    while i < n:
        if blob[i] in (0xCC, 0x90):
            j = i
            while j < n and blob[j] in (0xCC, 0x90):
                j += 1
            if j - i >= 2 and j < n:
                cands.add(tv['va'] + j)
            i = j
        else:
            i += 1
    def add_after(idx):
        j = idx
        while j < n and blob[j] in (0xCC, 0x90):
            j += 1
        if j < n:
            cands.add(tv['va'] + j)

    for i in range(n - 2):
        if blob[i] == 0xC3:                       # ret
            add_after(i + 1)
        elif blob[i] == 0xC2 and i + 3 <= n:      # ret imm16
            add_after(i + 3)
        elif blob[i] == 0xEB and i + 2 <= n:      # jmp rel8
            add_after(i + 2)
        elif blob[i] == 0xE9 and i + 5 <= n:      # jmp rel32
            add_after(i + 5)
    pos = blob.find(b'\xe8')
    while pos >= 0:
        if pos + 5 <= len(blob):
            rel = struct.unpack('<i', blob[pos + 1:pos + 5])[0]
            tgt = tv['va'] + pos + 5 + rel
            if img.is_text(tgt):
                cands.add(tgt)
        pos = blob.find(b'\xe8', pos + 1)
    return cands


DTOR_FREE_CALLS = ()          # filled by audit from the image


def dtor_shape(dis, host, free_callees, vt_writers=None):
    """Recognise `??_G` (scalar deleting destructor: flag test + deallocator call
    + ret imm) and `??1` (re-installs a vtable, then tail-jumps to a base dtor)."""
    body = dis.body(host, limit=200000)
    insns = sorted(body.items())
    flags, callees = set(), []
    has_flag_test = False
    tail_jmp = None
    for a, ins in insns:
        if ins.mnemonic == 'test' and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_MEM and \
                'esp' in ins.op_str and ins.op_str.rstrip().endswith(', 1'):
            has_flag_test = True
        t = dis.calltarget(ins)
        if t is not None:
            callees.append(t)
        if ins.mnemonic == 'jmp' and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_IMM:
            tail_jmp = ins.operands[0].imm
    frees = [c for c in callees if c in free_callees]
    if has_flag_test and frees:
        flags.add('scalar-deleting-dtor')
    if tail_jmp is not None and vt_writers is not None:
        ok = vt_writers(tail_jmp) if callable(vt_writers) else (tail_jmp in vt_writers)
        if ok:
            flags.add('base-dtor-tailjmp')
    return dict(flags=sorted(flags), has_flag_test=has_flag_test,
                frees=['%08X' % c for c in frees],
                tail_jmp=('%08X' % tail_jmp) if tail_jmp else None)


def store_target(dis, host, site, insn):
    """Resolve the memory destination of the install instruction when possible:
    absolute disp, or [reg+disp] with the last `mov reg, imm32` before it."""
    op = dis.mem(insn)
    if op is None:
        return None
    if op.mem.base == 0 and op.mem.index == 0:
        return ('absolute', op.mem.disp & 0xFFFFFFFF)
    if op.mem.index == 0:
        body = dis.body(host, limit=200000)
        reg = op.mem.base
        val = None
        for a in sorted(x for x in body if x < site):
            i2 = body[a]
            if i2.mnemonic == 'mov' and i2.operands and \
                    i2.operands[0].type == capstone.x86.X86_OP_REG and \
                    i2.operands[0].reg == reg and len(i2.operands) > 1 and \
                    i2.operands[1].type == capstone.x86.X86_OP_IMM:
                val = i2.operands[1].imm
        if val is not None:
            return ('reg-loaded-static', (val + (op.mem.disp - (1 << 32 if op.mem.disp > 0x7FFFFFFF else 0))) & 0xFFFFFFFF, '%08X' % val)
    return ('register-relative', None)


def host_for_site(dis, site, cands, window=0x4000):
    """Largest candidate start within `window` below site whose CFG body
    (calls not followed) contains the site. Padding bytes themselves are never
    accepted as starts."""
    near = sorted([c for c in cands if site - window <= c <= site and
                   dis.img.raw(c, 1) not in (None, b'\x90', b'\xcc')], reverse=True)
    for c in near:
        if site in dis.body(c, limit=200000):
            return c
    return None


def indirect_sites(img, dis, value, maxn=14):
    """`mov reg, imm32(value)` followed by `mov [mem], same reg` in the same
    straight-line run: the equivalent of an immediate store."""
    tv = img.text
    blob = img.buf[tv['raw_off']:tv['raw_off'] + tv['raw_size']]
    pat = struct.pack('<I', value)
    out = {}
    pos = blob.find(pat)
    while pos >= 0:
        end = pos + 4
        ins = None
        for st in range(max(0, end - 15), end):
            for i in dis.md.disasm(blob[st:end], tv['va'] + st):
                ins = i
                break
            if ins is not None and ins.address + ins.size == tv['va'] + end:
                break
            ins = None
        if ins is not None and ins.mnemonic.startswith('mov') and ins.operands \
                and ins.operands[0].type == capstone.x86.X86_OP_REG \
                and any(op.type == capstone.x86.X86_OP_IMM and op.imm == value
                        for op in ins.operands):
            reg = ins.operands[0].reg
            a = ins.address + ins.size
            for _ in range(maxn):
                nxt = dis.one(a)
                if nxt is None:
                    break
                if nxt.mnemonic.startswith('mov') and nxt.operands \
                        and nxt.operands[0].type == capstone.x86.X86_OP_MEM \
                        and len(nxt.operands) > 1 \
                        and nxt.operands[1].type == capstone.x86.X86_OP_REG \
                        and nxt.operands[1].reg == reg:
                    out[nxt.address] = (ins.address, nxt)
                    break
                if nxt.group(capstone.x86.X86_GRP_JUMP) or nxt.mnemonic in (
                        'call', 'ret', 'push', 'pop'):
                    break
                if any(op.type == capstone.x86.X86_OP_REG and op.reg == reg
                       and i == 0 for i, op in enumerate(nxt.operands)):
                    break
                a = nxt.address + nxt.size
        pos = blob.find(pat, pos + 1)
    return out


def iat_map(img):
    m = {}
    for d in getattr(img.pe, 'DIRECTORY_ENTRY_IMPORT', []):
        for imp in d.imports:
            if imp.name:
                m[imp.address] = imp.name.decode()
    return m
