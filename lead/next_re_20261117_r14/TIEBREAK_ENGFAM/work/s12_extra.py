"""s12: identity of the two extra vectors seen around the chain."""
import pe

VECS = [0x008B4154, 0x00A8B230, 0x008B4120]


def main():
    p = pe.open_pe()
    t = p.text()
    data = p.raw(t["vstart"], t["vsz"])
    for vec in VECS:
        n = b"\xC7\x05" + vec.to_bytes(4, "little")
        i = 0
        print(f"vector 0x{vec:08X}")
        hit = False
        while True:
            i = data.find(n, i)
            if i < 0:
                break
            hit = True
            site = t["vstart"] + i
            vt = int.from_bytes(data[i + 6:i + 10], "little")
            r = p.rtti(vt)
            print(f"   write 0x{site:08X} -> vt 0x{vt:08X}  "
                  f"{r.get('name') or r.get('err')}")
            i += 1
        if not hit:
            print("   no `C7 05` install found")


if __name__ == "__main__":
    main()
