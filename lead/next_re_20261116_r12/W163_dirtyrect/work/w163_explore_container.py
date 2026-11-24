"""W163 exploratory: inspect memory layout around 0xB0CE88 (dirty-rect Count candidate).

Interpret as DynamicVectorClass if Count@0xB0CE88 => base@0xB0CE78:
  +0 vptr / +4 Items / +8 Cap / +0xC flags / +0x10 Count / +0x14 Inc
Also dump a wider window and interpret each 4-byte word; try plausible DVC bases
at Count-0x10 and count references.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w

def main():
    b = w.Bin()
    print("ImageBase", hex(b.image_base))
    for s in b.sections:
        print("  SEC %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X" %
              (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
    print("=== words around 0xB0CE88 ===")
    base = 0xB0CE88
    for va in range(base - 0x40, base + 0x40, 4):
        v = b.u32(va)
        tag = ""
        sec = b.sec_of(v)
        if sec: tag = " -> %s(%08X)" % (sec["name"], v)
        print("  %08X = %08X%s" % (va, v, tag))
    print("=== byte window 0xB0CE70..0xB0CEB0 ===")
    dbg = b.read(0xB0CE70, 0x40)
    print("  " + " ".join("%02X" % x for x in dbg[:16]))
    print("  " + " ".join("%02X" % x for x in dbg[16:32]))
    print("  " + " ".join("%02X" % x for x in dbg[32:48]))
    print("  " + " ".join("%02X" % x for x in dbg[48:64]))
    # DVC interpretation assuming base = Count-0x10
    print("=== DVC interp base=0xB0CE78 ===")
    f = {0xB0CE78:"vptr",0xB0CE7C:"Items",0xB0CE80:"Cap",0xB0CE84:"flags",
         0xB0CE88:"Count",0xB0CE8C:"Inc"}
    for va,name in f.items():
        print("  %-6s %08X = %08X" % (name,va,b.u32(va)))
    flags = b.read(0xB0CE84,4)
    print("  flags bytes @B0CE84 =", " ".join("%02X"%x for x in flags))

if __name__ == "__main__":
    main()
