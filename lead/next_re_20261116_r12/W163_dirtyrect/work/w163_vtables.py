"""W163: look up the two vtables written into the dirty-rect container ctor,
and record nearby vtable words (class names via COL where possible).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w

def main():
    b = w.Bin()
    vtms = w.load_vtable_members()
    for vt in (0x7F429C, 0x7F42BC):
        print("=== vtable %08X ===" % vt)
        # read words around vt
        for va in range(vt-0x10, vt+0x40, 4):
            v = b.u32(va)
            sec = b.sec_of(v)
            tag = (" -> "+sec["name"]) if sec else ""
            print("  %08X = %08X%s" % (va, v, tag))
        if vt in vtms:
            print("  members:", [(hex(s),hex(f),c) for s,f,c in vtms[vt]])
        else:
            print("  (not in vtable_members.tsv)")
    # also check vtables_canonical.json for a class name
    cp = w.VTABLES_CANON
    with open(cp,"r",encoding="utf-8",errors="replace") as f:
        j = json.load(f)
    print("=== search canonical json for vtables ===")
    # structure unknown; do a text search
    txt = json.dumps(j)
    for s in ("7f429c","7F429C","7f42bc","7F42BC"):
        idx = txt.find(s)
        print("  token",s,"at",idx)
        if idx>=0:
            print("  ctx:", txt[max(0,idx-200):idx+200])

if __name__=="__main__":
    main()
