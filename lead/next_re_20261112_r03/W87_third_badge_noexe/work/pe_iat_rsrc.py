import hashlib
import struct
from pathlib import Path
import capstone

WORK = Path(__file__).resolve().parent
GAMEMD = WORK / "gamemd.exe"
DDRAW = WORK / "ddraw.dll"


class MiniPE:
    def __init__(self, raw: bytes):
        self.raw = raw
        if raw[:2] != b"MZ":
            raise ValueError("not MZ")
        self.e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
        if raw[self.e_lfanew:self.e_lfanew + 4] != b"PE\x00\x00":
            raise ValueError("not PE")
        coff = self.e_lfanew + 4
        (
            self.machine,
            self.num_sections,
            self.timestamp,
            _,
            _,
            self.opt_size,
            self.characteristics,
        ) = struct.unpack_from("<HHIIIHH", raw, coff)
        opt = coff + 20
        self.magic = struct.unpack_from("<H", raw, opt)[0]
        assert self.magic == 0x10B, f"unexpected PE magic 0x{self.magic:X}"
        self.entry_rva = struct.unpack_from("<I", raw, opt + 16)[0]
        self.image_base = struct.unpack_from("<I", raw, opt + 28)[0]
        self.size_of_image = struct.unpack_from("<I", raw, opt + 56)[0]
        self.checksum = struct.unpack_from("<I", raw, opt + 64)[0]
        self.num_rva_sizes = struct.unpack_from("<I", raw, opt + 92)[0]
        dd_off = opt + 96
        self.data_dirs = [
            struct.unpack_from("<II", raw, dd_off + i * 8)
            for i in range(self.num_rva_sizes)
        ]
        sec_off = opt + self.opt_size
        self.sections = []
        for i in range(self.num_sections):
            o = sec_off + i * 40
            name = raw[o:o + 8].split(b"\x00", 1)[0].decode("ascii", "replace")
            vsize, rva, raw_size, raw_ptr, _, _, _, _, char = struct.unpack_from(
                "<IIIIIIHHI", raw, o + 8
            )
            self.sections.append({
                "name": name,
                "vsize": vsize,
                "rva": rva,
                "va": self.image_base + rva,
                "raw_size": raw_size,
                "raw_ptr": raw_ptr,
                "char": char,
            })

    def rva_to_foff(self, rva: int) -> int | None:
        for s in self.sections:
            span = max(s["vsize"], s["raw_size"])
            if s["rva"] <= rva < s["rva"] + span:
                off = s["raw_ptr"] + (rva - s["rva"])
                if off < len(self.raw):
                    return off
                return None
        if rva < self.sections[0]["rva"] and rva < len(self.raw):
            return rva
        return None

    def va_to_foff(self, va: int) -> int | None:
        return self.rva_to_foff(va - self.image_base)

    def read_cstr_rva(self, rva: int) -> str:
        foff = self.rva_to_foff(rva)
        if foff is None:
            return f"<bad_rva:0x{rva:X}>"
        end = self.raw.find(b"\x00", foff)
        return self.raw[foff:end].decode("ascii", "replace")

    def parse_imports(self):
        if len(self.data_dirs) <= 1 or self.data_dirs[1][0] == 0:
            return []
        imp_rva, _ = self.data_dirs[1]
        foff = self.rva_to_foff(imp_rva)
        out = []
        while True:
            ilt_rva, ts, fwd, name_rva, iat_rva = struct.unpack_from("<IIIII", self.raw, foff)
            foff += 20
            if ilt_rva == 0 and name_rva == 0 and iat_rva == 0:
                break
            dll_name = self.read_cstr_rva(name_rva)
            tbl_rva = ilt_rva if ilt_rva != 0 else iat_rva
            tbl_foff = self.rva_to_foff(tbl_rva)
            entries = []
            idx = 0
            while True:
                val = struct.unpack_from("<I", self.raw, tbl_foff + idx * 4)[0]
                if val == 0:
                    break
                slot_rva = iat_rva + idx * 4
                slot_va = self.image_base + slot_rva
                if val & 0x80000000:
                    entries.append((slot_va, slot_rva, f"ord_{val & 0xFFFF}"))
                else:
                    hint_foff = self.rva_to_foff(val)
                    hint = struct.unpack_from("<H", self.raw, hint_foff)[0]
                    end = self.raw.find(b"\x00", hint_foff + 2)
                    fname = self.raw[hint_foff + 2:end].decode("ascii", "replace")
                    entries.append((slot_va, slot_rva, fname))
                idx += 1
            out.append((dll_name, iat_rva, entries))
        return out

    def parse_exports(self):
        if len(self.data_dirs) <= 0 or self.data_dirs[0][0] == 0:
            return []
        exp_rva, exp_size = self.data_dirs[0]
        foff = self.rva_to_foff(exp_rva)
        _, ts, _, _, _, base, num_funcs, num_names, addr_funcs_rva, addr_names_rva, addr_ords_rva = struct.unpack_from(
            "<IIHHIIIIIII", self.raw, foff
        )
        funcs_foff = self.rva_to_foff(addr_funcs_rva)
        names_foff = self.rva_to_foff(addr_names_rva)
        ords_foff = self.rva_to_foff(addr_ords_rva)
        ord_to_name = {}
        for i in range(num_names):
            nrva = struct.unpack_from("<I", self.raw, names_foff + i * 4)[0]
            ord_idx = struct.unpack_from("<H", self.raw, ords_foff + i * 2)[0]
            ord_to_name[ord_idx] = self.read_cstr_rva(nrva)
        out = []
        for idx in range(num_funcs):
            frva = struct.unpack_from("<I", self.raw, funcs_foff + idx * 4)[0]
            if frva == 0:
                continue
            fwd = ""
            if exp_rva <= frva < exp_rva + exp_size:
                fwd = self.read_cstr_rva(frva)
            out.append((base + idx, frva, ord_to_name.get(idx, "(ordinal-only)"), fwd))
        return out

    def find_resources(self):
        if len(self.data_dirs) <= 2 or self.data_dirs[2][0] == 0:
            return []
        rsrc_rva, _ = self.data_dirs[2]
        rsrc_base = self.rva_to_foff(rsrc_rva)
        leaves = []

        def walk(dir_off_rel, path):
            abs_off = rsrc_base + dir_off_rel
            _, _, _, _, n_named, n_id = struct.unpack_from("<IIHHHH", self.raw, abs_off)
            total = n_named + n_id
            for i in range(total):
                name_or_id, off_to_data = struct.unpack_from("<II", self.raw, abs_off + 16 + i * 8)
                if name_or_id & 0x80000000:
                    s_off = rsrc_base + (name_or_id & 0x7FFFFFFF)
                    slen = struct.unpack_from("<H", self.raw, s_off)[0]
                    key = self.raw[s_off + 2:s_off + 2 + slen * 2].decode("utf-16-le", "replace")
                else:
                    key = name_or_id
                if off_to_data & 0x80000000:
                    walk(off_to_data & 0x7FFFFFFF, path + (key,))
                else:
                    de_off = rsrc_base + off_to_data
                    data_rva, size, cp, _ = struct.unpack_from("<IIII", self.raw, de_off)
                    leaves.append((path + (key,), data_rva, size, de_off))

        walk(0, ())
        return leaves


def dump_pe_info(path: Path, label: str):
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    pe = MiniPE(raw)
    print(f"=== {label}: {path.name} ({len(raw)} B, sha256={sha}) ===")
    print(f"ImageBase=0x{pe.image_base:08X} SizeOfImage=0x{pe.size_of_image:08X} "
          f"EntryPoint=0x{pe.image_base + pe.entry_rva:08X} CheckSum=0x{pe.checksum:08X} TimeDateStamp=0x{pe.timestamp:08X}")
    print("Sections:")
    for s in pe.sections:
        print(f"  {s['name']:10s} VA=0x{s['va']:08X} VSize=0x{s['vsize']:08X} "
              f"RawPtr=0x{s['raw_ptr']:08X} RawSize=0x{s['raw_size']:08X} "
              f"Delta=0x{s['va'] - s['raw_ptr']:08X} Char=0x{s['char']:08X}")
    return raw, pe


def parse_dlgtemplateex(blob: bytes):
    off = 0
    dlgVer, sig, helpID, exStyle, style, cDlgItems, x, y, cx, cy = struct.unpack_from("<HHIIIHhhhh", blob, off)
    off += 26

    def read_sz_or_ord(b, p):
        val = struct.unpack_from("<H", b, p)[0]
        if val == 0x0000:
            return ("empty", 0), p + 2
        if val == 0xFFFF:
            ordv = struct.unpack_from("<H", b, p + 2)[0]
            return ("ord", ordv), p + 4
        chars = []
        while True:
            ch = struct.unpack_from("<H", b, p)[0]
            p += 2
            if ch == 0:
                break
            chars.append(chr(ch))
        return ("str", "".join(chars)), p

    menu, off = read_sz_or_ord(blob, off)
    wcls, off = read_sz_or_ord(blob, off)
    title, off = read_sz_or_ord(blob, off)
    font = None
    if style & 0x48:
        pt, weight, italic, charset = struct.unpack_from("<HHBB", blob, off)
        off += 6
        face, off = read_sz_or_ord(blob, off)
        font = (pt, weight, italic, charset, face)
    print(f"\n--- RT_DIALOG 148 (len={len(blob)}) ---")
    print(f"dlgVer={dlgVer} sig=0x{sig:04X} helpID={helpID} exStyle=0x{exStyle:08X} style=0x{style:08X} "
          f"cDlgItems={cDlgItems} rect=({x},{y},{cx},{cy}) menu={menu} cls={wcls} title={title} font={font}")
    for i in range(cDlgItems):
        off = (off + 3) & ~3
        start = off
        i_help, i_ex, i_st, ix, iy, icx, icy, iid = struct.unpack_from("<IIIhhhhI", blob, off)
        off += 24
        icls, off = read_sz_or_ord(blob, off)
        ititle, off = read_sz_or_ord(blob, off)
        extraCount = struct.unpack_from("<H", blob, off)[0]
        off += 2 + extraCount
        raw_item = blob[start:off]
        print(f"  [{i:2d}] off=0x{start:03X}..0x{off:03X} ({len(raw_item)}B) id={iid:4d}(0x{iid:03X}) "
              f"pos=({ix},{iy}) size=({icx}x{icy}) style=0x{i_st:08X} ex=0x{i_ex:08X} "
              f"cls={icls} title={ititle} extra={extraCount}")
    print(f"end_off=0x{off:03X} trailing={len(blob) - off}")


def find_iat_calls(raw: bytes, pe: MiniPE, iat_map: dict, interesting_apis: set[str]):
    text = [s for s in pe.sections if s["name"] == ".text"][0]
    t_raw = text["raw_ptr"]
    t_va = text["va"]
    t_bytes = raw[t_raw:t_raw + text["vsize"]]

    target_vas = {va: full for va, full in iat_map.items() if full.split("!", 1)[1] in interesting_apis}
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    print("\n--- IAT references to dialog/resource/window APIs in .text ---")
    for va, full in sorted(target_vas.items()):
        pat = struct.pack("<I", va)
        idx = 0
        hits = []
        while True:
            pos = t_bytes.find(pat, idx)
            if pos < 0:
                break
            idx = pos + 1
            insn_va = None
            ctx = ""
            for back in (2, 1):
                if pos >= back:
                    code = t_bytes[pos - back:pos + 8]
                    insns = list(md.disasm(code, t_va + pos - back, count=1))
                    if insns and insns[0].size >= back + 4 and pat in insns[0].bytes:
                        insn = insns[0]
                        insn_va = insn.address
                        ctx = f"{insn.bytes.hex()} | {insn.mnemonic} {insn.op_str}"
                        break
            if insn_va is None:
                insn_va = t_va + pos
                ctx = f"(raw imm32 at VA 0x{insn_va:08X})"
            hits.append((insn_va, t_raw + (insn_va - t_va), ctx))
        print(f"API {full} (IAT 0x{va:08X}): {len(hits)} hits")
        for h_va, h_foff, h_ctx in hits:
            print(f"  VA 0x{h_va:08X} (foff 0x{h_foff:06X}): {h_ctx}")


def main():
    g_raw, g_pe = dump_pe_info(GAMEMD, "gamemd.exe")
    iat_map = {}
    print("\n--- Imports (USER32 / KERNEL32 dialog-resource-related / DDRAW / all DLLs) ---")
    for dll, iat_rva, entries in g_pe.parse_imports():
        print(f"DLL: {dll} (FirstThunk RVA=0x{iat_rva:08X}, count={len(entries)})")
        show = dll.lower() in {"user32.dll", "ddraw.dll"}
        for slot_va, slot_rva, fname in entries:
            iat_map[slot_va] = f"{dll}!{fname}"
            if show or any(k in fname.lower() for k in ("resource", "dialog", "window", "module", "library", "proc")):
                print(f"  IAT 0x{slot_va:08X} (RVA 0x{slot_rva:08X}): {fname}")

    leaves = g_pe.find_resources()
    print(f"\n--- Resource Summary (total leaves={len(leaves)}) ---")
    by_type = {}
    for path, rva, sz, de_off in leaves:
        by_type.setdefault(path[0], 0)
        by_type[path[0]] += 1
        if path[0] == 5 and path[1] == 148:
            foff = g_pe.rva_to_foff(rva)
            print(f"RT_DIALOG 148: RVA=0x{rva:08X} foff=0x{foff:06X} Size={sz} DataEntry_foff=0x{de_off:06X}")
            parse_dlgtemplateex(g_raw[foff:foff + sz])
    print("Resource type counts:", by_type)

    interesting = {
        "DialogBoxParamA", "DialogBoxParamW", "DialogBoxIndirectParamA", "DialogBoxIndirectParamW",
        "CreateDialogParamA", "CreateDialogParamW", "CreateDialogIndirectParamA", "CreateDialogIndirectParamW",
        "FindResourceA", "FindResourceW", "FindResourceExA", "FindResourceExW",
        "LoadResource", "LockResource", "SizeofResource",
        "SetWindowLongA", "SetWindowLongW", "GetWindowLongA", "SetDlgItemTextA", "SetDlgItemInt",
        "ChildWindowFromPoint", "ChildWindowFromPointEx", "GetDlgCtrlID", "GetDlgItem",
        "SendDlgItemMessageA", "CreateWindowExA", "RegisterClassA", "RegisterClassExA",
        "DirectDrawCreate", "DirectDrawCreateEx", "DirectDrawEnumerateA", "DirectDrawEnumerateExA",
    }
    find_iat_calls(g_raw, g_pe, iat_map, interesting)

    print("\n" + "=" * 70)
    d_raw, d_pe = dump_pe_info(DDRAW, "ddraw.dll")
    print("\n--- ddraw.dll Imports ---")
    for dll, iat_rva, entries in d_pe.parse_imports():
        print(f"DLL: {dll} ({len(entries)} imports)")
        for slot_va, slot_rva, fname in entries:
            if any(k in fname.lower() for k in ("dialog", "resource", "hook", "proc", "window", "virtual", "library")):
                print(f"  IAT 0x{slot_va:08X}: {fname}")
    print("\n--- ddraw.dll Exports ---")
    for ordv, frva, name, fwd in d_pe.parse_exports():
        print(f"  ord={ordv:3d} RVA=0x{frva:08X} name={name} {('-> ' + fwd) if fwd else ''}")


if __name__ == "__main__":
    main()
