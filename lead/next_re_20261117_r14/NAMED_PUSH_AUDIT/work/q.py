"""行查询：持有表 / 安装点 / 同槽派发点 / 直接调用者。"""
import json, os, sys
import core as C

S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan.json")))


def q(entry):
    print("=== entry %08X  body=%s" % (entry, C.body(entry)))
    hs = C.holdings(entry)
    print("-- holdings (%d)" % len(hs))
    for h in hs:
        slotval = C.u32(h["vt"] + h["slot_off"])
        print("   vt=%08X slot=%d off=+%02X val=%08X cls=%s col=%08X td=%08X sect=%s"
              % (h["vt"], h["slot"], h["slot_off"], slotval, h["cls"], h["col"], h["td"], h["sect"]))
    for h in hs:
        vt = h["vt"]
        body = C.body(entry)
        print("-- install sites for vt %08X (abs=static global)" % vt)
        cnt = 0
        for ins in S["installs"]:
            if ins["imm"] != vt:
                continue
            cnt += 1
            fn = C.func_at(ins["site"])
            inrow = bool(body and body[0] <= ins["site"] < body[0] + body[1])
            print("   %s  fn=%s in_row=%s" % (ins["ins"], fn, inrow))
        print("   total", cnt)
        print("-- vcall sites with disp=%d (0x%X)" % (h["disp"] if "disp" in h else h["slot_off"], h["slot_off"]))
        vc = [v for v in S["vcalls"] if v["disp"] == h["slot_off"] and not v["index"]]
        print("   count", len(vc), "(全程序，无类型信息，仅计数)")
    print("-- direct callers of entry")
    cs = [c for c in S["calls"] if c["target"] == entry]
    print("   count", len(cs), [("%08X" % c["site"]) for c in cs][:20])


if __name__ == "__main__":
    for a in sys.argv[1:]:
        q(int(a, 16))
