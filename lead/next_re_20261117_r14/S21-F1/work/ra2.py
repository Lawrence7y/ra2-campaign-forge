"""S21-F1 公共二进制工具：只读 gamemd.exe，capstone skipdata=True。"""
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A

BIN = A.Bin()
MD = A.md32(skipdata=True)
MD_DETAIL = A.md32(skipdata=True)


def disasm(va, nbytes=0x400, stop_at=None):
    """线性反汇编（skipdata=True），返回 [(addr,mnem,op,size,bytes), ...]。"""
    data = BIN.read(va, nbytes)
    out = []
    for insn in MD.disasm(data, va):
        if insn.id == 0:
            continue
        out.append((insn.address, insn.mnemonic, insn.op_str, insn.size,
                    insn.bytes.hex()))
        if stop_at is not None and insn.address >= stop_at:
            break
    return out


def dump(va, nbytes=0x200, stop_at=None, grep=None):
    for addr, m, o, sz, b in disasm(va, nbytes, stop_at):
        line = f"{addr:08X}  {b:<20} {m:<8} {o}"
        if grep is None or grep.lower() in line.lower():
            print(line)


def u32(va):
    return BIN.u32(va)


def u16(va):
    return BIN.u16(va)


def u8(va):
    return BIN.u8(va)


def cstr(va, maxn=200):
    """读以 0 结尾的 ASCII 字符串。"""
    out = bytearray()
    for i in range(maxn):
        c = u8(va + i)
        if c == 0:
            break
        out.append(c)
    return out.decode("latin-1")


def iat_names():
    import pefile
    pe = pefile.PE(A.EXE, fast_load=False)
    names = {}
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode(errors="replace")
        for imp in entry.imports:
            if imp.address:
                names[imp.address] = f"{dll}!{imp.name.decode() if imp.name else hex(imp.ordinal)}"
    return names


IAT = iat_names()


def calls_in(va, nbytes=0x400):
    """列出区间内所有直接 call 目标及其中间解释。"""
    res = []
    for addr, m, o, sz, b in disasm(va, nbytes):
        if m == "call":
            res.append((addr, o))
    return res


if __name__ == "__main__":
    va = int(sys.argv[1], 16)
    n = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x200
    dump(va, n)
