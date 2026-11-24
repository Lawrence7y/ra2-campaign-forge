"""W163: decode COL class-name records referenced by the two dirty-rect vtables,
and disassemble 0x6D2790 (Add candidate) fully with boundary-verified call sites.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

def col_name(b, p):
    # Westwood COL: 0xFFFF marker, then name string; print a window as ascii
    try:
        d = b.read(p, 0x80)
    except Exception as e:
        return "READ_ERR %s"%e
    # find first printable run >= 4 chars
    runs=[]; cur=bytearray()
    for x in d:
        if 32 <= x < 127:
            cur.append(x)
        else:
            if len(cur)>=4: runs.append(cur.decode('ascii'))
            cur=bytearray()
    if len(cur)>=4: runs.append(cur.decode('ascii'))
    return runs[:6]

def main():
    b = w.Bin()
    print("=== COL decode for vtable trailing dwords ===")
    for p in (0x80B830,0x80B860,0x80B8C8,0x80B8F8):
        print("  %08X:"%p, col_name(b,p))
        dbg=b.read(p,24)
        print("     raw:", " ".join("%02X"%x for x in dbg))

    print("=== full disasm 0x6D2790 (Add candidate) ===")
    rows,hdr=w.load_atlas(); atlas={va:r for va,r in rows}
    m=w.md32(skipdata=True)
    f=0x6D2790; size=int(atlas[f]["size"],10)
    data=b.read(f,size)
    for insn in m.disasm(data,f):
        if insn.id==0:
            print("  %08X  (skipdata %d)"%(insn.address,insn.size)); continue
        print("  %08X  %-8s %s"%(insn.address,insn.mnemonic,insn.op_str))

if __name__=="__main__":
    main()
